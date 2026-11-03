#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s704.py -- kit S704_SPINE_VOUCHER_FOLD (03-Nov-2026, Sanjeevni session 383).

    python3 -B walk_s704.py --new ROOT  [--scratch DIR]   the checks on ROOT/finance/{spine/spine_build.py, order_rules.py}: 'N of N green'
    python3 -B walk_s704.py --old ROOT  [--scratch DIR]   the CONTROL on the live files: the S704 checks must go red, the rest green
    python3 -B walk_s704.py --proof --old-root R --new R2 --readings DIR --findb FINANCE_DB [--rules JSON] --db COPY --scratch DIR
                                                          OLD against NEW on real data: the spine built twice from the same readings
                                                          and the same finance.db (read-only); plan() and the owner's fold on a COPY

Every row a check stands on is made here (made-up items, 2026-04 days, its own scratch databases) -- F-998. No real export, no number.
The kit's own folder is dropped from sys.path, so the ROOT's files answer, never a copy beside the walk.
"""
import argparse
import collections
import contextlib
import datetime as dt
import importlib.util
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") not in (HERE, os.path.abspath("."))]
RES = []                                   # (kind, name, ok, detail) kind: S704 | REG


def ck(kind, name, fn):
    try:
        ok, det = fn()
    except Exception as e:                 # noqa: BLE001 -- a check that cannot run is red
        ok, det = False, "%s: %s" % (type(e).__name__, str(e)[:160])
    RES.append((kind, name, bool(ok), det))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# ===================================================================== the spine (F-1025)
def fin_db(path, vouchers=None, void=(), tables=True):
    """A made-up finance.db: the count baseline's 373 rows, and (tables=True) the three voucher tables with `vouchers` =
    [(round, kind, batch, item, change, [(voucher_no, entered_on, at), ...]), ...]."""
    if os.path.exists(path):
        os.remove(path)
    c = sqlite3.connect(path)
    c.execute("CREATE TABLE stock_count_item (id INTEGER)")
    c.executemany("INSERT INTO stock_count_item VALUES (?)", [(i,) for i in range(373)])
    if tables:
        c.execute("CREATE TABLE stock_voucher_line (id INTEGER PRIMARY KEY, count_id INTEGER, round_no INTEGER, kind TEXT, batch_no INTEGER, item TEXT, change INTEGER)")
        c.execute("CREATE TABLE stock_voucher_entered (id INTEGER PRIMARY KEY, count_id INTEGER, round_no INTEGER, kind TEXT, batch_no INTEGER, marg_voucher_no TEXT NOT NULL, entered_on TEXT, by_user TEXT, at TEXT NOT NULL)")
        c.execute("CREATE TABLE stock_voucher_void (id INTEGER PRIMARY KEY, count_id INTEGER, round_no INTEGER, kind TEXT, batch_no INTEGER, by_user TEXT, at TEXT, reason TEXT)")
        for rno, kind, bno, item, ch, ents in (vouchers or []):
            c.execute("INSERT INTO stock_voucher_line (count_id, round_no, kind, batch_no, item, change) VALUES (1,?,?,?,?,?)", (rno, kind, bno, item, ch))
            for vno, eon, at in ents:
                c.execute("INSERT INTO stock_voucher_entered (count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, by_user, at) VALUES (1,?,?,?,?,?,?,?)",
                          (rno, kind, bno, vno, eon, "walk", at))
        for rno, kind, bno in void:
            c.execute("INSERT INTO stock_voucher_void (count_id, round_no, kind, batch_no, by_user, at, reason) VALUES (1,?,?,?,'walk','2026-04-04T10:00','walk')", (rno, kind, bno))
    c.commit()
    c.close()
    return path


def spine_checks(root, scratch):
    sd = os.path.join(root, "finance", "spine")
    for p in (sd, os.path.join(root, "finance")):
        if p not in sys.path:
            sys.path.insert(0, p)
    B = load("spine_build", os.path.join(sd, "spine_build.py"))
    T = load("selftest_spine", os.path.join(sd, "selftest_spine.py"))
    from spine_read import Spine
    base = os.path.join(scratch, "spine")
    os.makedirs(base, exist_ok=True)
    rd, rp = T.store(os.path.join(base, "store36"), opening_units=36, recon=False)   # the spine 21, Marg 20 at 05-Apr: a -1 difference

    def build(tag, fdb, acceptance=False):
        out = os.path.join(base, tag, "s.db")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        argv = ["--readings", rd, "--rules", rp, "--out", out, "--finance-db", fdb] + (["--acceptance"] if acceptance else [])
        with contextlib.redirect_stdout(io.StringIO()):
            rc = B.main(argv)
        return rc, out

    def notes(out):
        c = sqlite3.connect(out)
        r = [tuple(x) for x in c.execute("SELECT as_on, k20, diff, note FROM sp_finding ORDER BY as_on, k20")]
        c.close()
        return r

    def V(ch=-1, ents=(("V1", "03-04-2026", "2026-04-03T10:00:00"),), item="ALPHA TAB"):
        return [(1, "ISSUE", 1, item, ch, list(ents))]

    def case(tag, vouchers=None, void=(), tables=True):
        fdb = fin_db(os.path.join(base, tag + ".db"), vouchers, void, tables)
        rc, out = build(tag, fdb)
        return rc, out, notes(out)

    def is_v(n):
        return len(n) == 1 and n[0][3].startswith("VOUCHER") and n[0][1] == "ALPHA TAB" and abs(n[0][2] + 1) < 1e-9

    def is_o(n):
        return len(n) == 1 and n[0][3].startswith("OPEN")

    ck("REG", "spine: no voucher tables -- the -1 difference is an OPEN finding (as before)", lambda: (lambda r: (r[0] == 0 and is_o(r[2]), r[2]))(case("none", tables=False)))
    ck("REG", "spine: voucher tables, no voucher at all -- OPEN (as before)", lambda: (lambda r: (r[0] == 0 and is_o(r[2]), r[2]))(case("empty")))
    ck("S704", "spine: a voucher filed in Marg on 03-04 (dd-mm-yyyy) equal to the difference -- VOUCHER, not OPEN", lambda: (lambda r: (r[0] == 0 and is_v(r[2]), r[2]))(case("filed", V())))
    ck("S704", "spine: the status line has no EXCEPT when the vouchers explain every difference", lambda: (lambda r: ("EXCEPT" not in Spine(r[1]).status() and Spine(r[1]).findings() == [], Spine(r[1]).status()))(case("filed_s", V())))
    ck("S704", "spine: entered_on ISO (2026-04-03) -- VOUCHER", lambda: (lambda r: (is_v(r[2]), r[2]))(case("iso", V(ents=(("V1", "2026-04-03", "2026-04-03T10:00:00"),)))))
    ck("S704", "spine: entered_on dd/mm/yyyy -- VOUCHER", lambda: (lambda r: (is_v(r[2]), r[2]))(case("slash", V(ents=(("V1", "03/04/2026", "2026-04-03T10:00:00"),)))))
    ck("S704", "spine: no entered_on -- the day of `at` (04-04) decides -- VOUCHER", lambda: (lambda r: (is_v(r[2]), r[2]))(case("at", V(ents=(("V1", None, "2026-04-04T10:00:00"),)))))
    ck("S704", "spine: the voucher is said with its units in the note (-1)", lambda: (lambda r: ("(-1)" in r[2][0][3], r[2]))(case("units", V())))
    ck("REG", "spine: a voucher with NO number (not in Marg) explains nothing -- OPEN", lambda: (lambda r: (is_o(r[2]), r[2]))(case("nonum", V(ents=(("", "03-04-2026", "2026-04-03T10:00:00"),)))))
    ck("REG", "spine: the newest row of the batch cleared its number -- OPEN", lambda: (lambda r: (is_o(r[2]), r[2]))(case("cleared", V(ents=(("V1", "03-04-2026", "2026-04-03T10:00:00"), ("", None, "2026-04-03T11:00:00"))))))
    ck("REG", "spine: a voided batch explains nothing -- OPEN", lambda: (lambda r: (is_o(r[2]), r[2]))(case("void", V(), void=[(1, "ISSUE", 1)])))
    ck("REG", "spine: a voucher filed AFTER the closing (06-04) explains nothing at 05-04 -- OPEN", lambda: (lambda r: (is_o(r[2]), r[2]))(case("late", V(ents=(("V1", "06-04-2026", "2026-04-06T10:00:00"),)))))
    ck("REG", "spine: a voucher of -2 against a -1 difference explains nothing -- OPEN", lambda: (lambda r: (is_o(r[2]), r[2]))(case("wrong", V(ch=-2))))
    ck("REG", "spine: a voucher for another item explains nothing -- OPEN", lambda: (lambda r: (is_o(r[2]), r[2]))(case("other", V(item="BETA TAB"))))
    ck("REG", "spine: a voucher dated on the opening day (31-03) is outside (opening, closing] -- OPEN", lambda: (lambda r: (is_o(r[2]), r[2]))(case("opening", V(ents=(("V1", "31-03-2026", "2026-03-31T10:00:00"),)))))
    ck("S704", "spine: two batches -3 and +2 summing to the -1 difference -- VOUCHER", lambda: (lambda r: (is_v(r[2]), r[2]))(case("two", [(1, "ISSUE", 1, "ALPHA TAB", -3, [("V1", "03-04-2026", "2026-04-03T10:00:00")]),
                                                                                                                                       (1, "RECEIVE", 1, "ALPHA TAB", 2, [("V2", "03-04-2026", "2026-04-03T10:05:00")])])))

    def same_moves():
        a = case("mv_a", tables=False)[1]
        b = case("mv_b", V())[1]
        q = lambda p, t: sorted(tuple(x) for x in sqlite3.connect(p).execute("SELECT * FROM %s" % t))
        diffs = [t for t in ("sp_move", "sp_check", "sp_close", "sp_recon", "sp_sale_line", "sp_purchase_line", "sp_item") if q(a, t) != q(b, t)]
        kinds = sorted({r[0] for r in sqlite3.connect(b).execute("SELECT DISTINCT kind FROM sp_move")})
        return (not diffs and "VOUCHER" not in kinds, "differ: %s; kinds %s" % (diffs, kinds))
    ck("REG", "spine: the vouchers are never booked -- sp_move, sp_check and every stock table are the same with and without them", same_moves)

    def gate_row():
        out = case("gate", V())[1]
        r = sqlite3.connect(out).execute("SELECT blocking, ok, detail FROM sp_gate WHERE name LIKE 'STOCK: the spine equals Marg on every item%'").fetchone()
        return (r is not None and r[0] == 0 and r[1] == 0, r)
    ck("REG", "spine: the STOCK gate row keeps its ok and blocking (0 / 0 without --acceptance) -- a voucher difference is still a difference", gate_row)

    def gate_detail():
        out = case("gate_d", V())[1]
        d = sqlite3.connect(out).execute("SELECT detail FROM sp_gate WHERE name LIKE 'STOCK: the spine equals Marg on every item%'").fetchone()[0]
        return ("explained by Amir's filed vouchers: 1" in d and "open: []" in d, d[-160:])
    ck("S704", "spine: the STOCK gate row says how many the vouchers explain, and lists only the open ones", gate_detail)

    def accept():
        fdb = fin_db(os.path.join(base, "acc.db"), V())
        rc, out = build("acc", fdb, acceptance=True)
        return (rc == 3, "rc %s" % rc)
    ck("REG", "spine: --acceptance still refuses a build with any difference, voucher or not", accept)
    ck("S704", "spine: BUILD_VERSION is S704.1", lambda: (B.BUILD_VERSION == "S704.1", B.BUILD_VERSION))

    def own_selftest():
        p = subprocess.run([sys.executable, "-B", os.path.join(sd, "selftest_spine.py")], cwd=scratch, capture_output=True, text=True, timeout=600,
                           env=dict(os.environ, PYTHONPYCACHEPREFIX=os.path.join(scratch, "pyc")))
        last = (p.stdout.strip().splitlines() or [""])[-1]
        return (p.returncode == 0 and last.startswith("SELFTEST OK"), last or p.stderr[-200:])
    ck("REG", "spine: its own selftest_spine.py, against this root's spine_build", own_selftest)


# ===================================================================== the owner's fold (F-1028)
NOTE = dict(sales_through="2026-04-04", capture=dict(md5="abcd1234", as_on="2026-04-04", end_day="2026-04-04", stamp="20260404-231000"),
            spine_built="2026-04-05T09:40:47+05:30", counted=300, marg=60, absent=2, made_at="2026-04-05T09:00:10", window_end="2026-04-04")
STAMP = json.dumps(dict(end_day="2026-04-04", sales_through="2026-04-04", spine_built="2026-04-05T09:40:47+05:30"), sort_keys=True)


def fold_checks(root, scratch):
    fd = os.path.join(root, "finance")
    for p in (os.path.join(fd, "spine"), fd):
        if p not in sys.path:
            sys.path.insert(0, p)
    OR = load("order_rules_walk", os.path.join(fd, "order_rules.py"))

    def mem(model="levels"):
        c = sqlite3.connect(":memory:")
        c.row_factory = sqlite3.Row
        c.execute("CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT)")
        c.execute("INSERT INTO setting VALUES ('order.model', ?)", (model,))
        c.execute("CREATE TABLE order_notice (id INTEGER PRIMARY KEY, day TEXT NOT NULL, slot TEXT NOT NULL, text TEXT NOT NULL, sent TEXT, at TEXT, UNIQUE(day, slot))")
        return c

    saved = {k: getattr(OR, k) for k in ("plan_before_s704", "_s644_stamp_day_before_s704", "_s644_relist_before_s704", "_s644_owner_before_s704",
                                         "_s470_inputs_note") if hasattr(OR, k)}

    saved.update({k: getattr(OR, k) for k in ("plan", "_s644_owner", "_s644_relist")})

    def restore():
        for k, v in saved.items():
            setattr(OR, k, v)

    def patch(new_name, old_name, fn):
        """S704's files wrap the base under <name>_before_s704; the live file has no wrapper, so the base itself is replaced and the
        control sees the live behaviour exactly."""
        setattr(OR, new_name if hasattr(OR, new_name) else old_name, fn)

    def fake_plan(con, today=None, suppliers=None):
        return dict(vendors={"KEDAR": dict(lines=[dict(item="ALPHA TAB", qty=10, model="levels"), dict(item="RANI TAB", qty=5, why=["short-supplied -- carried"])]),
                             "LK": dict(lines=[dict(item="GAMMA", qty=2, model="fixed")])}, inputs=None)

    def plan_case(model):
        patch("plan_before_s704", "plan", fake_plan)
        try:
            d = OR.plan(mem(model), dt.date(2026, 4, 6))
        finally:
            restore()
        L = {l["item"]: l for v in d["vendors"].values() for l in v["lines"]}
        return L
    ck("S704", "fold (c): on levels a carried line with no model word takes 'levels'", lambda: (lambda L: (L["RANI TAB"].get("model") == "levels", L["RANI TAB"]))(plan_case("levels")))
    ck("S704", "fold (c): on fixed it takes 'fixed'", lambda: (lambda L: (L["RANI TAB"].get("model") == "fixed", L["RANI TAB"]))(plan_case("fixed")))
    ck("S704", "fold (c): a line that has its word keeps it, and nothing else on any line moves", lambda: (lambda L: (L["ALPHA TAB"] == dict(item="ALPHA TAB", qty=10, model="levels") and L["GAMMA"] == dict(item="GAMMA", qty=2, model="fixed")
                                                                                                    and L["RANI TAB"] == dict(item="RANI TAB", qty=5, why=["short-supplied -- carried"], model="levels"), L))(plan_case("levels")))

    def keep_case(note, which, res=None):
        c = mem()
        OR._s470_inputs_note = lambda process=False: note
        try:
            if which == "stamp":
                OR._s644_stamp_day(c, dt.date(2026, 4, 5))
            else:
                patch("_s644_relist_before_s704", "_s644_relist", lambda con, today, now: res)
                OR._s644_relist(c, dt.date(2026, 4, 5), dt.datetime(2026, 4, 5, 10, 0))
        finally:
            restore()
        return {r["slot"]: r["text"] for r in c.execute("SELECT slot, text FROM order_notice WHERE day='2026-04-05'")}
    ck("S704", "fold (a): the 09:00 list keeps its inputs beside made_through (slot inputs_note, the whole note)",
       lambda: (lambda S: ("inputs_note" in S and json.loads(S["inputs_note"]) == NOTE and json.loads(S.get("made_through", "null")) == json.loads(STAMP), S))(keep_case(NOTE, "stamp")))
    ck("REG", "fold (a): with no note nothing is kept (no made_through, no inputs_note)", lambda: (lambda S: (S == {}, S))(keep_case(None, "stamp")))
    ck("S704", "fold (a): a relist that made the list again keeps the new inputs", lambda: (lambda S: ("inputs_note" in S, S))(keep_case(NOTE, "relist", "relisted 4")))
    ck("REG", "fold (a): a relist that changed nothing keeps nothing", lambda: (lambda S: (S == {}, S))(keep_case(NOTE, "relist", "same")))

    BASE = dict(value="levels", words="Levels", other="fixed", other_words="Fixed", settings=[dict(key="order.model", value="levels", note="n")], inputs=None,
                made_through=dict(text=STAMP, at="x"), relist=dict(text="made again at 12:50: 16 rows, inputs " + STAMP, at="y"),
                stale=dict(text="the list was touched before newer inputs landed: " + STAMP, at="z"), score="score line", rhythm=[dict(supplier="KEDAR")])

    def owner_case(day, rows, base=None):
        c = mem()
        for d, t in rows:
            c.execute("INSERT INTO order_notice (day, slot, text, sent, at) VALUES (?,?,?,?,?)", (d, "inputs_note", t, None, "a"))
        b = json.loads(json.dumps(base or BASE))
        patch("_s644_owner_before_s704", "_s644_owner", lambda con, today=None: json.loads(json.dumps(b)))
        try:
            return OR._s644_owner(c, day)
        finally:
            restore()
    two = [("2026-04-04", json.dumps(dict(NOTE, sales_through="2026-04-03"))), ("2026-04-05", json.dumps(NOTE))]
    ck("S704", "fold (a): the fold's inputs are the newest kept list's -- the line 'The last list stood on' has every field it draws",
       lambda: (lambda o: (o["inputs"] and o["inputs"]["sales_through"] == "2026-04-04" and o["inputs"]["capture"]["end_day"] == "2026-04-04"
                           and all(k in o["inputs"] for k in ("spine_built", "counted", "marg", "absent")) and o["inputs"]["list_day"] == "2026-04-05", o.get("inputs")))(owner_case(dt.date(2026, 4, 5), two)))
    ck("S704", "fold (a): read on the 04th it is the 04th's list (never a later day's)", lambda: (lambda o: (o["inputs"] and o["inputs"]["list_day"] == "2026-04-04", o.get("inputs")))(owner_case(dt.date(2026, 4, 4), two)))
    ck("REG", "fold (a): with no kept list the base's inputs stand (None)", lambda: (lambda o: (o["inputs"] is None, o.get("inputs")))(owner_case(dt.date(2026, 4, 5), [])))
    ck("REG", "fold (a): a kept row that is not JSON is ignored", lambda: (lambda o: (o["inputs"] is None, o.get("inputs")))(owner_case(dt.date(2026, 4, 5), [("2026-04-05", "not json")])))
    ck("S704", "fold (b): the relist line in words -- no raw JSON, the time, the count and the three figures",
       lambda: (lambda t: ("{" not in t and t.startswith("Made again at 12:50") and "16 supplier lists" in t and "04-Apr-2026" in t and "05-Apr-2026 09:40" in t, t))(owner_case(dt.date(2026, 4, 5), [])["relist"]["text"]))
    ck("S704", "fold (b): the stale line in words", lambda: (lambda t: ("{" not in t and t.startswith("Not made again") and "04-Apr-2026" in t, t))(owner_case(dt.date(2026, 4, 5), [])["stale"]["text"]))
    ck("S704", "fold (b): a relist of 0 rows says it checked and had nothing to make again",
       lambda: (lambda t: (t.startswith("Checked again at 09:50") and "{" not in t, t))(owner_case(dt.date(2026, 4, 5), [], dict(BASE, relist=dict(text="made again at 09:50: 0 rows, inputs " + STAMP, at="y")))["relist"]["text"]))
    ck("REG", "fold (b): a text that is not S644's shape is left exactly as it was",
       lambda: (lambda t: (t == "something else", t))(owner_case(dt.date(2026, 4, 5), [], dict(BASE, relist=dict(text="something else", at="y")))["relist"]["text"]))
    ck("REG", "fold: every other key of the fold is the base's, unchanged (value, words, settings, made_through, score, rhythm)",
       lambda: (lambda o: (all(o[k] == BASE[k] for k in ("value", "words", "other", "other_words", "settings", "made_through", "score", "rhythm")), {k: o[k] for k in ("value", "made_through")}))(owner_case(dt.date(2026, 4, 5), two)))
    ck("REG", "fold: owner_state still wraps _s644_owner (the page's door is the same)", lambda: (callable(getattr(OR, "owner_state", None)) and "_s644_owner" in OR.owner_state.__code__.co_names, OR.owner_state.__code__.co_names))
    ck("REG", "order_rules: never writes order.source (no such text in the file)", lambda: (lambda s: ("order.source" not in s.split("# ---- S644 end")[-1], "tail clean"))(open(os.path.join(fd, "order_rules.py"), encoding="utf-8").read()))


# ===================================================================== the proof on real data (the box)
def proof(a):
    out = []
    say = lambda s: (out.append(s), print(s))
    os.makedirs(a.scratch, exist_ok=True)
    # ---- the spine, twice, the same readings and the same finance.db (read-only door)
    res = {}
    for tag, root in (("old", a.old_root), ("new", a.new)):
        o = os.path.join(a.scratch, tag, "spine.db")
        os.makedirs(os.path.dirname(o), exist_ok=True)
        p = subprocess.run([sys.executable, "-B", os.path.join(root, "finance", "spine", "spine_build.py"), "--readings", a.readings,
                            "--rules", a.rules or os.path.join(a.old_root, "finance", "spine", "spine_rules.json"), "--out", o, "--finance-db", a.findb],
                           cwd=os.path.join(a.scratch, tag), capture_output=True, text=True, timeout=900, env=dict(os.environ, PYTHONPYCACHEPREFIX=os.path.join(a.scratch, "pyc")))
        res[tag] = (p.returncode, o)
        say("  --  spine %s build rc %d" % (tag, p.returncode))
    bad = []
    built = lambda o: os.path.exists(o) and sqlite3.connect(o).execute("SELECT COUNT(*) FROM sqlite_master WHERE name='sp_meta'").fetchone()[0] == 1
    if res["old"][0] != 0 or res["new"][0] != 0 or not built(res["old"][1]) or not built(res["new"][1]):
        bad.append("a build did not swap (old rc %d, new rc %d)" % (res["old"][0], res["new"][0]))
    else:
        A, Bc = sqlite3.connect(res["old"][1]), sqlite3.connect(res["new"][1])
        tabs = sorted(r[0] for r in A.execute("SELECT name FROM sqlite_master WHERE type='table'"))
        if tabs != sorted(r[0] for r in Bc.execute("SELECT name FROM sqlite_master WHERE type='table'")):
            bad.append("the table lists differ")
        for t in tabs:
            if t in ("sp_meta", "sp_finding", "sp_gate"):
                continue
            if sorted(map(tuple, A.execute("SELECT * FROM %s" % t))) != sorted(map(tuple, Bc.execute("SELECT * FROM %s" % t))):
                bad.append("%s differs" % t)
        ma = {k: v for k, v in A.execute("SELECT * FROM sp_meta") if k not in ("built", "build_version")}
        mb = {k: v for k, v in Bc.execute("SELECT * FROM sp_meta") if k not in ("built", "build_version")}
        if ma != mb:
            bad.append("sp_meta differs beyond built / build_version")
        fa = sorted(map(tuple, A.execute("SELECT as_on, k20, diff, note FROM sp_finding")))
        fb = sorted(map(tuple, Bc.execute("SELECT as_on, k20, diff, note FROM sp_finding")))
        if [f[:3] for f in fa] != [f[:3] for f in fb]:
            bad.append("the findings themselves differ (not only their notes)")
        moved = [(x, y) for x, y in zip(fa, fb) if x[3] != y[3]]
        if any(not y[3].startswith("VOUCHER") for x, y in moved):
            bad.append("a note changed to something other than VOUCHER")
        # every VOUCHER equal to the vouchers filed, worked out again here by plain SQL (the newest row, a number, not void)
        F = sqlite3.connect("file:%s?mode=ro" % a.findb, uri=True)
        stt = {}
        for cid, r, k, b, v, e, at in F.execute("SELECT count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, at FROM stock_voucher_entered ORDER BY id"):
            stt[(cid, r, k, b)] = v
        void = {tuple(x) for x in F.execute("SELECT count_id, round_no, kind, batch_no FROM stock_voucher_void")} if F.execute("SELECT 1 FROM sqlite_master WHERE name='stock_voucher_void'").fetchone() else set()
        net = collections.Counter()
        for cid, r, k, b, item, ch in F.execute("SELECT count_id, round_no, kind, batch_no, item, change FROM stock_voucher_line"):
            if str(stt.get((cid, r, k, b)) or "").strip() and (cid, r, k, b) not in void:
                net[" ".join(str(item).split())[:20].strip()] += ch
        F.close()
        last = (dict(A.execute("SELECT key, value FROM sp_meta").fetchall()).get("checkable") or "").split(",")[-1]
        vo = [y for x, y in moved if y[0] == last]
        off = [y[1] for y in vo if abs(net.get(y[1], 0) - y[2]) >= 0.5]
        if off:
            say("  --  %d VOUCHER item(s) whose figure is not the plain net of their filed vouchers (an alias or a family key): %s" % (len(off), off[:6]))
        open_old = {f[1] for f in fa if f[0] == last and f[3].startswith("OPEN")}
        if not vo and any(abs(net.get(k, 0)) >= 0.5 for k in open_old):
            bad.append("the filed vouchers explained nothing, though %d open item(s) carry a filed net change" % sum(1 for k in open_old if abs(net.get(k, 0)) >= 0.5))
        ga = list(A.execute("SELECT name, blocking, ok FROM sp_gate ORDER BY n"))
        gb = list(Bc.execute("SELECT name, blocking, ok FROM sp_gate ORDER BY n"))
        if ga != gb:
            bad.append("the gate rows differ in name, blocking or ok")
        oa = sum(1 for f in fa if f[0] == last and f[3].startswith("OPEN"))
        ob = sum(1 for f in fb if f[0] == last and f[3].startswith("OPEN"))
        nv = sum(1 for f in fb if f[0] == last and f[3].startswith("VOUCHER"))
        say("  --  the latest checkable closing %s: OPEN %d (old) -> %d (new); VOUCHER %d; every other table and gate row the same" % (last, oa, ob, nv))
        sys.path.insert(0, os.path.join(a.new, "finance", "spine"))
        from spine_read import Spine
        say("  --  new status: %s" % Spine(res["new"][1]).status()[:300])
        res["spine_line"] = "spine OPEN %d -> %d, VOUCHER %d" % (oa, ob, nv)
    # ---- the order engine and the fold, old against new, on the COPY (never the live database)
    if a.db:
        for p in (os.path.join(a.new, "finance", "spine"), os.path.join(a.new, "finance")):
            if p not in sys.path:
                sys.path.insert(0, p)
        Oo = load("order_rules_old", os.path.join(a.old_root, "finance", "order_rules.py"))
        On = load("order_rules_new", os.path.join(a.new, "finance", "order_rules.py"))

        def P(mod):
            c = sqlite3.connect(a.db, timeout=60)
            c.row_factory = sqlite3.Row
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    d = mod.plan(c)
                return d, mod._s644_on(c)
            finally:
                c.close()
        p0, on = P(Oo)
        p1, _ = P(On)
        p2, _ = P(Oo)
        word = "levels" if on else "fixed"

        def lines(d):
            return {(vn, l["item"]): l for vn, v in (d.get("vendors") or {}).items() for l in v.get("lines") or []}
        L0, L1, L2 = lines(p0), lines(p1), lines(p2)
        steady = {k for k in L0 if k in L2 and L0[k] == L2[k]}
        given = 0
        if set(L0) != set(L1):
            bad.append("plan(): the set of lines differs old / new")
        for k in steady & set(L1):
            o, n = dict(L0[k]), dict(L1[k])
            if "model" not in o and n.get("model") == word:
                n.pop("model")
                given += 1
            if o != n:
                bad.append("plan(): line %s differs beyond its model word" % (k[1][:20],))
                break
        tot = lambda d: {vn: (v.get("total_p"), v.get("held"), v.get("paused")) for vn, v in (d.get("vendors") or {}).items()}
        if tot(p0) != tot(p1) and tot(p0) == tot(p2):
            bad.append("plan(): a supplier's total / held / paused differs")
        say("  --  plan() on the copy (%s): %d suppliers, %d lines; old = new on every steady line; %d carried line(s) given '%s'; %d line(s) moved on their own between two old runs"
            % (word, len(p0.get("vendors") or {}), len(L0), given, word, len(L0) - len(steady)))

        def Ow(mod):
            c = sqlite3.connect(a.db, timeout=60)
            c.row_factory = sqlite3.Row
            try:
                return mod.owner_state(c).get("model") or {}
            finally:
                c.close()
        mo, mn = Ow(Oo), Ow(On)
        if mo.get("error") or mn.get("error"):
            bad.append("the fold errs (old %s / new %s)" % (mo.get("error"), mn.get("error")))
        for k in set(mo) | set(mn):
            if k in ("inputs", "relist", "stale", "score"):
                continue
            if mo.get(k) != mn.get(k):
                bad.append("the fold's %s differs" % k)
        for s in ("relist", "stale"):
            if (mo.get(s) is None) != (mn.get(s) is None):
                bad.append("the fold's %s appears / vanishes" % s)
            elif mn.get(s) and "{" in str(mn[s].get("text")):
                bad.append("the fold's %s line still carries raw JSON" % s)
        say("  --  the fold old vs new: the same but for inputs / relist / stale words; relist now: %s" % (str((mn.get("relist") or {}).get("text"))[:160],))
    line = "proof: old vs new on the live readings and a copy of the database . %s . %s" % ("CLEAN" if not bad else "RED: " + "; ".join(bad[:6]), res.get("spine_line", "spine not built"))
    print(line)
    return 0 if not bad else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new")
    ap.add_argument("--old")
    ap.add_argument("--scratch", default="")
    ap.add_argument("--proof", action="store_true")
    ap.add_argument("--old-root")
    ap.add_argument("--readings")
    ap.add_argument("--rules", default="")
    ap.add_argument("--findb")
    ap.add_argument("--db")
    a = ap.parse_args()
    scratch = a.scratch or tempfile.mkdtemp(prefix="s704w_")
    os.makedirs(scratch, exist_ok=True)
    if a.proof:
        return proof(a)
    root = a.new or a.old
    spine_checks(root, scratch)
    fold_checks(root, scratch)
    for kind, name, ok, det in RES:
        if not ok:
            print("  RED  [%s] %s -- %s" % (kind, name, str(det)[:200]))
    s7 = [r for r in RES if r[0] == "S704"]
    rg = [r for r in RES if r[0] == "REG"]
    if a.new:
        g = sum(1 for r in RES if r[2])
        print("%d of %d green" % (g, len(RES)))
        return 0 if g == len(RES) else 1
    print("%d S704 check(s) red . %d green" % (sum(1 for r in s7 if not r[2]), sum(1 for r in RES if r[2])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
