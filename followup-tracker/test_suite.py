"""
Comprehensive test suite for the Follow-Up Tracker.
Tests all edge cases before deployment.
"""
import sys
import os
import shutil
import pandas as pd
from datetime import date, timedelta
from pathlib import Path
import traceback

# ── Setup ─────────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

# Redirect data dir to a temp test location so we don't corrupt real data
import processor as P
TEST_DATA = Path("/tmp/tracker_test_data")
P.DATA_DIR      = TEST_DATA
P.MASTER_FILE   = TEST_DATA / "patient_master.csv"
P.VISITS_FILE   = TEST_DATA / "visit_ledger.csv"
P.FOLLOWUP_FILE = TEST_DATA / "followup_ledger.csv"
P.OUTPUTS_DIR   = TEST_DATA / "outputs"

PASS = 0
FAIL = 0

def reset():
    if TEST_DATA.exists():
        shutil.rmtree(TEST_DATA)
    TEST_DATA.mkdir()
    (TEST_DATA / "outputs").mkdir()

def ok(name):
    global PASS
    PASS += 1
    print(f"  ✅  {name}")

def fail(name, detail=""):
    global FAIL
    FAIL += 1
    print(f"  ❌  {name}")
    if detail:
        print(f"      {detail}")

def section(title):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")

# ── CSV helpers ───────────────────────────────────────────────────────────────
def make_consult_csv(path, rows, date_str):
    """
    rows = list of dicts with keys: uid, csid, name, mobile
    Writes a Docterz-format consultation CSV with the clinic header row.
    """
    cols = [
        "Sr No","Patient Name","Patient UID","Mobile","Gender","DOB","Age",
        "Address","Consultation Date","Doctor","Clinic Specific Id",
        "Prescription","Purpose Of Visit","Bill Amount","Amount collected",
        "Bill Amount Pending","Advance Collected","Adjust Advance",
        "Consultation Amount","Consultation Discount","Procedure Amount",
        "Procedure Discount","Drugs Amount","Drugs Discount",
        "Vaccination Amount","Vaccination Discount","Package Amount",
        "Package Discount","Laboratory Amount","Laboratory Discount",
        "Radiology Amount","Radiology Discount","Cashback","Points",
        "Mode Of Payment","Payment Collected By","Invoice No.","Schedule","Notes"
    ]
    empty_row = {c: "" for c in cols}
    header_row = dict(empty_row)
    header_row["Sr No"] = "Dr. Manoj Agarwal Clinic"

    data_rows = []
    for i, r in enumerate(rows, 1):
        row = dict(empty_row)
        row["Sr No"]              = str(i)
        row["Patient Name"]       = r["name"]
        row["Patient UID"]        = r["uid"]
        row["Mobile"]             = r.get("mobile", "")
        row["Clinic Specific Id"] = r.get("csid", "")
        row["Consultation Date"]  = f"{date_str} 10:00 AM"
        row["Doctor"]             = "Manoj Agarwal"
        data_rows.append(row)

    df = pd.DataFrame([header_row] + data_rows, columns=cols)
    df.to_csv(path, index=False)

def make_followup_csv(path, rows):
    """
    rows = list of dicts with keys: appt_id, mobile, name, due_date (YYYY-MM-DD)
    """
    data = []
    for r in rows:
        due = r["due_date"]
        # Convert YYYY-MM-DD → DD-MM-YYYY for Docterz format
        d = date.fromisoformat(due)
        due_docterz = d.strftime("%d-%m-%Y")
        data.append({
            "Appointment ID": r["appt_id"],
            "Mobile No":      r.get("mobile", ""),
            "Patient Name":   r["name"],
            "Followup Text":  f"Dr Manoj Agarwal has advised followup for {r['name']} on {due_docterz}.",
            "Followup Date":  due_docterz,
            "Doctor Name":    "Manoj Agarwal",
            "Comments":       ""
        })
    pd.DataFrame(data).to_csv(path, index=False)

# ══════════════════════════════════════════════════════════════════════════════
# TEST GROUPS
# ══════════════════════════════════════════════════════════════════════════════

