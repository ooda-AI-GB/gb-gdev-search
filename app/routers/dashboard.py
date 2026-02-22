from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..database import get_db
from ..models import Index, SearchLog
from ..schemas import AppFreshness, DashboardResponse, SearchLogResponse

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard", response_model=DashboardResponse, summary="Search index overview")
def dashboard(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token),
):
    # Total records indexed
    total_indexed: int = db.query(func.count(Index.id)).scalar() or 0

    # Count per source_app
    app_counts = (
        db.query(Index.source_app, func.count(Index.id).label("cnt"))
        .group_by(Index.source_app)
        .all()
    )
    by_app = {row.source_app: row.cnt for row in app_counts}

    # Recent 10 searches
    recent_rows = (
        db.query(SearchLog)
        .order_by(SearchLog.searched_at.desc())
        .limit(10)
        .all()
    )
    recent_searches = [SearchLogResponse.model_validate(r) for r in recent_rows]

    # Index freshness per app
    freshness_rows = (
        db.query(
            Index.source_app,
            func.count(Index.id).label("record_count"),
            func.max(Index.last_synced).label("last_synced"),
        )
        .group_by(Index.source_app)
        .order_by(Index.source_app)
        .all()
    )
    index_freshness = [
        AppFreshness(
            source_app=row.source_app,
            record_count=row.record_count,
            last_synced=row.last_synced,
        )
        for row in freshness_rows
    ]

    return DashboardResponse(
        total_indexed=total_indexed,
        by_app=by_app,
        recent_searches=recent_searches,
        index_freshness=index_freshness,
    )
