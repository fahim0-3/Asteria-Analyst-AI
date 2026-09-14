import re

import pandas as pd

from app.schemas.analysis import Aggregation, AnalysisPlan, Metric, Sort

AMBIGUOUS = {"show performance", "how are we doing", "tell me about the data"}


def plan_question(question: str, source_id: str, frame: pd.DataFrame) -> AnalysisPlan | str:
    """Deterministic planner used for demos/tests; validates into the same contract as an LLM."""
    q = question.lower().strip(" ?.!")
    if q in AMBIGUOUS:
        return "Which metric, dimension, and time period should I use to define performance?"
    columns = list(map(str, frame.columns))
    numeric = [c for c in columns if pd.api.types.is_numeric_dtype(frame[c])]
    dates = [c for c in columns if "date" in c.lower()]
    categorical = [c for c in columns if c not in numeric and c not in dates]
    mentioned = [c for c in columns if c.lower().replace("_", " ") in q or c.lower() in q]
    metric_col = next((c for c in numeric if c in mentioned), None)
    for candidate in ["revenue", "total_amount", "sales", "quantity", "rating", "discount_amount"]:
        if candidate in columns and (candidate.replace("_", " ") in q or candidate in {"revenue", "total_amount"} and "revenue" in q):
            metric_col = candidate
            break
    if any(word in q for word in ["how many", "count", "number of"]):
        metric = Metric(name="count", column="*", aggregation=Aggregation.count)
    else:
        metric_col = metric_col or (numeric[0] if numeric else None)
        if metric_col is None:
            metric = Metric(name="count", column="*", aggregation=Aggregation.count)
        else:
            aggregation = Aggregation.mean if any(w in q for w in ["average", "mean"]) else Aggregation.sum
            metric = Metric(name=f"{aggregation.value}_{metric_col}", column=metric_col, aggregation=aggregation)
    dimension = next((c for c in mentioned if c != metric_col), None)
    if not dimension:
        dimension = next((c for c in categorical if re.search(rf"\b(by|per|across)\s+{re.escape(c.replace('_', ' '))}\b", q)), None)
    if ("monthly" in q or "trend" in q or "over time" in q) and dates:
        dimension = dates[0]
    ranking = any(word in q for word in ["top", "bottom", "highest", "lowest", "best", "worst"])
    chart = "line" if dimension in dates else "bar" if dimension else "kpi"
    sort = [Sort(field=metric.name, direction="asc" if any(w in q for w in ["bottom", "lowest", "worst"]) else "desc")] if dimension else []
    limit_match = re.search(r"\b(\d{1,3})\b", q)
    return AnalysisPlan(
        question=question, data_source_id=source_id,
        analysis_type="trend" if dimension in dates else "ranking" if ranking else "aggregation",
        dimensions=[dimension] if dimension else [], metrics=[metric], sort=sort,
        limit=int(limit_match.group(1)) if limit_match else (10 if ranking else 100), recommended_chart=chart,
    )

