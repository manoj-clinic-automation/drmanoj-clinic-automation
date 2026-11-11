#!/bin/bash
# =============================================================================
#  install_S791_XRAY_MATCH_RULES.sh . kit S791 (11-Nov-2026, session S430, the parent) . D906, the owner 09:41 / 09:45 IST:
#  "maximum patients matched through all the data pipelines ... only flag those which really need to be flagged" and an X-ray of
#  someone not registered "could be a payment gap, so it should also be highlighted".
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s791kit && cp -rp /root/deploy/repo/deploy_kits/S791_XRAY_MATCH_RULES /tmp/s791kit && bash /tmp/s791kit/install_S791_XRAY_MATCH_RULES.sh
#  /root/finance/check_screens.py dc713523 -> a8a3552c . records.py a2481f74 -> b81e4e8f . owner_console.py 97d63d71 -> 2c77db31
#  (finance restarted once).   Undo: bash /tmp/s791kit/install_S791_XRAY_MATCH_RULES.sh --undo
# =============================================================================
set -u
KIT="S791_XRAY_MATCH_RULES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
NAMES=(check_screens.py records.py owner_console.py)
FROMS=(dc713523857d668a8fcb930e26cc0fc4 a2481f74ee0054c45cef06a9e8fa923e 97d63d71479a7a4598c1e8395d0516d0)
TOS=(a8a3552c4dd14f4a01848b063d9cefef b81e4e8fe2f7c78e89f7d8fba37bcd14 2c77db3122d66374f7b32643a18f3dbc)
DB="${FINANCE_DB:-$ROOT/finance/finance.db}"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
fhz() { hcode "http://127.0.0.1:$FIN_PORT/finance/healthz"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
live() { echo "$ROOT/finance/$1"; }
bak() { echo "$(live "$1").bak_S791_${2:0:8}"; }
putback() {   # 1 when all three are back byte-identically
  local ok=1 i
  for i in 0 1 2; do
    local f b; f=$(live "${NAMES[$i]}"); b=$(bak "${NAMES[$i]}" "${FROMS[$i]}")
    [ -f "$b" ] && \cp -p "$b" "$f"
    [ "$(m5 "$f")" = "${FROMS[$i]}" ] || ok=0
  done
  find "$ROOT/finance" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; echo $ok
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting the three files back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$FSVC" || true
  [ "$ok" = 1 ] && echo "   all three are back byte-identically" || echo "   !! NOT all back -- copy the .bak_S791_* files back by hand"
  echo "   finance healthz $(wait200 fhz). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
for i in 0 1 2; do [ "$(m5 "${NAMES[$i]}")" = "${TOS[$i]}" ] || stop "the kit's ${NAMES[$i]} is not the built one"; done
if [ "${1:-}" = "--undo" ]; then
  for i in 0 1 2; do [ -f "$(bak "${NAMES[$i]}" "${FROMS[$i]}")" ] || stop "no backup of ${NAMES[$i]} -- nothing to undo"; done
  ok=$(putback); "$SYSTEMCTL" restart "$FSVC" || true
  [ "$ok" = 1 ] && echo "UNDONE: the three files are back; finance $(wait200 fhz). (Answers the rules already gave stay -- each is a 'system · S791' line on his 'Filed by themselves' tile, with 'Wrong patient? Move'.)" || echo "!! not back -- send a photo"
  exit 0
fi
echo "[1/6] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
NDONE=0
for i in 0 1 2; do
  L=$(m5 "$(live "${NAMES[$i]}")")
  if [ "$L" = "${TOS[$i]}" ]; then NDONE=$((NDONE+1)); continue; fi
  [ "$L" = "${FROMS[$i]}" ] || stop "the live ${NAMES[$i]} is not the expected one (live ${L:0:8}, kit expects ${FROMS[$i]:0:8})"
done
[ "$NDONE" = 3 ] && { echo "-- ALREADY INSTALLED. Nothing written. finance $(fhz)"; exit 0; }
[ "$NDONE" = 0 ] || stop "only some of the three files are this kit's -- a half install; send a photo"
SCR=$(mktemp -d /tmp/s791.XXXX); chmod 700 "$SCR"; mkdir -p "$SCR/remake" "$SCR/live" "$SCR/w7"
for n in "${NAMES[@]}"; do \cp -p "$(live "$n")" "$SCR/live/"; done
"$APY" -B "$KDIR/make_s791.py" "$SCR/live" "$SCR/remake" >/dev/null 2>&1 || stop "make_s791.py on the live bytes does not give the kit's files"
for i in 0 1 2; do [ "$(m5 "$SCR/remake/${NAMES[$i]}")" = "${TOS[$i]}" ] || stop "the remade ${NAMES[$i]} is not the kit's"; done
for n in "${NAMES[@]}"; do "$APY" -W ignore -B -m py_compile "$KDIR/$n" 2>/dev/null || stop "$n does not compile with $APY"; done
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[2/6] the live files are the expected ones; the kit's are those + the S791 change (remade on the box); they compile"
"$APY" -c "import sqlite3; s=sqlite3.connect('file:$DB?mode=ro', uri=True); d=sqlite3.connect('$SCR/f.db'); s.backup(d); d.close(); s.close()" 2>/dev/null || stop "could not copy finance.db for the walk"
\cp -p "$KDIR/check_screens.py" "$KDIR/records.py" "$KDIR/DUTY_MAP.json.s787" "$SCR/w7/"
run() { (cd "$SCR" && TMPDIR="$SCR" S791_LIBS="$ROOT/finance" S787_LIBS="$ROOT/finance" S788_LIBS="$ROOT/finance" S789_LIBS="$ROOT/finance" S787_ANY=1 \
         timeout 300 "$APY" -W ignore -B "$@" "$SCR/f.db" 2>&1); }
R1=$(run "$KDIR/walk_s791.py" "$KDIR" | tail -1)
case "$R1" in "WALK OK"*) ;; *) run "$KDIR/walk_s791.py" "$KDIR" | grep -E '^BAD|Error' | head -6; stop "the S791 walk on a copy of today's database is not green ($R1)";; esac
R7=$(run "$KDIR/walk_s787.py" "$SCR/w7" | tail -1)
case "$R7" in "WALK OK"*) ;; *) run "$KDIR/walk_s787.py" "$SCR/w7" | grep -E '^BAD|Error' | head -6; stop "S787's walk on the new files is not green ($R7)";; esac
R8=$(run "$KDIR/walk_s788.py" "$KDIR" | tail -1)
case "$R8" in "WALK OK"*) ;; *) run "$KDIR/walk_s788.py" "$KDIR" | grep -E '^BAD|Error' | head -6; stop "S788's walk on the new files is not green ($R8)";; esac
R9=$(run "$KDIR/walk_s789.py" "$KDIR" | tail -1)
case "$R9" in "WALK OK"*) ;; *) run "$KDIR/walk_s789.py" "$KDIR" | grep -E '^BAD|Error' | head -6; stop "S789's walk on the new files is not green ($R9)";; esac
RC=$(run "$KDIR/walk_s791.py" "$SCR/live" --control | tail -1)
case "$RC" in "CONTROL: red"*) ;; *) stop "the control on the live files did not go red ($RC)";; esac
rm -f "$SCR/f.db"; find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[3/6] on a copy of today's finance.db: S791 $R1 | S787 $R7 | S788 $R8 | S789 $R9 | the live files: $RC"
[ "$(fhz)" = 200 ] || stop "finance is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
echo "[4/6] the build lock taken; the doctor's auto-fix paused for the restart"
for i in 0 1 2; do
  f=$(live "${NAMES[$i]}"); b=$(bak "${NAMES[$i]}" "${FROMS[$i]}")
  { \cp -p "$f" "$b" && [ "$(m5 "$b")" = "${FROMS[$i]}" ]; } || stop "could not keep a backup of $f"
