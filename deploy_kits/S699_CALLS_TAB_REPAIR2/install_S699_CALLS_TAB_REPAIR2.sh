#!/bin/bash
# =============================================================================
#  install_S699_CALLS_TAB_REPAIR2.sh · kit S699 (02-Nov-2026, the parent, session 379) · F-1083, the second run of the tab's repair.
#  The first run (S698, 11:13 IST) rebuilt the region, then its own check found 15 keys twice -- calls of 12-Jul that the raw log
#  holds AND that already sat in the rows above the region -- and put the original rows back. v2 of the tool keeps a call that is
#  already above the region where it is. ONE file: /root/wa/call-hook/repair_call_durations_s698.py 27609eb5 -> TO (the kit's).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s699kit && cp -rp /root/deploy/repo/deploy_kits/S699_CALLS_TAB_REPAIR2 /tmp/s699kit && bash /tmp/s699kit/install_S699_CALLS_TAB_REPAIR2.sh
#  ORDER: gates -> the live pin -> compile + the tool's selftest -> backup + place -> the dry run (the plan, counts) -> the apply
#  (CSV backup first, verified, restored by the tool on a failure) -> call-hook restarted (its row index) -> console.db rebuilt once.
#  The tool's output is kept whole in /root/wa/call-hook/backups/repair_S699_<stamp>.log; the screen shows its summary lines.
# =============================================================================
set -u
KIT="S699_CALLS_TAB_REPAIR2"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; WA="$ROOT/wa"; HK="$WA/call-hook"
TOOL="repair_call_durations_s698.py"; LIVE="$HK/$TOOL"
FROM="27609eb5b2c5690d808eb2522c4849c5"
TO="$(awk -v f="$TOOL" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
HSVC="${HSVC:-call-hook}"; HPORT="${HPORT:-8098}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
CRON_LOCK="${CRON_LOCK:-$WA/console_cron.lock}"
STAMP="$(date +%Y%m%d_%H%M%S)"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
halive() { curl -s -m 8 "http://127.0.0.1:$HPORT/" 2>/dev/null | grep -q "alive" && echo alive || echo down; }
waitalive() { local h=down; for _t in 1 2 3 4 5 6 7 8; do sleep 2; h=$(halive); [ "$h" = alive ] && break; done; echo "$h"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${SKIP_WINDOW:-0}" = 1 ] || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/6] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing done"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing done"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing done"; exit 1; }
[ -n "$TO" ] && [ "$(m5 "$KDIR/$TOOL")" = "$TO" ] || { say "!! [1/6] the kit's $TOOL is not at its TO pin - nothing done"; exit 1; }
[ -f "$LIVE" ] || { say "!! [1/6] $LIVE is missing (S698 not installed?) - nothing done"; exit 1; }
[ -f "$HK/call_hook_capture.py" ] && grep -q "receiver v3.2" "$HK/call_hook_capture.py" || { say "!! [1/6] the receiver on the box is not v3.2 (S698 not installed?) - nothing done"; exit 1; }
say "[1/6] kit gates green (SUMS, KIT_ID, the window, the receiver v3.2 in place)"
C="$(m5 "$LIVE")"
if [ "$C" = "$TO" ]; then say "[2/6] the tool is already v2 ($TO) - placing skipped"
elif [ "$C" = "$FROM" ]; then say "[2/6] live pin exact: $TOOL ${FROM:0:8}"
else say "!! [2/6] $LIVE is ${C:0:8}, expected ${FROM:0:8} or the kit's - STOP, nothing done. Tell Claude."; exit 1; fi
for py in "$APY" "$VPY"; do "$py" -m py_compile "$KDIR/$TOOL" 2>/dev/null || { say "!! [3/6] $TOOL does not compile on $py - nothing done"; exit 1; }; done
S3="$(cd "$KDIR" && timeout 120 "$VPY" -B "$TOOL" --selftest 2>&1 | tail -1)"
[ "$S3" = "selftest: PASSED" ] || { say "!! [3/6] the tool's selftest: $S3 - nothing done"; exit 1; }
say "[3/6] compiles on both pythons; selftest PASSED"
if [ "${DRY:-0}" = 1 ]; then say "[4/6] DRY RUN: nothing placed (the plan below runs the kit's copy of the tool)"; RUNTOOL="$KDIR/$TOOL"
elif [ "$C" = "$FROM" ]; then
  B="$LIVE.bak_S699_${FROM:0:8}"
  { \cp -p "$LIVE" "$B" && [ "$(m5 "$B")" = "$FROM" ]; } || { say "!! [4/6] could not write the backup $B - nothing placed"; exit 1; }
  STG="$HK/.$TOOL.s699"
  { cat "$KDIR/$TOOL" > "$STG" && [ "$(m5 "$STG")" = "$TO" ]; } || { rm -f "$STG"; say "!! [4/6] could not stage $TOOL - nothing placed"; exit 1; }
  chmod --reference="$LIVE" "$STG" 2>/dev/null; chown --reference="$LIVE" "$STG" 2>/dev/null
  mv -f "$STG" "$LIVE" || { say "!! [4/6] the rename failed - the live file is unchanged"; exit 1; }
  [ "$(m5 "$LIVE")" = "$TO" ] || { \cp -p "$B" "$LIVE"; say "!! [4/6] read back wrong - put back from $B"; exit 1; }
  chmod 700 "$LIVE" 2>/dev/null
  say "[4/6] placed and read back: $TOOL ${TO:0:8} (backup $B)"
