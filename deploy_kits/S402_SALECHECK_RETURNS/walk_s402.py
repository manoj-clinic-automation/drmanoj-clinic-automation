#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s402.py -- kit S402_SALECHECK_RETURNS. THE REAL finance_app.py (a copy of /root/finance with the kit's two files)
over a SCRATCH COPY of the live finance.db, driven through Flask's test client with header identity (walk only).
Own rows dated 2099-12-05 (two credit notes) and 2099-12-06 (none), found by key.
  --app NEW  --old OLD (a copy of the box as it is = S400, the negative control)  --db scratch
Prints dates, its own bill keys, counts and rupees. No name, no number.
"""
import argparse
import datetime as dt
import json
import os
import sqlite3
import subprocess
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--app", required=True)
ap.add_argument("--old", required=True)
ap.add_argument("--db", required=True)
a = ap.parse_args()
assert "walk" in a.db or "scratch" in a.db or a.db.startswith("/tmp"), "refusing a non-scratch database"
n, fails = 0, []


def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:300] + "]") if got is not None else ""))
    if not cond:
        fails.append(label)


D5, D6 = "2099-12-05", "2099-12-06"
NOW = dt.datetime.now().replace(microsecond=0).isoformat()
con = sqlite3.connect(a.db, timeout=30)
con.row_factory = sqlite3.Row
roles = sorted(tuple(r) for r in con.execute("SELECT username, role FROM unit_role WHERE unit='salecheck' AND active=1"))
assert roles == [("bhati", "maker"), ("manoj", "checker")], "the salecheck unit is not seeded as S400 left it: %s" % roles


def plant():
    c = con
    c.execute("INSERT OR IGNORE INTO patient_ref (clinic_id, name, first_seen) VALUES ('W402-01','Walk Patient Two',?)", (D5,))
    pid = c.execute("SELECT id FROM patient_ref WHERE clinic_id='W402-01'").fetchone()[0]
    for d, cash in ((D5, 100000), (D6, 50000)):
        c.execute("DELETE FROM day_entry WHERE unit='medical' AND business_date=?", (d,))
        c.execute("INSERT INTO day_entry (unit, business_date, status, source, entered_by, entered_at) VALUES ('medical',?,'submitted','app','auto',?)", (d, NOW))
        eid = c.execute("SELECT id FROM day_entry WHERE unit='medical' AND business_date=?", (d,)).fetchone()[0]
        c.execute("INSERT INTO day_line (day_entry_id, service, mode, amount_p) VALUES (?,'pharmacy_sale','cash',?)", (eid, cash))
    E = {d: c.execute("SELECT id FROM day_entry WHERE unit='medical' AND business_date=?", (d,)).fetchone()[0] for d in (D5, D6)}
    c.execute("DELETE FROM sale_bill WHERE unit='medical' AND business_date IN (?,?)", (D5, D6))
    c.execute("DELETE FROM sale_line_item WHERE unit='medical' AND bill_no LIKE 'W402%'")
    for d, bill, net, cn in ((D5, "W402A001", 150000, 0), (D5, "W402C001", -30000, 1), (D5, "W402C002", -20000, 1), (D6, "W402B001", 50000, 0)):
        c.execute("INSERT INTO sale_bill (unit, business_date, bill_no, gross_p, disc_p, tax_p, drcr_p, net_p, cash_p, noncash_p, "
                  "is_credit_note, round_p, source_name, source_stamp, source_md5, written_at) VALUES "
                  "('medical',?,?,?,0,0,0,?,?,0,?,0,'walk_s402','20991205-000000','walk',?)", (d, bill, net, net, net, cn, NOW))
        c.execute("INSERT INTO sale_item (day_entry_id, unit, patient_ref_id, service, description, amount_p, mode, source, source_ref) "
                  "VALUES (?,'medical',?,?,'walk',?,'cash','ocr',?)", (E[d], pid, "pharmacy_return" if cn else "pharmacy", abs(net), bill))
    # a medicine line on a credit note: it must NOT reach Bhati's returns rows
    c.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, pack, qty_raw, amount_p) "
              "VALUES (?,'medical',?,'W402C001',1,1,'WALK RET TAB','walkrettab','10','1:0',30000)", (E[D5], D5))
    c.commit()


plant()
real = con.execute("SELECT MAX(business_date) FROM day_entry WHERE unit='medical' AND status IN ('submitted','draft') "
                   "AND business_date < '2099-01-01'").fetchone()[0] or "2026-09-24"
print("-- own rows planted: %s (sale 1,500; two credit notes 300 + 200) · %s (no return) · real unapproved day %s" % (D5, D6, real))

PROBE = r'''
import json, os, sys
sys.path.insert(0, os.environ["APPDIR"]); os.chdir(os.environ["APPDIR"])
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
import finance_app as fa
c = fa.app.test_client()
D5, D6, REAL = os.environ["D5"], os.environ["D6"], os.environ["REAL"]
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
def G(u, p):
    r = c.get(p, headers=H(u)); j = r.get_json(silent=True)
    return [r.status_code, j if j is not None else r.get_data(as_text=True)]
out = {}
out["list"] = G("bhati", "/finance/salecheck/api/days")
out["d5"] = G("bhati", "/finance/salecheck/api/day/" + D5)
out["d6"] = G("bhati", "/finance/salecheck/api/day/" + D6)
out["owner_d5"] = G("manoj", "/finance/sanjeevni/api/day/" + D5)
out["real_bhati"] = G("bhati", "/finance/salecheck/api/day/" + REAL)
out["real_owner"] = G("manoj", "/finance/sanjeevni/api/day/" + REAL)
pg = G("bhati", "/finance/salecheck"); out["page"] = [pg[0], "retBlock(" in pg[1], "Sale return" in pg[1], "S402_SALECHECK_RETURNS" in pg[1]]
GATE = ["/finance/approvals", "/finance/sanjeevni/api/day/" + D5, "/finance/sanjeevni/api/days", "/finance/sanjeevni/api/months",
        "/finance/sanjeevni/api/bank", "/finance/sanjeevni/api/needs-you", "/finance/darpan/kal/month", "/finance/darpan/kal/api/month",
        "/finance/darpan/kal/api/owner"]
out["bhati_gate"] = {p: G("bhati", p)[0] for p in GATE}
out["others"] = {u: G(u, "/finance/salecheck")[0] for u in ("darpan", "bhawna", "shavez", "stranger")}
import sale_check; out["version"] = sale_check.VERSION
print("JSON:" + json.dumps(out))
'''


def probe(appdir):
    env = dict(os.environ, APPDIR=appdir, FINANCE_DB=a.db, D5=D5, D6=D6, REAL=real, FINANCE_UI_DIR=os.path.join(appdir, "finance_ui"),
               FINANCE_ALLOW_HEADER_AUTH="1")
    p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=appdir)
    O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
    if not O:
        sys.exit("!! the app in %s did not answer: %s" % (appdir, p.stderr[-2500:]))
    return O


N, O = probe(a.app), probe(a.old)

print("-- 1  the day's returns block")
r5 = N["d5"][1]["returns"]
check("sale_check v1.1 answers; the walk day reads Sale return count 2, total 500", N["version"] == "1.1" and r5["count"] == 2 and r5["total"] == "500", (N["version"], r5))
check("expanded: exactly bill no · name · amount per return, amounts positive, whole rupees",
      [sorted(x.keys()) for x in r5["list"]] == [["amount", "bill", "name"], ["amount", "bill", "name"]]
      and [(x["bill"], x["amount"]) for x in r5["list"]] == [("W402C001", "300"), ("W402C002", "200")]
      and all(x["name"].startswith("Walk Patient") for x in r5["list"]), r5["list"])
check("no item fields for returns although a medicine line exists on W402C001", not any("items" in x for x in r5["list"]), r5["list"])
check("the sale side of the same day is unchanged: 1 Marg bill, 1,500, its cash received 1,000", N["d5"][1]["sale"]["bills"] == 1 and N["d5"][1]["sale"]["total"] == "1,500"
      and N["d5"][1]["cash_received"] == "1,000", N["d5"][1]["sale"])
r6 = N["d6"][1]["returns"]
check("a day with no return: count 0, total 0, no rows", r6["count"] == 0 and r6["total"] == "0" and r6["list"] == [], r6)
print("-- 2  the card line")
L = {d["date"]: d for d in N["list"][1]["days"]}
check("the card carries returns {count 2, total 500} -- the same figures as the block", L[D5]["returns"] == {"count": 2, "total": "500"}, L[D5].get("returns"))
check("the 0 day's card carries count 0 (the page omits the line)", L[D6]["returns"] == {"count": 0, "total": "0"}, L[D6].get("returns"))
check("the page carries the block, the words 'Sale return' and the S402 stamp", N["page"] == [200, True, True, True], N["page"])
print("-- 3  the same figures as the owner's day panel")
o5 = N["owner_d5"][1]["returns"]
check("the walk day: the owner's panel reads returns count 2, total 500 -- equal to Bhati's", o5["count"] == r5["count"] and o5["total"] == r5["total"], o5)
rb, ro = N["real_bhati"][1]["returns"], N["real_owner"][1]["returns"]
check("the real unapproved day %s: Bhati's count/total == the owner's panel's (%d · %s)" % (real, ro["count"], ro["total"]),
      N["real_bhati"][0] == 200 and rb["count"] == ro["count"] and rb["total"] == ro["total"], (rb["count"], rb["total"]))
check("the real day's rows are bill · name · amount only, one per credit note", len(rb["list"]) == ro["count"] and all(sorted(x.keys()) == ["amount", "bill", "name"] for x in rb["list"]), len(rb["list"]))
print("-- 4  access unchanged")
check("bhati is still refused on every S400 §6 address", all(s in (302, 401, 403) for s in N["bhati_gate"].values()), N["bhati_gate"])
check("darpan, bhawna, shavez, a stranger still cannot open the page", all(s in (302, 403) for s in N["others"].values()), N["others"])
print("-- 5  negative control: the box as it is (S400)")
o5r = O["d5"][1]["returns"]
check("NEGATIVE CONTROL: S400's day view carries item fields on a return row (the block did not exist)", O["version"] == "1.0" and any("items" in x for x in o5r["list"]), (O["version"], o5r["list"][:1]))
check("NEGATIVE CONTROL: S400's card has no returns line", "returns" not in {d["date"]: d for d in O["list"][1]["days"]}[D5], sorted({d["date"]: d for d in O["list"][1]["days"]}[D5].keys()))
check("NEGATIVE CONTROL: S400's page has no retBlock / S402 stamp", O["page"][0] == 200 and O["page"][1] is False and O["page"][3] is False, O["page"])
print(("WALK_S402 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S402 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
