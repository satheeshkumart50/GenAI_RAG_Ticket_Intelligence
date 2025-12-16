import psycopg2
from psycopg2.extras import RealDictCursor
from rag.embeddings import get_query_embedding


# Database config
DB_CONFIG = {
    "host": "localhost",
    "database": "vectordb",
    "user": "postgres",
    "password": "postgres",
    "port": 5432
}


def get_db_connection():
    """Returns a PostgreSQL connection."""
    return psycopg2.connect(**DB_CONFIG)


def search_similar_chunks(query: str, top_k: int = 5):
    """
    Generates an embedding for the query, converts it to pgvector format,
    and retrieves top-k most similar text chunks from PostgreSQL.
    """

    # Generate embedding (Python list of floats)
    embedding = get_query_embedding(query)

    # Convert list to pgvector string format: '[0.24, -0.11, ...]'
    emb_str = "[" + ",".join(str(x) for x in embedding) + "]"

    # Connect to PostgreSQL
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Perform similarity search
    cur.execute(
        """
        SELECT
            chunk_id,
            IncId,
            chunk_type,
            chunk_no,
            text_chunk,
            1 - (embedding <-> %s::vector) AS similarity
        FROM ticket_chunks
        ORDER BY embedding <-> %s::vector
        LIMIT %s;
        """,
        (emb_str, emb_str, top_k)
    )

    results = cur.fetchall()

    conn.close()
    return results
