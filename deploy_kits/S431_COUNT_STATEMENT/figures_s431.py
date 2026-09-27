#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figures_s431.py -- kit S431_COUNT_STATEMENT. READ-ONLY in effect: run on a SCRATCH COPY of the database (the installer makes one with the
backup API right after placing), it prints the statement's figures for the report's owner lines: the three sections' totals at selling
price, the orthotic block, the unpriced residue per section (named), the price sources, the close as the statement counts it. Item names
and rupees only.

  figures_s431.py --app DIR --db SCRATCH   (FINANCE_DB must name the same scratch copy)
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

c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}          # noqa: E731
D = c.get("/finance/stock/api/statement/1", headers=H("manoj")).get_json()
rs = stock_app._loss_rs
print("count #%d of %s -- the count statement, section by section, at SELLING PRICE (built %s)" % (D["count_id"], D["day"], D["built_text"]))
print("  price rule: %s" % D["price_rule"])
O = D["overall"]
print("  ALL SECTIONS  %4d lines (%d differ, %d matched)  short %14s  excess %14s  net %14s  without a price %d" % (O["lines"], O["differing"], O["matched"], rs(O["short_p"]), rs(O["over_p"]), rs(O["net_p"]), O["unpriced"]))
for S in D["sections"]:
    T = S["totals"]
    print("  %-12s  %4d lines (%d differ, %d matched)  short %14s (%d lines)  excess %14s (%d lines)  net %14s  swaps %d  without a price %d" % (
        S["title"].upper(), T["lines"], T["differing"], T["matched"], rs(T["short_p"]), T["short_lines"], rs(T["over_p"]), T["over_lines"], rs(T["net_p"]), T["swaps"], T["unpriced"]))
    if T["unpriced_items"]:
        print("     no price -- name it: %s" % ", ".join(T["unpriced_items"]))
    print("     price sources: %s" % ", ".join("%s %d" % (k, v) for k, v in sorted(T["sources"].items())))
    if S.get("groups"):
        print("     the close's groups here: %s%s%s" % ("; ".join("%s %d (%s)" % (g["title"], g["n"], rs(g["short_p"])) for g in S["groups"]), ("; back in store %d" % S["back"]) if S.get("back") else "", ("; open %d" % S["open"]) if S.get("open") else ""))
    if S.get("block"):
        B = S["block"]
        print("     orthotic block: lines still open (Darpan) %d%s; awaiting the owner's word %d%s; not yet on a voucher %d%s; renames unverified %d of %d; %s" % (
            B["open_lines"], (" (%s)" % ", ".join(B["open_items"])) if B["open_items"] else "", B["await_owner"], (" (%s)" % ", ".join(B["await_owner_items"])) if B["await_owner_items"] else "",
            B["not_vouchered"], (" (%s)" % ", ".join(B["not_vouchered_items"][:8])) if B["not_vouchered_items"] else "",
            B["renames_unverified"], B["renames_total"], B["verdict"]))
        top = sorted(S["lines"], key=lambda l: -(l["short_p"] or 0))[:8]
        print("     the largest orthotic shortages: %s" % "; ".join("%s %s %s (%s)" % (l["item"], l["short_text"], rs(l["short_p"]) if l["price_p"] else "no price", l["price_src"] or "-") for l in top if l["short"]))
C = D.get("close")
if C:
    print("  the close (%s by %s) as the statement counts it: %d lines written off, %s at the desk's MRP; %d back in store; %d open; groups %s" % (
        C["at_text"], C["by"], C["written_off"], rs(C["written_off_p"]), C["back"], C["open"], ", ".join("%s %d (%s)" % (g, v["n"], rs(v["mrp_p"])) for g, v in sorted(C["groups"].items()))))
F = D.get("frozen_list") or []
print("  frozen copies: %d%s" % (len(F), (" -- latest as at %s IST by %s, fingerprint %s" % (F[0]["made_text"], F[0]["made_by"], F[0]["md5"][:8])) if F else ""))
