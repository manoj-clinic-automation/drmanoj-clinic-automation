#!/bin/bash
# install_c2a.sh · kit S184_C2a — regenerate medical exceptions after the C1a correction.
# preflight -> SUMS -> KIT_ID -> STATE gate (C1a applied, C2a not) -> backup ->
# apply (FK on) -> post-verify -> honest red that restores.
set -u
KIT_NAME="S184_C2a"; FIN=/root/finance; PY=/usr/bin/python3; DB="$FIN/finance.db"
SQL=finance_migration_S184_C2a_exceptions.sql
for c in md5sum awk cp; do command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing"; exit 1; }; done
[ -x "$PY" ] || { echo "!! preflight: $PY not executable"; exit 1; }
[ -f "$DB" ] || { echo "!! preflight: $DB not found"; exit 1; }
KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; cd "$KIT_DIR" || exit 1; export FINANCE_DB="$DB"
md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT_NAME" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum $SQL | awk '{print $1}')" ] \
&& echo "-- integrity + kit identity OK" \
&& "$PY" -m py_compile gate_c2a.py \
&& GATE="$("$PY" gate_c2a.py before)" \
&& { [ "$GATE" = "OK" ] || { echo "!! REFUSING — gate says: $GATE"; echo "   (C2a needs C1a applied first, and must not have run before.)"; exit 1; }; } \
&& echo "-- state OK: C1a applied, C2a not yet run" \
&& STAMP="$(date +%Y%m%d_%H%M%S)" \
&& cp -p "$DB" "$DB.bak_S184C2_$STAMP" \
&& echo "-- finance.db backed up: finance.db.bak_S184C2_$STAMP" \
&& touch "$FIN/.S184C2_touched" \
&& echo "-- regenerating exceptions (one transaction)" \
&& "$PY" -c "import sqlite3;c=sqlite3.connect('$DB');c.execute('PRAGMA foreign_keys=ON');c.executescript(open('$SQL').read());c.commit();c.close()" \
&& VERIFY="$("$PY" gate_c2a.py after)" \
&& { [ "$VERIFY" = "OK" ] || { echo "!! post-verify: $VERIFY"; false; }; } \
&& rm -f "$FIN/.S184C2_touched" \
&& echo "" \
&& echo "=============================================================" \
&& echo " $KIT_NAME INSTALLED — exceptions regenerated on corrected data" \
&& echo "   carry_forward_break : all resolved (were stale after C1a)" \
&& echo "   negative_cash       : recomputed from the live ledger" \
&& echo "                         (the real cash-parking windows)" \
&& echo "   line_sum / missing  : untouched" \
&& echo "   backup              : finance.db.bak_S184C2_$STAMP" \
&& echo "=============================================================" \
|| { echo ""; echo "RED — regeneration did not complete."; \
     if [ -f "$FIN/.S184C2_touched" ]; then \
        cp -f "$DB.bak_S184C2_$STAMP" "$DB" && echo "   finance.db restored from backup"; \
        rm -f "$FIN/.S184C2_touched"; \
     else echo "   gate fired before anything was touched — nothing to restore."; fi; exit 1; }
