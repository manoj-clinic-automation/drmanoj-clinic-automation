"""S779 walk: python -B walk_s779.py <dir holding docterz_pickup.py (+ dx_feed.py, diagnosis_normalizer.py)> <scratch db> [--control]
Made-up exports only (no real patient, no number). Prints 'WALK OK n/n' or, with --control, 'CONTROL: red (...)'."""
import sys, os, sqlite3, tempfile, importlib, csv, io, datetime as dt
code, db = sys.argv[1], sys.argv[2]
control = "--control" in sys.argv
store = tempfile.mkdtemp(prefix="s779store.")
os.environ["DOCTERZ_EXPORT_STORE"] = store
sys.path.insert(0, code)
for m in ("docterz_pickup", "dx_feed", "diagnosis_normalizer"):
    sys.modules.pop(m, None)
DP = importlib.import_module("docterz_pickup")
con = sqlite3.connect(db); con.row_factory = sqlite3.Row
DP.ensure(con)
D = dt.date(2031, 3, 14)                                    # a day far from any real export
ds = lambda d: d.strftime("%d-%m-%Y")
CONS_H = ["Sr No", "Patient Name", "Patient UID", "Mobile", "Consultation Date", "Clinic Specific Id", "Bill Amount", "Amount collected", "Mode Of Payment"]
CLIN_H = CONS_H + ["Complaints", "Findings", "Diagnosis", "Drugs Prescribed", "Follow Up"]
def csvb(head, rows):
    s = io.StringIO(); w = csv.writer(s); w.writerow(head); w.writerow(["Dr. Manoj Agarwal Clinic"]); [w.writerow(r) for r in rows]
    return s.getvalue().encode("utf-8")
cons = csvb(CONS_H, [["1", "TEST A", "WALKUID1", "", ds(D) + " 10:00 AM", "W1", "500", "500", "Cash"],
                     ["2", "TEST B", "WALKUID2", "", ds(D) + " 11:00 AM", "W2", "500", "500", "UPI"]])
