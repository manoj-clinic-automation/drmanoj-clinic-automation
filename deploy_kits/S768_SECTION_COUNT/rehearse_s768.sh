#!/bin/bash
# rehearse_s768.sh LIVE_DIR -- the installer on a MADE-UP root (never /root): dry / a changed file / install / again / a red at [6/6].
# LIVE_DIR holds copies of stockmatch.py, stockmatch.html, section_map.py. Last line: 'REHEARSAL S768 5/5' when all five behave.
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; LIVE="$1"
PY="${PY:-$(command -v python3)}"
R=/tmp/r768; OK=0
mk() { rm -rf "$R"; mkdir -p "$R/root/finance" "$R/root/shared" "$R/tmp"; \cp -p "$LIVE/stockmatch.py" "$LIVE/stockmatch.html" "$LIVE/section_map.py" "$R/root/finance/";
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
          REHEARSE_PROOF=skip "$@" bash "$KDIR/install_S768_SECTION_COUNT.sh" 2>&1; }
pins() { for f in stockmatch.py stockmatch.html section_count.py section_count.html; do printf '%s ' "$(md5sum "$R/root/finance/$f" 2>/dev/null | cut -c1-8)"; done; }

mk; O=$(run DRY=1); P=$(pins)
echo "$O" | grep -q "DRY RUN: every gate" && [ "$P" = "623cb6f1 02826136   " ] && { echo "GREEN 1 dry: green, nothing written"; OK=$((OK+1)); } || { echo "RED 1 dry"; echo "$O" | tail -5; echo "pins: $P"; }

mk; echo "# a change" >> "$R/root/finance/stockmatch.py"; O=$(run)
echo "$O" | grep -q "\[2/6\].*changed after this kit was built" && [ ! -e "$R/root/finance/section_count.py" ] && [ ! -d "$R/lock" ] && { echo "GREEN 2 a changed live file: stopped at [2/6], nothing placed, lock released"; OK=$((OK+1)); } || { echo "RED 2"; echo "$O" | tail -4; }

mk; O=$(run); P=$(pins)
TOP=$(awk '{printf "%s ", substr($1,1,8)}' "$KDIR/TO_PINS.md5")
SEEDN=$("$PY" -c "import sqlite3; c=sqlite3.connect('$R/root/finance/finance.db'); print(c.execute('select count(*) from section_item_display').fetchone()[0], c.execute('select count(*) from section_count_flag').fetchone()[0])")
echo "$O" | grep -q "S768_SECTION_COUNT: DONE" && [ "$P" = "$TOP" ] && [ "$SEEDN" = "75 21" ] && ls "$R/root/finance/"stockmatch.*.bak_S768_* >/dev/null 2>&1 && [ ! -d "$R/lock" ] \
  && { echo "GREEN 3 install: the four files at TO, the seed 75 + 21, backups, lock released"; OK=$((OK+1)); } || { echo "RED 3"; echo "$O" | tail -8; echo "pins $P / $TOP; seed $SEEDN"; }

O=$(run); echo "$O" | grep -q "ALREADY INSTALLED" && { echo "GREEN 4 again: already installed, nothing written"; OK=$((OK+1)); } || { echo "RED 4"; echo "$O" | tail -3; }

mk; O=$(run REHEARSE_RED_AT=6); P=$(pins)
echo "$O" | grep -q "RED after placing" && [ "$P" = "623cb6f1 02826136   " ] && [ ! -d "$R/lock" ] && { echo "GREEN 5 a red at [6/6]: both files put back, the new ones removed, lock released"; OK=$((OK+1)); } || { echo "RED 5"; echo "$O" | tail -6; echo "pins: $P"; }
rm -rf "$R" "$R.sysctl" "$R.health"
echo "REHEARSAL S768 $OK/5"
