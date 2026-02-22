from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import TSVECTOR

from .database import Base


class Index(Base):
    __tablename__ = "indexes"
    __table_args__ = (
        UniqueConstraint("source_app", "record_id", name="uq_indexes_source_record"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    source_app = Column(String(100), nullable=False, index=True)
    source_type = Column(String(100), nullable=False, index=True)
    record_id = Column(String(255), nullable=False)
    title = Column(String(1000), nullable=False)
    content = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    url = Column(String(2000), nullable=True)
    last_synced = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    # Populated automatically by the DB trigger on INSERT / UPDATE
    search_vector = Column(TSVECTOR, nullable=True)


class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    query = Column(String(1000), nullable=False)
    filters = Column(JSON, nullable=True)
    user = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SearchLog(Base):
    __tablename__ = "search_log"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(1000), nullable=False)
    filters = Column(JSON, nullable=True)
    results_count = Column(Integer, nullable=False, default=0)
    user = Column(String(255), nullable=True)
    searched_at = Column(DateTime(timezone=True), server_default=func.now())
