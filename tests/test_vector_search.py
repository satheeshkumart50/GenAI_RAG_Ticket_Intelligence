import time
from rag.vector_search import search_similar_chunks


# ================================================
# Predefined Telecom Semantic Queries
# ================================================
TEST_QUERIES = [
    "video outage in west region with signal drop detected",
    "cmts upstream channel flap incidents",
    "technician dispatched to node issue and performed initial triage",
    "optical power low or fiber cut alarms on hubs",
    "high snr variance alerts affecting customers in east region",
]


# ================================================
# Pretty Print Helper
# ================================================
def print_result(item):
    inc_id = item.get("IncId") or item.get("incid") or "UNKNOWN"
    chunk_id = item.get("chunk_id", "UNKNOWN")
    chunk_type = item.get("chunk_type", "unknown")
    chunk_no = item.get("chunk_no", "?")
    similarity = round(item.get("similarity", 0), 4)
    text_preview = item.get("text_chunk", "")[:160]

    print(f"   • ChunkID     : {chunk_id}")
    print(f"     Ticket      : {inc_id}")
    print(f"     Chunk Type  : {chunk_type} (#{chunk_no})")
    print(f"     Similarity  : {similarity}")
    print(f"     Preview     : {text_preview}...")
    print("     " + "-" * 70)


# ================================================
# Run Vector Search With Timings
# ================================================
def run_query_with_timing(query, top_k=5):
    print(f"\n Query: {query}")
    print("=" * 90)

    # Measure wall-clock time
    t0 = time.time()

    try:
        results = search_similar_chunks(query, top_k=top_k)
    except Exception as e:
        print(f" ERROR: {e}")
        return

    t1 = time.time()

    search_time = t1 - t0

    # Print results
    if not results:
        print("No similar chunks found.")
        return

    print(f"Top {len(results)} Results:\n")
    for item in results:
        print_result(item)

    print("\n Timing Summary:")
    print(f"   • Total Vector Search Time: {search_time:.4f} sec")
    print(f"   • Results Returned: {len(results)} items")
    print("-" * 90)


# ================================================
# Run Full Suite
# ================================================
def run_vector_tests():
    print("\n============================================================")
    print(" TELECOM VECTOR SEARCH TEST SUITE (WITH PERFORMANCE TIMING) ")
    print("============================================================\n")

    for query in TEST_QUERIES:
        run_query_with_timing(query, top_k=5)

    print("\nAll queries completed.\n")


# ================================================
# Entry Point
# ================================================
if __name__ == "__main__":
    run_vector_tests()
