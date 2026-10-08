#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s497.py -- kit S497_RING_LIST: builds the two programs the installer places, from the LIVE bytes.

    python3 -B make_s497.py <folder holding the live ring_outcome.py and portal.py> <out folder>
    python3 -B make_s497.py --check <live folder> <folder to compare>     builds in memory, compares, writes nothing
    python3 -B make_s497.py --pins                                         FROM and TO md5 of each file

How it works (the estate's rules, each paid for):
  * each live file's md5 is held against its FROM pin before anything else (rule 1: pin before touching);
  * every edit is an exact piece of the live text that must occur EXACTLY ONCE -- else it stops and says which (rule 2,
    F-472: built on the real bytes, never from an inferred anchor; the live file is never re-typed);
  * the new text is built IN MEMORY and checked there -- it compiles, it parses as Python 3.8, its markers are present,
    the tile sits where it should, its md5 is the TO pin -- and only then is any file opened for writing (F-792);
  * it never writes into the folder it reads from.
tile_grants.json is not built here: apply_s497.py edits it by exact text (a .json cannot ride in the kit: .gitignore).
"""
import ast
import hashlib
import os
import sys
import warnings

FROM = {"ring_outcome.py": "495b0ada681cda359a1a621a22f4efa5", "portal.py": "63df9d49672e19e878245b30c0455bef"}
TO = {"ring_outcome.py": "7cb60aad2df80f87fdc4a674ebe7ee45", "portal.py": "f8b059f61fa8b885f024f4f4ce73e4f2"}

# ======================================================================================= the new text: ring_outcome.py
RO_HEAD = r'''#
# S497_RING_LIST (session 302, 08-Oct-2026) -- D693, the owner, 07-Oct-2026: "what happens after they click the book
# appointment button is nowhere visible to them ... they get to see it as a list whose appointment was booked by whom
# at what time"; then "tabular ... updated from the Docterz exports confirming that these patient turned up, and
# persist for the no shows distinctly"; then "full mobile numbers, weekdays in english, leave scope for whatsaap".
#   /portal/ring/list   ONE table in three parts: Nahi aaye (stays, whatever the span, until the patient comes or a
#                       person presses one of two buttons) . Aane baaki . Aa gaye (filled by itself from patient_visit
#                       in finance.db, opened READ-ONLY; nobody ticks). Spans Aaj . 7 din . 30 din.
#   the card after 'Appointment book ho gaya'  one OPTIONAL tap, 'Kis din aayenge?' (Aaj . Kal . Parso . Aur din).
#   no-show            from the day AFTER the promised day; with no day, after the booking day + wait_days (3, a setting)
#                      -- and ONLY once the visits on the server reach that day (can_judge); till then Aane baaki.
#   the floor          nothing booked before the day the list was first turned on is followed (floor_day); he may
#                      move that date earlier on his box, never before 01-Oct-2026 (HARD_FLOOR).
#   WhatsApp           room only: a column, a place on the card, three empty columns in the store. Nothing is sent.
#   installed OFF for staff: the doctor sees the page and turns it on there; until then the staff's card is the old one.
# The store gains columns on `outcome` (appt_day, appt_state, recalls, wa_state ...) and two small tables (kv, appt_event);
# nothing that was there is changed. The tap, the mirror into the tracker and the sweeper are untouched.
# It also mends F-797 (a name with the letters S-I-D was broken on the tap's page) -- see _page().
'''

RO_COLS = r'''# S497: what the after-call list adds to `outcome`. Added by lazy ALTER, never dropped, never retyped (the estate's own
# pattern, finance_patient_sync.ensure_columns). appt_day = the promised day 'YYYY-MM-DD' in India time ('' = none given);
# appt_state = 'closed' once a person pressed 'Ab nahi aayenge'; recalls / recall_at = 'Phir call kiya' presses;
# wa_* = the WhatsApp message's state -- ROOM ONLY, nothing writes them.
S497_COLS = (("appt_day", "TEXT"), ("appt_day_by", "TEXT"), ("appt_day_at", "TEXT"),
             ("appt_state", "TEXT"), ("appt_state_by", "TEXT"), ("appt_state_at", "TEXT"),
             ("recalls", "INTEGER DEFAULT 0"), ("recall_at", "TEXT"),
             ("wa_state", "TEXT"), ("wa_at", "TEXT"), ("wa_ref", "TEXT"))


def _s497_columns(con):
    have = {r[1] for r in con.execute("PRAGMA table_info(outcome)")}
    for name, typ in S497_COLS:
        if name not in have:
            try:
                con.execute("ALTER TABLE outcome ADD COLUMN %s %s" % (name, typ))
            except sqlite3.OperationalError:
                pass                             # the other service added it between the look and the ALTER


'''

RO_MAIN = r'''# ------------------------------------------------------------------ S497: the after-call list (tile 'Call ke baad')
# D693 (the owner, 07-Oct-2026). One table in three parts -- Nahi aaye, Aane baaki, Aa gaye -- and one optional tap on
# the card after 'Appointment book ho gaya'. THE SPECIFICATION IS HIS FINAL MOCK-UP: every staff word and every inline
# style below is copied from it. Come-or-not is read from patient_visit (finance.db, read-only); nobody ticks.
LIST_TILE = "Call ke baad"                       # the tile's name in portal.py and tile_grants.json, byte for byte
GRANTS_FILE = os.environ.get("TILE_GRANTS_FILE", os.path.join(rc.PORTAL_DIR, "tile_grants.json"))
APPT_CODE = "appointment_booked"
WAIT_DAYS_DEFAULT = 3                            # no day given: wait this many days after the booking day (setting wait_days)
SPANS = (("aaj", "Aaj", 1), ("7", "7 din", 7), ("30", "30 din", 30))
SPAN_DEFAULT = "7"
HARD_FLOOR = "2026-10-01"                        # no appointment booked before this day is ever followed (his ruling, 08-Oct)
WA_ENABLED = False                               # WhatsApp to the patient: ROOM ONLY (D693 point 6). Nothing here sends.
_MON = ("", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_DOW = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")        # date.weekday(): Monday is 0. English, his word.
_ISO_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# --- the staff's words (Roman Hinglish). The first group is the mock-up's, letter for letter. ---
T_TITLE = "Call ke baad — appointment list"
T_NOSHOW = "Nahi aaye"
T_DUE = "Aane baaki"
T_CAME = "Aa gaye"
T_NOSHOW_H = "Nahi aaye — appointment liya tha, Docterz mein visit nahi mili"
T_NOSHOW_NOTE = "Yeh line tab tak yahin rahegi jab tak mareez aa na jaye ya aap neeche ka ek button na dabayein"
T_DUE_H = "Aane baaki — din abhi aaya nahi ya aaj hai"
T_CAME_H = "Aa gaye — Docterz ke export se pakka"
T_CAME_NOTE = "Yahan kisi ko kuch tick nahi karna — yeh apne aap bharta hai"
T_NEW = "Naya number"
T_NEW_SUB = "Docterz mein abhi koi record nahi"
T_WAS_NEW = "call ke samay naya number tha"
T_NO_DAY = "din nahi likha"
T_WA_BTN = "WhatsApp message"
T_WA_OFF = "jald — abhi band"
T_RECALL = "Phir call kiya — naya din"
T_CLOSE = "Ab nahi aayenge"
T_CARD_DONE = "Likh gaya — Appointment book ho gaya"
T_CARD_ASK = "Kis din aayenge?"
T_DAYS = ("Aaj", "Kal", "Parso")
T_OTHER = "Aur din chuniye"
T_CARD_NOTE = "Note (chahein to)"
T_CARD_WA = "Mareez ko WhatsApp par appointment ka message"
T_CARD_WA_OFF = "Jald — abhi band. Chalu hone par din chunte hi clinic ke WhatsApp number se jayega."
T_CARD_LINK = "Aaj ki list dekho"
T_HOW = ("Call ke baad notification par “Appointment book ho gaya” dabate hi mareez “Aane baaki” mein aa jata hai.",
         "Docterz ka roz ka export aate hi jis mareez ki visit mil jati hai, woh apne aap “Aa gaye” mein chala jata hai.",
         "WhatsApp: mareez ko appointment ka message clinic ke WhatsApp number se bhejne ki jagah rakhi gayi hai. "
         "Abhi band hai; chalu hone par yahin se jayega aur “bheja gaya” yahin dikhega.")
# --- not on the mock-up: said only when something is off or missing (the assistant's words, kept as few as possible) ---
T_OFF = "Yeh list abhi band hai. Dr sahab chalu karenge."
T_DENIED = "Yeh list aapke login ke liye nahi hai."
T_CANNOT = ("Docterz ka record abhi padha nahi ja saka — kaun aa gaya, yeh abhi pakka nahi ho sakta. "
            "Thodi der mein dobara dekhein.")
T_STORE = "List abhi padhi nahi ja saki. Thodi der mein dobara dekhein."
T_BAD_DAY = "Yeh din nahi chalega — aaj ya aage ka din chuniye."
T_NO_APPT = "Yeh appointment nahi mila."
T_NOT_NOSHOW = "Yeh line ab “Nahi aaye” mein nahi hai. List dobara dekhein."
T_UNSURE = "Docterz se abhi pakka nahi hua"       # overdue, but the visits on the server do not reach its day yet
T_NO_MATCH = "Is number se Docterz ki visit nahi mil sakti"    # a landline, a withheld or an empty number, and no ID
T_VISIT_OF = "%s ki visit"                       # under 'Aaye · date' when the visit is another ID's (a family mobile)


def _ro_db(path=None):
    """The ring store opened READ-ONLY. F-793: a read does not create, sweep or commit -- and with this door it cannot.
    Raises sqlite3.Error when the file is not there."""
    con = sqlite3.connect("file:%s?mode=ro" % (path or DB_FILE), uri=True, timeout=5)
    con.row_factory = sqlite3.Row
    return con


def _kv_get(k, path=None):
    """One setting, or None. A read: an absent store or an absent table answers None and makes nothing."""
    try:
        con = _ro_db(path)
    except sqlite3.Error:
        return None
    try:
        r = con.execute("SELECT v FROM kv WHERE k=?", (k,)).fetchone()
        return r["v"] if r else None
    except sqlite3.Error:
        return None
    finally:
        con.close()


def _kv_set(k, v, by, path=None, now=None):
    init_db(path)
    con = db(path)
    try:
        con.execute("INSERT OR REPLACE INTO kv(k, v, by_whom, at) VALUES(?,?,?,?)", (k, str(v), by or "", _fmt(_ist(now))))
        con.commit()
    finally:
        con.close()


def list_on(path=None):
    """Is the list switched on for staff? OFF until the doctor says so; a store that cannot be read is OFF."""
    return _kv_get("list_on", path) == "1"


def set_list_on(on, by, path=None, now=None):
    """His switch. The FIRST time it is turned on, that India day is written under its own key -- once: no later
    turn of the switch moves it (INSERT OR IGNORE). Both rows go in one commit."""
    t = _ist(now)
    init_db(path)
    con = db(path)
    try:
        if on:
            con.execute("INSERT OR IGNORE INTO kv(k, v, by_whom, at) VALUES('switch_on_day',?,?,?)", (t.date().isoformat(), by or "", _fmt(t)))
        con.execute("INSERT OR REPLACE INTO kv(k, v, by_whom, at) VALUES('list_on',?,?,?)", ("1" if on else "0", by or "", _fmt(t)))
        con.commit()
    finally:
        con.close()


def switch_on_day(path=None):
    """The India day the list was FIRST turned on for staff, or None while it never has been."""
    return _day(_kv_get("switch_on_day", path))


def wait_days(path=None):
    """How many days a booking with no day waits before it is a no-show. A setting; 3 unless he changes it."""
    try:
        n = int(_kv_get("wait_days", path) or WAIT_DAYS_DEFAULT)
    except (TypeError, ValueError):
        n = WAIT_DAYS_DEFAULT
    return n if 1 <= n <= 30 else WAIT_DAYS_DEFAULT


def wait_days_ok(n):
    """A wait the box may hold: a whole number of days, 1 to 30. Asks only; writes nothing."""
    try:
        return 1 <= int(n) <= 30
    except (TypeError, ValueError):
        return False


def set_wait_days(n, by, path=None, now=None):
    if not wait_days_ok(n):
        return False
    _kv_set("wait_days", int(n), by, path, now)
    return True


def follow_from(path=None):
    """HIS setting 'follow appointments booked on or after': 'YYYY-MM-DD', or '' while he has set none."""
    v = str(_kv_get("follow_from", path) or "")
    return v if _day(v) is not None else ""


def floor_day(path=None, now=None):
    """The first booking day the list follows -- ALWAYS a day; nothing booked before it is shown or can be pressed.
      his setting, when he has set one -- he may put it EARLIER than the switch-on day, never before HARD_FLOOR;
      else the day the list was first turned on for staff, so that no old line meets them on the first morning;
      else (never turned on yet) today: what he is shown is what they would be shown if he turned it on now."""
    hard = _day(HARD_FLOOR)
    own = _day(follow_from(path))
    if own is not None:
        return max(own, hard)
    return max(switch_on_day(path) or _ist(now).date(), hard)


def appt_followed(row, path=None, now=None):
    """Is this appointment one the list follows -- booked on or after the floor?"""
    b = _booked_day(row or {})
    return b is not None and b >= floor_day(path, now)


def follow_from_ok(day):
    """A date the box may hold: '' (his setting taken away), or a real date not before HARD_FLOOR. Asks only."""
    day = str(day or "").strip()
    d = _day(day)
    return not day or (d is not None and day == d.isoformat() and d >= _day(HARD_FLOOR))


def set_follow_from(day, by, path=None, now=None, shown=None):
    """'' takes his setting away (the floor is the switch-on day again). A day before HARD_FLOOR is refused. While he
    has set no date of his own, the date his box was SHOWING (`shown`, sent back by the form), or the day in force
    now, sent back untouched, pins nothing -- so a box opened before India midnight and saved after it cannot make
    yesterday his own date."""
    day = str(day or "").strip()
    if not follow_from_ok(day):
        return False
    if day:
        d = _day(day)
        if not follow_from(path) and (d == floor_day(path, now) or day == str(shown or "").strip()):
            return True
    elif not follow_from(path):
        return True
    _kv_set("follow_from", day, by, path, now)
    return True


def good_id(v):
    """An appointment's id as a request gives it: a whole number (or its digits), 0 < id < 2**63 -- the range SQLite
    can hold. Anything else (a fraction, true/false, a huge number, text) is None, so it never reaches the store."""
    if isinstance(v, bool):
        return None
    if isinstance(v, str) and v.strip().isdigit() and len(v.strip()) <= 19:
        v = int(v.strip())
    return v if isinstance(v, int) and 0 < v < 2 ** 63 else None


def list_holders(grants_file=None):
    """The logins SHOWN the tile 'Call ke baad' by name (tile_grants.json, read fresh; unreadable = nobody). A login
    whose grants MASK the tile is not shown it by the portal, so it does not hold it here either."""
    try:
        with open(grants_file or GRANTS_FILE, "r", encoding="utf-8") as fh:
            g = json.load(fh)
        return {u for u, d in (g.get("users") or {}).items()
                if LIST_TILE in ((d or {}).get("extra") or []) and LIST_TILE not in ((d or {}).get("mask") or [])}
    except Exception:
        return set()


def list_access(who, path=None):
    """'doctor' -- always; 'staff' -- holds the tile and the list is on; 'off' -- holds the tile, the list is off;
    '' -- anyone else. The page, the card's new part and the two buttons all ask here."""
    who = who or {}
    if who.get("role") == "doctor":
        return "doctor"
    if not who.get("user") or who.get("user") not in list_holders():
        return ""
    return "staff" if list_on(path) else "off"


# ------------------------------------------------------------------ S497: days, in India time, in English
def _ist(now=None):
    """The moment to work from, ALWAYS in India time: the clock when none is given; a moment given in another zone is
    moved to India time; one given with no zone is taken as India time. The server's own zone is never asked (F-772)."""
    if now is None:
        return now_ist()
    return now.replace(tzinfo=IST) if now.tzinfo is None else now.astimezone(IST)


def _day(s):
    """'YYYY-MM-DD' -> a date, or None."""
    s = str(s or "")[:10]
    if not _ISO_DAY.match(s):
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def _dm(d):
    """05-Oct"""
    return "%02d-%s" % (d.day, _MON[d.month])


def _dm_dow(d):
    """05-Oct (Mon) -- the weekday in English, from the date itself (never the server's language or clock)."""
    return "%s (%s)" % (_dm(d), _DOW[d.weekday()])


def _dm_far(d, today):
    """05-Oct; with its year when it is more than half a year from today, so an old visit is not read as this year's."""
    return _dm(d) if abs((today - d).days) <= 180 else "%s-%d" % (_dm(d), d.year)


def _booked_day(row):
    """The day (India time) the appointment was filed: when_ist first, the row's own day key if that is damaged."""
    d = _day(row.get("when_ist"))
    if d is None:
        k = str(row.get("day_key") or "")
        if len(k) == 8 and k.isdigit():
            d = _day("%s-%s-%s" % (k[:4], k[4:6], k[6:]))
    return d


def _n_din(n, one, many):
    return "%d %s" % (n, one if n == 1 else many)


def _agent_names():
    """{login: the name the call system holds for it} -- ring_agents.json, read fresh; unreadable = none."""
    try:
        return {str((a or {}).get("user") or "").strip().lower(): str((a or {}).get("name") or "").strip()
                for a in rc.load_agents().values() if (a or {}).get("user") and (a or {}).get("name")}
    except Exception:
        return {}


def _cap(s):
    """'alisha' -> 'Alisha'. A name that already has a capital letter is left exactly as it is."""
    s = str(s or "").strip()
    return s if (not s or s != s.lower()) else " ".join(w[:1].upper() + w[1:] for w in s.split(" "))


def _person(login, handler="", names=None):
    """A person, as a NAME: the one filed with the row; else the one the call system holds for the login; else the
    login with its first letter made a capital. A bare small-letter login is never shown."""
    login, handler = str(login or "").strip(), str(handler or "").strip()
    if handler and handler != login:                           # a name was filed -- 'Shivani' for the login 'shivani' is one
        return _cap(handler)
    names = _agent_names() if names is None else names
    return _cap(names.get(login.lower()) or login or handler)


class _FinancePath(object):
    """ring_common finds the clinic's fingerprint module by putting the finance folder FIRST on the import path. In
    the ring-hook service that is how it has always run; in the portal's process the folder is taken off again on the
    way out, so no later import in the portal can ever be answered from the finance folder."""

    def __enter__(self):
        import sys
        self.had = rc.FINANCE_DIR in sys.path
        return self

    def __exit__(self, *a):
        import sys
        if not self.had:
            while rc.FINANCE_DIR in sys.path:
                sys.path.remove(rc.FINANCE_DIR)
        return False


def _mobile_fp(mobile):
    """The clinic's own salted fingerprint of a mobile ('' when it cannot be made). Never re-implemented here."""
    m10 = rc.mobile10(mobile)
    if not m10:
        return ""
    with _FinancePath():
        return rc._fp(m10) or ""


def _docterz_name(mobile, clinic_id, finance_db=None):
    """A number that was new at the call takes the name and the ID Docterz gives it: asked of the caller lookup the
    ring card already uses (ring_common.lookup_caller, read-only). ('', '') when it has no answer."""
    try:
        with _FinancePath():
            info = rc.lookup_caller(mobile, db_path=finance_db)
    except Exception:
        return "", ""
    ps = info.get("patients") or []
    for p in ps:
        if clinic_id and str(p.get("clinic_id") or "") == str(clinic_id):
            return (p.get("name") or "").strip(), str(p.get("clinic_id") or "")
    if ps and not clinic_id:
        return (ps[0].get("name") or "").strip(), str(ps[0].get("clinic_id") or "")
    return "", ""


# ------------------------------------------------------------------ S497: the visit, from Docterz, read-only
def visits_since(day_iso, today, db_path=None):
    """Every visit dated from day_iso to today, from the table patient_visit ONLY, finance.db opened READ-ONLY.
    Never raises: a finance.db that is absent, locked or not as expected answers ok=False and the page says so."""
    out = {"ok": False, "by_id": {}, "by_fp": {}, "through": None}
    try:
        con = sqlite3.connect("file:%s?mode=ro" % (db_path or rc.FINANCE_DB), uri=True, timeout=3)
    except sqlite3.Error:
        return out
    try:
        top = con.execute("SELECT MAX(visit_date) FROM patient_visit WHERE visit_date<=?", (today.isoformat() + "~",)).fetchone()
        rows = con.execute("SELECT visit_date, clinic_id, mobile_fp FROM patient_visit WHERE visit_date>=? AND visit_date<=? "
                           "ORDER BY visit_date", (day_iso, today.isoformat() + "~")).fetchall()
    except sqlite3.Error:
        return out
    finally:
        con.close()
    out["through"] = _day(top[0]) if (top and top[0] is not None) else None
    if out["through"] is None:
        return out                               # no visit on file, or dates not written YYYY-MM-DD: nothing can be confirmed
    for vd, cid, fp in rows:
        d = _day(vd)
        if d is None or d > today:
            continue
        cid, fp = str(cid or "").strip(), str(fp or "").strip()
        if cid:
            out["by_id"].setdefault(cid, []).append(d)
        if fp:
            out["by_fp"].setdefault(fp, []).append((d, cid))
    out["ok"] = True
    return out


def _ids_on_call(row):
    """Every clinic ID the caller card showed for this number (a family shares a mobile), the filed one first."""
    ids = []
    one = str(row.get("clinic_id") or "").strip()
    if one:
        ids.append(one)
    try:
        for p in (json.loads(row.get("s497_cj") or "{}").get("patients")) or []:
            c = str((p or {}).get("clinic_id") or "").strip()
            if c and c not in ids:
                ids.append(c)
    except Exception:
        pass
    return ids


def _name_on_call(row, clinic_id):
    """The name the caller card showed for one clinic ID of that mobile, or ''."""
    try:
        for p in (json.loads(row.get("s497_cj") or "{}").get("patients")) or []:
            if str((p or {}).get("clinic_id") or "").strip() == str(clinic_id):
                return str((p or {}).get("name") or "").strip()
    except Exception:
        pass
    return ""


def first_visit(row, booked, visits, fp):
    """(day, clinic id, how) of the first visit on or after the booking day, or (None, '', '').
    A caller who was known is looked for by the clinic IDs on the card, then by the same mobile's fingerprint (a family
    member registered at that visit has a new ID); a number that was new, by the fingerprint."""
    best = (None, "", "")
    for cid in _ids_on_call(row):
        for d in visits["by_id"].get(cid, ()):
            if d >= booked and (best[0] is None or d < best[0]):
                best = (d, cid, "id")
    if fp:
        for d, cid in visits["by_fp"].get(fp, ()):
            if d >= booked and (best[0] is None or d < best[0]):
                best = (d, cid, "mobile")
    return best


def appt_state(booked, appt, closed, visit, today, wait):
    """THE RULE (D693 point 7), in one place.
      came    Docterz shows a visit on or after the booking day -- a late one counts, and it wins over everything.
      closed  a person pressed 'Ab nahi aayenge'.
      noshow  the day AFTER the promised day has come and there is no visit; with no day given, the booking day and
              `wait` more days have gone by.
      due     everything else: the day has not come, or is today.
    This is the rule by the calendar alone. list_data() then asks whether a 'noshow' can be SAID yet (can_judge)."""
    if visit is not None:
        return "came"
    if closed:
        return "closed"
    last = appt if appt is not None else booked + timedelta(days=wait)
    return "noshow" if today > last else "due"


def can_judge(last, through):
    """May a line whose last day was `last` be called a no-show? ONLY when the visits on the server reach that day.
    patient_visit keeps no record of WHEN a row was brought in (finance_patient_sync.py writes none, and keeps no
    log table), so 'reach' is the newest visit date on file: through >= last. No readable visit -> never."""
    return through is not None and through >= last


def list_data(span=None, path=None, now=None, finance_db=None, everything=False, floor=None):
    """Everything the list shows. A READ: the ring store and finance.db are both opened read-only and nothing is
    written, made or swept here (F-793). `now` is India time; the walk passes its own.
    A span holds a line booked or re-called within it looking BACK, or promised from today up to as far AHEAD.
    `everything` leaves the span out (a press asks where ONE line stands); `floor` is a what-if for the installer's
    last lines. Neither is offered to a page."""
    t = _ist(now)
    today = t.date()
    key = span if span in [s[0] for s in SPANS] else SPAN_DEFAULT
    reach = [s[2] for s in SPANS if s[0] == key][0] - 1
    back, ahead = today - timedelta(days=reach), today + timedelta(days=reach)
    wait = wait_days(path)
    floor = floor if floor is not None else floor_day(path, now)
    out = {"span": key, "today": today, "wait_days": wait, "follow_from": floor, "switch_on": switch_on_day(path),
           "store_ok": True, "visits_ok": True, "visits_through": None, "noshow": [], "due": [], "came": []}
    try:
        con = _ro_db(path)
    except sqlite3.Error:
        out["store_ok"] = False
        return out
    try:
        raw = [dict(r) for r in con.execute(
            "SELECT o.*, c.caller_json AS s497_cj FROM outcome o LEFT JOIN call c ON c.sid=o.sid "
            "WHERE o.code=? ORDER BY o.when_ist DESC, o.id DESC", (APPT_CODE,))]
    except sqlite3.Error:
        out["store_ok"] = False
        return out
    finally:
        con.close()
    if raw and "appt_day" not in raw[0]:
        out["store_ok"] = False                                # the new columns are made on a page request, never here
        return out
    rows = []
    for r in raw:
        booked = _booked_day(r)
        if booked is None or booked < floor:
            continue                                           # booked before the floor: not followed, not shown
        r["booked"] = booked
        r["appt"] = _day(r.get("appt_day"))
        r["closed"] = (r.get("appt_state") or "") == "closed"
        r["in_span"] = bool(everything or max(booked, _day(r.get("recall_at")) or booked) >= back
                            or (r["appt"] is not None and today <= r["appt"] <= ahead))
        if r["closed"] and not r["in_span"]:
            continue                                           # dealt with long ago: not asked of Docterz again
        rows.append(r)
    v = visits_since(min([r["booked"] for r in rows] or [today]).isoformat(), today, finance_db)
    out["visits_through"] = v["through"]
    out["visits_ok"] = v["ok"]
    through = v["through"] if v["ok"] else None
    fps = {}
    for r in rows:
        m = r.get("mobile") or ""
        m10 = rc.mobile10(m)
        has_id = bool(_ids_on_call(r))
        r["known"] = bool(str(r.get("clinic_id") or "").strip() or str(r.get("patient") or "").strip())
        if m not in fps:
            fps[m] = _mobile_fp(m) if (v["ok"] and m10) else ""
        r["unmatchable"] = not has_id and not m10               # no ID and no mobile to look for: said on THAT line only
        blind = bool(v["ok"] and m10 and not fps[m] and not has_id)
        if blind:
            out["visits_ok"] = False                           # a mobile whose fingerprint could not be made: the page says so
        r["visit"], r["visit_id"], r["visit_by"] = first_visit(r, r["booked"], v, fps[m]) if v["ok"] else (None, "", "")
        r["state"] = appt_state(r["booked"], r["appt"], r["closed"], r["visit"], today, wait)
        r["unsure"] = False
        if r["state"] == "noshow":
            last = r["appt"] if r["appt"] is not None else r["booked"] + timedelta(days=wait)
            if blind or not can_judge(last, through):
                r["state"], r["unsure"] = "due", True          # overdue, but it cannot be SAID yet: Aane baaki, no buttons
        if r["state"] == "noshow":
            r["since"] = (today - (r["appt"] or r["booked"])).days
            out["noshow"].append(r)
        elif r["state"] == "due" and (r["in_span"] or r["unsure"]):
            out["due"].append(r)
        elif r["state"] == "came" and r["in_span"]:
            r["late"] = (r["visit"] - r["appt"]).days if (r["appt"] is not None and r["visit"] > r["appt"]) else 0
            if not r["known"]:
                r["dz_name"], r["dz_id"] = _docterz_name(m, r["visit_id"], finance_db)
                r["dz_id"] = r["dz_id"] or r["visit_id"]
            elif r["visit_id"] and r["visit_id"] != str(r.get("clinic_id") or "").strip():
                r["visit_name"] = _name_on_call(r, r["visit_id"]) or _docterz_name(m, r["visit_id"], finance_db)[0]
            out["came"].append(r)
    return out


def where_now(oid, path=None, now=None, finance_db=None):
    """Where ONE appointment stands this minute: 'noshow', 'due', 'came' -- or '' (closed, before the floor, not there)."""
    d = list_data(None, path, now, finance_db, everything=True)
    for part in ("noshow", "due", "came"):
        if any(r["id"] == oid for r in d[part]):
            return part
    return ""


# ------------------------------------------------------------------ S497: what a person presses
def _appt_row(con, where, arg):
    r = con.execute("SELECT * FROM outcome WHERE %s AND code=? ORDER BY id DESC LIMIT 1" % where, (arg, APPT_CODE)).fetchone()
    return dict(r) if r else None


def _good_day(day, today):
    """A promised day: a real date, today or later, within a year. Else None."""
    d = _day(day)
    if d is None or str(day) != d.isoformat() or d < today or d > today + timedelta(days=366):
        return None
    return d


def _appt_event(con, oid, kind, old, new, by_login, by_name, t):
    """Every press is kept: the earlier promised day is never lost (D693: 'the earlier one kept as history')."""
    con.execute("INSERT INTO appt_event(outcome_id, kind, old_value, new_value, by_login, by_name, at_ist, created_at) "
                "VALUES(?,?,?,?,?,?,?,?)", (oid, kind, old or "", new or "", by_login or "", by_name or "", _fmt(t), int(time.time())))


def set_appt_day(sid, day, by_login, by_name, path=None, now=None, finance_db=None):
    """The card's one optional tap -- Aaj, Kal, Parso or another day ('' takes it back). Returns (ok, msg).
    A line that is standing in Nahi aaye and is given a day here has been CALLED AGAIN: it is written as a recall
    (recall_at, recalls), exactly as the list's own button writes it, so the line is in Aane baaki and not nowhere."""
    t = _ist(now)
    new = ""
    if day:
        d = _good_day(day, t.date())
        if d is None:
            return False, T_BAD_DAY
        new = d.isoformat()
    init_db(path)
    con = db(path)
    try:
        o = _appt_row(con, "sid=?", sid)
    finally:
        con.close()
    if not o or (o.get("appt_state") or "") == "closed" or not appt_followed(o, path, now):
        return False, T_NO_APPT
    old = o.get("appt_day") or ""
    if old == new:
        return True, "ok"
    again = bool(new) and where_now(o["id"], path, now, finance_db) == "noshow"
    con = db(path)
    try:
        if again:
            cur = con.execute("UPDATE outcome SET appt_day=?, appt_day_by=?, appt_day_at=?, recalls=COALESCE(recalls,0)+1, recall_at=? "
                              "WHERE id=? AND COALESCE(appt_day,'')=? AND COALESCE(recalls,0)=? AND COALESCE(appt_state,'')=''",
                              (new, by_login or "", _fmt(t), _fmt(t), o["id"], old, int(o.get("recalls") or 0)))
        else:
            cur = con.execute("UPDATE outcome SET appt_day=?, appt_day_by=?, appt_day_at=? WHERE id=? AND COALESCE(appt_day,'')=? "
                              "AND COALESCE(appt_state,'')=''", (new, by_login or "", _fmt(t), o["id"], old))
        if cur.rowcount != 1:
            return False, T_STORE                              # another press changed the line in the same moment
        _appt_event(con, o["id"], "recall" if again else "day", old, new, by_login, by_name, t)
        con.commit()
        return True, "ok"
    finally:
        con.close()


def set_appt_note(sid, note, by_login, by_name, path=None, now=None):
    """The note stays, and can be put right on the card after the tap. Returns (ok, msg)."""
    t = _ist(now)
    new = (note or "").strip()[:300]
    init_db(path)
    con = db(path)
    try:
        o = _appt_row(con, "sid=?", sid)
        if not o or (o.get("appt_state") or "") == "closed" or not appt_followed(o, path, now):
            return False, T_NO_APPT                            # closed with 'Ab nahi aayenge', or before the floor: as the day
        old = o.get("detail") or ""
        if old != new:
            con.execute("UPDATE outcome SET detail=? WHERE id=?", (new, o["id"]))
            _appt_event(con, o["id"], "note", old, new, by_login, by_name, t)
            con.commit()
        return True, "ok"
    finally:
        con.close()


def _noshow_now(oid, path, now, finance_db):
    """(the stored row, '') when this line is standing in Nahi aaye this minute; else (None, why not)."""
    oid = good_id(oid)
    if oid is None:
        return None, T_NO_APPT
    init_db(path)
    con = db(path)
    try:
        o = _appt_row(con, "id=?", oid)
    finally:
        con.close()
    if not o or not appt_followed(o, path, now):
        return None, T_NO_APPT
    if where_now(o["id"], path, now, finance_db) != "noshow":
        return None, T_NOT_NOSHOW
    return o, ""


def recall_appt(oid, day, by_login, by_name, path=None, now=None, finance_db=None):
    """'Phir call kiya — naya din': a new promised day; the earlier one stays in appt_event. Returns (ok, msg).
    Taken ONLY for a line standing in Nahi aaye this minute. The write names the day and the count it saw, so the
    same press sent twice is written once."""
    t = _ist(now)
    d = _good_day(day, t.date())
    if d is None:
        return False, T_BAD_DAY
    o, why = _noshow_now(oid, path, now, finance_db)
    if o is None:
        return False, why
    old = o.get("appt_day") or ""
    con = db(path)
    try:
        cur = con.execute("UPDATE outcome SET appt_day=?, appt_day_by=?, appt_day_at=?, recalls=COALESCE(recalls,0)+1, recall_at=? "
                          "WHERE id=? AND COALESCE(appt_day,'')=? AND COALESCE(recalls,0)=? AND COALESCE(appt_state,'')=''",
                          (d.isoformat(), by_login or "", _fmt(t), _fmt(t), o["id"], old, int(o.get("recalls") or 0)))
        if cur.rowcount != 1:
            return False, T_NOT_NOSHOW
        _appt_event(con, o["id"], "recall", old, d.isoformat(), by_login, by_name, t)
        con.commit()
        return True, "ok"
    finally:
        con.close()


def close_appt(oid, by_login, by_name, path=None, now=None, finance_db=None):
    """'Ab nahi aayenge': the line leaves the list. Kept in the store with who and when. Returns (ok, msg).
    Taken ONLY for a line standing in Nahi aaye this minute -- never for one Docterz cannot yet speak for."""
    t = _ist(now)
    o, why = _noshow_now(oid, path, now, finance_db)
    if o is None:
        return False, why
    con = db(path)
    try:
        cur = con.execute("UPDATE outcome SET appt_state='closed', appt_state_by=?, appt_state_at=? WHERE id=? AND COALESCE(appt_state,'')=''",
                          (by_login or "", _fmt(t), o["id"]))
        if cur.rowcount != 1:
            return False, T_NOT_NOSHOW
        _appt_event(con, o["id"], "closed", o.get("appt_state") or "", "closed", by_login, by_name, t)
        con.commit()
        return True, "ok"
    finally:
        con.close()


# ------------------------------------------------------------------ S497: the screens (the mock-up's own styles)
_S_HEADTAGS = ('<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">')
_S_FONT = "font-family: system-ui, -apple-system, 'Segoe UI', sans-serif"
LIST_HEAD = ('<!doctype html><html lang="hi-Latn"><head>' + _S_HEADTAGS + '<title>' + T_TITLE + '</title><style>\n'
             'body{margin:0;background:#0f172a}\n'
             'a{color:#93c5fd}a:hover{color:#bfdbfe}\n'
             'table{border-collapse:collapse;width:100%}\n'
             'th{text-align:left;font-weight:600;font-size:14px;color:#a8b5c8;padding:10px 12px;border-bottom:1px solid #3b4a63;white-space:nowrap}\n'
             'td{padding:13px 12px;border-bottom:1px solid #2c3a52;font-size:16px;vertical-align:top}\n'
             'tr:last-child td{border-bottom:0}\n'
             '@media (max-width: 820px){th:nth-child(2),td:nth-child(2){position:sticky;left:0;z-index:1;background:#1e293b}}\n'
             '</style></head><body>\n'
             '<div style="box-sizing: border-box; max-width: 1280px; margin: 0 auto; padding: 20px 16px 40px; background: #0f172a; '
             'color: #e5eefb; ' + _S_FONT + '; display: flex; flex-direction: column; gap: 16px">\n')
LIST_JS = """<script>
var s497busy=false;
function s497post(b){if(s497busy){return;} s497busy=true;
fetch('/portal/ring/list/act',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)})
.then(function(r){return r.json()}).then(function(j){ if(!j.ok){alert(j.msg||'error');} location.reload(); })
.catch(function(){s497busy=false;alert('server se jawab nahi');});}
function s497open(b){var p=b.parentNode.parentNode.querySelector('[data-s497-pick]'); if(p){p.style.display=(p.style.display==='none')?'flex':'none';}}
function s497day(b){s497post({id:Number(b.getAttribute('data-id')),act:'recall',day:b.getAttribute('data-day')});}
function s497other(b){var i=b.parentNode.querySelector('input[type=date]'); if(!i){return;} i.style.display='block'; try{i.showPicker();}catch(e){i.focus();}}
function s497good(i){var v=i.value||''; return (/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(v) && v>=i.getAttribute('min') && v<=i.getAttribute('max'))?v:'';}
function s497key(i,e){if(e.key==='Enter'){i.s497k=0;s497date(i);}else{i.s497k=1;}}
function s497date(i){clearTimeout(i.s497t); var v=s497good(i); if(!v){return;}
var go=function(){if(s497good(i)===v){s497post({id:Number(i.getAttribute('data-id')),act:'recall',day:v});}};
if(i.s497k){i.s497t=setTimeout(go,1500);}else{go();}}
function s497close(b){if(confirm(b.textContent+'?')){s497post({id:Number(b.getAttribute('data-id')),act:'closed'});}}
</script>"""
LIST_FOOT = "</div>\n" + LIST_JS + "</body></html>"
_S_SUB = "font-size: 14px; color: #a8b5c8"
_S_NOWRAP = "white-space: nowrap"
_S_WA_BTN = ("min-height: 40px; padding: 0 12px; border: 1px dashed #64748b; border-radius: 10px; background: #1e293b; "
             "color: #a8b5c8; font-size: 14px; font-weight: 600")
_S_BTN_BLUE = ("min-height: 44px; padding: 0 14px; border: 0; border-radius: 10px; background: #2563eb; color: #ffffff; "
               "font-size: 15px; font-weight: 600")
_S_BTN_LINE = ("min-height: 44px; padding: 0 14px; border: 1px solid #64748b; border-radius: 10px; background: #1e293b; "
               "color: #e5eefb; font-size: 15px; font-weight: 600")
_S_PILL = "display: inline-block; padding: 10px 16px; border-radius: 999px; %s; text-decoration: none; font-size: 15px; font-weight: 600"


def _mobile_words(m):
    """Five digits, a space, five digits -- the FULL number, as he ruled for his and the staff's screens (21-Sep; 07-Oct)."""
    d = _DIGITS.sub("", str(m or ""))
    return (d[:5] + " " + d[5:]) if len(d) == 10 else str(m or "")


def _mobile_cell(m, unmatchable=False):
    d = _DIGITS.sub("", str(m or ""))
    if len(d) == 10:
        return '<td style="%s"><a href="tel:+91%s">%s</a></td>' % (_S_NOWRAP, d, _esc(_mobile_words(d)))
    if unmatchable:
        return '<td>%s<div style="%s">%s</div></td>' % (_esc(m) or "—", _S_SUB, T_NO_MATCH)
    return '<td style="%s">%s</td>' % (_S_NOWRAP, _esc(m) or "—")


def _who_cell(r):
    """Kisne book kiya: a NAME, never a bare login."""
    return '<td>%s</td>' % _esc(r.get("who") or _person(r.get("login"), r.get("handler"), {}))


def _booked_cell(r):
    """03-Oct · 11:20"""
    w = str(r.get("when_ist") or "")
    return '<td style="%s">%s · %s</td>' % (_S_NOWRAP, _esc(_dm(r["booked"])), _esc(w[11:16]))


def _patient_cell(r, today, came=False):
    """Mareez: the name in bold, then the ID and the last visit known at the call. A number that was new says so --
    and, once Docterz has it, carries the name and the ID Docterz gave it."""
    cid = str(r.get("clinic_id") or "").strip()
    if r["known"]:
        name = str(r.get("patient") or "").strip() or ("ID " + cid)
        bits = []
        if cid and name != "ID " + cid:
            bits.append("ID " + cid)
        lv = _day(r.get("last_visit"))
        if lv is not None and not came:
            bits.append("pichhli visit " + _dm_far(lv, today))
        sub = " · ".join(bits)
    elif came:
        name = r.get("dz_name") or T_NEW
        sub = T_WAS_NEW + ((" · ab ID " + r["dz_id"]) if r.get("dz_id") else "")
    else:
        name, sub = T_NEW, T_NEW_SUB
    return '<td><b>%s</b>%s</td>' % (_esc(name), ('<div style="%s">%s</div>' % (_S_SUB, _esc(sub))) if sub else "")


def _note_cell(r):
    n = str(r.get("detail") or "").strip()
    return '<td style="color: #dbe5f3">%s</td>' % _esc(n) if n else '<td style="color: #a8b5c8">—</td>'


def _wa_cell():
    """The WhatsApp place: there, and switched off. The button is disabled and wired to nothing."""
    return ('<td><button type="button" disabled style="%s">%s</button><div style="font-size: 13px; color: #a8b5c8; margin-top: 4px">%s</div></td>'
            % (_S_WA_BTN, T_WA_BTN, T_WA_OFF))


def _pick_days(today):
    """[(word, 'YYYY-MM-DD')] for Aaj, Kal, Parso -- worked out here in India time, never in the phone's clock."""
    return [(T_DAYS[i], (today + timedelta(days=i)).isoformat()) for i in range(3)]


def _row_noshow(r, today, first=False):
    day = _esc(_dm_dow(r["appt"])) if r["appt"] is not None else T_NO_DAY
    pick = "".join('<button type="button" data-id="%d" data-day="%s" onclick="s497day(this)" style="%s">%s</button>'
                   % (r["id"], d, _S_BTN_LINE, w) for w, d in _pick_days(today))
    pick += ('<button type="button" onclick="s497other(this)" style="%s">%s</button>'
             '<input type="date" data-id="%d" min="%s" max="%s" onchange="s497date(this)" onkeydown="s497key(this,event)" '
             'style="display: none; min-height: 44px; padding: 0 10px; '
             'border: 1px solid #64748b; border-radius: 10px; background: #0f172a; color: #e5eefb; font-size: 15px">'
             % (_S_BTN_LINE, T_OTHER, r["id"], today.isoformat(), (today + timedelta(days=366)).isoformat()))
    return ('<tr>' + _booked_cell(r) + _patient_cell(r, today) + _mobile_cell(r.get("mobile"), r.get("unmatchable"))
            + '<td style="%s">%s<div style="font-size: 14px; color: #fdba74; font-weight: 600">%s</div></td>'
            % (_S_NOWRAP, day, _n_din(r["since"], "din ho gaya", "din ho gaye"))
            + _who_cell(r)
            + _note_cell(r) + _wa_cell()
            + '<td%s><div style="display: flex; flex-wrap: wrap; gap: 8px">'
              '<button type="button" onclick="s497open(this)" style="%s">%s</button>'
              '<button type="button" data-id="%d" onclick="s497close(this)" style="%s">%s</button></div>'
              '<div data-s497-pick style="display: none; flex-wrap: wrap; gap: 8px; margin-top: 8px">%s</div></td></tr>\n'
            % (' style="min-width: 300px"' if first else "", _S_BTN_BLUE, T_RECALL, r["id"], _S_BTN_LINE, T_CLOSE, pick))


def _row_due(r, today):
    if r["appt"] is None:
        day = T_NO_DAY
    else:
        gap = (r["appt"] - today).days
        day = _esc(_dm_dow(r["appt"])) + (" · aaj" if gap == 0 else (" · kal" if gap == 1 else ""))
    if r.get("unsure"):                                        # its day has gone by, and Docterz cannot yet speak for it
        day += '<div style="font-size: 14px; color: #fdba74; font-weight: 600">%s</div>' % T_UNSURE
    return ('<tr>' + _booked_cell(r) + _patient_cell(r, today) + _mobile_cell(r.get("mobile"), r.get("unmatchable"))
            + '<td style="%s">%s</td>' % (_S_NOWRAP, day)
            + _who_cell(r)
            + _note_cell(r) + _wa_cell() + '</tr>\n')


def _row_came(r, today):
    day = _esc(_dm_dow(r["appt"])) if r["appt"] is not None else T_NO_DAY
    late = ('<div style="font-size: 14px; font-weight: 400; color: #a8b5c8">%s</div>' % _n_din(r["late"], "din baad", "din baad")) if r.get("late") else ""
    cid = str(r.get("clinic_id") or "").strip()
    if r["known"] and r.get("visit_id") and r["visit_id"] != cid:      # a family mobile: the visit is another ID's -- say whose
        whose = " · ".join(x for x in (r.get("visit_name") or "", "ID " + r["visit_id"]) if x)
        late += '<div style="font-size: 14px; font-weight: 400; color: #a8b5c8">%s</div>' % _esc(T_VISIT_OF % whose)
    return ('<tr>' + _booked_cell(r) + _patient_cell(r, today, came=True) + _mobile_cell(r.get("mobile"))
            + '<td style="%s">%s</td>' % (_S_NOWRAP, day)
            + '<td style="white-space: nowrap; font-weight: 700; color: #f1f5f9">Aaye · %s%s</td>' % (_esc(_dm(r["visit"])), late)
            + _who_cell(r) + '</tr>\n')


def _part(box, head, cols, rows):
    empty = '<tr><td colspan="%d" style="color: #a8b5c8">—</td></tr>\n' % len(cols)
    return ('  <div style="%s; border-radius: 14px; padding: 14px 16px 6px; display: flex; flex-direction: column; gap: 8px">\n%s'
            '    <div style="overflow-x: auto">\n      <table>\n        <thead>\n          <tr>%s</tr>\n        </thead>\n        <tbody>\n%s'
            '        </tbody>\n      </table>\n    </div>\n  </div>\n'
            % (box, head, "".join("<th>%s</th>" % c for c in cols), "".join(rows) or empty))


def _owner_box(data, on, holders, msg):
    """HIS box, in English, on top of the staff's page. No staff login is ever sent it."""
    names = _agent_names()
    who = ", ".join(sorted(_person(u, "", names) for u in holders)) or "Nobody yet"
    line = ("Shown to staff: <b>ON</b>. %s see the tile, this list, and the day question on the card after "
            "“Appointment book ho gaya”." % _esc(who)) if on else \
        "Shown to staff: <b>OFF</b>. Only a doctor's login sees this list. The tile is hidden from staff until you turn this on."
    hard = _day(HARD_FLOOR)
    hard_words = "%s-%d" % (_dm(hard), hard.year)
    said = {"on": "Turned on.", "off": "Turned off.", "saved": "Saved.",
            "bad": "Not saved — the days must be 1 to 30, and the date not before %s." % hard_words}.get(msg, "")
    thr = data.get("visits_through")
    seen = ("Docterz visits on the server up to <b>%s</b>." % _esc(_dm_dow(thr))) if thr is not None else \
        "Docterz visits could not be read just now — arrivals cannot be confirmed until they can."
    son = data.get("switch_on")
    first = ("the day the list was first turned on (%s)" % _esc(_dm_dow(son))) if son is not None else "the day you first turn the list on"
    box = "min-height: 40px; padding: 0 10px; border: 1px solid #64748b; border-radius: 10px; background: #0f172a; color: #e5eefb; font-size: 15px"
    return ('  <div style="background: #1e293b; border: 1px dashed #64748b; border-radius: 14px; padding: 14px 18px; font-size: 15px; '
            'color: #dbe5f3; display: flex; flex-direction: column; gap: 10px">\n'
            '    <div><b>For you only</b> — staff never see this box.%s</div>\n'
            '    <div>%s</div>\n'
            '    <form method="post" action="/portal/ring/list/switch" style="margin: 0"><input type="hidden" name="on" value="%s">'
            '<button type="submit" style="%s">%s</button></form>\n'
            '    <form method="post" action="/portal/ring/list/setting" style="margin: 0; display: flex; flex-wrap: wrap; gap: 10px; align-items: center">'
            '<label>When no day is written, wait <input type="number" name="wait_days" min="1" max="30" value="%d" style="%s; width: 70px"> days</label>'
            '<label>Follow appointments booked on or after <input type="date" name="follow_from" min="%s" value="%s" style="%s"></label>'
            '<input type="hidden" name="follow_shown" value="%s">'
            '<button type="submit" style="%s">Save</button>'
            '<div style="flex-basis: 100%%; font-size: 14px; color: #a8b5c8">Nothing booked before that date is on the list. You may move it earlier, '
            'back to %s and no further. Emptied, it returns to %s.</div></form>\n'
            '    <div style="font-size: 14px; color: #a8b5c8">%s WhatsApp to the patient: <b>OFF</b> — nothing is sent; only the place is kept. '
            '<a href="/portal/ring/counts">Per-person call counts</a></div>\n'
            '  </div>\n'
            % ((" <b>" + said + "</b>") if said else "", line, "0" if on else "1", _S_BTN_LINE if on else _S_BTN_BLUE,
               "Turn it off for staff" if on else "Turn it on for staff", data["wait_days"], box,
               HARD_FLOOR, data["follow_from"].isoformat(), box, data["follow_from"].isoformat(), _S_BTN_LINE, hard_words, first, seen))


def render_list(data, doctor=False, on=False, holders=(), msg=""):
    """The staff's page, as the mock-up draws it: the head, the three counts, then ONE table in three parts."""
    today = data["today"]
    names = _agent_names()
    for part in ("noshow", "due", "came"):
        for r in data[part]:
            r["who"] = _person(r.get("login"), r.get("handler"), names)
    n = (len(data["noshow"]), len(data["due"]), len(data["came"]))
    pills = "".join('      <a href="/portal/ring/list?d=%s" style="%s">%s</a>\n'
                    % (k, _S_PILL % ("background: #2563eb; color: #ffffff" if data["span"] == k else "background: #334155; color: #dbe5f3"), w)
                    for k, w, _n in SPANS)
    tile = ('      <div style="background: %s; border: 1px solid %s; border-radius: 12px; padding: 12px 14px">\n'
            '        <div style="font-size: 28px; font-weight: 700; color: %s">%d</div>\n'
            '        <div style="font-size: 15px; color: %s">%s</div>\n      </div>\n')
    head = ('  <div style="background: #1e293b; border: 1px solid #334155; border-radius: 14px; padding: 16px 18px; display: flex; flex-direction: column; gap: 12px">\n'
            '    <div style="display: flex; flex-wrap: wrap; gap: 12px; align-items: baseline; justify-content: space-between">\n'
            '      <h1 style="margin: 0; font-size: 24px; font-weight: 700">%s</h1>\n    </div>\n'
            '    <div style="display: flex; flex-wrap: wrap; gap: 8px">\n%s    </div>\n'
            '    <div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px">\n%s%s%s    </div>\n  </div>\n'
            % (T_TITLE, pills,
               tile % ("#3a2a12", "#b45309", "#fdba74", n[0], "#fde0bf", T_NOSHOW),
               tile % ("#172554", "#2563eb", "#bfdbfe", n[1], "#dbe9ff", T_DUE),
               tile % ("#1e293b", "#475569", "#f1f5f9", n[2], "#dbe5f3", T_CAME)))
    warn = ""
    if not data["store_ok"] or not data["visits_ok"]:
        warn = ('  <div style="background: #3a2a12; border: 1px solid #b45309; border-radius: 14px; padding: 12px 16px; font-size: 15px; '
                'color: #fde0bf">%s</div>\n' % (T_STORE if not data["store_ok"] else T_CANNOT))
    p1 = _part("background: #1e293b; border: 2px solid #b45309",
               '    <div style="display: flex; flex-wrap: wrap; gap: 10px; align-items: baseline; justify-content: space-between">\n'
               '      <h2 style="margin: 0; font-size: 19px; font-weight: 700; color: #fdba74">%s (%d)</h2>\n'
               '      <div style="font-size: 14px; color: #fde0bf">%s</div>\n    </div>\n' % (T_NOSHOW_H, n[0], T_NOSHOW_NOTE),
               ("Kab book hua", "Mareez", "Mobile", "Kis din aana tha", "Kisne book kiya", "Note", "WhatsApp", "Ab kya karna hai"),
               [_row_noshow(r, today, i == 0) for i, r in enumerate(data["noshow"])])
    p2 = _part("background: #1e293b; border: 1px solid #2563eb",
               '    <h2 style="margin: 0; font-size: 19px; font-weight: 700; color: #bfdbfe">%s (%d)</h2>\n' % (T_DUE_H, n[1]),
               ("Kab book hua", "Mareez", "Mobile", "Kis din aana hai", "Kisne book kiya", "Note", "WhatsApp"),
               [_row_due(r, today) for r in data["due"]])
    p3 = _part("background: #1e293b; border: 1px solid #475569",
               '    <div style="display: flex; flex-wrap: wrap; gap: 10px; align-items: baseline; justify-content: space-between">\n'
               '      <h2 style="margin: 0; font-size: 19px; font-weight: 700; color: #f1f5f9">%s (%d)</h2>\n'
               '      <div style="font-size: 14px; color: #a8b5c8">%s</div>\n    </div>\n' % (T_CAME_H, n[2], T_CAME_NOTE),
               ("Kab book hua", "Mareez", "Mobile", "Kis din aana tha", "Aaye (Docterz)", "Kisne book kiya"),
               [_row_came(r, today) for r in data["came"]])
    how = ('  <div style="background: #1e293b; border: 1px solid #334155; border-radius: 14px; padding: 14px 18px; font-size: 15px; '
           'color: #dbe5f3; display: flex; flex-direction: column; gap: 6px">\n    <div><b>Yeh list kaise bharti hai</b></div>\n%s'
           '    <div>Jis din aana tha uske agle din tak visit na mile to mareez “Nahi aaye” mein aa jata hai. '
           'Din na likha ho to %d din baad.</div>\n  </div>\n'
           % ("".join("    <div>%s</div>\n" % line for line in T_HOW), data["wait_days"]))
    return LIST_HEAD + (_owner_box(data, on, holders, msg) if doctor else "") + head + warn + p1 + p2 + p3 + how + LIST_FOOT


def render_list_note(text):
    """One line in the list's own frame: the list is off, or it is not this login's."""
    return (LIST_HEAD + '  <div style="background: #1e293b; border: 1px solid #334155; border-radius: 14px; padding: 16px 18px; '
            'font-size: 17px">%s</div>\n</div>\n</body></html>' % _esc(text))


CARD_HEAD = ('<!doctype html><html lang="hi-Latn"><head>' + _S_HEADTAGS + '<title>Call outcome</title><style>\n'
             'body{margin:0;background:#0f172a}\n'
             'a{color:#93c5fd}a:hover{color:#bfdbfe}\n'
             '</style></head><body>\n'
             '<div style="box-sizing: border-box; max-width: 480px; margin: 0 auto; padding: 18px 14px 28px; background: #0f172a; '
             'color: #e5eefb; ' + _S_FONT + '; display: flex; flex-direction: column; gap: 14px">\n')
CARD_JS = """<script>
var S497_SID=@@SID@@;
function s497post(b,done){b.s=S497_SID;fetch('/portal/ring/appt',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)})
.then(function(r){return r.json()}).then(function(j){ if(j.ok){done();} else {alert(j.msg||'error');} })
.catch(function(){alert('server se jawab nahi');});}
function s497again(){location.replace('/portal/ring/outcome?s='+encodeURIComponent(S497_SID));}
function s497note(){return (document.getElementById('note')||{}).value||'';}
function s497day(b){s497post({day:b.getAttribute('data-day'),note:s497note()},s497again);}
function s497other(){var i=document.getElementById('aurdin'); i.style.display='block'; try{i.showPicker();}catch(e){i.focus();}}
function s497good(i){var v=i.value||''; return (/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(v) && v>=i.getAttribute('min') && v<=i.getAttribute('max'))?v:'';}
function s497key(i,e){if(e.key==='Enter'){i.s497k=0;s497date(i);}else{i.s497k=1;}}
function s497date(i){clearTimeout(i.s497t); var v=s497good(i); if(!v){return;}
var go=function(){if(s497good(i)===v){s497post({day:v,note:s497note()},s497again);}};
if(i.s497k){i.s497t=setTimeout(go,1500);}else{go();}}
function s497save(i){s497post({note:i.value},function(){i.style.borderColor='#22c55e';});}
</script>"""
_S_CARD = "background: #1e293b; border: 1px solid %s; border-radius: 14px; padding: 16px; display: flex; flex-direction: column; gap: %dpx"
_S_DAY_ON = "min-height: 52px; border: 0; border-radius: 12px; background: #2563eb; color: #ffffff; font-size: 17px; font-weight: 600"
_S_DAY = "min-height: 52px; border: 1px solid #64748b; border-radius: 12px; background: #1e293b; color: #e5eefb; font-size: 17px; font-weight: 600"


def _json_js(v):
    """A value for a <script>: JSON, with '<' written so that no text can ever close the script early."""
    return json.dumps(v).replace("<", "\\u003c")


def render_appt_card(call, outcome, sid, path=None, now=None):
    """The card AFTER 'Appointment book ho gaya', as the mock-up draws it: what was written; the one optional tap
    'Kis din aayenge?'; the note; the WhatsApp place (off); the way to the list."""
    today = _ist(now).date()
    wait = wait_days(path)
    name = str(outcome.get("patient") or "").strip() or T_NEW
    cid = str(outcome.get("clinic_id") or "").strip()
    w = str(outcome.get("when_ist") or "")
    booked = _booked_day(outcome) or today
    appt = _day(outcome.get("appt_day"))
    days = _pick_days(today)
    btns = ""
    for word, d in days:
        on = appt is not None and appt.isoformat() == d
        btns += '      <button type="button" data-day="%s" onclick="s497day(this)" style="%s">%s</button>\n' % ("" if on else d, _S_DAY_ON if on else _S_DAY, word)
    far = appt is not None and appt.isoformat() not in [d for _w, d in days]
    btns += '      <button type="button" onclick="s497other()" style="%s">%s</button>\n' % (
        _S_DAY_ON if far else _S_DAY, ("Aur din · " + _esc(_dm_dow(appt))) if far else T_OTHER)
    return (CARD_HEAD
            + '  <div style="%s">\n    <div style="font-size: 20px; font-weight: 700">%s</div>\n'
              '    <div style="font-size: 16px; color: #dbe5f3">%s</div>\n    <div style="font-size: 15px; color: #a8b5c8">%s · %s %s · %s</div>\n  </div>\n'
            % (_S_CARD % ("#334155", 10), T_CARD_DONE, _esc(name + ((" · ID " + cid) if cid else "")),
               _esc(_mobile_words(outcome.get("mobile"))), _esc(_dm(booked)), _esc(w[11:16]), _esc(_person(outcome.get("login"), outcome.get("handler"))))
            + '  <div style="%s">\n    <div style="font-size: 18px; font-weight: 700">%s</div>\n'
              '    <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px">\n%s    </div>\n'
              '    <input id="aurdin" type="date" min="%s" max="%s" value="%s" onchange="s497date(this)" onkeydown="s497key(this,event)" '
              'style="display: none; box-sizing: border-box; width: 100%%; '
              'min-height: 48px; padding: 0 12px; border: 1px solid #64748b; border-radius: 10px; background: #0f172a; color: #e5eefb; font-size: 16px">\n'
              '    <div style="font-size: 15px; color: #a8b5c8">Zaroori nahi hai. Din na batayein to %d din tak intezaar hoga, phir mareez “Nahi aaye” mein dikhega.</div>\n  </div>\n'
            % (_S_CARD % ("#2563eb", 12), T_CARD_ASK, btns, today.isoformat(), (today + timedelta(days=366)).isoformat(),
               appt.isoformat() if far else "", wait)
            + '  <div style="%s">\n    <label for="note" style="font-size: 16px; font-weight: 600">%s</label>\n'
              '    <input id="note" type="text" value="%s" maxlength="300" onchange="s497save(this)" style="box-sizing: border-box; width: 100%%; min-height: 48px; '
              'padding: 0 12px; border: 1px solid #64748b; border-radius: 10px; background: #0f172a; color: #e5eefb; font-size: 16px">\n  </div>\n'
            % (_S_CARD % ("#334155", 10), T_CARD_NOTE, _esc(outcome.get("detail") or ""))
            + '  <div style="background: #1e293b; border: 1px dashed #64748b; border-radius: 14px; padding: 14px 16px; display: flex; flex-direction: column; gap: 6px">\n'
              '    <div style="font-size: 16px; font-weight: 600; color: #a8b5c8">%s</div>\n    <div style="font-size: 15px; color: #a8b5c8">%s</div>\n  </div>\n'
            % (T_CARD_WA, T_CARD_WA_OFF)
            + '  <a href="/portal/ring/list?d=aaj" style="display: block; text-align: center; padding: 15px 12px; border-radius: 12px; background: #334155; '
              'color: #ffffff; text-decoration: none; font-size: 17px; font-weight: 600">%s</a>\n</div>\n' % T_CARD_LINK
            + CARD_JS.replace("@@SID@@", _json_js(sid)) + "</body></html>")


'''

RO_PAGE = r'''

def _page(body, sid=""):
    """PAGE with the call's id in its script and the body in its place. S497 mends F-797: the id used to be put in by
    replacing the three letters S-I-D through the WHOLE page, after the patient's name was already in it, so a name
    written SIDDIQUI or SIDDHARTH lost them. The id now goes into the TEMPLATE and the body is placed after it -- and
    the id is written so that nothing in it can close the script early (_json_js)."""
    mark = "\x00S497-BODY\x00"
    return (PAGE % mark).replace("SID", _json_js(sid)).replace(mark, body)
'''

RO_ROUTES = r'''    # ---- S497: the after-call list -----------------------------------------------------------------------------
    def _s497_by():
        who = sso_user(request) or {}
        login = who.get("user", "")
        agents = rc.load_agents()
        name = next(((a or {}).get("name") for a in agents.values() if (a or {}).get("user") == login), None) or who.get("name") or ""
        return who, login, _person(login, name, {})

    def _s497_said(ok, msg):
        """A press that was not taken answers 4xx, with the reason in the staff's words: 400 a day that will not do,
        404 no such appointment, 409 the line is no longer where the button was."""
        return jsonify({"ok": ok, "msg": msg}), (200 if ok else (400 if msg == T_BAD_DAY else (404 if msg == T_NO_APPT else 409)))

    def _s497_page(html, code=200):
        resp = make_response(html, code)
        resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.route("/portal/ring/list", methods=["GET"])
    @login_required
    def ring_list():
        """S497: ONE table in three parts. All a GET may do to the store is make its new columns (never inside a read)."""
        kind = list_access(sso_user(request) or {}, path)
        if not kind:
            return _s497_page(render_list_note(T_DENIED), 403)
        if kind == "off":
            return _s497_page(render_list_note(T_OFF))
        try:
            init_db(path)
        except Exception:
            pass
        data = list_data(str(request.args.get("d") or "").strip(), path)
        return _s497_page(render_list(data, kind == "doctor", list_on(path), sorted(list_holders()),
                                      str(request.args.get("m") or "").strip()))

    @app.route("/portal/ring/list/switch", methods=["POST"])
    @login_required
    def ring_list_switch():
        """S497: the doctor's switch -- the list, its tile and the card's new part shown to staff, or not."""
        from flask import redirect
        who = sso_user(request) or {}
        if who.get("role") != "doctor":
            return jsonify({"ok": False}), 403
        on = str(request.form.get("on") or "") == "1"
        set_list_on(on, who.get("user", ""), path)
        return redirect("/portal/ring/list?m=%s" % ("on" if on else "off"))

    @app.route("/portal/ring/list/setting", methods=["POST"])
    @login_required
    def ring_list_setting():
        """S497: the doctor's two settings -- how long a booking with no day waits; from which booking day to follow
        (never before HARD_FLOOR; emptied, the day the list was first turned on)."""
        from flask import redirect
        who = sso_user(request) or {}
        if who.get("role") != "doctor":
            return jsonify({"ok": False}), 403
        by = who.get("user", "")
        wd, ff = request.form.get("wait_days"), request.form.get("follow_from")
        if not (wait_days_ok(wd) and follow_from_ok(ff)):
            return redirect("/portal/ring/list?m=bad")     # one box wrong: NOTHING is written, as the page will say
        good = set_wait_days(wd, by, path)
        good = set_follow_from(ff, by, path, shown=request.form.get("follow_shown")) and good
        return redirect("/portal/ring/list?m=%s" % ("saved" if good else "bad"))

    @app.route("/portal/ring/list/act", methods=["POST"])
    @login_required
    def ring_list_act():
        """S497: the two buttons of a 'Nahi aaye' line -- Phir call kiya (a new day) . Ab nahi aayenge. Taken only for a
        line that is standing in Nahi aaye this minute; anything else is answered 4xx."""
        who, login, name = _s497_by()
        if list_access(who, path) not in ("doctor", "staff"):
            return jsonify({"ok": False, "msg": T_DENIED}), 403
        body = request.get_json(silent=True)
        body = body if isinstance(body, dict) else {}
        oid = good_id(body.get("id"))
        if oid is None:                                        # 0 < id < 2**63, a whole number -- else it never reaches SQLite
            return jsonify({"ok": False, "msg": T_NO_APPT}), 400
        act = str(body.get("act") or "")
        if act == "recall":
            ok, msg = recall_appt(oid, str(body.get("day") or "").strip(), login, name, path)
        elif act == "closed":
            ok, msg = close_appt(oid, login, name, path)
        else:
            return jsonify({"ok": False, "msg": T_NO_APPT}), 400
        return _s497_said(ok, msg)

    @app.route("/portal/ring/appt", methods=["POST"])
    @login_required
    def ring_appt():
        """S497: the card after the tap -- the one optional day, and the note."""
        who, login, name = _s497_by()
        if list_access(who, path) not in ("doctor", "staff"):
            return jsonify({"ok": False, "msg": T_DENIED}), 403
        body = request.get_json(silent=True)
        body = body if isinstance(body, dict) else {}
        sid = str(body.get("s") or "").strip()[:80]
        ok, msg = True, "ok"
        if "note" in body:
            ok, msg = set_appt_note(sid, str(body.get("note") or ""), login, name, path)
        if ok and "day" in body:
            ok, msg = set_appt_day(sid, str(body.get("day") or "").strip(), login, name, path)
        return _s497_said(ok, msg)

'''

# ======================================================================================= the new text: portal.py
PO_TILE = r'''
    {"icon": "\U0001F4CB", "name": "Call ke baad",
     # S497 NEW (the owner, 07-Oct-2026, D693). What the staff file after a call, as a list they can see: ONE table in
     # three parts -- Nahi aaye (stays until it is dealt with), Aane baaki, Aa gaye (filled by itself from the Docterz
     # export). ring_outcome.py, /portal/ring/list. Granted by name in tile_grants.json v33 to the four who hold Call
     # Tracker; the doctor holds it by role. Installed OFF for staff: until he turns the list on from its own page no
     # staff login is drawn this tile (_s497_tile_on, below).
     "desc": "Appointment list · kaun aaya, kaun nahi", "live": True,
     "url": "/portal/ring/list",
     "roles": ["doctor"]},
'''

PO_HELPER = r'''# ---- S497_RING_LIST (D693): 'Call ke baad' is drawn for staff only once the doctor has turned the list on ------------
# The list is installed switched off for staff (his rule of 05-Oct: a new screen is shown to him first), and a tile that
# only refuses is a trap (S223) -- so while the list is off the tile is not drawn for a staff login at all. The switch
# lives in ring_outcomes.db and is read by ring_outcome.list_on(), a read that makes nothing. If it cannot be read, it
# is off (fail closed); the doctor is never asked.
S497_TILE = "Call ke baad"


def _s497_tile_on(role):
    if role == "doctor":
        return True
    try:
        import ring_outcome as _s497_ro
        return bool(_s497_ro.list_on())
    except Exception:
        return False


'''

# ======================================================================================= the edits (old must occur once)
A_RO_HEAD = '''# Every number lives in the database (0600) or in the tracker -- none in this file (F-185).
'''
A_RO_INIT = '''def init_db(path=None):
'''
A_RO_SCHEMA = '''    CREATE INDEX IF NOT EXISTS ix_outcome_sid ON outcome(sid);
    CREATE INDEX IF NOT EXISTS ix_call_day ON call(day_key);
    """)
    con.commit()
'''
N_RO_SCHEMA = '''    CREATE INDEX IF NOT EXISTS ix_outcome_sid ON outcome(sid);
    CREATE INDEX IF NOT EXISTS ix_call_day ON call(day_key);
    CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT, by_whom TEXT, at TEXT);
    CREATE TABLE IF NOT EXISTS appt_event (
      id INTEGER PRIMARY KEY AUTOINCREMENT, outcome_id INTEGER NOT NULL, kind TEXT NOT NULL, old_value TEXT,
      new_value TEXT, by_login TEXT, by_name TEXT, at_ist TEXT, created_at INTEGER);
    CREATE INDEX IF NOT EXISTS ix_appt_event_outcome ON appt_event(outcome_id);
    """)
    _s497_columns(con)                           # S497: the list's columns on `outcome`, added once, never dropped
    con.commit()
