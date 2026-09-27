#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figures_s427.py -- kit S427_LOSS_DESK_RULINGS. READ-ONLY in effect: run on a SCRATCH COPY of the database (the
installer makes one with the backup API right after placing), it prints the four piles under the new rules as the owner
will see them -- lines and rupees per pile, the write-off groups, where the named items sit (TYRO BR, VFER, G DRESS,
LEUKOCREPE, BLADE), the lines the sales-after-count test closed, and the staff block as Darpan will see it after the
close -- through the real app (Flask test client, header identity). Item names and rupees only.

  figures_s427.py --app DIR --db SCRATCH [--dump DIR]   (FINANCE_DB must name the same scratch copy)
"""
import argparse
import json
import os
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--app", required=True)
ap.add_argument("--db", required=True)
ap.add_argument("--dump", default="")
a = ap.parse_args()
assert "scratch" in a.db or a.db.startswith("/tmp"), "figures run on a scratch copy only"
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
os.environ["FINANCE_DB"] = a.db
sys.path.insert(0, a.app)
os.chdir(a.app)
import finance_app as fa  # noqa: E402
import stock_app  # noqa: E402

c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}          # noqa: E731
D = c.get("/finance/stock/api/loss/1/piles", headers=H("manoj")).get_json()
hub = c.get("/finance/stock/api/pad/hub/1", headers=H("manoj")).get_json()
sm = c.get("/finance/stockmatch/api/state?count=1", headers=H("darpan")).get_json()
rs = stock_app._loss_rs
T = D["totals"]
print("count #%d of %s -- the desk under the 27-Sep rulings, as the owner will first see it" % (D["count_id"], D["day"]))
for k, t in (("open", "Still open"), ("with_me", "  With me / back in store"), ("writeoff", "  Write off"), ("bigloss", "  Big losses"),
             ("consume", "  Consumption"), ("back", "Back in store / explained"), ("written_off", "Written off"), ("short", "Short at the count (all)")):
    x = T[k]
    print("  %-30s %4d lines  %14s at MRP  %14s at cost%s" % (t, x["n"], rs(x["mrp_p"]), rs(x["cost_p"]), ("  (%d without a price)" % x["unpriced"]) if x["unpriced"] else ""))
for g, v in T["writeoff"]["groups"].items():
    if v["n"]:
        print("    write-off pile, %-12s %4d lines  %14s at MRP  %14s at cost" % (g, v["n"], rs(v["mrp_p"]), rs(v["cost_p"])))
where = {}
for p in D["piles"]:
    for l in p["lines"]:
        where[l["item"]] = (p["key"], l)
for l in D["over"]:
    where[l["item"]] = ("over", l)
for k in ("back", "written_off"):
    for l in D["done"][k]:
        where[l["item"]] = (k, l)
print("  the named items:")
for name in ("TYRO BR", "VFER 500", "G DRESS 10", "G DRESS 20", "LEUKOCREPE 8 CM", "LEUKOCREPE 10CM*4IN", "LEUKOBAND 4 INCH", "BLADE", "GLOVES SURGICAL 7",
             "ZIG ZAG COTTON 500GM", "INTACOXIA-60", "DOLOGESIC SP", "GEMCAL XT TABLETS", "ETOZOX 90", "ROSIKA FORTE", "BIO D3 MAX"):
    w = where.get(name)
    if not w:
        print("     %-24s not on this desk" % name)
        continue
    k, l = w
    print("     %-24s %-10s %-9s %-22s %12s  %s" % (name, k, l.get("group") or "", (l.get("short_text") or l.get("over_text") or "")[:22],
                                                   rs(l["mrp_p"]) if l["mrp_p"] is not None else "no price", (l.get("why") or "")[:80]))
for p in D["piles"]:
    print("  %s -- first lines:" % p["title"])
    for l in p["lines"][:8]:
        print("     %-28s %-22s %12s  %s" % (l["item"][:28], (l["short_text"] or "")[:22], rs(l["mrp_p"]) if l["mrp_p"] is not None else "no price", l["why"][:78]))
print("  sold after the count -- closed by the system: %d" % len(D["sold_after"]))
for l in D["sold_after"]:
    t = l["test"]
    print("     %-28s counted %s, sold since %s, bought %s" % (l["item"][:28], t["counted_text"], t["sold_text"], t["bought_text"]))
print("  over on the shelf (never a loss): %d lines; orthotic lines on their own section: %d" % (len(D["over"]), D["orthotics_elsewhere"]))
B = D["block_preview"]
print("  'Close the count' would write off %d lines, %s at MRP; the staff block would read:" % (D["close"]["n"], rs(D["close"]["mrp_p"])))
for ln in B["lines_hi"]:
    print("     HI  " + ln)
for ln in B["lines_en"]:
    print("     EN  " + ln)
print("  closed already: %s" % ("yes, %s" % D["block"]["at_text"] if D["block"] else "no -- the owner closes"))
hd = {k: v for k, v in (hub.get("desk") or {}).items() if k != "ok"}
print("  the hub's status card carries the same totals: %s" % ("YES" if hd == T else "NO"))
print("  Stock milaan: block pinned %s; Dobara ginna hai answers so far: %d" % ("yes" if sm.get("block") else "no (not yet closed)", len(sm.get("recounts") or [])))
if a.dump:
    os.makedirs(a.dump, exist_ok=True)
    for name, obj in (("piles.json", D), ("hub.json", hub), ("stockmatch.json", sm)):
        with open(os.path.join(a.dump, name), "w") as fh:
            json.dump(obj, fh)
    print("  dumped piles / hub / stockmatch JSON to %s" % a.dump)
