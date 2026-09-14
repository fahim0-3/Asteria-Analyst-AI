import pandas as pd

from app.agents.mock_planner import plan_question
from app.schemas.analysis import AnalysisPlan


def test_ambiguous_question_requests_clarification() -> None:
    assert isinstance(plan_question("Show performance", "x", pd.DataFrame({"revenue": [1]})), str)


def test_ranking_question_builds_typed_plan() -> None:
    frame = pd.DataFrame({"product_name": ["A"], "revenue": [10.0]})
    result = plan_question("Top 5 product name by revenue", "source", frame)
    assert isinstance(result, AnalysisPlan)
    assert result.limit == 5
    assert result.recommended_chart == "bar"


def test_count_uses_wildcard_only_with_registered_count() -> None:
    result = plan_question("How many customers?", "x", pd.DataFrame({"customer_id": [1]}))
    assert isinstance(result, AnalysisPlan)
    assert result.metrics[0].aggregation.value == "count"

