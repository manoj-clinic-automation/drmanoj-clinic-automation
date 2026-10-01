#!/bin/bash
# install_S445_RING_OUTCOMES_BACKUP.sh -- session 287, 01-Oct-2026 -- F-677 / D654: /root/portal/ring_outcomes.db
# (the ring card's store, S419) had no second copy anywhere. ONE anchored edit on exact bytes adds it to the
# encrypted nightly's named files in /root/state_backup/clinic_state_backup.py (S429 0e841f35). No service to
# restart (cron 01:50). The walk runs twice: on a scratch copy with a fake database, then on the REAL database,
# read-only, before anything is placed.
set -u
KIT="S445_RING_OUTCOMES_BACKUP"; KDIR="$(cd "$(dirname "$0")" && pwd)"; VPY="${VPY:-/root/wa/venv/bin/python3}"
F="${F:-/root/state_backup/clinic_state_backup.py}"; DB="${DB:-/root/portal/ring_outcomes.db}"
FROM=0e841f3569f6e00f92fdc99031ed1242; TO=3bf7caea3828c4e2a58227e161feec36
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }; say() { echo "$@"; }
cd "$KDIR" || exit 1
say "[1/5] kit gates"
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit"; exit 1; }
say "      green"
[ "$(m5 "$F")" = "$TO" ] && { say "-- ALREADY INSTALLED. Nothing to do."; exit 0; }
say "[2/5] live pin + the database"
[ "$(m5 "$F")" = "$FROM" ] || { say "!! [2/5] live clinic_state_backup.py is $(m5 "$F"), not the S429 bytes $FROM - nothing installed"; exit 1; }
[ -f "$DB" ] || { say "!! [2/5] $DB is not on the box - nothing installed"; exit 1; }
say "      exact (S429) · database present"
say "[3/5] scratch: patch a copy + the walk (fake db, then the REAL db read-only)"
W="/tmp/s445_walk_$(date +%Y%m%d_%H%M%S)"; mkdir -p "$W" && \cp -p "$F" "$W/orig.py" && \cp -p "$F" "$W/csb.py" || { say "!! [3/5] scratch copy failed"; exit 1; }
"$VPY" -B apply_s445.py "$W/csb.py" >/dev/null && [ "$(m5 "$W/csb.py")" = "$TO" ] || { say "!! [3/5] the patched copy is not the predicted bytes - nothing installed"; rm -rf "$W"; exit 1; }
"$VPY" -B -m py_compile "$W/csb.py" || { say "!! [3/5] py_compile failed"; rm -rf "$W"; exit 1; }
W1="$( cd /tmp && timeout 120 "$VPY" -B "$KDIR/walk_s445.py" "$W/orig.py" "$W/csb.py" 2>&1 | tail -1 )"
W2="$( cd /tmp && timeout 120 "$VPY" -B "$KDIR/walk_s445.py" "$W/orig.py" "$W/csb.py" "$DB" 2>&1 | tail -1 )"; rm -rf "$W"
echo "$W1" | grep -q "^WALK OK" || { say "!! [3/5] walk (fake db) red: $W1 - nothing installed"; exit 1; }
echo "$W2" | grep -q "^WALK OK" || { say "!! [3/5] walk (real db) red: $W2 - nothing installed"; exit 1; }
say "      fake db: $W1 · real db: $W2"
say "[4/5] backup + place"
BAK="$F.bak_S445_0e841f35"; \cp -p "$F" "$BAK" || { say "!! [4/5] backup failed"; exit 1; }
"$VPY" -B apply_s445.py "$F" | sed 's/^/      /'
[ "$(m5 "$F")" = "$TO" ] || { \cp -p "$BAK" "$F"; say "!! [4/5] placed bytes wrong - restored"; exit 1; }
say "[5/5] the placed file loads (import only, nothing run)"
"$VPY" -B -c "import importlib.util as u; s=u.spec_from_file_location('csb','$F'); m=u.module_from_spec(s); s.loader.exec_module(m); assert '/root/portal/ring_outcomes.db' in m.SRC_FILES; print('      loads ·', len(m.SRC_FILES), 'named files, ring_outcomes.db among them')" || { \cp -p "$BAK" "$F"; say "!! [5/5] the placed file does not load - restored"; exit 1; }
say "      all green -- $KIT: DONE (tonight's 01:50 run is the first that carries it)"
say "      backup: $BAK"
md5sum "$F"
