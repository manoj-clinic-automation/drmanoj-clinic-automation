#!/bin/bash
# install_S946_A2_REST.sh -- S946 (the parent, S512, 24-Nov-2026): roadmap S510 phase 0, A2's rest.
#   (i)  the 403 watchdog (call-hook/callhook_watchdog.py, S125, scheduled nowhere): KEPT and run 11:15 daily through NEW
#        callhook_watch_run.py (a state file + a freshness leg) IF this box's web log matches a glob and carries our route;
#        else RETIRED to /root/_retired/S510/ (its leg not declared). The box decides, the DRY says which.
#   (ii) call_pipeline_worker.py 3c8be7f0 -> TO: a state file after every at-hangup run; the leg 'AI judged within 15 min'
#        (freshness_legs.json 2a03e305 -> TO_A with both legs, or TO_B with the pipeline leg only). call-pipeline restarted
#        with its lock free.
#   (iii) the one-off s946_verdict_cleanup.py on Call_Verdicts: owner-only CSV backup first; FAILED rows whose call has a done
#        row removed; the July calls marked 'Not judgeable'; read back -- the pipeline lock held from the first read to the read-back.
#        The DRY runs it read-only (backup + counts). Refused inside 01:55-04:05 IST (the night sweeps take no lock).
#   [1/6] SUMS gate  [2/6] the ground + the web-log probe  [3/6] walk + control + the one-off DRY (counts)  [4/6] files, cron,
#   the service restarted  [5/6] the one-off LIVE  [6/6] said.   DRY=1: [1]-[3] only.   --undo: files back, the runner aside,
#   cron out, the watchdog back from _retired, the service restarted. The sheet is NOT undone (the backup CSV is named).
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s946kit && cp -rp /root/deploy/repo/deploy_kits/S946_A2_REST /tmp/s946kit && bash /tmp/s946kit/install_S946_A2_REST.sh
set -u
KIT="S946_A2_REST"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FIN="${FIN:-$ROOT/finance}"; WA="${WA:-$ROOT/wa}"; RA="${RA:-$WA/recordings-archive}"; CH="${CH:-$WA/call-hook}"
APY="${APY:-$WA/venv/bin/python3}"; RET="${RET:-$ROOT/_retired/S510}"; FRESH="${FRESH:-$FIN/freshness.py}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; PSVC="${PSVC:-call-pipeline}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; CRONTAB="${CRONTAB:-crontab}"
TAG="# S946_CALLHOOK_WATCH"
WK="call_pipeline_worker.py"; LG="freshness_legs.json"; RN="callhook_watch_run.py"; WD="callhook_watchdog.py"; CL="s946_verdict_cleanup.py"
WK_FROM="3c8be7f0f6f5960103fb1ed586c48cce"; LG_FROM="2a03e30521e39510280831afab8f12c8"; WD_LIVE="665797f8d18d2cfed66952614718551e"
CAND_GLOBS="${CAND_GLOBS:-/home/*/logs/*access* /usr/local/lsws/logs/*access* /var/log/*access* /var/log/*/*access*}"
SCR="$(mktemp -d /tmp/s946_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0; WK_CHANGED=0; LG_CHANGED=0; RN_PLACED=0; WD_MOVED=0; CRON_IN=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
m8() { m5 "$1" | cut -c1-8; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { release_lock; rm -rf "${SCR:?}" "$RA/.$WK.s946" "$FIN/.$LG.s946" "$CH/.$RN.s946"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
pya() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PYA_TIMEOUT:-900}" "$APY" -W ignore -B "$@" 2>&1); }
cron_has() { $CRONTAB -l 2>/dev/null | grep -qF "$TAG"; }
cron_out() { $CRONTAB -l 2>/dev/null | grep -vF "$TAG" | $CRONTAB -; }
svc_active() { "$SYSTEMCTL" is-active --quiet "$PSVC"; }
lock_free() { ( exec 9>"$RA/pipeline.lock"; flock -n 9 ) 2>/dev/null; }
wait_lock() { for _t in $(seq 1 "${LOCK_TRIES:-20}"); do lock_free && return 0; sleep "${NAP:-3}"; done; return 1; }
restart_pipeline() { local t; for t in $(seq 1 "${LOCK_TRIES:-20}"); do ( exec 9>"$RA/pipeline.lock"; flock -n 9 || exit 9; "$SYSTEMCTL" restart "$PSVC" ) 2>/dev/null; rc=$?; [ "$rc" = 9 ] && { sleep "${NAP:-3}"; continue; }; [ "$rc" = 0 ] || return 1; sleep "${NAP:-3}"; svc_active; return $?; done; return 1; }   # the lock held across the restart: no stage killed mid-run
WK_BAK="$RA/$WK.bak_S946_${WK_FROM:0:8}"; LG_BAK="$FIN/$LG.bak_S946_${LG_FROM:0:8}"
restore() { say "!! RED ($1) - putting back"
  [ "$WK_CHANGED" = 1 ] && [ -f "$WK_BAK" ] && \cp -p "$WK_BAK" "$RA/$WK"
  [ "$LG_CHANGED" = 1 ] && [ -f "$LG_BAK" ] && \cp -p "$LG_BAK" "$FIN/$LG"
  [ "$RN_PLACED" = 1 ] && [ -f "$CH/$RN" ] && mv -f "$CH/$RN" "$CH/$RN.undone_S946"
  [ "$WD_MOVED" = 1 ] && [ -f "$RET/$WD" ] && mv -f "$RET/$WD" "$CH/$WD"
  cron_has && cron_out
  if [ "$WK_CHANGED" = 1 ]; then restart_pipeline && s=active || s="$(svc_active && echo "active but NOT restarted (lock busy) - restart it when quiet" || echo NOT-ACTIVE)"; else s="(not restarted)"; fi
  say "   restored: $WK $(m8 "$RA/$WK") (expected ${WK_FROM:0:8}), $LG $(m8 "$FIN/$LG") (expected ${LG_FROM:0:8}), runner aside, watchdog $([ -f "$CH/$WD" ] && echo in place || echo MISSING), cron out; $PSVC $s. Tell Claude."
  release_lock; exit 1; }
if [ "${1:-}" = "--undo" ]; then
  n=0
  [ -f "$WK_BAK" ] && { [ "$(m5 "$RA/$WK")" = "$(to_of $WK)" ] || stop "!! --undo: $WK is $(m8 "$RA/$WK"), not S946's (a later kit?) - not undoing"; }
  [ -f "$LG_BAK" ] && { g="$(m5 "$FIN/$LG")"; [ "$g" = "$(to_of freshness_legs_a.json)" ] || [ "$g" = "$(to_of freshness_legs_b.json)" ] || stop "!! --undo: $LG is ${g:0:8}, not S946's (a later kit?) - not undoing"; }
  mkdir "$LOCK" 2>/dev/null || stop "!! --undo: another build holds $LOCK - try again in five minutes"; TOOK_LOCK=1; echo "$KIT undo" > "$LOCK/owner"
  [ -f "$LG_BAK" ] && { \cp -p "$LG_BAK" "$FIN/$LG"; n=$((n+1)); }
  [ -f "$CH/$RN" ] && { mv -f "$CH/$RN" "$CH/$RN.undone_S946"; n=$((n+1)); }
  [ -f "$RET/$WD" ] && [ ! -f "$CH/$WD" ] && { mv -f "$RET/$WD" "$CH/$WD"; n=$((n+1)); }
  cron_has && { cron_out; n=$((n+1)); }
  if [ -f "$WK_BAK" ]; then \cp -p "$WK_BAK" "$RA/$WK"; n=$((n+1)); restart_pipeline || { say "!! UNDONE but $PSVC is not active - tell Claude"; exit 1; }; fi
  release_lock
  [ "$n" = 0 ] && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  say "$KIT: UNDONE ($n thing(s) back: $WK $(m8 "$RA/$WK"), $LG $(m8 "$FIN/$LG"), runner aside, watchdog $([ -f "$CH/$WD" ] && echo in place || echo absent), cron $(cron_has && echo STILL THERE || echo out); the sheet as the one-off left it - its backup CSV is under $RA/backup_S946/)"; exit 0
fi
cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "!! [1/6] KIT_ID.txt names another kit - nothing installed"
for n in $WK $RN $CL freshness_legs_a.json freshness_legs_b.json; do [ "$(m5 "$KDIR/$n")" = "$(to_of $n)" ] || stop "!! [1/6] the kit's $n is not as built - nothing installed"; done
say "   [1/6] kit sums ok"
[ -x "$APY" ] || stop "!! [2/6] $APY is not there - STOP. Tell Claude."
[ -f "$RA/$WK" ] && [ -f "$FIN/$LG" ] && [ -d "$CH" ] || stop "!! [2/6] $RA/$WK, $FIN/$LG or $CH missing - STOP. Tell Claude."
w="$(m5 "$RA/$WK")"; g="$(m5 "$FIN/$LG")"; r="$(m5 "$CH/$RN")"; d="$(m5 "$CH/$WD")"
[ "$w" = "$WK_FROM" ] || [ "$w" = "$(to_of $WK)" ] || stop "!! [2/6] $RA/$WK is ${w:0:8}, not ${WK_FROM:0:8} (the 24-Nov bundle's) - it changed after this kit was built: STOP. Tell Claude."
[ "$g" = "$LG_FROM" ] || [ "$g" = "$(to_of freshness_legs_a.json)" ] || [ "$g" = "$(to_of freshness_legs_b.json)" ] || stop "!! [2/6] $FIN/$LG is ${g:0:8}, not ${LG_FROM:0:8} (S943's) - STOP. Tell Claude."
[ -z "$r" ] || [ "$r" = "$(to_of $RN)" ] || stop "!! [2/6] $CH/$RN exists and is not this kit's - STOP. Tell Claude."
[ -z "$d" ] || [ "$d" = "$WD_LIVE" ] || stop "!! [2/6] $CH/$WD is ${d:0:8}, not ${WD_LIVE:0:8} (the bundle's) - STOP. Tell Claude."
svc_active || stop "!! [2/6] $PSVC is not active before the install - STOP. Tell Claude."
hm="${REHEARSE_CLOCK:-$(TZ=Asia/Kolkata date +%H%M)}"; [ "${QUIET_CHECK:-1}" = 1 ] && [ "$((10#$hm))" -ge 155 ] && [ "$((10#$hm))" -lt 405 ] && stop "!! [2/6] it is $hm IST, inside the night sweeps' window 01:55-04:05 (they do not take the pipeline lock) - run this after 04:05. Nothing installed."
for n in $WK $RN $CL; do pya -m py_compile "$KDIR/$n" >/dev/null 2>&1 || stop "!! [2/6] the kit's $n does not compile under $APY - nothing installed"; done
# --- the web-log probe: which glob, if any, matches a log that carries our route ---------------------------------------
GLOB=""; NROUTE=0
if [ -n "$d" ] && [ ! -f "$RET/$WD" ]; then
  ST="$(pya "$CH/$WD" --selftest | tail -1)"; pya "$CH/$WD" --selftest >/dev/null 2>&1 || stop "!! [2/6] the live watchdog's --selftest failed ($ST) - STOP. Tell Claude."
  for gl in $CAND_GLOBS; do
    files="$(ls $gl 2>/dev/null)"; [ -n "$files" ] || continue
    nr=0; for f in $files; do case "$f" in *.gz) c=$(zcat "$f" 2>/dev/null | grep -c "mo-callhook");; *) c=$(grep -c "mo-callhook" "$f" 2>/dev/null);; esac; nr=$((nr + ${c:-0})); done
    [ "$nr" -gt 0 ] && { GLOB="$gl"; NROUTE=$nr; break; }
  done
  if [ -n "$GLOB" ]; then
    PJ="$(pya "$CH/$WD" --json --access-glob "$GLOB" --date "$(date -d yesterday +%F)" | grep -c '"exit_code"')"
    [ "$PJ" = 1 ] || stop "!! [2/6] the watchdog did not report on $GLOB - STOP. Tell Claude."
    WDEC="KEEP: the web log $GLOB carries our route ($NROUTE lines); the watchdog runs 11:15 daily"
  else WDEC="RETIRE: no web log under $CAND_GLOBS carries our route; the watchdog goes to $RET/ (its leg not declared)"; fi
