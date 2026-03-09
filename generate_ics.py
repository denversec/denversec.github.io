#!/usr/bin/env python3
"""
Generate Densec_events.ics and feed.xml for DenverSec monthly meetup.
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
RSS_FILE          = "feed.xml"
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


def rss_dt(dt: datetime) -> str:
    """Format datetime for RSS pubDate (RFC 2822)."""
    # RSS requires timezone offset; use -0600 (MT standard) / -0700 (MT daylight)
    # Simple approach: just use UTC representation
    utc_dt = dt.replace(tzinfo=timezone(timedelta(hours=-6)))
    return dt.strftime("%a, %d %b %Y %H:%M:%S -0600")


def build_rss(events: list[datetime]) -> str:
    now = datetime.now(tz=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

    items = ""
    for dt in events:
        human_date = dt.strftime("%A, %B %-d, %Y at %-I:%M %p MT")
        items += f"""
  <item>
    <title>{EVENT_TITLE} — {dt.strftime("%B %Y")}</title>
    <link>{EVENT_URL}</link>
    <guid isPermaLink="false">denversec-{dt.strftime("%Y%m")}-meetup</guid>
    <pubDate>{rss_dt(dt)}</pubDate>
    <description>{EVENT_DESCRIPTION} Date: {human_date}. Location: {EVENT_LOCATION}.</description>
  </item>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{EVENT_TITLE}</title>
    <link>{EVENT_URL}</link>
    <description>Upcoming DenverSec meetups — every 3rd Wednesday of the month.</description>
    <language>en-us</language>
    <lastBuildDate>{now}</lastBuildDate>
    <ttl>1440</ttl>{items}
  </channel>
</rss>
"""


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

    # Write ICS
    ics_content = build_ics(events)
    with open(OUTPUT_FILE, "w", newline="") as f:
        f.write(ics_content)

    # Write RSS
    rss_content = build_rss(events)
    with open(RSS_FILE, "w") as f:
        f.write(rss_content)

    print(f"✅ Written {OUTPUT_FILE} and {RSS_FILE} with {len(events)} event(s):")
    for e in events:
        print(f"   • {e.strftime('%A, %B %-d, %Y at %-I:%M %p')} MT")


if __name__ == "__main__":
    main()
