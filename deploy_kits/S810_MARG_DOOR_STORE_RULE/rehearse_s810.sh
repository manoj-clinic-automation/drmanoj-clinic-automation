#!/bin/bash
# rehearse_s810.sh LIVE_ROOT -- the installer on a MADE-UP root (a copy of the live files, never /root). Last line: 'REHEARSAL S810 7/7'.
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; LIVE="$1"; PY="${PY:-$(command -v python3)}"; R=/tmp/r810; OK=0
mk() { rm -rf "${R:?}"; mkdir -p "$R/root" "$R/tmp"; \cp -rp "$LIVE/marg_ingest" "$LIVE/finance" "$R/root/"; }
printf '#!/bin/bash\necho 200\n' > "$R.health"; printf '#!/bin/bash\necho "$@" >> /tmp/r810.sysctl\n' > "$R.sys"; chmod +x "$R.health" "$R.sys"
run() { env ROOT="$R/root" LOCK="$R/lock" TMPW="$R/tmp" APY="$PY" VPY="$PY" NAP=0 HEALTH_CMD="$R.health" SYSTEMCTL="$R.sys" "$@" bash "$KDIR/install_S810_MARG_DOOR_STORE_RULE.sh" 2>&1; }
pin() { echo "$(md5sum "$R/root/marg_ingest/marg_router.py" | cut -c1-8)/$(md5sum "$R/root/finance/reports_tile.py" | cut -c1-8)"; }
TOP="$(awk '$2=="marg_ingest/marg_router.py"{print substr($1,1,8)}' "$KDIR/TO_PINS.md5")/$(awk '$2=="finance/reports_tile.py"{print substr($1,1,8)}' "$KDIR/TO_PINS.md5")"
FROMP="318086e3/4eaeadbd"
mk; O=$(run DRY=1); echo "$O" | grep -q "DRY RUN: every gate" && [ "$(pin)" = "$FROMP" ] && [ ! -d "$R/lock" ] && { echo "GREEN 1 dry: nothing written"; OK=$((OK+1)); } || { echo "RED 1"; echo "$O" | tail -6; }
mk; echo "# a change" >> "$R/root/finance/reports_tile.py"; O=$(run); echo "$O" | grep -q "\[2/6\].*changed after this kit" && [ ! -d "$R/lock" ] && { echo "GREEN 2 a changed live file: stop, nothing installed"; OK=$((OK+1)); } || { echo "RED 2"; echo "$O" | tail -4; }
mk; rm -f /tmp/r810.sysctl; O=$(run); echo "$O" | grep -q "S810_MARG_DOOR_STORE_RULE: DONE" && [ "$(pin)" = "$TOP" ] && [ -f "$R/root/marg_ingest/marg_router.py.bak_S810_318086e3" ] && [ -f "$R/root/finance/reports_tile.py.bak_S810_4eaeadbd" ] && [ ! -d "$R/lock" ] && grep -q "restart clinic-finance" /tmp/r810.sysctl && echo "$O" | grep -q "selftest OK; walk_s810 on the placed files: GREEN" && { echo "GREEN 3 the install: both placed, backups, restarted, selftest and walk in place"; OK=$((OK+1)); } || { echo "RED 3"; echo "$O" | tail -8; }
O=$(run); echo "$O" | grep -q "ALREADY INSTALLED" && [ "$(pin)" = "$TOP" ] && { echo "GREEN 4 again: nothing more"; OK=$((OK+1)); } || { echo "RED 4"; echo "$O" | tail -4; }
U=$(echo "$O" ; true); mk; O=$(run); L=$(echo "$O" | grep "undo (one line)" | sed 's/.*undo (one line): //; s/ && [^ ]*sys restart.*//'); eval "$L"; [ "$(pin)" = "$FROMP" ] && { echo "GREEN 5 the undo line puts both files back byte for byte"; OK=$((OK+1)); } || { echo "RED 5 ($L)"; }
mk; O=$(run REHEARSE_RED_AT=4); echo "$O" | grep -q "RED after placing" && [ "$(pin)" = "$FROMP" ] && [ ! -d "$R/lock" ] && { echo "GREEN 6 a red at [4/6]: both files put back"; OK=$((OK+1)); } || { echo "RED 6"; echo "$O" | tail -4; }
mk; mkdir -p "$R/lock"; echo "another" > "$R/lock/owner"; O=$(run); echo "$O" | grep -q "another build holds the lock" && [ "$(pin)" = "$FROMP" ] && [ -f "$R/lock/owner" ] && { echo "GREEN 7 the lock held by another: nothing installed, their lock left"; OK=$((OK+1)); } || { echo "RED 7"; echo "$O" | tail -4; }
rm -rf "${R:?}" "$R.health" "$R.sys" /tmp/r810.sysctl
echo "REHEARSAL S810 $OK/7"
