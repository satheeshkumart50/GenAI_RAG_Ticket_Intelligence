# mcp/db.py

import psycopg2
import psycopg2.extras
import logging

# Update this when needed — or load from ENV later
DB_URL = "postgresql://postgres:postgres@localhost:5432/vectordb"

def run_readonly_query(sql: str):
    """
    Executes a READ-ONLY SQL query and returns rows as list of dictionaries.
    Uses psycopg2 with RealDictCursor for JSON-like output.
    """

    logging.info(f"[MCP SQL] Executing query: {sql}")

    conn = psycopg2.connect(DB_URL)

    # READ ONLY mode
    conn.set_session(readonly=True)

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            return {"rows": rows}

    except Exception as exc:
        logging.error(f"[MCP SQL ERROR] {exc}")
        return {"error": str(exc)}

    finally:
        conn.close()
