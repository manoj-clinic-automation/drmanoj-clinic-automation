#!/bin/bash
# =============================================================================
# install_S475_YES_INTEREST_ROW.sh -- session 293, 04-Oct-2026 -- F-720: the Yes Bank readers accept the bank's quarter-end interest row
#  WHAT WENT WRONG (seen live 04-Oct, read in the statement itself): the branch's September statements of two savings accounts
#  carry 'CREDIT INTEREST CAPITALISED ON SB A/C' with TXN DATE 01-OCT-2026 and VALUE DATE 30-SEP-2026, counted by the bank inside
#  September's totals. Every arithmetic proof passed; the period check looked at the txn date alone and refused the whole file:
#  'a row dated 2026-10-01 falls outside the printed period 2026-09-01 to 2026-09-30'. Both Yes Bank readers have the same check.
#  EDITS, by apply_s475.py (exact anchors on the real bytes of the 04-Oct 01:35 bundle; every anchor found exactly once):
#   /root/finance/yes_branch.py       378539d9 -> fec5c520   in_period(): a row is inside the period when its VALUE date OR its txn
#   /root/finance/finance_yesbank.py  5a088cd9 -> 3509f728   date is; the refusal names both dates. Nothing accepted before is refused now.
#  THEN, on this box only: the shelf rows that carry that refusal are given back to the reader (read_status cleared; the slot
#  stays) and the shelf is run once (fetch + identify), so the two September statements are read today, not next month.
#  NOT TOUCHED: packs.py, stmt_shelf.py, the ICICI reader, the tables' shape, every page.
# Walked first, on this box, hermetically (F-709): both readers copied to /tmp twice (old / new) and fed made-up statement text
# in each layout; SHOWN refused on the old, read on the new; both-dates-outside still refused; the arithmetic proofs unchanged.
# Restarts clinic-finance (about 8 seconds; its 're-read the shelf inbox' button runs the reader in-process). Red after placing ->
# both files are put back. DRY=1 places nothing and runs no shelf. NEEDS the build lock free (F-694).
# =============================================================================
set -u
KIT="S475_YES_INTEREST_ROW"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
DB="${FINANCE_DB:-$FIN/finance.db}"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
declare -A FROM=( [yes_branch.py]=378539d930b8fc3caa5b0ce9d6664c5e [finance_yesbank.py]=5a088cd91bc1b8d873cc779f3fa9b0a8 )
declare -A TO=( [yes_branch.py]=fec5c520bfc4f563439d8f2dd6b24105 [finance_yesbank.py]=3509f7285fbae0d40fcb2daadb3a5b9f )
FILES="yes_branch.py finance_yesbank.py"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="/tmp/s475_scratch_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$SCR"; for f in $FILES; do rm -f "$FIN/.$f.s475"; done; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }

md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
if ! mkdir "$LOCK" 2>/dev/null; then
  say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
trap 'rm -rf "$LOCK"' EXIT
say "[1/7] kit gates green (SUMS, KIT_ID); the build lock is taken"

shelf_rerun() {
  # the rows the old check refused, given back to the reader; then one shelf run (fetch + identify), as the 05:40 cron runs it
  N="$("$SPY" - "$DB" <<'PY'
import sqlite3, sys
con = sqlite3.connect(sys.argv[1], timeout=60)
rows = con.execute("SELECT id, name, read_status FROM stmt_file WHERE read_status LIKE 'refused: a row dated % falls outside the printed period%'").fetchall()
for r in rows:
    print("   row %d · %s · %s" % (r[0], r[1][:48], r[2][:90]), file=sys.stderr)
con.execute("UPDATE stmt_file SET read_status=NULL, matched_status=NULL WHERE read_status LIKE 'refused: a row dated % falls outside the printed period%'")
con.commit(); print(len(rows))
PY
)"
  say "   $N shelf row(s) given back to the reader"
  ( cd "$FIN" && FINANCE_DB="$DB" timeout 900 "$VPY" -B "$FIN/stmt_shelf.py" run >> "$FIN/stmt_shelf.log" 2>&1 ); RC=$?
  say "   stmt_shelf.py run: rc $RC · $(tail -2 "$FIN/stmt_shelf.log" | cut -c1-200 | tr '\n' ' ')"
  "$SPY" - "$DB" <<'PY'
import sqlite3, sys
con = sqlite3.connect(sys.argv[1], timeout=60)
for r in con.execute("SELECT f.name, f.period_from, f.period_to, f.read_status FROM stmt_file f JOIN stmt_slot s ON s.id=f.slot_id WHERE s.bank='YES' AND f.period_from >= '2026-09-01' ORDER BY f.id"):
    print("   YES · %s · %s -> %s · %s" % (r[0][:40], r[1], r[2], (r[3] or 'arrived')[:80]))
PY
}

