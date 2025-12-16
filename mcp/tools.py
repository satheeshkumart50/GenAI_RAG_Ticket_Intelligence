# mcp/tools.py

from .db import run_readonly_query


def sql_query(args):
    """
    MCP tool: sql.query
    Expected:
        args = { "sql": "<query>" }
    """

    sql = args.get("sql")

    if not sql:
        return {"error": "SQL query missing"}

    # Basic SQL security checks
    lowered = sql.lower().strip()

    if ";" in lowered:
        return {"error": "Multiple SQL statements are not allowed"}

    # Protect against modification queries
    forbidden = ["insert", "update", "delete", "drop", "create", "alter"]
    if any(keyword in lowered.split()[:2] for keyword in forbidden):
        return {"error": "Only read-only (SELECT) queries allowed"}

    return run_readonly_query(sql)