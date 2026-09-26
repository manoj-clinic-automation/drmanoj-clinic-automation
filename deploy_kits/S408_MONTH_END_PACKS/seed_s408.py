#!/usr/bin/env python3
"""seed_s408.py -- kit S408_MONTH_END_PACKS (D624). INSERT OR IGNORE only:
  business_unit  packs 'Month-end packs' · unit_role shavez maker, manoj checker
  setting        packs.accountant_to  (read from the filer script's ACCOUNTANT_EMAILS at install -- --gas <path>; never typed into code)
                 packs.electricity_words · packs.mail_limit_mb
  stmt_slot      the owner's list of accounts and cards (via packs.ensure); packs_item  the checklist's four groups
Usage: seed_s408.py DB_PATH [--gas /root/deploy/repo/deploy_kits/GAS_CURRENT/UPIReconciliation/Bank_Statement_Filer.gs]
"""
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROLES = [("shavez", "maker"), ("manoj", "checker")]


def accountants_from_gas(path):
    try:
        txt = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return []
    m = re.search(r"ACCOUNTANT_EMAILS\s*=\s*\[(.*?)\]", txt, re.S)
    if not m:
        return []
    return re.findall(r"'([^'@\s]+@[^'\s]+)'", m.group(1))


def seed(path, gas=None):
    for d in (HERE, os.environ.get("FINANCE_DIR", "/root/finance")):
        if os.path.isfile(os.path.join(d, "packs.py")) and d not in sys.path:
            sys.path.insert(0, d)
    import packs  # noqa: E402
    con = sqlite3.connect(path, timeout=30)
    con.row_factory = sqlite3.Row
    cols = [r[1] for r in con.execute("PRAGMA table_info(business_unit)")]
    if "open_sunday" in cols and "active" in cols:
        con.execute("INSERT OR IGNORE INTO business_unit (code, name, open_sunday, active) VALUES ('packs','Month-end packs',1,1)")
    else:
        con.execute("INSERT OR IGNORE INTO business_unit (code, name) VALUES ('packs','Month-end packs')")
    for user, role in ROLES:
        if not con.execute("SELECT 1 FROM unit_role WHERE unit='packs' AND username=? AND role=?", (user, role)).fetchone():
            con.execute("INSERT INTO unit_role (unit, username, role, active, note) VALUES ('packs',?,?,1,'S408')", (user, role))
    con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    for k, (v, note) in packs.SETTINGS.items():
        con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, note))
    if gas:
        emails = accountants_from_gas(gas)
        cur = con.execute("SELECT value FROM setting WHERE key='packs.accountant_to'").fetchone()
        if emails and not (cur and cur[0]):
            con.execute("UPDATE setting SET value=? WHERE key='packs.accountant_to'", (",".join(emails),))
    con.commit()
    packs.ensure(con)
    got = sorted(tuple(r) for r in con.execute("SELECT username, role FROM unit_role WHERE unit='packs' AND active=1"))
    to = con.execute("SELECT value FROM setting WHERE key='packs.accountant_to'").fetchone()[0]
    ns = con.execute("SELECT COUNT(*) FROM stmt_slot").fetchone()[0]
    ni = con.execute("SELECT COUNT(*) FROM packs_item").fetchone()[0]
    con.close()
    if got != sorted(ROLES):
        print("SEED WRONG: packs roles are %s" % got)
        return 1
    print("seed: packs unit + %d roles; accountants set: %s (%d address%s); slots %d; checklist items %d" % (len(ROLES), "yes" if to else "NO", len([x for x in to.split(",") if x.strip()]), "" if to.count(",") == 0 else "es", ns, ni))
    return 0


if __name__ == "__main__":
    if len(sys.argv) not in (2, 4):
        print(__doc__)
        sys.exit(2)
    sys.exit(seed(sys.argv[1], sys.argv[3] if len(sys.argv) == 4 and sys.argv[2] == "--gas" else None))
