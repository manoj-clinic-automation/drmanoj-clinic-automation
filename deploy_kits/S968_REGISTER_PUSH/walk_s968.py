#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s968.py -- the walk of kit S968_REGISTER_PUSH (the parent, S531, 27-Nov-2026).

    python3 walk_s968.py walk <dir>          <dir> holds clinic_register.py, day_check.py (and register_push.py on the TO side).
                                             Last line ALL PASS, exit 0. On the FROM files it goes red -- the control.
    python3 walk_s968.py live <dir> <db>     the live shape, read-only: a COPY of <db> in a temp folder, every day of the last
                                             week with a register judged with no push -- COUNTS ONLY are printed.
Made-up days and amounts only; no name, no number; never the network; never a live file.
"""
import datetime as dt
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import types

PASS, FAIL = [], []


def ok(cond, name):
    (PASS if cond else FAIL).append(name)
    print(("  PASS  " if cond else "  FAIL  ") + name)


def _stub_flask():
    try:
        import flask  # noqa: F401
        return
    except Exception:                                                   # noqa: BLE001
        pass
    f = types.ModuleType("flask")

    class _BP(object):
        def __init__(self, *a, **k):
            pass

        def route(self, *a, **k):
            return lambda fn: fn

        def before_app_request(self, fn):
            return fn
    f.Blueprint = _BP
    f.request = types.SimpleNamespace(args={}, form={}, method="GET", headers={})
    for n in ("redirect", "jsonify", "Response", "abort", "make_response", "send_file"):
        setattr(f, n, lambda *a, **k: (a, k))
    sys.modules["flask"] = f


def load(d):
    sys.path.insert(0, d)
    _stub_flask()
    import clinic_register as cr                                        # noqa: E402
    import day_check as dc                                              # noqa: E402
    try:
        import register_push as rp                                      # noqa: E402
    except ImportError:
        rp = None
    for m in (cr, dc) + ((rp,) if rp else ()):
        if os.path.dirname(os.path.abspath(m.__file__)) != os.path.abspath(d):
            raise SystemExit("REFUSED: %s did not load from %s" % (m.__name__, d))
    return cr, dc, rp


class FakeDC(object):
    """A day check whose answer the walk sets."""
    def __init__(self):
        self.chk = {}

    def check_day(self, con, day):
        return dict(self.chk.get(day) or {"state": "no_register", "day": day})

    @staticmethod
    def is_clean(chk):
        return chk.get("state") == "checked" and not chk.get("cards") and not chk.get("backdate") \
            and not (chk.get("top") or {}).get("left")

    @staticmethod
    def summary_hi(chk):
        return "%s: kuch theek karna" % chk.get("day")


def card(key, amount=10000, kind="notfound"):
    return {"key": key, "kind": kind, "amount": amount, "who": "docterz", "hi": "line %s" % key, "en": "line %s" % key}


def walk_push(rp, tmp):
    db = os.path.join(tmp, "push.db")
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE clinic_register_day (business_date TEXT PRIMARY KEY)")
    for d in ("2026-11-20", "2026-11-25", "2026-11-26"):
        con.execute("INSERT INTO clinic_register_day VALUES (?)", (d,))
    con.commit()
    fake = FakeDC()
    fake.chk["2026-11-20"] = {"state": "checked", "day": "2026-11-20", "cards": [card("old:1")]}   # there, unseen, at install
    rp.DC_MOD = fake
    rp.LIVE_DB = db
    sent = []
    rp._send = lambda who, title, body, tag: (sent.append((tuple(who), title, body, tag)) or ((len(who), 0, 0), ""))
    os.environ["REGPUSH_TO"] = "shavez,reception"
    os.environ.pop("REGPUSH_ON", None)
    at = dt.datetime(2026, 11, 27, 9, 31)
    D = "2026-11-26"
    fake.chk[D] = {"state": "no_register", "day": D}
    w = rp.one_day(con, D, at=at, from_save=True)
    ok(w.startswith("skip") and not sent, "a day not yet checked (no register / no Docterz): nothing pushed")
    fake.chk[D] = {"state": "checked", "day": D, "cards": [card("nf:cash:proc:10000")]}
    w = rp.one_day(con, D, at=at, from_save=True)
    ok(" open 1 " in w and len(sent) == 1 and sent[0][0] == ("shavez", "reception") and "26-Nov: 1 galti" in sent[0][1]
       and sent[0][3] == "daycheck-" + D, "the Save of a day with a line: ONE push to shavez + reception, '26-Nov: 1 galti'")
    ok("line nf:cash:proc:10000" in sent[0][2], "the push carries the day check's own line words")
    rp.one_day(con, D, at=at, from_save=True)
    rp.sweep(con, at=at)
    ok(len(sent) == 1, "the same line again (a second Save, the sweep): no second push")
    fake.chk[D]["cards"] = [card("nf:cash:proc:10000"), card("pmiss:x:proc", kind="parchi_missing")]
    rp.sweep(con, at=at)
    ok(len(sent) == 2 and "2 galtiyan" in sent[1][1], "a NEW line on the day: pushed again, '2 galtiyan'")
    fake.chk[D]["cards"] = [card("pmiss:x:proc", kind="parchi_missing")]
    rp.sweep(con, at=at)
    ok(len(sent) == 2, "one line fixed, one left: no push (nothing new to say)")
    fake.chk[D] = {"state": "checked", "day": D, "cards": []}
    rp.sweep(con, at=at)
    ok(len(sent) == 3 and "sab galtiyan theek" in sent[2][1], "every line fixed after a push: 'sab galtiyan theek'")
    rp.sweep(con, at=at)
    ok(len(sent) == 3, "clean and already told: no push")
    # a clean first look
    D2 = "2026-11-25"
    fake.chk[D2] = {"state": "checked", "day": D2, "cards": []}
    w = rp.one_day(con, D2, at=at, from_save=True)
    ok(len(sent) == 4 and "sab mile" in sent[3][1], "a day clean at its first look: '<day>: register, Docterz aur parchi sab mile'")
    # an old day the sweep meets first: recorded quietly; its old lines never pushed later
    D3 = "2026-11-20"
    rp.sweep(con, at=at)
    ok(len(sent) == 4, "an old day met first by the sweep (install): recorded quietly, no push")
    rp.sweep(con, at=at)
    ok(len(sent) == 4, "the old day's old line: still no push")
    fake.chk[D3]["cards"] = [card("old:1"), card("old:2")]
    rp.sweep(con, at=at)
    ok(len(sent) == 5, "a new line on the old day later: pushed")
    # a Save of an old day judges it at once
    D4 = "2026-11-21"
    con.execute("INSERT INTO clinic_register_day VALUES (?)", (D4,))
    con.commit()
    fake.chk[D4] = {"state": "checked", "day": D4, "cards": [card("s:1")]}
    rp.one_day(con, D4, at=at, from_save=True)
    ok(len(sent) == 6, "a Save of an older day (a Monday entry for Saturday): pushed at once")
    # the switch, the live database, the logins
    D5 = "2026-11-27"
    con.execute("INSERT INTO clinic_register_day VALUES (?)", (D5,))
    con.commit()
    fake.chk[D5] = {"state": "checked", "day": D5, "cards": [card("t:1")]}
    os.environ["REGPUSH_ON"] = "0"
    w = rp.one_day(con, D5, at=at, from_save=True)
    ok(len(sent) == 6 and " off " in w, "REGPUSH_ON=0: nothing pushed, 'off' recorded")
    os.environ.pop("REGPUSH_ON", None)
    rp.LIVE_DB = os.path.join(tmp, "not_this.db")
    con.execute("DELETE FROM register_push WHERE day=?", (D5,))
    con.commit()
    w = rp.one_day(con, D5, at=at, from_save=True)
    ok(len(sent) == 6 and "not the live database" in w, "not the live database: the answer recorded, nothing pushed")
    rp.LIVE_DB = db
    # a failing send never raises
    rp._send = lambda *a: (None, "send: boom")
    con.execute("DELETE FROM register_push WHERE day=?", (D5,))
    con.commit()
    w = rp.one_day(con, D5, at=at, from_save=True)
    ok("not pushed (send: boom)" in w, "a send that fails: recorded in words, never raised")
    # cold review S968: what is pushed is the STAFF's lines only; a partly fixed line is not new; a late check is still told
    D6 = "2026-11-24"
    con.execute("INSERT INTO clinic_register_day VALUES (?)", (D6,))
    con.commit()
    rp._send = lambda who, title, body, tag: (sent.append((tuple(who), title, body, tag)) or ((len(who), 0, 0), ""))
    n0 = len(sent)
    hand = dict(card("hand:1"), who="hand")
    fake.chk[D6] = {"state": "checked", "day": D6, "cards": [hand], "backdate": [{"key": "bd:1", "cid": "x", "amount": 1}]}
    rp.one_day(con, D6, at=at, from_save=True)
    ok(len(sent) == n0, "only the owner's back-date row and a 'check by hand' line: nothing pushed to the staff")
    fake.chk[D6]["cards"] = [hand, dict(card("nf:cash:proc:30000"), tick={"act": "found"})]
    rp.one_day(con, D6, at=at, from_save=True)
    ok(len(sent) == n0, "a line the staff ticked (waiting for the re-export): not pushed")
    fake.chk[D6]["cards"] = [card("nf:cash:proc:30000")]
    rp.one_day(con, D6, at=at, from_save=True)
    ok(len(sent) == n0 + 1, "the line un-ticked (the re-export did not fix it): pushed")
    fake.chk[D6]["cards"] = [card("nf:cash:proc:20000")]
    rp.sweep(con, at=at)
    ok(len(sent) == n0 + 1, "the same line with a smaller amount (partly fixed): no new push")
    D7 = "2026-11-22"
    con.execute("INSERT INTO clinic_register_day VALUES (?)", (D7,))
    con.commit()
    fake.chk[D7] = {"state": "no_docterz", "day": D7}
    rp.sweep(con, at=at)
    fake.chk[D7] = {"state": "checked", "day": D7, "cards": [card("late:a")]}
    rp.sweep(con, at=at)
    ok(len(sent) == n0 + 2 and "22-Nov" in sent[-1][1], "a day checked late (its Docterz export days after the register): still told")
    fake.chk[D7]["cards"] = [card("late:a"), card("late:b")]
    rp.sweep(con, at=at)
    ok(len(sent) == n0 + 3 and "late:b" in sent[-1][2].split(" ; ")[0], "a new line leads the push's words")
    ok(rp._norm("add:12") != rp._norm("add:13") and rp._norm("nf:cash:proc:300") == rp._norm("nf:cash:proc:200"),
       "two different missing items stay two lines; only a not-found line's amount is dropped from its name")
    # no names, no numbers in the store
    row = con.execute("SELECT keys FROM register_push WHERE day=?", (D,)).fetchone()
    ok(row is not None and "line" not in (row[0] or ""), "the store keeps line keys only, never the words")
    con.close()


def walk_register(cr, tmp):
    """The heading: the module's own three_way with its readers replaced by made-up records."""
    reg = {"%s_%s_p" % (s, t): 0 for s, _ in cr.SECTIONS for t, _x in cr.TENDERS}
    reg["cons_cash_p"], reg["xray_cash_p"], reg["dress_cash_p"], reg["cons_upi_p"] = 420000, 340000, 10000, 150000
    doc = {"known": True, "cash": 760000, "upi": 150000, "card": 0}
    cr.register_row = lambda con, d: reg
    cr.docterz_day = lambda con, d: doc
    cr.physio_row = lambda con, d: None
    cr.drawer_row = lambda con, d: None
    cr.expected_handover_p = lambda con, d: None
    cr.bank_upi = lambda con, d: (150000, True)
    if hasattr(cr, "_cm"):
        cr._cm = None
    t = cr.three_way(None, "2026-11-26")
    ok(t["verdict"] == "cash differs" and "Rs 7,700" in t["why"] and "Rs 7,600" in t["why"],
       "the 26-Nov case: UPI agrees, cash Rs 100 apart -> 'cash differs', both figures named (not 'all agree')")
    doc["cash"] = 770000
    t = cr.three_way(None, "2026-11-26")
    ok(t["verdict"] == "all agree" and t["why"] == "all three records agree on UPI", "all three agree, cash too: 'all agree' as before")
    doc["cash"] = 760000
    cr.bank_upi = lambda con, d: (None, False)
    t = cr.three_way(None, "2026-11-26")
    ok(t["verdict"] == "waiting_bank" and "differ on cash" in t["why"], "bank not in yet: the line also names the cash difference")
    doc["cash"] = 770000
    t = cr.three_way(None, "2026-11-26")
    ok(t["verdict"] == "waiting_bank" and "differ on" not in t["why"], "bank not in, cash equal: the line as before")
    src = open(cr.__file__, encoding="utf-8").read()
    ok(".pill.cash_differs" in src, "the new heading has its colour (red, as 'Docterz differs')")


