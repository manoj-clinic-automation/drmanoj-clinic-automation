#!/usr/bin/env python3
"""walk_s371.py -- kit S371_PURCHASE_WRONG_RESOLVE. The REAL app (purchase_app.py patched) over a SCRATCH COPY
of finance.db: the two August bills are marked WRONG at the amounts the owner named (4,608 and 1,862) exactly
as the page does it; then EITHER Marg's 22-Sep supplier-wise export is pushed through the door (--push
ROWS.json, at build) OR the resolver is run as the installer runs it (on the box, where the export already
landed): both bills resolve themselves, the audit says so, August can finalise, and a WRONG bill that does
NOT match keeps its Correct button. Prints bill numbers, counts and rupees only.
  python3 walk_s371.py --app DIR --db scratch.db [--push rows.json]
"""
import argparse, json, os, sqlite3, subprocess, sys
ap = argparse.ArgumentParser(); ap.add_argument("--app", required=True); ap.add_argument("--db", required=True); ap.add_argument("--push")
a = ap.parse_args()
n, fails = 0, []
def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got) + "]") if got is not None else ""))
    if not cond: fails.append(label)
PROBE = r'''
import json, os, sys
sys.path.insert(0, os.environ["APPDIR"]); os.chdir(os.environ["APPDIR"])
os.environ.update(FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_DEV_USER="manoj", FINANCE_DEV_ROLE="owner", FINANCE_MARG_TOKEN="walk-token")
import finance_app as fa, purchase_app as pa
c = fa.app.test_client(); H = {"X-Clinic-User": "manoj", "X-Clinic-Role": "owner"}
out = {}
with fa.app.app_context():
    con = fa.db(); pa._ensure(con)
    ids = {}
    for sup, bno, want in (("KEDAR", "148", 460800), ("L.K", "67025", 186200)):
        r = con.execute("SELECT id, amount_p, sw_amount_p FROM purchase_bill WHERE supplier LIKE ? AND bill_no=? AND month='2026-08'", ("%" + sup + "%", bno)).fetchone()
        ids[bno] = (r["id"], want)
    con.commit()
with fa.app.app_context():
    con = fa.db(); out["audit0"] = con.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='verdict_resolved'").fetchone()[0]; con.commit()
# the owner marks both WRONG, as the page does (amount he believes right + reason)
for bno, (bid, want) in ids.items():
    r = c.post("/finance/purchase/api/verdict", json=dict(bill_id=bid, verdict="WRONG", wrong_amount=want / 100.0, reason="matches Amir's working"), headers=H)
    out["mark_" + bno] = r.status_code
# a third WRONG at an amount Marg will NOT carry: must stay WRONG and keep its button
with fa.app.app_context():
    con = fa.db()
    other = con.execute("SELECT id, bill_no, amount_p FROM purchase_bill WHERE month='2026-08' AND id NOT IN (?,?) ORDER BY id LIMIT 1", (ids["148"][0], ids["67025"][0])).fetchone()
    con.commit()
r = c.post("/finance/purchase/api/verdict", json=dict(bill_id=other["id"], verdict="WRONG", wrong_amount=(other["amount_p"] + 50000) / 100.0, reason="walk: does not match"), headers=H)
out["mark_other"] = [r.status_code, other["bill_no"]]
with fa.app.app_context():
    con = fa.db(); s = pa._month_summary(con, "2026-08"); out["reasons_marked"] = s["reasons"]; out["can_marked"] = s["can_finalise"]
    out["btn_marked"] = [ids["148"][0] in s["needs_verdict"], ids["67025"][0] in s["needs_verdict"], other["id"] in s["needs_verdict"]]
    con.commit()
if os.environ.get("PUSH"):
    body = json.load(open(os.environ["PUSH"]))
    r = c.post("/finance/purchase/api/push", json=body, headers={"X-Finance-Marg": "walk-token"})
    out["push"] = [r.status_code, r.get_json()]
else:
    with fa.app.app_context():
        con = fa.db(); done = pa._resolve_wrong(con, who="walk"); con.commit(); out["push"] = ["resolve_now", [d[2] for d in done]]
with fa.app.app_context():
    con = fa.db()
    out["after"] = {bno: dict(con.execute("SELECT verdict, verdict_by, reason, amount_p, sw_amount_p FROM purchase_bill WHERE id=?", (bid,)).fetchone()) for bno, (bid, w) in ids.items()}
    out["other_after"] = dict(con.execute("SELECT verdict FROM purchase_bill WHERE id=?", (other["id"],)).fetchone())
    out["audit"] = con.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='verdict_resolved'").fetchone()[0] - out["audit0"]
    s = pa._month_summary(con, "2026-08"); out["reasons_after"] = s["reasons"]; out["can_after"] = s["can_finalise"]
    out["btn_other"] = other["id"] in s["needs_verdict"]
    # clear the walk's own third WRONG by hand -- the button path -- and the month can finalise
    con.commit()
r = c.post("/finance/purchase/api/verdict", json=dict(bill_id=other["id"], verdict="CORRECT"), headers=H); out["hand_correct"] = r.status_code
with fa.app.app_context():
    con = fa.db(); s = pa._month_summary(con, "2026-08"); out["reasons_final"] = s["reasons"]; out["can_final"] = s["can_finalise"]
    con.commit()
r = c.get("/finance/purchase/page/month/2026-08", headers=H); t = r.get_data(as_text=True)
out["page"] = [r.status_code, "FINALISE" in t and "cannot finalise" not in t, "resolved: Marg" in t]
print("JSON:" + json.dumps(out, default=str))
'''
env = dict(os.environ, APPDIR=a.app, FINANCE_DB=a.db)
if a.push: env["PUSH"] = os.path.abspath(a.push)
p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=a.app)
O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
if not O:
    sys.exit("!! the app did not answer: " + p.stderr[-2000:])
