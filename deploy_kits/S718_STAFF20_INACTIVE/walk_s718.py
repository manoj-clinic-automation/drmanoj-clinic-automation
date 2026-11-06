#!/usr/bin/env python3
"""walk_s718.py -- kit S718. Made-up staff lists and registers only; no real path is read or written.
   python walk_s718.py <staff20_s718.py> [--control]
--control runs the state checks on a list the tool has NOT touched: it must go RED."""
import os, sqlite3, subprocess, sys, tempfile

tool = os.path.abspath(sys.argv[1])
control = "--control" in sys.argv
PY = sys.executable
HEAD = "user_id,name,department,base_salary,allowed_offs,wd_start,wd_end,sun_start,sun_end,active,minutes_exempt"
ROWS = ["7,Shavez,Pharmacy,15000,2,09:00,20:00,,,Y,N",
        "20,Arjun,Cleaner,3500,4,09:00,10:30,09:00,10:30,Y,Y",
        "21,Vikki,Reception,9000,2,09:00,20:00,,,Y,N"]
oks, fails = [], []


def ck(n, c):
    (oks if c else fails).append(n)
    print(("  ok   " if c else "  FAIL ") + n)


def mk(t, rows=ROWS, nl="\n", bom=False, locked=("2026-09", "2026-10"), reg_rows=()):
    m = os.path.join(t, "staff_master.csv")
    open(m, "wb").write((("﻿" if bom else "") + nl.join([HEAD] + list(rows)) + nl).encode())
    d = os.path.join(t, "sr")
    os.makedirs(d, exist_ok=True)
    c = sqlite3.connect(os.path.join(d, "staff_register.db"))
    c.executescript("CREATE TABLE locked_run (ym TEXT PRIMARY KEY, status TEXT);"
                    "CREATE TABLE staff (staff_id INTEGER PRIMARY KEY, name TEXT, join_date TEXT, last_working TEXT, active INTEGER);"
                    "CREATE TABLE audit_log (id INTEGER PRIMARY KEY, entity TEXT, entity_ref TEXT, action TEXT, old_value TEXT, "
                    "new_value TEXT, actor TEXT, ts TEXT, note TEXT);")
    for ym in ("2026-08", "2026-09", "2026-10"):
        c.execute("INSERT INTO locked_run VALUES (?,?)", (ym, "locked" if ym in locked or ym == "2026-08" else "draft"))
    c.executemany("INSERT INTO staff VALUES (?,?,?,?,?)", reg_rows)
    c.commit(); c.close()
    return m, d


def run(m, d, *extra):
    env = dict(os.environ); env.pop("SR_DB_PATH", None)
    p = subprocess.run([PY, "-B", tool, "--master", m, "--dir", d] + list(extra), capture_output=True, text=True, env=env, cwd=os.path.dirname(m))
    return p.returncode, p.stdout + p.stderr


def line20(m):
    t = open(m, "rb").read().decode("utf-8").lstrip("﻿")
    return [x for x in t.replace("\r\n", "\n").split("\n") if x.startswith("20,")]


for nl, bom, tag in (("\n", False, "LF"), ("\r\n", False, "CRLF"), ("\n", True, "BOM")):
    t = tempfile.mkdtemp(prefix="s718_")
    m, d = mk(t, nl=nl, bom=bom)
    before = open(m, "rb").read()
    if not control:
        rc, out = run(m, d)
    else:
        rc, out = 0, ""
    after = open(m, "rb").read()
    ck("%s: rc 0" % tag, rc == 0)
    ck("%s: number 20 Arjun base 3200, inactive" % tag, line20(m) == ["20,Arjun,Cleaner,3200,4,09:00,10:30,09:00,10:30,N,Y"])
    diff = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    ck("%s: only his two cells differ (same size, 3 bytes: 5->2, 0->0 none, Y->N)" % tag, len(before) == len(after) and 1 <= len(diff) <= 3)
    ck("%s: everyone else byte-identical" % tag,
       before.replace(b"20,Arjun,Cleaner,3500,4,09:00,10:30,09:00,10:30,Y,Y", b"") ==
       after.replace(b"20,Arjun,Cleaner,3200,4,09:00,10:30,09:00,10:30,N,Y", b""))
    ck("%s: a backup was kept" % tag, any(n.startswith("staff_master.csv.bak_S718_") for n in os.listdir(t)))
    if not control:
        rc2, out2 = run(m, d)
        ck("%s: a second run says ALREADY and writes nothing" % tag, rc2 == 0 and "ALREADY" in out2 and open(m, "rb").read() == after)

