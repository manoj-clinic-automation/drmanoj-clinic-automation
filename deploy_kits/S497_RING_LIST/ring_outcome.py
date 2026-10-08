#!/usr/bin/env python3
# ring_outcome.py -- kit S419_RING_OUTCOME (session 284, 27-Sep-2026) -- D590 steps 2 and 3.
#
# What happens AFTER the call the staff phone was told about (S366): at hang-up the phone that answered is
# asked "Kya hua?"; a tap opens /portal/ring/outcome?s=<session> (signed-in portal), one button files the
# outcome; ten minutes without an outcome brings ONE reminder push; the doctor sees per-person counts.
#
# Where an outcome lives (the assistant's call, D630's direction): FIRST in ring_outcomes.db beside the ring
# state (the store the VPS tracker will grow from), THEN mirrored into the Google tracker's Followup_Outcomes
# tab as a row of exactly the shape WebApp.gs saveIncomingOutcome / Callconsole.gs saveKOutcome write, through
# the venv's gspread and the same service-account key push_followups_vps.py uses (found by content in
# /root/wa, never named here). The Google tracker, its summary cross-tab and its escalation queue then see the
# outcome as if it had been typed there. A mirror that fails is retried by the sweeper (never lost).
#
# Shared by TWO processes: ring_hook (gunicorn, records the call, pushes the card, runs the 10-minute sweeper)
# and the portal (gunicorn, serves the page, files the outcome). SQLite with a short busy timeout is enough.
#
# Every number lives in the database (0600) or in the tracker -- none in this file (F-185).
#
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
import json
import os
import re
import sqlite3
import threading
import time
import urllib.request
from datetime import datetime, timezone, timedelta

import ring_common as rc

IST = timezone(timedelta(hours=5, minutes=30))
DB_FILE = os.environ.get("RING_OUTCOME_DB", os.path.join(rc.PORTAL_DIR, "ring_outcomes.db"))
WA_DIR = os.environ.get("RING_WA_DIR", "/root/wa")
WA_ENV = os.environ.get("RING_WA_ENV", os.path.join(WA_DIR, ".env"))
KEY_DIR = os.environ.get("FU_KEY_DIR", WA_DIR)
OUTCOMES_TAB = "Followup_Outcomes"
ESCAL_TAB = "Followup_Escalations"
AGENTS_TAB = "Agents"
REMIND_AFTER = int(os.environ.get("RING_REMIND_SECONDS", "600"))     # the owner's 10 minutes
SWEEP_EVERY = 30

# --- the tracker's own headers, copied, never re-invented (WebApp.gs 885, 890) ---
FU_OUTCOME_HEADERS = ['When', 'Key', 'Patient', 'Mobile', 'Section', 'Outcome', 'Source', 'Days', 'Expected Date',
                      'Detail', 'Handled By', 'Agent Ext', 'Settle', 'Identity', 'Reason', 'Channel', 'For Whom', 'Clinic ID']
FU_ESCAL_HEADERS = ['Raised', 'Key', 'Patient', 'Clinic ID', 'Diagnosis', 'Mobile', 'Last Visit', 'Reason', 'Detail',
                    'Raised By', 'Status', 'Resolution', 'Resolved When']
SOURCE_MARK = "ring"            # the Source column, like the one-tap UI's 'K' (Callconsole.gs 1197)

