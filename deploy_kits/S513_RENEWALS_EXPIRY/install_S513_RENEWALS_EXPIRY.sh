#!/bin/bash
# =============================================================================
# install_S513_RENEWALS_EXPIRY.sh -- session 304, 10-Oct-2026 -- D689, closes F-775.
# THE OWNER'S RULING: a renewal comes up 45 days before its REAL expiry and is red only after it. Until now the Renewals
# row of /finance/health read each row's early-alert day as the deadline -- the arms licence (alert 27-Sep, expiry in
# December) has shown OVERDUE since 27-Sep. An alert day and a deadline are two fields.
#   EDIT  /root/finance/finance_app.py   bff362c3 (the 10-Oct bundle) -> ec5b3ab1, by apply_s513.py (read whole first):
#         the window 30 -> 45 days; the push keeps expiryISO beside dateISO (a row without one keeps its alert day as its
#         expiry, as before); the row counts days to the expiry; red only after it; a stale feed still names what is
#         near; one bad stored row is skipped, not the whole row; the selftest's renewals block follows.
#   COMPANION: Renewal_Nag.gs v3 in the owner's personal Janitor project (placed by the assistant in his signed-in browser)
#         sends expiryISO and leaves out every bracket holding a number. Either order works.
#   WRITES NOTHING else: no table, no setting. The feed file is read once, read-only, for the data step.
# Walked first, on this box: the app's code copied to /tmp, an EMPTY database, the health page asked as a made-up checker
# through fourteen situations on the old file and the new, a made-up push through the token door, and the selftest's own
# renewals block run as each file writes it. Restarts clinic-finance only (about 8 seconds); red after placing -> the
# file is put back. DRY=1 places nothing.
# =============================================================================
set -u
KIT="S513_RENEWALS_EXPIRY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
APP_FROM=bff362c38ec61526ea0047fd136df826; APP_TO=ec5b3ab170ff37c63ac98f6f1f11ad09; RNS="${RENEWALS_STATE_LIVE:-$FIN/renewals_state.json}"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="/tmp/s513_scratch_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$SCR" "$FIN/.finance_app.py.s513"; }
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
say "[2/7] finance_app.py at its 10-Oct pin (bff362c3)"

mkdir -p "$SCR" && \cp -p "$FIN/finance_app.py" "$SCR/finance_app.py" || { say "!! [3/7] no scratch copy - nothing installed"; clean; exit 1; }
"$SPY" -B apply_s513.py "$SCR/finance_app.py" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/7] the edits did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
[ "$(m5 "$SCR/finance_app.py")" = "$APP_TO" ] || { say "!! [3/7] the edited scratch copy is not its predicted bytes - nothing installed"; clean; exit 1; }
"$SPY" -m py_compile apply_s513.py walk_s513.py "$SCR/finance_app.py" 2>/dev/null || { say "!! [3/7] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the edits apply to a scratch copy and give the predicted bytes; compiles"

WOUT="$( cd /tmp && timeout 900 "$SPY" -B "$KDIR/walk_s513.py" --apply "$KDIR/apply_s513.py" --finance "$FIN" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^  NOTE|^WALK_S513' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S513 GREEN" || { say "!! [4/7] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
[ "$(m5 "$FIN/finance_app.py")" = "$APP_FROM" ] || { say "!! [4/7] finance_app.py changed during the walk - nothing installed"; clean; exit 1; }
say "[4/7] walk green: an alert day gone by with the expiry 77 days off is quiet (the old file: OVERDUE); 40 days before the expiry info, 5 days warn, the expiry day warn, the day after red; a feed in the old shape means what it meant; the push keeps expiryISO; every other row of the page unchanged; the selftest's renewals block green on both files"
LIVE="$("$SPY" - "$RNS" <<'PYEOF' 2>&1
import datetime, json, os, sys
p = sys.argv[1]
if not os.path.isfile(p):
    print("LIVE_S513 OK: no feed file yet, so the Renewals row stays 'no feed yet'"); sys.exit(0)
try:
    st = json.load(open(p, encoding="utf-8"))
    items = st.get("items") or []
    t = datetime.date.today()
    old = new = None
    with_exp = 0
    for it in items:
        try:
            a = (datetime.date.fromisoformat(str(it["dateISO"])[:10]) - t).days
            e = (datetime.date.fromisoformat(str(it.get("expiryISO") or it["dateISO"])[:10]) - t).days
        except Exception:
            continue
        with_exp += 1 if it.get("expiryISO") else 0
        old = a if old is None else min(old, a)
        new = e if new is None else min(new, e)
    print("LIVE_S513 OK: the stored feed (read only, names not printed) has %d row(s), %d carrying a real expiry; nearest by the old reading %s, by the new %s"
          % (len(items), with_exp, "none" if old is None else "%+d days" % old, "none" if new is None else "%+d days" % new))
except Exception as ex:
    print("LIVE_S513 RED: %s: %s" % (type(ex).__name__, ex)); sys.exit(1)
PYEOF
)"
echo "$LIVE" | grep -E '^LIVE_S513' | cut -c1-300 | sed 's/^/   /'
echo "$LIVE" | grep -q "^LIVE_S513 OK" || { say "!! [4/7] the box's own renewals feed could not be read - nothing installed"; echo "$LIVE" | tail -5 | cut -c1-300; clean; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

BA="$FIN/finance_app.py.bak_S513_$(echo "$APP_FROM" | cut -c1-8)"
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
\cp -p "$FIN/finance_app.py" "$FIN/.finance_app.py.s513" && cat "$SCR/finance_app.py" > "$FIN/.finance_app.py.s513" && [ "$(m5 "$FIN/.finance_app.py.s513")" = "$APP_TO" ] || { say "!! [6/7] could not stage the new file - nothing placed"; clean; exit 1; }
mv -f "$FIN/.finance_app.py.s513" "$FIN/finance_app.py" || restore "placing finance_app.py"
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
say "[7/7] from now: https://followup.dr-manoj.in/finance/health -- the Renewals row counts each renewal to its real expiry: shown from 45 days before it, red only after it"
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/finance_app.py"