def test_mobile_cleaning():
    section("1. Mobile Cleaning")
    cases = [
        ("9837077893",        "9837077893", "plain 10-digit"),
        ("09837077893",       "9837077893", "leading zero"),
        ("+919837077893",     "9837077893", "+91 prefix"),
        ("919837077893",      "9837077893", "91 prefix no plus"),
        ("98370 77893",       "9837077893", "spaces"),
        ("9837-077-893",      "9837077893", "hyphens"),
        ("8390518904.0",      "8390518904", "float string from pandas"),
        ("8390518904",        "8390518904", "int as string"),
        (8390518904.0,        "8390518904", "actual float"),
        (8390518904,          "8390518904", "actual int"),
        ("1111111111",        "",           "Docterz no-mobile placeholder"),
        ("1234567890",        "",           "starts with 1 — invalid Indian"),
        ("12345",             "",           "too short"),
        ("",                  "",           "empty string"),
        (None,                "",           "None"),
        (float("nan"),        "",           "NaN"),
        ("abcdefghij",        "",           "all letters"),
    ]
    for raw, expected, label in cases:
        result = P.clean_mobile(raw)
        if result == expected:
            ok(f"Mobile: {label} → '{result}'")
        else:
            fail(f"Mobile: {label}", f"expected '{expected}', got '{result}'")

def test_date_parsing():
    section("2. Date Parsing")
    cases = [
        ("01-06-2026",            date(2026,6,1),  "DD-MM-YYYY"),
        ("2026-06-01",            date(2026,6,1),  "YYYY-MM-DD"),
        ("01/06/2026",            date(2026,6,1),  "DD/MM/YYYY"),
        ("01-06-2026 01:25 PM",   date(2026,6,1),  "Docterz datetime"),
        ("",                      None,             "empty"),
        (None,                    None,             "None"),
        ("not-a-date",            None,             "garbage string"),
    ]
    for raw, expected, label in cases:
        result = P.parse_date(raw)
        if result == expected:
            ok(f"Date: {label} → {result}")
        else:
            fail(f"Date: {label}", f"expected {expected}, got {result}")

def test_followup_log_date_derivation():
    section("3. Follow-Up Log Date Derivation (Due_Date - 1 day)")
    path = "/tmp/test_fu.csv"
    # Due date is 2026-06-02 → log date should be 2026-06-01
    make_followup_csv(path, [
        {"appt_id": "100", "mobile": "9837077893", "name": "Test Patient", "due_date": "2026-06-02"}
    ])
    df, log_date = P.parse_followup_log(path)
    if log_date == "2026-06-01":
        ok(f"Log date derived correctly: {log_date}")
    else:
        fail("Log date derivation", f"expected 2026-06-01, got {log_date}")

    # Mixed due dates: 2026-06-02 and 2026-06-05 → log date should be 2026-06-01
    make_followup_csv(path, [
        {"appt_id": "101", "mobile": "9837077893", "name": "A", "due_date": "2026-06-02"},
        {"appt_id": "102", "mobile": "9837077894", "name": "B", "due_date": "2026-06-05"},
    ])
    df2, log_date2 = P.parse_followup_log(path)
    if log_date2 == "2026-06-01":
        ok(f"Mixed due dates → log date uses earliest: {log_date2}")
    else:
        fail("Mixed due dates log date", f"expected 2026-06-01, got {log_date2}")

    # Empty follow-up log
    make_followup_csv(path, [])
    try:
        df3, log_date3 = P.parse_followup_log(path)
        ok(f"Empty follow-up log handled (log_date={log_date3})")
    except Exception as e:
        fail("Empty follow-up log", str(e))

def test_patient_master_init():
    section("4. Patient Master Initialisation")
    reset()
    path = "/tmp/test_consult.csv"
    make_consult_csv(path, [
        {"uid":"UID001","csid":"1001","name":"Ramesh Kumar","mobile":"9837000001"},
        {"uid":"UID002","csid":"1002","name":"Sunita Devi", "mobile":"9837000002"},
        {"uid":"UID003","csid":"1003","name":"Mohan Lal",   "mobile":"9837000001"},  # shared mobile
        {"uid":"UID004","csid":"1004","name":"No Mobile",   "mobile":""},
        {"uid":"UID005","csid":"1005","name":"Bad Mobile",  "mobile":"12345"},
    ], "01-06-2026")

    consult, _ = P.parse_consultation_report(path)
    master = P.pd.DataFrame(columns=P.MASTER_COLS)
    master, new_count = P.update_master_from_consultation(master, consult, "2026-06-01")
    P.save_master(master)

    if new_count == 5:
        ok(f"5 patients added")
    else:
        fail("Patient count", f"expected 5, got {new_count}")

    # Shared mobile flagged correctly
    shared = master[master["Identity_Status"] == "Shared Mobile"]
    if len(shared) == 2:
        ok("Shared mobile: 2 patients flagged as Shared Mobile")
    else:
        fail("Shared mobile count", f"expected 2, got {len(shared)}")

    # No/Invalid mobile
    no_mob = master[master["Identity_Status"] == "No/Invalid Mobile"]
    if len(no_mob) == 2:
        ok("No/Invalid mobile: 2 patients flagged")
    else:
        fail("No/Invalid mobile count", f"expected 2, got {len(no_mob)}")

    # Unique mobile
    unique = master[master["Identity_Status"] == "Unique Mobile"]
    if len(unique) == 1:
        ok("Unique mobile: 1 patient correctly unique")
    else:
        fail("Unique mobile count", f"expected 1, got {len(unique)}")

