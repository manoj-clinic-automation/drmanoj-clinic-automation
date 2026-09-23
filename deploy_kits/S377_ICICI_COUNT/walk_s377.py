#!/usr/bin/env python3
"""walk_s377.py -- kit S377_ICICI_COUNT (F-615). The REAL app over a SCRATCH COPY of finance.db:

  * his real 20-Sep transfers -- 2,50,000 and the 40,000 the page refused -- both go in, and the one the old
    rule refused is RECORDED with the shortfall named instead;
  * the anchor seed then puts the count on the bank's own closing balance, and the position reads
    that balance + the settlements credited since - what has been moved out, never below zero;
  * the seed is idempotent;
  * every other refusal still stands (future date, before the anchor, zero, repeat, a route not his);
  * no month's sale, online or cash moves; staff are refused; the page says where the count starts.

Prints dates, counts and rupees only.
  python3 walk_s377.py --app DIR --db scratch.db --seed SEED.py
"""
import argparse, json, os, subprocess, sys
ap = argparse.ArgumentParser(); ap.add_argument("--app", required=True); ap.add_argument("--db", required=True)
ap.add_argument("--seed", required=True)
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
B = "/finance/sanjeevni/api/bank"
out = {"v": sa.VERSION, "stage": os.environ["STAGE"]}
def months():
    with fa.app.app_context():
        con = fa.db(); m = {x["ym"]: (x["sale_p"], x["upi_p"], x["cash_p"]) for x in sc.month_rows(con)}; con.commit()
    return m
if os.environ["STAGE"] == "before":
    out["months"] = months()
    for amt in (250000, 40000):
        r = c.post(B + "/transfer", json={"date": "2026-09-20", "amount": amt, "from": "icici", "to": "yesbank"}, headers=H)
        out["t%d" % amt] = [r.status_code, r.get_json()]
    with fa.app.app_context():
        con = fa.db()
        out["rows"] = [(t["date"], t["amount_p"], t["frm"], t["to"]) for t in sa.transfers(con)]
        out["pos"] = sa.icici_position(con); con.commit()
    out["months_after"] = months()
    j = c.get(B + "?month=2026-09", headers=H).get_json(); out["icici_view"] = j.get("icici")
else:
    with fa.app.app_context():
        con = fa.db(); out["pos"] = sa.icici_position(con); con.commit()
    j = c.get(B + "?month=2026-09", headers=H).get_json(); out["icici_view"] = j.get("icici")
    TOM = (dt.date.today() + dt.timedelta(days=1)).isoformat()
    out["refusals"] = [
        c.post(B + "/transfer", json={"date": TOM, "amount": 100, "from": "icici", "to": "yesbank"}, headers=H).status_code,
        c.post(B + "/transfer", json={"date": "2026-08-01", "amount": 100, "from": "icici", "to": "yesbank"}, headers=H).status_code,
        c.post(B + "/transfer", json={"date": "2026-09-20", "amount": 0, "from": "icici", "to": "yesbank"}, headers=H).status_code,
        c.post(B + "/transfer", json={"date": "2026-09-20", "amount": 40000, "from": "icici", "to": "yesbank"}, headers=H).status_code,
        c.post(B + "/transfer", json={"date": "2026-09-20", "amount": 100, "from": "huf_icici", "to": "icici"}, headers=H).status_code,
        c.post(B + "/deposit", json={"date": TOM, "amount": 100}, headers=H).status_code]
    out["staff"] = [c.post(B + "/transfer", json={"date": "2026-09-21", "amount": 100, "from": "icici", "to": "yesbank"}, headers=M).status_code,
                    c.post(B + "/deposit", json={"date": "2026-09-21", "amount": 100}, headers=M).status_code]
    out["months"] = months()
    r = c.get("/finance/approvals", headers=H); t = r.get_data(as_text=True)
    out["page"] = [r.status_code, "on the bank" in t and "own statement of" in t, "Our count is" in t,
                   "S377_ICICI_COUNT" in t, "Record a transfer" in t, "id=\"needsCard\"" in t]
