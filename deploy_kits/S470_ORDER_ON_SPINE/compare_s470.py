#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compare_s470.py -- kit S470_ORDER_ON_SPINE: what the install prints BEFORE placing, on SCRATCH COPIES (the brief's B.3 and section 8).

  1  Marg's stock from the spine's latest accepted closing against stock_snapshot's newest: the two dates, and every item where the
     figures differ (a finding for the report, never a reason to stop)
  2  the sale units of the pace window, the spine's reading against the old store's, key by key: the items that differ
  3  the plan on order.engine_source = spine against the plan on tables, the same copy, the same day, on the stock basis as it is set
     and on the other one: lines added, lines gone, quantities changed -- each with the inputs that moved (rate, stock, on the way,
     supplier, cost) -- and the interim plan the same way
  4  the no_supplier list
  5  how long one plan takes on each source

    compare_s470.py --fin DIR(the built files) --db SCRATCH.db --spine SCRATCH_spine.db
Writes nothing but its scratch copy's settings rows. No phone number in its output.
"""
import argparse
import datetime as dt
import os
import re
import sqlite3
import sys
import time


def main():
    ap = argparse.ArgumentParser()
    for k in ("--fin", "--db", "--spine"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    assert a.db.startswith("/tmp/") and a.spine.startswith("/tmp/"), "scratch copies only"
    os.environ["FINANCE_DB"], os.environ["SPINE_DB"] = a.db, a.spine
    for k in ("ORDER_TODAY", "ORDER_TICK"):
        os.environ.pop(k, None)
    sys.path.insert(0, a.fin)
    os.chdir(a.fin)
    import order_rules as orr                                  # noqa: E402
    import purchase_app as pa                                  # noqa: E402
    assert orr.__file__.startswith(a.fin) and pa.__file__.startswith(a.fin)
    con = sqlite3.connect(a.db, timeout=60)
    con.row_factory = sqlite3.Row
    orr.ensure(con)
    today = orr._today()

    def setv(k, v):
        con.execute("INSERT INTO setting (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v))
        con.commit()

    def iso(d):
        m = re.match(r"^(\d\d)-(\d\d)-(\d{4})$", str(d or ""))
        return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1)) if m else str(d or "")[:10]
    basis0 = orr._s454_basis(con)
    print("-- 1  Marg's stock: the spine's latest closing against stock_snapshot's newest")
    setv("order.stock_basis", "marg")
    setv("order.engine_source", "tables")
    as_t, snap_t = orr._snapshot_inputs(con, today)[:2]
    setv("order.engine_source", "spine")
    as_s, snap_s = orr._snapshot_inputs(con, today)[:2]
    print("   the engine on spine reads: %s" % orr._s470_engine())
    print("   dates: the spine's closing %s · stock_snapshot %s%s" % (iso(as_s), iso(as_t), "" if iso(as_s) == iso(as_t) else "   <-- NOT the same day"))
    only_s, only_t = sorted(set(snap_s) - set(snap_t)), sorted(set(snap_t) - set(snap_s))
    diff = sorted((snap_t[k]["item"], snap_t[k]["qty"], snap_s[k]["qty"], snap_s[k]["_s470"]["family"]) for k in snap_t if k in snap_s and snap_t[k]["qty"] != snap_s[k]["qty"])
    packs = sorted((snap_t[k]["item"], snap_t[k]["pack_size"], snap_s[k]["pack_size"]) for k in snap_t if k in snap_s and snap_t[k]["pack_size"] != snap_s[k]["pack_size"])
    print("   items: the spine %d · stock_snapshot %d · in both %d · only in the spine %d %s · only in stock_snapshot %d %s"
          % (len(snap_s), len(snap_t), len(set(snap_s) & set(snap_t)), len(only_s), [snap_s[k]["item"] for k in only_s][:12], len(only_t), [snap_t[k]["item"] for k in only_t][:12]))
    print("   figures that differ: %d (of them in a family: %d)" % (len(diff), sum(1 for d in diff if d[3] > 1)))
    for item, qt, qs, fam in diff:
        print("      %-30s stock_snapshot %6d · the spine %6d%s" % (item, qt, qs, ("   (1 of %d under one 20-letter key: the key's figure shared equally)" % fam) if fam > 1 else ""))
    print("   pack sizes that differ: %d %s" % (len(packs), packs[:10]))
    setv("order.stock_basis", basis0)
    print("-- 2  the sale units of the pace window (%d days), item by item, on order.stock_basis = %s: the spine's reading against the old store's"
          % (orr._s470_days(con, "order.pace_days"), basis0))
    pace_days = orr._s470_days(con, "order.pace_days")
    setv("order.engine_source", "tables")
    pace_t = orr._snapshot_inputs(con, today)[2]
    setv("order.engine_source", "spine")
    pace_s = orr._snapshot_inputs(con, today)[2]
    pd = []
    for k in sorted(set(pace_t) | set(pace_s)):
        if k not in snap_s and k not in snap_t:
            continue
        rt, rs = (pace_t.get(k) or {}).get("rate_per_day"), (pace_s.get(k) or {}).get("rate_per_day")
        if rt is None or rs is None or abs(rt - rs) * pace_days >= 0.5:
            pd.append(((snap_s.get(k) or snap_t.get(k))["item"], None if rt is None else round(rt * pace_days, 1), None if rs is None else round(rs * pace_days, 1)))
    print("   items with a pace: tables %d · spine %d; the window's units differ (or one side has none) on %d" % (len(pace_t), len(pace_s), len(pd)))
    for item, ut, us in pd[:60]:
        print("      %-30s tables %s · spine %s" % (item, "none" if ut is None else ut, "none" if us is None else us))
    ds = [(snap_s[k]["item"], (pace_t[k] or {}).get("days_since_sale"), (pace_s[k] or {}).get("days_since_sale")) for k in pace_s
          if k in pace_t and (pace_t[k] or {}).get("days_since_sale") != (pace_s[k] or {}).get("days_since_sale")]
    print("   days since the last sale differ on %d %s" % (len(ds), ds[:8]))

    def lines_of(p):
        out = {}
        for vn, v in (p.get("vendors") or {}).items():
            for l in v["lines"]:
                out[(vn, l["item"])] = l
        return out

    def inputs(k):
        x = orr._snapshot_inputs(con, today)
        s, p, pu, tr = x[1].get(k) or {}, x[2].get(k) or {}, x[3].get(k) or {}, x[4].get(k) or {}
        return dict(stock=s.get("qty"), rate=round(p.get("rate_per_day") or 0, 3), way=tr.get("units") or 0, vendor=pu.get("vendor"), cost=pu.get("rate_p"),
                    dsl=p.get("days_since_sale"), suppliers=sorted(pu.get("suppliers") or ()), box=pu.get("box"))
    res = {}
    for basis in (basis0, "marg" if basis0 == "count" else "count"):
        setv("order.stock_basis", basis)
        P, T, I = {}, {}, {}
        for src in ("tables", "spine"):
            setv("order.engine_source", src)
            t0 = time.time()
            P[src] = orr.plan(con, today)
            T[src] = time.time() - t0
            I[src] = orr.interim_plan(con, today)
        lt, ls = lines_of(P["tables"]), lines_of(P["spine"])
        added, gone = sorted(set(ls) - set(lt)), sorted(set(lt) - set(ls))
        changed = sorted(k for k in ls if k in lt and (ls[k]["qty"], ls[k]["value_p"]) != (lt[k]["qty"], lt[k]["value_p"]))
        qchanged = [k for k in changed if ls[k]["qty"] != lt[k]["qty"]]
        print("-- 3  the plan of %s on order.stock_basis = %s%s: tables %d lines / %d suppliers · spine %d lines / %d suppliers (the plan says: %s)"
              % (today.isoformat(), basis, " (as it is set)" if basis == basis0 else " (the other basis)", len(lt), len(P["tables"]["vendors"]), len(ls),
                 len(P["spine"]["vendors"]), P["spine"].get("engine")))
        print("   lines added on spine: %d · gone: %d · quantity changed: %d · the same quantity at another value: %d" % (len(added), len(gone), len(qchanged), len(changed) - len(qchanged)))
        for lab, keys in (("ADDED", added), ("GONE", gone), ("QTY", qchanged)):
            for vn, item in keys:
                k = pa.norm(item)
                setv("order.engine_source", "tables")
                it = inputs(k)
                setv("order.engine_source", "spine")
                is_ = inputs(k)
                moved = ["%s %s -> %s" % (f, it[f], is_[f]) for f in ("rate", "stock", "way", "vendor", "cost", "dsl", "suppliers", "box") if it[f] != is_[f]]
                q = ("%s %s" % ((lt.get((vn, item)) or {}).get("qty", "-"), (ls.get((vn, item)) or {}).get("qty", "-")))
                print("      %-5s %-28s %-22s qty tables/spine %-9s  moved: %s" % (lab, item[:28], vn[:22], q, "; ".join(moved) or "nothing in the inputs (a threshold on the value)"))
        vt = sum(l["value_p"] for l in lt.values())
        vs = sum(l["value_p"] for l in ls.values())
        print("   the plan's value: tables Rs %s · spine Rs %s (the spine's cost is the bill's net amount per pack, with tax; the old table's is the purchase rate)"
              % ("{:,}".format(vt // 100), "{:,}".format(vs // 100)))
        held_t = sorted(v["vendor_norm"] for v in P["tables"]["vendors"].values() if v.get("held"))
        held_s = sorted(v["vendor_norm"] for v in P["spine"]["vendors"].values() if v.get("held"))
        print("   suppliers held under the minimum order: tables %d · spine %d%s" % (len(held_t), len(held_s), "" if held_t == held_s else "   moved: %s" % sorted(set(held_t) ^ set(held_s))))
        it_, is2 = lines_of(I["tables"]), lines_of(I["spine"])
        print("   the interim plan: tables %d lines · spine %d lines%s%s" % (len(it_), len(is2), (" (%s)" % I["spine"].get("off")) if I["spine"].get("off") else "",
              "" if set(it_) == set(is2) else "   added %s · gone %s" % (sorted(i for _v, i in set(is2) - set(it_)), sorted(i for _v, i in set(it_) - set(is2)))))
        print("   one plan took: tables %.2f s · spine %.2f s" % (T["tables"], T["spine"]))
        res[basis] = P["spine"]
    setv("order.stock_basis", basis0)
    setv("order.engine_source", "spine")
    ns = res[basis0].get("no_supplier") or []
    print("-- 4  no_supplier on spine (sold, never bought on a bill the spine holds): %d" % len(ns))
    for x in ns:
        print("      %-30s on hand %5s · %.2f a day" % (x["item"], x["on_hand"], x["rate_per_day"]))
    fam = [(l["item"], l["family"]) for l in lines_of(res[basis0]).values() if l.get("family")]
    print("-- 5  family members on the plan: %d %s" % (len(fam), fam))
    lots = [l for l in lines_of(res[basis0]).values() if l.get("lot") is not None]
    print("   lines carrying a lot / free (read, used by no rail yet): %d of %d; e.g. %s" % (len(lots), len(lines_of(res[basis0])),
          [(l["item"], l["lot"], l["free"]) for l in lots[:4]]))
    print("COMPARE_S470 DONE %s" % dt.datetime.now().strftime("%H:%M:%S"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
