
import psycopg2
from dotenv import load_dotenv
import os


load_dotenv()


def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL is missing from environment.")

    conn = psycopg2.connect(
        database_url,
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
                c.conrelid::regclass::text AS source_table,
                src_col.attname AS source_column,
                c.confrelid::regclass::text AS target_table,
                target_col.attname AS target_column
            FROM pg_constraint c
            JOIN LATERAL
                unnest(c.conkey) WITH ORDINALITY
                AS src(attnum, position)
                ON TRUE
            JOIN LATERAL
                unnest(c.confkey) WITH ORDINALITY
                AS dst(attnum, position)
                ON dst.position = src.position
            JOIN pg_attribute src_col
                ON src_col.attrelid = c.conrelid
                AND src_col.attnum = src.attnum
            JOIN pg_attribute target_col
                ON target_col.attrelid = c.confrelid
                AND target_col.attnum = dst.attnum
            WHERE c.contype = 'f'
              AND c.connamespace = 'public'::regnamespace
            ORDER BY source_table, source_column;
        """)

        relationships = cur.fetchall()

    result = []

    for table, columns in schema.items():
        result.append(f"Table: {table}\nColumns: {', '.join(columns)}")

    result.append("\nForeign-key relationships:")

    for source, source_col, target, target_col in relationships:
        result.append(f"{source}.{source_col} -> {target}.{target_col}")

    return "\n".join(result)


def get_allowed_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE';
        """)

        return {row[0].lower() for row in cur.fetchall()}


def get_table_columns(conn):
    """
    Returns the database schema in SQLGlot-compatible format:
    {
        "customers": {
            "customer_id": "UNKNOWN",
            "first_name": "UNKNOWN"
        }
    }
    """

    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
        """)

        rows = cur.fetchall()

    schema = {}

    for table_name, column_name in rows:
        schema.setdefault(table_name.lower(), {})[
            column_name.lower()
        ] = "UNKNOWN"

    return schema


def run_query(conn, sql):
    try:
        with conn.cursor() as cur:
            cur.execute(sql)

            if cur.description is None:
                return None, None, "Query did not return a result set."

            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

        return columns, rows, None

    except Exception as exc:
        conn.rollback()
        return None, None, str(exc)
