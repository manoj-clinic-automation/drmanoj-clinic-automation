#!/bin/bash
# =============================================================================
#  install_S772_XRAY_FILM_DATE.sh . kit S772 (10-Nov-2026, session S422, the parent) . the owner's "do all thats possible" 11:13 IST
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s772kit && cp -rp /root/deploy/repo/deploy_kits/S772_XRAY_FILM_DATE /tmp/s772kit && bash /tmp/s772kit/install_S772_XRAY_FILM_DATE.sh
#  (DRY=1 before bash: every gate, the walks, the first film read and the proof on a SCRATCH copy; nothing live written.)
#
#  /root/finance/records.py  d86f2ada -> TO: the S752 re-try plans a parked X-ray picture on the date printed on its film (an
#      X-ray day of its ID, or of the ID printed on the film; an open day within 2 days of the film's date), else on its ID's one
#      X-ray day with no photo in 60 days; the older parked copies of a corrected picture, and copies filed to another patient
#      under a mistyped ID, go to the mailbox's duplicates folder (that record void; nothing deleted).
#  NEW /root/finance/xray_filmdate.py + cron every 30 minutes (RapidOCR in /root/xray_ocr/venv): reads each parked picture's
#      film ONCE into the new table xray_filmdate (dates, IDs). Switch: /root/finance/_off/XRAY_FILMDATE_OFF.
#  ON THE BOX before records.py is placed: the S772 walk green on the new file and red on the live one; S752's and S373's walks
#  green on the new file; the film-reader walk green; all on scratch copies in /tmp; the first film read; the proof (counts only).
#  Red after placing: records.py back byte-identically, the cron line out, clinic-finance restarted.
#  Undo:  bash /tmp/s772kit/install_S772_XRAY_FILM_DATE.sh --undo
# =============================================================================
set -u
KIT="S772_XRAY_FILM_DATE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; DB="${DB:-$FIN/finance.db}"
REPO752="${REPO752:-/root/deploy/repo/deploy_kits/S752_XRAY_CHECK_RETRY}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
OCRD="${OCRD:-$ROOT/xray_ocr}"; OCRV="$OCRD/venv"; OPY="$OCRV/bin/python3"
OCR_IMPORT="${OCR_IMPORT:-rapidocr_onnxruntime, PIL}"   # a rehearsal box with tesseract only sets OCR_IMPORT=PIL
F1="$FIN/records.py"; F2="$FIN/xray_filmdate.py"
FROM1=d86f2adae16afa32afc4443042e5aacc
TO1=bfd5b845d2218ba93cd04791f9b6505d
TO2=f8ef85fdd55c50c020c2242300de52c8
TAG="# S772 X-ray film date"
CRONLINE="*/30 * * * * $OPY -B $F2 >> $OCRD/filmdate.log 2>&1 $TAG"
BAK="$F1.bak_S772_${FROM1:0:8}"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { hcode /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
cron_out() { crontab -l 2>/dev/null | grep -v -F "$TAG" | crontab - 2>/dev/null; }
putback() { [ -f "$BAK" ] && \cp -p "$BAK" "$F1"; find "$FIN" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; [ "$(m5 "$F1")" = "$FROM1" ] && echo 1 || echo 0; }
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting records.py back and taking the cron line out"
  local ok; ok=$(putback); cron_out; "$SYSTEMCTL" restart "$FSVC" || true
  [ "$ok" = 1 ] && echo "   records.py is back byte-identically (${FROM1:0:8})" || echo "   !! records.py is NOT back -- copy $BAK back by hand"
  echo "   finance healthz $(wait200). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 records.py)" = "$TO1" ] || stop "the kit's records.py is not the built one"
[ "$(m5 xray_filmdate.py)" = "$TO2" ] || stop "the kit's xray_filmdate.py is not the built one"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK" ] || stop "no $BAK -- nothing to undo"
  ok=$(putback); cron_out; "$SYSTEMCTL" restart "$FSVC" || true
  [ "$ok" = 1 ] && echo "UNDONE: records.py is back (${FROM1:0:8}); the film-reading cron line is out; finance healthz $(wait200). (xray_filmdate.py and its table stay; nothing reads them now.)" \
                || echo "!! records.py is not back -- send a photo"
  exit 0
