#!/usr/bin/env python3
"""walk_s725.py -- made-up finance databases only.  python walk_s725.py <retire20_s725.py> [--control]"""
import os, sqlite3, subprocess, sys, tempfile
tool = os.path.abspath(sys.argv[1]); control = "--control" in sys.argv
oks, fails = [], []
def ck(n, c):
    (oks if c else fails).append(n); print(("  ok   " if c else "  FAIL ") + n)
def mk(emp=None, person="Arjun", status="PORTAL_DISABLED", code_person="Arjun", retired=None, other=False):
    t = tempfile.mkdtemp(prefix="s725_"); db = os.path.join(t, "f.db"); c = sqlite3.connect(db)
    c.executescript("CREATE TABLE joiner (id INTEGER PRIMARY KEY, ref TEXT, kind TEXT, person TEXT, status TEXT, emp_code TEXT, updated_at TEXT);"
                    "CREATE TABLE emp_code (code INTEGER PRIMARY KEY, person TEXT, issued_on TEXT, retired_on TEXT, source TEXT, note TEXT);"
                    "CREATE TABLE joiner_event (id INTEGER PRIMARY KEY, joiner_id INT, at TEXT, actor TEXT, kind TEXT, detail TEXT);")
    c.execute("INSERT INTO joiner VALUES (3,'JOIN-2026-0002','JOIN','Arjun Dev','details',NULL,'x')")
    c.execute("INSERT INTO joiner VALUES (4,'EXIT-2026-0002','EXIT',?,?,?,'x')", (person, status, emp))
    if other: c.execute("INSERT INTO joiner VALUES (5,'EXIT-2026-0009','EXIT','Arjun','x','20','x')")
    c.execute("INSERT INTO emp_code VALUES (20,?,'2026-08-30',?,'seed',NULL)", (code_person, retired))
    c.execute("INSERT INTO emp_code VALUES (17,'Pravesh','2026-08-30','2026-08-31','seed',NULL)"); c.commit(); c.close(); return t, db
def run(db, *x):
    if control: return 0, ""
    p = subprocess.run([sys.executable, "-B", tool, db] + list(x), capture_output=True, text=True); return p.returncode, p.stdout
t, db = mk(); rc, out = run(db)
c = sqlite3.connect(db)
ck("rc 0 and written", rc == 0 and "written" in out)
ck("EXIT-2026-0002 carries Emp Code 20", c.execute("SELECT emp_code FROM joiner WHERE ref='EXIT-2026-0002'").fetchone() == ("20",))
ck("code 20 retired 2026-09-30", c.execute("SELECT retired_on FROM emp_code WHERE code=20").fetchone() == ("2026-09-30",))
ck("one event row", c.execute("SELECT COUNT(*) FROM joiner_event WHERE kind='EMP_CODE_RETIRED'").fetchone() == (1,))
ck("Arjun Dev's joining and code 17 untouched", c.execute("SELECT emp_code FROM joiner WHERE id=3").fetchone() == (None,) and c.execute("SELECT retired_on FROM emp_code WHERE code=17").fetchone() == ("2026-08-31",))
ck("a backup through the backup API", any("bak_S725_" in n for n in os.listdir(t)))
rc2, out2 = run(db); ck("a second run says ALREADY", rc2 == 0 and "ALREADY" in out2)
for name, kw in (("the record is someone else's", dict(person="Arjun Dev")), ("the record is complete", dict(status="COMPLETE")),
                 ("the record carries another code", dict(emp="21")), ("code 20 is someone else's", dict(code_person="Ranjeet")),
                 ("code 20 is on another record", dict(other=True))):
    t, db = mk(**kw); b = open(db, "rb").read(); rc, out = run(db)
    ck("STOP, nothing written: " + name, rc == 2 and "STOPPED" in out and open(db, "rb").read() == b and not any("bak_S725_" in n for n in os.listdir(t)))
t, db = mk(); b = open(db, "rb").read(); rc, out = run(db, "--dry"); ck("--dry writes nothing", rc == 0 and "DRY" in out and open(db, "rb").read() == b)
print(("WALK OK %d/%d" % (len(oks), len(oks) + len(fails))) if not fails else ("WALK RED %d of %d failed" % (len(fails), len(oks) + len(fails))))
sys.exit(1 if fails else 0)
