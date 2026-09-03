#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
close_amir_joiner_s222.py -- S222 star-1-2: close Amir's joiner record at 6/6.

THE OWNER'S INSTRUCTION at the S221 close: "tick CREDENTIALS_SENT + STAFF_MASTER so his
joiner record closes at 6/6."

IT REPORTS BY DEFAULT AND WRITES NOTHING. Pass --apply to write.

WHY IT IS NOT THREE UPDATE STATEMENTS

The joiner register exists to stop exactly one failure: a person marked fully added who is
invisible to attendance, because a step was signed off that was not true. Its own selftest
caught STAFF_MASTER being ticked while the Emp Code was still missing -- and that is the hole
the register was built to close. So this script never writes a step by hand:

  * it imports joiner_app and uses **its** blocked_by() / steps_for() / done_steps(), so
    ordering, LATE_OK and HARD_REQUIRES bind exactly as they do on the live page;
  * it writes the step, the event and the COMPLETE transition the same way api_step() does;
  * and it REFUSES to tick STAFF_MASTER unless Amir is ACTUALLY IN the staff master file.
    "staff master rebuilt and the person appears" is the step's own definition. A tick that
    only says somebody meant to do it is worth less than no tick at all.

THE ONE STEP NOBODY CAN VERIFY

`FIRST_LOGIN` -- "signed in once". Nothing in the portal records a last login, so no file on
this box can prove or disprove it. It is therefore an ATTESTATION, and this script will not
invent one. If it is the only step standing between the record and 6/6, the script says so and
stops. Re-run with --first-login-attested once the owner has said Amir has signed in (it is
recorded against his name, with the reason, so the register stays honest about what kind of
evidence each tick carries).

`CREDENTIALS_SENT` is also an attestation, but the owner made it explicitly at the S221 close
-- his words are the evidence and are written into the step's detail.

    /root/wa/venv/bin/python3 -B /root/finance/close_amir_joiner_s222.py
    /root/wa/venv/bin/python3 -B /root/finance/close_amir_joiner_s222.py --apply
