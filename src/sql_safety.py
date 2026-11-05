
import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError
from sqlglot.optimizer.scope import traverse_scope


MAX_ROWS = 100

# Conservative function allowlist.
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


def validate_sql(sql, allowed_tables, max_rows=MAX_ROWS):
    """
    Validate generated SQL before execution.

    Returns:
        (safe_sql, None) on success.
        (None, error_message) on rejection.
    """

    # 1. Parse SQL using PostgreSQL dialect.
    try:
        statements = sqlglot.parse(sql, read="postgres")

    except SqlglotError as exc:
        return None, f"SQL parsing failed: {exc}"

    # 2. Require exactly one non-empty statement.
    if len(statements) != 1 or statements[0] is None:
        return None, "Only one SQL statement is allowed."

    tree = statements[0]

    # 3. Only SELECT and set-operation queries.
    allowed_roots = (
        exp.Select,
        exp.Union,
        exp.Intersect,
        exp.Except,
    )

    if not isinstance(tree, allowed_roots):
        return None, "Only SELECT queries are allowed."

    # 4. Reject forbidden operations anywhere in the AST.
    for node in tree.walk():
        if node.key.lower() in FORBIDDEN_NODE_TYPES:
            return None, f"Forbidden SQL operation: {node.key}"

    # 5. Restrict SQL functions.
    for func in tree.find_all(exp.Func):

        if isinstance(func, exp.Anonymous):
            function_name = func.name.lower()
        else:
            function_name = func.sql_name().lower()

        if function_name not in ALLOWED_FUNCTIONS:
            return None, f"Function not allowed: {function_name}"

    # 6. Normalize the table allowlist.
    allowed_tables = {
        name.lower() for name in allowed_tables
    }

    # 7. Reject non-public schemas and cross-database references.
    for table in tree.find_all(exp.Table):

        if table.db and table.db.lower() != "public":
            return None, (
                f"Non-public schema access rejected: {table.db}"
            )

        if table.catalog:
            return None, "Cross-database access is not allowed."

        # Reject table-valued functions.
        if not isinstance(table.this, exp.Identifier):
            return None, "Table-valued functions are not allowed."

    # 8. Resolve physical tables using SQLGlot scopes.
    # CTEs and derived tables resolve to Scope objects.
    for scope in traverse_scope(tree):

        for alias, (node, source) in scope.selected_sources.items():

            if isinstance(source, exp.Table):
                table_name = source.name.lower()

                if table_name not in allowed_tables:
                    return None, f"Table not allowed: {table_name}"

    # 9. Enforce maximum result-row limit.
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

    # 10. Return the validated, normalized SQL.
    return tree.sql(dialect="postgres"), None
