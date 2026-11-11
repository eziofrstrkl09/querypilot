from src.db import (
    get_connection,
    get_schema_text,
    get_allowed_tables,
    get_table_columns,
    run_query,
)
from src.llm import generate_sql
from src.sql_safety import validate_sql
from src.ambiguity import detect


QUESTIONS = [
    "How many customers do we have?",
    "How many orders were delivered?",
    "What are the names of all product categories?",
    "How many orders did each store handle?",
    "What was our total revenue?",
    "Who are our best customers?",
]


def main():
    conn = get_connection()

    try:
        schema = get_schema_text(conn)
        allowed_tables = get_allowed_tables(conn)
        column_schema = get_table_columns(conn)

        print(f"Schema retrieved: {len(schema)} characters")
        print(f"Allowed tables: {len(allowed_tables)}")
        print(f"Tables with column metadata: {len(column_schema)}")

        for i, question in enumerate(QUESTIONS, start=1):
            print("\n" + "=" * 70)
            print(f"QUESTION {i}: {question}")

            try:
                # Stage A: ambiguity detection
                ambiguity = detect(question)

                if ambiguity["status"] == "ambiguous":
                    print("\nCLARIFICATION REQUIRED")
                    print(ambiguity["clarification"])
                    continue

                # Generate SQL only for clear questions
                sql = generate_sql(question, schema)
                print(f"\nGenerated SQL:\n{sql}")

                # Validate SQL before execution
                safe_sql, validation_error = validate_sql(
                    sql,
                    allowed_tables,
                    column_schema,
                )

                if validation_error:
                    print(f"\nSQL SAFETY REJECTION: {validation_error}")
                    continue

                print(f"\nValidated SQL:\n{safe_sql}")

                columns, rows, error = run_query(conn, safe_sql)

                if error:
                    print(f"\nDATABASE ERROR: {error}")
                    continue

                print(f"\nRows returned: {len(rows)}")
                print(f"Columns: {columns}")

                for row in rows[:10]:
                    print(row)

            except Exception as exc:
                print(f"\nPIPELINE ERROR: {exc}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
