import csv
import io
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    AnalysisRun,
    Conversation,
    Dashboard,
    DataSource,
    DataSourceColumn,
    QueryAuditLog,
    SavedAnalysis,
    User,
)
from app.db.session import get_db
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.security.auth import admin_user, create_token, current_user, verify_password
from app.services.analysis import run_analysis
from app.services.data_sources import delete_source, ingest_upload, owned_source, read_frame

router = APIRouter(prefix="/api/v1")


class Login(BaseModel):
    email: str
    password: str


class ColumnPatch(BaseModel):
    user_override_type: str | None = Field(
        pattern="^(string|integer|float|boolean|date|datetime|category)?$"
    )


class SaveRequest(BaseModel):
    analysis_run_id: str
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    chart_config: dict[str, Any] = Field(default_factory=dict)


class DashboardRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = ""


def source_json(source: DataSource) -> dict[str, Any]:
    return {
        "id": source.id,
        "name": source.name,
        "source_type": source.source_type,
        "file_name": source.file_name,
        "status": source.status,
        "row_count": source.row_count,
        "column_count": source.column_count,
        "created_at": source.created_at,
    }


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "asteria-analyst-api"}


@router.get("/readiness")
def readiness(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(select(1))
    return {"status": "ready", "database": "connected"}


@router.post("/auth/login")
def login(payload: Login, db: Session = Depends(get_db)) -> dict[str, Any]:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    return {
        "access_token": create_token(user),
        "token_type": "bearer",
        "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role},
    }


@router.post("/auth/logout", status_code=204)
def logout(_: User = Depends(current_user)) -> None:
    return None


@router.get("/auth/me")
def me(user: User = Depends(current_user)) -> dict[str, Any]:
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}


@router.post("/data-sources/upload", status_code=201)
def upload(
    file: UploadFile = File(...),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return source_json(ingest_upload(db, user, file))


@router.get("/data-sources")
def sources(
    user: User = Depends(current_user), db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    statement = (
        select(DataSource)
        .where(DataSource.owner_id == user.id)
        .order_by(DataSource.created_at.desc())
    )
    return [source_json(item) for item in db.scalars(statement)]


@router.get("/data-sources/{source_id}")
def source_detail(
    source_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    source = owned_source(db, source_id, user)
    return {**source_json(source), "profile": source.profile}


@router.get("/data-sources/{source_id}/schema")
def schema(
    source_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    source = owned_source(db, source_id, user)
    return [
        {
            "id": column.id,
            "name": column.column_name,
            "inferred_type": column.inferred_type,
            "override_type": column.user_override_type,
            "nullable": column.nullable,
            "unique_count": column.unique_count,
            "missing_count": column.missing_count,
            "samples": column.sample_values,
        }
        for column in source.columns
    ]


@router.get("/data-sources/{source_id}/profile")
def profile(
    source_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    return owned_source(db, source_id, user).profile


@router.get("/data-sources/{source_id}/preview")
def preview(
    source_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    source = owned_source(db, source_id, user)
    frame = read_frame(Path(source.storage_path or "")).head(50).fillna("")
    return {"columns": list(frame.columns), "rows": frame.astype(str).to_dict(orient="records")}


@router.patch("/data-sources/{source_id}/columns/{column_id}")
def patch_column(
    source_id: str,
    column_id: str,
    payload: ColumnPatch,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    source = owned_source(db, source_id, user)
    column = db.scalar(
        select(DataSourceColumn).where(
            DataSourceColumn.id == column_id,
            DataSourceColumn.data_source_id == source.id,
        )
    )
    if not column:
        raise HTTPException(404, "Column not found")
    column.user_override_type = payload.user_override_type
    db.commit()
    return {"id": column.id, "user_override_type": column.user_override_type}


@router.delete("/data-sources/{source_id}", status_code=204)
def remove_source(
    source_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> None:
    delete_source(db, owned_source(db, source_id, user))


@router.post("/analysis/run", response_model=AnalysisResponse)
def analyse(
    payload: AnalysisRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> AnalysisResponse:
    return run_analysis(db, user, owned_source(db, payload.data_source_id, user), payload)


@router.post("/saved-analyses", status_code=201)
def save_analysis(
    payload: SaveRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    run = db.get(AnalysisRun, payload.analysis_run_id)
    conversation = db.get(Conversation, run.conversation_id) if run else None
    if not run or not conversation or conversation.user_id != user.id:
        raise HTTPException(404, "Analysis not found")
    item = SavedAnalysis(user_id=user.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "title": item.title}


@router.get("/saved-analyses")
def saved(
    user: User = Depends(current_user), db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    return [
        {
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "analysis_run_id": item.analysis_run_id,
            "chart_config": item.chart_config,
        }
        for item in db.scalars(select(SavedAnalysis).where(SavedAnalysis.user_id == user.id))
    ]


@router.post("/dashboards", status_code=201)
def create_dashboard(
    payload: DashboardRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    item = Dashboard(user_id=user.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "name": item.name, "description": item.description}


@router.get("/dashboards")
def dashboards(
    user: User = Depends(current_user), db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    return [
        {"id": item.id, "name": item.name, "description": item.description}
        for item in db.scalars(select(Dashboard).where(Dashboard.user_id == user.id))
    ]


@router.get("/analyses/{analysis_id}/export.csv")
def export_csv(
    analysis_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    run = db.get(AnalysisRun, analysis_id)
    conversation = db.get(Conversation, run.conversation_id) if run else None
    if not run or not conversation or conversation.user_id != user.id:
        raise HTTPException(404, "Analysis not found")
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(run.result_schema.get("columns", [])))
    writer.writeheader()
    writer.writerows(run.result_rows)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=analysis-{run.id}.csv"},
    )


@router.get("/admin/metrics")
def metrics(_: User = Depends(admin_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    queries = db.scalar(select(func.count()).select_from(QueryAuditLog)) or 0
    failed = (
        db.scalar(
            select(func.count())
            .select_from(QueryAuditLog)
            .where(QueryAuditLog.execution_status != "succeeded")
        )
        or 0
    )
    average = db.scalar(select(func.avg(QueryAuditLog.execution_time_ms))) or 0
    source_count = db.scalar(select(func.count()).select_from(DataSource)) or 0
    return {
        "query_count": queries,
        "failed_query_count": failed,
        "average_execution_time_ms": round(average, 1),
        "data_source_count": source_count,
    }

