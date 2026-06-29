"""
test_ivr_reconcile.py — self-contained checks for the IVR telephony reconciliation
(Feature A). Run from the followup_tracker folder:

    python test_ivr_reconcile.py

It builds its own in-memory ledgers and a temp outbound file, so it never reads or
writes the real data\\ ledgers. Expect: ALL 9 PASSED.
"""
import tempfile, os
from pathlib import Path
import pandas as pd
import processor as P

D = "2026-06-20"
results = []
def check(name, cond):
    results.append((name, bool(cond)))
    print(("  PASS " if cond else "  FAIL ") + name)

def fu(fid, name, mob):
    r = {c: "" for c in P.FU_COLS}
    r.update({"Followup_ID": fid, "Standard_Name": name, "FU_Name_Raw": name,
              "FU_Mobile_Clean": mob, "Followup_Status": "Grace Period"})
    return r

def cl(key, resp, by, d=D):
    r = {c: "" for c in P.CALL_LOG_COLS}
    r.update({"Obligation_Key": key, "Patient_UID": "U" + key, "Call_Date": d,
              "Response": resp, "Called_By": by, "Key_Type": "FOLLOWUP"})
    return r

def ob(d, ph, agent, status, su, direction="outgoing"):
    return {"Date": d, "Time": "09:10", "Phone10": ph, "Direction": direction,
            "Agent": agent, "Duration_s": "40", "Status": status, "Start_Unix": str(su)}

fu_ledger = pd.DataFrame([
    fu("F000001", "Asha",  "9000000001"),
    fu("F000002", "Beena", "9000000002"),
    fu("F000003", "Chaya", "9000000003"),
    fu("F000004", "Deepa", "9000000004"),
    fu("F000005", "Esha",  "9000000005"),
    fu("F000006", "Farah", "9000000006"),
    fu("F000007", "Gita",  "9000000007"),
])
visits = pd.DataFrame(columns=P.VISIT_COLS)
call_log = pd.DataFrame([
    cl("F000001", "YES",      "Shivani"),
    cl("F000002", "YES",      "Alisha"),
    cl("F000003", "NOT PICK", "Shivani"),
    cl("F000004", "YES",      "Shivani"),
    cl("F000005", "YES",      "Shivani"),
    cl("F000006", "YES",      "Ranjeet"),
])
outbound = pd.DataFrame([
    ob(D, "9000000001", "Shivani Srivastava", "connected", 1),
    ob(D, "9000000002", "Alisha Khan",        "missed",    2),
    ob(D, "9000000003", "Shivani Srivastava", "connected", 3),
    ob(D, "9000000004", "Alisha Khan",        "connected", 4),
    ob(D, "9000000006", "Reception Mobile",   "connected", 5),
    ob(D, "9000000007", "Shivani Srivastava", "connected", 6),
], columns=P.OUTBOUND_LOG_COLS)

print("IVR reconciliation tests")
res = P.reconcile_calls(call_log, fu_ledger, visits, outbound)
c = res["counts"]
check("consistent counts 2 (connected+match, and Ranjeet/shared)", c["consistent"] == 2)
check("claims_reached_no_connect counts 1", c["claims_reached_no_connect"] == 1)
check("claims_noanswer_but_connected counts 1", c["claims_noanswer_but_connected"] == 1)
check("agent_mismatch counts 1 (Shivani logged, IVR Alisha)", c["agent_mismatch"] == 1)
check("logged_no_call counts 1 (no outbound)", c["logged_no_call"] == 1)
check("call_not_logged counts 1 (Gita called, never logged)", c["call_not_logged"] == 1)

by_key = {r["key"]: r for r in res["rows"] if r["key"]}
check("Ranjeet call is consistent (shared line, no mismatch)",
      by_key["F000006"]["flag"] == "consistent")

# empty outbound -> no false logged_no_call
res0 = P.reconcile_calls(call_log, fu_ledger, visits,
                         pd.DataFrame(columns=P.OUTBOUND_LOG_COLS))
check("empty outbound -> no_outbound, no false flags",
      res0["meta"].get("no_outbound") and all(v == 0 for v in res0["counts"].values()))

# ingest idempotency, redirected to a temp file (never touches real data\)
tmp = Path(tempfile.mkdtemp())
saved = P.OUTBOUND_LOG_FILE
try:
    P.OUTBOUND_LOG_FILE = tmp / "ob.csv"
    f = tmp / "in.csv"
    f.write_text("Date,Time,Phone10,Agent,Duration_s,Status,Start_Unix\n"
                 "2026-06-20,09:10,9000000001,Shivani Srivastava,40,connected,1\n"
                 "2026-06-20,09:12,9000000002,Alisha Khan,40,missed,2\n")
    r1 = P.ingest_outbound_log(str(f))
    r2 = P.ingest_outbound_log(str(f))
    check("ingest: 2 added first, 0 added on re-upload",
          r1.get("added") == 2 and r2.get("added") == 0 and r2.get("total") == 2)