done
PLACED=1
for i in 0 1 2; do
  f=$(live "${NAMES[$i]}"); b=$(bak "${NAMES[$i]}" "${FROMS[$i]}")
  \cp "$KDIR/${NAMES[$i]}" "$f.s791new" && chmod --reference="$b" "$f.s791new" && chown --reference="$b" "$f.s791new" 2>/dev/null; mv -f "$f.s791new" "$f" || restore "${NAMES[$i]} could not be placed"
  [ "$(m5 "$f")" = "${TOS[$i]}" ] || restore "${NAMES[$i]} read-back did not match"
done
find "$ROOT/finance" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(hcode "http://127.0.0.1:$FIN_PORT/finance/records/xray-check"); case "$c2" in 302|401|403|303) ;; *) restore "his X-ray page answered $c2 without a login";; esac
c3=$(hcode "http://127.0.0.1:$FIN_PORT/finance/records/api/xray-plan"); case "$c3" in 302|303|401|403) ;; *) restore "the filing plan's door answered $c3 without its token";; esac   # S430 run 1: the live box sends it to the login (302)
sleep 2
JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'check_screens|owner_console|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'check|console|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
PLACED=0
echo "[5/6] placed (backups *.bak_S791_*); restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): finance $c1; his X-ray page's door closed without a login ($c2); the plan's door wants its token ($c3); journal clean"
echo "[6/6] $KIT: DONE. The next filing run (every 15 minutes) files what the 8 rules settle; X-rays of someone not registered show red on your console."
