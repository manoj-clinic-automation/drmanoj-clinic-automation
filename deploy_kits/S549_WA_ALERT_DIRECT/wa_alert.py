#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wa_alert.py -- kit S549 (session 313, 13-Oct-2026): the WhatsApp -> phone alert, sent by the receiver itself.

THE OWNER, 13-Oct-2026: "ntfy whatsapp alert have stopped from 7th October, system ones are still coming" (18:23) ·
"why not move to server from Google sheets, if it's more reliable?" (18:29) · "It's urgent" (18:47).

WHAT WENT WRONG. notifier_wa.py re-read the WA_Inbox sheet every 30 seconds and pushed what was new. On 7-Oct at 14:37 IST
a Google read never returned; the process stayed "active", so no watch noticed, and no alert went out for six days while
the messages kept landing in the sheet.

WHAT THIS DOES INSTEAD. wa_receiver.py -- the service MyOperator pushes every inbound WhatsApp to -- hands the message here
the moment it arrives, BEFORE it touches Google. One worker thread sends it to the WhatsApp ntfy topic; a failed send is
retried (5 s, 30 s, 2 min, 10 min); if every try fails, one warning goes to the system topic (at most once in 30 minutes).
Google is no longer on the alert path at all: the sheet is still written exactly as before, for the tracker, and the
patient names (Patient_Master) are refreshed in the background -- a slow or failed Google read only means a name may be
missing from an alert, never that the alert is missing.

The same alert as before (S231 / S420, D587): title "New WhatsApp - <name>", body "<number>\\n<message>"; an unknown sender
reads "new contact"; a photo or file with no text says so. Each message id alerts once.

