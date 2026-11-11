#!/bin/bash
# =============================================================================
#  install_S793_WA_OPEN_IN_MYOP.sh . kit S793 (11-Nov-2026, session S431, the parent) . the owner 17:46 IST: an "Open in MyOperator"
#  button on each chat of his WhatsApp inbox, so he replies through MyOperator while the clinic's own sends fail (F-1031, ticket 691386).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s793kit && cp -rp /root/deploy/repo/deploy_kits/S793_WA_OPEN_IN_MYOP /tmp/s793kit && bash /tmp/s793kit/install_S793_WA_OPEN_IN_MYOP.sh
#  /root/portal/portal_inbox.py f89ad282 (S701) -> TO (the portal restarted once).   Undo: bash /tmp/s793kit/install_S793_WA_OPEN_IN_MYOP.sh --undo
# =============================================================================
set -u
KIT="S793_WA_OPEN_IN_MYOP"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F1="$ROOT/portal/portal_inbox.py"; FROM1=f89ad282bf81982af7f5e8b15cb238ac; TO1=06e2c28e412ca1b2359182d16ff0cf65; BAK1="$F1.bak_S793_${FROM1:0:8}"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
putback() { [ -f "$BAK1" ] && \cp -p "$BAK1" "$F1"; find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; [ "$(m5 "$F1")" = "$FROM1" ] && echo 1 || echo 0; }
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting portal_inbox.py back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "   portal_inbox.py is back byte-identically" || echo "   !! NOT back -- copy $BAK1 back by hand"
  echo "   portal health $(wait200 phz). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 portal_inbox.py)" = "$TO1" ] || stop "the kit's file is not the built one"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK1" ] || stop "no backup -- nothing to undo"
  ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "UNDONE: portal_inbox.py (${FROM1:0:8}) is back; portal $(wait200 phz)." || echo "!! not back -- send a photo"
  exit 0
fi
echo "[1/6] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1")
[ "$L1" = "$TO1" ] && { echo "-- ALREADY INSTALLED. Nothing written. portal $(phz)"; exit 0; }
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not the expected one (live ${L1:0:8}, kit expects ${FROM1:0:8})"
SCR=$(mktemp -d /tmp/s793.XXXX); chmod 700 "$SCR"; mkdir -p "$SCR/remake" "$SCR/live"
"$APY" -B "$KDIR/make_s793.py" "$F1" "$SCR/remake" >/dev/null 2>&1 && [ "$(m5 "$SCR/remake/portal_inbox.py")" = "$TO1" ] || stop "make_s793.py on the live bytes does not give the kit's file"
"$APY" -W ignore -B -m py_compile "$KDIR/portal_inbox.py" 2>/dev/null || stop "portal_inbox.py does not compile with $APY"
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[2/6] the live file is ${FROM1:0:8}; the kit's is that + the S793 button (remade on the box); it compiles"
\cp -p "$F1" "$SCR/live/"
R=$(cd "$SCR" && "$APY" -B "$KDIR/walk_s793.py" "$KDIR" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) (cd "$SCR" && "$APY" -B "$KDIR/walk_s793.py" "$KDIR" 2>&1 | grep '^BAD' | head -6); stop "the S793 walk on the kit's file is not green ($R)";; esac
R2=$(cd "$SCR" && "$APY" -B "$KDIR/walk_s793.py" "$SCR/live" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live file did not go red ($R2)";; esac
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[3/6] walk: $R | the live file: $R2"
[ "$(phz)" = 200 ] || stop "the portal is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
echo "[4/6] the build lock taken; the doctor's auto-fix paused for the restart"
{ \cp -p "$F1" "$BAK1" && [ "$(m5 "$BAK1")" = "$FROM1" ]; } || stop "could not keep a backup of $F1"
PLACED=1
\cp "$KDIR/portal_inbox.py" "$F1.s793new" && chmod --reference="$BAK1" "$F1.s793new" && chown --reference="$BAK1" "$F1.s793new" 2>/dev/null; mv -f "$F1.s793new" "$F1" || restore "could not be placed"
[ "$(m5 "$F1")" = "$TO1" ] || restore "read-back did not match"
find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
c1=$(wait200 phz); [ "$c1" = 200 ] || restore "portal health $c1"
# read live at S431 (20:1x IST, without a login): /portal/inbox/health -> 200 {"inbox":"ok","kit":"S701"}; /portal/inbox -> a redirect to the login
c2=$(curl -s -m 8 "http://127.0.0.1:$PPORT/portal/inbox/health"); case "$c2" in *'"S793"'*) ;; *) restore "the inbox health does not name S793 ($c2)";; esac
c3=$(hcode "http://127.0.0.1:$PPORT/portal/inbox"); case "$c3" in 301|302|303|307|308|401|403) ;; *) restore "his inbox answered $c3 without a login";; esac
sleep 2
JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -c -i -E 'portal_inbox|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'inbox|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
PLACED=0
echo "[5/6] placed (backup $BAK1); restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): portal $c1; inbox health names S793; the inbox's door closed without a login ($c3); journal clean"
echo "[6/6] $KIT: DONE. Each chat in your WhatsApp inbox has an 'Open in MyOperator' button beside Call."