fi
echo "[1/8] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1")
if [ "$L1" = "$TO1" ] && [ "$(m5 "$F2")" = "$TO2" ] && crontab -l 2>/dev/null | grep -q -F "$TAG"; then
  echo "-- ALREADY INSTALLED: records.py and xray_filmdate.py are the kit's and the cron line is in. Nothing written. finance healthz $(fhz)"; exit 0
fi
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not the expected one (live ${L1:0:8}, kit expects ${FROM1:0:8})"
[ -f "$REPO752/walk_s752.py" ] && [ -f "$REPO752/walk_s373.py" ] || stop "S752's walks not found in $REPO752"
SCR=$(mktemp -d /tmp/s772.XXXX); chmod 700 "$SCR"; mkdir -p "$SCR/new" "$SCR/live" "$SCR/remake"
\cp "$KDIR/records.py" "$SCR/new/records.py"; \cp "$F1" "$SCR/live/records.py"
"$APY" -B "$KDIR/make_s772.py" "$F1" "$SCR/remake" >/dev/null 2>&1 && [ "$(m5 "$SCR/remake/records.py")" = "$TO1" ] || stop "make_s772.py on the live bytes does not give the kit's records.py"
"$APY" -B -m py_compile "$SCR/new/records.py" 2>/dev/null || stop "records.py does not compile with $APY"
"$VPY" -B -m py_compile "$SCR/new/records.py" 2>/dev/null || stop "records.py does not compile with $VPY"
echo "[2/8] the live file is ${FROM1:0:8}; the kit's records.py is that file + the S772 edits (remade on the box); it compiles under both pythons"
if ! "$OPY" -c "import $OCR_IMPORT" 2>/dev/null; then
  echo "      setting up the film reader (RapidOCR) in $OCRV -- 1 to 3 minutes ..."
  mkdir -p "$OCRD" && chmod 700 "$OCRD"; rm -rf "$OCRV"
  { python3 -m venv "$OCRV" || "$VPY" -m venv "$OCRV" || { rm -rf "$OCRV"; python3 -m venv --without-pip "$OCRV"; }; } > "$OCRD/setup.log" 2>&1
  if "$OPY" -m pip --version >/dev/null 2>&1; then
    timeout 900 "$OPY" -m pip install -q --disable-pip-version-check rapidocr_onnxruntime >> "$OCRD/setup.log" 2>&1
  else                                                   # a python with no ensurepip: another pip installs into the venv
    for P in "python3 -m pip" "$VPY -m pip" "pip3" "pip"; do
      timeout 900 $P --python "$OPY" install -q --disable-pip-version-check rapidocr_onnxruntime >> "$OCRD/setup.log" 2>&1 && break
    done
  fi
  "$OPY" -c "import rapidocr_onnxruntime, PIL" 2>/dev/null || stop "the film reader did not install ($(tail -1 "$OCRD/setup.log" | cut -c1-120))"
fi
"$OPY" -B -m py_compile "$KDIR/xray_filmdate.py" 2>/dev/null || stop "xray_filmdate.py does not compile with $OPY"
echo "[3/8] the film reader is ready: $OPY (RapidOCR)"
scratch() { rm -f "$SCR/walk.db"; "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro', uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$SCR/walk.db"; chmod 600 "$SCR/walk.db"; }
scratch || stop "could not make the scratch copy of finance.db"
R=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$APY" -W ignore -B "$KDIR/walk_s772.py" "$SCR/new" "$SCR/walk.db" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) stop "the S772 walk is not green ($R)";; esac
scratch
R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$APY" -W ignore -B "$KDIR/walk_s772.py" "$SCR/live" "$SCR/walk.db" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live file did not go red ($R2)";; esac
scratch
R3=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$APY" -W ignore -B "$REPO752/walk_s752.py" "$SCR/new" "$SCR/walk.db" 2>&1 | tail -1)
case "$R3" in "WALK OK"*) ;; *) stop "S752's walk is not green on the new file ($R3)";; esac
scratch
R4=$(cd "$SCR" && TMPDIR="$SCR" FINANCE_DB="$SCR/walk.db" timeout 300 "$APY" -W ignore -B "$REPO752/walk_s373.py" "$SCR/new" 2>&1 | tail -1)
case "$R4" in "WALK OK"*) ;; *) stop "S373's walk (the filing as it was) is not green on the new file ($R4)";; esac
R5=$(cd "$SCR" && TMPDIR="$SCR" WALK_PY_PLAIN="$APY" timeout 600 "$OPY" -W ignore -B "$KDIR/walk_s772_filmdate.py" "$KDIR/xray_filmdate.py" "$FIN/records_drive.py" 2>&1 | tail -1)
case "$R5" in "WALK OK"*) ;; *) stop "the film reader's walk is not green ($R5)";; esac
rm -f "$SCR/walk.db"
echo "[4/8] on scratch copies: $R | the live file: $R2 | S752: $R3 | S373: $R4 | film reader: $R5"
[ "$(fhz)" = 200 ] || stop "finance is not healthy before the install"
if [ "${DRY:-0}" = 1 ]; then
  scratch; FDB="$SCR/walk.db"; echo "[5/8] DRY: the first film read on the SCRATCH copy (about 3-5 minutes) ..."
