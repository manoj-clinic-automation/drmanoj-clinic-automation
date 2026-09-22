#!/usr/bin/env python3
"""
ring_hook.py -- kit S366_RING_POPUP (session 279, 22-Sep-2026) -- the caller's name on the staff phone as it rings (D590).

A SECOND MyOperator webhook entry (call.dial_begin + call.answered + call.end) posts here. The live
call-hook (call_hook_capture.py, :8098, /mo-callhook) is not touched and keeps every duty it has.

  dial_begin  -> for every agent leg being dialled: which login owns that phone (ring_agents.json), who is
                 calling (finance.db, by the clinic's own fingerprint), one Web Push to that login's phones.
  answered    -> the OTHER dialled phones see "<name> ne utha liya" in place of the ring pop-up.
  end         -> bridged: the pop-ups close on every phone; missed: every dialled phone keeps "missed" (stays
                 until tapped -- the Tracker's callback list has it too).

The reply is always 200 and immediate; the pushes go out on a background thread, so MyOperator never waits
on Google's push service. Every event body is written whole to ring_state/YYYY-MM-DD.jsonl (0700 dir) with
receive and push clock times -- that file is how the first real call's delay is measured.

GATE: ?key=<RING_HOOK_SECRET> (or header X-Webhook-Key). Rejections are counted and logged (metadata only),
never silent (the call-hook's F-? lesson of 06-08 Jul: 4,449 silent 403s).

Run:  /root/wa/venv/bin/gunicorn -w 1 -b 127.0.0.1:${RING_HOOK_PORT} --chdir /root/portal ring_hook:app
"""
import json
import os
import threading
import time
from datetime import datetime, timezone, timedelta

from flask import Flask, request, jsonify

import ring_common as rc

ENV = rc.load_env()
SECRET = (os.environ.get("RING_HOOK_SECRET") or ENV.get("RING_HOOK_SECRET") or "").strip()
INTERNAL_KEY = (os.environ.get("RING_INTERNAL_KEY") or ENV.get("RING_INTERNAL_KEY") or "").strip()
STATE_DIR = os.environ.get("RING_STATE_DIR", os.path.join(rc.PORTAL_DIR, "ring_state"))
IST = timezone(timedelta(hours=5, minutes=30))
TRACKER_URL = "/portal/go/call-tracker"
SESSION_TTL = 3 * 3600

app = Flask(__name__)
_sessions = {}            # session_id -> {"dialed": {login: name}, "answered": login|None, "caller": info, "t": epoch}
_lock = threading.Lock()
_stats = {"events": 0, "rejected": 0, "pushed": 0, "push_failed": 0, "started": int(time.time())}
PUSHER = None             # tests inject a fake webpush here


