#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s809.py -- kit S809_WA_POST_VISIT_TEMPLATE. Made-up patients and numbers; a recorder stands where the request leaves.

    walk_s809.py <folder holding portal/portal_wa.py and portal/wa_ladder.py> [--control]
    S809_SEND=<folder holding the LIVE wa_ladder_send.py (kit S808)>      S809_OLD_WA=<the live portal_wa.py, before this kit>

Last line: "WALK OK n/n" | "WALK RED ..." ; with --control (the live files): "CONTROL: red n of m".
"""
import csv
import datetime as dt
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile

KIT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else "."
CONTROL = "--control" in sys.argv
ROOT = tempfile.mkdtemp(prefix="walk809_")
P = lambda *a: os.path.join(ROOT, *a)                                    # noqa: E731
os.environ.update({"FINANCE_DB": P("finance.db"), "WA_LADDER_DB": P("wa_ladder.db"), "WA_LADDER_INBOX_DB": P("inbox.db"),
                   "WA_LADDER_OLD_OPTOUT": P("old_optout.csv"), "WA_LADDER_CONSOLE_DB": P("console.db"), "WA_LADDER_ALL_OFF": P("ALL_OFF"),
                   "WA_LADDER_PORTAL_CONFIG": P("portal_config.py"), "WA_LADDER_INGEST": "0", "PORTAL_WA_DIR": P("wa_portal"),
                   "WA_LADDER_SEND_LOCK": P("run.lock")})
os.environ.pop("WA_LADDER_PORTAL_LOG", None)
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(KIT, "portal"))
sys.path.append(os.environ.get("S809_SEND", "/nonexistent"))
NEW, OLD = "copy_drmanoj_post_visit", "drmanoj_post_visit"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
T = "2026-11-17"
CLOCK = [dt.datetime(2026, 11, 17, 21, 5, tzinfo=IST)]
mob = lambda i: "9" + "%09d" % (80900 + i)                               # noqa: E731 -- made up at run time (F-185)
SENT = []
try:
    import portal_wa as W
    import wa_ladder as L
    import wa_ladder_send as S
    L.now_ist = lambda: CLOCK[0]

    class FakeConn(object):                                              # stands where the line to MyOperator is: records, answers "success"
        def __init__(self, host, timeout=20):
            self.host = host

        def request(self, method, path, data, headers):
            SENT.append({"host": self.host, "method": method, "body": json.loads(data.decode("utf-8")), "headers": sorted(headers)})

        def getresponse(self):
            class R(object):
                status, reason = 200, "OK"

                def read(self):
                    return json.dumps({"status": "success", "data": {"message_id": "m1", "conversation_id": "c1"}}).encode("utf-8")
            return R()

        def close(self):
            pass
    W.http.client.HTTPSConnection = FakeConn
    W.http.client.HTTPConnection = FakeConn
    HAVE = True
except Exception as e:                                                   # noqa: BLE001
    HAVE = False


def world():
    for f in os.listdir(ROOT):
        p = P(f)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(P("wa_portal"))
    con = sqlite3.connect(P("finance.db"))
    con.executescript("CREATE TABLE dx_visit(patient_uid, visit_date, clinic_id, follow_up_date);CREATE TABLE patient_visit(patient_uid, clinic_id, visit_date);"
                      "CREATE TABLE patient_ref(clinic_id, name, mobile, phone_last4);CREATE TABLE online_booking(name, mobile, appt_at);")
    con.execute("INSERT INTO patient_visit VALUES ('u1','5501',?)", (T,))
    con.execute("INSERT INTO patient_ref VALUES ('5501','Lata Made-up','',?)", (mob(1)[-4:],))
    con.commit(), con.close()
    cc = sqlite3.connect(P("console.db"))
    cc.execute("CREATE TABLE patients(phone10, patient_uid, clinic_id)"), cc.execute("INSERT INTO patients VALUES (?,?,?)", (mob(1), "u1", "5501"))
    cc.commit(), cc.close()
    ib = sqlite3.connect(P("inbox.db"))
    ib.execute("CREATE TABLE msgs(rid INTEGER PRIMARY KEY, dir, phone, ts, body)"), ib.commit(), ib.close()
    with open(P("portal_config.py"), "w") as fh:
        fh.write("MYOP_AUTH_TOKEN = 'made-up-key'\nPORTAL_WA_DRYRUN = '0'\nPORTAL_WA_USERS = 'manoj'\n")
    with open(W.LOG, "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerow(W.LOG_COLS)                              # the portal's send log, as it stands on the server: there, with its columns
    del SENT[:]
    S.SENDER = None                                                      # the REAL portal sender; only its last step (_post) is the recorder
    st = S.store()
    L._set(st, "send_test_mobile", mob(9))
    st.execute("INSERT INTO send_test(list, sent_at, ok, mode, confirmed_at, confirmed_by) VALUES ('post_visit','2026-11-17 12:00:00',1,'LIVE','2026-11-17 12:01:00','manoj')")
    st.execute("INSERT OR REPLACE INTO send_switch(list, is_on, at, by) VALUES ('post_visit',1,'2026-11-17 09:00:00','manoj')")
    st.commit(), st.close()


CHECKS = []


def check(name):
    def deco(fn):
        CHECKS.append((name, fn))
        return fn
    return deco


@check("01 the portal's sender knows the new post-visit message: one blank (the name), the same shape as the old one; every old message is still there, unchanged")
def _():
    old = open(os.environ["S809_OLD_WA"], encoding="utf-8").read()
    new = open(os.path.join(KIT, "portal", "portal_wa.py"), encoding="utf-8").read()
    a, b = W.TEMPLATES[NEW], W.TEMPLATES[OLD]
    kept = all(line in new for line in old.splitlines())
    return (a["fields"] == b["fields"] and a["family"] == b["family"] and a["lang"] == b["lang"] and "eport" not in a["preview"]
            and kept and len(new.splitlines()) == len(old.splitlines()) + 7 and len(W.TEMPLATES) == old.count('"family":') + 1)


@check("02 what leaves for the new message: its own name, the patient's name in the one blank, nothing else")
def _():
    t, body = W.build_body(NEW, {"1": "  Lata Made-up "})
    t2, body2 = W.build_body(OLD, {"1": "X"})
    try:
        W.build_body(NEW, {"1": ""})
        empty = False
    except ValueError:
        empty = True
    return body == {"1": "Lata Made-up"} and t is W.TEMPLATES[NEW] and body2 == {"1": "X"} and empty


@check("03 the 'After today's visit' list uses the new message; the other five lists are as they were")
def _():
    want = {"tomorrow": "drmanoj_followup_tomorrow", "post_visit": NEW, "appt": "appointment_reminder_1day_ortho", "due1": "drmanoj_followup_due",
            "due5": "drmanoj_followup_missed", "overdue": "drmanoj_followup_dropout"}
    world()
    p = L.plan(T)
    return {k: tp for k, _t, _w, tp in L.LISTS} == want and S.TPL == want and [x["template"] for x in p["lists"] if x["key"] == "post_visit"] == [NEW]


@check("04 the sending file and the sender still fit each other with the new name (the contract)")
def _():
    ok, _text = S.contract()
    return ok


@check("05 at 9:05 pm the timed run sends the NEW message to today's patient through the real portal sender -- one request, the right number and name")
def _():
    world()
    S.tick()
    row = sqlite3.connect(P("wa_ladder.db")).execute("SELECT template, state FROM send_row").fetchall()
    log = list(csv.DictReader(open(W.LOG, encoding="utf-8")))
    b = SENT[0]["body"] if len(SENT) == 1 else {}
    ctx = (b.get("data") or {}).get("context") or {}
    return (len(SENT) == 1 and ctx == {"template_name": NEW, "language": "en", "body": {"1": "Lata Made-up"}} and b.get("customer_number") == mob(1)
            and row == [(NEW, "sent")] and len(log) == 1 and log[0]["template"] == NEW and log[0]["mode"] == "LIVE" and log[0]["ok"] == "1")


@check("06 the test of 'After today's visit' to the doctor's phone is the NEW message")
def _():
    world()
    CLOCK[0] = dt.datetime(2026, 11, 17, 12, 30, tzinfo=IST)
    ok, _text = S.send_test("post_visit", "manoj", CLOCK[0])
    CLOCK[0] = dt.datetime(2026, 11, 17, 21, 5, tzinfo=IST)
    b = SENT[0]["body"] if len(SENT) == 1 else {}
    ctx = (b.get("data") or {}).get("context") or {}
    return ok and ctx == {"template_name": NEW, "language": "en", "body": {"1": "Test Patient"}} and b.get("customer_number") == mob(9)


@check("07 no phone number is written in the kit's own files (F-185); the kit ships no copy of a live file")
def _():
    here = os.path.dirname(os.path.abspath(__file__))
    bad = 0
    for f in os.listdir(here):
        if f.endswith((".py", ".sh", ".md", ".txt", ".md5")):
            bad += len(re.findall(r"(?<![\d.])[6-9]\d{9}(?!\d)", open(os.path.join(here, f), encoding="utf-8", errors="replace").read()))
    return bad == 0 and not os.path.isdir(os.path.join(here, "portal"))


def main():
    red = []
    for name, fn in CHECKS:
        try:
            good = HAVE and bool(fn())
        except Exception as e:                                           # noqa: BLE001
            good = False
            name += "   [%s: %s]" % (type(e).__name__, str(e)[:100])
        if not good:
            red.append(name)
    shutil.rmtree(ROOT, ignore_errors=True)
    n = len(CHECKS)
    if CONTROL:
        print("CONTROL: red %d of %d" % (len(red), n) if red else "CONTROL: GREEN -- the control did not go red")
        return 0
    for r in red:
        print("BAD " + r)
    print("WALK OK %d/%d" % (n, n) if not red else "WALK RED %d of %d" % (len(red), n))
    return 0 if not red else 1


if __name__ == "__main__":
    sys.exit(main())