else
  \cp "$KDIR/xray_filmdate.py" "$F2.s772new" && chmod 644 "$F2.s772new" && mv -f "$F2.s772new" "$F2" && [ "$(m5 "$F2")" = "$TO2" ] || stop "xray_filmdate.py could not be placed"
  FDB="$DB"; echo "[5/8] xray_filmdate.py placed (${TO2:0:8}); the first film read of the parked pictures (about 3-5 minutes) ..."
fi
FR=$(FINANCE_DB="$FDB" S772_MAX=300 S772_SECS=1200 timeout 1500 nice -n 10 "$OPY" -B "$KDIR/xray_filmdate.py" 2>&1 | tail -1)
echo "      $FR"
case "$FR" in *"read "*|"") ;; *) stop "the first film read did not finish ($FR)" "xray_filmdate.py is placed; nothing else changed.";; esac
[ "${DRY:-0}" = 1 ] || scratch
echo "[6/8] the proof on a copy of the LIVE database with the film's dates (counts only) -- what the next filing runs will do:"
(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$APY" -W ignore -B "$KDIR/shape_s772.py" "$SCR/new" "$SCR/walk.db" "$(TZ=Asia/Kolkata date +%Y-%m-%dT%H:%M:%S)") > "$SCR/proof.txt" 2>&1
sed 's/^/      /' "$SCR/proof.txt"
tail -1 "$SCR/proof.txt" | grep -q '^SHAPE DONE' || stop "the proof did not finish" "Only xray_filmdate.py and its table are new; records.py is untouched."
rm -f "$SCR/walk.db"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing live written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
echo "[7/8] the build lock taken; the doctor's auto-fix paused for the restart"
{ \cp -p "$F1" "$BAK" && [ "$(m5 "$BAK")" = "$FROM1" ]; } || stop "could not keep a backup of $F1"
PLACED=1
\cp "$KDIR/records.py" "$F1.s772new" && chmod --reference="$BAK" "$F1.s772new" && chown --reference="$BAK" "$F1.s772new" 2>/dev/null; mv -f "$F1.s772new" "$F1" || restore "records.py could not be placed"
[ "$(m5 "$F1")" = "$TO1" ] || restore "records.py read-back did not match"
find "$FIN" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(hcode /finance/checks); case "$c2" in 302|401|403|303) ;; *) restore "Check karein answered $c2 without a login";; esac
c3=$(hcode /finance/records/api/xray-plan); case "$c3" in 302|401|403|303) ;; *) restore "the X-ray plan door answered $c3 without the token";; esac
c4=$(hcode /finance/slips/pending); case "$c4" in 302|401|403|303) ;; *) restore "Report baaki answered $c4 without a login";; esac
sleep 2
JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'records\.py|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'records|failed to load|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
cron_out; { crontab -l 2>/dev/null; echo "$CRONLINE"; } | crontab - && crontab -l 2>/dev/null | grep -q -F "$TAG" || restore "the cron line could not be added"
PLACED=0
echo "[8/8] records.py ${TO1:0:8} placed (backup $BAK); $FSVC restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): healthz $c1; doors closed without a login ($c2 $c4) and without the token ($c3); journal clean; the film reader every 30 minutes"
echo ""
echo "$KIT: DONE. The next X-ray filing runs (hourly, at :25) file the pictures the proof counts, 25 at a time."
