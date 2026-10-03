#!/bin/bash
# =============================================================================
# install_S466_EXPENSE_WARRANTY.sh -- session 292, 03-Oct-2026 -- D664, at the owner's word: "build."  Slice 3 of 3.
# A DR MK EXPENSE KEEPS ITS WARRANTY: on the paper's own page, "Keep the warranty" -- what it is, warranty till, remind
# 30 days / 7 days before, or never. It then shows, to the OWNER only, on the asset app's "Renewals & warranties" page:
# inside its reminder window by default, every warranty under "show all upcoming". An ended warranty is never
# "overdue" and drops off after 60 days. NOTHING GOES OUT ON WHATSAPP: /api/due is not touched (walked: its answer is
# byte for byte the same with six warranties saved).
#   REPLACE /root/assetapp/clinic_papers.py   231cd6a9 (S465.1) -> this kit's (S466.1)
#   EDIT    /root/assetapp/asset_register.py  b0e0915e (S465) -> e774be89, by apply_s466.py (3 exact anchors): the card's
#           hook on the Renewals page (two lines) and 'Warranty: ...' on a Dr MK expense bill's page -- each behind
#           its own 'is defined'
#   DATABASE  ONE new table, d664_warranty, made by the app at start. assets.db copied first.
#   NOT TOUCHED: /api/due, the dashboard, the lanes, the intake, scanner_widget.js, shared/scan_checks_s441.py, the
#           pharmacy hand-over, every finance file. NEEDS S465 installed first (it refuses on the pins otherwise).
# Walked first, on this box (old / new / new-without-the-module / new-with-S465's-module, each on an empty database).
# Then THE REAL PAPERS: the edited app on a COPY of assets.db -- Renewals, the list and each Dr MK expense paper's page
# are opened, and ONE REAL SAVE is rehearsed there and removed. Restarts assetapp only. Red after placing -> both old
# files are put back. DRY=1 places nothing.
# =============================================================================
set -u
KIT="S466_EXPENSE_WARRANTY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; AST="$ROOT/assetapp"; ADB="${ASSETS_DB_LIVE:-$AST/assets.db}"
SHARED="${SHARED_LIB_DIR:-$ROOT/shared}"
ASTURL="${ASTURL:-http://127.0.0.1:8030}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
AR_FROM=b0e0915e0b73a6ffb1f4a6e17aec8274; AR_TO=e774be89193472dfa4b142d85bdcc46c
CP_FROM=231cd6a959d2030160ec9de43fb4d076
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="/tmp/s466_scratch_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$SCR" "$AST/.asset_register.py.s466" "$AST/.clinic_papers.py.s466"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }

md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$SPY" -c "import flask, werkzeug" 2>/dev/null || { say "!! [1/8] $SPY lacks flask - nothing installed"; exit 1; }
CP_TO="$(m5 built/clinic_papers.py)"
if ! mkdir "$LOCK" 2>/dev/null; then
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
trap 'rm -rf "$LOCK"' EXIT
say "[1/8] kit gates green (SUMS, KIT_ID, flask); the build lock is taken"

HAVE="$(m5 "$AST/asset_register.py")"; HAVECP="$(m5 "$AST/clinic_papers.py")"
if [ "$HAVE" = "$AR_TO" ] && [ "$HAVECP" = "$CP_TO" ]; then
  say "-- ALREADY INSTALLED: both files are at the kit's pins; assetapp $(systemctl is-active assetapp 2>/dev/null)"; exit 0; fi
[ "$HAVE" = "$AR_FROM" ] || { say "!! [2/8] $AST/asset_register.py is $HAVE, not $AR_FROM (S465) - S465_PAPERS_JOIN goes in first; if it is in, another kit changed the file and this one is rebuilt on the new bytes. Nothing installed."; exit 1; }
[ "$HAVECP" = "$CP_FROM" ] || { say "!! [2/8] $AST/clinic_papers.py is ${HAVECP:-absent}, not $CP_FROM (S465.1) - S465_PAPERS_JOIN goes in first. Nothing installed."; exit 1; }
[ -f "$ADB" ] || { say "!! [2/8] $ADB is not there - nothing installed"; exit 1; }
say "[2/8] both files at their S465 pins"

