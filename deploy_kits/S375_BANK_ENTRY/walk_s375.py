#!/usr/bin/env python3
"""walk_s375.py -- kit S375_BANK_ENTRY. The REAL app over a SCRATCH COPY of finance.db: the owner records a
cash deposit and each of the three transfer routes; a transfer changes no sale, no day and no income; a
deposit leaves the doctors' pool at once; a transfer out of ICICI lowers what ICICI holds; the entries read
"waiting for the statement" and turn "confirmed" where the loaded Yes Bank statement shows them; a bad route,
a future date, a repeat and an amount larger than ICICI holds are all refused; an unconfirmed entry can be
removed and a confirmed one cannot; staff are refused throughout. Prints dates, counts and rupees only.
  python3 walk_s375.py --app DIR --db scratch.db
"""
import argparse, json, os, sqlite3, subprocess, sys
ap = argparse.ArgumentParser(); ap.add_argument("--app", required=True); ap.add_argument("--db", required=True)
a = ap.parse_args()
n, fails = 0, []
def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got) + "]") if got is not None else ""))
    if not cond: fails.append(label)
PROBE = r'''
import json, os, sys, datetime as dt
sys.path.insert(0, os.environ["APPDIR"]); os.chdir(os.environ["APPDIR"])
os.environ.update(FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_DEV_USER="manoj", FINANCE_DEV_ROLE="owner")
import finance_app as fa, sanjeevni_approvals as sa, sanjeevni_cash as sc
c = fa.app.test_client(); H = {"X-Clinic-User": "manoj", "X-Clinic-Role": "owner"}
M = {"X-Clinic-User": "darpan", "X-Clinic-Role": "maker"}
out = {"v": sa.VERSION}
def money():
    with fa.app.app_context():
        con = fa.db()
        r = sc.days(con, "2026-08-17", "9999-12-31")
        row = r["rows"][-1]
        m = {k: v for k, v in row["close"].items()}
        months = {x["ym"]: (x["sale_p"], x["upi_p"], x["cash_p"]) for x in sc.month_rows(con)}
        con.commit()
    return m, months
out["before"] = money()
BANK = "/finance/sanjeevni/api/bank"
YDAY = (dt.date.today() - dt.timedelta(days=1)).isoformat()
TOM = (dt.date.today() + dt.timedelta(days=1)).isoformat()
# 1 a deposit he records himself
r = c.post(BANK + "/deposit", json=dict(date=YDAY, amount=50000, place="Bareilly"), headers=H); out["dep"] = [r.status_code, r.get_json()]
out["dep_again"] = c.post(BANK + "/deposit", json=dict(date=YDAY, amount=50000), headers=H).status_code
out["dep_future"] = c.post(BANK + "/deposit", json=dict(date=TOM, amount=100), headers=H).status_code
out["dep_zero"] = c.post(BANK + "/deposit", json=dict(date=YDAY, amount=0), headers=H).status_code
# 2 the three routes
for k, (f, t, amt) in {"icici_yes": ("icici", "yesbank", 20000), "icici_huf": ("icici", "huf_icici", 10000),
                       "yes_huf": ("yesbank", "huf_yesbank", 5000)}.items():
    r = c.post(BANK + "/transfer", json=dict(date=YDAY, amount=amt, **{"from": f, "to": t}), headers=H)
    out[k] = [r.status_code, r.get_json()]
out["bad_route"] = c.post(BANK + "/transfer", json=dict(date=YDAY, amount=100, **{"from": "huf_icici", "to": "icici"}), headers=H).status_code
out["repeat"] = c.post(BANK + "/transfer", json=dict(date=YDAY, amount=20000, **{"from": "icici", "to": "yesbank"}), headers=H).status_code
r = c.post(BANK + "/transfer", json=dict(date=YDAY, amount=99999999, **{"from": "icici", "to": "yesbank"}), headers=H)
out["over"] = [r.status_code, (r.get_json() or {}).get("message", "")[:120]]
out["after"] = money()
# 3 what the page's Bank view now says
j = c.get("/finance/sanjeevni/api/bank?month=" + YDAY[:7], headers=H).get_json()
out["bank"] = [j.get("ok"), j.get("icici"), [(x["date"], x["amount"], x["status"]) for x in j.get("deposits", [])],
               [(x["date"], x["amount"], x["frm_key"], x["to_key"], x["status"], x["leaves"]) for x in j.get("transfers", [])]]
# 4 the September deposits the statement already proves cannot be removed; ours can
dep = [x for x in j["deposits"] if x.get("source") == "pool"]
conf = next((x for x in dep if x["status"] == "ok"), None)
mine = next((x for x in dep if x["status"] != "ok"), None)
out["undo_confirmed"] = c.post(BANK + "/undo", json=dict(kind="deposit", id=conf["id"]), headers=H).status_code if conf else None
tid = j["transfers"][0]["id"]
out["undo_transfer"] = c.post(BANK + "/undo", json=dict(kind="transfer", id=tid), headers=H).status_code
out["undo_mine"] = c.post(BANK + "/undo", json=dict(kind="deposit", id=mine["id"]), headers=H).status_code if mine else None
out["end"] = money()
# 5 staff
out["staff"] = [c.post(BANK + "/deposit", json=dict(date=YDAY, amount=100), headers=M).status_code,
                c.post(BANK + "/transfer", json=dict(date=YDAY, amount=100, **{"from": "icici", "to": "yesbank"}), headers=M).status_code,
                c.post(BANK + "/undo", json=dict(kind="transfer", id=1), headers=M).status_code]
r = c.get("/finance/approvals", headers=H); t = r.get_data(as_text=True)
out["page"] = [r.status_code, "Record a cash deposit" in t, "Record a transfer" in t, "huf_yesbank" in t,
               "id=\"needsCard\"" in t, "id=\"checksCard\"" in t, "S375_BANK_ENTRY" in t]
print("JSON:" + json.dumps(out, default=str))
'''
env = dict(os.environ, APPDIR=a.app, FINANCE_DB=a.db)
p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=a.app)
O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
if not O:
    sys.exit("!! the app did not answer: " + p.stderr[-2000:])
