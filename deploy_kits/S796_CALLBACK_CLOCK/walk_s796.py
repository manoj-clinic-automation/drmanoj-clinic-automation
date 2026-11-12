#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s796.py <kit dir> [--control] -- the walk of kit S796_CALLBACK_CLOCK on a made-up console.db (made-up numbers, no patient).
It imports <kit dir>/portal/callback_clock.py and drives run() with a stand-in pusher and fixed clocks.
Last line: 'WALK OK n/n' or 'WALK RED k of n'; with --control (a kit dir without the file): 'CONTROL: red ...' is the pass."""
import datetime as dt
import importlib.util
import os
import sqlite3
import sys
import tempfile

kit = sys.argv[1]
control = "--control" in sys.argv[2:]
src = os.path.join(kit, "portal", "callback_clock.py")
try:
    spec = importlib.util.spec_from_file_location("callback_clock", src)
    cc = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(cc)
except Exception as e:                                   # noqa: BLE001
    print(("CONTROL: red (%s) -- the walk cannot pass without the file" if control else "WALK RED: cannot load the file (%s)") % type(e).__name__)
    sys.exit(0 if control else 1)
if control:
    print("CONTROL: NOT red -- the file was found where none should be")
    sys.exit(1)

tmp = tempfile.mkdtemp(prefix="s796walk")
res = []


def chk(name, ok, got=""):
    res.append(ok)
    print(("ok  " if ok else "BAD ") + name + ("" if ok else "  -> %r" % (got,)))


def make(path, built, calls, pats=()):
    if os.path.exists(path):
        os.remove(path)
    c = sqlite3.connect(path)
    c.executescript("CREATE TABLE calls(id INTEGER PRIMARY KEY, direction TEXT, answered INTEGER, phone10 TEXT, join_key TEXT, "
                    "client_ref_id TEXT, ended_at_ist TEXT); CREATE TABLE patients(phone10 TEXT, name TEXT, clinic_id TEXT); "
                    "CREATE TABLE meta(k TEXT, v TEXT);")
    c.execute("INSERT INTO meta VALUES('built_at', ?)", (built,))
    for ph, d, a, t in calls:
        c.execute("INSERT INTO calls(direction, answered, phone10, join_key, client_ref_id, ended_at_ist) VALUES(?,?,?,?,?,?)",
                  (d, a, ph, "", "", t))
    for ph, n, cid in pats:
        c.execute("INSERT INTO patients VALUES(?,?,?)", (ph, n, cid))
    c.commit()
    c.close()


def rev(path, spam):
    c = sqlite3.connect(path)
    c.execute("CREATE TABLE IF NOT EXISTS dispositions(join_key TEXT, final_outcome TEXT)")
    for ph in spam:
        c.execute("INSERT INTO dispositions VALUES(?,?)", (ph + "_1700000000", "Spam / marketing"))
    c.commit()
    c.close()


class Push:
    def __init__(self):
        self.log = []

    def __call__(self, who, payload):
        self.log.append((who, payload["title"], payload["body"], payload["url"]))
        return 1, 0


D = "2026-11-12"          # a Thursday
Y = "2026-11-11"
A, B, C, Dd, E, F, G, H, I, J, K, L = ["90000000%02d" % i for i in range(1, 13)]
CALLS = [
    (A, "In", 0, D + "T10:00:00+05:30"),
    (B, "In", 0, D + "T09:40:00+05:30"),
    (C, "In", 0, D + "T10:40:00+05:30"),
    (Dd, "In", 0, D + "T10:00:00+05:30"), (Dd, "In", 1, D + "T10:05:00+05:30"),
    (E, "In", 0, D + "T10:00:00+05:30"), (E, "Out", 1, D + "T10:20:00+05:30"),
    (F, "In", 0, D + "T10:00:00+05:30"), (F, "Out", 0, D + "T10:10:00+05:30"),
    (G, "In", 0, D + "T07:30:00+05:30"),
    (H, "In", 0, Y + "T20:45:00+05:30"),
    (I, "In", 0, Y + "T15:00:00+05:30"),
    (J, "In", 0, D + "T09:00:00+05:30"),
    (K, "In", 1, D + "T09:00:00+05:30"), (K, "In", 0, D + "T09:30:00+05:30"),
    (L, "In", 0, D + "T10:00:00+05:30"),
]
PATS = [(L, "MADE UP PATIENT", "99999")]
db, rv, st = os.path.join(tmp, "console.db"), os.path.join(tmp, "rev.db"), os.path.join(tmp, "clock.db")
rev(rv, [J])
T = lambda s: dt.datetime.strptime(s, "%Y-%m-%d %H:%M")           # noqa: E731

# --- the duty clock
chk("duty minutes inside one day", cc.duty_minutes(T(D + " 10:00"), T(D + " 10:58")) == 58, cc.duty_minutes(T(D + " 10:00"), T(D + " 10:58")))
chk("a call before opening counts from 09:00", cc.duty_minutes(T(D + " 07:30"), T(D + " 10:58")) == 118)
chk("a call after closing counts from the next 09:00", cc.duty_minutes(T(Y + " 20:45"), T(D + " 10:58")) == 118)
chk("Sunday closes at 14:30", cc.duty_minutes(T("2026-11-15 14:00"), T("2026-11-15 18:00")) == 30)
chk("no negative time", cc.duty_minutes(T(D + " 11:00"), T(D + " 10:00")) == 0)

# --- run 1: 11:00, the store built 10:58
make(db, D + "T10:58:00+05:30", CALLS, PATS)
p = Push()
r = cc.run(now=T(D + " 11:00"), pusher=p, console=db, store=st, reviews=rv)
chk("run 1 judged", r.get("ok") is True, r)
chk("open callers = A B C F G H K L (8): answered-again, called-back, spam and before-yesterday's-close are out", r.get("open") == 8, r.get("open"))
chk("unknown numbers 7 of 8", r.get("unknown") == 7, r.get("unknown"))
chk("30 min: A B F G H K L = 7 new", r.get("new1") == 7, r.get("new1"))
chk("60 min: B G H K = 4 new", r.get("new2") == 4, r.get("new2"))
staff = [x for x in p.log if x[0] in cc.STAFF]
back = [x for x in p.log if x[0] in cc.BACKUP]
chk("ONE notification to each of the three staff phones", sorted(x[0] for x in staff) == sorted(cc.STAFF), [x[0] for x in staff])
chk("ONE notification to Shavez only", [x[0] for x in back] == ["shavez"], [x[0] for x in back])
chk("the owner hears nothing in the day", not [x for x in p.log if x[0] in cc.OWNER])
chk("the staff title carries the count 7", staff and "7" in staff[0][1], staff[0][1] if staff else "")
chk("the 30-min caller C (18 min) is not named", all(C not in x[2] for x in p.log))
chk("the staff link is the call tracker", staff and staff[0][3] == "/portal/go/call-tracker")

# --- run 2: same minute -> nothing again
p2 = Push()
r2 = cc.run(now=T(D + " 11:00"), pusher=p2, console=db, store=st, reviews=rv)
chk("run 2 sends nothing (each stage once)", r2.get("new1") == 0 and r2.get("new2") == 0 and not p2.log, (r2, p2.log))

# --- run 3: 11:10, built 11:08; L has been called back and answered
make(db, D + "T11:08:00+05:30", CALLS + [(L, "Out", 1, D + "T11:02:00+05:30")], PATS)
p3 = Push()
r3 = cc.run(now=T(D + " 11:10"), pusher=p3, console=db, store=st, reviews=rv)
chk("run 3: L spoken to -> 7 open", r3.get("open") == 7, r3.get("open"))
chk("run 3: nobody new at 30 (C is at 28)", r3.get("new1") == 0, r3.get("new1"))
chk("run 3: A and F reach 60 -> Shavez, 2 new", r3.get("new2") == 2 and [x[0] for x in p3.log] == ["shavez"], (r3.get("new2"), [x[0] for x in p3.log]))

# --- a known patient is named, a number is not shown for him
make(db, D + "T10:58:00+05:30", [(L, "In", 0, D + "T10:00:00+05:30")], PATS)
p4 = Push()
st4 = os.path.join(tmp, "clock4.db")
cc.run(now=T(D + " 11:00"), pusher=p4, console=db, store=st4, reviews=rv)
chk("a known patient is named with the clinic ID, without the number", p4.log and "MADE UP PATIENT (ID 99999)" in p4.log[0][2] and L not in p4.log[0][2], p4.log[:1])

# --- judged as of the store's build time, and a stale store is not judged
make(db, D + "T10:25:00+05:30", [(A, "In", 0, D + "T10:00:00+05:30")])
p5 = Push()
r5 = cc.run(now=T(D + " 10:45"), pusher=p5, console=db, store=os.path.join(tmp, "c5.db"), reviews=rv)
chk("45 min by the clock but 25 by the store's build time -> not yet", r5.get("ok") is True and r5.get("new1") == 0 and not p5.log, (r5, p5.log))
r6 = cc.run(now=T(D + " 11:00"), pusher=p5, console=db, store=os.path.join(tmp, "c5.db"), reviews=rv)
chk("a store 35 minutes old is not judged", r6.get("ok") is False and r6.get("why") == "stale" and not p5.log, r6)

# --- closing: the owner, once, only above zero; no staff push after hours
make(db, D + "T20:38:00+05:30", [(A, "In", 0, D + "T10:00:00+05:30"), (B, "In", 0, D + "T20:10:00+05:30")])
p7 = Push()
st7 = os.path.join(tmp, "c7.db")
r7 = cc.run(now=T(D + " 20:40"), pusher=p7, console=db, store=st7, reviews=rv)
chk("closing: one notification to the owner with the count 2", r7.get("closing") == 1 and [x[0] for x in p7.log] == ["manoj"] and "2" in p7.log[0][1], (r7, p7.log))
chk("closing: the owner's link is the Call Console, in English", p7.log and p7.log[0][3] == "/portal/console" and "Callers not called back" in p7.log[0][1])
p8 = Push()
r8 = cc.run(now=T(D + " 20:45"), pusher=p8, console=db, store=st7, reviews=rv)
chk("closing is said once", r8.get("closing") == 0 and not p8.log, (r8, p8.log))
make(db, D + "T20:38:00+05:30", [(A, "In", 0, D + "T10:00:00+05:30"), (A, "Out", 1, D + "T10:30:00+05:30")])
p9 = Push()
r9 = cc.run(now=T(D + " 20:40"), pusher=p9, console=db, store=os.path.join(tmp, "c9.db"), reviews=rv)
chk("closing with nobody open says nothing", r9.get("closing") == 0 and not p9.log, (r9, p9.log))

# --- dry: counts only, nothing written, nothing sent
make(db, D + "T10:58:00+05:30", CALLS, PATS)
p10 = Push()
st10 = os.path.join(tmp, "c10.db")
r10 = cc.run(dry=True, now=T(D + " 11:00"), pusher=p10, console=db, store=st10, reviews=rv)
chk("dry: counts, no push, no store file", r10.get("open") == 8 and not p10.log and not os.path.exists(st10), (r10, p10.log))

# --- the console store is never written
import hashlib                                                         # noqa: E402
h1 = hashlib.md5(open(db, "rb").read()).hexdigest()
cc.run(now=T(D + " 11:00"), pusher=Push(), console=db, store=os.path.join(tmp, "c11.db"), reviews=rv)
chk("console.db is read-only (same md5 after a run)", hashlib.md5(open(db, "rb").read()).hexdigest() == h1)
chk("a missing console.db is survived", cc.run(now=T(D + " 11:00"), pusher=Push(), console=os.path.join(tmp, "none.db"), store=os.path.join(tmp, "c12.db"), reviews=rv).get("ok") is False)

bad = res.count(False)
print("WALK OK %d/%d" % (len(res), len(res)) if not bad else "WALK RED %d of %d" % (bad, len(res)))
sys.exit(0 if not bad else 1)
