#!/usr/bin/env python3
"""walk_s368.py -- kit S368_APPROVALS_TREE. The REAL app (kit files placed in a copy of /root/finance) over a
SCRATCH COPY of finance.db: the four doors answer and their rupees are sanjeevni_cash's own; the Needs-you
count for returns equals the returns card's; both pool deposits read confirmed; the page is the tree and still
carries the S365 day panel and its fallback; the old page is served byte for byte; staff refused.
Prints dates, counts and rupees only.
  python3 walk_s368.py --app DIR --db scratch.db [--old-md5 6c668ccc...]
"""
import argparse, hashlib, json, os, sqlite3, subprocess, sys
ap = argparse.ArgumentParser(); ap.add_argument("--app", required=True); ap.add_argument("--db", required=True)
ap.add_argument("--old-md5", default="6c668cccc9e80bec8c843599a274951d")
a = ap.parse_args()
n, fails = 0, []
def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got) + "]") if got is not None else ""))
    if not cond: fails.append(label)
PROBE = r'''
import json, os, sys, hashlib
sys.path.insert(0, os.environ["APPDIR"]); os.chdir(os.environ["APPDIR"])
os.environ.update(FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_DEV_USER="manoj", FINANCE_DEV_ROLE="owner")
import finance_app as fa, sanjeevni_approvals, sanjeevni_day
c = fa.app.test_client(); H = {"X-Clinic-User": "manoj", "X-Clinic-Role": "owner"}
out = {"v": sanjeevni_approvals.VERSION, "vday": sanjeevni_day.VERSION}
for k, p in (("needs", "/finance/sanjeevni/api/needs-you"), ("days", "/finance/sanjeevni/api/days"),
             ("bank", "/finance/sanjeevni/api/bank?month=2026-09"), ("months", "/finance/sanjeevni/api/months"),
             ("cn", "/finance/darpan/api/cn-detail?month=" + os.environ["YM"]), ("pos", "/finance/api/cash-position")):
    r = c.get(p, headers=H); out[k] = [r.status_code, r.get_json()]
r = c.get("/finance/approvals", headers=H); t = r.get_data(as_text=True)
out["page"] = [r.status_code, "id=\"needsCard\"" in t, "id=\"checksCard\"" in t, "/finance/sanjeevni/api/day/" in t,
               "function dayDetailOld" in t, "sanjeevni/api/needs-you" in t, "id=\"mgApply\"" in t, "S368_APPROVALS_TREE" in t]
r = c.get("/finance/approvals/old", headers=H); out["old"] = [r.status_code, hashlib.md5(r.get_data()).hexdigest()]
M = {"X-Clinic-User": "darpan", "X-Clinic-Role": "maker"}
out["staff"] = [c.get("/finance/sanjeevni/api/needs-you", headers=M).status_code, c.get("/finance/sanjeevni/api/days", headers=M).status_code,
                c.get("/finance/approvals/old", headers=M).status_code]
print("JSON:" + json.dumps(out))
'''
import datetime as dt
env = dict(os.environ, APPDIR=a.app, FINANCE_DB=a.db, YM=dt.date.today().isoformat()[:7])
p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=a.app)
O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
if not O:
    sys.exit("!! the app did not answer: " + p.stderr[-1500:])
check("sanjeevni_approvals v1.0 mounted; the day panel v1.1 still there", O["v"] == "1.0" and O["vday"] == "1.1", (O["v"], O["vday"]))
check("the four doors answer", all(O[k][0] == 200 and O[k][1].get("ok") for k in ("needs", "days", "bank", "months")),
      {k: O[k][0] for k in ("needs", "days", "bank", "months")})
sys.path.insert(0, a.app)
import sanjeevni_cash as sc
con = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
rows = sc.days(con, "2026-08-17", "9999-12-31")["rows"]
D = O["days"][1]["days"]
check("one line per filed day from the anchor (%d days), in the one calculation's order" % len(rows),
      [d["date"] for d in D] == [r["date"] for r in rows], (len(D), len(rows)))
bad = [d["date"] for d, r in zip(D, rows) if d["cash_p"] != r["into_drawer_p"]]
check("every day's cash = sanjeevni_cash's into_drawer", not bad, bad[:5])
pos = O["days"][1]["position"]; close = rows[-1]["close"]
def rs(p):
    import sanjeevni_approvals as sa
    return sa.rs(p)
check("the position after the last day is the one calculation's close",
      pos["drawer"] == rs(close["drawer"]) and pos["with_doctors"] == rs(close["with_doctors"]) and pos["bank"] == rs(close["bank"]), pos)
mr = {m["ym"]: m for m in sc.month_rows(con)}
MM = O["months"][1]["months"]
check("every month's sale, online, cash are sanjeevni_cash.month_rows'",
      all(m["sale"] == rs(mr[m["ym"]]["sale_p"]) and m["upi"] == rs(mr[m["ym"]]["upi_p"]) and m["cash"] == rs(mr[m["ym"]]["cash_p"]) for m in MM), len(MM))
NL = O["needs"][1]["lines"]
ret = [l for l in NL if l["target"] == "returns"]
cnp = int((O["cn"][1] or {}).get("pending_approval") or 0)
check("Needs-you names the returns waiting for his OK exactly as the returns card counts them (%d)" % cnp,
      (cnp == 0 and not ret) or (len(ret) == 1 and ret[0]["text"].startswith("%d return" % cnp)), [l["text"] for l in ret])
pend = [r[0] for r in con.execute("SELECT business_date FROM day_entry WHERE unit='medical' AND status IN ('submitted','draft')")]
dl = [l for l in NL if l["target"] == "days" and "to approve" in l["text"]]
check("Needs-you names the days to approve (%d) or says nothing when there are none" % len(pend),
      (not pend and not dl) or (dl and dl[0]["text"].startswith("%d day" % len(pend))), [l["text"] for l in dl])
check("no machine word reaches the Needs-you lines", not any(w in l["text"] for l in NL for w in ("line_sum", "upi_vs", "variance", "recon_exception")))
B = O["bank"][1]
dep = {d["date"]: d for d in B["deposits"]}
check("03-Sep 3,00,000 and 15-Sep 1,00,000 read confirmed in the Yes Bank statement",
      dep.get("2026-09-03", {}).get("status") == "ok" and dep.get("2026-09-15", {}).get("status") == "ok", [(k, v["status"]) for k, v in dep.items()])
check("the statement's reach is stated (to 20-Sep or later)", (B.get("statement") or {}).get("to", "") >= "2026-09-20", (B.get("statement") or {}).get("to"))
check("the page is the tree: Needs you, Checks, the S365 day panel, its fallback, the Marg upload kept", all(O["page"]), O["page"])
check("the old page is served byte for byte at /finance/approvals/old", O["old"] == [200, a.old_md5], O["old"][1][:8])
check("staff logins are refused (doors and the old page)", O["staff"] == [403, 403, 403], O["staff"])
print(("WALK_S368 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S368 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