NOTHING SECRET IS WRITTEN HERE. The topics come from /root/wa/.env through the receiver's environment (NTFY_TOPIC,
NTFY_SERVER, WATCHDOG_NTFY_URL). The state file wa_alert_state.json holds counts and times only -- no number, no text.
"""
import collections
import datetime
import json
import os
import queue
import re
import threading
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
MAX_PUSH_CHARS = 1500
RETRY_WAITS = (5, 30, 120, 600)          # seconds before each retry; after the last, the warning
WARN_EVERY = 1800                         # at most one failure warning in this many seconds
NAMES_EVERY = 1800                        # Patient_Master re-read
NAMES_LIMIT = 90                          # a name read that takes longer is left behind (it may hang; alerts never wait)

_q = queue.Queue()
_seen = collections.OrderedDict()
_lock = threading.Lock()
_names = {}
_st = {"started": None, "sent": 0, "failed": 0, "retried": 0, "dupes": 0, "last_ok": "", "last_fail": "",
       "last_warn": "", "names": 0, "names_at": "", "names_err": ""}
_threads = {"worker": None, "names": None}
_last_warn = [0.0]
_names_try = [0.0]


def _now():
    return datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


def _log(*a):
    print("[wa_alert]", *a, flush=True)


def _env(k, d=""):
    return (os.environ.get(k) or d).strip()


def state_path():
    return _env("WA_ALERT_STATE", os.path.join(HERE, "wa_alert_state.json"))


def _save():
    try:
        p = state_path()
        tmp = "%s.part%d" % (p, os.getpid())
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(dict(_st, queued=_q.qsize()), fh)
        os.chmod(tmp, 0o600)
        os.replace(tmp, p)
    except OSError:
        pass


def last10(s):
    d = re.sub(r"\D", "", str(s or ""))
    return d[-10:] if len(d) >= 10 else d


def ascii_title(s):
    t = re.sub(r"\s+", " ", str(s or ""))
    return "".join(ch for ch in t if 32 <= ord(ch) < 127).strip()


def clip(s, n=MAX_PUSH_CHARS):
    s = str(s or "").strip()
    return s if len(s) <= n else s[:n - 1].rstrip() + "…"


def _post(url, title, body, priority="high", tags="speech_balloon"):
    """One HTTP POST to ntfy. True on 2xx. The walk replaces this function."""
    req = urllib.request.Request(url, data=body.encode("utf-8"), method="POST")
    req.add_header("Title", ascii_title(title) or "New WhatsApp")
    req.add_header("Priority", priority)
    req.add_header("Tags", tags)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return 200 <= resp.status < 300
    except Exception as e:                                         # noqa: BLE001
        _log("push failed:", type(e).__name__, str(e)[:120])
        return False


def _topic_url():
    t = _env("NTFY_TOPIC")
    if not t:
        return ""
    return "%s/%s" % (_env("NTFY_SERVER", "https://ntfy.sh").rstrip("/") or "https://ntfy.sh", t)


def _warn(text):
    """The system topic, at most once in WARN_EVERY. Never raises."""
    url = _env("WATCHDOG_NTFY_URL")
    if not url or time.time() - _last_warn[0] < WARN_EVERY:
        return
    _last_warn[0] = time.time()
    _st["last_warn"] = _now()
    try:
        _post(url, "WhatsApp alerts failing", text, priority="high", tags="warning")
    except Exception:                                              # noqa: BLE001
        pass


# ------------------------------------------------------------------ names (background only; never on the alert's path)
def _load_names():
    import gspread                                                 # noqa: PLC0415
    from google.oauth2.service_account import Credentials           # noqa: PLC0415
    creds = Credentials.from_service_account_file(_env("WA_SA_KEY"),
                                                  scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    gc = gspread.authorize(creds)
    if hasattr(gc, "set_timeout"):
        try:
            gc.set_timeout(60)
        except Exception:                                          # noqa: BLE001
            pass
    sheet = _env("PATIENT_SHEET_ID") or _env("WA_SHEET_ID")
    vals = gc.open_by_key(sheet).worksheet(_env("PATIENT_TAB", "Patient_Master")).get_all_values()
    m = {}
    if len(vals) < 2:
        return m
    H = [str(x).strip().lower() for x in vals[0]]

    def col(cands):
        for c in cands:
            if c in H:
                return H.index(c)
        for c in cands:
            for i, h in enumerate(H):
                if c in h:
                    return i
        return -1
    ip = col(['phone number', 'mobile number', 'mobile no', 'mobile', 'phone', 'number', 'phone10'])
    iname = col(['patient name', 'name', 'first name'])
    if ip < 0:
        return m
    for r in vals[1:]:
        ph = last10(r[ip]) if ip < len(r) else ""
        nm = r[iname].strip() if 0 <= iname < len(r) else ""
        if ph and nm and ph not in m:
            m[ph] = nm
    return m


def _names_job():
    try:
        m = _load_names()
        if m:
            _names.clear()
            _names.update(m)
        _st["names"], _st["names_at"], _st["names_err"] = len(_names), _now(), ""
    except Exception as e:                                         # noqa: BLE001
        _st["names_err"] = "%s %s" % (_now(), type(e).__name__)
        _log("names not refreshed:", type(e).__name__, str(e)[:120])
    _save()


def _maybe_names():
    t = _threads["names"]
    if t is not None and t.is_alive():
        return                                                     # a read still running (or hung): leave it, alert anyway
    if time.time() - _names_try[0] < (NAMES_EVERY if _names else 120):
        return
    _names_try[0] = time.time()
    if not _env("WA_SA_KEY"):
        return
    t = threading.Thread(target=_names_job, name="wa_alert_names", daemon=True)
    _threads["names"] = t
    t.start()


# ------------------------------------------------------------------ the queue
def _worker():
    while True:
        item = _q.get()
        try:
            _send(item)
        except Exception as e:                                     # noqa: BLE001 -- the worker never dies
            _log("worker error:", type(e).__name__, str(e)[:120])
        finally:
            _q.task_done()
            _save()


def _send(item):
    url = _topic_url()
    if not url:
        _st["failed"] += 1
        _st["last_fail"] = _now()
        _log("NTFY_TOPIC is not set -- alert not sent")
        _warn("NTFY_TOPIC is not set on the server, so WhatsApp alerts cannot be sent. Messages are still in the tracker.")
        return
    name = _names.get(last10(item["phone"]), "") or "new contact"
    number = last10(item["phone"]) or str(item["phone"] or "").strip()
    text = clip(item["text"]) or "(no text - a photo, file or empty message)"
    title = ascii_title("New WhatsApp - " + name)
    if name not in title:                                          # a name the ASCII header cannot carry rides in the body
        title, body = "New WhatsApp", "%s · %s\n%s" % (name, number, text) if number else "%s\n%s" % (name, text)
    else:
        body = "%s\n%s" % (number, text) if number else text
    for i in range(len(RETRY_WAITS) + 1):
        if _post(url, title, body):
            _st["sent"] += 1
            _st["last_ok"] = _now()
            return
        if i < len(RETRY_WAITS):
            _st["retried"] += 1
            _save()
            time.sleep(RETRY_WAITS[i])
    _st["failed"] += 1
    _st["last_fail"] = _now()
    _warn("A WhatsApp alert could not be sent after %d tries (%d failed so far). The message is in the follow-up tracker."
          % (len(RETRY_WAITS) + 1, _st["failed"]))


def _ensure_worker():
    with _lock:
        t = _threads["worker"]
        if t is None or not t.is_alive():
            if _st["started"] is None:
                _st["started"] = _now()
            t = threading.Thread(target=_worker, name="wa_alert_worker", daemon=True)
            _threads["worker"] = t
            t.start()


def alert(phone, text, msg_id=""):
    """Queue one alert. Returns True when queued, False for a repeat of a message already alerted. Never raises."""
    try:
        mid = str(msg_id or "").strip()
        with _lock:
            if mid:
                if mid in _seen:
                    _st["dupes"] += 1
                    return False
                _seen[mid] = 1
                while len(_seen) > 5000:
                    _seen.popitem(last=False)
        _ensure_worker()
        _maybe_names()
        _q.put({"phone": phone, "text": text})
        return True
    except Exception as e:                                         # noqa: BLE001
        _log("alert not queued:", type(e).__name__, str(e)[:120])
        return False


MEDIA_TYPES = ("image", "document", "video", "audio", "sticker", "voice")


def from_payload(payload, dig, is_inbound_message):
    """The receiver's raw push -> one queued alert, or nothing (a status ping, our own outbound, a repeat).
    The field paths are the receiver's own (build_row), so the alert reads exactly what the sheet gets."""
    phone = dig(payload, "customer_identifier", "payload.customer_identifier", "data.customer_identifier", "customer_number",
                "payload.customer_number", "payload.data.context.from", "contact.wa_id")
    direction = dig(payload, "direction", "payload.direction", "data.direction", default="incoming")
    mtype = dig(payload, "payload.data.type", "data.type", "payload.type", "type", default="text")
    message = dig(payload, "payload.data.context.body", "data.context.body", "payload.data.body", "data.body", "message",
                  "text", default="")
    msg_id = dig(payload, "payload.id", "payload.message_id", "data.id", "id", "message_id")
    event = dig(payload, "event_type", "event", "payload.event_type", default="")
    if not is_inbound_message(event, direction, mtype, message):
        return False
    if not message and str(mtype).lower() in MEDIA_TYPES:
        message = "(%s)" % str(mtype).lower()
    return alert("".join(ch for ch in str(phone) if ch.isdigit()), str(message or ""), str(msg_id or ""))
