#!/usr/bin/env python3
"""
attlistener_v2.py — STANDALONE attendance capture + local ack (no upstream).
S535 (12-Oct-2026): + THE SOURCE WATCH (records who sends each punch; changes nothing the device sees).

    Secureye device  ->  THIS listener (your VPS)  ->  HTTP 200 + response_code header
                                 |
                                 +-> appends every NEW punch to punches.csv (de-duplicated)

STANDALONE MODE (28 Jun 2026):
- This listener answers the device itself. It does NOT call the ONtime cloud.
  The device only needs ONE response header to mark a record "delivered":
      * a real punch (body has user_id + io_time)  -> response_code: OK
      * anything else (heartbeat / command poll)   -> response_code: ERROR_NO_CMD
  These are exactly the two acknowledgements Secureye used to return
  (reverse-engineered 21 Jun 2026). The device reads nothing else from the reply.

- DE-DUPLICATION: punches are keyed on (user_id, datetime) — the SAME key
  att_core.py uses on the read side — so a device re-send can never create a
  duplicate row. The file is APPEND-ONLY; existing rows are never edited.

- Quiet by default. Set DEBUG = True to trace every request.

EMERGENCY REVERT (no code change needed): on the DEVICE, set Server IP back to
054.186.015.016 — it then talks to Secureye/ONtime directly, exactly as before.

Deploy: scp this one file to /root/ then `systemctl restart attlistener`.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime
import json, os, threading

# --- settings -------------------------------------------------------------
# The env overrides exist ONLY so the file can be tested off-box. On the VPS
# none of these env vars are set, so the production defaults below are used.
PORT      = int(os.environ.get("ATT_LISTENER_PORT", "8041"))
PUNCH_CSV = os.environ.get("ATT_PUNCH_CSV", "/root/punches.csv")
LOG_FILE  = os.environ.get("ATT_LISTENER_LOG", "/root/attlistener.log")
DEBUG     = False
SOURCE_LOG = os.environ.get("ATT_SOURCE_LOG", "/root/attlistener_sources.jsonl")   # S535

CSV_HEADER = "user_id,datetime,io_mode,verify_mode,received_at\n"

# Shared state (the capture server is multi-threaded).
_lock = threading.Lock()
_seen = set()                  # {(user_id, datetime)} already present in punches.csv
_ack_map_logged = set()        # one-time "request_code -> response_code" log lines


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(text):
    line = f"[{now_str()}] {text}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def extract_json(raw):
    """The device frames the body as [4-byte LE length][JSON][null]; grab the JSON."""
    s = raw.find(b"{")
    e = raw.rfind(b"}")
    return raw[s:e + 1] if (s >= 0 and e > s) else None


def parse_io_time(s):
    try:
        return datetime.strptime(s, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return s


def load_seen():
    """Populate the de-dup set from the existing CSV once, at startup."""
    _seen.clear()
    if not os.path.exists(PUNCH_CSV):
        return
    try:
        with open(PUNCH_CSV, "r", encoding="utf-8") as f:
            next(f, None)  # skip header row
            for line in f:
                parts = line.rstrip("\n").split(",")
                if len(parts) >= 2 and parts[0] != "user_id":
                    _seen.add((parts[0], parts[1]))
    except Exception as e:
        log(f"WARN  could not preload punches.csv for de-dup: {e}")


def save_punch(uid, when, iom, vm):
    """Append one punch iff (uid, when) is new. Return True if written, False if duplicate."""
    key = (str(uid), when)
    with _lock:
        if key in _seen:
            return False
        fresh = not os.path.exists(PUNCH_CSV)
        with open(PUNCH_CSV, "a", encoding="utf-8") as f:
            if fresh:
                f.write(CSV_HEADER)
            f.write(f"{uid},{when},{iom},{vm},{now_str()}\n")
        _seen.add(key)
        return True


# --- S535 (session 305, 12-Oct-2026): THE SOURCE WATCH -- step 1 of 2, it only RECORDS -------------------------
# The owner, 12-Oct 05:33 IST: "close it only if it is safe and keeps attendance running glitch free" (D713; his
# word is the waiver of the attendance freeze D247 for this change only).
# Step 1 changes NOTHING the device sees and nothing in punches.csv. For every punch -- and for the first
# SRC_OTHER_PER_DAY other requests from each sender each day -- it appends one line to SOURCE_LOG: who sent it
# (the address), the device's own headers (a header named like a password or key is masked), and the punch's
# user and time. A week of these lines shows which mark is on every genuine punch; step 2 (refuse a stranger,
# keep it aside, never lose a genuine punch) is built only on that evidence. Every failure here is swallowed:
# the ack never depends on it. /root/att_source_summary.py reads the file each night (01:25).
SRC_OTHER_PER_DAY = 30
_src_lock = threading.Lock()
_src_other = {}                # {(day, address): other requests recorded today}
_SRC_MASK = ("pass", "pwd", "key", "auth", "token", "secret", "cookie")


def record_source(handler, method, rc_hdr, ack, raw):
    try:
        ip = handler.client_address[0] if handler.client_address else ""
        day = datetime.now().strftime("%Y-%m-%d")
        punch = (ack == "OK")
        uid = when = None
        if punch:
            try:
                obj = json.loads(extract_json(raw).decode("utf-8", "replace"))
                uid = str(obj.get("user_id"))
                when = parse_io_time(obj.get("io_time", ""))
            except Exception:
                pass
        hdrs = {}
        for k, v in handler.headers.items():
            kl = k.lower()
            if kl == "content-length":
                continue
            v = str(v)
            if any(m in kl for m in _SRC_MASK):
                v = "<masked len=%d>" % len(v)
            hdrs[k] = v[:80]
        line = json.dumps({"t": now_str(), "ip": ip, "method": method, "path": (handler.path or "")[:120],
                           "request_code": rc_hdr, "ack": ack, "punch": punch, "user_id": uid, "datetime": when,
                           "headers": hdrs}, ensure_ascii=True, sort_keys=True)
        with _src_lock:
            if not punch:
                if len(_src_other) > 200:
                    for k in [k for k in _src_other if k[0] != day]:
                        del _src_other[k]
                n = _src_other.get((day, ip), 0)
                if n >= SRC_OTHER_PER_DAY:
                    return
                _src_other[(day, ip)] = n + 1
            with open(SOURCE_LOG, "a", encoding="utf-8") as f:
                f.write(line + "\n")
    except Exception:
        pass


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # silence the default stderr access log

    def _read_body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        return self.rfile.read(n) if n else b""

    def _classify_and_capture(self, raw):
        """Capture a real punch and return 'OK'; return 'ERROR_NO_CMD' for everything else."""
        payload = extract_json(raw)
        if payload:
            try:
                obj = json.loads(payload.decode("utf-8", "replace"))
            except Exception:
                obj = None
            if obj and "user_id" in obj and "io_time" in obj:
                uid = obj.get("user_id")
                when = parse_io_time(obj.get("io_time", ""))
                iom = str(obj.get("io_mode"))
                vm = obj.get("verify_mode")
                direction = {"0": "IN", "1": "OUT"}.get(iom, f"mode{iom}")
                wrote = save_punch(uid, when, iom, vm)
                if wrote:
                    log(f"PUNCH  user {uid}  {when}  {direction}  -> response_code OK")
                else:
                    log(f"DUP    user {uid}  {when}  {direction}  (re-send, not stored) -> response_code OK")
                return "OK"
        return "ERROR_NO_CMD"

    def _respond(self, method):
        raw = self._read_body()
        rc_hdr = self.headers.get("request_code", "")
        ack = self._classify_and_capture(raw)

        # One-time visibility: prove, in the log, what we reply to each request type.
        sig = (rc_hdr, ack)
        if sig not in _ack_map_logged:
            _ack_map_logged.add(sig)
            log(f"ACK MAP  request_code='{rc_hdr or '(none)'}'  ->  response_code: {ack}")

        # Anomaly cross-check (does not change behaviour; just flags surprises).
        if rc_hdr == "realtime_glog" and ack != "OK":
            log(f"WARN  request_code=realtime_glog but no punch parsed (replied {ack})")

        record_source(self, method, rc_hdr, ack, raw)   # S535: records only; never raises

        if DEBUG:
            log(f"{method} request_code='{rc_hdr}' -> 200 response_code={ack}")

        self.send_response(200)
        self.send_header("response_code", ack)   # the only header the device cares about
        self.send_header("Content-Length", "0")  # empty body, exactly like Secureye
        self.end_headers()

    def do_POST(self):
        self._respond("POST")

    def do_GET(self):
        self._respond("GET")


if __name__ == "__main__":
    load_seen()
    log(f"attlistener v2 STANDALONE (capture + local ack) on :{PORT}  "
        f"loaded {len(_seen)} existing punch keys  DEBUG={DEBUG}  — NO upstream call  SOURCE_WATCH=S535")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
