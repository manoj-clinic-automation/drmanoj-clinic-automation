#!/bin/bash
# =============================================================================
#  install_c1a.sh · kit S189_C1a — the counted custody position, recorded.
#
#  WRITES TO THE LIVE DATABASE. Gated, backed up, verified, reversible.
#
#  WHAT IT DOES
#    Writes the physical cash position counted on 17 Aug 2026 into
#    cash_custody_event, where until now it has existed only as a sentence
#    inside cash_count.explanation. Four rows:
#        6 Aug   counter -> Dr Bhawna      7,309   (S186 s4, itemised)
#       15 Aug   counter -> Dr Bhawna      3,926   (S186 s4, itemised)
#       17 Aug   counter -> Dr Bhawna  1,45,000   (balance to the count)
#       17 Aug   drawer  -> Dr Manoj     18,963   (the drawer clearing)
#                                       ---------
#                                       1,75,198  = cash_count for that day
#
#  WHAT IT DOES NOT DO
#    It does not write cash_movement, and therefore CANNOT move cash in hand.
#    Custody is location; movement is quantity (F-137). The gate proves the
#    ledger, day_line, cash_movement, cash_adjustment and day_expense are all
#    byte-identical afterwards -- and RESTORES the whole database if any of
#    them moved by a single paisa.
#
#  ORDER: install S189_W1a FIRST. Until it is in, the card reads movements and
#  these rows would be invisible. This installer refuses if it is not.
#
#  SHAPE (D317)  preflight -> SUMS -> KIT_ID -> live-code currency gate ->
#  PRECHECK (refuses before writing) -> whole-db backup -> apply -> VERIFY ->
#  restore automatically on red. An honest red leaves the books exactly as found.
# =============================================================================
set -u

KIT_NAME="S189_C1a"
DB=/root/finance/finance.db
LIVE_APP=/root/finance/finance_app.py
APP_MD5_EXPECTED=583092c015c37d97fc240d09637b5ea7    # the S189_W1a build
PY=/usr/bin/python3
SNAP=/tmp/s189_before.json
export S189_SNAP="$SNAP"

for c in md5sum awk cp date; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — refusing"; exit 1; }
done
[ -x "$PY" ] || { echo "!! preflight: $PY not executable — refusing"; exit 1; }
[ -f "$DB" ] || { echo "!! preflight: $DB not found — refusing"; exit 1; }

KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; cd "$KIT_DIR" || exit 1

md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT_NAME" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum finance_migration_S189_custody.sql | awk '{print $1}')" ] \
&& echo "-- kit integrity + currency OK" \
&& echo "" \
&& echo "-- LIVE-CODE CURRENCY GATE (F-97)" \
&& LIVE_NOW="$(md5sum "$LIVE_APP" | awk '{print $1}')" \
&& { [ "$LIVE_NOW" = "$APP_MD5_EXPECTED" ] \
     || { echo "!! live finance_app.py is $LIVE_NOW, expected $APP_MD5_EXPECTED"; \
          echo "   That is the S189_W1a build. Install S189_W1a first --"; \
          echo "   without it the card still reads cash_movement and these rows"; \
          echo "   would be written and never seen. Refusing."; exit 1; }; } \
&& echo "   live app = 583092c015... (S189_W1a, reads custody)" \
&& echo "" \
&& echo "-- PRECHECK (read-only; nothing is written unless this is green)" \
&& "$PY" gate_s189.py "$DB" --precheck \
&& echo "" \
&& echo "-- backing up the whole database before touching it" \
&& BAK="${DB}.bak_${KIT_NAME}_$(date +%Y%m%d_%H%M%S)" \
&& cp -f "$DB" "$BAK" \
&& echo "   backup: $BAK" \
&& echo "" \
&& echo "-- applying the migration (one transaction)" \
&& "$PY" -c "import sqlite3;c=sqlite3.connect('$DB');c.execute('PRAGMA foreign_keys=ON');c.executescript(open('finance_migration_S189_custody.sql').read());c.commit();c.close()" \
&& echo "-- applied; verifying" \
&& { "$PY" gate_s189.py "$DB" --verify; VRC=$?; \
     if [ $VRC -ne 0 ]; then \
       echo ""; echo "!! VERIFY RED — RESTORING the backup. The books are exactly as found."; \
       cp -f "$BAK" "$DB"; \
       echo "   restored from $BAK"; \
       echo "   Send this whole output back. Nothing was left half-applied."; \
       exit 1; \
     fi; } \
&& echo "" \
&& echo "-- re-running the live smoke suite, because the store changed" \
&& { OUT="$(cd /root/finance && FINANCE_DB="$DB" "$PY" finance_app.py --selftest 2>&1)"; \
     echo "$OUT" | tail -4; \
     echo "$OUT" | grep -q '^SMOKE \([0-9]*\)/\1 passed' \
       || { echo "!! the suite is red after the migration — RESTORING."; \
            cp -f "$BAK" "$DB"; echo "   restored from $BAK"; exit 1; }; } \
&& echo "=============================================================" \
&& echo " $KIT_NAME INSTALLED — the counted position is now in the system." \
&& echo "" \
&& echo " Darpan's \"Where the cash is\" card will now read:" \
&& echo "     Dr Manoj    Rs    18,963" \
&& echo "     Dr Bhawna   Rs 1,56,235" \
&& echo "     total       Rs 1,75,198   as at the count of 17 Aug 2026" \
&& echo "" \
&& echo " Cash in hand is UNCHANGED at Rs 2,05,198. It was never overstated." \
&& echo " It becomes Rs 1,75,198 when Darpan's Rs 30,000 goes in through the" \
&& echo " app — and that is the same 1,75,198 you counted." \
&& echo "" \
&& echo " Rollback if you ever want it: the block at the foot of the .sql," \
&& echo " or simply restore \$BAK" \
&& echo "=============================================================" \
&& exit 0 \
|| { echo ""; \
     echo "RED — install did not complete."; \
     echo "   A gate fired BEFORE the database was written, or a step failed."; \
     echo "   If a backup was taken it is beside the database; the verify step"; \
     echo "   restores automatically, so the books are not half-changed."; \
     exit 1; }
