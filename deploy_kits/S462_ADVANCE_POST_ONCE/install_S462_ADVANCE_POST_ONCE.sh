#!/bin/bash
# =============================================================================
# install_S462_ADVANCE_POST_ONCE.sh -- session 292, 03-Oct-2026 -- at the owner's word: "Do these".
# A PHARMACY SALARY ADVANCE REACHES THE STAFF LEDGER ONCE (F-706, proven on a scratch copy before a line was written):
#   (a) a day with two advances whose second failed left the first in the ledger, unstamped, and every retry posted it again;
#   (b) an APPROVED day that was corrected lost its stamps, so re-approval posted the advance a second time.
#   EDIT  /root/finance/finance_app.py   26a532a6 (S461) -> 27a162e6, by apply_s462.py (5 exact anchors):
#     api_approve   every row is checked, and the ledger's month ceiling asked for the day's total, BEFORE any row is
#                   posted; a row the ledger already took keeps its stamp if a later one still fails.
#     api_save_day  a posted advance keeps its stamp through a correction; changing or removing one the ledger still
#                   holds is refused in words that say what to do (reverse it in the Staff Ledger first).
#   NOT TOUCHED: /root/staff_ledger.py and the ledger's data; every other file; the database's rows. No setting.
# Walked first, on this box: the app's code copied to /tmp, an EMPTY database and an EMPTY ledger in /tmp, the box's own
# staff_ledger.py doing the posting; each fault shown on the old file and gone on the new one. The live ledger's md5 is
# read before and after the walk. Restarts clinic-finance only (about 8 seconds); red after placing -> the file is put
# back. DRY=1 places nothing. The last step READS the live ledger and says whether any advance is already there twice.
# =============================================================================
set -u
KIT="S462_ADVANCE_POST_ONCE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
APP_FROM=26a532a6ec212ac66e6cfb41b37844eb; APP_TO=27a162e6740140d4ce7d2e293eae9809; APP_LATER=49f52391f44643c10b052609cffc5bbe
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="/tmp/s462_scratch_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$SCR" "$FIN/.finance_app.py.s462"; }
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

HAVE="$(m5 "$FIN/finance_app.py")"
if [ "$HAVE" = "$APP_LATER" ]; then
  say "-- ALREADY INSTALLED: finance_app.py is a later kit's file (S463), which carries this change; clinic-finance $(systemctl is-active clinic-finance 2>/dev/null)"; exit 0; fi
if [ "$HAVE" = "$APP_TO" ]; then
  say "-- ALREADY INSTALLED: finance_app.py is at the kit's pin; clinic-finance $(systemctl is-active clinic-finance 2>/dev/null)"; exit 0; fi
[ "$HAVE" = "$APP_FROM" ] || { say "!! [2/7] $FIN/finance_app.py is $HAVE, not $APP_FROM - another kit changed it after this one was built. Nothing installed; tell the assistant, the kit is rebuilt on the new file."; exit 1; }
for f in finance_schema.sql finance_migration_S182_clinic.sql; do [ -f "$FIN/$f" ] || { say "!! [2/7] $FIN/$f is not there (the walk makes its empty database from it) - nothing installed"; exit 1; }; done
[ -f "$ROOT/staff_ledger.py" ] || { say "!! [2/7] $ROOT/staff_ledger.py is not there (the walk posts with it) - nothing installed"; exit 1; }
say "[2/7] finance_app.py at its S461 pin; the Staff Ledger's own code is here"

