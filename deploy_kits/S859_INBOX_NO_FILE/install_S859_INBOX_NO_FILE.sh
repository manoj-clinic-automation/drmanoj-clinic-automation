#!/bin/bash
# =============================================================================
#  install_S859_INBOX_NO_FILE.sh . kit S859 (17-Nov-2026, session S478, the parent) . F-1358's page half, F-1366, D964
#  The WhatsApp Inbox: (1) an incoming photo/PDF/voice whose push came without a file link and none came after 10 minutes says
#  "MyOperator did not give this file" with an "Open in MyOperator" link, instead of "has not arrived yet" for good; (2) the
#  Inbox's health answer counts such rows (last 30 days; a number only); (3) the file route fetches a link with a space or a
#  non-English letter percent-encoded, and a read timeout / an invalid link answers a plain 502 sentence, never a bare 500.
#    /root/portal/portal_inbox.py 973cc74f -> ff0f02a8
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s859kit && cp -rp /root/deploy/repo/deploy_kits/S859_INBOX_NO_FILE /tmp/s859kit && bash /tmp/s859kit/install_S859_INBOX_NO_FILE.sh
#  DRY=1 runs every gate and writes nothing.   Undo:  bash /tmp/s859kit/install_S859_INBOX_NO_FILE.sh --undo
# =============================================================================
set -u
KIT="S859_INBOX_NO_FILE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F1="$ROOT/portal/portal_inbox.py"; FROM1=973cc74f1603ecd2594ac69f52c543df; TO1=ff0f02a89d66863b228de0a22e888367; BAK1="$F1.bak_S859_${FROM1:0:8}"
DOORS="/portal /portal/console /portal/inbox /portal/messages /portal/wa"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
doors() { local o=""; for d in $DOORS; do o="$o $d=$(hcode "http://127.0.0.1:$PPORT$d")"; done; echo "${o# }"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${WAITS:-3}"; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
pyc() { "$1" -W ignore -B -c "import sys;compile(open(sys.argv[1],encoding='utf-8').read(),sys.argv[1],'exec')" "$2" 2>/dev/null; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
take_lock() {
  mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
  HAVE_LOCK=1; echo "$KIT $$ $(TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M:%S IST')" > "$LOCK/owner"
  if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(TZ=Asia/Kolkata date '+%F %T IST')" > "$OFFSW" && OFF_MINE=1; fi
}
putback() {
  [ -f "$BAK1" ] && \cp -p "$BAK1" "$F1"
  rm -f "$F1.s859new"
  find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  [ "$(m5 "$F1")" = "$FROM1" ] && echo 1 || echo 0
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting the old file back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "   portal_inbox.py is back byte-identically; the Inbox is as it was" \
                || echo "   !! NOT back -- copy $BAK1 back by hand"
  echo "   portal health $(wait200 phz). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 portal_inbox.py)" = "$TO1" ] || stop "the kit's portal_inbox.py is not the built one"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK1" ] && [ "$(m5 "$BAK1")" = "$FROM1" ] || stop "no good backup -- nothing to undo"
  L1=$(m5 "$F1")
  { [ "$L1" = "$TO1" ] || [ "$L1" = "$FROM1" ]; } || stop "portal_inbox.py has been changed since this kit (a later kit is on top) -- not undone"
  take_lock
  ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  hu=$(wait200 phz)
  [ "$ok" = 1 ] && [ "$hu" = 200 ] && { echo "UNDONE: portal_inbox.py is back byte-identically; portal health $hu"; exit 0; }
  echo "!! not back (file back: $ok, portal health $hu) -- send a photo of this screen to Claude"; exit 1
fi
echo "[1/5] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1")
if [ "$L1" = "$TO1" ]; then echo "-- ALREADY INSTALLED. Nothing written. portal $(phz)"; exit 0; fi
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not the expected one (live ${L1:0:8}, kit expects ${FROM1:0:8})"
pyc "$APY" "$KDIR/portal_inbox.py" || stop "the kit's portal_inbox.py does not compile with $APY"
pyc "$VPY" "$KDIR/portal_inbox.py" || stop "the kit's portal_inbox.py does not compile with $VPY"
echo "[2/5] the live portal_inbox.py is ${FROM1:0:8}; the kit's compiles"
SCR=$(mktemp -d /tmp/s859.XXXX) || stop "no scratch folder"; chmod 700 "$SCR"
\cp -p "$F1" "$SCR/live_inbox.py"
R=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s859.py" "$KDIR/portal_inbox.py" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) (cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s859.py" "$KDIR/portal_inbox.py" 2>&1 | grep FAIL | head -6); stop "the walk is not green ($R)";; esac
R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s859.py" "$SCR/live_inbox.py" 2>&1 | tail -1)
case "$R2" in "WALK RED"*) ;; *) stop "the control (the live file) did not go red ($R2)";; esac
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[3/5] the walk (a made-up store, a stand-in fetch, the page opened): $R | control: $R2"
c1=$(phz); [ "$c1" = 200 ] || stop "the portal is not healthy before the install (health $c1)"
D0=$(doors)
echo "[4/5] before: portal health $c1; the doors without a login: $D0"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
take_lock
{ \cp -p "$F1" "$BAK1" && [ "$(m5 "$BAK1")" = "$FROM1" ]; } || stop "could not keep a backup of $F1"
PLACED=1
for pair in "portal_inbox.py:$F1:$BAK1:$TO1"; do
  IFS=: read -r src dst ref to <<< "$pair"
  \cp "$KDIR/$src" "$dst.s859new" && chmod --reference="$ref" "$dst.s859new" && chown --reference="$ref" "$dst.s859new" 2>/dev/null; mv -f "$dst.s859new" "$dst" || restore "$src could not be placed"
  [ "$(m5 "$dst")" = "$to" ] || restore "$src read-back did not match"
done
find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
c2=$(wait200 phz); [ "$c2" = 200 ] || restore "portal health $c2"
D1=$(doors); [ "$D1" = "$D0" ] || restore "a door answers differently after the restart (before: $D0 | after: $D1)"
IH=$(curl -s -m 8 "http://127.0.0.1:$PPORT/portal/inbox/health")
case "$IH" in *'"inbox": "ok"'*'"no_file_30d"'*|*'"inbox":"ok"'*'"no_file_30d"'*|*'"no_file_30d"'*'"inbox": "ok"'*|*'"no_file_30d"'*'"inbox":"ok"'*) ;; *) restore "the Inbox's health does not answer as built (${IH:0:120})";; esac
sleep "${WAITS:-2}"
JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'NOT mounted|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|AssertionError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'tile|mounted|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
[ "$(m5 "$F1")" = "$TO1" ] || restore "portal_inbox.py is not the placed one at the end"
PLACED=0
echo "[5/5] placed (backup $BAK1); the portal restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): health $c2; every door answers as before; the Inbox's health: $IH; journal clean"
echo "$KIT: DONE. In the WhatsApp Inbox, a photo or PDF that MyOperator never gave now says so, with an Open in MyOperator link; a file that cannot be fetched gives a plain message, never an error page."
