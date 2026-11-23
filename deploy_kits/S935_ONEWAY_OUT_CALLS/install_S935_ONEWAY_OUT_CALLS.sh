#!/bin/bash
# =============================================================================
#  install_S935_ONEWAY_OUT_CALLS.sh · kit S935 (the parent, S498, 23-Nov-2026) · his 11:09 word
#  Alisha's follow-up calls, dialled from her own MyOperator app, never reached the Call Console: the call hook kept
#  only incoming calls and the Callback Tracker's own dialler calls; MyOperator reports an app call as
#  category 'oneway', direction 'outgoing', and the hook set those aside (raw log only) since July.
#   1. /root/wa/call-hook/call_hook_capture.py 2d25fe7b -> TO  keeps them as one row "OUT-<session>" with the patient's number
#   2. /root/wa/portal_console.py              a8d050ef -> TO  counts category 'oneway' as Out
#   3. once, after the restart: backfill_call_durations.py adds every such call already in the raw logs (insert-only)
#  call-hook restarted (the doctor's auto-fix paused for it). The Call Console picks them up at its next 10-minute reading.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s935kit && cp -rp /root/deploy/repo/deploy_kits/S935_ONEWAY_OUT_CALLS /tmp/s935kit && bash /tmp/s935kit/install_S935_ONEWAY_OUT_CALLS.sh
#  DRY=1 before bash: every gate, the walk and the backfill's own dry run (counts); nothing live changes.
#  --undo: the two files back, call-hook restarted (rows already added stay: they are real calls).
# =============================================================================
set -u
KIT="S935_ONEWAY_OUT_CALLS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; WA="$ROOT/wa"; HK="$WA/call-hook"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
SVC="${SVC:-call-hook}"; HPORT="${HPORT:-8098}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
RAWD="${RAWD:-$HK/call_hook_logs}"
NAMES="call_hook_capture.py portal_console.py"
dir_of() { case "$1" in call_hook_capture.py) echo "$HK";; portal_console.py) echo "$WA";; esac; }
from_of() { case "$1" in call_hook_capture.py) echo 2d25fe7b93dd82dd8eab164d8459acbe;; portal_console.py) echo a8d050ef8c9e78b57467b58a68789841;; esac; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
live() { echo "$(dir_of "$1")/$1"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s935_inst_$STAMP"; TOOK_LOCK=0; OFF_MINE=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
isfrom() { [ "$(m5 "$(live "$1")")" = "$(from_of "$1")" ]; }
say() { echo "$@"; }
bak() { echo "$(live "$1").bak_S935_$(from_of "$1" | cut -c1-8)"; }
hz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$HPORT/"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(hz); [ "$h" = 200 ] && break; done; echo "$h"; }
jlog() { if [ -n "${JOURNAL_CMD:-}" ]; then $JOURNAL_CMD; else journalctl -u "$SVC" --since "$1" --no-pager 2>/dev/null; fi; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES; do rm -f "$(dir_of "$n")/.$n.s935"; done; release; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release; exit 1; }
pause_doctor() { if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi; }
restore() { say "!! RED after placing ($1) - putting the files back"
  for n in $NAMES; do [ -f "$(bak "$n")" ] && \cp -p "$(bak "$n")" "$(live "$n")"; done
  "$SYSTEMCTL" restart "$SVC" || true
  for n in $NAMES; do say "   $n $(m5 "$(live "$n")" | cut -c1-8) (expected $(from_of "$n" | cut -c1-8))"; done
  say "   $SVC restarted, its health $(wait200). Send a photo of this screen to Claude."; release; exit 1; }
pyv() { (cd "$SCR" && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 600 "$VPY" -W ignore -B "$@" 2>&1); }

if [ "${1:-}" = "--undo" ]; then
  U=1; for n in $NAMES; do isfrom "$n" || U=0; done
  [ "$U" = 1 ] && { say "-- $KIT is not installed - nothing to undo."; exit 0; }
  for n in $NAMES; do isfrom "$n" || [ "$(m5 "$(live "$n")")" = "$(to_of "$n")" ] || { say "!! $(live "$n") is $(m5 "$(live "$n")" | cut -c1-8), not this kit's - nothing undone. Tell Claude."; exit 1; }; done
  for n in $NAMES; do isfrom "$n" && continue; b=$(bak "$n"); [ -f "$b" ] && [ "$(m5 "$b")" = "$(from_of "$n")" ] || { say "!! no good backup $b - nothing undone"; exit 1; }; done
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo" > "$LOCK/owner"; pause_doctor
  for n in $NAMES; do isfrom "$n" || \cp -p "$(bak "$n")" "$(live "$n")"; done; "$SYSTEMCTL" restart "$SVC"
  h=$(wait200); release
  [ "$h" = 200 ] || { say "!! UNDONE but $SVC health is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE (two files back; $SVC restarted, health 200; the rows already added stay -- they are real calls)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
ALL=1; for n in $NAMES; do [ "$(m5 "$(live "$n")")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do isfrom "$n" || stop "!! [2/5] $(live "$n") is $(m5 "$(live "$n")" | cut -c1-8), expected $(from_of "$n" | cut -c1-8) - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
[ -f "$HK/backfill_call_durations.py" ] && [ -d "$RAWD" ] || stop "!! [2/5] $HK/backfill_call_durations.py or $RAWD is not there - nothing installed"
# the kit carries no copy of the two files (their own selftest fixtures hold 10-digit made-up numbers the repo refuses):
# make_s935.py patches the LIVE bytes (FROM pinned, exact anchors) and the result must equal the TO pins.
mkdir -p "$SCR/new" "$SCR/live" "$SCR/bf" || stop "!! [2/5] could not make the scratch folders - nothing installed"
for n in $NAMES; do \cp -p "$(live "$n")" "$SCR/live/$n" || stop "!! [2/5] could not copy $n - nothing installed"; done
MK=$(pyv "$KDIR/make_s935.py" "$SCR/live/call_hook_capture.py" "$SCR/live/portal_console.py" "$SCR/new")
for n in $NAMES; do [ "$(m5 "$SCR/new/$n")" = "$(to_of "$n")" ] || { echo "$MK" | tail -2 | sed 's/^/      /'; stop "!! [2/5] the patch of $n did not give its TO pin - nothing installed"; }; done
for n in $NAMES; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$VPY" -W ignore -m py_compile "$SCR/new/$n" || stop "!! [2/5] $n does not compile on $VPY - nothing installed"; done
say "[2/5] the live pins exact; both files patched to their TO pins and compile"
{ \cp -p "$SCR/new/call_hook_capture.py" "$SCR/bf/" && \cp -p "$HK/backfill_call_durations.py" "$SCR/bf/"; } || stop "!! [3/5] could not lay out the backfill's dry run - nothing installed"
R1=$(pyv "$KDIR/walk_s935.py" "$SCR/new/call_hook_capture.py" "$SCR/new/portal_console.py" | tail -1)
[ "$R1" = "WALK 23/23" ] || { pyv "$KDIR/walk_s935.py" "$SCR/new/call_hook_capture.py" "$SCR/new/portal_console.py" | grep RED | head -6; stop "!! [3/5] walk_s935 on the new files: $R1 - nothing installed"; }
R1c=$(pyv "$KDIR/walk_s935.py" "$SCR/live/call_hook_capture.py" "$SCR/live/portal_console.py" | tail -1)
case "$R1c" in "WALK 23/23") stop "!! [3/5] walk_s935's control (the live files) did not go red - nothing installed";; "WALK "*) ;;
  *) stop "!! [3/5] walk_s935's control did not finish ($R1c) - nothing installed";; esac