def _now_ist():
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _log(rec):
    try:
        os.makedirs(STATE_DIR, mode=0o700, exist_ok=True)
        rec["logged_ist"] = _now_ist()
        with open(os.path.join(STATE_DIR, datetime.now(IST).strftime("%Y-%m-%d") + ".jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _prune():
    cut = time.time() - SESSION_TTL
    for k in [k for k, v in _sessions.items() if v.get("t", 0) < cut]:
        _sessions.pop(k, None)


def _push(login, payload, session_id, kind):
    t0 = time.time()
    sent, failed = rc.push_user(login, payload, env=ENV, pusher=PUSHER)
    with _lock:
        _stats["pushed"] += sent
        _stats["push_failed"] += failed
    _log({"type": "push", "kind": kind, "session": session_id, "user": login, "sent": sent, "failed": failed,
          "took_ms": int((time.time() - t0) * 1000)})
    return sent, failed


def _legs(body):
    p = body.get("payload") if isinstance(body.get("payload"), dict) else {}
    legs = p.get("legs") if isinstance(p.get("legs"), list) else []
    return p, [l for l in legs if isinstance(l, dict)]


def handle_event(body, received_ist):
    """The whole decision for one webhook body. Returns a small dict for the log. Never raises."""
    ev = str(body.get("event_type") or "").lower()
    sid = str(body.get("session_id") or "")
    direction = str(body.get("direction") or "").lower()
    caller_num = body.get("customer_identifier") or ""
    p, legs = _legs(body)
    if not sid or direction not in ("incoming", "callback", ""):
        return {"skip": "no session or not incoming", "event": ev}
    agents = rc.load_agents()
    with _lock:
        _prune()
        st = _sessions.setdefault(sid, {"dialed": {}, "answered": None, "caller": None, "t": time.time(), "notified": set()})
        st["t"] = time.time()
    out = {"event": ev, "session": sid, "pushed_to": []}

    if ev == "call.dial_begin":
        if not caller_num:
            cust = [l for l in legs if str(l.get("type")) == "customer"]
            caller_num = cust[0].get("phone_number") if cust else ""
        if st["caller"] is None:
            st["caller"] = rc.lookup_caller(caller_num)
        title, text = rc.caller_card(st["caller"])
        for l in legs:
            if str(l.get("type")) != "agent":
                continue
            if str(l.get("result") or "").lower() not in ("dialing", "ringing", "", "not_answered") or l.get("answered_at"):
                continue
            a = rc.agent_for(l.get("phone_number"), agents)
            if not a:
                out.setdefault("unmapped_agents", 0)
                out["unmapped_agents"] += 1
                continue
            login = a["user"]
            st["dialed"][login] = a.get("name") or login
            if login in st["notified"]:
                continue
            st["notified"].add(login)
            payload = {"kind": "ring", "tag": "call-" + sid, "title": title, "body": text, "url": TRACKER_URL,
                       "mobile": st["caller"].get("mobile", ""), "ts": int(time.time() * 1000), "ttl": 60,
                       "requireInteraction": True, "renotify": True}
            threading.Thread(target=_push, args=(login, payload, sid, "ring"), daemon=True).start()
            out["pushed_to"].append(login)
        out["caller_known"] = bool((st["caller"] or {}).get("patients"))

    elif ev == "call.answered":
        who = None
        for l in legs:
            if str(l.get("type")) == "agent" and (str(l.get("result") or "").lower() == "answered" or l.get("answered_at")):
                who = rc.agent_for(l.get("phone_number"), agents)
        if who:
            st["answered"] = who["user"]
            name = who.get("name") or who["user"]
            title, _ = rc.caller_card(st["caller"] or rc.lookup_caller(caller_num))
            for login in list(st["dialed"].keys()):
                if login == who["user"]:
                    continue
                payload = {"kind": "answered", "tag": "call-" + sid, "title": title,
                           "body": name + " ने उठा लिया",   # <name> ने उठा लिया
                           "url": TRACKER_URL, "ts": int(time.time() * 1000), "ttl": 60,
                           "requireInteraction": False, "renotify": False}
                threading.Thread(target=_push, args=(login, payload, sid, "answered"), daemon=True).start()
                out["pushed_to"].append(login)
        out["answered_by"] = st["answered"]

    elif ev in ("call.end", "call.summary"):
        status = str(p.get("status") or "").lower()
        if not st["dialed"]:
            for l in legs:
                if str(l.get("type")) == "agent":
                    a = rc.agent_for(l.get("phone_number"), agents)
                    if a:
                        st["dialed"][a["user"]] = a.get("name") or a["user"]
        if status == "missed":
            title, text = rc.caller_card(st["caller"] or rc.lookup_caller(caller_num))
            for login in list(st["dialed"].keys()):
                payload = {"kind": "missed", "tag": "call-" + sid,
                           "title": "❌ Missed · " + title.replace("\U0001F4DE ", ""), "body": text + " · call back करें",
                           "url": TRACKER_URL, "ts": int(time.time() * 1000), "ttl": 600, "requireInteraction": True, "renotify": True}
                threading.Thread(target=_push, args=(login, payload, sid, "missed"), daemon=True).start()
                out["pushed_to"].append(login)
        else:
            for login in list(st["dialed"].keys()):
                payload = {"kind": "close", "tag": "call-" + sid, "ts": int(time.time() * 1000), "ttl": 60}
                threading.Thread(target=_push, args=(login, payload, sid, "close"), daemon=True).start()
                out["pushed_to"].append(login)
        out["status"] = status
        with _lock:
            _sessions.pop(sid, None)
    else:
        out["skip"] = "event not handled"
    return out


def _gate_ok():
    given = (request.args.get("key", "") or request.headers.get("X-Webhook-Key", "")).strip()
    return bool(SECRET) and given == SECRET


@app.route("/", methods=["GET"])
@app.route("/ring-hook/", methods=["GET"])
@app.route("/ring-hook/health", methods=["GET"])
def health():
    with _lock:
        s = dict(_stats)
    s.update({"service": "ring-hook", "status": "ok" if SECRET else "unconfigured", "sessions_open": len(_sessions),
              "agents_mapped": len(rc.load_agents()), "logins_subscribed": len([u for u, l in rc.load_subs()["users"].items() if l])})
    return jsonify(s), (200 if SECRET else 503)


@app.route("/ring-hook", methods=["GET", "POST"])
def hook():
    received = _now_ist()
    if not _gate_ok():
        with _lock:
            _stats["rejected"] += 1
        _log({"type": "reject", "ip": request.headers.get("X-Forwarded-For", request.remote_addr or ""), "method": request.method})
        return jsonify({"ok": False, "error": "forbidden"}), 403
    if request.method == "GET":
        ch = request.args.get("challenge") or request.args.get("hub.challenge")
        return (ch, 200, {"Content-Type": "text/plain"}) if ch else (jsonify({"ok": True, "service": "ring-hook"}), 200)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        try:
            body = json.loads(request.get_data(as_text=True) or "{}")
        except Exception:
            body = {}
    if not isinstance(body, dict):
        body = {}
    with _lock:
        _stats["events"] += 1
    try:
        out = handle_event(body, received)
    except Exception as e:  # noqa: BLE001
        out = {"error": type(e).__name__ + ": " + str(e)[:200]}
    _log({"type": "event", "received_ist": received, "event_type": body.get("event_type"), "event_ts": body.get("timestamp"),
          "session": body.get("session_id"), "result": out, "body": body})
    return jsonify({"ok": True}), 200


@app.route("/ring-hook/test", methods=["POST"])
def test_push():
    """The portal asks (from 127.0.0.1, with the internal key) for a test pop-up on one login's phones."""
    if not INTERNAL_KEY or request.headers.get("X-Internal-Key", "") != INTERNAL_KEY:
        return jsonify({"ok": False, "error": "forbidden"}), 403
    body = request.get_json(silent=True) or {}
    user = str(body.get("user") or "").strip()
    if not user:
        return jsonify({"ok": False, "error": "no user"}), 400
    payload = {"kind": "test", "tag": "test-" + user, "title": "✅ Clinic app · सूचना चालू",   # ✅ Clinic app · सूचना चालू
               "body": "अब call आने पर मरीज़ का नाम यहीं दिखेगा",  # अब call आने पर मरीज़ का नाम यहीं दिखेगा
               "url": "/portal", "ts": int(time.time() * 1000), "ttl": 60, "requireInteraction": False, "renotify": True}
    sent, failed = _push(user, payload, "test", "test")
    return jsonify({"ok": sent > 0, "sent": sent, "failed": failed}), 200


if __name__ == "__main__":
    port = int(os.environ.get("RING_HOOK_PORT") or ENV.get("RING_HOOK_PORT") or "8110")
    app.run(host="127.0.0.1", port=port)
