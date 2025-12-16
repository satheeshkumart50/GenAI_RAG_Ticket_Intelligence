from fastapi import FastAPI
import asyncpg
import uvicorn

DB_URL = "postgresql://postgres:postgres@localhost:5432/vectordb"

app = FastAPI(title="SQL MCP Server (HTTP JSON Mode)")


@app.post("/sql_query")
async def sql_query(payload: dict):
    sql = payload.get("sql", "").strip()

    if not sql.lower().startswith("select"):
        return {"error": "Only SELECT statements allowed"}

    try:
        conn = await asyncpg.connect(DB_URL)
        rows = await conn.fetch(sql)
        await conn.close()

        return {"rows": [dict(r) for r in rows]}

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9000)
