#!/usr/bin/env python3
"""seed_s552.py -- the data step of kit S552_PHYSIO_REGISTER (session 313, 14-Oct-2026, D646). Idempotent: a second run changes nothing.
  tables    physio_patient, physio_course, physio_session, physio_payment + the one-live-entry-per-slip index -- the SCHEMA
            text read out of physio_book.py itself (one source; the module is not imported), CREATE ... IF NOT EXISTS
  settings  physio_book.on = 0 (switched off for Bhati), physio_book.clinic_rate_p = 25000, physio_book.home_rate_p = 50000
            -- INSERT OR IGNORE: a value already there is never changed
  unit      business_unit 'physiobook'; unit_role bhati maker, manoj checker, bhawna checker -- only where absent. No other login.
NEVER touches clinic_physio_day, any tile, or any other unit's rows.
    python3 -B seed_s552.py <finance.db> <physio_book.py>"""
import ast
import sqlite3
import sys

ROLES = (("bhati", "maker"), ("manoj", "checker"), ("bhawna", "checker"))
SETTINGS = (("physio_book.on", "0", "S552: 1 = Bhati's physio register open for him; 0 = only the doctors see it"),
            ("physio_book.clinic_rate_p", "25000", "S552: the clinic physiotherapy slip, in paise (Rs 250)"),
            ("physio_book.home_rate_p", "50000", "S552: one home visit, in paise (Rs 500)"))


def schema_of(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "SCHEMA" for t in n.targets):
            return n.value.value
    raise SystemExit("seed: no SCHEMA in %s" % path)


def seed(db, module):
    con = sqlite3.connect(db, timeout=30)
    con.execute("PRAGMA busy_timeout = 30000")
    con.execute("PRAGMA foreign_keys = ON")
    before = dict(t=con.execute("SELECT COUNT(*) FROM sqlite_master WHERE name LIKE 'physio\\_%' ESCAPE '\\' OR name='ux_physio_session_slip'").fetchone()[0],
                  r=con.execute("SELECT COUNT(*) FROM unit_role WHERE unit='physiobook'").fetchone()[0])
    con.executescript(schema_of(module))
    for k, v, note in SETTINGS:
        con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, note))
    cols = [r[1] for r in con.execute("PRAGMA table_info(business_unit)")]
    if "open_sunday" in cols and "active" in cols:
        con.execute("INSERT OR IGNORE INTO business_unit (code, name, open_sunday, active) VALUES ('physiobook','Physio register',1,1)")
    else:
        con.execute("INSERT OR IGNORE INTO business_unit (code, name) VALUES ('physiobook','Physio register')")
    added = 0
    for user, role in ROLES:
        if not con.execute("SELECT 1 FROM unit_role WHERE unit='physiobook' AND lower(username)=? AND role=?", (user, role)).fetchone():
            con.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active, note) VALUES ('physiobook',?,?,1,'S552')", (user, role))
            added += 1
    con.commit()
    got = sorted(tuple(r) for r in con.execute("SELECT username, role FROM unit_role WHERE unit='physiobook' AND active=1"))
    tabs = sorted(r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN "
                                           "('physio_patient','physio_course','physio_session','physio_payment')"))
    ux = con.execute("SELECT 1 FROM sqlite_master WHERE type='index' AND name='ux_physio_session_slip'").fetchone()
    on = con.execute("SELECT value FROM setting WHERE key='physio_book.on'").fetchone()
    con.close()
    if tabs != ["physio_course", "physio_patient", "physio_payment", "physio_session"] or not ux:
        print("SEED WRONG: tables %s, slip index %s" % (tabs, bool(ux)))
        return 1
    if got != sorted(ROLES):
        print("SEED WRONG: physiobook roles are %s" % got)
        return 1
    print("seed S552: 4 tables + the slip index (%s) · physiobook roles %s (%d added) · physio_book.on = %s" % (
        "already there" if before["t"] >= 5 else "made", ", ".join("%s %s" % x for x in got), added, on[0] if on else "?"))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(seed(sys.argv[1], sys.argv[2]))
