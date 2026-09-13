#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_reports_role_s243.py -- S243_REPORTS_TILE: let the report generator's login through the gate.

/finance/reports/aaj is gated like Amir's page: ANY role on the medical unit (maker / checker /
viewer).  The portal's `shavez` login is role `manager` there, which the finance app does not map
to anything (SSO_ROLE_MAP is empty on purpose, S179); only a unit_role row admits him.  The S182
migrations gave him medical maker (the portal.py comment says so) -- if that row is there and
active, this script changes NOTHING.  If he holds no active medical role at all, ONE row is added:

    unit_role (medical, shavez, viewer)   -- the S214/S221/S222 precedent; a viewer reads, never writes

Idempotent: a second run prints "NOT changed".  Never removes or downgrades a role.

    /root/wa/venv/bin/python3 -B seed_reports_role_s243.py /root/finance/finance.db [login]

The installer runs this itself with the default login `shavez`.
"""
import sqlite3
import sys

DEFAULT_LOGIN = "shavez"
NOTE = "S243_REPORTS_TILE: the Marg report generator; reads /finance/reports/aaj"


def main(db, login):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    have = con.execute("SELECT role FROM unit_role WHERE unit='medical' AND lower(username)=lower(?) AND active=1",
                       (login,)).fetchall()
    if have:
        print("unit_role medical/%s already: %s -- NOT changed" % (login, ", ".join(x["role"] for x in have)))
    else:
        inactive = con.execute("SELECT id FROM unit_role WHERE unit='medical' AND lower(username)=lower(?) AND role='viewer'",
                               (login,)).fetchone()
        if inactive:
            con.execute("UPDATE unit_role SET active=1, note=? WHERE id=?", (NOTE, inactive["id"]))
            print("re-activated unit_role medical/%s = viewer" % login.lower())
        else:
            con.execute("INSERT INTO unit_role (unit, username, role, note, active) VALUES ('medical',?,'viewer',?,1)",
                        (login.lower(), NOTE))
            print("added unit_role medical/%s = viewer" % login.lower())
    con.commit()
    rows = con.execute("SELECT username, role FROM unit_role WHERE unit='medical' AND active=1 ORDER BY username").fetchall()
    print("medical unit roles now: %s" % ", ".join("%s(%s)" % (x["username"], x["role"]) for x in rows))
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or len(a) > 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(a[0], a[1] if len(a) > 1 else DEFAULT_LOGIN))