def test_second_day_no_duplication():
    section("5. Second Day Run — No Ledger Duplication")
    reset()
    consult_path = "/tmp/test_consult.csv"
    fu_path      = "/tmp/test_fu.csv"

    # Day 1
    make_consult_csv(consult_path, [
        {"uid":"UID001","csid":"1001","name":"Ramesh Kumar","mobile":"9837000001"},
    ], "01-06-2026")
    make_followup_csv(fu_path, [
        {"appt_id":"A001","mobile":"9837000001","name":"Ramesh Kumar","due_date":"2026-06-02"},
    ])
    P.run_daily(consult_path, fu_path, today=date(2026,6,1))

    # Day 2 — same patient seen again, same follow-up appt_id uploaded again
    make_consult_csv(consult_path, [
        {"uid":"UID001","csid":"1001","name":"Ramesh Kumar","mobile":"9837000001"},
        {"uid":"UID002","csid":"1002","name":"New Patient", "mobile":"9837000002"},
    ], "02-06-2026")
    # Same follow-up log re-uploaded (simulating accidental re-upload)
    P.run_daily(consult_path, fu_path, today=date(2026,6,2))

    visits = P.load_visits()
    master = P.load_master()
    fu     = P.load_followups()

    # UID001 should have 2 visits (one per day), not 3 or 4
    uid001_visits = visits[visits["Patient_UID"]=="UID001"]
    if len(uid001_visits) == 2:
        ok("Visit deduplication: UID001 has exactly 2 visits across 2 days")
    else:
        fail("Visit deduplication", f"expected 2, got {len(uid001_visits)}")

    # Follow-up obligation should not be duplicated
    fu_count = len(fu[fu["Appointment_ID"]=="A001"])
    if fu_count == 1:
        ok("Follow-up deduplication: A001 appears exactly once in ledger")
    else:
        fail("Follow-up deduplication", f"expected 1, got {fu_count}")

    # Master should have 2 patients
    if len(master) == 2:
        ok("Patient Master: 2 patients after 2 days")
    else:
        fail("Patient Master count", f"expected 2, got {len(master)}")

    # UID001 Last_Seen_Date should be day 2
    last_seen = master[master["Patient_UID"]=="UID001"]["Last_Seen_Date"].iloc[0]
    if last_seen == "2026-06-02":
        ok(f"Last_Seen_Date updated to day 2: {last_seen}")
    else:
        fail("Last_Seen_Date", f"expected 2026-06-02, got {last_seen}")

