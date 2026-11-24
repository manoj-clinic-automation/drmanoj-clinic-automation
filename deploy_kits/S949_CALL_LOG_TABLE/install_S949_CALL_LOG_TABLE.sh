#!/bin/bash
# =============================================================================
#  install_S949_CALL_LOG_TABLE.sh . kit S949 (the parent, S516, 24-Nov-2026) . roadmap S510 F1, its first half (F1a)
#  The call log on the server: every call the hook puts on the Call_Durations Sheet is written FIRST to the table
#  call_log_raw (/root/wa/calls.db), then to the Sheet exactly as before. Nothing reads the table yet: a nightly compare
#  (23:40) proves table = Sheet on his health page; after three equal nights with calls, F1b moves the console to it.
#   1. /root/wa/call-hook/call_hook_capture.py 70c3d257 -> TO (patched on the box from its live bytes by make_s949.py:
#      the kit carries no copy -- its selftest fixtures hold made-up 10-digit numbers the repository refuses)
#   2. /root/wa/call-hook/call_log_db.py       NEW (the table; the hook its one writer)
#   3. /root/wa/call-hook/call_log_compare.py  NEW + cron 23:40 '# S949_CALL_LOG_COMPARE' (its own flock, the ALL_OFF gate)
#   4. /root/finance/freshness_legs.json       abcb8565 -> TO (one leg appended: 'call log table = sheet')
#  call-hook restarted (about three seconds; the doctor's auto-fix paused for it). Refused in duty hours (Mon-Sat
#  09:00-20:30, Sun 09:00-14:30 IST) so no webhook meets the restart; ANYTIME=1 overrides.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s949kit && cp -rp /root/deploy/repo/deploy_kits/S949_CALL_LOG_TABLE /tmp/s949kit && bash /tmp/s949kit/install_S949_CALL_LOG_TABLE.sh
#  DRY=1 before bash: every gate, the patch, the walk and the selftests; nothing live changes.
#  --undo: the hook and the legs back, the two new scripts set aside, the cron line out, call-hook restarted
#  (the table file stays -- it holds only calls the Sheet also holds; the raw log stays the truth).
# =============================================================================
set -u
KIT="S949_CALL_LOG_TABLE"; KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; WA="${WA:-$ROOT/wa}"; HK="${HK:-$WA/call-hook}"; FIN="${FIN:-$ROOT/finance}"; FRESH="${FRESH:-$FIN/freshness.py}"
DBF="${DBF:-$WA/calls.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
SVC="${SVC:-call-hook}"; HPORT="${HPORT:-8098}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; CRONTAB="${CRONTAB:-crontab}"
TAG="# S949_CALL_LOG_COMPARE"
HOOK="call_hook_capture.py"; DBM="call_log_db.py"; CMP="call_log_compare.py"; LG="freshness_legs.json"
HOOK_FROM="70c3d257cf9b576bda54acbdf83b99ee"; LG_FROM="abcb85653f286736e26243434df307b2"
CRONLINE="40 23 * * * [ -e $FIN/_off/ALL_OFF ] || flock -n /tmp/call_log_compare.lock $VPY -B $HK/$CMP >> $HK/call_log_compare.log 2>&1 $TAG"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s949_inst_$STAMP"; TOOK_LOCK=0; OFF_MINE=0
HK_CHANGED=0; LG_CHANGED=0; DBM_PLACED=0; CMP_PLACED=0; CRON_IN=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
m8() { m5 "$1" | cut -c1-8; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
HK_BAK="$HK/$HOOK.bak_S949_${HOOK_FROM:0:8}"; LG_BAK="$FIN/$LG.bak_S949_${LG_FROM:0:8}"
hz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$HPORT/"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(hz); [ "$h" = 200 ] && break; done; echo "$h"; }
jlog() { if [ -n "${JOURNAL_CMD:-}" ]; then $JOURNAL_CMD; else journalctl -u "$SVC" --since "$1" --no-pager 2>/dev/null; fi; }
cron_has() { $CRONTAB -l 2>/dev/null | grep -qF "$TAG"; }
cron_out() { $CRONTAB -l 2>/dev/null | grep -vF "$TAG" | $CRONTAB -; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $HOOK $DBM $CMP; do rm -f "$HK/.$n.s949"; done; rm -f "$FIN/.$LG.s949"; release; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release; exit 1; }
pause_doctor() { if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi; }
pyv() { (cd "$SCR" && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PYV_TIMEOUT:-600}" "$VPY" -W ignore -B "$@" 2>&1); }
aside() { [ -f "$HK/$1" ] && mv -f "$HK/$1" "$HK/$1.undone_S949"; }
put_back() {   # the hook and the legs from their backups; the new scripts aside; the cron line out; the service restarted
  [ "$HK_CHANGED" = 1 ] && [ -f "$HK_BAK" ] && \cp -p "$HK_BAK" "$HK/$HOOK"
  [ "$LG_CHANGED" = 1 ] && [ -f "$LG_BAK" ] && \cp -p "$LG_BAK" "$FIN/$LG"
  [ "$DBM_PLACED" = 1 ] && aside "$DBM"; [ "$CMP_PLACED" = 1 ] && aside "$CMP"
  cron_has && cron_out
  [ "$HK_CHANGED" = 1 ] && { "$SYSTEMCTL" restart "$SVC" || true; }; }
restore() { say "!! RED ($1) - putting back"; put_back
  say "   $HOOK $(m8 "$HK/$HOOK") (expected ${HOOK_FROM:0:8}), $LG $(m8 "$FIN/$LG") (expected ${LG_FROM:0:8}), the new scripts aside, cron $(cron_has && echo STILL IN || echo out); $SVC health $([ "$HK_CHANGED" = 1 ] && wait200 || hz)."
  say "   Send a photo of this screen to Claude."; release; exit 1; }

if [ "${1:-}" = "--undo" ]; then
  h="$(m5 "$HK/$HOOK")"; g="$(m5 "$FIN/$LG")"
  [ "$h" = "$HOOK_FROM" ] && [ "$g" = "$LG_FROM" ] && [ ! -f "$HK/$DBM" ] && [ ! -f "$HK/$CMP" ] && ! cron_has && { say "-- $KIT is not installed - nothing to undo."; exit 0; }
  [ "$h" = "$HOOK_FROM" ] || [ "$h" = "$(to_of $HOOK)" ] || { say "!! --undo: $HK/$HOOK is ${h:0:8}, not this kit's (a later kit?) - nothing undone. Tell Claude."; exit 1; }
  [ "$g" = "$LG_FROM" ] || [ "$g" = "$(to_of $LG)" ] || { say "!! --undo: $FIN/$LG is ${g:0:8}, not this kit's (a later kit?) - nothing undone. Tell Claude."; exit 1; }
  [ "$h" = "$HOOK_FROM" ] || { [ -f "$HK_BAK" ] && [ "$(m5 "$HK_BAK")" = "$HOOK_FROM" ]; } || { say "!! --undo: no good backup $HK_BAK - nothing undone"; exit 1; }
  [ "$g" = "$LG_FROM" ] || { [ -f "$LG_BAK" ] && [ "$(m5 "$LG_BAK")" = "$LG_FROM" ]; } || { say "!! --undo: no good backup $LG_BAK - nothing undone"; exit 1; }
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo" > "$LOCK/owner"; pause_doctor
  [ "$h" = "$HOOK_FROM" ] || HK_CHANGED=1; [ "$g" = "$LG_FROM" ] || LG_CHANGED=1; [ -f "$HK/$DBM" ] && DBM_PLACED=1; [ -f "$HK/$CMP" ] && CMP_PLACED=1
  put_back
  hh=200; [ "$HK_CHANGED" = 1 ] && hh=$(wait200); release
  [ "$(m5 "$HK/$HOOK")" = "$HOOK_FROM" ] && [ "$(m5 "$FIN/$LG")" = "$LG_FROM" ] || { say "!! --undo: the hook is $(m8 "$HK/$HOOK") and the legs $(m8 "$FIN/$LG") after putting back, not ${HOOK_FROM:0:8} / ${LG_FROM:0:8} - send a photo of this screen to Claude."; exit 1; }
  cron_has && { say "!! --undo: the cron line $TAG is still in the crontab after removing it - send a photo of this screen to Claude."; exit 1; }
  [ "$hh" = 200 ] || { say "!! UNDONE but $SVC health is $hh - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE ($HOOK $(m8 "$HK/$HOOK"), $LG $(m8 "$FIN/$LG"), the two new scripts set aside as *.undone_S949, cron $(cron_has && echo STILL IN || echo out); $SVC health 200). The table file $DBF stays."; exit 0
fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $DBM $CMP $LG; do [ "$(m5 "$KDIR/$n")" = "$(to_of $n)" ] || { say "!! [1/6] the kit's $n is not as built - nothing installed"; exit 1; }; done
say "[1/6] kit sums ok"
[ -x "$VPY" ] || stop "!! [2/6] $VPY is not there - STOP. Tell Claude."
[ -f "$HK/$HOOK" ] && [ -f "$FIN/$LG" ] && [ -f "$FRESH" ] || stop "!! [2/6] $HK/$HOOK, $FIN/$LG or $FRESH missing - STOP. Tell Claude."
h="$(m5 "$HK/$HOOK")"; g="$(m5 "$FIN/$LG")"; d="$(m5 "$HK/$DBM")"; c="$(m5 "$HK/$CMP")"
[ "$h" = "$HOOK_FROM" ] || [ "$h" = "$(to_of $HOOK)" ] || stop "!! [2/6] $HK/$HOOK is ${h:0:8}, not ${HOOK_FROM:0:8} (the 24-Nov bundle's) - it changed after this kit was built: STOP, nothing installed. Tell Claude."
[ "$g" = "$LG_FROM" ] || [ "$g" = "$(to_of $LG)" ] || stop "!! [2/6] $FIN/$LG is ${g:0:8}, not ${LG_FROM:0:8} (S946's) - STOP, nothing installed. Tell Claude."
[ -z "$d" ] || [ "$d" = "$(to_of $DBM)" ] || stop "!! [2/6] $HK/$DBM exists and is not this kit's - STOP. Tell Claude."
[ -z "$c" ] || [ "$c" = "$(to_of $CMP)" ] || stop "!! [2/6] $HK/$CMP exists and is not this kit's - STOP. Tell Claude."
if [ "$h" = "$(to_of $HOOK)" ] && [ "$g" = "$(to_of $LG)" ] && [ "$d" = "$(to_of $DBM)" ] && [ "$c" = "$(to_of $CMP)" ] && cron_has; then
  say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; fi
hm="${REHEARSE_CLOCK:-$(TZ=Asia/Kolkata date +%H%M)}"; dw="${REHEARSE_DOW:-$(TZ=Asia/Kolkata date +%u)}"; hm=$((10#$hm))
if [ "${ANYTIME:-0}" != 1 ]; then
  if [ "$dw" = 7 ]; then [ "$hm" -ge 900 ] && [ "$hm" -lt 1430 ] && stop "!! [2/6] it is Sunday $(printf %04d $hm) IST, inside duty hours (09:00-14:30): the call hook restarts for a few seconds and a call could meet it. Run this after 14:30. Nothing installed."
  else [ "$hm" -ge 900 ] && [ "$hm" -lt 2030 ] && stop "!! [2/6] it is $(printf %04d $hm) IST, inside duty hours (09:00-20:30): the call hook restarts for a few seconds and a call could meet it. Run this after 20:30 or before 09:00. Nothing installed."; fi
fi
mkdir -p "$SCR/new" "$SCR/live" && chmod 700 "$SCR" || stop "!! [2/6] cannot make $SCR - nothing installed"
if [ "${DRY:-0}" = 1 ]; then say "[2/6] DRY RUN: no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
else stop "!! [2/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; fi
# the FROM bytes: the live file, or its backup if an earlier run of this kit already placed the TO
if [ "$h" = "$HOOK_FROM" ]; then HF="$HK/$HOOK"; else HF="$HK_BAK"; [ "$(m5 "$HF")" = "$HOOK_FROM" ] || stop "!! [2/6] the hook is this kit's but no good backup $HK_BAK - STOP. Tell Claude."; fi
if [ "$g" = "$LG_FROM" ]; then LF="$FIN/$LG"; else LF="$LG_BAK"; [ "$(m5 "$LF")" = "$LG_FROM" ] || stop "!! [2/6] the legs are this kit's but no good backup $LG_BAK - STOP. Tell Claude."; fi
\cp -p "$HF" "$SCR/live/$HOOK" && \cp -p "$LF" "$SCR/live/$LG" || stop "!! [2/6] could not copy the live files - nothing installed"
MK=$(pyv "$KDIR/make_s949.py" "$SCR/live/$HOOK" "$SCR/new/$HOOK")
[ "$(m5 "$SCR/new/$HOOK")" = "$(to_of $HOOK)" ] || { echo "$MK" | tail -2 | sed 's/^/      /'; stop "!! [2/6] the patch of $HOOK did not give its TO pin - nothing installed"; }
\cp -p "$KDIR/$DBM" "$KDIR/$CMP" "$SCR/new/" || stop "!! [2/6] could not lay out the new files - nothing installed"
for n in $HOOK $DBM $CMP; do (cd "$SCR" && PYTHONPYCACHEPREFIX="$SCR/pyc" "$VPY" -W ignore -m py_compile "$SCR/new/$n") || stop "!! [2/6] $n does not compile on $VPY - nothing installed"; done
say "[2/6] live pins exact ($HOOK ${h:0:8}, $LG ${g:0:8}); the hook patched to its TO pin; three files compile; $([ "$TOOK_LOCK" = 1 ] && echo "the build lock taken" || echo "no lock (DRY)")"
W=$(pyv "$KDIR/walk_s949.py" "$SCR/new/$HOOK" "$KDIR" | tail -1)
[ "$W" = "WALK 27/27" ] || { pyv "$KDIR/walk_s949.py" "$SCR/new/$HOOK" "$KDIR" | grep RED | head -6 | sed 's/^/      /'; stop "!! [3/6] walk_s949: $W - nothing installed"; }
Wc=$(LEGS_FROM="$SCR/live/$LG" pyv "$KDIR/walk_s949.py" "$SCR/live/$HOOK" "$KDIR" --control | tail -1)
case "$Wc" in "WALK 27/27") stop "!! [3/6] walk_s949's control (the FROM files) did not go red - nothing installed";; "WALK "*) ;;
  *) stop "!! [3/6] walk_s949's control did not finish ($Wc) - nothing installed";; esac
S1=$(cd "$SCR/new" && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" CALLHOOK_RAW_LOG_DIR="$SCR/raw" CALLHOOK_REJECT_DIR="$SCR/rej" CALLHOOK_QUEUE_DIR="$SCR/q" CALLHOOK_DB="$SCR/st.db" timeout 120 "$VPY" -W ignore -B "$HOOK" --selftest 2>&1 | tail -1)
case "$S1" in "selftest: 75/75 passed") ;; *) stop "!! [3/6] the hook's own selftest on the new file: $S1 - nothing installed";; esac
S2=$(pyv "$SCR/new/$DBM" --selftest | tail -1); [ "$S2" = "selftest: 15/15 passed" ] || stop "!! [3/6] $DBM --selftest: $S2 - nothing installed"
S3=$(CALLHOOK_DB="$SCR/st3.db" pyv "$SCR/new/$CMP" --selftest | tail -1); [ "$S3" = "selftest: 18/18 passed" ] || stop "!! [3/6] $CMP --selftest: $S3 - nothing installed"
say "[3/6] walk $W (control red: $Wc); selftests: the hook $S1, the table ${S2#selftest: }, the compare ${S3#selftest: }"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the patch, the walk and the selftests green; nothing live changed."; exit 0; fi
h0=$(hz); [ "$h0" = 200 ] || stop "!! [4/6] $SVC health $h0 before the install - nothing installed"
"$SYSTEMCTL" is-active --quiet "$SVC" || stop "!! [4/6] $SVC is not active before the install - nothing installed"
if [ "$h" = "$HOOK_FROM" ]; then { \cp -p "$HK/$HOOK" "$HK_BAK" && [ "$(m5 "$HK_BAK")" = "$HOOK_FROM" ]; } || stop "!! [4/6] could not write the backup of $HOOK - nothing placed"; fi
if [ "$g" = "$LG_FROM" ]; then { \cp -p "$FIN/$LG" "$LG_BAK" && [ "$(m5 "$LG_BAK")" = "$LG_FROM" ]; } || stop "!! [4/6] could not write the backup of $LG - nothing placed"; fi
for n in $HOOK $DBM $CMP; do st="$HK/.$n.s949"; { cat "$SCR/new/$n" > "$st" && chmod --reference="$HK/$HOOK" "$st" 2>/dev/null; chown --reference="$HK/$HOOK" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of $n)" ]; } || stop "!! [4/6] could not stage $n - nothing placed"; done
{ cat "$KDIR/$LG" > "$FIN/.$LG.s949" && chmod --reference="$FIN/$LG" "$FIN/.$LG.s949" 2>/dev/null; chown --reference="$FIN/$LG" "$FIN/.$LG.s949" 2>/dev/null; [ "$(m5 "$FIN/.$LG.s949")" = "$(to_of $LG)" ]; } || stop "!! [4/6] could not stage $LG - nothing placed"
# a table left by an earlier install that was undone would start the compare's window in the past: set it aside (kept)
DB_ASIDE=""; if [ "$h" = "$HOOK_FROM" ] && [ -f "$DBF" ]; then DB_ASIDE="$DBF.before_S949_$STAMP"; mv -f "$DBF" "$DB_ASIDE" || stop "!! [4/6] could not set the old table $DBF aside - nothing placed"; fi
pause_doctor
T0="$(date '+%Y-%m-%d %H:%M:%S')"
[ "$d" = "$(to_of $DBM)" ] || { mv -f "$HK/.$DBM.s949" "$HK/$DBM" || restore "placing $DBM"; DBM_PLACED=1; }
[ "$c" = "$(to_of $CMP)" ] || { mv -f "$HK/.$CMP.s949" "$HK/$CMP" || restore "placing $CMP"; CMP_PLACED=1; }
[ "$g" = "$(to_of $LG)" ] || { mv -f "$FIN/.$LG.s949" "$FIN/$LG" || restore "placing $LG"; LG_CHANGED=1; }
[ "$h" = "$(to_of $HOOK)" ] || { mv -f "$HK/.$HOOK.s949" "$HK/$HOOK" || restore "placing $HOOK"; HK_CHANGED=1; }
for n in $HOOK $DBM $CMP; do [ "$(m5 "$HK/$n")" = "$(to_of $n)" ] || restore "read back of $n"; done
[ "$(m5 "$FIN/$LG")" = "$(to_of $LG)" ] || restore "read back of $LG"
HK_CHANGED=1; "$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
h1=$(wait200); [ "$h1" = 200 ] || restore "$SVC health $h1 after the restart"
ML=""; for _t in 1 2 3 4 5 6; do J="$(jlog "$T0")"; echo "$J" | grep -q "receiver v3.4" && echo "$J" | grep -qF "call log table: $DBF -- " && { ML=ok; break; }; sleep "${NAP:-3}"; done
[ "$ML" = ok ] || restore "the service log does not show receiver v3.4 with the table $DBF ready"
[ -f "$DBF" ] && [ "$(stat -c %a "$DBF")" = 600 ] || restore "the table file $DBF is missing or not owner-only"
LL="$(cd "$SCR" && "$VPY" -B "$FRESH" list 2>&1 | tail -1)"; case "$LL" in *"45 leg(s) declared"*) ;; *) restore "freshness.py list after the legs: $LL (wanted 45 declared)";; esac
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
say "[4/6] placed and read back: $HOOK $(m8 "$HK/$HOOK"), $DBM $(m8 "$HK/$DBM") NEW, $CMP $(m8 "$HK/$CMP") NEW, $LG $(m8 "$FIN/$LG") (45 legs); $SVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), health $h1; the log: receiver v3.4, the table ready$([ -n "$DB_ASIDE" ] && echo "; an older table kept as $DB_ASIDE")"
$CRONTAB -l > "$SCR/cron_before.txt" 2>/dev/null || true
[ -s "$SCR/cron_before.txt" ] || restore "crontab -l came back empty - the crontab not touched"
{ grep -vF "$TAG" "$SCR/cron_before.txt"; echo "$CRONLINE"; } | $CRONTAB - || restore "the cron line"
cron_has || restore "the cron line did not read back"; CRON_IN=1
[ "$(( $($CRONTAB -l | wc -l) ))" = "$(( $(grep -vcF "$TAG" "$SCR/cron_before.txt") + 1 ))" ] || restore "the crontab's line count after the cron line"
C1=$(cd "$SCR" && CALL_LOG_COMPARE_RETRY_S=5 TZ=Asia/Kolkata timeout 300 "$VPY" -W ignore -B "$HK/$CMP" 2>&1 | tail -1)
case "$C1" in "COMPARE EQUAL"*) ;; *) restore "the first compare: $C1";; esac
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/6]"
release
say "[5/6] cron 23:40 in; the first compare: $C1"
say "[6/6] the doctor's auto-fix resumed. Undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""; say "$KIT: DONE. His health page shows the leg 'call log table = sheet': https://followup.dr-manoj.in/finance/health"; exit 0
