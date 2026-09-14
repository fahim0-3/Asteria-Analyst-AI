import pandas as pd
import pytest
from pydantic import ValidationError

from app.analytics.dataframe_dsl import InvalidPlan, execute_plan
from app.schemas.analysis import AnalysisPlan, Filter


def plan(**changes: object) -> AnalysisPlan:
    data = {"question": "Revenue by region", "data_source_id": "x", "analysis_type": "ranking", "dimensions": ["region"], "metrics": [{"name": "revenue", "column": "amount", "aggregation": "sum"}], "sort": [{"field": "revenue", "direction": "desc"}], "limit": 2, "recommended_chart": "bar"}
    data.update(changes)
    return AnalysisPlan.model_validate(data)


def test_group_aggregate_sort_limit() -> None:
    frame = pd.DataFrame({"region": ["N", "S", "N", "W"], "amount": [10, 30, 15, 2]})
    result = execute_plan(frame, plan())
    assert result.to_dict("records") == [{"region": "S", "revenue": 30}, {"region": "N", "revenue": 25}]


def test_filter_is_registered_not_evaluated() -> None:
    frame = pd.DataFrame({"region": ["North", "South"], "amount": [10, 20]})
    result = execute_plan(frame, plan(filters=[{"column": "region", "operator": "eq", "value": "North"}]))
    assert result.iloc[0].revenue == 10


def test_unknown_column_is_rejected() -> None:
    with pytest.raises(InvalidPlan, match="Unknown"):
        execute_plan(pd.DataFrame({"amount": [1]}), plan())


def test_arbitrary_operator_fails_schema_validation() -> None:
    with pytest.raises(ValidationError):
        Filter(column="x", operator="exec", value="import os")  # type: ignore[arg-type]


def test_plan_limit_is_bounded() -> None:
    with pytest.raises(ValidationError):
        plan(limit=5001)

