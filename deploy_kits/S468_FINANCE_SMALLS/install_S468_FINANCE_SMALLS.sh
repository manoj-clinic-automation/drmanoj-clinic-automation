#!/bin/bash
# =============================================================================
# install_S468_FINANCE_SMALLS.sh -- session 292, 03-Oct-2026 -- at the owner's word: "then proceed with this work."
# THREE SMALL THINGS LEFT OVER FROM S461/S462, none of which changes what anyone sees or does:
#  (a) EDIT /root/finance/finance_app.py  72d25382 (S467) -> 8f69f192, by apply_s468.py: three insertions, ALL inside
#      selftest(). The self-test stored its made-up bank statements in the LIVE upi_statements / yesbank_statements
#      folders (S461 sandboxed the scans only). Both are throwaway folders for the run now.
#  (b) READ-ONLY: names the pharmacy salary advances S462 counted (one stamped, one on an approved day with no stamp):
#      the day, the person, the amount, and the Staff Ledger row that answers it -- or that none does.
#  (c) the tiny test scans older self-test runs left in /root/finance/finance_scans (under 65 bytes, *.pdf; the live
#      scan folder is another one) are MOVED into /root/finance/finance_scans.test_scans_set_aside_S468 -- moved, not
#      deleted, and never one that a row of the database names. The self-test's old statements are counted only.
#   NOT TOUCHED: every route, page and setting; the database; the ledger; the live scan and statement folders.
#   NEEDS S467 installed first (it refuses on the pin otherwise). --selftest itself is NOT run by this installer.
# Walked first, on this box: the app's code copied to /tmp, an EMPTY database, the REAL selftest() started on the old
# file and the new, and where its two made-up statements land; then the housekeeping script on made-up data.
# Restarts clinic-finance only (about 8 seconds); red after placing -> the file is put back. DRY=1 places nothing.
# =============================================================================
set -u
KIT="S468_FINANCE_SMALLS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
APP_FROM=72d2538222a8fbd6a12d5ac2434c5a4e; APP_TO=8f69f192020205b302ac413a039f7c31; APP_S463=49f52391f44643c10b052609cffc5bbe
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="/tmp/s468_scratch_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$SCR" "$FIN/.finance_app.py.s468"; }
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
if [ "$HAVE" = "$APP_TO" ]; then
  say "-- ALREADY INSTALLED: finance_app.py is at the kit's pin; clinic-finance $(systemctl is-active clinic-finance 2>/dev/null)"; exit 0; fi
if [ "$HAVE" = "$APP_S463" ]; then
  say "!! [2/7] $FIN/finance_app.py is still the S463 file - S467_WARRANTY_ON_HEALTH goes in first; nothing installed"; exit 1; fi
[ "$HAVE" = "$APP_FROM" ] || { say "!! [2/7] $FIN/finance_app.py is $HAVE, not $APP_FROM - another kit changed it after this one was built. Nothing installed; tell the assistant, the kit is rebuilt on the new file."; exit 1; }
for f in finance_schema.sql finance_migration_S182_clinic.sql; do [ -f "$FIN/$f" ] || { say "!! [2/7] $FIN/$f is not there (the walk makes its empty database from it) - nothing installed"; exit 1; }; done
say "[2/7] finance_app.py at its S467 pin"

