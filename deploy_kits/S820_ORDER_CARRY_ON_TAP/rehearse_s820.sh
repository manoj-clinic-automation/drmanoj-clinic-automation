#!/bin/bash
# rehearse_s820.sh LIVE_ROOT DBCOPY -- the installer on a MADE-UP root (copies of the live files and of a database copy; never /root). Last line: 'REHEARSAL S820 7/7'.
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; LIVE="$1"; DBC="$2"; PY="${PY:-$(command -v python3)}"; R=/tmp/r820; OK=0
mk() { rm -rf "${R:?}"; mkdir -p "$R/root" "$R/tmp"; \cp -rp "$LIVE/finance" "$LIVE/shared" "$R/root/"; \cp -p "$DBC" "$R/root/finance/finance.db"; }
printf '#!/bin/bash\necho 200\n' > "$R.health"; printf '#!/bin/bash\necho "$@" >> /tmp/r820.sysctl\n' > "$R.sys"; chmod +x "$R.health" "$R.sys"
run() { env ROOT="$R/root" LOCK="$R/lock" TMPW="$R/tmp" APY="$PY" VPY="$PY" NAP=0 HEALTH_CMD="$R.health" SYSTEMCTL="$R.sys" "$@" bash "$KDIR/install_S820_ORDER_CARRY_ON_TAP.sh" 2>&1; }
pin() { local s=""; for f in order_sheet.py order_s778.py porders_s454.py order_track.py order_track_page.py; do s="$s$(md5sum "$R/root/finance/$f" | cut -c1-8)/"; done; echo "${s%/}"; }
TOP="$(for f in order_sheet.py order_s778.py porders_s454.py order_track.py order_track_page.py; do awk -v f="finance/$f" '$2==f{printf "%s/", substr($1,1,8)}' "$KDIR/TO_PINS.md5"; done)"; TOP="${TOP%/}"
FROMP="53abf461/819f60ff/21bf0abc/6f4746c5/4e6bd715"
mk; O=$(run DRY=1); echo "$O" | grep -q "DRY RUN: every gate" && [ "$(pin)" = "$FROMP" ] && [ ! -d "$R/lock" ] && { echo "GREEN 1 dry: nothing written"; OK=$((OK+1)); } || { echo "RED 1"; echo "$O" | tail -8; }
mk; echo "# a change" >> "$R/root/finance/order_s778.py"; O=$(run); echo "$O" | grep -q "\[2/6\].*changed after this kit" && [ ! -d "$R/lock" ] && { echo "GREEN 2 a changed live file: stop, nothing installed"; OK=$((OK+1)); } || { echo "RED 2"; echo "$O" | tail -4; }
mk; rm -f /tmp/r820.sysctl; O=$(run); echo "$O" | grep -q "S820_ORDER_CARRY_ON_TAP: DONE" && [ "$(pin)" = "$TOP" ] && [ -f "$R/root/finance/order_sheet.py.bak_S820_53abf461" ] && [ -f "$R/root/finance/order_s778.py.bak_S820_819f60ff" ] && [ -f "$R/root/finance/porders_s454.py.bak_S820_21bf0abc" ] && [ -f "$R/root/finance/order_track.py.bak_S820_6f4746c5" ] && [ -f "$R/root/finance/order_track_page.py.bak_S820_4e6bd715" ] && [ ! -d "$R/lock" ] && grep -q "restart clinic-finance" /tmp/r820.sysctl && { echo "GREEN 3 the install: five placed at their TO pins, backups, restarted, lock released"; OK=$((OK+1)); } || { echo "RED 3"; echo "$O" | tail -10; }
O=$(run); echo "$O" | grep -q "ALREADY INSTALLED" && [ "$(pin)" = "$TOP" ] && { echo "GREEN 4 again: nothing more"; OK=$((OK+1)); } || { echo "RED 4"; echo "$O" | tail -4; }
mk; O=$(run); L=$(echo "$O" | grep "undo (one line)" | sed 's/.*undo (one line): //; s/ [^ ]*sys restart.*//; s/ && *$//'); eval "$L"; [ "$(pin)" = "$FROMP" ] && { echo "GREEN 5 the undo line puts the five files back byte for byte"; OK=$((OK+1)); } || { echo "RED 5 ($L)"; }
mk; O=$(run REHEARSE_RED_AT=4); echo "$O" | grep -q "RED after placing" && [ "$(pin)" = "$FROMP" ] && [ ! -d "$R/lock" ] && { echo "GREEN 6 a red at [4/6]: the five files put back"; OK=$((OK+1)); } || { echo "RED 6"; echo "$O" | tail -4; }
mk; mkdir -p "$R/lock"; echo "another" > "$R/lock/owner"; O=$(run); echo "$O" | grep -q "another build holds the lock" && [ "$(pin)" = "$FROMP" ] && [ -f "$R/lock/owner" ] && { echo "GREEN 7 the lock held by another: nothing installed, their lock left"; OK=$((OK+1)); } || { echo "RED 7"; echo "$O" | tail -4; }
rm -rf "${R:?}" "$R.health" "$R.sys" /tmp/r820.sysctl
echo "REHEARSAL S820 $OK/7"
