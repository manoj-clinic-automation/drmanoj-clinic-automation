#!/bin/bash
# =============================================================================
#  install_S484_SPINE_BILL_TIES.sh · kit S484_SPINE_BILL_TIES (Sanjeevni, session 295, 05-Oct-2026; F-734, F-735, F-736; F-737 recorded)
#  The spine ties a bill number two suppliers share, orders same-second exports by what they are, and takes S483's two reader edits.
#
#  Run by (on the VPS, holding the build lock /root/deploy/.claude_code_build.lock with owner S484_SPINE_BILL_TIES):
#    bash <kit>/install_S484_SPINE_BILL_TIES.sh       (DRY=1: every gate, both builds, both compiles and the whole walk; nothing placed.)
#
#  PATCHED ON THE BOX from the live bytes (every anchor exactly once; FROM -> TO pinned), TWO files:
#     /root/finance/spine/spine_build.py   ce99bedf -> PINS.sh   (make_s484.py: five sites)
#     /root/finance/spine/marg_read.py     099d6213 -> 96f565a8  (make_s484_reader.py = S483's make_s483.py, the same bytes)
#  TWO READINGS the old reader wrote (readings/de92f5d5….json 0af44311, f62cc9e3….json b054e6c8) are removed with .bak_S484_<md5-8>
#  copies beside them; spine_evidence.py writes them again with the mended reader.
#  RESTARTS clinic-finance once (reports_tile.py imports marg_read to certify a kept file). Then the spine's own job is run once, by
#  hand, exactly as the crontab spells it, under flock -n /tmp/spine.lock, appending to spine.log as the cron does -- and the gate's
#  line is read back. The build swaps spine.db by itself when its gate passes; this kit never writes it.
#  DATA: finance.db is not written (backed up all the same, by the backup API -- the rulebook's rule 6).
#  NOT TOUCHED (md5 before = after, or the install is undone): spine_evidence.py, spine_read.py, selftest_spine.py, spine_rules.json,
#  reports_tile.py, finance_app.py, the crontab.
# =============================================================================
set -u
KIT="S484_SPINE_BILL_TIES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; SP="$FIN/spine"; ING=/root/marg_ingest
DBF="${FINANCE_DB:-$FIN/finance.db}"
ORDER=(spine_build.py marg_read.py)
declare -A FROM=( [spine_build.py]=ce99bedf60194a84fe93455927a336e2 [marg_read.py]=099d621315f3bf9297a9b4626a5caee5 )
declare -A TO
RD1="$SP/readings/de92f5d5185646d4de563e30d5464f6e.json"; R1_FROM=0af44311254ecad7603e243faff743f8
RD2="$SP/readings/f62cc9e3d93c692f1795229be9e7cfe1.json"; R2_FROM=b054e6c826902234c0af98524de29450
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s484_walk_$STAMP"
SVC=clinic-finance
declare -A RO=( [$SP/spine_evidence.py]=0fcf6c6419d5a69d7314e152421a2aa7 [$SP/spine_read.py]=712a1e4ef827f6be4e8b23415c3ceb62
                [$SP/selftest_spine.py]=fc63d2c683a1970c58f60502302187a9 )
