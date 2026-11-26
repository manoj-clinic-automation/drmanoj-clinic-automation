#!/usr/bin/env python3
"""
attlistener_v2.py — STANDALONE attendance capture + local ack (no upstream).
S535 (12-Oct-2026): + THE SOURCE WATCH (records who sends each punch; changes nothing the device sees).
S792 (11-Nov-2026): + THE MACHINE'S CLOCK. A punch's time is the machine's own clock, and on 11-Nov that clock ran
1 h 39 min to 2 h 57 min behind (power cuts stop it) -- the server received each punch at the true time. Now, when the
machine has been STEADILY online for the last five minutes (it checks in about every 12 seconds; no silence over a
minute) and a punch's machine time is more than five minutes off the server's, the SERVER's time is stored in
'datetime' and the machine's in the new last column 'machine_time'. Punches sent late in a burst after the machine was
offline keep the machine's time (it is right; the delivery was late). De-duplication is on the machine's time, as before.
The owner, 12:10 IST 11-Nov: "Ok and correct today's punches also" (his word waives the attendance freeze D247 for this).
S957 (26-Nov-2026, session S523; F-773, roadmap E0): + THE DOOR -- step 2 of the S535 source watch. Every punch the machine has
sent since 12-Oct carried the machine's own mark in one header, one value throughout (686 punches over 45 days; its internet address
changed 13 times, so the address is NOT the lock). A punch is now admitted only when it carries that mark. The header's name and its
value are NOT in this file: they are read from DOOR_CONF (/root/punch_door.json, 0600, written by the S957 installer from the
watch's own evidence). A punch without the mark is KEPT ASIDE in REFUSED_CSV -- never in punches.csv, never lost -- acknowledged
'OK' as before, counted in DOOR_STATE, and the console's health leg "punch door" turns red for a day. DOOR_CONF missing or
incomplete = the door open (as before S957); mode "watch" = every punch stored and the ones without the mark only counted.

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
from datetime import datetime, timedelta
import json, os, threading

# --- settings -------------------------------------------------------------
# The env overrides exist ONLY so the file can be tested off-box. On the VPS
# none of these env vars are set, so the production defaults below are used.
PORT      = int(os.environ.get("ATT_LISTENER_PORT", "8041"))
PUNCH_CSV = os.environ.get("ATT_PUNCH_CSV", "/root/punches.csv")
LOG_FILE  = os.environ.get("ATT_LISTENER_LOG", "/root/attlistener.log")
DEBUG     = False
SOURCE_LOG = os.environ.get("ATT_SOURCE_LOG", "/root/attlistener_sources.jsonl")   # S535

CSV_HEADER = "user_id,datetime,io_mode,verify_mode,received_at,machine_time\n"   # S792: + machine_time

# --- S792: the machine's clock ----------------------------------------------------------------------------------
CLOCK_FIX_MIN = float(os.environ.get("ATT_CLOCK_FIX_MIN", "5"))        # minutes off before the server's time is stored
ONLINE_WINDOW_S = float(os.environ.get("ATT_ONLINE_WINDOW_S", "300"))   # steadily online over the last five minutes ...
ONLINE_GAP_S = float(os.environ.get("ATT_ONLINE_GAP_S", "60"))          # ... with no silence longer than a minute
COUNT_LOOPBACK = os.environ.get("ATT_COUNT_LOOPBACK") == "1"            # tests only: count calls from this box as the machine's
_contacts = []                 # server times of the machine's recent requests, oldest first (S792)

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


def note_contact(handler, t):
    """S792: remember that the machine (anything but this box itself) called at server time t."""
    ip = handler.client_address[0] if handler.client_address else ""
    if ip in ("127.0.0.1", "::1", "::ffff:127.0.0.1") and not COUNT_LOOPBACK:
        return
    with _lock:
        _contacts.append(t)
        cut = t - timedelta(seconds=ONLINE_WINDOW_S + 120)
        while _contacts and _contacts[0] < cut:
            _contacts.pop(0)


def steadily_online(t):
    """S792: True when the machine's calls before t cover the last ONLINE_WINDOW_S seconds with no silence over ONLINE_GAP_S --
    then a punch arriving at t was sent the moment it was made, and t is its true time."""
    with _lock:
        c = [x for x in _contacts if t - timedelta(seconds=ONLINE_WINDOW_S) <= x <= t]
        older = any(x < t - timedelta(seconds=ONLINE_WINDOW_S - ONLINE_GAP_S) for x in _contacts if x <= t)
    if not c or not older:
        return False
    pts = c + [t]
    if (pts[0] - (t - timedelta(seconds=ONLINE_WINDOW_S))).total_seconds() > ONLINE_GAP_S:
        return False
    return all((b - a).total_seconds() <= ONLINE_GAP_S for a, b in zip(pts, pts[1:]))


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
                    if len(parts) >= 6 and parts[5]:       # S792: a corrected row -- its machine time is the key
                        _seen.add((parts[0], parts[5]))
    except Exception as e:
        log(f"WARN  could not preload punches.csv for de-dup: {e}")


def save_punch(uid, when, iom, vm, live=False):
    """Append one punch iff (uid, when) is new. Return True if written, False if duplicate. S792: 'when' is the machine's
    time; when the machine is steadily online (live) and its time is more than CLOCK_FIX_MIN off the server's, the
    server's time is stored and the machine's kept in the last column."""
    key = (str(uid), when)
    with _lock:
        if key in _seen:
            return False
        rec = now_str()
        stored = when
        try:
            off = (datetime.strptime(rec, "%Y-%m-%d %H:%M:%S") - datetime.strptime(when, "%Y-%m-%d %H:%M:%S")).total_seconds() / 60
        except Exception:
            off = None
        if live and (off is None or abs(off) > CLOCK_FIX_MIN):
            stored = rec
        fresh = not os.path.exists(PUNCH_CSV)
        with open(PUNCH_CSV, "a", encoding="utf-8") as f:
            if fresh:
                f.write(CSV_HEADER)
            f.write(f"{uid},{stored},{iom},{vm},{rec},{when}\n")
        _seen.add(key)
    if stored != when:
        log(f"CLOCK  user {uid}  machine {when}  server {rec}  ({'?' if off is None else round(off)} min) -- the server's time stored")
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
                           "headers": hdrs, "door": getattr(handler, "_door", None)}, ensure_ascii=True, sort_keys=True)
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


# --- S957 (session S523, 26-Nov-2026; F-773, roadmap E0): THE DOOR -- step 2 of the S535 source watch --------------------------
# The owner, 07-Oct (F-773): "the listener admits only the machine it knows, checked on every punch, and counts what it refuses
# where the health page can see it". The mark (a header name and its one value) is in DOOR_CONF, never in this file.
# Every failure here leaves the door as it was configured: a fault reading the state never stops a punch.
DOOR_CONF = os.environ.get("ATT_DOOR_CONF", "/root/punch_door.json")
DOOR_STATE = os.environ.get("ATT_DOOR_STATE", "/root/punch_door.state.json")
REFUSED_CSV = os.environ.get("ATT_REFUSED_CSV", "/root/punches_refused.csv")
DOOR_RED_H = float(os.environ.get("ATT_DOOR_RED_H", "24"))   # a refusal keeps the health leg red this long
REFUSED_HEADER = "user_id,datetime,io_mode,verify_mode,received_at,ip,reason\n"
_door_lock = threading.Lock()
_door_cache = {"mtime": None, "conf": None}


def door_conf():
    """{'mode': 'enforce' | 'watch' | 'open', 'header': ..., 'value': ...}; re-read when the file changes."""
    try:
        mt = os.stat(DOOR_CONF).st_mtime
    except OSError:
        return {"mode": "open", "header": "", "value": ""}
    if _door_cache["mtime"] == mt and _door_cache["conf"] is not None:
        return _door_cache["conf"]
    c = {"mode": "open", "header": "", "value": ""}
    try:
        with open(DOOR_CONF, encoding="utf-8") as f:
            d = json.load(f)
        h, v, m = str(d.get("header") or "").strip(), str(d.get("value") or "").strip(), str(d.get("mode") or "").strip()
        if h and v and m in ("enforce", "watch"):
            c = {"mode": m, "header": h, "value": v}
    except Exception:
        pass
    _door_cache.update(mtime=mt, conf=c)
    return c


def door_judge(handler):
    """(admit, flagged, why) for one punch-shaped request."""
    c = door_conf()
    if c["mode"] == "open":
        return True, False, "open"
    got = handler.headers.get(c["header"])
    if got is not None and str(got).strip() == c["value"]:
        return True, False, "mark"
    why = "no mark" if got is None else "wrong mark"
    return (c["mode"] == "watch"), True, why


def door_note(admitted, flagged, refused=False):
    """Update DOOR_STATE (atomic): counts, the newest refusal (last_failure_iso) and the newest admitted punch; last_ok_iso
    moves only when no refusal is younger than DOOR_RED_H -- the health leg stays red that long. admitted None = start-up."""
    try:
        with _door_lock:
            try:
                with open(DOOR_STATE, encoding="utf-8") as f:
                    st = json.load(f)
            except Exception:
                st = {}
            t = datetime.now()
            iso = t.strftime("%Y-%m-%dT%H:%M:%S")
            day = iso[:10]
            st["kit"], st["mode"] = "S957", door_conf()["mode"]
            byday = st.get("by_day") or {}
            if flagged:
                k = "refused" if refused else "would_refuse"
                st[k + "_total"] = int(st.get(k + "_total") or 0) + 1
                ent = byday.setdefault(day, {})
                ent[k] = int(ent.get(k) or 0) + 1
                st["last_failure_iso"] = iso
            if admitted:
                st["last_admitted_iso"] = iso
            st["by_day"] = {d: byday[d] for d in sorted(byday)[-14:]}
            lf = st.get("last_failure_iso") or ""
            fresh = True
            if lf:
                try:
                    fresh = (t - datetime.strptime(lf, "%Y-%m-%dT%H:%M:%S")).total_seconds() > DOOR_RED_H * 3600
                except Exception:
                    fresh = False
            if (admitted or admitted is None) and fresh:
                st["last_ok_iso"] = iso
            tmp = DOOR_STATE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(st, f, indent=1, sort_keys=True)
            os.replace(tmp, DOOR_STATE)
    except Exception:
        pass


def keep_aside(handler, uid, when, iom, vm, why):
    """A refused punch: one row in REFUSED_CSV (0600), never in punches.csv. Never raises."""
    try:
        ip = handler.client_address[0] if handler.client_address else ""
        with _door_lock:
            fresh = not os.path.exists(REFUSED_CSV)
            fd = os.open(REFUSED_CSV, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            with os.fdopen(fd, "a", encoding="utf-8") as f:
                if fresh:
                    f.write(REFUSED_HEADER)
                f.write("%s,%s,%s,%s,%s,%s,%s\n" % (str(uid).replace(",", " "), when, iom, vm, now_str(), ip, why))
    except Exception:
        pass


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # silence the default stderr access log

    def _read_body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        return self.rfile.read(n) if n else b""

    def _classify_and_capture(self, raw, live=False):
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
                admit, flagged, why = door_judge(self)              # S957: the door
                self._door = why
                if not admit:
                    self._door = "refused"
                    keep_aside(self, uid, when, iom, vm, why)
                    door_note(False, True, refused=True)
                    log(f"REFUSED user {uid}  {when}  {direction}  ({why}) -- kept aside in {REFUSED_CSV}, not stored -> response_code OK")
                    return "OK"
                wrote = save_punch(uid, when, iom, vm, live)
                door_note(True, flagged)
                if flagged:
                    log(f"DOOR   user {uid}  {when}  {direction}  ({why}) -- watch mode: stored, would be refused")
                if wrote:
                    log(f"PUNCH  user {uid}  {when}  {direction}  -> response_code OK")
                else:
                    log(f"DUP    user {uid}  {when}  {direction}  (re-send, not stored) -> response_code OK")
                return "OK"
        return "ERROR_NO_CMD"

    def _respond(self, method):
        raw = self._read_body()
        rc_hdr = self.headers.get("request_code", "")
        t = datetime.now()
        live = steadily_online(t)                        # S792: judged on the calls BEFORE this one
        note_contact(self, t)
        ack = self._classify_and_capture(raw, live)

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
    door_note(None, False)                                   # S957: the door's state, at start-up
    log(f"attlistener v2 STANDALONE (capture + local ack) on :{PORT}  "
        f"loaded {len(_seen)} existing punch keys  DEBUG={DEBUG}  — NO upstream call  SOURCE_WATCH=S535  DOOR={door_conf()['mode']} (S957)")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
