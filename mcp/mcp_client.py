import requests


class MCPClient:
    """
    SIMPLE JSON-OVER-HTTP SQL CLIENT
    --------------------------------
    Sends SQL queries to the MCP SQL Server over HTTP.

    Server: FastAPI running in mcp/sql_server.py
    Endpoint: POST /sql_query
    """

    def __init__(self, url="http://127.0.0.1:9000/sql_query"):
        self.url = url

    def sql_query(self, sql: str):
        """
        Send SQL query to MCP HTTP server and return rows or error.
        """
        try:
            payload = {"sql": sql}
            response = requests.post(self.url, json=payload, timeout=10)

            # If server responded with non-JSON or HTTP error
            try:
                return response.json()
            except Exception:
                return {"error": f"Invalid JSON from server: {response.text}"}

        except Exception as e:
            return {"error": str(e)}