# --- the choices. code -> (Hindi label, the tracker's outcome code, settle, identity, extra) ---
# Known patient: Appointment booked FIRST (owner, 21/22-Sep), then the tracker's own one-tap set in its own
# order (Dashboard.html K_ORDER; Callconsole.gs K_CODE_MAP), K_TO_DOCTOR = the 'problem' escalation.
KNOWN = [
    ("appointment_booked", "अपॉइंटमेंट बुक हो गया",        # अपॉइंटमेंट बुक हो गया
     "in_appointment_booked", "settle", "known"),
    ("K_COMING", "मरीज़ आ रहे हैं", "k_coming", "settle", "known"),               # मरीज़ आ रहे हैं
    ("K_NOT_COMING", "नहीं आएँगे", "k_not_coming", "settle", "known"),                        # नहीं आएँगे
    ("K_CALL_AGAIN", "बात हुई — फिर call करना", "k_call_again", "retry", "known"),   # बात हुई — फिर call करना
    ("K_NO_CONTACT", "बात नहीं हो पाई", "no_answer", "retry", "known"),           # बात नहीं हो पाई
    ("K_TO_DOCTOR", "डॉक्टर को दिखाना है", "problem", "escalate", "known"),   # डॉक्टर को दिखाना है
]
# New number: the D225 lead set, Appointment booked first (Dashboard.html L_ORDER / L_LABELS, S140 build).
# 'escalated' rides the tracker's Doctor/urgent path (identity surgery_enquiry: escalation + the instant buzz).
NEW = [
    ("appointment_booked", "अपॉइंटमेंट बुक हो गया", "in_appointment_booked", "settle", "new_patient"),
    ("will_come", "सोच कर बताएँगे", "in_will_come", "settle", "new_patient"),                    # सोच कर बताएँगे
    ("enquiry_only", "जानकारी दे दी", "in_enquiry_only", "settle", "new_patient"),                    # जानकारी दे दी
    ("needs_callback", "फिर call करना है", "in_needs_callback", "retry", "new_patient"),                  # फिर call करना है
    ("escalated", "\U0001F6A8 डॉक्टर — surgery / urgent", "in_escalated", "escalate", "surgery_enquiry"),   # 🚨 डॉक्टर — surgery / urgent
    ("no_action", "काम का नहीं", "in_no_action", "settle", "new_patient"),                              # काम का नहीं
]
LABEL = {c[0]: c[1] for c in KNOWN + NEW}
_DIGITS = re.compile(r"\D+")


def now_ist():
    return datetime.now(IST)


def _fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M")


# ------------------------------------------------------------------ the database
def db(path=None):
    con = sqlite3.connect(path or DB_FILE, timeout=5)
    con.row_factory = sqlite3.Row
    return con


# S497: what the after-call list adds to `outcome`. Added by lazy ALTER, never dropped, never retyped (the estate's own
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


