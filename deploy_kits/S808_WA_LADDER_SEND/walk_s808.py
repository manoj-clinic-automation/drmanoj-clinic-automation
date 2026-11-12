#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s808.py -- kit S808_WA_LADDER_SEND. The plan's thirteen rules, each walked on MADE-UP patients and numbers, with a
recorder standing where the sender is. Nothing is sent to anyone; nothing outside its own scratch folder is read or written.

    walk_s808.py <folder that holds portal/wa_ladder.py and portal/wa_ladder_send.py> [--control]
    S808_PORTAL_WA=<folder that holds the LIVE portal_wa.py>   (the contract check reads it)

Last line: "WALK OK n/n" or "WALK RED ..."; with --control (the live files, which cannot send): "CONTROL: red n of m".
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
ROOT = tempfile.mkdtemp(prefix="walk808_")
P = lambda *a: os.path.join(ROOT, *a)                                    # noqa: E731
os.environ.update({"FINANCE_DB": P("finance.db"), "WA_LADDER_DB": P("wa_ladder.db"), "WA_LADDER_INBOX_DB": P("inbox.db"),
                   "WA_LADDER_OLD_OPTOUT": P("old_optout.csv"), "WA_LADDER_CONSOLE_DB": P("console.db"),
                   "WA_LADDER_ALL_OFF": P("ALL_OFF"), "WA_LADDER_PORTAL_CONFIG": P("portal_config.py"),
                   "WA_LADDER_PORTAL_LOG": P("wa_portal_sends.csv"), "WA_LADDER_INGEST": "0", "PORTAL_WA_DIR": P("wa_portal"),
                   "WA_LADDER_SEND_LOCK": P("run.lock")})
for k in ("MYOP_AUTH_TOKEN", "PORTAL_WA_DRYRUN", "PORTAL_WA_USERS"):
    os.environ.pop(k, None)
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(KIT, "portal"))
if os.environ.get("S808_PORTAL_WA"):
    sys.path.append(os.environ["S808_PORTAL_WA"])

RES = []
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
KEYWORD = "madeup-key-" + "s808walk"                                     # stands for the WhatsApp key; must never reach a page
T = "2026-11-17"                                                         # a Tuesday
CLOCK = [dt.datetime(2026, 11, 17, 9, 0, tzinfo=IST)]


def at(hhmm, day=T):
    CLOCK[0] = dt.datetime.strptime(day + " " + hhmm, "%Y-%m-%d %H:%M").replace(tzinfo=IST)
    return CLOCK[0]


def mob(i):
    return "9" + "%09d" % (80800 + i)                                     # made up at run time: no number is written here (F-185)


try:
    import wa_ladder as L
    import wa_ladder_send as S
    L.now_ist = lambda: CLOCK[0]
    HAVE = True
except Exception as e:                                                   # noqa: BLE001 -- the control: the live files cannot send
    HAVE, IMPORT_ERR = False, "%s: %s" % (type(e).__name__, e)


