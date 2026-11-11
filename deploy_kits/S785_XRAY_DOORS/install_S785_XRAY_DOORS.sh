#!/bin/bash
# =============================================================================
#  install_S785_XRAY_DOORS.sh . kit S785 (11-Nov-2026, session S427, the parent) . the owner 06:34 IST: "Cannot find the flow from my
#  portal page or through my command console" -> 06:38 "go".
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s785kit && cp -rp /root/deploy/repo/deploy_kits/S785_XRAY_DOORS /tmp/s785kit && bash /tmp/s785kit/install_S785_XRAY_DOORS.sh
#  /root/portal/portal.py 59b5c252 -> TO: an "X-ray photos" tile in the Patients group (the doctors; Dr Bhawna's 'only' keeps it off hers).
#  /root/finance/owner_console.py 27d31775 -> TO: a Needs-you line while X-ray photos older than 7 days wait (S782's).
#  Undo:  bash /tmp/s785kit/install_S785_XRAY_DOORS.sh --undo
# =============================================================================
set -u
KIT="S785_XRAY_DOORS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F1="$ROOT/portal/portal.py";          FROM1=59b5c252141f25488cafba91ef3f8e55; TO1=34750b241d6e4bb9fb57bd52beebe1ee; BAK1="$F1.bak_S785_${FROM1:0:8}"
F2="$ROOT/finance/owner_console.py";  FROM2=27d31775f81ab9538969be8c2a01d1af; TO2=1a3d4fd4a212429f3d7f604680a1cc32; BAK2="$F2.bak_S785_${FROM2:0:8}"
CS782=c259e6a258c19f1222820b47e9e9ad34
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
fhz() { hcode "http://127.0.0.1:$FIN_PORT/finance/healthz"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
putback() { [ -f "$BAK1" ] && \cp -p "$BAK1" "$F1"; [ -f "$BAK2" ] && \cp -p "$BAK2" "$F2"; find "$ROOT/portal" "$ROOT/finance" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; [ "$(m5 "$F1")" = "$FROM1" ] && [ "$(m5 "$F2")" = "$FROM2" ] && echo 1 || echo 0; }
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting both files back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$FSVC" || true; "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "   portal.py and owner_console.py are back byte-identically" || echo "   !! NOT back -- copy $BAK1 and $BAK2 back by hand"
  echo "   finance healthz $(wait200 fhz) . portal health $(wait200 phz). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 portal/portal.py)" = "$TO1" ] && [ "$(m5 finance/owner_console.py)" = "$TO2" ] || stop "the kit's files are not the built ones"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK1" ] && [ -f "$BAK2" ] || stop "no backups -- nothing to undo"
  ok=$(putback); "$SYSTEMCTL" restart "$FSVC" || true; "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "UNDONE: portal.py (${FROM1:0:8}) and owner_console.py (${FROM2:0:8}) are back; finance $(wait200 fhz) . portal $(wait200 phz)" || echo "!! not back -- send a photo"
  exit 0
fi
echo "[1/6] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1"); L2=$(m5 "$F2")
[ "$L1" = "$TO1" ] && [ "$L2" = "$TO2" ] && { echo "-- ALREADY INSTALLED. Nothing written. finance $(fhz) . portal $(phz)"; exit 0; }
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not the expected one (live ${L1:0:8}, kit expects ${FROM1:0:8})"
[ "$L2" = "$FROM2" ] || stop "the live $F2 is not the expected one (live ${L2:0:8}, kit expects ${FROM2:0:8})"
[ "$(m5 "$ROOT/finance/check_screens.py")" = "$CS782" ] || stop "S782's check_screens.py (${CS782:0:8}) is not live -- install S782 first"
SCR=$(mktemp -d /tmp/s785.XXXX); chmod 700 "$SCR"; mkdir -p "$SCR/remake" "$SCR/live/portal" "$SCR/live/finance"
"$APY" -B "$KDIR/make_s785.py" "$F1" "$F2" "$SCR/remake" >/dev/null 2>&1 && [ "$(m5 "$SCR/remake/portal/portal.py")" = "$TO1" ] && [ "$(m5 "$SCR/remake/finance/owner_console.py")" = "$TO2" ] || stop "make_s785.py on the live bytes does not give the kit's files"
for f in portal/portal.py finance/owner_console.py; do
  "$APY" -W ignore -B -m py_compile "$KDIR/$f" 2>/dev/null || stop "$f does not compile with $APY"
  "$VPY" -W ignore -B -m py_compile "$KDIR/$f" 2>/dev/null || stop "$f does not compile with $VPY"
done
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[2/6] the live files are ${FROM1:0:8} and ${FROM2:0:8}; the kit's are those + the S785 edits (remade on the box); both compile under both pythons"
\cp -p "$F1" "$SCR/live/portal/portal.py"; \cp -p "$F2" "$SCR/live/finance/owner_console.py"
R=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$APY" -W ignore -B "$KDIR/walk_s785.py" "$KDIR" "$ROOT" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) stop "the S785 walk is not green ($R)";; esac
R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$APY" -W ignore -B "$KDIR/walk_s785.py" "$SCR/live" "$ROOT" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live files did not go red ($R2)";; esac
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[3/6] the walk: $R | the live files: $R2"
[ "$(fhz)" = 200 ] && [ "$(phz)" = 200 ] || stop "finance or portal is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
echo "[4/6] the build lock taken; the doctor's auto-fix paused for the restarts"
{ \cp -p "$F1" "$BAK1" && [ "$(m5 "$BAK1")" = "$FROM1" ]; } || stop "could not keep a backup of $F1"
{ \cp -p "$F2" "$BAK2" && [ "$(m5 "$BAK2")" = "$FROM2" ]; } || stop "could not keep a backup of $F2"
PLACED=1
for pair in "portal/portal.py:$F1:$BAK1:$TO1" "finance/owner_console.py:$F2:$BAK2:$TO2"; do
  IFS=: read -r src dst bak to <<< "$pair"
  \cp "$KDIR/$src" "$dst.s785new" && chmod --reference="$bak" "$dst.s785new" && chown --reference="$bak" "$dst.s785new" 2>/dev/null; mv -f "$dst.s785new" "$dst" || restore "$src could not be placed"
  [ "$(m5 "$dst")" = "$to" ] || restore "$src read-back did not match"
done
find "$ROOT/portal" "$ROOT/finance" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
c2=$(wait200 phz); [ "$c2" = 200 ] || restore "portal health $c2"
c3=$(hcode "http://127.0.0.1:$FIN_PORT/finance/console"); case "$c3" in 302|401|403|303) ;; *) restore "the console answered $c3 without a login";; esac
sleep 2
JL="$("$JOURNALCTL" -u "$FSVC" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'portal\.py|owner_console|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|AssertionError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'portal|console|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restarts"; }
PLACED=0
echo "[5/6] placed (backups $BAK1, $BAK2); restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): finance $c1 . portal $c2; the console's door closed ($c3); journal clean"
echo "[6/6] $KIT: DONE. Your portal: Patients -> X-ray photos. Your console: Needs you shows the X-ray line while older photos wait."