def test_status_transitions():
    section("6. Status Transitions Across Days")
    reset()
    consult_path = "/tmp/test_consult.csv"
    fu_path      = "/tmp/test_fu.csv"

    # Day 0 (30 May): seed master with 4 patients
    make_consult_csv(consult_path, [
        {"uid":"P001","csid":"101","name":"On Time Patient",  "mobile":"9001000001"},
        {"uid":"P002","csid":"102","name":"Late Patient",     "mobile":"9001000002"},
        {"uid":"P003","csid":"103","name":"Dropout Patient",  "mobile":"9001000003"},
        {"uid":"P004","csid":"104","name":"Early Patient",    "mobile":"9001000004"},
    ], "30-05-2026")
    make_followup_csv(fu_path, [])  # no follow-ups on day 0
    P.run_daily(consult_path, fu_path, today=date(2026,5,30))

    # Day 1 (31 May): follow-ups given for 02 June
    make_consult_csv(consult_path, [], "31-05-2026")
    make_followup_csv(fu_path, [
        {"appt_id":"F001","mobile":"9001000001","name":"On Time Patient", "due_date":"2026-06-02"},
        {"appt_id":"F002","mobile":"9001000002","name":"Late Patient",    "due_date":"2026-06-02"},
        {"appt_id":"F003","mobile":"9001000003","name":"Dropout Patient", "due_date":"2026-06-02"},
        {"appt_id":"F004","mobile":"9001000004","name":"Early Patient",   "due_date":"2026-06-02"},
    ])
    P.run_daily(consult_path, fu_path, today=date(2026,5,31))

    # Verify all show "Not Due" on 31 May
    fu = P.load_followups()
    not_due = fu[fu["Followup_Status"]=="Not Due"]
    if len(not_due) == 4:
        ok("31 May: all 4 follow-ups show Not Due")
    else:
        fail("Not Due count on 31 May", f"expected 4, got {len(not_due)}")

    # Day 2 (01 June): Early Patient comes in before due date
    make_consult_csv(consult_path, [
        {"uid":"P004","csid":"104","name":"Early Patient","mobile":"9001000004"},
    ], "01-06-2026")
    make_followup_csv(fu_path, [])
    P.run_daily(consult_path, fu_path, today=date(2026,6,1))

    fu = P.load_followups()
    early_status = fu[fu["Appointment_ID"]=="F004"]["Followup_Status"].iloc[0]
    if early_status == "Returned Early":
        ok(f"01 Jun: Early Patient = Returned Early ✓")
    else:
        fail("Early return status", f"expected 'Returned Early', got '{early_status}'")

    # Day 3 (02 June = due date): On Time Patient comes in on due date
    make_consult_csv(consult_path, [
        {"uid":"P001","csid":"101","name":"On Time Patient","mobile":"9001000001"},
    ], "02-06-2026")
    make_followup_csv(fu_path, [])
    P.run_daily(consult_path, fu_path, today=date(2026,6,2))

    fu = P.load_followups()
    ontime_status = fu[fu["Appointment_ID"]=="F001"]["Followup_Status"].iloc[0]
    if ontime_status == "Returned On Time":
        ok(f"02 Jun: On Time Patient = Returned On Time ✓")
    else:
        fail("On-time return status", f"expected 'Returned On Time', got '{ontime_status}'")

    # Day 5 (04 June = 2 days past due): no-shows should be Grace Period
    make_consult_csv(consult_path, [], "04-06-2026")
    make_followup_csv(fu_path, [])
    P.run_daily(consult_path, fu_path, today=date(2026,6,4))

    fu = P.load_followups()
    grace_statuses = fu[fu["Appointment_ID"].isin(["F002","F003"])]["Followup_Status"].tolist()
    if all(s == "Grace Period" for s in grace_statuses):
        ok(f"04 Jun (2 days overdue): 2 patients in Grace Period ✓")
    else:
        fail("Grace Period", f"expected both Grace Period, got {grace_statuses}")

    # Day 7 (06 June = 4 days past due): Late Patient comes in
    make_consult_csv(consult_path, [
        {"uid":"P002","csid":"102","name":"Late Patient","mobile":"9001000002"},
    ], "06-06-2026")
    make_followup_csv(fu_path, [])
    P.run_daily(consult_path, fu_path, today=date(2026,6,6))

    fu = P.load_followups()
    late_status   = fu[fu["Appointment_ID"]=="F002"]["Followup_Status"].iloc[0]
    action_status = fu[fu["Appointment_ID"]=="F003"]["Followup_Status"].iloc[0]
    if late_status == "Returned Late":
        ok(f"06 Jun: Late Patient = Returned Late ✓ (delay={fu[fu['Appointment_ID']=='F002']['Return_Delay_Days'].iloc[0]} days)")
    else:
        fail("Late return status", f"expected 'Returned Late', got '{late_status}'")
    if action_status == "Actionable Missed Follow-Up":
        ok(f"06 Jun: Dropout Patient = Actionable Missed Follow-Up ✓")
    else:
        fail("Actionable Missed status", f"expected 'Actionable Missed Follow-Up', got '{action_status}'")

    # Day 14 (13 June = 11 days past due): Dropout Patient still missing
    make_consult_csv(consult_path, [], "13-06-2026")
    make_followup_csv(fu_path, [])
    P.run_daily(consult_path, fu_path, today=date(2026,6,13))

    fu = P.load_followups()
    dropout_status = fu[fu["Appointment_ID"]=="F003"]["Followup_Status"].iloc[0]
    days_overdue   = fu[fu["Appointment_ID"]=="F003"]["Days_Overdue"].iloc[0]
    if dropout_status == "Probable Dropout":
        ok(f"13 Jun: Dropout Patient = Probable Dropout ✓ ({days_overdue} days overdue)")
    else:
        fail("Probable Dropout status", f"expected 'Probable Dropout', got '{dropout_status}'")

    # Once returned, status must NOT regress even if run again
    fu_before = fu[fu["Appointment_ID"]=="F001"]["Followup_Status"].iloc[0]
    make_consult_csv(consult_path, [], "14-06-2026")
    make_followup_csv(fu_path, [])
    P.run_daily(consult_path, fu_path, today=date(2026,6,14))
    fu_after = P.load_followups()
    fu_after_status = fu_after[fu_after["Appointment_ID"]=="F001"]["Followup_Status"].iloc[0]
    if fu_after_status == "Returned On Time":
        ok("Returned status does not regress on subsequent runs ✓")
    else:
        fail("Status regression", f"On Time Patient changed to '{fu_after_status}' after re-run")

