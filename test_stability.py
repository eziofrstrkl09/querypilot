import time
from google.genai.errors import APIError

from src.db import get_connection, get_schema_text, get_allowed_tables, run_query
from src.llm import generate_sql
from src.sql_safety import validate_sql


QUESTIONS = [
    # "How many customers do we have?",
    # "How many orders were delivered?",
    # "What are the names of all product categories?",
    "How many orders did each store handle?",
    "What was our total revenue?",
]

TARGET = 5
MAX_RETRIES = 3


def result_signature(rows):
    """Compare result sets independently of row ordering."""
    return tuple(sorted(tuple(str(value) for value in row) for row in rows))


def main():
    conn = get_connection()

    try:
        schema = get_schema_text(conn)
        allowed_tables = get_allowed_tables(conn)

        print(f"Schema: {len(schema)} characters | Tables: {len(allowed_tables)}")

        for question in QUESTIONS:
            successes = 0
            failures = 0
            signatures = {}
            sql_variants = set()

            print(f"\n{'=' * 65}\n{question}")

            while successes < TARGET and failures < MAX_RETRIES * 2:
                retry = 0

                while True:
                    try:
                        sql = generate_sql(question, schema)
                        safe_sql, validation_error = validate_sql(sql, allowed_tables)

                        if validation_error:
                            print(f"VALIDATION_ERROR: {validation_error}")
                            failures += 1
                            break

                        columns, rows, error = run_query(conn, safe_sql)

                        if error:
                            print(f"DB_ERROR: {error}")
                            failures += 1
                            break

                        signature = result_signature(rows)
                        signatures[signature] = signatures.get(signature, 0) + 1
                        sql_variants.add(safe_sql)
                        successes += 1

                        preview = str(rows[:2])
                        print(f"{successes}/{TARGET} OK | {preview} | {safe_sql}")

                        time.sleep(5)
                        break

                    except APIError as exc:
                        code = getattr(exc, "code", None)

                        if code in (429, 503) and retry < MAX_RETRIES:
                            retry += 1
                            wait = 10 if retry == 1 else 30
                            print(f"INFRA_ERROR {code} | retry {retry}/{MAX_RETRIES} in {wait}s")
                            time.sleep(wait)
                        else:
                            print(f"INFRA_ERROR {code}: {exc}")
                            failures += 1
                            break

                    except Exception as exc:
                        print(f"PIPELINE_ERROR: {exc}")
                        failures += 1
                        break

            print("\nSUMMARY")
            print(f"Successful samples: {successes}/{TARGET}")
            print(f"Distinct result sets: {len(signatures)}")
            print(f"Failed attempts: {failures}")
            print("SQL variants:")
            for variant in sorted(sql_variants):
                print(f"  {variant}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()