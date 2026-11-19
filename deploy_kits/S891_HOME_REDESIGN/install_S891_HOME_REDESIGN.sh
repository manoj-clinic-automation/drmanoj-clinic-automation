#!/bin/bash
# =============================================================================
#  install_S891_HOME_REDESIGN.sh · kit S891 (the parent, S489, 19-Nov-2026) · his "ok" 08:12 on the live preview
#  The owner's portal home redesigned -- ONE file:
#   /root/portal/portal.py   9da49bd1 -> TO   (S890's TO)
#     · folders as coloured cards (each its own colour), the inside pages as LIGHT cards with dark type, the open panel in the
#       folder's colour; the top compacted (the call-alert bar one slim line, Today + Tasks in one row, health and the four counts
#       one row of pills); on a phone / the opened Fold the folders are icon + name, four to a row -- the home on one Fold screen
#     · drawn on the home only (a style block inside PORTAL_HTML); the Forms page, which shares the head, is untouched
#     · the call-alert bar in English on the owner's home (role doctor); every staff home keeps its Hindi
#  Run as root on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s891kit && cp -rp /root/deploy/repo/deploy_kits/S891_HOME_REDESIGN /tmp/s891kit && bash /tmp/s891kit/install_S891_HOME_REDESIGN.sh
#  DRY=1 before bash: every gate and the walk (made-up secrets; the control on the live file); nothing live changes.
#  --undo: portal.py back to 9da49bd1 from its backup, clinic-portal restarted.
# =============================================================================
set -u
KIT="S891_HOME_REDESIGN"
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; PD="${PD:-$ROOT/portal}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
PSVC="${PSVC:-clinic-portal}"; PPORT="${PPORT:-8099}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
N="portal.py"; LIVEF="$PD/$N"; FROM="9da49bd1"; FROMFULL="9da49bd14088498e0fe27fbe2f13134a"
TO="$(awk -v f="$N" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
BAK="$PD/$N.bak_S891_$FROM"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s891_inst_$STAMP"; TOOK_LOCK=0; OFF_MINE=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
m8() { m5 "$1" | cut -c1-8; }
say() { echo "$@"; }
hget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1" "$2"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$1$2"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(hget "$1" "$2"); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$PD/.$N.s891"; release; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release; exit 1; }
pause_doctor() { if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi; }
restore() { say "!! RED after placing ($1) - putting portal.py back"
  [ -f "$BAK" ] && \cp -p "$BAK" "$LIVEF"
  "$SYSTEMCTL" restart "$PSVC" || true
  say "   $N $(m8 "$LIVEF") (expected $FROM); $PSVC health $(wait200 "$PPORT" /portal/health). Send a photo of this screen to Claude."; release; exit 1; }
pyv() { local py="$1"; shift; (cd "$SCR" && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 600 "$py" -W ignore -B "$@" 2>&1); }

if [ "${1:-}" = "--undo" ]; then
  [ "$(m5 "$LIVEF")" = "$FROMFULL" ] && { say "-- $KIT is not installed - nothing to undo."; exit 0; }
  [ "$(m5 "$LIVEF")" = "$TO" ] || { say "!! $LIVEF is $(m8 "$LIVEF"), not this kit's - nothing undone. Tell Claude."; exit 1; }
  [ -f "$BAK" ] && [ "$(m5 "$BAK")" = "$FROMFULL" ] || { say "!! no good backup $BAK - nothing undone. Tell Claude."; exit 1; }
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo" > "$LOCK/owner"; pause_doctor
  \cp -p "$BAK" "$LIVEF"; "$SYSTEMCTL" restart "$PSVC"
  p=$(wait200 "$PPORT" /portal/health); release
  [ "$p" = 200 ] && [ "$(m5 "$LIVEF")" = "$FROMFULL" ] || { say "!! UNDONE but $PSVC health $p, portal.py $(m8 "$LIVEF") - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE (portal.py back at $FROM; $PSVC restarted, health 200). The old home is back."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$TO" ] && [ "$(m5 "$KDIR/$N")" = "$TO" ] || { say "!! [1/5] the kit's $N is not as built - nothing installed"; exit 1; }
[ "$(m5 "$LIVEF")" = "$TO" ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$LIVEF")" = "$FROMFULL" ] || stop "!! [2/5] $LIVEF is $(m8 "$LIVEF"), expected $FROM - it changed after this kit was built: STOP, nothing installed. Tell Claude."
PYTHONPYCACHEPREFIX="$SCR/pyc" "$VPY" -W ignore -m py_compile "$KDIR/$N" || stop "!! [2/5] $N does not compile on $VPY - nothing installed"
say "[2/5] the live pin exact ($FROM); the new portal.py compiles"
R=$(pyv "$VPY" "$KDIR/walk_s891_portal.py" --live "$PD" --files "$KDIR" --box | tail -1)
case "$R" in "WALK S891 PORTAL: 13 green, 0 red") ;; *) pyv "$VPY" "$KDIR/walk_s891_portal.py" --live "$PD" --files "$KDIR" --box | grep -E "^RED" | head -6; stop "!! [3/5] walk_s891_portal on the new file: $R - nothing installed";; esac
Rc=$(pyv "$VPY" "$KDIR/walk_s891_portal.py" --live "$PD" --expect-red --box | tail -1)
case "$Rc" in *"NOT AS IT MUST BE"*) stop "!! [3/5] walk_s891_portal's control (the live file): $Rc - nothing installed";; *"AS IT MUST BE"*) ;; *) stop "!! [3/5] walk_s891_portal's control did not finish ($Rc) - nothing installed";; esac
say "[3/5] $R (control on the live file: red as it must be) -- made-up secrets, nothing of the live store read"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; nothing live changed"; exit 0; fi
p0=$(hget "$PPORT" /portal/health); [ "$p0" = 200 ] || stop "!! [4/5] $PSVC health before the install: $p0 - nothing installed"
{ \cp -p "$LIVEF" "$BAK" && [ "$(m5 "$BAK")" = "$FROMFULL" ]; } || stop "!! [4/5] could not write the backup $BAK - nothing placed"
ST="$PD/.$N.s891"; { cat "$KDIR/$N" > "$ST" && chmod --reference="$LIVEF" "$ST" 2>/dev/null; chown --reference="$LIVEF" "$ST" 2>/dev/null; [ "$(m5 "$ST")" = "$TO" ]; } || stop "!! [4/5] could not stage $N - nothing placed"
pause_doctor
mv -f "$ST" "$LIVEF" || restore "the rename of $N"
[ "$(m5 "$LIVEF")" = "$TO" ] || restore "read back of $N"
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
p1=$(wait200 "$PPORT" /portal/health); [ "$p1" = 200 ] || restore "$PSVC health $p1 after the restart"
pg=$(hget "$PPORT" /portal); case "$pg" in 200|302|303) ;; *) restore "/portal answered $pg";; esac
release
say "[4/5] placed and read back: portal.py at its TO pin ($(echo "$TO" | cut -c1-8)); $PSVC restarted (health $p1; /portal $pg) $(TZ=Asia/Kolkata date '+%H:%M IST')"
say "[5/5] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""; say "$KIT: DONE. Open your home: https://followup.dr-manoj.in/portal"; exit 0
