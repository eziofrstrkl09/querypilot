
from src.db import get_connection, get_allowed_tables
from src.sql_safety import validate_sql


conn = get_connection()

try:
    ALLOWED_TABLES = get_allowed_tables(conn)

    print(f"Loaded {len(ALLOWED_TABLES)} allowed tables.\n")

    must_accept = [

        # Basic SELECT
        "SELECT COUNT(*) FROM customers",

        # Reference top-customer query
        """
        SELECT
            c.customer_id,
            SUM(oi.quantity * oi.unit_price - oi.discount_amount)
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.status NOT IN ('cancelled', 'pending')
        GROUP BY c.customer_id
        ORDER BY SUM(oi.quantity * oi.unit_price - oi.discount_amount) DESC
        LIMIT 10
        """,

        # Valid date_trunc query
        """
        SELECT
            DATE_TRUNC('month', ordered_at),
            COUNT(*)
        FROM orders
        GROUP BY DATE_TRUNC('month', ordered_at)
        """,

        # Normal CTE
        """
        WITH customer_orders AS (
            SELECT customer_id FROM orders
        )
        SELECT * FROM customer_orders
        """,

        # Chained CTEs
        """
        WITH first_cte AS (
            SELECT customer_id FROM customers
        ),
        second_cte AS (
            SELECT customer_id FROM first_cte
        )
        SELECT * FROM second_cte
        """,

        # CTE inside a subquery
        """
        SELECT *
        FROM (
            WITH c AS (
                SELECT customer_id FROM customers
            )
            SELECT * FROM c
        ) AS sub
        """,

        # Self-join
        """
        SELECT a.customer_id
        FROM customers a
        JOIN customers b
            ON a.customer_id = b.customer_id
        """,

        # UNION of CTEs
        """
        WITH a AS (
            SELECT customer_id FROM customers
        ),
        b AS (
            SELECT customer_id FROM customers
        )
        SELECT customer_id FROM a
        UNION
        SELECT customer_id FROM b
        """,
    ]

    must_reject = [

        # Write operation
        "DELETE FROM customers",

        # Multiple statements
        "SELECT * FROM customers; DROP TABLE orders;",

        # SELECT INTO
        "SELECT * INTO backup FROM customers",

        # Non-public schema
        "SELECT * FROM information_schema.tables",

        # CTE self-reference to a physical system table
        """
        WITH pg_user AS (
            SELECT * FROM pg_user
        )
        SELECT * FROM pg_user
        """,

        # Later sibling CTE must not excuse physical pg_user
        """
        WITH z AS (
            SELECT * FROM pg_user
        ),
        pg_user AS (
            SELECT 1
        )
        SELECT * FROM z
        """,

        # Nested CTE must not excuse outer physical table
        """
        SELECT *
        FROM (
            WITH pg_user AS (SELECT 1)
            SELECT 1
        ) s, pg_user
        """,

        # Nested CTE name must not leak into another scope
        """
        SELECT *
        FROM (
            WITH secret_table AS (SELECT 1)
            SELECT 1
        ) s
        JOIN pg_user ON TRUE
        """,

        # Timeout manipulation
        "SELECT set_config('statement_timeout', '0', false)",

        # Server file access
        "SELECT pg_read_file('/etc/hostname')",

        # Expensive function
        "SELECT pg_sleep(100)",

        # Configuration disclosure
        "SELECT current_setting('data_directory')",

        # Invalid SQL
        "SELECT 'abc",
    ]

    def run_tests(test_cases, expected_error):
        for sql in test_cases:
            safe_sql, error = validate_sql(sql, ALLOWED_TABLES)

            if expected_error:
                passed = error is not None
                status = "PASS (rejected)" if passed else "FAIL (accepted)"
                detail = error if error else safe_sql
            else:
                passed = error is None
                status = "PASS (accepted)" if passed else "FAIL (rejected)"
                detail = safe_sql if safe_sql else error

            print(f"{status}: {detail}\n")

            assert passed, f"Unexpected result for SQL:\n{sql}"

    run_tests(must_accept, expected_error=False)
    run_tests(must_reject, expected_error=True)

    print("All SQL safety tests passed.")

finally:
    conn.close()