finally:
    P.OUTBOUND_LOG_FILE = saved

# ── Feature B: called-in & due worklist ─────────────────────────────────────
fu_b = pd.DataFrame([
    fu("F000010", "Hema",  "9000000010"),   # due + called in (missed)  -> listed
    fu("F000011", "Indu",  "9000000011"),   # due + called in (connected) -> NOT listed
    fu("F000012", "Jaya",  "9000000012"),   # called in (missed) but NOT due -> NOT listed
])
fu_b.loc[fu_b["Followup_ID"] == "F000010", "Followup_Status"] = "Probable Dropout"
fu_b.loc[fu_b["Followup_ID"] == "F000011", "Followup_Status"] = "Grace Period"
fu_b.loc[fu_b["Followup_ID"] == "F000012", "Followup_Status"] = "Returned On Time"

feed_b = pd.DataFrame([
    ob(D, "9000000010", "", "missed",    11, direction="incoming"),
    ob(D, "9000000011", "", "connected", 12, direction="incoming"),  # connected, not missed
    ob(D, "9000000012", "", "missed",    13, direction="incoming"),  # not due
    ob(D, "9000000099", "Shivani Srivastava", "connected", 14, direction="outgoing"),  # outbound, ignored
], columns=P.OUTBOUND_LOG_COLS)

b = P.find_called_in_and_due(fu_b, feed_b)
names = {r["name"] for r in b["rows"]}
check("Feature B lists a due patient who called in & was missed (Hema)", "Hema" in names)
check("Feature B excludes connected call-ins (Indu not listed)", "Indu" not in names)
check("Feature B excludes call-ins from non-due patients (Jaya not listed)", "Jaya" not in names)
check("Feature B ignores outbound calls (count is 1)", b["count"] == 1)

# inbound rows must not leak into reconciliation
mixed = pd.concat([outbound, feed_b], ignore_index=True)
resm = P.reconcile_calls(call_log, fu_ledger, visits, mixed)
check("reconcile ignores inbound rows (still 6 logged outcomes classified)",
      sum(resm["counts"][k] for k in
          ["consistent","claims_reached_no_connect","claims_noanswer_but_connected",
           "agent_mismatch","logged_no_call"]) == 6)

# ── Reinstated callbacks (deterrent) ────────────────────────────────────────
import datetime as _dt
_tmpr = Path(tempfile.mkdtemp())
_saved_r = P.REINSTATE_FILE
try:
    P.REINSTATE_FILE = _tmpr / "reinstate.csv"
    fr_ledger = pd.DataFrame([fu("F000020", "Lajjawati", "9000000020")])
    fr_call = pd.DataFrame([cl("F000020", "NOT PICK", "Alisha")])
    fr_ob = pd.DataFrame([ob(D, "9000000020", "Shivani Srivastava", "connected", 1)],
                         columns=P.OUTBOUND_LOG_COLS)
    s1 = P.sync_reinstatements(fr_call, fr_ledger, visits, fr_ob, _dt.date(2026, 6, 23))
    check("reinstatement opens from NOT-PICK-but-connected", s1["new"] == 1 and s1["open"] == 1)
    s2 = P.sync_reinstatements(fr_call, fr_ledger, visits, fr_ob, _dt.date(2026, 6, 23))
    check("reinstatement sync is idempotent (no second open)", s2["new"] == 0 and s2["open"] == 1)
    recs = P.open_reinstatement_records()
    check("reinstatement row is callable & keyed to the follow-up",
          len(recs) == 1 and recs[0]["key"] == "F000020" and "Alisha" in recs[0]["info"])
    # re-logging NOT PICK on a new day must NOT add a second row or clear it
    fr_call2 = pd.concat([fr_call, pd.DataFrame([cl("F000020", "NOT PICK", "Alisha", "2026-06-23")])], ignore_index=True)
    fr_ob2 = pd.concat([fr_ob, pd.DataFrame([ob("2026-06-23", "9000000020", "Shivani Srivastava", "connected", 2)],
                                            columns=P.OUTBOUND_LOG_COLS)], ignore_index=True)
    s3 = P.sync_reinstatements(fr_call2, fr_ledger, visits, fr_ob2, _dt.date(2026, 6, 24))
    check("re-logging NOT PICK keeps exactly one open (un-escapable)", s3["open"] == 1)
    # a later genuine RESOLVE clears it
    fr_call3 = pd.concat([fr_call2, pd.DataFrame([cl("F000020", "YES", "Alisha", "2026-06-24")])], ignore_index=True)
    s4 = P.sync_reinstatements(fr_call3, fr_ledger, visits, fr_ob2, _dt.date(2026, 6, 25))
    check("later RESOLVE clears the reinstatement", s4["cleared"] == 1 and s4["open"] == 0)