def test_shared_mobile_resolution():
    section("7. Shared Mobile Identity Resolution")
    reset()
    consult_path = "/tmp/test_consult.csv"
    fu_path      = "/tmp/test_fu.csv"

    # Two family members sharing one mobile
    make_consult_csv(consult_path, [
        {"uid":"FAM001","csid":"201","name":"Ramesh Gupta", "mobile":"9500000001"},
        {"uid":"FAM002","csid":"202","name":"Sunita Gupta", "mobile":"9500000001"},
        {"uid":"FAM003","csid":"203","name":"Unrelated",    "mobile":"9500000002"},
    ], "01-06-2026")
    make_followup_csv(fu_path, [
        # Follow-up for Ramesh — name should match FAM001
        {"appt_id":"FA01","mobile":"9500000001","name":"Ramesh Gupta","due_date":"2026-06-02"},
        # Follow-up for Sunita — name should match FAM002
        {"appt_id":"FA02","mobile":"9500000001","name":"Sunita Gupta","due_date":"2026-06-02"},
        # Follow-up for a completely different name on shared mobile — should be Ambiguous
        {"appt_id":"FA03","mobile":"9500000001","name":"Xyz Unknown", "due_date":"2026-06-02"},
    ])
    P.run_daily(consult_path, fu_path, today=date(2026,6,1))

    fu = P.load_followups()

    r1 = fu[fu["Appointment_ID"]=="FA01"].iloc[0]
    if r1["Patient_UID_Resolved"] == "FAM001" and r1["Identity_Confidence"] == "Medium":
        ok(f"Shared mobile: Ramesh correctly resolved to FAM001 (Medium confidence)")
    else:
        fail("Shared mobile Ramesh", f"UID={r1['Patient_UID_Resolved']}, conf={r1['Identity_Confidence']}")

    r2 = fu[fu["Appointment_ID"]=="FA02"].iloc[0]
    if r2["Patient_UID_Resolved"] == "FAM002" and r2["Identity_Confidence"] == "Medium":
        ok(f"Shared mobile: Sunita correctly resolved to FAM002 (Medium confidence)")
    else:
        fail("Shared mobile Sunita", f"UID={r2['Patient_UID_Resolved']}, conf={r2['Identity_Confidence']}")

    r3 = fu[fu["Appointment_ID"]=="FA03"].iloc[0]
    if r3["Identity_Confidence"] == "Ambiguous":
        ok(f"Shared mobile: Unknown name correctly flagged as Ambiguous")
    else:
        fail("Shared mobile ambiguous", f"expected Ambiguous, got '{r3['Identity_Confidence']}'")