def init_db(path=None):
    p = path or DB_FILE
    new = not os.path.exists(p)
    con = db(p)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS call (
      sid TEXT PRIMARY KEY, mobile TEXT, caller_json TEXT, dialed_json TEXT, answered_by TEXT,
      began_at INTEGER, ended_at INTEGER, status TEXT, day_key TEXT,
      card_pushed_to TEXT, remind_due INTEGER, reminded_at INTEGER, closed_by TEXT, closed_at INTEGER);
    CREATE TABLE IF NOT EXISTS outcome (
      id INTEGER PRIMARY KEY AUTOINCREMENT, sid TEXT, row_key TEXT, day_key TEXT, mobile TEXT, patient TEXT,
      clinic_id TEXT, last_visit TEXT, login TEXT, handler TEXT, code TEXT, outcome_code TEXT, settle TEXT,
      identity TEXT, detail TEXT, when_ist TEXT, created_at INTEGER,
      mirrored_at INTEGER, mirror_tries INTEGER DEFAULT 0, mirror_err TEXT, escal_mirrored INTEGER DEFAULT 0);
    CREATE INDEX IF NOT EXISTS ix_outcome_sid ON outcome(sid);
    CREATE INDEX IF NOT EXISTS ix_call_day ON call(day_key);
    CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT, by_whom TEXT, at TEXT);
    CREATE TABLE IF NOT EXISTS appt_event (
      id INTEGER PRIMARY KEY AUTOINCREMENT, outcome_id INTEGER NOT NULL, kind TEXT NOT NULL, old_value TEXT,
      new_value TEXT, by_login TEXT, by_name TEXT, at_ist TEXT, created_at INTEGER);
    CREATE INDEX IF NOT EXISTS ix_appt_event_outcome ON appt_event(outcome_id);
    """)
    _s497_columns(con)                           # S497: the list's columns on `outcome`, added once, never dropped
    con.commit()
    con.close()
    if new:
        try:
            os.chmod(p, 0o600)
        except OSError:
            pass


def record_call(sid, mobile, caller, dialed, path=None):
    """dial_begin: the call exists. Idempotent."""
    init_db(path)
    con = db(path)
    con.execute("INSERT OR IGNORE INTO call(sid, mobile, caller_json, dialed_json, began_at, day_key) VALUES(?,?,?,?,?,?)",
                (sid, rc.mobile10(mobile) or str(mobile or ""), json.dumps(caller or {}, ensure_ascii=False),
                 json.dumps(dialed or {}, ensure_ascii=False), int(time.time()), now_ist().strftime("%Y%m%d")))
    con.execute("UPDATE call SET dialed_json=? WHERE sid=? AND (dialed_json IS NULL OR dialed_json='{}')",
                (json.dumps(dialed or {}, ensure_ascii=False), sid))
    con.commit()
    con.close()


def record_answered(sid, login, path=None):
    init_db(path)
    con = db(path)
    con.execute("UPDATE call SET answered_by=? WHERE sid=?", (login, sid))
    con.commit()
    con.close()


def record_end(sid, status, dialed, pushed_to, path=None):
    """call.end: who gets the outcome card and when the reminder falls due. Returns the row."""
    init_db(path)
    con = db(path)
    con.execute("UPDATE call SET ended_at=?, status=?, dialed_json=COALESCE(NULLIF(dialed_json,'{}'),?), card_pushed_to=?, remind_due=? WHERE sid=?",
                (int(time.time()), status, json.dumps(dialed or {}, ensure_ascii=False),
                 json.dumps(pushed_to or [], ensure_ascii=False),
                 (int(time.time()) + REMIND_AFTER) if (status != "missed" and pushed_to) else None, sid))
    con.commit()
    row = con.execute("SELECT * FROM call WHERE sid=?", (sid,)).fetchone()
    con.close()
    return dict(row) if row else None


def get_call(sid, path=None):
    init_db(path)
    con = db(path)
    row = con.execute("SELECT * FROM call WHERE sid=?", (sid,)).fetchone()
    con.close()
    return dict(row) if row else None


def get_outcome(sid, path=None):
    init_db(path)
    con = db(path)
    row = con.execute("SELECT * FROM outcome WHERE sid=? ORDER BY id DESC LIMIT 1", (sid,)).fetchone()
    con.close()
    return dict(row) if row else None


def close_call(sid, by, path=None):
    con = db(path)
    con.execute("UPDATE call SET closed_by=?, closed_at=?, remind_due=NULL WHERE sid=? AND closed_at IS NULL",
                (by, int(time.time()), sid))
    con.commit()
    con.close()


# ------------------------------------------------------------------ the choices for one call
def choices_for(call):
    caller = json.loads(call.get("caller_json") or "{}")
    known = bool(caller.get("patients"))
    return ("known" if known else "new"), (KNOWN if known else NEW)


def file_outcome(sid, code, login, handler, detail="", path=None, now=None):
    """The staff member's one tap. Writes the row FIRST here; the mirror runs after. Returns (ok, msg, row)."""
    call = get_call(sid, path)
    if not call:
        return False, "call not found", None
    kind, opts = choices_for(call)
    opt = next((o for o in opts if o[0] == code), None)
    if not opt:
        return False, "unknown choice", None
    prev = get_outcome(sid, path)
    if prev:
        return False, "already filed", prev
    caller = json.loads(call.get("caller_json") or "{}")
    ps = caller.get("patients") or []
    p0 = ps[0] if ps else {}
    mobile = rc.mobile10(call.get("mobile")) or str(call.get("mobile") or "")
    t = now or now_ist()
    day_key = t.strftime("%Y%m%d")
    row = {
        "sid": sid, "row_key": "IN_%s_%s" % (mobile, day_key), "day_key": day_key, "mobile": mobile,
        "patient": (p0.get("name") or "").strip(), "clinic_id": str(p0.get("clinic_id") or ""),
        "last_visit": str(p0.get("last_visit") or ""), "login": login, "handler": handler or login,
        "code": opt[0], "outcome_code": opt[2], "settle": opt[3], "identity": opt[4],
        "detail": (detail or "").strip()[:300], "when_ist": _fmt(t), "created_at": int(time.time()),
    }
    init_db(path)
    con = db(path)
    cur = con.execute("INSERT INTO outcome(sid,row_key,day_key,mobile,patient,clinic_id,last_visit,login,handler,code,"
                      "outcome_code,settle,identity,detail,when_ist,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (row["sid"], row["row_key"], row["day_key"], row["mobile"], row["patient"], row["clinic_id"],
                       row["last_visit"], row["login"], row["handler"], row["code"], row["outcome_code"], row["settle"],
                       row["identity"], row["detail"], row["when_ist"], row["created_at"]))
    row["id"] = cur.lastrowid
    con.execute("UPDATE call SET closed_by=?, closed_at=?, remind_due=NULL WHERE sid=?", ("outcome", int(time.time()), sid))
    con.commit()
    con.close()
    return True, "ok", row


