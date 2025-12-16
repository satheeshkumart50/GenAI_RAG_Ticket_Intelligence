import ollama

ollama.host = "http://localhost:11434"

EMBED_MODEL = "qllama/bge-small-en-v1.5"


def get_query_embedding(text: str):
    """
    Generate embedding for user query text using Ollama.
    Returns a Python list (vector of length 384).
    """

    response = ollama.embeddings(
        model=EMBED_MODEL,
        prompt=text
    )

    return response["embedding"]
