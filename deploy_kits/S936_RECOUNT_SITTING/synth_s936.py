#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""synth_s936_v1.py -- kit S936_RECOUNT_SITTING (23-Nov-2026, Sanjeevni session 506). MADE-UP data only, in a scratch folder.
    python3 -B synth_s936_v1.py <dir with the files under test (a copy of /root/finance)> <schema-from: a COPY of finance.db> [--control] [--keep]
A finance.db with the copy's schema and NO rows of its own; two made-up spines (spine_build.SCHEMA) -- before / with the count day's sale report.
The recount rule (R1-R20) and one bill per sitting (S1-S8), the routes and the page (P1-P5). --control runs the SAME checks on the OLD files and
must go red. No patient data anywhere. Prints 'RESULT: ...'."""
import datetime as dt
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import time

RUN, FAILS = [0], []


def say(s):
    print(re.sub(r"\d{8,}", lambda m: "#" * len(m.group(0)), str(s)), flush=True)


def check(label, cond, got=None):
    RUN[0] += 1
    say(("ok   " if cond else "FAIL ") + label + (("  [%s]" % str(got)[:300]) if (got is not None and not cond) else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def attempt(label, fn):
    try:
        return fn()
    except Exception as e:                                    # noqa: BLE001
        check(label + " (raised %s: %s)" % (type(e).__name__, str(e)[:160]), False)
        return None


def schema_from(copy, path):
    src = sqlite3.connect("file:%s?mode=ro" % copy, uri=True)
    dst = sqlite3.connect(path)
    for (sql,) in src.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' ORDER BY CASE type WHEN 'table' THEN 0 ELSE 1 END, name"):
        try:
            dst.execute(sql)
        except sqlite3.Error:
            pass
    dst.commit()
    src.close()
    return dst


os.environ["TZ"] = "Asia/Kolkata"
time.tzset()
TODAY = dt.date.today()
D = TODAY.isoformat()
Y = (TODAY - dt.timedelta(days=1)).isoformat()
Z = (TODAY - dt.timedelta(days=2)).isoformat()
OLD9 = (TODAY - dt.timedelta(days=9)).isoformat()
OLD8 = (TODAY - dt.timedelta(days=8)).isoformat()
T1D = (TODAY + dt.timedelta(days=1)).isoformat()
CAP = "W936CAP00000000000000000000000001"
NAMES = ("W936 CART 10", "W936 LOSS 10", "W936 OLD 10", "W936 RE 10", "W936 RE2 10", "W936 GAD 10", "W936 ROST 10", "W936 SMALL 10",
         "W936 BILL 10", "W936 S1 10", "W936 S2 10", "W936 S3 10", "W936 ROUTE 10", "W936 X1 10", "W936 X2 10", "W936 PRE 10", "W936 SAME 10", "W936 X3 10")
DELIVERED = ("W936 CART 10", "W936 RE 10", "W936 RE2 10", "W936 GAD 10", "W936 ROST 10", "W936 SMALL 10", "W936 BILL 10", "W936 X1 10", "W936 X2 10", "W936 X3 10")


def make_spine(fin, path, with_day_sales):
    sys.path.insert(0, os.path.join(fin, "spine"))
    import spine_build as SB                                  # noqa: E402
    sys.path.pop(0)
    sys.modules.pop("spine_build", None)
    sp = sqlite3.connect(path)
    sp.executescript(SB.SCHEMA)
    sp.execute("INSERT INTO sp_meta VALUES ('built', ?)", ((D if with_day_sales else Y) + "T08:00:00+05:30",))
    E = "INSERT INTO sp_export VALUES (?,?,?,?,?,?,?,?,?,?,?)"
    sp.execute(E, (CAP, "closing", "STOCK_CLOSING", Y.replace("-", "") + "-093000", None, None, Z, 1, None, "closing", "walk"))
    sp.execute(E, ("W936SALE", "sale", "SALE_BILLWISE", ((T1D if with_day_sales else D).replace("-", "") + "-074000"), "2026-11-01", (D if with_day_sales else Y), None, 1, None, "sale", "walk"))
    for name in NAMES:
        k = name[:20]
        sp.execute("INSERT INTO sp_item VALUES (?,?,?,?,?,?)", (k, name, "1*10", "strip", "2026-09-01", Z))
        sp.execute("INSERT INTO sp_close_name VALUES (?,?,?,?,?)", (CAP, name, "1*10", k, 100.0))
        sp.execute("INSERT INTO sp_close VALUES (?,?,?,?)", (Z, k, 100.0, CAP))
        sp.execute("INSERT INTO sp_move VALUES (?,?,?,?,?)", (k, "2026-11-01", "OPENING", 100.0, "OPEN"))
        sp.execute("INSERT INTO sp_item_fact VALUES (?,?,?,?,?,?)", (name, "1*10", "mrp", "120.00", Z, "walk"))   # Rs 120 a strip
        if name in DELIVERED or name in ("W936 OLD 10", "W936 PRE 10", "W936 SAME 10"):   # the delivery is in Marg's purchases (as TRAMATEE's bill 502 was by 22-11)
            dd = OLD8 if name == "W936 OLD 10" else (Z if name == "W936 PRE 10" else Y)
            sk, bill = ("W936OLDP", "A000417") if name == "W936 OLD 10" else ("W936PHAR", "502")
            sp.execute("INSERT INTO sp_move VALUES (?,?,?,?,?)", (k, dd, "PURCHASE", 300.0, sk + "/" + bill))
            sp.execute("INSERT INTO sp_purchase_line VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (sk, bill, dd, 1, name[:27], k, "1*10", 30, 0, 300.0, 0, 0, "PURCHASE", "walk"))
    sp.commit()
    sp.close()


def main():
    fin, copy = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    control = "--control" in sys.argv
    scratch = tempfile.mkdtemp(prefix="s936_", dir=os.environ.get("TMPDIR") or "/tmp")
    try:
        run(fin, copy, control, scratch)
    finally:
        if "--keep" in sys.argv:
            say("KEPT %s" % scratch)
        else:
            shutil.rmtree(scratch, ignore_errors=True)
    say("RESULT: %s (%d checks)" % ("ALL PASS" if not FAILS else "%d FAIL" % len(FAILS), RUN[0]))
    sys.exit(0 if not FAILS else 1)


def run(fin, copy, control, scratch):
    dbp, sp1p, sp2p = os.path.join(scratch, "fin.db"), os.path.join(scratch, "spine1.db"), os.path.join(scratch, "spine2.db")
    con = schema_from(copy, dbp)
    make_spine(fin, sp1p, False)
    make_spine(fin, sp2p, True)
    os.environ.update(FINANCE_DB=dbp, SPINE_DB=sp1p, ASSETS_DB=os.path.join(scratch, "assets.db"), PYTHONDONTWRITEBYTECODE="1")
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [x for x in sys.path if os.path.abspath(x or ".") != here]
    sys.path.insert(0, fin)
    os.chdir(fin)
    import stock_watch as SW                                  # noqa: E402
    import stock_figure as SF                                 # noqa: E402
    import shelf_figure as SHF                                # noqa: E402
    assert SW.__file__.startswith(fin) and SF.__file__.startswith(fin), (SW.__file__, SF.__file__)
    say("-- S936 synth on the %s files: %s (stock_watch KIT %s) -- today %s" % ("OLD (control)" if control else "new", fin, SW.KIT, D))
    SW.ensure(con)
    con.execute("INSERT INTO mi_bill_chain (series, day, first_no, last_no, n_bills, gap_before, gap_inside, empty, source_md5, computed_at) VALUES ('A',?,4980,5000,21,'','',0,'walk',?)",
                (Y, Y + "T08:00:00"))
    nm = SW.norm_name
    for n in NAMES:
        at, q0 = (OLD9 + "T10:00:00", 100) if n == "W936 OLD 10" else ((Y + "T20:00:00", 400) if n in ("W936 PRE 10", "W936 SAME 10") else (Z + "T10:00:00", 100))
        con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, status) VALUES (?,?,?,?,?,?,?)", (nm(n), n, at, q0, "spot", "darpan", "settled"))
    con.execute("INSERT INTO purchase_order (id, created_at, created_by, vendor, status, supplier_norm, received_at) VALUES (938,?,?,?,?,?,?)",
                (Z + "T09:00:00", "walk", "W936 PREPHARMA", "received", "W936 PREPHARMA", Z + "T12:00:00"))
    con.execute("INSERT INTO purchase_order_line (id, order_id, item, packs, pack_size, units, supplied, arrived_at, arrived_by, billed_qty, billed_bill_no, billed_date) "
                "VALUES (9380,938,?,?,?,?,?,?,?,?,?,?)", ("W936 PRE 10", 30, 10, 300, 30, Z + "T12:00:00", "reception", 30, "A000418", Z))   # came BEFORE PRE's base count (Y 20:00, 400)
    con.execute("INSERT INTO purchase_order (id, created_at, created_by, vendor, status, supplier_norm, received_at) VALUES (936,?,?,?,?,?,?)",
                (Y + "T09:00:00", "walk", "W936 PHARMA", "received", "W936 PHARMA", Y + "T19:00:00"))
    con.execute("INSERT INTO purchase_order (id, created_at, created_by, vendor, status, supplier_norm, received_at) VALUES (937,?,?,?,?,?,?)",
                (OLD8 + "T09:00:00", "walk", "W936 OLDPHARMA", "received", "W936 OLDPHARMA", OLD8 + "T19:00:00"))
    lid = 9360
    for n in DELIVERED:
        lid += 1
        con.execute("INSERT INTO purchase_order_line (id, order_id, item, packs, pack_size, units, supplied, arrived_at, arrived_by, billed_qty, billed_bill_no, billed_date) "
                    "VALUES (?,936,?,?,?,?,?,?,?,?,?,?)", (lid, n, 30, 10, 300, 30, Y + "T19:00:00", "reception", 30, "502", Y))
    con.execute("INSERT INTO purchase_order_line (id, order_id, item, packs, pack_size, units, supplied, arrived_at, arrived_by, billed_qty, billed_bill_no, billed_date) "
                "VALUES (9399,937,?,?,?,?,?,?,?,?,?,?)", ("W936 OLD 10", 30, 10, 300, 30, OLD8 + "T19:00:00", "reception", 30, "A000417", OLD8))
    con.commit()
    sp1 = SW.Spine(sp1p)
    check("R0 the made-up spine reads", sp1.ok)
    cols = {r[1] for r in con.execute("PRAGMA table_info(stock_watch_ask)")}
    check("R0b ensure() adds stock_watch_ask.recount_of / why / why_hi", {"recount_of", "why", "why_hi"} <= cols, cols)
    S = SW.settings(con)
    check("R0c the three new settings read with their defaults (25%, 5 days, 60 minutes)", S.get("recount_tol_pct") == 25.0 and S.get("recount_days") == 5 and S.get("sitting_minutes") == 60,
          {k: S.get(k) for k in ("recount_tol_pct", "recount_days", "sitting_minutes")})

    def shelf_of(n, sp=sp1):
        return SF.shelf(con, sp, n, None, SF.Ctx(con, sp))

    def order_view(n, sp=sp1):
        F = SHF.figures(con, sp=sp, items=[n], ctx=SF.Ctx(con, sp)).get(n) or {}
        return dict(shelf=F.get("shelf"), base=F.get("base"), base_at=F.get("base_at"))

    sh0 = shelf_of("W936 CART 10")
    ov0 = order_view("W936 CART 10")
    check("R0d CART before the count: the shelf = the count of Z (100) + 30 strips tapped yesterday = 400", sh0.get("shelf") == 400 and sh0.get("base") == 100, sh0)
    leak0 = attempt("R0e month_leak", lambda: SW.month_leak(con, D[:7], S, sp1)) or {}

    # ---- CART: Darpan's 'Stock batao' 100 -- the carton of bill 502 not counted
    r = attempt("R1 darpan_point CART", lambda: SW.darpan_point(con, "W936 CART 10", 100, "darpan", sp=sp1))
    p = con.execute("SELECT id, status, expected_units, gap_units, note FROM stock_point WHERE item='W936 CART 10' ORDER BY id DESC LIMIT 1").fetchone()
    check("R1 CART counted 100 against 400: the point is HELD (status 'recount'), its gap kept (-300), its note says why (bill 502, not a loss)",
          bool(p) and p[1] == "recount" and p[3] == -300 and "held for a recount" in (p[4] or "") and "bill 502" in (p[4] or ""), p)
    check("R1b Darpan's reply says it is held and the recount comes on Abhi ginti, naming bill 502", bool(r) and r[0] and "Dobara ginti" in (r[1] or "") and "502" in (r[1] or ""), r)
    ll = con.execute("SELECT COUNT(*) FROM stock_watch_loss_line WHERE item='W936 CART 10'").fetchone()[0]
    tr = con.execute("SELECT COUNT(*) FROM stock_trace WHERE item='W936 CART 10'").fetchone()[0]
    check("R2 no loss line, no trace", ll == 0 and tr == 0, (ll, tr))
    a = con.execute("SELECT id, mode, by, recount_of, why_hi, done_at FROM stock_watch_ask WHERE item='W936 CART 10' ORDER BY id DESC LIMIT 1").fetchone() if "recount_of" in cols else None
    check("R3 ONE Count-now ask opened by itself: mode now, by system, recount_of the held point, the Hindi question names bill 502, open",
          bool(a) and a[1] == "now" and a[2] == "system" and bool(p) and a[3] == p[0] and "502" in (a[4] or "") and a[5] is None, a)
    sh1 = shelf_of("W936 CART 10")
    ov1 = order_view("W936 CART 10")
    check("R4 the held count is NOT the shelf base: stock_figure.shelf still stands on the count of Z (100) and reads 400", sh1.get("base") == 100 and sh1.get("shelf") == 400 and
          str(sh1.get("base_at") or "").startswith(Z), sh1)
    check("R5 the order engine's door (shelf_figure.figures) sees exactly what it saw before the count", ov1 == ov0, (ov0, ov1))
    leak1 = attempt("R6 month_leak", lambda: SW.month_leak(con, D[:7], S, sp1)) or {}
    check("R6 the month's leakage does not count the held shortfall", leak1.get("points_p") == leak0.get("points_p"), (leak0.get("points_p"), leak1.get("points_p")))
    nv = attempt("R7 now_view", lambda: SW.now_view(con, sp1, "darpan")) or {}
    it = [x for x in nv.get("items", []) if x["item"] == "W936 CART 10"]
    check("R7 Darpan's Abhi ginti card carries CART as a recount with its question", bool(it) and it[0].get("recount") is True and "502" in (it[0].get("why_hi") or ""), nv)
    line = con.execute("SELECT text FROM stock_watch_notice WHERE kind='count_day' AND once_key=?", ("counted:%s" % D,)).fetchone()
    check("R8 the day's line on his Needs-you says CART is held for a recount, not a loss", bool(line) and "W936 CART 10" in line[0] and "held for a recount" in line[0], line)
    lp = SW.last_point(con, nm("W936 CART 10"))
    check("R8b last_point() never picks the held count", bool(lp) and lp["id"] != (p[0] if p else -1), lp)

    # ---- the controls: not a delivery, an old delivery, a small short, his gadbad
    attempt("R9 LOSS", lambda: SW.darpan_point(con, "W936 LOSS 10", 40, "darpan", sp=sp1))
    p = con.execute("SELECT status, gap_units FROM stock_point WHERE item='W936 LOSS 10' ORDER BY id DESC LIMIT 1").fetchone()
    ll = con.execute("SELECT COUNT(*) FROM stock_watch_loss_line WHERE item='W936 LOSS 10'").fetchone()[0]
    check("R9 LOSS (no delivery at all): 60 short is a loss line by name, as before -- never held", bool(p) and p[0] != "recount" and p[1] == -60 and ll == 1, (p, ll))
    attempt("R10 OLD", lambda: SW.darpan_point(con, "W936 OLD 10", 100, "darpan", sp=sp1))
    p = con.execute("SELECT status, gap_units FROM stock_point WHERE item='W936 OLD 10' ORDER BY id DESC LIMIT 1").fetchone()
    ll = con.execute("SELECT COUNT(*) FROM stock_watch_loss_line WHERE item='W936 OLD 10'").fetchone()[0]
    check("R10 OLD (its 30 strips came 8 days ago, past the 5-day window): 300 short is a loss line -- never held", bool(p) and p[0] != "recount" and p[1] == -300 and ll == 1, (p, ll))
    attempt("R11 SMALL", lambda: SW.darpan_point(con, "W936 SMALL 10", 395, "darpan", sp=sp1))
    p = con.execute("SELECT status, gap_units FROM stock_point WHERE item='W936 SMALL 10' ORDER BY id DESC LIMIT 1").fetchone()
    check("R11 SMALL (5 tabs short, inside the allowance): not held", bool(p) and p[0] != "recount" and p[1] == -5, p)
    attempt("R12 GAD", lambda: SW.gadbad(con, "W936 GAD 10", "kam lag raha hai", "darpan", qty_units=100, sp=sp1))
    p = con.execute("SELECT status, gap_units FROM stock_point WHERE item='W936 GAD 10' ORDER BY id DESC LIMIT 1").fetchone()
    check("R12 GAD: Darpan's own flag ('Kuchh gadbad hai') is never held -- the trace runs as before", bool(p) and p[0] != "recount" and p[1] == -300, p)

    # ---- RE: held, then the recount agrees
    attempt("R13 RE first", lambda: SW.darpan_point(con, "W936 RE 10", 100, "darpan", sp=sp1))
    held = con.execute("SELECT id, status FROM stock_point WHERE item='W936 RE 10' ORDER BY id DESC LIMIT 1").fetchone()
    ra = con.execute("SELECT id FROM stock_watch_ask WHERE item='W936 RE 10' AND done_at IS NULL").fetchone()
    check("R13 RE held, its recount open", bool(held) and held[1] == "recount" and bool(ra), (held, ra))
    ok = attempt("R14 recount RE", lambda: SW.answer_now(con, ra[0] if ra else 0, 400, "", "darpan", sp=sp1, no_bill=True))
    p = con.execute("SELECT id, status, gap_units FROM stock_point WHERE item='W936 RE 10' ORDER BY id DESC LIMIT 1").fetchone()
    h2 = con.execute("SELECT status, note FROM stock_point WHERE id=?", (held[0] if held else 0,)).fetchone()
    a2 = con.execute("SELECT done_at, closed_how FROM stock_watch_ask WHERE id=?", (ra[0] if ra else 0,)).fetchone()
    more = con.execute("SELECT COUNT(*) FROM stock_watch_ask WHERE item='W936 RE 10' AND done_at IS NULL").fetchone()[0]
    check("R14 the recount (400, the carton found) is judged against the base before the held count: gap 0, judged (settled, or provisional while Marg lacks the bill)",
          bool(ok) and ok[0] and bool(p) and p[2] == 0 and p[1] in ("settled", "provisional"), (ok, p))
    check("R15 the held count becomes 'recounted' (its note says so); the recount ask is closed as counted; nothing open for RE", bool(h2) and h2[0] == "recounted" and "recounted" in (h2[1] or "")
          and bool(a2) and a2[0] and a2[1] == "counted" and more == 0, (h2, a2, more))
    sh = shelf_of("W936 RE 10")
    check("R16 RE's shelf now stands on the recount (400)", sh.get("base") == 400 and sh.get("shelf") == 400, sh)

    # ---- RE2: held, the recount short again -> a loss by name, never held twice
    attempt("R17 RE2 first", lambda: SW.darpan_point(con, "W936 RE2 10", 100, "darpan", sp=sp1))
    attempt("R17 RE2 recount by Stock batao", lambda: SW.darpan_point(con, "W936 RE2 10", 100, "darpan", sp=sp1))
    p = con.execute("SELECT status, gap_units FROM stock_point WHERE item='W936 RE2 10' ORDER BY id DESC LIMIT 1").fetchone()
    ll = con.execute("SELECT COUNT(*) FROM stock_watch_loss_line WHERE item='W936 RE2 10' AND void_at IS NULL").fetchone()[0]
    st = [r[0] for r in con.execute("SELECT status FROM stock_point WHERE item='W936 RE2 10' AND source='darpan' ORDER BY id")]
    more = con.execute("SELECT COUNT(*) FROM stock_watch_ask WHERE item='W936 RE2 10' AND done_at IS NULL").fetchone()[0]
    check("R17 RE2: the second count (any door) answers the recount; still 300 short -> a loss line by name, not held again, no new recount",
          bool(p) and p[0] != "recount" and p[1] == -300 and ll == 1 and st == ["recounted", p[0]] and more == 0, (p, ll, st, more))
    leak2 = attempt("R17b month_leak", lambda: SW.month_leak(con, D[:7], S, sp1)) or {}
    check("R17b the confirmed loss does reach the month's leakage (the control of R6)", (leak2.get("points_p") or 0) > (leak1.get("points_p") or 0), (leak1.get("points_p"), leak2.get("points_p")))

    # ---- ROST: a morning-list answer held, then corrected the same day
    con.execute("INSERT INTO stock_spot_roster (day, item_norm, item, reason, reason_hi, rank, asked_at, pack, packing, carried) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (D, nm("W936 ROST 10"), "W936 ROST 10", "walk", "", 1, D + "T07:00:00", 10, "1*10", 0))
    con.commit()
    rid = con.execute("SELECT id FROM stock_spot_roster WHERE item='W936 ROST 10'").fetchone()[0]
    attempt("R18 answer_roster ROST", lambda: SW.answer_roster(con, rid, 100, "darpan", sp=sp1))
    p = con.execute("SELECT id, status FROM stock_point WHERE item='W936 ROST 10' ORDER BY id DESC LIMIT 1").fetchone()
    ra = con.execute("SELECT id FROM stock_watch_ask WHERE item='W936 ROST 10' AND done_at IS NULL AND recount_of IS NOT NULL").fetchone() if "recount_of" in cols else None
    check("R18 a morning-list answer short by the delivery is held too, its recount open (after the list closed its own asks)", bool(p) and p[1] == "recount" and bool(ra), (p, ra))
    fx = attempt("R19 correct_roster ROST", lambda: SW.correct_roster(con, rid, 400, "darpan", sp=sp1))
    p2 = con.execute("SELECT status, gap_units FROM stock_point WHERE item='W936 ROST 10' ORDER BY id DESC LIMIT 1").fetchone()
    a2 = con.execute("SELECT closed_how FROM stock_watch_ask WHERE id=?", (ra[0] if ra else 0,)).fetchone()
    more = con.execute("SELECT COUNT(*) FROM stock_watch_ask WHERE item='W936 ROST 10' AND done_at IS NULL").fetchone()[0]
    check("R19 'Galat likha? Badlo' to 400: the held count superseded, its recount WITHDRAWN (not answered by the correction), the correction judged gap 0",
          bool(fx) and fx[0] and bool(p2) and p2[1] == 0 and bool(a2) and a2[0] == "withdrawn" and more == 0, (fx, p2, a2, more))

    # ---- BILL: a Count now placed to the bill, judged when the sales are in -> held then
    attempt("R20 ask BILL now", lambda: SW.ask(con, "W936 BILL 10", "manoj", sp=sp1, mode="now"))
    ba = con.execute("SELECT id FROM stock_watch_ask WHERE item='W936 BILL 10' AND done_at IS NULL").fetchone()
    attempt("R20 answer BILL", lambda: SW.answer_now(con, ba[0], 100, "5002", "darpan", sp=sp1))
    sp2 = SW.Spine(sp2p)
    attempt("R20 settle", lambda: SW._s934_settle(con, sp2))
    p = con.execute("SELECT status, gap_units, note FROM stock_point WHERE item='W936 BILL 10' ORDER BY id DESC LIMIT 1").fetchone()
    ra = con.execute("SELECT recount_of FROM stock_watch_ask WHERE item='W936 BILL 10' AND done_at IS NULL").fetchone() if "recount_of" in cols else None
    ll = con.execute("SELECT COUNT(*) FROM stock_watch_loss_line WHERE item='W936 BILL 10'").fetchone()[0]
    check("R20 a bill-placed count judged 300 short once the day's sales are in: held (no loss line), its note keeps 'Count now, to bill 5002' first, a recount opened",
          bool(p) and p[0] == "recount" and p[1] == -300 and (p[2] or "").startswith("Count now, to bill 5002") and "held for a recount" in (p[2] or "") and ll == 0 and bool(ra) and ra[0],
          (p, ll, ra))

    # ---- the cold review's scenarios (S506)
    attempt("R21 PRE", lambda: SW.darpan_point(con, "W936 PRE 10", 100, "darpan", sp=sp1))
    p = con.execute("SELECT status, gap_units FROM stock_point WHERE item='W936 PRE 10' ORDER BY id DESC LIMIT 1").fetchone()
    ll = con.execute("SELECT COUNT(*) FROM stock_watch_loss_line WHERE item='W936 PRE 10'").fetchone()[0]
    check("R21 PRE: its 30 strips came BEFORE the base count (which counted them): 300 short is a loss line, never held (review finding 7)",
          bool(p) and p[0] != "recount" and p[1] == -300 and ll == 1, (p, ll))
    attempt("R22 X1 first", lambda: SW.darpan_point(con, "W936 X1 10", 100, "darpan", sp=sp1))
    held = con.execute("SELECT id, status FROM stock_point WHERE item='W936 X1 10' ORDER BY id DESC LIMIT 1").fetchone()
    con.execute("INSERT INTO stock_spot_roster (day, item_norm, item, reason, reason_hi, rank, asked_at, pack, packing, carried) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (D, nm("W936 X1 10"), "W936 X1 10", "walk", "", 2, D + "T07:00:00", 10, "1*10", 0))
    con.commit()
    xr = con.execute("SELECT id FROM stock_spot_roster WHERE item='W936 X1 10'").fetchone()[0]
    attempt("R22 X1 answered on the morning list", lambda: SW.answer_roster(con, xr, 100, "darpan", sp=sp1))
    b = con.execute("SELECT id, status FROM stock_point WHERE item='W936 X1 10' ORDER BY id DESC LIMIT 1").fetchone()
    attempt("R22 X1 corrected", lambda: SW.correct_roster(con, xr, 110, "darpan", sp=sp1))
    c = con.execute("SELECT id, status, gap_units FROM stock_point WHERE item='W936 X1 10' ORDER BY id DESC LIMIT 1").fetchone()
    rf = con.execute("SELECT recount_for FROM stock_point WHERE id=?", (c[0] if c else 0,)).fetchone() if "recount_for" in {r[1] for r in con.execute("PRAGMA table_info(stock_point)")} else None
    more = con.execute("SELECT COUNT(*) FROM stock_watch_ask WHERE item='W936 X1 10' AND done_at IS NULL").fetchone()[0]
    check("R22 X1: held; the morning list answers the recount (still short: a loss); its same-day correction (290 short) is NEVER held again, carries the recount it answers, opens nothing (review finding 2)",
          bool(held) and held[1] == "recount" and bool(b) and b[1] != "recount" and bool(c) and c[1] != "recount" and c[2] == -290 and bool(rf) and rf[0] == held[0] and more == 0,
          (held, b, c, rf, more))

    attempt("R24 SAME", lambda: SW.darpan_point(con, "W936 SAME 10", 100, "darpan", sp=sp1))
    p = con.execute("SELECT status, gap_units FROM stock_point WHERE item='W936 SAME 10' ORDER BY id DESC LIMIT 1").fetchone()
    check("R24 SAME: its Marg purchase is dated the base count's own day (the evening count of Y saw it): 300 short is never held (review 2, MUST 2)",
          bool(p) and p[0] != "recount" and p[1] == -300, p)
    attempt("R25 ask X3 next", lambda: SW.ask(con, "W936 X3 10", "manoj", sp=sp1, mode="next"))
    attempt("R25 X3 Stock batao", lambda: SW.darpan_point(con, "W936 X3 10", 100, "darpan", sp=sp1))
    nt = con.execute("SELECT COUNT(*) FROM stock_watch_notice WHERE kind='asked_count' AND text LIKE '%W936 X3 10%'").fetchone()[0]
    op = con.execute("SELECT id, mode, recount_of FROM stock_watch_ask WHERE item='W936 X3 10' AND done_at IS NULL").fetchall()
    check("R25 X3: his Next-list ask is answered with his 'you asked' line (review 2, finding 3); one card left, the recount, on Count now",
          nt == 1 and len(op) == 1 and op[0][1] == "now" and op[0][2] is not None, (nt, op))
    k = attempt("R26 ask X3 next again", lambda: SW.ask(con, "W936 X3 10", "manoj", sp=sp1, mode="next"))
    op2 = con.execute("SELECT mode, why_hi FROM stock_watch_ask WHERE item='W936 X3 10' AND done_at IS NULL").fetchall()
    w = attempt("R26 withdraw the recount", lambda: SW.withdraw_ask(con, op[0][0] if op else 0, "manoj"))
    check("R26 his Count this on an item with an open recount leaves the recount on Abhi ginti with its question; withdrawing a recount is refused (409)",
          bool(k) and k[0] and "recount" in k[1] and len(op2) == 1 and op2[0][0] == "now" and "bill" in (op2[0][1] or "") and bool(w) and not w[0] and w[2] == 409, (k, op2, w))
    st = con.execute("SELECT value FROM setting WHERE key='count._s936_held_at'").fetchone()
    check("R27 a hold touches the count.% row the stock of record's fingerprint reads (review 2, finding 5)", bool(st) and st[0], st)

    # ---- one bill per sitting (D1047) -- the BILL count above was darpan's, to 5002, just now
    for n in ("W936 S1 10", "W936 S2 10", "W936 S3 10"):
        attempt("S0 ask " + n, lambda n=n: SW.ask(con, n, "manoj", sp=sp1, mode="now"))
    ids = {r[1]: r[0] for r in con.execute("SELECT id, item FROM stock_watch_ask WHERE done_at IS NULL AND item LIKE 'W936 S_ 10'")}
    nv = attempt("S1 now_view darpan", lambda: SW.now_view(con, sp1, "darpan")) or {}
    nv2 = attempt("S1 now_view amir", lambda: SW.now_view(con, sp1, "amir")) or {}
    check("S1 the sitting's bill: Darpan's card carries 5002 (his Count now of a minute ago); another person's card none; the minutes (60) ride along",
          nv.get("sitting_bill") == 5002 and nv2.get("sitting_bill") is None and nv.get("sitting_minutes") == 60, (nv.get("sitting_bill"), nv2.get("sitting_bill"), nv.get("sitting_minutes")))
    check("S1b ... with the seconds since that bill was keyed (the page keeps the sitting's clock from it, review 2 MUST 1)",
          isinstance(nv.get("sitting_age_s"), int) and 0 <= nv["sitting_age_s"] < 600, nv.get("sitting_age_s"))
    o1 = attempt("S2 answer S1 with no bill typed", lambda: SW.answer_now(con, ids.get("W936 S1 10"), 100, "", "darpan", sp=sp1))
    p = con.execute("SELECT status, last_bill, note FROM stock_point WHERE item='W936 S1 10' ORDER BY id DESC LIMIT 1").fetchone()
    check("S2 an item saved with no bill in the sitting takes the sitting's bill (5002): placed to it, his reply says 'is baithak ka bill 5002'",
          bool(o1) and o1[0] and bool(p) and p[0] == "awaits_sales" and p[1] == "5002" and "is baithak ka bill 5002" in (o1[1] or ""), (o1, p))
    o2 = attempt("S3 answer S2 with no_bill", lambda: SW.answer_now(con, ids.get("W936 S2 10"), 100, "", "darpan", sp=sp1, no_bill=True))
    p = con.execute("SELECT status, last_bill FROM stock_point WHERE item='W936 S2 10' ORDER BY id DESC LIMIT 1").fetchone()
    check("S3 after 'Sale hui?' the page sends no_bill: the count is placed by its time (no bill), as before", bool(o2) and o2[0] and bool(p) and p[0] != "awaits_sales" and p[1] is None
          and "samay se" in (o2[1] or ""), (o2, p))
    old = (dt.datetime.now() - dt.timedelta(minutes=90)).replace(microsecond=0).isoformat()
    if old[:10] == D:
        con.execute("UPDATE stock_point SET at=? WHERE by='darpan' AND last_bill IS NOT NULL", (old,))
        con.commit()
        sb = attempt("S4 sitting after 90 min", lambda: SW._s936_sitting_bill(con, "darpan"))
        check("S4 90 minutes later the sitting is over: no sitting bill (a new sitting asks again)", sb is None, sb)
    else:
        say("skip S4 (90 minutes ago is yesterday)")
    o3 = attempt("S5 a typed bill still wins", lambda: SW.answer_now(con, ids.get("W936 S3 10"), 100, "5003", "darpan", sp=sp1))
    p = con.execute("SELECT last_bill FROM stock_point WHERE item='W936 S3 10' ORDER BY id DESC LIMIT 1").fetchone()
    check("S5 a bill typed with the item is used as typed (5003)", bool(o3) and o3[0] and bool(p) and p[0] == "5003", (o3, p))
    sb = attempt("S6 sitting now", lambda: SW._s936_sitting_bill(con, "darpan"))
    check("S6 ... and that is now the sitting's bill", sb == 5003, sb)

    # X2: his own Count now open when Darpan's count is held -- one card, the recount; answered to a bill; never held again at the settle
    attempt("R23 ask X2 now", lambda: SW.ask(con, "W936 X2 10", "manoj", sp=sp1, mode="now"))
    attempt("R23 X2 Stock batao", lambda: SW.darpan_point(con, "W936 X2 10", 100, "darpan", sp=sp1))
    op = con.execute("SELECT id, recount_of FROM stock_watch_ask WHERE item='W936 X2 10' AND done_at IS NULL").fetchall()
    check("R23 X2: one open card for the item after the hold -- the recount (his own ask is answered by the same count) (review finding 3)",
          len(op) == 1 and op[0][1] is not None, op)
    attempt("R23 X2 recount to a bill", lambda: SW.answer_now(con, op[0][0] if op else 0, 100, "5003", "darpan", sp=sp1))
    attempt("R23 settle", lambda: SW._s934_settle(con, SW.Spine(sp2p)))
    p = con.execute("SELECT status, gap_units FROM stock_point WHERE item='W936 X2 10' ORDER BY id DESC LIMIT 1").fetchone()
    ll = con.execute("SELECT COUNT(*) FROM stock_watch_loss_line WHERE item='W936 X2 10' AND void_at IS NULL").fetchone()[0]
    more = con.execute("SELECT COUNT(*) FROM stock_watch_ask WHERE item='W936 X2 10' AND done_at IS NULL").fetchone()[0]
    check("R23b the recount answered to bill 5003, judged at the settle 300 short again: a loss line by name -- never held twice, no new card",
          bool(p) and p[0] == "settled" and p[1] == -300 and ll == 1 and more == 0, (p, ll, more))

    # ---- the routes and the page
    import flask                                              # noqa: E402
    import stockmatch as SM                                   # noqa: E402
    app = flask.Flask("s936walk")
    SM._db = lambda: con
    SM._require = lambda *a, **k: (dict(user="darpan", roles=["maker"]), None)
    app.register_blueprint(SM.bp)
    cl = app.test_client()
    attempt("P0 ask ROUTE", lambda: SW.ask(con, "W936 ROUTE 10", "manoj", sp=sp1, mode="now"))
    rr = con.execute("SELECT id FROM stock_watch_ask WHERE item='W936 ROUTE 10' AND done_at IS NULL").fetchone()
    rv = cl.post("/finance/stockmatch/api/now", json=dict(ask_id=(rr[0] if rr else 0), strips=10, loose=0))
    j = rv.get_json(silent=True) or {}
    rp = con.execute("SELECT last_bill FROM stock_point WHERE item='W936 ROUTE 10' ORDER BY id DESC LIMIT 1").fetchone()
    check("P1 POST /finance/stockmatch/api/now with no bill and no 'no_bill' (a page from before the kit): takes the sitting's bill (5003)",
          rv.status_code == 200 and j.get("ok") and bool(rp) and rp[0] == "5003", (rv.status_code, str(j)[:160], rp))
    w = (attempt("P2 stockmatch._sw_view(con, 'darpan')", lambda: SM._sw_view(con, "darpan")) or {}).get("now") or {}
    w2 = (attempt("P2 _sw_view amir", lambda: SM._sw_view(con, "amir")) or {}).get("now") or {}
    check("P2 the state the page reads (stockmatch._sw_view with the person signed in) carries HIS sitting's bill (5003); another person's none",
          w.get("sitting_bill") == 5003 and w2.get("sitting_bill") is None, (w.get("sitting_bill"), w2.get("sitting_bill")))
    html = open(os.path.join(fin, "stockmatch.html"), encoding="utf-8").read()
    check("P3 the card: ONE bill box at the top (nbS), 'Sale hui? Naya bill likhiye', the bill shown on each line, no per-item bill box",
          'id="nbS"' in html and "Sale hui? Naya bill likhiye" in html and "sbShow" in html and "id=\"nb'+r.id" not in html, None)
    check("P4 the page sends no_bill after 'Sale hui?' and shows a recount's question (why_hi, 'dobara ginti'); no confirm() dialog",
          "body.no_bill=1" in html and "why_hi" in html and "dobara ginti" in html and "confirm(" not in html, None)
    check("P4b the bill on the phone expires with the sitting: never shown or sent once the sitting's minutes pass; Darpan is asked to type it again (review MUST 1)",
          "function sbFresh()" in html and "if(SB&&!sbFresh()) SB=''" in html and "if(v&&!sbFresh())" in html and "Aakhri bill dobara likhiye" in html
          and "NW.sitting_age_s" in html and "Date.now()-Math.max(0,(+age||0))*1000" in html, None)
    src = open(os.path.join(fin, "stock_figure.py"), encoding="utf-8").read()
    check("P5 stock_figure.points() leaves out 'recount' and 'recounted'", "NOT IN ('superseded','recount','recounted')" in src, None)


if __name__ == "__main__":
    main()