# ------------------------------------------------------------------ the mirror into the Google tracker
def _find_key():
    """The one service-account key in /root/wa, found by content (push_followups_vps.find_key)."""
    import glob
    keys = []
    for p in glob.glob(os.path.join(KEY_DIR, "*.json")):
        try:
            with open(p, "r", encoding="utf-8") as fh:
                o = json.load(fh)
            if isinstance(o, dict) and o.get("type") == "service_account" and o.get("client_email"):
                keys.append(p)
        except Exception:
            pass
    return keys[0] if len(keys) == 1 else None


def _sheet_id():
    """The tracker's spreadsheet id, read from push_followups_vps.py's own constant (one source, never a copy)."""
    v = os.environ.get("FU_SHEET_ID", "").strip()
    if v:
        return v
    try:
        with open(os.path.join(WA_DIR, "push_followups_vps.py"), "r", encoding="utf-8") as fh:
            m = re.search(r'^SHEET_ID\s*=\s*"([^"]+)"', fh.read(), re.M)
        return m.group(1) if m else ""
    except Exception:
        return ""


_SHEET_CACHE = {"sh": None, "t": 0}


def open_sheet(client=None):
    """gspread Spreadsheet, cached 10 minutes. client= lets the walk inject a fake."""
    if client is not None:
        return client
    if _SHEET_CACHE["sh"] is not None and time.time() - _SHEET_CACHE["t"] < 600:
        return _SHEET_CACHE["sh"]
    import gspread
    key = _find_key()
    sid = _sheet_id()
    if not (key and sid):
        raise RuntimeError("no key or sheet id")
    sh = gspread.service_account(filename=key).open_by_key(sid)
    _SHEET_CACHE.update({"sh": sh, "t": time.time()})
    return sh


def _ws(sh, title, headers):
    try:
        return sh.worksheet(title)
    except Exception:
        ws = sh.add_worksheet(title=title, rows=200, cols=len(headers))
        ws.append_row(headers, value_input_option="RAW")
        return ws


def _agent_ext(sh, handler):
    """Agent Ext from the tracker's own Agents tab, by name; '' when unknown. Best effort."""
    try:
        vals = sh.worksheet(AGENTS_TAB).get_all_values()
        head = [str(h or "").strip().lower() for h in vals[0]]
        ie, iname = head.index("ext"), head.index("name")
        for r in vals[1:]:
            if str(r[iname] or "").strip().lower() == str(handler or "").strip().lower():
                return _DIGITS.sub("", str(r[ie] or ""))
    except Exception:
        pass
    return ""


