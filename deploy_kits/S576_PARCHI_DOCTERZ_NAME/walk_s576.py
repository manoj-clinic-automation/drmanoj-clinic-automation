#!/usr/bin/env python3
"""walk_s576.py -- the walk for kit S576_PARCHI_DOCTERZ_NAME. Takes patient() and its helpers out of a slip_log.py by
the parser (no Flask needed), runs them on a made-up database (made-up names only), prints one line per check.
    python3 walk_s576.py <slip_log.py>            the new file: every check green
    python3 walk_s576.py <slip_log.py> --old      the old file: the S576 checks must be red"""
import ast, sqlite3, sys

path, old = sys.argv[1], "--old" in sys.argv
tree = ast.parse(open(path, encoding="utf-8").read())
want = {"patient", "_s576_norm", "_docterz_newest_name"}
ns = {}
code = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in want]
exec(compile(ast.Module(body=code, type_ignores=[]), path, "exec"), ns)
patient = ns["patient"]

def db(with_lines=True):
    c = sqlite3.connect(":memory:"); c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT, name TEXT, phone_last4 TEXT, merged_into TEXT)")
    rows = [("9001", "Asha Kumari", "1111", None), ("9002", "RAVI  prasad", "2222", None), ("9003", "Only Master", "3333", None),
            ("9005", "Merged Away", "5555", "9003"), ("9005", "Kept Person", "5556", None)]
    c.executemany("INSERT INTO patient_ref (clinic_id,name,phone_last4,merged_into) VALUES (?,?,?,?)", rows)
    if with_lines:
        c.execute("CREATE TABLE clinic_day_line (business_date TEXT, section TEXT, clinic_id TEXT, patient TEXT)")
        c.executemany("INSERT INTO clinic_day_line VALUES (?,?,?,?)", [
            ("2026-07-11", "consult", "9001", "Asha Kumari"), ("2026-07-14", "revisit", "9001", "MEENA DEVI"),
            ("2026-09-12", "consult", "9001", "MEENA DEVI"), ("2026-08-01", "consult", "9002", "Ravi Prasad"),
            ("2026-08-02", "consult", "9004", "Day Line Only"), ("2026-08-03", "consult", "9001", "")])
    return c

R = []
def check(name, cond, s576=False):
    R.append((name, bool(cond), s576)); print(("GREEN " if cond else "RED   ") + ("[S576] " if s576 else "       ") + name)

c = db()
check("renamed in Docterz: the newest Docterz name, the master's last-4", patient(c, "9001") == ("MEENA DEVI", "1111"), True)
check("same name in another case/spacing: the master's name kept", patient(c, "9002") == ("RAVI  prasad", "2222"))
check("no Docterz line: the master's name", patient(c, "9003") == ("Only Master", "3333"))
check("not in the master: Docterz's own name (as before)", patient(c, "9004") == ("Day Line Only", ""))
check("a merged-away row is skipped (as before)", patient(c, "9005") == ("Kept Person", "5556"))
check("unknown ID: None (as before)", patient(c, "9999") is None)
check("empty ID: None (as before)", patient(c, "") is None)
c2 = db(with_lines=False)
check("no Docterz table on the box: the master's name, no error", patient(c2, "9001") == ("Asha Kumari", "1111"))
g = sum(1 for _, ok, _ in R if ok)
if old:
    red = [n for n, ok, s in R if s and not ok]
    keep = [n for n, ok, s in R if not s and not ok]
    print("\nwalk_s576 --old: %d S576 check(s) red as they must be; %d older check(s) red (must be 0)" % (len(red), len(keep)))
    sys.exit(0 if red and not keep else 1)
print("\nwalk_s576: %d of %d green" % (g, len(R)))
sys.exit(0 if g == len(R) else 1)
