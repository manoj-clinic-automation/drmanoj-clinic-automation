#!/usr/bin/env python3
"""
call_hook_capture.py - MyOperator call-webhook receiver for Dr. Manoj Agarwal Clinic.
PHASE B (the "duration gate", D77): passive capture PLUS a PHI-clean Call_Durations feed.

v2.0  --  Session 125  --  DUAL-KEY ACCEPTANCE + REJECTION VISIBILITY
  Changed from v1 (03-Jul-2026) in exactly three places, all inside the secret
  gate. Capture, extraction, upsert, and the Sheet path are untouched.

    1. The gate now accepts CALLHOOK_SECRET *or* CALLHOOK_SECRET_PREV.
       Either key opens the door. This means the MyOperator panel and this
       server may hold different keys during a rotation without the webhook
       failing. A hard cutover is no longer possible.

    2. When a request arrives on the PREV key, a WARN line is logged naming
       which key was used. That is the signal that one side of the rotation
       is not finished. It is the warning that did not exist on 06-08 Jul.

    3. A rejected request is now WRITTEN DOWN BEFORE it is refused, to
       call_hook_rejects/YYYY-MM-DD.jsonl. Metadata only -- masked key label,
       source ip, path, method, timestamp. Never the key, never the body.
       On 06-08 Jul 2026 this receiver returned 403 four thousand four hundred
       and forty-nine times and left no trace anywhere. A receptionist found
       it, three clinic days later. That is the hole this closes.

  Also: a startup sanity check that shouts if the configured secret contains
  whitespace, an '=', or is implausibly long. On 07-Jul-2026 CALLHOOK_SECRET
  held 61 characters -- the real 12-char key with `FU_UPLOAD_SECRET=<frag>`
  appended to it. Composition confirmed: 12 + 17 + 32 = 61, non-alphanumerics
  `@ _ _ =` in that order. MECHANISM UNKNOWN. It was a DUPLICATION, not a
  deletion: the separate FU_UPLOAD_SECRET line survives intact in the 07-Jul
  .env backup, and a lost newline would have consumed it. So it was NOT a lost
  newline, and it was NOT `sed` -- `sed -i '17s'` was the S94 repair that
  REMOVED the run-on. Two wrong causes have been recorded for these 61
  characters already (incident report v1: `sed`; S125 correction: lost
  newline). Record no third until something proves it. This check would have
  caught the value the moment a worker read the file, instead of after two
  clinic days.

WHAT IT DOES
  A tiny always-on web service. MyOperator POSTs each call-lifecycle event here
  (we subscribe to call.end and call.summary). For every event it:
    1. Writes the ENTIRE raw body to a daily .jsonl log file (the safety net).
    2. If it is one of OUR outbound OBD calls (category == "obd" AND a
       client_ref_id is present), it UPSERTS one row into the "Call_Durations"
       tab of the Clinic Callback Tracker, keyed on client_ref_id, so call.end
       and call.summary for the same call collapse to a single row.

  The dashboard (Phase C) will read that tab after a call to decide whether an
  outcome may be logged: it compares the CUSTOMER leg's talk_duration against a
  threshold. Below threshold / not answered -> missed state, no outcome.

WHY client_ref_id (not ref_id)
  Confirmed from a real captured body on 03 Jul 2026: the webhook's `ref_id` is
  MyOperator's OWN uuid; the value our dialer stamps (make_reference_id in
  call_api.py) comes back as `client_ref_id`. THAT is the join key. `ref_id` and
  `session_id` are stored too, as backups.

PHI / PRIVACY (important)
  - The Call_Durations tab holds NO phone number -- only ref-ids, status,
    durations, recording filename, timestamps. Patient identity stays out of it.
  - The raw .jsonl log DOES contain numbers (it is the vendor's raw push) -> the
    folder is owner-only (700) and each file 600, exactly like wa_receiver.
  - The reject log holds NO body and NO key -- only an md5[:6] label of the key
    that was offered, so two wrong keys can be told apart without either being
    readable. Same 700/600 permissions.
  - Optional shared secret (CALLHOOK_SECRET) blocks strangers from posting.

DEGRADE-SAFE
  - Google Sheets write is best-effort. If the key/tab/network isn't ready, the
    event is still raw-logged and we still return 200. We NEVER break the webhook
    and NEVER retry-storm. The raw log is always the recovery source.
  - Reject logging is best-effort and throttled. It can never raise, and it can
    never fill the disk during a 403 storm or a hostile scan.

CONFIG  (read from /root/wa/.env, a local .env, or the environment)
  CALLHOOK_SECRET      (optional) shared secret; if set, the webhook URL must
                                  carry ?key=<secret> (or header X-Webhook-Key)
  CALLHOOK_SECRET_PREV (optional) the PREVIOUS secret, also accepted. Set this
                                  before rotating; clear it once the panel has
                                  been updated and the WARN lines stop.
  CALLHOOK_SHEET_ID    (optional) spreadsheet id   [default: the Clinic tracker id]
                                  (WA_SHEET_ID is also accepted)
  CALLHOOK_SA_KEY      (optional) full path to the service-account JSON key
                                  (WA_SA_KEY is also accepted; else auto-discovered
                                   as the single service_account *.json in /root/wa)
  CALLHOOK_TAB         (optional) sheet tab name          [default: Call_Durations]
  CALLHOOK_PORT        (optional) port to listen on       [default: 8098]
  CALLHOOK_HOST        (optional) bind address            [default: 127.0.0.1]
  CALLHOOK_RAW_LOG_DIR (optional) raw-log folder   [default: <script dir>/call_hook_logs]
  CALLHOOK_REJECT_DIR  (optional) reject-log folder [default: <script dir>/call_hook_rejects]

ROTATING THE KEY (the whole point of v2)
  1. Put the CURRENT key into CALLHOOK_SECRET_PREV as well. Restart. Nothing
     changes -- both variables hold the same value, both are accepted.
  2. Put the NEW key into CALLHOOK_SECRET. Restart. Deliveries keep arriving
     on the old key, each one logging a WARN naming key_<label>.
  3. Update the MyOperator panel to the new key. The WARN lines stop.
  4. Clear CALLHOOK_SECRET_PREV. Restart. Rotation complete.
  At no point in that sequence can a mismatch stop the clinic.

RUN
  Quick test:  /root/wa/venv/bin/python3 call_hook_capture.py
  Production:  /root/wa/venv/bin/gunicorn -w 1 -b 127.0.0.1:8098 call_hook_capture:app

  NOTE on `-w 1` with no --preload: the worker reads .env once, at import. A
  change to .env therefore takes effect at an unpredictable later moment -- the
  next worker respawn -- with nothing to connect cause to effect. Dual-key
  acceptance is what makes that harmless. Do not remove it.

SELFTEST
  /root/wa/venv/bin/python3 call_hook_capture.py --selftest
  Offline. No network, no Sheet, no .env. Exercises the gate only.
"""

