#!/bin/bash
# =============================================================================
#  install_S483_SPINE_READS_TEXT.sh · kit S483_SPINE_READS_TEXT (Sanjeevni, session 295, 05-Oct-2026; F-734, F-735)
#  The spine's reader takes the two text-made sheets that froze its build on 05-Oct: a date-only row is a DATE wherever its one
#  cell sits (the BILL/ITEM WISE purchase statement), and a heading may carry ONE short code beside its name (the category list).
#
#  Run by (on the VPS, holding the build lock /root/deploy/.claude_code_build.lock with owner S483_SPINE_READS_TEXT):
#    bash <kit>/install_S483_SPINE_READS_TEXT.sh      (DRY=1: every gate, the build, both compiles and the whole walk; nothing placed.)
#
#  PATCHED ON THE BOX from the live bytes (make_s483.py; every anchor exactly once; FROM -> TO pinned), ONE file:
#     /root/finance/spine/marg_read.py   099d6213 -> the kit's pin (PINS.sh)
#  TWO READINGS the old reader wrote (/root/finance/spine/readings/de92f5d5….json, f62cc9e3….json) are removed with .bak_S483 copies
#  beside them; spine_evidence.py writes them again with the mended reader.
#  RESTARTS clinic-finance once (reports_tile.py imports marg_read to certify a kept file). Then the spine's own job is run once, by
#  hand, exactly as the crontab spells it and under its lock (/tmp/spine.lock), appending to spine.log as the cron does -- and the
#  gate's line is read back. The build swaps spine.db by itself when the gate passes; this kit never writes it.
#  DATA: finance.db is not written (a backup is made all the same, by the backup API -- the rulebook's standing rule).
#  NOT TOUCHED (md5 before = after, or the install is undone): spine_build.py, spine_evidence.py, spine_read.py, selftest_spine.py,
#  spine_rules.json, reports_tile.py, finance_app.py, the crontab.
# =============================================================================
set -u
KIT="S483_SPINE_READS_TEXT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; SP="$FIN/spine"; ING=/root/marg_ingest
DBF="${FINANCE_DB:-$FIN/finance.db}"
LIVE="$SP/marg_read.py"
FROM=099d621315f3bf9297a9b4626a5caee5
RD1="$SP/readings/de92f5d5185646d4de563e30d5464f6e.json"      # the BILL/ITEM WISE purchase sheet (F-734)
RD2="$SP/readings/f62cc9e3d93c692f1795229be9e7cfe1.json"      # the whole-shop category list (F-735)
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s483_walk_$STAMP"
SVC=clinic-finance
declare -A RO=( [$SP/spine_evidence.py]=0fcf6c6419d5a69d7314e152421a2aa7 [$SP/spine_read.py]=712a1e4ef827f6be4e8b23415c3ceb62 )
NOTT=("$SP/spine_build.py" "$SP/spine_evidence.py" "$SP/spine_read.py" "$SP/selftest_spine.py" "$SP/spine_rules.json" "$FIN/reports_tile.py" "$FIN/finance_app.py")
G_PUR="every purchase line of an export that is the authority for its whole period belongs to exactly one bill"
G_CAT="every CATEGORY_WISE_ITEM_LIST export passes its own witness"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
reading_now() { "$SPY" -c "
import json,sys
try:
    d=json.load(open(sys.argv[1])); x=d.get('data') or {}
    print('ok=%s failed=%s lines=%s dated=%s items=%s code=%s read_at=%s' % (d.get('ok'), len(d.get('failed') or []), len(x.get('lines') or []) or '-',
          sum(1 for l in (x.get('lines') or []) if l.get('date')) if x.get('lines') else '-', len(x.get('items') or []) or '-', x.get('code'), d.get('read_at')))
except Exception as e:
    print('absent (%s)' % e.__class__.__name__)
" "$1"; }
state_now() { "$SPY" -c "
import json,sys
try:
    d=json.load(open(sys.argv[1])); print('at=%s gate=%s passed=%s last_success=%s failed=%s' % (d.get('at'), d.get('gate'), d.get('passed'), d.get('last_success_iso'), d.get('failed')))
except Exception as e:
    print('unreadable (%s)' % e.__class__.__name__)
" "$SP/spine_state.json"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/12] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/12] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$VPY" -c "import flask" 2>/dev/null || { say "!! [1/12] the venv python lacks flask; nothing installed"; exit 1; }
for k in "$DBF" "$SP/spine_build.py" "$SP/selftest_spine.py" "$SP/spine_rules.json" "$ING/xlrd/__init__.py"; do
  [ -f "$k" ] || { say "!! [1/12] $k must be reachable - nothing installed"; exit 1; }
done
. "$KDIR/PINS.sh" || { say "!! [1/12] PINS.sh missing - nothing installed"; exit 1; }
for f in "${!RO[@]}"; do
  [ "$(m5 "$f")" = "${RO[$f]}" ] || { say "!! [1/12] $f is $(m5 "$f"), not the brief's pin ${RO[$f]} (read only here) - nothing installed"; exit 1; }
done
say "[1/12] kit gates green (SUMS, KIT_ID, the venv's flask, the database, the spine's files; spine_evidence.py and spine_read.py at the brief's pins; spine_build.py is $(m5 "$SP/spine_build.py"), read only)"
if [ "$(m5 "$LIVE")" = "$TO" ]; then
  say "-- ALREADY INSTALLED: marg_read.py is at the kit's pin; $SVC $(systemctl is-active "$SVC"); healthz $(health http://127.0.0.1:8106/finance/healthz)"
  say "   spine_state.json: $(state_now)"; say "   $(basename "$RD1"): $(reading_now "$RD1")"; say "   $(basename "$RD2"): $(reading_now "$RD2")"; exit 0
fi
[ "$(m5 "$LIVE")" = "$FROM" ] || { say "!! [2/12] $LIVE is $(m5 "$LIVE"), not its FROM pin $FROM - someone changed it since the brief; nothing installed"; exit 1; }
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"
say "[2/12] marg_read.py at its FROM pin $FROM (the post-S482 bytes)"
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s483.py --spine "$SP" --out "$WALK/built" | sed 's/^/   /'
[ "$(m5 "$WALK/built/marg_read.py")" = "$TO" ] || { say "!! [3/12] the built marg_read.py is $(m5 "$WALK/built/marg_read.py"), not the kit's pin $TO - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/12] live bytes + anchored edits give the pinned file ($TO)"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && cp -p "$WALK/built/marg_read.py" "$WALK/cc/built_marg_read.py"
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || { say "!! [4/12] compile on both pythons failed - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK/cc/__pycache__"
say "[4/12] compiles on /usr/bin/python3 and the venv python (a scratch copy)"
R="$WALK/run"
for side in new old; do
  mkdir -p "$R/$side" && cp -p "$SP"/*.py "$SP"/*.json "$R/$side/" || { say "!! [5/12] no scratch copy of the spine folder - nothing installed"; rm -rf "$WALK"; exit 1; }
done
cp -p "$WALK/built/marg_read.py" "$R/new/marg_read.py"
copydb "$DBF" "$R/scratch.db" || { say "!! [5/12] no scratch copy of finance.db - nothing installed"; rm -rf "$WALK"; exit 1; }
SN="$( cd "$R/new" && timeout 900 "$VPY" -B selftest_spine.py 2>&1 | tail -1 )"
SO="$( cd "$R/old" && timeout 900 "$VPY" -B selftest_spine.py 2>&1 | tail -1 )"
case "$SN" in "SELFTEST OK"*) ;; *) SO="(not compared)";; esac
[ "$SN" = "$SO" ] || { say "!! [5/12] selftest_spine.py on the built reader says '$SN'; on the box as it is '$SO' - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[5/12] selftest_spine.py with the built marg_read.py (a scratch copy of the spine folder): $(echo "$SN" | cut -c1-90) -- every check passes, the same line as the box as it is"
WOUT="$( cd "$R" && timeout 3000 "$VPY" -B "$KDIR/walk_s483.py" server --work "$R/w" --spine-new "$R/new" --spine-old "$R/old" --readings "$SP/readings" \
         --archive "$ING/archive" --ingest "$ING" --fin "$FIN" --db "$R/scratch.db" 2>&1 )"
echo "$WOUT" | cut -c1-1200 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S483 server GREEN" || { say "!! [6/12] walk_s483 (server) red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[6/12] walk_s483 sections 3 and 4 green on scratch copies; the negative controls red on the old reader and the old readings (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed, nothing written"; rm -rf "$WALK"; exit 0; fi
[ -d "$LOCK" ] && [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/12] the build lock is not held by $KIT - nothing installed"; rm -rf "$WALK"; exit 1; }
[ "$(m5 "$LIVE")" = "$FROM" ] || { say "!! [7/12] marg_read.py moved during the walk - nothing installed"; rm -rf "$WALK"; exit 1; }
copydb "$DBF" "$FIN/finance.db.bak_S483_$STAMP" && [ -s "$FIN/finance.db.bak_S483_$STAMP" ] || { say "!! [7/12] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
BAK="$LIVE.bak_S483_${FROM:0:8}"
\cp -p "$LIVE" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ] || { say "!! [7/12] the backup of marg_read.py does not read back - nothing placed"; rm -rf "$WALK"; exit 1; }
R1_0="$(m5 "$RD1")"; R2_0="$(m5 "$RD2")"
say "   before: $(basename "$RD1") $R1_0  $(reading_now "$RD1")"
say "   before: $(basename "$RD2") $R2_0  $(reading_now "$RD2")"
say "   before: spine_state.json  $(state_now)"
say "   before: spine.db  $(stat -c '%y' "$SP/spine.db" | cut -c1-19)  $(m5 "$SP/spine.db")"
for rd in "$RD1" "$RD2"; do
  [ -f "$rd" ] || { say "!! [7/12] $rd is not in the store - nothing placed"; rm -rf "$WALK"; exit 1; }
  \cp -p "$rd" "$rd.bak_S483" && [ "$(m5 "$rd.bak_S483")" = "$(m5 "$rd")" ] || { say "!! [7/12] the copy of $rd does not read back - nothing placed"; rm -rf "$WALK"; exit 1; }
done
say "[7/12] the lock is held by $KIT; finance.db.bak_S483_$STAMP made (backup API; the kit writes no row); marg_read.py.bak_S483_${FROM:0:8} and a .bak_S483 copy of each of the two readings, read back"
putfile() { \cp -p "$1" "$2.s483_new" && mv -f "$2.s483_new" "$2"; }      # a rename: the ten-minute job never reads half a file
restore() {
  say "!! RED after placing ($1) - restoring byte-identically"
  putfile "$BAK" "$LIVE"
  for rd in "$RD1" "$RD2"; do \cp -p "$rd.bak_S483" "$rd"; done
  systemctl restart "$SVC" || true; sleep 8
  say "   $LIVE $(m5 "$LIVE") (FROM $FROM) · the two readings $(m5 "$RD1") / $(m5 "$RD2") (before: $R1_0 / $R2_0)"
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC") · the spine is as it was this morning (its gate fails on the same two lines)"
  rm -rf "$WALK"; exit 1
}
putfile "$WALK/built/marg_read.py" "$LIVE" || restore "copy"
[ "$(m5 "$LIVE")" = "$TO" ] || restore "md5 read-back"
say "[8/12] placed by a rename; md5 read back = $TO"
rm -f "$RD1" "$RD2" || restore "the two readings could not be removed"
say "[9/12] the two readings removed from the store (their .bak_S483 copies beside them are not read by anything: they do not end in .json)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz)
say "health : finance healthz $c1"
[ "$c1" = 200 ] || restore "finance healthz"
c=$(health http://127.0.0.1:8106/finance/reports/aaj); say "         /finance/reports/aaj $c (302/401 = the login gate, expected)"
[ "$c" = 302 ] || [ "$c" = 401 ] || restore "a gated page answered $c"
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
[ "$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')" = 0 ] || restore "$SVC journal errors"
say "[10/12] $SVC active (restarted once, $T0); healthz 200; the gated page answers the gate"
# ---- the spine's own job, once, as the crontab spells it, under its lock, into its log
L0="$(wc -l < "$SP/spine.log")"
( cd "$SP" && flock -w 600 /tmp/spine.lock sh -c "$VPY -B spine_evidence.py && $VPY -B spine_build.py --readings readings --out spine.db --finance-db /root/finance/finance.db" >> "$SP/spine.log" 2>&1 ); rc=$?
NEWL="$(tail -n +"$((L0 + 1))" "$SP/spine.log")"
echo "$NEWL" | grep 'de92f5d5\|f62cc9e3\|spine_evidence 20\|FAIL \|SPINE BUILT\|GATE FAILED' | cut -c1-260 | sed 's/^/   spine.log: /'
say "   exit $rc · spine_state.json  $(state_now)"
say "   after : $(basename "$RD1") $(m5 "$RD1")  $(reading_now "$RD1")"
say "   after : $(basename "$RD2") $(m5 "$RD2")  $(reading_now "$RD2")"
say "   after : spine.db  $(stat -c '%y' "$SP/spine.db" | cut -c1-19)  $(m5 "$SP/spine.db")"
if echo "$NEWL" | grep -q "^SPINE BUILT AND SWAPPED"; then
  say "[11/12] THE GATE PASSES AND spine.db IS SWAPPED -- the spine builds again (its own line and the state file's clock time are above)"
elif echo "$NEWL" | grep -qF "FAIL $G_PUR" || echo "$NEWL" | grep -qF "FAIL $G_CAT"; then
  restore "the gate still fails on a line this kit mends"
elif [ ! -f "$RD1" ] || [ ! -f "$RD2" ]; then
  say "[11/12] NOT CONFIRMED NOW: spine_evidence.py did not write both readings in this run (exit $rc: Drive, or the lock) -- the mended reader stays; the next ten-minute run writes them and builds. Read spine.log after it."
else
  say "[11/12] NOT SWAPPED, for a reason that is not this kit's: both readings are written and the two mended gate lines pass; the lines that fail are above. The mended reader stays."
fi
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz at the end"
md5sum "$LIVE" "$BAK"
rm -rf "$WALK"
say "[12/12] done · healthz 200 · nothing else moved (spine_build.py, spine_evidence.py, spine_read.py, reports_tile.py, the crontab) · backups: $BAK, the two readings' .bak_S483, $FIN/finance.db.bak_S483_$STAMP"
say "$KIT: DONE"
