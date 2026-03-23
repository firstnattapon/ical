"""
🏨 Hana House — Simplified Room Manager
Calendar-First, Single-Page Dashboard for 2 Standard Rooms.
1-Click Booking. Zero Learning Curve.
"""
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from calendar import monthrange
import database as db
from streamlit_autorefresh import st_autorefresh

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Hana House",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 🔄 Autorefresh UI every 15 minutes (900,000 milliseconds)
# to fetch data that was synced in the background
st_autorefresh(interval=15 * 60 * 1000, key="data_refresh")

# ─── Init DB ──────────────────────────────────────────────────────────────────
db.init_db()
db.seed_demo_data()

# ─── Premium CSS ──────────────────────────────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Base ── */
:root {
    --bg: #0B0F19;
    --surface: #141926;
    --surface2: #1C2333;
    --surface3: #242D3F;
    --accent1: #818CF8;
    --accent2: #6366F1;
    --green: #34D399;
    --green-dim: #34D39933;
    --red: #F87171;
    --red-dim: #F8717133;
    --orange: #FBBF24;
    --blue: #60A5FA;
    --text: #F1F5F9;
    --text2: #94A3B8;
    --text3: #64748B;
    --border: #1E293B;
    --room1: #818CF8;
    --room2: #34D399;
}

.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg) !important;
}

/* Hide Streamlit defaults */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"] { display: none !important; }