elif [ -f "$RET/$WD" ]; then WDEC="RETIRED already ($RET/$WD)"
else WDEC="ABSENT: no $CH/$WD on the box - nothing to schedule or retire"; fi
if [ -n "$GLOB" ]; then LEGS_TO="freshness_legs_a.json"; NLEGS=44; else LEGS_TO="freshness_legs_b.json"; NLEGS=43; fi
CRONLINE="15 11 * * * [ -e $FIN/_off/ALL_OFF ] || flock -n /tmp/callhook_watch.lock $APY -B $CH/$RN --access-glob '$GLOB' >> $CH/callhook_watch.log 2>&1 $TAG"
done_already=0
if [ "$w" = "$(to_of $WK)" ] && [ "$g" = "$(to_of $LEGS_TO)" ]; then
  if [ -n "$GLOB" ]; then [ "$r" = "$(to_of $RN)" ] && cron_has && done_already=1; else [ -z "$r" ] && done_already=1; fi; fi
[ "$done_already" = 1 ] && { say "-- $KIT is already installed ($WDEC). Nothing done."; exit 0; }
if [ "${DRY:-0}" = 1 ]; then say "   [2/6] DRY RUN: pins $WK ${w:0:8}, $LG ${g:0:8}, runner ${r:-absent}, watchdog ${d:-absent}; compile ok; $PSVC active; no lock"
elif mkdir "$LOCK" 2>/dev/null; then echo "$KIT $$" > "$LOCK/owner"; TOOK_LOCK=1; say "   [2/6] pins $WK ${w:0:8}, $LG ${g:0:8}, runner ${r:-absent}, watchdog ${d:-absent}; compile ok; $PSVC active; the build lock taken"
else stop "!! [2/6] another build holds $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - try again in five minutes"; fi
say "         watchdog: $WDEC"
if [ "$w" = "$WK_FROM" ]; then WF="$RA/$WK"; else WF="$WK_BAK"; fi
if [ "$g" = "$LG_FROM" ]; then LF="$FIN/$LG"; else LF="$LG_BAK"; fi
W="$(pya "$KDIR/walk_s946.py" "$KDIR" "$SCR/w946" | tail -1)"; case "$W" in "WALK 39/39") ;; *) stop "!! [3/6] walk_s946: $W - nothing installed";; esac
Wc="$(WORKER_FROM="$WF" LEGS_FROM="$LF" pya "$KDIR/walk_s946.py" "$KDIR" "$SCR/w946c" --control | tail -1)"; [ "$Wc" != "WALK 39/39" ] || { [ "$w" = "$(to_of $WK)" ] || stop "!! [3/6] walk_s946's control did not go red - nothing installed"; }
D1="$(S946_RA_DIR="$RA" pya "$KDIR/$CL" --dry --backup-dir "$RA/backup_S946")"; echo "$D1" | sed 's/^/         /'
case "$D1" in *"DRY: nothing written"*) ;; *) stop "!! [3/6] the one-off's dry read did not finish - nothing installed";; esac
say "   [3/6] walk $W (control $Wc); the one-off's dry read above (the backup CSV written, owner-only)"
[ "${DRY:-0}" = 1 ] && { say "-- DRY RUN: every gate, the walk, the probe and the dry read green; nothing live changed. Decision: $WDEC"; exit 0; }
# --- [4/6] the files -----------------------------------------------------------------------------------------------------
if [ "$w" != "$(to_of $WK)" ]; then { \cp -p "$RA/$WK" "$WK_BAK" && [ "$(m5 "$WK_BAK")" = "$WK_FROM" ]; } || stop "!! [4/6] could not write the backup of $WK - nothing placed"; fi
if [ "$g" != "$(to_of $LEGS_TO)" ] && [ "$g" = "$LG_FROM" ]; then { \cp -p "$FIN/$LG" "$LG_BAK" && [ "$(m5 "$LG_BAK")" = "$LG_FROM" ]; } || stop "!! [4/6] could not write the backup of $LG - nothing placed"; fi
{ cat "$KDIR/$WK" > "$RA/.$WK.s946" && chmod --reference="$RA/$WK" "$RA/.$WK.s946" && chown --reference="$RA/$WK" "$RA/.$WK.s946" && [ "$(m5 "$RA/.$WK.s946")" = "$(to_of $WK)" ]; } || stop "!! [4/6] could not stage $WK - nothing placed"
{ cat "$KDIR/$LEGS_TO" > "$FIN/.$LG.s946" && chmod --reference="$FIN/$LG" "$FIN/.$LG.s946" && chown --reference="$FIN/$LG" "$FIN/.$LG.s946" && [ "$(m5 "$FIN/.$LG.s946")" = "$(to_of $LEGS_TO)" ]; } || stop "!! [4/6] could not stage $LG - nothing placed"
if [ -n "$GLOB" ]; then { cat "$KDIR/$RN" > "$CH/.$RN.s946" && chmod 700 "$CH/.$RN.s946" && chown --reference="$CH/$WD" "$CH/.$RN.s946" && [ "$(m5 "$CH/.$RN.s946")" = "$(to_of $RN)" ]; } || stop "!! [4/6] could not stage $RN - nothing placed"; fi
[ "$w" = "$(to_of $WK)" ] || { mv -f "$RA/.$WK.s946" "$RA/$WK" || restore "placing $WK"; WK_CHANGED=1; }
[ "$g" = "$(to_of $LEGS_TO)" ] || { mv -f "$FIN/.$LG.s946" "$FIN/$LG" || restore "placing $LG"; LG_CHANGED=1; }
[ "$(m5 "$RA/$WK")" = "$(to_of $WK)" ] || restore "read back of $WK ($(m8 "$RA/$WK"))"
[ "$(m5 "$FIN/$LG")" = "$(to_of $LEGS_TO)" ] || restore "read back of $LG ($(m8 "$FIN/$LG"))"
if [ -n "$GLOB" ]; then
  [ "$r" = "$(to_of $RN)" ] || { mv -f "$CH/.$RN.s946" "$CH/$RN" || restore "placing $RN"; RN_PLACED=1; }
  [ "$(m5 "$CH/$RN")" = "$(to_of $RN)" ] || restore "read back of $RN"
  R1="$(pya "$CH/$RN" --access-glob "$GLOB" | tail -1)"; case "$R1" in WATCH\ OK*|WATCH\ WARN*|WATCH\ CRITICAL*) ;; *) restore "the runner's first run: $R1";; esac
  $CRONTAB -l > "$SCR/cron_before.txt" 2>/dev/null || true
  [ -s "$SCR/cron_before.txt" ] || restore "crontab -l came back empty - the crontab not touched"
  { grep -vF "$TAG" "$SCR/cron_before.txt"; echo "$CRONLINE"; } | $CRONTAB - || restore "the cron line"
  cron_has || restore "the cron line did not read back"; CRON_IN=1
