#!/bin/bash
# =============================================================================
# install_S471_PACKS_SEPTEMBER.sh -- session 293, 04-Oct-2026 -- the owner's four refinements of the month-end packs
# (his words, 04-Oct: "the accountant pack section needs refinement", "for each Yes Bank account there should be a separate
# password", and the September road; "do all that you have planned ... according to the technical flow").
#  EDITS, by apply_s471.py (exact anchors on the real bytes of the 04-Oct 01:35 bundle; every anchor found exactly once):
#   /root/finance/packs.py       23fda41a -> 6738d65d  stitch: two consecutive cycle statements ARE the month's statement (both
#                                 go in the pack, part 1 of 2); a lone cycle statement is 'partial' on row and shelf alike and
#                                 says which statement completes the month and when it is due; one password key per Yes Bank
#                                 account ('YES:<slot>') before the bank-wide ones; row numbers 3.1.., 4.1.., 8.1/8.2; the
#                                 electricity row explains itself while the ICICI statements are not on the shelf
#   /root/finance/packs.html     4c46cd0e -> 1349b37b  the page for all of the above; the Shavez summary says done AND open
#   /root/finance/stmt_shelf.py  95ba0a4f -> 52a5fb07  the unlock step tries an account's own password before a bank-wide one
#  ONE crontab line added: a second shelf fetch at 07:30 IST (after the personal account's relay at 07:00), same command as
#  S408's 05:40 line, tagged S471_PACKS_SEPTEMBER. The crontab is backed up first.
#  NOT TOUCHED: the database (no schema change -- the account keys live in stmt_secret's existing bank column), every other
#  route, the checklist page, the send, Amir's pack, the Sanjeevni files.
# Walked first, on this box, hermetically (F-709): the edited files beside the box's own readers in /tmp, an EMPTY database,
# made-up PDFs, the unlock under the venv python; SHOWN on the old file that two cycle statements read 'partial' there.
# Restarts clinic-finance only (about 8 seconds); red after placing -> all three files and the crontab are put back.
# DRY=1 places nothing. NEEDS the build lock free (F-694).
# =============================================================================
set -u
KIT="S471_PACKS_SEPTEMBER"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
PY_FROM=23fda41a19a6d4be398922e906d06702; PY_TO=6738d65dacd26b3f308fe8fd688b806a
HT_FROM=4c46cd0e19ec08a7678dd6088624a174; HT_TO=1349b37b2a952ee4566376a577541e31
SH_FROM=95ba0a4fadd25d9f30a67e7f99eba9f1; SH_TO=52a5fb07339e12d6a875b6fbdb6acddc
CRON_LINE="30 7 * * * cd /root/finance && FINANCE_DB=/root/finance/finance.db $VPY -B /root/finance/stmt_shelf.py run >> /root/finance/stmt_shelf.log 2>&1 # $KIT"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="/tmp/s471_scratch_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$SCR" "$FIN/.packs.py.s471" "$FIN/.packs.html.s471" "$FIN/.stmt_shelf.py.s471"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }

md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$SPY" -c "import flask, werkzeug" 2>/dev/null || { say "!! [1/7] $SPY lacks flask - nothing installed"; exit 1; }
"$VPY" -c "import pypdf" 2>/dev/null || { say "!! [1/7] $VPY lacks pypdf (the unlock step's python) - nothing installed"; exit 1; }
if ! mkdir "$LOCK" 2>/dev/null; then
  say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
trap 'rm -rf "$LOCK"' EXIT
say "[1/7] kit gates green (SUMS, KIT_ID, flask, pypdf); the build lock is taken"

H1="$(m5 "$FIN/packs.py")"; H2="$(m5 "$FIN/packs.html")"; H3="$(m5 "$FIN/stmt_shelf.py")"
if [ "$H1" = "$PY_TO" ] && [ "$H2" = "$HT_TO" ] && [ "$H3" = "$SH_TO" ]; then
  crontab -l 2>/dev/null | grep -q "# $KIT" && say "-- ALREADY INSTALLED: all three files at the kit's pins; the 07:30 cron line present; clinic-finance $(systemctl is-active clinic-finance 2>/dev/null)" || say "-- files at the kit's pins but the 07:30 cron line is MISSING - tell the assistant"
  exit 0
