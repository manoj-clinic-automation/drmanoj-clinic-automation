#!/usr/bin/env python3
"""walk_s549.py -- kit S549 (session 313, 13-Oct-2026). Nothing is sent anywhere: the ntfy POST is replaced by a recorder,
Google by a stand-in that is DOWN, and the raw log goes to a temporary folder.
    python3 -B walk_s549.py <folder holding wa_receiver.py, wa_alert.py, clinic_watchdog.py, clinic_health_report.py>
                            [--expect-red]
A: wa_alert alone -- the alert's words (a known name, an unknown sender, a name the header cannot carry, a photo), one
   alert per message id, the retries and the one warning to the system topic when sending fails, no topic configured.
B: the receiver itself, with Google DOWN: an inbound WhatsApp still raises its alert; a status ping and our own outbound
   reply raise none; a re-push of the same message raises none.
C: the watchman and the health report no longer list wa-notifier.
--expect-red runs the same on the OLD files: they must fail. Prints 'WALK OK ...'; exit 1 on any failure."""
import importlib.util
import os
import re
import shutil
import sys
import tempfile
import time
import types

FAILS, RUN = [], [0]


def P(a, b):
    """A made-up mobile number, joined at run time (the repository holds no number at all, F-185)."""
    return a + b


def ok(c, what):
    RUN[0] += 1
    if not c:
        FAILS.append(what)


def stubs():
    for name in ("gspread",):
        try:
            __import__(name)
        except ImportError:
            m = types.ModuleType(name)
            m.authorize = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no gspread here"))
            sys.modules[name] = m
    try:
        from google.oauth2.service_account import Credentials  # noqa: F401
    except ImportError:
        g = types.ModuleType("google"); o = types.ModuleType("google.oauth2"); s = types.ModuleType("google.oauth2.service_account")

        class Credentials(object):
            @staticmethod
            def from_service_account_file(*a, **k):
                raise RuntimeError("no google here")
        s.Credentials = Credentials
        g.oauth2 = o; o.service_account = s
        sys.modules.update({"google": g, "google.oauth2": o, "google.oauth2.service_account": s})


