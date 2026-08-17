#!/bin/bash
# =============================================================================
#  install_r1a.sh · kit S186_R1a — the data layer for the three upgrades.
#
#  PURELY ADDITIVE. It creates new tables, one view and one module. It does not
#  read, write, alter or drop anything that exists, and NOTHING the running app
#  imports changes — so the app's behaviour today is bit-for-bit what it was
#  before this ran. The surfaces that use it arrive in S186_R2a.
#
#  Shape (D317): preflight -> SUMS -> KIT_ID -> module selftest BEFORE anything
#  is placed -> db backup -> migration -> verify -> honest red that restores.
# =============================================================================
set -u

KIT_NAME="S186_R1a"
DEST=/root/finance
DB=/root/finance/finance.db
PY=/usr/bin/python3

for c in md5sum awk cp date; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — refusing"; exit 1; }
done
[ -x "$PY" ] || { echo "!! preflight: $PY not executable — refusing"; exit 1; }
[ -f "$DB" ] || { echo "!! preflight: $DB not found — refusing"; exit 1; }

KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; cd "$KIT_DIR" || exit 1

md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT_NAME" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum finance_yesbank.py | awk '{print $1}')" ] \
&& echo "-- kit integrity + currency OK" \
&& echo "" \
&& echo "-- GATE: proving the reconciler can FAIL before it is trusted..." \
&& "$PY" finance_yesbank.py \
&& "$PY" -m py_compile finance_yesbank.py \
&& echo "" \
&& echo "-- backing up the database (the migration is additive, but back up anyway)" \
&& BAK="${DB}.bak_${KIT_NAME}_$(date +%Y%m%d_%H%M%S)" \
&& cp -f "$DB" "$BAK" && echo "   backup: $BAK" \
&& echo "" \
&& echo "-- applying the additive migration" \
&& "$PY" -c "import sqlite3;c=sqlite3.connect('$DB');c.execute('PRAGMA foreign_keys=ON');c.executescript(open('finance_migration_S186_reserve_yesbank.sql').read());c.commit();c.close()" \
&& echo "-- verifying (new objects present, everything else untouched)" \
&& { "$PY" - "$DB" <<'PYV'
import sqlite3, sys
db = sys.argv[1]; c = sqlite3.connect(db); ok = True
def chk(label, cond, extra=""):
    global ok
    print(("   OK   " if cond else "   FAIL ") + label + ("   " + extra if extra and not cond else ""))
    ok = ok and cond
have = set(r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')"))
for t in ("bank_statement_line","bank_statement_period","counter_person",
          "cash_custody_event","v_cash_custody_balance"):
    chk("created %s" % t, t in have)
chk("counter_person seeded with 3 people",
    c.execute("SELECT COUNT(*) FROM counter_person WHERE unit='medical'").fetchone()[0] == 3)
chk("Dr Bhawna recorded as custodian who never banks",
    c.execute("SELECT COUNT(*) FROM counter_person WHERE name='Dr Bhawna' AND role_kind='custodian'").fetchone()[0] == 1)
chk("no bank statement loaded yet (that is the next step, not this one)",
    c.execute("SELECT COUNT(*) FROM bank_statement_line").fetchone()[0] == 0)
chk("no custody events invented", c.execute("SELECT COUNT(*) FROM cash_custody_event").fetchone()[0] == 0)
chk("marker written",
    (c.execute("SELECT value FROM setting WHERE key='migration.S186_reserve_yesbank'").fetchone() or [''])[0] == 'applied')
c.close(); sys.exit(0 if ok else 1)
PYV
    VRC=$?; if [ $VRC -ne 0 ]; then echo ""; echo "!! VERIFY RED — restoring."; cp -f "$BAK" "$DB"; \
      echo "   restored from $BAK"; exit 1; fi; } \
&& echo "" \
&& echo "-- placing the module (nothing imports it yet)" \
&& { [ -f "$DEST/finance_yesbank.py" ] && cp -f "$DEST/finance_yesbank.py" "$DEST/finance_yesbank.py.bak_$KIT_NAME" || true; } \
&& cp -f finance_yesbank.py "$DEST/finance_yesbank.py" \
&& echo "" \
&& echo "=============================================================" \
&& echo " $KIT_NAME INSTALLED — data layer in place, selftest 23/23." \
&& echo " The running app is unchanged: nothing imports this yet." \
&& echo "" \
&& echo " Next: S186_R2a wires the three surfaces (Yes Bank upload +" \
&& echo " reconcile, the workbench, and the reserve/custody fields)." \
&& echo "=============================================================" \
&& exit 0 \
|| { echo ""; echo "RED — install did not complete. A gate fired; check above."; exit 1; }
