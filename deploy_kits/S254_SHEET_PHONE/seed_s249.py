#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_s249.py -- S249_CLINIC_MONEY: the physiotherapy unit, its roles, and the named checker.

WHY A UNIT AND NOT A ROLE.  finance_schema's unit_role has  CHECK (role IN ('maker','checker','viewer'))
and  unit REFERENCES business_unit(code).  A fourth role word is refused by the database (S214 met
this).  So "the physio role" is a NEW business_unit 'physio' with the three ordinary role words in
it, and the front gate (_unit_for_path, patched by this kit) resolves /finance/physio/... to that
unit.  Bhati gets a viewer row THERE and no row in 'clinic': every /finance/clinic/... address
refuses him before any route runs.  That is the owner's boundary, enforced by the server.

Rows written (INSERT OR IGNORE -- a second run changes nothing):
    business_unit  physio  'Physiotherapy'  merchant NULL  open_sunday 1
    unit_role      physio/bhati    viewer    the physiotherapist: reads the table, nothing else
                   physio/manoj    checker   the doctors tap "received"
                   physio/bhawna   checker
                   physio/shavez   maker     the desk sees the table too (reception writes it from the sheet)
                   physio/shivani  maker
                   physio/alisha   maker
    setting        clinic_money.checker = shavez   (the morning match's named checker; change it here, not in code)

It also REFUSES to leave a 'clinic' row for bhati in place: if one exists it is printed loudly and
deactivated, because the boundary is the whole point.

    /root/wa/venv/bin/python3 -B seed_s249.py /root/finance/finance.db
"""
import sqlite3
import sys

UNIT = "physio"
ROWS = (("bhati", "viewer", "S249 physiotherapist: the physiotherapy table and nothing else"),
        ("manoj", "checker", "S249 the doctor taps received"),
        ("bhawna", "checker", "S249 Dr Bhawna taps received"),
        ("shavez", "maker", "S249 the desk reads the physiotherapy table"),
        ("shivani", "maker", "S249 reception writes physiotherapy from the counter sheet"),
        ("alisha", "maker", "S249 reception writes physiotherapy from the counter sheet"))
CHECKER = ("clinic_money.checker", "shavez", "S249: the morning match's named checker (reception makes the first pass)")


def main(db):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    changed = []
    if con.execute("SELECT 1 FROM business_unit WHERE code=?", (UNIT,)).fetchone() is None:
        con.execute("INSERT INTO business_unit (code, name, merchant_id, open_sunday, active) VALUES (?,?,NULL,1,1)",
                    (UNIT, "Physiotherapy"))
        changed.append("business_unit physio")
    for user, role, note in ROWS:
        n = con.execute("SELECT COUNT(*) FROM unit_role WHERE unit=? AND lower(username)=? AND role=? AND active=1",
                        (UNIT, user, role)).fetchone()[0]
        if not n:
            con.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active, note) VALUES (?,?,?,1,?)",
                        (UNIT, user, role, note))
            con.execute("UPDATE unit_role SET active=1 WHERE unit=? AND lower(username)=? AND role=?", (UNIT, user, role))
            changed.append("unit_role %s/%s %s" % (UNIT, user, role))
    if con.execute("SELECT 1 FROM setting WHERE key=?", (CHECKER[0],)).fetchone() is None:
        con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?)", CHECKER)
        changed.append("setting %s=%s" % (CHECKER[0], CHECKER[1]))
    # the boundary: bhati must hold nothing in the clinic unit (nor medical, nor lab)
    stray = list(con.execute("SELECT id, unit, role FROM unit_role WHERE lower(username)='bhati' AND unit<>? AND active=1", (UNIT,)))
    for r in stray:
        con.execute("UPDATE unit_role SET active=0, note=COALESCE(note,'')||' [deactivated by S249: bhati is physio only]' WHERE id=?", (r["id"],))
        changed.append("DEACTIVATED stray row %s/bhati %s" % (r["unit"], r["role"]))
    con.commit()
    print("seed_s249: %s" % ("; ".join(changed) if changed else "NOT changed (already seeded)"))
    for u in ("clinic", "physio"):
        rows = con.execute("SELECT username, role FROM unit_role WHERE unit=? AND active=1 ORDER BY role, username", (u,)).fetchall()
        print("   %-7s %s" % (u, ", ".join("%s(%s)" % (r["username"], r["role"]) for r in rows)))
    print("   checker for the morning match: %s" % con.execute("SELECT value FROM setting WHERE key=?", (CHECKER[0],)).fetchone()[0])
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/root/finance/finance.db"))
