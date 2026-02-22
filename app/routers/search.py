from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..database import get_db
from ..models import Index, SearchLog
from ..schemas import SearchResponse, SearchResult, SuggestionResponse

router = APIRouter(tags=["Search"])


def _build_rank(q: str):
    """Return a ts_rank_cd expression using plainto_tsquery."""
    ts = func.plainto_tsquery("english", q)
    return func.ts_rank_cd(Index.search_vector, ts).label("rank")


@router.get("/search", response_model=SearchResponse, summary="Unified full-text search")
def unified_search(
    q: str = Query(..., description="Search keyword(s)"),
    app: Optional[str] = Query(
        None, description="Comma-separated source apps to filter (e.g. crm,helpdesk)"
    ),
    type: Optional[str] = Query(
        None, description="Comma-separated source types to filter (e.g. contact,ticket)"
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: Optional[str] = Query(None, description="Identifier of the searching user"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token),
):
    apps = [a.strip() for a in app.split(",")] if app else None
    types = [t.strip() for t in type.split(",")] if type else None

    ts_func = func.plainto_tsquery("english", q)
    rank_col = func.ts_rank_cd(Index.search_vector, ts_func).label("rank")

    base_q = db.query(Index, rank_col)

    # Full-text search – fall back to ILIKE for very short / stop-word-only queries
    base_q = base_q.filter(
        or_(
            Index.search_vector.op("@@")(ts_func),
            Index.title.ilike(f"%{q}%"),
        )
    )

    if apps:
        base_q = base_q.filter(Index.source_app.in_(apps))
    if types:
        base_q = base_q.filter(Index.source_type.in_(types))

    total = base_q.count()

    rows = base_q.order_by(desc("rank"), Index.title).offset(offset).limit(limit).all()

    results: list[SearchResult] = []
    for idx, rank in rows:
        data = {
            col.name: getattr(idx, col.name)
            for col in Index.__table__.columns
            if col.name != "search_vector"
        }
        data["rank"] = float(rank) if rank else 0.0
        results.append(SearchResult(**data))

    # Log the search
    db.add(
        SearchLog(
            query=q,
            filters={"app": apps, "type": types},
            results_count=total,
            user=user,
        )
    )
    db.commit()

    return SearchResponse(query=q, total=total, limit=limit, offset=offset, results=results)


@router.get(
    "/search/suggestions",
    response_model=SuggestionResponse,
    summary="Autocomplete suggestions from indexed titles",
)
def search_suggestions(
    q: str = Query(..., description="Partial search string"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token),
):
    rows = (
        db.query(Index.title)
        .filter(Index.title.ilike(f"%{q}%"))
        .distinct()
        .order_by(Index.title)
        .limit(limit)
        .all()
    )
    return SuggestionResponse(query=q, suggestions=[r[0] for r in rows])