def outcome_rows(row, ext=""):
    """(Followup_Outcomes row, Followup_Escalations row or None) -- the tracker's own shapes."""
    esc_reason = ""
    if row["settle"] == "escalate":
        if row["identity"] == "surgery_enquiry":
            esc_reason = "Incoming: Doctor/urgent (surgery / fracture / accident / severe pain)"
        else:
            esc_reason = "Problem / needs attention"          # K_TO_DOCTOR = the 'problem' outcome (WebApp.gs 1227)
    detail = row["detail"]
    if row["code"] == "K_TO_DOCTOR":
        detail = "[K] डॉक्टर को दिखाना है" + ((" — " + detail) if detail else "")
    is_k = row["code"].startswith("K_")
    o = [row["when_ist"], row["row_key"], row["patient"], row["mobile"], "Incoming", row["outcome_code"],
         "K" if is_k else SOURCE_MARK, "", "", detail, row["handler"], ext, row["settle"],
         "" if is_k else row["identity"], "", "", "", "" if is_k else row["clinic_id"]]
    e = None
    if esc_reason:
        e = [row["when_ist"], row["row_key"], row["patient"], row["clinic_id"], "", row["mobile"], row["last_visit"],
             esc_reason, detail, row["handler"], "OPEN", "", ""]
    return o, e


def _ntfy_urgent(row):
    """The tracker's instant buzz for the Doctor/urgent path (WebApp.gs notifyUrgentIncoming_), same topic."""
    env = rc.load_env(WA_ENV)
    topic = env.get("NTFY_TOPIC", "")
    if not topic:
        return False
    server = (env.get("NTFY_SERVER") or "https://ntfy.sh").rstrip("/")
    body = "%s %s - by %s (via call pop-up)" % (row["patient"] or "new patient", row["mobile"], row["handler"])
    req = urllib.request.Request(server + "/" + topic, data=body.encode("utf-8"), method="POST")
    req.add_header("Title", "URGENT incoming call")
    req.add_header("Priority", "high")
    req.add_header("Tags", "rotating_light")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return 200 <= r.status < 300
    except Exception:
        return False


def mirror_one(row, client=None, path=None):
    """One outcome into the tracker. Records success or the error on the row. Never raises."""
    con = db(path)
    try:
        sh = open_sheet(client)
        ext = _agent_ext(sh, row["handler"])
        o, e = outcome_rows(row, ext)
        _ws(sh, OUTCOMES_TAB, FU_OUTCOME_HEADERS).append_row(o, value_input_option="RAW")
        if e is not None:
            _ws(sh, ESCAL_TAB, FU_ESCAL_HEADERS).append_row(e, value_input_option="RAW")
        con.execute("UPDATE outcome SET mirrored_at=?, mirror_tries=mirror_tries+1, mirror_err=NULL, escal_mirrored=? WHERE id=?",
                    (int(time.time()), 1 if e is not None else 0, row["id"]))
        con.commit()
        con.close()
        if row.get("identity") == "surgery_enquiry":
            _ntfy_urgent(row)
        return True
    except Exception as ex:  # noqa: BLE001
        con.execute("UPDATE outcome SET mirror_tries=mirror_tries+1, mirror_err=? WHERE id=?",
                    ((type(ex).__name__ + ": " + str(ex))[:200], row["id"]))
        con.commit()
        con.close()
        return False


def mirror_pending(client=None, path=None, limit=20):
    """Every outcome not yet in the tracker (the sweeper's job; also called right after a tap)."""
    init_db(path)
    con = db(path)
    rows = [dict(r) for r in con.execute("SELECT * FROM outcome WHERE mirrored_at IS NULL AND mirror_tries < 200 ORDER BY id LIMIT ?", (limit,))]
    con.close()
    done = 0
    for r in rows:
        if mirror_one(r, client=client, path=path):
            done += 1
    return done, len(rows)


def tracker_has_outcome(row_key, client=None, since=""):
    """True when the Google tracker already holds an outcome for IN_<phone>_<day> typed there at or after
    `since` ('yyyy-MM-dd HH:mm'; '' = any time). The same number twice in a day shares one key in the tracker
    (its own rule), so only an outcome written after THIS call ended counts for this call."""
    try:
        sh = open_sheet(client)
        ws = sh.worksheet(OUTCOMES_TAB)
        whens, keys = ws.col_values(1), ws.col_values(2)
        for i, k in enumerate(keys):
            if str(k).strip() == row_key and (not since or str(whens[i] if i < len(whens) else "").strip()[:16] >= since):
                return True
        return False
    except Exception:
        return False