import os
import re
import sys
import glob
import json
import hmac
import hashlib
import threading
import datetime
from flask import Flask, request, jsonify

try:
    import gspread
    from gspread.exceptions import WorksheetNotFound
    _GSPREAD_OK = True
except Exception:                      # noqa: BLE001
    _GSPREAD_OK = False
    WorksheetNotFound = Exception      # placeholder so except clauses parse


# --------------------------------------------------------------------------
# tiny .env loader (reads /root/wa/.env then a local .env; env wins)
# --------------------------------------------------------------------------
def _load_env():
    here = os.path.dirname(os.path.abspath(__file__))
    for path in ("/root/wa/.env", os.path.join(here, ".env")):
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except OSError:
            pass

_load_env()

_HERE       = os.path.dirname(os.path.abspath(__file__))
SECRET      = os.environ.get("CALLHOOK_SECRET", "").strip()
SECRET_PREV = os.environ.get("CALLHOOK_SECRET_PREV", "").strip()
PORT        = int(os.environ.get("CALLHOOK_PORT", "8098"))
HOST        = os.environ.get("CALLHOOK_HOST", "127.0.0.1").strip() or "127.0.0.1"
RAW_DIR     = os.environ.get("CALLHOOK_RAW_LOG_DIR", "").strip() \
    or os.path.join(_HERE, "call_hook_logs")
REJECT_DIR  = os.environ.get("CALLHOOK_REJECT_DIR", "").strip() \
    or os.path.join(_HERE, "call_hook_rejects")
SHEET_ID    = os.environ.get("CALLHOOK_SHEET_ID", "").strip() \
    or os.environ.get("WA_SHEET_ID", "").strip() \
    or "1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0"
SA_KEY      = os.environ.get("CALLHOOK_SA_KEY", "").strip() \
    or os.environ.get("WA_SA_KEY", "").strip()
