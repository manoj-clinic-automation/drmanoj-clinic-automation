#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""liveshape_s934.py -- kit S934_COUNT_NOW (23-Nov-2026). On COPIES of the live databases (never the live files):
    python3 -B liveshape_s934.py <new dir> <old dir> <finance.db copy> <spine.db copy>
(1) the stock of record built with the OLD files and with the NEW files on two copies of the same database: every row identical (no live
count carries a last bill yet, so S934 must change no figure); (2) the new files on the copy: ensure() adds the columns, his open asks read
with their mode, Darpan's view carries an (empty or real) Abhi ginti card, the Stock check page's record() answers, _s934_settle judges
nothing (no point waits). Prints counts and item names only -- no patient data exists in these tables. 'RESULT: ALL PASS' or 'RESULT: n FAIL'."""
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

FAILS = []


def say(s):
    print(re.sub(r"\d{8,}", lambda m: "#" * len(m.group(0)), str(s)), flush=True)


def check(label, cond, got=None):
    say(("ok   " if cond else "FAIL ") + label + (("  [%s]" % str(got)[:300]) if (got is not None and not cond) else ""))
    if not cond:
        FAILS.append(label)


def side(fin, dbp, spp, out, new):
    os.environ.update(FINANCE_DB=dbp, SPINE_DB=spp, PYTHONDONTWRITEBYTECODE="1")
    sys.path[:] = [x for x in sys.path if os.path.abspath(x or ".") != os.path.dirname(os.path.abspath(__file__))]
    sys.path.insert(0, fin)
    os.chdir(fin)
    import stock_watch as SW                                  # noqa: E402
    import stock_figure as SF                                 # noqa: E402
    import stock_record as SR                                 # noqa: E402
    con = sqlite3.connect(dbp, timeout=60)
    sp = SW.Spine(spp)
    t = time.time()
    r = SR.build(con, sp, log=lambda s: None)
    took = round(time.time() - t, 1)
    rows, _M = SR.rows(con, sp, "never")
    keep = ("item", "marg_units", "shelf_units", "waiting_units", "gap_units", "state", "base_kind", "base_day", "marg_flag")
    res = dict(build=dict(ok=r.get("ok"), n=r.get("n"), errors=r.get("errors")), took=took,
               rows=sorted([{k: d.get(k) for k in keep} for d in rows], key=lambda d: d["item"]))
    if new:
        SW.ensure(con)                                        # the columns arrive with the first call into stock_watch, as on the box
        cols = {x[1] for x in con.execute("PRAGMA table_info(stock_watch_ask)")}
        pcols = {x[1] for x in con.execute("PRAGMA table_info(stock_point)")}
        res["cols"] = sorted((cols & {"mode", "closed_how"}) | (pcols & {"last_bill", "ask_id"}))
        res["open_asks"] = [dict(item=a, mode=m) for a, m in con.execute("SELECT item, COALESCE(mode,'next') FROM stock_watch_ask WHERE done_at IS NULL ORDER BY id")]
        dv = SW.darpan_view(con)
        res["darpan_view_ok"] = bool(dv.get("ok"))
        res["now_items"] = len(((dv.get("now") or {}).get("items")) or [])
        res["last_no"] = (dv.get("now") or {}).get("last_no")
        res["settled"] = SW._s934_settle(con, sp)
        import stock_check as SC                              # noqa: E402
        SC._db = lambda: con
        rec = SC.record(con)
        res["page_ok"] = bool(rec.get("ok"))
        res["page_asks"] = [dict(item=a.get("item"), mode=a.get("mode"), has_id=bool(a.get("id"))) for a in rec.get("asks") or []]
        res["page_counts"] = len(rec.get("counts") or [])
        res["page_look"] = (rec.get("totals") or {}).get("look")
    json.dump(res, open(out, "w"), default=str)


def main():
    if "--side" in sys.argv:
        a = sys.argv[sys.argv.index("--side") + 1:]
        side(a[0], a[1], a[2], a[3], a[4] == "new")
        return
    new, old, dbp, spp = [os.path.abspath(x) for x in sys.argv[1:5]]
    scr = tempfile.mkdtemp(prefix="ls934_", dir=os.environ.get("TMPDIR") or "/tmp")
    try:
        R = {}
        for name, fin in (("old", old), ("new", new)):
            d = os.path.join(scr, name + ".db")
            shutil.copyfile(dbp, d)
            o = os.path.join(scr, name + ".json")
            p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--side", fin, d, spp, o, name], capture_output=True, text=True, timeout=1200)
            if p.returncode != 0 or not os.path.exists(o):
                check("the %s side ran" % name, False, (p.stderr or p.stdout)[-400:])
                continue
            R[name] = json.load(open(o))
        if len(R) < 2:
            say("RESULT: %d FAIL" % len(FAILS))
            sys.exit(1)
        O, N = R["old"], R["new"]
        say("INFO the record: old %s rows in %ss, new %s rows in %ss" % (len(O["rows"]), O["took"], len(N["rows"]), N["took"]))
        check("L1 both builds ok, no item skipped, at least 200 rows", O["build"]["ok"] and N["build"]["ok"] and not O["build"]["errors"] and not N["build"]["errors"] and len(N["rows"]) >= int(os.environ.get("LS_MIN_ROWS", "200")), (O["build"], N["build"], len(N["rows"])))
        diff = [(a["item"], {k: (a[k], b.get(k)) for k in a if a[k] != b.get(k)}) for a, b in zip(O["rows"], N["rows"]) if a != b]
        check("L2 the stock of record is IDENTICAL row for row on the old and the new files (no live count carries a last bill yet)",
              len(O["rows"]) == len(N["rows"]) and not diff, diff[:5])
        check("L3 the new columns are added on the copy (mode, closed_how, last_bill, ask_id)", N.get("cols") == ["ask_id", "closed_how", "last_bill", "mode"], N.get("cols"))
        say("INFO his open asks on the copy: %s" % "; ".join("%s (%s)" % (a["item"], a["mode"]) for a in N.get("open_asks") or []))
        check("L4 Darpan's view answers with an Abhi ginti card (%s items now), the last bill known %s" % (N.get("now_items"), N.get("last_no")), N.get("darpan_view_ok") and N.get("now_items") == 0)
        check("L5 nothing waits to be judged to a bill, so nothing is judged", N.get("settled") == 0, N.get("settled"))
        check("L6 the Stock check page's record() answers; every open ask carries its id and mode; counts %s, look %s" % (N.get("page_counts"), N.get("page_look")),
              N.get("page_ok") and all(a["has_id"] and a["mode"] in ("now", "next") for a in N.get("page_asks") or []) and len(N.get("page_asks") or []) == len(N.get("open_asks") or []), N.get("page_asks"))
    finally:
        shutil.rmtree(scr, ignore_errors=True)
    say("RESULT: %s" % ("ALL PASS" if not FAILS else "%d FAIL" % len(FAILS)))
    sys.exit(0 if not FAILS else 1)


if __name__ == "__main__":
    main()
