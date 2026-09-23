#!/usr/bin/env python3
"""walk_s378.py -- kit S378_BANK_BALANCES. The REAL app over a SCRATCH COPY of finance.db: both accounts
carry a balance; Yes Bank is the balance its own statement closes on plus only the movements that statement
does NOT show (a confirmed deposit is never added twice); a new deposit raises it by exactly its amount and
removing it puts it back; a transfer out of Yes Bank lowers it; ICICI stays S377's count; no month's sale,
online or cash moves; the page carries both figures in bold. Prints dates, counts and rupees only.
  python3 walk_s378.py --app DIR --db scratch.db
"""
import argparse, json, os, subprocess, sys
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
B = "/finance/sanjeevni/api/bank"
out = {"v": sa.VERSION}
def pos():
    with fa.app.app_context():
        con = fa.db(); y = sa.yesbank_position(con); i = sa.icici_position(con)
        months = {x["ym"]: (x["sale_p"], x["upi_p"], x["cash_p"]) for x in sc.month_rows(con)}
        conf = None
        if sa._has(con, "cash_pool_deposit"):
            for d, amt, rid in con.execute("SELECT deposit_date, amount_p, id FROM cash_pool_deposit WHERE unit='medical'"):
                if sa._seen_in_yesbank(con, d, int(amt), True):
                    conf = (d, int(amt), rid); break
        con.commit()
    return y, i, months, conf
out["start"] = pos()
YDAY = (dt.date.today() - dt.timedelta(days=1)).isoformat()
r = c.post(B + "/deposit", json=dict(date=YDAY, amount=11000), headers=H); out["dep"] = [r.status_code, (r.get_json() or {}).get("ok")]
out["after_dep"] = pos()
j = c.get(B + "?month=" + YDAY[:7], headers=H).get_json()
out["view"] = [j.get("icici"), j.get("yesbank")]
did = [x["id"] for x in j["deposits"] if x.get("source") == "pool" and x["status"] != "ok"][-1]
r = c.post(B + "/transfer", json={"date": YDAY, "amount": 7000, "from": "yesbank", "to": "huf_yesbank"}, headers=H)
out["out"] = [r.status_code, (r.get_json() or {}).get("ok")]
out["after_out"] = pos()
c.post(B + "/undo", json=dict(kind="deposit", id=did), headers=H)
tid = [x["id"] for x in c.get(B + "?month=" + YDAY[:7], headers=H).get_json()["transfers"] if x["to_key"] == "huf_yesbank"][-1]
c.post(B + "/undo", json=dict(kind="transfer", id=tid), headers=H)
out["end"] = pos()
r = c.get("/finance/approvals", headers=H); t = r.get_data(as_text=True)
out["page"] = [r.status_code, 'class="bal"' in t, "balbox" in t, "Yes Bank Sanjeevni" in t, "ICICI Sanjeevni" in t,
               "S378_BANK_BALANCES" in t, "id=\"needsCard\"" in t, "Record a transfer" in t]
print("JSON:" + json.dumps(out, default=str))
'''
env = dict(os.environ, APPDIR=a.app, FINANCE_DB=a.db)
p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=a.app)
O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
if not O:
    sys.exit("!! the app did not answer: " + p.stderr[-2000:])
y0, i0, m0, conf = O["start"]
check("sanjeevni_approvals is v1.3", O["v"] == "1.3", O["v"])
check("Yes Bank is anchored on its own statement, and the figure is that closing balance plus what it does not show",
      y0["anchored"] and y0["holds_p"] == y0["base_p"] + y0["added_p"] - y0["taken_p"],
      (y0["base_p"] // 100, y0["added_p"] // 100, y0["taken_p"] // 100, y0["holds_p"] // 100))
check("a deposit the statement already shows is NOT added again", conf is not None and
      conf[1] <= y0["base_p"] + y0["added_p"] and not (conf[1] in (y0["added_p"],)),
      (conf[0] if conf else None, (conf[1] // 100) if conf else None, y0["added_p"] // 100))
check("ICICI still reads S377's count, from the bank's own balance", i0["anchored"] and i0["holds_p"] == i0["base_p"] + i0["credited_p"] - i0["out_p"],
      (i0["base_p"] // 100, i0["holds_p"] // 100))
y1 = O["after_dep"][0]
check("a new cash deposit raises Yes Bank by exactly its amount", O["dep"] == [200, True] and y1["holds_p"] - y0["holds_p"] == 1100000,
      (y1["holds_p"] - y0["holds_p"]) // 100)
y2 = O["after_out"][0]
check("a transfer out of Yes Bank lowers it by exactly its amount", O["out"] == [200, True] and y2["holds_p"] - y1["holds_p"] == -700000,
      (y2["holds_p"] - y1["holds_p"]) // 100)
check("ICICI is untouched by both", O["after_out"][1]["holds_p"] == i0["holds_p"], O["after_out"][1]["holds_p"] // 100)
y3, i3, m3, _ = O["end"]
check("removing them puts both figures back exactly", y3["holds_p"] == y0["holds_p"] and i3["holds_p"] == i0["holds_p"],
      ((y3["holds_p"] - y0["holds_p"]) // 100, (i3["holds_p"] - i0["holds_p"]) // 100))
check("no month's sale, online or cash moved throughout", m0 == m3, [k for k in m3 if m3[k] != m0.get(k)])
vi, vy = O["view"]
check("the Bank view serves both balances, with how each was made",
      vi and vy and vy.get("holds") and vy.get("base") and vy.get("as_on") and vi.get("holds"),
      (vi.get("holds"), vy.get("holds"), vy.get("as_on")))
check("the page carries the two bold tiles and the rest of the tree", all(O["page"]), O["page"])
print(("WALK_S378 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S378 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
