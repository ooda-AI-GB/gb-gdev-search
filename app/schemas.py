from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SourceApp(str, Enum):
    crm = "crm"
    helpdesk = "helpdesk"
    analytics = "analytics"
    social = "social"
    jobs = "jobs"
    cloud = "cloud"
    finance = "finance"
    legal = "legal"
    research = "research"
    productivity = "productivity"


class SourceType(str, Enum):
    contact = "contact"
    deal = "deal"
    ticket = "ticket"
    article = "article"
    post = "post"
    job = "job"
    transaction = "transaction"
    contract = "contract"
    task = "task"
    source = "source"


# ── Index schemas ──────────────────────────────────────────────────────────────

class IndexCreate(BaseModel):
    name: str = Field(..., max_length=500)
    source_app: SourceApp
    source_type: SourceType
    record_id: str = Field(..., max_length=255)
    title: str = Field(..., max_length=1000)
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    url: Optional[str] = Field(None, max_length=2000)


class IndexUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=500)
    title: Optional[str] = Field(None, max_length=1000)
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    url: Optional[str] = Field(None, max_length=2000)


class IndexResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    source_app: str
    source_type: str
    record_id: str
    title: str
    content: Optional[str]
    tags: Optional[List[str]]
    url: Optional[str]
    last_synced: datetime
    created_at: datetime
    updated_at: datetime


class IndexListResponse(BaseModel):
    total: int
    items: List[IndexResponse]


class BulkIndexRequest(BaseModel):
    items: List[IndexCreate]


class BulkIndexResponse(BaseModel):
    created: int
    updated: int
    errors: List[str] = []


# ── Search schemas ─────────────────────────────────────────────────────────────

class SearchResult(IndexResponse):
    rank: float = 0.0


class SearchResponse(BaseModel):
    query: str
    total: int
    limit: int
    offset: int
    results: List[SearchResult]


class SuggestionResponse(BaseModel):
    query: str
    suggestions: List[str]


# ── SavedSearch schemas ────────────────────────────────────────────────────────

class SavedSearchCreate(BaseModel):
    name: str = Field(..., max_length=500)
    query: str = Field(..., max_length=1000)
    filters: Optional[Dict[str, Any]] = None
    user: Optional[str] = Field(None, max_length=255)


class SavedSearchUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=500)
    query: Optional[str] = Field(None, max_length=1000)
    filters: Optional[Dict[str, Any]] = None


class SavedSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    query: str
    filters: Optional[Dict[str, Any]]
    user: Optional[str]
    created_at: datetime


class SavedSearchListResponse(BaseModel):
    total: int
    items: List[SavedSearchResponse]


# ── SearchLog schemas ──────────────────────────────────────────────────────────

class SearchLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query: str
    filters: Optional[Dict[str, Any]]
    results_count: int
    user: Optional[str]
    searched_at: datetime


# ── Dashboard schemas ──────────────────────────────────────────────────────────

class AppFreshness(BaseModel):
    source_app: str
    record_count: int
    last_synced: Optional[datetime]


class DashboardResponse(BaseModel):
    total_indexed: int
    by_app: Dict[str, int]
    recent_searches: List[SearchLogResponse]
    index_freshness: List[AppFreshness]
