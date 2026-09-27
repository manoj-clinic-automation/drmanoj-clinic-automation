#!/bin/bash
# install_S429_MONTHLY_PIN_GUARD.sh -- session 284, 27-Sep-2026 -- F-649: the monthly "keep forever" backup copy
# closed its month even when Drive refused the pin, so that month could end with no pinned copy. Now only a
# CONFIRMED pin closes the month; otherwise the next night retries. ONE anchored edit on exact bytes to
# /root/state_backup/clinic_state_backup.py (S424 ede26d98); no service to restart (cron 01:50).
set -u
KIT="S429_MONTHLY_PIN_GUARD"; KDIR="$(cd "$(dirname "$0")" && pwd)"; VPY="${VPY:-/root/wa/venv/bin/python3}"
F="${F:-/root/state_backup/clinic_state_backup.py}"; FROM=ede26d98a6aaf36188a797d732f4a4d7; TO=0e841f3569f6e00f92fdc99031ed1242
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }; say() { echo "$@"; }
cd "$KDIR" || exit 1
say "[1/5] kit gates"
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit"; exit 1; }
say "      green"
[ "$(m5 "$F")" = "$TO" ] && { say "-- ALREADY INSTALLED. Nothing to do."; exit 0; }
say "[2/5] live pin"
[ "$(m5 "$F")" = "$FROM" ] || { say "!! [2/5] live clinic_state_backup.py is $(m5 "$F"), not the S424 bytes $FROM - nothing installed"; exit 1; }
say "      exact (S424)"
say "[3/5] scratch: patch a copy + the walk"
W="/tmp/s429_walk_$(date +%Y%m%d_%H%M%S)"; mkdir -p "$W" && \cp -p "$F" "$W/orig.py" && \cp -p "$F" "$W/csb.py" || { say "!! [3/5] scratch copy failed"; exit 1; }
"$VPY" -B apply_s429.py "$W/csb.py" >/dev/null && [ "$(m5 "$W/csb.py")" = "$TO" ] || { say "!! [3/5] the patched copy is not the predicted bytes - nothing installed"; rm -rf "$W"; exit 1; }
"$VPY" -B -m py_compile "$W/csb.py" || { say "!! [3/5] py_compile failed"; rm -rf "$W"; exit 1; }
WOUT="$( cd /tmp && timeout 120 "$VPY" -B "$KDIR/walk_s429.py" "$W/orig.py" "$W/csb.py" 2>&1 | tail -1 )"; rm -rf "$W"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [3/5] walk red: $WOUT - nothing installed"; exit 1; }
say "      $WOUT"
say "[4/5] backup + place"
BAK="$F.bak_S429_ede26d98"; \cp -p "$F" "$BAK" || { say "!! [4/5] backup failed"; exit 1; }
"$VPY" -B apply_s429.py "$F" | sed 's/^/      /'
[ "$(m5 "$F")" = "$TO" ] || { \cp -p "$BAK" "$F"; say "!! [4/5] placed bytes wrong - restored"; exit 1; }
say "[5/5] the placed file loads (import only, nothing run)"
"$VPY" -B -c "import importlib.util as u; s=u.spec_from_file_location('csb','$F'); m=u.module_from_spec(s); s.loader.exec_module(m); print('      loads · monthly slot', m.MONTHLY)" || { \cp -p "$BAK" "$F"; say "!! [5/5] the placed file does not load - restored"; exit 1; }
say "      all green -- $KIT: DONE (the 1-Oct 01:50 run is the first that uses it)"
say "      backup: $BAK"
md5sum "$F"
