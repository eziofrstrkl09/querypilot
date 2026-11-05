
from src.db import get_connection, get_schema_text, run_query
from src.llm import generate_sql

QUESTIONS = [
    "How many customers do we have?",
    "How many orders were delivered?",
    "What are the names of all product categories?",
    "How many orders did each store handle?",
    "What was our total revenue?",
]


def main():
    conn = get_connection()

    try:
        schema = get_schema_text(conn)
        print(f"Schema retrieved (~{len(schema) // 4} tokens)\n")

        for i, question in enumerate(QUESTIONS, start=1):
            print("\n" + "=" * 70)
            print(f"QUESTION {i}: {question}")

            try:
                sql = generate_sql(question, schema)
                print(f"\nGenerated SQL:\n{sql}")

                columns, rows, error = run_query(conn, sql)

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