mkdir -p "$SCR" && \cp -p "$FIN/finance_app.py" "$SCR/finance_app.py" || { say "!! [3/7] no scratch copy - nothing installed"; clean; exit 1; }
"$SPY" -B apply_s468.py "$SCR/finance_app.py" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/7] the edits did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
[ "$(m5 "$SCR/finance_app.py")" = "$APP_TO" ] || { say "!! [3/7] the edited scratch copy is not its predicted bytes - nothing installed"; clean; exit 1; }
"$SPY" -m py_compile apply_s468.py walk_s468.py report_s468.py "$SCR/finance_app.py" 2>/dev/null || { say "!! [3/7] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the three insertions apply to a scratch copy and give the predicted bytes; compiles"

WOUT="$( cd /tmp && timeout 900 "$SPY" -B "$KDIR/walk_s468.py" --apply "$KDIR/apply_s468.py" --report "$KDIR/report_s468.py" --finance "$FIN" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^  NOTE|^WALK_S468' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S468 GREEN" || { say "!! [4/7] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
[ "$(m5 "$FIN/finance_app.py")" = "$APP_FROM" ] || { say "!! [4/7] finance_app.py changed during the walk - nothing installed"; clean; exit 1; }
say "[4/7] walk green: SHOWN on the old file, the self-test's two made-up statements land in the app's own statement folders; on the new file they land in throwaway folders that are gone when the run ends; the housekeeping moves only tiny unnamed test scans and refuses the live folder"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

BA="$FIN/finance_app.py.bak_S468_$(echo "$APP_FROM" | cut -c1-8)"
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
\cp -p "$FIN/finance_app.py" "$FIN/.finance_app.py.s468" && cat "$SCR/finance_app.py" > "$FIN/.finance_app.py.s468" && [ "$(m5 "$FIN/.finance_app.py.s468")" = "$APP_TO" ] || { say "!! [6/7] could not stage the new file - nothing placed"; clean; exit 1; }
mv -f "$FIN/.finance_app.py.s468" "$FIN/finance_app.py" || restore "placing finance_app.py"
[ "$(m5 "$FIN/finance_app.py")" = "$APP_TO" ] || restore "md5 read-back of finance_app.py"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
sleep 8
systemctl is-active --quiet clinic-finance || restore "clinic-finance not active"
c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health "$FINURL/finance/health"); case "$c2" in 302|401) ;; *) restore "/finance/health answered $c2 without a login";; esac
c3=$(health "$FINURL/finance/api/health"); case "$c3" in 401|403) ;; *) restore "/finance/api/health answered $c3 without a login";; esac
c4=$(health "$FINURL/finance/pcs"); case "$c4" in 302|401) ;; *) restore "/finance/pcs answered $c4 without a login";; esac
D1="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
echo "$D1" | grep -q '"NOT_YOU"' || restore "the heartbeat door no longer refuses an unsigned heartbeat: $(echo "$D1" | cut -c1-160)"
D4="$(curl -s -m 10 "$FINURL/finance/api/pc-kit/fetch?part=kit")"
echo "$D4" | grep -q 'Clinic PCs page' || restore "the kit door (S450) no longer answers"
journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a module NOT mounted"
JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
[ "${JR:-0}" = 0 ] || restore "clinic-finance journal: $JR error line(s)"
say "[6/7] placed, md5 read back = the kit's pin · clinic-finance active · healthz 200 · /finance/health $c2, its data $c3 and /finance/pcs $c4 (the login gate) · the heartbeat and kit doors answer as before · every part mounted · journal clean"
say "[7/7] housekeeping (the report reads only; the scans are moved, never deleted):"
LIVESCAN="$(systemctl show clinic-finance -p Environment --value 2>/dev/null | tr ' ' '\n' | sed -n 's/^FINANCE_SCAN_DIR=//p' | head -1)"
FDB="${FINANCE_DB:-$FIN/finance.db}"
"$SPY" -B report_s468.py advances "${LEDGER_JSONL:-$ROOT/staff_ledger/ledger.jsonl}" "$FDB" 2>&1 | cut -c1-420 | sed 's/^/      /'
"$SPY" -B report_s468.py statements "$FIN/upi_statements" "$FIN/yesbank_statements" 2>&1 | cut -c1-300 | sed 's/^/      /'
if [ -n "$LIVESCAN" ] && [ -d "$LIVESCAN" ]; then
  "$SPY" -B report_s468.py scans "$FIN/finance_scans" "$FDB" "$LIVESCAN" --move 2>&1 | cut -c1-400 | sed 's/^/      /'
else
  say "      test scans: the service's own scan folder could not be read from its settings, so NOTHING is moved:"
  "$SPY" -B report_s468.py scans "$FIN/finance_scans" "$FDB" "$FIN/__no_live_folder_known__" 2>&1 | cut -c1-300 | sed 's/^/      /'
fi
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/finance_app.py"
