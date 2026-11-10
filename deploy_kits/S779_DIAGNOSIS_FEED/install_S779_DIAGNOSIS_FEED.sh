#!/bin/bash
# =============================================================================
#  install_S779_DIAGNOSIS_FEED.sh . kit S779 (10-Nov-2026, session S424, the parent) . D884 part 1: the diagnosis feed.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s779kit && cp -rp /root/deploy/repo/deploy_kits/S779_DIAGNOSIS_FEED /tmp/s779kit && bash /tmp/s779kit/install_S779_DIAGNOSIS_FEED.sh
#  (DRY=1 before bash: every gate and the walks; nothing written.)
#  /root/finance/docterz_pickup.py f8cb978e (S507/S509) -> a third kind, 'clinical' (Docterz's clinical data report, which
#  today is taken for a consultation report and would replace the day's real one) + NEW /root/finance/dx_feed.py and
#  /root/finance/diagnosis_normalizer.py (the owner's taxonomy): every visit's diagnosis into dx_visit. Nothing visible changes.
#  Undo:  bash /tmp/s779kit/install_S779_DIAGNOSIS_FEED.sh --undo
# =============================================================================
set -u
KIT="S779_DIAGNOSIS_FEED"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F1="$FIN/docterz_pickup.py"; F2="$FIN/dx_feed.py"; F3="$FIN/diagnosis_normalizer.py"
FROM1=f8cb978e8d29a03d931b4e4a2d01ce6e
TO1=a26c1467314a754f8966bfbf72c00b2b
TO2=f18c565262193c98494193c4974a2634
TO3=daef69dab7acf20eeaac30eb9dbfecef
BAK="$F1.bak_S779_${FROM1:0:8}"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { hcode /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
putback() {
  [ -f "$BAK" ] && \cp -p "$BAK" "$F1"
  for f in "$F2" "$F3"; do [ -f "$f" ] && mv -f "$f" "$f.s779undo"; done
  find "$FIN" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  [ "$(m5 "$F1")" = "$FROM1" ] && echo 1 || echo 0
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting docterz_pickup.py back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$FSVC" || true
  [ "$ok" = 1 ] && echo "   docterz_pickup.py is back byte-identically (${FROM1:0:8})" || echo "   !! docterz_pickup.py is NOT back -- copy $BAK back by hand"
  echo "   finance healthz $(wait200). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 docterz_pickup.py)" = "$TO1" ] && [ "$(m5 dx_feed.py)" = "$TO2" ] && [ "$(m5 diagnosis_normalizer.py)" = "$TO3" ] || stop "the kit's files are not the built ones"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK" ] || stop "no $BAK -- nothing to undo"
  ok=$(putback); "$SYSTEMCTL" restart "$FSVC" || true
  [ "$ok" = 1 ] && echo "UNDONE: docterz_pickup.py is back (${FROM1:0:8}); dx_feed.py and diagnosis_normalizer.py set aside (.s779undo); the dx_ tables stay, unread; finance healthz $(wait200)" || echo "!! docterz_pickup.py is not back -- send a photo"
  exit 0
fi
echo "[1/6] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1")
[ "$L1" = "$TO1" ] && [ "$(m5 "$F2")" = "$TO2" ] && [ "$(m5 "$F3")" = "$TO3" ] && { echo "-- ALREADY INSTALLED. Nothing written. finance healthz $(fhz)"; exit 0; }
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not the expected one (live ${L1:0:8}, kit expects ${FROM1:0:8} = S507/S509)"
for f in "$F2" "$F3"; do [ ! -e "$f" ] || [ "$(m5 "$f")" = "$(m5 "$KDIR/$(basename "$f")")" ] || stop "$f already exists and is not the kit's"; done
SCR=$(mktemp -d /tmp/s779.XXXX); chmod 700 "$SCR"; mkdir -p "$SCR/new" "$SCR/live"
\cp "$KDIR/docterz_pickup.py" "$KDIR/dx_feed.py" "$KDIR/diagnosis_normalizer.py" "$SCR/new/"; \cp "$F1" "$SCR/live/docterz_pickup.py"
"$APY" -B "$KDIR/make_s779.py" "$F1" "$SCR/remake.py" >/dev/null 2>&1 && [ "$(m5 "$SCR/remake.py")" = "$TO1" ] || stop "make_s779.py on the live bytes does not give the kit's docterz_pickup.py"
for p in "$APY" "$VPY"; do for f in docterz_pickup.py dx_feed.py diagnosis_normalizer.py; do "$p" -B -m py_compile "$SCR/new/$f" 2>/dev/null || stop "$f does not compile with $p"; done; done
echo "[2/6] the live file is ${FROM1:0:8}; the kit's docterz_pickup.py is that file + the S779 edits (remade on the box); all three compile under both pythons"
scratch() { rm -f "$SCR/walk.db"; "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro', uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$SCR/walk.db"; }
run() { (cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$@" 2>&1 | tail -1); }
scratch || stop "could not make the scratch copy of finance.db"
R=$(run "$KDIR/walk_s779.py" "$SCR/new" "$SCR/walk.db"); case "$R" in "WALK OK"*) ;; *) stop "the S779 walk is not green ($R)";; esac
scratch; R2=$(run "$KDIR/walk_s779.py" "$SCR/live" "$SCR/walk.db" --control); case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live file did not go red ($R2)";; esac
rm -f "$SCR/walk.db"
echo "[3/6] on scratch copies of finance.db: $R | the live file: ${R2:0:60}..."
[ "$(fhz)" = 200 ] || stop "finance is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
echo "[4/6] the build lock taken; the doctor's auto-fix paused for the restart"
{ \cp -p "$F1" "$BAK" && [ "$(m5 "$BAK")" = "$FROM1" ]; } || stop "could not keep a backup of $F1"
PLACED=1
for n in dx_feed.py diagnosis_normalizer.py; do
  \cp "$KDIR/$n" "$FIN/$n.s779new" && chmod --reference="$BAK" "$FIN/$n.s779new" && chown --reference="$BAK" "$FIN/$n.s779new" 2>/dev/null; mv -f "$FIN/$n.s779new" "$FIN/$n" || restore "$n could not be placed"
done
\cp "$KDIR/docterz_pickup.py" "$F1.s779new" && chmod --reference="$BAK" "$F1.s779new" && chown --reference="$BAK" "$F1.s779new" 2>/dev/null; mv -f "$F1.s779new" "$F1" || restore "docterz_pickup.py could not be placed"
[ "$(m5 "$F1")" = "$TO1" ] && [ "$(m5 "$F2")" = "$TO2" ] && [ "$(m5 "$F3")" = "$TO3" ] || restore "read-back did not match"
find "$FIN" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(hcode /finance/api/reception/report); case "$c2" in 400|401|403|405) ;; *) restore "the reception report door answered $c2 to an unsigned call";; esac
sleep 2
JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'docterz_pickup|dx_feed|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'docterz|dx_feed|failed to load|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
S=$(cd "$FIN" && timeout 120 "$VPY" -B "$F2" --db "$DB" 2>&1 | tail -1)
case "$S" in "dx_feed: {"*) ;; *) restore "dx_feed.py did not run on the live database ($S)";; esac
find "$FIN" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0
echo "[5/6] docterz_pickup.py ${TO1:0:8} + dx_feed.py + diagnosis_normalizer.py placed (backup $BAK); $FSVC restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): healthz $c1; reception door closed ($c2); journal clean"
echo "[6/6] $S"
echo ""
echo "$KIT: DONE. A clinical data report put in the Drive folder (or sent by the reception PC) is now kept as its own kind and its diagnoses read at once."
