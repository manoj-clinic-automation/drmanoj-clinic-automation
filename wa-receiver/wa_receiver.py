#!/usr/bin/env python3
"""
wa_receiver.py - inbound WhatsApp webhook receiver for Dr. Manoj Agarwal Clinic.

WHAT IT DOES
  A tiny always-on web service. MyOperator PUSHES each inbound WhatsApp message
  to it (Webhooks v2 -> "message received"). For every inbound message it:
    1. Writes the raw push to a daily log file (the safety net + a way to confirm
       the exact field names on the first real message).
    2. Pulls out the useful fields (who, what, when, ids).
    3. Appends one row to the "WA_Inbox" tab of the Clinic Callback Tracker sheet,
       in that tab's existing column order.
  The live dashboard already READS that tab, so the WhatsApp panels fill in by
  themselves once messages start landing.

WHY A RECEIVER AT ALL
  MyOperator's WhatsApp API has no "fetch past messages" call. Inbound messages
  only arrive by push. This service is the thing that catches the push.

SAFETY / PRIVACY
  - Google auth = the SAME patient-mirror service-account key, reused (it already
    has write access to the sheet). Path comes from the environment; the file
    itself stays only on the VPS.
  - An optional shared secret (WA_WEBHOOK_SECRET) blocks strangers from posting.
  - Raw log files contain patient numbers + message text -> keep them local and
    access-controlled (the script restricts the folder to the owner).
  - De-dupe on the message id, so a re-delivered push never doubles a row.

CONFIG  (set as environment variables, or in a .env file next to this script)
  WA_SHEET_ID         (required) the Clinic Callback Tracker spreadsheet id
  WA_SA_KEY           (required) full path to the service-account JSON key on the VPS
  WA_TAB              (optional) sheet tab name           [default: WA_Inbox]
  WA_WEBHOOK_SECRET   (optional) shared secret; if set, the webhook URL must carry
                                 ?key=<secret>  (or header X-Webhook-Key)
  WA_PORT             (optional) port to listen on        [default: 8095]
  WA_HOST             (optional) bind address             [default: 127.0.0.1]
  WA_RAW_LOG_DIR      (optional) raw-log folder           [default: ./wa_logs]

RUN
  Quick test:   python wa_receiver.py          (Flask's built-in server)
  Production :  gunicorn -w 2 -b 127.0.0.1:8095 wa_receiver:app   (see deploy guide)

DEPENDENCIES
  pip install Flask gspread google-auth
"""

import os
import re
import json
import threading
import datetime
from flask import Flask, request, jsonify

import gspread
from google.oauth2.service_account import Credentials

# --------------------------------------------------------------------------
# tiny .env loader (no extra dependency) - reads KEY=VALUE lines if a .env
# file sits next to this script and the var isn't already in the environment.
# --------------------------------------------------------------------------
def _load_env():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, ".env")
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip(); v = v.strip().strip('"').strip("'")
                os.environ.setdefault(k, v)
    except OSError:
        pass

_load_env()

SHEET_ID   = os.environ.get("WA_SHEET_ID", "").strip()
SA_KEY     = os.environ.get("WA_SA_KEY", "").strip()
TAB        = os.environ.get("WA_TAB", "WA_Inbox").strip() or "WA_Inbox"
SECRET     = os.environ.get("WA_WEBHOOK_SECRET", "").strip()
PORT       = int(os.environ.get("WA_PORT", "8095"))
HOST       = os.environ.get("WA_HOST", "127.0.0.1").strip() or "127.0.0.1"
RAW_DIR    = os.environ.get("WA_RAW_LOG_DIR", "wa_logs").strip() or "wa_logs"
SCOPES     = ["https://www.googleapis.com/auth/spreadsheets"]
IST        = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

app = Flask(__name__)
_lock = threading.Lock()
_state = {"ws": None, "header": [], "id_col": -1, "seen": set()}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def log(*a):
    print("[wa_receiver]", *a, flush=True)


