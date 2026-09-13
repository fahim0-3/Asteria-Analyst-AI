import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def now() -> datetime:
    return datetime.now(UTC)


class Role(str, enum.Enum):
    analyst = "analyst"
    admin = "admin"


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.analyst)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class DataSource(Base):
    __tablename__ = "data_sources"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    source_type: Mapped[str] = mapped_column(String(30), default="file")
    file_name: Mapped[str | None] = mapped_column(String(255))
    file_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    storage_path: Mapped[str | None] = mapped_column(String(500))
    connection_type: Mapped[str | None] = mapped_column(String(30))
    encrypted_secret: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="ready")
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    column_count: Mapped[int] = mapped_column(Integer, default=0)
    profile: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    error_message: Mapped[str | None] = mapped_column(Text)
    columns: Mapped[list["DataSourceColumn"]] = relationship(cascade="all, delete-orphan")


class DataSourceColumn(Base):
    __tablename__ = "data_source_columns"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data_source_id: Mapped[str] = mapped_column(ForeignKey("data_sources.id", ondelete="CASCADE"))
    column_name: Mapped[str] = mapped_column(String(255))
    inferred_type: Mapped[str] = mapped_column(String(50))
    user_override_type: Mapped[str | None] = mapped_column(String(50))
    nullable: Mapped[bool] = mapped_column(Boolean)
    unique_count: Mapped[int] = mapped_column(Integer)
    missing_count: Mapped[int] = mapped_column(Integer)
    sample_values: Mapped[list[Any]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Conversation(Base):
    __tablename__ = "analysis_conversations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(200))
    data_source_id: Mapped[str] = mapped_column(ForeignKey("data_sources.id"))
    context: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(ForeignKey("analysis_conversations.id"))
    user_question: Mapped[str] = mapped_column(Text)
    analysis_plan: Mapped[dict[str, Any]] = mapped_column(JSON)
    query_type: Mapped[str] = mapped_column(String(30))
    generated_query: Mapped[str] = mapped_column(Text)
    result_schema: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    result_rows: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30))
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class SavedAnalysis(Base):
    __tablename__ = "saved_analyses"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    chart_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Dashboard(Base):
    __tablename__ = "dashboards"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class DashboardItem(Base):
    __tablename__ = "dashboard_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dashboard_id: Mapped[str] = mapped_column(ForeignKey("dashboards.id", ondelete="CASCADE"))
    saved_analysis_id: Mapped[str] = mapped_column(ForeignKey("saved_analyses.id"))
    item_type: Mapped[str] = mapped_column(String(30), default="chart")
    position: Mapped[int] = mapped_column(Integer, default=0)
    display_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class QueryAuditLog(Base):
    __tablename__ = "query_audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    data_source_id: Mapped[str] = mapped_column(ForeignKey("data_sources.id"))
    query_type: Mapped[str] = mapped_column(String(30))
    query_text: Mapped[str] = mapped_column(Text)
    validation_status: Mapped[str] = mapped_column(String(30))
    execution_status: Mapped[str] = mapped_column(String(30))
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

