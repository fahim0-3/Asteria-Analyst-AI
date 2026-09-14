import time
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.agents.mock_planner import plan_question
from app.analytics.dataframe_dsl import describe_plan, execute_plan
from app.analytics.profiling import json_value
from app.db.models import AnalysisRun, Conversation, DataSource, QueryAuditLog, User
from app.schemas.analysis import AnalysisRequest, AnalysisResponse, ChartConfig, Quality
from app.services.data_sources import read_frame


def serialise_frame(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [{str(k): json_value(v) for k, v in row.items()} for row in frame.to_dict(orient="records")]


def answer_text(rows: list[dict[str, Any]], metric: str) -> str:
    if not rows:
        return "No records matched the requested analysis."
    first = rows[0]
    if len(first) == 1:
        return f"The requested {metric.replace('_', ' ')} is {first[metric]:,.2f}." if isinstance(first[metric], (int, float)) else f"The result is {first[metric]}."
    dimension = next(key for key in first if key != metric)
    value = first[metric]
    shown = f"{value:,.2f}" if isinstance(value, (int, float)) else str(value)
    return f"{first[dimension]} is the leading result, with {metric.replace('_', ' ')} of {shown}."


def run_analysis(db: Session, user: User, source: DataSource, request: AnalysisRequest) -> AnalysisResponse:
    started = time.perf_counter()
    frame = read_frame(Path(source.storage_path or ""))
    conversation = db.get(Conversation, request.conversation_id) if request.conversation_id else None
    if conversation and conversation.user_id != user.id:
        conversation = None
    if conversation is None:
        conversation = Conversation(user_id=user.id, data_source_id=source.id, title=request.question[:80])
        db.add(conversation)
        db.flush()
    planned = plan_question(request.question, source.id, frame)
    if isinstance(planned, str):
        db.commit()
        return AnalysisResponse(
            response_type="clarification_required", answer=planned, conversation_id=conversation.id,
            data_source_id=source.id, assumptions=[], warnings=["No query was executed."],
        )
    try:
        result = execute_plan(frame, planned)
        rows = serialise_frame(result)
        elapsed = round((time.perf_counter() - started) * 1000)
        metric = planned.metrics[0].name
        run = AnalysisRun(
            conversation_id=conversation.id, user_question=request.question,
            analysis_plan=planned.model_dump(mode="json"), query_type="dataframe_dsl",
            generated_query=describe_plan(planned), result_schema={"columns": list(result.columns)},
            result_rows=rows, row_count=len(rows), status="succeeded", execution_time_ms=elapsed,
        )
        db.add(run)
        db.flush()
        db.add(QueryAuditLog(
            user_id=user.id, data_source_id=source.id, query_type="dataframe_dsl",
            query_text=describe_plan(planned), validation_status="passed", execution_status="succeeded",
            row_count=len(rows), execution_time_ms=elapsed,
        ))
        conversation.context = {"last_plan": planned.model_dump(mode="json"), "last_analysis_id": run.id}
        db.commit()
        missing = bool(source.profile.get("warnings"))
        return AnalysisResponse(
            response_type="empty_result" if not rows else "analysis_result",
            answer=answer_text(rows, metric), analysis_id=run.id, conversation_id=conversation.id,
            data_source_id=source.id, query=describe_plan(planned), columns=list(result.columns), rows=rows,
            chart=ChartConfig(
                type=planned.recommended_chart,
                x=planned.dimensions[0] if planned.dimensions else None, y=metric,
                title=request.question.rstrip("?"),
            ), plan=planned,
            assumptions=["Null values are ignored by aggregations.", "Results describe the uploaded dataset only."],
            warnings=list(source.profile.get("warnings", []))[:3],
            quality=Quality(row_count=len(rows), missing_data_warning=missing, confidence="medium" if missing else "high"),
            follow_up_suggestions=["Break this down by another category", "Show a time trend", "Export this result"],
            execution_time_ms=elapsed,
        )
    except Exception as exc:
        elapsed = round((time.perf_counter() - started) * 1000)
        db.add(QueryAuditLog(
            user_id=user.id, data_source_id=source.id, query_type="dataframe_dsl",
            query_text=planned.model_dump_json(), validation_status="failed", execution_status="blocked",
            execution_time_ms=elapsed,
        ))
        db.commit()
        return AnalysisResponse(
            response_type="query_error", answer="The requested plan could not be executed safely.",
            conversation_id=conversation.id, data_source_id=source.id,
            query=planned.model_dump_json(indent=2), plan=planned, warnings=[str(exc)], execution_time_ms=elapsed,
        )

