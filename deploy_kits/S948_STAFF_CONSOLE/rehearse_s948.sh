#!/bin/bash
# rehearse_s948.sh -- S948_STAFF_CONSOLE: the installer on a MADE-UP root (stub systemctl / health / journal), every path.
#   bash rehearse_s948.sh <kit dir> <dir holding the FROM calls_console.py, tile_grants.json, ring_outcome.py, ring_common.py> <python with flask>
set -u
KD="$(cd "$1" && pwd)"; FROMD="$(cd "$2" && pwd)"; PY="$3"
W="$(mktemp -d /tmp/s948_reh.XXXXXX)"; PASS=0; FAIL=0
m5() { if [ -f "$1" ]; then md5sum "$1" | awk '{print $1}'; else echo ABSENT; fi; }
to_of() { awk -v f="to/$1" '$2==f{print $1}' "$KD/TO_PINS.md5"; }
CCF=eb13790d1a761fedf6d5b0e2faa37d50; TGF=8299e8d44b5938343d2a2c66315f3f67
fresh() { rm -rf "$W/r"; mkdir -p "$W/r/portal" "$W/r/deploy/_off" "$W/bin"
  \cp "$FROMD"/calls_console.py "$FROMD"/tile_grants.json "$FROMD"/ring_outcome.py "$FROMD"/ring_common.py "$W/r/portal/"
  chmod 755 "$W/r/portal/calls_console.py"; chmod 644 "$W/r/portal/tile_grants.json"
  rm -rf "$W/kit"; \cp -rp "$KD" "$W/kit"
  printf '#!/bin/bash\necho "$@" >> %s/sysctl.log\n' "$W" > "$W/bin/sysctl"
  printf '#!/bin/bash\ncase "$1" in /portal/health) echo 200;; /portal/console/staff*) [ -f %s/r/portal/calls_staff.py ] && [ ! -e %s/r/STAFF404 ] && echo 302 || echo 404;; *) echo 302;; esac\n' "$W" "$W" > "$W/bin/hget"
  printf '#!/bin/bash\n[ -e %s/r/JOURNAL_BAD ] && echo "calls_staff NOT mounted: boom"; true\n' "$W" > "$W/bin/jr"
  printf '#!/bin/bash\n[ -f %s/r/portal/calls_staff.py ] && [ ! -e %s/r/IMPORT_BAD ] && echo "IMPORT OK" || echo "AssertionError"\n' "$W" "$W" > "$W/bin/ic"
  chmod +x "$W/bin/"*; : > "$W/sysctl.log"; }
run() { ROOT="$W/r" PD="$W/r/portal" APY="$PY" LOCK="$W/r/deploy/lock" OFFSW="$W/r/deploy/_off/DOCTOR_AUTO_OFF" SYSTEMCTL="$W/bin/sysctl" \
  HEALTH_CMD="$W/bin/hget" JOURNAL_CMD="$W/bin/jr" IMPORT_CHECK_CMD="$W/bin/ic" NAP=0 bash "$W/kit/install_S948_STAFF_CONSOLE.sh" "$@" 2>&1; }
