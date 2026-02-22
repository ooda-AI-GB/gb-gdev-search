"""
Seed data – sample index records covering every source_app and source_type.
Only runs when the indexes table is empty so restarts are idempotent.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .models import Index, SavedSearch

logger = logging.getLogger(__name__)

_NOW = datetime.now(timezone.utc)


SEED_INDEXES: list[dict] = [
    # ── CRM ────────────────────────────────────────────────────────────────────
    dict(
        source_app="crm", source_type="contact", record_id="crm-c-001",
        name="John Smith",
        title="John Smith – VP Engineering, Acme Corp",
        content=(
            "Key enterprise contact at Acme Corp responsible for all engineering tooling purchases. "
            "Budget authority up to $500 k annually. Last engaged February 2026 regarding Q2 renewal."
        ),
        tags=["vip", "enterprise", "engineering", "decision-maker"],
        url="https://crm.example.com/contacts/1",
    ),
    dict(
        source_app="crm", source_type="contact", record_id="crm-c-002",
        name="Sarah Johnson",
        title="Sarah Johnson – Head of Procurement, GlobalTech",
        content=(
            "Procurement lead managing all SaaS vendor relationships at GlobalTech. "
            "Currently evaluating three search platform vendors. Strong interest in unified indexing."
        ),
        tags=["procurement", "evaluation", "globaltech"],
        url="https://crm.example.com/contacts/2",
    ),
    dict(
        source_app="crm", source_type="contact", record_id="crm-c-003",
        name="Marco Reyes",
        title="Marco Reyes – CTO, Nimbus Logistics",
        content=(
            "Technical decision-maker for Nimbus Logistics. Interested in API-first integrations "
            "and data governance. Attended our webinar on enterprise search in January 2026."
        ),
        tags=["cto", "api", "logistics", "nimbus"],
        url="https://crm.example.com/contacts/3",
    ),
    dict(
        source_app="crm", source_type="deal", record_id="crm-d-001",
        name="Acme Corp Enterprise License",
        title="Acme Corp – Enterprise License Renewal Q1 2026",
        content=(
            "Annual enterprise license for 500 seats. Contract value $450 000. "
            "Currently in legal review; SLA terms under negotiation. Expected close: March 2026."
        ),
        tags=["enterprise", "renewal", "Q1-2026", "legal-review"],
        url="https://crm.example.com/deals/1",
    ),
    dict(
        source_app="crm", source_type="deal", record_id="crm-d-002",
        name="GlobalTech Pilot",
        title="GlobalTech – Analytics Platform 90-Day Pilot",
        content=(
            "Pilot program for 50 users at $15 000. Expansion potential to $200 k ARR. "
            "Pilot started February 2026; checkpoint review scheduled for April 2026."
        ),
        tags=["pilot", "analytics", "expansion", "globaltech"],
        url="https://crm.example.com/deals/2",
    ),

    # ── Helpdesk ───────────────────────────────────────────────────────────────
    dict(
        source_app="helpdesk", source_type="ticket", record_id="hd-t-001",
        name="TICKET-4521 SSO Login Failure",
        title="TICKET-4521: SSO login broken after Okta config update",
        content=(
            "Critical: approximately 200 enterprise users across 5 accounts cannot log in via SSO "
            "following Okta configuration push on 2026-02-20. Engineering investigating certificate "
            "mismatch between entity ID and ACS URL. Workaround: direct username/password login."
        ),
        tags=["critical", "sso", "okta", "authentication", "enterprise"],
        url="https://helpdesk.example.com/tickets/4521",
    ),
    dict(
        source_app="helpdesk", source_type="ticket", record_id="hd-t-002",
        name="TICKET-4519 API Rate Limit 429 Errors",
        title="TICKET-4519: Unexpected 429 errors on burst API requests",
        content=(
            "Customer reports 429 Too Many Requests errors when performing burst uploads. "
            "Rate limit: 1 000 req/min standard tier. Customer needs guidance on exponential "
            "backoff and request batching best practices."
        ),
        tags=["api", "rate-limit", "429", "customer"],
        url="https://helpdesk.example.com/tickets/4519",
    ),
    dict(
        source_app="helpdesk", source_type="article", record_id="hd-a-001",
        name="SSO SAML Okta Setup Guide",
        title="How to Configure SAML SSO with Okta",
        content=(
            "Step-by-step guide: create Okta application, set entity ID and ACS URL, "
            "configure attribute mapping (email, firstName, lastName, groups), "
            "run test login, troubleshoot certificate mismatches and clock skew errors."
        ),
        tags=["sso", "saml", "okta", "guide", "authentication"],
        url="https://helpdesk.example.com/articles/sso-okta",
    ),
    dict(
        source_app="helpdesk", source_type="article", record_id="hd-a-002",
        name="API Rate Limiting Best Practices",
        title="Understanding API Rate Limits and Retry Strategies",
        content=(
            "Default limits: 1 000 req/min (standard), 10 000 req/min (enterprise). "
            "Implement exponential backoff: wait 2^attempt seconds before retry. "
            "Use bulk endpoints to reduce request count. Monitor X-RateLimit-Remaining header."
        ),
        tags=["api", "rate-limit", "retry", "best-practices"],
        url="https://helpdesk.example.com/articles/api-rate-limits",
    ),

    # ── Analytics ──────────────────────────────────────────────────────────────
    dict(
        source_app="analytics", source_type="source", record_id="an-s-001",
        name="Q1 2026 Revenue Dashboard",
        title="Q1 2026 Revenue Analytics – 23 % YoY Growth",
        content=(
            "Monthly Recurring Revenue reached $2.4 M. Growth drivers: enterprise upsells (+41 %), "
            "new logo acquisition (+18 %). Churn improved to 1.8 %. "
            "Top revenue segment: Enterprise (45 %), Mid-Market (35 %), SMB (20 %)."
        ),
        tags=["revenue", "Q1-2026", "mrr", "growth", "churn"],
        url="https://analytics.example.com/dashboards/q1-2026-revenue",
    ),
    dict(
        source_app="analytics", source_type="source", record_id="an-s-002",
        name="User Engagement Report Feb 2026",
        title="Monthly Active User Engagement – February 2026",
        content=(
            "MAU: 45 000 (+12 % MoM). Average session duration: 12 minutes. "
            "Feature adoption: Search (78 %), Reports (65 %), API (45 %), Exports (30 %). "
            "Mobile usage grew 34 %; iOS app rating 4.7 stars."
        ),
        tags=["mau", "engagement", "mobile", "features", "february-2026"],
        url="https://analytics.example.com/dashboards/engagement-feb-2026",
    ),

    # ── Social ─────────────────────────────────────────────────────────────────
    dict(
        source_app="social", source_type="post", record_id="sm-p-001",
        name="SearchPro 2.0 Launch Tweet",
        title="Twitter/X: SearchPro 2.0 General Availability Announcement",
        content=(
            "Announcing SearchPro 2.0 with unified cross-app full-text search! "
            "Index CRM, helpdesk, finance, legal and more in one place. "
            "847 likes, 312 retweets, 95 replies. Trending under #ProductHunt on launch day."
        ),
        tags=["launch", "product", "twitter", "trending", "searchpro-2.0"],
        url="https://twitter.com/searchpro/status/178920000001",
    ),
    dict(
        source_app="social", source_type="post", record_id="sm-p-002",
        name="Acme Corp Case Study LinkedIn",
        title="LinkedIn: How Acme Corp 10x'd Search ROI with SearchPro",
        content=(
            "Long-form case study: Acme Corp reduced time-to-find from 4 minutes to 25 seconds. "
            "2 341 impressions, 187 reactions, 23 comments. "
            "Highest-performing content this quarter; strong CTOs and engineering VP engagement."
        ),
        tags=["case-study", "linkedin", "roi", "acme-corp", "enterprise"],
        url="https://linkedin.com/posts/searchpro-acme-case-study",
    ),
    dict(
        source_app="social", source_type="post", record_id="sm-p-003",
        name="ProductHunt Launch Day Post",
        title="ProductHunt: SearchPro – #2 Product of the Day",
        content=(
            "Launched on ProductHunt February 18 2026. Achieved #2 Product of the Day. "
            "512 upvotes, 87 comments. Featured in the ProductHunt newsletter with 250 k subscribers."
        ),
        tags=["producthunt", "launch", "upvotes", "newsletter"],
        url="https://producthunt.com/posts/searchpro",
    ),

    # ── Jobs ───────────────────────────────────────────────────────────────────
    dict(
        source_app="jobs", source_type="job", record_id="jb-j-001",
        name="Senior Backend Engineer",
        title="Senior Backend Engineer – Python / FastAPI (Remote)",
        content=(
            "Platform team hiring a senior backend engineer. Requirements: 5+ years Python, "
            "FastAPI or Django REST, PostgreSQL, Redis, Docker. "
            "Compensation: $150 k–$180 k + equity. Remote-first, US/EU timezones."
        ),
        tags=["python", "fastapi", "backend", "remote", "senior", "postgresql"],
        url="https://jobs.example.com/senior-backend-engineer",
    ),
    dict(
        source_app="jobs", source_type="job", record_id="jb-j-002",
        name="ML Engineer Search Relevance",
        title="Machine Learning Engineer – Search Relevance & Ranking",
        content=(
            "Join the search team to improve ranking and relevance. "
            "Required: PyTorch, transformer models, learning-to-rank, information retrieval. "
            "Nice-to-have: experience with tsvector, Elasticsearch, or Vespa."
        ),
        tags=["ml", "nlp", "search", "pytorch", "ranking", "relevance"],
        url="https://jobs.example.com/ml-engineer-search",
    ),

    # ── Cloud ──────────────────────────────────────────────────────────────────
    dict(
        source_app="cloud", source_type="source", record_id="cl-s-001",
        name="AWS Production Architecture",
        title="AWS Production Infrastructure – Architecture Overview",
        content=(
            "Production stack on AWS us-east-1: ECS Fargate (application), "
            "RDS PostgreSQL 15 Multi-AZ (primary DB), ElastiCache Redis 7 (caching), "
            "S3 + CloudFront (static assets & CDN). Monthly cost ~$8 500."
        ),
        tags=["aws", "infrastructure", "ecs", "rds", "postgresql", "production"],
        url="https://cloud.example.com/docs/infrastructure",
    ),
    dict(
        source_app="cloud", source_type="source", record_id="cl-s-002",
        name="Disaster Recovery Plan",
        title="Cloud Disaster Recovery & Business Continuity Plan",
        content=(
            "RTO: 4 hours. RPO: 1 hour. Strategy: daily automated RDS snapshots retained 30 days, "
            "Multi-AZ failover, cross-region S3 replication. Incident runbook reviewed quarterly."
        ),
        tags=["disaster-recovery", "rto", "rpo", "backup", "runbook", "aws"],
        url="https://cloud.example.com/docs/disaster-recovery",
    ),

    # ── Finance ────────────────────────────────────────────────────────────────
    dict(
        source_app="finance", source_type="transaction", record_id="fi-t-001",
        name="AWS February 2026 Invoice",
        title="AWS Cloud Services Invoice – February 2026",
        content=(
            "AWS invoice breakdown: EC2 $3 200, RDS $1 800, S3 $450, "
            "Data Transfer $620, ElastiCache $230, Other $200. Total: $6 500. "
            "Cost centre: Infrastructure. Approved by CFO on 2026-02-05."
        ),
        tags=["aws", "invoice", "cloud", "infrastructure", "february-2026"],
        url="https://finance.example.com/transactions/inv-2026-02-aws",
    ),
    dict(
        source_app="finance", source_type="transaction", record_id="fi-t-002",
        name="Acme Corp Q1 Payment",
        title="Acme Corp – Enterprise License Payment Q1 2026",
        content=(
            "Wire transfer received: $112 500 (Q1 instalment of $450 000 annual contract). "
            "Invoice INV-2026-001. Revenue recognised January 2026. "
            "Remaining balance: $337 500 due in Q2–Q4."
        ),
        tags=["payment", "enterprise", "acme-corp", "revenue", "wire-transfer"],
        url="https://finance.example.com/transactions/pay-2026-01-acme",
    ),
    dict(
        source_app="finance", source_type="transaction", record_id="fi-t-003",
        name="Stripe Payout February",
        title="Stripe Payout – February 2026 SaaS Subscriptions",
        content=(
            "Stripe payout of $186 400 covering SMB and mid-market monthly subscriptions. "
            "Net after Stripe fees (2.9 % + $0.30): $180 798. "
            "Deposited to operating account on 2026-02-15."
        ),
        tags=["stripe", "payout", "subscriptions", "smb", "mid-market"],
        url="https://finance.example.com/transactions/payout-2026-02-stripe",
    ),

    # ── Legal ──────────────────────────────────────────────────────────────────
    dict(
        source_app="legal", source_type="contract", record_id="lg-c-001",
        name="Acme Corp MSA 2026",
        title="Acme Corp – Master Service Agreement 2026",
        content=(
            "Three-year MSA with Acme Corp. Annual value: $450 000. Term: Jan 2026 – Dec 2028. "
            "Includes: 99.9 % uptime SLA, SOC 2 Type II compliance, GDPR data processing addendum. "
            "Signed by both parties 2026-01-10."
        ),
        tags=["msa", "enterprise", "acme-corp", "sla", "soc2", "signed"],
        url="https://legal.example.com/contracts/msa-acme-2026",
    ),
    dict(
        source_app="legal", source_type="contract", record_id="lg-c-002",
        name="AWS Enterprise Discount Program",
        title="AWS Enterprise Discount Program (EDP) Agreement",
        content=(
            "Three-year committed-spend agreement with AWS. Annual commitment: $100 000. "
            "Discount: 20 % off on-demand pricing across all services. "
            "Signed January 2026. Renewal date: January 2029."
        ),
        tags=["aws", "edp", "commitment", "discount", "cloud", "signed"],
        url="https://legal.example.com/contracts/aws-edp-2026",
    ),
    dict(
        source_app="legal", source_type="contract", record_id="lg-c-003",
        name="GlobalTech NDA",
        title="GlobalTech – Mutual Non-Disclosure Agreement",
        content=(
            "Mutual NDA with GlobalTech covering technical specifications and pricing "
            "during pilot evaluation. Effective 2026-01-20, expires 2027-01-20. "
            "Signed by General Counsel on both sides."
        ),
        tags=["nda", "globaltech", "pilot", "confidentiality"],
        url="https://legal.example.com/contracts/nda-globaltech-2026",
    ),

    # ── Research ───────────────────────────────────────────────────────────────
    dict(
        source_app="research", source_type="article", record_id="re-a-001",
        name="Vector Search vs Full-Text Search 2026",
        title="Vector Search vs PostgreSQL Full-Text Search – 2026 Benchmark",
        content=(
            "Benchmark on 10 M document corpus: FTS (tsvector) excels at exact boolean and "
            "keyword queries with sub-10 ms P99. Semantic vector search (pgvector) scores 40 % "
            "higher on subjective relevance for ambiguous queries but 3× slower. "
            "Recommendation: hybrid approach for production."
        ),
        tags=["vector-search", "fts", "postgresql", "pgvector", "benchmark", "research"],
        url="https://research.example.com/articles/vector-vs-fts-2026",
    ),
    dict(
        source_app="research", source_type="source", record_id="re-s-001",
        name="Competitor Analysis Q1 2026",
        title="Enterprise Search Platforms – Competitive Analysis Q1 2026",
        content=(
            "Reviewed five platforms: Elasticsearch, Algolia, Typesense, Meilisearch, and custom "
            "PostgreSQL FTS. Key differentiators: Algolia highest DX score, Elasticsearch most "
            "scalable, Typesense best OSS option, SearchPro unique on multi-source unified indexing."
        ),
        tags=["competitive-analysis", "elasticsearch", "algolia", "typesense", "market"],
        url="https://research.example.com/sources/competitive-analysis-q1-2026",
    ),

    # ── Productivity ───────────────────────────────────────────────────────────
    dict(
        source_app="productivity", source_type="task", record_id="pr-t-001",
        name="Q1 OKR Review Preparation",
        title="Task: Prepare and Present Q1 2026 OKR Review",
        content=(
            "Compile key results data for Q1 OKR review. Owner: Product team. "
            "Due: 2026-03-15. Status: In Progress. "
            "KRs to present: NPS +10 pts, feature adoption 70 %, enterprise churn < 2 %."
        ),
        tags=["okr", "Q1-2026", "planning", "product-team", "kpi"],
        url="https://productivity.example.com/tasks/q1-okr-review",
    ),
    dict(
        source_app="productivity", source_type="task", record_id="pr-t-002",
        name="SOC2 Type II Audit Prep",
        title="Task: Prepare Documentation for SOC2 Type II Audit",
        content=(
            "Gather and organise evidence for SOC 2 Type II audit scheduled April 2026. "
            "Required docs: access-control policies, incident-response procedures, "
            "vendor security assessments, penetration-test report (conducted 2025-11)."
        ),
        tags=["soc2", "audit", "security", "compliance", "documentation"],
        url="https://productivity.example.com/tasks/soc2-audit-prep",
    ),
    dict(
        source_app="productivity", source_type="task", record_id="pr-t-003",
        name="SearchPro Public API Docs",
        title="Task: Publish SearchPro Public API Documentation",
        content=(
            "Write and publish developer-facing API docs covering authentication, "
            "all /api/v1 endpoints, request/response schemas, code examples in Python, "
            "JavaScript, and cURL. Target: developer portal launch Q2 2026."
        ),
        tags=["documentation", "api", "developer-portal", "Q2-2026"],
        url="https://productivity.example.com/tasks/api-docs-publish",
    ),
]

SEED_SAVED_SEARCHES: list[dict] = [
    dict(
        name="All CRM Contacts",
        query="contact customer",
        filters={"app": ["crm"], "type": ["contact"]},
        user="admin",
    ),
    dict(
        name="Open Helpdesk Tickets",
        query="ticket issue error bug",
        filters={"app": ["helpdesk"], "type": ["ticket"]},
        user="support-team",
    ),
    dict(
        name="Finance Invoices & Payments",
        query="invoice payment transaction",
        filters={"app": ["finance"]},
        user="finance-team",
    ),
    dict(
        name="Active Legal Contracts",
        query="contract agreement signed",
        filters={"app": ["legal"], "type": ["contract"]},
        user="legal-team",
    ),
    dict(
        name="Open Engineering Tasks",
        query="task engineering development",
        filters={"app": ["productivity"], "type": ["task"]},
        user="engineering",
    ),
]


def run_seed(db: Session) -> None:
    if db.query(Index).count() > 0:
        logger.info("Seed data already present – skipping.")
        return

    logger.info("Inserting seed indexes …")
    for item in SEED_INDEXES:
        db.add(
            Index(
                **item,
                last_synced=_NOW,
                created_at=_NOW,
                updated_at=_NOW,
            )
        )

    logger.info("Inserting seed saved searches …")
    for item in SEED_SAVED_SEARCHES:
        db.add(SavedSearch(**item, created_at=_NOW))

    db.commit()
    logger.info("Seed data inserted successfully.")