if not control:
    # the register row, when there is one
    t = tempfile.mkdtemp(prefix="s718r_")
    m, d = mk(t, reg_rows=[(5, "Arjun", "2026-01-01", None, 1), (6, "Arjun Dev", "2026-11-01", None, 1)])
    rc, out = run(m, d)
    c = sqlite3.connect(os.path.join(d, "staff_register.db"))
    ck("register: Arjun last working 2026-09-30, inactive", c.execute("SELECT last_working, active FROM staff WHERE staff_id=5").fetchone() == ("2026-09-30", 0))
    ck("register: Arjun Dev untouched", c.execute("SELECT last_working, active FROM staff WHERE staff_id=6").fetchone() == (None, 1))
    ck("register: one audit row", c.execute("SELECT COUNT(*) FROM audit_log WHERE action='exit_s718'").fetchone()[0] == 1)
    ck("register: a backup through the backup API", any(n.startswith("staff_register.db.bak_S718_") for n in os.listdir(d)))
    # every refusal writes nothing
    cases = [("October not locked", dict(locked=("2026-09",))),
             ("September not locked", dict(locked=("2026-10",))),
             ("number 20 is someone else", dict(rows=[ROWS[0], ROWS[1].replace("Arjun", "Arjun Dev"), ROWS[2]])),
             ("pay not 3500 or 3200", dict(rows=[ROWS[0], ROWS[1].replace("3500", "3000"), ROWS[2]])),
             ("number 20 twice", dict(rows=ROWS + [ROWS[1]])),
             ("a quoted line", dict(rows=[ROWS[0], ROWS[1].replace("Cleaner", '"Clean,er"'), ROWS[2]])),
             ("two register rows named Arjun", dict(reg_rows=[(5, "Arjun", "x", None, 1), (9, "arjun", "y", None, 1)])),
             ("a half-changed register row", dict(reg_rows=[(5, "Arjun", "x", "2026-09-30", 1)]))]
    for name, kw in cases:
        t = tempfile.mkdtemp(prefix="s718s_")
        m, d = mk(t, **kw)
        b = open(m, "rb").read()
        db = open(os.path.join(d, "staff_register.db"), "rb").read()
        rc, out = run(m, d)
        ck("STOP, nothing written: %s" % name, rc == 2 and "STOPPED" in out and open(m, "rb").read() == b
           and open(os.path.join(d, "staff_register.db"), "rb").read() == db and not [n for n in os.listdir(t) if "bak_S718" in n])
    t = tempfile.mkdtemp(prefix="s718d_")
    m, d = mk(t)
    b = open(m, "rb").read()
    rc, out = run(m, d, "--dry")
    ck("--dry: says what it would do, writes nothing", rc == 0 and "DRY" in out and "3500 -> 3200" in out and open(m, "rb").read() == b)
    t = tempfile.mkdtemp(prefix="s718e_")
    m, d = mk(t)
    rc, out = run(m, os.path.join(t, "nowhere"))
    ck("no register at all: STOP (cannot tell the locks)", rc == 2 and "STOPPED" in out)
print(("WALK OK %d/%d" % (len(oks), len(oks) + len(fails))) if not fails else ("WALK RED %d of %d failed" % (len(fails), len(oks) + len(fails))))
sys.exit(1 if fails else 0)
