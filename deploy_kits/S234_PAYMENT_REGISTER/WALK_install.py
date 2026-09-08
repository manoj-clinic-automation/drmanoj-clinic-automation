#!/usr/bin/env python3
"""WALK_install.py — S234_PAYMENT_REGISTER

Drives install.sh in a sandbox with fake roots and proves BOTH that it works
and that each refusal actually refuses. Runs offline, touches no live path,
never writes a crontab (CRON_ON=0 throughout).

The reason this exists: at S208 two defects sat behind 65 green checks, and at
S209 a page that killed a whole console sat behind four green gates. A kit is
proven by walking it, not by asserting it.
"""
import csv
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "payments_register.py")
INSTALL = os.path.join(HERE, "install.sh")
HDR = ["Date", "Vendor", "Description", "Amount (Rs)",
       "Attachment in Drive", "Gmail Link"]
ROWS = [["19-07-2026", "Hostinger", "Renewal", "3560", "No", "https://m/1"],
        ["20-07-2026", "ICICI", "Card bill", "", "Yes", "https://m/2"],
        ["21-07-2026", "Tata Power", "Electricity", "1,240.50", "Yes",
         "https://m/3"]]

fails = []
n = [0]


def check(name, cond):
    n[0] += 1
    if not cond:
        fails.append(name)
        print("  FAIL  %s" % name)


def make_book(sheets, rows):
    d = os.path.join(sheets, "payment_register")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "Sheet1.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(HDR)
        w.writerows(rows)
    with open(os.path.join(d, "_BOOK.json"), "w", encoding="utf-8") as fh:
        json.dump({"title": "Payment Register",
                   "pulled_at_ist": time.strftime("%Y-%m-%d %H:%M:%S IST"),
                   "tabs": [{"tab": "Sheet1", "file": "Sheet1.csv"}]}, fh)
    return d


def sandbox(rows=None, with_kit=True, with_book=True):
    root = tempfile.mkdtemp(prefix="s234walk_")
    fin = os.path.join(root, "finance")
    sheets = os.path.join(root, "sheets")
    kit = os.path.join(root, "kit")
    os.makedirs(fin)
    os.makedirs(sheets)
    os.makedirs(kit)
    if with_kit:
        shutil.copy(SCRIPT, os.path.join(kit, "payments_register.py"))
    if with_book:
        make_book(sheets, ROWS if rows is None else rows)
    return root, fin, sheets, kit


def run(fin, sheets, kit):
    env = dict(os.environ)
    env.update({"FIN_ROOT": fin, "SHEETS_ROOT": sheets, "KIT_DIR": kit,
                "PY": sys.executable, "CRON_ON": "0",
                "LOG": os.path.join(fin, "p.log")})
    p = subprocess.run(["bash", INSTALL], env=env, capture_output=True,
                       text=True)
    return p.returncode, p.stdout + p.stderr


def rows_in(fin):
    db = os.path.join(fin, "finance.db")
    if not os.path.exists(db):
        return None
    con = sqlite3.connect(db)
    try:
        return con.execute("SELECT COUNT(*) FROM payment_register").fetchone()[0]
    except sqlite3.Error:
        return None
    finally:
        con.close()