finally:
    P.REINSTATE_FILE = _saved_r

# ── Confirmation layer (Tt COMPLETE / MED HERE / NO) ────────────────────────
_tmpc = Path(tempfile.mkdtemp())
_saved_c, _saved_r2 = P.CONFIRM_FILE, P.REINSTATE_FILE
try:
    P.CONFIRM_FILE = _tmpc / "confirmations.csv"
    P.REINSTATE_FILE = _tmpc / "reinstate.csv"
    cfu = pd.DataFrame([
        fu("F000030", "Asha", "9000000030"), fu("F000031", "Bina", "9000000031"),
        fu("F000032", "Chaya", "9000000032"), fu("F000033", "Devi", "9000000033")])
    for _i, _r in cfu.iterrows():
        cfu.at[_i, "Clinic_Specific_Id_Resolved"] = "C-" + cfu.at[_i, "Followup_ID"][-3:]
    ccl = pd.DataFrame([
        cl("F000030", "Tt COMPLETE", "Alisha"), cl("F000031", "MED HERE", "Shivani"),
        cl("F000032", "NO", "Shavez"), cl("F000033", "MED OUTSIDE", "Alisha")])
    cs1 = P.sync_confirmations(ccl, cfu, _dt.date(2026, 6, 23))
    check("confirmations open from Tt COMPLETE / MED HERE / NO (not MED OUTSIDE)",
          cs1["new"] == 3 and cs1["open"] == 3)
    cs2 = P.sync_confirmations(ccl, cfu, _dt.date(2026, 6, 23))
    check("confirmation sync is idempotent", cs2["new"] == 0 and cs2["open"] == 3)
    cv = P.open_confirmations_view()
    owners = {x["Conf_Type"]: x["Owner"] for x in cv}
    check("owners routed correctly (Tt→Shavez, MED HERE→Pharmacy, DECLINE→Shavez)",
          owners.get("Tt COMPLETE") == "Shavez" and owners.get("MED HERE") == "Pharmacy"
          and owners.get("DECLINE") == "Shavez")
    check("confirmation carries Clinic ID",
          all(x["Clinic_Id"].startswith("C-") for x in cv))
    tt_id = [x["Confirm_ID"] for x in cv if x["Conf_Type"] == "Tt COMPLETE"][0]
    check("confirm closes the item", P.confirm_confirmation(tt_id, "Shavez")
          and len(P.open_confirmations_view()) == 2)
    med_id = [x["Confirm_ID"] for x in cv if x["Conf_Type"] == "MED HERE"][0]
    check("reject reinstates a callback",
          P.reject_confirmation(med_id, "Pharmacy", "no bill found")
          and len(P.open_reinstatement_records()) == 1)
finally:
    P.CONFIRM_FILE, P.REINSTATE_FILE = _saved_c, _saved_r2

# ── Perpetual-LATER escalation ──────────────────────────────────────────────
def _cll(key, resp, d):
    r = {c: "" for c in P.CALL_LOG_COLS}
    r.update({"Obligation_Key": key, "Call_Date": d, "Response": resp,
              "Called_By": "Alisha", "Key_Type": "Followup", "Call_ID": d,
              "Resolution_Class": P.RESOLUTION_MAP.get(resp, "")})
    return r
lfu = pd.DataFrame([fu("F1", "Asha", "9000000001"), fu("F2", "Bina", "9000000002")])
llog = pd.DataFrame([_cll("F1", "LATER", "2026-06-10"), _cll("F1", "LATER", "2026-06-14"),
                     _cll("F1", "LATER", "2026-06-18"), _cll("F2", "LATER", "2026-06-12"),
                     _cll("F2", "LATER", "2026-06-16")])
lout = P.recompute_call_summary(lfu, llog)
lres = dict(zip(lout["Followup_ID"], lout["Call_Resolution"]))
check("3 consecutive LATERs escalate (perpetual deferral)", lres["F1"] == "ESCALATE")
check("2 consecutive LATERs do not escalate yet", lres["F2"] == "RESCHEDULE")

passed = sum(1 for _, ok in results if ok)
total = len(results)
print(f"\n{'ALL ' + str(total) + ' PASSED' if passed == total else str(total - passed) + ' FAILED'} "
      f"({passed}/{total})")
raise SystemExit(0 if passed == total else 1)