else say "[4/6] nothing to place"; fi
mkdir -p "$HK/backups"; L="$HK/backups/repair_S699_$STAMP.log"
FILT='FutureWarning|warnings.warn|^\[call_hook_capture\]|^  20[0-9][0-9]-'
RD="$(cd "$HK" && timeout 600 "$VPY" -B "${REPAIR_PY:-${RUNTOOL:-$LIVE}}" --dry-run --force --hook "$HK/call_hook_capture.py" 2>&1 | tee -a "$L")"
printf '%s\n' "$RD" | grep -v -E "$FILT" | sed 's/^/      /'
printf '%s\n' "$RD" | grep -q "DRY RUN: nothing written" || { say "!! [5/6] the dry run did not finish its plan - nothing applied. Tell Claude."; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: the plan above; NOTHING applied"; exit 0; fi
RP="$(cd "$HK" && timeout 900 "$VPY" -B "${REPAIR_PY:-$LIVE}" --apply --force 2>&1 | tee -a "$L")"
printf '%s\n' "$RP" | grep -v -E "$FILT" | sed 's/^/      /'
"$SYSTEMCTL" restart "$HSVC" || say "!! call-hook could not be restarted - run: systemctl restart call-hook"
h=$(waitalive)
if printf '%s\n' "$RP" | grep -q "VERIFIED"; then say "[5/6] the tab repaired and VERIFIED; call-hook restarted ($h); the log: $L"; RES="the tab repaired and verified"
elif printf '%s\n' "$RP" | grep -q "nothing to repair"; then say "[5/6] the tab needed no repair; call-hook restarted ($h)"; RES="the tab needed no repair"
else say "!! [5/6] THE REPAIR DID NOT VERIFY (the tool put the rows back; see $L). call-hook restarted ($h). Tell Claude."; RES="the repair did not verify -- tell Claude"; fi
if command -v flock >/dev/null 2>&1 && flock -n "$CRON_LOCK" true 2>/dev/null; then
  if (cd "$WA" && timeout 600 flock -n "$CRON_LOCK" "$VPY" "$WA/portal_console.py" --build --with-myop-reconcile --with-transcripts --days 60 >"$HK/backups/build_S699_$STAMP.txt" 2>&1); then
    say "[6/6] console.db rebuilt: $(grep -o 'BUILD complete.*' "$HK/backups/build_S699_$STAMP.txt" | head -1)"
  else say "[6/6] the rebuild did not finish ($(tail -1 "$HK/backups/build_S699_$STAMP.txt")) -- the cron's next run makes it"; fi
else say "[6/6] the console cron is building this moment; its run carries the clean tab"; fi
say ""
say "$KIT: DONE. $RES."
exit 0
