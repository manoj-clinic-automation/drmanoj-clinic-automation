#!/bin/bash
# =============================================================================
#  install_s202.sh · kit S202_DARPAN20K — the Rs 20,000 that left the drawer
#                                          on 17-Aug and was never recorded.
#
#  WRITES TO THE LIVE DATABASE. Gated, backed up, verified, reversible.
#
#  ESTABLISHED BY PHYSICAL COUNT, not by argument (owner, 25-Aug-2026):
#      books say the drawer holds   63,903
#      the drawer physically holds  43,903
#      difference                   20,000  exactly, to the rupee
#
#  WHAT IT DOES        ONE INSERT into day_expense + one marker.
#  WHAT IT CANNOT DO   touch day_line (the money, D313), cash_movement,
#                      cash_adjustment, cash_count, cash_custody_event,
#                      sale_item, or the Staff Ledger. The gate proves each is
#                      unchanged and RESTORES the whole database on any red.
#
#  THE ONE THING THAT MAKES THIS SAFE
#      The new row is stamped ledger_posted=1 against SPECIAL 0cc0b26b38c5.
#      finance_app.py's approval path posts salary advances WHERE
#      ledger_posted=0 -- a row left at 0 would push a SECOND Rs 20,000 into
#      the Staff Ledger and Darpan would appear to owe 40,000. The gate fails
#      the install if that stamp is missing.
#
#  SHAPE (D317)  preflight -> SUMS -> live-code currency gate -> PRECHECK
#                -> whole-db backup -> apply -> VERIFY -> auto-restore on red.
# =============================================================================
set -u

KIT_NAME="S202_DARPAN20K"
DB=/root/finance/finance.db
LIVE_APP=/root/finance/finance_app.py
APP_MD5_EXPECTED=3f72e9ad16d915fe5ced45c4e28a2248     # the S201_UI build
PY=/usr/bin/python3
SNAP=/tmp/s202_before.json
export FINANCE_DB="$DB"
export S202_SNAP="$SNAP"

echo "=============================================================="
echo "  $KIT_NAME — recording the 17-Aug Rs 20,000 drawer advance"
echo "=============================================================="

for c in md5sum awk cp date sqlite3; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — refusing"; exit 1; }
done
[ -x "$PY" ] || { echo "!! preflight: $PY not executable — refusing"; exit 1; }
[ -f "$DB" ]  || { echo "!! preflight: $DB not found — refusing"; exit 1; }
echo "[1/7] preflight ok"

md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [2/7] kit SUMS mismatch — refusing"; exit 1; }
echo "[2/7] kit integrity ok"

ACTUAL="$(md5sum "$LIVE_APP" | awk '{print $1}')"
if [ "$ACTUAL" != "$APP_MD5_EXPECTED" ]; then
  echo "!! [3/7] LIVE CODE CURRENCY GATE — refusing."
  echo "   $LIVE_APP is $ACTUAL"
  echo "   this kit was built against  $APP_MD5_EXPECTED"
  echo "   The approval path's ledger_posted guard is what makes this safe."
  echo "   If the app has moved, that guard must be re-read before installing."
  exit 1
fi
echo "[3/7] live-code currency gate ok ($APP_MD5_EXPECTED)"

"$PY" gate_s202.py before || { echo "!! [4/7] precheck refused — nothing written"; exit 1; }
echo "[4/7] precheck ok — not already applied"

BAK="${DB}.bak_S202_DARPAN20K_$(date +%Y%m%d_%H%M%S)"
cp -f "$DB" "$BAK" || { echo "!! [5/7] backup failed — refusing"; exit 1; }
echo "[5/7] whole-database backup: $BAK"

if ! "$PY" -c "
import sqlite3
c=sqlite3.connect('$DB')
c.execute('PRAGMA foreign_keys=ON')
c.executescript(open('finance_migration_S202_darpan20k.sql').read())
c.commit(); c.close()
"; then
  echo "!! [6/7] apply FAILED — restoring"
  cp -f "$BAK" "$DB"; echo "   restored from $BAK"; exit 1
fi
echo "[6/7] applied"

echo "[7/7] verifying..."
if ! "$PY" gate_s202.py after; then
  echo "!! VERIFY RED — restoring the database untouched"
  cp -f "$BAK" "$DB"
  echo "   restored from $BAK — the books are exactly as they were found"
  exit 1
fi

OUT="$(cd /root/finance && FINANCE_DB="$DB" "$PY" finance_app.py --selftest 2>&1)"
if ! echo "$OUT" | grep -qiE "([0-9]+)/\1|all .*pass|OK"; then
  echo "!! app selftest did not report clean — restoring"
  echo "$OUT" | tail -20
  cp -f "$BAK" "$DB"; echo "   restored from $BAK"; exit 1
fi
echo "$OUT" | tail -3

echo
echo "=============================================================="
echo "  GREEN. The drawer should now read Rs 43,903 — the figure you"
echo "  counted. Darpan's ledger is UNCHANGED at Rs 20,000 owing."
echo
echo "  Check both:  https://followup.dr-manoj.in/finance/approvals"
echo "               https://followup.dr-manoj.in/ledger/statement?staff=Darpan"
echo
echo "  To reverse:  sqlite3 $DB \\"
echo "     \"DELETE FROM day_expense WHERE expense_uid='exS202darpan20k17aug';\""
echo "     \"DELETE FROM setting WHERE key='migration.S202_darpan20k';\""
echo "  or simply restore $BAK"
echo "=============================================================="
