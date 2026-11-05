from src.db import get_connection, run_query

sql = """
SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    SUM(oi.quantity * oi.unit_price - oi.discount_amount)
        AS total_spending
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status NOT IN ('cancelled', 'pending')
GROUP BY c.customer_id, c.first_name, c.last_name
ORDER BY total_spending DESC
LIMIT 10;
"""

conn = get_connection()

try:
    columns, rows, error = run_query(conn, sql)

    if error:
        print("Error:", error)
    else:
        print(columns)
        for row in rows:
            print(row)

finally:
    conn.close()