clin_rows = [
  ["1", "TEST A", "WALKUID1", "", ds(D - dt.timedelta(30)) + " 10:00 AM", "W1", "500", "500", "Cash", "", "", "OSTEOARTHRITIS KNEE", "x", ds(D - dt.timedelta(16))],
  ["2", "TEST A", "WALKUID1", "", ds(D) + " 10:00 AM", "W1", "500", "500", "Cash", "", "", "OSTEOARTHRITIS KNEE", "x", ds(D + dt.timedelta(14))],
  ["3", "TEST B", "WALKUID2", "", ds(D) + " 11:00 AM", "W2", "500", "500", "UPI", "", "", "", "", ""],
  ["4", "TEST B", "WALKUID2", "", ds(D) + " 11:30 AM", "W2", "300", "300", "UPI", "", "", "ZZQ WALK TERM", "x", ds(D + dt.timedelta(7))],
  ["5", "TEST C", "WALKUID3", "", ds(D - dt.timedelta(9)) + " 12:00 PM", "W3", "500", "500", "Cash", "", "", "", "", ""],
]
clin = csvb(CLIN_H, clin_rows)
clin_day = csvb(CLIN_H, [clin_rows[1][:11] + ["LOW BACK PAIN", "x", ds(D + dt.timedelta(10))]])
fu_h = ["Appointment ID", "Mobile No", "Patient Name", "Followup Text", "Followup Date", "Doctor Name", "Comments"]
fol = csvb(fu_h, [["1", "", "TEST A", "t", ds(D + dt.timedelta(1)), "d", ""]])
def f(name, mt): return {"id": "walk:" + name, "name": name, "modifiedTime": mt}
res = []
def check(name, cond): res.append((name, bool(cond)))
k = DP.take(con, f("cons", "2031-03-14T15:00:00.000Z"), cons)
check("a consultation report is still a consultation report, current", k[0] == "consultation" and k[3] == "current")
cons_id = con.execute("SELECT id FROM docterz_export WHERE kind='consultation' AND business_date=? AND status='current'", (D.isoformat(),)).fetchone()[0]
k = DP.take(con, f("fol", "2031-03-14T15:01:00.000Z"), fol)
check("a follow-up log is still a follow-up log", k[0] == "followup")
k = DP.take(con, f("clin", "2031-03-14T15:30:00.000Z"), clin)
check("the clinical data report is its own kind", k[0] == "clinical")
check("the clinical report is current and named for its latest day", k[0] == "clinical" and k[3] == "current" and k[1] == D.isoformat())
r = con.execute("SELECT id, status FROM docterz_export WHERE kind='consultation' AND business_date=? ORDER BY id DESC LIMIT 1", (D.isoformat(),)).fetchone()
check("the day's consultation report is NOT replaced by it", r["id"] == cons_id and r["status"] == "current")
if not control:
    v = {(x["patient_uid"], x["visit_date"]): x for x in con.execute("SELECT * FROM dx_visit WHERE patient_uid LIKE 'WALKUID%'")}
    check("one row per patient per visit day (5 rows -> 4 visits)", len(v) == 4)
    a = v.get(("WALKUID1", D.isoformat()))
    check("a known diagnosis is standardised by the taxonomy", a is not None and a["std_dx"] == "Knee Osteoarthritis")
    check("the advised follow-up date is kept", a is not None and a["follow_up_date"] == (D + dt.timedelta(14)).isoformat())
    b = v.get(("WALKUID2", D.isoformat()))
    check("two rows on one day: the diagnosis written, the follow-up kept", b is not None and b["diagnosis_raw"] and b["follow_up_date"] == (D + dt.timedelta(7)).isoformat())
    check("an unknown term stays Other / Unclassified", b is not None and b["std_dx"] == "Other / Unclassified")
    check("no name or mobile column in the diagnosis table", not {"patient_name", "mobile"} & {c[1] for c in con.execute("PRAGMA table_info(dx_visit)")})
    k = DP.take(con, f("clin-again", "2031-03-14T16:00:00.000Z"), clin)
    check("the same clinical export again is a duplicate", k[3] == "duplicate")
    k = DP.take(con, f("clin-day", "2031-03-15T15:00:00.000Z"), clin_day)
    check("a later one-day clinical export with fewer rows is taken, not quarantined", k[0] == "clinical" and k[3] == "current")
    a2 = con.execute("SELECT std_dx, follow_up_date FROM dx_visit WHERE patient_uid='WALKUID1' AND visit_date=?", (D.isoformat(),)).fetchone()
    check("the newer export's diagnosis wins for that visit", a2 is not None and a2[1] == (D + dt.timedelta(10)).isoformat() and a2[0] != "Knee Osteoarthritis")
    old = con.execute("SELECT COUNT(*) FROM dx_visit WHERE patient_uid='WALKUID1'").fetchone()[0]
    check("the earlier export's other visits stay", old == 2)
    import dx_feed
    con.execute("INSERT OR REPLACE INTO dx_term_map (term, std_dx, set_by, set_at) VALUES ('ZZQ WALK TERM', 'Knee Osteoarthritis', 'walk', 'now')"); con.commit()
    dx_feed.reclassify(con)
    b2 = con.execute("SELECT std_dx FROM dx_visit WHERE patient_uid='WALKUID2' AND visit_date=?", (D.isoformat(),)).fetchone()
    check("a term the owner maps once is standardised on re-read", b2 is not None and b2[0] == "Knee Osteoarthritis")
    check("the owner's red lines do not count a clinical export as the consultation report",
          not any("clinical" in x.lower() for x in DP.owner_lines(con, dt.datetime(2031, 3, 15, 11, 0))))
bad = [n for n, ok in res if not ok]
if control:
    print("CONTROL: red (%s)" % "; ".join(bad) if bad else "CONTROL: GREEN -- the control did not go red")
else:
    for n, ok in res:
        print(("ok    " if ok else "FAIL  ") + n)
    print(("WALK OK %d/%d" % (len(res), len(res))) if not bad else "WALK FAILED %d/%d" % (len(res) - len(bad), len(res)))
