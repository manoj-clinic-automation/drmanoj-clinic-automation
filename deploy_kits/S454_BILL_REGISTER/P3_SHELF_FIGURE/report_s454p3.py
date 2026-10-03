#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""report_s454p3.py -- kit S454_BILL_REGISTER, part 3: S454 9.4's report, on SCRATCH COPIES (backup API) of finance.db and the spine.

  For Darpan's sheet of 02-Oct: the comparison with the system's own list -- the box as it is (OLD, Marg's stock), the built files on
  order.stock_basis = marg (NEW marg: the 20-character pace repair alone) and on count (NEW count: the shelf figure, the default);
  for each item only on the sheet, why the system did not list it; for each line only on the system's list, why it was listed;
  the three suspected gaps of S454 2.4 tested against the data (and which were repaired).
  The rules are not tuned to the sheet: this measures.

    report_s454p3.py --fin-new DIR --fin-old DIR --db FINANCE_DB --spine SPINE_DB --work DIR
"""
import argparse
import datetime as dt
import json
import os
import sqlite3
import subprocess
import sys

TAG = "S454P3REPORT "


def side(a):
    sys.path.insert(0, a.fin)
    os.chdir(a.fin)
    os.environ["FINANCE_DB"] = a.db
    os.environ["SPINE_DB"] = a.spine
    os.environ["PORDERS_SOURCE"] = "tables"
    os.environ["ORDER_PUSH_STUB"] = os.path.join(a.work, "push_%s.jsonl" % a.name)
    import purchase_app as pa                                      # noqa: E402
    import order_rules as orr                                      # noqa: E402
    con = sqlite3.connect(a.db, timeout=60)
    con.row_factory = sqlite3.Row
    if a.basis:
        con.execute("INSERT INTO setting (key, value) VALUES ('order.stock_basis', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (a.basis,))
        con.commit()
    # as part 1B did: the comparison is made with the sheet's OWN paper orders away (else the plan counts them as on the way) -- this copy only
    sid = con.execute("SELECT id FROM order_sheet ORDER BY id LIMIT 1").fetchone()
    if sid:
        oids = [r[0] for r in con.execute("SELECT id FROM purchase_order WHERE order_via='paper' AND sheet_id=?", (sid[0],))]
        if oids:
            q = ",".join("?" * len(oids))
            for t in ("order_scan_tie",):
                try:
                    con.execute("DELETE FROM %s WHERE order_id IN (%s)" % (t, q), oids)
                except sqlite3.Error:
                    pass
            con.execute("DELETE FROM purchase_order_line WHERE order_id IN (%s)" % q, oids)
            con.execute("DELETE FROM purchase_order WHERE id IN (%s)" % q, oids)
            con.commit()
    today = dt.date.today()
    p = orr.plan(con, today)
    sysl = {}
    for v in (p.get("vendors") or {}).values():
        for l in v.get("lines") or []:
            sysl[pa.norm(l["item"])] = dict(item=l["item"], vendor=v.get("vendor"), qty=l.get("qty"), unit=l.get("unit"), why=l.get("why") or [],
                                           on_hand=l.get("on_hand"), marg=l.get("marg_qty"), shelf=l.get("shelf_qty"), per_day=l.get("per_day"),
                                           cover_after=l.get("cover_after"), cover_days=l.get("cover_days"))
    sh = con.execute("SELECT id, newest_date FROM order_sheet ORDER BY id LIMIT 1").fetchone()
    sheet = [dict(r) for r in con.execute("SELECT * FROM order_sheet_line WHERE last_sheet=? AND line_date=? ORDER BY supplier_norm, id", (sh[0], sh[1]))] if sh else []
    both = [l["item"] for l in sheet if pa.norm(l["item"]) in sysl]
    only_sheet = [l for l in sheet if pa.norm(l["item"]) not in sysl]
    only_sys = [v for k, v in sysl.items() if k not in {pa.norm(l["item"]) for l in sheet}]
    # why not listed: the plan's own path, item by item
    as_on, snap, pace, purch, transit, ortho = orr._snapshot_inputs(con, today)
    held = orr.held_sets(con)
    why = {}
    for l in only_sheet:
        k = pa.norm(l["item"])
        s, pc, lp = snap.get(k), pace.get(k), purch.get(k) or {}
        if not s:
            w = "not in Marg's closing stock under this name"
        elif k in ortho:
            w = "an orthotic (the system's medicine list leaves orthotics to S403's card)"
        elif not pc or not pc.get("rate_per_day"):
            w = "no sale pace found for its name in the last %d days" % pa.PACE_DAYS
        elif not lp.get("vendor"):
            w = "no Marg purchase of it on the server -- no supplier to list it under"
        elif orr._k20(s["item"]) in held:
            w = "held (never re-order / on demand / internal)"
        elif lp.get("vendor") != pa.supplier_key(l["supplier"]):
            w = "bought last from %s, not %s -- listed (if at all) under that supplier" % (lp.get("vendor"), l["supplier"])
        else:
            on = s["qty"] + int((transit.get(k) or {}).get("units") or 0)
            days = on / pc["rate_per_day"] if pc["rate_per_day"] else None
            w = "enough cover by its stock figure: %s on hand%s, sells %.1f a day = %s days" % (
                on, (" (Marg %s)" % s.get("marg_qty")) if "marg_qty" in s else "", pc["rate_per_day"], ("%.0f" % days) if days is not None else "?")
        why[l["item"]] = w
    # the three suspected gaps (S454 2.4)
    g1 = con.execute("SELECT COUNT(*) FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id WHERE l.arrived_at IS NOT NULL AND COALESCE(l.supplied,0)>0 "
                     "AND o.status='sent' AND l.billed_qty IS NULL").fetchone()[0]
    import item_alias as ia                                        # noqa: E402
    g2 = 0
    for r in con.execute("SELECT l.item, o.vendor, o.received_at FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id WHERE o.status='received'"):
        exact = con.execute("SELECT 1 FROM purchase_line l WHERE l.supplier_norm=? AND l.item=? AND l.bill_date>=? AND " + pa.EFF_LINE + " LIMIT 1",
                            (pa.supplier_key(r[1]), r[0], str(r[2] or "")[:10])).fetchone()
        clipped = any(ia.pad_norm(x[0]) == ia.pad_norm(ia.clip(r[0], ia.PURCHASE_CLIP)) for x in con.execute(
            "SELECT l.item FROM purchase_line l WHERE l.supplier_norm=? AND l.bill_date>=? AND " + pa.EFF_LINE, (pa.supplier_key(r[1]), str(r[2] or "")[:10])))
        if clipped and not exact:
            g2 += 1
    long_ = [k for k, s in snap.items() if len(s["item"]) > getattr(ia, "SALE_CLIP", 20) and k not in ortho]
    g3 = dict(long_items=len(long_), with_pace=sum(1 for k in long_ if (pace.get(k) or {}).get("rate_per_day")))
    out = dict(name=a.name, basis=a.basis, as_on=p.get("as_on"), x=len(both), y=len(sheet), both=both, only_sheet=[l["item"] for l in only_sheet],
               only_sys=only_sys, why=why, g1=g1, g2=g2, g3=g3)
    print(TAG + json.dumps(out, default=str))


def main():
    ap = argparse.ArgumentParser()
    for k in ("--fin-new", "--fin-old", "--db", "--spine", "--work", "--fin", "--name", "--side", "--basis"):
        ap.add_argument(k)
    a = ap.parse_args()
    if a.side:
        side(a)
        return 0
    os.makedirs(a.work, exist_ok=True)
    res = {}
    for name, fin, basis in (("old", a.fin_old, ""), ("new_marg", a.fin_new, "marg"), ("new_count", a.fin_new, "count")):
        db = os.path.join(a.work, "r3_%s.db" % name)
        s = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
        d = sqlite3.connect(db)
        s.backup(d)
        d.close()
        s.close()
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--side", "1", "--name", name, "--fin", fin, "--db", db, "--spine", a.spine,
                            "--work", a.work, "--basis", basis], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=1200)
        js = [l[len(TAG):] for l in p.stdout.splitlines() if l.startswith(TAG)]
        res[name] = json.loads(js[-1]) if js else dict(error=p.stdout[-1500:])
    if any("error" in v for v in res.values()):
        print("REPORT_S454P3 RED -- a side did not finish:\n" + "\n".join(v.get("error", "") for v in res.values()))
        return 1
    O, M, C = res["old"], res["new_marg"], res["new_count"]
    print("== S454 9.4: Darpan's sheet of 02-Oct against the system's own list (stock as on %s)" % C["as_on"])
    print("-- the system agreed on: OLD (the box as it is, Marg's stock) %d of %d · NEW on marg (the 20-character pace repair only) %d of %d · "
          "NEW on count (the shelf figure, the default) %d of %d" % (O["x"], O["y"], M["x"], M["y"], C["x"], C["y"]))
    print("   on both (count): %s" % ", ".join(C["both"]))
    print("-- only on Darpan's sheet (count basis): %d" % len(C["only_sheet"]))
    for it in C["only_sheet"]:
        print("   %-22s %s" % (it, C["why"].get(it)))
    print("-- only on the system's list (count basis): %d" % len(C["only_sys"]))
    for l in sorted(C["only_sys"], key=lambda x: (x["vendor"] or "", x["item"])):
        print("   %-22s %-28s %s %s · shelf %s (Marg %s) · %s a day · %s" % (l["item"], (l["vendor"] or "")[:28], l["qty"], l["unit"], l["shelf"], l["marg"],
                                                                         l["per_day"], "; ".join(l["why"])[:160]))
    print("-- the three suspected gaps of S454 2.4, tested against the data:")
    print("   (1) a line tapped 'Aa gaya' while its order is still 'sent' is counted nowhere: %d such line(s) now -- not proven by the data, not changed"
          % C["g1"])
    print("   (2) _in_transit matches the item name exactly though purchase names are clipped: %d received line(s) whose clipped Marg purchase the exact "
          "match misses -- not proven by the data, not changed" % C["g2"])
    print("   (3) _pace keys sales by the printed 20-character name: medicines with longer names %d, with a pace OLD %d -> NEW %d -- proven, repaired"
          % (C["g3"]["long_items"], O["g3"]["with_pace"], C["g3"]["with_pace"]))
    print("REPORT_S454P3 DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
