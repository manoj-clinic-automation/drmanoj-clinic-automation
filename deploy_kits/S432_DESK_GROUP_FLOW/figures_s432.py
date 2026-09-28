#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figures_s432.py -- kit S432_DESK_GROUP_FLOW. Run on a SCRATCH COPY of the database (the installer makes one with the backup API right
after placing): the desk's MEASURED times through the real app -- the first read (the cache built), the second (served), the light read,
a setting change (rebuilt) -- the cache's stamp, the stored watch, the statement's new totals with the Marg-negative lines, and the
section map's contradictions (stored section vs the name rule). Item names, rupees and milliseconds only.

  figures_s432.py --app DIR --db SCRATCH   (FINANCE_DB must name the same scratch copy)
"""
import argparse
import os
import sys
import time

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
import section_map  # noqa: E402
import sqlite3  # noqa: E402

c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}          # noqa: E731
rs = stock_app._loss_rs
db = sqlite3.connect(a.db, timeout=30)
root = db.execute("SELECT MAX(id) FROM stock_count WHERE id NOT IN (SELECT count_id FROM stock_count_part)").fetchone()[0] or 1
db.execute("DELETE FROM stock_pile_cache_meta WHERE count_id=?", (root,)); db.execute("DELETE FROM stock_pile_cache WHERE count_id=?", (root,)); db.commit()


def timed(path):
    t = time.time(); r = c.get(path, headers=H("manoj")); ms = int((time.time() - t) * 1000)
    return ms, r.status_code, (r.get_json(silent=True) or {}), len(r.data)


ms1, s1, j1, b1 = timed("/finance/stock/api/loss/%d/piles" % root)
ms2, s2, j2, b2 = timed("/finance/stock/api/loss/%d/piles" % root)
ms3, s3, j3, b3 = timed("/finance/stock/api/loss/%d/piles?lite=1" % root)
print("count #%d -- the desk read through the live files (the test client, this box):" % root)
print("  first read (the cache built from the report, the sales test once)  %6d ms  status %s  %s bytes  built=%s in %s ms, %s lines" % (ms1, s1, b1, j1.get("cache", {}).get("built"), j1.get("cache", {}).get("ms"), j1.get("cache", {}).get("lines_n")))
print("  second read (served from the cache)                                  %6d ms  status %s  %s bytes  built=%s" % (ms2, s2, b2, j2.get("cache", {}).get("built")))
print("  light read (?lite=1: the totals first)                              %6d ms  status %s  %s bytes" % (ms3, s3, b3))
t = time.time(); r = c.post("/finance/stock/api/loss/%d/pile/setting" % root, json={"key": "stock.allowance_pct", "value": "1.0"}, headers=H("manoj")); ms4 = int((time.time() - t) * 1000)
ms5, s5, j5, b5 = timed("/finance/stock/api/loss/%d/piles" % root)
print("  a setting saved (no change) %d ms; the read after it %d ms built=%s" % (ms4, ms5, j5.get("cache", {}).get("built")))
W = j2.get("watch") or {}
print("  the watch card: %s, as at %s (%s), %d traces shown, first-count %s" % ("stored" if W.get("stored") else "live", W.get("stored_text"), W.get("refreshed_by"), len(W.get("traces") or []), W.get("first_count_n")))
T = j2.get("totals") or {}
print("  totals: open %s (%s lines) · back %s · written off %s · short at the count %s (%s lines)" % (rs(T.get("open", {}).get("mrp_p")), T.get("open", {}).get("n"), rs(T.get("back", {}).get("mrp_p")), rs(T.get("written_off", {}).get("mrp_p")), rs(T.get("short", {}).get("mrp_p")), T.get("short", {}).get("n")))
print("  groups open: %s" % ", ".join("%s %d" % (g["title"], g["open_n"]) for g in j2.get("groups", []) if g.get("open_n")) or "none (the count is closed)")
D = c.get("/finance/stock/api/statement/%d" % root, headers=H("manoj")).get_json()
if D and D.get("ok"):
    O = D["overall"]
    print("the statement of count #%d (S431, with the S432 Marg-negative rule):" % root)
    print("  ALL SECTIONS  %4d lines (%d differ, %d matched)  short %14s  excess %14s  net %14s  without a price %d  Marg-negative %d" % (O["lines"], O["differing"], O["matched"], rs(O["short_p"]), rs(O["over_p"]), rs(O["net_p"]), O["unpriced"], O.get("neg_lines", 0)))
    for S in D["sections"]:
        Tt = S["totals"]
        print("  %-12s  %4d lines (%d differ, %d matched)  short %14s (%d lines)  excess %14s (%d lines)  net %14s  without a price %d  Marg-negative %d" % (
            S["title"].upper(), Tt["lines"], Tt["differing"], Tt["matched"], rs(Tt["short_p"]), Tt["short_lines"], rs(Tt["over_p"]), Tt["over_lines"], rs(Tt["net_p"]), Tt["unpriced"], Tt.get("neg_lines", 0)))
        if Tt.get("neg_text"):
            print("     Marg negative -- book correction, no goods: %s" % Tt["neg_text"])
        if Tt["unpriced_items"]:
            print("     no price -- name it: %s" % ", ".join(Tt["unpriced_items"]))
print("the section map (stock_item_section) against the name rule (section_map.classify):")
n = 0
for r in db.execute("SELECT item, section, source, by_user FROM stock_item_section ORDER BY item"):
    w = section_map.classify(r[0])
    if w != r[1]:
        n += 1
        print("  %-32s stored %-12s by name %-12s (%s%s)" % (r[0], r[1], w, r[2], (" " + r[3]) if r[3] else ""))
print("  %d of %d lines sit in a section their name contradicts" % (n, db.execute("SELECT COUNT(*) FROM stock_item_section").fetchone()[0]))
