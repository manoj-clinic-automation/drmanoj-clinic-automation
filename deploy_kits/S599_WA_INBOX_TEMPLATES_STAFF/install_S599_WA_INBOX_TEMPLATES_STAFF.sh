#!/bin/bash
# =============================================================================
#  install_S599_WA_INBOX_TEMPLATES_STAFF.sh · kit S599 (session S329, 19-Oct-2026) · D744
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S599_WA_INBOX_TEMPLATES_STAFF/install_S599_WA_INBOX_TEMPLATES_STAFF.sh
#  DRY=1 before bash: the key check and the switch read, nothing changed.   --undo at the end: everything back.
#
#  THE OWNER, 08:52 IST 19-Oct: "I want to send templates" · "I would like to see the replies which are sent by my staff
#  members in the chat also" · 08:57 "go".
#   1. every WhatsApp key the server holds is held against MyOperator by READING the approved-template list (nothing sent);
#   2. the inbox is told which key works (config.json names its place, never the key) -- the S597 test text was refused
#      (HTTP 500) by the key it had guessed;
#   3. templates go live: portal_config.py PORTAL_WA_DRYRUN = "0" (and the portal's key, if its own is a refused one) --
#      this also makes the Send WhatsApp page and the follow-up batch send for real, as the owner asked;
#   4. portal_inbox.py: the proved key, and each chat shows the clinic's replies from the portal's template log and the
#      call tracker's sheet, with who sent them;
#   5. clinic-portal restarted and checked (a bad answer puts everything back by itself);
#   6. the proof: one text and one approved template (Post-visit, name "Test") to the owner's OWN number.
# =============================================================================
set -u
KIT="S599_WA_INBOX_TEMPLATES_STAFF"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/root/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK=/root/s599_backup
PORTAL_DIR=/root/portal
PIN_IN="14c94a46cb65c388ae10bd5bbe166e58"
HAVE_LOCK=0
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
PYTHONPYCACHEPREFIX=/tmp/s599_pyc "$PY" -m py_compile portal_inbox.py setup_s599.py || stop "the kit's code does not compile"
rm -rf /tmp/s599_pyc
NEW_MD5=$(md5sum portal_inbox.py | cut -c1-32)

health() {                         # sets CODE; never inside $( )
  systemctl restart clinic-portal </dev/null >/dev/null 2>&1
  CODE=""
  for i in $(seq 1 25); do
    sleep 1
    CODE=$(curl -s --max-time 5 http://127.0.0.1:8099/portal/inbox/health)
    [ "$CODE" = '{"inbox":"ok","kit":"S599"}' ] && { CODE=ok; break; }
  done
}

if [ "${1:-}" = "--undo" ]; then
  echo "[undo]"
  [ -f "$BK/portal_inbox.py.before_s599" ] && \cp -f "$BK/portal_inbox.py.before_s599" "$PORTAL_DIR/portal_inbox.py" && echo "    portal_inbox.py put back"
  "$PY" -B setup_s599.py undo
  systemctl restart clinic-portal </dev/null >/dev/null 2>&1; sleep 3
  echo "    clinic-portal: $(systemctl is-active clinic-portal)"
  echo "UNDONE."; exit 0
fi

echo "[1] the WhatsApp keys, held against MyOperator (a read -- nothing is sent)"
"$PY" -B setup_s599.py check || exit 1
if [ "${DRY:-0}" = "1" ]; then echo "-- DRY RUN: nothing changed"; exit 0; fi

echo "[2] the inbox module"
NOW=$(md5sum "$PORTAL_DIR/portal_inbox.py" 2>/dev/null | cut -c1-32)
if [ "$NOW" = "$NEW_MD5" ]; then echo "    already the S599 version"
elif [ "$NOW" = "$PIN_IN" ]; then
  mkdir -p "$BK"; chmod 700 "$BK"
  [ -f "$BK/portal_inbox.py.before_s599" ] || \cp -f "$PORTAL_DIR/portal_inbox.py" "$BK/portal_inbox.py.before_s599"
  \cp -f portal_inbox.py "$PORTAL_DIR/portal_inbox.py"
  echo "    ${PIN_IN:0:8} -> ${NEW_MD5:0:8}"
else stop "portal_inbox.py is not the S597 file (${NOW:0:8}, expected ${PIN_IN:0:8})"; fi

echo "[3] the inbox's key, and templates live"
"$PY" -B setup_s599.py apply || { \cp -f "$BK/portal_inbox.py.before_s599" "$PORTAL_DIR/portal_inbox.py" 2>/dev/null; stop "the settings did not go in" "portal_inbox.py was put back."; }

echo "[4] clinic-portal restarted"
health
gate=$(curl -s --max-time 5 -o /dev/null -w '%{http_code}' http://127.0.0.1:8099/portal/inbox)
if [ "$CODE" != "ok" ] || [ "$gate" = "200" ] || [ "$gate" = "500" ]; then
  \cp -f "$BK/portal_inbox.py.before_s599" "$PORTAL_DIR/portal_inbox.py"; "$PY" -B setup_s599.py undo
  systemctl restart clinic-portal </dev/null >/dev/null 2>&1
  stop "the portal did not come back with the new inbox (health: ${CODE:0:60} · page without login: $gate)" "Everything was put back and the portal restarted."
fi
echo "    inbox in (health ok) · the page asks for the login ($gate) · portal home $(curl -s --max-time 10 -o /dev/null -w '%{http_code}' http://127.0.0.1:8099/portal/)"

echo "[5] the proof -- to YOUR number only"
"$PY" -B setup_s599.py test

echo "[6] pins"
md5sum "$PORTAL_DIR/portal_inbox.py" | sed 's/^/    /'
[ -f "$PORTAL_DIR/portal_config.py" ] && echo "    portal_config.py $(md5sum "$PORTAL_DIR/portal_config.py" | cut -c1-8) (VPS-only; backup in $BK)"
echo "DONE. Your phone should now have the two test messages from the clinic number. Open https://followup.dr-manoj.in/portal/inbox"