ALL=1; for f in $FILES; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then
  say "-- ALREADY INSTALLED: both readers at the kit's pins; clinic-finance $(systemctl is-active clinic-finance 2>/dev/null)"
  [ "${DRY:-0}" = 1 ] || { say "   the shelf run again, in case a refused row still waits:"; shelf_rerun; }
  exit 0
fi
for f in $FILES; do
  H="$(m5 "$FIN/$f")"
  [ "$H" = "${FROM[$f]}" ] || { say "!! [2/7] $FIN/$f is $H, not ${FROM[$f]} - another kit changed it after this one was built. Nothing installed; tell the assistant, the kit is rebuilt on the new file."; exit 1; }
done
[ -f "$DB" ] || { say "!! [2/7] $DB is not there - nothing installed"; exit 1; }
[ -x "$VPY" ] || { say "!! [2/7] $VPY is not there (the shelf's own python) - nothing installed"; exit 1; }
say "[2/7] both readers at their 04-Oct pins; the database and the shelf's python in place"

mkdir -p "$SCR" && for f in $FILES; do \cp -p "$FIN/$f" "$SCR/$f" || { say "!! [3/7] no scratch copy - nothing installed"; clean; exit 1; }; done
"$SPY" -B apply_s475.py "$SCR/yes_branch.py" "$SCR/finance_yesbank.py" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/7] the edits did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
for f in $FILES; do [ "$(m5 "$SCR/$f")" = "${TO[$f]}" ] || { say "!! [3/7] the edited scratch copy of $f is not its predicted bytes - nothing installed"; clean; exit 1; }; done
"$SPY" -m py_compile apply_s475.py walk_s475.py "$SCR/yes_branch.py" "$SCR/finance_yesbank.py" 2>/dev/null || { say "!! [3/7] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the four edits apply to scratch copies and give the predicted bytes; compiles"

WOUT="$( cd /tmp && timeout 600 "$SPY" -B "$KDIR/walk_s475.py" --apply "$KDIR/apply_s475.py" --finance "$FIN" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^WALK_S475' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S475 GREEN" || { say "!! [4/7] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
for f in $FILES; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [4/7] $f changed during the walk - nothing installed"; clean; exit 1; }; done
say "[4/7] walk green on this box: SHOWN refused on the old readers (both layouts), read on the new; both-dates-outside still refused; the arithmetic proofs unchanged"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted, the shelf not run"; clean; exit 0; fi

declare -A BAK
for f in $FILES; do
  B="$FIN/$f.bak_S475_$(echo "${FROM[$f]}" | cut -c1-8)"
  \cp -p "$FIN/$f" "$B" && [ "$(m5 "$B")" = "${FROM[$f]}" ] || { say "!! [5/7] the backup of $f failed - nothing placed"; clean; exit 1; }
  BAK[$f]="$B"
done
say "[5/7] backups: ${BAK[yes_branch.py]} and ${BAK[finance_yesbank.py]}"
restore() {
  say "!! RED after placing ($1) - restoring"
  for f in $FILES; do \cp -p "${BAK[$f]}" "$FIN/$f"; done
  systemctl restart clinic-finance 2>/dev/null || true; sleep 7
  say "   yes_branch.py $(m5 "$FIN/yes_branch.py") · finance healthz $(health "$FINURL/finance/healthz")"
  clean; exit 1
}
for f in $FILES; do
  \cp -p "$FIN/$f" "$FIN/.$f.s475" && cat "$SCR/$f" > "$FIN/.$f.s475" && [ "$(m5 "$FIN/.$f.s475")" = "${TO[$f]}" ] || { say "!! [6/7] could not stage $f - nothing placed"; clean; exit 1; }
done
for f in $FILES; do mv -f "$FIN/.$f.s475" "$FIN/$f" || restore "placing $f"; done
for f in $FILES; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore "md5 read-back of $f"; done
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
sleep 8
systemctl is-active --quiet clinic-finance || restore "clinic-finance not active"
c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health "$FINURL/finance/packs"); case "$c2" in 302|401) ;; *) restore "/finance/packs answered $c2 without a login";; esac
D1="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
echo "$D1" | grep -q '"NOT_YOU"' || restore "the heartbeat door no longer refuses an unsigned heartbeat: $(echo "$D1" | cut -c1-160)"
journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a module NOT mounted"
JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
[ "${JR:-0}" = 0 ] || restore "clinic-finance journal: $JR error line(s)"
say "[6/7] placed, md5 read back = the kit's pins · clinic-finance active · healthz 200 · /finance/packs $c2 (the login gate) · the heartbeat door answers as before · every part mounted · journal clean"

say "[7/7] the refused rows given back to the reader and the shelf run once:"
shelf_rerun
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/yes_branch.py" "$FIN/finance_yesbank.py"
