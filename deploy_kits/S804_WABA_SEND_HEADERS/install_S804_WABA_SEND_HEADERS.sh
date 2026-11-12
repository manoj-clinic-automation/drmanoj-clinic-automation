#!/bin/bash
# =============================================================================
#  install_S804_WABA_SEND_HEADERS.sh . kit S804 (12-Nov-2026, session S439, the parent) . F-1294 (F-1031's cause, S802).
#  /root/wa/waba.py -- the send arm behind the older approve-and-send page (wa_approve.py, service wa-approve) -- still sends
#  through urllib, which re-cases header names on the wire ("X-MYOP-COMPANY-ID" leaves as "X-Myop-Company-Id"); MyOperator's
#  gateway refuses that form at its authorizer. send_template's ONE request per try moves to http.client (names as written):
#    /root/wa/waba.py 031b4642 -> 82f3503b
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s804kit && cp -rp /root/deploy/repo/deploy_kits/S804_WABA_SEND_HEADERS /tmp/s804kit && bash /tmp/s804kit/install_S804_WABA_SEND_HEADERS.sh
#  FIRST it is PROVEN on the live gateway -- NOTHING SENT: fresh made-up keys (no earlier request can help them), and the real key
#  only with an empty number and empty text. Placed ONLY on PROVEN. DRY=1 runs the gates and the proof, and changes nothing.
#  Undo:  bash /tmp/s804kit/install_S804_WABA_SEND_HEADERS.sh --undo
# =============================================================================
set -u
KIT="S804_WABA_SEND_HEADERS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
APORT="${APORT:-8101}"; ASVC="${ASVC:-wa-approve}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F1="$ROOT/wa/waba.py"; FROM1=031b46429c08832922d7a08d3a33a87f; TO1=82f3503b3e63a6852585409182af33ae; BAK1="$F1.bak_S804_${FROM1:0:8}"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""; ACT=""; CB=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
adoor() { hcode "http://127.0.0.1:$APORT/wa-approve"; }
waitsame() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(adoor); [ "$h" = "$1" ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
putback() {
  [ -f "$BAK1" ] && \cp -p "$BAK1" "$F1"; rm -f "$F1.s804new"; rm -f "$ROOT"/wa/__pycache__/waba.*.pyc 2>/dev/null
  [ "$(m5 "$F1")" = "$FROM1" ] && echo 1 || echo 0
}
restart_page() { [ "$ACT" = active ] && { "$SYSTEMCTL" restart "$ASVC" || true; }; }
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting waba.py back"
  local ok; ok=$(putback); restart_page
  [ "$ok" = 1 ] && echo "   waba.py is back byte-identically" || echo "   !! NOT back -- copy $BAK1 back by hand"
  [ "$ACT" = active ] && echo "   the approve page's door answers $(waitsame "$CB") (before: $CB)."
  echo "   Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP
probe_installed() { ( cd /tmp && S804_ENV_FILE="$ROOT/wa/.env" timeout 200 "$VPY" -W ignore -B "$KDIR/prove_s804.py" "$ROOT/wa" --installed 2>&1 | tail -1 ); }

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
# The kit carries NO copy of waba.py (its opening notes hold the account's IDs -- no number goes into the repository, F-185,
# F-1293): make_s804.py makes it on this box from the live bytes and the result is checked against the pin below.
ACT=$("$SYSTEMCTL" is-active "$ASVC" 2>/dev/null | head -1)
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK1" ] && [ "$(m5 "$BAK1")" = "$FROM1" ] || stop "no good backup -- nothing to undo"
  L1=$(m5 "$F1")
  { [ "$L1" = "$TO1" ] || [ "$L1" = "$FROM1" ]; } || stop "waba.py has been changed since this kit (a later kit is on top) -- not undone"
  CB=$(adoor); ok=$(putback); restart_page
  [ "$ok" = 1 ] && { echo "UNDONE: waba.py is back as before$([ "$ACT" = active ] && echo "; the approve page's door answers $(waitsame "$CB")")"; exit 0; }
  echo "!! not back -- send a photo"; exit 1
fi
echo "[1/6] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1")
if [ "$L1" = "$TO1" ]; then
  echo "-- ALREADY INSTALLED. Nothing written."; echo "   $(probe_installed)"; exit 0; fi
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not the expected one (live ${L1:0:8}, kit expects ${FROM1:0:8})"
SCR=$(mktemp -d /tmp/s804.XXXX) || stop "no scratch folder could be made in /tmp"
[ -n "$SCR" ] && [ -d "$SCR" ] || stop "no scratch folder could be made in /tmp"
chmod 700 "$SCR"; mkdir -p "$SCR/remake" "$SCR/live/wa"
"$APY" -B "$KDIR/make_s804.py" "$F1" "$SCR/remake" >/dev/null 2>&1 && [ "$(m5 "$SCR/remake/wa/waba.py")" = "$TO1" ] \
  || stop "make_s804.py on the live bytes does not give the pinned file"
for f in "$SCR/remake/wa/waba.py" "$KDIR/prove_s804.py"; do
  "$APY" -W ignore -B -m py_compile "$f" 2>/dev/null || stop "$(basename "$f") does not compile with $APY"
  "$VPY" -W ignore -B -m py_compile "$f" 2>/dev/null || stop "$(basename "$f") does not compile with $VPY"
done
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[2/6] the live waba.py is ${FROM1:0:8}; the kit's is that with the one request moved to http.client (remade on the box); it compiles"
\cp -p "$F1" "$SCR/live/wa/waba.py"
R=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s804.py" "$SCR/remake" "$KDIR" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) (cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s804.py" "$SCR/remake" "$KDIR" 2>&1 | grep '^BAD' | head -6); stop "the S804 walk is not green ($R)";; esac
R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s804.py" "$SCR/live" "$KDIR" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live file did not go red ($R2)";; esac
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[3/6] the walk (a stand-in gateway on this machine, nothing leaves it): $R | the live file: $R2"
echo "[4/6] the proof on MyOperator's gateway -- NOTHING SENT:"
( cd /tmp && S804_ENV_FILE="$ROOT/wa/.env" timeout 300 "$VPY" -W ignore -B "$KDIR/prove_s804.py" "$SCR/remake/wa" > "$SCR/prove.txt" 2>&1 )
find "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
sed 's/^/      /' "$SCR/prove.txt" | head -12
V=$(grep '^PROVE: ' "$SCR/prove.txt" | tail -1 | awk '{print $2}')
[ -n "$V" ] || stop "the proof gave no result"
# The approve page's door is READ before anything is placed; after the restart it must answer the same (F-1265).
if [ "$ACT" = active ]; then
  CB=$(adoor)
  case "$CB" in 000|"") stop "the approve page's service ($ASVC) is running but its door does not answer -- not healthy before the install";; esac
  echo "      the approve page ($ASVC) is running; its door answers $CB without a key. It is restarted in a moment -- do not run this while a send from the approve page is going on."
