#!/bin/bash
# rehearse_s951.sh -- S951_YESTERDAY_CARRY: the installer on a MADE-UP root (stub systemctl / health / journal), every path.
#   bash rehearse_s951.sh <kit dir> <dir holding the FROM calls_staff.py, calls_console.py, ring_outcome.py, ring_common.py> <python with flask>
set -u
KD="$(cd "$1" && pwd)"; FROMD="$(cd "$2" && pwd)"; PY="$3"
W="$(mktemp -d /tmp/s951_reh.XXXXXX)"; PASS=0; FAIL=0
m5() { if [ -f "$1" ]; then md5sum "$1" | awk '{print $1}'; else echo ABSENT; fi; }
TO="$(awk '$2=="to/calls_staff.py"{print $1}' "$KD/TO_PINS.md5")"; FR=05caf1c32db2e25b7b0723292c234572
fresh() { rm -rf "$W/r"; mkdir -p "$W/r/portal" "$W/r/deploy/_off" "$W/bin"
  \cp "$FROMD"/calls_staff.py "$FROMD"/calls_console.py "$FROMD"/ring_outcome.py "$FROMD"/ring_common.py "$W/r/portal/"
  chmod 644 "$W/r/portal/calls_staff.py"
  rm -rf "$W/kit"; \cp -rp "$KD" "$W/kit"
  printf '#!/bin/bash\necho "$@" >> %s/sysctl.log\n' "$W" > "$W/bin/sysctl"
  printf '#!/bin/bash\ncase "$1" in /portal/health) echo 200;; /portal/console/staff*) [ ! -e %s/r/STAFF404 ] && echo 302 || echo 404;; *) echo 302;; esac\n' "$W" > "$W/bin/hget"
  printf '#!/bin/bash\n[ -e %s/r/JOURNAL_BAD ] && echo "calls_staff NOT mounted: boom"; true\n' "$W" > "$W/bin/jr"
  chmod +x "$W/bin/"*; : > "$W/sysctl.log"; }
run() { ROOT="$W/r" PD="$W/r/portal" APY="$PY" LOCK="$W/r/deploy/lock" OFFSW="$W/r/deploy/_off/DOCTOR_AUTO_OFF" SYSTEMCTL="$W/bin/sysctl" \
  HEALTH_CMD="$W/bin/hget" JOURNAL_CMD="$W/bin/jr" NAP=0 bash "$W/kit/install_S951_YESTERDAY_CARRY.sh" "$@" 2>&1; }
chk() { if eval "$2"; then PASS=$((PASS+1)); echo "  ok   $1"; else FAIL=$((FAIL+1)); echo "  FAIL $1"; echo "$OUT" | tail -6 | sed 's/^/        /'; fi; }
isfrom() { [ "$(m5 "$W/r/portal/calls_staff.py")" = $FR ]; }
isto() { [ "$(m5 "$W/r/portal/calls_staff.py")" = "$TO" ]; }
clean() { [ ! -e "$W/r/deploy/lock" ] && [ ! -e "$W/r/deploy/_off/DOCTOR_AUTO_OFF" ] && [ -z "$(ls -A "$W/r/portal" | grep '\.s951$')" ] && [ -z "$(ls /tmp | grep '^s951_inst\.' )" ]; }
fresh; OUT="$(DRY=1 run)"; chk "DRY: runs [1]-[3], nothing changed" 'echo "$OUT" | grep -q "DRY ok" && isfrom && clean && [ ! -s "$W/sysctl.log" ]'
OUT="$(run)"; chk "install: INSTALLED, TO, restarted" 'echo "$OUT" | grep -q "INSTALLED" && isto && grep -q "restart clinic-portal" "$W/sysctl.log" && clean'
chk "backup 0600 reads as FROM, mode kept" '[ "$(m5 "$W/r/portal/calls_staff.py.bak_S951_05caf1c3")" = $FR ] && [ "$(stat -c %a "$W/r/portal/calls_staff.py.bak_S951_05caf1c3")" = 600 ] && [ "$(stat -c %a "$W/r/portal/calls_staff.py")" = 644 ]'
OUT="$(run)"; chk "again: ALREADY" 'echo "$OUT" | grep -q "ALREADY" && isto && clean'
OUT="$(run --undo)"; chk "--undo: back to FROM" 'echo "$OUT" | grep -q "UNDONE" && isfrom && clean'
OUT="$(run --undo)"; chk "--undo twice: not installed" 'echo "$OUT" | grep -q "not installed" && isfrom'
OUT="$(run)"; chk "re-install after undo" 'echo "$OUT" | grep -q "INSTALLED" && isto && clean'
echo x >> "$W/r/portal/calls_staff.py"; OUT="$(run --undo)"; chk "--undo refuses a later kit's file" 'echo "$OUT" | grep -q "not S951" && clean'
fresh; OUT="$(FORCE_RED_AT=4 run)"; chk "forced red at [4/5]: put back, restarted" 'echo "$OUT" | grep -q "RED" && isfrom && grep -q restart "$W/sysctl.log" && clean'
fresh; OUT="$(FORCE_RED_AT=5 run)"; chk "forced red at [5/5]: put back" 'echo "$OUT" | grep -q "RED" && isfrom && clean'
fresh; OUT="$(FORCE_KILL_AT=4 run)"; chk "killed mid-[4/5]: put back" 'echo "$OUT" | grep -q "ended before its proof" && isfrom && clean'
fresh; touch "$W/r/JOURNAL_BAD"; OUT="$(run)"; chk "journal says NOT mounted: put back" 'echo "$OUT" | grep -q "NOT mounted" && isfrom && clean'
fresh; touch "$W/r/STAFF404"; OUT="$(run)"; chk "the staff page answers 404: put back" 'echo "$OUT" | grep -q "answered 404" && isfrom && clean'
fresh; mkdir "$W/r/deploy/lock"; OUT="$(run)"; chk "the build lock held: stops, nothing changed" 'echo "$OUT" | grep -q "another build holds" && isfrom && [ ! -e "$W/r/deploy/_off/DOCTOR_AUTO_OFF" ]'
fresh; echo "# drift" >> "$W/r/portal/calls_staff.py"; OUT="$(run)"; chk "a drifted live file: stops at [2/5]" 'echo "$OUT" | grep -q "\[2/5\].*changed after" && clean'
fresh; echo "# x" >> "$W/kit/to/calls_staff.py"; OUT="$(run)"; chk "a corrupt kit: stops at [1/5]" 'echo "$OUT" | grep -q "\[1/5\]" && isfrom'
fresh; \cp "$KD/../mut/calls_staff.py" "$W/kit/to/calls_staff.py" 2>/dev/null; if [ -f "$KD/../mut/calls_staff.py" ]; then (cd "$W/kit" && sed -i "s#^[0-9a-f]\{32\}  to/calls_staff.py#$(m5 "$W/kit/to/calls_staff.py")  to/calls_staff.py#" TO_PINS.md5 && md5sum KIT_ID.txt TO_PINS.md5 install_S951_YESTERDAY_CARRY.sh make_s951.py rehearse_s951.sh walk_s948.py walk_s951.py to/calls_staff.py | sed 's#  #  ./#' > SUMS.md5); OUT="$(run)"; chk "a kit whose TO is not what make_s951 makes: stops at [3/5]" 'echo "$OUT" | grep -q "\[3/5\]" && isfrom && clean'; fi
rm -rf "$W"
echo "REHEARSAL: $PASS/$((PASS+FAIL)) $([ $FAIL = 0 ] && echo PASS || echo FAIL)"
[ $FAIL = 0 ]