def main():
    print("WALK_install — S234_PAYMENT_REGISTER")

    # 1 · the ordinary install
    root, fin, sheets, kit = sandbox()
    rc, out = run(fin, sheets, kit)
    check("install: a clean box installs and exits 0", rc == 0)
    check("install: the script is in place", os.path.exists(
        os.path.join(fin, "payments_register.py")))
    check("install: the table holds the sheet's rows", rows_in(fin) == 3)
    check("install: it says DONE and asks for three lines back",
          "DONE" in out and "md5:" in out)
    check("install: it prints the undo lines", "To undo everything" in out)

    # 2 · running it a second time is safe
    rc2, out2 = run(fin, sheets, kit)
    check("install: a SECOND run is safe and exits 0", rc2 == 0)
    check("install: the second run kept a dated copy of the first",
          any(f.startswith("payments_register.py.bak_")
              for f in os.listdir(fin)))
    check("install: the second run did not duplicate rows", rows_in(fin) == 3)
    shutil.rmtree(root)

    # 3 · a sheet the pull has never produced
    root, fin, sheets, kit = sandbox(with_book=False)
    rc, out = run(fin, sheets, kit)
    check("refusal: no pulled book -> stops, non-zero", rc != 0)
    check("refusal: no pulled book -> the script is NOT installed",
          not os.path.exists(os.path.join(fin, "payments_register.py")))
    check("refusal: it names sheets_pull.py as the thing to run",
          "sheets_pull.py" in out)
    shutil.rmtree(root)

    # 4 · the kit itself missing (the deploy clone was not pulled)
    root, fin, sheets, kit = sandbox(with_kit=False)
    rc, out = run(fin, sheets, kit)
    check("refusal: no kit in the clone -> stops, non-zero", rc != 0)
    check("refusal: and it says to run the first line again",
          "deploy clone" in out)
    shutil.rmtree(root)

    # 5 · a script whose selftest fails must never be installed
    root, fin, sheets, kit = sandbox()
    # A stand-in whose selftest reports a failure. It replaces the kit's copy
    # only inside this sandbox; the real file is never edited.
    with open(os.path.join(kit, "payments_register.py"), "w",
              encoding="utf-8") as fh:
        fh.write("import sys\n"
                 "print('selftest: 3 checks, 1 failures')\n"
                 "sys.exit(1)\n")
    rc, out = run(fin, sheets, kit)
    check("refusal: a failing selftest stops the install", rc != 0)
    check("refusal: and nothing was copied into the finance directory",
          not os.path.exists(os.path.join(fin, "payments_register.py")))
    shutil.rmtree(root)

    # 6 · a header that changed in Google
    root, fin, sheets, kit = sandbox()
    d = os.path.join(sheets, "payment_register")
    with open(os.path.join(d, "Sheet1.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(HDR + ["Notes"])
        w.writerows([r + ["x"] for r in ROWS])
    rc, out = run(fin, sheets, kit)
    check("refusal: a changed sheet header stops the install", rc != 0)
    check("refusal: and the real database was never created",
          rows_in(fin) is None)
    shutil.rmtree(root)

    # 7 · a shrink after a good install refuses and keeps the table
    root, fin, sheets, kit = sandbox()
    rc, _ = run(fin, sheets, kit)
    check("shrink: the first install is good", rc == 0 and rows_in(fin) == 3)
    make_book(sheets, ROWS[:1])
    rc, out = run(fin, sheets, kit)
    check("shrink: a shorter sheet stops the install", rc != 0)
    check("shrink: and the table still holds all three rows",
          rows_in(fin) == 3)
    check("shrink: and it says how to proceed on purpose",
          "--allow-shrink" in out)
    shutil.rmtree(root)

    # 8 · the promise that matters most: no existing table is touched
    root, fin, sheets, kit = sandbox()
    db = os.path.join(fin, "finance.db")
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE cash_book (id INTEGER PRIMARY KEY, amt INTEGER)")
    con.execute("INSERT INTO cash_book VALUES (1, 987654)")
    con.commit()
    con.close()
    rc, out = run(fin, sheets, kit)
    con = sqlite3.connect(db)
    got = con.execute("SELECT amt FROM cash_book WHERE id=1").fetchone()[0]
    tables = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
    con.close()
    check("safety: the install exits 0 beside an existing books table", rc == 0)
    check("safety: THE EXISTING TABLE IS UNTOUCHED, row and value",
          got == 987654)
    check("safety: everything it created is named payment_register*",
          {t for t in tables if not t.startswith("payment_register")
           and not t.startswith("sqlite_")} == {"cash_book"})
    shutil.rmtree(root)

    print("")
    print("WALK_install: %d checks, %d failures" % (n[0], len(fails)))
    for f in fails:
        print("  FAILED: %s" % f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