print("JSON:" + json.dumps(out, default=str))
'''
def run(stage):
    env = dict(os.environ, APPDIR=a.app, FINANCE_DB=a.db, STAGE=stage)
    p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=a.app)
    O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
    if not O:
        sys.exit("!! the app did not answer: " + p.stderr[-2000:])
    return O

A = run("before")
check("sanjeevni_approvals is v1.2", A["v"] == "1.2", A["v"])
ok250 = A["t250000"][0] in (200, 409)
ok40 = A["t40000"][0] == 200 and A["t40000"][1].get("ok")
check("his 20-Sep 2,50,000 is on record (taken now, or already there)", ok250, A["t250000"][0])
check("the 40,000 the old rule REFUSED is now recorded", ok40, A["t40000"])
check("and the answer says by how much our count was short, instead of refusing",
      bool(A["t40000"][1].get("short")) and "short" in (A["t40000"][1].get("message") or ""),
      A["t40000"][1].get("message", "")[:90])
rows = [(d, p) for d, p, f, t in A["rows"] if d == "2026-09-20" and f == "icici" and t == "yesbank"]
check("both transfers of that day stand in the book (2,50,000 and 40,000)",
      sorted(p for d, p in rows)[-2:] == [4000000, 25000000], [p // 100 for d, p in rows])
check("recording them moved no month's sale, online or cash", A["months"] == A["months_after"],
      [k for k in A["months_after"] if A["months_after"][k] != A["months"].get(k)])
check("before the anchor the count is under water, and the page shows ICICI at 0 with the shortfall named",
      A["pos"]["holds_p"] < 0 and A["icici_view"]["holds"] == "0" and A["icici_view"]["short"],
      (A["pos"]["holds_p"] // 100, A["icici_view"]["short"]))
seed = subprocess.run([sys.executable, "-B", a.seed, "--db", a.db], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                      text=True, cwd=a.app, env=dict(os.environ, FINANCE_APP_DIR=a.app))
print("   " + "\n   ".join(x for x in seed.stdout.strip().splitlines() if x))
check("the seed anchors ICICI on the bank's own closing balance", seed.returncode == 0 and seed.stdout.startswith("DONE"), seed.stdout.strip()[:60])
again = subprocess.run([sys.executable, "-B", a.seed, "--db", a.db], stdout=subprocess.PIPE, text=True, cwd=a.app,
                       env=dict(os.environ, FINANCE_APP_DIR=a.app))
check("a second seeding changes nothing", again.stdout.startswith("ALREADY"), again.stdout.strip()[:60])
Bv = run("after")
pos, view = Bv["pos"], Bv["icici_view"]
check("the count now starts at the bank's own figure, on its own date",
      pos["anchored"] and pos["base_p"] == 15026342 and pos["since"] == "2026-08-31", (pos["base_p"], pos["since"]))
check("holds = that balance + settlements credited since - what has been moved out",
      pos["holds_p"] == pos["base_p"] + pos["credited_p"] - pos["out_p"] and pos["holds_p"] > 0,
      (pos["holds_p"] // 100, pos["credited_p"] // 100, pos["out_p"] // 100))
check("with the anchor the count is no longer short", not view.get("short"), view.get("short"))
check("the page names the bank's own statement as where the count starts", view.get("anchored") and view.get("source"),
      (view.get("anchored"), (view.get("source") or "")[:40]))
check("every other refusal still stands: future, before the anchor, zero, repeat, a route not his, a future deposit",
      Bv["refusals"] == [400, 400, 400, 409, 400, 400], Bv["refusals"])
check("staff are still refused", Bv["staff"] == [403, 403], Bv["staff"])
check("the seeding moved no month's figure either", A["months"] == Bv["months"],
      [k for k in Bv["months"] if Bv["months"][k] != A["months"].get(k)])
check("the page carries the new wording and the tree", all(Bv["page"]), Bv["page"])
print(("WALK_S377 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S377 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
