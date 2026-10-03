#!/bin/bash
# =============================================================================
# install_S469_CLINIC_TILE_FIELDS.sh -- session 292, 03-Oct-2026 -- at the owner's word: "then proceed with this work."
# RECEPTION IS HANDED WHAT ITS PAGE SHOWS, AND NO MORE (the last part of F-707; the clinic twin of F-127).
# The clinic tile and the clinic exceptions list answer ANY signed-in clinic identity with the unit's whole position --
# cash in hand and who holds it, the month to date, drawings, the bank-trip clock, every open shout -- while
# reception's entry page shows one deposit banner and the missing-day list. S463 left both for this kit.
#   EDIT  /root/finance/finance_app.py   8f69f192 (S468) -> 727a2e7a, by apply_s469.py (2 exact anchors):
#     /finance/clinic/api/tile        a non-checker gets ok, unit_name, deposit_due and -- only when the limit is
#                                     crossed -- the banner's three figures. The checker's answer is unchanged.
#     /finance/clinic/api/exceptions  a non-checker gets the missing-day rows only. The checker's answer is unchanged.
#   FIELDS ONLY: nobody who gets in today is refused; no role gate is added.
#   NOT TOUCHED: every other route, every page, the database, the portal. NEEDS S468 installed first.
# Walked first, on this box: the app's code copied to /tmp, an EMPTY database with a made-up clinic day and made-up
# exceptions; reception, a viewer, a checker and a pharmacy-only login ask both routes, old file and new, with the
# limit not crossed and crossed; the fields reception's page reads are read off the page's own code.
# Restarts clinic-finance only (about 8 seconds); red after placing -> the file is put back. DRY=1 places nothing.
# =============================================================================
set -u
KIT="S469_CLINIC_TILE_FIELDS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
APP_FROM=8f69f192020205b302ac413a039f7c31; APP_TO=727a2e7a5b23a606776fa12d75f8dcc8; APP_S467=72d2538222a8fbd6a12d5ac2434c5a4e
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="/tmp/s469_scratch_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$SCR" "$FIN/.finance_app.py.s469"; }
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
if [ "$HAVE" = "$APP_S467" ]; then
  say "!! [2/7] $FIN/finance_app.py is still the S467 file - S468_FINANCE_SMALLS goes in first (the owner's line runs it before this one); nothing installed"; exit 1; fi
[ "$HAVE" = "$APP_FROM" ] || { say "!! [2/7] $FIN/finance_app.py is $HAVE, not $APP_FROM - another kit changed it after this one was built. Nothing installed; tell the assistant, the kit is rebuilt on the new file."; exit 1; }
for f in finance_schema.sql finance_migration_S182_clinic.sql; do [ -f "$FIN/$f" ] || { say "!! [2/7] $FIN/$f is not there (the walk makes its empty database from it) - nothing installed"; exit 1; }; done
say "[2/7] finance_app.py at its S468 pin"

mkdir -p "$SCR" && \cp -p "$FIN/finance_app.py" "$SCR/finance_app.py" || { say "!! [3/7] no scratch copy - nothing installed"; clean; exit 1; }
"$SPY" -B apply_s469.py "$SCR/finance_app.py" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/7] the edits did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
[ "$(m5 "$SCR/finance_app.py")" = "$APP_TO" ] || { say "!! [3/7] the edited scratch copy is not its predicted bytes - nothing installed"; clean; exit 1; }
"$SPY" -m py_compile apply_s469.py walk_s469.py "$SCR/finance_app.py" 2>/dev/null || { say "!! [3/7] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the two edits apply to a scratch copy and give the predicted bytes; compiles"

WOUT="$( cd /tmp && timeout 900 "$SPY" -B "$KDIR/walk_s469.py" --apply "$KDIR/apply_s469.py" --finance "$FIN" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^  NOTE|^WALK_S469' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S469 GREEN" || { say "!! [4/7] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
[ "$(m5 "$FIN/finance_app.py")" = "$APP_FROM" ] || { say "!! [4/7] finance_app.py changed during the walk - nothing installed"; clean; exit 1; }
say "[4/7] walk green: each leak SHOWN on the old file and closed on the new one; reception gets the deposit banner's figures and the missing-day rows, as its page reads them; the checker's answers whole and unchanged; nobody refused who was not refused before"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

BA="$FIN/finance_app.py.bak_S469_$(echo "$APP_FROM" | cut -c1-8)"
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
\cp -p "$FIN/finance_app.py" "$FIN/.finance_app.py.s469" && cat "$SCR/finance_app.py" > "$FIN/.finance_app.py.s469" && [ "$(m5 "$FIN/.finance_app.py.s469")" = "$APP_TO" ] || { say "!! [6/7] could not stage the new file - nothing placed"; clean; exit 1; }
mv -f "$FIN/.finance_app.py.s469" "$FIN/finance_app.py" || restore "placing finance_app.py"
[ "$(m5 "$FIN/finance_app.py")" = "$APP_TO" ] || restore "md5 read-back of finance_app.py"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
sleep 8
systemctl is-active --quiet clinic-finance || restore "clinic-finance not active"
c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health "$FINURL/finance/health"); case "$c2" in 302|401) ;; *) restore "/finance/health answered $c2 without a login";; esac
c3=$(health "$FINURL/finance/clinic/api/tile"); case "$c3" in 401|403) ;; *) restore "/finance/clinic/api/tile answered $c3 without a login";; esac
c7=$(health "$FINURL/finance/clinic/api/exceptions"); case "$c7" in 401|403) ;; *) restore "/finance/clinic/api/exceptions answered $c7 without a login";; esac
c8=$(health "$FINURL/finance/clinic/entry"); case "$c8" in 302|401) ;; *) restore "/finance/clinic/entry answered $c8 without a login";; esac
c4=$(health "$FINURL/finance/pcs"); case "$c4" in 302|401) ;; *) restore "/finance/pcs answered $c4 without a login";; esac
D1="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
echo "$D1" | grep -q '"NOT_YOU"' || restore "the heartbeat door no longer refuses an unsigned heartbeat: $(echo "$D1" | cut -c1-160)"
D4="$(curl -s -m 10 "$FINURL/finance/api/pc-kit/fetch?part=kit")"
echo "$D4" | grep -q 'Clinic PCs page' || restore "the kit door (S450) no longer answers"
journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a module NOT mounted"
JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
[ "${JR:-0}" = 0 ] || restore "clinic-finance journal: $JR error line(s)"
say "[6/7] placed, md5 read back = the kit's pin · clinic-finance active · healthz 200 · /finance/health $c2, the clinic tile $c3, the clinic exceptions $c7, the clinic entry page $c8 and /finance/pcs $c4 (the login gate) · the heartbeat and kit doors answer as before · every part mounted · journal clean"
say "[7/7] from now: reception's login (and any non-checker) gets from the clinic tile only the deposit banner, and from the exceptions only the days not filled; the reception entry page is unchanged: https://followup.dr-manoj.in/finance/clinic/entry"
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/finance_app.py"