def walk_spawn(cr, tmp):
    """The Save's start of register_push.py: a stand-in script beside a copy of the module records how it was started."""
    d = os.path.join(tmp, "spawn")
    os.makedirs(os.path.join(d, "logs"))
    shutil.copy(cr.__file__, os.path.join(d, "clinic_register.py"))
    mark = os.path.join(d, "started.txt")
    with open(os.path.join(d, "register_push.py"), "w") as fh:
        fh.write("import sys\nopen(%r, 'w').write(' '.join(sys.argv[1:]))\n" % mark)
    db = os.path.join(d, "x.db")
    sqlite3.connect(db).close()
    code = ("import sys, sqlite3, os; sys.path.insert(0, %r); sys.path.insert(1, %r); import walk_s968 as w; w._stub_flask(); "
            "import clinic_register as cr; con = sqlite3.connect(%r); print(cr._s968_spawn(con, '2026-11-26'))"
            % (d, os.path.dirname(os.path.abspath(__file__)), db))
    env = dict(os.environ, REGPUSH_PY=sys.executable)
    r = subprocess.run([sys.executable, "-B", "-c", code], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                       env=env, cwd=d, timeout=60)
    for _ in range(50):
        if os.path.exists(mark):
            break
        import time
        time.sleep(0.1)
    got = open(mark).read() if os.path.exists(mark) else ""
    ok(r.stdout.strip().endswith("True") and got == "--day 2026-11-26 --db %s" % db,
       "a Save starts register_push.py --day <day> --db <the same database>, detached")
    env["REGPUSH_SPAWN"] = "0"
    os.remove(mark) if os.path.exists(mark) else None
    r = subprocess.run([sys.executable, "-B", "-c", code], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                       env=env, cwd=d, timeout=60)
    ok(r.stdout.strip().endswith("False") and not os.path.exists(mark), "REGPUSH_SPAWN=0: the Save starts nothing")
    src = open(cr.__file__, encoding="utf-8").read()
    ok(src.count("_s968_spawn(con, date)") == 1, "the Save calls it once, after the day is written and committed")


