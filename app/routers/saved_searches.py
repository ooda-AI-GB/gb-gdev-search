from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..database import get_db
from ..models import SavedSearch
from ..schemas import (
    SavedSearchCreate,
    SavedSearchListResponse,
    SavedSearchResponse,
    SavedSearchUpdate,
)

router = APIRouter(tags=["Saved Searches"])


# ── GET /saved_searches ────────────────────────────────────────────────────────

@router.get(
    "/saved_searches",
    response_model=SavedSearchListResponse,
    summary="List all saved searches",
)
def list_saved_searches(
    user: Optional[str] = Query(None, description="Filter by user"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token),
):
    q = db.query(SavedSearch)
    if user:
        q = q.filter(SavedSearch.user == user)
    total = q.count()
    items = q.order_by(SavedSearch.created_at.desc()).offset(offset).limit(limit).all()
    return SavedSearchListResponse(
        total=total,
        items=[SavedSearchResponse.model_validate(s) for s in items],
    )


# ── POST /saved_searches ───────────────────────────────────────────────────────

@router.post(
    "/saved_searches",
    response_model=SavedSearchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a saved search",
)
def create_saved_search(
    payload: SavedSearchCreate,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token),
):
    record = SavedSearch(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return SavedSearchResponse.model_validate(record)


# ── GET /saved_searches/{id} ───────────────────────────────────────────────────

@router.get(
    "/saved_searches/{saved_search_id}",
    response_model=SavedSearchResponse,
    summary="Get a saved search by ID",
)
def get_saved_search(
    saved_search_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token),
):
    record = db.query(SavedSearch).filter(SavedSearch.id == saved_search_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")
    return SavedSearchResponse.model_validate(record)


# ── PUT /saved_searches/{id} ───────────────────────────────────────────────────

@router.put(
    "/saved_searches/{saved_search_id}",
    response_model=SavedSearchResponse,
    summary="Update a saved search",
)
def update_saved_search(
    saved_search_id: int,
    payload: SavedSearchUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token),
):
    record = db.query(SavedSearch).filter(SavedSearch.id == saved_search_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return SavedSearchResponse.model_validate(record)


# ── DELETE /saved_searches/{id} ────────────────────────────────────────────────

@router.delete(
    "/saved_searches/{saved_search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a saved search",
)
def delete_saved_search(
    saved_search_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token),
):
    deleted = (
        db.query(SavedSearch)
        .filter(SavedSearch.id == saved_search_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")
