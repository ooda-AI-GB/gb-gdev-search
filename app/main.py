"""
SearchPro – unified search and knowledge index across all business data.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import text, func as sqlfunc
from sqlalchemy.orm import Session

from .database import SessionLocal, engine, get_db
from .models import Base, Index, SavedSearch, SearchLog
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


# ── Root dashboard (no auth) ──────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root_dashboard(db: Session = Depends(get_db)):
    index_count = db.query(sqlfunc.count(Index.id)).scalar() or 0
    saved_count = db.query(sqlfunc.count(SavedSearch.id)).scalar() or 0
    search_count = db.query(sqlfunc.count(SearchLog.id)).scalar() or 0
    apps = db.query(Index.source_app, sqlfunc.count(Index.id)).group_by(Index.source_app).all()
    app_count = len(apps)
    app_rows = ""
    for app_name, cnt in sorted(apps, key=lambda x: x[1], reverse=True):
        app_rows += f'<tr><td>{app_name}</td><td style="font-weight:600">{cnt}</td></tr>'
    recent = db.query(SearchLog).order_by(SearchLog.searched_at.desc()).limit(8).all()
    log_rows = ""
    for s in recent:
        ts = s.searched_at.strftime("%Y-%m-%d %H:%M") if s.searched_at else "—"
        log_rows += f'<tr><td>{s.query}</td><td>{s.results_count}</td><td>{s.user or "—"}</td><td>{ts}</td></tr>'
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Search Pro</title>
<style>
:root{{--primary:#4f8ef7;--success:#34c759;--warning:#f5a623;--danger:#e74c3c;--bg:#1a1f36;--bg-light:#f5f7fa;--card:#fff;--text:#2c3e50;--muted:#7f8c9b;--border:#e1e5eb}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:system-ui,-apple-system,sans-serif;background:var(--bg-light);color:var(--text);display:flex;min-height:100vh}}
.sidebar{{width:240px;background:var(--bg);color:#fff;display:flex;flex-direction:column;flex-shrink:0}}
.logo{{padding:1.5rem;font-size:1.4rem;font-weight:700}}
.nav-links{{flex:1;padding:0 1rem}}
.nav-link{{display:block;padding:.75rem 1rem;color:#cbd5e1;text-decoration:none;border-radius:6px;margin-bottom:.25rem}}
.nav-link:hover,.nav-link.active{{background:rgba(255,255,255,.15);color:#fff}}
.main{{flex:1;padding:2rem;overflow-y:auto}}
h1{{font-size:1.8rem;margin-bottom:1.5rem}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem;margin-bottom:2rem}}
.card{{background:var(--card);border-radius:10px;padding:1.5rem;border:1px solid var(--border)}}
.card .label{{font-size:.85rem;color:var(--muted);margin-bottom:.25rem}}
.card .value{{font-size:1.6rem;font-weight:700}}
.card .value.blue{{color:var(--primary)}} .card .value.green{{color:var(--success)}} .card .value.orange{{color:var(--warning)}}
.tables{{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem}}
@media(max-width:900px){{.tables{{grid-template-columns:1fr}}}}
table{{width:100%;border-collapse:collapse;background:var(--card);border-radius:10px;overflow:hidden;border:1px solid var(--border)}}
th,td{{padding:.75rem 1rem;text-align:left;border-bottom:1px solid var(--border)}}
th{{background:var(--bg);color:#fff;font-weight:600;font-size:.85rem;text-transform:uppercase;letter-spacing:.5px}}
tr:last-child td{{border-bottom:none}}
.section-title{{font-size:1.1rem;font-weight:600;margin-bottom:1rem}}
a.api-link{{display:inline-block;margin-top:1.5rem;padding:.5rem 1rem;background:var(--primary);color:#fff;border-radius:6px;text-decoration:none;font-size:.9rem}}
</style></head><body>
<div class="sidebar">
  <div class="logo">Search Pro</div>
  <div class="nav-links">
    <a href="/" class="nav-link active">Dashboard</a>
    <a href="/docs" class="nav-link">API Docs</a>
  </div>
</div>
<div class="main">
  <h1>Dashboard</h1>
  <div class="cards">
    <div class="card"><div class="label">Indexed Records</div><div class="value blue">{index_count}</div></div>
    <div class="card"><div class="label">Source Apps</div><div class="value green">{app_count}</div></div>
    <div class="card"><div class="label">Saved Searches</div><div class="value orange">{saved_count}</div></div>
    <div class="card"><div class="label">Total Searches</div><div class="value">{search_count}</div></div>
  </div>
  <div class="tables">
    <div>
      <div class="section-title">Records by Source App</div>
      <table><thead><tr><th>App</th><th>Records</th></tr></thead><tbody>{app_rows if app_rows else '<tr><td colspan="2" style="text-align:center;color:var(--muted)">No indexed records yet</td></tr>'}</tbody></table>
    </div>
    <div>
      <div class="section-title">Recent Searches</div>
      <table><thead><tr><th>Query</th><th>Results</th><th>User</th><th>Time</th></tr></thead><tbody>{log_rows if log_rows else '<tr><td colspan="4" style="text-align:center;color:var(--muted)">No searches yet</td></tr>'}</tbody></table>
    </div>
  </div>
  <a href="/docs" class="api-link">API Documentation &rarr;</a>
</div></body></html>"""


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
