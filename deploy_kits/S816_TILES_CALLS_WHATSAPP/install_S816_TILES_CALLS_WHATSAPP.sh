#!/bin/bash
# =============================================================================
#  install_S816_TILES_CALLS_WHATSAPP.sh . kit S816 (13-Nov-2026, session S447, the parent) . the owner's approved mock-up
#  "the tiles" (artifact 8J3R3QtW9awbajmLN4rmic; his finding F-1324): on the portal's home screen
#    1. the tile "WhatsApp messages" moves from Patients to Calls & WhatsApp, with a new small line
#    2. the tile "Follow-up WhatsApps" is retired      3. the tile "WhatsApp Approvals" is retired
#    4. the folded System group's small line no longer names "WhatsApp approvals"
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s816kit && cp -rp /root/deploy/repo/deploy_kits/S816_TILES_CALLS_WHATSAPP /tmp/s816kit && bash /tmp/s816kit/install_S816_TILES_CALLS_WHATSAPP.sh
#  ONE live file changes: /root/portal/portal.py 3a0f7cd1 -> 8f60b310, REMADE on the box from the live bytes by make_s816.py
#  (the kit carries no copy of it). No route, no page, no grant, no other tile, no other group face. The wa-approve SERVICE IS NOT TOUCHED: the
#  clinic-doctor watches it (README). DRY=1 runs every gate and writes nothing.
#  Undo:  bash /tmp/s816kit/install_S816_TILES_CALLS_WHATSAPP.sh --undo
# =============================================================================
set -u
KIT="S816_TILES_CALLS_WHATSAPP"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F1="$ROOT/portal/portal.py"; FROM1=3a0f7cd17803d8b74af7b67eb4d68964; TO1=8f60b3106e6b2b9687495b01a74b90c5; BAK1="$F1.bak_S816_${FROM1:0:8}"
DOORS="/portal /portal/messages /portal/console /portal/inbox /portal/wa /portal/gist"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
doors() { local o=""; for d in $DOORS; do o="$o $d=$(hcode "http://127.0.0.1:$PPORT$d")"; done; echo "${o# }"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${WAITS:-3}"; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
pyc() { "$1" -W ignore -B -c "import sys;compile(open(sys.argv[1],encoding='utf-8').read(),sys.argv[1],'exec')" "$2" 2>/dev/null; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
take_lock() {
  mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
  HAVE_LOCK=1; echo "$KIT $$ $(TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M:%S IST')" > "$LOCK/owner"
  if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(TZ=Asia/Kolkata date '+%F %T IST')" > "$OFFSW" && OFF_MINE=1; fi
}
putback() {
  [ -f "$BAK1" ] && \cp -p "$BAK1" "$F1"
  rm -f "$F1.s816new"
  find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  [ "$(m5 "$F1")" = "$FROM1" ] && echo 1 || echo 0
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting the old file back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "   portal.py is back byte-identically (${FROM1:0:8}); the home screen is as it was" \
                || echo "   !! NOT back -- copy $BAK1 back over $F1 by hand"
  echo "   portal health $(wait200 phz). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK1" ] && [ "$(m5 "$BAK1")" = "$FROM1" ] || stop "no good backup of portal.py ($BAK1) -- nothing to undo"
  LU=$(m5 "$F1")
  [ "$LU" = "$TO1" ] || [ "$LU" = "$FROM1" ] || stop "portal.py has been changed since this kit (live ${LU:0:8}) -- a later kit is on top; not undone"
  take_lock
  ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  hu=$(wait200 phz)
  [ "$ok" = 1 ] && [ "$hu" = 200 ] && { echo "UNDONE: portal.py is back byte-identically (${FROM1:0:8}); the three tiles are where they were; portal health $hu"; exit 0; }
  echo "!! not back (file back: $ok, portal health $hu) -- send a photo of this screen to Claude"; exit 1
fi
echo "[1/5] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1")
if [ "$L1" = "$TO1" ]; then echo "-- ALREADY INSTALLED. Nothing written. portal $(phz)"; exit 0; fi
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not the expected one (live ${L1:0:8}, kit expects ${FROM1:0:8})"
SCR=$(mktemp -d /tmp/s816.XXXX) || stop "no scratch folder"; chmod 700 "$SCR"; mkdir -p "$SCR/remake"
"$APY" -B "$KDIR/make_s816.py" "$F1" "$SCR/remake" >/dev/null 2>&1 && [ "$(m5 "$SCR/remake/portal/portal.py")" = "$TO1" ] \
  || stop "make_s816.py on the live bytes does not give the pinned portal.py (${TO1:0:8})"
NEW="$SCR/remake/portal/portal.py"
pyc "$APY" "$NEW" || stop "the remade portal.py does not compile with $APY"
pyc "$VPY" "$NEW" || stop "the remade portal.py does not compile with $VPY"
echo "[2/5] the live portal.py is ${FROM1:0:8}; remade on the box from it: ${TO1:0:8} (the pinned one); it compiles"
R=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s816.py" "$F1" "$NEW" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) (cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s816.py" "$F1" "$NEW" 2>&1 | grep '^BAD' | head -6); stop "the S816 walk is not green ($R)";; esac
R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s816.py" "$F1" "$F1" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live file did not go red ($R2)";; esac
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[3/5] the walk (every role's tiles, before against after; made-up logins): $R | the live file alone: $R2"
[ "$(m5 "$F1")" = "$FROM1" ] || stop "the live portal.py changed while the gates ran"
c1=$(phz); [ "$c1" = 200 ] || stop "the portal is not healthy before the install (health $c1)"
D0=$(doors)
case " $D0 " in *" /portal/messages=302 "*|*" /portal/messages=303 "*|*" /portal/messages=401 "*|*" /portal/messages=403 "*) ;; *) stop "the WhatsApp messages page does not answer as a closed door before the install ($D0)";; esac
echo "[4/5] before: portal health $c1; the doors without a login: $D0"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
take_lock
{ \cp -p "$F1" "$BAK1" && [ "$(m5 "$BAK1")" = "$FROM1" ]; } || stop "could not keep a backup of $F1"
PLACED=1
\cp "$NEW" "$F1.s816new" && chmod --reference="$BAK1" "$F1.s816new" && chown --reference="$BAK1" "$F1.s816new" 2>/dev/null; mv -f "$F1.s816new" "$F1" || restore "portal.py could not be placed"
[ "$(m5 "$F1")" = "$TO1" ] || restore "portal.py read-back did not match"
find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
c2=$(wait200 phz); [ "$c2" = 200 ] || restore "portal health $c2"
D1=$(doors); [ "$D1" = "$D0" ] || restore "a door answers differently after the restart (before: $D0 | after: $D1)"
sleep "${WAITS:-2}"
JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'ungrouped tile|group not in GROUP_ORDER|a group without a face|NOT mounted|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|AssertionError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'tile|mounted|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
[ "$(m5 "$F1")" = "$TO1" ] || restore "portal.py is not the placed one at the end"
PLACED=0
WA=$("$SYSTEMCTL" is-active wa-approve 2>/dev/null | head -1)
echo "[5/5] placed (backup $BAK1); the portal restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): health $c2; every door answers as before ($D1); journal clean; the wa-approve service was not touched (it is: ${WA:-not read})"
echo "$KIT: DONE. On your portal, WhatsApp messages now sits under Calls & WhatsApp, and the Follow-up WhatsApps and WhatsApp Approvals tiles are gone from the home screen (the System folder's small line no longer names WhatsApp approvals); nothing else has changed."
