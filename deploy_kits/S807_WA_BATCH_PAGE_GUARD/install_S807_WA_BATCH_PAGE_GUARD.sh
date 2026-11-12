#!/bin/bash
# =============================================================================
#  install_S807_WA_BATCH_PAGE_GUARD.sh . kit S807 (12-Nov-2026, session S440, the parent) . F-1301.
#  The old follow-up batch page /portal/wa/followups is LIVE and stood on a list of 13-Aug with nothing saying so. After this
#  kit the page and its send door work on TODAY's list only (a file named Staff_Action_Today_YYYY-MM-DD.xlsx for today, IST),
#  the send door sends only a sendable row of today's list read again at the moment of sending (number and words from the
#  list), stops at a sender failure, and the page says LIVE or TEST at its top.
#  ONE file changes: /root/portal/portal_followups.py (98547bc4 -> the kit's). The page file is untouched. Nothing is sent.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s807kit && cp -rp /root/deploy/repo/deploy_kits/S807_WA_BATCH_PAGE_GUARD /tmp/s807kit && bash /tmp/s807kit/install_S807_WA_BATCH_PAGE_GUARD.sh
#  DRY=1 runs every gate and writes nothing.   Undo: ... --undo
# =============================================================================
set -u
KIT="S807_WA_BATCH_PAGE_GUARD"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F1="$ROOT/portal/portal_followups.py"; FROM1=98547bc41869360bf224b190fc27cc5d; TO1=ed1121ec09d039bc9176f065f1bcb731; BAK1="$F1.bak_S807_${FROM1:0:8}"
FUDIR="${PORTAL_FOLLOWUP_DIR:-$ROOT/wa/followups}"; PAGEF="${PORTAL_WA_DIR:-$ROOT/wa/wa_portal}/followups_page.html"
WALK_WANT="WALK OK 47/47"; PAGE_REPO=9c22db64
U_PAGE="http://127.0.0.1:$PPORT/portal/wa/followups"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""; PB=""; DB0=""; SB0=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
pcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{"items":[]}' "$1"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${WAITS:-3}"; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
closed() { case "$1" in 302|303|401|403) return 0;; *) return 1;; esac; }
# mine LOCK / OFF switch left by a run of THIS kit that was killed
stale_mine() { [ -f "$LOCK/owner" ] && grep -q "^$KIT " "$LOCK/owner" 2>/dev/null && { rm -rf "$LOCK"; echo "   (a lock left by an earlier, interrupted run of this kit was cleared)"; }
  [ -f "$OFFSW" ] && grep -q "^$KIT " "$OFFSW" 2>/dev/null && { rm -f "$OFFSW"; echo "   (the pause switch left by an earlier, interrupted run of this kit was cleared)"; }; return 0; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
putback() {
  [ -f "$BAK1" ] && \cp -p "$BAK1" "$F1"; rm -f "$F1.s807new"
  find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  [ "$(m5 "$F1")" = "$FROM1" ] && echo 1 || echo 0
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting the file back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "   portal_followups.py is back byte-identically" || echo "   !! NOT back -- copy $BAK1 over $F1 by hand"
  echo "   portal health $(wait200 phz). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP
# what a given copy of the module says about the list on the server -- the list's date only, never a row of it
liststate() { ( cd /tmp && PORTAL_FOLLOWUP_DIR="$FUDIR" timeout 30 "$VPY" -I -B -c '
import sys
sys.path.insert(0, sys.argv[1])
import portal_followups as m
s = m.list_state(m.find_latest())
print("the list on the server: %s -> %s" % (s["file_date"] or ("not named for a day" if s["file"] else "none"), "today'"'"'s, the page works" if s["fresh"] else "REFUSED, nothing can be sent from the page"))
' "$1" 2>&1 | tail -1 ); }

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 portal/portal_followups.py)" = "$TO1" ] || stop "the kit's file is not the built one"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK1" ] && [ "$(m5 "$BAK1")" = "$FROM1" ] || stop "no good backup -- nothing to undo"
  L1=$(m5 "$F1"); [ "$L1" = "$TO1" ] || [ "$L1" = "$FROM1" ] || stop "portal_followups.py has been changed since this kit (a later kit is on top) -- not undone"
  ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && { echo "UNDONE: portal_followups.py is back as it was before S807; portal $(wait200 phz). The old batch page again shows whatever list is on the server, with no LIVE / TEST strip."; exit 0; }
  echo "!! not back -- send a photo"; exit 1
fi
echo "[1/5] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1")
if [ "$L1" = "$TO1" ]; then
  echo "-- ALREADY INSTALLED. Nothing written. portal $(phz)"; stale_mine
  a1=$(hcode "$U_PAGE"); a2=$(hcode "$U_PAGE/data"); a3=$(pcode "$U_PAGE/send")
  if closed "$a1" && closed "$a2" && closed "$a3"; then echo "   the three doors answer $a1 $a2 $a3 without a login (closed)"; else echo "!! the three doors answer $a1 $a2 $a3 without a login -- NOT as expected (404 on the second = the page did not load). Send a photo of this screen to Claude."; fi
  echo "   now: $(liststate "$ROOT/portal")"; exit 0
fi
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not the expected one (live ${L1:0:8}, kit expects ${FROM1:0:8})"
SCR=$(mktemp -d /tmp/s807.XXXX) || stop "no scratch folder could be made in /tmp"
[ -n "$SCR" ] && [ -d "$SCR" ] || stop "no scratch folder could be made in /tmp"
chmod 700 "$SCR"; mkdir -p "$SCR/remake" "$SCR/live/portal"
"$APY" -B "$KDIR/make_s807.py" "$F1" "$SCR/remake" >/dev/null 2>&1 && [ "$(m5 "$SCR/remake/portal/portal_followups.py")" = "$TO1" ] || stop "make_s807.py on the live bytes does not give the kit's file"
"$APY" -W ignore -B -m py_compile "$KDIR/portal/portal_followups.py" 2>/dev/null && "$VPY" -W ignore -B -m py_compile "$KDIR/portal/portal_followups.py" 2>/dev/null || stop "portal_followups.py does not compile"
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[2/5] the live portal_followups.py is ${FROM1:0:8}; the kit's is that + the S807 edits (remade on the box); it compiles"
\cp -p "$F1" "$SCR/live/portal/portal_followups.py"
R=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s807.py" "$KDIR" 2>&1 | tail -1)
[ "$R" = "$WALK_WANT" ] || { (cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s807.py" "$KDIR" 2>&1 | grep '^BAD' | head -6); stop "the S807 walk is not green ($R; wanted $WALK_WANT)"; }
R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s807.py" "$SCR/live" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live file did not go red ($R2)";; esac
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[3/5] the walk (made-up patients and numbers only; the sender is a recorder): $R | the live file: $R2"
[ "$(phz)" = 200 ] || stop "the portal is not healthy before the install"
PB=$(hcode "$U_PAGE"); closed "$PB" || stop "the page's door answers $PB without a login before the install -- not as expected"
DB0=$(hcode "$U_PAGE/data"); closed "$DB0" || stop "the page's data door answers $DB0 without a login before the install -- not as expected (404 = the batch page is not loaded in the portal)"
SB0=$(pcode "$U_PAGE/send"); closed "$SB0" || stop "the page's send door answers $SB0 without a login before the install -- not as expected"
[ -f "$PAGEF" ] || stop "the page file $PAGEF is not there -- the page is not as this kit expects"
[ "$(grep -o -i '<body' "$PAGEF" | wc -l)" = 1 ] || stop "the page file $PAGEF does not have exactly one <body> tag -- not as this kit expects"
PG=$(m5 "$PAGEF" | cut -c1-8); PGN="the repository's copy"; [ "$PG" = "$PAGE_REPO" ] || PGN="NOT the repository's copy ($PAGE_REPO) -- the strip still goes in; if its Send button does not carry the list's date it is refused (the safe side)"
XB=$(hcode "$U_PAGE/s807-no-such-door"); BLIND=""; closed "$XB" && BLIND=" | note: the portal answers $XB to ANY path without a login, so the door check cannot tell a page that did not load -- the compile, the walk and the read with the placed file stand for it"
LS0=$(liststate "$KDIR/portal")
case "$LS0" in "the list on the server: "*) ;; *) stop "the kit's file could not read the list's date on the server ($LS0)";; esac
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[4/5] before: portal healthy | the three doors closed without a login ($PB $DB0 $SB0) | the page file is there (${PAGEF##*/} $PG, $PGN) | with the new file: $LS0$BLIND"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
{ \cp -p "$F1" "$BAK1" && [ "$(m5 "$BAK1")" = "$FROM1" ]; } || stop "could not keep a backup of $F1"
PLACED=1
{ \cp "$KDIR/portal/portal_followups.py" "$F1.s807new" && [ "$(m5 "$F1.s807new")" = "$TO1" ] && chmod --reference="$BAK1" "$F1.s807new"; } || restore "the new file could not be copied beside the live one"
chown --reference="$BAK1" "$F1.s807new" 2>/dev/null
mv -f "$F1.s807new" "$F1" || restore "portal_followups.py could not be placed"
[ "$(m5 "$F1")" = "$TO1" ] || restore "the read-back did not match"
find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
c2=$(wait200 phz); [ "$c2" = 200 ] || restore "portal health $c2"
c3=$(hcode "$U_PAGE"); [ "$c3" = "$PB" ] || restore "the page's door answers $c3 without a login (before: $PB)"
c4=$(hcode "$U_PAGE/data"); [ "$c4" = "$DB0" ] || restore "the page's data door answers $c4 without a login (before: $DB0; 404 = the batch page did not load)"
c5=$(pcode "$U_PAGE/send"); [ "$c5" = "$SB0" ] || restore "the page's send door answers $c5 without a login (before: $SB0)"
sleep "${WAITS:-2}"
JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null)" || restore "the portal's journal could not be read after the restart"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'Follow-up batch failed|NOT mounted|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|AssertionError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'Follow-up batch|mounted|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
LS1=$(liststate "$ROOT/portal")
case "$LS1" in "the list on the server: "*) ;; *) restore "the placed file could not read the list's date ($LS1)";; esac
find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0
echo "[5/5] placed (backup $BAK1); the portal restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): health $c2; the three doors closed without a login as before ($c3 $c4 $c5); journal clean ($(printf '%s\n' "$JL" | grep -c .) line(s) read)"
echo "      now: $LS1"
echo "      $KIT: DONE. The old follow-up batch page says LIVE or TEST at its top and works on today's list only -- $LS1. Nothing was sent to anyone."
