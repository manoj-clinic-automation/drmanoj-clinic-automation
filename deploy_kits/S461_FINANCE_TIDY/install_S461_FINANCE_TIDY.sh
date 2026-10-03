#!/bin/bash
# =============================================================================
# install_S461_FINANCE_TIDY.sh -- session 292, 03-Oct-2026 -- at the owner's word: "2. Finance app tidy-up".
# FOUR DISPLAY/HYGIENE EDITS to /root/finance/finance_app.py, from the S291 whole read. No figure, no row, no gate,
# no role and no route changes.
#   EDIT  /root/finance/finance_app.py   40aef4df (S457) -> 26a532a6, by apply_s461.py (14 exact anchors, one of them twice, + the 14 mounts):
#     1  /finance/health escapes every row's label, words and hint (a hint naming "<the medical address>" was being
#        swallowed by the browser as a tag; the Reception PC row carries words that PC supplies).
#     2  --selftest sends its fake scans to a throwaway folder and removes what it made in temp at exit, even when it
#        aborts (before: junk in the live scan folder, and an abort left a whole copy of the database in temp).
#     3  the 14 print-only mounts record their failure, and the 'mounts' health row shows the stored reason.
#     4  the three unguarded ?days= parses answer the default instead of a 500.
#   NOT TOUCHED: every other file; the database; the portal. No setting is written.
#   NOT IN THIS KIT (each its own walked kit): role checks on open routes, the Staff-Ledger post inside api_approve's
#     loop, the negative-cash guard, the apply-abort rollbacks.
# Walked first, on this box: the app's own code copied to /tmp, an EMPTY database made from its own schema, each fault
# shown on the old file and shown gone on the new one. The live database and the live scan folder are not opened.
# Restarts clinic-finance only (about 8 seconds); anything red after placing -> the file is put back. DRY=1 places nothing.
# =============================================================================
set -u
KIT="S461_FINANCE_TIDY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
APP_FROM=40aef4dfe976a596c81be46da1fbb429; APP_TO=26a532a6ec212ac66e6cfb41b37844eb
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="/tmp/s461_scratch_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$SCR" "$FIN/.finance_app.py.s461"; }
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
[ "$HAVE" = "$APP_FROM" ] || { say "!! [2/7] $FIN/finance_app.py is $HAVE, not $APP_FROM - another kit changed it after this one was built. Nothing installed; tell the assistant, the kit is rebuilt on the new file."; exit 1; }
for f in finance_schema.sql finance_migration_S182_clinic.sql; do [ -f "$FIN/$f" ] || { say "!! [2/7] $FIN/$f is not there (the walk makes its empty database from it) - nothing installed"; exit 1; }; done
say "[2/7] finance_app.py at its S457 pin"

mkdir -p "$SCR" && \cp -p "$FIN/finance_app.py" "$SCR/finance_app.py" || { say "!! [3/7] no scratch copy - nothing installed"; clean; exit 1; }
"$SPY" -B apply_s461.py "$SCR/finance_app.py" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/7] the edits did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
[ "$(m5 "$SCR/finance_app.py")" = "$APP_TO" ] || { say "!! [3/7] the edited scratch copy is not its predicted bytes - nothing installed"; clean; exit 1; }
"$SPY" -m py_compile apply_s461.py walk_s461.py "$SCR/finance_app.py" 2>/dev/null || { say "!! [3/7] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the edits apply to a scratch copy and give the predicted bytes; compiles"

WOUT="$( cd /tmp && timeout 900 "$SPY" -B "$KDIR/walk_s461.py" --apply "$KDIR/apply_s461.py" --finance "$FIN" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^  NOTE|^WALK_S461' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S461 GREEN" || { say "!! [4/7] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
[ "$(m5 "$FIN/finance_app.py")" = "$APP_FROM" ] || { say "!! [4/7] finance_app.py changed during the walk - nothing installed"; clean; exit 1; }
say "[4/7] walk green: each fault shown on the old file and gone on the new one; every unchanged answer is byte for byte the same"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

BA="$FIN/finance_app.py.bak_S461_$(echo "$APP_FROM" | cut -c1-8)"
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
\cp -p "$FIN/finance_app.py" "$FIN/.finance_app.py.s461" && cat "$SCR/finance_app.py" > "$FIN/.finance_app.py.s461" && [ "$(m5 "$FIN/.finance_app.py.s461")" = "$APP_TO" ] || { say "!! [6/7] could not stage the new file - nothing placed"; clean; exit 1; }
mv -f "$FIN/.finance_app.py.s461" "$FIN/finance_app.py" || restore "placing finance_app.py"
[ "$(m5 "$FIN/finance_app.py")" = "$APP_TO" ] || restore "md5 read-back of finance_app.py"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
sleep 8
systemctl is-active --quiet clinic-finance || restore "clinic-finance not active"
c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health "$FINURL/finance/health"); case "$c2" in 302|401) ;; *) restore "/finance/health answered $c2 without a login";; esac
c3=$(health "$FINURL/finance/api/days?days=abc"); case "$c3" in 401|403|302) ;; *) restore "/finance/api/days answered $c3 without a login";; esac
c4=$(health "$FINURL/finance/pcs"); case "$c4" in 302|401) ;; *) restore "/finance/pcs answered $c4 without a login";; esac
D1="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
echo "$D1" | grep -q '"NOT_YOU"' || restore "the heartbeat door no longer refuses an unsigned heartbeat: $(echo "$D1" | cut -c1-160)"
D4="$(curl -s -m 10 "$FINURL/finance/api/pc-kit/fetch?part=kit")"
echo "$D4" | grep -q 'Clinic PCs page' || restore "the kit door (S450) no longer answers"
journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a module NOT mounted"
JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
[ "${JR:-0}" = 0 ] || restore "clinic-finance journal: $JR error line(s)"
say "[6/7] placed, md5 read back = the kit's pin · clinic-finance active · healthz 200 · /finance/health $c2, /finance/api/days $c3 and /finance/pcs $c4 (the login gate) · the heartbeat and kit doors answer as before · every part mounted · journal clean"

# read-only, for the assistant: what earlier gate runs left behind (this kit stops new ones; it removes nothing)
N1="$(find "$FIN/finance_scans" -type f -size -65c -name '*.pdf' 2>/dev/null | wc -l)"
N2="$(find /tmp -maxdepth 1 -name 'finance_smoke_*.db' 2>/dev/null | wc -l)"
N3="$(find /tmp -maxdepth 1 -type d \( -name 'smoke_ledger_*' -o -name 'smoke_renewals_*' \) 2>/dev/null | wc -l)"
say "[7/7] left by earlier test runs (counted only, nothing removed): $N1 tiny test scan(s) in the scan folder · $N2 database copy(ies) and $N3 smoke folder(s) in /tmp"
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/finance_app.py"
