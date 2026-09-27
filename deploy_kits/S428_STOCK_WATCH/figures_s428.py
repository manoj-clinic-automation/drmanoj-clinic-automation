#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figures_s428.py -- kit S428_STOCK_WATCH. READ-ONLY in effect: run on a SCRATCH COPY of the database (the installer makes one
with the backup API right after placing), it prints what the owner will see -- whether a full count is due and what Amir sees,
the next morning's roster (the real items and why each was chosen), the watch list as it stands, this month's leakage line --
through the real app (Flask test client, header identity). Item names and rupees only.

  figures_s428.py --app DIR --db SCRATCH   (FINANCE_DB must name the same scratch copy)
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

c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}          # noqa: E731
W = c.get("/finance/stock/api/watch", headers=H("manoj")).get_json()
am = c.get("/finance/stock/api/pad/amir/1", headers=H("amir")).get_json()
sm = c.get("/finance/stockmatch/api/state?count=1", headers=H("darpan")).get_json()
ny = c.get("/finance/sanjeevni/api/needs-you", headers=H("manoj")).get_json()
P = W["plan"]
print("the stock watch, as the owner will first see it (today %s)" % P["today"])
print("  full count: last closed %s; every %g months; next due from %s; %s" % (P["last"]["as_on"] if P["last"] else "-", P["cadence_months"], P["due_from"],
      ("DUE -- plan %s%s" % (P["plan"]["status"], (" Sunday " + P["plan"]["sunday_text"]) if P["plan"].get("sunday") else " (Amir picks from %s)" % ", ".join(P["plan"]["window_text"]))) if P.get("plan") else "not due today"))
aw = (am.get("watch") or {})
print("  Amir's board: %s; bill entry pending %d; fix lines %d" % ("the Sunday buttons: " + ", ".join(aw["plan"]["window_text"]) if aw.get("plan") and aw["plan"]["status"] != "confirmed" else "no Sunday to pick", len(aw.get("bill_pending") or []), len(aw.get("fixes") or [])))
R = W["roster_today"]
print("  spot mornings %s, up to %d items; today %s: %s" % (", ".join(W["spot_days"]), W["cap"], R["day_text"], ("%d item(s): %s" % (len(R["items"]), ", ".join(x["item"] for x in R["items"]))) if R["items"] else ("no list" + ("" if R["is_spot_day"] else " (not a spot morning)"))))
print("  next morning %s -- the roster the job would write:" % W["next_day_text"])
for x in W["roster_next"]:
    print("     %-28s %s" % (x["item"][:28], x["reason"]))
print("  Darpan's Stock milaan: roster items %d, plan question %s, loss lines %d, traces to see %d" % (len((sm.get("watch") or {}).get("roster", {}).get("items", [])), "yes" if (sm.get("watch") or {}).get("plan") else "no",
      len((sm.get("watch") or {}).get("losses", [])), len((sm.get("watch") or {}).get("traces", []))))
print("  the watch list (%d):" % len(W["watch"]))
for x in W["watch"][:24]:
    print("     %-28s %-34s %s" % (x["item"][:28], x["why"][:34], " · ".join("%s %s" % (p["at_text"], p["qty_text"]) for p in x["points"]) or "no count yet"))
print("  traces open on the desk's Big-loss lines: %d (%s)" % (len(W["traces"]), ", ".join(sorted({t["verdict"] for t in W["traces"]})) or "-"))
for t in W["traces"][:6]:
    print("     %-28s %-10s %-22s %s" % (t["item"][:28], t["verdict"], t["gap_text"], (t["fix"] or "; ".join(f["text"] for f in t["findings"] if not f["ok"]))[:70]))
L = W["leak"]
print("  leakage this month: %s%s" % (L["text"] if L else "-", "" if not L or L.get("pct") is None else (" -- " + ("RED" if L["red"] else "green"))))
if W.get("leak_prev"):
    print("  leakage previous month: %s" % W["leak_prev"]["text"])
print("  tap vs bill lines: %d; owner asks pending: %d; points on record: %d" % (len(W["tap_vs_bill"]), len(W["asks"]), W["points_n"]))
print("  Needs you carries %d stock-watch line(s): %s" % (sum(1 for l in ny.get("lines", []) if l.get("target") == "stock"), " | ".join(l["text"] for l in ny.get("lines", []) if l.get("target") == "stock") or "-"))