elif [ -n "$d" ] && [ ! -f "$RET/$WD" ]; then
  mkdir -p "$RET" && chmod 700 "$RET" || restore "making $RET"
  mv -f "$CH/$WD" "$RET/$WD" || restore "retiring $WD"; WD_MOVED=1
  [ "$(m5 "$RET/$WD")" = "$WD_LIVE" ] || restore "the retired watchdog's read back"
  R1="(retired)"
fi
LL="$(pya "$FRESH" list | tail -1)"; case "$LL" in *"$NLEGS leg(s) declared"*) ;; *) restore "freshness.py list after the legs: $LL (wanted $NLEGS declared)";; esac
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
if [ "$WK_CHANGED" = 1 ]; then restart_pipeline || restore "restart $PSVC (its lock busy for a minute, or not active after)"; fi
say "   [4/6] placed: $WK $(m8 "$RA/$WK") (bak beside), $LG $(m8 "$FIN/$LG") (= $LEGS_TO, bak beside), runner $([ -n "$GLOB" ] && echo "$(m8 "$CH/$RN") NEW + cron 11:15" || echo "not placed"); watchdog $WDEC; $PSVC $(svc_active && echo active || echo NOT-ACTIVE); first watch: $R1"
# --- [5/6] the one-off, live ----------------------------------------------------------------------------------------------
L1="$(S946_RA_DIR="$RA" pya "$KDIR/$CL" --backup-dir "$RA/backup_S946")"; echo "$L1" | sed 's/^/         /'
case "$L1" in *"CLEANUP OK"*) ;; *) restore "the one-off: not CLEANUP OK (the sheet's backup CSV is under $RA/backup_S946/)";; esac
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/6]"
release_lock
say "   [5/6] the one-off: $(echo "$L1" | grep -m1 'CLEANUP OK')"
say "   [6/6] the pipeline's state file is written at the next call's hangup (the leg reads 'nothing recorded yet' until then); the watchdog's leg $([ -n "$GLOB" ] && echo 'has its first record' || echo 'is not declared')"
say "$KIT: DONE. Undo: bash $KDIR/install_$KIT.sh --undo  (or from the repo copy /root/deploy/repo/deploy_kits/$KIT/ after a reboot)"
exit 0