chk() { if eval "$2"; then PASS=$((PASS+1)); echo "  ok   $1"; else FAIL=$((FAIL+1)); echo "  FAIL $1"; echo "$OUT" | tail -6 | sed 's/^/        /'; fi; }
isfrom() { [ "$(m5 "$W/r/portal/calls_console.py")" = $CCF ] && [ "$(m5 "$W/r/portal/tile_grants.json")" = $TGF ] && [ ! -f "$W/r/portal/calls_staff.py" ]; }
isto() { for n in calls_console.py tile_grants.json calls_staff.py; do [ "$(m5 "$W/r/portal/$n")" = "$(to_of $n)" ] || return 1; done; }
clean() { [ ! -e "$W/r/deploy/lock" ] && [ ! -e "$W/r/deploy/_off/DOCTOR_AUTO_OFF" ] && [ -z "$(ls -A "$W/r/portal" | grep '\.s948$')" ] && [ -z "$(ls /tmp | grep '^s948_inst\.' )" ]; }
fresh; OUT="$(DRY=1 run)"; chk "DRY: nothing changed" 'echo "$OUT" | grep -q "DRY ok" && isfrom && clean && [ ! -s "$W/sysctl.log" ]'
OUT="$(run)"; chk "install: INSTALLED, three files at TO, restarted" 'echo "$OUT" | grep -q "INSTALLED" && isto && grep -q "restart clinic-portal" "$W/sysctl.log" && clean'
chk "backups 0600 read as FROM, modes kept" '[ "$(m5 "$W/r/portal/calls_console.py.bak_S948_eb13790d")" = $CCF ] && [ "$(stat -c %a "$W/r/portal/calls_console.py.bak_S948_eb13790d")" = 600 ] && [ "$(stat -c %a "$W/r/portal/calls_console.py")" = 755 ] && [ "$(stat -c %a "$W/r/portal/tile_grants.json")" = 644 ]'
OUT="$(run)"; chk "again: ALREADY" 'echo "$OUT" | grep -q "ALREADY" && isto && clean'
OUT="$(run --undo)"; chk "--undo: back to FROM, calls_staff moved aside" 'echo "$OUT" | grep -q "UNDONE" && isfrom && ls "$W/r/portal" | grep -q "calls_staff.py.bak_S948_off_" && clean'
OUT="$(run --undo)"; chk "--undo twice: not installed" 'echo "$OUT" | grep -q "not installed" && isfrom'
OUT="$(run)"; chk "re-install after undo" 'echo "$OUT" | grep -q "INSTALLED" && isto && clean'
echo x >> "$W/r/portal/calls_console.py"; OUT="$(run --undo)"; chk "--undo refuses a later kit's file" 'echo "$OUT" | grep -q "not S948" && clean'
fresh; OUT="$(FORCE_RED_AT=4 run)"; chk "forced red at [4/5]: put back, restarted" 'echo "$OUT" | grep -q "RED" && isfrom && grep -q restart "$W/sysctl.log" && clean'
fresh; OUT="$(FORCE_RED_AT=5 run)"; chk "forced red at [5/5]: put back" 'echo "$OUT" | grep -q "RED" && isfrom && clean'
fresh; OUT="$(FORCE_KILL_AT=4:calls_staff.py run)"; chk "killed mid-[4/5]: put back" 'echo "$OUT" | grep -q "ended before its proof" && isfrom && clean'
fresh; touch "$W/r/JOURNAL_BAD"; OUT="$(run)"; chk "journal says NOT mounted: put back" 'echo "$OUT" | grep -q "NOT mounted" && isfrom && clean'
fresh; touch "$W/r/IMPORT_BAD"; OUT="$(run)"; chk "the portal import lacks the routes: put back, before any restart" 'echo "$OUT" | grep -q "lacks the staff routes" && isfrom && clean'
fresh; touch "$W/r/STAFF404"; OUT="$(run)"; chk "the staff page answers 404: put back" 'echo "$OUT" | grep -q "answered 404" && isfrom && clean'
fresh; mkdir "$W/r/deploy/lock"; OUT="$(run)"; chk "the build lock held: stops, nothing changed" 'echo "$OUT" | grep -q "another build holds" && isfrom && [ ! -e "$W/r/deploy/_off/DOCTOR_AUTO_OFF" ]'
fresh; echo " " >> "$W/r/portal/tile_grants.json"; OUT="$(run)"; chk "a drifted live file: stops at [2/5]" 'echo "$OUT" | grep -q "\[2/5\].*changed after" && [ "$(m5 "$W/r/portal/calls_console.py")" = $CCF ] && clean'
fresh; \cp "$KD/to/calls_staff.py" "$W/r/portal/"; OUT="$(run)"; chk "only part in place: stops" 'echo "$OUT" | grep -q "only part" && [ "$(m5 "$W/r/portal/calls_console.py")" = $CCF ]'
fresh; echo "# x" >> "$W/kit/to/calls_staff.py"; OUT="$(run)"; chk "a corrupt kit: stops at [1/5]" 'echo "$OUT" | grep -q "\[1/5\]" && isfrom'
rm -rf "$W"
echo "REHEARSAL: $PASS/$((PASS+FAIL)) $([ $FAIL = 0 ] && echo PASS || echo FAIL)"
[ $FAIL = 0 ]
