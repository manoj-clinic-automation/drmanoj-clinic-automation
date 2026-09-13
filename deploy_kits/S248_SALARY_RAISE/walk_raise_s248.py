#!/usr/bin/env python3
"""LIVE-SHAPE walk of S248_SALARY_RAISE.

Real CSV files on disk, the real script run as a subprocess the way the installer
runs it, and — because this money ends up in a salary sheet — the real
staff_ledger.py reading the file back afterwards to prove the new base is what the
salary engine now sees.

Run:  python3 walk_raise_s248.py [path/to/raise_salary_s248.py] [path/to/staff_ledger.py]
Exit 0 only if every check is ok.
"""
import csv
import io
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, "raise_salary_s248.py")
LEDGER = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else ""

OK = [0]
BAD = []


def check(name, cond, detail=""):
    if cond:
        OK[0] += 1
        print("  ok    %s" % name)
    else:
        BAD.append(name)
        print("  FAIL  %s %s" % (name, ("-- " + detail) if detail else ""))


TMP = tempfile.mkdtemp(prefix="s248_")

# The master written the way the real one is: more columns than we touch, a person
# with a comma in the name, a blank line's worth of oddity, and rows in an order
# that must be preserved exactly.
HEADER = ["user_id", "name", "active", "base_salary", "joined", "note"]
MASTER = [
    ["1", "Alisha", "Y", "10000", "2024-04-01", "reception"],
    ["2", "Amir Sohail", "Y", "2500", "2025-01-09", "part time, purchase"],
    ["3", "Arjun", "Y", "3200", "2026-02-11", ""],
    ["4", "Awdhesh", "Y", "10000", "2023-06-15", "OT, evening"],
    ["5", "Pravesh", "Y", "11000", "2022-08-01", ""],
    ["6", "Ranjeet", "Y", "10000", "2024-11-03", ""],
    ["7", "Sandip", "Y", "7400", "2025-03-20", "x-ray"],
    ["8", "Shavez", "Y", "15000", "2021-05-05", ""],
    ["9", "Shivani", "Y", "8600", "2023-09-12", ""],
    ["10", "Sukhveer", "Y", "16000", "2020-01-02", ""],
    ["11", "Surendra", "Y", "10500", "2019-07-07", ""],
    ["12", "Vikki", "Y", "7300", "2025-06-01", ""],
    ["13", "Darpan", "Y", "20000", "2018-04-01", "counter"],
    ["14", "Purana", "N", "5000", "2017-01-01", "left"],
]


def fresh(name="staff_master.csv"):
    p = os.path.join(TMP, name)
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        for r in MASTER:
            w.writerow(r)
    return p


