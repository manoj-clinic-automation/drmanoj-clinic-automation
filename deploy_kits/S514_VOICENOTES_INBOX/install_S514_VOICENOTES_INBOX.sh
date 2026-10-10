#!/bin/bash
# =============================================================================
# install_S514_VOICENOTES_INBOX.sh -- session 304, 10-Oct-2026 -- the owner's pick (D689, item 2):
# A TO-DO LIST HE MAKES IN VOICENOTES REACHES THE TASK BOX OF HIS STAFF-LISTS PANEL BY ITSELF (until now: paste).
#   NEW   /root/finance/voicenotes_inbox.py   the one public door POST /finance/api/voicenotes-push?key=..., opened only by
#         the key in /root/finance/voicenotes.key (made here once, mode 600, never printed); the owner's inbox
#         GET/POST /finance/aaj/api/vn. A list waits there; nothing becomes a task until he puts it in the box and presses Give.
#   EDIT  /root/finance/finance_app.py   ec5b3ab1 (S513) -> 0d713b14: the door among the public paths (the module checks
#         the key), the inbox among the identity-only paths (the module checks the owner), the module mounted guarded
#         (S209) and counted among the parts that must load (30).
#   EDIT  /root/finance/aaj_panel.html   898c42e1 (S493) -> 36bd57bc: the Voicenotes lines above the task box; the
#         one-time set-up (the address to paste, with a Copy button) below it.
#   DATA  two tables, vn_inbox and vn_seen, made on the first post or the first look (CREATE TABLE IF NOT EXISTS).
# Walked first, on this box: the code copied to /tmp, an EMPTY database, made-up logins and key; the door, the shapes a
# to-do list may come in, the owner's inbox and both marks, old file and new. Restarts clinic-finance only (about 8 s);
# red after placing -> all three put back. DRY=1 places nothing. Needs S513 installed first (its pin is this kit's FROM).
# =============================================================================
set -u
KIT="S514_VOICENOTES_INBOX"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
APP_FROM=ec5b3ab170ff37c63ac98f6f1f11ad09; APP_TO=0d713b14570384e0de07ac93a3b113db
PAN_FROM=898c42e14b142e06f2800d83aaaf01ca; PAN_TO=36bd57bcda586f18183aec54c537e2e6
VNI_TO="$(awk '$2=="voicenotes_inbox.py"{print $1}' "$KDIR/SUMS.md5" 2>/dev/null)"
KEYF="$FIN/voicenotes.key"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="/tmp/s514_scratch_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$SCR" "$FIN/.finance_app.py.s514" "$FIN/.aaj_panel.html.s514" "$FIN/.voicenotes_inbox.py.s514"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }

md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$SPY" -c "import flask, werkzeug" 2>/dev/null || { say "!! [1/7] $SPY lacks flask - nothing installed"; exit 1; }
if ! mkdir "$LOCK" 2>/dev/null; then
  say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
trap 'rm -rf "$LOCK"' EXIT
say "[1/7] kit gates green (SUMS, KIT_ID, flask); the build lock is taken"

HA="$(m5 "$FIN/finance_app.py")"; HP="$(m5 "$FIN/aaj_panel.html")"; HV="$(m5 "$FIN/voicenotes_inbox.py")"
if [ "$HA" = "$APP_TO" ] && [ "$HP" = "$PAN_TO" ] && [ "$HV" = "$VNI_TO" ]; then
  say "-- ALREADY INSTALLED: the three files are at the kit's pins; clinic-finance $(systemctl is-active clinic-finance 2>/dev/null)"; exit 0; fi
[ "$HA" = "$APP_FROM" ] || { say "!! [2/7] $FIN/finance_app.py is $HA, not $APP_FROM (S513's pin). Install S513_RENEWALS_EXPIRY first; if it is in, tell the assistant - nothing installed."; exit 1; }
[ "$HP" = "$PAN_FROM" ] || { say "!! [2/7] $FIN/aaj_panel.html is $HP, not $PAN_FROM - another kit changed it. Nothing installed; tell the assistant."; exit 1; }
[ -e "$FIN/voicenotes_inbox.py" ] && { say "!! [2/7] $FIN/voicenotes_inbox.py is already there ($HV) - nothing installed; tell the assistant."; exit 1; }
for f in finance_schema.sql finance_migration_S182_clinic.sql; do [ -f "$FIN/$f" ] || { say "!! [2/7] $FIN/$f is not there - nothing installed"; exit 1; }; done
say "[2/7] finance_app.py at S513's pin, aaj_panel.html at S493's, voicenotes_inbox.py not yet there"

