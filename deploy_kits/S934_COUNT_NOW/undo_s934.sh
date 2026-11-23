#!/bin/bash
# undo_s934.sh -- kit S934_COUNT_NOW: the six files back to their FROM pins from the install's backups; clinic-finance restarted.
# The new columns (stock_watch_ask.mode / closed_how, stock_point.last_bill / ask_id) stay -- the old code never reads them. The asks the
# install withdrew stay withdrawn. A count already placed to a bill stays as it is ('awaits_sales' is shown as a plain count by the old page).
set -u
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
NAMES=("finance/stock_watch.py" "finance/stock_figure.py" "finance/stock_check.py" "finance/stock_check.html" "finance/stockmatch.py" "finance/stockmatch.html")
FROMS=("0dd0a40a238f0cfeb3c907cd488dd791" "5d15e77dae11c7ee0799290e1a442760" "bf68c55b20f90673b134e8d25c23aaa5" "4d6cbc6f8733226663688371473c0ff0" "57d04d3e9c272ebafdcae2e77086f6fc" "0ec2e32d74d5d9167b38b1786eca6032")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
for k in 0 1 2 3 4 5; do b="$ROOT/${NAMES[$k]}.bak_S934_${FROMS[$k]:0:8}"
  [ "$(m5 "$ROOT/${NAMES[$k]}")" = "${FROMS[$k]}" ] && continue
  [ -f "$b" ] && [ "$(m5 "$b")" = "${FROMS[$k]}" ] || { echo "!! no backup at $b with the FROM pin - stop, nothing changed"; exit 1; }; done
n=0
for k in 0 1 2 3 4 5; do b="$ROOT/${NAMES[$k]}.bak_S934_${FROMS[$k]:0:8}"
  if [ "$(m5 "$ROOT/${NAMES[$k]}")" = "${FROMS[$k]}" ]; then echo "   ${NAMES[$k]} already at its FROM pin"; continue; fi
  \cp -p "$b" "$ROOT/${NAMES[$k]}" && [ "$(m5 "$ROOT/${NAMES[$k]}")" = "${FROMS[$k]}" ] || { echo "!! could not put ${NAMES[$k]} back"; exit 1; }
  n=$((n+1)); done
# a count still waiting for its sale report would wait for ever under the old code: it is closed unjudged, said in its note
PYB="${VPY:-/root/wa/venv/bin/python3}"; [ -x "$PYB" ] || PYB=python3
W=$("$PYB" -c "
import sqlite3, datetime
con = sqlite3.connect('$ROOT/finance/finance.db', timeout=60)
try:
    n = con.execute(\"UPDATE stock_point SET status='settled', settled_at=?, note=COALESCE(note,'') || ' · S934 undone -- not judged' WHERE status='awaits_sales'\", (datetime.datetime.now().replace(microsecond=0).isoformat(),)).rowcount
    con.commit(); print(n)
except sqlite3.Error as e:
    print('error %s' % e)
" 2>&1 | tail -1)
echo "   counts waiting for their sale report, closed unjudged: $W"
[ "$n" = 0 ] && { echo "S934 undo: nothing to do"; exit 0; }
"$SYSTEMCTL" restart "$FSVC"; sleep 4
echo "   note: an item whose last count was a Count now placed to a bill shows a shelf figure a little low (that day's sales up to the bill are taken off again by the old rule) until it is counted again"
echo "S934 undo: $n file(s) back; finance healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz")"
