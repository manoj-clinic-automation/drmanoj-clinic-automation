#!/bin/bash
# =============================================================================
#  install_S782_XRAY_LEFTOVERS.sh . kit S782 (11-Nov-2026, session S427, the parent) . F-1236 . the owner 13:01 IST 10-Nov: "I do not
#  want to leave any work for staff in Check karein as much as possible."
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s782kit && cp -rp /root/deploy/repo/deploy_kits/S782_XRAY_LEFTOVERS /tmp/s782kit && bash /tmp/s782kit/install_S782_XRAY_LEFTOVERS.sh
#  (DRY=1 before bash: every gate, the walks and the proof; nothing written.)
#  /root/finance/records.py bae45d82 (S776) -> TO: a 1-3-digit photo number in a parked picture's name that no patient of that day
#  has is not read as a clinic ID; a second upload of a photo already filed (same name, the film's same date and ID) goes to
#  duplicates, never filed twice; nothing is filed while its film prints another patient of that day; a name that is one X-ray
#  patient's but for the spelling files on him. /root/finance/check_screens.py ce7d248d (S757) -> TO: reception's Check karein
#  shows the last 7 days (older: the owner and Shavez); that day's patients listed closest name first. The duty map v22 (the
#  reception's X-ray line, last 7 days) comes with the git pull.
#  Undo:  bash /tmp/s782kit/install_S782_XRAY_LEFTOVERS.sh --undo
# =============================================================================
set -u
KIT="S782_XRAY_LEFTOVERS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; DB="${DB:-$FIN/finance.db}"
REPO752="${REPO752:-/root/deploy/repo/deploy_kits/S752_XRAY_CHECK_RETRY}"
REPO776="${REPO776:-/root/deploy/repo/deploy_kits/S776_XRAY_FEWER_LEFT}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F1="$FIN/records.py"
FROM1=bae45d82c0a431e5d876fb23c52ee9b2
TO1=794cb87f64afb89742e6bf0b04114b8e
BAK="$F1.bak_S782_${FROM1:0:8}"
F2="$FIN/check_screens.py"
FROM2=ce7d248de626660586b6a5caa064b5d6
TO2=c259e6a258c19f1222820b47e9e9ad34
BAK2="$F2.bak_S782_${FROM2:0:8}"
DMAP="${DMAP:-/root/deploy/repo/claude_code_briefs/DUTY_MAP.json}"; DMAP_TO=616e08397a15cc0994e53e549b9aefca
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { hcode /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
putback() { [ -f "$BAK" ] && \cp -p "$BAK" "$F1"; [ -f "$BAK2" ] && \cp -p "$BAK2" "$F2"; find "$FIN" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; [ "$(m5 "$F1")" = "$FROM1" ] && [ "$(m5 "$F2")" = "$FROM2" ] && echo 1 || echo 0; }
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting records.py back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$FSVC" || true
  [ "$ok" = 1 ] && echo "   records.py and check_screens.py are back byte-identically" || echo "   !! NOT back -- copy $BAK and $BAK2 back by hand"
  echo "   finance healthz $(wait200). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 records.py)" = "$TO1" ] || stop "the kit's records.py is not the built one"
[ "$(m5 check_screens.py)" = "$TO2" ] || stop "the kit's check_screens.py is not the built one"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK" ] || stop "no $BAK -- nothing to undo"
  ok=$(putback); "$SYSTEMCTL" restart "$FSVC" || true
  [ "$ok" = 1 ] && echo "UNDONE: records.py (${FROM1:0:8}, S776) and check_screens.py (${FROM2:0:8}, S757) are back; finance healthz $(wait200)" || echo "!! not back -- send a photo"
  exit 0
fi
echo "[1/6] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1"); L2=$(m5 "$F2")
[ "$L1" = "$TO1" ] && [ "$L2" = "$TO2" ] && { echo "-- ALREADY INSTALLED: both files are the kit's. Nothing written. finance healthz $(fhz)"; exit 0; }
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not the expected one (live ${L1:0:8}, kit expects ${FROM1:0:8} = S776)"
[ "$L2" = "$FROM2" ] || stop "the live $F2 is not the expected one (live ${L2:0:8}, kit expects ${FROM2:0:8} = S757)"
[ "$(m5 "$DMAP")" = "$DMAP_TO" ] || stop "the duty map in the repository is not v22 (${DMAP_TO:0:8}) -- was the publish pulled?"
[ -f "$REPO752/walk_s752.py" ] && [ -f "$REPO752/walk_s373.py" ] || stop "S752's walks not found in $REPO752"
[ -f "$REPO776/walk_s776.py" ] && [ -f "$REPO776/walk_s772.py" ] || stop "S776's walks not found in $REPO776"
SCR=$(mktemp -d /tmp/s782.XXXX); chmod 700 "$SCR"; mkdir -p "$SCR/new" "$SCR/newrec" "$SCR/live" "$SCR/remake"
\cp "$KDIR/records.py" "$SCR/new/records.py"; \cp "$KDIR/check_screens.py" "$SCR/new/check_screens.py"; \cp "$KDIR/records.py" "$SCR/newrec/records.py"
\cp "$F1" "$SCR/live/records.py"; \cp "$F2" "$SCR/live/check_screens.py"
"$APY" -B "$KDIR/make_s782.py" "$F1" "$SCR/remake/records.py" >/dev/null 2>&1 && [ "$(m5 "$SCR/remake/records.py")" = "$TO1" ] || stop "make_s782.py on the live bytes does not give the kit's records.py"
"$APY" -B "$KDIR/make_s782_cs.py" "$F2" "$SCR/remake/check_screens.py" >/dev/null 2>&1 && [ "$(m5 "$SCR/remake/check_screens.py")" = "$TO2" ] || stop "make_s782_cs.py on the live bytes does not give the kit's check_screens.py"
for f in records.py check_screens.py; do
  "$APY" -B -m py_compile "$SCR/new/$f" 2>/dev/null || stop "$f does not compile with $APY"
  "$VPY" -B -m py_compile "$SCR/new/$f" 2>/dev/null || stop "$f does not compile with $VPY"
