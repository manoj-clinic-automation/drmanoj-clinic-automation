#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""po_build.py — run po_engine against the real archive and write the plan."""
import collections, datetime as dt, glob, json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
for rel in ("../S206_SANJEEVNI_MARG_PURCHASE", "../S206_SANJEEVNI_RECONCILE", "."):
    sys.path.insert(0, os.path.abspath(os.path.join(HERE, rel)))
import po_engine as E
import item_company as IC
import ingest, packmap as PM, marg_stock as MS, marg_purchase as MP
import resolve as RS

# --- archive location -------------------------------------------------------
# S212 FIX. This was hard-coded to "~/mnt/Downloads/margsync/MargArchive" --
# the assistant's own sandbox mount. On manojz, where this actually runs, that
# path does not exist, so the script could not start. Found at S212 by asking
# where each kit runs rather than where it was written.
#
# The AUTHORITY is the MARG_ARCHIVE environment variable (or --archive where
# the script takes arguments). The candidate list below is only a fallback, so
# if these lists ever drift between kits it changes nothing -- the setting wins.
def _find_archive():
    env = os.environ.get("MARG_ARCHIVE")
    if env:
        return env
    for c in (r"D:\Downloads\margsync\MargArchive",
              os.path.expanduser("~/mnt/Downloads/margsync/MargArchive"),
              os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "..", "..", "Downloads", "margsync", "MargArchive")):
        if os.path.isdir(c):
            return os.path.abspath(c)
    # Nothing found: return the Windows path so the error names the real place.
    return r"D:\Downloads\margsync\MargArchive"
# ---------------------------------------------------------------------------

A = _find_archive()
TODAY = dt.date(2026, 8, 28)


