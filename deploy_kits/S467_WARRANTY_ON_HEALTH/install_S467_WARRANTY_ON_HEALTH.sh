#!/bin/bash
# =============================================================================
# install_S467_WARRANTY_ON_HEALTH.sh -- session 292, 03-Oct-2026 -- D664, at the owner's word: "build."
# THE OWNER'S HEALTH PAGE REMINDS HIM OF A WARRANTY. His ruling: the inverter battery is a Dr MK expense, and the
# renewals list must remind him of the warranty date. S466 keeps the warranty in the asset app; this makes the Renewals
# row of /finance/health say it while it is INSIDE ITS OWN reminder window: info, and warn inside 7 days (which is what
# reaches the portal tile). A warranty that has ended is never said and can never turn the row red.
#   EDIT  /root/finance/finance_app.py   49f52391 (S463) -> 72d25382, by apply_s467.py: TWO INSERTIONS, nothing removed --
#         a read-only reader of /root/assetapp/assets.db (table d664_warranty; the path purchase_app already takes),
#         and a block after the Renewals row is made. Section 6 itself is not edited.
#   WRITES NOTHING: no table, no file, no setting. The asset database is opened read-only.
#   NOT TOUCHED: every other file; the renewals feed and its push; the database; the portal.
#   INDEPENDENT OF S465/S466: with no d664_warranty table the row is byte for byte today's (walked).
# Walked first, on this box: the app's code copied to /tmp, an EMPTY database, the health page asked as the checker
# through eleven situations on the old file and the new, with a made-up asset database. Then the box's OWN asset
# database is read once, read-only, by the same query (counts only). Restarts clinic-finance only (about 8 seconds);
# red after placing -> the file is put back. DRY=1 places nothing.
# =============================================================================
set -u
KIT="S467_WARRANTY_ON_HEALTH"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
APP_FROM=49f52391f44643c10b052609cffc5bbe; APP_TO=72d2538222a8fbd6a12d5ac2434c5a4e; ADB="${ASSETS_DB_LIVE:-$ROOT/assetapp/assets.db}"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="/tmp/s467_scratch_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$SCR" "$FIN/.finance_app.py.s467"; }
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
say "[2/7] finance_app.py at its S463 pin"

mkdir -p "$SCR" && \cp -p "$FIN/finance_app.py" "$SCR/finance_app.py" || { say "!! [3/7] no scratch copy - nothing installed"; clean; exit 1; }
"$SPY" -B apply_s467.py "$SCR/finance_app.py" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/7] the edits did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
[ "$(m5 "$SCR/finance_app.py")" = "$APP_TO" ] || { say "!! [3/7] the edited scratch copy is not its predicted bytes - nothing installed"; clean; exit 1; }
"$SPY" -m py_compile apply_s467.py walk_s467.py "$SCR/finance_app.py" 2>/dev/null || { say "!! [3/7] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the two insertions apply to a scratch copy and give the predicted bytes; compiles"

WOUT="$( cd /tmp && timeout 900 "$SPY" -B "$KDIR/walk_s467.py" --apply "$KDIR/apply_s467.py" --finance "$FIN" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^  NOTE|^WALK_S467' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S467 GREEN" || { say "!! [4/7] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
[ "$(m5 "$FIN/finance_app.py")" = "$APP_FROM" ] || { say "!! [4/7] finance_app.py changed during the walk - nothing installed"; clean; exit 1; }
say "[4/7] walk green: with no warranty due the health page is byte for byte the old one (no asset database, no table, a damaged file, only ended warranties); a due one is said, info then warn inside 7 days; an overdue renewal still leads; the asset database is only read"
LIVE="$("$SPY" - "$ADB" <<'PYEOF' 2>&1
import datetime, os, sqlite3, sys
p = sys.argv[1]
if not os.path.isfile(p):
    print("LIVE_S467 OK: %s is not there, so the Renewals row stays exactly as it is" % p); sys.exit(0)
try:
    c = sqlite3.connect("file:%s?mode=ro" % p, uri=True, timeout=2)
    if not c.execute("SELECT 1 FROM sqlite_master WHERE name='d664_warranty'").fetchone():
        print("LIVE_S467 OK: the asset database opens read-only; it has no warranty table yet (S466 not installed), so the Renewals row stays exactly as it is"); sys.exit(0)
    t, n, due = datetime.date.today(), 0, 0
    for what, till, rd in c.execute("SELECT w.what, w.till, w.remind_days FROM d664_warranty w JOIN bills b ON b.id=w.bill_id WHERE COALESCE(b.lane,'clinic')='owner_expense' AND b.status<>'rejected'"):
        n += 1
        try:
            dd = (datetime.date.fromisoformat(str(till)[:10]) - t).days
        except Exception:
            continue
        due += 1 if (rd and 0 <= dd <= int(rd)) else 0
    print("LIVE_S467 OK: the asset database opens read-only (journal mode %s); warranties noted: %d, inside their reminder window today: %d" % (c.execute("PRAGMA journal_mode").fetchone()[0], n, due))
except Exception as ex:
    print("LIVE_S467 RED: %s: %s" % (type(ex).__name__, ex)); sys.exit(1)
PYEOF
)"
echo "$LIVE" | grep -E '^LIVE_S467' | cut -c1-300 | sed 's/^/   /'
echo "$LIVE" | grep -q "^LIVE_S467 OK" || { say "!! [4/7] the box's own asset database could not be read read-only - nothing installed"; echo "$LIVE" | tail -5 | cut -c1-300; clean; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

BA="$FIN/finance_app.py.bak_S467_$(echo "$APP_FROM" | cut -c1-8)"
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
\cp -p "$FIN/finance_app.py" "$FIN/.finance_app.py.s467" && cat "$SCR/finance_app.py" > "$FIN/.finance_app.py.s467" && [ "$(m5 "$FIN/.finance_app.py.s467")" = "$APP_TO" ] || { say "!! [6/7] could not stage the new file - nothing placed"; clean; exit 1; }
mv -f "$FIN/.finance_app.py.s467" "$FIN/finance_app.py" || restore "placing finance_app.py"
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
say "[7/7] from now: https://followup.dr-manoj.in/finance/health -- the Renewals row also names a Dr MK expense warranty while it is inside its reminder window (and nothing else about that page has moved)"
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/finance_app.py"