"""

import datetime as dt
import io
import os
import sqlite3
import sys

DB = os.environ.get("FIN_DB", "/root/finance/finance.db")
FIN_DIR = os.environ.get("FIN_DIR", "/root/finance")
STAFF_MASTER = os.environ.get("ATT_STAFF_MASTER", "/root/staff_master.csv")
PERSON = os.environ.get("JOINER_PERSON", "amir")
BY = "Dr Manoj"

APPLY = "--apply" in sys.argv
FIRST_LOGIN_OK = "--first-login-attested" in sys.argv

DETAIL = {
    "CREDENTIALS_SENT": "S222 -- owner's attestation at the S221 close: the link, user id "
                        "and password were handed over. (F-295: the joiner page shows the "
                        "message but has no send button; this went by hand.)",
    "FIRST_LOGIN":      "S222 -- owner's attestation. Nothing on this box records a last "
                        "login, so this tick is his word, not a measurement.",
    "STAFF_MASTER":     "S222 -- VERIFIED by this script: the person was found in %s "
                        "before the tick was written." % STAFF_MASTER,
}


def staff_master_has(name, emp_code):
    """Is he actually there? Matched on the Emp Code first, then the name."""
    if not os.path.exists(STAFF_MASTER):
        return False, "staff_master.csv is not at %s" % STAFF_MASTER
    with io.open(STAFF_MASTER, encoding="utf-8", errors="replace") as fh:
        rows = [ln.rstrip("\n") for ln in fh if ln.strip()]
    low = name.strip().lower()
    for ln in rows[1:] if rows else []:
        cells = [c.strip().strip('"').lower() for c in ln.split(",")]
        if emp_code and str(emp_code).strip() in cells:
            return True, "matched on Emp Code %s" % emp_code
        if low and any(low == c or low in c.split() for c in cells):
            return True, "matched on the name '%s'" % name
    return False, ("%s is not in %s (%d data rows read). The staff master has not been "
                   "rebuilt since he was enrolled." % (name, STAFF_MASTER, max(0, len(rows) - 1)))


def main():
    if FIN_DIR not in sys.path:
        sys.path.insert(0, FIN_DIR)
    import joiner_app as JA

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    JA.ensure_schema(con)

    rows = con.execute(
        "SELECT id,ref,kind,person,role,status,username,emp_code FROM joiner "
        "WHERE kind='JOIN' AND lower(person) LIKE ?", ("%" + PERSON.lower() + "%",)).fetchall()
    if len(rows) != 1:
        print("REFUSED: found %d JOIN records matching '%s' (need exactly 1)." % (len(rows), PERSON))
        for r in rows:
            print("   %s  %s  status=%s" % (r["ref"], r["person"], r["status"]))
        return 2
    r = rows[0]
    jid, ref, kind = r["id"], r["ref"], r["kind"]
    order = JA.steps_for(kind)
    done = JA.done_steps(con, jid)

    print("record   %s   %s   role=%s   username=%s   emp_code=%s   status=%s"
          % (ref, r["person"], r["role"], r["username"], r["emp_code"], r["status"]))
    print("steps    %d/%d" % (len(done & set(order)), len(order)))
    for s in order:
        print("   [%s] %-18s %s" % ("x" if s in done else " ", s, JA.STEP_LABEL.get(s, "")))

    todo = [s for s in order if s not in done]
    if not todo:
        print("\nalready 6/6 -- nothing to do.")
        return 0

    # ---- the one measurable step, measured BEFORE anything is written --------
    sm_ok, sm_why = staff_master_has(r["person"], r["emp_code"])
    print("\nstaff master check: %s -- %s" % ("FOUND" if sm_ok else "NOT FOUND", sm_why))

    plan, refused = [], []
    for s in todo:
        ok, why = JA.blocked_by(kind, done | {p for p in plan}, s)
        if not ok:
            refused.append((s, why))
            continue
        if s == "FIRST_LOGIN" and not FIRST_LOGIN_OK:
            refused.append((s, "nothing on this box records a login. Re-run with "
                               "--first-login-attested once you confirm he has signed in."))
            continue
        if s == "STAFF_MASTER" and not sm_ok:
            refused.append((s, "he is not in the staff master yet -- %s" % sm_why))
            continue
        plan.append(s)

    print("\nwill tick : %s" % (", ".join(plan) if plan else "(nothing)"))
    for s, why in refused:
        print("will NOT  : %-18s %s" % (s, why))

    if not APPLY:
        print("\nREPORT ONLY -- nothing written. Re-run with --apply to write.")
        return 0
    if not plan:
        print("\nnothing to write.")
        return 1

    for s in plan:
        con.execute("INSERT INTO joiner_step (joiner_id,step,done_on,done_by,detail) "
                    "VALUES (?,?,?,?,?) ON CONFLICT(joiner_id,step) DO UPDATE SET "
                    "done_on=excluded.done_on, done_by=excluded.done_by, "
                    "detail=excluded.detail",
                    (jid, s, JA.today(), BY, DETAIL.get(s)))
        con.execute("UPDATE joiner SET status=?, updated_at=? WHERE id=?",
                    (s, JA.now_iso(), jid))
        con.execute("INSERT INTO joiner_event (joiner_id,at,actor,kind,detail) "
                    "VALUES (?,?,?,?,?)",
                    (jid, JA.now_iso(), "S222 close_amir_joiner", s, BY))
        print("ticked   %s" % s)

    done = JA.done_steps(con, jid) | set(plan)
    complete = all(s in done for s in order)
    if complete:
        con.execute("UPDATE joiner SET status='COMPLETE', closed_on=?, closed_by=? "
                    "WHERE id=?", (JA.today(), BY, jid))
        print("\nRECORD COMPLETE -- %s closed at %d/%d." % (ref, len(order), len(order)))
    else:
        left = [s for s in order if s not in done]
        print("\nnot complete. Still open: %s" % ", ".join(left))
    con.commit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
