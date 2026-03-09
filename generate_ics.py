#!/usr/bin/env python3
"""
Generate events.ics for DenverSec monthly meetup.
Meets every 3rd Wednesday of the month.
To cancel a specific month, add a line to cancelled_months.txt like: 2026-04
To stop permanently, disable the GitHub Action.
"""

import os
from datetime import datetime, timedelta, timezone
import calendar

# ── Config ────────────────────────────────────────────────────────────────────
EVENT_TITLE       = "DenverSec Monthly Meetup"
EVENT_DESCRIPTION = "Denver Security Community monthly meetup. See denversec.org for details."
EVENT_LOCATION    = "Denver, CO"
EVENT_URL         = "https://denversec.org"
EVENT_HOUR        = 18   # 6:00 PM local (Mountain)
EVENT_DURATION_H  = 2
TIMEZONE          = "America/Denver"
CANCELLED_FILE    = "cancelled_months.txt"   # optional, relative to repo root
OUTPUT_FILE       = "Densec_events.ics"
# How many future occurrences to include
FUTURE_MONTHS     = 3
# ──────────────────────────────────────────────────────────────────────────────


def third_wednesday(year: int, month: int) -> datetime:
    """Return the datetime of the 3rd Wednesday for a given year/month."""
    cal = calendar.monthcalendar(year, month)
    wednesdays = [week[calendar.WEDNESDAY] for week in cal if week[calendar.WEDNESDAY] != 0]
    day = wednesdays[2]  # 0-indexed, so index 2 = 3rd Wednesday
    return datetime(year, month, day, EVENT_HOUR, 0, 0)


def load_cancelled() -> set:
    """Load cancelled months from file (format: YYYY-MM, one per line)."""
    if not os.path.exists(CANCELLED_FILE):
        return set()
    with open(CANCELLED_FILE) as f:
        return {line.strip() for line in f if line.strip()}


def uid(dt: datetime) -> str:
    return f"denversec-{dt.strftime('%Y%m')}-meetup@denversec.org"


def ics_dt(dt: datetime) -> str:
    """Format datetime for ICS (local time with TZID)."""
    return dt.strftime("%Y%m%dT%H%M%S")


def build_ics(events: list[datetime]) -> str:
    now = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//DenverSec//Monthly Meetup//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{EVENT_TITLE}",
        f"X-WR-TIMEZONE:{TIMEZONE}",
    ]

    for dt in events:
        dt_end = dt + timedelta(hours=EVENT_DURATION_H)
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid(dt)}",
            f"DTSTAMP:{now}",
            f"DTSTART;TZID={TIMEZONE}:{ics_dt(dt)}",
            f"DTEND;TZID={TIMEZONE}:{ics_dt(dt_end)}",
            f"SUMMARY:{EVENT_TITLE}",
            f"DESCRIPTION:{EVENT_DESCRIPTION}",
            f"LOCATION:{EVENT_LOCATION}",
            f"URL:{EVENT_URL}",
            "STATUS:CONFIRMED",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")
    # ICS lines must be CRLF
    return "\r\n".join(lines) + "\r\n"


def main():
    cancelled = load_cancelled()
    today = datetime.today()

    events = []
    year, month = today.year, today.month

    while len(events) < FUTURE_MONTHS:
        month_key = f"{year}-{month:02d}"
        if month_key not in cancelled:
            dt = third_wednesday(year, month)
            # Include if the event hasn't fully passed yet (give same-day grace)
            if dt.date() >= today.date():
                events.append(dt)

        month += 1
        if month > 12:
            month = 1
            year += 1

    ics_content = build_ics(events)

    with open(OUTPUT_FILE, "w", newline="") as f:
        f.write(ics_content)

    print(f"✅ Written {OUTPUT_FILE} with {len(events)} event(s):")
    for e in events:
        print(f"   • {e.strftime('%A, %B %-d, %Y at %-I:%M %p')} MT")


if __name__ == "__main__":
    main()
