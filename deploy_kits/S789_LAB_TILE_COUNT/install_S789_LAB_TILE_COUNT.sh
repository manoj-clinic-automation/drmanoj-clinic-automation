#!/bin/bash
# =============================================================================
#  install_S789_LAB_TILE_COUNT.sh . kit S788 (11-Nov-2026, session S428, the parent) . the owner 09:14 IST: "the name should be the
#  deciding factor where all other parameters match and the ID is only slightly off" (a 24-Oct photo: the film read another patient's ID, one digit off hers).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s789kit && cp -rp /root/deploy/repo/deploy_kits/S789_LAB_TILE_COUNT /tmp/s789kit && bash /tmp/s789kit/install_S789_LAB_TILE_COUNT.sh
#  /root/finance/check_screens.py 597dd8c9 (S787) -> TO (finance restarted once).   Undo: bash /tmp/s789kit/install_S789_LAB_TILE_COUNT.sh --undo
# =============================================================================
set -u
KIT="S789_LAB_TILE_COUNT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F1="$ROOT/finance/check_screens.py"; FROM1=e86f16e15a2db78ba1c6d5b70bb75766; TO1=dc713523857d668a8fcb930e26cc0fc4; BAK1="$F1.bak_S789_${FROM1:0:8}"
DB="${FINANCE_DB:-$ROOT/finance/finance.db}"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
fhz() { hcode "http://127.0.0.1:$FIN_PORT/finance/healthz"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
putback() { [ -f "$BAK1" ] && \cp -p "$BAK1" "$F1"; find "$ROOT/finance" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; [ "$(m5 "$F1")" = "$FROM1" ] && echo 1 || echo 0; }
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting check_screens.py back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$FSVC" || true
  [ "$ok" = 1 ] && echo "   check_screens.py is back byte-identically" || echo "   !! NOT back -- copy $BAK1 back by hand"
  echo "   finance healthz $(wait200 fhz). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 check_screens.py)" = "$TO1" ] || stop "the kit's file is not the built one"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK1" ] || stop "no backup -- nothing to undo"
  ok=$(putback); "$SYSTEMCTL" restart "$FSVC" || true
  [ "$ok" = 1 ] && echo "UNDONE: check_screens.py (${FROM1:0:8}) is back; finance $(wait200 fhz). (Answers already given stay.)" || echo "!! not back -- send a photo"
  exit 0
fi
echo "[1/6] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1")
[ "$L1" = "$TO1" ] && { echo "-- ALREADY INSTALLED. Nothing written. finance $(fhz)"; exit 0; }
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not the expected one (live ${L1:0:8}, kit expects ${FROM1:0:8} -- S788 first)"
SCR=$(mktemp -d /tmp/s789.XXXX); chmod 700 "$SCR"; mkdir -p "$SCR/remake" "$SCR/live" "$SCR/w7"
"$APY" -B "$KDIR/make_s789.py" "$F1" "$SCR/remake" >/dev/null 2>&1 && [ "$(m5 "$SCR/remake/check_screens.py")" = "$TO1" ] || stop "make_s789.py on the live bytes does not give the kit's file"
"$APY" -W ignore -B -m py_compile "$KDIR/check_screens.py" 2>/dev/null || stop "check_screens.py does not compile with $APY"
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[2/6] the live file is ${FROM1:0:8}; the kit's is that + the S789 change (remade on the box); it compiles"
"$APY" -c "import sqlite3; s=sqlite3.connect('file:$DB?mode=ro', uri=True); d=sqlite3.connect('$SCR/f.db'); s.backup(d); d.close(); s.close()" 2>/dev/null || stop "could not copy finance.db for the walk"
\cp -p "$F1" "$SCR/live/"; \cp -p "$KDIR/check_screens.py" "$KDIR/DUTY_MAP.json.s787" "$SCR/w7/"; \cp -p "$ROOT/finance/records.py" "$SCR/w7/"
R=$(cd "$SCR" && TMPDIR="$SCR" S788_LIBS="$ROOT/finance" timeout 300 "$APY" -W ignore -B "$KDIR/walk_s788.py" "$KDIR" "$SCR/f.db" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) (cd "$SCR" && TMPDIR="$SCR" S788_LIBS="$ROOT/finance" timeout 300 "$APY" -W ignore -B "$KDIR/walk_s788.py" "$KDIR" "$SCR/f.db" 2>&1 | grep -E '^BAD|Error' | head -6); stop "the S788 walk on a copy of today's database is not green ($R)";; esac
R7=$(cd "$SCR" && TMPDIR="$SCR" S787_ANY=1 S787_LIBS="$ROOT/finance" timeout 300 "$APY" -W ignore -B "$KDIR/walk_s787.py" "$SCR/w7" "$SCR/f.db" 2>&1 | tail -1)
case "$R7" in "WALK OK"*) ;; *) (cd "$SCR" && TMPDIR="$SCR" S787_ANY=1 S787_LIBS="$ROOT/finance" timeout 300 "$APY" -W ignore -B "$KDIR/walk_s787.py" "$SCR/w7" "$SCR/f.db" 2>&1 | grep -E '^BAD|Error' | head -6); stop "S787's walk on the new file is not green ($R7)";; esac
R9=$(cd "$SCR" && TMPDIR="$SCR" S789_LIBS="$ROOT/finance" timeout 300 "$APY" -W ignore -B "$KDIR/walk_s789.py" "$KDIR" "$SCR/f.db" 2>&1 | tail -1)
case "$R9" in "WALK OK"*) ;; *) (cd "$SCR" && TMPDIR="$SCR" S789_LIBS="$ROOT/finance" timeout 300 "$APY" -W ignore -B "$KDIR/walk_s789.py" "$KDIR" "$SCR/f.db" 2>&1 | grep -E '^BAD|Error' | head -6); stop "the S789 walk is not green ($R9)";; esac
R2=$(cd "$SCR" && TMPDIR="$SCR" S789_LIBS="$ROOT/finance" timeout 300 "$APY" -W ignore -B "$KDIR/walk_s789.py" "$SCR/live" "$SCR/f.db" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live file did not go red ($R2)";; esac
rm -f "$SCR/f.db"; find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[3/6] on a copy of today's finance.db: S789 $R9 | S788 $R | S787 $R7 | the live file: $R2"
[ "$(fhz)" = 200 ] || stop "finance is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
echo "[4/6] the build lock taken; the doctor's auto-fix paused for the restart"
{ \cp -p "$F1" "$BAK1" && [ "$(m5 "$BAK1")" = "$FROM1" ]; } || stop "could not keep a backup of $F1"
PLACED=1
\cp "$KDIR/check_screens.py" "$F1.s789new" && chmod --reference="$BAK1" "$F1.s789new" && chown --reference="$BAK1" "$F1.s789new" 2>/dev/null; mv -f "$F1.s789new" "$F1" || restore "could not be placed"
[ "$(m5 "$F1")" = "$TO1" ] || restore "read-back did not match"
find "$ROOT/finance" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(hcode "http://127.0.0.1:$FIN_PORT/finance/records/xray-check"); case "$c2" in 302|401|403|303) ;; *) restore "his X-ray page answered $c2 without a login";; esac
sleep 2
JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'check_screens|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'check|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
PLACED=0
echo "[5/6] placed (backup $BAK1); restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): finance $c1; his X-ray page's door closed without a login ($c2); journal clean"
echo "[6/6] $KIT: DONE. Your X-ray page's lab tile and your console count only the reports that need an answer."
