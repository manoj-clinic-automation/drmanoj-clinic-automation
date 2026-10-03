#!/bin/bash
# =============================================================================
# install_S465_PAPERS_JOIN.sh -- session 292, 03-Oct-2026 -- D664, at the owner's word: "build."  Slice 2 of 3.
# ONE PURCHASE, ONE PDF: a bill, its warranty card and its second page were scanned as three papers; the owner or the
# manager now joins them. The bill keeps its number; each joined page keeps its own number and reads "a page of B-xxxx";
# the PDFs become one NEW file (the originals stay on disk); "Undo the last join" puts everything back.
# AND THE SUGGESTIONS, AS THE FIRST 29 REAL PAPERS TAUGHT THEM: medicine bills on the clinic lane are named a Pharmacy
# purchase; "DHL 8*10" is X-ray film; Yuvika's and Agarwal Surgicals' handwritten slips are Procedure room even when the
# reading is garbled (and Agarwal Surgicals' name now matches at all -- F-710).
#   REPLACE /root/assetapp/clinic_papers.py   46cfdf8c (S464.1) -> this kit's (S465.1)
#   EDIT    /root/assetapp/asset_register.py  6dd5f3ab (S464) -> b0e0915e, by apply_s465.py: ONE line, S464's own line on
#           the bill page ("join pages" beside the group; on every lane but the pharmacy's)
#   DATABASE  ONE new table, d664_join (what was joined, for the undo), made by the app at start. assets.db copied first.
#   NOT TOUCHED: the lanes and how each lands, the intake, scanner_widget.js, shared/scan_checks_s441.py (its PDF merge is
#           called, not changed), the pharmacy hand-over and every pharmacy scan, every finance file.
# Walked first, on this box (old / new / new-without-the-module / new-with-S464's-module, each on an empty database with made-up papers and tiny
# made-up PDFs). Then THE REAL PAPERS: the edited app is pointed at a COPY of assets.db, and ONE REAL JOIN is rehearsed
# there on copies of two of the scanner's own PDFs, counted, and undone. The live uploads folder is only read.
# Restarts assetapp only. Red after placing -> both old files are put back. DRY=1 places nothing.
# =============================================================================
set -u
KIT="S465_PAPERS_JOIN"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; AST="$ROOT/assetapp"; ADB="${ASSETS_DB_LIVE:-$AST/assets.db}"
SHARED="${SHARED_LIB_DIR:-$ROOT/shared}"
ASTURL="${ASTURL:-http://127.0.0.1:8030}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
AR_FROM=6dd5f3abb3aa1e9be801028fdd6e40d2; AR_TO=b0e0915e0b73a6ffb1f4a6e17aec8274
CP_FROM=46cfdf8c46e90f0a70ff544a2a304529
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="/tmp/s465_scratch_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$SCR" "$AST/.asset_register.py.s465" "$AST/.clinic_papers.py.s465"; }
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
[ "$HAVE" = "$AR_FROM" ] || { say "!! [2/8] $AST/asset_register.py is $HAVE, not $AR_FROM (S464) - another kit changed it after this one was built. Nothing installed; tell the assistant, the kit is rebuilt on the new file."; exit 1; }
[ "$HAVECP" = "$CP_FROM" ] || { say "!! [2/8] $AST/clinic_papers.py is ${HAVECP:-absent}, not $CP_FROM (S464.1) - nothing installed; tell the assistant."; exit 1; }
[ -f "$ADB" ] || { say "!! [2/8] $ADB is not there - nothing installed"; exit 1; }
[ -f "$SHARED/scan_checks_s441.py" ] || { say "!! [2/8] $SHARED/scan_checks_s441.py is not there (its PDF merge is what joins the pages) - nothing installed"; exit 1; }
UP="${ASSETS_UPLOADS_LIVE:-$(systemctl show assetapp -p Environment --value 2>/dev/null | tr ' ' '\n' | sed -n 's/^ASSETS_UPLOADS=//p' | head -1)}"; UP="${UP:-$AST/uploads}"
[ -d "$UP" ] || { say "!! [2/8] the uploads folder $UP is not there - nothing installed"; exit 1; }
say "[2/8] both files at their S464 pins; the shared PDF merge is there; uploads folder $UP"

