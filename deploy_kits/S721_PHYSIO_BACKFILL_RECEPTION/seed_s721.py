#!/usr/bin/env python3
"""seed_s721.py -- the data step of kit S721 (session 390, 06-Nov-2026). Idempotent: a second run changes nothing.
  unit_role  reception's three logins become makers of the physio register (unit physiobook): alisha, shivani and the shared
             'reception' login; the shared login also gets a 'physio' VIEWER row, because the finance front gate asks every
             /finance/physio/ page for a 'physio' row first (alisha and shivani already hold 'physio' maker).
             Added only where absent (note 'S721'); an inactive row of that exact kind is switched on (note 'S721 on; was: ...').
             NO other login, unit or role is touched.
  --undo     the rows this kit added are removed; rows it switched on are switched off again, as they were found.
    python3 -B seed_s721.py <finance.db> [--undo] [--dry]"""
import sqlite3
import sys

ROWS = (("physiobook", "alisha", "maker"), ("physiobook", "shivani", "maker"), ("physiobook", "reception", "maker"),
        ("physio", "reception", "viewer"))


def main(argv):
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 2
    db, undo, dry = argv[0], "--undo" in argv, "--dry" in argv
    con = sqlite3.connect(db, timeout=30)
    con.execute("PRAGMA busy_timeout = 30000")
    for unit in sorted(set(r[0] for r in ROWS)):
        if not con.execute("SELECT 1 FROM business_unit WHERE code=?", (unit,)).fetchone():
            print("SEED STOPPED: the unit %s is not on this database. Nothing written." % unit)
            return 1
    said = []
    for unit, user, role in ROWS:
        r = con.execute("SELECT id, active, note FROM unit_role WHERE unit=? AND lower(username)=? AND role=?", (unit, user, role)).fetchone()
        tag = "%s %s %s" % (unit, user, role)
        if undo:
            if r and (r[2] or "") == "S721":
                dry or con.execute("DELETE FROM unit_role WHERE id=?", (r[0],))
                said.append(tag + " removed")
            elif r and (r[2] or "").startswith("S721 on; was: "):
                dry or con.execute("UPDATE unit_role SET active=0, note=? WHERE id=?", (r[2][len("S721 on; was: "):] or None, r[0]))
                said.append(tag + " switched off again")
            continue
        if r and r[1] == 1:
            said.append(tag + " already")
            continue
        if not dry:
            if r:
                con.execute("UPDATE unit_role SET active=1, note=? WHERE id=?", ("S721 on; was: " + (r[2] or ""), r[0]))
            else:
                con.execute("INSERT INTO unit_role (unit, username, role, active, note) VALUES (?,?,?,1,'S721')", (unit, user, role))
        said.append(tag + (" switched on" if r else " added"))
    if dry:
        print("seed S721 DRY (nothing written): " + "; ".join(said or ["nothing of this kit's"]))
        return 0
    con.commit()
    if not undo:
        for unit, user, role in ROWS:
            got = con.execute("SELECT active FROM unit_role WHERE unit=? AND lower(username)=? AND role=?", (unit, user, role)).fetchone()
            if not got or got[0] != 1:
                print("SEED WRONG: %s %s %s did not read back" % (unit, user, role))
                return 1
    con.close()
    print("seed S721%s: %s" % (" undo" if undo else "", "; ".join(said or ["nothing of this kit's to undo"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
