import pytest

from app.analytics.sql_safety import UnsafeQuery, validate_sql


def test_select_gets_limit() -> None:
    result = validate_sql("SELECT region, SUM(total_amount) FROM orders GROUP BY region", {"orders"})
    assert "LIMIT" in result.sql.upper()
    assert result.tables == {"orders"}


@pytest.mark.parametrize("query", [
    "DROP TABLE orders", "DELETE FROM orders", "UPDATE orders SET x=1",
    "SELECT * FROM orders; DELETE FROM orders", "SELECT * FROM orders -- bypass",
    "PRAGMA table_info(orders)", "ATTACH DATABASE 'x' AS x",
])
def test_dangerous_sql_is_blocked(query: str) -> None:
    with pytest.raises(UnsafeQuery):
        validate_sql(query, {"orders"})


def test_unapproved_table_is_blocked() -> None:
    with pytest.raises(UnsafeQuery, match="Unapproved"):
        validate_sql("SELECT * FROM private_payroll", {"orders"})


def test_too_many_joins_is_blocked() -> None:
    query = "SELECT * FROM a JOIN b ON 1=1 JOIN c ON 1=1 JOIN d ON 1=1 JOIN e ON 1=1 JOIN f ON 1=1 JOIN g ON 1=1"
    with pytest.raises(UnsafeQuery, match="join"):
        validate_sql(query, {"a", "b", "c", "d", "e", "f", "g"})

