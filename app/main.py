"""
SearchPro – unified search and knowledge index across all business data.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from .database import SessionLocal, engine
from .models import Base
from .routers import dashboard, indexes, saved_searches, search
from .seed import run_seed

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ── DB setup SQL ───────────────────────────────────────────────────────────────

_TRIGGER_SEARCH_VECTOR = """
CREATE OR REPLACE FUNCTION searchpro_update_search_vector()
RETURNS trigger AS $$
BEGIN
  NEW.search_vector = to_tsvector(
    'english',
    coalesce(NEW.name,        '') || ' ' ||
    coalesce(NEW.title,       '') || ' ' ||
    coalesce(NEW.content,     '') || ' ' ||
    coalesce(NEW.source_app,  '') || ' ' ||
    coalesce(NEW.source_type, '')
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

_TRIGGER_UPDATED_AT = """
CREATE OR REPLACE FUNCTION searchpro_set_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

_DDL_STATEMENTS = [
    # Trigger functions
    _TRIGGER_SEARCH_VECTOR,
    _TRIGGER_UPDATED_AT,
    # Drop + recreate so updates to the function body take effect
    "DROP TRIGGER IF EXISTS trg_indexes_search_vector ON indexes;",
    """
    CREATE TRIGGER trg_indexes_search_vector
    BEFORE INSERT OR UPDATE ON indexes
    FOR EACH ROW EXECUTE FUNCTION searchpro_update_search_vector();
    """,
    "DROP TRIGGER IF EXISTS trg_indexes_updated_at ON indexes;",
    """
    CREATE TRIGGER trg_indexes_updated_at
    BEFORE UPDATE ON indexes
    FOR EACH ROW EXECUTE FUNCTION searchpro_set_updated_at();
    """,
    # Indexes for performance
    "CREATE INDEX IF NOT EXISTS idx_indexes_search_vector ON indexes USING GIN(search_vector);",
    "CREATE INDEX IF NOT EXISTS idx_indexes_source_app    ON indexes (source_app);",
    "CREATE INDEX IF NOT EXISTS idx_indexes_source_type   ON indexes (source_type);",
    "CREATE INDEX IF NOT EXISTS idx_indexes_last_synced   ON indexes (last_synced DESC);",
    "CREATE INDEX IF NOT EXISTS idx_search_log_searched_at ON search_log (searched_at DESC);",
]


# ── Lifespan ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SearchPro starting up …")

    # 1. Create tables (idempotent)
    Base.metadata.create_all(engine)
    logger.info("Tables verified / created.")

    # 2. Install triggers and performance indexes
    with engine.connect() as conn:
        for stmt in _DDL_STATEMENTS:
            conn.execute(text(stmt))
        conn.commit()
    logger.info("Triggers and indexes installed.")

    # 3. Seed sample data (no-op if already present)
    db = SessionLocal()
    try:
        run_seed(db)
    finally:
        db.close()

    logger.info("SearchPro ready.")
    yield
    logger.info("SearchPro shutting down.")


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SearchPro",
    description=(
        "Unified search and knowledge index across all business data.\n\n"
        "**Authentication**: pass your API token in the `GDEV_API_TOKEN` header."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ── Health (no auth) ───────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"], summary="Liveness check")
def health():
    return {"status": "ok"}


# ── Routers ────────────────────────────────────────────────────────────────────

_PREFIX = "/api/v1"

app.include_router(search.router,         prefix=_PREFIX)
app.include_router(indexes.router,        prefix=_PREFIX)
app.include_router(saved_searches.router, prefix=_PREFIX)
app.include_router(dashboard.router,      prefix=_PREFIX)