# ------------------------------------------------------------------ the 10-minute reminder (ring_hook's sweeper)
def due_reminders(path=None, now=None):
    init_db(path)
    con = db(path)
    t = int(now or time.time())
    rows = [dict(r) for r in con.execute("SELECT * FROM call WHERE remind_due IS NOT NULL AND remind_due<=? AND reminded_at IS NULL AND closed_at IS NULL", (t,))]
    con.close()
    return rows


def mark_reminded(sid, path=None):
    con = db(path)
    con.execute("UPDATE call SET reminded_at=?, remind_due=NULL WHERE sid=?", (int(time.time()), sid))
    con.commit()
    con.close()


def reminder_payload(call):
    caller = json.loads(call.get("caller_json") or "{}")
    ps = caller.get("patients") or []
    who = (ps[0].get("name") if ps else "") or ("…" + str(call.get("mobile") or "")[-4:])
    return {"kind": "outcome", "tag": "call-" + call["sid"],
            "title": "Outcome बाकी — " + who,                              # Outcome बाकी — <name / last 4>
            "body": "क्या हुआ? एक tap में बताएँ",   # क्या हुआ? एक tap में बताएँ
            "url": "/portal/ring/outcome?s=" + call["sid"], "ts": int(time.time() * 1000), "ttl": 1800,
            "requireInteraction": True, "renotify": True}


def sweep_once(push_user, client=None, path=None, now=None, log=None):
    """One pass: mirror what waits; remind what is due. push_user(login, payload) -> (sent, failed)."""
    out = {"mirrored": 0, "reminded": 0, "closed_by_tracker": 0}
    try:
        out["mirrored"], _ = mirror_pending(client=client, path=path)
    except Exception:
        pass
    for call in due_reminders(path, now):
        if get_outcome(call["sid"], path):
            close_call(call["sid"], "outcome", path)
            continue
        mobile = rc.mobile10(call.get("mobile")) or str(call.get("mobile") or "")
        row_key = "IN_%s_%s" % (mobile, call.get("day_key") or now_ist().strftime("%Y%m%d"))
        since = _fmt(datetime.fromtimestamp(int(call.get("ended_at") or time.time()), IST))   # same minute counts
        if tracker_has_outcome(row_key, client, since):
            close_call(call["sid"], "tracker", path)
            out["closed_by_tracker"] += 1
            continue
        logins = json.loads(call.get("card_pushed_to") or "[]")
        payload = reminder_payload(call)
        for login in logins:
            try:
                push_user(login, payload)
            except Exception:
                pass
        mark_reminded(call["sid"], path)
        out["reminded"] += 1
        if log:
            log({"type": "remind", "session": call["sid"], "users": logins})
    return out


def start_sweeper(push_user, log=None, path=None):
    """ring_hook calls this once at import: a daemon thread, every 30 s. Restart-safe -- everything is in the db."""
    def run():
        while True:
            try:
                sweep_once(push_user, path=path, log=log)
            except Exception:
                pass
            time.sleep(SWEEP_EVERY)
    th = threading.Thread(target=run, daemon=True)
    th.start()
    return th


# ------------------------------------------------------------------ per-person counts (step 3)
def counts(day_key=None, path=None):
    """Per login for one day: rung · answered · outcome logged · outcome missing · appointments. Numbers only."""
    init_db(path)
    day_key = day_key or now_ist().strftime("%Y%m%d")
    con = db(path)
    per = {}
    def slot(u):
        return per.setdefault(u, {"rung": 0, "answered": 0, "logged": 0, "missing": 0, "appointments": 0})
    for c in con.execute("SELECT * FROM call WHERE day_key=?", (day_key,)):
        dialed = json.loads(c["dialed_json"] or "{}")
        for u in dialed:
            slot(u)["rung"] += 1
        if c["answered_by"]:
            s = slot(c["answered_by"])
            s["answered"] += 1
            o = con.execute("SELECT code FROM outcome WHERE sid=? LIMIT 1", (c["sid"],)).fetchone()
            if o or c["closed_by"] == "tracker":
                s["logged"] += 1
            elif c["status"] and c["status"] != "missed":
                s["missing"] += 1
            if o and o["code"] == "appointment_booked":
                s["appointments"] += 1
    tot = {"calls": con.execute("SELECT COUNT(*) FROM call WHERE day_key=?", (day_key,)).fetchone()[0],
           "missed": con.execute("SELECT COUNT(*) FROM call WHERE day_key=? AND status='missed'", (day_key,)).fetchone()[0],
           "unmirrored": con.execute("SELECT COUNT(*) FROM outcome WHERE mirrored_at IS NULL").fetchone()[0]}
    con.close()
    return {"day": day_key, "per_person": per, "totals": tot}


