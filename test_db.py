from src.db import get_connection, run_query

conn = get_connection()

try:
    columns, rows, error = run_query(
        conn,
        "DELETE FROM customers"
    )

    assert error is not None
    assert "read-only" in error.lower()

    print("Read-only regression test passed.")

    print(run_query(conn, "SELECT pg_sleep(15)")[2])

finally:
    conn.close()