def run(path, mode="--apply"):
    r = subprocess.run([sys.executable, SCRIPT, mode, path],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def rows_of(path):
    with io.open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def base(path, name):
    for r in rows_of(path):
        if r["name"] == name:
            return r["base_salary"]
    return None


def baks(path):
    d, b = os.path.dirname(path), os.path.basename(path)
    return sorted(x for x in os.listdir(d) if x.startswith(b + ".bak_S248"))


print("\n== S248 walk -- %s" % SCRIPT)

print("\n-- A. the dry run tells the truth and writes nothing")
# --------------------------------------------------------------------------
p = fresh("a.csv")
before = open(p, "rb").read()
rc, out = run(p, "--dry")
check("A1 the dry run succeeds", rc == 0, out)
check("A2 it names both raises, with both figures",
      "Awdhesh" in out and "10000" in out and "10500" in out
      and "Sandip" in out and "7400" in out and "8000" in out, out)
check("A3 it says it wrote nothing", "DRY RUN" in out)
check("A4 and the file is byte-identical", open(p, "rb").read() == before)
check("A5 no backup was taken for a dry run", not baks(p))

print("\n-- B. the raise itself")
# --------------------------------------------------------------------------
p = fresh("b.csv")
before_rows = rows_of(p)
rc, out = run(p)
check("B1 it applies", rc == 0 and "APPLIED" in out, out)
check("B2 Awdhesh is Rs 10500", base(p, "Awdhesh") == "10500", str(base(p, "Awdhesh")))
check("B3 Sandip is Rs 8000", base(p, "Sandip") == "8000", str(base(p, "Sandip")))
check("B4 it printed before and after", "before:" in out and "after:" in out)
check("B5 a backup was taken, and it still holds the old figures",
      len(baks(p)) == 1 and base(os.path.join(TMP, baks(p)[0]), "Awdhesh") == "10000")

after_rows = rows_of(p)
check("B6 every row is still there, in the same order",
      [r["name"] for r in after_rows] == [r["name"] for r in before_rows])
moved = [r["name"] for a, r in zip(before_rows, after_rows)
         if any(a[k] != r[k] for k in a)]
check("B7 EXACTLY two rows changed, and they are the two", moved == ["Awdhesh", "Sandip"],
      str(moved))
diff_cols = set()
for a, r in zip(before_rows, after_rows):
    for k in a:
        if a[k] != r[k]:
            diff_cols.add(k)
check("B8 and only the base_salary column moved", diff_cols == {"base_salary"}, str(diff_cols))
check("B9 the inactive person is untouched", base(p, "Purana") == "5000")
check("B10 a name with a space survives the rewrite",
      any(r["name"] == "Amir Sohail" and r["base_salary"] == "2500" for r in after_rows))
check("B11 every column of the header survives, in order",
      list(after_rows[0].keys()) == HEADER, str(list(after_rows[0].keys())))
check("B12 the notes column is not mangled",
      base(p, "Sandip") == "8000" and
      [r for r in after_rows if r["name"] == "Sandip"][0]["note"] == "x-ray")

print("\n-- C. a second run changes nothing")
# --------------------------------------------------------------------------
stable = open(p, "rb").read()
rc, out = run(p)
check("C1 it says ALREADY APPLIED", rc == 0 and "ALREADY APPLIED" in out, out)
check("C2 and the file is byte-identical", open(p, "rb").read() == stable)
check("C3 no second backup was taken", len(baks(p)) == 1)

print("\n-- D. what it refuses, writing nothing")
# --------------------------------------------------------------------------
p = fresh("d1.csv")
rr = rows_of(p)
with io.open(p, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=HEADER)
    w.writeheader()
    for r in rr:
        if r["name"] == "Sandip":
            r["base_salary"] = "7900"        # someone else moved it first
        w.writerow(r)
before = open(p, "rb").read()
rc, out = run(p)
check("D1 a figure that is not what the raise was worked out from is refused",
      rc != 0 and "not the Rs 7400" in out, out)
check("D2 and nothing at all is written -- not even Awdhesh's half",
      open(p, "rb").read() == before and not baks(p))

p = fresh("d2.csv")
rr = [r for r in rows_of(p) if r["name"] != "Awdhesh"]
with io.open(p, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=HEADER)
    w.writeheader()
    for r in rr:
        w.writerow(r)
before = open(p, "rb").read()
rc, out = run(p)
check("D3 a missing person is refused by name",
      rc != 0 and "Awdhesh is not in the staff master" in out, out)
check("D4 and nothing is written", open(p, "rb").read() == before and not baks(p))

p = fresh("d3.csv")
rr = rows_of(p)
with io.open(p, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=HEADER)
    w.writeheader()
    for r in rr:
        w.writerow(r)
        if r["name"] == "Sandip":
            w.writerow(dict(r, user_id="99"))     # the same person twice
before = open(p, "rb").read()
rc, out = run(p)
check("D5 a person listed twice is refused", rc != 0 and "appears 2 times" in out, out)
check("D6 and nothing is written", open(p, "rb").read() == before and not baks(p))

rc, out = run(os.path.join(TMP, "no_such_file.csv"))
check("D7 a missing file is refused", rc != 0 and "does not exist" in out)

p = os.path.join(TMP, "d4.csv")
with io.open(p, "w", encoding="utf-8", newline="") as f:
    f.write("user_id,name,active\n1,Awdhesh,Y\n")
rc, out = run(p)
check("D8 a master with no base_salary column is refused",
      rc != 0 and "no name/base_salary column" in out, out)

print("\n-- E. what the salary engine then reads")
# --------------------------------------------------------------------------
if LEDGER and os.path.exists(LEDGER):
    sys.path.insert(0, os.path.dirname(LEDGER))
    import staff_ledger as L                                     # noqa: E402
    p = fresh("e.csv")
    L.STAFF_CSV = p
    b0 = L.staff_bases()
    check("E1 the engine reads the old figures first",
          b0.get("Awdhesh") == 10000.0 and b0.get("Sandip") == 7400.0, str(b0))
    run(p)
    b1 = L.staff_bases()
    check("E2 after the raise the engine reads the new ones",
          b1.get("Awdhesh") == 10500.0 and b1.get("Sandip") == 8000.0, str(b1))
    check("E3 nobody else moved by a rupee",
          {k: v for k, v in b1.items() if k not in ("Awdhesh", "Sandip")}
          == {k: v for k, v in b0.items() if k not in ("Awdhesh", "Sandip")})
    check("E4 the inactive person is still out of the engine's list",
          "Purana" not in b1)
    check("E5 the advance ceiling follows the new base, as it should",
          L.advance_ceiling("Sandip") > L.advance_ceiling("Vikki"))
else:
    print("  (staff_ledger.py not given — section E skipped)")

shutil.rmtree(TMP, ignore_errors=True)
print("\n== %d checks, %d ok, %d failed" % (OK[0] + len(BAD), OK[0], len(BAD)))
if BAD:
    for b in BAD:
        print("   FAILED: %s" % b)
    sys.exit(1)
print("== WALK GREEN")
sys.exit(0)