# ------------------------------------------------------------------ S497: the after-call list (tile 'Call ke baad')
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


# ------------------------------------------------------------------ the portal routes
PAGE = """<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Call outcome</title><style>
body{margin:0;background:#0f172a;color:#e5eefb;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:520px;margin:0 auto;padding:16px}
.card{background:#1e293b;border:1px solid #334155;border-radius:14px;padding:14px 16px;margin-bottom:12px}
.who{font-size:20px;font-weight:700}.sub{color:#94a3b8;font-size:14px;margin-top:4px}
.btn{display:block;width:100%%;box-sizing:border-box;text-align:left;background:#2563eb;color:#fff;border:0;border-radius:12px;padding:14px 16px;font-size:17px;font-weight:600;margin:8px 0}
.btn.mut{background:#334155;color:#cbd5e1}.btn.urg{background:#b91c1c}.btn.esc{background:#b45309}
.note{width:100%%;box-sizing:border-box;background:#0f172a;color:#e5eefb;border:1px solid #334155;border-radius:10px;padding:10px;font-size:15px;margin-top:6px}
.ok{background:#14532d;border-color:#166534;font-size:18px}.err{background:#7f1d1d}
a.lnk{color:#93c5fd;font-size:14px}
</style></head><body><div class="wrap">%s</div>
<script>
function go(code){var b=document.querySelectorAll('.btn');b.forEach(function(x){x.disabled=true});
fetch('/portal/ring/outcome',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({s:SID,code:code,note:(document.getElementById('note')||{}).value||''})})
.then(function(r){return r.json()}).then(function(j){ if(j.ok){location.replace('/portal/ring/outcome?s='+SID);} else {alert(j.msg||'error'); b.forEach(function(x){x.disabled=false});} })
.catch(function(){alert('server se jawab nahi'); b.forEach(function(x){x.disabled=false});});}
</script></body></html>"""


def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def _page(body, sid=""):
    """PAGE with the call's id in its script and the body in its place. S497 mends F-797: the id used to be put in by
    replacing the three letters S-I-D through the WHOLE page, after the patient's name was already in it, so a name
    written SIDDIQUI or SIDDHARTH lost them. The id now goes into the TEMPLATE and the body is placed after it -- and
    the id is written so that nothing in it can close the script early (_json_js)."""
    mark = "\x00S497-BODY\x00"
    return (PAGE % mark).replace("SID", _json_js(sid)).replace(mark, body)


def render_page(call, outcome, sid):
    caller = json.loads(call.get("caller_json") or "{}") if call else {}
    title, text = rc.caller_card(caller) if call else ("", "")
    head = '<div class="card"><div class="who">%s</div><div class="sub">%s</div></div>' % (_esc(title), _esc(text))
    if not call:
        body = head + '<div class="card err">यह call नहीं मिली — Call Tracker में लिखें</div>'   # यह call नहीं मिली — Call Tracker में लिखें
    elif outcome:
        body = head + ('<div class="card ok">✓ लिख गया: <b>%s</b><div class="sub">%s · %s%s</div></div>'   # ✓ लिख गया
                       % (_esc(LABEL.get(outcome["code"], outcome["code"])), _esc(outcome["when_ist"]), _esc(outcome["handler"]),
                          "" if outcome.get("mirrored_at") else " · tracker में थोड़ी देर में"))   # tracker में थोड़ी देर में
    elif call.get("status") == "missed":
        body = head + '<div class="card">❌ Missed — call back करें; outcome Call Tracker में</div>'
    else:
        kind, opts = choices_for(call)
        btns = []
        for code, label, _oc, settle, ident in opts:
            cls = "btn" + (" urg" if ident == "surgery_enquiry" else (" esc" if settle == "escalate" else (" mut" if code in ("no_action", "K_NO_CONTACT") else "")))
            btns.append('<button class="%s" onclick="go(\'%s\')">%s</button>' % (cls, code, _esc(label)))
        extra = ""
        if kind == "new":
            extra = '<a class="lnk" href="/portal/go/call-tracker">पुराने मरीज़ — नया नंबर? Call Tracker में जोड़ें →</a>'   # पुराने मरीज़ — नया नंबर? Call Tracker में जोड़ें →
        body = head + ('<div class="card"><div class="sub" style="margin-bottom:6px">क्या हुआ? एक tap</div>%s'   # क्या हुआ? एक tap
                       '<input class="note" id="note" placeholder="note (optional)">%s</div>' % ("".join(btns), extra))
    return _page(body, sid)


