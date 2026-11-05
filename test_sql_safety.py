
from src.db import get_connection, get_allowed_tables, get_table_columns
from src.sql_safety import validate_sql


MUST_ACCEPT = [
    "SELECT COUNT(*) FROM customers",

    """
    SELECT c.customer_id, c.first_name
    FROM customers c
    """,

    """
    SELECT customer_id, COUNT(*) AS order_count
    FROM orders
    GROUP BY customer_id
    ORDER BY order_count DESC
    """,

    """
    WITH customer_data AS (
        SELECT customer_id FROM customers
    )
    SELECT customer_id FROM customer_data
    """,

    """
    SELECT DATE_TRUNC('month', ordered_at), COUNT(*)
    FROM orders
    GROUP BY DATE_TRUNC('month', ordered_at)
    """,

    """
    SELECT c.customer_id, o.order_id
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    """,

    """
    WITH customer_orders AS (
        SELECT customer_id FROM orders
    ),
    customer_list AS (
        SELECT customer_id FROM customer_orders
    )
    SELECT customer_id FROM customer_list
    """,

    """
    SELECT customer_id FROM customers
    UNION
    SELECT customer_id FROM orders
    """,
]


MUST_REJECT = [
    "DELETE FROM customers",

    "SELECT * FROM customers; SELECT * FROM orders",

    "SELECT * INTO new_table FROM customers",

    "SELECT * FROM information_schema.tables",

    "SELECT * FROM pg_user",

    "SELECT set_config('statement_timeout', '0', false)",

    "SELECT pg_read_file('/etc/hostname')",

    "SELECT pg_sleep(100)",

    "SELECT current_setting('data_directory')",

    "SELECT 'unterminated",

    "SELECT nonexistent_column FROM customers",

    "SELECT c.nonexistent_column FROM customers c",

    """
    SELECT customer_id
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    """,
]


def main():
    conn = get_connection()

    try:
        allowed_tables = get_allowed_tables(conn)
        column_schema = get_table_columns(conn)

        print(f"Allowed tables: {len(allowed_tables)}")
        print(f"Tables with column metadata: {len(column_schema)}")

        accepted_count = 0
        rejected_count = 0

        print("\nTesting queries that must be accepted...")

        for sql in MUST_ACCEPT:
            safe_sql, error = validate_sql(
                sql,
                allowed_tables,
                column_schema,
            )

            if error:
                print(f"\nUNEXPECTED REJECTION:\n{sql}\nReason: {error}")
            else:
                accepted_count += 1

        print("\nTesting queries that must be rejected...")

        for sql in MUST_REJECT:
            safe_sql, error = validate_sql(
                sql,
                allowed_tables,
                column_schema,
            )

            if error:
                rejected_count += 1
            else:
                print(f"\nUNEXPECTED ACCEPTANCE:\n{sql}")

        print("\n" + "=" * 50)
        print(f"Accepted correctly: {accepted_count}/{len(MUST_ACCEPT)}")
        print(f"Rejected correctly: {rejected_count}/{len(MUST_REJECT)}")

        if (
            accepted_count == len(MUST_ACCEPT)
            and rejected_count == len(MUST_REJECT)
        ):
            print("\nAll SQL safety tests passed.")
        else:
            print("\nSome SQL safety tests failed.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
