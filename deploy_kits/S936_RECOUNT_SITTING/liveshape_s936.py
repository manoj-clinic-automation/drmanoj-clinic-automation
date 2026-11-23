#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""liveshape_s936.py -- kit S936_RECOUNT_SITTING (23-Nov-2026). On COPIES of the live databases (never the live files):
    python3 -B liveshape_s936.py <new dir> <old dir> <finance.db copy> <spine.db copy> <repair_s936.py>
(1) the stock of record built with the OLD and the NEW files on two copies of the same database: every row identical (no live count is held
yet, so S936 by itself changes no figure); (2) the new files on the copy: ensure() adds the columns, Darpan's view answers with the sitting's
bill field, the Stock check page's record() answers; (3) the TRAMATEE repair run on the new copy: REPAIRED, point 388 'recounted', loss line
7 void, trace 35 closed, and the record rebuilt after it -- every other row identical, TRAMATEE's shelf figure unchanged (its base was
already the 23-11 count). Prints counts and item names only. 'RESULT: ALL PASS' or 'RESULT: n FAIL'."""
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
KEEP = ("item", "marg_units", "shelf_units", "waiting_units", "gap_units", "state", "base_kind", "base_day", "marg_flag")


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
    import stock_record as SR                                 # noqa: E402
    con = sqlite3.connect(dbp, timeout=60)
    sp = SW.Spine(spp)
    t = time.time()
    r = SR.build(con, sp, log=lambda s: None)
    took = round(time.time() - t, 1)
    rows, _M = SR.rows(con, sp, "never")
    res = dict(build=dict(ok=r.get("ok"), n=r.get("n"), errors=r.get("errors")), took=took,
               rows=sorted([{k: d.get(k) for k in KEEP} for d in rows], key=lambda d: d["item"]))
    if new in ("new", "after"):
        SW.ensure(con)
        cols = {x[1] for x in con.execute("PRAGMA table_info(stock_watch_ask)")}
        res["cols"] = sorted(cols & {"recount_of", "why", "why_hi"})
        dv = SW.darpan_view(con, "darpan")
        res["darpan_view_ok"] = bool(dv.get("ok"))
        res["now_keys"] = sorted((dv.get("now") or {}).keys())
        res["held"] = con.execute("SELECT COUNT(*) FROM stock_point WHERE status IN ('recount','recounted')").fetchone()[0]
        import stock_check as SC                              # noqa: E402
        SC._db = lambda: con
        rec = SC.record(con)
        res["page_ok"] = bool(rec.get("ok"))
        res["page_counts"] = len(rec.get("counts") or [])
        res["tram_counts"] = [dict(at=c.get("at"), qty=c.get("qty_t"), exp=c.get("expected_t"), gap=c.get("gap_t"), note=(c.get("note") or "")[:90])
                              for c in rec.get("counts") or [] if str(c.get("item") or "").startswith("TRAMATEE P")]
        if new == "after":
            res["r388"] = con.execute("SELECT status FROM stock_point WHERE id=388").fetchone()
            res["ll7"] = con.execute("SELECT void_at IS NOT NULL FROM stock_watch_loss_line WHERE id=7").fetchone()
            res["t35"] = con.execute("SELECT status FROM stock_trace WHERE id=35").fetchone()
    json.dump(res, open(out, "w"), default=str)


def run_side(scr, name, fin, d, spp):
    o = os.path.join(scr, name + ".json")
    p = subprocess.run([sys.executable, "-B", "-W", "ignore", os.path.abspath(__file__), "--side", fin, d, spp, o, name], capture_output=True, text=True, timeout=1200)
    if p.returncode != 0 or not os.path.exists(o):
        check("the %s side ran" % name, False, (p.stderr or p.stdout)[-400:])
        return None
    return json.load(open(o))


def main():
    if "--side" in sys.argv:
        a = sys.argv[sys.argv.index("--side") + 1:]
        side(a[0], a[1], a[2], a[3], a[4])
        return
    new, old, dbp, spp, rep = [os.path.abspath(x) for x in sys.argv[1:6]]
    scr = tempfile.mkdtemp(prefix="ls936_", dir=os.environ.get("TMPDIR") or "/tmp")
    try:
        do, dn = os.path.join(scr, "old.db"), os.path.join(scr, "new.db")
        shutil.copyfile(dbp, do)
        shutil.copyfile(dbp, dn)
        O = run_side(scr, "old", old, do, spp)
        N = run_side(scr, "new", new, dn, spp)
        if not (O and N):
            say("RESULT: %d FAIL" % len(FAILS))
            sys.exit(1)
        say("INFO the record: old %s rows in %ss, new %s rows in %ss" % (len(O["rows"]), O["took"], len(N["rows"]), N["took"]))
        check("L1 both builds ok, no item skipped, at least %s rows" % os.environ.get("LS_MIN_ROWS", "200"),
              O["build"]["ok"] and N["build"]["ok"] and not O["build"]["errors"] and not N["build"]["errors"] and len(N["rows"]) >= int(os.environ.get("LS_MIN_ROWS", "200")),
              (O["build"], N["build"]))
        diff = [(a["item"], {k: (a[k], b.get(k)) for k in a if a[k] != b.get(k)}) for a, b in zip(O["rows"], N["rows"]) if a != b]
        check("L2 the stock of record is IDENTICAL row for row on the old and the new files (no live count is held yet)", len(O["rows"]) == len(N["rows"]) and not diff, diff[:5])
        check("L3 the new columns are added on the copy (recount_of, why, why_hi); no count held yet", N.get("cols") == ["recount_of", "why", "why_hi"] and N.get("held") == 0,
              (N.get("cols"), N.get("held")))
        check("L4 Darpan's view answers; its Abhi ginti card carries the sitting's bill field", N.get("darpan_view_ok") and "sitting_bill" in (N.get("now_keys") or []), N.get("now_keys"))
        check("L5 the Stock check page's record() answers (%s counts)" % N.get("page_counts"), N.get("page_ok"))
        say("INFO TRAMATEE on the Stock check before the repair: %s" % N.get("tram_counts"))
        p = subprocess.run([sys.executable, "-B", "-W", "ignore", rep, dn], cwd=new, capture_output=True, text=True, timeout=600,
                           env=dict(os.environ, FINANCE_DB=dn, SPINE_DB=spp, PYTHONDONTWRITEBYTECODE="1"))
        out = (p.stdout or "").strip().splitlines()
        for ln in out[:-1]:
            say("INFO repair: " + ln[:240])
        check("L6 the TRAMATEE repair on the copy: REPAIRED", bool(out) and out[-1] == "RESULT: REPAIRED", (out[-1:] if out else p.stderr[-300:]))
        A = run_side(scr, "after", new, dn, spp)
        if A:
            check("L7 on the copy: point 388 'recounted', loss line 7 void, trace 35 closed", A.get("r388") == ["recounted"] and A.get("ll7") == [1] and A.get("t35") == ["fixed"],
                  (A.get("r388"), A.get("ll7"), A.get("t35")))
            d2 = [(a["item"], {k: (a[k], b.get(k)) for k in a if a[k] != b.get(k)}) for a, b in zip(N["rows"], A["rows"]) if a != b]
            others = [x for x in d2 if not x[0].startswith("TRAMATEE P")]
            tram = [x for x in d2 if x[0].startswith("TRAMATEE P")]
            check("L8 the record after the repair: every other row identical; TRAMATEE's shelf figure unchanged", len(N["rows"]) == len(A["rows"]) and not others
                  and not any("shelf_units" in x[1] for x in tram), (others[:3], tram))
            say("INFO TRAMATEE on the Stock check after the repair: %s" % A.get("tram_counts"))
    finally:
        shutil.rmtree(scr, ignore_errors=True)
    say("RESULT: %s" % ("ALL PASS" if not FAILS else "%d FAIL" % len(FAILS)))
    sys.exit(0 if not FAILS else 1)


if __name__ == "__main__":
    main()
