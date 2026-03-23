"""
iCal Sync Engine for Hana House — Simplified 2-Room System.
Handles parsing iCal feeds from OTAs and generating iCal exports.
"""

import requests
from datetime import datetime, date, timedelta
from icalendar import Calendar, Event
import uuid
import database as db


# ─── iCal Import (Parse from OTA) ────────────────────────────────────────────

def fetch_ical_from_url(url, timeout=15):
    """Fetch iCal data from a URL."""
    try:
        headers = {
            "User-Agent": "HanaHouse-RoomManager/2.0",
            "Accept": "text/calendar",
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text, None
    except requests.exceptions.Timeout:
        return None, "Connection timed out"
    except requests.exceptions.ConnectionError:
        return None, "Could not connect to server"
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP error: {e.response.status_code}"
    except Exception as e:
        return None, f"Error: {str(e)}"


def parse_ical_events(ical_text):
    """Parse iCal text and extract booking events."""
    events = []
    try:
        cal = Calendar.from_ical(ical_text)
        for component in cal.walk():
            if component.name == "VEVENT":
                event = {}

                # UID
                uid = component.get("uid")
                event["uid"] = str(uid) if uid else str(uuid.uuid4())

                # Summary / Guest Name
                summary = component.get("summary")
                event["summary"] = str(summary) if summary else "Blocked / Reserved"

                # Dates
                dtstart = component.get("dtstart")
                dtend = component.get("dtend")

                if dtstart:
                    dt = dtstart.dt
                    event["check_in"] = dt.date() if hasattr(dt, "date") else dt
                else:
                    continue

                if dtend:
                    dt = dtend.dt
                    event["check_out"] = dt.date() if hasattr(dt, "date") else dt
                else:
                    event["check_out"] = event["check_in"] + timedelta(days=1)

                # Description
                desc = component.get("description")
                event["description"] = str(desc) if desc else ""

                events.append(event)
    except Exception as e:
        return [], f"Parse error: {str(e)}"

    return events, None


def sync_ical_source(source_id):
    """Sync a single iCal source: fetch, parse, and update bookings."""
    with db.get_connection() as conn:
        source = conn.execute(
            "SELECT s.*, r.name as room_name FROM ical_sources s JOIN rooms r ON s.room_id = r.id WHERE s.id = ?",
            (source_id,),
        ).fetchone()

    if not source:
        return {"status": "error", "message": "Source not found"}

    room_id = source["room_id"]
    platform = source["platform"]
    url = source["ical_url"]

    db.update_ical_source_status(source_id, "syncing")

    # Fetch
    ical_text, error = fetch_ical_from_url(url)
    if error:
        db.update_ical_source_status(source_id, "error")
        db.add_sync_log(source_id, "import", "error", error)
        return {"status": "error", "message": error}

    # Parse
    events, parse_error = parse_ical_events(ical_text)
    if parse_error:
        db.update_ical_source_status(source_id, "error")
        db.add_sync_log(source_id, "import", "error", parse_error)
        return {"status": "error", "message": parse_error}

    # Process
    new_count = 0
    updated_count = 0
    skipped_count = 0

    for event in events:
        uid = event["uid"]
        existing = db.get_booking_by_ical_uid(uid, room_id)

        if existing:
            db.update_booking(
                existing["id"],
                event["summary"],
                "",  # phone not available from iCal
                event["check_in"].isoformat(),
                event["check_out"].isoformat(),
                platform,
                event.get("description", ""),
                "confirmed",
            )
            updated_count += 1
        else:
            if db.check_availability(room_id, event["check_in"].isoformat(), event["check_out"].isoformat()):
                db.create_booking(
                    room_id,
                    event["summary"],
                    "",  # phone not available from iCal
                    event["check_in"].isoformat(),
                    event["check_out"].isoformat(),
                    platform,
                    event.get("description", ""),
                    uid,
                )
                new_count += 1
            else:
                skipped_count += 1

    now = datetime.now().isoformat()
    db.update_ical_source_status(source_id, "success", now)

    message = f"Synced {len(events)} events: {new_count} new, {updated_count} updated, {skipped_count} conflicts"
    db.add_sync_log(source_id, "import", "success", message, len(events))

    return {
        "status": "success",
        "message": message,
        "total": len(events),
        "new": new_count,
        "updated": updated_count,
        "skipped": skipped_count,
    }


def sync_all_sources():
    """Sync all active iCal sources."""
    sources = db.get_ical_sources()
    results = []
    for source in sources:
        if source["auto_sync"]:
            result = sync_ical_source(source["id"])
            result["source_id"] = source["id"]
            result["room_name"] = source["room_name"]
            result["platform"] = source["platform"]
            results.append(result)
    return results


# ─── iCal Export (Generate for OTA) ──────────────────────────────────────────

def generate_ical_for_room(room_id):
    """Generate iCal calendar for a specific room."""
    rooms = db.get_rooms()
    room = next((r for r in rooms if r["id"] == room_id), None)
    if not room:
        return None

    cal = Calendar()
    cal.add("prodid", "-//Hana House Room Manager//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", f"Hana House - {room['name']}")

    bookings = db.get_bookings(room_id=room_id)

    for booking in bookings:
        event = Event()

        uid = booking["ical_uid"] if booking["ical_uid"] else f"hana-{booking['id']}@hanahouse.local"
        event.add("uid", uid)
        event.add("dtstart", date.fromisoformat(booking["check_in"]))
        event.add("dtend", date.fromisoformat(booking["check_out"]))
        event.add("summary", f"Reserved - {booking['guest_name']}")
        event.add("description", f"Source: {booking['source']}\nRoom: {room['name']}")
        event.add("dtstamp", datetime.now())
        event.add("transp", "OPAQUE")

        cal.add_component(event)

    return cal.to_ical().decode("utf-8")


# ─── Conflict Detection ──────────────────────────────────────────────────────

def detect_conflicts(room_id=None):
    """Detect booking conflicts (overlapping dates)."""
    with db.get_connection() as conn:
        query = """
            SELECT b1.id as booking1_id, b1.guest_name as guest1, b1.check_in as ci1, b1.check_out as co1,
                   b2.id as booking2_id, b2.guest_name as guest2, b2.check_in as ci2, b2.check_out as co2,
                   r.name as room_name, r.id as room_id
            FROM bookings b1
            JOIN bookings b2 ON b1.room_id = b2.room_id AND b1.id < b2.id
            JOIN rooms r ON b1.room_id = r.id
            WHERE b1.check_in < b2.check_out AND b1.check_out > b2.check_in
              AND b1.status = 'confirmed' AND b2.status = 'confirmed'
        """
        params = []
        if room_id:
            query += " AND b1.room_id = ?"
            params.append(room_id)

        query += " ORDER BY r.name, b1.check_in"
        return conn.execute(query, params).fetchall()
