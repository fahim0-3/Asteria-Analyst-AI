import json
from typing import Any

import pandas as pd

from app.schemas.analysis import AnalysisPlan, Filter


class InvalidPlan(ValueError):
    pass


def validate_columns(plan: AnalysisPlan, frame: pd.DataFrame) -> None:
    available = set(map(str, frame.columns))
    requested = set(plan.dimensions)
    requested |= {metric.column for metric in plan.metrics if metric.column != "*"}
    requested |= {item.column for item in plan.filters}
    if requested - available:
        raise InvalidPlan(f"Unknown columns: {', '.join(sorted(requested - available))}")


def apply_filter(frame: pd.DataFrame, item: Filter) -> pd.DataFrame:
    """Apply one allowlisted comparator without dynamic expressions or generated closures."""
    column = frame[item.column]
    value = item.value
    if item.operator == "eq":
        mask = column == value
    elif item.operator == "ne":
        mask = column != value
    elif item.operator == "gt":
        mask = column > value
    elif item.operator == "gte":
        mask = column >= value
    elif item.operator == "lt":
        mask = column < value
    elif item.operator == "lte":
        mask = column <= value
    elif item.operator == "in":
        mask = column.isin(value if isinstance(value, list) else [value])
    else:
        mask = column.astype(str).str.contains(str(value), case=False, na=False)
    return frame[mask]


def execute_plan(frame: pd.DataFrame, plan: AnalysisPlan) -> pd.DataFrame:
    """Translate the typed DSL into registered pandas operations; no dynamic code runs."""
    validate_columns(plan, frame)
    working = frame.copy()
    for item in plan.filters:
        working = apply_filter(working, item)
    named = {}
    for metric in plan.metrics:
        if metric.column == "*":
            if metric.aggregation != "count":
                raise InvalidPlan("Wildcard is only valid for count")
            named[metric.name] = (working.columns[0], "size")
        else:
            named[metric.name] = (metric.column, metric.aggregation.value)
    if plan.dimensions:
        result = working.groupby(plan.dimensions, dropna=False).agg(**named).reset_index()
    else:
        values: dict[str, Any] = {}
        for metric in plan.metrics:
            values[metric.name] = (
                len(working)
                if metric.column == "*"
                else getattr(working[metric.column], metric.aggregation.value)()
            )
        result = pd.DataFrame([values])
    for sort in plan.sort:
        if sort.field in result.columns:
            result = result.sort_values(sort.field, ascending=sort.direction == "asc")
    return result.head(plan.limit)


def describe_plan(plan: AnalysisPlan) -> str:
    return json.dumps(plan.model_dump(mode="json"), indent=2)