else
  echo "      the approve page's service ($ASVC) is not running (${ACT:-unknown}) -- it will not be restarted"
fi
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: the proof says $V; nothing written."; exit 0; }
if [ "$V" != "PROVEN" ]; then
  echo "[5/6] NOT APPLIED -- the proof says $V: the table above does not show that header names as written get through."
  echo "[6/6] $KIT: NOTHING CHANGED. Send a photo of this screen to Claude -- the lines above are what is needed."
  exit 0
fi
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
{ \cp -p "$F1" "$BAK1" && [ "$(m5 "$BAK1")" = "$FROM1" ]; } || stop "could not keep a backup of $F1"
PLACED=1
\cp "$SCR/remake/wa/waba.py" "$F1.s804new" && chmod --reference="$BAK1" "$F1.s804new" && chown --reference="$BAK1" "$F1.s804new" 2>/dev/null; mv -f "$F1.s804new" "$F1" || restore "waba.py could not be placed"
[ "$(m5 "$F1")" = "$TO1" ] || restore "waba.py read-back did not match"
rm -f "$ROOT"/wa/__pycache__/waba.*.pyc 2>/dev/null
T0=$(date '+%Y-%m-%d %H:%M:%S')
if [ "$ACT" = active ]; then
  "$SYSTEMCTL" restart "$ASVC" || restore "restart $ASVC"
  c2=$(waitsame "$CB"); [ "$c2" = "$CB" ] || restore "the approve page's door answers $c2 after the restart (before: $CB)"
  sleep 2
  JL="$("$JOURNALCTL" -u "$ASVC" --since "$T0" --no-pager 2>/dev/null)"
  JR="$(printf '%s\n' "$JL" | grep -c -i -E 'could not import waba|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|AssertionError|Traceback|Worker failed to boot')"
  [ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'waba|Error|Traceback|boot' | head -5; restore "journal: $JR error line(s) since the restart"; }
fi
PI=""
for _try in 1 2 3; do PI=$(probe_installed); case "$PI" in *"let through"*) break;; esac; sleep 4; done
case "$PI" in *"let through"*) ;; *) restore "the installed waba.send_template is not let through, three tries ($PI)";; esac
PLACED=0
if [ "$ACT" = active ]; then
  echo "[5/6] placed (backup $(basename "$BAK1")); $ASVC restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): its door answers $c2 as before; journal clean"
else
  echo "[5/6] placed (backup $(basename "$BAK1")); $ASVC was not running and was left so"
fi
echo "      $PI"
echo "[6/6] $KIT: DONE. The older approve-and-send page's sender now reaches MyOperator with the header names as written. Nothing was sent to anyone."
