#!/bin/bash
# =============================================================================
#  install_S608_WA_SEND_LOG.sh · kit S608 (session S331, 21-Oct-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S608_WA_SEND_LOG/install_S608_WA_SEND_LOG.sh
#  DRY=1 before bash: pins, rebuild, walk and control only -- nothing changed.   --undo at the end: the S599 file back.
#
#  THE OWNER, 21-Oct-2026 10:57 IST: "maintain a detailed log, which I can share with myoperator team as needed,
#  without needing you."  The inbox kept no record when MyOperator refused a message.
#   1. every send from the inbox (text, photo, PDF, voice, template) is logged: time, who, customer, what, MyOperator's
#      HTTP status, full reply, x-amzn-requestid, time taken, the exact request (never the key);
#   2. https://followup.dr-manoj.in/portal/inbox/sendlog -- the owner's page: all / refused only, CSV download, and
#      "Email to MyOperator" (from the clinic Gmail, on ticket 691386, the CSV attached);
#   3. each refused send is mailed to the clinic Gmail by itself ("[WA send refused] ..."), ready to forward.
#   Sending itself is unchanged: the same request, the same key, the same answers on screen.
# =============================================================================
set -u
KIT="S608_WA_SEND_LOG"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/root/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-/root/s608_backup}"
PD="${PD:-/root/portal}"
SVC="${SVC:-clinic-portal}"
BASE="${BASE:-http://127.0.0.1:8099}"
WAENV="${WAENV:-/root/wa/.env}"
PIN_IN="7bb6e0d7c1540103067ffbe4b5f2de76"
W=/tmp/s608_walk
HAVE_LOCK=0
on_exit() { rm -rf "$W" /tmp/s608_rb.py; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
m5() { md5sum "$1" 2>/dev/null | cut -c1-32; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
"$PY" -c "import flask" 2>/dev/null || PY=/usr/bin/python3
PYTHONPYCACHEPREFIX=/tmp/s608_pyc "$PY" -m py_compile portal_inbox.py walk_s608.py edits_s608.py || stop "the kit's code does not compile"
rm -rf /tmp/s608_pyc
NEW=$(m5 portal_inbox.py)

check_up() {                      # sets OKH; never inside $( )
  OKH=0
  systemctl restart "$SVC" </dev/null >/dev/null 2>&1
  HL=""
  for i in $(seq 1 30); do
    sleep 1
    HL=$(curl -s --max-time 5 "$BASE/portal/inbox/health")
    [ "$HL" = '{"inbox":"ok","kit":"S608"}' ] && break
  done
  GATE=$(curl -s --max-time 5 -o /dev/null -w '%{http_code}' "$BASE/portal/inbox/sendlog")
  HOME_=$(curl -s --max-time 8 -o /dev/null -w '%{http_code}' "$BASE/portal/")
  [ "$HL" = '{"inbox":"ok","kit":"S608"}' ] && [ "$GATE" != "200" ] && [ "$GATE" != "404" ] && [ "${GATE:0:1}" != "5" ] && OKH=1
}

if [ "${1:-}" = "--undo" ]; then
  echo "[undo]"
  b=$(ls -1t "$BK"/portal_inbox.py.bak_S608_* 2>/dev/null | head -1)
  [ -n "$b" ] && \cp -f "$b" "$PD/portal_inbox.py" && echo "    portal_inbox.py put back ($(m5 "$PD/portal_inbox.py" | cut -c1-8))"
  systemctl restart "$SVC" </dev/null >/dev/null 2>&1; sleep 4
  echo "    $SVC: $(systemctl is-active "$SVC") · inbox health $(curl -s --max-time 5 "$BASE/portal/inbox/health")"
  echo "    The log file /root/wa/wa_inbox/send_log.jsonl stays (the record of what was sent)."
  echo "UNDONE."; exit 0
fi

echo "[1] pins"
NOW=$(m5 "$PD/portal_inbox.py")
if [ "$NOW" = "$NEW" ]; then echo "    ALREADY INSTALLED (portal_inbox.py ${NEW:0:8})"; exit 0; fi
[ "$NOW" = "$PIN_IN" ] || stop "portal_inbox.py is not the S599 file this kit was built on (${NOW:0:8}, expected ${PIN_IN:0:8})"
echo "    portal_inbox.py ${NOW:0:8} (S599)"

echo "[2] rebuild from the live bytes"
"$PY" -B edits_s608.py "$PD/portal_inbox.py" /tmp/s608_rb.py "$KDIR/portal_inbox.py" || stop "the kit's file is not exactly the live file plus this kit's edits"

echo "[3] the walk (a stand-in MyOperator and mail server, a scratch store -- nothing real sent)"
rm -rf "$W"; mkdir -p "$W/code" "$W/ctl"; chmod 700 "$W"
\cp -f portal_inbox.py "$W/code/"; \cp -f "$PD/portal_inbox.py" "$W/ctl/"
for f in portal_wa.py; do [ -f "$PD/$f" ] && \cp -f "$PD/$f" "$W/code/" && \cp -f "$PD/$f" "$W/ctl/"; done
[ -d "$PD/static_inbox" ] && \cp -rf "$PD/static_inbox" "$W/code/" && \cp -rf "$PD/static_inbox" "$W/ctl/"
"$PY" -B walk_s608.py --code "$W/code" --scratch "$W/s1" > "$W/walk.txt" 2>&1
WK=$?; grep -E "^WALK" "$W/walk.txt" | sed 's/^/    /'; tail -1 "$W/walk.txt" | sed 's/^/    walk: /'
[ "$WK" = 0 ] || { grep "FAIL\|RED\|Error" "$W/walk.txt" | head -8; stop "the walk is not green"; }
"$PY" -B walk_s608.py --code "$W/ctl" --scratch "$W/s2" > "$W/ctl.txt" 2>&1
[ $? != 0 ] && echo "    control on the live (S599) file: RED, as it must be ($(grep -m1 'RED' "$W/ctl.txt" | cut -c1-60))" \
            || stop "the control did not go red -- the walk cannot tell old from new"
rm -rf "$W"
if [ "${DRY:-0}" = "1" ]; then echo "-- DRY RUN: nothing changed"; exit 0; fi

echo "[4] backup -> $BK"
mkdir -p "$BK"; chmod 700 "$BK"
\cp -f "$PD/portal_inbox.py" "$BK/portal_inbox.py.bak_S608_$NOW"; chmod 600 "$BK"/*
echo "    portal_inbox.py kept"

echo "[5] placed"
\cp -f portal_inbox.py "$PD/portal_inbox.py"
[ "$(m5 "$PD/portal_inbox.py")" = "$NEW" ] || stop "portal_inbox.py did not land byte-exact" "Run the line again with --undo at the end."
echo "    portal_inbox.py ${NOW:0:8} -> ${NEW:0:8}"

echo "[6] $SVC restarted and checked"
check_up
if [ "$OKH" != 1 ]; then
  \cp -f "$BK/portal_inbox.py.bak_S608_$NOW" "$PD/portal_inbox.py"
  systemctl restart "$SVC" </dev/null >/dev/null 2>&1
  stop "the portal did not come back with the send log (health: ${HL:0:60} · log page without login: $GATE)" \
       "The S599 file was put back and $SVC restarted."
fi
echo "    inbox health S608 · the log page asks for the login ($GATE) · portal home $HOME_"
grep -q '^WATCHDOG_SMTP_USER=.' "$WAENV" 2>/dev/null && grep -q '^WATCHDOG_SMTP_PASS=.' "$WAENV" 2>/dev/null \
  && echo "    the clinic Gmail settings the mails use: present (not shown)" \
  || echo "    !! the clinic Gmail settings are not in $WAENV -- the log works, the two mails will not go"

echo "[7] pins"
echo "    $(md5sum "$PD/portal_inbox.py")"
echo "DONE. Open https://followup.dr-manoj.in/portal/inbox/sendlog"
