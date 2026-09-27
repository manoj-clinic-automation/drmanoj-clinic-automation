#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figures_s430.py -- kit S430_DESK_FIRST_READ. READ-ONLY in effect: run on a SCRATCH COPY of the database (the installer makes one
with the backup API right after placing and seeding), it prints where the named items now sit and why, the close as it would run
(the groups, the period leakage line), and the watch list as it stands. Item names and rupees only.

  figures_s430.py --app DIR --db SCRATCH   (FINANCE_DB must name the same scratch copy)
"""
import argparse
import os
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--app", required=True)
ap.add_argument("--db", required=True)
a = ap.parse_args()
assert "scratch" in a.db or a.db.startswith("/tmp"), "figures run on a scratch copy only"
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
os.environ["FINANCE_DB"] = a.db
sys.path.insert(0, a.app)
os.chdir(a.app)
import finance_app as fa  # noqa: E402
import stock_app  # noqa: E402
import stock_watch  # noqa: E402
import sqlite3  # noqa: E402

c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}          # noqa: E731
D = c.get("/finance/stock/api/loss/1/piles", headers=H("manoj")).get_json()
rs = stock_app._loss_rs
T = D["totals"]
print("count #1 of %s -- the desk after S430, as the owner will see it (not closed)" % D["day"])
for k, t in (("open", "Still open"), ("with_me", "  With me / back in store"), ("writeoff", "  Write off"), ("bigloss", "  Big losses"), ("consume", "  Consumption & owner's use"),
             ("back", "Back in store / explained"), ("written_off", "Written off"), ("short", "Short at the count (all)")):
    x = T[k]
    print("  %-30s %4d lines  %14s at MRP  %14s at cost%s" % (t, x["n"], rs(x["mrp_p"]), rs(x["cost_p"]), ("  (%d without a price)" % x["unpriced"]) if x["unpriced"] else ""))
for g, v in T["writeoff"]["groups"].items():
    if v["n"]:
        print("    write-off pile, %-10s %4d lines  %14s at MRP  %14s at cost" % (g, v["n"], rs(v["mrp_p"]), rs(v["cost_p"])))
cons = [p for p in D["piles"] if p["key"] == "consume"][0]
for g in ("consume", "owner_use"):
    ls = [l for l in cons["lines"] if l["group"] == g]
    print("    consumption pile, %-10s %4d lines: %s" % (g, len(ls), ", ".join(l["item"] for l in ls)))
where = {}
for p in D["piles"]:
    for l in p["lines"]:
        where[l["item"]] = (p["key"], l)
for k in ("back", "written_off"):
    for l in D["done"][k]:
        where[l["item"]] = (k, l)
print("  the named items:")
for name in ("ECONORM CAP", "PARI CR 25", "VINBACTUM DS", "VINTAZ P 4500 INJ", "GLOCREPE", "CORTIRI", "CUFLIN D", "TYRO BR", "VFER 500", "G DRESS 10"):
    w = where.get(name)
    if not w:
        print("     %-22s not on this desk" % name); continue
    k, l = w
    print("     %-22s %-9s %-10s %-20s %10s  %s" % (name, k, l.get("group") or "", (l.get("short_text") or "")[:20], rs(l["mrp_p"]) if l["mrp_p"] is not None else "no price", (l.get("why") or "")[:90]))
B = D["block_preview"]
print("  'Close the count' would write off %d lines, %s at MRP; the staff block would read:" % (D["close"]["n"], rs(D["close"]["mrp_p"])))
for ln in B["lines_en"]:
    print("     EN  " + ln[:200])
# the period leakage line as it would read after the close: allowance + small + big at cost against 01-Apr -> 06-Sep sales
con = sqlite3.connect(a.db)
sp = stock_watch.Spine()
loss_cost = sum((l["cost_p"] or 0) for p in D["piles"] if p["key"] in ("writeoff", "bigloss") for l in p["lines"] if l.get("group") in ("allowance", "small", "big"))
sales = sp.q("SELECT COALESCE(SUM(net_p),0) AS p FROM sp_sale_bill WHERE date>'2026-04-01' AND date<='2026-09-06'")[0]["p"] if sp.ok else 0
print("  after the close, the Month section would read for September: '01-Apr → 06-Sep: leakage %s = %.1f%% of sales · budget 1%%' (allowance + small + big at cost; owner's use and old stock excluded)"
      % (rs(loss_cost), (100.0 * loss_cost / sales) if sales else 0))
W = c.get("/finance/stock/api/watch", headers=H("manoj")).get_json()
print("  traces: %d first-count lines collapsed to one line; %d other traces; Needs-you stock lines: %s" % (W["first_count_n"], len(W["traces"]),
      " | ".join(l["text"] for l in c.get("/finance/sanjeevni/api/needs-you", headers=H("manoj")).get_json().get("lines", []) if l.get("target") == "stock") or "-"))
print("  the watch list (%d):" % len(W["watch"]))
for x in W["watch"]:
    print("     %-30s %s" % (x["item"][:30], x["why"][:70]))
print("  left out of the watch list (%d):" % len(W["watch_left_out"]))
for it, why in W["watch_left_out"]:
    print("     %-30s %s" % (it[:30], why))