fi
[ "$H1" = "$PY_FROM" ] || { say "!! [2/7] $FIN/packs.py is $H1, not $PY_FROM - another kit changed it after this one was built. Nothing installed; tell the assistant, the kit is rebuilt on the new file."; exit 1; }
[ "$H2" = "$HT_FROM" ] || { say "!! [2/7] $FIN/packs.html is $H2, not $HT_FROM - nothing installed; tell the assistant"; exit 1; }
[ "$H3" = "$SH_FROM" ] || { say "!! [2/7] $FIN/stmt_shelf.py is $H3, not $SH_FROM - nothing installed; tell the assistant"; exit 1; }
for f in finance_icici.py finance_yesbank.py yes_branch.py; do [ -f "$FIN/$f" ] || { say "!! [2/7] $FIN/$f is not there (the walk copies the readers beside the scratch) - nothing installed"; exit 1; }; done
say "[2/7] packs.py, packs.html and stmt_shelf.py at their 04-Oct pins"

mkdir -p "$SCR" && \cp -p "$FIN/packs.py" "$FIN/packs.html" "$FIN/stmt_shelf.py" "$SCR/" || { say "!! [3/7] no scratch copy - nothing installed"; clean; exit 1; }
"$SPY" -B apply_s471.py "$SCR/packs.py" "$SCR/packs.html" "$SCR/stmt_shelf.py" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/7] the edits did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
[ "$(m5 "$SCR/packs.py")" = "$PY_TO" ] && [ "$(m5 "$SCR/packs.html")" = "$HT_TO" ] && [ "$(m5 "$SCR/stmt_shelf.py")" = "$SH_TO" ] || { say "!! [3/7] the edited scratch copies are not their predicted bytes - nothing installed"; clean; exit 1; }
"$SPY" -m py_compile apply_s471.py walk_s471.py "$SCR/packs.py" "$SCR/stmt_shelf.py" 2>/dev/null || { say "!! [3/7] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the 21 edits apply to scratch copies and give the predicted bytes; compiles"

WOUT="$( cd /tmp && timeout 900 "$SPY" -B "$KDIR/walk_s471.py" --apply "$KDIR/apply_s471.py" --finance "$FIN" --venv "$VPY" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^  NOTE|^WALK_S471' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S471 GREEN" || { say "!! [4/7] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
[ "$(m5 "$FIN/packs.py")" = "$PY_FROM" ] || { say "!! [4/7] packs.py changed during the walk - nothing installed"; clean; exit 1; }
say "[4/7] walk green on this box: two cycle statements stitch (and read 'partial' on the OLD file); a lone one is 'partial' on row and shelf with its due date; six Yes Bank account keys before the bank-wide ones; the unlock opens a made-up locked PDF by the ACCOUNT key under $VPY; numbering 3.1.., 4.1.., 8.1/8.2; the page's words"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted, no cron line"; clean; exit 0; fi

B1="$FIN/packs.py.bak_S471_$(echo "$PY_FROM" | cut -c1-8)"; B2="$FIN/packs.html.bak_S471_$(echo "$HT_FROM" | cut -c1-8)"; B3="$FIN/stmt_shelf.py.bak_S471_$(echo "$SH_FROM" | cut -c1-8)"
\cp -p "$FIN/packs.py" "$B1" && \cp -p "$FIN/packs.html" "$B2" && \cp -p "$FIN/stmt_shelf.py" "$B3" && [ "$(m5 "$B1")" = "$PY_FROM" ] && [ "$(m5 "$B2")" = "$HT_FROM" ] && [ "$(m5 "$B3")" = "$SH_FROM" ] || { say "!! [5/7] the backups failed - nothing placed"; clean; exit 1; }
crontab -l > "$FIN/crontab.bak_S471_$STAMP" 2>/dev/null || true
say "[5/7] backups: $B1 · $B2 · $B3 · crontab.bak_S471_$STAMP"
restore() {
  say "!! RED after placing ($1) - restoring"
  \cp -p "$B1" "$FIN/packs.py"; \cp -p "$B2" "$FIN/packs.html"; \cp -p "$B3" "$FIN/stmt_shelf.py"
  crontab -l 2>/dev/null | grep -v "# $KIT" | crontab - 2>/dev/null || true
  systemctl restart clinic-finance 2>/dev/null || true; sleep 7
  say "   packs.py $(m5 "$FIN/packs.py") · packs.html $(m5 "$FIN/packs.html") · stmt_shelf.py $(m5 "$FIN/stmt_shelf.py") · finance healthz $(health "$FINURL/finance/healthz")"
  clean; exit 1
}
# the walked scratch files go in by a rename each, so no file is ever half-written; owner and mode are the old file's
for pair in "packs.py:$PY_TO" "packs.html:$HT_TO" "stmt_shelf.py:$SH_TO"; do
  f="${pair%%:*}"; want="${pair##*:}"
  \cp -p "$FIN/$f" "$FIN/.$f.s471" && cat "$SCR/$f" > "$FIN/.$f.s471" && [ "$(m5 "$FIN/.$f.s471")" = "$want" ] || { say "!! [6/7] could not stage $f - nothing placed"; clean; exit 1; }
done
mv -f "$FIN/.packs.py.s471" "$FIN/packs.py" || restore "placing packs.py"
mv -f "$FIN/.packs.html.s471" "$FIN/packs.html" || restore "placing packs.html"
mv -f "$FIN/.stmt_shelf.py.s471" "$FIN/stmt_shelf.py" || restore "placing stmt_shelf.py"
[ "$(m5 "$FIN/packs.py")" = "$PY_TO" ] && [ "$(m5 "$FIN/packs.html")" = "$HT_TO" ] && [ "$(m5 "$FIN/stmt_shelf.py")" = "$SH_TO" ] || restore "md5 read-back"
( crontab -l 2>/dev/null | grep -v "# $KIT"; echo "$CRON_LINE" ) | crontab - || restore "crontab"
crontab -l | grep -q "# $KIT" || restore "the 07:30 cron line did not land"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
sleep 8
systemctl is-active --quiet clinic-finance || restore "clinic-finance not active"
c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health "$FINURL/finance/packs"); case "$c2" in 302|401) ;; *) restore "/finance/packs answered $c2 without a login";; esac
c3=$(health "$FINURL/finance/packs/api/state?month=2026-09"); case "$c3" in 401|403|302) ;; *) restore "/finance/packs/api/state answered $c3 without a login";; esac
c4=$(health "$FINURL/finance/packs/checklist"); case "$c4" in 302|401) ;; *) restore "/finance/packs/checklist answered $c4 without a login";; esac
D1="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
echo "$D1" | grep -q '"NOT_YOU"' || restore "the heartbeat door no longer refuses an unsigned heartbeat: $(echo "$D1" | cut -c1-160)"
journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a module NOT mounted"
JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
[ "${JR:-0}" = 0 ] || restore "clinic-finance journal: $JR error line(s)"
say "[6/7] placed, md5 read back = the kit's pins · the 07:30 cron line in · clinic-finance active · healthz 200 · /finance/packs $c2, its data $c3, the checklist $c4 (the login gate) · the heartbeat door answers as before · every part mounted · journal clean"
say "[7/7] the shelf re-read once now (the same command as the cron line; counts only):"
( cd /root/finance && FINANCE_DB=/root/finance/finance.db timeout 600 "$VPY" -B /root/finance/stmt_shelf.py run 2>&1 | tail -3 | cut -c1-300 | sed 's/^/      /' )
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/packs.py" "$FIN/packs.html" "$FIN/stmt_shelf.py"
crontab -l | grep "stmt_shelf" | cut -c1-120
