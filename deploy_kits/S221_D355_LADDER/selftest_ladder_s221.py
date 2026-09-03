#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_ladder_s221.py -- the refusals.

The walk proves the ladder NAMES the right patient. This proves the harder
half: that it REFUSES when it should, which is the whole reason F-277 exists.
Every case here is built on a synthetic master in memory -- no live database,
no patient's real name, no real number.

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/selftest_ladder_s221.py
"""

import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

FAILED = []
PASSED = []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label,
                          ("   [%s]" % detail) if detail and not cond else ""))


def master():
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT,"
                " name TEXT, phone_last4 TEXT, mobile_fp TEXT, mobile TEXT,"
                " merged_into INTEGER)")
    con.execute("CREATE TABLE patient_visit (visit_id INTEGER PRIMARY KEY,"
                " visit_date TEXT, clinic_id TEXT, mobile_fp TEXT)")
    return con


def add(con, cid, name, last4="", fp=""):
    con.execute("INSERT INTO patient_ref (clinic_id, name, phone_last4, mobile_fp)"
                " VALUES (?,?,?,?)", (cid, name, last4, fp))


def main():
    os.environ["PATIENT_FP_SALT"] = "s221-selftest-salt"
    import finance_patient_match as M
    import finance_ingest as FI

    ck("the patched ingest is the one under test", "S221 F-283" in
       open(FI.__file__, encoding="utf-8").read())
    ck("the ladder is importable", callable(getattr(FI, "ladder_lookup", None)))

    # numbers are ASSEMBLED, never written as literals (F-185)
    n1 = "9" + "1" * 4 + "2" * 5
    n2 = "9" + "3" * 4 + "4" * 5
    fp1 = M.fingerprint(M.normalise_mobile(n1), M.salt())
    fp2 = M.fingerprint(M.normalise_mobile(n2), M.salt())

    con = master()
    add(con, "1001", "Ramesh Kumar Verma", "2222", fp1)
    add(con, "1002", "Sunita Verma", "2222", fp2)          # same family number? no: own fp
    add(con, "1003", "Anil Sharma", "5555")
    add(con, "1004", "Anita Sharma", "5555")               # last-four collision
    add(con, "1005", "Mohan Lal", "7777")
    con.commit()

    L = FI.ladder_lookup

    # ---- rung 2: the full mobile
    cid, nm, rung = L(con, dict(patient_name="Ramesh Kumar Verma", mobile=n1), None)
    ck("the full mobile names its owner", (cid, rung) == ("1001", "mobile"), str((cid, rung)))

    cid, nm, rung = L(con, dict(patient_name="Somebody Else Entirely", mobile=n1), None)
    ck("the number fits but the name does not -- NO ANSWER", cid is None, str((cid, rung)))

    cid, nm, rung = L(con, dict(patient_name="Ramesh Verma", mobile=n1), None)
    ck("a tolerant name still agrees (dropped middle name)",
       (cid, rung) == ("1001", "mobile"), str((cid, rung)))

    # ---- a family number: two people, one number
    con2 = master()
    add(con2, "2001", "Ram Prakash Gupta", "8888", fp1)
    add(con2, "2002", "Sita Gupta", "8888", fp1)
    con2.commit()
    cid, nm, rung = L(con2, dict(patient_name="Sita Gupta", mobile=n1), None)
    ck("a family number is separated by the GIVEN name",
       (cid, rung) == ("2002", "mobile"), str((cid, rung)))
    cid, nm, rung = L(con2, dict(patient_name="Gupta", mobile=n1), None)
    ck("a family number and only the surname -- NO ANSWER", cid is None, str((cid, rung)))

    # ---- no salt means no guess
    old = os.environ.pop("PATIENT_FP_SALT", None)
    import importlib
    importlib.reload(M)
    saved_file = M.SALT_FILE
    M.SALT_FILE = "/nonexistent/patient_fp.env"
    cid, nm, rung = L(con, dict(patient_name="Ramesh Kumar Verma", mobile=n1), None)
    ck("NO SALT means no fingerprint and NO GUESS from the mobile",
       rung != "mobile", str((cid, rung)))
    M.SALT_FILE = saved_file
    if old:
        os.environ["PATIENT_FP_SALT"] = old
    importlib.reload(M)

    # ---- rung 3: last-four + name
    cid, nm, rung = L(con, dict(patient_name="Mohan Lal", phone_last4="7777"), None)
    ck("last-four plus a name that fits one person names them",
       (cid, rung) == ("1005", "last-4 + name"), str((cid, rung)))

    cid, nm, rung = L(con, dict(patient_name="Sharma", phone_last4="5555"), None)
    ck("last-four shared by two, only a surname -- NO ANSWER", cid is None, str((cid, rung)))

    cid, nm, rung = L(con, dict(patient_name="Anita Sharma", phone_last4="5555"), None)
    ck("last-four shared by two, the given name separates them",
       (cid, rung) == ("1004", "last-4 + name"), str((cid, rung)))

    cid, nm, rung = L(con, dict(phone_last4="7777"), None)
    ck("a last-four with NO NAME is never enough on its own", cid is None, str((cid, rung)))

    cid, nm, rung = L(con, dict(patient_name="Mohan Lal"), None)
    ck("a name with nothing beside it is corroboration, never an identifier",
       cid is None, str((cid, rung)))

    # ---- rung 4: the same-day visit list
    con3 = master()
    add(con3, "3001", "Kamla Devi Yadav", "")
    add(con3, "3002", "Rakesh Yadav", "")
    add(con3, "3003", "Kamla Devi Singh", "")
    for cid_, d in (("3001", "2026-08-10"), ("3002", "2026-08-10"),
                    ("3001", "2026-08-11"), ("3003", "2026-08-11")):
        con3.execute("INSERT INTO patient_visit (visit_date, clinic_id) VALUES (?,?)", (d, cid_))
    con3.commit()

    cid, nm, rung = L(con3, dict(patient_name="Kamla Devi Yadav"), "2026-08-10")
    ck("the same-day list names the one patient who fits",
       (cid, rung) == ("3001", "same-day visit"), str((cid, rung)))

    cid, nm, rung = L(con3, dict(patient_name="Kamla Devi"), "2026-08-11")
    ck("two patients on that day fit the name -- NO ANSWER", cid is None, str((cid, rung)))

    cid, nm, rung = L(con3, dict(patient_name="Kamla Devi Yadav"), "2026-08-12")
    ck("a day with no visit feed (a Sunday) gives NO ANSWER", cid is None, str((cid, rung)))

    cid, nm, rung = L(con3, dict(patient_name="Kamla Devi Yadav"), None)
    ck("no business date, no visit rung", cid is None, str((cid, rung)))

    # ---- order: the mobile outranks the last-four, and the ID outranks both
    con4 = master()
    add(con4, "4001", "Vinod Kumar Jain", "9999", fp1)
    add(con4, "4002", "Vinod Kumar Jain", "9999", fp2)
    con4.commit()
    cid, nm, rung = L(con4, dict(patient_name="Vinod Kumar Jain",
                                 mobile=n2, phone_last4="9999"), None)
    ck("with two identical names the MOBILE decides, not the last-four",
       (cid, rung) == ("4002", "mobile"), str((cid, rung)))

    cid, nm, rung = L(con, dict(clinic_id="1003", patient_name="Anil Sharma"), None)
    ck("a clinic ID that agrees with the name is rung one",
       (cid, rung) == ("1003", "clinic id"), str((cid, rung)))
    cid, nm, rung = L(con, dict(clinic_id="1003", patient_name="Ramesh Kumar Verma"), None)
    ck("a clinic ID whose name DISAGREES does not name anybody on rung one",
       rung != "clinic id", str((cid, rung)))

    # ---- fail-soft
    broken = sqlite3.connect(":memory:")
    cid, nm, rung = L(broken, dict(patient_name="Anyone", phone_last4="1234"), "2026-08-10")
    ck("a database with no master at all fails soft: no answer, no exception",
       cid is None, str((cid, rung)))

    cid, nm, rung = L(con, dict(), None)
    ck("an empty line gives no answer", cid is None, str((cid, rung)))

    ck("the ladder wrote nothing to the master",
       con.execute("SELECT COUNT(*) FROM patient_ref").fetchone()[0] == 5)

    print("\n%s -- %d passed, %d failed" %
          ("ALL GREEN" if not FAILED else "RED", len(PASSED), len(FAILED)))
    for f in FAILED:
        print("   FAILED: %s" % f)
    return 0 if not FAILED else 1


if __name__ == "__main__":
    sys.exit(main())
