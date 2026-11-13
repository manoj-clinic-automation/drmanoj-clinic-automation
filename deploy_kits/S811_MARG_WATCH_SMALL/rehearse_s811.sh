#!/bin/bash
# rehearse_s811.sh LIVE_ROOT DBCOPY -- the installer on a MADE-UP root (copies of the live files and of a database copy; never /root). Last line: 'REHEARSAL S811 7/7'.
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; LIVE="$1"; DBC="$2"; PY="${PY:-$(command -v python3)}"; R=/tmp/r811; OK=0
mk() { rm -rf "${R:?}"; mkdir -p "$R/root" "$R/tmp"; \cp -rp "$LIVE/finance" "$LIVE/shared" "$R/root/"; \cp -p "$DBC" "$R/root/finance/finance.db"; }
printf '#!/bin/bash\necho 200\n' > "$R.health"; printf '#!/bin/bash\necho "$@" >> /tmp/r811.sysctl\n' > "$R.sys"; chmod +x "$R.health" "$R.sys"
run() { env ROOT="$R/root" LOCK="$R/lock" TMPW="$R/tmp" APY="$PY" VPY="$PY" NAP=0 HEALTH_CMD="$R.health" SYSTEMCTL="$R.sys" "$@" bash "$KDIR/install_S811_MARG_WATCH_SMALL.sh" 2>&1; }
pin() { echo "$(md5sum "$R/root/finance/marg_billwatch.py" | cut -c1-8)/$(md5sum "$R/root/finance/owner_console.py" | cut -c1-8)"; }
live3() { "$PY" -c "import sqlite3,sys;print(sqlite3.connect(sys.argv[1]).execute(\"SELECT COUNT(*) FROM purchase_export WHERE superseded_by IS NULL AND md5 IN ('15b48bc5a25d04f1635db6b29ad04c6d','957b473f59d911ea4d10eea91ae4c71f','de92f5d5185646d4de563e30d5464f6e')\").fetchone()[0])" "$R/root/finance/finance.db"; }
TOP="$(awk '$2=="finance/marg_billwatch.py"{print substr($1,1,8)}' "$KDIR/TO_PINS.md5")/$(awk '$2=="finance/owner_console.py"{print substr($1,1,8)}' "$KDIR/TO_PINS.md5")"
FROMP="616490b4/ba977832"
mk; O=$(run DRY=1); echo "$O" | grep -q "DRY RUN: every gate" && [ "$(pin)" = "$FROMP" ] && [ "$(live3)" = 3 ] && [ ! -d "$R/lock" ] && { echo "GREEN 1 dry: nothing written"; OK=$((OK+1)); } || { echo "RED 1"; echo "$O" | tail -8; }
mk; echo "# a change" >> "$R/root/finance/owner_console.py"; O=$(run); echo "$O" | grep -q "\[2/7\].*changed after this kit" && [ ! -d "$R/lock" ] && [ "$(live3)" = 3 ] && { echo "GREEN 2 a changed live file (the parent's): stop, nothing installed"; OK=$((OK+1)); } || { echo "RED 2"; echo "$O" | tail -4; }
mk; rm -f /tmp/r811.sysctl; O=$(run); echo "$O" | grep -q "S811_MARG_WATCH_SMALL: DONE" && [ "$(pin)" = "$TOP" ] && [ "$(live3)" = 0 ] && [ -f "$R/root/finance/marg_billwatch.py.bak_S811_616490b4" ] && [ -f "$R/root/finance/owner_console.py.bak_S811_ba977832" ] && [ ! -d "$R/lock" ] && grep -q "restart clinic-finance" /tmp/r811.sysctl && ls "$R"/root/finance/s811_repair_before_*.json >/dev/null 2>&1 && { echo "GREEN 3 the install: both placed, restarted, the three lists retired, before-state saved"; OK=$((OK+1)); } || { echo "RED 3"; echo "$O" | tail -10; }
O=$(run); echo "$O" | grep -q "ALREADY INSTALLED" && echo "$O" | grep -q "ALREADY: the three" && [ "$(live3)" = 0 ] && { echo "GREEN 4 again: nothing more"; OK=$((OK+1)); } || { echo "RED 4"; echo "$O" | tail -4; }
mk; O=$(run); L=$(echo "$O" | grep "undo the files (one line)" | sed 's/.*undo the files (one line): //; s/ && [^ ]*sys restart.*//'); eval "$L"; [ "$(pin)" = "$FROMP" ] && { echo "GREEN 5 the undo line puts both files back byte for byte"; OK=$((OK+1)); } || { echo "RED 5 ($L)"; }
mk; O=$(run REHEARSE_RED_AT=5); echo "$O" | grep -q "RED after placing" && [ "$(pin)" = "$FROMP" ] && [ "$(live3)" = 3 ] && [ ! -d "$R/lock" ] && { echo "GREEN 6 a red at [5/7]: both files put back, the database untouched"; OK=$((OK+1)); } || { echo "RED 6"; echo "$O" | tail -4; }
mk; mkdir -p "$R/lock"; echo "another" > "$R/lock/owner"; O=$(run); echo "$O" | grep -q "another build holds the lock" && [ "$(pin)" = "$FROMP" ] && [ -f "$R/lock/owner" ] && { echo "GREEN 7 the lock held by another: nothing installed, their lock left"; OK=$((OK+1)); } || { echo "RED 7"; echo "$O" | tail -4; }
rm -rf "${R:?}" "$R.health" "$R.sys" /tmp/r811.sysctl
echo "REHEARSAL S811 $OK/7"
