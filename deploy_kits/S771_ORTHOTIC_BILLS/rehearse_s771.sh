#!/bin/bash
# rehearse_s771.sh LIVE_DIR -- the installer on a MADE-UP root (never /root): dry / a changed file / install / again / a red at [6/6].
# LIVE_DIR holds copies of the two live files and section_map.py. Last line: 'REHEARSAL S771 5/5' when all five behave.
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; LIVE="$1"
PY="${PY:-$(command -v python3)}"
R=/tmp/r771; OK=0
mk() { rm -rf "$R"; mkdir -p "$R/root/finance" "$R/root/shared" "$R/tmp"; \cp -p "$LIVE/section_map.py" "$LIVE/stock_hub.html" "$LIVE/section_count.py" "$R/root/finance/";
       "$PY" -c "import sqlite3; sqlite3.connect('$R/root/finance/finance.db').execute('CREATE TABLE t (x)')"; }
cat > "$R.sysctl" <<'E'
#!/bin/bash
exit 0
E
chmod +x "$R.sysctl"
cat > "$R.health" <<'E'
#!/bin/bash
[ "${2:-}" = route ] && { echo 401; exit 0; }; echo 200
E
chmod +x "$R.health"
run() { env ROOT="$R/root" SKIP_WINDOW=1 LOCK="$R/lock" TMPW="$R/tmp" APY="$PY" VPY="$PY" SYSTEMCTL="$R.sysctl" JOURNALCTL=/nonexistent HEALTH_CMD="$R.health" \
          REHEARSE_PROOF=skip "$@" bash "$KDIR/install_S771_ORTHOTIC_BILLS.sh" 2>&1; }
pins() { for f in finance/section_count.py finance/stock_hub.html; do printf '%s ' "$(md5sum "$R/root/$f" 2>/dev/null | cut -c1-8)"; done; }

mk; O=$(run DRY=1); P=$(pins)
echo "$O" | grep -q "DRY RUN: every gate" && [ "$P" = "d69e1681 90da7707 " ] && { echo "GREEN 1 dry: green, nothing written"; OK=$((OK+1)); } || { echo "RED 1 dry"; echo "$O" | tail -5; echo "pins: $P"; }

mk; echo "# a change" >> "$R/root/finance/section_count.py"; O=$(run)
echo "$O" | grep -q "\[2/6\].*changed after this kit was built" && [ "$(md5sum "$R/root/finance/stock_hub.html" | cut -c1-8)" = 90da7707 ] && [ ! -d "$R/lock" ] && { echo "GREEN 2 a changed live file: stopped at [2/6], nothing placed, lock released"; OK=$((OK+1)); } || { echo "RED 2"; echo "$O" | tail -4; }

mk; O=$(run); P=$(pins)
TOP=$(awk '{printf "%s ", substr($1,1,8)}' "$KDIR/TO_PINS.md5")
echo "$O" | grep -q "S771_ORTHOTIC_BILLS: DONE" && [ "$P" = "$TOP" ] && ls "$R/root/finance/"stock_hub.html.bak_S771_* "$R/root/finance/"section_count.py.bak_S771_* >/dev/null 2>&1 && [ ! -d "$R/lock" ] \
  && { echo "GREEN 3 install: the two files at TO, backups, lock released"; OK=$((OK+1)); } || { echo "RED 3"; echo "$O" | tail -8; echo "pins $P / $TOP"; }

O=$(run); echo "$O" | grep -q "ALREADY INSTALLED" && { echo "GREEN 4 again: already installed, nothing written"; OK=$((OK+1)); } || { echo "RED 4"; echo "$O" | tail -3; }

mk; O=$(run REHEARSE_RED_AT=6); P=$(pins)
echo "$O" | grep -q "RED after placing" && [ "$P" = "d69e1681 90da7707 " ] && [ ! -d "$R/lock" ] && { echo "GREEN 5 a red at [6/6]: both files put back, lock released"; OK=$((OK+1)); } || { echo "RED 5"; echo "$O" | tail -6; echo "pins: $P"; }
rm -rf "$R" "$R.sysctl" "$R.health"
echo "REHEARSAL S771 $OK/5"