def build(cap_p=None):
    lines, _, _ = ingest.read_sale()

    def units(l):
        """Use the kit's OWN reader, never a fresh one.

        My first version did strips*size + loose. That is precisely the fault
        the reconciliation exists because of: a strip line writes '0:1', but a
        tube, vial or spray writes '1.0', and a reader that only understands
        the first returns NOTHING for the second -- 2,807 lines, 16.3% of the
        year, reading as zero and their items looking dead while they sold
        well. It also undercounted TYRO BR at 32.6 a day against the 112.6
        S206 measured, which is the difference between ordering 12 strips and
        ordering 98.

        ingest.sale_units() already handles both shapes and is asserted in the
        reconcile suite. Reimplementing a parser that exists is how a fixed
        fault comes back."""
        # THE ROW'S OWN PACKING, never a map-wide size. s2_ledger states the
        # rule outright: "Marg printed that pair against that packing; using a
        # different one changes the answer by a multiple." I used a map first
        # and a bare int() fallback second -- packmap has no pack_sizes(), so
        # the map was empty and int("1*10") threw, leaving size=1. Every strip
        # line counted as one unit. TYRO BR came out at 32.6 a day against the
        # 112.6 S206 measured: a third of the truth, and an order for 12 strips
        # where 98 were needed.
        size = PM.pack_size(l.get("pack"))
        u, _kind = ingest.sale_units(l, size)
        return int(u or 0)

    # ---- THE 20-CHARACTER CAP. This is not optional.
    # The sale report truncates item names at 20 characters, and the cut can
    # land on a space and be stripped, so a length test misses the biggest
    # ones. Matching the truncated sale name against the full stock name
    # silently loses the item: its consumption reads as zero and it is never
    # ordered. The first run of this builder considered 158 items out of the
    # 285 that actually moved -- a third of the shop invisible to the order
    # plan, and nothing on screen would have said so.
    #
    # resolve.py already solved this for the reconciliation. Same map, reused.
    # A name it cannot resolve WITH CERTAINTY is left alone and counted, never
    # bent to fit: six belt sizes cut to the same 20 characters and pooling
    # them into one would invent a size the report never recorded.
    stock_names = None

    sale = collections.defaultdict(lambda: {"u": 0, "days": set(), "last": None,
                                            "byday": collections.Counter()})
    for l in lines:
        it = l.get("item")
        if not it or not l.get("date"):
            continue
        u = units(l)
        r = sale[it]
        r["u"] += u
        r["days"].add(l["date"])
        r["byday"][l["date"]] += u
        r["last"] = max(r["last"], l["date"]) if r["last"] else l["date"]

    # purchases -> vendor, cost, how many vendors, vendor spend and cadence
    ven_items = collections.defaultdict(set)
    item_ven = collections.defaultdict(collections.Counter)
    cost, vspend = {}, collections.Counter()
    pq = collections.defaultdict(list)          # purchase quantities, per item
    vbills = collections.defaultdict(set)
    for p in sorted(glob.glob(os.path.join(A, "PURCHASE_ITEMWISE", "*", "*.XLS"))):
        try:
            rep = MP.read_purchase(p)
        except Exception:
            continue
        for r in rep["rows"]:
            it, v = r.get("item"), (r.get("supplier") or "").strip()
            if not it or not v:
                continue
            ven_items[v].add(it)
            item_ven[it][v] += 1
            nr = r.get("net_rate") or r.get("rate")
            if nr:
                try:
                    cost[it] = int(round(float(nr) * 100))
                except (TypeError, ValueError):
                    pass
            try:
                vspend[v] += int(round(float(r.get("net_amount") or r.get("amount") or 0) * 100))
            except (TypeError, ValueError):
                pass
            if r.get("bill"):
                vbills[v].add((v, str(r["bill"])))
            if r.get("qty"):
                try:
                    pq[it].append(int(round(float(r["qty"]))))
                except (TypeError, ValueError):
                    pass

    # stock, largest export for the newest date (F-235)
    best = None
    for p in glob.glob(os.path.join(A, "STOCK_CLOSING", "*", "*")):
        try:
            r = MS.read_closing(p)
        except Exception:
            continue
        if r.get("store") != "WHOLE STORES":
            continue
        if best is None or (E.as_on_key(r.get("as_on")), len(r["rows"])) > \
                           (E.as_on_key(best.get("as_on")), len(best["rows"])):
            best = r
    stock = {x["item"]: int(x["units"] or 0) for x in best["rows"]}
    sizes2 = {x["item"]: int(x["pack_size"] or 1) for x in best["rows"]}

    # now the master names exist, resolve the truncated sale keys onto them
    master = set(stock) | set(cost)
    mapping, ambiguous, unresolved = RS.build_map(list(sale), master)
    for k, full in mapping.items():
        src, dst = sale[k], sale[full]
        dst["u"] += src["u"]
        dst["days"] |= src["days"]
        dst["byday"].update(src["byday"])
        dst["last"] = max(dst["last"], src["last"]) if dst["last"] else src["last"]
        del sale[k]
    resolved_stats = {"renamed": len(mapping), "ambiguous": len(ambiguous),
                      "unresolved": len(unresolved)}

    MONTHS = 5.0
    vend_cad = {}
    for v in ven_items:
        per_month = len(vbills[v]) / MONTHS
        cad, want = E.cadence_for(int(vspend[v] / MONTHS), per_month)
        vend_cad[v] = {"cadence": cad, "tier_wanted": want,
                       "monthly_p": int(vspend[v] / MONTHS),
                       "bills_per_month": round(per_month, 1)}

    # Marg's LIST OF ITEMS export gives the MANUFACTURER for every item. It is
    # not the stockist, but distributors carry particular companies, so the
    # shop's own buying history turns one into a suggestion for the other.
    _p, _sh = IC.find_export(A)
    companies = IC.read_companies(_sh) if _sh else {}
    cv = IC.company_to_stockist(companies, item_ven)

    # THE BOX, measured. The GCD of every quantity an item has actually been
    # bought in: 42 items buy in tens, 24 in fives, 8 in twenties. One purchase
    # tells you nothing about a box, so those fall back to the default.
    import math as _m
    boxes = {}
    for it, qs in pq.items():
        qs = [x for x in qs if x > 0]
        if len(qs) < 2:
            continue
        g = 0
        for x in qs:
            g = _m.gcd(g, x)
        if g > 1:
            boxes[it] = g

    rows, orphans = [], []
    for it, s in sale.items():
        if it not in stock:
            continue
        vs = item_ven.get(it)
        if not vs:
            co, sv, cnt, strength = IC.suggest(it, companies, cv)
            orphans.append({"item": it, "sold": s["u"], "on_hand": stock.get(it, 0),
                            "company": co, "suggest": sv, "behind": cnt,
                            "strength": strength})
            continue
        v = vs.most_common(1)[0][0]
        last = dt.date(*map(int, s["last"].split("-")))
        peak = (max(s["byday"].values()) / s["u"]) if s["u"] else 0.0
        rows.append(E.plan_line({
            "item": it, "vendor": v, "on_hand": stock.get(it, 0),
            "rate_per_day": s["u"] / float(E.TRADING_DAYS),
            "sell_days": len(s["days"]),
            "pack_size": sizes2.get(it) or sizes.get(it) or 1,
            "cost_p": cost.get(it, 0),
            "single_source": len(vs) == 1,
            "days_since_sale": (TODAY - last).days,
            "peak_share": peak,
        }, E.CADENCE_DAYS[vend_cad[v]["cadence"]]))

    order = [r for r in rows if r["order_strips"] > 0]
    order.sort(key=lambda r: -r["value_p"])
    auto = [r for r in order if not r["confirm"]]
    ask = [r for r in order if r["confirm"]]

    # the budget rail: fill from the auto lines by value until the cap
    included, spent = [], 0
    for r in auto:
        if cap_p and spent + r["value_p"] > cap_p:
            continue
        included.append(r)
        spent += r["value_p"]
    deferred = [r for r in auto if r not in included]

    byv = collections.defaultdict(list)
    for r in included:
        byv[r["vendor"]].append(r)
    vendors = []
    for v, ls in sorted(byv.items(), key=lambda kv: -sum(x["value_p"] for x in kv[1])):
        vendors.append({"vendor": v, "cadence": vend_cad[v]["cadence"],
                        "monthly_p": vend_cad[v]["monthly_p"],
                        "lines": sorted(ls, key=lambda x: -x["value_p"]),
                        "value_p": sum(x["value_p"] for x in ls)})
    return {"as_on": best.get("as_on"), "cap_p": cap_p,
            "resolved": resolved_stats,
            "vendors": vendors, "confirm": ask, "deferred": deferred,
            "orphans": sorted(orphans, key=lambda o: -o["sold"]),
            "companies": len(companies),
            "totals": {"items_considered": len(rows), "lines_needed": len(order),
                       "auto": len(auto), "confirm": len(ask),
                       "included": len(included), "value_p": spent,
                       "confirm_value_p": sum(r["value_p"] for r in ask),
                       "orphans": len(orphans)}}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=60000, help="rupee cap for this run")
    ap.add_argument("--json", default=os.path.join(HERE, "po_plan.json"))
    a = ap.parse_args()
    plan = build(cap_p=a.cap * 100)
    with open(a.json, "w", encoding="utf-8") as fh:
        json.dump(plan, fh, separators=(",", ":"))
    t = plan["totals"]
    print("stock as on %s   cap Rs %s" % (plan["as_on"], "{:,}".format(a.cap)))
    print("  items considered   : %d" % t["items_considered"])
    print("  lines needing stock: %d" % t["lines_needed"])
    print("  auto-orderable     : %d" % t["auto"])
    print("  need your word     : %d  (Rs %s)" % (t["confirm"], "{:,}".format(t["confirm_value_p"] // 100)))
    print("  IN THIS RUN        : %d lines, %d vendors, Rs %s"
          % (t["included"], len(plan["vendors"]), "{:,}".format(t["value_p"] // 100)))
    print("  deferred by the cap: %d" % len(plan["deferred"]))
    print("  no vendor on record: %d" % t["orphans"])
    r = plan["resolved"]
    print("  truncated sale names resolved onto the item master: %d "
          "(ambiguous %d, unmatched %d)" % (r["renamed"], r["ambiguous"], r["unresolved"]))
    print()
    for v in plan["vendors"][:6]:
        print("  %-32s %-12s %2d lines  Rs %s"
              % (v["vendor"][:32], v["cadence"], len(v["lines"]),
                 "{:,}".format(v["value_p"] // 100)))
