#!/bin/bash
# undo_s894.sh -- kit S894: stock_watch.py back to f0d9092a (from its .bak), clinic-finance restarted, the two jobs taken off Amir's card
# if still open. The asks closed by the data step stay closed (they were answered).
set -u
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
F1="f0d9092a051c4cd043645e4510ef4cee"; B1="$ROOT/finance/stock_watch.py.bak_S894_${F1:0:8}"
[ "$(md5sum "$B1" 2>/dev/null | awk '{print $1}')" = "$F1" ] || { echo "!! $B1 is not the FROM file - nothing undone"; exit 1; }
\cp -p "$B1" "$ROOT/finance/stock_watch.py" && "$SYSTEMCTL" restart "$FSVC" || { echo "!! the copy or restart failed"; exit 1; }
"$VPY" -c "import sqlite3,sys;c=sqlite3.connect(sys.argv[1]);n=c.execute(\"DELETE FROM amir_job WHERE key IN ('S894:zibon-extra:count-18nov','S894:gemcal-xt:count-18nov') AND done_at IS NULL AND said_at IS NULL\").rowcount;c.commit();print('jobs removed:',n)" "$DB"
sleep "${NAP:-6}"; HZ=$(curl -s -o /dev/null -m 8 -w "%{http_code}" "http://127.0.0.1:${FIN_PORT:-8106}/finance/healthz" 2>/dev/null)
echo "S894 undone: stock_watch.py $(md5sum "$ROOT/finance/stock_watch.py" | cut -c1-8), $FSVC restarted, finance healthz $HZ (jobs Amir already answered stay on his card)."
