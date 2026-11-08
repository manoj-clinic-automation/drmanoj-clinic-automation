#!/bin/bash
# =============================================================================
#  install_S752_XRAY_CHECK_RETRY.sh . kit S752 (08-Nov-2026, session S404, the parent) . the owner's 'build it' 14:46 IST
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s752kit && cp -rp /root/deploy/repo/deploy_kits/S752_XRAY_CHECK_RETRY /tmp/s752kit && bash /tmp/s752kit/install_S752_XRAY_CHECK_RETRY.sh
#  (DRY=1 before bash: every gate, the walks and the proof on the live database; nothing written.)
#
#  /root/finance/records.py  5b325c6f -> TO: every X-ray filing run re-tries the pictures parked in Drive's "X-ray check" folder that
#      nobody has answered -- filed when their ID is now on the day's X-ray list (the slip came after the 17:40 run), or when a
#      name-only picture matches exactly one X-ray patient of that day; an ID one digit off (or a looser name match) is a one-tap
#      "Shayad ID ..." on Check karein, never filed by itself. The Drive side (VPS_Lab_Files.gs) is unchanged.
#  ON THE BOX before anything is written: the S752 walk green on the new file and red on the live one; S373's walk (the filing as
#      it was) green on the new file; both on a scratch copy of finance.db in /tmp; the proof on the LIVE database (a read-only copy,
#      counts and last-4 only) -- what would be filed today.
#  Red after placing: the file back byte-identically and clinic-finance restarted.
#  Undo:  bash /tmp/s752kit/install_S752_XRAY_CHECK_RETRY.sh --undo
# =============================================================================
set -u
KIT="S752_XRAY_CHECK_RETRY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F1="$FIN/records.py"
FROM1=5b325c6f4c42893ed11d4ace19020bf8
TO1=a6ec1052937e1aee99b515e07e13a853
BAK="$F1.bak_S752_${FROM1:0:8}"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { hcode /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
putback() { [ -f "$BAK" ] && \cp -p "$BAK" "$F1"; find "$FIN" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; [ "$(m5 "$F1")" = "$FROM1" ] && echo 1 || echo 0; }
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting records.py back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$FSVC" || true
  [ "$ok" = 1 ] && echo "   records.py is back byte-identically (${FROM1:0:8})" || echo "   !! records.py is NOT back -- copy $BAK back by hand"
  echo "   finance healthz $(wait200). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 records.py)" = "$TO1" ] || stop "the kit's records.py is not the built one"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK" ] || stop "no $BAK -- nothing to undo"
  ok=$(putback); "$SYSTEMCTL" restart "$FSVC" || true
  [ "$ok" = 1 ] && echo "UNDONE: records.py is back (${FROM1:0:8}); finance healthz $(wait200)" || echo "!! records.py is not back -- send a photo"
  exit 0
fi
echo "[1/7] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1")
if [ "$L1" = "$TO1" ]; then echo "-- ALREADY INSTALLED: records.py is the kit's. Nothing written. finance healthz $(fhz)"; exit 0; fi
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not the expected one (live ${L1:0:8}, kit expects ${FROM1:0:8})"
SCR=$(mktemp -d /tmp/s752.XXXX); chmod 700 "$SCR"; mkdir -p "$SCR/new" "$SCR/live" "$SCR/remake"
\cp "$KDIR/records.py" "$SCR/new/records.py"; \cp "$F1" "$SCR/live/records.py"
"$APY" -B "$KDIR/make_s752.py" "$F1" "$SCR/remake" >/dev/null 2>&1 && [ "$(m5 "$SCR/remake/records.py")" = "$TO1" ] || stop "make_s752.py on the live bytes does not give the kit's records.py"
"$APY" -B -m py_compile "$SCR/new/records.py" 2>/dev/null || stop "records.py does not compile with $APY"
"$VPY" -B -m py_compile "$SCR/new/records.py" 2>/dev/null || stop "records.py does not compile with $VPY"
echo "[2/7] the live file is ${FROM1:0:8}; the kit's records.py is that file + the S752 edits (remade on the box); it compiles under both pythons"
scratch() { rm -f "$SCR/walk.db"; "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro', uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$SCR/walk.db"; chmod 600 "$SCR/walk.db"; }
scratch || stop "could not make the scratch copy of finance.db"
R=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$APY" -W ignore -B "$KDIR/walk_s752.py" "$SCR/new" "$SCR/walk.db" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) stop "the S752 walk is not green ($R)";; esac
scratch
R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$APY" -W ignore -B "$KDIR/walk_s752.py" "$SCR/live" "$SCR/walk.db" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live file did not go red ($R2)";; esac
scratch
R3=$(cd "$SCR" && TMPDIR="$SCR" FINANCE_DB="$SCR/walk.db" timeout 300 "$APY" -W ignore -B "$KDIR/walk_s373.py" "$SCR/new" 2>&1 | tail -1)
case "$R3" in "WALK OK"*) ;; *) stop "S373's walk (the filing as it was) is not green on the new file ($R3)";; esac
rm -f "$SCR/walk.db"
echo "[3/7] on a scratch copy of finance.db: $R; the live file: $R2; S373's walk on the new file: $R3"
echo "[4/7] the proof on the LIVE database (a read-only copy; counts and last-4 only) -- what the new file would do today:"
(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$APY" -W ignore -B "$KDIR/proof_s752.py" "$SCR/new" "$DB") > "$SCR/proof.txt" 2>&1
sed 's/^/      /' "$SCR/proof.txt"
tail -1 "$SCR/proof.txt" | grep -q '^PROOF DONE' || stop "the proof did not finish"
[ "$(fhz)" = 200 ] || stop "finance is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
echo "[5/7] the build lock taken; the doctor's auto-fix paused for the restart ($([ "$OFF_MINE" = 1 ] && echo 'by this kit' || echo 'it was already off -- left as it is'))"
{ \cp -p "$F1" "$BAK" && [ "$(m5 "$BAK")" = "$FROM1" ]; } || stop "could not keep a backup of $F1"
PLACED=1
\cp "$KDIR/records.py" "$F1.s752new" && chmod --reference="$BAK" "$F1.s752new" && chown --reference="$BAK" "$F1.s752new" 2>/dev/null; mv -f "$F1.s752new" "$F1" || restore "records.py could not be placed"
[ "$(m5 "$F1")" = "$TO1" ] || restore "records.py read-back did not match"
find "$FIN" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[6/7] placed and read back: records.py ${TO1:0:8} (backup $BAK)"
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(hcode /finance/checks); case "$c2" in 302|401|403|303) ;; *) restore "Check karein answered $c2 without a login";; esac
c3=$(hcode /finance/records/api/xray-plan); case "$c3" in 302|401|403|303) ;; *) restore "the X-ray plan door answered $c3 without the token";; esac
c4=$(hcode /finance/slips/pending); case "$c4" in 302|401|403|303) ;; *) restore "Report baaki answered $c4 without a login";; esac
sleep 2
JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null | awk '/Starting gunicorn|Listening at:/{f=1} f{print} END{if(!f)exit 9}')" || JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'records\.py|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'records|failed to load|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
PLACED=0
echo "[7/7] $FSVC restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): healthz $c1; without a login Check karein $c2, Report baaki $c4; the X-ray plan door without the token $c3; the journal clean"
echo ""
echo "$KIT: DONE. The parked X-ray pictures are re-tried from the next mailbox run (within the hour)."
