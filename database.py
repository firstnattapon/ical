"""
Database module for Hana House — Simplified 2-Room System.
Modified for PostgreSQL (Neon / Supabase).
"""

import os
from datetime import datetime, date, timedelta
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    raise ImportError("Please install psycopg2-binary: pip install psycopg2-binary")

def get_db_url():
    # 1. Environment Variable
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return db_url
        
    # 2. Streamlit Secrets (for Streamlit Cloud or local .streamlit/secrets.toml)
    try:
        import streamlit as st
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass
        
    # 3. .env file fallback
    try:
        from dotenv import load_dotenv
        load_dotenv()
        db_url = os.environ.get("DATABASE_URL")
        if db_url:
            return db_url
    except Exception:
        pass

    raise ValueError("DATABASE_URL is not set. Please set it in .env, Streamlit Secrets, or environment variables.")

# ─── Hardcoded Room Config ────────────────────────────────────────────────────
ROOMS = [
    {"id": 1, "name": "ห้อง 1 (Standard)", "color": "#818CF8"},
    {"id": 2, "name": "ห้อง 2 (Standard)", "color": "#34D399"},
]

@contextmanager
def get_connection():
    """Context manager for PostgreSQL database connections."""
    db_url = get_db_url()
    conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize database with tables for Postgres."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    color TEXT DEFAULT '#818CF8'
                );

                CREATE TABLE IF NOT EXISTS bookings (
                    id SERIAL PRIMARY KEY,
                    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
                    guest_name TEXT DEFAULT 'Guest',
                    guest_phone TEXT DEFAULT '',
                    check_in DATE NOT NULL,
                    check_out DATE NOT NULL,
                    source TEXT DEFAULT 'direct',
                    notes TEXT DEFAULT '',
                    status TEXT DEFAULT 'confirmed',
                    ical_uid TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS ical_sources (
                    id SERIAL PRIMARY KEY,
                    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
                    platform TEXT NOT NULL,
                    ical_url TEXT NOT NULL,
                    last_synced TIMESTAMP,
                    sync_status TEXT DEFAULT 'pending',
                    auto_sync INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS sync_log (
                    id SERIAL PRIMARY KEY,
                    ical_source_id INTEGER REFERENCES ical_sources(id) ON DELETE SET NULL,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT DEFAULT '',
                    events_count INTEGER DEFAULT 0,
                    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Ensure the 2 hardcoded rooms exist
            for room in ROOMS:
                cur.execute("SELECT id FROM rooms WHERE id = %s", (room["id"],))
                existing = cur.fetchone()
                if not existing:
                    cur.execute(
                        "INSERT INTO rooms (id, name, color) VALUES (%s, %s, %s)",
                        (room["id"], room["name"], room["color"]),
                    )

def get_rooms():
    """Return the 2 hardcoded rooms."""
    return ROOMS

# ─── Booking CRUD ─────────────────────────────────────────────────────────────

def create_booking(room_id, guest_name, guest_phone, check_in, check_out, source="direct", notes="", ical_uid=""):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO bookings (room_id, guest_name, guest_phone, check_in, check_out, source, notes, ical_uid)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (room_id, guest_name, guest_phone, check_in, check_out, source, notes, ical_uid),
            )
            return cur.fetchone()["id"]

def get_bookings(room_id=None, start_date=None, end_date=None, source=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            query = """SELECT b.*, r.name as room_name, r.color as room_color
                       FROM bookings b 
                       JOIN rooms r ON b.room_id = r.id
                       WHERE b.status = 'confirmed'"""
            params = []
            if room_id:
                query += " AND b.room_id = %s"
                params.append(room_id)
            if start_date:
                query += " AND b.check_out > %s"
                params.append(start_date)
            if end_date:
                query += " AND b.check_in < %s"
                params.append(end_date)
            if source:
                query += " AND b.source = %s"
                params.append(source)
            query += " ORDER BY b.check_in"
            
            cur.execute(query, tuple(params))
            return cur.fetchall()

def get_booking(booking_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT b.*, r.name as room_name, r.color as room_color
                   FROM bookings b JOIN rooms r ON b.room_id = r.id WHERE b.id = %s""",
                (booking_id,),
            )
            return cur.fetchone()

def get_booking_by_ical_uid(ical_uid, room_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM bookings WHERE ical_uid = %s AND room_id = %s",
                (ical_uid, room_id),
            )
            return cur.fetchone()

def update_booking(booking_id, guest_name, guest_phone, check_in, check_out, source, notes, status):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE bookings SET guest_name=%s, guest_phone=%s, check_in=%s, check_out=%s, 
                   source=%s, notes=%s, status=%s WHERE id=%s""",
                (guest_name, guest_phone, check_in, check_out, source, notes, status, booking_id),
            )

def cancel_booking(booking_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE bookings SET status='cancelled' WHERE id=%s", (booking_id,))

def delete_booking(booking_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM bookings WHERE id = %s", (booking_id,))

def check_availability(room_id, check_in, check_out, exclude_booking_id=None):
    """Check if a room is available for the given dates."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            query = """SELECT COUNT(*) as cnt FROM bookings 
                       WHERE room_id = %s AND check_in < %s AND check_out > %s AND status = 'confirmed'"""
            params = [room_id, check_out, check_in]
            if exclude_booking_id:
                query += " AND id != %s"
                params.append(exclude_booking_id)
            cur.execute(query, tuple(params))
            result = cur.fetchone()
            return result["cnt"] == 0

# ─── Quick Stats ──────────────────────────────────────────────────────────────

def get_today_status():
    """Get today's occupancy status for both rooms."""
    today = date.today().isoformat()
    with get_connection() as conn:
        with conn.cursor() as cur:
            results = {}
            for room in ROOMS:
                cur.execute(
                    """SELECT * FROM bookings 
                       WHERE room_id = %s AND check_in <= %s AND check_out > %s AND status = 'confirmed'
                       ORDER BY check_in LIMIT 1""",
                    (room["id"], today, today),
                )
                booking = cur.fetchone()
                results[room["id"]] = dict(booking) if booking else None
            return results

def get_upcoming_bookings(days=7):
    """Get bookings starting within the next N days."""
    today = date.today()
    future = (today + timedelta(days=days)).isoformat()
    return get_bookings(start_date=today.isoformat(), end_date=future)

# ─── iCal Sources CRUD ────────────────────────────────────────────────────────

def add_ical_source(room_id, platform, ical_url, auto_sync=1):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO ical_sources (room_id, platform, ical_url, auto_sync) VALUES (%s, %s, %s, %s) RETURNING id",
                (room_id, platform, ical_url, auto_sync),
            )
            return cur.fetchone()["id"]

def get_ical_sources(room_id=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if room_id:
                cur.execute(
                    """SELECT s.*, r.name as room_name FROM ical_sources s 
                       JOIN rooms r ON s.room_id = r.id WHERE s.room_id = %s ORDER BY s.platform""",
                    (room_id,),
                )
                return cur.fetchall()
            
            cur.execute(
                """SELECT s.*, r.name as room_name FROM ical_sources s 
                   JOIN rooms r ON s.room_id = r.id ORDER BY r.name, s.platform"""
            )
            return cur.fetchall()

def update_ical_source_status(source_id, status, last_synced=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if last_synced:
                cur.execute(
                    "UPDATE ical_sources SET sync_status=%s, last_synced=%s WHERE id=%s",
                    (status, last_synced, source_id),
                )
            else:
                cur.execute(
                    "UPDATE ical_sources SET sync_status=%s WHERE id=%s",
                    (status, source_id),
                )

def delete_ical_source(source_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM ical_sources WHERE id = %s", (source_id,))

# ─── Sync Log ─────────────────────────────────────────────────────────────────

def add_sync_log(ical_source_id, action, status, message="", events_count=0):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO sync_log (ical_source_id, action, status, message, events_count) VALUES (%s, %s, %s, %s, %s)",
                (ical_source_id, action, status, message, events_count),
            )

def get_sync_logs(limit=20):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT sl.*, s.platform, r.name as room_name 
                   FROM sync_log sl 
                   LEFT JOIN ical_sources s ON sl.ical_source_id = s.id
                   LEFT JOIN rooms r ON s.room_id = r.id
                   ORDER BY sl.synced_at DESC LIMIT %s""",
                (limit,),
            )
            return cur.fetchall()

# ─── Seed Demo Data ───────────────────────────────────────────────────────────

def seed_demo_data():
    """Insert demo bookings if the database is empty."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as c FROM bookings")
            count = cur.fetchone()["c"]
            if count > 0:
                return False

    today = date.today()
    demo_bookings = [
        (1, "คุณสมชาย", "081-234-5678", today - timedelta(days=1), today + timedelta(days=2), "agoda", ""),
        (2, "คุณนิดา", "089-876-5432", today + timedelta(days=1), today + timedelta(days=4), "booking", ""),
        (1, "Mr. James", "092-111-2222", today + timedelta(days=4), today + timedelta(days=7), "direct", ""),
        (2, "คุณวิชัย", "063-333-4444", today + timedelta(days=5), today + timedelta(days=8), "agoda", "Late check-in"),
    ]
    for rid, guest, phone, ci, co, src, note in demo_bookings:
        create_booking(rid, guest, phone, ci.isoformat(), co.isoformat(), src, note)
    return True
