#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_kal_recipients_s243.py -- S243_DARPAN_KAL: name who receives Darpan's cash.

Two visible rows, no code:
  setting  darpan_kal.recipients = '<owner login>:dr_manoj,<Dr Bhawna login>:dr_bhawna'
  unit_role (medical, <Dr Bhawna login>, viewer)  -- so her login reaches /finance/darpan/kal;
           the page itself then shows her ONLY the days handed to her (darpan_kal._who).
           The owner already holds checker; no row is added for him.

The owner's own rule stands: Dr Bhawna gets no pharmacy checker role.  `viewer` is the
S221/S222 precedent (the corrections desk and the stock count accept a viewer; the Vaapsi
desk is gated further by returns.desk_users, which does not name her).

    /root/wa/venv/bin/python3 -B seed_kal_recipients_s243.py /root/finance/finance.db [owner_login] [bhawna_login]

Defaults are the real logins (owner, 13-Sep): owner `manoj`, Dr Bhawna `bhawna`.  The installer
runs this itself, so no step is left for the owner.  Re-runnable.  It never overwrites a recipients setting the owner has edited by hand:
if the row differs from the default it prints it and changes nothing.
"""
import sqlite3
import sys

KEY = "darpan_kal.recipients"
DEFAULT = "manoj:dr_manoj,bhawna:dr_bhawna"


def main(db, owner, bhawna):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    want = "%s:dr_manoj,%s:dr_bhawna" % (owner.lower(), bhawna.lower())
    r = con.execute("SELECT value FROM setting WHERE key=?", (KEY,)).fetchone()
    if r is not None and r["value"] not in ("", DEFAULT, want):
        print("recipients already set by hand -- NOT changed:  %s = %s" % (KEY, r["value"]))
    else:
        con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",
                    (KEY, want, "S243_DARPAN_KAL: login:party pairs; who may be handed the day's cash and see it"))
        print("set  %s = %s" % (KEY, want))
    have = con.execute("SELECT role FROM unit_role WHERE unit='medical' AND lower(username)=lower(?) AND active=1",
                       (bhawna,)).fetchall()
    if have:
        print("unit_role medical/%s already: %s -- NOT changed" % (bhawna, ", ".join(x["role"] for x in have)))
    else:
        con.execute("INSERT INTO unit_role (unit, username, role, note, active) VALUES ('medical',?,'viewer',?,1)",
                    (bhawna.lower(), "S243_DARPAN_KAL: receives Darpan's cash; sees only /finance/darpan/kal days handed to her"))
        print("added unit_role medical/%s = viewer" % bhawna.lower())
    con.commit()
    rows = con.execute("SELECT username, role FROM unit_role WHERE unit='medical' AND active=1 ORDER BY username").fetchall()
    print("medical unit roles now: %s" % ", ".join("%s(%s)" % (x["username"], x["role"]) for x in rows))
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or len(a) > 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(a[0], a[1] if len(a) > 1 else "manoj", a[2] if len(a) > 2 else "bhawna"))
