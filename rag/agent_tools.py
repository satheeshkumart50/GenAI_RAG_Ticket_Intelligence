from rag.sql_search import run_sql
from rag.vector_search import search_similar_chunks


def sql_tool(query: str):
    """Executes SQL and returns structured result."""
    try:
        result = run_sql(query)
        return {"type": "sql_result", "data": result}
    except Exception as e:
        return {"type": "error", "message": str(e)}


def vector_tool(query: str):
    """Executes vector search for semantic lookup."""
    try:
        result = search_similar_chunks(query)
        return {"type": "vector_result", "data": result}
    except Exception as e:
        return {"type": "error", "message": str(e)}