def walk_daycheck(dc):
    src = open(dc.__file__, encoding="utf-8").read()
    ok("make the parchi if there is none" in src and "parchi na ho to parchi bhi banaiye" in src,
       "the 'patient not found' card asks for the parchi too (English and Hindi)")
    ok("Parchi banayein" in src and "'opd' if" not in src and '"opd" if c.get("section") == "consult" else "xp"' in src,
       "Shavez gets 'Parchi banayein' on that card (OPD for a consultation, X-ray/Proc otherwise)")


def do_walk(d):
    tmp = tempfile.mkdtemp(prefix="s968w_")
    try:
        cr, dc, rp = load(d)
        ok(rp is not None and hasattr(cr, "_s968_spawn"), "kit S968 marked (register_push.py beside the register, the Save's start)")
        if rp is not None:
            walk_push(rp, tmp)
        walk_register(cr, tmp)
        if hasattr(cr, "_s968_spawn"):
            walk_spawn(cr, tmp)
        walk_daycheck(dc)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def do_live(d, db):
    """Read-only: a copy of the database in a temp folder; each day of the last week with a register judged, no push. Counts."""
    tmp = tempfile.mkdtemp(prefix="s968l_")
    try:
        os.chmod(tmp, 0o700)
        cp = os.path.join(tmp, "copy.db")
        src = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
        dst = sqlite3.connect(cp)
        src.backup(dst)
        src.close()
        cr, dc, rp = load(d)
        dst.row_factory = sqlite3.Row
        rp.LIVE_DB = os.path.join(tmp, "never.db")
        today = rp.now_ist().date()
        days = [r[0] for r in dst.execute("SELECT business_date FROM clinic_register_day WHERE business_date>=? ORDER BY business_date",
                                          ((today - dt.timedelta(days=7)).isoformat(),))]
        counts, errs = {}, 0
        for x in days:
            try:
                w = rp.judge(dst, x, push=False, at=rp.now_ist(), from_save=True)
                k = w.split(" ")[1] if not w.startswith("skip") else "skip"
            except Exception:                                           # noqa: BLE001
                k, errs = "error", errs + 1
            counts[k] = counts.get(k, 0) + 1
        dst.close()
        print("LIVE days %d errors %d %s" % (len(days), errs, " ".join("%s %d" % kv for kv in sorted(counts.items()))))
        ok(errs == 0 and len(days) > 0, "the live shape: every recent day judged with no error (%d days)" % len(days))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(a):
    if len(a) >= 2 and a[0] == "walk":
        do_walk(a[1])
    elif len(a) >= 3 and a[0] == "live":
        do_live(a[1], a[2])
    else:
        print(__doc__)
        return 2
    print("%d checks, %d failed" % (len(PASS) + len(FAIL), len(FAIL)))
    print("ALL PASS" if not FAIL else "NOT ALL PASS")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception as e:                                              # noqa: BLE001
        import traceback
        traceback.print_exc()
        print("  FAIL  the walk crashed: %s" % type(e).__name__)
        print("NOT ALL PASS")
        sys.exit(1)
