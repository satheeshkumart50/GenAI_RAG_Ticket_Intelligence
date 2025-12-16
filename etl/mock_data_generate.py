import csv
import random
from datetime import datetime, timedelta, timezone

# ---------------------------
# Helpers
# ---------------------------

regions = ["West", "Central", "East", "South"]
cities = {
    "West": ["Denver", "Boulder", "Salt Lake City"],
    "Central": ["Chicago", "St. Louis", "Dallas"],
    "East": ["New York", "Boston", "Philadelphia"],
    "South": ["Atlanta", "Miami", "Houston"]
}

categories = [
    "Video Outage",
    "Internet Down",
    "Slow Speed",
    "Packet Loss",
    "Node Down",
    "Hub Issue",
    "Authentication Failure",
    "Modem Offline",
    "Fiber Cut",
    "CMTS Congestion"
]

incident_statuses = ["Open", "In Progress", "Resolved", "Cancelled"]
assigned_groups = ["NOC-Level1", "NOC-Level2", "FieldOps", "VideoOps", "NetEng"]
submitters = ["System", "AutoMonitor", "BMC-Remedy", "Technician", "CustomerCare"]

agents = ["AlertBot", "SignalAnalyzer", "NoiseReducer", "AutoMonitorX", "PulseAI"]

hubs = ["HUB-A1", "HUB-B1", "HUB-C2", "HUB-D4"]
nodes = ["NODE-101", "NODE-202", "NODE-303", "NODE-404", "NODE-505"]

alert_templates = [
    "Signal drop detected",
    "High SNR variance",
    "MAC domain downstream failure",
    "Video feed disruption",
    "CMTS upstream channel flap",
    "Optical power low",
    "Frequent modem resets observed"
]

cr_descriptions = [
    "Planned CMTS software upgrade",
    "Fiber maintenance activity",
    "Core router reboot for patching",
    "Scheduled hub clean-up activity",
    "Optical node recalibration event",
    "Backbone congestion mitigation changes",
    "Planned power cycle maintenance"
]

# ---------------------------
# Generate CSV
# ---------------------------

with open("etl/tickets.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    # header
    writer.writerow([
        "IncId", "Description", "Submitter", "CreateDate",
        "IncidentStatus", "AssignedGroup", "Region", "City",
        "Category", "WorkLog", "Hub", "Node", "Agent",
        "AlertDetails", "AlertProcessId", "AlertKey",
        "Related_Tickets", "Related_CR", "CR_Description",
        "CR_StartTime", "CR_EndTime", "CR_Region"
    ])

    start_time = datetime(2024, 1, 1)

    # Pre-generate all INC IDs so we can reference them
    all_inc_ids = [f"INC{i:04d}" for i in range(1, 501)]

    for i in range(1, 501):
        inc_id = f"INC{i:04d}"

        region = random.choice(regions)
        city = random.choice(cities[region])
        category = random.choice(categories)
        desc = f"{category} reported in {city}. Automated monitoring detected abnormal behavior."

        submit = random.choice(submitters)
        status = random.choice(incident_statuses)
        group = random.choice(assigned_groups)
        hub = random.choice(hubs)
        node = random.choice(nodes)
        agent = random.choice(agents)

        alert_detail = random.choice(alert_templates)
        alert_process_id = random.randint(100000, 999999)
        alert_key = f"{hub}-{node}-{alert_process_id}"

        # Ticket time
        now_utc = datetime.now(timezone.utc)

        six_months_ago = now_utc - timedelta(days=180)

        # Random datetime between six_months_ago and now
        created_at = six_months_ago + timedelta(
            seconds=random.randint(
                0,
                int((now_utc - six_months_ago).total_seconds())
            )
        )

        # Convert to epoch seconds (UTC-safe)
        epoch_time = int(created_at.timestamp())

        # Worklog JSON
        worklog_json = f'{{"notes": "Initial triage performed", "updated_by": "{agent}"}}'

        # ----------------------------------------------------------
        # New Fields: Related Ticket + CR Information
        # ----------------------------------------------------------

        # Pick a related ticket that is NOT itself
        possible_related = [x for x in all_inc_ids if x != inc_id]
        related_ticket = random.choice(possible_related)

        # CR ID
        related_cr = f"CR{random.randint(10000, 99999)}"

        # CR Description
        cr_desc = random.choice(cr_descriptions)

        # -------------------------------
        # CR Start & End times (epoch)
        # -------------------------------

        # Randomly decide CR relation to ticket
        cr_relation = random.choice(["before", "after", "none"])

        if cr_relation == "before":
            # CR started 2–3 hours BEFORE ticket creation
            cr_start = created_at - timedelta(hours=random.randint(2, 3))

        elif cr_relation == "after":
            # CR started 1–6 hours AFTER ticket creation
            cr_start = created_at + timedelta(hours=random.randint(1, 6))

        else:
            # No CR associated
            cr_start = None
            cr_end = None

        # CR end is ALWAYS after CR start
        if cr_start:
            cr_end = cr_start + timedelta(hours=random.randint(1, 12))

            cr_start_epoch = int(cr_start.timestamp())
            cr_end_epoch = int(cr_end.timestamp())
        else:
            cr_start_epoch = None
            cr_end_epoch = None

        # CR Region must match ticket region
        cr_region = region

        # ----------------------------------------------------------
        # Write row
        # ----------------------------------------------------------
        writer.writerow([
            inc_id,
            desc,
            submit,
            epoch_time,
            status,
            group,
            region,
            city,
            category,
            worklog_json,
            hub,
            node,
            agent,
            alert_detail,
            alert_process_id,
            alert_key,
            related_ticket,
            related_cr,
            cr_desc,
            cr_start_epoch,
            cr_end_epoch,
            cr_region
        ])

print("Generated tickets.csv with 500 rows successfully.")