/* ── Hero Header ── */
.hero-header {
    background: linear-gradient(135deg, #141926 0%, #1C1B4B 50%, #141926 100%);
    border: 1px solid #818CF822;
    border-radius: 20px;
    padding: 24px 32px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: relative;
    overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, #818CF811 0%, transparent 70%);
    pointer-events: none;
}
.hero-title {
    font-size: 1.6rem;
    font-weight: 800;
    background: linear-gradient(135deg, #818CF8, #34D399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    letter-spacing: -0.5px;
}
.hero-sub {
    font-size: 0.85rem;
    color: #94A3B8;
    margin-top: 2px;
}

/* ── Status Cards ── */
.status-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 24px;
}
.room-status {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 20px 24px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}
.room-status:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.3);
}
.room-status::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
}
.room-status.room1::after { background: linear-gradient(90deg, #818CF8, #6366F1); }
.room-status.room2::after { background: linear-gradient(90deg, #34D399, #10B981); }

.room-name {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
}
.room-name.r1 { color: #818CF8; }
.room-name.r2 { color: #34D399; }

.guest-name {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 4px;
}
.guest-phone {
    font-size: 0.85rem;
    color: var(--text2);
}
.guest-dates {
    font-size: 0.8rem;
    color: var(--text3);
    margin-top: 6px;
}
.status-vacant {
    font-size: 1rem;
    font-weight: 600;
    color: var(--green);
}
.source-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 6px;
}
.pill-agoda { background: #FF385C18; color: #FF6B8A; border: 1px solid #FF385C33; }
.pill-booking { background: #003B9518; color: #60A5FA; border: 1px solid #4A9FF533; }
.pill-direct { background: #34D39918; color: #34D399; border: 1px solid #34D39933; }

/* ── Calendar Grid ── */
.cal-header {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text);
    margin: 20px 0 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.cal-grid {
    display: grid;
    gap: 3px;
    margin-bottom: 6px;
}
.cal-day-header {
    font-size: 0.65rem;
    font-weight: 600;
    color: var(--text3);
    text-align: center;
    padding: 4px 0;
}
.cal-cell {
    position: relative;
    min-height: 38px;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    cursor: pointer;
    transition: all 0.2s ease;
    border: 1px solid transparent;
}
.cal-cell:hover {
    transform: scale(1.08);
    z-index: 2;
}
.cal-empty {
    background: transparent;
    cursor: default;
}
.cal-empty:hover { transform: none; }
.cal-vacant {
    background: var(--surface);
    border-color: var(--border);
    color: var(--text2);
}
.cal-vacant:hover {
    border-color: var(--accent1);
    background: #818CF811;
    box-shadow: 0 0 12px #818CF822;
}
.cal-booked-1 {
    background: #818CF818;
    border-color: #818CF844;
    color: #818CF8;
}
.cal-booked-2 {
    background: #34D39918;
    border-color: #34D39944;
    color: #34D399;
}
.cal-booked-both {
    background: linear-gradient(135deg, #818CF818, #34D39918);
    border-color: #FBBF2444;
    color: #FBBF24;
}
.cal-today {
    box-shadow: 0 0 0 2px #818CF8 !important;
}
.cal-past {
    opacity: 0.4;
}
.cal-daynum {
    font-weight: 600;
    font-size: 0.8rem;
}
.cal-indicator {
    font-size: 0.55rem;
    margin-top: 1px;
    font-weight: 600;
}
.cal-dot-row {
    display: flex;
    gap: 3px;
    margin-top: 2px;
}
.cal-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
}

/* ── Room Timeline ── */
.timeline-container {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 20px;
}
.timeline-label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}
.timeline-label.r1 { color: #818CF8; }
.timeline-label.r2 { color: #34D399; }

/* ── Booking List ── */
.booking-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.2s ease;
}
.booking-card:hover {
    border-color: var(--accent1);
    background: var(--surface2);
}
.booking-info {
    flex: 1;
}
.booking-guest {
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--text);
}
.booking-meta {
    font-size: 0.8rem;
    color: var(--text2);
    margin-top: 2px;
}

/* ── Section Title ── */
.section-title {
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--accent1);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin: 28px 0 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #818CF822;
}

/* ── Quick Action Button ── */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #818CF8, #6366F1) !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    padding: 12px 24px !important;
    transition: all 0.3s ease !important;
}
div.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35) !important;
}

/* ── Form styling ── */
[data-testid="stForm"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: var(--surface);
    border-radius: 12px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-weight: 500;
    font-size: 0.85rem;
}

/* ── Dialog ── */
[data-testid="stModal"] > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 20px !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--surface3); border-radius: 3px; }

div[data-testid="stHorizontalBlock"] { gap: 12px; }
</style>""", unsafe_allow_html=True)


# ─── Helper Functions ─────────────────────────────────────────────────────────

def source_pill(src):
    cls = {"agoda": "pill-agoda", "booking": "pill-booking"}.get(src, "pill-direct")
    return f'<span class="source-pill {cls}">{src}</span>'


def get_month_dates(ref_date):
    """Return first day, last day, and total days for a month."""
    first = ref_date.replace(day=1)
    _, days = monthrange(first.year, first.month)
    last = first.replace(day=days)
    return first, last, days


# ══════════════════════════════════════════════════════════════════════════════
# 🏠 HERO HEADER
# ══════════════════════════════════════════════════════════════════════════════
today = date.today()

st.markdown(f"""
<div class="hero-header">
    <div>
        <div class="hero-title">🏨 Hana House</div>
        <div class="hero-sub">Room Manager — {today.strftime('%A, %d %B %Y')}</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 📊 TODAY'S STATUS — 2 Room Cards
# ══════════════════════════════════════════════════════════════════════════════
today_status = db.get_today_status()
rooms = db.get_rooms()

cols_status = st.columns(2)
for idx, room in enumerate(rooms):
    booking = today_status.get(room["id"])
    room_cls = "room1" if idx == 0 else "room2"
    name_cls = "r1" if idx == 0 else "r2"

    with cols_status[idx]:
        if booking:
            pill = source_pill(booking.get("source", "direct"))
            phone_display = booking.get("guest_phone", "") or "—"
            ci = booking.get("check_in", "")
            co = booking.get("check_out", "")
            st.markdown(f"""
            <div class="room-status {room_cls}">
                <div class="room-name {name_cls}">{room['name']}</div>
                <div class="guest-name">👤 {booking['guest_name']}</div>
                <div class="guest-phone">📱 {phone_display}</div>
                <div class="guest-dates">📅 {ci} → {co} {pill}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="room-status {room_cls}">
                <div class="room-name {name_cls}">{room['name']}</div>
                <div class="status-vacant">✅ ว่าง (Available)</div>
                <div class="guest-dates">ไม่มีผู้เข้าพักวันนี้</div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 📅 CALENDAR VIEW — 2-Row Horizontal Timeline
# ══════════════════════════════════════════════════════════════════════════════

# Month navigation
st.markdown('<div class="section-title">📅 ปฏิทินการจอง</div>', unsafe_allow_html=True)

nav_cols = st.columns([1, 2, 1, 4])
with nav_cols[0]:
    if st.button("◀ เดือนก่อน", use_container_width=True, key="prev_month"):
        ref = st.session_state.get("cal_ref", today)
        new_ref = (ref.replace(day=1) - timedelta(days=1)).replace(day=1)
        st.session_state["cal_ref"] = new_ref
        st.rerun()
with nav_cols[2]:
    if st.button("เดือนถัดไป ▶", use_container_width=True, key="next_month"):
        ref = st.session_state.get("cal_ref", today)
        _, days = monthrange(ref.year, ref.month)
        new_ref = ref.replace(day=days) + timedelta(days=1)
        st.session_state["cal_ref"] = new_ref
        st.rerun()

cal_ref = st.session_state.get("cal_ref", today)
month_first, month_last, total_days = get_month_dates(cal_ref)

with nav_cols[1]:
    st.markdown(f"<div style='text-align:center;font-size:1.2rem;font-weight:700;color:#F1F5F9;padding:6px 0'>"
                f"{month_first.strftime('%B %Y')}</div>", unsafe_allow_html=True)

# Get bookings for this month
month_bookings = db.get_bookings(
    start_date=month_first.isoformat(),
    end_date=(month_last + timedelta(days=1)).isoformat()
)

# Build booking lookup: date → set of room_ids
booking_map = {}  # date_str → {room_id: booking_info}
for b in month_bookings:
    ci = date.fromisoformat(b["check_in"])
    co = date.fromisoformat(b["check_out"])
    d = max(ci, month_first)
    end = min(co, month_last + timedelta(days=1))
    while d < end:
        key = d.isoformat()
        if key not in booking_map:
            booking_map[key] = {}
        booking_map[key][b["room_id"]] = {
            "guest": b["guest_name"],
            "source": b["source"] if b["source"] else "direct",
        }
        d += timedelta(days=1)

# Build calendar grid
weekday_offset = month_first.weekday()  # Monday = 0
day_names_th = ["จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส.", "อา."]

# Determine number of weeks needed
total_cells = weekday_offset + total_days
num_weeks = (total_cells + 6) // 7

grid_cols = f"repeat(7, 1fr)"
calendar_html = f'<div class="cal-grid" style="grid-template-columns: {grid_cols};">'

# Day headers
for dn in day_names_th:
    calendar_html += f'<div class="cal-day-header">{dn}</div>'

# Day cells
for cell_idx in range(num_weeks * 7):
    day_num = cell_idx - weekday_offset + 1
    if day_num < 1 or day_num > total_days:
        calendar_html += '<div class="cal-cell cal-empty"></div>'
        continue

    cell_date = month_first.replace(day=day_num)
    date_key = cell_date.isoformat()
    is_today = cell_date == today
    is_past = cell_date < today

    booked_rooms = booking_map.get(date_key, {})
    r1_booked = 1 in booked_rooms
    r2_booked = 2 in booked_rooms

    # Determine cell class
    extra_cls = ""
    if is_today:
        extra_cls += " cal-today"
    if is_past:
        extra_cls += " cal-past"

    if r1_booked and r2_booked:
        cell_cls = "cal-booked-both"
        indicator = "เต็ม"
    elif r1_booked:
        cell_cls = "cal-booked-1"
        indicator = "ห้อง1"
    elif r2_booked:
        cell_cls = "cal-booked-2"
        indicator = "ห้อง2"
    else:
        cell_cls = "cal-vacant"
        indicator = ""

    # Dots for rooms
    dots_html = '<div class="cal-dot-row">'
    if r1_booked:
        dots_html += '<div class="cal-dot" style="background:#818CF8"></div>'
    if r2_booked:
        dots_html += '<div class="cal-dot" style="background:#34D399"></div>'
    dots_html += '</div>'

    tooltip = f"{cell_date.strftime('%d %b')}\\n"
    if r1_booked:
        tooltip += f"ห้อง1: {booked_rooms[1]['guest']}\\n"
    if r2_booked:
        tooltip += f"ห้อง2: {booked_rooms[2]['guest']}"
    if not r1_booked and not r2_booked:
        tooltip += "ว่างทั้ง 2 ห้อง"

    calendar_html += (
        f'<div class="cal-cell {cell_cls}{extra_cls}" title="{tooltip}">'
        f'<div class="cal-daynum">{day_num}</div>'
        f'{dots_html}'
        f'</div>'
    )

calendar_html += '</div>'

# Legend
legend_html = """
<div style="display:flex;gap:16px;margin:8px 0 0;flex-wrap:wrap">
    <div style="display:flex;align-items:center;gap:5px;font-size:0.75rem;color:#94A3B8">
        <div style="width:12px;height:12px;border-radius:3px;background:#141926;border:1px solid #1E293B"></div> ว่าง
    </div>
    <div style="display:flex;align-items:center;gap:5px;font-size:0.75rem;color:#94A3B8">
        <div style="width:12px;height:12px;border-radius:3px;background:#818CF818;border:1px solid #818CF844"></div> ห้อง 1
    </div>
    <div style="display:flex;align-items:center;gap:5px;font-size:0.75rem;color:#94A3B8">
        <div style="width:12px;height:12px;border-radius:3px;background:#34D39918;border:1px solid #34D39944"></div> ห้อง 2
    </div>
    <div style="display:flex;align-items:center;gap:5px;font-size:0.75rem;color:#94A3B8">
        <div style="width:12px;height:12px;border-radius:3px;background:linear-gradient(135deg,#818CF818,#34D39918);border:1px solid #FBBF2444"></div> เต็ม
    </div>
    <div style="display:flex;align-items:center;gap:5px;font-size:0.75rem;color:#94A3B8">
        <div style="width:12px;height:12px;border-radius:3px;box-shadow:0 0 0 2px #818CF8"></div> วันนี้
    </div>
</div>
"""

st.markdown(calendar_html + legend_html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ➕ QUICK BOOKING — 1-Click Action
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="section-title">➕ จองห้องพัก</div>', unsafe_allow_html=True)

with st.form("quick_booking", clear_on_submit=True):
    fc1, fc2 = st.columns(2)
    with fc1:
        sel_room = st.selectbox(
            "เลือกห้อง",
            options=[r["id"] for r in rooms],
            format_func=lambda x: next(r["name"] for r in rooms if r["id"] == x),
            key="book_room"
        )
    with fc2:
        source = st.selectbox("แหล่งที่มา", ["direct", "agoda", "booking"], key="book_source")

    gc1, gc2 = st.columns(2)
    with gc1:
        guest_name = st.text_input("ชื่อผู้เข้าพัก", placeholder="เช่น คุณสมชาย", key="book_name")
    with gc2:
        guest_phone = st.text_input("เบอร์โทร", placeholder="081-xxx-xxxx", key="book_phone")

    dc1, dc2 = st.columns(2)
    with dc1:
        check_in = st.date_input("วันเข้าพัก", today, key="book_ci")
    with dc2:
        check_out = st.date_input("วันออก", today + timedelta(days=2), key="book_co")

    notes = st.text_input("หมายเหตุ (ไม่จำเป็น)", placeholder="เช่น Late check-in", key="book_notes")

    submitted = st.form_submit_button("✅ บันทึกการจอง", use_container_width=True, type="primary")
    if submitted:
        if not guest_name:
            st.error("⚠️ กรุณากรอกชื่อผู้เข้าพัก")
        elif check_in >= check_out:
            st.error("⚠️ วันออกต้องหลังวันเข้าพัก")
        elif not db.check_availability(sel_room, check_in.isoformat(), check_out.isoformat()):
            st.error("⚠️ ห้องไม่ว่างในช่วงวันที่เลือก!")
        else:
            db.create_booking(
                sel_room, guest_name, guest_phone,
                check_in.isoformat(), check_out.isoformat(),
                source, notes
            )
            st.success(f"✅ จองสำเร็จ! {guest_name} → {check_in} ถึง {check_out}")
            st.balloons()
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# 📋 UPCOMING BOOKINGS LIST
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="section-title">📋 การจองที่กำลังจะมาถึง</div>', unsafe_allow_html=True)

upcoming = db.get_bookings(
    start_date=(today - timedelta(days=1)).isoformat(),
    end_date=(today + timedelta(days=30)).isoformat()
)

if upcoming:
    for b in upcoming:
        room_color = b["room_color"]
        pill = source_pill(b["source"] if b["source"] else "direct")
        ci = b["check_in"]
        co = b["check_out"]
        nights = (date.fromisoformat(co) - date.fromisoformat(ci)).days
        phone = (b["guest_phone"] or "") if "guest_phone" in b.keys() else ""
        phone_display = f" · 📱 {phone}" if phone else ""

        notes_text = f' · 📝 {b["notes"]}' if b["notes"] else ''
        card_html = (
            f'<div class="booking-card" style="border-left: 3px solid {room_color}">'
            f'<div class="booking-info">'
            f'<div class="booking-guest">👤 {b["guest_name"]}{phone_display} {pill}</div>'
            f'<div class="booking-meta">'
            f'🏠 {b["room_name"]} · 📅 {ci} → {co} ({nights} คืน){notes_text}'
            f'</div></div></div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)


    # Cancel booking section
    with st.expander("🗑️ ยกเลิกการจอง"):
        booking_options = {f"{b['guest_name']} — {b['room_name']} ({b['check_in']} → {b['check_out']})": b["id"] for b in upcoming}
        if booking_options:
            selected_cancel = st.selectbox("เลือกการจองที่ต้องการยกเลิก", list(booking_options.keys()), key="cancel_select")
            c1, c2 = st.columns([3, 1])
            with c2:
                if st.button("❌ ยกเลิก", type="primary", key="cancel_btn", use_container_width=True):
                    db.cancel_booking(booking_options[selected_cancel])
                    st.success("ยกเลิกเรียบร้อย!")
                    st.rerun()
else:
    st.info("ยังไม่มีการจองในช่วง 30 วันข้างหน้า")


# ══════════════════════════════════════════════════════════════════════════════
# 🔄 iCal SYNC — Compact Section
# ══════════════════════════════════════════════════════════════════════════════

with st.expander("🔄 iCal Sync (Agoda / Booking.com)"):
    import ical_engine as ical

    tab_import, tab_export = st.tabs(["📥 นำเข้า", "📤 ส่งออก"])

    with tab_import:
        sources = db.get_ical_sources()
        if sources:
            for s in sources:
                sc1, sc2, sc3 = st.columns([4, 1, 1])
                sc1.markdown(f"**{s['room_name']}** — {s['platform'].upper()}")
                status_color = "#34D399" if s["sync_status"] == "success" else "#F87171"
                sc2.markdown(f"<span style='color:{status_color};font-size:0.8rem'>{s['sync_status']}</span>", unsafe_allow_html=True)
                if sc3.button("🔄", key=f"sync_{s['id']}"):
                    with st.spinner("Syncing..."):
                        result = ical.sync_ical_source(s["id"])
                        if result["status"] == "success":
                            st.success(result["message"])
                        else:
                            st.error(result["message"])
                    st.rerun()
            if st.button("🔄 Sync ทั้งหมด", use_container_width=True, type="primary"):
                with st.spinner("Syncing all..."):
                    results = ical.sync_all_sources()
                    for r in results:
                        if r["status"] == "success":
                            st.success(f"✅ {r['room_name']}: {r['message']}")
                        else:
                            st.error(f"❌ {r['room_name']}: {r['message']}")
                st.rerun()

        st.divider()
        st.markdown("**➕ เพิ่มแหล่ง iCal**")
        with st.form("add_ical"):
            rm = st.selectbox(
                "ห้อง",
                options=[r["id"] for r in rooms],
                format_func=lambda x: next(r["name"] for r in rooms if r["id"] == x),
            )
            platform = st.selectbox("แพลตฟอร์ม", ["agoda", "booking", "airbnb"])
            url = st.text_input("iCal URL", placeholder="https://www.agoda.com/ical/...")
            if st.form_submit_button("➕ เพิ่ม", use_container_width=True):
                if url:
                    db.add_ical_source(rm, platform, url)
                    st.success("✅ เพิ่มเรียบร้อย!")
                    st.rerun()
                else:
                    st.error("กรุณากรอก URL")

    with tab_export:
        st.info("💡 ดาวน์โหลดไฟล์ .ics แล้วนำไปวางใน Agoda/Booking Extranet → Calendar → Import")
        for room in rooms:
            ical_text = ical.generate_ical_for_room(room["id"])
            if ical_text:
                room_bookings = db.get_bookings(room_id=room["id"])
                st.download_button(
                    f"⬇️ {room['name']} ({len(room_bookings)} bookings)",
                    ical_text,
                    file_name=f"hana_room_{room['id']}.ics",
                    mime="text/calendar",
                    key=f"dl_{room['id']}",
                    use_container_width=True,
                )
            else:
                st.caption(f"{room['name']}: ไม่มีการจอง")


# ══════════════════════════════════════════════════════════════════════════════
# Footer
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style='text-align:center;padding:32px 0 16px;color:#475569;font-size:0.75rem'>
    🏨 Hana House Room Manager v2.0 — Calendar-First Design<br>
    2 Standard Rooms · 1-Click Booking · Zero Complexity
</div>
""", unsafe_allow_html=True)
