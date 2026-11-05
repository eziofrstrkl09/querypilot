from src.db import (
    get_connection,
    get_schema_text,
    get_allowed_tables,
    get_table_columns,
)

conn = get_connection()

try:
    schema = get_schema_text(conn)
    tables = get_allowed_tables(conn)
    column_schema = get_table_columns(conn)

    foreign_keys = [
        line for line in schema.splitlines()
        if " -> " in line
    ]

    column_count = sum(
        len(columns) for columns in column_schema.values()
    )

    print(f"Tables: {len(tables)}")
    print(f"Tables with column metadata: {len(column_schema)}")
    print(f"Columns: {column_count}")
    print(f"Foreign-key relationships: {len(foreign_keys)}")
    print(f"Schema length: {len(schema)} characters")

    assert len(tables) == 28
    assert len(column_schema) == 28
    assert column_count == 160
    assert len(foreign_keys) == 41

    print("\nSchema regression test passed.")

finally:
    conn.close()