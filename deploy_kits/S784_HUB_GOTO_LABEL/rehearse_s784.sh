#!/bin/bash
# rehearse_s784.sh LIVE_HTML -- the installer on a MADE-UP root (never /root). Last line: 'REHEARSAL S784 5/5'.
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; LIVE="$1"; PY="${PY:-$(command -v python3)}"; R=/tmp/r784; OK=0
mk() { rm -rf "${R:?}"; mkdir -p "$R/root/finance/finance_ui" "$R/tmp"; \cp -p "$LIVE" "$R/root/finance/finance_ui/finance_approvals.html"; }
printf '#!/bin/bash\necho 200\n' > "$R.health"; chmod +x "$R.health"
run() { env ROOT="$R/root" LOCK="$R/lock" TMPW="$R/tmp" APY="$PY" HEALTH_CMD="$R.health" "$@" bash "$KDIR/install_S784_HUB_GOTO_LABEL.sh" 2>&1; }
pin() { md5sum "$R/root/finance/finance_ui/finance_approvals.html" | cut -c1-8; }
TOP="$(awk '{print substr($1,1,8)}' "$KDIR/TO_PINS.md5")"
mk; O=$(run DRY=1); echo "$O" | grep -q "DRY RUN: every gate" && [ "$(pin)" = dcd94412 ] && { echo "GREEN 1 dry"; OK=$((OK+1)); } || { echo "RED 1"; echo "$O" | tail -4; }
mk; echo "<!-- a change -->" >> "$R/root/finance/finance_ui/finance_approvals.html"; O=$(run); echo "$O" | grep -q "\[2/4\].*changed after this kit" && [ ! -d "$R/lock" ] && { echo "GREEN 2 a changed live file: stopped"; OK=$((OK+1)); } || { echo "RED 2"; echo "$O" | tail -3; }
mk; O=$(run); echo "$O" | grep -q "S784_HUB_GOTO_LABEL: DONE" && [ "$(pin)" = "$TOP" ] && [ -f "$R/root/finance/finance_ui/finance_approvals.html.bak_S784_dcd94412" ] && [ ! -d "$R/lock" ] && { echo "GREEN 3 install"; OK=$((OK+1)); } || { echo "RED 3"; echo "$O" | tail -4; }
O=$(run); echo "$O" | grep -q "ALREADY INSTALLED" && { echo "GREEN 4 again"; OK=$((OK+1)); } || { echo "RED 4"; echo "$O" | tail -3; }
mk; O=$(run REHEARSE_RED_AT=4); echo "$O" | grep -q "RED after placing" && [ "$(pin)" = dcd94412 ] && [ ! -d "$R/lock" ] && { echo "GREEN 5 a red at [4/4]: put back"; OK=$((OK+1)); } || { echo "RED 5"; echo "$O" | tail -4; }
rm -rf "${R:?}" "$R.health"
echo "REHEARSAL S784 $OK/5"
