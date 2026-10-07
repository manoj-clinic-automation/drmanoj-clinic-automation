#!/bin/bash
# =============================================================================
# install_S492_SETUP_NOTES.sh -- session 298, 07-Oct-2026 -- 'Other set-ups' on the Clinic PCs & phones page
#  THE OWNER, 06-Oct on his board and 07-Oct in the chat: set-up notes and links in the portal for the biometric machine,
#  Hostinger, CyberPanel, SSH, the websites and Bitwarden -- "build biometric and also list all , the proposed ones in the
#  to be built section there".
#  NEW:   /root/finance/setup_notes.py   the notes as data and their HTML. No secret, no number, no door, nothing written.
#  EDIT, by apply_s492.py (three exact anchors on the real bytes, each found exactly once):
#         /root/finance/pc_kits.py       708fd203 (S473) -> 9c2b3615   a guarded import and one guarded place on the page
#                                         /finance/pcs, after the phones. The same owner-only gate. Without the notes
#                                         file, or if a note raises, the page is byte for byte what it is today.
#  NOT TOUCHED: finance_app.py, portal.py, every door, the database, the kits, the keys, the attendance programs.
# Walked first, on this box, hermetically (F-709): the edited file in /tmp, three throwaway apps, a scratch punch file.
# Restarts clinic-finance only (about 8 seconds); red after placing -> both files are put back as they were.
# DRY=1 places nothing. NEEDS the build lock free (F-694).
# =============================================================================
set -u
KIT="S492_SETUP_NOTES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FROM=708fd2030cdf7b13aa7232ba00ef4b7a; TO=9c2b3615bced5cd425b345d60f3daa15
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="/tmp/s492_scratch_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$SCR" "$FIN/.pc_kits.py.s492" "$FIN/.setup_notes.py.s492"; }
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

NOTES="$(m5 "$KDIR/setup_notes.py")"
HAVE="$(m5 "$FIN/pc_kits.py")"
HADNOTES=0; [ -f "$FIN/setup_notes.py" ] && HADNOTES=1
if [ "$HAVE" = "$TO" ] && [ "$(m5 "$FIN/setup_notes.py")" = "$NOTES" ]; then say "-- ALREADY INSTALLED: pc_kits.py and setup_notes.py are at the kit's pins; clinic-finance $(systemctl is-active clinic-finance 2>/dev/null)"; exit 0; fi
[ "$HAVE" = "$FROM" ] || { say "!! [2/7] $FIN/pc_kits.py is $HAVE, not $FROM (S473) - another kit changed it after this one was built. Nothing installed; tell the assistant, the kit is rebuilt on the new file."; exit 1; }
if [ "$HADNOTES" = 1 ] && [ "$(m5 "$FIN/setup_notes.py")" != "$NOTES" ]; then say "!! [2/7] $FIN/setup_notes.py is already there and is not this kit's file - nothing installed; tell the assistant."; exit 1; fi
say "[2/7] pc_kits.py at its S473 pin; no other setup_notes.py in the way"

