#!/usr/bin/env python3
"""walk_s895.py -- the offline walk for kit S895 on a MADE-UP root (no live file, no patient data).
  python3 walk_s895.py <kit_dir> <control_ingest.py>
Checks: docterz_ingest server-first (box files first; Drive never overwrites a date the box owns; local legs first);
the CONTROL (the live ingest, before the kit) goes red on the same scene; push_followups_vps carries the
Do_Not_Call filter; followup_receiver marks the origin; server_runner's own selftest."""
import importlib.util, os, sqlite3, sys, tempfile, shutil, subprocess, datetime as dt

KIT = os.path.abspath(sys.argv[1]); CONTROL = os.path.abspath(sys.argv[2])
fails = []
def check(name, cond):
    print("  %s %s" % ("ok  " if cond else "FAIL", name))
    if not cond: fails.append(name)

def load(path, name, local_dir, nosheet):
    os.environ["DOCTERZ_LOCAL_OUTPUTS"] = local_dir
    os.environ["DOCTERZ_NOSHEET_FILE"] = nosheet
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def scene(m, root, drive):
    """stub Drive + the parser: a file's 'bytes' are its title; the parser maps a title to a business date"""
    m.list_day_files = lambda: list(drive)
    titles = {fid: title for (title, fid, _mt) in drive}
    m.fetch_bytes = lambda fid: ("DRIVE:" + titles[fid]).encode()
    m.find_tender_file = lambda: None
    def parse(raw):
        t = raw.decode()
        day = t.split("Staff_Action_Today_")[1][:10]
        bd = (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat()
        amt = 1000 if t.startswith("DRIVE:") else 2000
        return dict(business_date=bd, cons_count=1, cons_amount_p=amt, xray_count=0, xray_amount_p=0, proc_count=0, proc_amount_p=0,
                    total_count=1, total_amount_p=amt, morning=1, evening=0, free_revisits=0, free_concession=0, f93_phantom_rows=0,
                    tender={}, sheet_total_p=amt, sheet_cash_p=amt, sheet_online_p=0, variance_note="", lines=[])
    m.parse_bytes = parse
    m.upsert_lines = lambda con, d: None

def run_ingest(path, name, tag):
    root = tempfile.mkdtemp(prefix="walk895_" + tag + "_")
    local = os.path.join(root, "outputs"); os.makedirs(local)
    with open(os.path.join(local, "Staff_Action_Today_2026-11-21.xlsx"), "wb") as fh: fh.write(b"Staff_Action_Today_2026-11-21")
    with open(os.path.join(local, "Day_Tenders.csv"), "w") as fh: fh.write("business_date,clinic_id,invoice_no,tender,amount_p,source_file\n2026-11-20,X1,1,UPI,500,local\n")
    db = os.path.join(root, "f.db")
    m = load(path, name, local, os.path.join(root, "nosheet.json"))
    drive = [("Staff_Action_Today_2026-11-21.xlsx", "driveA", "2026-11-21T09:00:00.000Z"),   # same date as the box's, modified LATER
             ("Staff_Action_Today_2026-11-19.xlsx", "driveB", "2026-11-19T09:00:00.000Z")]
    scene(m, root, drive)
    saved = sys.argv; sys.argv = ["docterz_ingest.py", "--db", db]
    try:
        m.main()
    finally:
        sys.argv = saved
    con = sqlite3.connect(db); con.row_factory = sqlite3.Row
    rows = {r["business_date"]: (r["source_id"], r["total_amount_p"]) for r in con.execute("SELECT business_date, source_id, total_amount_p FROM %s" % m.TABLE)}
    legs = con.execute("SELECT COUNT(*) FROM clinic_day_tender").fetchone()[0] if con.execute("SELECT name FROM sqlite_master WHERE name='clinic_day_tender'").fetchone() else -1
    con.close(); shutil.rmtree(root, ignore_errors=True)
    return rows, legs

print("== docterz_ingest (the kit) on the made-up scene")
rows, legs = run_ingest(os.path.join(KIT, "docterz_ingest.py"), "ingest_kit", "kit")
check("the box's 20-Nov row is there, source local:", rows.get("2026-11-20", ("",))[0].startswith("local:"))
check("Drive's later copy of 20-Nov did NOT overwrite it (amount stays the box's)", rows.get("2026-11-20", ("", 0))[1] == 2000)
check("Drive's 18-Nov (a date the box never made) is taken", rows.get("2026-11-18", ("",))[0] == "driveB")
check("the box's Day_Tenders.csv is read first (1 leg)", legs == 1)
print("== CONTROL: the live ingest (before the kit) on the same scene -- must go red")
try:
    crows, clegs = run_ingest(CONTROL, "ingest_live", "ctl")
    check("CONTROL red: the live ingest never sees the box's file", "2026-11-20" not in crows or not str(crows["2026-11-20"][0]).startswith("local:"))
    check("CONTROL red: the live ingest reads no local legs", clegs <= 0)
except Exception as e:
    check("CONTROL ran (raised %s)" % type(e).__name__, False)
print("== push_followups_vps: the Do_Not_Call filter is back; the box's paths")
s = open(os.path.join(KIT, "push_followups_vps.py"), encoding="utf-8").read()
check("fetch_dnc_set present and used", s.count("fetch_dnc_set(") >= 2)
check("inbox + key dir from the box's env", 'FU_INBOX_DIR' in s and 'FU_KEY_DIR' in s)
check("no PC path left", "D:\\\\" not in s and "C:\\\\" not in s)
print("== followup_receiver: the origin mark")
s = open(os.path.join(KIT, "followup_receiver.py"), encoding="utf-8").read()
check("X-FU-Origin read, .last_pc_upload written when not the server", "X-FU-Origin" in s and ".last_pc_upload" in s and 'origin != "server"' in s)
print("== server_runner selftest")
r = subprocess.run([sys.executable, "-B", os.path.join(KIT, "server_runner.py"), "--selftest"], capture_output=True, text=True, timeout=120)
print("\n".join("     " + x for x in r.stdout.splitlines()[-14:]))
check("server_runner selftest 0 failures", r.returncode == 0 and "selftest: 0 failure(s)" in r.stdout)
print("WALK: %d failure(s) of %d checks" % (len(fails), 12))
sys.exit(1 if fails else 0)
