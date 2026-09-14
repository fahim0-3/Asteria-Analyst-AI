import pandas as pd

from app.analytics.profiling import profile_frame


def test_profile_reports_quality_and_statistics() -> None:
    frame = pd.DataFrame({"id": [1, 2, 2], "value": [10.0, None, 1000.0], "constant": ["x", "x", "x"]})
    profile = profile_frame(frame)
    assert profile["row_count"] == 3
    assert profile["duplicate_row_count"] == 0
    assert any("constant" in warning for warning in profile["warnings"])
    value = next(item for item in profile["columns"] if item["name"] == "value")
    assert value["missing_count"] == 1
    assert "numeric_summary" in value


def test_duplicate_rows_are_counted() -> None:
    assert profile_frame(pd.DataFrame({"x": [1, 1]}))["duplicate_row_count"] == 1