mkdir -p "$SCR/live/assetapp" && \cp -p "$AST/asset_register.py" "$AST/scanner_widget.js" "$SCR/live/assetapp/" || { say "!! [3/8] no scratch copy - nothing installed"; clean; exit 1; }
"$SPY" -B apply_s466.py "$SCR/live/assetapp/asset_register.py" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/8] the edits did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
[ "$(m5 "$SCR/live/assetapp/asset_register.py")" = "$AR_TO" ] || { say "!! [3/8] the edited scratch copy is not its predicted bytes - nothing installed"; clean; exit 1; }
\cp -p built/clinic_papers.py "$SCR/live/assetapp/clinic_papers.py"
"$SPY" -m py_compile apply_s466.py walk_s466.py figure_s466.py built/clinic_papers.py "$SCR/live/assetapp/asset_register.py" 2>/dev/null || { say "!! [3/8] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/8] the three edits apply to a scratch copy and give the predicted bytes; everything compiles"

WOUT="$( cd /tmp && SHARED_LIB_DIR="$SHARED" timeout 900 "$SPY" -B "$KDIR/walk_s466.py" --apply "$KDIR/apply_s466.py" --module "$KDIR/built/clinic_papers.py" --assetapp "$AST" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^  NOTE|^WALK_S466' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S466 GREEN" || { say "!! [4/8] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
say "[4/8] walk green: the card and its save, every refusal, who may ask, Renewals for the owner and (unchanged) for the manager, /api/due byte for byte the same, the guard, the half-way state"

copydb "$ADB" "$SCR/live/assets.db" && mkdir -p "$SCR/live/uploads" || { say "!! [5/8] no copy of assets.db for the real-papers check - nothing installed"; clean; exit 1; }
FOUT="$( cd /tmp && S466_ROOT="$SCR" SHARED_LIB_DIR="$SHARED" ASSETS_DB="$SCR/live/assets.db" ASSETS_UPLOADS="$SCR/live/uploads" SARVAM_API_KEY="" FINANCE_LOCAL_URL="http://127.0.0.1:9" FINANCE_DB_FOR_SCANS="$SCR/no_finance.db" timeout 300 "$SPY" -B "$KDIR/figure_s466.py" "$SCR/live/assetapp" 2>&1 )"
echo "$FOUT" | grep -E '^FIGURE_S466' | cut -c1-900 | sed 's/^/   /'
echo "$FOUT" | grep -q "^FIGURE_S466 OK" || { say "!! [5/8] the real-papers check is red - nothing installed"; echo "$FOUT" | tail -20 | cut -c1-400; clean; exit 1; }
[ "$(m5 "$AST/asset_register.py")" = "$AR_FROM" ] && [ "$(m5 "$AST/clinic_papers.py")" = "$CP_FROM" ] || { say "!! [5/8] a live file changed during the checks - nothing installed"; clean; exit 1; }
say "[5/8] the real papers: every page opens on a copy of assets.db (the copy is removed at the end)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the real-papers check green; NOTHING placed, nothing restarted"; clean; exit 0; fi

BA="$AST/asset_register.py.bak_S466_$(echo "$AR_FROM" | cut -c1-8)"; BC="$AST/clinic_papers.py.bak_S466_$(echo "$CP_FROM" | cut -c1-8)"; BD="$AST/assets.db.bak_S466_$STAMP"
\cp -p "$AST/asset_register.py" "$BA" && [ "$(m5 "$BA")" = "$AR_FROM" ] || { say "!! [6/8] the backup of asset_register.py failed - nothing placed"; clean; exit 1; }
\cp -p "$AST/clinic_papers.py" "$BC" && [ "$(m5 "$BC")" = "$CP_FROM" ] || { say "!! [6/8] the backup of clinic_papers.py failed - nothing placed"; clean; exit 1; }
copydb "$ADB" "$BD" || { say "!! [6/8] the copy of assets.db failed - nothing placed"; clean; exit 1; }
say "[6/8] backups: $BA · $BC · $BD"
restore() {
  say "!! RED after placing ($1) - restoring"
  \cp -p "$BA" "$AST/asset_register.py"; \cp -p "$BC" "$AST/clinic_papers.py"
  systemctl restart assetapp 2>/dev/null || true; sleep 6
  say "   asset_register.py $(m5 "$AST/asset_register.py") · clinic_papers.py $(m5 "$AST/clinic_papers.py") · asset app login $(health "$ASTURL/login") (the one new table, if it was made, is harmless; the database copy is $BD)"
  clean; exit 1
}
# both files go in by a rename, so neither is ever half-written; owner and mode are the old files' own
\cp -p "$AST/clinic_papers.py" "$AST/.clinic_papers.py.s466" && cat built/clinic_papers.py > "$AST/.clinic_papers.py.s466" && [ "$(m5 "$AST/.clinic_papers.py.s466")" = "$CP_TO" ] || { say "!! [7/8] could not stage clinic_papers.py - nothing placed"; clean; exit 1; }
\cp -p "$AST/asset_register.py" "$AST/.asset_register.py.s466" && cat "$SCR/live/assetapp/asset_register.py" > "$AST/.asset_register.py.s466" && [ "$(m5 "$AST/.asset_register.py.s466")" = "$AR_TO" ] || { say "!! [7/8] could not stage asset_register.py - nothing placed"; clean; exit 1; }
mv -f "$AST/.clinic_papers.py.s466" "$AST/clinic_papers.py" || restore "placing clinic_papers.py"
mv -f "$AST/.asset_register.py.s466" "$AST/asset_register.py" || restore "placing asset_register.py"
[ "$(m5 "$AST/asset_register.py")" = "$AR_TO" ] && [ "$(m5 "$AST/clinic_papers.py")" = "$CP_TO" ] || restore "md5 read-back"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart assetapp || restore "restart assetapp"
sleep 6
systemctl is-active --quiet assetapp || restore "assetapp not active"
a0=$(health "$ASTURL/healthz"); [ "$a0" = 200 ] || restore "asset app healthz $a0"
a1=$(health "$ASTURL/login"); [ "$a1" = 200 ] || restore "asset app login $a1"
a2=$(health "$ASTURL/intake"); case "$a2" in 302|401) ;; *) restore "/intake answered $a2 without a login";; esac
a3=$(health "$ASTURL/scan/widget.js"); [ "$a3" = 200 ] || restore "widget.js $a3"
a4=$(health "$ASTURL/papers"); case "$a4" in 302|401) ;; *) restore "/papers answered $a4 without a login (404 = clinic_papers did not mount)";; esac
a5=$(health -X POST "$ASTURL/papers/1/warranty"); case "$a5" in 302|401) ;; *) restore "the warranty address answered $a5 without a login (404 = it did not mount)";; esac
a6=$(health "$ASTURL/renewals"); case "$a6" in 302|401) ;; *) restore "/renewals answered $a6 without a login";; esac
journalctl -u assetapp --since "$T0" --no-pager 2>/dev/null | grep -q "clinic_papers NOT mounted" && restore "clinic_papers NOT mounted"
JR="$(journalctl -u assetapp --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')"
[ "${JR:-0}" = 0 ] || restore "assetapp journal: $JR error line(s)"
TBL="$("$SPY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); print('yes' if c.execute(\"SELECT 1 FROM sqlite_master WHERE name='d664_warranty'\").fetchone() else 'no')" "$ADB" 2>/dev/null)"
[ "$TBL" = yes ] || restore "the table d664_warranty was not made"
say "[7/8] placed, both md5s read back = the kit's pins · assetapp active · healthz 200 · login 200 · /intake $a2, /papers $a4, the warranty address $a5 and /renewals $a6 (the login gate) · widget.js 200 · clinic_papers mounted · d664_warranty is there · journal clean"
say "[8/8] open a Dr MK expense paper from https://followup.dr-manoj.in/scanapp/bills  -> 'Warranty: not noted · note it'; it then shows on https://followup.dr-manoj.in/scanapp/renewals"
clean
say "all green -- $KIT: DONE."
md5sum "$AST/asset_register.py" "$AST/clinic_papers.py"