mkdir -p "$SCR/fin" && \cp -p "$FIN/pc_kits.py" "$SCR/fin/pc_kits.py" && \cp -p "$FIN/pc_kits.py" "$SCR/pc_kits.py" || { say "!! [3/7] no scratch copy - nothing installed"; clean; exit 1; }
"$SPY" -B apply_s492.py "$SCR/pc_kits.py" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/7] the edits did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
[ "$(m5 "$SCR/pc_kits.py")" = "$TO" ] || { say "!! [3/7] the edited scratch copy is not its predicted bytes - nothing installed"; clean; exit 1; }
"$SPY" -m py_compile apply_s492.py walk_s492.py setup_notes.py "$SCR/pc_kits.py" 2>/dev/null || { say "!! [3/7] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the three edits apply to a scratch copy and give the predicted bytes; everything compiles"

WOUT="$( cd /tmp && timeout 600 "$SPY" -B "$KDIR/walk_s492.py" --apply "$KDIR/apply_s492.py" --notes "$KDIR/setup_notes.py" --finance "$SCR/fin" --to "$TO" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^WALK_S492' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S492 GREEN" || { say "!! [4/7] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
[ "$(m5 "$FIN/pc_kits.py")" = "$FROM" ] || { say "!! [4/7] pc_kits.py changed during the walk - nothing installed"; clean; exit 1; }
say "[4/7] walk green on this box: the old page whole and in order, the new section after the phones, the punch file read three ways, the notes closed to everyone but the owner, nothing secret-shaped, and both guards (no notes file / a note that raises) give today's page byte for byte"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

BA="$FIN/pc_kits.py.bak_S492_$(echo "$FROM" | cut -c1-8)"
\cp -p "$FIN/pc_kits.py" "$BA" && [ "$(m5 "$BA")" = "$FROM" ] || { say "!! [5/7] the backup failed - nothing placed"; clean; exit 1; }
say "[5/7] backup: $BA"
restore() {
  say "!! RED after placing ($1) - restoring"
  \cp -p "$BA" "$FIN/pc_kits.py"
  [ "$HADNOTES" = 0 ] && rm -f "$FIN/setup_notes.py"
  systemctl restart clinic-finance 2>/dev/null || true; sleep 7
  say "   pc_kits.py $(m5 "$FIN/pc_kits.py") · setup_notes.py $([ -f "$FIN/setup_notes.py" ] && echo there || echo gone) · finance healthz $(health "$FINURL/finance/healthz")"
  clean; exit 1
}
\cp -p "$FIN/pc_kits.py" "$FIN/.setup_notes.py.s492" && cat "$KDIR/setup_notes.py" > "$FIN/.setup_notes.py.s492" && [ "$(m5 "$FIN/.setup_notes.py.s492")" = "$NOTES" ] || { say "!! [6/7] could not stage setup_notes.py - nothing placed"; clean; exit 1; }
\cp -p "$FIN/pc_kits.py" "$FIN/.pc_kits.py.s492" && cat "$SCR/pc_kits.py" > "$FIN/.pc_kits.py.s492" && [ "$(m5 "$FIN/.pc_kits.py.s492")" = "$TO" ] || { say "!! [6/7] could not stage the new pc_kits.py - nothing placed"; clean; exit 1; }
mv -f "$FIN/.setup_notes.py.s492" "$FIN/setup_notes.py" || restore "placing setup_notes.py"
mv -f "$FIN/.pc_kits.py.s492" "$FIN/pc_kits.py" || restore "placing pc_kits.py"
[ "$(m5 "$FIN/pc_kits.py")" = "$TO" ] && [ "$(m5 "$FIN/setup_notes.py")" = "$NOTES" ] || restore "md5 read-back"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
sleep 8
systemctl is-active --quiet clinic-finance || restore "clinic-finance not active"
c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health "$FINURL/finance/pcs"); case "$c2" in 302|401|403) ;; *) restore "/finance/pcs answered $c2 without a login";; esac
D2="$(curl -s -m 10 "$FINURL/finance/pcs")"
echo "$D2" | grep -q 'Biometric\|Other set-ups\|attlistener' && restore "the notes are readable without a login"
D4="$(curl -s -m 10 "$FINURL/finance/api/pc-kit/fetch?part=kit")"
echo "$D4" | grep -q 'Clinic PCs page' || restore "the kit door (S450) no longer answers"
D1="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
echo "$D1" | grep -q '"NOT_YOU"' || restore "the heartbeat door no longer refuses an unsigned heartbeat: $(echo "$D1" | cut -c1-160)"
journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a module NOT mounted"
JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
[ "${JR:-0}" = 0 ] || restore "clinic-finance journal: $JR error line(s)"
( cd "$FIN" && "$SPY" -B -c "import setup_notes as s; h=s.section(); assert 'Biometric attendance machine' in h and h.count('To be built</span>')==5; print('   on this box: ' + s.last_punch()[2])" ) || restore "setup_notes.py does not load beside pc_kits.py"
say "[6/7] placed, md5 read back = the kit's pins · clinic-finance active · healthz 200 · /finance/pcs $c2 without a login and not a word of the notes · the kit and heartbeat doors answer as before · every part mounted · journal clean"
say "[7/7] 'Other set-ups' is on https://followup.dr-manoj.in/finance/pcs for the owner's login"
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/pc_kits.py" "$FIN/setup_notes.py"
