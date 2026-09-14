import re
from dataclasses import dataclass

from app.core.config import get_settings

try:
    from sqlglot import exp, parse
except ImportError:  # pragma: no cover - conservative fallback is tested locally
    exp = None
    parse = None


class UnsafeQuery(ValueError):
    pass


@dataclass
class ValidatedSQL:
    sql: str
    tables: set[str]


BLOCKED = re.compile(r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|attach|detach|pragma|copy|call|execute)\b", re.I)
TABLE_TOKEN = re.compile(r"\b(?:from|join)\s+([A-Za-z_][\w.]*)", re.I)
CTE_TOKEN = re.compile(r"(?:\bwith|,)\s*([A-Za-z_][\w]*)\s+as\s*\(", re.I)


def _fallback_validate(clean: str, approved_tables: set[str]) -> ValidatedSQL:
    """Conservative dependency-free validation for simple SELECT/CTE queries."""
    if not re.match(r"^(select|with)\b", clean, re.I):
        raise UnsafeQuery("Only SELECT queries are allowed")
    # Quotes and parentheses are allowed, but attempts that defeat simple tokenisation are denied.
    if re.search(r"\b(union|intersect|except)\b", clean, re.I):
        raise UnsafeQuery("Set operations require the SQLGlot validator")
    ctes = {match.group(1) for match in CTE_TOKEN.finditer(clean)}
    referenced = {match.group(1).split(".")[-1] for match in TABLE_TOKEN.finditer(clean)}
    physical = referenced - ctes
    unknown = physical - approved_tables
    if unknown:
        raise UnsafeQuery(f"Unapproved tables: {', '.join(sorted(unknown))}")
    joins = len(re.findall(r"\bjoin\b", clean, re.I))
    if joins > get_settings().max_query_joins:
        raise UnsafeQuery("Query exceeds the maximum join count")
    bounded = clean.rstrip(";")
    if not re.search(r"\blimit\s+\d+\s*$", bounded, re.I):
        bounded += f" LIMIT {get_settings().default_query_rows}"
    else:
        match = re.search(r"\blimit\s+(\d+)\s*$", bounded, re.I)
        if match and int(match.group(1)) > get_settings().max_query_rows:
            bounded = bounded[:match.start()] + f"LIMIT {get_settings().max_query_rows}"
    return ValidatedSQL(bounded, physical)


def validate_sql(sql: str, approved_tables: set[str]) -> ValidatedSQL:
    """Accept exactly one bounded read-only query over allowlisted tables."""
    clean = sql.strip()
    semicolons = clean.count(";")
    if not clean or BLOCKED.search(clean) or "--" in clean or "/*" in clean or semicolons > (1 if clean.endswith(";") else 0):
        raise UnsafeQuery("Query contains a blocked operation, comment, or multiple statements")
    if parse is None:
        return _fallback_validate(clean, approved_tables)
    trees = parse(clean)
    if len(trees) != 1 or not isinstance(trees[0], exp.Query):
        raise UnsafeQuery("Exactly one read-only query is required")
    tree = trees[0]
    tables = {node.name for node in tree.find_all(exp.Table)}
    cte_names = {node.alias for node in tree.find_all(exp.CTE)}
    physical = tables - cte_names
    if physical - approved_tables:
        raise UnsafeQuery(f"Unapproved tables: {', '.join(sorted(physical - approved_tables))}")
    if sum(1 for _ in tree.find_all(exp.Join)) > get_settings().max_query_joins:
        raise UnsafeQuery("Query exceeds the maximum join count")
    limit = tree.args.get("limit")
    if limit is None:
        tree = tree.limit(get_settings().default_query_rows)
    return ValidatedSQL(tree.sql(), physical)