def dig(d, *paths, default=""):
    """Return the first non-empty value found at any of the dotted paths."""
    for path in paths:
        cur = d
        ok = True
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur not in (None, "", [], {}):
            return cur
    return default


def to_ist_iso(ts):
    """Make an unambiguous IST timestamp string the dashboard can parse."""
    try:
        s = str(ts).strip()
        if s.isdigit():
            v = int(s)
            if v > 10 ** 12:      # milliseconds -> seconds
                v //= 1000
            d = datetime.datetime.fromtimestamp(v, IST)
            return d.strftime("%Y-%m-%dT%H:%M:%S") + "+05:30"
        if s:
            try:
                # Normalise: 'Z' -> '+00:00', and trim fractional seconds to at
                # most 6 digits (Python 3.9's fromisoformat rejects 7-9 digit
                # nanoseconds, e.g. MyOperator's '...56.956814767Z').
                t = s.replace("Z", "+00:00")
                m = re.match(r"^(.*?)(\.\d+)?([+-]\d{2}:?\d{2})?$", t)
                if m:
                    base = m.group(1)
                    frac = m.group(2) or ""
                    off = m.group(3) or ""
                    if frac:
                        frac = frac[:7]          # dot + up to 6 digits
                    t = base + frac + off
                d = datetime.datetime.fromisoformat(t)
                if d.tzinfo is None:
                    d = d.replace(tzinfo=datetime.timezone.utc)
                return d.astimezone(IST).strftime("%Y-%m-%dT%H:%M:%S") + "+05:30"
            except ValueError:
                return s
    except Exception:             # noqa: BLE001
        pass
    return datetime.datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S") + "+05:30"


