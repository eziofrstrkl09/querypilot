from src.db import get_connection, get_schema_text

conn = get_connection()

try:
    schema = get_schema_text(conn)
    print(schema)
finally:
    conn.close()