NOTT=("$SP/spine_evidence.py" "$SP/spine_read.py" "$SP/selftest_spine.py" "$SP/spine_rules.json" "$FIN/reports_tile.py" "$FIN/finance_app.py")
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
spine_now() { "$SPY" -c "
import sqlite3,sys,collections
try:
    c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True)
    m=dict(c.execute('SELECT key,value FROM sp_meta'))
    src=collections.Counter(r[0][:8] for r in c.execute(\"SELECT source_md5 FROM sp_purchase_line WHERE date BETWEEN '2026-09-01' AND '2026-10-03'\"))
    sep=c.execute(\"SELECT COUNT(*) FROM sp_purchase_line WHERE date BETWEEN '2026-09-01' AND '2026-09-30'\").fetchone()[0]
    b=[(r[0][:4],r[1],r[2]) for r in c.execute(\"SELECT supkey,COUNT(*),SUM(net_amount_p) FROM sp_purchase_line WHERE date='2026-09-01' AND ltrim(bill,'0')='160' GROUP BY supkey ORDER BY 2\")]
    g=c.execute('SELECT SUM(ok),COUNT(*) FROM sp_gate WHERE blocking=1').fetchone()
    print('built=%s build_version=%s gate=%s/%s exports=%s | purchase lines 01-Sep..03-Oct: %s by source %s; September: %s | bill 160 of 01-Sep: %s' % (
        m.get('built'), m.get('build_version'), g[0], g[1], c.execute('SELECT COUNT(*) FROM sp_export').fetchone()[0], sum(src.values()), dict(src), sep, b))
except Exception as e:
    print('unreadable (%s: %s)' % (e.__class__.__name__, e))
" "$SP/spine.db"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/12] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/12] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$VPY" -c "import flask" 2>/dev/null || { say "!! [1/12] the venv python lacks flask; nothing installed"; exit 1; }
for k in "$DBF" "$SP/spine.db" "$SP/spine_rules.json" "$ING/xlrd/__init__.py"; do
  [ -f "$k" ] || { say "!! [1/12] $k must be reachable - nothing installed"; exit 1; }
done
. "$KDIR/PINS.sh" || { say "!! [1/12] PINS.sh missing - nothing installed"; exit 1; }
for f in "${!RO[@]}"; do
  [ "$(m5 "$f")" = "${RO[$f]}" ] || { say "!! [1/12] $f is $(m5 "$f"), not the brief's pin ${RO[$f]} (read only here) - nothing installed"; exit 1; }
done
[ -e "$FIN/_off/ALL_OFF" ] || [ -e "$SP/OFF" ] && { say "!! [1/12] an OFF switch is set ($FIN/_off/ALL_OFF or $SP/OFF): the spine would not build - nothing installed"; exit 1; }
say "[1/12] kit gates green (SUMS, KIT_ID, the venv's flask, the database, the spine's files; spine_evidence.py, spine_read.py and selftest_spine.py at the brief's pins; no OFF switch)"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "$SP/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then
  say "-- ALREADY INSTALLED: both files are at the kit's pins; $SVC $(systemctl is-active "$SVC"); healthz $(health http://127.0.0.1:8106/finance/healthz)"
  say "   spine_state.json: $(state_now)"; say "   spine.db: $(spine_now)"; say "   $(basename "$RD1"): $(reading_now "$RD1")"; say "   $(basename "$RD2"): $(reading_now "$RD2")"; exit 0
fi
for f in "${ORDER[@]}"; do
  [ "$(m5 "$SP/$f")" = "${FROM[$f]}" ] || { say "!! [2/12] $SP/$f is $(m5 "$SP/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }
done
[ "$(m5 "$RD1")" = "$R1_FROM" ] && [ "$(m5 "$RD2")" = "$R2_FROM" ] || { say "!! [2/12] the two readings are $(m5 "$RD1") / $(m5 "$RD2"), not the brief's $R1_FROM / $R2_FROM - nothing installed"; exit 1; }
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"
say "[2/12] spine_build.py, marg_read.py and the two readings at their FROM pins"
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s484.py --spine "$SP" --out "$WALK/built" | sed 's/^/   /'
"$SPY" -B make_s484_reader.py --spine "$SP" --out "$WALK/built" | sed 's/^/   /'
for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/12] the built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
say "[3/12] live bytes + anchored edits give the two pinned files (marg_read.py comes out S483's 96f565a8, as the brief requires)"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && for f in "${ORDER[@]}"; do cp -p "$WALK/built/$f" "$WALK/cc/built_$f"; done
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || { say "!! [4/12] compile on both pythons failed - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK/cc/__pycache__"
say "[4/12] compiles on /usr/bin/python3 and the venv python (a scratch copy)"
R="$WALK/run"
for side in new old; do
  mkdir -p "$R/$side" && cp -p "$SP"/*.py "$SP"/*.json "$R/$side/" || { say "!! [5/12] no scratch copy of the spine folder - nothing installed"; rm -rf "$WALK"; exit 1; }
  rm -f "$R/$side/spine_state.json"
done
for f in "${ORDER[@]}"; do cp -p "$WALK/built/$f" "$R/new/$f"; done
copydb "$DBF" "$R/scratch.db" || { say "!! [5/12] no scratch copy of finance.db - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[5/12] scratch copies: the spine folder twice (NEW with the two built files, OLD as it is), finance.db by the backup API"
WOUT="$( cd "$R" && timeout 3000 "$VPY" -B "$KDIR/walk_s484.py" --work "$R/w" --spine-new "$R/new" --spine-old "$R/old" --readings "$SP/readings" \
         --archive "$ING/archive" --ingest "$ING" --fin "$FIN" --db "$R/scratch.db" --live-db "$SP/spine.db" 2>&1 )"
echo "$WOUT" | cut -c1-1500 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S484 GREEN" || { say "!! [6/12] walk_s484 red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[6/12] walk_s484 sections 1-6 green on scratch copies; every named control red on the old file (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed, nothing written"; rm -rf "$WALK"; exit 0; fi
[ -d "$LOCK" ] && [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/12] the build lock is not held by $KIT - nothing installed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do [ "$(m5 "$SP/$f")" = "${FROM[$f]}" ] || { say "!! [7/12] $SP/$f moved during the walk - nothing installed"; rm -rf "$WALK"; exit 1; }; done
[ "$(m5 "$RD1")" = "$R1_FROM" ] && [ "$(m5 "$RD2")" = "$R2_FROM" ] || { say "!! [7/12] a reading moved during the walk - nothing installed"; rm -rf "$WALK"; exit 1; }
copydb "$DBF" "$FIN/finance.db.bak_S484_$STAMP" && [ -s "$FIN/finance.db.bak_S484_$STAMP" ] || { say "!! [7/12] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do
  BAK[$f]="$SP/$f.bak_S484_${FROM[$f]:0:8}"
  \cp -p "$SP/$f" "${BAK[$f]}" && [ "$(m5 "${BAK[$f]}")" = "${FROM[$f]}" ] || { say "!! [7/12] the backup of $f does not read back - nothing placed"; rm -rf "$WALK"; exit 1; }
done
B1="$RD1.bak_S484_${R1_FROM:0:8}"; B2="$RD2.bak_S484_${R2_FROM:0:8}"
\cp -p "$RD1" "$B1" && [ "$(m5 "$B1")" = "$R1_FROM" ] && \cp -p "$RD2" "$B2" && [ "$(m5 "$B2")" = "$R2_FROM" ] || { say "!! [7/12] the copies of the two readings do not read back - nothing placed"; rm -rf "$WALK"; exit 1; }
say "   before: $(basename "$RD1")  $(reading_now "$RD1")"
say "   before: $(basename "$RD2")  $(reading_now "$RD2")"
say "   before: spine_state.json  $(state_now)"
say "   before: spine.db  $(stat -c '%y' "$SP/spine.db" | cut -c1-19)  $(spine_now)"
say "[7/12] the lock is held by $KIT; finance.db.bak_S484_$STAMP made (backup API; the kit writes no row); a .bak_S484_<from8> beside each of the two files and each of the two readings, read back"
putfile() { \cp -p "$1" "$2.s484_new" && mv -f "$2.s484_new" "$2"; }      # a rename: the ten-minute job never reads half a file
restore() {
  say "!! RED after placing ($1) - restoring byte-identically"
  for f in "${ORDER[@]}"; do putfile "${BAK[$f]}" "$SP/$f"; done
  \cp -p "$B1" "$RD1"; \cp -p "$B2" "$RD2"
  systemctl restart "$SVC" || true; sleep 8
  for f in "${ORDER[@]}"; do say "   $SP/$f $(m5 "$SP/$f") (FROM ${FROM[$f]})"; done
  say "   the two readings $(m5 "$RD1") / $(m5 "$RD2") (FROM $R1_FROM / $R2_FROM)"
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC") · spine.db is whatever the spine's own gate last let through: $(stat -c '%y' "$SP/spine.db" | cut -c1-19)"
  rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do putfile "$WALK/built/$f" "$SP/$f" || restore "copy $f"; done
for f in "${ORDER[@]}"; do [ "$(m5 "$SP/$f")" = "${TO[$f]}" ] || restore "md5 read-back of $f"; done
say "[8/12] both files placed, each by a rename; md5 read back = the two TO pins"
rm -f "$RD1" "$RD2" || restore "the two readings could not be removed"
say "[9/12] the two readings removed from the store (their .bak_S484 copies are not read by anything: they do not end in .json)"
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
# ---- the spine's own job, once, as the crontab spells it, under its lock (flock -n: when the ten-minute job holds it, try again), into its log
L0="$(wc -l < "$SP/spine.log")"; rc=1; tries=0
while [ "$tries" -lt 20 ]; do
  tries=$((tries + 1))
  ( cd "$SP" && flock -n /tmp/spine.lock sh -c "$VPY -B spine_evidence.py && $VPY -B spine_build.py --readings readings --out spine.db --finance-db /root/finance/finance.db" >> "$SP/spine.log" 2>&1 ); rc=$?
  [ "$(wc -l < "$SP/spine.log")" -gt "$L0" ] && break                # the job ran (it wrote its lines); a busy lock writes nothing
  sleep 15
done
NEWL="$(tail -n +"$((L0 + 1))" "$SP/spine.log")"
echo "$NEWL" | grep 'de92f5d5\|f62cc9e3\|spine_evidence 20\|^  FAIL \|SPINE BUILT\|GATE FAILED\|re-add to the bill' | cut -c1-260 | sed 's/^/   spine.log: /'
say "   exit $rc after $tries try(s) · spine_state.json  $(state_now)"
say "   after : $(basename "$RD1") $(m5 "$RD1")  $(reading_now "$RD1")"
say "   after : $(basename "$RD2") $(m5 "$RD2")  $(reading_now "$RD2")"
say "   after : spine.db  $(stat -c '%y' "$SP/spine.db" | cut -c1-19)  $(spine_now)"
if echo "$NEWL" | grep -q "^SPINE BUILT AND SWAPPED"; then
  say "[11/12] THE GATE PASSES AND spine.db IS SWAPPED -- the spine builds again (its own line, the state file's clock time and the new spine's own figures are above)"
elif echo "$NEWL" | grep -qF "FAIL $G_PUR" || echo "$NEWL" | grep -qF "FAIL $G_CAT"; then
  restore "the gate still fails on a line this kit mends"
elif [ ! -f "$RD1" ] || [ ! -f "$RD2" ]; then
  say "[11/12] NOT CONFIRMED NOW: spine_evidence.py did not write both readings in this run (exit $rc: Drive, or the lock stayed busy) -- the mended files stay; the next ten-minute run writes them and builds. Read spine.log after it."
else
  say "[11/12] NOT SWAPPED, for a reason that is not this kit's: both readings are written and the two mended gate lines pass; the lines that fail are above. The mended files stay."
fi
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz at the end"
for f in "${ORDER[@]}"; do md5sum "$SP/$f" "${BAK[$f]}"; done
rm -rf "$WALK"
say "[12/12] done · healthz 200 · nothing else moved (spine_evidence.py, spine_read.py, selftest_spine.py, spine_rules.json, reports_tile.py, the crontab) · backups: a .bak_S484_<from8> beside both files and both readings, $FIN/finance.db.bak_S484_$STAMP"
say "$KIT: DONE"