TAB         = os.environ.get("CALLHOOK_TAB", "Call_Durations").strip() or "Call_Durations"
SCOPES      = ["https://www.googleapis.com/auth/spreadsheets"]
IST         = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

# A secret longer than this is almost certainly a corrupted .env line, not a key.
SECRET_SANE_MAX_LEN = 40

# Reject-log throttle: log every reject up to this many per day, then 1 in 100.
# A 403 storm must be visible without being able to fill the disk.
REJECT_LOG_FULL_UPTO = 500
REJECT_LOG_THEN_EVERY = 100

HEADER = [
    "client_ref_id", "ref_id", "session_id", "category", "status",
    "total_duration", "customer_result", "customer_talk_duration",
    "customer_ring_duration", "recording_filename",
    "ended_at_ist", "captured_at_ist", "source_event",
]

app = Flask(__name__)
_lock = threading.Lock()
_store = {"ws": None, "index": {}}     # index: client_ref_id -> row number

# reject counters, per-day, in-memory only (reset on respawn -- that is fine,
# the on-disk log is the record; this only governs how much we write)
_reject_lock = threading.Lock()
_reject_count = {"day": "", "n": 0}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def log(*a):
    print("[call_hook_capture]", *a, flush=True)


def mask_key(raw_key):
    """Opaque, stable, non-reversible label. Never the key itself.

    Deliberately identical to callhook_watchdog.mask_key so a label seen here
    and a label seen there mean the same thing. NOTE: the watchdog reads the
    access log, where the key is percent-encoded on the wire ('@' -> '%40');
    Flask has already decoded it by the time we see it here. The two therefore
    label the SAME key differently. Compare like with like.
    """
    if raw_key is None:
        return "key_none"
    digest = hashlib.md5(raw_key.encode("utf-8", "replace")).hexdigest()
    return "key_" + digest[:6]


def _secret_looks_corrupt(value):
    """Return a reason string if this secret looks like a mangled .env line."""
    if not value:
        return ""
    if len(value) > SECRET_SANE_MAX_LEN:
        return "length %d exceeds %d -- looks like a run-on .env line" % (
            len(value), SECRET_SANE_MAX_LEN)
    if any(c.isspace() for c in value):
        return "contains whitespace"
    if "=" in value:
        return "contains '=' -- a second VAR=value may have been welded on"
    return ""


def key_matches(given):
    """Constant-time check against both accepted secrets.

    Returns: "current", "previous", or "" (no match).
    Order matters: the current key is checked first so the common path is
    reported as current even in the degenerate case where PREV == SECRET.
    """
    if not given:
        return ""
    g = given.encode("utf-8", "replace")
    if SECRET and hmac.compare_digest(g, SECRET.encode("utf-8", "replace")):
        return "current"
    if SECRET_PREV and hmac.compare_digest(g, SECRET_PREV.encode("utf-8", "replace")):
        return "previous"
    return ""


def _reject_should_write():
    """Throttle. Full detail for the first N of the day, then 1 in 100."""
    day = datetime.datetime.now(IST).strftime("%Y-%m-%d")
    with _reject_lock:
        if _reject_count["day"] != day:
            _reject_count["day"] = day
            _reject_count["n"] = 0
        _reject_count["n"] += 1
        n = _reject_count["n"]
    if n <= REJECT_LOG_FULL_UPTO:
        return True, n
    return (n % REJECT_LOG_THEN_EVERY == 0), n