mkdir -p "$SCR/live/assetapp" && \cp -p "$AST/asset_register.py" "$AST/scanner_widget.js" "$SCR/live/assetapp/" || { say "!! [3/8] no scratch copy - nothing installed"; clean; exit 1; }
"$SPY" -B apply_s465.py "$SCR/live/assetapp/asset_register.py" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/8] the edit did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
[ "$(m5 "$SCR/live/assetapp/asset_register.py")" = "$AR_TO" ] || { say "!! [3/8] the edited scratch copy is not its predicted bytes - nothing installed"; clean; exit 1; }
\cp -p built/clinic_papers.py "$SCR/live/assetapp/clinic_papers.py"
"$SPY" -m py_compile apply_s465.py walk_s465.py figure_s465.py built/clinic_papers.py "$SCR/live/assetapp/asset_register.py" 2>/dev/null || { say "!! [3/8] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/8] the one edit applies to a scratch copy and gives the predicted bytes; everything compiles"

WOUT="$( cd /tmp && SHARED_LIB_DIR="$SHARED" timeout 900 "$SPY" -B "$KDIR/walk_s465.py" --apply "$KDIR/apply_s465.py" --module "$KDIR/built/clinic_papers.py" --assetapp "$AST" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^  NOTE|^WALK_S465' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S465 GREEN" || { say "!! [4/8] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
say "[4/8] walk green: the join and its undo (page counts read off the PDFs), every refusal, who may ask, the corrected suggestions, the guard, the pharmacy scans untouched"

copydb "$ADB" "$SCR/live/assets.db" && mkdir -p "$SCR/live/uploads" || { say "!! [5/8] no copy of assets.db for the real-papers check - nothing installed"; clean; exit 1; }
FOUT="$( cd /tmp && S465_ROOT="$SCR" S465_LIVE_UPLOADS="$UP" SHARED_LIB_DIR="$SHARED" ASSETS_DB="$SCR/live/assets.db" ASSETS_UPLOADS="$SCR/live/uploads" SARVAM_API_KEY="" FINANCE_LOCAL_URL="http://127.0.0.1:9" FINANCE_DB_FOR_SCANS="$SCR/no_finance.db" timeout 300 "$SPY" -B "$KDIR/figure_s465.py" "$SCR/live/assetapp" 2>&1 )"
echo "$FOUT" | grep -E '^FIGURE_S465' | cut -c1-900 | sed 's/^/   /'
echo "$FOUT" | grep -q "^FIGURE_S465 OK" || { say "!! [5/8] the real-papers check is red - nothing installed"; echo "$FOUT" | tail -20 | cut -c1-400; clean; exit 1; }
[ "$(m5 "$AST/asset_register.py")" = "$AR_FROM" ] && [ "$(m5 "$AST/clinic_papers.py")" = "$CP_FROM" ] || { say "!! [5/8] a live file changed during the checks - nothing installed"; clean; exit 1; }
say "[5/8] the real papers: every page opens on a copy of assets.db (the copy and the copied scans are removed at the end)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the real-papers check green; NOTHING placed, nothing restarted"; clean; exit 0; fi

BA="$AST/asset_register.py.bak_S465_$(echo "$AR_FROM" | cut -c1-8)"; BC="$AST/clinic_papers.py.bak_S465_$(echo "$CP_FROM" | cut -c1-8)"; BD="$AST/assets.db.bak_S465_$STAMP"
\cp -p "$AST/asset_register.py" "$BA" && [ "$(m5 "$BA")" = "$AR_FROM" ] || { say "!! [6/8] the backup of asset_register.py failed - nothing placed"; clean; exit 1; }
\cp -p "$AST/clinic_papers.py" "$BC" && [ "$(m5 "$BC")" = "$CP_FROM" ] || { say "!! [6/8] the backup of clinic_papers.py failed - nothing placed"; clean; exit 1; }
copydb "$ADB" "$BD" || { say "!! [6/8] the copy of assets.db failed - nothing placed"; clean; exit 1; }
say "[6/8] backups: $BA · $BC · $BD"
restore() {
  say "!! RED after placing ($1) - restoring"
  \cp -p "$BA" "$AST/asset_register.py"; \cp -p "$BC" "$AST/clinic_papers.py"
  systemctl restart assetapp 2>/dev/null || true; sleep 6
  say "   asset_register.py $(m5 "$AST/asset_register.py") · clinic_papers.py $(m5 "$AST/clinic_papers.py") · asset app login $(health "$ASTURL/login") (the one new table, if it was made, is empty and harmless; the database copy is $BD)"
  clean; exit 1
}
# both files go in by a rename, so neither is ever half-written; owner and mode are the old files' own
\cp -p "$AST/clinic_papers.py" "$AST/.clinic_papers.py.s465" && cat built/clinic_papers.py > "$AST/.clinic_papers.py.s465" && [ "$(m5 "$AST/.clinic_papers.py.s465")" = "$CP_TO" ] || { say "!! [7/8] could not stage clinic_papers.py - nothing placed"; clean; exit 1; }
\cp -p "$AST/asset_register.py" "$AST/.asset_register.py.s465" && cat "$SCR/live/assetapp/asset_register.py" > "$AST/.asset_register.py.s465" && [ "$(m5 "$AST/.asset_register.py.s465")" = "$AR_TO" ] || { say "!! [7/8] could not stage asset_register.py - nothing placed"; clean; exit 1; }
mv -f "$AST/.clinic_papers.py.s465" "$AST/clinic_papers.py" || restore "placing clinic_papers.py"
mv -f "$AST/.asset_register.py.s465" "$AST/asset_register.py" || restore "placing asset_register.py"
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
a5=$(health "$ASTURL/papers/1/join"); case "$a5" in 302|401) ;; *) restore "/papers/1/join answered $a5 without a login (404 = the join did not mount)";; esac
journalctl -u assetapp --since "$T0" --no-pager 2>/dev/null | grep -q "clinic_papers NOT mounted" && restore "clinic_papers NOT mounted"
JR="$(journalctl -u assetapp --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')"
[ "${JR:-0}" = 0 ] || restore "assetapp journal: $JR error line(s)"
TBL="$("$SPY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); print('yes' if c.execute(\"SELECT 1 FROM sqlite_master WHERE name='d664_join'\").fetchone() else 'no')" "$ADB" 2>/dev/null)"
[ "$TBL" = yes ] || restore "the table d664_join was not made"
say "[7/8] placed, both md5s read back = the kit's pins · assetapp active · healthz 200 · login 200 · /intake $a2, /papers $a4 and the join $a5 (the login gate) · widget.js 200 · clinic_papers mounted · d664_join is there · journal clean"
say "[8/8] open it: https://followup.dr-manoj.in/scanapp/papers   (a scan with nothing read on it now says which bill it follows, with 'Join into B-xxxx')"
clean
say "all green -- $KIT: DONE."
md5sum "$AST/asset_register.py" "$AST/clinic_papers.py"
