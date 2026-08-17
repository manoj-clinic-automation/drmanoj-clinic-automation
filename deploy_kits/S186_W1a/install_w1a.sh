#!/bin/bash
# =============================================================================
#  install_w1a.sh · kit S186_W1a — F-104, the WALK-IN reclass.
#
#  TOUCHES ATTRIBUTION ONLY. day_line — the sale money — is never written to,
#  and the gate proves it by sum, by row count, and by cash-in-hand.
#
#  The PRECHECK projects the result before a single row is written: how many
#  days are flagged now, how many would be flagged after, and any day that would
#  end up FURTHER from balanced. If the trade is bad you see it first.
#
#  Shape (D317): preflight -> SUMS -> KIT_ID -> currency gate -> precheck ->
#  db backup -> apply -> verify -> automatic restore on red.
# =============================================================================
set -u
KIT_NAME="S186_W1a"
DB=/root/finance/finance.db
LIVE_APP=/root/finance/finance_app.py
APP_MD5_EXPECTED=d04167a848e5d6f0baae19df014f70d4    # after S186_I1a
PY=/usr/bin/python3
SNAP=/tmp/f104_before.json
export F104_SNAP="$SNAP"

for c in md5sum awk cp date; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — refusing"; exit 1; }
done
[ -x "$PY" ] || { echo "!! preflight: $PY not executable — refusing"; exit 1; }
[ -f "$DB" ] || { echo "!! preflight: $DB not found — refusing"; exit 1; }
KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; cd "$KIT_DIR" || exit 1

md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT_NAME" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum finance_migration_S186_walkin.sql | awk '{print $1}')" ] \
&& echo "-- kit integrity + currency OK" \
&& echo "" \
&& echo "-- LIVE-CODE CURRENCY GATE (F-97)" \
&& LIVE_NOW="$(md5sum "$LIVE_APP" | awk '{print $1}')" \
&& { [ "$LIVE_NOW" = "$APP_MD5_EXPECTED" ] \
     || { echo "!! live finance_app.py is $LIVE_NOW, expected $APP_MD5_EXPECTED (post-S186_I1a)"; \
          echo "   Refusing. Correct the Register FROM the box first (D321(d))."; exit 1; }; } \
&& echo "   live app = d04167a848... as expected" \
&& echo "" \
&& "$PY" gate_f104.py "$DB" --precheck \
&& echo "-- backing up the whole database before touching it" \
&& BAK="${DB}.bak_${KIT_NAME}_$(date +%Y%m%d_%H%M%S)" \
&& cp -f "$DB" "$BAK" && echo "   backup: $BAK" \
&& echo "" \
&& echo "-- applying (one transaction)" \
&& "$PY" -c "import sqlite3;c=sqlite3.connect('$DB');c.execute('PRAGMA foreign_keys=ON');c.executescript(open('finance_migration_S186_walkin.sql').read());c.commit();c.close()" \
&& echo "-- applied; verifying" \
&& { "$PY" gate_f104.py "$DB" --verify; VRC=$?; \
     if [ $VRC -ne 0 ]; then \
       echo ""; echo "!! VERIFY RED — RESTORING. The books are exactly as found."; \
       cp -f "$BAK" "$DB"; echo "   restored from $BAK"; exit 1; fi; } \
&& echo "=============================================================" \
&& echo " $KIT_NAME INSTALLED — F-104 cleared." \
&& echo "" \
&& echo " The review queue is empty and the dashboard is quiet." \
&& echo " No money moved: day_line untouched, cash in hand unchanged." \
&& echo "" \
&& echo " Any day still flagged is NOT a legacy no-ID day — its Marg" \
&& echo " lines genuinely disagree with the declared total. Those are" \
&& echo " worth looking at; they were hidden in the noise before." \
&& echo "" \
&& echo " Rollback: the block at the foot of the .sql, or restore $BAK" \
&& echo "=============================================================" \
&& exit 0 \
|| { echo ""; echo "RED — install did not complete."; \
     echo "   A gate fired before the database was written, or verify restored it."; exit 1; }