mkdir -p "$SCR" && \cp -p "$FIN/finance_app.py" "$SCR/finance_app.py" || { say "!! [3/7] no scratch copy - nothing installed"; clean; exit 1; }
"$SPY" -B apply_s462.py "$SCR/finance_app.py" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/7] the edits did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
[ "$(m5 "$SCR/finance_app.py")" = "$APP_TO" ] || { say "!! [3/7] the edited scratch copy is not its predicted bytes - nothing installed"; clean; exit 1; }
"$SPY" -m py_compile apply_s462.py walk_s462.py report_s462.py "$SCR/finance_app.py" 2>/dev/null || { say "!! [3/7] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the edits apply to a scratch copy and give the predicted bytes; compiles"

WOUT="$( cd /tmp && timeout 900 "$SPY" -B "$KDIR/walk_s462.py" --apply "$KDIR/apply_s462.py" --finance "$FIN" --ledger-py "$ROOT" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^  NOTE|^WALK_S462' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S462 GREEN" || { say "!! [4/7] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
[ "$(m5 "$FIN/finance_app.py")" = "$APP_FROM" ] || { say "!! [4/7] finance_app.py changed during the walk - nothing installed"; clean; exit 1; }
say "[4/7] walk green: each double posting shown on the old file and gone on the new one; the live Staff Ledger untouched by the walk"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

BA="$FIN/finance_app.py.bak_S462_$(echo "$APP_FROM" | cut -c1-8)"
\cp -p "$FIN/finance_app.py" "$BA" && [ "$(m5 "$BA")" = "$APP_FROM" ] || { say "!! [5/7] the backup failed - nothing placed"; clean; exit 1; }
say "[5/7] backup: $BA"
restore() {
  say "!! RED after placing ($1) - restoring"
  \cp -p "$BA" "$FIN/finance_app.py"
  systemctl restart clinic-finance 2>/dev/null || true; sleep 7
  say "   finance_app.py $(m5 "$FIN/finance_app.py") · finance healthz $(health "$FINURL/finance/healthz")"
  clean; exit 1
}
# the walked scratch file goes in by a rename, so the app's file is never half-written; owner and mode are the old file's
\cp -p "$FIN/finance_app.py" "$FIN/.finance_app.py.s462" && cat "$SCR/finance_app.py" > "$FIN/.finance_app.py.s462" && [ "$(m5 "$FIN/.finance_app.py.s462")" = "$APP_TO" ] || { say "!! [6/7] could not stage the new file - nothing placed"; clean; exit 1; }
mv -f "$FIN/.finance_app.py.s462" "$FIN/finance_app.py" || restore "placing finance_app.py"
[ "$(m5 "$FIN/finance_app.py")" = "$APP_TO" ] || restore "md5 read-back of finance_app.py"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
sleep 8
systemctl is-active --quiet clinic-finance || restore "clinic-finance not active"
c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health "$FINURL/finance/health"); case "$c2" in 302|401) ;; *) restore "/finance/health answered $c2 without a login";; esac
c3=$(health "$FINURL/finance/api/approve/2026-01-01" -X POST); case "$c3" in 401|403|302) ;; *) restore "the approve door answered $c3 without a login";; esac
c4=$(health "$FINURL/finance/pcs"); case "$c4" in 302|401) ;; *) restore "/finance/pcs answered $c4 without a login";; esac
D1="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
echo "$D1" | grep -q '"NOT_YOU"' || restore "the heartbeat door no longer refuses an unsigned heartbeat: $(echo "$D1" | cut -c1-160)"
D4="$(curl -s -m 10 "$FINURL/finance/api/pc-kit/fetch?part=kit")"
echo "$D4" | grep -q 'Clinic PCs page' || restore "the kit door (S450) no longer answers"
journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a module NOT mounted"
JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
[ "${JR:-0}" = 0 ] || restore "clinic-finance journal: $JR error line(s)"
say "[6/7] placed, md5 read back = the kit's pin · clinic-finance active · healthz 200 · /finance/health $c2, the approve door $c3 and /finance/pcs $c4 (the login gate) · the heartbeat and kit doors answer as before · every part mounted · journal clean"

# read-only: is an advance ALREADY in the live Staff Ledger twice? (this kit stops new ones; it corrects nothing)
say "[7/7] the live Staff Ledger, read only:"
"$SPY" -B report_s462.py "${LEDGER_JSONL:-$ROOT/staff_ledger/ledger.jsonl}" "${FINANCE_DB:-$FIN/finance.db}" 2>&1 | cut -c1-200 | sed 's/^/      /'
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/finance_app.py"
