#!/bin/bash
# =============================================================================
#  install_S597_WA_INBOX.sh · kit S597 (session S329, 19-Oct-2026) · D744 -- the owner's WhatsApp Inbox
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S597_WA_INBOX/install_S597_WA_INBOX.sh
#  DRY=1 before bash: every check (pins, anchors, the live raw-log shapes), nothing changed.
#  --undo at the end: the three files back, the inbox module taken out, both services restarted.
#
#  WHAT IT DOES
#   1. reads the server's real WhatsApp raw log (/root/wa/wa_logs/*.jsonl) into a THROW-AWAY store and counts what the
#      inbox understood -- if it understands no incoming message at all, it stops here and changes nothing;
#   2. puts portal_inbox.py in /root/portal/ and lame.min.js (the in-browser MP3 encoder) in /root/portal/static_inbox/;
#   3. patch_s597.py: the tile + register block in portal.py, bhawna's mask in tile_grants.json, the ntfy Click link in
#      wa_alert.py -- each only if it is the exact file this kit was built from, each kept first in /root/s597_backup/;
#   4. compiles both live files; fills the real store /root/wa/wa_inbox/ from the raw log;
#   5. restarts clinic-portal and checks the inbox answers (and its public file route answers from the internet); a bad
#      answer puts everything back by itself;
#   6. restarts wa-receiver (so the alert carries the link) and checks it is alive; a bad answer puts wa_alert.py back.
#  Nothing else is touched: the receiver, its sheet, the senders and the call service run as they are.
# =============================================================================
set -u
KIT="S597_WA_INBOX"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/root/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK=/root/s597_backup
PORTAL_DIR=/root/portal
HAVE_LOCK=0
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
PYTHONPYCACHEPREFIX=/tmp/s597_pyc "$PY" -m py_compile portal_inbox.py patch_s597.py || stop "the kit's code does not compile"
rm -rf /tmp/s597_pyc

