#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s454p1b.py -- kit S454_BILL_REGISTER, part 1B: the first load's comparison, on scratch copies of finance.db (never the live file).

Each side runs in its own process on its own backup-API copy: NEW = the finance files with the built order_sheet.py, OLD = the box as it is
(part 1's order_sheet.py) -- the negative control. On each copy the walk takes away its OWN rows, found by key (the sheet's md5 and the
orders made from that sheet), loads Darpan's sheet of 02-Oct again "as already ordered" (first_load_s454.load_text, copied out of the
part-1 kit), and reads the comparison. The reference is the same comparison made with the sheet's paper orders absent.

    walk_s454p1b.py --fin-new DIR --fin-old DIR --marg DIR --db FINANCE_DB --reader marg_txt.py --sheet SHEET.txt --first-load first_load_s454.py --work DIR
"""
import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys

TAG = "W454BJSON "


def side(a):
    """One side, in its own process: sys.path = that side's finance folder."""
    for p in (a.fin, a.marg, a.work):
        sys.path.insert(0, p)
    os.environ["FINANCE_DB"] = a.db
    os.environ["MARG_INGEST_DIR"] = a.marg
    os.environ["ORDER_PUSH_STUB"] = os.path.join(a.work, "push_%s.jsonl" % a.name)     # no push can leave the walk
    con = sqlite3.connect(a.db, timeout=60)
    con.row_factory = sqlite3.Row
    import order_sheet as OS                                  # noqa: PLC0415
    import first_load_s454 as FL                              # noqa: PLC0415 -- the copy in the walk's own folder
    raw = open(a.sheet, "rb").read()
    xls_md5 = FL.hashlib.md5(FL._reader(a.reader).convert(raw)[0]).hexdigest()
    sids = [r[0] for r in con.execute("SELECT id FROM order_sheet WHERE md5=?", (xls_md5,))]
    oids = [r[0] for r in con.execute("SELECT id FROM purchase_order WHERE order_via='paper' AND sheet_id IN (%s)" % ",".join("?" * len(sids)), sids)] if sids else []
    q = ",".join("?" * len(oids))
    if oids:
        con.execute("DELETE FROM order_scan_tie WHERE order_id IN (%s)" % q, oids)
        con.execute("DELETE FROM purchase_order_line WHERE order_id IN (%s)" % q, oids)
        con.execute("DELETE FROM purchase_order WHERE id IN (%s)" % q, oids)
    if sids:
        qs = ",".join("?" * len(sids))
        con.execute("DELETE FROM order_sheet_line WHERE first_sheet IN (%s) OR last_sheet IN (%s)" % (qs, qs), sids + sids)
        con.execute("DELETE FROM order_sheet WHERE id IN (%s)" % qs, sids)
    con.commit()
    r = FL.load_text(con, raw, a.reader, name="W454B walk")
    sid = r["sheet_id"]
    got = json.loads(con.execute("SELECT cmp FROM order_sheet WHERE id=?", (sid,)).fetchone()[0] or "{}")
    made = len(r.get("paper_orders") or [])
    new_oids = [x["order_id"] for x in r.get("paper_orders") or []]
    qn = ",".join("?" * len(new_oids))
    con.execute("DELETE FROM purchase_order_line WHERE order_id IN (%s)" % qn, new_oids)
    con.execute("DELETE FROM purchase_order WHERE id IN (%s)" % qn, new_oids)
    con.commit()
    ref = OS.compare(con, sid)
    pushes = os.path.exists(os.environ["ORDER_PUSH_STUB"])
    print(TAG + json.dumps(dict(removed=dict(sheets=len(sids), orders=len(oids)), made=made, x=got.get("x"), y=got.get("y"),
                                both=sorted(b["item"] for b in got.get("both") or []), ref_x=ref["x"], ref_y=ref["y"],
                                ref_both=sorted(b["item"] for b in ref["both"]), pushes=pushes)))


def main():
    ap = argparse.ArgumentParser()
    for k in ("--fin-new", "--fin-old", "--marg", "--db", "--reader", "--sheet", "--first-load", "--work"):
        ap.add_argument(k)
    ap.add_argument("--side")
    ap.add_argument("--fin")
    ap.add_argument("--name")
    a = ap.parse_args()
    if a.side:
        side(a)
        return 0
    os.makedirs(a.work, exist_ok=True)
    shutil.copyfile(a.first_load, os.path.join(a.work, "first_load_s454.py"))
    res = {}
    for name, fin in (("new", a.fin_new), ("old", a.fin_old)):
        db = os.path.join(a.work, "scratch_%s.db" % name)
        s = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
        d = sqlite3.connect(db)
        s.backup(d)
        d.close()
        s.close()
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--side", "1", "--name", name, "--fin", fin, "--marg", a.marg, "--db", db,
                            "--reader", a.reader, "--sheet", a.sheet, "--work", a.work], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=1200)
        js = [l[len(TAG):] for l in p.stdout.splitlines() if l.startswith(TAG)]
        res[name] = json.loads(js[-1]) if js else dict(error=p.stdout[-600:])
    ok = [0, 0]

    def check(label, cond, got=None):
        ok[0] += 1
        ok[1] += 1 if cond else 0
        print(("  ok   " if cond else "  FAIL ") + label + ("" if got is None else "   [%s]" % (got,)))
    N, O = res["new"], res["old"]
    print("-- the first load of 02-Oct, again on scratch copies (the walk's own rows taken away by key first)")
    check("NEW: the sheet's 10 paper orders made again; no push left the walk", N.get("made") == 10 and not N.get("pushes"), N)
    check("NEW: the comparison kept at the load equals the comparison made with the sheet's own orders absent (%s of %s)" % (N.get("x"), N.get("y")),
          N.get("x") == N.get("ref_x") and N.get("y") == N.get("ref_y") == 21 and N.get("both") == N.get("ref_both") and (N.get("x") or 0) > 0, N)
    check("NEGATIVE: the box as it is (part 1's order_sheet) keeps 0 of 21 -- its own paper orders counted as on the way",
          O.get("x") == 0 and O.get("ref_x") == N.get("ref_x"), O)
    print("WALK_S454P1B %s -- %d of %d passed" % ("GREEN" if ok[0] == ok[1] else "RED", ok[1], ok[0]))
    return 0 if ok[0] == ok[1] else 1


if __name__ == "__main__":
    sys.exit(main())