mkdir -p "$SCR" && \cp -p "$FIN/finance_app.py" "$FIN/aaj_panel.html" "$SCR/" && \cp "$KDIR/voicenotes_inbox.py" "$SCR/" || { say "!! [3/7] no scratch copy - nothing installed"; clean; exit 1; }
"$SPY" -B make_s514.py "$SCR" >/dev/null 2>"$SCR/make.err" || { say "!! [3/7] the edits did not apply: $(tail -1 "$SCR/make.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
[ "$(m5 "$SCR/finance_app.py")" = "$APP_TO" ] && [ "$(m5 "$SCR/aaj_panel.html")" = "$PAN_TO" ] && [ "$(m5 "$SCR/voicenotes_inbox.py")" = "$VNI_TO" ] || { say "!! [3/7] the scratch files are not their predicted bytes - nothing installed"; clean; exit 1; }
"$SPY" -m py_compile make_s514.py walk_s514.py "$SCR/finance_app.py" "$SCR/voicenotes_inbox.py" 2>/dev/null || { say "!! [3/7] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the edits apply to scratch copies and give the predicted bytes; compiles"

WOUT="$( cd /tmp && timeout 900 "$SPY" -B "$KDIR/walk_s514.py" --kit "$KDIR" --finance "$FIN" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^WALK_S514' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S514 GREEN" || { say "!! [4/7] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
[ "$(m5 "$FIN/finance_app.py")" = "$APP_FROM" ] && [ "$(m5 "$FIN/aaj_panel.html")" = "$PAN_FROM" ] || { say "!! [4/7] a file changed during the walk - nothing installed"; clean; exit 1; }
say "[4/7] walk green: no key or a wrong key refused; a to-do list in Markdown, HTML or a list is kept line by line, once; a summary or a note is not; the owner's inbox and its marks; a staff login refused; no task made by itself; every other health row unchanged"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted, no key made"; clean; exit 0; fi

BA="$FIN/finance_app.py.bak_S514_$(echo "$APP_FROM" | cut -c1-8)"; BP="$FIN/aaj_panel.html.bak_S514_$(echo "$PAN_FROM" | cut -c1-8)"
\cp -p "$FIN/finance_app.py" "$BA" && \cp -p "$FIN/aaj_panel.html" "$BP" && [ "$(m5 "$BA")" = "$APP_FROM" ] && [ "$(m5 "$BP")" = "$PAN_FROM" ] || { say "!! [5/7] the backup failed - nothing placed"; clean; exit 1; }
MADEKEY=0
if [ ! -s "$KEYF" ]; then
  ( umask 077; "$SPY" -c "import secrets; print(secrets.token_hex(24))" > "$KEYF" ) && chmod 600 "$KEYF" && MADEKEY=1 || { say "!! [5/7] the key file could not be made - nothing placed"; clean; exit 1; }
fi
say "[5/7] backups: $BA · $BP · the key file $([ "$MADEKEY" = 1 ] && echo 'made' || echo 'already there') (mode $(stat -c %a "$KEYF"), not printed)"
restore() {
  say "!! RED after placing ($1) - restoring"
  \cp -p "$BA" "$FIN/finance_app.py"; \cp -p "$BP" "$FIN/aaj_panel.html"; rm -f "$FIN/voicenotes_inbox.py"
  systemctl restart clinic-finance 2>/dev/null || true; sleep 7
  say "   finance_app.py $(m5 "$FIN/finance_app.py") · aaj_panel.html $(m5 "$FIN/aaj_panel.html") · voicenotes_inbox.py $( [ -e "$FIN/voicenotes_inbox.py" ] && echo present || echo removed) · finance healthz $(health "$FINURL/finance/healthz")"
  clean; exit 1
}
# each walked scratch file goes in by a rename, so no file is ever half-written; owner and mode are the old file's
\cp -p "$FIN/finance_app.py" "$FIN/.finance_app.py.s514" && cat "$SCR/finance_app.py" > "$FIN/.finance_app.py.s514" \
  && \cp -p "$FIN/aaj_panel.html" "$FIN/.aaj_panel.html.s514" && cat "$SCR/aaj_panel.html" > "$FIN/.aaj_panel.html.s514" \
  && \cp -p "$FIN/aaj_panel.html" "$FIN/.voicenotes_inbox.py.s514" && cat "$SCR/voicenotes_inbox.py" > "$FIN/.voicenotes_inbox.py.s514" \
  || { say "!! [6/7] could not stage the new files - nothing placed"; clean; exit 1; }
mv -f "$FIN/.voicenotes_inbox.py.s514" "$FIN/voicenotes_inbox.py" || restore "placing voicenotes_inbox.py"
mv -f "$FIN/.aaj_panel.html.s514" "$FIN/aaj_panel.html" || restore "placing aaj_panel.html"
mv -f "$FIN/.finance_app.py.s514" "$FIN/finance_app.py" || restore "placing finance_app.py"
[ "$(m5 "$FIN/finance_app.py")" = "$APP_TO" ] && [ "$(m5 "$FIN/aaj_panel.html")" = "$PAN_TO" ] && [ "$(m5 "$FIN/voicenotes_inbox.py")" = "$VNI_TO" ] || restore "md5 read-back"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
sleep 8
systemctl is-active --quiet clinic-finance || restore "clinic-finance not active"
c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health "$FINURL/finance/health"); case "$c2" in 302|401) ;; *) restore "/finance/health answered $c2 without a login";; esac
c3=$(health "$FINURL/finance/api/health"); case "$c3" in 401|403) ;; *) restore "/finance/api/health answered $c3 without a login";; esac
c4=$(health "$FINURL/finance/aaj/api/vn"); case "$c4" in 302|401|403) ;; *) restore "/finance/aaj/api/vn answered $c4 without a login";; esac
D1="$(curl -s -m 10 -X POST -H 'Content-Type: application/json' --data-binary '{}' "$FINURL/finance/api/voicenotes-push")"
echo "$D1" | grep -q '"bad_key"' || restore "the Voicenotes door does not answer with its own key check: $(echo "$D1" | cut -c1-160)"
D2="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
echo "$D2" | grep -q '"NOT_YOU"' || restore "the heartbeat door no longer refuses an unsigned heartbeat: $(echo "$D2" | cut -c1-160)"
journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a module NOT mounted"
JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
[ "${JR:-0}" = 0 ] || restore "clinic-finance journal: $JR error line(s)"
say "[6/7] placed, md5 read back = the kit's pins · clinic-finance active · healthz 200 · /finance/health $c2, its data $c3, the inbox $c4 without a login · the Voicenotes door answers with its own key check · the heartbeat door as before · every part mounted · journal clean"
say "[7/7] from now: https://followup.dr-manoj.in/finance/aaj -> Tasks -> 'Voicenotes sending here by itself' holds the address to paste into Voicenotes once"
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/finance_app.py" "$FIN/aaj_panel.html" "$FIN/voicenotes_inbox.py"
