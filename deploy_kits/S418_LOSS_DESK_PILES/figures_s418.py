#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figures_s418.py -- kit S418_LOSS_DESK_PILES. READ-ONLY in effect: run on a SCRATCH COPY of the database (the
installer makes one with the backup API right after placing), it prints the four piles as the owner will see them
before he touches anything -- lines and rupees per pile, the write-off groups, the dial's preview, the first lines of
'With me' -- through the real app (Flask test client, header identity). Item names and rupees only.

  figures_s418.py --app DIR --db SCRATCH [--dump DIR]   (FINANCE_DB must name the same scratch copy)
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
print("count #%d of %s -- the desk as the owner will first see it" % (D["count_id"], D["day"]))
for k, t in (("open", "Still open"), ("with_me", "  With me / back in store"), ("writeoff", "  Write off as normal loss"),
             ("pursue", "  Pursue"), ("recount", "  Recount"), ("back", "Back in store / explained"), ("written_off", "Written off"),
             ("short", "Short at the count (all)")):
    x = T[k]
    print("  %-30s %4d lines  %14s at MRP  %14s at cost%s" % (t, x["n"], rs(x["mrp_p"]), rs(x["cost_p"]), ("  (%d without a price)" % x["unpriced"]) if x["unpriced"] else ""))
for g, v in T["writeoff"]["groups"].items():
    if v["n"]:
        print("    write-off pile, %-12s %4d lines  %14s at MRP  %14s at cost" % (g, v["n"], rs(v["mrp_p"]), rs(v["cost_p"])))
for g, v in T["written_off"]["groups"].items():
    if v["n"]:
        print("    written off already, %-8s %4d lines  %14s at MRP" % (g, v["n"], rs(v["mrp_p"])))
print("  dial: " + " | ".join("%s%s: +%d in (%s) / -%d out (%s), write-off pile %d" % (p["name"], " (now)" if p["current"] else "", p["into_n"], rs(p["into_p"]), p["out_n"], rs(p["out_p"]), p["writeoff_n"]) for p in D["preview"]))
for p in D["piles"]:
    print("  %s -- first lines:" % p["title"])
    for l in p["lines"][:6]:
        print("     %-28s %-22s %12s  %s" % (l["item"][:28], (l["short_text"] or l.get("over_text") or "")[:22], rs(l["mrp_p"]) if l["mrp_p"] is not None else "no price", l["why"][:70]))
print("  over on the shelf (never a loss): %d lines; orthotic lines on their own section: %d" % (len(D["over"]), D["orthotics_elsewhere"]))
hd = {k: v for k, v in (hub.get("desk") or {}).items() if k != "ok"}
print("  the hub's status card carries the same five totals: %s" % ("YES" if hd == T else "NO"))
print("  the old two figures, for the record: S228 board 'short' %s; hub 'still open' %s" % (
    rs(c.get("/finance/stock/api/loss/1", headers=H("manoj")).get_json()["totals"]["all_mrp_p"]), hub["words"]["open_rs"]))
if a.dump:
    os.makedirs(a.dump, exist_ok=True)
    for name, obj in (("piles.json", D), ("hub.json", hub), ("stockmatch.json", sm)):
        with open(os.path.join(a.dump, name), "w") as fh:
            json.dump(obj, fh)
    print("  dumped piles / hub / stockmatch JSON to %s" % a.dump)
