#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figures_s437.py -- kit S437_COUNT_PAGES_FINAL. Run on a SCRATCH COPY of the database: the RECEIVE vouchers made (how many, the biggest
lines), Amir's board in three lines, the CCM line as it now reads, the whole-piece candidates, Darpan's block as he sees it. Item names,
rupees only.

  figures_s437.py --app DIR --db SCRATCH   (FINANCE_DB must name the same scratch copy)
"""
import argparse
import json
import os
import sqlite3
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
import loss_piles  # noqa: E402

c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}          # noqa: E731
db = sqlite3.connect(a.db, timeout=30)
run = db.execute("SELECT id, at, by_user, lines_n, groups, round_no FROM stock_writeoff_run WHERE count_id=1 AND kind='receive_close' ORDER BY id LIMIT 1").fetchone()
if run:
    g = json.loads(run[4])
    rc, ie = g.get("receive", []), g.get("issue_earlier", [])
    print("the RECEIVE round by rule (run %s at %s IST, by %s): %d STOCK RECEIVE lines, %d STOCK ISSUE lines (written off earlier, on no voucher); round %s" % (run[0], stock_app._r_stamp(run[1]), run[2], len(rc), len(ie), run[5]))
    for x in sorted(rc, key=lambda x: -abs(x.get("change") or 0))[:8]:
        print("   RECEIVE %-28s Marg %4s -> %4s   + %s" % (x["item"], x.get("marg_from"), x.get("marg_to"), x.get("over_text")))
    for x in sorted(ie, key=lambda x: -abs(x.get("change") or 0))[:5]:
        print("   ISSUE   %-28s Marg %4s -> %4s   - %s" % (x["item"], x.get("marg_from"), x.get("marg_to"), x.get("short_text")))
else:
    print("the RECEIVE round: NOT made")
am = c.get("/finance/stock/api/pad/amir/1", headers=H("amir")).get_json()
if am and am.get("ok"):
    VF = am["made"].get("vouchers_flat") or []
    nI = sum(1 for v in VF if v["kind"] == "ISSUE")
    print("Amir's board: %d vouchers -- STOCK ISSUE 1..%d, STOCK RECEIVE 1..%d; %d keyed; pending lines %d" % (len(VF), nI, len(VF) - nI, sum(1 for v in VF if v["entered"]), am["made"]["pending_issue"] + am["made"]["pending_receive"]))
    for v in VF[:2] + [x for x in VF if x["kind"] == "RECEIVE"][:1]:
        print("   %s (%d lines): %s" % (v["title"], v["n"], " | ".join("%s (%s) Marg %s -> %s %s%s" % (l["item"], l["packing"], l["from_hi"], l["to_hi"], "- " if l["change"] < 0 else "+ ", l["qty_hi"]) for l in v["lines"][:3])))
    ccm = [(v["title"], l) for v in VF for l in v["lines"] if l["item"] == "CCM"]
    print("   CCM on the board: %s" % ("; ".join("%s: Marg %s -> %s, - %s" % (t, l["from_hi"], l["to_hi"], l["qty_hi"]) for t, l in ccm) or "no CCM line"))
    print("   Naam badlo: %s (proof %s)" % ("shown" if am.get("renames_ready") else ("hidden -- " + am.get("renames_wait_hi", "")), am.get("proof_state")))
hb = c.get("/finance/stock/api/pad/hub/1", headers=H("manoj")).get_json()
if hb and hb.get("ok"):
    print("the hub: not yet on a voucher %s; vouchers entered %s of %s" % (hb["vouchers"]["pending"], hb["vouchers"]["batches_entered"], hb["vouchers"]["batches_total"]))
D = c.get("/finance/stock/api/loss/1/piles", headers=H("manoj")).get_json()
if D and D.get("ok"):
    ccm = [l for l in (D.get("done") or {}).get("written_off", []) if l["item"] == "CCM"]
    print("the desk: CCM reads %s" % ("; ".join("short %s (Marg %s, counted %s)" % (l["short_text"], l.get("marg_text"), l.get("counted_text")) for l in ccm) or "not on the desk"))
    S = [s for s in D.get("settings", []) if s["key"] == "stock.whole_unit_items"]
    if S:
        print("   whole-piece list: %s" % S[0]["shown"])
        print("   candidates (%d): %s" % (len(S[0].get("candidates") or []), "; ".join("%s %s -> %s" % (x["item"], x["packing"], x["word"]) for x in (S[0].get("candidates") or []))))
    B = D.get("block")
    if B and B.get("tables"):
        T = B["tables"]
        print("Darpan's block: %s" % T["kul"]["hi"])
        print("   %s -- %d rows, total %s; first rows: %s" % (T["badi"]["hi"], T["badi"]["n"], T["badi"]["rs"], "; ".join("%s Marg %s gina %s kami %s %s" % (r["item"], r["marg_hi"], r["counted_hi"], r["short_hi"], r["rs"]) for r in T["badi"]["rows"][:3])))
        print("   %s -- %d rows (collapsed), total %s" % (T["chhoti"]["hi"], T["chhoti"]["n"], T["chhoti"]["rs"]))
        print("   %s -- %d rows (collapsed)" % (T["ortho"]["hi"], T["ortho"]["n"]))
st = c.get("/finance/stock/api/statement/1", headers=H("manoj")).get_json()
if st and st.get("ok", True) and st.get("sections"):
    med = [s for s in st["sections"] if s["key"] == "Medicines"][0]
    ov = [l for l in med["lines"] if l["over"] or l.get("neg_marg")]
    print("the statement: %d shelf-more / Marg-negative medicine lines; e.g. %s" % (len(ov), "; ".join("%s: %s" % (l["item"], l["voucher"]) for l in ov[:3])))
    ccm = [l for l in med["lines"] + med["matched"] if l["item"] == "CCM"]
    if ccm:
        print("   CCM: Marg %s, counted %s, short %s" % (ccm[0]["marg_text"], ccm[0]["counted_text"], ccm[0]["short_text"]))
