import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


AUDIT_FILE = "data/audit.jsonl"

IST = ZoneInfo("Asia/Kolkata")


def log_event(event_type, **details):
    """Record an event in both UTC and IST."""

    os.makedirs("data", exist_ok=True)

    now = datetime.now(timezone.utc)

    event = {
        "timestamp_utc": now.isoformat(),
        "timestamp_ist": now.astimezone(IST).isoformat(),
        "event_type": event_type,
        "details": details,
    }

    with open(
        AUDIT_FILE,
        "a",
        encoding="utf-8"
    ) as file:
        file.write(json.dumps(event) + "\n")


def get_recent_events(limit=20):
    """Return the most recent audit events."""

    if not os.path.exists(AUDIT_FILE):
        return []

    with open(
        AUDIT_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        events = [
            json.loads(line)
            for line in file
            if line.strip()
        ]

    return events[-limit:]