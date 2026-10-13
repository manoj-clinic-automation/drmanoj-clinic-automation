#!/usr/bin/env python3
"""make_s549.py -- kit S549 (session 313, 13-Oct-2026). Builds the new /root/wa/wa_receiver.py, clinic_watchdog.py and
clinic_health_report.py from their LIVE bytes (9f46279e, 35e40626, beb33190) by exact, counted, anchored edits, in memory
first (F-792); nothing is written unless every anchor occurs exactly once.
    python3 make_s549.py <wa_receiver FROM> <out> <clinic_watchdog FROM> <out> <clinic_health_report FROM> <out>"""
import hashlib
import sys

FROM = {"rx": "9f46279ebc080262102ab13ad200d6a9", "wd": "35e406261f27b2b0845911ee6382bb3d",
        "hr": "beb331903e227f7c2661f05aeaf12f8b"}
N = {"rx": 0, "wd": 0, "hr": 0}
EDITS = {
    "rx": [
        ('''DEPENDENCIES
  pip install Flask gspread google-auth
"""''', '''DEPENDENCIES
  pip install Flask gspread google-auth

S549 (13-Oct-2026, the owner: "ntfy whatsapp alert have stopped from 7th October" ... "why not move to server from Google
sheets"): the phone alert is sent from HERE, the moment a message arrives and before Google is touched -- wa_alert.py beside
this file (a queue with retries; a warning to the system topic when it cannot send). notifier_wa.py, which re-read the sheet
every 30 s and hung on a Google read at 14:37 IST 7-Oct, is retired (wa-notifier.service stopped and disabled).
"""'''),
        ('''import gspread
from google.oauth2.service_account import Credentials
''', '''import gspread
from google.oauth2.service_account import Credentials

try:
    import wa_alert                         # S549: the phone alert, sent from here -- never behind Google
except Exception as _e_alert:               # noqa: BLE001 -- without it the sheet is still written; the health page says so
    wa_alert = None
    print("[wa_receiver] wa_alert NOT loaded: %s" % _e_alert, flush=True)
'''),
        ('''    raw_log(payload)                       # ALWAYS keep the raw copy first
''', '''    raw_log(payload)                       # ALWAYS keep the raw copy first

    if wa_alert is not None:               # S549: the alert next, before Google -- a slow sheet can never hold it back
        try:
            wa_alert.from_payload(payload, dig, is_inbound_message)
        except Exception as e:             # noqa: BLE001
            log("alert hand-off failed:", e)
'''),
    ],
    "wd": [
        ('''    ("wa-notifier.service",              "WhatsApp -> phone notifier",       "systemctl restart wa-notifier"),
''', '''    # S549: wa-notifier.service retired -- the phone alert is sent by wa-receiver itself (wa_alert.py).
'''),
    ],
    "hr": [
        ('''    "wa-notifier",
''', '''    # "wa-notifier" retired at S549 -- the phone alert is sent by wa-receiver itself (wa_alert.py)
'''),
        ('''"SERVICES (9 always-on) ... %s" % svc_line''', '''"SERVICES (%d always-on) ... %s" % (len(SERVICES), svc_line)'''),
    ],
}


def main(a):
    if len(a) != 6:
        print(__doc__)
        return 2
    out = []
    for k, src_p, dst_p in (("rx", a[0], a[1]), ("wd", a[2], a[3]), ("hr", a[4], a[5])):
        raw = open(src_p, "rb").read()
        if hashlib.md5(raw).hexdigest() != FROM[k]:
            print("REFUSED: %s is %s, expected %s" % (src_p, hashlib.md5(raw).hexdigest(), FROM[k]))
            return 1
        s = raw.decode("utf-8")
        for old, new in EDITS[k]:
            if s.count(old) != 1:
                print("REFUSED: %s anchor found %d times: %r" % (k, s.count(old), old[:70]))
                return 1
            s = s.replace(old, new, 1)
            N[k] += 1
        out.append((dst_p, s.encode("utf-8")))
    for dst_p, b in out:
        open(dst_p, "wb").write(b)
        print("%s  %s" % (hashlib.md5(b).hexdigest(), dst_p))
    print("edits: wa_receiver %(rx)d · clinic_watchdog %(wd)d · clinic_health_report %(hr)d" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
