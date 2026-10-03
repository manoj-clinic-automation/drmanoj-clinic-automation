#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rules_report_s454p2.py -- kit S454_BILL_REGISTER, part 2: S454 section 5's report BEFORE anything is placed -- the rules run on September
on SCRATCH COPIES (backup API) of finance.db and assets.db: the box as it is (OLD) and the built files (NEW), each in its own process.

  how many of the month's unlinked scans now pair by themselves (and how); how many of the linked bills are Verified / Has its scan /
  Amount differs; how many questions are left (before -> after); every row whose state changes; for every new pair, the scan's own item
  lines against Marg's lines of that bill (a check that it is the right paper). A pair whose items share nothing with Marg's is printed as
  SUSPECT and the report ends RED -- S454 5: "If a rule pairs a wrong scan and bill on the copy, stop and report."

    rules_report_s454p2.py --fin-new DIR --fin-old DIR --db FINANCE_DB --adb ASSETS_DB --work DIR [--month 2026-09]
"""
import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys

TAG = "S454P2RULES "


def side(a):
    sys.path.insert(0, a.fin)
    os.chdir(a.fin)
    os.environ["FINANCE_DB"] = a.db
    os.environ["ASSETS_DB"] = a.adb
    os.environ["ORDER_PUSH_STUB"] = os.path.join(a.work, "push_%s.jsonl" % a.name)
    import purchase_app as pa                                     # noqa: E402
    pa._assets_db = a.adb
    import porders                                                # noqa: E402
    con = sqlite3.connect(a.db, timeout=60)
    con.row_factory = sqlite3.Row
    pa._ensure(con)
    month = a.month

    def bmonth(bid):
        r = con.execute("SELECT COALESCE(month, substr(bill_date,1,7)) FROM purchase_bill WHERE id=?", (bid,)).fetchone()
        return r[0] if r else None
    links0 = {r[0]: (r[1], r[2]) for r in con.execute("SELECT bill_id, asset_bill_id, grade FROM purchase_scan_link")}
    res = pa._rematch(con, "S454 P2 rules report (%s)" % a.name)
    links1 = {r[0]: (r[1], r[2], r[3]) for r in con.execute("SELECT bill_id, asset_bill_id, grade, matched_on FROM purchase_scan_link")}
    acon = sqlite3.connect("file:%s?mode=ro" % a.adb, uri=True)
    acon.row_factory = sqlite3.Row
    new = []
    for bid, (sid, grade, rule) in sorted(links1.items()):
        if bid in links0 or bmonth(bid) != month:
            continue
        b = dict(con.execute("SELECT * FROM purchase_bill WHERE id=?", (bid,)).fetchone())
        s = dict(acon.execute("SELECT id, stamp_no, vendor, bill_no, bill_date, total_amount FROM bills WHERE id=?", (sid,)).fetchone())
        items = [dict(r) for r in acon.execute("SELECT item_name, quantity, rate FROM bill_items WHERE bill_id=?", (sid,))]
        ml = [dict(r) for r in con.execute("SELECT DISTINCT item, qty, rate_p FROM purchase_line WHERE supplier_norm=? AND bill_no=? AND bill_date=?",
                                           (b["supplier_norm"], b["bill_no"], b["bill_date"]))]

        def same(it, x):
            """the same line: the names alike (0.6), or the same quantity at the same rate (within 1%)"""
            import difflib                                        # noqa: PLC0415
            a1 = re.sub(r"[^A-Z0-9]", "", str(it["item_name"] or "").upper())
            b1 = re.sub(r"[^A-Z0-9]", "", str(x["item"] or "").upper())
            if a1 and b1 and difflib.SequenceMatcher(None, a1[:len(b1) + 2], b1).ratio() >= 0.6:
                return True
            try:
                return (abs(float(it["quantity"]) - float(x["qty"])) < 0.001 and x["rate_p"]
                        and abs(float(it["rate"]) * 100 - float(x["rate_p"])) <= 0.01 * float(x["rate_p"]))
            except (TypeError, ValueError):
                return False
        hit = sum(1 for it in items if any(same(it, x) for x in ml))
        new.append(dict(bill=bid, supplier=b["supplier"], marg_no=b["bill_no"], marg_date=b["bill_date"], marg_p=b["amount_p"], scan=sid,
                        stamp=s["stamp_no"], scan_vendor=s["vendor"], scan_no=s["bill_no"], scan_date=s["bill_date"], scan_total=s["total_amount"],
                        grade=grade, rule=rule, items_scan=len(items), items_marg=len(ml), items_shared=hit))
    dropped = sorted(b for b in links0 if b not in links1)
    out = dict(name=a.name, rematch=dict((k, res.get(k)) for k in ("links", "new", "dups", "dropped", "reasons")) if res else None, new=new, dropped=dropped)
    k = porders.scan_work(con)
    mb = lambda x: bmonth(x["bill_id"]) == month if x.get("bill_id") else None   # noqa: E731
    out["questions"] = dict(confirm=sum(1 for x in k["confirm"] if mb(x)), amount=sum(1 for x in k["amount"] if mb(x)),
                            vendor=len(k["vendor"]), twin=len(k.get("twin") or []), dup=k["counts"].get("dup"),
                            amount_list=sorted((x["bill_id"], x.get("scan_amount_p"), x["amount_p"]) for x in k["amount"] if mb(x)),
                            confirm_list=sorted((x["scan"], x["bill_id"], bool(x.get("taken_by"))) for x in k["confirm"] if mb(x)),
                            vendor_list=sorted(x["scan"] for x in k["vendor"]))
    try:
        import scan_register as SR                                # noqa: E402
        r = SR.register(con, month)
        out["register"] = dict(counts=r["counts"], scan_counts=r["scan_counts"], settled=r["settled"], total=r["total"],
                               rows=[(x["id"], x["state"], x["supplier"], x["bill_no"], x["stamp"], x["note"][:160]) for x in r["rows"]])
        out["sarvam"] = SR.sarvam(con, month)
        cx = SR.Ctx(con)
        sc = SR.asset_scans(con) or {}
        miss = dict(supplier=[], billno=[], date=[], total=[])
        for bid, (sid, _g, _r) in sorted(links1.items()):
            if bmonth(bid) != month or sid not in sc:
                continue
            b = dict(con.execute("SELECT * FROM purchase_bill WHERE id=?", (bid,)).fetchone())
            f = SR.sarvam_flags(cx, dict(sc[sid]), b)
            for k in miss:
                if not f[k + "_ok"]:
                    s = sc[sid]
                    miss[k].append("%s%s %s: scan %s reads %s" % ("NEW " if bid not in links0 else "", pa.supplier_key(b["supplier"]), b["bill_no"],
                                                                  s.get("stamp_no"), {"supplier": repr(s.get("vendor")), "billno": repr(s.get("bill_no")),
                                                                                      "date": "%s (Marg %s)" % (s.get("bill_date"), b["bill_date"]),
                                                                                      "total": "%s (Marg %.2f)" % (s.get("total_amount"), b["amount_p"] / 100.0)}[k]))
        out["miss"] = miss
        out["linked_before_states"] = {}
        for x in r["rows"]:
            if x["id"] in links0:
                out["linked_before_states"][x["state"]] = out["linked_before_states"].get(x["state"], 0) + 1
    except ImportError:
        out["register"] = None
    print(TAG + json.dumps(out, default=str))


def main():
    ap = argparse.ArgumentParser()
    for k in ("--fin-new", "--fin-old", "--db", "--adb", "--work", "--fin", "--name", "--side"):
        ap.add_argument(k)
    ap.add_argument("--month", default="2026-09")
    a = ap.parse_args()
    if a.side:
        side(a)
        return 0
    os.makedirs(a.work, exist_ok=True)
    res = {}
    for name, fin in (("old", a.fin_old), ("new", a.fin_new)):
        db, adb = os.path.join(a.work, "rr_%s.db" % name), os.path.join(a.work, "rr_%s_assets.db" % name)
        for src, dst in ((a.db, db), (a.adb, adb)):
            s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
            d = sqlite3.connect(dst)
            s.backup(d)
            d.close()
            s.close()
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--side", "1", "--name", name, "--fin", fin, "--db", db, "--adb", adb,
                            "--work", a.work, "--month", a.month], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=1200)
        js = [l[len(TAG):] for l in p.stdout.splitlines() if l.startswith(TAG)]
        res[name] = json.loads(js[-1]) if js else dict(error=p.stdout[-1500:])
    O, N = res["old"], res["new"]
    if "error" in O or "error" in N:
        print("RULES_REPORT RED -- a side did not finish:\n%s\n%s" % (O.get("error", ""), N.get("error", "")))
        return 1
    m = a.month
    print("== S454 section 5: the rules on %s, on scratch copies (OLD = the box as it is, NEW = the built files)" % m)
    nr = N.get("register") or {}
    c = nr.get("counts") or {}
    linked0 = sum((N.get("linked_before_states") or {}).values())
    print("-- the linked bills (%d before this pass): Verified %d · Has its scan %d · Amount differs %d (by the rules: %s)"
          % (linked0, (N["linked_before_states"] or {}).get("verified", 0), (N["linked_before_states"] or {}).get("has_scan", 0),
             (N["linked_before_states"] or {}).get("amount_differs", 0), json.dumps(N.get("linked_before_states"))))
    print("-- new pairs made by the rules on the copy: %d (OLD made %d)" % (len(N["new"]), len(O["new"])))
    suspect = []
    for x in N["new"]:
        ok = x["items_scan"] == 0 or x["items_shared"] > 0
        if not ok:
            suspect.append(x)
        print("   %s %s · Marg %s %s Rs %.2f  <-  scan %s reads '%s' / '%s' / %s / %s  [%s]  items: scan %d, Marg %d, shared %d%s"
              % (x["grade"], x["supplier"], x["marg_no"], x["marg_date"], x["marg_p"] / 100.0, x["stamp"], x["scan_vendor"], x["scan_no"], x["scan_date"],
                 x["scan_total"], x["rule"], x["items_scan"], x["items_marg"], x["items_shared"], "" if ok else "  <-- SUSPECT: no item in common"))
    print("-- links dropped: OLD %s · NEW %s (a link that exists is never undone)" % (O["dropped"], N["dropped"]))
    qo, qn = O["questions"], N["questions"]
    print("-- questions for %s: Is this the bill? %d -> %d · Match the amount %d -> %d · Choose the supplier %d -> %d · second scans %s -> %s · S441's %d -> %d"
          % (m, qo["confirm"], qn["confirm"], qo["amount"], qn["amount"], qo["vendor"], qn["vendor"], qo["dup"], qn["dup"], qo["twin"], qn["twin"]))
    print("   amount questions OLD %s" % qo["amount_list"])
    print("   amount questions NEW %s" % qn["amount_list"])
    print("   'is this the bill?' OLD %s" % qo["confirm_list"])
    print("   'is this the bill?' NEW %s" % qn["confirm_list"])
    print("-- the register of %s (NEW): %s · settled %d of %d · scans with no Marg bill %s" % (m, json.dumps(c), nr.get("settled", 0), nr.get("total", 0),
                                                                                         json.dumps(nr.get("scan_counts"))))
    newb = {x["bill"] for x in N["new"]}
    amt_new = {x[0] for x in qn["amount_list"]} - {x[0] for x in qo["amount_list"]}
    amt_gone = {x[0] for x in qo["amount_list"]} - {x[0] for x in qn["amount_list"]}
    print("-- every row whose state changes:")
    for rid, st, sup, bno, stamp, note in nr.get("rows") or []:
        if rid in newb:
            print("   bill %s %s %s: No scan -> %s (scan %s) -- %s" % (rid, sup, bno, st, stamp, note))
        elif rid in amt_new:
            print("   bill %s %s %s: linked, no question (within 2%%) -> %s, one question -- %s" % (rid, sup, bno, st, note))
        elif rid in amt_gone:
            print("   bill %s %s %s: an amount question (beyond 2%%) -> %s, no question -- %s" % (rid, sup, bno, st, note))
    s = N.get("sarvam") or {}
    if s:
        print("-- the Sarvam counter for %s by the rules: %d linked bills · misread: supplier %d · bill no. %d · date %d · total %d · item lines %d of %d read right"
              % (m, s["n"], s["misses"]["supplier"], s["misses"]["billno"], s["misses"]["date"], s["misses"]["total"], s["items_right"], s["items_read"]))
    for k, v in (N.get("miss") or {}).items():
        print("   %s misread (%d): %s" % (k, len(v), "; ".join(v)))
    if suspect:
        print("RULES_REPORT RED -- %d new pair(s) share no item with Marg's lines: STOP (S454 5)" % len(suspect))
        return 1
    print("RULES_REPORT GREEN -- no new pair is suspect")
    return 0


if __name__ == "__main__":
    sys.exit(main())
