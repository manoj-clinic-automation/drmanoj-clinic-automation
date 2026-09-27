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
    """)
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
    return (PAGE % body).replace("SID", json.dumps(sid))


def install(app, login_required, sso_user, path=None):
    from flask import request, jsonify, make_response

    @app.route("/portal/ring/outcome", methods=["GET"])
    @login_required
    def ring_outcome_page():
        sid = str(request.args.get("s") or "").strip()[:80]
        call = get_call(sid, path) if sid else None
        outcome = get_outcome(sid, path) if call else None
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
                % (c["day"], c["totals"]["calls"], c["totals"]["missed"], c["totals"]["unmirrored"], rows or "<tr><td colspan=6>—</td></tr>"))
        return (PAGE % html).replace("SID", '""')
