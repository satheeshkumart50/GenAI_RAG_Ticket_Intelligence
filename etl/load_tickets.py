import pandas as pd
import psycopg2
import json

CSV_PATH = "etl/tickets.csv"

# ============================================================
# Database Connection
# ============================================================
conn = psycopg2.connect(
    host="localhost",
    database="vectordb",
    user="postgres",
    password="postgres",
    port=5432
)
cur = conn.cursor()

# ============================================================
# Load CSV
# ============================================================
df = pd.read_csv(CSV_PATH)
print(f"Loading {len(df)} tickets into database...")

# Helper to safely extract CSV values
def safe(row, col, default=None):
    return row[col] if col in row and pd.notna(row[col]) else default

for _, row in df.iterrows():

    # ------------ WorkLog JSON Handling ------------
    try:
        worklog_json = json.dumps(json.loads(row["WorkLog"]))
    except:
        worklog_json = json.dumps({"notes": "Missing", "updated_by": "system"})

    # ------------ CR Fields (SAFE ACCESS) ------------
    related_ticket   = safe(row, "Related_Tickets", None)
    related_cr       = safe(row, "Related_CR", None)
    cr_desc          = safe(row, "CR_Description", None)
    cr_start         = safe(row, "CR_StartTime", 0)
    cr_end           = safe(row, "CR_EndTime", 0)
    cr_region        = safe(row, "CR_Region", None)

    cur.execute(
        """
        INSERT INTO tickets (
            IncId, Description, Submitter, CreateDate, IncidentStatus,
            AssignedGroup, Region, City, Category, WorkLog,
            Hub, Node, Agent, AlertDetails, AlertProcessId, AlertKey,
            Related_Tickets, Related_CR, CR_Description,
            CR_StartTime, CR_EndTime, CR_Region
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s)
        ON CONFLICT (IncId) DO NOTHING;
        """,
        (
            row["IncId"],
            row["Description"],
            row["Submitter"],
            int(row["CreateDate"]),
            row["IncidentStatus"],
            row["AssignedGroup"],
            row["Region"],
            row["City"],
            row["Category"],
            worklog_json,
            row["Hub"],
            row["Node"],
            row["Agent"],
            row["AlertDetails"],
            int(row["AlertProcessId"]),
            row["AlertKey"],
            related_ticket,
            related_cr,
            cr_desc,
            int(cr_start),
            int(cr_end),
            cr_region
        )
    )

conn.commit()
cur.close()
conn.close()

print("Loaded all tickets into vectordb successfully!")
