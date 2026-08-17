#!/bin/bash
# =============================================================================
#  install_c1a.sh · kit S184_C1a — correct the Sanjeevni (medical) cash books
#
#  Applies finance_migration_S184_cash_correction.sql:
#    31 sheet deposits -> 16 Yes Bank verified · 36 legacy adjustments removed
#    (backed up) · Rs 40,000 advances as drawer expenses (NOT Ledger) · Rs 337
#    procedure-medicine noncash. day_line (the sale money) is never touched.
#
#  Shape per D317: preflight -> SUMS -> KIT_ID -> STATE gate (refuse unless the
#  box is at the exact -30,056 we built against and the marker is absent) ->
#  backup finance.db -> apply in one transaction -> post-verify -> honest red
#  that RESTORES the backup. Nothing is left half-applied.
# =============================================================================
set -u

KIT_NAME="S184_C1a"
FIN=/root/finance
PY=/usr/bin/python3
DB="$FIN/finance.db"

for c in md5sum awk cp; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — refusing"; exit 1; }
done
[ -x "$PY" ] || { echo "!! preflight: $PY not executable — refusing"; exit 1; }
[ -f "$DB" ] || { echo "!! preflight: $DB not found — refusing"; exit 1; }

KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; cd "$KIT_DIR" || exit 1
export FINANCE_DB="$DB"

md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT_NAME" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum finance_migration_S184_cash_correction.sql | awk '{print $1}')" ] \
&& echo "-- integrity + kit identity OK" \
&& "$PY" -m py_compile gate_c1a.py \
&& echo "-- STATE gate (read-only): is the box exactly the -30,056 we built against?" \
&& GATE="$("$PY" gate_c1a.py before)" \
&& { [ "$GATE" = "OK" ] || { echo "!! REFUSING — gate says: $GATE"; echo "   Nothing touched. The box is not the state this kit corrects."; exit 1; }; } \
&& echo "-- state OK: closing is -30,056, cash total matches, correction not run before" \
&& STAMP="$(date +%Y%m%d_%H%M%S)" \
&& cp -p "$DB" "$DB.bak_S184C1_$STAMP" \
&& echo "-- finance.db backed up: finance.db.bak_S184C1_$STAMP" \
&& touch "$FIN/.S184C1_touched" \
&& echo "-- applying the correction (one transaction)" \
&& "$PY" -c "import sqlite3;c=sqlite3.connect('$DB');c.execute('PRAGMA foreign_keys=ON');c.executescript(open('finance_migration_S184_cash_correction.sql').read());c.commit();c.close()" \
&& echo "-- post-verify (read-only)" \
&& VERIFY="$("$PY" gate_c1a.py after)" \
&& { [ "$VERIFY" = "OK" ] || { echo "!! post-verify: $VERIFY"; false; }; } \
&& rm -f "$FIN/.S184C1_touched" \
&& echo "" \
&& echo "=============================================================" \
&& echo " $KIT_NAME INSTALLED — medical cash books corrected" \
&& echo "   closing 13 Aug : -30,056  ->  +27,654" \
&& echo "   deposits       : 31 sheet -> 16 Yes Bank verified (16,45,600)" \
&& echo "   adjustments    : 36 legacy removed (backed up in s184_removed_*)" \
&& echo "   advances       : 3 x Darpan = 40,000 (drawer only, not Ledger)" \
&& echo "   sale money     : UNCHANGED" \
&& echo "   backup         : finance.db.bak_S184C1_$STAMP" \
&& echo "   NO service restarted (no code changed)." \
&& echo "   Interim negative-cash days are the parking footprint — verify from" \
&& echo "   Dr Bhawna's copy for the periods in DELIVERY_NOTE.md, then option 2." \
&& echo "=============================================================" \
|| { echo ""; echo "RED — the correction did not complete cleanly."; \
     if [ -f "$FIN/.S184C1_touched" ]; then \
        echo "   restoring finance.db from the backup taken moments ago:"; \
        cp -f "$DB.bak_S184C1_$STAMP" "$DB" && echo "   finance.db restored to the -30,056 state"; \
        rm -f "$FIN/.S184C1_touched"; \
     else echo "   the gate fired BEFORE anything was touched — nothing to restore."; fi; \
     exit 1; }