S1=$(cd "$SCR/new" && TMPDIR="$SCR" CALLHOOK_RAW_LOG_DIR="$SCR/raw" CALLHOOK_REJECT_DIR="$SCR/rej" timeout 120 "$VPY" -W ignore -B call_hook_capture.py --selftest 2>&1 | tail -1)
case "$S1" in "selftest: "*) x="${S1#selftest: }"; x="${x% passed}"; [ "${x%/*}" = "${x#*/}" ] || stop "!! [3/5] the hook's own selftest on the new file: $S1 - nothing installed";; *) stop "!! [3/5] the hook's own selftest did not finish ($S1) - nothing installed";; esac
S2=$(pyv "$SCR/new/portal_console.py" --selftest | grep -E "^SELFTEST" | tail -1)
case "$S2" in "SELFTEST PASSED"*) ;; *) stop "!! [3/5] the console builder's own selftest on the new file: $S2 - nothing installed";; esac
BF=$(cd "$SCR/bf" && TMPDIR="$SCR" CALLHOOK_RAW_LOG_DIR="$RAWD" CALLHOOK_REJECT_DIR="$SCR/rej" TZ=Asia/Kolkata timeout 300 "$VPY" -W ignore -B backfill_call_durations.py --dry-run 2>&1)
echo "$BF" | grep -q "^DRY RUN: nothing written" || { echo "$BF" | grep -v "would insert" | tail -4 | sed 's/^/      /'; stop "!! [3/5] the backfill's dry run (new hook) did not finish - nothing installed"; }
say "[3/5] walk_s935 $R1 (control red: $R1c); the hook's selftest $S1; the console's selftest passed; the backfill's dry run with the new hook:"
echo "$BF" | grep -E "^raw logs:|^already in tab:" | sed 's/^/      /'
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the backfill's dry run green; nothing live changed"; exit 0; fi
h0=$(hz); [ "$h0" = 200 ] || stop "!! [4/5] $SVC health $h0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$(live "$n")" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
for n in $NAMES; do st="$(dir_of "$n")/.$n.s935"; { cat "$SCR/new/$n" > "$st" && chmod --reference="$(live "$n")" "$st" 2>/dev/null; chown --reference="$(live "$n")" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
pause_doctor
T0="$(date '+%Y-%m-%d %H:%M:%S')"
for n in portal_console.py call_hook_capture.py; do mv -f "$(dir_of "$n")/.$n.s935" "$(live "$n")" || restore "the rename of $n"; done
for n in $NAMES; do [ "$(m5 "$(live "$n")")" = "$(to_of "$n")" ] || restore "read back of $n"; done
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
h1=$(wait200); [ "$h1" = 200 ] || restore "$SVC health $h1 after the restart"
ML=""; for _t in 1 2 3 4 5; do jlog "$T0" | grep -q "receiver v3.3" && { ML=ok; break; }; sleep "${NAP:-3}"; done
[ "$ML" = ok ] || restore "the service log does not show the new receiver (v3.3) started"
say "[4/5] placed and read back: two files at their TO pins; $SVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), health $h1, the log shows receiver v3.3"
BL=$(cd "$HK" && TMPDIR="$SCR" TZ=Asia/Kolkata timeout 600 "$VPY" -W ignore -B backfill_call_durations.py 2>&1)
release
if echo "$BL" | grep -q "^inserted "; then
  say "[5/5] the calls already in the raw logs added (insert-only):"; echo "$BL" | grep -E "^raw logs:|^already in tab:|^inserted " | sed 's/^/      /'
else say "[5/5] !! the code is live, but the one-time backfill did not finish -- send a photo of this screen to Claude:"; echo "$BL" | grep -v "would insert" | tail -4 | sed 's/^/      /'; fi
say "      undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""; say "$KIT: DONE. The Call Console counts them at its next reading (within 10 minutes): https://followup.dr-manoj.in/portal/console"; exit 0