def load(folder, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(folder, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


SENT = []


def recorder(fail_urls=()):
    def _post(url, title, body, priority="high", tags="speech_balloon"):
        SENT.append((url, title, body, tags))
        return url not in fail_urls
    return _post


def drain(wa, secs=10):
    t = time.time() + secs
    while time.time() < t:
        if wa._q.unfinished_tasks == 0:
            return True
        time.sleep(0.05)
    return False


def part_a(folder):
    path = os.path.join(folder, "wa_alert.py")
    ok(os.path.exists(path), "A: there is no wa_alert.py")
    if not os.path.exists(path):
        return None
    wa = load(folder, "wa_alert")
    wa.RETRY_WAITS = (0, 0, 0, 0)
    wa.NAMES_EVERY = 10 ** 9
    wa._names_try[0] = time.time()
    os.environ.update(NTFY_TOPIC="walktopic", NTFY_SERVER="http://walk.invalid", WATCHDOG_NTFY_URL="http://walk.invalid/system")
    T = "http://walk.invalid/walktopic"
    wa._post = recorder()
    del SENT[:]
    ok(wa.alert((P("91987", "6543210")), "knee pain since morning", "id-1") is True, "A: the alert was not queued")
    drain(wa)
    ok(SENT[-1:] == [(T, "New WhatsApp - new contact", (P("98765", "43210") + "\nknee pain since morning"), "speech_balloon")],
       "A: an unknown sender's alert reads %r" % (SENT[-1:],))
    ok(wa.alert((P("91987", "6543210")), "again", "id-1") is False and len(SENT) == 1, "A: the same message id alerted twice")
    wa._names[(P("98765", "43210"))] = "Ram Kumar"
    wa.alert("+91 " + P("98765", " 43210"), "ok", "id-2"); drain(wa)
    ok(SENT[-1][1] == "New WhatsApp - Ram Kumar" and SENT[-1][2] == (P("98765", "43210") + "\nok"), "A: a known name's alert reads %r" % (SENT[-1],))
    wa._names[(P("98111", "11111"))] = "राम"
    wa.alert((P("98111", "11111")), "", "id-3"); drain(wa)
    ok(SENT[-1][1] == "New WhatsApp" and SENT[-1][2].startswith(("राम · " + P("98111", "11111") + "\n(no text")),
       "A: a name in Hindi script, or an empty message, reads %r" % (SENT[-1],))
    del SENT[:]
    wa._post = recorder(fail_urls=(T,))
    wa._last_warn[0] = 0
    wa.alert((P("98222", "22222")), "x", "id-4"); drain(wa)
    tries = [s for s in SENT if s[0] == T]
    warns = [s for s in SENT if s[0].endswith("/system")]
    ok(len(tries) == 5 and len(warns) == 1 and warns[0][1] == "WhatsApp alerts failing",
       "A: a failing send made %d tries and %d warnings" % (len(tries), len(warns)))
    del SENT[:]
    wa.alert((P("98222", "22223")), "y", "id-5"); drain(wa)
    ok(len([s for s in SENT if s[0].endswith("/system")]) == 0, "A: a second failure inside 30 minutes warned again")
    del SENT[:]
    wa._post = recorder()
    os.environ["NTFY_TOPIC"] = ""
    wa._last_warn[0] = 0
    wa.alert((P("98333", "33333")), "z", "id-6"); drain(wa)
    ok([s[0] for s in SENT] == ["http://walk.invalid/system"], "A: with no topic configured: %r" % ([s[0] for s in SENT],))
    os.environ["NTFY_TOPIC"] = "walktopic"
    st = os.path.exists(wa.state_path()) and open(wa.state_path()).read()
    ok(bool(st) and (P("98222", "22222")) not in st and "knee" not in st, "A: the state file is missing or carries a number or a message")
    return wa


def part_b(folder, wa, tmp):
    os.environ.update(WA_SHEET_ID="walk-sheet", WA_SA_KEY="/nonexistent/key.json", WA_RAW_LOG_DIR=os.path.join(tmp, "rawlog"),
                      WA_WEBHOOK_SECRET="")
    rx = load(folder, "wa_receiver")

    def google_down(*a, **k):
        raise RuntimeError("Google is down (walk)")
    rx.ws_handle = google_down
    rx._state.update(ws=None, header=[], id_col=-1, seen=set())
    c = rx.app.test_client()
    if wa is not None:
        wa._post = recorder()
        wa._names.clear()
    del SENT[:]
    inbound = {"event_type": "message received", "customer_identifier": (P("91981", "2345678")), "direction": "incoming",
               "payload": {"id": "walk-m1", "data": {"type": "text", "context": {"body": "pain in knee"}}}}
    r = c.post("/wa-webhook", json=inbound)
    ok(r.status_code == 200, "B: the webhook answered %s" % r.status_code)
    if wa is not None:
        drain(wa)
    ok([s[1:3] for s in SENT] == [("New WhatsApp - new contact", (P("98123", "45678") + "\npain in knee"))],
       "B: with Google down, an inbound WhatsApp raised %r" % ([s[1:3] for s in SENT],))
    c.post("/wa-webhook", json=inbound)
    c.post("/wa-webhook", json={"event_type": "message delivered", "customer_identifier": (P("91981", "2345678")),
                                "payload": {"id": "walk-m2", "status": "delivered"}})
    c.post("/wa-webhook", json={"event_type": "message sent", "direction": "outgoing", "customer_identifier": (P("91981", "2345678")),
                                "payload": {"id": "walk-m3", "data": {"type": "text", "context": {"body": "our reply"}}}})
    if wa is not None:
        drain(wa)
    ok(len(SENT) == 1, "B: a repeat, a status ping or our own reply raised an alert (%d sent)" % len(SENT))
    ok(os.path.isdir(os.path.join(tmp, "rawlog")), "B: the raw log was not kept")


def part_c(folder):
    for f in ("clinic_watchdog.py", "clinic_health_report.py"):
        src = open(os.path.join(folder, f), encoding="utf-8").read()
        ok(not re.search(r'^\s*\(?"wa-notifier', src, re.M), "C: %s still lists wa-notifier" % f)


def main(a):
    folder = os.path.abspath(a[0])
    red = "--expect-red" in a
    stubs()
    tmp = tempfile.mkdtemp(prefix="walk_s549_")
    os.environ["WA_ALERT_STATE"] = os.path.join(tmp, "wa_alert_state.json")
    try:
        wa = None
        try:
            wa = part_a(folder)
        except Exception as e:                                     # noqa: BLE001
            ok(False, "A raised %r" % (e,))
        try:
            part_b(folder, wa, tmp)
        except Exception as e:                                     # noqa: BLE001
            ok(False, "B raised %r" % (e,))
        part_c(folder)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if red:
        if FAILS:
            print("WALK OK (negative control: the old files fail %d of %d checks, e.g. %s)" % (len(FAILS), RUN[0], FAILS[0][:90]))
            return 0
        print("WALK RED: the negative control passed on the old files -- the walk proves nothing")
        return 1
    if FAILS:
        print("WALK RED: %d of %d checks failed" % (len(FAILS), RUN[0]))
        for f in FAILS:
            print("  - " + f)
        return 1
    print("WALK OK: %d checks green (alert words, one per message, retries and one warning, no topic; the receiver alerts "
          "with Google down and stays quiet for status, repeats and our own replies; wa-notifier retired)" % RUN[0])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