'''
A_RO_ROUTES_HEAD = '''# ------------------------------------------------------------------ the portal routes
PAGE = """<!doctype html>'''
A_RO_ESC = '''def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))
'''
A_RO_RET1 = '''    return (PAGE % body).replace("SID", json.dumps(sid))
'''
N_RO_RET1 = '''    return _page(body, sid)
'''
A_RO_RET2 = '''        return (PAGE % html).replace("SID", '""')
'''
N_RO_RET2 = '''        return _page(html)
'''
A_RO_GET = '''        call = get_call(sid, path) if sid else None
        outcome = get_outcome(sid, path) if call else None
        resp = make_response(render_page(call, outcome, sid))
'''
N_RO_GET = '''        call = get_call(sid, path) if sid else None
        outcome = get_outcome(sid, path) if call else None
        # S497: after 'Appointment book ho gaya' the card asks the one optional day -- for a doctor, and for those shown
        # the tile once the list is on. For everyone else, and for every other outcome, the page is the one it was.
        # An appointment booked before the list's first day is not followed: its card is the old card too.
        if outcome and outcome.get("code") == APPT_CODE and list_access(sso_user(request) or {}, path) in ("doctor", "staff") \\
                and appt_followed(outcome, path):
            resp = make_response(render_appt_card(call, outcome, sid, path))
        else:
            resp = make_response(render_page(call, outcome, sid))
'''
A_RO_COUNTS = '''    @app.route("/portal/ring/counts")
    @login_required
    def ring_counts():'''
A_RO_DAY = '''                % (c["day"], c["totals"]["calls"], c["totals"]["missed"], c["totals"]["unmirrored"], rows or "<tr><td colspan=6>—</td></tr>"))
'''
N_RO_DAY = '''                % (_esc(c["day"]), c["totals"]["calls"], c["totals"]["missed"], c["totals"]["unmirrored"], rows or "<tr><td colspan=6>—</td></tr>"))
'''

A_PO_TILE = '''    {"icon": "\\U0001F4DE", "name": "Call Tracker",
     "desc": "Staff's working tracker (the Sheet app)", "live": True,
     "url": "/portal/go/call-tracker",
     "roles": ["doctor"]},
'''
A_PO_GROUP = '''    "Call Console": "Clinic", "Call Tracker": "Clinic",
'''
N_PO_GROUP = '''    "Call Console": "Clinic", "Call Tracker": "Clinic", "Call ke baad": "Clinic",
'''
A_PO_VIS = '''def _visible_sections(role, pc, user=""):
'''
A_PO_FILTER = '''                  and t["name"] not in mask
                  and (not t.get("pc_only") or pc)]
'''
N_PO_FILTER = '''                  and t["name"] not in mask
                  and (not t.get("pc_only") or pc)
                  and (t["name"] != S497_TILE or _s497_tile_on(role))]      # S497: off for staff until he turns it on
'''

EDITS = {
    "ring_outcome.py": [
        ("the header note", A_RO_HEAD, A_RO_HEAD + RO_HEAD),
        ("the store's new columns", A_RO_INIT, RO_COLS + A_RO_INIT),
        ("the store's two new tables", A_RO_SCHEMA, N_RO_SCHEMA),
        ("the list, the rule, the two screens", A_RO_ROUTES_HEAD, RO_MAIN + A_RO_ROUTES_HEAD),
        ("F-797: the page helper", A_RO_ESC, A_RO_ESC + RO_PAGE),
        ("F-797: the tap's page", A_RO_RET1, N_RO_RET1),
        ("F-797: the counts page", A_RO_RET2, N_RO_RET2),
        ("the card after the tap", A_RO_GET, N_RO_GET),
        ("the list's routes", A_RO_COUNTS, RO_ROUTES + A_RO_COUNTS),
        ("the counts page: the day from the address is escaped", A_RO_DAY, N_RO_DAY),
    ],
    "portal.py": [
        ("the tile, after Call Tracker", A_PO_TILE, A_PO_TILE + PO_TILE),
        ("the tile's section", A_PO_GROUP, N_PO_GROUP),
        ("the tile's switch", A_PO_VIS, PO_HELPER + A_PO_VIS),
        ("the tile is drawn only when on", A_PO_FILTER, N_PO_FILTER),
    ],
}
MARKERS = {
    "ring_outcome.py": ['LIST_TILE = "Call ke baad"', "def list_data(", "def appt_state(", "def visits_since(", "def render_list(",
                        "def render_appt_card(", "def _page(", "def _s497_columns(", '@app.route("/portal/ring/list", methods=["GET"])',
                        '@app.route("/portal/ring/appt", methods=["POST"])', "WA_ENABLED = False", "?mode=ro",
                        'HARD_FLOOR = "2026-10-01"', "def floor_day(", "def can_judge(", "def where_now(", '% (_esc(c["day"]), c["totals"]["calls"]'],
    "portal.py": ['"name": "Call ke baad"', '"Call ke baad": "Clinic"', "def _s497_tile_on(role):", "_s497_tile_on(role))]"],
}


class Stop(Exception):
    pass


def md5(b):
    return hashlib.md5(b).hexdigest()


def _lit(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_lit(x) for x in node.elts]
    if isinstance(node, ast.Dict):
        return {_lit(k): _lit(v) for k, v in zip(node.keys, node.values)}
    return None


def check(name, text):
    """Everything that can be known about the new text before a byte is written."""
    if "\r" in text or not text.endswith("\n"):
        raise Stop("%s: line endings are not LF, or the last line is not ended" % name)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        compile(text, name, "exec")
        tree = ast.parse(text, feature_version=(3, 8))
    for m in MARKERS[name]:
        if text.count(m) < 1:
            raise Stop("%s: the built text lacks %r" % (name, m))
    if name == "ring_outcome.py":
        if text.count('.replace("SID"') != 1:
            raise Stop("ring_outcome.py: the page's id is put in at %d places, not one" % text.count('.replace("SID"'))
    if name == "portal.py":
        got = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                    and node.targets[0].id in ("TILES", "_TILE_GROUP"):
                got[node.targets[0].id] = _lit(node.value)
        names = [t.get("name") for t in got.get("TILES") or [] if isinstance(t, dict)]
        if names.count("Call ke baad") != 1 or names[names.index("Call ke baad") - 1] != "Call Tracker":
            raise Stop("portal.py: the tile is not there once, right after Call Tracker")
        if (got.get("_TILE_GROUP") or {}).get("Call ke baad") != "Clinic":
            raise Stop("portal.py: the tile has no section")
    if not TO[name].startswith("@@") and md5(text.encode("utf-8")) != TO[name]:
        raise Stop("%s: built %s, the kit's pin is %s" % (name, md5(text.encode("utf-8")), TO[name]))


def build(src):
    """{file name: new bytes}, built and checked in memory from the live files in `src`. Writes nothing."""
    out = {}
    for name in ("ring_outcome.py", "portal.py"):
        with open(os.path.join(src, name), "rb") as fh:
            raw = fh.read()
        if md5(raw) != FROM[name]:
            raise Stop("%s in %s is %s, not %s -- it changed since this kit was built; nothing is built" % (name, src, md5(raw), FROM[name]))
        text = raw.decode("utf-8")
        for what, old, new in EDITS[name]:
            n = text.count(old)
            if n != 1:
                raise Stop("%s: the place for '%s' occurs %d times in the live file, not once" % (name, what, n))
            text = text.replace(old, new)
        check(name, text)
        out[name] = text.encode("utf-8")
    return out


def main(argv):
    if argv == ["--pins"]:
        for name in ("ring_outcome.py", "portal.py"):
            print("%s %s %s" % (name, FROM[name], TO[name]))
        return 0
    comparing = bool(argv) and argv[0] == "--check"
    args = argv[1:] if comparing else argv
    if len(args) != 2:
        print(__doc__)
        return 2
    src, dst = os.path.abspath(args[0]), os.path.abspath(args[1])
    try:
        out = build(src)
    except Stop as ex:
        print("!! make_s497: %s" % ex)
        return 1
    if comparing:
        bad = 0
        for name, data in sorted(out.items()):
            try:
                with open(os.path.join(dst, name), "rb") as fh:
                    same = fh.read() == data
            except OSError:
                same = False
            print("%-16s %s -> %s  %s" % (name, FROM[name][:8], md5(data), "= the file in %s" % dst if same else "!! NOT the file in %s" % dst))
            bad += 0 if same else 1
        return 1 if bad else 0
    if os.path.realpath(src) == os.path.realpath(dst):
        print("!! make_s497: the out folder is the folder the live files are read from -- nothing written")
        return 1
    if not os.path.isdir(dst):
        print("!! make_s497: no such out folder: %s -- nothing written" % dst)
        return 1
    for name, data in sorted(out.items()):          # every file is built and checked before the first one is written
        tmp = os.path.join(dst, "." + name + ".s497_new")
        with open(tmp, "wb") as fh:
            fh.write(data)
        os.replace(tmp, os.path.join(dst, name))
        print("%-16s %s -> %s  %d B" % (name, FROM[name][:8], md5(data), len(data)))
    print("built.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
