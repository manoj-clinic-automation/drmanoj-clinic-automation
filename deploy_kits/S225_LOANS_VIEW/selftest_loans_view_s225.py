#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest_loans_view_s225.py -- the Loans view (D371) on a synthetic ledger in a temp dir:
tranches, lanes, schedule, defer, reversal, pending, the per-role page, and the schedule field on
the entry form. Run from inside the kit folder:  python3 -B selftest_loans_view_s225.py"""
import csv, datetime, io, json, os, re, secrets, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
TMP = tempfile.mkdtemp(prefix="s225loans_")
os.environ["LEDGER_DIR"] = TMP; os.environ["STAFF_CSV"] = os.path.join(TMP, "staff.csv")
import staff_ledger as SL
SL.LEDGER_DIR = TMP; SL.STAFF_CSV = os.path.join(TMP, "staff.csv")
with open(SL.STAFF_CSV, "w", newline="") as f:
    w = csv.writer(f); w.writerow(["user_id", "name", "active"])
    for i, n in enumerate(["Alpha", "Beta", "Gamma"]): w.writerow([i + 1, n, "Y"])
for name, role, link in (("doc", "checker", ""), ("mbeta", "maker_full", "Beta"), ("mnolink", "maker_full", "")):
    salt = secrets.token_hex(16); u = SL.load_users()
    u[name] = {"pw": SL.hash_pw("pw", salt), "salt": salt, "role": role, "staff_link": link, "active": True}; SL.save_users(u)
users = SL.load_users()
P, F = [], []
def ck(label, cond, detail=""):
    (P if cond else F).append(label); print("  %s  %s%s" % ("PASS" if cond else "FAIL", label, ("   [%s]" % detail) if detail and not cond else ""))

M = "2026-09"
# Alpha: an interest loan 10000 @2000 + an interest-free 3000 @1000 (waits behind the loan)
la = SL.make_entry(users, "doc", "Alpha", "ADVANCE_ISSUE", "2026-07-05", "2026-07-05", 0, "10000", "loan", instalment="2000", interest=True)
fa = SL.make_entry(users, "doc", "Alpha", "ADVANCE_ISSUE", "2026-08-02", "2026-08-02", 0, "3000", "free", instalment="1000")
# Beta: a SCHEDULED 13000 (Surendra-shaped): 5000 Sep, 4000 Oct, 4000 Nov
sb = SL.make_entry(users, "doc", "Beta", "ADVANCE_ISSUE", "2026-08-28", "2026-08-28", 0, "13000", "aug advance", schedule="2026-09:5000, 2026-10:4000, 2026-11:4000")
ck("a scheduled advance is stored with its 3 steps", len(SL.advance_schedule(sb)) == 3 and SL.advance_lane({"issue": sb, "interest": False, "instalment": 13000}) == "schedule")
# Beta: a reversed (corrected) advance -- never a loan
rb = SL.make_entry(users, "doc", "Beta", "ADVANCE_ISSUE", "2026-08-10", "2026-08-10", 0, "2000", "wrong entry")
SL.make_contra(users, "doc", rb["id"], "entered twice")
# Gamma: pending (maker-entered) advance
pg = SL.make_entry(users, "mbeta", "Gamma", "ADVANCE_ISSUE", "2026-09-01", "2026-09-01", 0, "1500", "pending one")
ck("the maker's advance is PENDING", pg["status"] == "PENDING")
# an instalment already recovered on Alpha's loan (system row, as the close writes it)
SL.append_ledger({"id": "sys1", "ts_entry": SL.now(), "maker": "system", "staff": "Alpha", "category": "ADVANCE_INSTALMENT",
                  "date_from": "2026-08-31", "date_to": "2026-08-31", "days": 0, "amount": -2000, "instalment": None,
                  "narration": "close 2026-08", "self_flag": False, "direct": True, "status": "APPROVED", "checker": "system",
                  "ts_decision": SL.now(), "contra_of": la["id"], "closed_month": "2026-08", "interest": False,
                  "against_month": "", "special": False, "schedule": None})
rows = SL.load_ledger()
v = SL.loans_view(rows, M)
by = {d["staff"]: d for d in v["staff"]}
ck("three people in the view (Alpha, Beta, Gamma)", set(by) == {"Alpha", "Beta", "Gamma"})
A = by["Alpha"]
ck("Alpha: two tranches, loan first", [t["interest"] for t in A["tranches"]] == [True, False])
loan, free = A["tranches"]
ck("Alpha loan: recovered 2000, balance 8000, due 2000 this month, 4 months left, lane loan",
   loan["recovered"] == 2000 and loan["balance"] == 8000 and loan["due_this_month"] == 2000 and loan["months_left"] == 4 and loan["lane"] == "loan", str(loan))
ck("Alpha free advance WAITS behind the loan (D250): due 0, says so", free["due_this_month"] == 0 and "waits" in free["how"] and free["lane"] == "waterfall")
ck("Alpha outstanding 11000, falling due 2000", A["outstanding"] == 11000 and A["due"] == 2000)
B = by["Beta"]
ck("Beta: the reversed advance is NOT a tranche, counted as 1 corrected entry", len(B["tranches"]) == 1 and B["reversed"] == 1)
s = B["tranches"][0]
ck("Beta schedule: next Rs 5000 in 2026-09, 3 months left, balance 13000", s["next_amount"] == 5000 and s["next_month"] == "2026-09" and s["months_left"] == 3 and s["balance"] == 13000 and s["due_this_month"] == 5000, str(s))
ck("Beta 'how' names the schedule", "2026-09 Rs 5000" in s["how"] and "2026-11 Rs 4000" in s["how"])
v_oct = SL.loans_view(rows, "2026-10")
so = {d["staff"]: d for d in v_oct["staff"]}["Beta"]["tranches"][0]
ck("in October the schedule's due is the FIRST unpaid step (5000, since Sep never recovered) -- never a silent skip", so["due_this_month"] == 5000 and so["next_month"] == "2026-09")
# a DEFER on Beta's schedule for September
SL.record_defer(users, "doc", sb["id"], "2026-09", "owner said wait", waive_penalty=False)
rows = SL.load_ledger(); v2 = SL.loans_view(rows, M); s2 = {d["staff"]: d for d in v2["staff"]}["Beta"]["tranches"][0]
ck("after a DEFER for 2026-09: due 0 this month, flagged deferred, the defer month listed", s2["due_this_month"] == 0 and s2["deferred_now"] and s2["defers"] == ["2026-09"])
G = by["Gamma"]
ck("Gamma: no tranche, 1 awaiting approval, nothing outstanding", not G["tranches"] and G["pending"] == 1 and G["outstanding"] == 0)
ck("staff filter narrows the view", [d["staff"] for d in SL.loans_view(rows, M, "Alpha")["staff"]] == ["Alpha"])
# a fully recovered tranche shows as recovered, not open
SL.append_ledger(dict(SL.load_ledger()[-1], id="sys2", contra_of=fa["id"], amount=-3000, category="ADVANCE_INSTALMENT", closed_month="2026-09", date_from="2026-09-30", status="APPROVED"))
rows = SL.load_ledger(); A3 = {d["staff"]: d for d in SL.loans_view(rows, M)["staff"]}["Alpha"]
ck("a fully recovered tranche is listed as recovered (open=False, balance 0, last paid 2026-09) and sorted last",
   A3["tranches"][-1]["open"] is False and A3["tranches"][-1]["balance"] == 0 and A3["tranches"][-1]["last_paid"] == "2026-09")
# ---- the page, through the real app ----
app = SL.create_app(); app.config["TESTING"] = True
cl = app.test_client()
ck("signed out -> login redirect", cl.get("/ledger/loans").status_code == 302)
with cl.session_transaction() as sx: sx["u"] = "doc"
r = cl.get("/ledger/loans?m=" + M); h = r.get_data(as_text=True)
ck("checker page 200 with everyone", r.status_code == 200 and "Alpha" in h and "Beta" in h and "Gamma" in h)
for w in ("the clean view", "how it recovers", "next collection", "falling due", "outstanding <b>Rs 8000</b>", "agreed schedule", "1 awaiting approval", "1 corrected entry not counted", "D349"):
    ck("checker page shows '%s'" % w, w in h)
ck("system/contra rows are NOT listed as lines (no 'close 2026-08', no 'entered twice')", "close 2026-08" not in h and "entered twice" not in h)
r = cl.get("/ledger/loans?m=" + M + "&staff=Beta"); h2 = r.get_data(as_text=True)
ck("checker filter to Beta: Alpha absent", r.status_code == 200 and "Alpha" not in h2.split("<select")[1].split("</select>")[1] if "<select" in h2 else False)
ck("nav carries Loans for the checker", '/ledger/loans"><b>Loans</b>' in h)
with cl.session_transaction() as sx: sx["u"] = "mbeta"
r = cl.get("/ledger/loans"); h3 = r.get_data(as_text=True)
ck("a linked maker sees ONLY her own (Beta), titled My loans, no picker", r.status_code == 200 and "Beta" in h3 and "Alpha" not in h3 and "My loans" in h3 and "<select" not in h3)
with cl.session_transaction() as sx: sx["u"] = "mnolink"
r = cl.get("/ledger/loans")
ck("an unlinked maker is told to ask for a relink", r.status_code == 200 and "not linked" in r.get_data(as_text=True))
# ---- the entry form carries the schedule field and passes it through ----
with cl.session_transaction() as sx: sx["u"] = "doc"
h4 = cl.get("/ledger/").get_data(as_text=True)
ck("entry form has the schedule textarea", 'name="schedule"' in h4)
n0 = len(SL.load_ledger())
r = cl.post("/ledger/", data=dict(category="ADVANCE_ISSUE", staff="Gamma", date_from="2026-09-04", date_to="2026-09-04", amount="6000", narration="via form",
                                  instalment="", against_month="", schedule="2026-10:3000\n2026-11:3000"), follow_redirects=True)
new = [x for x in SL.load_ledger() if x["staff"] == "Gamma" and x["amount"] == 6000]
ck("a scheduled advance saved through the FORM carries its 2 steps", len(new) == 1 and len(SL.advance_schedule(new[0])) == 2, str(new[:1]))
r = cl.post("/ledger/", data=dict(category="ADVANCE_ISSUE", staff="Gamma", date_from="2026-09-04", date_to="2026-09-04", amount="6000", narration="bad",
                                  instalment="", against_month="", schedule="2026-10:1000"), follow_redirects=True)
ck("a schedule that does not add up is REFUSED and nothing saved", "must match" in r.get_data(as_text=True) and len([x for x in SL.load_ledger() if x["narration"] == "bad"]) == 0)
ck("APP_VERSION bumped", SL.APP_VERSION == "3.5.1-S225-LOANS")
print("\n%d PASS  %d FAIL" % (len(P), len(F)))
for f in F: print("  FAILED: " + f)
sys.exit(1 if F else 0)
