#!/bin/bash
# rehearse_s783.sh FINANCE_DIR ASSETAPP_DIR SHARED_DIR SCHEMA_JSON -- the installer on a MADE-UP root (never /root): dry / a changed file / install /
# again / a red at [6/6] / a Traceback in the journal. FINANCE_DIR (with S781 installed), ASSETAPP_DIR, SHARED_DIR: copies of the live code; SCHEMA_JSON: the tables'
# layout only (an empty finance.db is made from it). Last line: 'REHEARSAL S783 6/6'.
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; LIVE="$1"; APP="$2"; SHARED="$3"; SCHEMA="$4"
PY="${PY:-$(command -v python3)}"
R=/tmp/r783; OK=0
mk() { rm -rf "${R:?}"; mkdir -p "$R/root/finance" "$R/root/assetapp" "$R/root/shared" "$R/tmp"
       \cp -rp "$LIVE/." "$R/root/finance/"; \cp -rp "$APP/." "$R/root/assetapp/"; \cp -rp "$SHARED/." "$R/root/shared/"
       find "$R/root" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
       "$PY" - "$R/root/finance/finance.db" "$SCHEMA" <<'P'
import json, sqlite3, sys
c = sqlite3.connect(sys.argv[1])
for q in json.load(open(sys.argv[2]))["ddl"]:
    try:
        c.execute(q)
    except sqlite3.Error:
        pass
c.commit()
P
}
cat > "$R.sysctl" <<'E'
#!/bin/bash
exit 0
E
chmod +x "$R.sysctl"
cat > "$R.health" <<'E'
#!/bin/bash
echo 200
E
chmod +x "$R.health"
run() { env ROOT="$R/root" SKIP_WINDOW=1 LOCK="$R/lock" TMPW="$R/tmp" APY="$PY" VPY="$PY" SYSTEMCTL="$R.sysctl" JOURNALCTL=/nonexistent HEALTH_CMD="$R.health" \
          "$@" bash "$KDIR/install_S783_SCAN_LINE_EXTRAS.sh" 2>&1; }
pins() { printf '%s %s' "$(md5sum "$R/root/assetapp/claude_reader.py" | cut -c1-8)" "$(md5sum "$R/root/finance/provisional_s781.py" | cut -c1-8)"; }
TOP="$(awk '$2=="assetapp/claude_reader.py"{print substr($1,1,8)}' "$KDIR/TO_PINS.md5") $(awk '$2=="finance/provisional_s781.py"{print substr($1,1,8)}' "$KDIR/TO_PINS.md5")"
FRP="ce3868ed 15daff39"

mk; O=$(run DRY=1); P=$(pins)
echo "$O" | grep -q "DRY RUN: every gate" && [ "$P" = "$FRP" ] && { echo "GREEN 1 dry: green, nothing written"; OK=$((OK+1)); } || { echo "RED 1 dry"; echo "$O" | tail -8; echo "pins: $P"; }

mk; echo "# a change" >> "$R/root/assetapp/claude_reader.py"; O=$(run)
echo "$O" | grep -q "\[2/6\].*changed after this kit was built" && [ ! -d "$R/lock" ] && [ "$(md5sum "$R/root/finance/provisional_s781.py" | cut -c1-8)" = 15daff39 ] \
  && { echo "GREEN 2 a changed live file: stopped at [2/6], nothing placed, lock released"; OK=$((OK+1)); } || { echo "RED 2"; echo "$O" | tail -4; }

mk; O=$(run); P=$(pins)
echo "$O" | grep -q "S783_SCAN_LINE_EXTRAS: DONE" && [ "$P" = "$TOP" ] && ls "$R/root/assetapp/"claude_reader.py.bak_S783_ce3868ed "$R/root/finance/"provisional_s781.py.bak_S783_15daff39 >/dev/null 2>&1 && [ ! -d "$R/lock" ] \
  && { echo "GREEN 3 install: both files at TO, both backups, lock released"; OK=$((OK+1)); } || { echo "RED 3"; echo "$O" | tail -8; echo "pins $P / $TOP"; }

O=$(run); echo "$O" | grep -q "ALREADY INSTALLED" && { echo "GREEN 4 again: already installed, nothing written"; OK=$((OK+1)); } || { echo "RED 4"; echo "$O" | tail -3; }

mk; O=$(run REHEARSE_RED_AT=6); P=$(pins)
echo "$O" | grep -q "RED after placing" && [ "$P" = "$FRP" ] && [ ! -d "$R/lock" ] && { echo "GREEN 5 a red at [6/6]: both files put back, lock released"; OK=$((OK+1)); } || { echo "RED 5"; echo "$O" | tail -6; echo "pins: $P"; }
cat > "$R.journal" <<'E'
#!/bin/bash
echo "Nov 11 06:00:00 box gunicorn[99999]: Traceback (most recent call last):"
E
chmod +x "$R.journal"
mk; O=$(env ROOT="$R/root" SKIP_WINDOW=1 LOCK="$R/lock" TMPW="$R/tmp" APY="$PY" VPY="$PY" SYSTEMCTL="$R.sysctl" JOURNALCTL="$R.journal" HEALTH_CMD="$R.health" \
        bash "$KDIR/install_S783_SCAN_LINE_EXTRAS.sh" 2>&1); P=$(pins)
echo "$O" | grep -q "RED after placing (journal" && [ "$P" = "$FRP" ] && [ ! -d "$R/lock" ] && { echo "GREEN 6 a Traceback in the journal after the restart: both files put back"; OK=$((OK+1)); } || { echo "RED 6"; echo "$O" | tail -6; echo "pins: $P"; }
rm -rf "${R:?}" "$R.sysctl" "$R.health" "$R.journal"
echo "REHEARSAL S783 $OK/6"
