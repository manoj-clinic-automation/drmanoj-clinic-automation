#!/bin/bash
# install_S435_SCAN_BILL_MONTH.sh -- session 286 (parent), 28-Sep-2026 -- F-658: the scanner asks which month a bill is from.
#   /root/assetapp/asset_register.py  df8c0e19 -> 1f80773b  (12 anchored edits: bills.bill_month; the intake's month choice;
#   late_for follows the person's month before the OCR's date; the bill page shows the month; checker's one-tap /bills/<id>/month)
# Proven on a SCRATCH COPY of assets.db first (walk_s435.py). RED after placing = the old file back. Restarts assetapp.
set -u -o pipefail
KIT="S435_SCAN_BILL_MONTH"; KDIR="$(cd "$(dirname "$0")" && pwd)"; AD="${AD:-/root/assetapp}"; SPY=/usr/bin/python3
FROM=df8c0e19; TO=1f80773b
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }; say() { echo "$@"; }
cd "$KDIR" || exit 1
say "[1/6] kit gates"
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit"; exit 1; }
[ "$(m5 asset_register.py | cut -c1-8)" = "$TO" ] || { say "!! [1/6] the kit's file is not the built one"; exit 1; }
$SPY -B -c "import sys; [compile(open(f).read(), f, 'exec', dont_inherit=True) for f in sys.argv[1:]]" asset_register.py walk_s435.py || { say "!! [1/6] compile check failed"; exit 1; }
say "      green"
say "[2/6] the live file"
A0="$(m5 "$AD/asset_register.py")"; ALREADY=0
if [ "${A0:0:8}" = "$TO" ]; then say "      already in -- nothing to place"; ALREADY=1
elif [ "${A0:0:8}" != "$FROM" ]; then say "!! [2/6] asset_register.py is ${A0:0:8}, not $FROM -- it moved. Nothing installed; the kit is rebuilt from the new bytes."; exit 1
else say "      asset_register.py ${A0:0:8} = the bytes this kit was built from"; fi
say "[3/6] the walk, on a scratch copy of assets.db"
W="/tmp/s435_walk_$(date +%Y%m%d_%H%M%S)"; mkdir -p "$W"
$SPY -B -c "import sqlite3; s=sqlite3.connect('file:$AD/assets.db?mode=ro', uri=True); d=sqlite3.connect('$W/assets.db'); s.backup(d); d.close(); s.close()" || { say "!! [3/6] copy of assets.db failed"; rm -rf "$W"; exit 1; }
( cd /tmp && ASSETS_LIVE="$AD" timeout 300 $SPY -B "$KDIR/walk_s435.py" "$KDIR" "$W" "$W/assets.db" ) > "$W.log" 2>&1
WOUT="$(tail -1 "$W.log")"; sed 's/^/      /' "$W.log"; rm -rf "$W"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [3/6] walk red - nothing installed (the log: $W.log)"; exit 1; }
[ "$ALREADY" = 1 ] && { say "      all green -- $KIT: already DONE"; exit 0; }
say "[4/6] backups"
STAMP="$(date +%Y%m%d_%H%M%S)"; BA="$AD/asset_register.py.bak_S435_${A0:0:8}"; BD="$AD/assets.db.bak_S435_$STAMP"
\cp -p "$AD/asset_register.py" "$BA" || { say "!! [4/6] backup failed"; exit 1; }
$SPY -B -c "import sqlite3; s=sqlite3.connect('$AD/assets.db'); d=sqlite3.connect('$BD'); s.backup(d); d.close(); s.close()" || { say "!! [4/6] database backup failed"; exit 1; }
say "      $BA · $BD"
restore() { say "!! RED after placing ($1) - the old file back"; \cp -p "$BA" "$AD/asset_register.py"; systemctl restart assetapp || true; sleep 4; say "   asset_register.py $(m5 "$AD/asset_register.py") (was $A0) · database backup kept: $BD"; exit 1; }
say "[5/6] place + restart assetapp"
\cp -p "$KDIR/asset_register.py" "$AD/asset_register.py" || restore "copy"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart assetapp || restore "restart"; sleep 5; systemctl is-active --quiet assetapp || restore "not active"
L="$(curl -s -o /dev/null -m 10 -w '%{http_code}' http://127.0.0.1:8030/login)"
I="$(curl -s -o /dev/null -m 10 -w '%{http_code}' http://127.0.0.1:8030/intake)"
say "      login page $L (200 expected) · intake without login $I (302 expected)"
[ "$L" = 200 ] || restore "login page"; [ "$I" = 302 ] || restore "intake gate"
JR="$(journalctl -u assetapp --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')"
[ "$JR" = 0 ] || { journalctl -u assetapp --since "$T0" --no-pager | grep -i -A6 'Traceback\|Error' | head -30; restore "journal: $JR error line(s)"; }
say "[6/6] the bills already scanned, and the month each would fall in"
$SPY -B - "$AD/assets.db" <<'PY' | sed 's/^/      /'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
for r in c.execute("SELECT stamp_no, COALESCE(lane,'clinic'), COALESCE(bill_date,'-'), COALESCE(bill_month,''), substr(created_at,1,10), status FROM bills WHERE stamp_no IS NOT NULL ORDER BY id"):
    print("%-7s %-13s bill date %-10s month %-7s scanned %s  %s" % r)
PY
say "      all green -- $KIT: DONE"
md5sum "$AD/asset_register.py"
