#!/bin/bash
# =============================================================================
# install_S474_FINANCE_TIDY.sh -- session 293, 04-Oct-2026 -- the finance app tidied after its whole read, and F-716 repaired
#  EDITS, by apply_s474.py (exact anchors on the real bytes of the 04-Oct 01:35 bundle; every anchor found exactly once):
#   /root/finance/finance_app.py      727a2e7a -> 56eb421b  (a) the clinic tile answers a non-checker (reception's deposit
#                                      banner) FIRST -- no write to recon_exception on every page load, no month figures thrown
#                                      away; the checker's answer unchanged  (b) selftest teardown puts the ledger env back
#                                      (c) CLINIC_TENDERS, never used, removed  (d) F-716: the three Marg apply paths (push
#                                      apply, autoreplay at save, portal upload) call the loaders with commit=False and commit
#                                      once per day, so their rollback on a count mismatch is real  (e) a file the reader
#                                      refused may be sent again (a 'rejected' row is not 'received'; replaced when it reads)
#   /root/finance/finance_ingest.py   747b4a50 -> d7b07fb6  ingest_day(..., commit=True): commit=False leaves the day open
#   /root/finance/finance_returns.py  a46a87e6 -> 68d87d00  load_lines(..., commit=True): the same
#   /root/finance/marg_backfill.py    fa33ec8a -> b706456a  the backfill tool commits once per day, after bills and lines
#  Every other caller of the two loaders is unchanged (the default commits as before).
#  NOT TOUCHED: the database, every page, every setting, the ledger, the folders.
# Walked first, on this box, hermetically (F-709): the app's code copied to /tmp twice (old / new), each with an EMPTY
# database from the app's own schema; SHOWN on the old file that the maker's tile call writes missing-day rows, that a
# rolled-back second export still replaced the day, that refused bytes answered ALREADY-RECEIVED for ever.
# Restarts clinic-finance only (about 8 seconds); red after placing -> all four files are put back. DRY=1 places nothing.
# NEEDS the build lock free (F-694).
# =============================================================================
set -u
KIT="S474_FINANCE_TIDY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
declare -A FROM=( [finance_app.py]=727a2e7a5b23a606776fa12d75f8dcc8 [finance_ingest.py]=747b4a506042b95c862f3eafc74608f3 [finance_returns.py]=a46a87e65d951d59baeb9d86c9d8fe59 [marg_backfill.py]=fa33ec8a6dfa0ee0b6af5613160f3394 )
declare -A TO=( [finance_app.py]=56eb421b8d57a846e969b362e25b2c94 [finance_ingest.py]=d7b07fb6514da7129b969b878ce5fbbd [finance_returns.py]=68d87d00ccdb89a890ac98678befa393 [marg_backfill.py]=b706456ab8acaf2d6f01fcee8deaec33 )
FILES="finance_app.py finance_ingest.py finance_returns.py marg_backfill.py"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="/tmp/s474_scratch_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$SCR"; for f in $FILES; do rm -f "$FIN/.$f.s474"; done; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }

md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$SPY" -c "import flask, werkzeug" 2>/dev/null || { say "!! [1/6] $SPY lacks flask - nothing installed"; exit 1; }
if ! mkdir "$LOCK" 2>/dev/null; then
  say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
trap 'rm -rf "$LOCK"' EXIT
say "[1/6] kit gates green (SUMS, KIT_ID, flask); the build lock is taken"

ALL=1; for f in $FILES; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: all four files at the kit's pins; clinic-finance $(systemctl is-active clinic-finance 2>/dev/null)"; exit 0; fi
for f in $FILES; do
  H="$(m5 "$FIN/$f")"
  [ "$H" = "${FROM[$f]}" ] || { say "!! [2/6] $FIN/$f is $H, not ${FROM[$f]} - another kit changed it after this one was built. Nothing installed; tell the assistant, the kit is rebuilt on the new file."; exit 1; }
done
for f in finance_schema.sql finance_migration_S182_clinic.sql; do [ -f "$FIN/$f" ] || { say "!! [2/6] $FIN/$f is not there (the walk makes its empty database from it) - nothing installed"; exit 1; }; done
say "[2/6] the four files at their 04-Oct pins"