class Rec(object):
    """Stands where portal_wa.send is. script: a list of answers (a dict, or an Exception to raise), or a function(n, call)."""
    def __init__(self):
        self.calls, self.script, self.hook = [], [], None

    def __call__(self, phone, template_name, values, sent_by, token, dry_run=True, timeout=20):
        c = {"phone": phone, "template": template_name, "values": dict(values), "by": sent_by, "token": token, "dry": dry_run}
        self.calls.append(c)
        if self.hook:
            self.hook(len(self.calls), c)
        a = self.script.pop(0) if self.script else None
        if isinstance(a, Exception):
            raise a
        if a is None:
            a = {"ok": True, "message_id": "m%d" % len(self.calls), "conversation_id": "", "mode": "DRY" if dry_run else "LIVE", "error": ""}
        if not dry_run and a.get("mode") == "LIVE":                      # what the real sender does: one row in the portal's log
            with open(P("wa_portal_sends.csv"), "a", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerow([CLOCK[0].isoformat(timespec="seconds"), sent_by, phone, template_name, json.dumps(values), "LIVE",
                                         "1" if a.get("ok") else "0", a.get("message_id", ""), "", a.get("error", "")])
        return a

    def phones(self):
        return [c["phone"] for c in self.calls]


REC = Rec()
LOGCOLS = ["ts_ist", "sent_by", "phone", "template", "values_json", "mode", "ok", "message_id", "conversation_id", "error"]
PEOPLE = {  # key: (clinic id, name, number index, follow-up date, visit date)
    "A1": ("4401", "Asha Made-up", 1, "2026-11-18", "2026-11-10"), "A2": ("4402", "Bharat Made-up", 2, "2026-11-18", "2026-11-10"),
    "A3": ("4403", "Chand Made-up", 3, "2026-11-18", "2026-11-10"), "A4": ("4404", "Deepa Made-up", 4, "2026-11-18", "2026-11-10"),
    "A5": ("4405", "Ekta Made-up", 5, "2026-11-18", "2026-11-10"),
    "B1": ("4411", "Farid Made-up", 11, "2026-11-16", "2026-11-09"), "B2": ("4412", "Gita Made-up", 12, "2026-11-16", "2026-11-09"),
    "C1": ("4421", "Hari Made-up", 21, "2026-11-12", "2026-11-05"),
    "O1": ("4431", "Indu Made-up", 31, "2026-11-03", "2026-10-27"), "O2": ("4432", "Jai Made-up", 32, "2026-11-03", "2026-10-27"),
    "O3": ("4433", "Kiran Made-up", 33, "2026-11-03", "2026-10-27"),
}
M = lambda k: mob(PEOPLE[k][2])                                          # noqa: E731


def world(live=True, users="manoj", visits_to="2026-11-16", today_visits=True, test_all=True, a4_back=True):
    """A fresh made-up clinic. Every switch OFF. test_all: every message's test already confirmed."""
    for f in os.listdir(ROOT):
        p = P(f)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(P("wa_portal"))
    con = sqlite3.connect(P("finance.db"))
    con.executescript("CREATE TABLE dx_visit(patient_uid, visit_date, clinic_id, follow_up_date);"
                      "CREATE TABLE patient_visit(patient_uid, clinic_id, visit_date);"
                      "CREATE TABLE patient_ref(clinic_id, name, mobile, phone_last4);"
                      "CREATE TABLE online_booking(name, mobile, appt_at);")
    cc = sqlite3.connect(P("console.db"))
    cc.execute("CREATE TABLE patients(phone10, patient_uid, clinic_id)")
    for k, (cid, name, i, fu, vd) in PEOPLE.items():
        con.execute("INSERT INTO dx_visit VALUES (?,?,?,?)", ("u" + cid, vd, cid, fu))
        con.execute("INSERT INTO patient_visit VALUES (?,?,?)", ("u" + cid, cid, vd))
        con.execute("INSERT INTO patient_ref VALUES (?,?,?,?)", (cid, name, "", mob(i)[-4:]))
        cc.execute("INSERT INTO patients VALUES (?,?,?)", (mob(i), "u" + cid, cid))
    if a4_back:
        con.execute("INSERT INTO patient_visit VALUES ('u4404','4404','2026-11-15')")      # A4 has come since: on no list
    # someone seen on each clinic day up to visits_to (so the records are 'up to date' as far as that day)
    for d in ("2026-11-13", "2026-11-14", "2026-11-16"):
        if d <= visits_to:
            con.execute("INSERT INTO patient_visit VALUES ('u4490','4490',?)", (d,))
    con.execute("INSERT INTO patient_ref VALUES ('4490','Old Made-up','','0000')")
    if today_visits:                                                     # seen today: P1; P2 is of A1's family (the same number)
        for cid, name, i in (("4451", "Lata Made-up", 51), ("4452", "Mohan Made-up", 1)):
            con.execute("INSERT INTO patient_visit VALUES (?,?,?)", ("u" + cid, cid, T))
            con.execute("INSERT INTO patient_ref VALUES (?,?,?,?)", (cid, name, "", mob(i)[-4:]))
            cc.execute("INSERT INTO patients VALUES (?,?,?)", (mob(i), "u" + cid, cid))
    con.execute("INSERT INTO online_booking VALUES ('Neha Made-up', ?, '2026-11-18 18:45')", (mob(61),))
    con.commit(), con.close(), cc.commit(), cc.close()
    ib = sqlite3.connect(P("inbox.db"))
    ib.execute("CREATE TABLE msgs(rid INTEGER PRIMARY KEY, dir, phone, ts, body)")
    ib.commit(), ib.close()
    with open(P("wa_portal_sends.csv"), "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerow(LOGCOLS)
    with open(P("portal_config.py"), "w", encoding="utf-8") as fh:
        fh.write("MYOP_AUTH_TOKEN = %r\nPORTAL_WA_DRYRUN = %r\nPORTAL_WA_USERS = %r\n" % (KEYWORD, "0" if live else "1", users))
    REC.calls, REC.script, REC.hook = [], [], None
    S.SENDER = REC
    S.READER_RETRY_S = 0
    os.environ["WA_LADDER_INGEST"] = "0"
    sys.modules.pop("portal_inbox", None)
    at("09:00")
    st = S.store()
    st.execute("INSERT INTO optout(mobile, at, source, said, rid) VALUES (?,?,?,?,NULL)", (M("A3"), "2026-11-01 10:00:00", "WhatsApp reply", "stop"))
    L._set(st, "send_test_mobile", mob(99))
    L._set(st, "last_scan", "2026-11-17 08:59:00")
    if test_all:
        for k in S.TPL:
            st.execute("INSERT INTO send_test(list, sent_at, ok, mode, confirmed_at, confirmed_by) VALUES (?,?,1,'LIVE',?,'manoj')", (k, "2026-11-16 12:00:00", "2026-11-16 12:01:00"))
    st.commit(), st.close()


def on(*keys):
    for k in keys:
        ok, text = S.set_switch(k, True, "manoj", CLOCK[0])
        assert ok, text


def q(sql, args=()):
    con = sqlite3.connect(P("wa_ladder.db"))
    try:
        return con.execute(sql, args).fetchall()
    finally:
        con.close()


def plog(*rows):
    with open(P("wa_portal_sends.csv"), "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        for ts, phone, tpl, vals, mode, ok, err in rows:
            w.writerow([ts, "manoj", phone, tpl, json.dumps(vals), mode, ok, "x", "", err])


OWNER = {"user": "manoj", "role": "doctor"}
CHECKS = []


def check(name):
    def deco(fn):
        CHECKS.append((name, fn))
        return fn
    return deco


# ============================================================ rule 1 and 10: the switches, the tests
@check("01 a fresh store: every switch OFF; at a list's time nothing is sent (rule 1)")
def _():
    world()
    at("18:05")
    lines = S.tick()
    return not REC.calls and not lines and not q("SELECT 1 FROM send_row") and not q("SELECT 1 FROM send_switch WHERE is_on<>0")


@check("02 a switch cannot be turned ON before a LIVE test has been confirmed (rule 10)")
def _():
    world(test_all=False)
    a = S.set_switch("tomorrow", True, "manoj", CLOCK[0])
    ok1, t1 = S.send_test("tomorrow", "manoj", CLOCK[0])
    b = S.set_switch("tomorrow", True, "manoj", CLOCK[0])                 # sent, not yet confirmed
    ok2, _t = S.confirm_test("tomorrow", "manoj", CLOCK[0])
    c = S.set_switch("tomorrow", True, "manoj", CLOCK[0])
    d = S.set_switch("due1", True, "manoj", CLOCK[0])                     # another message: its own test
    return (not a[0] and ok1 and not b[0] and ok2 and c[0] and not d[0]
            and q("SELECT is_on FROM send_switch WHERE list='tomorrow'") == [(1,)] and not q("SELECT 1 FROM send_switch WHERE list='due1' AND is_on=1"))


@check("03 the test goes to the doctor's own number only, with a made-up name, through the one sender, once")
def _():
    world(test_all=False)
    ok, text = S.door("test", {"list": "due5", "mobile": M("A1"), "name": "Asha", "phone": M("A2")}, OWNER)
    c = REC.calls
    return (ok and len(c) == 1 and c[0]["phone"] == mob(99) and c[0]["template"] == "drmanoj_followup_missed" and c[0]["values"]["1"] == "Test Patient"
            and c[0]["by"] == "wa_ladder:test" and c[0]["dry"] is False and c[0]["token"] == KEYWORD and mob(99) not in text and mob(99)[-4:] in text)


@check("04 no number for the tests on the server: the test is refused and nothing is sent")
def _():
    world(test_all=False)
    st = S.store()
    st.execute("DELETE FROM meta WHERE k='send_test_mobile'"), st.commit(), st.close()
    ok, text = S.send_test("tomorrow", "manoj", CLOCK[0])
    bad = S.set_test_mobile("0581 2567890")[0] or S.set_test_mobile("12345")[0]
    good = S.set_test_mobile("+91 " + mob(98))[0]
    return not ok and not REC.calls and not bad and good and q("SELECT v FROM meta WHERE k='send_test_mobile'") == [(mob(98),)]


@check("05 TEST mode: a test does not leave and cannot be confirmed; no switch goes ON; the timed run sends nothing (rule 11)")
def _():
    world(live=False, test_all=False)
    ok, text = S.send_test("tomorrow", "manoj", CLOCK[0])
    dry_only = len(REC.calls) == 1 and REC.calls[0]["dry"] is True
    c = S.confirm_test("tomorrow", "manoj", CLOCK[0])
    world(live=False)                                                    # tests confirmed earlier, in LIVE; now the portal is in TEST
    a = S.set_switch("tomorrow", True, "manoj", CLOCK[0])
    st = S.store()
    st.execute("INSERT OR REPLACE INTO send_switch(list, is_on, at, by) VALUES ('tomorrow',1,'2026-11-16 09:00:00','manoj')"), st.commit(), st.close()
    at("18:05")
    S.tick()
    return ok and "TEST" in text and dry_only and not c[0] and not a[0] and not REC.calls and not q("SELECT 1 FROM send_row") and S.mode()[0] == "TEST"


@check("06 the estate's switch ALL_OFF: no test, no switch ON, no timed run, no ticked names (rule 13)")
def _():
    world()
    st = S.store()
    st.execute("INSERT OR REPLACE INTO send_switch(list, is_on, at, by) VALUES ('tomorrow',1,'2026-11-16 09:00:00','manoj')"), st.commit(), st.close()
    open(P("ALL_OFF"), "w").close()
    at("18:05")
    lines = S.tick()
    a = S.send_test("tomorrow", "manoj", CLOCK[0])
    b = S.set_switch("due1", True, "manoj", CLOCK[0])
    p = L.plan(T)
    toks = [S.token(T, "overdue", r) for x in p["lists"] if x["key"] == "overdue" for r in x["rows"]]
    c = S.send_ticked(toks, T, "manoj")
    return not REC.calls and not lines and not a[0] and not b[0] and not c[0] and len(toks) == 3 and S.mode()[0] == "OFF"


# ============================================================ rules 2, 6, 7, 8: one list, once, at its time
@check("07 before its time nothing; at its time the list goes: the right people, the right message, one request each (rules 2, 7, 8)")
def _():
    world()
    on("tomorrow")
    at("17:55")
    S.tick()
    early = len(REC.calls)
    at("18:05")
    lines = S.tick()
    c = REC.calls
    want = sorted([M("A1"), M("A2"), M("A5")])                           # A3 said STOP; A4 has come since
    return (early == 0 and sorted(REC.phones()) == want and all(x["template"] == "drmanoj_followup_tomorrow" and x["dry"] is False and x["by"] == "wa_ladder:tomorrow"
                                                                 and x["token"] == KEYWORD and x["values"]["2"] == "18 Nov 2026" for x in c)
            and sorted(x["values"]["1"] for x in c) == ["Asha Made-up", "Bharat Made-up", "Ekta Made-up"]
            and q("SELECT state, sent, failed, held FROM send_run WHERE day=? AND list='tomorrow'", (T,)) == [("done", 3, 0, 1)]
            and q("SELECT COUNT(*) FROM send_row WHERE state='sent' AND day=? AND ref_date='2026-11-18'", (T,)) == [(3,)] and len(lines) == 1)


@check("08 the same list never goes twice the same day: not at the next tick, not when called again directly (rule 8)")
def _():
    world()
    on("tomorrow")
    at("18:05"), S.tick()
    n = len(REC.calls)
    at("18:10"), S.tick()
    at("19:25"), S.tick()
    S.send_list("tomorrow", "timer")                                     # even called directly: every row is on record
    return n == 3 and len(REC.calls) == 3


@check("09 written ahead: when the request leaves, the row is already on record as 'trying' (rule 6)")
def _():
    world()
    on("tomorrow")
    seen = []
    REC.hook = lambda n, c: seen.append(q("SELECT state FROM send_row WHERE mobile=? AND day=?", (c["phone"], T)))
    at("18:05"), S.tick()
    return len(seen) == 3 and all(s == [("trying",)] for s in seen)


@check("10 the sender breaks after the request left: the row stays 'trying', the batch STOPS, nothing is tried again that day (rule 6, F-1297, F-1313)")
def _():
    world()
    on("tomorrow")
    REC.script = [RuntimeError("boom")]
    at("18:05"), S.tick()
    first = REC.phones()
    at("18:10"), S.tick()
    at("19:20"), S.tick()
    S.send_list("tomorrow", "timer")                                     # called again directly: the broken row is not tried, nor the rest
    run = q("SELECT state, sent, failed FROM send_run WHERE day=? AND list='tomorrow'", (T,))
    again = len(REC.calls)                                               # the direct call sends the two that were never tried -- once
    return (len(first) == 1 and again == 3 and first[0] not in REC.phones()[1:] and q("SELECT state FROM send_row WHERE mobile=?", (first[0],)) == [("trying",)]
            and run == [("stopped", 0, 1)] and q("SELECT COUNT(*) FROM send_row") == [(3,)])


@check("11 WhatsApp refuses with a wrong-key answer (HTTP 403): the batch stops at the first row; the rest keep their one try")
def _():
    world()
    on("tomorrow")
    REC.script = [{"ok": False, "mode": "LIVE", "error": "HTTP 403: {\"message\":\"x " + mob(1) + "\"}"}]
    at("18:05"), S.tick()
    at("18:10"), S.tick()
    r = q("SELECT state, reason FROM send_row")
    return len(REC.calls) == 1 and len(r) == 1 and r[0][0] == "failed" and "403" in r[0][1] and mob(1) not in r[0][1] and q("SELECT state FROM send_run") == [("stopped",)]


@check("12 no clear answer (a timeout): the row is 'may have gone', the batch stops, it is not tried again")
def _():
    world()
    on("tomorrow")
    REC.script = [{"ok": False, "mode": "LIVE", "error": "send failed: timed out"}]
    at("18:05"), S.tick()
    at("18:10"), S.tick()
    return len(REC.calls) == 1 and q("SELECT state FROM send_row") == [("unsure",)]


@check("13 one refusal of one row (HTTP 400) does not stop the list; two in a row do")
def _():
    world()
    on("tomorrow")
    REC.script = [{"ok": False, "mode": "LIVE", "error": "HTTP 400: bad"}]
    at("18:05"), S.tick()
    one = (len(REC.calls), sorted(x[0] for x in q("SELECT state FROM send_row")))
    world()
    on("tomorrow")
    REC.script = [{"ok": False, "mode": "LIVE", "error": "HTTP 400: bad"}, {"ok": False, "mode": "LIVE", "error": "HTTP 400: bad"}]
    at("18:05"), S.tick()
    return one == (3, ["failed", "sent", "sent"]) and len(REC.calls) == 2 and q("SELECT state FROM send_run") == [("stopped",)]


# ============================================================ rule 3: the stop list, read again at the moment of sending
@check("14 a STOP that arrives while the list is going is honoured for the rows still to go (rule 3)")
def _():
    world()
    on("tomorrow")

    def hook(n, c):
        if n == 1:
            st = S.store()
            for k in ("A1", "A2", "A5"):
                if M(k) != c["phone"]:
                    st.execute("INSERT OR IGNORE INTO optout(mobile, at, source, said, rid) VALUES (?,?,?,?,NULL)", (M(k), "2026-11-17 18:05:01", "WhatsApp reply", "stop"))
            st.commit(), st.close()
    REC.hook = hook
    at("18:05"), S.tick()
    return len(REC.calls) == 1 and q("SELECT COUNT(*) FROM send_hold WHERE reason='replied STOP' AND list='tomorrow'") == [(3,)]


@check("15 the stop list cannot be read: nothing goes (rule 3)")
def _():
    world()
    on("tomorrow")
    os.makedirs(P("old_optout.csv"))                                     # a folder where the older file is: it cannot be read
    at("18:05"), S.tick()
    return not REC.calls and not q("SELECT 1 FROM send_row")


@check("45 the stop list becomes unreadable while a list is going: the rows still to go are not sent (rule 3)")
def _():
    world()
    on("tomorrow")
    REC.hook = lambda n, c: os.makedirs(P("old_optout.csv")) if n == 1 else None
    at("18:05"), S.tick()
    return len(REC.calls) == 1 and q("SELECT state FROM send_run") == [("stopped",)]


# ============================================================ rules 4 and 5: one a day, never twice for a date, across pages
@check("16 one number, one message a day: a family's second patient is held; the number is asked once (rule 4)")
def _():
    world()
    on("tomorrow", "post_visit")
    at("18:05"), S.tick()
    at("21:05"), S.tick()
    ph = REC.phones()
    return ph.count(M("A1")) == 1 and mob(51) in ph and len(ph) == 4 and q("SELECT COUNT(*) FROM send_row WHERE day=? AND mobile=?", (T, M("A1"))) == [(1,)]


@check("17 the database itself refuses a second message to a number on one day, and a second one for the same date (rules 4, 5)")
def _():
    world()
    st = S.store()
    ins = "INSERT INTO send_row(day, list, mobile, ref_date, template, state, at) VALUES (?,?,?,?,?,'sent','x')"
    st.execute(ins, (T, "tomorrow", M("A1"), "2026-11-18", "t"))
    bad = 0
    for args in ((T, "post_visit", M("A1"), T, "t"), ("2026-11-16", "tomorrow", M("A1"), "2026-11-18", "t")):
        try:
            st.execute(ins, args)
        except sqlite3.IntegrityError:
            bad += 1
    st.close()
    return bad == 2


@check("18 another page already messaged the number today: held, not sent (rule 4, the portal's send log)")
def _():
    world()
    on("due1")
    plog((T + "T08:10:00+05:30", M("B1"), "drmanoj_post_visit", {"1": "x"}, "LIVE", "1", ""))
    at("10:05"), S.tick()
    return REC.phones() == [M("B2")] and "send log" in q("SELECT reason FROM send_hold WHERE mobile=?", (M("B1"),))[0][0]


@check("19 another page already sent this reminder for this follow-up date, days ago: held (rule 5)")
def _():
    world()
    on("due5")
    plog(("2026-11-13T10:00:00+05:30", M("C1"), "drmanoj_followup_missed", {"1": "x", "2": "12-11-2026"}, "LIVE", "1", ""))
    at("10:05"), S.tick()
    return not REC.calls and "already went" in q("SELECT reason FROM send_hold WHERE mobile=?", (M("C1"),))[0][0]


@check("20 ...but the same message for ANOTHER date, a test-mode row and a refused row do not hold it; an undated one near in time does")
def _():
    world()
    on("due5")
    plog(("2026-11-06T10:00:00+05:30", M("C1"), "drmanoj_followup_missed", {"1": "x", "2": "05 Nov 2026"}, "LIVE", "1", ""),
         ("2026-11-13T10:00:00+05:30", M("C1"), "drmanoj_followup_missed", {"1": "x", "2": "12 Nov 2026"}, "DRY", "1", ""),
         ("2026-11-13T10:00:00+05:30", M("C1"), "drmanoj_followup_missed", {"1": "x", "2": "12 Nov 2026"}, "LIVE", "0", "HTTP 403: no"))
    at("10:05"), S.tick()
    sent = REC.phones() == [M("C1")]
    world()
    on("due5")
    plog(("2026-11-13T10:00:00+05:30", M("C1"), "drmanoj_followup_missed", {"1": "x", "2": "soon"}, "LIVE", "1", ""))
    at("10:05"), S.tick()
    return sent and not REC.calls


@check("21 this page's own earlier try for the same follow-up date holds it on a later day (rule 5)")
def _():
    world()
    on("tomorrow")
    st = S.store()
    st.execute("INSERT INTO send_row(day, list, mobile, ref_date, template, state, at) VALUES ('2026-11-16','tomorrow',?,'2026-11-18','t','unsure','x')", (M("A2"),))
    st.commit(), st.close()
    at("18:05"), S.tick()
    return sorted(REC.phones()) == sorted([M("A1"), M("A5")])


@check("22 the portal's send log is missing, or not as expected: nothing goes (F-1291)")
def _():
    world()
    on("tomorrow")
    os.remove(P("wa_portal_sends.csv"))
    at("18:05"), S.tick()
    a = len(REC.calls)
    world()
    on("tomorrow")
    with open(P("wa_portal_sends.csv"), "w") as fh:
        fh.write("when,who,number\n")
    at("18:05"), S.tick()
    return a == 0 and not REC.calls and not q("SELECT 1 FROM send_row")


# ============================================================ rule 8: the window; rule 9: the ceiling
@check("23 the server was down at the time: inside 90 minutes it still goes; after that the day is skipped and said (rule 8)")
def _():
    world()
    on("tomorrow")
    at("19:29"), S.tick()
    late = len(REC.calls)
    world()
    on("tomorrow")
    at("19:31")
    lines = S.tick()
    at("19:36"), S.tick()
    r = q("SELECT state, note FROM send_run")
    return late == 3 and not REC.calls and len(r) == 1 and r[0][0] == "skipped" and "did not go between 6:00 pm and 7:30 pm" in r[0][1] and len(lines) == 1


@check("24 switched ON after today's time has passed: nothing today, no false 'skipped'; it goes tomorrow at its time")
def _():
    world()
    at("20:00")
    on("tomorrow")
    S.tick()
    a = (len(REC.calls), q("SELECT 1 FROM send_run"))
    con = sqlite3.connect(P("finance.db"))
    con.execute("INSERT INTO patient_visit VALUES ('u4490','4490','2026-11-17')")
    con.execute("INSERT INTO dx_visit VALUES ('u4490','2026-11-17','4490','2026-11-19')")
    con.commit(), con.close()
    cc = sqlite3.connect(P("console.db"))
    cc.execute("INSERT INTO patients VALUES (?,?,?)", (mob(90), "u4490", "4490")), cc.commit(), cc.close()
    at("18:05", "2026-11-18"), S.tick()
    return a == (0, []) and REC.phones() == [mob(90)] and REC.calls[0]["values"]["2"] == "19 Nov 2026"


@check("25 at most 150 a day across all lists: the rest are held and said (rule 9)")
def _():
    world()
    on("tomorrow")
    st = S.store()
    for i in range(S.CEILING - 1):
        st.execute("INSERT INTO send_row(day, list, mobile, ref_date, template, state, at) VALUES (?,?,?,?,'t','sent','x')", (T, "post_visit", mob(5000 + i), T))
    st.commit(), st.close()
    at("18:05"), S.tick()
    r = q("SELECT note, sent, held FROM send_run WHERE list='tomorrow'")
    return S.CEILING == 150 and len(REC.calls) == 1 and r[0][1] == 1 and r[0][2] == 3 and "ceiling" in r[0][0] and q("SELECT COUNT(*) FROM send_hold WHERE reason LIKE '%ceiling%'") == [(2,)]


# ============================================================ added: the visit records must be up to date
@check("26 yesterday's visits are not in yet: the 'date passed' reminders WAIT; they go when the visits arrive; else the day is skipped and says why")
def _():
    world(visits_to="2026-11-14", today_visits=False)
    on("due1")
    at("10:05"), S.tick()
    waited = (len(REC.calls), q("SELECT 1 FROM send_run"))
    con = sqlite3.connect(P("finance.db"))
    con.execute("INSERT INTO patient_visit VALUES ('u4411','4411','2026-11-16')")       # B1 DID come yesterday
    con.commit(), con.close()
    at("10:20"), S.tick()
    went = REC.phones() == [M("B2")]
    world(visits_to="2026-11-14", today_visits=False)
    on("due1")
    at("10:05"), S.tick()
    at("11:35"), S.tick()
    r = q("SELECT state, note FROM send_run")
    return waited == (0, []) and went and not REC.calls and r[0][0] == "skipped" and "visits" in r[0][1]


@check("27 after a Sunday the records need only reach Saturday; 'after today's visit' waits for today's visits")
def _():
    world()
    mon = dt.datetime(2026, 11, 16, 10, 5, tzinfo=IST)
    a = S.stale_reason("due1", {}, mon, lv="2026-11-14")
    b = S.stale_reason("due1", {}, mon, lv="2026-11-13")
    c = S.stale_reason("post_visit", {}, mon, lv="2026-11-15")
    d = S.stale_reason("post_visit", {}, mon, lv="2026-11-16")
    e = S.stale_reason("appt", {}, mon, lv="")
    world(today_visits=False)
    on("post_visit")
    at("21:05"), S.tick()
    return a == "" and b != "" and c != "" and d == "" and e == "" and not REC.calls and not q("SELECT 1 FROM send_run")


# ============================================================ rules 1 and 13 again: while it is going
@check("28 switched OFF, or ALL_OFF made, while a list is going: the rows still to go are not sent (rules 1, 13)")
def _():
    world()
    on("tomorrow")
    REC.hook = lambda n, c: S.set_switch("tomorrow", False, "manoj", CLOCK[0]) if n == 1 else None
    at("18:05"), S.tick()
    a = len(REC.calls)
    world()
    on("tomorrow")
    REC.hook = lambda n, c: open(P("ALL_OFF"), "w").close() if n == 1 else None
    at("18:05"), S.tick()
    return a == 1 and len(REC.calls) == 1


@check("29 'Stop all sending' turns every switch OFF at once and is on record")
def _():
    world()
    on("tomorrow", "due1", "appt")
    ok, _t = S.door("stopall", {}, OWNER)
    at("18:05"), S.tick()
    return ok and not q("SELECT 1 FROM send_switch WHERE is_on<>0") and not REC.calls and q("SELECT COUNT(*) FROM send_log WHERE what='stop all'") == [(1,)]


# ============================================================ long overdue: only the ticked names, only on his press
@check("30 long overdue never goes by itself -- not even with a switch row forced into the store")
def _():
    world()
    st = S.store()
    st.execute("INSERT OR REPLACE INTO send_switch(list, is_on, at, by) VALUES ('overdue',1,'2026-11-16 09:00:00','x')"), st.commit(), st.close()
    for hh in ("10:05", "18:05", "21:05"):
        at(hh), S.tick()
    return not REC.calls and S.set_switch("overdue", True, "manoj", CLOCK[0])[0] is False and "overdue" not in S.AUTO


@check("31 the ticked names: exactly those go, with the SERVER's name and number; a made-up or foreign token sends nothing")
def _():
    world()
    at("11:00")
    p = L.plan(T)
    rows = {r["cid"]: S.token(T, "overdue", r) for x in p["lists"] if x["key"] == "overdue" for r in x["rows"]}
    other = [S.token(T, "tomorrow", r) for x in p["lists"] if x["key"] == "tomorrow" for r in x["rows"]]
    ok, text = S.door("ticked", {"day": T, "tokens": [rows["4431"], rows["4433"]] + other + ["0" * 20], "mobile": mob(77), "name": "Evil"}, OWNER)
    c = REC.calls
    return (ok and sorted(REC.phones()) == sorted([M("O1"), M("O3")]) and all(x["template"] == "drmanoj_followup_dropout" and x["values"]["3"] == "14"
                                                                               and x["values"]["2"] == "3 Nov 2026" for x in c)
            and sorted(x["values"]["1"] for x in c) == ["Indu Made-up", "Kiran Made-up"] and "2 sent" in text)


@check("32 the ticked names are refused: on another day's list, at night, with nothing ticked, before the test, by another login")
def _():
    world()
    at("11:00")
    p = L.plan(T)
    toks = [S.token(T, "overdue", r) for x in p["lists"] if x["key"] == "overdue" for r in x["rows"]]
    a = S.door("ticked", {"day": "2026-11-16", "tokens": toks}, OWNER)
    b = S.door("ticked", {"day": T, "tokens": []}, OWNER)
    b2 = S.door("ticked", {"day": T, "tokens": "abc"}, OWNER)
    c = S.door("ticked", {"day": T, "tokens": toks}, {"user": "asha", "role": "doctor"})
    c2 = S.door("ticked", {"day": T, "tokens": toks}, {"user": "manoj", "role": "staff"})
    at("22:10")
    d = S.door("ticked", {"day": T, "tokens": toks}, OWNER)
    at("07:30")
    d2 = S.door("ticked", {"day": T, "tokens": toks}, OWNER)
    world(test_all=False)
    at("11:00")
    e = S.door("ticked", {"day": T, "tokens": toks}, OWNER)
    return not any(x[0] for x in (a, b, b2, c, c2, d, d2, e)) and not REC.calls and not q("SELECT 1 FROM send_row")


@check("33 a press on the page starts no new message after its time budget; what is left is said")
def _():
    world()
    at("11:00")
    p = L.plan(T)
    toks = set(S.token(T, "overdue", r) for x in p["lists"] if x["key"] == "overdue" for r in x["rows"])
    res = S.send_list("overdue", "manoj", only=toks, budget_s=-1)
    return not REC.calls and res["left"] == 3 and res["sent"] == 0


# ============================================================ the doors
@check("34 only the doctor's own login can change anything; an unknown door does nothing")
def _():
    world(test_all=False)
    n = 0
    for who in ({"user": "asha", "role": "doctor"}, {"user": "manoj", "role": "reception"}, {}, None):
        for what, d in (("switch", {"list": "tomorrow", "on": True}), ("test", {"list": "tomorrow"}), ("testok", {"list": "tomorrow"}), ("stopall", {})):
            n += 1 if S.door(what, d, who)[0] else 0
    x = S.door("nonsense", {}, OWNER)
    y = S.door("switch", {"list": "tomorrow", "on": "yes"}, OWNER)       # 'on' must be exactly true
    return n == 0 and not x[0] and y[0] and not REC.calls and not q("SELECT 1 FROM send_switch WHERE is_on<>0") and not q("SELECT 1 FROM send_test")


@check("35 what the page is told: the switches, tokens, what happened to each row -- and never the WhatsApp key")
def _():
    world()
    on("tomorrow")
    at("18:05"), S.tick()
    at("18:20")
    p = S.decorate(L.plan(T), OWNER)
    s = p["send"]
    rows = [r for x in p["lists"] if x["key"] == "tomorrow" for r in x["rows"]]
    sent = [r for r in rows if r.get("sent")]
    blob = json.dumps(p)
    return (s["ok"] and s["mode"] == "LIVE" and s["owner"] and s["lists"]["tomorrow"]["on"] and s["lists"]["tomorrow"]["run"]["state"] == "done"
            and s["sent_today"] == 3 and len(s["record"]) == 3 and len(sent) == 3 and all(r["sent"] == {"k": "ok", "t": "Sent 6:05 pm"} for r in sent)
            and all(re.match(r"^[0-9a-f]{20}$", r["token"]) for r in rows) and KEYWORD not in blob and s["test_last4"] == mob(99)[-4:] and mob(99) not in blob
            and not S.decorate(L.plan(T), {"user": "asha", "role": "doctor"})["send"]["owner"])


@check("36 the page's doors in the portal: closed without a login, to another role, without the page's own header; open to the doctor")
def _():
    from flask import Flask, request
    world(test_all=False)
    app = Flask("walk808")
    who = {"v": None}

    def login_required(view):
        from functools import wraps

        @wraps(view)
        def w(*a, **k):
            return view(*a, **k) if who["v"] is not None else ("", 302, {"Location": "/portal/login"})
        return w
    L.install(app, login_required, lambda req: who["v"])
    c = app.test_client()
    H = {"X-Messages": "1"}
    codes = [c.post("/portal/messages/api/send/switch", json={"list": "tomorrow", "on": True}, headers=H).status_code]
    who["v"] = {"user": "asha", "role": "reception"}
    codes.append(c.post("/portal/messages/api/send/test", json={"list": "tomorrow"}, headers=H).status_code)
    who["v"] = dict(OWNER)
    codes.append(c.post("/portal/messages/api/send/test", json={"list": "tomorrow"}).status_code)
    none_sent = not REC.calls
    r = c.post("/portal/messages/api/send/test", json={"list": "tomorrow"}, headers=H)
    codes.append(r.status_code)
    r2 = c.post("/portal/messages/api/send/switch", json={"list": "tomorrow", "on": True}, headers=H)   # test not confirmed
    codes.append(r2.status_code)
    pl = c.get("/portal/messages/api/plan").get_json()
    page = c.get("/portal/messages")
    who["v"] = {"user": "asha", "role": "doctor"}                        # another doctor: reads, cannot change
    r3 = c.post("/portal/messages/api/send/stopall", json={}, headers=H)
    codes.append(r3.status_code)
    return (codes == [302, 403, 400, 200, 409, 409] and none_sent and len(REC.calls) == 1 and pl["send"]["ok"] and pl["sends"] is True
            and page.status_code == 200 and b"Stop all sending" in page.data and b"SHOW ONLY" in page.data and KEYWORD.encode() not in page.data)


@check("37 without the sending file the page stands, show only: the lists answer, every send door answers 503")
def _():
    from flask import Flask
    world()
    app = Flask("walk808b")
    L.install(app, lambda v: v, lambda req: dict(OWNER))
    c = app.test_client()
    keep = sys.modules.get("wa_ladder_send")
    sys.modules["wa_ladder_send"] = None                                 # as if the file were not there
    try:
        pl = c.get("/portal/messages/api/plan").get_json()
        r = c.post("/portal/messages/api/send/switch", json={"list": "tomorrow", "on": True}, headers={"X-Messages": "1"})
    finally:
        sys.modules["wa_ladder_send"] = keep
    return pl["ok"] and pl["send"]["ok"] is False and pl["sends"] is False and r.status_code == 503 and len(pl["lists"]) == 6


# ============================================================ the files themselves
@check("38 wa_ladder.py still holds no send code; wa_ladder_send.py has no sender of its own -- two calls of the one sender (rule 7)")
def _():
    a = open(os.path.join(KIT, "portal", "wa_ladder.py"), encoding="utf-8").read()
    b = open(os.path.join(KIT, "portal", "wa_ladder_send.py"), encoding="utf-8").read()
    net = ("http.client", "urllib", "socket", "requests", "smtplib", "subprocess", "os.system")
    return (not any(w in a for w in net + ("portal_wa", "_sender"))) and not any(w in b for w in net) and b.count("_sender()(") == 2 and b.count("return portal_wa.send") == 1 and b.count("conn.request") == 0


@check("39 no phone number is written in the kit's files (F-185)")
def _():
    bad = 0
    for root, _d, files in os.walk(KIT):
        for f in files:
            if f.endswith((".py", ".html", ".sh", ".md", ".txt")):
                s = open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
                bad += len(re.findall(r"(?<![\d.])[6-9]\d{9}(?!\d)", s))
    return bad == 0


@check("40 the portal's own sender takes exactly what this file hands it (read from the live portal_wa.py)")
def _():
    ok, text = S.contract()
    return ok


@check("41 a patient with no name on record is held, not greeted as '?'")
def _():
    world()
    con = sqlite3.connect(P("finance.db"))
    con.execute("UPDATE patient_ref SET name='' WHERE clinic_id='4402'"), con.commit(), con.close()
    on("tomorrow")
    at("18:05"), S.tick()
    return M("A2") not in REC.phones() and len(REC.calls) == 2 and "no name" in q("SELECT reason FROM send_hold WHERE mobile=?", (M("A2"),))[0][0]


@check("42 every hold, every try and every change of a switch is on record (rule 12); the status line carries no number")
def _():
    world(test_all=False)
    S.door("test", {"list": "tomorrow"}, OWNER), S.door("testok", {"list": "tomorrow"}, OWNER), S.door("switch", {"list": "tomorrow", "on": True}, OWNER)
    at("18:05"), S.tick()
    S.door("switch", {"list": "tomorrow", "on": False}, OWNER)
    whats = [x[0] for x in q("SELECT what FROM send_log ORDER BY id")]
    line = S.status()
    return (whats == ["test", "test arrived", "switch on", "switch off"] and q("SELECT COUNT(*) FROM send_hold") == [(1,)] and q("SELECT COUNT(*) FROM send_row") == [(3,)]
            and line.startswith("ok mode LIVE") and not re.search(r"\d{6,}", line) and KEYWORD not in line)


@check("43 the appointment reminder: the booked name and the time as the patient reads it; all five timed messages at their own times")
def _():
    world()
    on("tomorrow", "post_visit", "appt", "due1", "due5")
    got = {}
    for hh in ("09:55", "10:05", "17:55", "18:05", "20:55", "21:05"):
        n = len(REC.calls)
        at(hh), S.tick()
        got[hh] = sorted(set(c["template"] for c in REC.calls[n:]))
    ap = [c for c in REC.calls if c["template"] == "appointment_reminder_1day_ortho"]
    return (got == {"09:55": [], "10:05": ["drmanoj_followup_due", "drmanoj_followup_missed"], "17:55": [], "18:05": ["appointment_reminder_1day_ortho", "drmanoj_followup_tomorrow"],
                    "20:55": [], "21:05": ["drmanoj_post_visit"]}
            and len(ap) == 1 and ap[0]["phone"] == mob(61) and ap[0]["values"] == {"var_1": "Neha Made-up", "var_2": "18 Nov 2026, 6:45 PM"}
            and len(REC.phones()) == len(set(REC.phones())))


@check("44 the settings file cannot be read: nothing is sent, mode() says so and no login is the owner; a missing key likewise")
def _():
    world()
    on("tomorrow")
    with open(P("portal_config.py"), "w") as fh:
        fh.write("this is not python (\n")
    at("18:05"), S.tick()
    a = (len(REC.calls), S.mode()[0], S.owner_ok(OWNER))
    world()
    on("tomorrow")
    with open(P("portal_config.py"), "w") as fh:
        fh.write("PORTAL_WA_DRYRUN = '0'\n")
    at("18:05"), S.tick()
    return a == (0, "ERR", False) and not REC.calls and S.mode()[0] == "ERR"


# ============================================================ added after the cold review (S442)
@check("46 the STOP listener is deaf (the Inbox store cannot be read): nothing goes; the list waits, then the day is skipped and says why (rule 3)")
def _():
    world()
    on("tomorrow")
    os.remove(P("inbox.db"))
    at("18:05"), S.tick()
    a = (len(REC.calls), q("SELECT 1 FROM send_run"))
    at("19:35"), S.tick()
    r = q("SELECT state, note FROM send_run")
    return a == (0, []) and not REC.calls and r[0][0] == "skipped" and "STOP listener" in r[0][1]


@check("47 a STOP that has reached the Inbox but was not yet read by the listener is honoured: the replies are read first (rule 3)")
def _():
    world()
    on("tomorrow")
    ib = sqlite3.connect(P("inbox.db"))
    ib.execute("INSERT INTO msgs(dir, phone, ts, body) VALUES ('in', ?, '2026-11-17 17:58:00', 'STOP')", ("91" + M("A1"),))
    ib.commit(), ib.close()
    at("18:00"), S.tick()
    return sorted(REC.phones()) == sorted([M("A2"), M("A5")]) and q("SELECT COUNT(*) FROM optout WHERE mobile=?", (M("A1"),)) == [(1,)]


@check("48 the listener's last pass is old and it cannot run now: nothing goes (the page's red banner is a gate, not a notice)")
def _():
    world()
    on("tomorrow")
    keep = L.stop_scan
    L.stop_scan = lambda *a, **k: (0, 0)                                  # as if the pass did nothing: the stored stamp stays 08:59
    try:
        at("18:05"), S.tick()
    finally:
        L.stop_scan = keep
    return not REC.calls and not q("SELECT 1 FROM send_row")


@check("49 words that come back from outside are never kept or shown: not the key, not a number -- in a test, in a list, on the page")
def _():
    world(test_all=False)
    evil = "HTTP 401: {\"token\":\"" + KEYWORD + "\",\"to\":\"" + mob(1) + "\"}"
    REC.script = [{"ok": False, "mode": "LIVE", "error": evil}]
    ok, text = S.door("test", {"list": "tomorrow"}, OWNER)
    world()
    on("tomorrow")
    REC.script = [{"ok": False, "mode": "LIVE", "error": "unexpected response: " + KEYWORD + " " + mob(2)}]
    at("18:05")
    lines = S.tick()
    blob = json.dumps(S.decorate(L.plan(T), OWNER)) + " ".join(lines) + text + S.status()
    con = sqlite3.connect(P("wa_ladder.db"))
    dump = "\n".join(con.iterdump())
    con.close()
    world(test_all=False)
    REC.script = [{"ok": False, "mode": "LIVE", "error": evil}]
    S.door("test", {"list": "tomorrow"}, OWNER)
    con = sqlite3.connect(P("wa_ladder.db"))
    dump += "\n".join(con.iterdump())
    con.close()
    return not ok and "HTTP 401" in text and KEYWORD not in blob and KEYWORD not in dump and "token" not in dump and KEYWORD not in text


@check("50 a switch forced ON in the store without a confirmed test: the timed run sends nothing (rule 10, read again at sending)")
def _():
    world(test_all=False)
    st = S.store()
    st.execute("INSERT OR REPLACE INTO send_switch(list, is_on, at, by) VALUES ('tomorrow',1,'2026-11-16 09:00:00','x')"), st.commit(), st.close()
    at("18:05"), S.tick()
    return not REC.calls and q("SELECT state FROM send_run") == [("stopped",)]


@check("51 the portal put into TEST, or its settings broken, while a list is going: the rows still to go do not leave (rule 11, every row)")
def _():
    world()
    on("tomorrow")
    REC.hook = lambda n, c: open(P("portal_config.py"), "w").write("MYOP_AUTH_TOKEN = 'x'\nPORTAL_WA_DRYRUN = '1'\n") if n == 1 else None
    at("18:05"), S.tick()
    a = len(REC.calls)
    world()
    on("tomorrow")
    REC.hook = lambda n, c: open(P("portal_config.py"), "w").write("broken (\n") if n == 1 else None
    at("18:05"), S.tick()
    return a == 1 and len(REC.calls) == 1


@check("52 a list's time runs out while it is going: no message STARTS after it; each list is judged by its own clock (rule 8)")
def _():
    world()
    on("tomorrow")
    REC.hook = lambda n, c: at("19:30") if n == 1 else None
    at("19:25"), S.tick()
    r = q("SELECT state, note, sent FROM send_run")
    return len(REC.calls) == 1 and r[0][0] == "stopped" and "time was over" in r[0][1] and r[0][2] == 1


@check("53 HTTP 429 and a gateway error stop the list at the first row; a gateway error is 'may have gone', never 'refused'")
def _():
    out = []
    for err in ("HTTP 429: slow down", "HTTP 502: bad gateway", "HTTP 504: timeout"):
        world()
        on("tomorrow")
        REC.script = [{"ok": False, "mode": "LIVE", "error": err}]
        at("18:05"), S.tick()
        out.append((len(REC.calls), q("SELECT state FROM send_row")[0][0]))
    return out == [(1, "failed"), (1, "unsure"), (1, "unsure")]


@check("54 the test: on record before it leaves; a second press within half a minute sends nothing; a later failed test does not undo 'It arrived'")
def _():
    world(test_all=False)
    seen = []
    REC.hook = lambda n, c: seen.append(q("SELECT error FROM send_test WHERE list='tomorrow'"))
    a = S.send_test("tomorrow", "manoj", CLOCK[0])
    b = S.send_test("tomorrow", "manoj", CLOCK[0] + dt.timedelta(seconds=20))
    c = S.confirm_test("tomorrow", "manoj", CLOCK[0])
    REC.script = [{"ok": False, "mode": "LIVE", "error": "HTTP 500: x"}]
    d = S.send_test("tomorrow", "manoj", CLOCK[0] + dt.timedelta(seconds=40))
    e = S.set_switch("tomorrow", True, "manoj", CLOCK[0])
    t = S.decorate(L.plan(T), OWNER)["send"]["lists"]["tomorrow"]["test"]
    return a[0] and not b[0] and len(REC.calls) == 2 and seen[0] == [("sending",)] and c[0] and not d[0] and e[0] and t["confirmed"] is True and t["ok"] is False


@check("55 the ticked names: at most 60 at a time; 8:00 am to 8:59 pm only; nothing starts at 9 pm")
def _():
    world()
    p = L.plan(T)
    toks = [S.token(T, "overdue", r) for x in p["lists"] if x["key"] == "overdue" for r in x["rows"]]
    at("11:00")
    a = S.door("ticked", {"day": T, "tokens": toks + ["%020x" % i for i in range(58)]}, OWNER)       # 61
    at("07:59")
    b = S.door("ticked", {"day": T, "tokens": toks[:1]}, OWNER)
    at("21:00")
    c = S.door("ticked", {"day": T, "tokens": toks[:1]}, OWNER)
    none = len(REC.calls)
    at("20:59")
    REC.hook = lambda n, c_: at("21:00") if n == 1 else None
    d = S.door("ticked", {"day": T, "tokens": toks}, OWNER)
    return not a[0] and "60" in a[1] and not b[0] and not c[0] and none == 0 and d[0] and len(REC.calls) == 1 and S.MAX_TICKED == 60


@check("56 the clock's edges: at exactly its time a list goes; at exactly 90 minutes after, it does not")
def _():
    world()
    on("tomorrow")
    at("18:00"), S.tick()
    a = len(REC.calls)
    world()
    on("tomorrow")
    at("19:30"), S.tick()
    return a == 3 and not REC.calls and q("SELECT state FROM send_run") == [("skipped",)]


@check("57 the portal's send log: a number written with +91, a row that may have gone, a gateway error -- each holds; and the log is read again for every row")
def _():
    world()
    on("tomorrow")
    plog((T + "T08:10:00+05:30", "+91 " + M("A1"), "x", {"1": "x"}, "LIVE", "1", ""))
    REC.hook = lambda n, c: plog((T + "T18:05:01+05:30", M("A5"), "x", {"1": "x"}, "LIVE", "0", "HTTP 504: gateway")) if n == 1 else None
    at("18:05"), S.tick()
    a = (REC.phones() == [M("A2")], q("SELECT COUNT(*) FROM send_hold WHERE reason LIKE '%send log%'"))
    world()
    on("tomorrow")
    plog((T + "T08:11:00+05:30", M("A2"), "x", {"1": "x"}, "LIVE", "0", "send failed: timed out"),
         (T + "T08:12:00+05:30", M("A5"), "x", {"1": "x"}, "LIVE", "0", "HTTP 400: refused"))      # plainly turned down: does not hold
    at("18:05"), S.tick()
    return a == (True, [(2,)]) and sorted(REC.phones()) == sorted([M("A1"), M("A5")])


@check("58 the ceiling counts every try, not only what was sent; two timed runs cannot go at once")
def _():
    import fcntl
    world()
    on("tomorrow")
    st = S.store()
    for i in range(S.CEILING):
        st.execute("INSERT INTO send_row(day, list, mobile, ref_date, template, state, at) VALUES (?,?,?,?,'t',?,'x')", (T, "post_visit", mob(5000 + i), T, "failed" if i % 2 else "unsure"))
    st.commit(), st.close()
    at("18:05"), S.tick()
    a = len(REC.calls)
    world()
    on("tomorrow")
    fh = open(P("run.lock"), "a")
    fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    at("18:05")
    lines = S.tick()
    b = (len(REC.calls), lines)
    fh.close()
    S.tick()
    return a == 0 and b == (0, []) and len(REC.calls) == 3


@check("59 a visit dated in the future does not make the records look up to date")
def _():
    world(visits_to="2026-11-14", today_visits=False)
    con = sqlite3.connect(P("finance.db"))
    con.execute("INSERT INTO patient_visit VALUES ('u4490','4490','2026-12-25')"), con.commit(), con.close()
    on("due1")
    at("10:05"), S.tick()
    return not REC.calls and S.last_visit_upto(T) == "2026-11-15"


@check("60 the store cannot be opened: 'Stop all' answers that it could NOT stop, a switch is not changed, nothing breaks")
def _():
    world()
    on("tomorrow")
    keep = L.STORE
    L.STORE = P("no_such_folder", "x.db")
    try:
        a = S.stop_all("manoj", CLOCK[0])
        b = S.set_switch("due1", True, "manoj", CLOCK[0])
        c = S.confirm_test("tomorrow", "manoj", CLOCK[0])
    finally:
        L.STORE = keep
    return not a[0] and "COULD NOT STOP" in a[1] and not b[0] and not c[0] and q("SELECT is_on FROM send_switch WHERE list='tomorrow'") == [(1,)]


@check("61 the login is the server's own: a name or a role written into the request changes nothing")
def _():
    from flask import Flask
    world()
    app = Flask("walk808c")
    L.install(app, lambda v: v, lambda req: {"user": "asha", "role": "doctor"})
    c = app.test_client()
    r = c.post("/portal/messages/api/send/switch", json={"list": "tomorrow", "on": True, "user": "manoj", "role": "doctor"}, headers={"X-Messages": "1"})
    return r.status_code == 409 and not q("SELECT 1 FROM send_switch WHERE is_on<>0")


@check("62 switched ON within the last minutes of today's time: told 'starting tomorrow', and nothing goes today")
def _():
    world()
    at("19:25")
    ok, text = S.set_switch("tomorrow", True, "manoj", CLOCK[0])
    at("19:29"), S.tick()
    at("19:35"), S.tick()
    a = (len(REC.calls), q("SELECT 1 FROM send_run"))
    world()
    at("19:20")
    ok2, text2 = S.set_switch("tomorrow", True, "manoj", CLOCK[0])
    at("19:22"), S.tick()
    return (ok and "starting tomorrow" in text and a == (0, []) and ok2 and "next few minutes" in text2 and len(REC.calls) == 3
            and q("SELECT state FROM send_run") == [("done",)])


@check("63 the Inbox's own reader fails: the listener's note is a gate -- nothing goes, and the day's skip says why (rule 3)")
def _():
    import types
    world()
    on("tomorrow")
    fake = types.ModuleType("portal_inbox")

    def bad(force=False):
        raise RuntimeError("reader down")
    fake.ingest = bad
    fake.RAW_DIR = ROOT
    sys.modules["portal_inbox"] = fake
    os.environ["WA_LADDER_INGEST"] = "1"
    try:
        at("18:05"), S.tick()
        a = (len(REC.calls), q("SELECT 1 FROM send_run"))
        at("19:35"), S.tick()
        r = q("SELECT state, note FROM send_run")
        fake.ingest = lambda force=False: None                           # the reader works again the next day
        at("18:05", "2026-11-18")
        con = sqlite3.connect(P("finance.db"))
        con.execute("INSERT INTO patient_visit VALUES ('u4490','4490','2026-11-17')")
        con.execute("INSERT INTO dx_visit VALUES ('u4490','2026-11-17','4490','2026-11-19')")
        con.commit(), con.close()
        cc = sqlite3.connect(P("console.db"))
        cc.execute("INSERT INTO patients VALUES (?,?,?)", (mob(90), "u4490", "4490")), cc.commit(), cc.close()
        S.tick()
    finally:
        os.environ["WA_LADDER_INGEST"] = "0"
        sys.modules.pop("portal_inbox", None)
    return a == (0, []) and r[0][0] == "skipped" and "reader did not run" in r[0][1] and REC.phones() == [mob(90)]


@check("64 a second ON press on a switch already ON changes nothing: a list waiting for the records is not dropped")
def _():
    world(visits_to="2026-11-14", today_visits=False)
    on("due1")
    at("10:05"), S.tick()
    at("11:26")
    ok, text = S.set_switch("due1", True, "manoj", CLOCK[0])              # a stale tab, late in the window
    con = sqlite3.connect(P("finance.db"))
    con.execute("INSERT INTO patient_visit VALUES ('u4490','4490','2026-11-16')"), con.commit(), con.close()
    at("11:28"), S.tick()
    return ok and "already ON" in text and sorted(REC.phones()) == sorted([M("B1"), M("B2")]) and q("SELECT at FROM send_switch WHERE list='due1'") == [("2026-11-17 09:00:00",)]


@check("65 when the switches cannot be read the page is told so (not 'show only'), and nothing a request adds is believed")
def _():
    from flask import Flask
    world(test_all=False)
    app = Flask("walk808d")
    L.install(app, lambda v: v, lambda req: dict(OWNER))
    c = app.test_client()
    keep = S.decorate
    S.decorate = lambda *a, **k: (_ for _ in ()).throw(sqlite3.OperationalError("locked"))
    try:
        pl = c.get("/portal/messages/api/plan").get_json()
    finally:
        S.decorate = keep
    r = c.post("/portal/messages/api/send/test", headers={"X-Messages": "1"},
               json={"list": "tomorrow", "mobile": M("A1"), "phone": M("A1"), "by": "x", "dry_run": True, "token": "t", "now": "2020-01-01", "values": {"1": "Evil"}, "template": "x"})
    page = c.get("/portal/messages").data
    return (pl["send"].get("broken") is True and "may still be ON" in pl["send"]["msg"] and pl["sends"] is False and len(pl["lists"]) == 6 and b"d.send.broken" in page
            and r.status_code == 200 and len(REC.calls) == 1 and REC.calls[0]["phone"] == mob(99) and REC.calls[0]["values"]["1"] == "Test Patient"
            and REC.calls[0]["dry"] is False and REC.calls[0]["template"] == "drmanoj_followup_tomorrow" and q("SELECT by FROM send_log") == [("manoj",)])


@check("66 'after today's visit' is not held because the same message went on an earlier visit; a message id is kept only as plain characters")
def _():
    world()
    on("post_visit")
    plog(("2026-11-14T21:00:00+05:30", mob(51), "drmanoj_post_visit", {"1": "Lata"}, "LIVE", "1", ""))
    REC.script = [{"ok": True, "mode": "LIVE", "message_id": "wamid.<b>x</b>'; DROP--" + "9" * 3, "error": ""}]
    at("21:05"), S.tick()
    ids = [x[0] for x in q("SELECT message_id FROM send_row ORDER BY id")]
    return REC.phones() == [mob(51)] and ids == ["wamid.bxbDROP--999"]


@check("67 the Inbox reader's silent failure (its log folder cannot be listed) holds the list too")
def _():
    import types
    world()
    on("tomorrow")
    fake = types.ModuleType("portal_inbox")
    fake.ingest = lambda force=False: None                               # returns without a word, as the live one does
    fake.RAW_DIR = P("no_such_folder")
    sys.modules["portal_inbox"] = fake
    os.environ["WA_LADDER_INGEST"] = "1"
    try:
        at("18:05"), S.tick()
        a = (len(REC.calls), q("SELECT 1 FROM send_run"))
        fake.RAW_DIR = ROOT
        at("18:10"), S.tick()
    finally:
        os.environ["WA_LADDER_INGEST"] = "0"
        sys.modules.pop("portal_inbox", None)
    return a == (0, []) and len(REC.calls) == 3


@check("68 another run writes a number's row first, between this run's look and its own write: held and on record, not sent twice")
def _():
    world()
    on("tomorrow")
    keep = S.values_for

    def racing(key, row, day):                                           # the other run gets in just before the written-ahead row
        con = sqlite3.connect(P("wa_ladder.db"))
        con.execute("INSERT OR IGNORE INTO send_row(day, list, mobile, ref_date, template, state, at) VALUES (?,?,?,?,'t','trying','x')", (day, "post_visit", row["mobile"], day))
        con.commit(), con.close()
        return keep(key, row, day)
    S.values_for = racing
    try:
        at("18:05"), S.tick()
    finally:
        S.values_for = keep
    return not REC.calls and q("SELECT COUNT(*) FROM send_hold WHERE reason LIKE 'another run%'") == [(3,)] and q("SELECT sent, held FROM send_run") == [(0, 4)]


def main():
    red = []
    for name, fn in CHECKS:
        if not HAVE:
            red.append(name)
            continue
        try:
            good = bool(fn())
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
