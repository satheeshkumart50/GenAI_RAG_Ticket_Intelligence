import psycopg2
import json
import textwrap
import ollama


# ================================
# Ollama Host
# ================================
ollama.host = "http://localhost:11434"

# ================================
# Database Connection
# ================================
conn = psycopg2.connect(
    host="localhost",
    database="vectordb",
    user="postgres",
    password="postgres",
    port=5432
)
cur = conn.cursor()

# ================================
# Config
# ================================
CHUNK_SIZE = 1000     # ~250 tokens
EMBED_MODEL = "qllama/bge-small-en-v1.5"


# ================================
# Text Chunking Helper
# ================================
def chunk_text(text, chunk_size=CHUNK_SIZE):
    text = text.replace("\n", " ").strip()
    if not text:
        return []
    return textwrap.wrap(text, chunk_size)


# ================================
# WorkLog Text Builder
# ================================
def build_worklog_text(worklog_json):
    if not worklog_json:
        return ""

    if isinstance(worklog_json, dict):
        notes = worklog_json.get("notes", "")
        updated = worklog_json.get("updated_by", "")
        return f"{notes} (updated_by: {updated})"

    if isinstance(worklog_json, list):
        logs = []
        for item in worklog_json:
            ts = item.get("timestamp")
            team = item.get("team", "")
            user = item.get("user", "")
            action = item.get("action", "")
            logs.append(f"[{ts}] {team} | {user}: {action}")
        return " ".join(logs)

    return ""


# ================================
# Get Embedding
# ================================
def get_embedding(text):
    response = ollama.embeddings(model=EMBED_MODEL, prompt=text)
    return response["embedding"]


# ================================
# Process Ticket → Create 5 Chunk Types
# ================================
def process_ticket(inc_id, description, worklog, alert_details, cr_desc, region, city, category):

    # -------------------------------------------------------------
    # 1. DESCRIPTION CHUNKS
    # -------------------------------------------------------------
    desc_text = f"Description: {description or ''}"
    for idx, chunk in enumerate(chunk_text(desc_text), start=1):
        embedding = get_embedding(chunk)
        cur.execute(
            """INSERT INTO ticket_chunks
               (IncId, chunk_type, chunk_no, text_chunk, embedding)
               VALUES (%s, %s, %s, %s, %s);""",
            (inc_id, "description", idx, chunk, embedding),
        )

    # -------------------------------------------------------------
    # 2. WORKLOG CHUNKS
    # -------------------------------------------------------------
    wl_text = f"WorkLog: {build_worklog_text(worklog)}"
    for idx, chunk in enumerate(chunk_text(wl_text), start=1):
        embedding = get_embedding(chunk)
        cur.execute(
            """INSERT INTO ticket_chunks
               (IncId, chunk_type, chunk_no, text_chunk, embedding)
               VALUES (%s, %s, %s, %s, %s);""",
            (inc_id, "worklog", idx, chunk, embedding),
        )

    # -------------------------------------------------------------
    # 3. ALERT DETAILS CHUNKS
    # -------------------------------------------------------------
    alert_text = f"AlertDetails: {alert_details or ''}"
    for idx, chunk in enumerate(chunk_text(alert_text), start=1):
        embedding = get_embedding(chunk)
        cur.execute(
            """INSERT INTO ticket_chunks
               (IncId, chunk_type, chunk_no, text_chunk, embedding)
               VALUES (%s, %s, %s, %s, %s);""",
            (inc_id, "alertdetails", idx, chunk, embedding),
        )

    # -------------------------------------------------------------
    # 4. CR DESCRIPTION CHUNKS (NEW!)
    # -------------------------------------------------------------
    cr_text = f"CR_Description: {cr_desc or ''}"
    for idx, chunk in enumerate(chunk_text(cr_text), start=1):
        embedding = get_embedding(chunk)
        cur.execute(
            """INSERT INTO ticket_chunks
               (IncId, chunk_type, chunk_no, text_chunk, embedding)
               VALUES (%s, %s, %s, %s, %s);""",
            (inc_id, "cr_description", idx, chunk, embedding),
        )

    # -------------------------------------------------------------
    # 5. CONTEXT CHUNKS (City + Region + Category)
    # -------------------------------------------------------------
    context_text = f"""
    Context Information:
    Region: {region}
    City: {city}
    Category: {category}
    """
    for idx, chunk in enumerate(chunk_text(context_text), start=1):
        embedding = get_embedding(chunk)
        cur.execute(
            """INSERT INTO ticket_chunks
               (IncId, chunk_type, chunk_no, text_chunk, embedding)
               VALUES (%s, %s, %s, %s, %s);""",
            (inc_id, "context", idx, chunk, embedding),
        )


# ================================
# Fetch All Tickets
# ================================
cur.execute("""
    SELECT
        IncId, Description, WorkLog, AlertDetails,
        CR_Description, Region, City, Category
    FROM tickets;
""")
tickets = cur.fetchall()

print(f"Found {len(tickets)} tickets. Generating embeddings for 5 chunk types each...")

# ================================
# Process All Tickets
# ================================
for inc_id, description, worklog, alertdetails, cr_desc, region, city, category in tickets:
    try:
        wl = json.loads(worklog) if isinstance(worklog, str) else worklog
    except:
        wl = {}

    process_ticket(inc_id, description, wl, alertdetails, cr_desc, region, city, category)

# ================================
# Finalize
# ================================
conn.commit()
cur.close()
conn.close()

print("All 5 chunk types (description, worklog, alertdetails, cr_description, context) embedded successfully!")
