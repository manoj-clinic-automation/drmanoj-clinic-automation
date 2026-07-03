#!/usr/bin/env python3
"""
call_hook_capture.py - MyOperator call-webhook receiver for Dr. Manoj Agarwal Clinic.
PHASE B (the "duration gate", D77): passive capture PLUS a PHI-clean Call_Durations feed.

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
  - Optional shared secret (CALLHOOK_SECRET) blocks strangers from posting.

DEGRADE-SAFE
  - Google Sheets write is best-effort. If the key/tab/network isn't ready, the
    event is still raw-logged and we still return 200. We NEVER break the webhook
    and NEVER retry-storm. The raw log is always the recovery source.

CONFIG  (read from /root/wa/.env, a local .env, or the environment)
  CALLHOOK_SECRET     (optional) shared secret; if set, the webhook URL must
                                 carry ?key=<secret> (or header X-Webhook-Key)
  CALLHOOK_SHEET_ID   (optional) spreadsheet id   [default: the Clinic tracker id]
                                 (WA_SHEET_ID is also accepted)
  CALLHOOK_SA_KEY     (optional) full path to the service-account JSON key
                                 (WA_SA_KEY is also accepted; else auto-discovered
                                  as the single service_account *.json in /root/wa)
  CALLHOOK_TAB        (optional) sheet tab name          [default: Call_Durations]
  CALLHOOK_PORT       (optional) port to listen on       [default: 8098]
  CALLHOOK_HOST       (optional) bind address            [default: 127.0.0.1]
  CALLHOOK_RAW_LOG_DIR(optional) raw-log folder   [default: <script dir>/call_hook_logs]

RUN
  Quick test:  /root/wa/venv/bin/python3 call_hook_capture.py
  Production:  /root/wa/venv/bin/gunicorn -w 1 -b 127.0.0.1:8098 call_hook_capture:app
"""

import os
import re
import glob
import json
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

_HERE      = os.path.dirname(os.path.abspath(__file__))
SECRET     = os.environ.get("CALLHOOK_SECRET", "").strip()
PORT       = int(os.environ.get("CALLHOOK_PORT", "8098"))
HOST       = os.environ.get("CALLHOOK_HOST", "127.0.0.1").strip() or "127.0.0.1"
RAW_DIR    = os.environ.get("CALLHOOK_RAW_LOG_DIR", "").strip() \
    or os.path.join(_HERE, "call_hook_logs")
SHEET_ID   = os.environ.get("CALLHOOK_SHEET_ID", "").strip() \
    or os.environ.get("WA_SHEET_ID", "").strip() \
    or "1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0"
SA_KEY     = os.environ.get("CALLHOOK_SA_KEY", "").strip() \
    or os.environ.get("WA_SA_KEY", "").strip()
TAB        = os.environ.get("CALLHOOK_TAB", "Call_Durations").strip() or "Call_Durations"
SCOPES     = ["https://www.googleapis.com/auth/spreadsheets"]
IST        = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

HEADER = [
    "client_ref_id", "ref_id", "session_id", "category", "status",
    "total_duration", "customer_result", "customer_talk_duration",
    "customer_ring_duration", "recording_filename",
    "ended_at_ist", "captured_at_ist", "source_event",
]

app = Flask(__name__)
_lock = threading.Lock()
_store = {"ws": None, "index": {}}     # index: client_ref_id -> row number


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def log(*a):
    print("[call_hook_capture]", *a, flush=True)


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
    if SECRET:
        given = request.args.get("key", "") or request.headers.get("X-Webhook-Key", "")
        if given != SECRET:
            return jsonify(ok=False, error="forbidden"), 403

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
    log("Phase B receiver. raw logs: %s" % RAW_DIR)
    log("secret gate: %s" % ("ON" if SECRET else "OFF (set CALLHOOK_SECRET to enable)"))
    if not _GSPREAD_OK:
        log("WARNING: gspread not importable -> sheet writes disabled (raw log still on)")
        return
    try:
        _connect_store()
    except Exception as e:              # noqa: BLE001
        log("startup sheet connect deferred (will retry on first event):", e)


_startup_connect()


if __name__ == "__main__":
    log("listening on http://%s:%d  (POST /mo-callhook)" % (HOST, PORT))
    app.run(host=HOST, port=PORT)
