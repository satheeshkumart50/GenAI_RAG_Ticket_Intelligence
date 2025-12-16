import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "host": "localhost",
    "database": "vectordb",
    "user": "postgres",
    "password": "postgres",
    "port": 5432
}


def get_connection():
    """Create a new PostgreSQL DB connection."""
    return psycopg2.connect(**DB_CONFIG)


def run_sql(sql: str, params=None):
    """
    Runs a SQL query safely and returns result as a list of dictionaries.
    Used by the agent when SQL TOOL decides to run a query.
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(sql, params or ())
        results = cur.fetchall()
        conn.close()
        return results

    except Exception as e:
        conn.close()
        raise Exception(f"SQL Execution Error: {str(e)}")


# ---- Convenience helper query functions (optional but useful) ---- #

def count_by_region(region: str):
    """Returns number of tickets in a specific region."""
    sql = "SELECT COUNT(*) FROM tickets WHERE region = %s;"
    return run_sql(sql, (region,))


def count_cancelled():
    """Returns number of cancelled tickets."""
    sql = "SELECT COUNT(*) FROM tickets WHERE incidentstatus = 'Cancelled';"
    return run_sql(sql)


def tickets_between(start_epoch: int, end_epoch: int):
    """Returns tickets created within an epoch time range."""
    sql = """
        SELECT *
        FROM tickets
        WHERE createdate BETWEEN %s AND %s;
    """
    return run_sql(sql, (start_epoch, end_epoch))