def test_edge_cases():
    section("8. Edge Cases")
    reset()

    fu_path      = "/tmp/test_fu.csv"
    consult_path = "/tmp/test_consult.csv"

    # Empty consultation report
    make_consult_csv(consult_path, [], "01-06-2026")
    make_followup_csv(fu_path, [])
    try:
        P.run_daily(consult_path, fu_path, today=date(2026,6,1))
        ok("Empty consultation report handled without crash")
    except Exception as e:
        fail("Empty consultation report", str(e))

    # Empty follow-up log
    make_consult_csv(consult_path, [
        {"uid":"E001","csid":"301","name":"Patient A","mobile":"9600000001"}
    ], "02-06-2026")
    make_followup_csv(fu_path, [])
    try:
        P.run_daily(consult_path, fu_path, today=date(2026,6,2))
        ok("Empty follow-up log handled without crash")
    except Exception as e:
        fail("Empty follow-up log", str(e))

    # Patient with completely missing mobile in follow-up log
    make_followup_csv(fu_path, [
        {"appt_id":"E001","mobile":"","name":"No Mobile Patient","due_date":"2026-06-04"},
    ])
    make_consult_csv(consult_path, [], "03-06-2026")
    try:
        P.run_daily(consult_path, fu_path, today=date(2026,6,3))
        fu = P.load_followups()
        status = fu[fu["Appointment_ID"]=="E001"]["Followup_Status"].iloc[0]
        if status == "Invalid Mobile / No Contact":
            ok(f"Missing mobile in follow-up log → '{status}' ✓")
        else:
            fail("Missing mobile status", f"expected 'Invalid Mobile / No Contact', got '{status}'")
    except Exception as e:
        fail("Missing mobile in follow-up log", str(e))

    # Mobile not in master at all
    make_followup_csv(fu_path, [
        {"appt_id":"E002","mobile":"9999999999","name":"Ghost Patient","due_date":"2026-06-04"},
    ])
    make_consult_csv(consult_path, [], "03-06-2026")
    try:
        P.run_daily(consult_path, fu_path, today=date(2026,6,3))
        fu = P.load_followups()
        status = fu[fu["Appointment_ID"]=="E002"]["Followup_Status"].iloc[0]
        if status == "Identity Unresolved":
            ok(f"Mobile not in Master → '{status}' ✓")
        else:
            fail("Unresolved identity status", f"expected 'Identity Unresolved', got '{status}'")
    except Exception as e:
        fail("Mobile not in master", str(e))

    # Follow-up log uploaded twice (accidental re-upload) — no duplication
    reset()
    make_consult_csv(consult_path, [
        {"uid":"DUP001","csid":"401","name":"Dup Test","mobile":"9700000001"}
    ], "01-06-2026")
    make_followup_csv(fu_path, [
        {"appt_id":"DUP_A","mobile":"9700000001","name":"Dup Test","due_date":"2026-06-02"},
    ])
    P.run_daily(consult_path, fu_path, today=date(2026,6,1))
    # Upload same follow-up log again
    make_consult_csv(consult_path, [], "02-06-2026")
    P.run_daily(consult_path, fu_path, today=date(2026,6,2))
    fu = P.load_followups()
    count = len(fu[fu["Appointment_ID"]=="DUP_A"])
    if count == 1:
        ok("Accidental re-upload of follow-up log: no duplication ✓")
    else:
        fail("Follow-up re-upload dedup", f"expected 1, got {count}")

def test_excel_output():
    section("9. Excel Output Structure")
    reset()
    consult_path = "/tmp/test_consult.csv"
    fu_path      = "/tmp/test_fu.csv"

    make_consult_csv(consult_path, [
        {"uid":"X001","csid":"501","name":"Excel Test","mobile":"9800000001"}
    ], "01-06-2026")
    make_followup_csv(fu_path, [
        {"appt_id":"X_F01","mobile":"9800000001","name":"Excel Test","due_date":"2026-06-02"},
    ])
    out = P.run_daily(consult_path, fu_path, today=date(2026,6,1))

    try:
        xl = pd.ExcelFile(out)
        expected_sheets = [
            "Dashboard", "Staff Action Today", "Probable Dropouts",
            "Returned Late", "Identity Problems",
            "Follow-Up Ledger", "Visit Ledger", "Patient Master"
        ]
        for sheet in expected_sheets:
            if sheet in xl.sheet_names:
                ok(f"Sheet exists: {sheet}")
            else:
                fail(f"Missing sheet: {sheet}")

        # Staff Action Today should have 1 row (Not Due — but wait, 
        # Not Due is excluded from Staff Action. So 0 rows.)
        df_action = xl.parse("Staff Action Today")
        if len(df_action) == 0:
            ok("Staff Action Today: 0 rows (Not Due excluded correctly) ✓")
        else:
            fail("Staff Action Today row count", f"expected 0, got {len(df_action)}: {df_action['Status'].tolist()}")
    except Exception as e:
        fail("Excel output", str(e))
        traceback.print_exc()