mkdir -p "$SCR" && for f in $FILES; do \cp -p "$FIN/$f" "$SCR/$f" || { say "!! [3/6] no scratch copy - nothing installed"; clean; exit 1; }; done
"$SPY" -B apply_s474.py "$SCR/finance_app.py" "$SCR/finance_ingest.py" "$SCR/finance_returns.py" "$SCR/marg_backfill.py" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/6] the edits did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
for f in $FILES; do [ "$(m5 "$SCR/$f")" = "${TO[$f]}" ] || { say "!! [3/6] the edited scratch copy of $f is not its predicted bytes - nothing installed"; clean; exit 1; }; done
"$SPY" -m py_compile apply_s474.py walk_s474.py "$SCR/finance_app.py" "$SCR/finance_ingest.py" "$SCR/finance_returns.py" "$SCR/marg_backfill.py" 2>/dev/null || { say "!! [3/6] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/6] the 20 edits apply to scratch copies and give the predicted bytes; compiles"

WOUT="$( cd /tmp && timeout 900 "$SPY" -B "$KDIR/walk_s474.py" --apply "$KDIR/apply_s474.py" --finance "$FIN" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^WALK_S474' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S474 GREEN" || { say "!! [4/6] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
for f in $FILES; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [4/6] $f changed during the walk - nothing installed"; clean; exit 1; }; done
say "[4/6] walk green on this box: SHOWN on the old file -- reception's tile call wrote missing-day rows, a rolled-back second export still replaced the day, refused bytes stayed ALREADY-RECEIVED; on the new file none of the three; the checker's tile answer identical old and new"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

declare -A BAK
for f in $FILES; do
  B="$FIN/$f.bak_S474_$(echo "${FROM[$f]}" | cut -c1-8)"
  \cp -p "$FIN/$f" "$B" && [ "$(m5 "$B")" = "${FROM[$f]}" ] || { say "!! [5/6] the backup of $f failed - nothing placed"; clean; exit 1; }
  BAK[$f]="$B"
done
say "[5/6] backups: ${BAK[finance_app.py]} and three beside it (.bak_S474_<from8>)"
restore() {
  say "!! RED after placing ($1) - restoring"
  for f in $FILES; do \cp -p "${BAK[$f]}" "$FIN/$f"; done
  systemctl restart clinic-finance 2>/dev/null || true; sleep 7
  say "   finance_app.py $(m5 "$FIN/finance_app.py") · finance healthz $(health "$FINURL/finance/healthz")"
  clean; exit 1
}
for f in $FILES; do
  \cp -p "$FIN/$f" "$FIN/.$f.s474" && cat "$SCR/$f" > "$FIN/.$f.s474" && [ "$(m5 "$FIN/.$f.s474")" = "${TO[$f]}" ] || { say "!! [6/6] could not stage $f - nothing placed"; clean; exit 1; }
done
for f in $FILES; do mv -f "$FIN/.$f.s474" "$FIN/$f" || restore "placing $f"; done
for f in $FILES; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore "md5 read-back of $f"; done
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
sleep 8
systemctl is-active --quiet clinic-finance || restore "clinic-finance not active"
c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health "$FINURL/finance/health"); case "$c2" in 302|401) ;; *) restore "/finance/health answered $c2 without a login";; esac
c3=$(health "$FINURL/finance/clinic/api/tile"); case "$c3" in 401|403|302) ;; *) restore "/finance/clinic/api/tile answered $c3 without a login";; esac
c4=$(health -X POST "$FINURL/finance/api/marg-push"); case "$c4" in 401) ;; *) restore "/finance/api/marg-push answered $c4 to an unsigned push";; esac
D1="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
echo "$D1" | grep -q '"NOT_YOU"' || restore "the heartbeat door no longer refuses an unsigned heartbeat: $(echo "$D1" | cut -c1-160)"
D4="$(curl -s -m 10 "$FINURL/finance/api/pc-kit/fetch?part=kit")"
echo "$D4" | grep -q 'Clinic PCs page' || restore "the kit door (S450) no longer answers"
journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a module NOT mounted"
JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
[ "${JR:-0}" = 0 ] || restore "clinic-finance journal: $JR error line(s)"
say "[6/6] placed, md5 read back = the kit's pins · clinic-finance active · healthz 200 · /finance/health $c2, the clinic tile $c3 (the login gate) · the Marg push door refuses an unsigned push ($c4) · the heartbeat and kit doors answer as before · every part mounted · journal clean"
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/finance_app.py" "$FIN/finance_ingest.py" "$FIN/finance_returns.py" "$FIN/marg_backfill.py"
