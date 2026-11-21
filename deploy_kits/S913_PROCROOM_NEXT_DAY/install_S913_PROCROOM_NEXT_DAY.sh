#!/bin/bash
# =============================================================================
#  install_S913_PROCROOM_NEXT_DAY.sh · kit S913 (the parent, on the Scan App's file, S496, 21-Nov-2026)
#  Kal ke procedures (Shavez's morning screen):  /root/assetapp/procroom.py 38c5bbaa -> TO
#   * opened with no day, it opens the OLDEST day still waiting (was always yesterday, even when yesterday was done);
#   * a Save that finishes the day goes on to the next waiting day and says so; the save itself is unchanged.
#  assetapp restarted.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s913kit && cp -rp /root/deploy/repo/deploy_kits/S913_PROCROOM_NEXT_DAY /tmp/s913kit && bash /tmp/s913kit/install_S913_PROCROOM_NEXT_DAY.sh
#  DRY=1 before bash: every gate and the walk, nothing changed. --undo: the file back.
# =============================================================================
set -u
KIT="S913_PROCROOM_NEXT_DAY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
APP="${APP:-/root/assetapp}"; SVC="${SVC:-assetapp}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
HEALTH="${HEALTH:-http://127.0.0.1:8030}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
N="procroom.py"; FROM="38c5bbaa79c8b05ac3394a412f74851d"
TO="$(awk -v f="assetapp/$N" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
BAK="$APP/$N.bak_S913_${FROM:0:8}"
SCR="${TMPW:-/tmp}/s913_inst_$(date +%Y%m%d_%H%M%S)"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
hc() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "$HEALTH$1"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(hc /healthz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$APP/.$N.s913"; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the file back"
  \cp -p "$BAK" "$APP/$N"; "$SYSTEMCTL" restart "$SVC" || true
  say "   $N $(m5 "$APP/$N" | cut -c1-8) (expected ${FROM:0:8}); $SVC restarted, healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }

if [ "${1:-}" = "--undo" ]; then
  [ "$(m5 "$APP/$N")" = "$FROM" ] && { say "-- $KIT is not installed - nothing to undo."; exit 0; }
  [ -f "$BAK" ] && [ "$(m5 "$BAK")" = "$FROM" ] || { say "!! no good backup $BAK - nothing undone"; exit 1; }
  [ "$(m5 "$APP/$N")" = "$TO" ] || { say "!! $APP/$N is $(m5 "$APP/$N" | cut -c1-8), not this kit's - a later change is on it: nothing undone. Tell Claude."; exit 1; }
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo" > "$LOCK/owner"
  \cp -p "$BAK" "$APP/$N"; "$SYSTEMCTL" restart "$SVC"; h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but healthz is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE ($SVC restarted, healthz 200)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 "$KDIR/$N")" = "$TO" ] || { say "!! [1/5] the kit's $N is not as built - nothing installed"; exit 1; }
[ -f "$APP/$N" ] || { say "!! [1/5] $APP/$N missing - nothing installed"; exit 1; }
[ "$(m5 "$APP/$N")" = "$TO" ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$APP/$N")" = "$FROM" ] || stop "!! [2/5] $APP/$N is $(m5 "$APP/$N" | cut -c1-8), expected ${FROM:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/$N" || stop "!! [2/5] $N does not compile on $p - nothing installed"; done
say "[2/5] the live pin exact; the file compiles on both pythons"
mkdir -p "$SCR/new" "$SCR/old" && \cp -p "$KDIR/$N" "$SCR/new/" && \cp -p "$APP/$N" "$SCR/old/" || stop "!! [3/5] could not lay out the walk - nothing installed"
R1=$(cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s913.py" "$SCR/new" 2>&1 | tail -1)
case "$R1" in "WALK 10/10") ;; *) stop "!! [3/5] walk_s913 on the new file: $R1 - nothing installed";; esac
R1c=$(cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s913.py" "$SCR/old" 2>&1 | tail -1)
case "$R1c" in "WALK 10/10") stop "!! [3/5] walk_s913's control (the live file) did not go red - nothing installed";; esac
say "[3/5] walk_s913 $R1 (control red: ${R1c:-crashed})"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the control green; nothing live changed"; exit 0; fi
h0=$(hc /healthz); [ "$h0" = 200 ] || stop "!! [4/5] healthz $h0 before the install - nothing installed"
{ \cp -p "$APP/$N" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop "!! [4/5] could not write the backup - nothing placed"
{ cat "$KDIR/$N" > "$APP/.$N.s913" && chmod --reference="$APP/$N" "$APP/.$N.s913" 2>/dev/null; chown --reference="$APP/$N" "$APP/.$N.s913" 2>/dev/null; [ "$(m5 "$APP/.$N.s913")" = "$TO" ]; } || stop "!! [4/5] could not stage $N - nothing placed"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
mv -f "$APP/.$N.s913" "$APP/$N" || restore "the rename"
[ "$(m5 "$APP/$N")" = "$TO" ] || restore "read back"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "healthz $c1 after the restart"
mp=$(hc /procroom/morning); case "$mp" in 200|302|303|401|403) ;; *) restore "the morning screen answered $mp";; esac
if [ -z "${HEALTH_CMD:-}" ]; then NM=$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c 'NOT mounted'); [ "${NM:-0}" = 0 ] || restore "the scan app's log says a part is NOT mounted"; fi
release_lock
say "[4/5] placed and read back: $N at its TO pin; $SVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), healthz $c1, the morning screen $mp, no part NOT mounted"
say "[5/5] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""
say "$KIT: DONE."
exit 0
