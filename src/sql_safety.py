
import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError, OptimizeError
from sqlglot.optimizer.scope import traverse_scope
from sqlglot.optimizer.qualify import qualify


MAX_ROWS = 100

ALLOWED_FUNCTIONS = {
    "count",
    "sum",
    "avg",
    "min",
    "max",
    "coalesce",
    "round",
    "cast",
    "lower",
    "upper",
    "abs",
    "nullif",
    "concat",
    "timestamp_trunc",
}

FORBIDDEN_NODE_TYPES = {
    "insert",
    "update",
    "delete",
    "create",
    "drop",
    "alter",
    "merge",
    "command",
    "copy",
    "transaction",
    "commit",
    "rollback",
    "into",
    "lock",
}


def validate_sql(sql, allowed_tables, column_schema, max_rows=MAX_ROWS):

    # 1. Parse SQL.
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except SqlglotError as exc:
        return None, f"SQL parsing failed: {exc}"

    if len(statements) != 1 or statements[0] is None:
        return None, "Only one SQL statement is allowed."

    tree = statements[0]

    # 2. Allow only SELECT-based queries.
    allowed_roots = (
        exp.Select,
        exp.Union,
        exp.Intersect,
        exp.Except,
    )

    if not isinstance(tree, allowed_roots):
        return None, "Only SELECT queries are allowed."

    # 3. Reject forbidden SQL operations.
    for node in tree.walk():
        if node.key.lower() in FORBIDDEN_NODE_TYPES:
            return None, f"Forbidden SQL operation: {node.key}"

    # 4. Function allowlist.
    for func in tree.find_all(exp.Func):
        if isinstance(func, exp.Anonymous):
            function_name = func.name.lower()
        else:
            function_name = func.sql_name().lower()

        if function_name not in ALLOWED_FUNCTIONS:
            return None, f"Function not allowed: {function_name}"

    # 5. Validate table references and schemas.
    allowed_tables = {name.lower() for name in allowed_tables}

    for table in tree.find_all(exp.Table):

        if table.db and table.db.lower() != "public":
            return None, f"Non-public schema access rejected: {table.db}"

        if table.catalog:
            return None, "Cross-database access is not allowed."

        if not isinstance(table.this, exp.Identifier):
            return None, "Table-valued functions are not allowed."

    # Resolve physical tables within each SQL scope.
    for scope in traverse_scope(tree):
        for alias, (node, source) in scope.selected_sources.items():

            if isinstance(source, exp.Table):
                table_name = source.name.lower()

                if table_name not in allowed_tables:
                    return None, f"Table not allowed: {table_name}"

    # 6. Validate column references.
    try:
        qualify(
            tree.copy(),
            dialect="postgres",
            schema=column_schema,
            validate_qualify_columns=True,
            quote_identifiers=False,
            identify=False,
        )

    except OptimizeError as exc:
        return None, f"Column validation failed: {exc}"

    except SqlglotError as exc:
        return None, f"Column validation failed: {exc}"

    # 7. Validate row limit.
    if max_rows <= 0:
        return None, "Maximum row limit must be positive."

    limit = tree.args.get("limit")

    if limit is None:
        tree = tree.limit(max_rows)

    else:
        limit_value = limit.expression

        if (
            not isinstance(limit_value, exp.Literal)
            or not limit_value.is_int
        ):
            return None, "LIMIT must be a numeric integer."

        requested_limit = int(limit_value.this)

        if requested_limit < 0:
            return None, "LIMIT cannot be negative."

        if requested_limit > max_rows:
            tree = tree.limit(max_rows)

    return tree.sql(dialect="postgres"), None