def test_patient_list_ingestion():
    section("10. Patient List Ingestion (DOCTERZ_PATIENT_LIST format)")
    reset()

    # Write a minimal patient list CSV in the real Docterz format
    path = "/tmp/test_patient_list.csv"
    pd.DataFrame([
        {"Name":"Ramesh Kumar",  "Age":"45","Sex":"male","DOB":"01/01/1980","Parent Name":"",
         "Mobile":"9837000001","Email":"","Address":"Bareilly",
         "Patient UID":"PL001","Clinic Specific Id":"101","Registered On":"01/01/2024",
         "Significant History":"","Past History":"","Surgeon Notes":"","Allergy History":"",
         "Delivery Notes":"","Feeding History":"","Family History":"","Social History":"",
         "Foot Notes":"","Patient Medical History":""},
        # Shared mobile
        {"Name":"Sunita Kumar","Age":"42","Sex":"female","DOB":"01/01/1983","Parent Name":"",
         "Mobile":"9837000001","Email":"","Address":"Bareilly",
         "Patient UID":"PL002","Clinic Specific Id":"102","Registered On":"01/01/2024",
         "Significant History":"","Past History":"","Surgeon Notes":"","Allergy History":"",
         "Delivery Notes":"","Feeding History":"","Family History":"","Social History":"",
         "Foot Notes":"","Patient Medical History":""},
        # 1111111111 placeholder
        {"Name":"No Mobile Patient","Age":"60","Sex":"male","DOB":"01/01/1965","Parent Name":"",
         "Mobile":"1111111111","Email":"","Address":"",
         "Patient UID":"PL003","Clinic Specific Id":"103","Registered On":"01/01/2024",
         "Significant History":"","Past History":"","Surgeon Notes":"","Allergy History":"",
         "Delivery Notes":"","Feeding History":"","Family History":"","Social History":"",
         "Foot Notes":"","Patient Medical History":""},
        # Duplicate UID (exact copy of PL001 — should be deduped)
        {"Name":"Ramesh Kumar",  "Age":"45","Sex":"male","DOB":"01/01/1980","Parent Name":"",
         "Mobile":"9837000001","Email":"","Address":"Bareilly",
         "Patient UID":"PL001","Clinic Specific Id":"101","Registered On":"01/01/2024",
         "Significant History":"","Past History":"","Surgeon Notes":"","Allergy History":"",
         "Delivery Notes":"","Feeding History":"","Family History":"","Social History":"",
         "Foot Notes":"","Patient Medical History":""},
    ]).to_csv(path, index=False)

    result = P.run_initial_master(path)
    master = P.load_master()

    # Should have 3 unique patients (PL001, PL002, PL003) — duplicate PL001 removed
    if len(master) == 3:
        ok(f"Patient list: 3 unique patients ingested (1 duplicate removed)")
    else:
        fail("Patient list count", f"expected 3, got {len(master)}")

    # 1111111111 should be No/Invalid Mobile (Mobile_Clean empty or nan when read from CSV)
    pl003 = master[master["Patient_UID"] == "PL003"].iloc[0]
    mob_clean_empty = pl003["Mobile_Clean"] == "" or pd.isna(pl003["Mobile_Clean"])
    if mob_clean_empty and pl003["Identity_Status"] == "No/Invalid Mobile":
        ok("1111111111 placeholder → No/Invalid Mobile, Mobile_Clean='' ✓")
    else:
        fail("1111111111 handling", f"Mobile_Clean='{pl003['Mobile_Clean']}', Identity='{pl003['Identity_Status']}'")

    # Shared mobile → Shared Mobile status, NOT No/Invalid Mobile
    pl001 = master[master["Patient_UID"] == "PL001"].iloc[0]
    pl002 = master[master["Patient_UID"] == "PL002"].iloc[0]
    if pl001["Identity_Status"] == "Shared Mobile" and pl002["Identity_Status"] == "Shared Mobile":
        ok("Shared family mobile → Shared Mobile status (not an error) ✓")
    else:
        fail("Shared mobile identity status",
             f"PL001={pl001['Identity_Status']}, PL002={pl002['Identity_Status']}")

    # 1111111111 must NOT be grouped with other patients as shared mobile
    no_mob_patients = master[master["Identity_Status"] == "No/Invalid Mobile"]
    if len(no_mob_patients) == 1 and no_mob_patients.iloc[0]["Patient_UID"] == "PL003":
        ok("1111111111 not incorrectly grouped as Shared Mobile ✓")
    else:
        fail("1111111111 grouping", f"No/Invalid patients: {no_mob_patients['Patient_UID'].tolist()}")

    # Summary string should be returned
    if "Patient Master initialised" in result and "3" in result:
        ok(f"Summary string returned correctly")
    else:
        fail("Summary string", result)


