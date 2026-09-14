from typing import Any

import pandas as pd


def json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def profile_frame(frame: pd.DataFrame) -> dict[str, Any]:
    """Build bounded, JSON-safe profiling metadata without trusting inferred types."""
    rows = len(frame)
    columns = []
    warnings = []
    for name in frame.columns:
        series = frame[name]
        missing = int(series.isna().sum())
        unique = int(series.nunique(dropna=True))
        item: dict[str, Any] = {
            "name": str(name), "inferred_type": str(series.dtype), "missing_count": missing,
            "missing_percentage": round(missing / max(rows, 1) * 100, 2), "unique_count": unique,
            "sample_values": [json_value(v) for v in series.dropna().head(5).tolist()],
            "potential_id": unique == rows and rows > 0, "constant": unique <= 1,
            "high_cardinality": rows > 20 and unique / rows > 0.8,
        }
        if pd.api.types.is_numeric_dtype(series):
            desc = series.describe()
            item["numeric_summary"] = {key: json_value(value) for key, value in desc.items()}
            q1, q3 = series.quantile([0.25, 0.75])
            iqr = q3 - q1
            item["outlier_count_iqr"] = int(((series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)).sum())
        elif unique <= 30:
            item["top_values"] = {str(k): int(v) for k, v in series.value_counts(dropna=False).head(10).items()}
        columns.append(item)
        if missing / max(rows, 1) > 0.2:
            warnings.append(f"{name} is {missing / max(rows, 1):.0%} missing")
        if unique <= 1:
            warnings.append(f"{name} is constant")
    numeric = frame.select_dtypes(include="number")
    correlations = numeric.corr().round(3).fillna(0).to_dict() if 1 < len(numeric.columns) <= 20 else {}
    return {
        "row_count": rows, "column_count": len(frame.columns),
        "duplicate_row_count": int(frame.duplicated().sum()), "columns": columns,
        "correlations": correlations, "warnings": warnings,
        "inference_notice": "Inferred types are suggestions and can be overridden by the user.",
    }

