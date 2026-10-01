#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s442.py -- kit S442_PARCHI_MAKER_CHECKER. The REAL finance app (a copy of /root/finance carrying the kit's three
files) over a SCRATCH COPY of finance.db, through Flask's test client (header identity), and the same probe over the box
as it is (the negative control). Its own rows live on a crafted day in the future (W442_DAY, two years ahead, so no real
row can be touched or counted) and on slip numbers of a crafted book; every row is found by that key.

  --new DIR --old DIR --db PATH
"""
import argparse
import json
import os
import sqlite3
import subprocess
import sys

ap = argparse.ArgumentParser()
for k in ("--new", "--old", "--db"):
    ap.add_argument(k, required=True)
a = ap.parse_args()
a.new, a.old, a.db = map(os.path.abspath, (a.new, a.old, a.db))
assert "scratch" in a.db or "walk" in a.db or a.db.startswith("/tmp"), "refusing a non-scratch database"
n, fails = 0, []


def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:400] + "]") if got is not None else ""))
    if not cond:
        fails.append(label)


PROBE = r'''
import os, sys, json, sqlite3, datetime as dt
APP = os.environ["W_APP"]; NEW = os.environ["W_MODE"] == "new"
sys.path.insert(0, APP); os.chdir(APP)
DAY = os.environ["SLIP_NOW"][:10]
PREV = (dt.date.fromisoformat(DAY) - dt.timedelta(days=1)).isoformat()
import finance_app as fa
fc = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30); db.row_factory = sqlite3.Row
out = {}
G = lambda u, p: fc.get(p, headers=H(u))
P = lambda u, p, d: fc.post(p, data=d, headers=H(u))
# a crafted day: Docterz lines for PREV (consult 600 cash for ID 99001; X-ray 300 for 99002, billed at 200; X-ray 300 for 99003 at 300;
# X-ray 300 for 99004 billed 0 (free); consult 600 cash for 99005 that will be cancelled after billing; consult 600 for 99006, no parchi)
X = db.execute("SELECT id, price_p FROM owner_service WHERE kind='xray' AND active=1 AND status='approved' AND price_p>0 ORDER BY id LIMIT 1").fetchone()
out["xray_service"] = bool(X)
XP = X["price_p"] if X else 30000
for sec, sn, cid, amt in (("consult", 1, "99001", 60000), ("xray", 1, "99002", XP - 10000), ("xray", 2, "99003", XP - 10000),
                          ("xray", 3, "99004", 0), ("consult", 2, "99005", 60000), ("consult", 3, "99006", 60000)):
    db.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode, shift, gateway_ref) VALUES (?,?,?,?,?,?,?,?,?)",
               (PREV, sec, sn, "W442 walk", cid, amt, "Cash", "Morning", ""))
db.execute("INSERT OR REPLACE INTO clinic_day_revenue (business_date, source_file, source_id, source_mtime, taken_at, cons_count, cons_amount_p, "
           "xray_count, xray_amount_p, proc_count, proc_amount_p, total_count, total_amount_p, free_revisits, free_concession, f93_phantom_rows, tender_json) "
           "VALUES (?,?,?,?,?,2,120000,3,?,0,0,5,?,0,0,0,'{}')", (PREV, "w442", "w442", PREV, PREV + " 23:00", 2 * (XP - 10000), 120000 + 2 * (XP - 10000)))
db.execute("INSERT OR REPLACE INTO clinic_register_day (business_date, cons_cash_p, cons_upi_p, cons_card_p, xray_cash_p, xray_upi_p, xray_card_p, "
           "proc_cash_p, proc_upi_p, proc_card_p, entered_by, entered_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
           (PREV, 120000, 0, 0, 2 * (XP - 10000), 0, 0, 0, 0, 0, "w442", PREV + " 21:00"))
db.execute("UPDATE slip_book SET first_no=900001, last_no=900400, start_no=900001 WHERE series='opd'")
db.execute("UPDATE slip_book SET first_no=800001, last_no=800400, start_no=800001 WHERE series='xp'")
db.commit()
# --- logging on PREV (late entries): X-ray with a chhoot and its reason; one without a reason; one free
xid = str(X["id"]) if X else "0"
r1 = P("alisha", "/finance/slips/save", {"series": "opd", "slip_no": "900001", "clinic_id": "99001", "day": PREV, "id_ok": "1", "gap_ok": "1"})
r2 = P("alisha", "/finance/slips/save", {"series": "xp", "slip_no": "800001", "clinic_id": "99002", "day": PREV, "id_ok": "1", "gap_ok": "1",
                                          "xray0": xid, "xray0_disc": "100", "xray0_why": "poor"})
r3 = P("alisha", "/finance/slips/save", {"series": "xp", "slip_no": "800002", "clinic_id": "99003", "day": PREV, "id_ok": "1",
                                          "xray0": xid})
r4 = P("alisha", "/finance/slips/save", {"series": "xp", "slip_no": "800003", "clinic_id": "99004", "day": PREV, "id_ok": "1",
                                          "xray0": xid, "xray0_disc": "50"})
r4b = P("alisha", "/finance/slips/save", {"series": "xp", "slip_no": "800003", "clinic_id": "99004", "day": PREV, "id_ok": "1",
                                          "xray0": xid, "xray0_free": "1", "xray0_why": "staff"})
r5 = P("shavez", "/finance/slips/save", {"series": "opd", "slip_no": "900002", "clinic_id": "99005", "day": PREV, "id_ok": "1"})
loc = lambda r: r.headers.get("Location", "")
out["save"] = [r1.status_code, "save" in loc(r2) or "ok=" in loc(r2), "err=" in loc(r4), "ok=" in loc(r4b), "ok=" in loc(r5)]
slip = lambda s, no: db.execute("SELECT * FROM slip WHERE series=? AND slip_no=?", (s, no)).fetchone()
items = lambda sid: [dict(r) for r in db.execute("SELECT * FROM slip_item WHERE slip_id=? ORDER BY sort", (sid,))]
s2 = slip("xp", 800001)
out["item_disc"] = [i["discount_p"] for i in items(s2["id"])] if s2 else None
has_adj = bool(db.execute("SELECT name FROM sqlite_master WHERE name='slip_adjust'").fetchone())
adj = lambda: [dict(r) for r in db.execute("SELECT a.*, s.slip_no FROM slip_adjust a JOIN slip s ON s.id=a.slip_id WHERE s.slip_no>=800001 ORDER BY a.id")] if has_adj else []
out["adj_after_log"] = [[x["slip_no"], x["kind"], x["amount_p"], x["reason"], x["state"], x["made_by"]] for x in adj()]
# --- the night check on PREV, before any approval
def flags():
    j = G("manoj", "/finance/slips/report/" + PREV).get_data(as_text=True)
    return j
rep0 = flags()
out["report0"] = ["discount not written" in rep0, "waiting for approval" in rep0, "W442" in rep0 or "99002" in rep0]
# --- approval: own entry refused, Shavez approves Alisha's, a reject needs a reason
if NEW:
    A = adj()
    aid = [x["id"] for x in A if x["slip_no"] == 800001][0]
    fid = [x["id"] for x in A if x["slip_no"] == 800003][0]
    q1 = P("alisha", "/finance/slips/decide/%d" % aid, {"act": "approve"})
    q2 = P("shivani", "/finance/slips/decide/%d" % aid, {"act": "approve"})
    q3 = P("shavez", "/finance/slips/decide/%d" % fid, {"act": "reject"})
    q4 = P("shavez", "/finance/slips/decide/%d" % aid, {"act": "approve"})
    q5 = P("bhawna", "/finance/slips/decide/%d" % fid, {"act": "reject", "note": "not staff", "back": "report"})
    st = {x["slip_no"]: [x["state"], x["checked_by"]] for x in adj()}
    out["decide"] = ["err=" in loc(q1), "err=" in loc(q2), "err=" in loc(q3), "ok=" in loc(q4), "ok=" in loc(q5), st.get(800001), st.get(800003)]
    rep1 = flags()
    out["report1"] = ["discount not written" in rep1, "REJECTED by bhawna" in rep1, "800001" in rep1 and "waiting for approval" not in rep1.split("Needs a look")[1].split("</details>")[0]]
    # --- radd after billing on 900002 (ID 99005): money never taken; then approved by the owner
    s5 = slip("opd", 900002)
    q6 = P("shavez", "/finance/slips/radd", {"slip_id": s5["id"], "clinic_id": "", "how": "never_taken"})
    q7 = P("shavez", "/finance/slips/decide/%d" % [x["id"] for x in adj() if x["kind"] == "cancel"][0], {"act": "approve"}) if False else None
    c = [x for x in [dict(r) for r in db.execute("SELECT * FROM slip_adjust WHERE kind='cancel' AND slip_id=?", (s5["id"],))]]
    q8 = P("manoj", "/finance/slips/decide/%d" % c[0]["id"], {"act": "approve", "back": "report"}) if c else None
    out["radd"] = ["ok=" in loc(q6), len(c), c[0]["clinic_id"] if c else None, slip("opd", 900002)["state"], "ok=" in loc(q8) if q8 else None]
    rep2 = flags()
    out["report2"] = ["Cancelled after billing" in rep2, "99005" in rep2.split("Cancelled after billing")[-1][:2000]]
    # the Tehzida shape: a parchi already 'cancelled' with NO ID takes its ID through Radd
    db.execute("INSERT INTO slip (series, slip_no, day, state, logged_by, logged_at, updated_by, updated_at) VALUES ('opd', 900003, ?, 'cancelled', 'shavez', ?, 'shavez', ?)",
               (PREV, PREV + " 20:12:51", PREV + " 20:13:32"))
    db.commit()
    late = G("alisha", "/finance/slips?s=late").get_data(as_text=True)
    s6 = slip("opd", 900003)
    q9 = P("alisha", "/finance/slips/radd", {"slip_id": s6["id"], "clinic_id": "99001", "how": "returned", "back": "late"})
    out["tehzida"] = ["Radd parchi" in late, "ok=" in loc(q9), slip("opd", 900003)["clinic_id"]]
    # --- the late parchi's day, proposed: the ID in the last Docterz day; a number below today's first
    j1 = G("alisha", "/finance/slips/api/day?series=opd&no=&id=99006").get_json()
    P("alisha", "/finance/slips/save", {"series": "opd", "slip_no": "900010", "clinic_id": "99100", "id_ok": "1", "gap_ok": "1"})
    j2 = G("alisha", "/finance/slips/api/day?series=opd&no=900005&id=").get_json()
    j3 = G("alisha", "/finance/slips/api/day?series=opd&no=900011&id=99100").get_json()
    out["propose"] = [j1.get("propose"), j2.get("propose"), j3.get("propose")]
    # --- the owner's month page and the approver's screen
    mp = G("manoj", "/finance/slips/discounts?m=" + PREV[:7]).get_data(as_text=True)
    out["month"] = ["approved on" in mp, "shavez" in mp, "bhawna" in mp]
    ap_ = G("shavez", "/finance/slips?s=approve").get_data(as_text=True)
    out["approve_screen"] = ["Chhoot / Radd manzoori" in ap_]
    menu = G("shavez", "/finance/slips").get_data(as_text=True)
    out["menu"] = ["Chhoot / Radd manzoori" in menu, "Chhoot / Radd manzoori" in G("alisha", "/finance/slips").get_data(as_text=True)]
# --- clinic money: the cancelled line leaves the expected money
import clinic_money as cm
m = cm.match_day(db, PREV)
out["money"] = [m.get("p1", {}).get("diff_p"), [e["code"] for e in m["explained"] if e["code"] == "cancelled_after_billing"], [f["code"] for f in m["flags"] if f["code"] == "total_diff"]]
print("W442JSON " + json.dumps(out, default=str))
'''


def run(mode, app, db):
    env = dict(os.environ, W_MODE=mode, W_APP=app, FINANCE_DB=db, FINANCE_ALLOW_HEADER_AUTH="1", PYTHONDONTWRITEBYTECODE="1",
               SLIP_NOW="2028-10-04T11:00:00", FINANCE_SSO_DIR=os.environ.get("W_PORTAL", "/root/portal"))
    p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, capture_output=True, text=True, timeout=900)
    line = [x for x in p.stdout.splitlines() if x.startswith("W442JSON ")]
    if not line:
        print(p.stdout[-3000:])
        print(p.stderr[-4000:])
        raise SystemExit("WALK_S442 RED -- the %s probe printed nothing" % mode)
    return json.loads(line[-1][9:])


s = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
d = sqlite3.connect(a.db + ".old")
s.backup(d)
d.close()
s.close()
NEW = run("new", a.new, a.db)
OLD = run("old", a.old, a.db + ".old")
print("-- new: " + json.dumps(NEW)[:1500])
print("-- old: " + json.dumps(OLD)[:800])
check("SETUP: an approved, priced X-ray on the rate page to bill against", NEW["xray_service"] is True)
check("LOG: an X-ray chhoot with its reason saves (X-rays could not carry one before); a chhoot with NO reason is refused; Free with a reason saves",
      NEW["save"][1:] == [True, True, True, True], NEW["save"])
check("LOG: the line carries the chhoot at once -- the patient never waits", NEW["item_disc"] == [10000], NEW["item_disc"])
check("LOG: each chhoot / free becomes a PENDING entry with who and why",
      NEW["adj_after_log"] == [[800001, "discount", 10000, "poor", "pending", "alisha"], [800003, "free", NEW["adj_after_log"][-1][2] if NEW["adj_after_log"] else 0, "staff", "pending", "alisha"]],
      NEW["adj_after_log"])
check("NIGHT: Docterz below the rate with no chhoot -> 'discount not written' to the person who logged it; a pending chhoot is named as waiting",
      NEW["report0"][:2] == [True, True], NEW["report0"])
check("CHECKER: own entry refused; a non-approver refused; a reject needs a reason; Shavez approves Alisha's; Dr Bhawna rejects with a reason",
      NEW["decide"][:5] == [True, True, True, True, True] and NEW["decide"][5] == ["approved", "shavez"] and NEW["decide"][6] == ["rejected", "bhawna"], NEW["decide"])
check("NIGHT: the rejected free line goes to the night report; the approved chhoot is quiet", NEW["report1"][1:] == [True, True], NEW["report1"])
check("RADD: the parchi's own ID is taken, 'money never taken', approved by the owner -> the parchi reads cancelled",
      NEW["radd"] == [True, 1, "99005", "cancelled", True], NEW["radd"])
check("RADD: the report lists it under 'Cancelled after billing'", NEW["report2"] == [True, True], NEW["report2"])
check("F-664: a parchi already radd with NO clinic ID shows on Chhooti parchi and takes its ID in one tap (never guessed)",
      NEW["tehzida"] == [True, True, "99001"], NEW["tehzida"])
check("F-663: the day is proposed -- an ID in the last Docterz day; a number below today's first; nothing for today's own",
      NEW["propose"][0] == "2028-10-03" and NEW["propose"][1] == "2028-10-03" and NEW["propose"][2] is None, NEW["propose"])
check("OWNER: the month's discounts -- totals, who asked, who approved", NEW["month"] == [True, True, True], NEW["month"])
check("CHECKER: Shavez's menu carries 'Chhoot / Radd manzoori'; Alisha (not an approver) never sees it",
      NEW["menu"] == [True, False] and NEW["approve_screen"] == [True], (NEW["menu"], NEW["approve_screen"]))
check("MONEY: the approved radd leaves Docterz's expected money -- the counter and Docterz agree; it is explained, not flagged",
      NEW["money"][0] == 0 and NEW["money"][1] == ["cancelled_after_billing"] and NEW["money"][2] == [], NEW["money"])
check("NEGATIVE: the box refuses an X-ray chhoot as part of no form -- it saves the X-ray at the full rate with no entry",
      OLD["adj_after_log"] == [] and OLD["item_disc"] == [0], (OLD["adj_after_log"], OLD["item_disc"]))
check("NEGATIVE: the box's money page reads ₹600 short (the cancelled consultation)", OLD["money"][0] == -60000 and OLD["money"][2] == ["total_diff"], OLD["money"])
print("WALK_S442 %s -- %d checks, %d failed%s" % ("GREEN" if not fails else "RED", n, len(fails), (": " + "; ".join(fails)) if fails else ""))
sys.exit(0 if not fails else 1)
