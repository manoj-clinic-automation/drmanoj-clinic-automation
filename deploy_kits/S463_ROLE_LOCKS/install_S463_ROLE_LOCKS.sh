#!/bin/bash
# =============================================================================
# install_S463_ROLE_LOCKS.sh -- session 292, 03-Oct-2026 -- at the owner's word: "Do these".
# THE CHECKER'S FIGURES ANSWER ONLY THE CHECKER (F-707). The gate lets in any login with ANY role on the unit, and these
# handlers had no check of their own: a 'viewer' (the returns desk) or a maker could read the month's totals, every
# day's closing drawer, parked cash and the patient-named day lines by typing the address.
#   EDIT  /root/finance/finance_app.py   27a162e6 (S462) -> 49f52391, by apply_s463.py (19 exact anchors):
#     the checker only   /finance/review, /finance/workbench, /finance/api/month/<ym>, /finance/api/days,
#                        /finance/api/parked, .../close-check, /finance/api/sources, /finance/api/archive/queue (or the
#                        worker's token); /finance/clinic/review, /finance/clinic/api/month/<ym>, .../days, .../parked
#     maker or checker   /finance/api/day/<date>/lines, /finance/clinic/api/day/<date>
#     five lines inside selftest() so its own role assumptions stay true.
#   LEFT AS THEY ARE: the clinic tile and clinic exceptions (reception's entry page reads both), both attachment routes,
#     /finance/api/shout, the clinic entry page, the five clinic 'not in this slice' stubs.
#   NOT TOUCHED: every other file; the database; the portal; unit_role. No setting is written. S462 must be in first
#   (the owner's one line runs it before this one).
# Walked first, on this box: the app's code copied to /tmp, an EMPTY database with two made-up days, six made-up logins
# (a maker, a viewer and a checker on each unit) asking every route touched and every route left, old file and new.
# Restarts clinic-finance only (about 8 seconds); red after placing -> the file is put back. DRY=1 places nothing.
# =============================================================================
set -u
KIT="S463_ROLE_LOCKS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
APP_FROM=27a162e6740140d4ce7d2e293eae9809; APP_TO=49f52391f44643c10b052609cffc5bbe; APP_S461=26a532a6ec212ac66e6cfb41b37844eb
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="/tmp/s463_scratch_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$SCR" "$FIN/.finance_app.py.s463"; }
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
if [ "$HAVE" = "$APP_S461" ]; then
  say "!! [2/7] $FIN/finance_app.py is still the S461 file - install S462_ADVANCE_POST_ONCE first (the owner's line runs it before this one); nothing installed"; exit 1; fi
[ "$HAVE" = "$APP_FROM" ] || { say "!! [2/7] $FIN/finance_app.py is $HAVE, not $APP_FROM - another kit changed it after this one was built. Nothing installed; tell the assistant, the kit is rebuilt on the new file."; exit 1; }
for f in finance_schema.sql finance_migration_S182_clinic.sql; do [ -f "$FIN/$f" ] || { say "!! [2/7] $FIN/$f is not there (the walk makes its empty database from it) - nothing installed"; exit 1; }; done
say "[2/7] finance_app.py at its S462 pin"

mkdir -p "$SCR" && \cp -p "$FIN/finance_app.py" "$SCR/finance_app.py" || { say "!! [3/7] no scratch copy - nothing installed"; clean; exit 1; }
"$SPY" -B apply_s463.py "$SCR/finance_app.py" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/7] the edits did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
[ "$(m5 "$SCR/finance_app.py")" = "$APP_TO" ] || { say "!! [3/7] the edited scratch copy is not its predicted bytes - nothing installed"; clean; exit 1; }
"$SPY" -m py_compile apply_s463.py walk_s463.py "$SCR/finance_app.py" 2>/dev/null || { say "!! [3/7] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the edits apply to a scratch copy and give the predicted bytes; compiles"

WOUT="$( cd /tmp && timeout 900 "$SPY" -B "$KDIR/walk_s463.py" --apply "$KDIR/apply_s463.py" --finance "$FIN" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^  NOTE|^WALK_S463' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S463 GREEN" || { say "!! [4/7] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
[ "$(m5 "$FIN/finance_app.py")" = "$APP_FROM" ] || { say "!! [4/7] finance_app.py changed during the walk - nothing installed"; clean; exit 1; }
say "[4/7] walk green: each leak shown on the old file and closed on the new one; the checker, reception and the pharmacy maker get byte for byte what they got"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

BA="$FIN/finance_app.py.bak_S463_$(echo "$APP_FROM" | cut -c1-8)"
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
\cp -p "$FIN/finance_app.py" "$FIN/.finance_app.py.s463" && cat "$SCR/finance_app.py" > "$FIN/.finance_app.py.s463" && [ "$(m5 "$FIN/.finance_app.py.s463")" = "$APP_TO" ] || { say "!! [6/7] could not stage the new file - nothing placed"; clean; exit 1; }
mv -f "$FIN/.finance_app.py.s463" "$FIN/finance_app.py" || restore "placing finance_app.py"
[ "$(m5 "$FIN/finance_app.py")" = "$APP_TO" ] || restore "md5 read-back of finance_app.py"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
sleep 8
systemctl is-active --quiet clinic-finance || restore "clinic-finance not active"
c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health "$FINURL/finance/health"); case "$c2" in 302|401) ;; *) restore "/finance/health answered $c2 without a login";; esac
c3=$(health "$FINURL/finance/api/month/2026-09"); case "$c3" in 401|403) ;; *) restore "/finance/api/month answered $c3 without a login";; esac
c5=$(health "$FINURL/finance/review"); case "$c5" in 302|401) ;; *) restore "/finance/review answered $c5 without a login";; esac
c6=$(health "$FINURL/finance/clinic/api/days"); case "$c6" in 401|403) ;; *) restore "/finance/clinic/api/days answered $c6 without a login";; esac
c4=$(health "$FINURL/finance/pcs"); case "$c4" in 302|401) ;; *) restore "/finance/pcs answered $c4 without a login";; esac
D1="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
echo "$D1" | grep -q '"NOT_YOU"' || restore "the heartbeat door no longer refuses an unsigned heartbeat: $(echo "$D1" | cut -c1-160)"
D4="$(curl -s -m 10 "$FINURL/finance/api/pc-kit/fetch?part=kit")"
echo "$D4" | grep -q 'Clinic PCs page' || restore "the kit door (S450) no longer answers"
journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a module NOT mounted"
JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
[ "${JR:-0}" = 0 ] || restore "clinic-finance journal: $JR error line(s)"
say "[6/7] placed, md5 read back = the kit's pin · clinic-finance active · healthz 200 · /finance/health $c2, /finance/review $c5, the month $c3, the clinic day list $c6 and /finance/pcs $c4 (the login gate) · the heartbeat and kit doors answer as before · every part mounted · journal clean"

say "[7/7] from now: the review and workbench pages, the month, the day list, parked cash, the close check, the sources and the archive queue answer the checker only (pharmacy and clinic); the day lines and the clinic day answer makers and checkers; nothing reception or the pharmacy maker uses has changed"
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/finance_app.py"
