#!/bin/bash
# =============================================================================
# install_S464_CLINIC_PAPERS.sh -- session 292, 03-Oct-2026 -- D664, at the owner's word: "build."  Slice 1 of 3.
# CLINIC CONSUMABLES GET THEIR GROUPS: a short list of clinic papers to sort (each with a suggestion from the supplier AND
# the words read on it: Yes / Change / Skip), three groups -- Procedure room, X-ray films (small / 11 x 14), Others --
# and the month by group. For the owner and the manager; the scanning staff are asked nothing new and see nothing new.
#   NEW   /root/assetapp/clinic_papers.py     everything D664 does lives here
#   EDIT  /root/assetapp/asset_register.py    446c671d (S441) -> 6dd5f3ab, by apply_s464.py (3 exact anchors): one guarded
#         import at the foot, two links on the Purchases page, one line on the bill page -- both behind 'is defined'
#   DATABASE  ONE additive column, bills.subgroup (added by the app itself at start, once). A copy of assets.db is kept first.
#   NOT TOUCHED: the lanes and how each lands, the intake, scanner_widget.js, shared/scan_checks_s441.py, the pharmacy
#         hand-over, every finance file. A move between lanes still goes through the app's own /bills/<id>/lane.
# Walked first, on this box: the app's code copied to /tmp three ways (old, new, and new WITHOUT clinic_papers.py -- the
# guard), each on an empty database of its own with made-up papers. Then THE REAL PAPERS: the edited app is pointed at a
# COPY of assets.db and every new page is opened on it (counts only are printed; the copy is removed).
# Restarts assetapp only (a few seconds; a scan in flight retries by itself). Red after placing -> the old file is put
# back and clinic_papers.py set aside. DRY=1 places nothing.
# =============================================================================
set -u
KIT="S464_CLINIC_PAPERS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; AST="$ROOT/assetapp"; ADB="${ASSETS_DB_LIVE:-$AST/assets.db}"
ASTURL="${ASTURL:-http://127.0.0.1:8030}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
AR_FROM=446c671ddc7589fa8b367c463d49cbaa; AR_TO=6dd5f3abb3aa1e9be801028fdd6e40d2
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="/tmp/s464_scratch_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$SCR" "$AST/.asset_register.py.s464" "$AST/.clinic_papers.py.s464"; }
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

HAVE="$(m5 "$AST/asset_register.py")"
if [ "$HAVE" = "$AR_TO" ] && [ "$(m5 "$AST/clinic_papers.py")" = "$CP_TO" ]; then
  say "-- ALREADY INSTALLED: both files are at the kit's pins; assetapp $(systemctl is-active assetapp 2>/dev/null)"; exit 0; fi
[ "$HAVE" = "$AR_FROM" ] || { say "!! [2/8] $AST/asset_register.py is $HAVE, not $AR_FROM - another kit changed it after this one was built. Nothing installed; tell the assistant, the kit is rebuilt on the new file."; exit 1; }
[ ! -e "$AST/clinic_papers.py" ] || [ "$(m5 "$AST/clinic_papers.py")" = "$CP_TO" ] || { say "!! [2/8] a different $AST/clinic_papers.py is already there - nothing installed"; exit 1; }
[ -f "$ADB" ] || { say "!! [2/8] $ADB is not there - nothing installed"; exit 1; }
[ -f "$AST/scanner_widget.js" ] || { say "!! [2/8] $AST/scanner_widget.js is not there - nothing installed"; exit 1; }
say "[2/8] asset_register.py at its S441 pin; no other clinic_papers.py in the way"

