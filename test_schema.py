from src.db import get_connection, get_schema_text

conn = get_connection()

try:
    schema = get_schema_text(conn)

    foreign_keys = [
        line for line in schema.splitlines()
        if " -> " in line
    ]

    print(f"Tables: {schema.count('Table: ')}")
    print(f"Foreign-key relationships: {len(foreign_keys)}")

    for relationship in foreign_keys:
        print(relationship)

    assert len(foreign_keys) == 41, (
        f"Expected 41 foreign keys, found {len(foreign_keys)}"
    )

    print("\nSchema regression test passed.")

finally:
    conn.close()