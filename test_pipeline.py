from src.db import get_connection, get_schema_text
from src.llm import generate_sql

question = "Show the top 10 customers by total spending"

conn = get_connection()

try:
    schema = get_schema_text(conn)

    sql = generate_sql(question, schema)

    print(f"\nQuestion: {question}")
    print(f"\nGenerated SQL:\n{sql}")

finally:
    conn.close()