mkdir -p "$SCR/live/assetapp" && \cp -p "$AST/asset_register.py" "$AST/scanner_widget.js" "$SCR/live/assetapp/" || { say "!! [3/8] no scratch copy - nothing installed"; clean; exit 1; }
"$SPY" -B apply_s464.py "$SCR/live/assetapp/asset_register.py" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/8] the edits did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
[ "$(m5 "$SCR/live/assetapp/asset_register.py")" = "$AR_TO" ] || { say "!! [3/8] the edited scratch copy is not its predicted bytes - nothing installed"; clean; exit 1; }
\cp -p built/clinic_papers.py "$SCR/live/assetapp/clinic_papers.py"
"$SPY" -m py_compile apply_s464.py walk_s464.py figure_s464.py built/clinic_papers.py "$SCR/live/assetapp/asset_register.py" 2>/dev/null || { say "!! [3/8] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/8] the three edits apply to a scratch copy and give the predicted bytes; everything compiles"

WOUT="$( cd /tmp && timeout 900 "$SPY" -B "$KDIR/walk_s464.py" --apply "$KDIR/apply_s464.py" --module "$KDIR/built/clinic_papers.py" --assetapp "$AST" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^  NOTE|^WALK_S464' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S464 GREEN" || { say "!! [4/8] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
say "[4/8] walk green: the list and its suggestions, the groups, the month, who may ask, the guard with the new file absent, the pharmacy scan untouched"

copydb "$ADB" "$SCR/live/assets.db" && mkdir -p "$SCR/live/uploads" || { say "!! [5/8] no copy of assets.db for the real-papers check - nothing installed"; clean; exit 1; }
FOUT="$( cd /tmp && S464_ROOT="$SCR" ASSETS_DB="$SCR/live/assets.db" ASSETS_UPLOADS="$SCR/live/uploads" SARVAM_API_KEY="" FINANCE_LOCAL_URL="http://127.0.0.1:9" FINANCE_DB_FOR_SCANS="$SCR/no_finance.db" timeout 300 "$SPY" -B "$KDIR/figure_s464.py" "$SCR/live/assetapp" 2>&1 )"
echo "$FOUT" | grep -E '^FIGURE_S464' | cut -c1-600 | sed 's/^/   /'
echo "$FOUT" | grep -q "^FIGURE_S464 OK" || { say "!! [5/8] the new pages did not all open on a copy of the real database - nothing installed"; echo "$FOUT" | tail -20 | cut -c1-400; clean; exit 1; }
[ "$(m5 "$AST/asset_register.py")" = "$AR_FROM" ] || { say "!! [5/8] asset_register.py changed during the checks - nothing installed"; clean; exit 1; }
say "[5/8] the real papers: every new page opens on a copy of assets.db (the copy is removed at the end)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the real-papers check green; NOTHING placed, nothing restarted"; clean; exit 0; fi

BA="$AST/asset_register.py.bak_S464_$(echo "$AR_FROM" | cut -c1-8)"; BD="$AST/assets.db.bak_S464_$STAMP"
\cp -p "$AST/asset_register.py" "$BA" && [ "$(m5 "$BA")" = "$AR_FROM" ] || { say "!! [6/8] the backup failed - nothing placed"; clean; exit 1; }
copydb "$ADB" "$BD" || { say "!! [6/8] the copy of assets.db failed - nothing placed"; clean; exit 1; }
say "[6/8] backups: $BA · $BD"
restore() {
  say "!! RED after placing ($1) - restoring"
  \cp -p "$BA" "$AST/asset_register.py"
  [ -f "$AST/clinic_papers.py" ] && mv -f "$AST/clinic_papers.py" "$AST/clinic_papers.py.set_aside_S464"
  systemctl restart assetapp 2>/dev/null || true; sleep 6
  say "   asset_register.py $(m5 "$AST/asset_register.py") · asset app login $(health "$ASTURL/login") · clinic_papers.py set aside (the one new column, if it was added, is harmless and stays; the database copy is $BD)"
  clean; exit 1
}
# both files go in by a rename, so neither is ever half-written; owner and mode are asset_register.py's
\cp -p "$AST/asset_register.py" "$AST/.clinic_papers.py.s464" && cat built/clinic_papers.py > "$AST/.clinic_papers.py.s464" && [ "$(m5 "$AST/.clinic_papers.py.s464")" = "$CP_TO" ] || { say "!! [7/8] could not stage clinic_papers.py - nothing placed"; clean; exit 1; }
\cp -p "$AST/asset_register.py" "$AST/.asset_register.py.s464" && cat "$SCR/live/assetapp/asset_register.py" > "$AST/.asset_register.py.s464" && [ "$(m5 "$AST/.asset_register.py.s464")" = "$AR_TO" ] || { say "!! [7/8] could not stage asset_register.py - nothing placed"; clean; exit 1; }
mv -f "$AST/.clinic_papers.py.s464" "$AST/clinic_papers.py" || restore "placing clinic_papers.py"
mv -f "$AST/.asset_register.py.s464" "$AST/asset_register.py" || restore "placing asset_register.py"
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
a5=$(health "$ASTURL/papers/month"); case "$a5" in 302|401) ;; *) restore "/papers/month answered $a5 without a login";; esac
journalctl -u assetapp --since "$T0" --no-pager 2>/dev/null | grep -q "clinic_papers NOT mounted" && restore "clinic_papers NOT mounted"
JR="$(journalctl -u assetapp --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')"
[ "${JR:-0}" = 0 ] || restore "assetapp journal: $JR error line(s)"
COL="$("$SPY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); print('yes' if 'subgroup' in [r[1] for r in c.execute('PRAGMA table_info(bills)')] else 'no')" "$ADB" 2>/dev/null)"
[ "$COL" = yes ] || restore "bills.subgroup was not added"
say "[7/8] placed, both md5s read back = the kit's pins · assetapp active · healthz 200 · login 200 · /intake $a2, /papers $a4 and /papers/month $a5 (the login gate) · widget.js 200 · clinic_papers mounted · bills.subgroup is there · journal clean"
say "[8/8] open it: https://followup.dr-manoj.in/scanapp/papers   (also from Purchases: 'Clinic papers to sort' and 'Clinic consumables by month')"
clean
say "all green -- $KIT: DONE."
md5sum "$AST/asset_register.py" "$AST/clinic_papers.py"
