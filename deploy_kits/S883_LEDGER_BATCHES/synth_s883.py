#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
synth_s883.py -- S883_LEDGER_BATCHES: the proof, on COPIES only (never the live databases).

    python3 synth_s883.py --code DIR --finance COPY.db --spine SPINE.db --archive MARGARCHIVE [--old FROMDIR] [--today YYYY-MM-DD] [--control]

  DIR holds item_ledger.py and expiry_watch.py to judge (the kit's TO files, or with --control the FROM files: then the S883 checks must
  go red). The finance copy is copied again inside a temporary folder for every write; the given files are only read.
Exit 0 = all green; 1 = a red check.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import time

OK, BAD = [], []


def check(name, cond, detail=""):
    (OK if cond else BAD).append(name)
    print(("  ok   " if cond else "  RED  ") + name + (("  -- " + str(detail)[:300]) if detail else ""))


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rows(con, sql, args=()):
    try:
        return con.execute(sql, args).fetchall()
    except sqlite3.Error:
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", required=True)
    ap.add_argument("--finance", required=True)
    ap.add_argument("--spine", required=True)
    ap.add_argument("--archive", required=True)
    ap.add_argument("--today", default="")
    ap.add_argument("--control", action="store_true")
    ap.add_argument("--item", default="DISPERZYME CD")
    ap.add_argument("--sample", type=int, default=0, help="judge every page of only N items spread over the list (0 = every item)")
    ap.add_argument("--old", default="", help="a folder holding the FROM expiry_watch.py (with its neighbours) for T1d/T1e")
    a = ap.parse_args()
    code = os.path.abspath(a.code)
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") not in (here, os.getcwd())]   # never the kit folder's own copy (F-1441)
    sys.path.insert(0, code)
    os.environ["SPINE_DB"] = a.spine
    import expiry_watch as EW                                  # noqa: E402
    import item_ledger as IL                                   # noqa: E402
    print("judging %s (item_ledger %s, expiry_watch %s)" % (code, md5(os.path.join(code, "item_ledger.py"))[:8], md5(os.path.join(code, "expiry_watch.py"))[:8]))
    today = dt.date.fromisoformat(a.today) if a.today else dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).date()
    tmp = tempfile.mkdtemp(prefix="s883_", dir=os.environ.get("TMPDIR") or "/tmp")
    try:
        # T1 -- the nightly run keeps every batch, and its lists are what they were
        fin = os.path.join(tmp, "f.db")
        shutil.copyfile(a.finance, fin)
        before = md5(a.finance)
        logs = []
        EW.run(db=fin, spine_path=a.spine, archive=a.archive, today=today, log=logs.append)
        con = sqlite3.connect(fin)
        n = rows(con, "SELECT COUNT(*), COUNT(DISTINCT k20) FROM stock_batch_now")
        check("T1a the run keeps the batch rows (stock_batch_now)", bool(n) and n[0][0] > 50, n)
        run = rows(con, "SELECT id, export_as_on, sales_to, counts FROM stock_expiry_run ORDER BY id DESC LIMIT 1")
        check("T1b the run itself is ok and used a whole-shop Batch Stock", bool(run) and run[0][1], run)
        tot_rows = rows(con, "SELECT k20, SUM(units) FROM stock_batch_now GROUP BY k20")
        # T1c the batch rows are the run's own bt: their per-item sum equals the run's own dump/near arithmetic source -- read back through compute
        sp = sqlite3.connect("file:%s?mode=ro" % a.spine, uri=True)
        sp.row_factory = sqlite3.Row
        alias = {r[0]: r[1] for r in sp.execute("SELECT alias, k20 FROM sp_alias")}
        r2, _l2 = EW.compute(con, sp, alias, a.archive, today)
        bt = r2.get("_bt") or {}
        want = {}
        for (k, _b), x in bt.items():
            want[k] = want.get(k, 0) + int(round(x["units"]))
        got = {k: int(v or 0) for k, v in tot_rows}
        check("T1c every item's batch rows add up to the run's own batches", got == want, "%d items, %d differ" % (len(want), len([k for k in want if got.get(k) != want[k]])))
        # T1d the lists of the run are exactly the old file's: run the FROM expiry_watch on a second copy when --old is beside --code
        old_dir = os.path.abspath(a.old) if a.old else ""
        if not a.control and old_dir and os.path.exists(os.path.join(old_dir, "expiry_watch.py")):
            import subprocess
            fin2 = os.path.join(tmp, "f2.db")
            shutil.copyfile(a.finance, fin2)
            src = ("import sys,datetime as dt;sys.path.insert(0,%r);import expiry_watch as E;E.run(db=%r,spine_path=%r,archive=%r,today=dt.date.fromisoformat(%r),log=lambda *x:None)"
                   % (old_dir, fin2, a.spine, a.archive, today.isoformat()))
            subprocess.run([sys.executable, "-B", "-I", "-c", src], check=False, cwd=tmp)
            c2 = sqlite3.connect(fin2)
            q = "SELECT section, part, k20, item, batch, expiry, units, pack, packing, last_sale, last_buy, info, seq FROM stock_expiry_line ORDER BY section, seq"
            l_new, l_old = rows(con, q), rows(c2, q)
            check("T1d the Expiry watch's lists are byte-for-byte the old file's", l_new == l_old and len(l_old) > 0, "%d vs %d lines" % (len(l_new), len(l_old)))
            fq = "SELECT * FROM stock_batch_fix ORDER BY id"
            f_new, f_old = rows(con, fq), rows(c2, fq)
            strip = lambda rs: [tuple(v for v in r if not (isinstance(v, str) and re.match(r"^\d{4}-\d{2}-\d{2}T", v))) for r in rs]  # noqa: E731
            check("T1e Amir's batch-fix cards are the old file's", strip(f_new) == strip(f_old), "%d vs %d" % (len(f_new), len(f_old)))
            c2.close()
        check("T1f the given finance copy is untouched", md5(a.finance) == before)
        # T2 -- the page: every item, full and last 30 days, read only, no error
        con.commit()
        con.close()
        ro = sqlite3.connect("file:%s?mode=ro" % fin, uri=True)
        m0 = md5(fin)
        keys = [r[0] for r in sp.execute("SELECT DISTINCT k20 FROM sp_item ORDER BY k20")]
        if a.sample and len(keys) > a.sample:
            step = len(keys) / float(a.sample)
            keys = sorted({keys[int(i * step)] for i in range(a.sample)} | {a.item})
        errs, slow, worst = [], 0, 0.0
        captured = {}
        import io
        import contextlib
        for k in keys:
            for rk in ("full", "30"):
                t0 = time.time()
                buf = io.StringIO()
                try:
                    with contextlib.redirect_stderr(buf):
                        h = IL.page_html(ro, {"k": k, "r": rk})
                except Exception as ex:                       # noqa: BLE001
                    errs.append((k, rk, repr(ex)[:80]))
                    continue
                dtm = time.time() - t0
                worst = max(worst, dtm)
                if dtm > 3:
                    slow += 1
                if "S883" in buf.getvalue():
                    errs.append((k, rk, buf.getvalue().strip()[:120]))
                if k == a.item and rk == "full":
                    captured["full"] = h
                if k == a.item and rk == "30":
                    captured["30"] = h
                if h.count("<details") != h.count("</details>") or h.count("<table") != h.count("</table>"):
                    errs.append((k, rk, "unbalanced details/table"))
        check("T2a every item's page renders, full and 30 days, no S883 error", not errs, "%d items; %s" % (len(keys), errs[:3]))
        check("T2b no page is slow (each under 3 s)", slow == 0, "worst %.2f s" % worst)
        check("T2c the pages wrote nothing", md5(fin) == m0)
        h = captured.get("full", "")
        txt = re.sub(r"<[^>]+>", " ", h)
        txt = re.sub(r"\s+", " ", txt)
        # T3 -- the Batches box
        check("T3a a Batches box is on the page, open", '<details class="card bx" open><summary><b>Batches</b>' in h)
        bx = rows(sqlite3.connect(fin), "SELECT batch, expiry, units FROM stock_batch_now WHERE k20=? AND units<>0 ORDER BY expiry", (a.item,))
        check("T3b every batch with stock (or below zero) of the item is a line", bool(bx) and all(("<b>%s</b>" % b) in h for b, _e, _u in bx), bx)
        if bx:
            pos = [x for x in bx if x[2] > 0]
            if pos:
                e = min(x[1] for x in pos)
                check("T3c the earliest expiry in the box's line", ("earliest expiry <b>%s/%s</b>" % (e[5:7], e[2:4])) in h, e)
        check("T3d the box says whether the batches add up to Marg", ("= Marg" in txt) or ("batches add up to" in txt))
        # T4 -- each line's batch; the totals in words; the bills fold
        n_bt = h.count('<td class="bb">') - h.count('<td class="bb"></td>')
        check("T4a sale and purchase lines carry their batch", n_bt > 0, n_bt)
        check("T4b the period's totals are in words (strips / tabs)", bool(re.search(r"bought [0-9]+ strips? in [0-9]+ bills?", txt)) or "bought 0 in" in txt, txt[txt.find("Full ledger"):][:200])
        check("T4c the purchase bills open from the totals line", '<details class="sumd">' in h and "Batch · exp" in h)
        # T5 -- folded by month; quiet days one line; the newest month open
        mons = re.findall(r'<details class="mon( mok)?"( open)?>', h)
        check("T5a the ledger is folded by month, the newest open", bool(mons) and mons[0][1] == " open", mons[:3])
        check("T5b a run of quiet days is one line", "no movement" in txt)
        check("T5c no confirm dialog on the page (F-1464)", "confirm(" not in h)
        # T6 -- no batch rows yet: the page still stands and says so
        fin3 = os.path.join(tmp, "f3.db")
        shutil.copyfile(a.finance, fin3)
        c3 = sqlite3.connect(fin3)
        c3.execute("DROP TABLE IF EXISTS stock_batch_now")
        c3.commit()
        c3.close()
        h3 = IL.page_html(sqlite3.connect("file:%s?mode=ro" % fin3, uri=True), {"k": a.item, "r": "30"})
        check("T6 with no batch rows the page stands and says when they come", "the batch figures come with the Expiry watch" in h3)
        # T7 -- words
        U = IL.Unit("1*10", "", "X")
        w = [U.words(950), U.words(1015), U.words(9), U.words(54), U.words(-9, True), U.words(0)]
        check("T7 strips and tabs in words", w == ["95 strips", "101 strips 5 tabs", "9 tabs", "5 strips 4 tabs", "−9 tabs", "0"], w)
        sp.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("synth_s883: %d ok, %d red" % (len(OK), len(BAD)))
    return 1 if BAD else 0


if __name__ == "__main__":
    sys.exit(main())
