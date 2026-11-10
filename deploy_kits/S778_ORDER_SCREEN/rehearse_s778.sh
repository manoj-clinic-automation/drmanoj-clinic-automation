#!/bin/bash
# rehearse_s778.sh FINANCE_DIR SHARED_DIR SCHEMA_JSON -- the installer on a MADE-UP root (never /root): dry / a changed file / install /
# again / a red at [6/6]. FINANCE_DIR and SHARED_DIR: copies of the live code (porders_s454.py at its FROM pin); SCHEMA_JSON: the tables'
# layout only (an empty finance.db is made from it). Last line: 'REHEARSAL S778 5/5'.
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; LIVE="$1"; SHARED="$2"; SCHEMA="$3"
PY="${PY:-$(command -v python3)}"
R=/tmp/r778; OK=0
mk() { rm -rf "${R:?}"; mkdir -p "$R/root/finance" "$R/root/shared" "$R/tmp"
       \cp -rp "$LIVE/." "$R/root/finance/"; \cp -rp "$SHARED/." "$R/root/shared/"; rm -f "$R/root/finance/order_s778.py"
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
[ "${2:-}" = route ] && { echo 401; exit 0; }; echo 200
E
chmod +x "$R.health"
run() { env ROOT="$R/root" SKIP_WINDOW=1 LOCK="$R/lock" TMPW="$R/tmp" APY="$PY" VPY="$PY" SYSTEMCTL="$R.sysctl" JOURNALCTL=/nonexistent HEALTH_CMD="$R.health" \
          REHEARSE_PROOF=skip "$@" bash "$KDIR/install_S778_ORDER_SCREEN.sh" 2>&1; }
pins() { printf '%s %s' "$(md5sum "$R/root/finance/porders_s454.py" 2>/dev/null | cut -c1-8)" "$( [ -e "$R/root/finance/order_s778.py" ] && md5sum "$R/root/finance/order_s778.py" | cut -c1-8 || echo none)"; }
TOP="$(awk '$2=="finance/porders_s454.py"{print substr($1,1,8)}' "$KDIR/TO_PINS.md5") $(awk '$2=="finance/order_s778.py"{print substr($1,1,8)}' "$KDIR/TO_PINS.md5")"

mk; O=$(run DRY=1); P=$(pins)
echo "$O" | grep -q "DRY RUN: every gate" && [ "$P" = "cd2feeb3 none" ] && { echo "GREEN 1 dry: green, nothing written"; OK=$((OK+1)); } || { echo "RED 1 dry"; echo "$O" | tail -8; echo "pins: $P"; }

mk; echo "# a change" >> "$R/root/finance/porders_s454.py"; O=$(run)
echo "$O" | grep -q "\[2/6\].*changed after this kit was built" && [ ! -d "$R/lock" ] && [ ! -e "$R/root/finance/order_s778.py" ] && { echo "GREEN 2 a changed live file: stopped at [2/6], nothing placed, lock released"; OK=$((OK+1)); } || { echo "RED 2"; echo "$O" | tail -4; }

mk; O=$(run); P=$(pins)
echo "$O" | grep -q "S778_ORDER_SCREEN: DONE" && [ "$P" = "$TOP" ] && ls "$R/root/finance/"porders_s454.py.bak_S778_cd2feeb3 >/dev/null 2>&1 && [ ! -d "$R/lock" ] \
  && { echo "GREEN 3 install: both files at TO, the backup, lock released"; OK=$((OK+1)); } || { echo "RED 3"; echo "$O" | tail -8; echo "pins $P / $TOP"; }

O=$(run); echo "$O" | grep -q "ALREADY INSTALLED" && { echo "GREEN 4 again: already installed, nothing written"; OK=$((OK+1)); } || { echo "RED 4"; echo "$O" | tail -3; }

mk; O=$(run REHEARSE_RED_AT=6); P=$(pins)
echo "$O" | grep -q "RED after placing" && [ "$P" = "cd2feeb3 none" ] && [ ! -d "$R/lock" ] && { echo "GREEN 5 a red at [6/6]: porders_s454.py put back, order_s778.py removed, lock released"; OK=$((OK+1)); } || { echo "RED 5"; echo "$O" | tail -6; echo "pins: $P"; }
rm -rf "${R:?}" "$R.sysctl" "$R.health"
echo "REHEARSAL S778 $OK/5"