def install(app, login_required, sso_user, path=None):
    from flask import request, jsonify, make_response

    @app.route("/portal/ring/outcome", methods=["GET"])
    @login_required
    def ring_outcome_page():
        sid = str(request.args.get("s") or "").strip()[:80]
        call = get_call(sid, path) if sid else None
        outcome = get_outcome(sid, path) if call else None
        # S497: after 'Appointment book ho gaya' the card asks the one optional day -- for a doctor, and for those shown
        # the tile once the list is on. For everyone else, and for every other outcome, the page is the one it was.
        # An appointment booked before the list's first day is not followed: its card is the old card too.
        if outcome and outcome.get("code") == APPT_CODE and list_access(sso_user(request) or {}, path) in ("doctor", "staff") \
                and appt_followed(outcome, path):
            resp = make_response(render_appt_card(call, outcome, sid, path))
        else:
            resp = make_response(render_page(call, outcome, sid))
        resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.route("/portal/ring/outcome", methods=["POST"])
    @login_required
    def ring_outcome_post():
        who = sso_user(request) or {}
        login = who.get("user", "")
        if not login:
            return jsonify({"ok": False, "msg": "no login"}), 401
        body = request.get_json(silent=True) or {}
        sid = str(body.get("s") or "").strip()[:80]
        code = str(body.get("code") or "").strip()[:40]
        agents = rc.load_agents()
        handler = next(((a or {}).get("name") for a in agents.values() if (a or {}).get("user") == login), None) or who.get("name") or login
        ok, msg, row = file_outcome(sid, code, login, handler, str(body.get("note") or ""), path)
        if ok:
            threading.Thread(target=mirror_pending, kwargs={"path": path}, daemon=True).start()
        return jsonify({"ok": ok, "msg": msg})

    # ---- S497: the after-call list -----------------------------------------------------------------------------
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

    @app.route("/portal/ring/counts")
    @login_required
    def ring_counts():
        who = sso_user(request) or {}
        if who.get("role") != "doctor":
            return jsonify({"ok": False}), 403
        day = str(request.args.get("day") or "").strip()[:8] or None
        c = counts(day, path)
        if request.args.get("json"):
            return jsonify({"ok": True, **c})
        rows = "".join("<tr><td>%s</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td></tr>"
                       % (_esc(u), v["rung"], v["answered"], v["logged"], v["missing"], v["appointments"])
                       for u, v in sorted(c["per_person"].items()))
        html = ('<div class="card"><div class="who">\U0001F4DE Calls · %s</div><div class="sub">calls %d · missed %d · outcomes waiting for the tracker %d</div></div>'
                '<div class="card"><table style="width:100%%;border-collapse:collapse;font-size:15px"><tr style="color:#94a3b8;text-align:left"><th>who</th><th>rang</th><th>answered</th><th>outcome</th><th>missing</th><th>appt</th></tr>%s</table>'
                '<div class="sub" style="margin-top:8px">day=YYYYMMDD in the address for another day · numbers only, no patient detail</div></div>'
                % (_esc(c["day"]), c["totals"]["calls"], c["totals"]["missed"], c["totals"]["unmirrored"], rows or "<tr><td colspan=6>—</td></tr>"))
        return _page(html)