done
echo "[2/6] the live files are ${FROM1:0:8} (S776) and ${FROM2:0:8} (S757); the kit's are those + the S782 edits (remade on the box); both compile under both pythons; the duty map is v22"
scratch() { rm -f "$SCR/walk.db"; "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro', uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$SCR/walk.db"; chmod 600 "$SCR/walk.db"; }
run() { (cd "$SCR" && TMPDIR="$SCR" timeout 300 "$APY" -W ignore -B "$@" 2>&1 | tail -1); }
scratch || stop "could not make the scratch copy of finance.db"
R=$(run "$KDIR/walk_s782.py" "$SCR/new" "$SCR/walk.db"); case "$R" in "WALK OK"*) ;; *) stop "the S782 walk is not green ($R)";; esac
scratch; R2=$(run "$KDIR/walk_s782.py" "$SCR/live" "$SCR/walk.db" --control); case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live file did not go red ($R2)";; esac
scratch; R3=$(run "$REPO776/walk_s772.py" "$SCR/new" "$SCR/walk.db"); case "$R3" in "WALK OK"*) ;; *) stop "S772's walk is not green on the new file ($R3)";; esac
scratch; R6=$(run "$REPO776/walk_s776.py" "$SCR/new" "$SCR/walk.db"); case "$R6" in "WALK OK"*) ;; *) stop "S776's walk is not green on the new file ($R6)";; esac
scratch; R4=$(run "$REPO752/walk_s752.py" "$SCR/newrec" "$SCR/walk.db"); case "$R4" in "WALK OK"*) ;; *) stop "S752's walk is not green on the new file ($R4)";; esac
scratch; R5=$(cd "$SCR" && TMPDIR="$SCR" FINANCE_DB="$SCR/walk.db" timeout 300 "$APY" -W ignore -B "$REPO752/walk_s373.py" "$SCR/newrec" 2>&1 | tail -1)
case "$R5" in "WALK OK"*) ;; *) stop "S373's walk is not green on the new file ($R5)";; esac
echo "[3/6] on scratch copies: $R | the live file: $R2 | S776: $R6 | S772: $R3 | S752: $R4 | S373: $R5"
scratch
echo "[4/6] the proof on a copy of the LIVE database (counts only) -- what the next filing runs will do:"
(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$APY" -W ignore -B "$KDIR/shape_s782.py" "$SCR/new" "$SCR/walk.db" "$(TZ=Asia/Kolkata date +%Y-%m-%dT%H:%M:%S)") > "$SCR/proof.txt" 2>&1
sed 's/^/      /' "$SCR/proof.txt"
tail -1 "$SCR/proof.txt" | grep -q '^SHAPE DONE' || stop "the proof did not finish"
rm -f "$SCR/walk.db"
[ "$(fhz)" = 200 ] || stop "finance is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
echo "[5/6] the build lock taken; the doctor's auto-fix paused for the restart"
{ \cp -p "$F1" "$BAK" && [ "$(m5 "$BAK")" = "$FROM1" ]; } || stop "could not keep a backup of $F1"
{ \cp -p "$F2" "$BAK2" && [ "$(m5 "$BAK2")" = "$FROM2" ]; } || stop "could not keep a backup of $F2"
PLACED=1
\cp "$KDIR/records.py" "$F1.s782new" && chmod --reference="$BAK" "$F1.s782new" && chown --reference="$BAK" "$F1.s782new" 2>/dev/null; mv -f "$F1.s782new" "$F1" || restore "records.py could not be placed"
[ "$(m5 "$F1")" = "$TO1" ] || restore "records.py read-back did not match"
\cp "$KDIR/check_screens.py" "$F2.s782new" && chmod --reference="$BAK2" "$F2.s782new" && chown --reference="$BAK2" "$F2.s782new" 2>/dev/null; mv -f "$F2.s782new" "$F2" || restore "check_screens.py could not be placed"
[ "$(m5 "$F2")" = "$TO2" ] || restore "check_screens.py read-back did not match"
find "$FIN" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(hcode /finance/checks); case "$c2" in 302|401|403|303) ;; *) restore "Check karein answered $c2 without a login";; esac
c3=$(hcode /finance/records/api/xray-plan); case "$c3" in 302|401|403|303) ;; *) restore "the X-ray plan door answered $c3 without the token";; esac
sleep 2
JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'records\.py|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'records|failed to load|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
PLACED=0
echo "[6/6] records.py ${TO1:0:8} and check_screens.py ${TO2:0:8} placed (backups $BAK, $BAK2); $FSVC restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): healthz $c1; doors closed ($c2 $c3); journal clean"
echo ""
echo "$KIT: DONE. The next X-ray filing run (hourly, at :25) does what the proof counts."