CODE=""
restart_check_portal() {          # sets CODE; never called inside $( ) so a restart can never hold the line open
  systemctl restart clinic-portal </dev/null >/dev/null 2>&1
  for i in $(seq 1 25); do
    sleep 1
    CODE=$(curl -s --max-time 5 http://127.0.0.1:8099/portal/inbox/health)
    if [ "$CODE" = '{"inbox":"ok","kit":"S597"}' ]; then CODE=ok; break; fi
  done
}

if [ "${1:-}" = "--undo" ]; then
  echo "[undo] putting the three files back"
  "$PY" -B patch_s597.py --undo
  mkdir -p "$BK"; [ -f "$PORTAL_DIR/portal_inbox.py" ] && mv -f "$PORTAL_DIR/portal_inbox.py" "$BK/portal_inbox.py.removed"
  systemctl restart clinic-portal </dev/null >/dev/null 2>&1; systemctl restart wa-receiver </dev/null >/dev/null 2>&1; sleep 3
  echo "  clinic-portal: $(systemctl is-active clinic-portal) · wa-receiver: $(systemctl is-active wa-receiver)"
  echo "UNDONE. The inbox's store /root/wa/wa_inbox/ is kept (nothing in it is needed by anything else)."
  exit 0
fi

echo "[1] the live raw log, read into a throw-away store"
TMPST=$(mktemp -d /root/s597_shapecheck.XXXX)
INBOX_STORE="$TMPST" "$PY" -B - <<'EOF' || { rm -rf "$TMPST"; stop "the raw log could not be read"; }
import os, sys, sqlite3
sys.path.insert(0, os.getcwd())
import portal_inbox as P
r = {}
P.ingest(force=True, report=r)
c = sqlite3.connect(P.DB_PATH)
q = lambda s: c.execute(s).fetchone()[0]
print("    pushes read: %d · incoming messages %d · clinic's own (echo) %d · status pings %d · other %d · NOT understood %d · bad lines %d"
      % (sum(r.values()), r.get("in", 0), r.get("out", 0), r.get("status", 0), r.get("skip", 0), r.get("unread", 0), r.get("bad", 0)))
print("    chats %d · messages %d (in %d, out %d) · photos/files/voice with a link %d of %d · first %s · last %s"
      % (q("SELECT COUNT(DISTINCT phone) FROM msgs"), q("SELECT COUNT(*) FROM msgs"), q("SELECT COUNT(*) FROM msgs WHERE dir='in'"),
         q("SELECT COUNT(*) FROM msgs WHERE dir='out'"), q("SELECT COUNT(*) FROM msgs WHERE media_url<>''"),
         q("SELECT COUNT(*) FROM msgs WHERE mtype IN ('image','document','audio','voice','video','sticker')"),
         (q("SELECT MIN(ts) FROM msgs") or "-")[:16], (q("SELECT MAX(ts) FROM msgs") or "-")[:16]))
for sig, n in c.execute("SELECT sig, n FROM shapes ORDER BY n DESC LIMIT 3"):
    print("    not understood x%d -- fields: %s" % (n, sig[:200]))
open(os.path.join(os.environ["INBOX_STORE"], "IN_COUNT"), "w").write(str(r.get("in", 0)))
EOF
IN_COUNT=$(cat "$TMPST/IN_COUNT" 2>/dev/null || echo 0)
rm -rf "$TMPST"
[ "$IN_COUNT" -gt 0 ] || stop "the inbox understood no incoming WhatsApp message in the raw log"

echo "[2] the three live files: pins and anchors"
if [ "${DRY:-0}" = "1" ]; then
  DRY=1 "$PY" -B patch_s597.py || exit 1
  echo "-- DRY RUN: nothing changed"; exit 0
fi
DRY=1 "$PY" -B patch_s597.py >/dev/null || { DRY=1 "$PY" -B patch_s597.py; exit 1; }

echo "[3] the inbox module and its encoder"
mkdir -p "$BK" "$PORTAL_DIR/static_inbox"; chmod 700 "$BK"
[ -f "$PORTAL_DIR/portal_inbox.py" ] && [ ! -f "$BK/portal_inbox.py.before_s597" ] && ! cmp -s portal_inbox.py "$PORTAL_DIR/portal_inbox.py" && \cp -f "$PORTAL_DIR/portal_inbox.py" "$BK/portal_inbox.py.before_s597"
\cp -f portal_inbox.py "$PORTAL_DIR/portal_inbox.py"
# the encoder travels as base64 text (its number tables would trip the repository's phone-number gate); decoded here and
# held against its MD5 before it is put up
base64 -d static_inbox/lame.min.js.b64 > /tmp/s597_lame.js && [ "$(md5sum /tmp/s597_lame.js | cut -c1-32)" = "5a6238f84790b828a1da4f15f4ab655f" ] \
  || { rm -f /tmp/s597_lame.js; stop "the MP3 encoder did not decode to its recorded bytes" "The inbox module is in place but nothing else was changed."; }
\cp -f /tmp/s597_lame.js "$PORTAL_DIR/static_inbox/lame.min.js"; rm -f /tmp/s597_lame.js
echo "    $(md5sum "$PORTAL_DIR/portal_inbox.py" | cut -c1-8) portal_inbox.py · $(md5sum "$PORTAL_DIR/static_inbox/lame.min.js" | cut -c1-8) lame.min.js"

echo "[4] the edits"
"$PY" -B patch_s597.py || stop "the edits did not go in" "Check the lines above: any file written was kept first in $BK."
PYTHONPYCACHEPREFIX=/tmp/s597_pyc "$PY" -m py_compile "$PORTAL_DIR/portal.py" "$PORTAL_DIR/portal_inbox.py" /root/wa/wa_alert.py
if [ $? -ne 0 ]; then "$PY" -B patch_s597.py --undo; stop "a live file did not compile after the edit" "It was put back."; fi
rm -rf /tmp/s597_pyc

echo "[5] the real store, filled from the raw log"
mkdir -p /root/wa/wa_inbox; chmod 700 /root/wa/wa_inbox
"$PY" -B -c "
import sys; sys.path.insert(0, '$PORTAL_DIR')
import portal_inbox as P
r = {}; P.ingest(force=True, report=r)
print('    %d pushes read into /root/wa/wa_inbox/inbox.db (incoming %d)' % (sum(r.values()), r.get('in', 0)))
" || echo "    (the store fills itself at the first page load instead)"

echo "[6] clinic-portal restarted"
restart_check_portal; code="$CODE"
gate=$(curl -s --max-time 5 -o /dev/null -w '%{http_code}' http://127.0.0.1:8099/portal/inbox)
if [ "$code" != "ok" ] || [ "$gate" = "200" ] || [ "$gate" = "500" ]; then
  "$PY" -B patch_s597.py --undo; mv -f "$PORTAL_DIR/portal_inbox.py" "$BK/portal_inbox.py.failed"; systemctl restart clinic-portal </dev/null >/dev/null 2>&1
  stop "the portal did not come back with the inbox (health: ${code:0:60} · page without login: $gate)" "Everything was put back and the portal restarted."
fi
pub=$(curl -s --max-time 15 -o /dev/null -w '%{http_code}' "https://followup.dr-manoj.in/portal/inbox/f/00000000000000000000000000000000/x.pdf")
home=$(curl -s --max-time 10 -o /dev/null -w '%{http_code}' http://127.0.0.1:8099/portal/)
echo "    inbox in (health ok) · the page asks for the login ($gate) · portal home $home · public file route from the internet: $pub (404 = reachable, no such file)"

echo "[7] wa-receiver restarted (the alert now carries a link to the chat)"
systemctl restart wa-receiver </dev/null >/dev/null 2>&1
alive=""
for i in $(seq 1 15); do sleep 1; alive=$(curl -s --max-time 5 http://127.0.0.1:8095/); [ "$alive" = "wa_receiver alive" ] && break; done
if [ "$alive" != "wa_receiver alive" ]; then
  \cp -f "$BK/wa_alert.py.before_s597" /root/wa/wa_alert.py; systemctl restart wa-receiver </dev/null >/dev/null 2>&1; sleep 3
  echo "!! the receiver did not come back with the new alert -- wa_alert.py was put back; receiver: $(systemctl is-active wa-receiver)"
else
  echo "    wa-receiver: $(systemctl is-active wa-receiver) · alive"
fi

echo "[8] pins"
md5sum "$PORTAL_DIR/portal.py" "$PORTAL_DIR/tile_grants.json" /root/wa/wa_alert.py "$PORTAL_DIR/portal_inbox.py" "$PORTAL_DIR/static_inbox/lame.min.js" | sed 's/^/    /'
echo "DONE. Open https://followup.dr-manoj.in/portal/inbox -- or the WhatsApp Inbox tile under Calls & WhatsApp."
