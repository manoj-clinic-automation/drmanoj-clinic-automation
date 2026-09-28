#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figures_s436.py -- kit S436_STAFF_PAGES_CLEAN. Run on a SCRATCH COPY of the database (the installer makes one with the backup API right
after placing and seeding): the orthotic loss as the run holds it (lines, rupees, the items, the round), Amir's board in four lines, the four
salt tasks, the staff block's lines, the Needs-you line. Item names, rupees only.

  figures_s436.py --app DIR --db SCRATCH   (FINANCE_DB must name the same scratch copy)
"""
import argparse
import json
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
import sqlite3  # noqa: E402

c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}          # noqa: E731
rs = stock_app._loss_rs
db = sqlite3.connect(a.db, timeout=30)
run = db.execute("SELECT id, at, mrp_p, unpriced, groups, round_no, lines_n FROM stock_writeoff_run WHERE count_id=1 AND kind='ortho_close' ORDER BY id DESC LIMIT 1").fetchone()
if run:
    g = json.loads(run[4])
    print("the orthotic loss (run %s at %s IST): %d lines short, %s at selling price, %d without a price; %d book corrections; the round %s" % (
        run[0], stock_app._r_stamp(run[1]), len(g.get("ortho_loss", [])), rs(run[2]), run[3], len(g.get("ortho_fix", [])), run[5]))
    for x in g.get("ortho_loss", []):
        print("   %-32s %-8s %14s  (%s)" % (x["item"], x["short_text"], rs(x["mrp_p"]) if x["mrp_p"] is not None else "no price", x.get("price_src") or "-"))
    for x in g.get("ortho_fix", []):
        print("   %-32s %-8s %14s  (%s)" % (x["item"], x.get("over_text") or "", "book correction", x["why"][:60]))
else:
    print("the orthotic loss: NOT computed (the section is still open)")
am = c.get("/finance/stock/api/pad/amir/1", headers=H("amir")).get_json()
if am and am.get("ok"):
    print("Amir's board:")
    for r in am["made"]["rounds"]:
        print("   round %d: %d vouchers, %d entered%s, made %s" % (r["round_no"], r["total"], r["entered"], " (closed)" if r["closed"] else "", r["made_text"]))
    print("   closing stock: %s" % am.get("proof_hi"))
    print("   salt fixes: %s" % "; ".join("%s: %s -> %s [%s]" % (x["item"], x["marg_now"] or x["salt_now"], x["salt_new"], x["state"]) for x in am.get("salt_fix", [])))
    print("   rate to enter: %s" % ", ".join(x["item"] for x in am.get("rate_tasks", [])))
    print("   renames: %s" % ("shown (%d)" % len(am["renames"]["rows"]) if am.get("renames_ready") else ("hidden -- %s" % am.get("renames_wait_hi"))))
    print("   rounds order: %s" % am.get("rounds_order"))
st = c.get("/finance/stockmatch/api/state?count=1", headers=H("manoj")).get_json()
if st and st.get("ok"):
    print("the section: %s" % st.get("verdict_en"))
    print("   Darpan's page: %d lines still tappable (defaulted %d); progress %s" % (sum(1 for l in st["lines"] if l["open"] or l.get("defaulted")), sum(1 for l in st["lines"] if l.get("defaulted")), st["progress"]["en"]))
    if st.get("block"):
        print("   the staff block (Hindi): %s" % " | ".join(st["block"]["lines_hi"]))
ny = c.get("/finance/sanjeevni/api/needs-you", headers=H("manoj")).get_json() or {}
print("Needs you: %s" % "; ".join(l["text"] for l in ny.get("lines", []) if "Orthotics" in l.get("text", "")) or "-")
hb = c.get("/finance/stock/api/pad/hub/1", headers=H("manoj")).get_json()
if hb and hb.get("ok"):
    print("the hub: %s" % hb["ortho"]["verdict_en"])
    print("   follow-ups: %s" % "; ".join("%s %s" % ("ok" if x["ok"] else "--", x["en"]) for x in hb["ortho"]["conds"]))
m = db.execute("SELECT short_item, over_item, answer, note FROM stock_match WHERE count_id=1 AND id IN (SELECT MAX(id) FROM stock_match WHERE count_id=1 GROUP BY short_item, over_item) AND note LIKE '%salt wrong%'").fetchall()
print("pairs noted 'salt wrong in Marg': %s" % "; ".join("%s <-> %s %s" % (r[0], r[1], r[2]) for r in m))
