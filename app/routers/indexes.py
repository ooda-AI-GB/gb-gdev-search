from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..database import get_db
from ..models import Index
from ..schemas import (
    BulkIndexRequest,
    BulkIndexResponse,
    IndexCreate,
    IndexListResponse,
    IndexResponse,
)

router = APIRouter(tags=["Indexes"])


def _upsert_index(db: Session, item: IndexCreate) -> tuple[IndexResponse, bool]:
    """
    Insert or update an index entry keyed on (source_app, record_id).
    Returns (IndexResponse, created: bool).
    """
    now = datetime.now(timezone.utc)
    values = dict(
        name=item.name,
        source_app=item.source_app.value,
        source_type=item.source_type.value,
        record_id=item.record_id,
        title=item.title,
        content=item.content,
        tags=item.tags,
        url=item.url,
        last_synced=now,
        updated_at=now,
    )

    stmt = pg_insert(Index).values(**values, created_at=now)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_indexes_source_record",
        set_={
            "name": stmt.excluded.name,
            "source_type": stmt.excluded.source_type,
            "title": stmt.excluded.title,
            "content": stmt.excluded.content,
            "tags": stmt.excluded.tags,
            "url": stmt.excluded.url,
            "last_synced": stmt.excluded.last_synced,
            "updated_at": stmt.excluded.updated_at,
        },
    ).returning(Index)

    result = db.execute(stmt)
    db.flush()

    # Determine whether a row was inserted (created) or updated
    row = result.fetchone()
    # created_at equals last_synced only on fresh insert (both set to `now`)
    created = row.created_at >= now.replace(microsecond=0)

    record = db.query(Index).filter(
        Index.source_app == item.source_app.value,
        Index.record_id == item.record_id,
    ).one()

    return IndexResponse.model_validate(record), created


# ── GET /indexes ───────────────────────────────────────────────────────────────

@router.get("/indexes", response_model=IndexListResponse, summary="Browse indexed records")
def list_indexes(
    source_app: Optional[str] = Query(None, description="Filter by source application"),
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token),
):
    q = db.query(Index)
    if source_app:
        q = q.filter(Index.source_app == source_app)
    if source_type:
        q = q.filter(Index.source_type == source_type)

    total = q.count()
    items = q.order_by(Index.updated_at.desc()).offset(offset).limit(limit).all()
    return IndexListResponse(
        total=total,
        items=[IndexResponse.model_validate(i) for i in items],
    )


# ── POST /indexes/bulk ─────────────────────────────────────────────────────────

@router.post(
    "/indexes/bulk",
    response_model=BulkIndexResponse,
    status_code=status.HTTP_200_OK,
    summary="Bulk upsert index entries",
)
def bulk_index(
    payload: BulkIndexRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token),
):
    created = updated = 0
    errors: list[str] = []

    for item in payload.items:
        try:
            _, was_created = _upsert_index(db, item)
            if was_created:
                created += 1
            else:
                updated += 1
        except Exception as exc:
            errors.append(f"{item.source_app}:{item.record_id} – {exc}")

    db.commit()
    return BulkIndexResponse(created=created, updated=updated, errors=errors)


# ── POST /indexes ──────────────────────────────────────────────────────────────

@router.post(
    "/indexes",
    response_model=IndexResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add or update a single index entry",
)
def create_or_update_index(
    payload: IndexCreate,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token),
):
    record, _ = _upsert_index(db, payload)
    db.commit()
    return record


# ── DELETE /indexes ────────────────────────────────────────────────────────────

@router.delete(
    "/indexes",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an indexed record",
)
def delete_index(
    source_app: str = Query(..., description="Source application identifier"),
    record_id: str = Query(..., description="Record ID within the source application"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token),
):
    deleted = (
        db.query(Index)
        .filter(Index.source_app == source_app, Index.record_id == record_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No index entry found for source_app={source_app!r}, record_id={record_id!r}",
        )