def raw_log(payload):
    """Append the raw push to wa_logs/YYYY-MM-DD.jsonl (the recovery safety net)."""
    try:
        os.makedirs(RAW_DIR, exist_ok=True)
        try:
            os.chmod(RAW_DIR, 0o700)
        except OSError:
            pass
        day = datetime.datetime.now(IST).strftime("%Y-%m-%d")
        line = json.dumps({"at": datetime.datetime.now(IST).isoformat(), "body": payload},
                          ensure_ascii=False)
        fp = os.path.join(RAW_DIR, day + ".jsonl")
        with open(fp, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        try:
            os.chmod(fp, 0o600)
        except OSError:
            pass
    except Exception as e:        # noqa: BLE001
        log("raw_log failed:", e)


def _connect():
    """Open the worksheet, read its header, and load existing message ids (de-dupe)."""
    creds = Credentials.from_service_account_file(SA_KEY, scopes=SCOPES)
    gc = gspread.authorize(creds)
    ws = gc.open_by_key(SHEET_ID).worksheet(TAB)
    header = ws.row_values(1)
    norm = [h.strip().lower() for h in header]
    id_col = norm.index("message id") if "message id" in norm else -1
    seen = set()
    if id_col >= 0:
        try:
            col = ws.col_values(id_col + 1)[1:]   # skip header
            seen = set(x for x in col if x)
        except Exception as e:    # noqa: BLE001
            log("could not preload ids:", e)
    _state.update({"ws": ws, "header": header, "id_col": id_col, "seen": seen})
    log("connected to '%s' - %d columns, %d ids known" % (TAB, len(header), len(seen)))
    return ws


def ws_handle():
    if _state["ws"] is None:
        _connect()
    return _state["ws"]


def is_inbound_message(et, direction, mtype, message):
    """Accept only inbound patient messages; skip delivered/read/sent status pings."""
    et = str(et).lower()
    direction = str(direction).lower()
    mtype = str(mtype).lower()
    status_only = ("received" not in et) and any(
        k in et for k in ("delivered", "read", "sent", "status", "failed"))
    if status_only:
        return False
    inbound = "out" not in direction          # 'incoming' or unspecified
    looks_message = ("received" in et) or bool(message) or (mtype and mtype != "status")
    return inbound and looks_message


def build_row(payload):
    """Map a push payload to a row in the WA_Inbox column order. Returns (row, msg_id) or None."""
    ts        = dig(payload, "timestamp", "payload.timestamp", "data.timestamp",
                    "payload.data.timestamp")
    phone     = dig(payload, "customer_identifier", "payload.customer_identifier",
                    "data.customer_identifier", "customer_number", "payload.customer_number",
                    "payload.data.context.from", "contact.wa_id")
    direction = dig(payload, "direction", "payload.direction", "data.direction",
                    default="incoming")
    mtype     = dig(payload, "payload.data.type", "data.type", "payload.type", "type",
                    default="text")
    message   = dig(payload, "payload.data.context.body", "data.context.body",
                    "payload.data.body", "data.body", "message", "text", default="")
    msg_id    = dig(payload, "payload.id", "payload.message_id", "data.id", "id", "message_id")
    conv_id   = dig(payload, "session_id", "payload.session_id", "data.session_id",
                    "conversation_id", "conversaton_id", "payload.conversation_id")
    status    = dig(payload, "payload.status", "data.status", "status", default="received")
    event     = dig(payload, "event_type", "event", "payload.event_type", default="")

    if not is_inbound_message(event, direction, mtype, message):
        return None

    fields = {
        "timestamp":       to_ist_iso(ts),
        "phone":           "".join(ch for ch in str(phone) if ch.isdigit()),
        "direction":       str(direction or "incoming"),
        "type":            str(mtype or "text"),
        "message":         str(message or ""),
        "message id":      str(msg_id or ""),
        "conversation id": str(conv_id or ""),
        "status":          str(status or "received"),
    }
    if not _state["header"]:
        ws_handle()                        # ensure we're connected + header is loaded
    row = [fields.get(h.strip().lower(), "") for h in _state["header"]]
    return row, str(msg_id or "")


# --------------------------------------------------------------------------
# routes
# --------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return "wa_receiver alive", 200


@app.route("/wa-webhook", methods=["GET", "POST"])
def webhook():
    # secret gate (optional but recommended)
    if SECRET:
        given = request.args.get("key", "") or request.headers.get("X-Webhook-Key", "")
        if given != SECRET:
            return jsonify(ok=False, error="forbidden"), 403

    # some platforms verify a webhook with a GET challenge
    if request.method == "GET":
        ch = request.args.get("challenge") or request.args.get("hub.challenge")
        return (ch, 200) if ch else ("ok", 200)

    payload = request.get_json(silent=True)
    if payload is None:
        try:
            payload = json.loads(request.get_data(as_text=True) or "{}")
        except ValueError:
            payload = {"_unparsed": request.get_data(as_text=True)}

    raw_log(payload)                       # ALWAYS keep the raw copy first

    try:
        built = build_row(payload)
        if not built:
            return jsonify(ok=True, skipped="not an inbound message"), 200
        row, msg_id = built

        with _lock:
            ws = ws_handle()
            if msg_id and msg_id in _state["seen"]:
                return jsonify(ok=True, skipped="duplicate"), 200
            try:
                ws.append_row(row, value_input_option="RAW")
            except Exception:          # one reconnect retry (token/network blips)
                _state["ws"] = None
                ws = ws_handle()
                ws.append_row(row, value_input_option="RAW")
            if msg_id:
                _state["seen"].add(msg_id)
        log("appended message %s" % (msg_id[-8:] if msg_id else "(no id)"))
        return jsonify(ok=True, written=True), 200
    except Exception as e:             # noqa: BLE001
        # never retry-storm: the raw log already has it for recovery
        log("write failed (kept in raw log):", e)
        return jsonify(ok=True, written=False, note="kept in raw log"), 200


if __name__ == "__main__":
    miss = [k for k, v in {"WA_SHEET_ID": SHEET_ID, "WA_SA_KEY": SA_KEY}.items() if not v]
    if miss:
        log("MISSING required config: " + ", ".join(miss) + " (set env or .env)")
    else:
        try:
            _connect()
        except Exception as e:         # noqa: BLE001
            log("startup connect failed (will retry on first message):", e)
    log("listening on http://%s:%d  (POST /wa-webhook)" % (HOST, PORT))
    app.run(host=HOST, port=PORT)
