#!/bin/bash
# =============================================================================
#  install_S792_PUNCH_CLOCK.sh . kit S792 (11-Nov-2026, session S430, the parent) . the owner 12:10 IST: "Ok and correct today's
#  punches also" -- the attendance machine's clock ran 1 h 39 min to 2 h 57 min behind on 11-Nov (power cuts stop it).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s792kit && cp -rp /root/deploy/repo/deploy_kits/S792_PUNCH_CLOCK /tmp/s792kit && bash /tmp/s792kit/install_S792_PUNCH_CLOCK.sh
#  /root/attlistener_v2.py 52b26645 -> 588ea08e (attlistener restarted) . /root/finance/owner_console.py 2c77db31 -> ba977832 (finance
#  restarted) . /root/punches.csv: 11-Nov's punches that arrived alone get the server's time (backup kept).
#  Undo: bash /tmp/s792kit/install_S792_PUNCH_CLOCK.sh --undo   (the two files back; the corrected times stay -- they are the true ones)
# =============================================================================
set -u
KIT="S792_PUNCH_CLOCK"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; ASVC="${ASVC:-attlistener}"; ATT_PORT="${ATT_PORT:-8041}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
FIXDAY="${FIXDAY:-2026-11-11}"
PATHS=("$ROOT/attlistener_v2.py" "$ROOT/finance/owner_console.py")
NAMES=(attlistener_v2.py owner_console.py)
FROMS=(52b26645a986c5c00492544f21ddaccb 2c77db3122d66374f7b32643a18f3dbc)
TOS=(588ea08e744d11fc9fbbee7e41d7515c ba97783223b689ab538a7ccaf0028ef7)
PCSV="${PCSV:-$ROOT/punches.csv}"
PBAK="$PCSV.bak_S792_$(date +%Y%m%d%H%M%S)"; PAFTER=""
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
fhz() { hcode "http://127.0.0.1:$FIN_PORT/finance/healthz"; }
ack() { curl -s -m 8 -D - -o /dev/null "http://127.0.0.1:$ATT_PORT/iclock/getrequest" 2>/dev/null | tr -d '\r' | awk -F': ' 'tolower($1)=="response_code"{print $2}'; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
waitack() { local a=""; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 1; a=$(ack); [ "$a" = ERROR_NO_CMD ] && break; done; echo "${a:-none}"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
bak() { echo "${PATHS[$1]}.bak_S792_${FROMS[$1]:0:8}"; }
putback() {
  local ok=1 i
  for i in 0 1; do [ -f "$(bak $i)" ] && \cp -p "$(bak $i)" "${PATHS[$i]}"; [ "$(m5 "${PATHS[$i]}")" = "${FROMS[$i]}" ] || ok=0; done
  find "$ROOT" "$ROOT/finance" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; echo $ok
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting the two files back"
  "$SYSTEMCTL" stop "$ASVC" 2>/dev/null || true
  local ok; ok=$(putback)
  if [ -n "$PAFTER" ] && [ -f "$PBAK" ] && [ "$(m5 "$PCSV")" = "$PAFTER" ]; then \cp -p "$PBAK" "$PCSV" && echo "   punches.csv back as it was (no punch had come since)"; \
  elif [ -n "$PAFTER" ]; then echo "   punches.csv keeps today's corrected times (punches have come since; the old copy is $PBAK)"; fi
  "$SYSTEMCTL" start "$ASVC" || true; "$SYSTEMCTL" restart "$FSVC" || true
  [ "$ok" = 1 ] && echo "   both files are back byte-identically" || echo "   !! NOT both back -- copy the .bak_S792_* files back by hand"
  echo "   attendance listener $(waitack) . finance healthz $(wait200 fhz). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
for i in 0 1; do [ "$(m5 "${NAMES[$i]}")" = "${TOS[$i]}" ] || stop "the kit's ${NAMES[$i]} is not the built one"; done
if [ "${1:-}" = "--undo" ]; then
  for i in 0 1; do [ -f "$(bak $i)" ] || stop "no backup of ${NAMES[$i]} -- nothing to undo"; done
  "$SYSTEMCTL" stop "$ASVC" || true; ok=$(putback); "$SYSTEMCTL" start "$ASVC" || true; "$SYSTEMCTL" restart "$FSVC" || true
  [ "$ok" = 1 ] && echo "UNDONE: both files are back; listener $(waitack); finance $(wait200 fhz). (Today's corrected punch times stay: they are the true ones.)" || echo "!! not back -- send a photo"
  exit 0
fi
echo "[1/6] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
ND=0
for i in 0 1; do
  L=$(m5 "${PATHS[$i]}")
  if [ "$L" = "${TOS[$i]}" ]; then ND=$((ND+1)); continue; fi
  [ "$L" = "${FROMS[$i]}" ] || stop "the live ${NAMES[$i]} is not the expected one (live ${L:0:8}, kit expects ${FROMS[$i]:0:8})"
done
[ "$ND" = 2 ] && { echo "-- ALREADY INSTALLED. Nothing written. listener $(ack); finance $(fhz)"; exit 0; }
[ "$ND" = 0 ] || stop "only one of the two files is this kit's -- a half install; send a photo"
[ -f "$PCSV" ] || stop "no $PCSV"
SCR=$(mktemp -d /tmp/s792.XXXX); chmod 700 "$SCR"; mkdir -p "$SCR/remake" "$SCR/live"
for i in 0 1; do \cp -p "${PATHS[$i]}" "$SCR/live/"; done; \cp -p "$KDIR/fix_punch_clock.py" "$SCR/live/"
"$APY" -B "$KDIR/make_s792.py" "$SCR/live" "$SCR/remake" >/dev/null 2>&1 || stop "make_s792.py on the live bytes does not give the kit's files"
for i in 0 1; do [ "$(m5 "$SCR/remake/${NAMES[$i]}")" = "${TOS[$i]}" ] || stop "the remade ${NAMES[$i]} is not the kit's"; done
for f in attlistener_v2.py owner_console.py fix_punch_clock.py; do "$APY" -W ignore -B -m py_compile "$KDIR/$f" 2>/dev/null || stop "$f does not compile"; done
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[2/6] the live files are the expected ones; the kit's are those + the S792 change (remade on the box); they compile"
run() { (cd "$SCR" && TMPDIR="$SCR" S792_LIBS="$ROOT/finance:$ROOT" timeout 240 "$APY" -W ignore -B "$@" 2>&1); }
R1=$(run "$KDIR/walk_s792.py" "$KDIR" | tail -1)
case "$R1" in "WALK OK"*) ;; *) run "$KDIR/walk_s792.py" "$KDIR" | grep -E '^BAD|Error' | head -6; stop "the S792 walk is not green ($R1)";; esac
RC=$(run "$KDIR/walk_s792.py" "$SCR/live" --control | tail -1)
case "$RC" in "CONTROL: red"*) ;; *) stop "the control on the live files did not go red ($RC)";; esac
\cp -p "$PCSV" "$SCR/p.csv"
FD=$("$APY" -B "$KDIR/fix_punch_clock.py" "$SCR/p.csv" "$FIXDAY" 2>&1 | tail -1)
N=$(printf '%s' "$FD" | sed -n 's/^rows on [0-9-]* corrected: \([0-9]*\).*/\1/p')
{ [ -n "$N" ] && [ "$N" -le 10 ]; } || stop "the correction on a copy of punches.csv did not read as expected ($FD)"
rm -f "$SCR/p.csv"
echo "[3/6] walk $R1 | the live files: $RC | on a copy of punches.csv: $FD"
[ "$(fhz)" = 200 ] || stop "finance is not healthy before the install"
[ "$(ack)" = ERROR_NO_CMD ] || stop "the attendance listener is not answering before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
echo "[4/6] the build lock taken; the doctor's auto-fix paused for the restarts"
for i in 0 1; do { \cp -p "${PATHS[$i]}" "$(bak $i)" && [ "$(m5 "$(bak $i)")" = "${FROMS[$i]}" ]; } || stop "could not keep a backup of ${PATHS[$i]}"; done
PLACED=1
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" stop "$ASVC" || restore "could not stop $ASVC"
{ \cp -p "$PCSV" "$PBAK" && [ "$(m5 "$PBAK")" = "$(m5 "$PCSV")" ]; } || restore "could not keep a backup of punches.csv"
FA=$("$APY" -B "$KDIR/fix_punch_clock.py" "$PCSV" "$FIXDAY" --apply 2>&1 | tr '\n' ' ')
case "$FA" in *APPLIED*) ;; *) restore "the correction did not apply ($FA)";; esac
PAFTER=$(m5 "$PCSV")
for i in 0 1; do
  f="${PATHS[$i]}"
  \cp "$KDIR/${NAMES[$i]}" "$f.s792new" && chmod --reference="$(bak $i)" "$f.s792new" && chown --reference="$(bak $i)" "$f.s792new" 2>/dev/null; mv -f "$f.s792new" "$f" || restore "${NAMES[$i]} could not be placed"
  [ "$(m5 "$f")" = "${TOS[$i]}" ] || restore "${NAMES[$i]} read-back did not match"
done
find "$ROOT" "$ROOT/finance" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
"$SYSTEMCTL" start "$ASVC" || restore "start $ASVC"
a1=$(waitack); [ "$a1" = ERROR_NO_CMD ] || restore "the attendance listener answered '$a1'"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
sleep 2
JL="$("$JOURNALCTL" -u "$FSVC" -u "$ASVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'owner_console|attlistener_v2|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'console|attlistener|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
PLACED=0
echo "[5/6] placed (backups *.bak_S792_*; punches.csv kept as $PBAK); $FA; listener answering ($a1); finance $c1; journal clean"
echo "[6/6] $KIT: DONE. Today's punches show their true times; from now on a wrong machine clock is corrected as punches arrive, and your console says when it happens."
