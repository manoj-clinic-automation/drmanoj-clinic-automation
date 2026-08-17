#!/bin/bash
# =============================================================================
#  install_s186.sh · kit S186_C1a — the Sanjeevni cash close.
#
#  CHANGES LIVE FINANCIAL BOOKS. Gated, backed up, verified, and reversible.
#
#  WHAT IT DOES
#    (A) removes the 13 Aug Rs 75,000 bank deposit that never happened (F-112)
#    (B) parks Rs 87,205 of pre-April cash-in-hand as ONE approved adjustment (D323)
#    (C) records the 17 Aug physical count in cash_count (evidence, not input)
#    (D) recomputes the negative_cash shouts from the corrected ledger
#
#  WHAT IT DOES NOT TOUCH
#    day_line — the sale money — is never written to, and the gate proves it.
#    Darpan's 17 Aug advances (10,000 + 20,000) are NOT here: they are ordinary
#    drawer expenses and belong in the app, through the maker-checker path.
#
#  SHAPE (D317)  preflight -> SUMS -> KIT_ID -> live-code currency gate ->
#  PRECHECK (refuses before writing) -> whole-db backup -> apply -> VERIFY ->
#  restore automatically on red. An honest red leaves the books exactly as found.
# =============================================================================
set -u

KIT_NAME="S186_C1a"
DB=/root/finance/finance.db
LIVE_APP=/root/finance/finance_app.py
APP_MD5_EXPECTED=c66bec2b9ea8c11af9c4a4244541e96f    # verified from the box, S186
PY=/usr/bin/python3
SNAP=/tmp/s186_before.json
export S186_SNAP="$SNAP"

for c in md5sum awk cp date; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — refusing"; exit 1; }
done
[ -x "$PY" ] || { echo "!! preflight: $PY not executable — refusing"; exit 1; }
[ -f "$DB" ] || { echo "!! preflight: $DB not found — refusing"; exit 1; }

KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; cd "$KIT_DIR" || exit 1

md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT_NAME" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum finance_migration_S186_cash_close.sql | awk '{print $1}')" ] \
&& echo "-- kit integrity + currency OK" \
&& echo "" \
&& echo "-- LIVE-CODE CURRENCY GATE (F-97)" \
&& LIVE_NOW="$(md5sum "$LIVE_APP" | awk '{print $1}')" \
&& { [ "$LIVE_NOW" = "$APP_MD5_EXPECTED" ] \
     || { echo "!! live finance_app.py is $LIVE_NOW, expected $APP_MD5_EXPECTED"; \
          echo "   Refusing. Correct the Register FROM the box first (D321(d))."; exit 1; }; } \
&& echo "   live app = c66bec2b9e... as verified at S186" \
&& echo "" \
&& echo "-- PRECHECK (read-only; nothing is written unless this is green)" \
&& "$PY" gate_s186.py "$DB" --precheck \
&& echo "-- backing up the whole database before touching it" \
&& BAK="${DB}.bak_${KIT_NAME}_$(date +%Y%m%d_%H%M%S)" \
&& cp -f "$DB" "$BAK" \
&& echo "   backup: $BAK" \
&& echo "" \
&& echo "-- applying the migration (one transaction)" \
&& "$PY" -c "import sqlite3;c=sqlite3.connect('$DB');c.execute('PRAGMA foreign_keys=ON');c.executescript(open('finance_migration_S186_cash_close.sql').read());c.commit();c.close()" \
&& echo "-- applied; verifying" \
&& { "$PY" gate_s186.py "$DB" --verify; VRC=$?; \
     if [ $VRC -ne 0 ]; then \
       echo ""; echo "!! VERIFY RED — RESTORING the backup. The books are exactly as found."; \
       cp -f "$BAK" "$DB"; \
       echo "   restored from $BAK"; \
       echo "   Send this whole output back. Nothing was left half-applied."; \
       exit 1; \
     fi; } \
&& echo "=============================================================" \
&& echo " $KIT_NAME INSTALLED — cash close applied and verified." \
&& echo "" \
&& echo " Cash in hand should now read Rs 2,05,198." \
&& echo " That figure INCLUDES the Rs 30,000 of 17 Aug advances, which are" \
&& echo " not yet entered. Once Darpan's two drawer expenses (10,000 +" \
&& echo " 20,000) go in through the app, it becomes Rs 1,75,198 — the cash" \
&& echo " physically counted today (Dr Bhawna 1,56,235 + you 18,963)." \
&& echo "" \
&& echo " Rollback if you ever want it: the block at the foot of the .sql," \
&& echo " or simply restore $BAK" \
&& echo "=============================================================" \
&& exit 0 \
|| { echo ""; \
     echo "RED — install did not complete."; \
     echo "   A gate fired BEFORE the database was written, or a step failed."; \
     echo "   If a backup was taken it is beside the database; the verify step"; \
     echo "   restores automatically, so the books are not half-changed."; \
     exit 1; }