def test_real_patient_list():
    section("11. Real Patient List — DOCTERZ_PATIENT_LIST_UPTO_31_MAY_2026.csv")
    real_csv = "/mnt/user-data/uploads/DOCTERZ_PATIENT_LIST_UPTO_31_MAY_2026.csv"
    import os
    if not os.path.exists(real_csv):
        ok("Real CSV not present in test environment — skipping")
        return

    reset()
    try:
        result = P.run_initial_master(real_csv)
        master = P.load_master()

        # Basic sanity checks
        if len(master) >= 7000:
            ok(f"Real CSV: {len(master)} patients loaded (expected ~7248)")
        else:
            fail("Real CSV patient count", f"only {len(master)} loaded")

        no_mob = master[master["Identity_Status"] == "No/Invalid Mobile"]
        if len(no_mob) >= 79:
            ok(f"Real CSV: {len(no_mob)} no/invalid mobile patients (incl. 1111111111 group)")
        else:
            fail("Real CSV no-mobile count", f"expected ≥79, got {len(no_mob)}")

        # 1111111111 should NOT appear as Mobile_Clean anywhere
        placeholder_leak = master[master["Mobile_Clean"] == "1111111111"]
        if len(placeholder_leak) == 0:
            ok("1111111111 fully stripped from Mobile_Clean in real data ✓")
        else:
            fail("1111111111 leak", f"{len(placeholder_leak)} rows still have 1111111111 in Mobile_Clean")

        shared = master[master["Identity_Status"] == "Shared Mobile"]
        ok(f"Real CSV: {len(shared)} patients on shared/family mobiles")

        print(f"\n  Summary from run_initial_master:\n")
        for line in result.split("\n"):
            print(f"    {line}")

    except Exception as e:
        fail("Real CSV ingestion", traceback.format_exc())


# ══════════════════════════════════════════════════════════════════════════════
# RUN ALL TESTS
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "═"*60)
    print("  FOLLOW-UP TRACKER — FULL TEST SUITE")
    print("═"*60)

    try: test_mobile_cleaning()
    except Exception as e: fail("test_mobile_cleaning CRASHED", traceback.format_exc())

    try: test_date_parsing()
    except Exception as e: fail("test_date_parsing CRASHED", traceback.format_exc())

    try: test_followup_log_date_derivation()
    except Exception as e: fail("test_followup_log_date CRASHED", traceback.format_exc())

    try: test_patient_master_init()
    except Exception as e: fail("test_patient_master_init CRASHED", traceback.format_exc())

    try: test_second_day_no_duplication()
    except Exception as e: fail("test_second_day_no_duplication CRASHED", traceback.format_exc())

    try: test_status_transitions()
    except Exception as e: fail("test_status_transitions CRASHED", traceback.format_exc())

    try: test_shared_mobile_resolution()
    except Exception as e: fail("test_shared_mobile_resolution CRASHED", traceback.format_exc())

    try: test_edge_cases()
    except Exception as e: fail("test_edge_cases CRASHED", traceback.format_exc())

    try: test_excel_output()
    except Exception as e: fail("test_excel_output CRASHED", traceback.format_exc())

    try: test_patient_list_ingestion()
    except Exception as e: fail("test_patient_list_ingestion CRASHED", traceback.format_exc())

    try: test_real_patient_list()
    except Exception as e: fail("test_real_patient_list CRASHED", traceback.format_exc())

    print(f"\n{'═'*60}")
    print(f"  RESULTS:  {PASS} passed   {FAIL} failed   {PASS+FAIL} total")
    print(f"{'═'*60}\n")
    sys.exit(0 if FAIL == 0 else 1)
