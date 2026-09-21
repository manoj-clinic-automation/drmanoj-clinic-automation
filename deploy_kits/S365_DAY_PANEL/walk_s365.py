#!/usr/bin/env python3
"""walk_s365.py -- kit S365_DAY_PANEL. Drives the REAL app (patched files, sanjeevni_day.py placed)
over a SCRATCH COPY of finance.db and reads the new day panel for every filed day from the count:
its cash for the drawer must equal the one calculation's, its sums must close, the owner's
figures must hold, no machine word may reach him, and the old panel must still answer.
Prints dates, counts and rupees only.
  python3 walk_s365.py --app DIR --db scratch.db
"""
import argparse, json, os, sqlite3, subprocess, sys
ap = argparse.ArgumentParser(); ap.add_argument("--app", required=True); ap.add_argument("--db", required=True)
a = ap.parse_args()
PROBE = r'''
import json, os, sys
sys.path.insert(0, os.environ["APPDIR"])
os.environ.update(FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_DEV_USER="manoj", FINANCE_DEV_ROLE="owner")
import finance_app as fa
c = fa.app.test_client(); H = {"X-Clinic-User": "manoj", "X-Clinic-Role": "owner"}
dates = json.loads(os.environ["DATES"])
out = {"days": {}}
for d in dates:
    r = c.get("/finance/sanjeevni/api/day/" + d, headers=H); out["days"][d] = [r.status_code, r.get_json()]
r = c.get("/finance/sanjeevni/api/day/2026-09-15", headers={"X-Clinic-User": "darpan", "X-Clinic-Role": "maker"}); out["maker"] = r.status_code
os.environ["FINANCE_DEV_USER"] = ""; os.environ["FINANCE_DEV_ROLE"] = ""
r = c.get("/finance/sanjeevni/api/day/2026-09-15"); out["anon"] = r.status_code
os.environ["FINANCE_DEV_USER"] = "manoj"; os.environ["FINANCE_DEV_ROLE"] = "owner"
r = c.get("/finance/api/day/2026-09-15/full", headers=H); out["full"] = r.status_code
r = c.get("/finance/approvals", headers=H); t = r.get_data(as_text=True); out["page"] = [r.status_code, "/finance/sanjeevni/api/day/" in t, "function dayDetailOld" in t]
print("JSON:" + json.dumps(out))
'''
sys.path.insert(0, a.app)
import sanjeevni_cash as sc
con = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
rows = {r["date"]: r for r in sc.days(con, "2026-08-17", "9999-12-31")["rows"]}
env = dict(os.environ, APPDIR=a.app, FINANCE_DB=a.db, DATES=json.dumps(sorted(rows)))
p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=a.app)
O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
if not O:
    sys.exit("!! the app did not answer: " + p.stderr[-1500:])
n, fails = 0, []
def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got) + "]") if got is not None else ""))
    if not cond: fails.append(label)
def P(x):
    return None if x is None else int(str(x).replace(",", "")) * 100
D = O["days"]
check("the panel answers for every filed day from the count (%d days)" % len(D), all(v[0] == 200 and v[1].get("ok") for v in D.values()))
bad = [d for d, (s, v) in D.items() if v.get("drawer_p") != rows[d]["into_drawer_p"]]
check("every day's 'cash for the drawer' = the one calculation's", not bad, bad[:5])
bad = []
for d, (s, v) in D.items():
    sale, ret, upi, wc = P(v["sale"]["total"]), P(v["returns"]["total"]), P(v["upi"]["total"]), P(v["without_cash"]["total"])
    if sale - ret - upi - wc != v["cash_received_p"] and not v["needs_you"]:
        bad.append(d)
check("every day closes: sale - returns - UPI - without cash = cash received (or it says why)", not bad, bad[:5])
v = D["2026-09-15"][1]
check("15-Sep: cash received 11,291 (the owner's figure), procedure 239 shown apart", v["cash_received"] == "11,291" and v["without_cash"]["total"] == "239", v["cash_received"])
v = D["2026-08-20"][1]
check("20-Aug: bill 2777 paid at the clinic counter (3,000), cash for the drawer 4,939", v["paid_elsewhere"]["total"] == "3,000" and v["drawer"] == "4,939", (v["paid_elsewhere"]["total"], v["drawer"]))
v = D["2026-09-11"][1]
check("11-Sep: the credit note is a named return and the 2,300 is put back (drawer 17,223)",
      v["returns"]["count"] == 1 and "return" in (v["returns"]["list"][0]["name"] or "").lower() and v["drawer"] == "17,223", v["drawer"])
check("11-Sep: the return opens to its medicines", bool(v["returns"]["list"][0]["items"]))
v = D["2026-09-04"][1]
check("04-Sep: the Rs 200 between the filed day and Marg's bills is put to you in words",
      any("23,875" in x for x in v["needs_you"]), v["needs_you"])
blob = json.dumps(D)
check("no machine word reaches the owner (line_sum_vs_day_total, variance, upi_vs_statement)",
      not any(w in blob for w in ("line_sum_vs_day_total", "variance", "upi_vs_statement")))
check("August days say where their cash went (the handovers)", all(D[d][1].get("went") for d in D if d <= "2026-08-31"))
check("the Marg bill lists carry their medicines", sum(1 for d in D for b in D[d][1]["sale"]["list"] if b["items"]) > 100)
check("only the owner sees it: a staff login is refused, no login is refused", O["maker"] in (401, 403) and O["anon"] in (302, 401, 403), (O["maker"], O["anon"]))
check("the old detailed panel still answers (the fallback)", O["full"] == 200)
check("the approvals page carries the new panel and keeps the old one", O["page"][0] == 200 and O["page"][1] and O["page"][2], O["page"])
print("WALK_S365 %s -- %d/%d" % ("GREEN" if not fails else "RED", n - len(fails), n))
sys.exit(1 if fails else 0)
