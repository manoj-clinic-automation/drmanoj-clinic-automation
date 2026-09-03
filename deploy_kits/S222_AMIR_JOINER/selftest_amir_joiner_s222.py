#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest_amir_joiner_s222.py -- the four paths that matter, offline.

It builds a joiner register from the REAL joiner_schema.sql, seeds a record in the shape
Amir's is in (DECIDED, ACCOUNT_CREATED and a LATE_OK BIOMETRIC with Emp Code 101), and runs
the REAL close script against it -- as a subprocess, exactly as the box will run it.

    python -B selftest_amir_joiner_s222.py [path-to-S208_STAFF]
"""
import datetime as dt
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
STAFF = os.path.abspath(sys.argv[1] if len(sys.argv) > 1
                        else os.path.join(HERE, "..", "S208_STAFF"))
SCRIPT = os.path.join(HERE, "close_amir_joiner_s222.py")
FAILS, N = [], 0


def ck(label, cond, detail=""):
    global N
    N += 1
    if cond:
        print("  PASS  %s" % label)
    else:
        print("  FAIL  %s   [%s]" % (label, detail))
        FAILS.append(label)


def main():
    for f in ("joiner_app.py", "joiner_schema.sql"):
        if not os.path.exists(os.path.join(STAFF, f)):
            raise SystemExit("need %s in %s" % (f, STAFF))
    tmp = tempfile.mkdtemp(prefix="s222_joiner_")
    fin = os.path.join(tmp, "fin")
    os.makedirs(fin)
    for f in ("joiner_app.py", "joiner_schema.sql"):
        shutil.copyfile(os.path.join(STAFF, f), os.path.join(fin, f))
    db = os.path.join(fin, "finance.db")
    sm = os.path.join(tmp, "staff_master.csv")

    con = sqlite3.connect(db)
    con.executescript(open(os.path.join(fin, "joiner_schema.sql"), encoding="utf-8").read())
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    today = dt.date.today().isoformat()
    con.execute("INSERT INTO joiner (ref,kind,person,role,status,username,employment,"
                "authorities,emp_code,opened_on,opened_by,created_at,updated_at) VALUES "
                "('JOIN-2026-0007','JOIN','Amir','purchase','BIOMETRIC','amir','BIWEEKLY',"
                "'self','101',?,'Dr Manoj',?,?)", (today, now, now))
    jid = con.execute("SELECT id FROM joiner WHERE ref='JOIN-2026-0007'").fetchone()[0]
    for s in ("DECIDED", "ACCOUNT_CREATED", "BIOMETRIC"):
        con.execute("INSERT INTO joiner_step (joiner_id,step,done_on,done_by) "
                    "VALUES (?,?,?,'Dr Manoj')", (jid, s, today))
    con.commit()
    con.close()

    env = dict(os.environ, FIN_DB=db, FIN_DIR=fin, ATT_STAFF_MASTER=sm)

    def run(*args):
        p = subprocess.run([sys.executable, "-B", SCRIPT] + list(args), env=env,
                           capture_output=True, text=True)
        return p.stdout + p.stderr

    def steps_done():
        c = sqlite3.connect(db)
        n = c.execute("SELECT COUNT(*) FROM joiner_step WHERE done_on IS NOT NULL").fetchone()[0]
        st = c.execute("SELECT status FROM joiner").fetchone()[0]
        c.close()
        return n, st

    open(sm, "w", encoding="utf-8").write("emp_code,name,sunday_group\n7,Darpan,A\n")

    print("-- 1  REPORT ONLY writes nothing -------------------------------")
    o = run()
    ck("it reports 3/6", "steps    3/6" in o)
    ck("it says REPORT ONLY", "REPORT ONLY" in o)
    ck("FIRST_LOGIN is refused without the attestation", "will NOT  : FIRST_LOGIN" in o)
    ck("nothing was written", steps_done() == (3, "BIOMETRIC"), str(steps_done()))

    print("\n-- 2  --apply ticks only what is honest -------------------------")
    o = run("--apply")
    ck("CREDENTIALS_SENT is ticked (the owner's own attestation)", "ticked   CREDENTIALS_SENT" in o)
    ck("STAFF_MASTER is NOT ticked", "ticked   STAFF_MASTER" not in o)
    ck("the record is not closed", "not complete" in o)
    ck("exactly one step was written", steps_done()[0] == 4, str(steps_done()))

    print("\n-- 3  STAFF_MASTER refuses while he is not in the file ----------")
    o = run("--apply", "--first-login-attested")
    ck("the staff master check says NOT FOUND", "staff master check: NOT FOUND" in o)
    ck("FIRST_LOGIN ticks once attested", "ticked   FIRST_LOGIN" in o)
    ck("STAFF_MASTER still refused", "will NOT  : STAFF_MASTER" in o)
    ck("still not 6/6", steps_done() == (5, "FIRST_LOGIN"), str(steps_done()))

    print("\n-- 4  rebuild the staff master, and it closes -------------------")
    open(sm, "w", encoding="utf-8").write(
        "emp_code,name,sunday_group\n7,Darpan,A\n101,Amir,B\n")
    o = run("--apply", "--first-login-attested")
    ck("the staff master check says FOUND", "staff master check: FOUND" in o)
    ck("STAFF_MASTER ticks", "ticked   STAFF_MASTER" in o)
    ck("the record closes at 6/6", "RECORD COMPLETE" in o)
    ck("the register says COMPLETE", steps_done() == (6, "COMPLETE"), str(steps_done()))

    print("\n-- 5  re-running changes nothing --------------------------------")
    o = run("--apply", "--first-login-attested")
    ck("it says already 6/6", "already 6/6" in o)
    ck("still 6/6 and COMPLETE", steps_done() == (6, "COMPLETE"), str(steps_done()))

    print("\n-- 6  every tick carries the kind of evidence behind it ---------")
    c = sqlite3.connect(db)
    d = dict(c.execute("SELECT step, coalesce(detail,'') FROM joiner_step").fetchall())
    c.close()
    ck("CREDENTIALS_SENT is marked an attestation", "attestation" in d["CREDENTIALS_SENT"])
    ck("FIRST_LOGIN says plainly it is not a measurement",
       "not a measurement" in d["FIRST_LOGIN"])
    ck("STAFF_MASTER says it was VERIFIED", "VERIFIED" in d["STAFF_MASTER"])

    shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s  %d checks, %d failed"
          % ("SELFTEST GREEN" if not FAILS else "SELFTEST RED", N, len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
