#!/bin/bash
# =============================================================================
#  install_S858_PATIENTS_TILE.sh . kit S858 (17-Nov-2026, session S478, the parent) . D997 item 3 (S816's pattern)
#  The owner's ask of 17:10 IST 17-Nov: a tile of its own for the Patients page. On his home a NEW tile
#  "Patients -- month by month" (/finance/console/patients) right after the Patients folder; a doctor tile by role, alone in
#  its own group so his folded home draws it flat. Nobody else's home changes (the walk proves it for every role and login).
#    /root/portal/portal.py 8f60b310 -> cb37c7fb  .  /root/portal/tile_grants.json b7b1fabf -> 8299e8d4 (manoj's order only)
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s858kit && cp -rp /root/deploy/repo/deploy_kits/S858_PATIENTS_TILE /tmp/s858kit && bash /tmp/s858kit/install_S858_PATIENTS_TILE.sh
#  DRY=1 runs every gate and writes nothing.   Undo:  bash /tmp/s858kit/install_S858_PATIENTS_TILE.sh --undo
# =============================================================================
set -u
KIT="S858_PATIENTS_TILE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F1="$ROOT/portal/portal.py";        FROM1=8f60b3106e6b2b9687495b01a74b90c5; TO1=cb37c7fb3b24341f57950cc63a54e3fc; BAK1="$F1.bak_S858_${FROM1:0:8}"
F2="$ROOT/portal/tile_grants.json"; FROM2=b7b1fabfa4106ce1041fa13b9ac2bbcf; TO2=8299e8d44b5938343d2a2c66315f3f67; BAK2="$F2.bak_S858_${FROM2:0:8}"
DOORS="/portal /portal/console /portal/inbox /portal/messages /portal/wa"
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
  [ -f "$BAK1" ] && \cp -p "$BAK1" "$F1"; [ -f "$BAK2" ] && \cp -p "$BAK2" "$F2"
  rm -f "$F1.s858new" "$F2.s858new"
  find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  [ "$(m5 "$F1")" = "$FROM1" ] && [ "$(m5 "$F2")" = "$FROM2" ] && echo 1 || echo 0
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting both files back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "   portal.py and tile_grants.json are back byte-identically; the home screen is as it was" \
                || echo "   !! NOT back -- copy $BAK1 and $BAK2 back by hand"
  echo "   portal health $(wait200 phz). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 portal.py)" = "$TO1" ] && [ "$(m5 tile_grants.json)" = "$TO2" ] || stop "the kit's files are not the built ones"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK1" ] && [ "$(m5 "$BAK1")" = "$FROM1" ] && [ -f "$BAK2" ] && [ "$(m5 "$BAK2")" = "$FROM2" ] || stop "no good backups -- nothing to undo"
  L1=$(m5 "$F1"); L2=$(m5 "$F2")
  { [ "$L1" = "$TO1" ] || [ "$L1" = "$FROM1" ]; } && { [ "$L2" = "$TO2" ] || [ "$L2" = "$FROM2" ]; } || stop "a file has been changed since this kit (a later kit is on top) -- not undone"
  take_lock
  ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  hu=$(wait200 phz)
  [ "$ok" = 1 ] && [ "$hu" = 200 ] && { echo "UNDONE: both files are back byte-identically; the Patients tile is gone from the home; portal health $hu"; exit 0; }
  echo "!! not back (files back: $ok, portal health $hu) -- send a photo of this screen to Claude"; exit 1
fi
echo "[1/5] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1"); L2=$(m5 "$F2")
if [ "$L1" = "$TO1" ] && [ "$L2" = "$TO2" ]; then echo "-- ALREADY INSTALLED. Nothing written. portal $(phz)"; exit 0; fi
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not the expected one (live ${L1:0:8}, kit expects ${FROM1:0:8})"
[ "$L2" = "$FROM2" ] || stop "the live $F2 is not the expected one (live ${L2:0:8}, kit expects ${FROM2:0:8})"
pyc "$APY" "$KDIR/portal.py" || stop "the kit's portal.py does not compile with $APY"
pyc "$VPY" "$KDIR/portal.py" || stop "the kit's portal.py does not compile with $VPY"
"$VPY" -c "import json,sys; json.load(open(sys.argv[1],encoding='utf-8'))" "$KDIR/tile_grants.json" 2>/dev/null || stop "the kit's tile_grants.json does not read as JSON"
echo "[2/5] the live files are ${FROM1:0:8} / ${FROM2:0:8}; the kit's compile and read"
SCR=$(mktemp -d /tmp/s858.XXXX) || stop "no scratch folder"; chmod 700 "$SCR"
R=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s858.py" "$F1" "$KDIR/portal.py" "$F2" "$KDIR/tile_grants.json" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) (cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s858.py" "$F1" "$KDIR/portal.py" "$F2" "$KDIR/tile_grants.json" 2>&1 | grep '^BAD' | head -6); stop "the walk is not green ($R)";; esac
R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s858.py" "$F1" "$F1" "$F2" "$F2" 2>&1 | tail -1)
case "$R2" in "WALK RED"*) ;; *) stop "the control (the live files as both) did not go red ($R2)";; esac
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[3/5] the walk (every role and every login's home, before against after): $R | control: $R2"
c1=$(phz); [ "$c1" = 200 ] || stop "the portal is not healthy before the install (health $c1)"
D0=$(doors)
echo "[4/5] before: portal health $c1; the doors without a login: $D0"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
take_lock
{ \cp -p "$F1" "$BAK1" && [ "$(m5 "$BAK1")" = "$FROM1" ]; } || stop "could not keep a backup of $F1"
{ \cp -p "$F2" "$BAK2" && [ "$(m5 "$BAK2")" = "$FROM2" ]; } || stop "could not keep a backup of $F2"
PLACED=1
for pair in "portal.py:$F1:$BAK1:$TO1" "tile_grants.json:$F2:$BAK2:$TO2"; do
  IFS=: read -r src dst ref to <<< "$pair"
  \cp "$KDIR/$src" "$dst.s858new" && chmod --reference="$ref" "$dst.s858new" && chown --reference="$ref" "$dst.s858new" 2>/dev/null; mv -f "$dst.s858new" "$dst" || restore "$src could not be placed"
  [ "$(m5 "$dst")" = "$to" ] || restore "$src read-back did not match"
done
find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
c2=$(wait200 phz); [ "$c2" = 200 ] || restore "portal health $c2"
D1=$(doors); [ "$D1" = "$D0" ] || restore "a door answers differently after the restart (before: $D0 | after: $D1)"
sleep "${WAITS:-2}"
JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'ungrouped tile|group not in GROUP_ORDER|a group without a face|NOT mounted|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|AssertionError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'tile|mounted|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
[ "$(m5 "$F1")" = "$TO1" ] && [ "$(m5 "$F2")" = "$TO2" ] || restore "a file is not the placed one at the end"
PLACED=0
echo "[5/5] placed (backups *.bak_S858_*); the portal restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): health $c2; every door answers as before; journal clean"
echo "$KIT: DONE. Your home now has its own Patients tile (Patients -- month by month), right after the Patients folder; it opens the Patients page. Nobody else's home changed."