def reject_log(given_key, reason):
    """Write down a refusal BEFORE refusing it. Metadata only. Never raises.

    No body. No key. Just enough to answer, months later, the question that
    could not be answered in July 2026: 'was anything arriving at all, and
    what key was it carrying?'
    """
    try:
        write, n = _reject_should_write()
        if not write:
            return
        os.makedirs(REJECT_DIR, exist_ok=True)
        try:
            os.chmod(REJECT_DIR, 0o700)
        except OSError:
            pass
        day = datetime.datetime.now(IST).strftime("%Y-%m-%d")
        line = json.dumps({
            "at": datetime.datetime.now(IST).isoformat(),
            "reason": reason,
            "key_label": mask_key(given_key) if given_key else "key_absent",
            "key_len": len(given_key or ""),
            "remote_addr": request.headers.get("X-Forwarded-For", "")
                           or (request.remote_addr or ""),
            "method": request.method,
            "path": request.path,
            "n_today": n,
        }, ensure_ascii=False)
        fp = os.path.join(REJECT_DIR, day + ".jsonl")
        with open(fp, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        try:
            os.chmod(fp, 0o600)
        except OSError:
            pass
    except Exception as e:              # noqa: BLE001
        log("reject_log failed:", e)


def raw_log(payload, event_type=""):
    """Append the raw push to call_hook_logs/YYYY-MM-DD.jsonl (owner-only)."""
    try:
        os.makedirs(RAW_DIR, exist_ok=True)
        try:
            os.chmod(RAW_DIR, 0o700)
        except OSError:
            pass
        day = datetime.datetime.now(IST).strftime("%Y-%m-%d")
        line = json.dumps(
            {"at": datetime.datetime.now(IST).isoformat(),
             "event_type": event_type, "body": payload},
            ensure_ascii=False)
        fp = os.path.join(RAW_DIR, day + ".jsonl")
        with open(fp, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        try:
            os.chmod(fp, 0o600)
        except OSError:
            pass
    except Exception as e:              # noqa: BLE001
        log("raw_log failed:", e)


def to_ist_iso(ts):
    """Turn an ISO-8601 UTC string (possibly with 'Z' + nanoseconds) into an
    unambiguous IST string the dashboard can parse. Blank -> ''. """
    s = str(ts or "").strip()
    if not s:
        return ""
    try:
        t = s.replace("Z", "+00:00")
        m = re.match(r"^(.*?)(\.\d+)?([+-]\d{2}:?\d{2})?$", t)
        if m:
            base = m.group(1)
            frac = (m.group(2) or "")[:7]      # dot + up to 6 digits (Py3.9)
            off = m.group(3) or ""
            t = base + frac + off
        d = datetime.datetime.fromisoformat(t)
        if d.tzinfo is None:
            d = d.replace(tzinfo=datetime.timezone.utc)
        return d.astimezone(IST).strftime("%Y-%m-%dT%H:%M:%S") + "+05:30"
    except ValueError:
        return s


def _find_sa_key():
    """Resolve the service-account json: explicit env first, else the single
    service_account *.json found under a few likely folders."""
    if SA_KEY and os.path.exists(SA_KEY):
        return SA_KEY
    for d in ("/root/wa", "/root/wa/keys", _HERE, "/root"):
        try:
            for path in glob.glob(os.path.join(d, "*.json")):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        obj = json.load(f)
                    if obj.get("type") == "service_account" and obj.get("client_email"):
                        return path
                except Exception:      # noqa: BLE001
                    continue
        except Exception:              # noqa: BLE001
            continue
    return ""


# --------------------------------------------------------------------------
# pure extraction (no network -> easy to unit-test)
# --------------------------------------------------------------------------
def extract_record(body, source_event=""):
    """Map a raw webhook body to a Call_Durations record, or None if this is
    not one of our outbound OBD calls (then it is raw-logged only)."""
    if not isinstance(body, dict):
        return None
    p = body.get("payload") if isinstance(body.get("payload"), dict) else body

    category = str(p.get("category", "")).lower()
    client_ref_id = str(p.get("client_ref_id", "") or "").strip()
    # Only our own outbound OBD calls carry a client_ref_id we can join on.
    if category != "obd" or not client_ref_id:
        return None

    # customer leg = the patient side; prefer the one with the most talk time.
    legs = p.get("legs") if isinstance(p.get("legs"), list) else []
    cust = [l for l in legs if isinstance(l, dict)
            and str(l.get("type", "")).lower() == "customer"]
    cust.sort(key=lambda l: (l.get("talk_duration") or 0), reverse=True)
    leg = cust[0] if cust else {}

    def _num(v):
        return "" if v is None else v

    return {
        "client_ref_id": client_ref_id,
        "ref_id": str(p.get("ref_id", "") or ""),
        "session_id": str(p.get("id", "") or body.get("session_id", "") or ""),
        "category": category,
        "status": str(p.get("status", "") or ""),
        "total_duration": _num(p.get("duration", "")),
        "customer_result": str(leg.get("result", "") or ""),
        "customer_talk_duration": _num(leg.get("talk_duration", "")),
        "customer_ring_duration": _num(leg.get("ring_duration", "")),
        "recording_filename": str(p.get("recording_filename", "") or ""),
        "ended_at_ist": to_ist_iso(p.get("ended_at", "")),
        "captured_at_ist": datetime.datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S") + "+05:30",
        "source_event": source_event or str(body.get("event_type", "") or ""),
    }


def record_to_row(rec):
    return [rec.get(h, "") for h in HEADER]


# --------------------------------------------------------------------------
# Google Sheet store (best-effort, degrade-safe)
# --------------------------------------------------------------------------
def _connect_store():
    if not _GSPREAD_OK:
        raise RuntimeError("gspread not installed")
    key = _find_sa_key()
    if not key:
        raise RuntimeError("no service-account key found")
    gc = gspread.service_account(filename=key)
    sh = gc.open_by_key(SHEET_ID)
    try:
        ws = sh.worksheet(TAB)
    except WorksheetNotFound:
        ws = sh.add_worksheet(title=TAB, rows=2000, cols=len(HEADER))
        ws.batch_update([{"range": "A1", "values": [HEADER]}], value_input_option="RAW")
        log("created tab '%s' with header" % TAB)
    header = ws.row_values(1)
    if [h.strip().lower() for h in header] != [h.lower() for h in HEADER]:
        # write/repair header if the first row isn't ours (empty or partial)
        if not header:
            ws.batch_update([{"range": "A1", "values": [HEADER]}], value_input_option="RAW")
    # build the client_ref_id -> row-number index (col A, skip header)
    index = {}
    try:
        col = ws.col_values(1)[1:]
        for i, v in enumerate(col, start=2):
            if v:
                index[v] = i
    except Exception as e:              # noqa: BLE001
        log("index preload failed:", e)
    _store.update({"ws": ws, "index": index})
    log("connected to '%s' (key=%s) - %d rows known" % (TAB, os.path.basename(key), len(index)))
    return ws


def store_handle():
    if _store["ws"] is None:
        _connect_store()
    return _store["ws"]


def upsert(rec):
    """Insert or update one Call_Durations row keyed on client_ref_id."""
    key = rec["client_ref_id"]
    row = record_to_row(rec)
    ws = store_handle()
    r = _store["index"].get(key)
    if r:
        ws.batch_update([{"range": "A%d" % r, "values": [row]}], value_input_option="RAW")
        return "updated", r
    ws.append_row(row, value_input_option="RAW")
    r = len(_store["index"]) + 2        # header + existing + this
    _store["index"][key] = r
    return "inserted", r


# --------------------------------------------------------------------------
# routes
# --------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return "call_hook_capture alive", 200


@app.route("/mo-callhook", methods=["GET", "POST"])
@app.route("/call-hook", methods=["GET", "POST"])   # local-test alias; harmless
def call_hook():
    # ---- secret gate: accept CURRENT or PREVIOUS; write down every refusal ----
    if SECRET or SECRET_PREV:
        given = request.args.get("key", "") or request.headers.get("X-Webhook-Key", "")
        which = key_matches(given)
        if not which:
            reject_log(given, "secret_mismatch" if given else "no_key_supplied")
            return jsonify(ok=False, error="forbidden"), 403
        if which == "previous":
            log("WARN: request accepted on the PREVIOUS key (%s). "
                "One side of the rotation is unfinished: update the MyOperator "
                "panel to the current key, then clear CALLHOOK_SECRET_PREV."
                % mask_key(given))

    if request.method == "GET":
        ch = request.args.get("challenge") or request.args.get("hub.challenge")
        return (ch, 200) if ch else ("ok", 200)

    payload = request.get_json(silent=True)
    if payload is None:
        try:
            payload = json.loads(request.get_data(as_text=True) or "{}")
        except ValueError:
            payload = {"_unparsed": request.get_data(as_text=True)}

    event_type = ""
    if isinstance(payload, dict):
        event_type = str(payload.get("event_type") or payload.get("event")
                         or (payload.get("payload", {}) or {}).get("event_type") or "")

    raw_log(payload, event_type)        # ALWAYS keep the raw copy first

    # best-effort PHI-clean upsert; never let a failure break the webhook
    try:
        rec = extract_record(payload, event_type)
        if not rec:
            return jsonify(ok=True, captured=True, event=event_type, sheet="skipped"), 200
        with _lock:
            try:
                action, r = upsert(rec)
            except Exception:           # one reconnect retry on token/network blips
                _store["ws"] = None
                action, r = upsert(rec)
        log("call %s -> row %d (%s, cust_talk=%s, status=%s)" % (
            action, r, event_type, rec.get("customer_talk_duration"), rec.get("status")))
        return jsonify(ok=True, captured=True, event=event_type, sheet=action, row=r), 200
    except Exception as e:              # noqa: BLE001
        log("sheet write failed (kept in raw log):", e)
        return jsonify(ok=True, captured=True, event=event_type, sheet="deferred"), 200


# --------------------------------------------------------------------------
# startup: connect to the sheet at IMPORT time (gunicorn does not run __main__),
# so a service restart itself verifies the write-path and creates the tab.
# Best-effort: never raises, so a missing key/network can't stop the service.
# --------------------------------------------------------------------------
def _startup_connect():
    log("Phase B receiver v2 (dual-key). raw logs: %s" % RAW_DIR)
    log("reject logs: %s" % REJECT_DIR)

    if SECRET and SECRET_PREV:
        if SECRET == SECRET_PREV:
            log("secret gate: ON  current=%s  previous=SAME AS CURRENT "
                "(rotation not started; harmless)" % mask_key(SECRET))
        else:
            log("secret gate: ON  current=%s  previous=%s  "
                "-> ROTATION IN PROGRESS. Clear CALLHOOK_SECRET_PREV when the "
                "panel is updated and the WARN lines stop."
                % (mask_key(SECRET), mask_key(SECRET_PREV)))
    elif SECRET:
        log("secret gate: ON  current=%s  previous=(unset)  "
            "-> single-key. A panel/.env mismatch will refuse every delivery. "
            "Set CALLHOOK_SECRET_PREV before rotating." % mask_key(SECRET))
    elif SECRET_PREV:
        log("secret gate: ON  current=(unset!)  previous=%s  "
            "-> CALLHOOK_SECRET is empty. Only the previous key is accepted. "
            "This is almost certainly a mistake." % mask_key(SECRET_PREV))
    else:
        log("secret gate: OFF (set CALLHOOK_SECRET to enable)")

    for name, value in (("CALLHOOK_SECRET", SECRET), ("CALLHOOK_SECRET_PREV", SECRET_PREV)):
        why = _secret_looks_corrupt(value)
        if why:
            log("WARNING: %s looks corrupt: %s. Check the .env line. Fix it with "
                "`awk`+ENVIRON or `printf`, never `sed -i '<N>s|...'`." % (name, why))

    if not _GSPREAD_OK:
        log("WARNING: gspread not importable -> sheet writes disabled (raw log still on)")
        return
    try:
        _connect_store()
    except Exception as e:              # noqa: BLE001
        log("startup sheet connect deferred (will retry on first event):", e)


# --------------------------------------------------------------------------
# selftest -- offline. Exercises the gate and nothing else.
# --------------------------------------------------------------------------
def _selftest():
    global SECRET, SECRET_PREV
    passed = failed = 0

    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
            print("  FAIL: %s" % name)

    # -- key_matches ---------------------------------------------------------
    SECRET, SECRET_PREV = "NewKey@12345", "OldKey@12345"
    check("current key accepted", key_matches("NewKey@12345") == "current")
    check("previous key accepted", key_matches("OldKey@12345") == "previous")
    check("wrong key refused", key_matches("Nonsense") == "")
    check("empty key refused", key_matches("") == "")
    check("none key refused", key_matches(None) == "")
    check("no partial match", key_matches("NewKey@1234") == "")
    check("trailing space refused", key_matches("NewKey@12345 ") == "")

    SECRET, SECRET_PREV = "OnlyKey@1234", ""
    check("single-key still works", key_matches("OnlyKey@1234") == "current")
    check("single-key refuses other", key_matches("OldKey@12345") == "")

    SECRET, SECRET_PREV = "Same@123", "Same@123"
    check("prev==current reports current", key_matches("Same@123") == "current")

    SECRET, SECRET_PREV = "", ""
    check("no secrets -> no match", key_matches("anything") == "")

    # -- masking -------------------------------------------------------------
    check("mask stable", mask_key("abc") == mask_key("abc"))
    check("mask distinguishes", mask_key("abc") != mask_key("abd"))
    check("mask hides", "abc" not in mask_key("abc"))
    check("mask len", len(mask_key("abc")) == 10)
    check("mask none", mask_key(None) == "key_none")
    # the encoding trap, recorded so nobody rediscovers it at 2am
    check("wire form labels differently", mask_key("a@b") != mask_key("a%40b"))

    # -- corruption sniffer --------------------------------------------------
    check("clean key is sane", _secret_looks_corrupt("NewKey@12345") == "")
    check("long key flagged", "length" in _secret_looks_corrupt("x" * 61))
    check("whitespace flagged", "whitespace" in _secret_looks_corrupt("abc def"))
    check("welded var flagged", "'='" in _secret_looks_corrupt("abcCALLHOOK_SECRET_PREV=x"))
    check("empty not flagged", _secret_looks_corrupt("") == "")

    # -- throttle ------------------------------------------------------------
    _reject_count["day"], _reject_count["n"] = "", 0
    writes = sum(1 for _ in range(1000) if _reject_should_write()[0])
    check("throttle writes first 500", writes == REJECT_LOG_FULL_UPTO + 5)
    check("counter kept counting", _reject_count["n"] == 1000)

    # -- the gate, end to end, through Flask ---------------------------------
    # reset the throttle: the test above left the counter at 1000, which would
    # push the refusals below into the 1-in-100 band and silently drop them.
    _reject_count["day"], _reject_count["n"] = "", 0
    SECRET, SECRET_PREV = "NewKey@12345", "OldKey@12345"
    prev_dir = globals()["REJECT_DIR"]
    import tempfile
    globals()["REJECT_DIR"] = tempfile.mkdtemp(prefix="rejtest_")
    c = app.test_client()

    r = c.get("/mo-callhook?key=NewKey@12345")
    check("GET current -> 200", r.status_code == 200)
    r = c.get("/mo-callhook?key=OldKey@12345")
    check("GET previous -> 200", r.status_code == 200)
    r = c.get("/mo-callhook?key=WrongKey")
    check("GET wrong -> 403", r.status_code == 403)
    r = c.get("/mo-callhook")
    check("GET no key -> 403", r.status_code == 403)
    r = c.get("/mo-callhook?key=NewKey%4012345")
    check("wire-encoded key decoded by flask -> 200", r.status_code == 200)
    r = c.get("/mo-callhook", headers={"X-Webhook-Key": "NewKey@12345"})
    check("header key -> 200", r.status_code == 200)
    r = c.get("/mo-callhook?key=NewKey@12345&challenge=abc123")
    check("challenge echoed", r.data == b"abc123")

    # the refusals must have been written down -- the whole point
    day = datetime.datetime.now(IST).strftime("%Y-%m-%d")
    fp = os.path.join(globals()["REJECT_DIR"], day + ".jsonl")
    check("reject log exists", os.path.exists(fp))
    if os.path.exists(fp):
        rows = [json.loads(l) for l in open(fp, encoding="utf-8")]
        check("two refusals written", len(rows) == 2)
        check("mismatch reason", rows[0]["reason"] == "secret_mismatch")
        check("absent-key reason", rows[1]["reason"] == "no_key_supplied")
        check("reject log never holds the key",
              all("WrongKey" not in json.dumps(r_) for r_ in rows))
        check("reject log holds a label", rows[0]["key_label"].startswith("key_"))
        check("absent key labelled", rows[1]["key_label"] == "key_absent")
        check("reject log has no body", all("body" not in r_ for r_ in rows))
    globals()["REJECT_DIR"] = prev_dir

    # -- untouched behaviour: extraction is byte-for-byte the old logic -------
    body = {"payload": {"category": "obd", "client_ref_id": "R1", "status": "answered",
                        "duration": 42, "legs": [{"type": "customer", "talk_duration": 30,
                                                  "ring_duration": 5, "result": "answered"}]}}
    rec = extract_record(body, "call.end")
    check("extract still works", rec["client_ref_id"] == "R1" and rec["customer_talk_duration"] == 30)
    check("non-obd still skipped", extract_record({"payload": {"category": "inbound"}}) is None)
    check("no client_ref_id skipped", extract_record({"payload": {"category": "obd"}}) is None)
    check("row order preserved", record_to_row(rec)[0] == "R1" and len(record_to_row(rec)) == 13)

    print("selftest: %d/%d passed" % (passed, passed + failed))
    return 0 if failed == 0 else 1



if __name__ == "__main__" and "--selftest" in sys.argv:
    sys.exit(_selftest())

_startup_connect()

if __name__ == "__main__":
    log("listening on http://%s:%d  (POST /mo-callhook)" % (HOST, PORT))
    app.run(host=HOST, port=PORT)
