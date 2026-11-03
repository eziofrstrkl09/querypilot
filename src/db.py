import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


# def get_connection():
#     conn = psycopg2.connect(os.getenv("DATABASE_URL"))
#     conn.set_session(readonly=True)
#     return conn

def get_connection():
    conn=psycopg2.connect(
        os.getenv("DATABASE_URL"),
        options="-c statement_timeout=10000"
    )

    conn.set_session(readonly=True)
    return conn


def get_schema_text(conn):
    schema = {}

    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
        """)

        for table, column, dtype in cur.fetchall():
            schema.setdefault(table, []).append(f"{column} ({dtype})")

        cur.execute("""
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name,
                ccu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
                AND tc.table_schema = ccu.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public';
        """)

        relationships = cur.fetchall()

    result = []

    for table, columns in schema.items():
        result.append(f"Table: {table}\nColumns: {', '.join(columns)}")

    result.append("\nForeign-key relationships:")

    for source, source_col, target, target_col in relationships:
        result.append(f"{source}.{source_col} -> {target}.{target_col}")

    return "\n".join(result)


def run_query(conn, sql):
    try:
        with conn.cursor() as cur:
            cur.execute(sql)

            if cur.description is None:
                return None, None, "Query did not return a result set."

            columns = [description[0] for description in cur.description]
            rows = cur.fetchall()

            return columns, rows, None

    except psycopg2.Error as exc:
        conn.rollback()
        return None, None, str(exc)