check("the owner's two WRONG verdicts land (148 at 4,608; 67025 at 1,862)", O["mark_148"] == 200 and O["mark_67025"] == 200, (O["mark_148"], O["mark_67025"]))
check("marked WRONG, August cannot finalise and names them", not O["can_marked"] and any("Wrong" in r for r in O["reasons_marked"]), O["reasons_marked"][:1])
check("a WRONG bill keeps its Correct button (all three)", all(O["btn_marked"]), O["btn_marked"])
if a.push:
    check("Marg's 22-Sep supplier-wise export is taken at the door as new", O["push"][0] == 200 and O["push"][1].get("stored") is True, O["push"])
else:
    check("the resolver ran over the live amounts", O["push"][0] == "resolve_now", O["push"])
A = O["after"]
check("148 resolved itself: CORRECT at 4,608, reason names Marg's re-export", A["148"]["verdict"] == "CORRECT" and A["148"]["sw_amount_p"] == 460800 and "resolved: Marg" in (A["148"]["reason"] or ""), A["148"])
check("67025 resolved itself: CORRECT at 1,862", A["67025"]["verdict"] == "CORRECT" and A["67025"]["sw_amount_p"] == 186200, A["67025"])
check("two new audit rows 'verdict_resolved'", O["audit"] == 2, O["audit"])
check("the third bill, marked at an amount Marg does not carry, stays WRONG with its button", O["other_after"]["verdict"] == "WRONG" and O["btn_other"], (O["other_after"], O["btn_other"]))
check("with only the walk's own WRONG left, that is August's one reason", len(O["reasons_after"]) == 1 and "Wrong" in O["reasons_after"][0] and O["mark_other"][1] in O["reasons_after"][0], O["reasons_after"])
check("the Correct button clears it by hand; August can finalise", O["hand_correct"] == 200 and O["can_final"] and not O["reasons_final"], O["reasons_final"])
check("the month page offers FINALISE to the doctor and shows the resolution", all(O["page"]), O["page"])
print(("WALK_S371 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S371 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
