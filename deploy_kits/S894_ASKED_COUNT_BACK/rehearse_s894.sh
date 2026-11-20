#!/bin/bash
# rehearse_s894.sh -- the installer on a made-up /root (a copy of the code and a copy of the database), never the live box.
set -u
K="$(cd "$(dirname "$0")" && pwd)"; W="${1:-/tmp/s894_reh}"; SRC="${2:?code dir}"; DBC="${3:?db copy}"; SH="${4:-}"
rm -rf "$W"; mkdir -p "$W/root/finance" "$W/bin"; cp -rp "$SRC"/* "$W/root/finance/"; [ -n "$SH" ] && cp -rp "$SH" "$W/root/shared"
cp "$K/../stock_watch_FROM.py" "$W/root/finance/stock_watch.py" 2>/dev/null || true
cp "$DBC" "$W/root/finance/finance.db"
printf '#!/bin/bash\necho 200\n' > "$W/bin/hz"; chmod +x "$W/bin/hz"
E="ROOT=$W/root VPY=python3 APY=python3 SYSTEMCTL=true HEALTH_CMD=$W/bin/hz NAP=0 LOCK=$W/lock TMPW=$W"
p=0; f=0
nj() { python3 -c "import sqlite3,sys;print(sqlite3.connect(sys.argv[1]).execute(\"select count(*) from amir_job where key like 'S894:%'\").fetchone()[0])" "$W/root/finance/finance.db"; }
t() { if eval "$2"; then echo "ok   $1"; p=$((p+1)); else echo "RED  $1"; f=$((f+1)); fi; }
o=$(env $E DRY=1 bash "$K/install_S894_ASKED_COUNT_BACK.sh" 2>&1); t "R1 dry run green, nothing written" 'echo "$o" | grep -q "DRY RUN: every gate" && [ "$(md5sum <"$W/root/finance/stock_watch.py"|cut -c1-8)" = f0d9092a ]'
o=$(env $E REHEARSE_RED_AT=4 bash "$K/install_S894_ASKED_COUNT_BACK.sh" 2>&1); t "R2 a red at [4/5] puts the file back, no job added" 'echo "$o" | grep -q "RED after placing" && [ "$(md5sum <"$W/root/finance/stock_watch.py"|cut -c1-8)" = f0d9092a ] && [ "$(nj)" = 0 ]'
o=$(env $E bash "$K/install_S894_ASKED_COUNT_BACK.sh" 2>&1); t "R3 install: DONE, file at TO, two jobs, asks closed" 'echo "$o" | grep -q "S894_ASKED_COUNT_BACK: DONE" && [ "$(md5sum <"$W/root/finance/stock_watch.py"|cut -d" " -f1)" = "$(awk "{print \$1}" "$K/TO_PINS.md5")" ] && [ "$(nj)" = 2 ]'
echo "$o" | sed -n '/\[3\/5\]/,$p' | head -12
o=$(env $E bash "$K/install_S894_ASKED_COUNT_BACK.sh" 2>&1); t "R4 again: already installed, nothing doubled" 'echo "$o" | grep -q "ALREADY" && [ "$(nj)" = 2 ]'
o=$(env ROOT=$W/root VPY=python3 SYSTEMCTL=true bash "$K/undo_s894.sh" 2>&1); t "R5 undo: file back, jobs off" '[ "$(md5sum <"$W/root/finance/stock_watch.py"|cut -c1-8)" = f0d9092a ] && [ "$(nj)" = 0 ]'
echo "x" >> "$K/s894_job.py"; o=$(env $E bash "$K/install_S894_ASKED_COUNT_BACK.sh" 2>&1); sed -i '$ d' "$K/s894_job.py"
t "R6 a tampered kit file is refused by SUMS" 'echo "$o" | grep -q "SUMS.md5 gate failed"'
echo "x" >> "$W/root/finance/stock_watch.py"; o=$(env $E bash "$K/install_S894_ASKED_COUNT_BACK.sh" 2>&1)
t "R7 a live file not at FROM: STOP, nothing placed" 'echo "$o" | grep -q "expected f0d9092a - STOP"'
rm -rf "$W"; echo "rehearse_s894: $p ok, $f red"
