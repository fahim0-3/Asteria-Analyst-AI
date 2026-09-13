from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class Aggregation(str, Enum):
    sum = "sum"
    mean = "mean"
    median = "median"
    min = "min"
    max = "max"
    count = "count"
    nunique = "nunique"


class Metric(BaseModel):
    name: str
    column: str = "*"
    aggregation: Aggregation


class Filter(BaseModel):
    column: str
    operator: Literal["eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"]
    value: Any


class Sort(BaseModel):
    field: str
    direction: Literal["asc", "desc"] = "desc"


class AnalysisPlan(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    data_source_id: str
    analysis_type: Literal["aggregation", "ranking", "trend", "distribution", "quality"]
    dimensions: list[str] = Field(default_factory=list, max_length=4)
    metrics: list[Metric] = Field(min_length=1, max_length=8)
    filters: list[Filter] = Field(default_factory=list, max_length=10)
    sort: list[Sort] = Field(default_factory=list, max_length=3)
    limit: int = Field(default=100, ge=1, le=5000)
    recommended_chart: Literal["bar", "line", "area", "scatter", "histogram", "box", "table", "kpi"]

    @model_validator(mode="after")
    def chart_semantics(self) -> "AnalysisPlan":
        if self.recommended_chart in {"line", "area"} and not self.dimensions:
            raise ValueError("time-series charts require a dimension")
        return self


class AnalysisRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    data_source_id: str
    conversation_id: str | None = None


class Quality(BaseModel):
    row_count: int
    missing_data_warning: bool
    confidence: Literal["low", "medium", "high"]


class ChartConfig(BaseModel):
    type: str
    x: str | None = None
    y: str | None = None
    title: str


class AnalysisResponse(BaseModel):
    response_type: Literal[
        "analysis_result", "clarification_required", "data_quality_warning",
        "unsupported_question", "query_error", "empty_result", "export_ready"
    ]
    answer: str
    analysis_id: str | None = None
    conversation_id: str
    data_source_id: str
    query_type: str = "dataframe_dsl"
    query: str = ""
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    chart: ChartConfig | None = None
    plan: AnalysisPlan | None = None
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    quality: Quality | None = None
    follow_up_suggestions: list[str] = Field(default_factory=list)
    execution_time_ms: int = 0

