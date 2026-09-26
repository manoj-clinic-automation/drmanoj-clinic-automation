#!/usr/bin/env python3
"""seed_s403.py -- the 'porders' unit (S403, the owner 26-Sep-2026, D618): the Purchase orders screen.
INSERT only where absent; nothing existing is altered. bhati gets NO row here (his view is inside Medical sale check).
  business_unit  porders  'Purchase orders'
  unit_role      maker darpan · maker shavez · maker shivani · maker alisha · checker manoj
  setting        porders.senders / porders.viewers / porders.ortho_vendor (the who and the vendor, as data)
Usage: seed_s403.py DB_PATH
"""
import sqlite3
import sys

ROLES = [("darpan", "maker"), ("shavez", "maker"), ("shivani", "maker"), ("alisha", "maker"), ("manoj", "checker")]
SETTINGS = {"porders.senders": "manoj,darpan,shavez,shivani,alisha", "porders.viewers": "bhati", "porders.ortho_vendor": "YUVIKA SURGICALS"}


def seed(path):
    con = sqlite3.connect(path, timeout=30)
    cols = [r[1] for r in con.execute("PRAGMA table_info(business_unit)")]
    if "open_sunday" in cols and "active" in cols:
        con.execute("INSERT OR IGNORE INTO business_unit (code, name, open_sunday, active) VALUES ('porders','Purchase orders',1,1)")
    else:
        con.execute("INSERT OR IGNORE INTO business_unit (code, name) VALUES ('porders','Purchase orders')")
    for user, role in ROLES:
        if not con.execute("SELECT 1 FROM unit_role WHERE unit='porders' AND username=? AND role=?", (user, role)).fetchone():
            con.execute("INSERT INTO unit_role (unit, username, role, active, note) VALUES ('porders',?,?,1,'S403')", (user, role))
    con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    for k, v in SETTINGS.items():
        con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, "S403 D618 -- a data edit changes it"))
    con.commit()
    got = sorted(tuple(r) for r in con.execute("SELECT username, role FROM unit_role WHERE unit='porders' AND active=1"))
    bh = con.execute("SELECT COUNT(*) FROM unit_role WHERE unit='porders' AND lower(username)='bhati'").fetchone()[0]
    st = {r[0]: r[1] for r in con.execute("SELECT key, value FROM setting WHERE key LIKE 'porders.%'")}
    con.close()
    if got != sorted(ROLES):
        print("SEED WRONG: porders roles are %s" % got)
        return 1
    if bh:
        print("SEED WRONG: bhati holds a porders row -- the brief forbids it")
        return 1
    if not all(k in st for k in SETTINGS):
        print("SEED WRONG: settings missing: %s" % [k for k in SETTINGS if k not in st])
        return 1
    print("seed: porders unit + %d roles; settings senders=%s viewers=%s vendor=%s" % (len(ROLES), st["porders.senders"], st["porders.viewers"], st["porders.ortho_vendor"]))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(seed(sys.argv[1]))