check("sanjeevni_approvals is v1.1", O["v"] == "1.1", O["v"])
check("a cash deposit he records is taken", O["dep"][0] == 200 and O["dep"][1].get("ok"), O["dep"])
check("the same deposit twice, a future date and a zero amount are all refused", [O["dep_again"], O["dep_future"], O["dep_zero"]] == [409, 400, 400],
      [O["dep_again"], O["dep_future"], O["dep_zero"]])
check("all three transfer routes are taken (ICICI→Yes Bank, ICICI→its HUF, Yes Bank→its HUF)",
      all(O[k][0] == 200 and O[k][1].get("ok") for k in ("icici_yes", "icici_huf", "yes_huf")),
      {k: O[k][0] for k in ("icici_yes", "icici_huf", "yes_huf")})
check("a route that is not his (HUF back into the pharmacy) is refused", O["bad_route"] == 400, O["bad_route"])
check("the same transfer twice is refused", O["repeat"] == 409, O["repeat"])
check("more than ICICI holds is refused, in words", O["over"][0] == 409 and "already been moved out" in O["over"][1], O["over"])
check("a transfer to the HUF says it leaves the pharmacy", any(x[5] for x in O["bank"][3] if x[3].startswith("huf")),
      [(x[3], x[5]) for x in O["bank"][3]])
b4, af = O["before"], O["after"]
check("the deposit left the doctors' pool at once (pool down by 50,000)", b4[0]["pool"] - af[0]["pool"] == 5000000,
      (b4[0]["pool"] - af[0]["pool"]) // 100)
check("NO transfer changed a month's sale, online or cash — not one figure", b4[1] == af[1],
      [k for k in af[1] if af[1][k] != b4[1].get(k)])
check("the drawer and what the doctors hold are untouched by the transfers",
      b4[0]["drawer"] == af[0]["drawer"] and (b4[0]["with_doctors"] - af[0]["with_doctors"]) == 5000000,
      (af[0]["drawer"], (b4[0]["with_doctors"] - af[0]["with_doctors"]) // 100))
ic = O["bank"][1]
check("ICICI's position is stated and 30,000 has been taken off it", ic and ic["out"] == "30,000", ic)
check("every new entry reads waiting for the statement; the proven September deposits still read confirmed",
      any(x[2] == "wait" for x in O["bank"][2]) and sum(1 for x in O["bank"][2] if x[2] == "ok") >= 2,
      [(x[0], x[2]) for x in O["bank"][2]])
check("a deposit the statement proves cannot be removed; an unconfirmed one can",
      O["undo_confirmed"] == 409 and O["undo_transfer"] == 200 and O["undo_mine"] == 200,
      [O["undo_confirmed"], O["undo_transfer"], O["undo_mine"]])
check("after the removals the pool is back where it started", O["end"][0]["pool"] == b4[0]["pool"],
      (O["end"][0]["pool"] - b4[0]["pool"]) // 100)
check("staff cannot record or remove anything", O["staff"] == [403, 403, 403], O["staff"])
check("the page carries both buttons, the three routes and the tree", all(O["page"]), O["page"])
print(("WALK_S375 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S375 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
