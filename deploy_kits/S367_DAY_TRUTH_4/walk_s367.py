#!/usr/bin/env python3
"""walk_s367.py -- kit S367_DAY_TRUTH_4. Over a SCRATCH COPY of finance.db and the REAL app with the kit's
files placed: applies the D602 correction, then reads the day panel for every filed day from the count and
runs day_resync (dry) -- the day says how it was filed, 04-Sep reads Marg's 23,875 with nothing needing you,
the 200 goes to the pool with the day, both pool deposits read confirmed by the Yes Bank statement, every
day's drawer still equals the one calculation's, no staff login sees it. Prints dates, counts, rupees only.
  python3 walk_s367.py --app DIR --db scratch.db
"""
import argparse, json, os, sqlite3, subprocess, sys
ap = argparse.ArgumentParser(); ap.add_argument("--app", required=True); ap.add_argument("--db", required=True)
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
n, fails = 0, []
def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got) + "]") if got is not None else ""))
    if not cond: fails.append(label)
sys.path.insert(0, a.app)
import sanjeevni_cash as sc
con = sqlite3.connect(a.db)
pool_before = sc.days(con, "2026-08-17", "9999-12-31")["rows"][-1]["close"]["pool"]
con.close()
r1 = subprocess.run([sys.executable, "-B", os.path.join(HERE, "correct_0904.py"), "--db", a.db], stdout=subprocess.PIPE, text=True)
check("the D602 correction applies once on the scratch copy", r1.stdout.startswith("DONE"), r1.stdout.strip()[:80])
r2 = subprocess.run([sys.executable, "-B", os.path.join(HERE, "correct_0904.py"), "--db", a.db], stdout=subprocess.PIPE, text=True)
check("a second run changes nothing", r2.stdout.startswith("ALREADY"))
con = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
rows = {r["date"]: r for r in sc.days(con, "2026-08-17", "9999-12-31")["rows"]}
pool_after = sc.days(con, "2026-08-17", "9999-12-31")["rows"][-1]["close"]["pool"]
check("the 200 goes to the doctors' pool with 04-Sep's cash (and nowhere else)", pool_after - pool_before == 20000, (pool_after - pool_before) // 100)
PROBE = r'''
import json, os, sys
sys.path.insert(0, os.environ["APPDIR"])
os.environ.update(FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_DEV_USER="manoj", FINANCE_DEV_ROLE="owner")
import finance_app as fa, sanjeevni_day
c = fa.app.test_client(); H = {"X-Clinic-User": "manoj", "X-Clinic-Role": "owner"}
out = {"v": sanjeevni_day.VERSION, "days": {}}
for d in json.loads(os.environ["DATES"]):
    r = c.get("/finance/sanjeevni/api/day/" + d, headers=H); out["days"][d] = [r.status_code, r.get_json()]
out["maker"] = c.get("/finance/sanjeevni/api/day/2026-09-04", headers={"X-Clinic-User": "darpan", "X-Clinic-Role": "maker"}).status_code
print("JSON:" + json.dumps(out))
'''
env = dict(os.environ, APPDIR=a.app, FINANCE_DB=a.db, DATES=json.dumps(sorted(rows)))
p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=a.app)
O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
if not O:
    sys.exit("!! the app did not answer: " + p.stderr[-1500:])
D = O["days"]
check("the day panel is v1.1", O["v"] == "1.1", O["v"])
check("the panel answers for every filed day from the count (%d days)" % len(D), all(v[0] == 200 and v[1].get("ok") for v in D.values()))
bad = [d for d, (s, v) in D.items() if v.get("drawer_p") != rows[d]["into_drawer_p"]]
check("every day's 'cash for the drawer' = the one calculation's", not bad, bad[:5])
bad = [d for d, (s, v) in D.items() if not any(("filed automatically" in c["text"]) or ("filed on the old form" in c["text"]) for c in v["checks"])]
check("every day says how it was filed", len(bad) <= 3, bad[:5])
v = D["2026-09-04"][1]
T = " | ".join(c["text"] for c in v["checks"])
check("04-Sep: sale 23,875, nothing needs you, drawer 5,928", v["needs_you"] == [] and v["drawer"] == "5,928" and v["sale"]["total"] == "23,875", (v["needs_you"], v["drawer"]))
check("04-Sep: says filed automatically from Marg's 08:53 export, 17 bills, nobody typed it", "08:53 on 05-Sep (17 bills)" in T and "nobody typed it" in T)
check("04-Sep: says the later export (18 bills) and the correction under D602", "18 bills" in T and "D602" in T)
for d, amt in (("2026-09-03", "3,00,000"), ("2026-09-15", "1,00,000")):
    T = " | ".join(c["text"] for c in D[d][1]["checks"])
    check("%s: the %s pool deposit reads confirmed in the Yes Bank statement" % (d, amt), (amt + " deposited from the pool") in T and "confirmed in the Yes Bank statement" in T)
v = D["2026-09-15"][1]
check("15-Sep still 11,291 (the owner's figure)", v["cash_received"] == "11,291", v["cash_received"])
check("no staff login sees it", O["maker"] == 403, O["maker"])
rs = subprocess.run([sys.executable, "-B", os.path.join(a.app, "day_resync.py"), "--db", a.db, "--dry-run", "--no-reconcile"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
check("day_resync v4 runs; no approved day differs from Marg now; nothing it would change", rs.returncode == 0 and "APPROVED " not in rs.stdout
      and "WOULD_FIX" not in rs.stdout and "S367_DAY_TRUTH_4" in rs.stdout, rs.stdout.count("\n"))
print(("WALK_S367 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S367 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
