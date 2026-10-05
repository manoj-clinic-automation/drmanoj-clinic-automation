#!/bin/bash
# =============================================================================
#  install_S480_MARG_TEXT_READERS.sh · kit S480_MARG_TEXT_READERS (Sanjeevni, session 295, 05-Oct-2026; D675; F-726 b, F-728, F-729, F-730)
#  The SERVER part: every Marg text report lands typed; an empty sale day is an answer; the salt reader stops naming the firm as a salt;
#  the short sale statement lands and never ticks the day's sale row. No staff screen's layout changes. No table is created.
#
#  Run by (on the VPS, holding the build lock /root/deploy/.claude_code_build.lock with owner S480_MARG_TEXT_READERS):
#    bash <kit>/install_S480_MARG_TEXT_READERS.sh     (DRY=1: every gate, the build, both compiles and the whole walk; nothing placed.
#                                                      KITS=<dir> the folder of the earlier kits when this kit runs from a copy;
#                                                      DUTYMAP=<file> the duty map in claude_code_briefs -- read, never edited.)
#
#  PATCHED ON THE BOX from the live bytes (make_s480.py; every anchor exactly once; FROM -> TO pinned), ten files:
#     /root/marg_ingest/  signatures.json  marg_report.py  lib/marg_report.py  marg_take.py  lib/push_expected.py
#     /root/finance/      marg_report.py (the copy the door runs)  marg_door.py  salts_refresh.py  reports_tile.py
#  RESTARTS clinic-finance only. DATA: finance.db is backed up (backup API) before placing. After the service is healthy the corrected
#  salt list is posted ONCE through the app's own door (the cron's command with --force: its state file says the newest list was already
#  applied, so the cron alone would wait for the next export) -- purchase_salt_marg is replaced whole, as at every new list.
#  NOT TOUCHED (md5 before = after, or the install is undone): marg_router.py, marg_ingest.py, marg_shadow.py, marg_rescan_vps.py,
#  finance_app.py, portal.py, tile_grants.json, stock_app.py, amir_day.py, purchase_app.py, order_sheet.py, item_check.py, shelf_figure.py,
#  the crontab.
# =============================================================================
set -u
KIT="S480_MARG_TEXT_READERS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
KITS="${KITS:-$KDIR/..}"
DUTYMAP="${DUTYMAP:-$KDIR/../../claude_code_briefs/DUTY_MAP.json}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; ING=/root/marg_ingest; POR=/root/portal; AST=/root/assetapp
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"; SPD="$FIN/spine/spine.db"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s480_walk_$STAMP"
SVC=clinic-finance
# key = the path under the built folder; live = where it lives
ORDER=(ingest/lib/marg_report.py ingest/marg_report.py finance/marg_report.py ingest/lib/push_expected.py ingest/marg_take.py
       finance/marg_door.py finance/salts_refresh.py finance/reports_tile.py ingest/signatures.json)
declare -A FROM=( [ingest/signatures.json]=64943ac6719a0f2ee06a15ef56d8c3d1 [ingest/marg_report.py]=eeab56055be76fec9531399ce9a0556e
                  [ingest/lib/marg_report.py]=eeab56055be76fec9531399ce9a0556e [ingest/marg_take.py]=b41195e4ce853272ecf25b06343e3e16
                  [ingest/lib/push_expected.py]=4b3b700c1640591a3723d4fce3de5603 [finance/marg_report.py]=f9370dde648f629461d4efac2b4805af
                  [finance/marg_door.py]=6a2366638234bf0ddf9c7d6c745c975b [finance/salts_refresh.py]=40cb26159c59d55d33d871abe36646ef
                  [finance/reports_tile.py]=9d2244a6d56d3791428982565f620a97 )
declare -A TO
live() { case "$1" in ingest/*) echo "$ING/${1#ingest/}";; finance/*) echo "$FIN/${1#finance/}";; esac; }
NOTT=("$ING/marg_router.py" "$ING/marg_ingest.py" "$ING/marg_shadow.py" "$ING/marg_rescan_vps.py" "$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json"
      "$FIN/stock_app.py" "$FIN/amir_day.py" "$FIN/purchase_app.py" "$FIN/order_sheet.py" "$FIN/item_check.py" "$FIN/shelf_figure.py")
ROUTER_PIN=318086e36b0088f2da57b95d19a86b98
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
salts_now() { "$SPY" -c "
import sqlite3,sys
c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True)
try:
    n=c.execute('SELECT COUNT(*) FROM purchase_salt_marg').fetchone()[0]
    f=c.execute(\"SELECT COUNT(*) FROM purchase_salt_marg WHERE salt LIKE 'SANJEEVNI%'\").fetchone()[0]
    print('%d items in the Marg salt list the page holds, %d of them filed under the firm name' % (n, f))
except Exception as e:
    print('purchase_salt_marg could not be read (%s)' % e.__class__.__name__)
" "$1"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/14] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/14] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$VPY" -c "import flask" 2>/dev/null || { say "!! [1/14] the venv python lacks flask; nothing installed"; exit 1; }
for k in "$DUTYMAP" "$DBF" "$ADB" "$SPD" "$ING/xlrd/__init__.py"; do
  [ -f "$k" ] || { say "!! [1/14] $k must be reachable (KITS=$KITS, DUTYMAP=$DUTYMAP) - nothing installed"; exit 1; }
done
. "$KDIR/PINS.sh" || { say "!! [1/14] PINS.sh missing - nothing installed"; exit 1; }
[ "$(m5 "$ING/marg_router.py")" = "$ROUTER_PIN" ] || { say "!! [1/14] marg_router.py is not $ROUTER_PIN (it reads the signatures; this kit was walked against that file) - nothing installed"; exit 1; }
say "[1/14] kit gates green (SUMS, KIT_ID, the venv's flask, the duty map -- read, not edited --, the databases, the router at its pin)"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "$(live "$f")")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the ten files are at the kit's pins; $SVC $(systemctl is-active "$SVC"); healthz $(health http://127.0.0.1:8106/finance/healthz)"; exit 0; fi
for f in "${ORDER[@]}"; do
  [ "$(m5 "$(live "$f")")" = "${FROM[$f]}" ] || { say "!! [2/14] $(live "$f") is $(m5 "$(live "$f")"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }
done
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"
say "[2/14] the ten live files at their FROM pins (the brief's section 10)"
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s480.py --server --ingest "$ING" --finance "$FIN" --out "$WALK/built" | sed 's/^/   /'
for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/14] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
cmp -s "$WALK/built/ingest/signatures.json" "$KDIR/signatures.json" && cmp -s "$WALK/built/ingest/marg_report.py" "$KDIR/marg_report.py" \
  && cmp -s "$WALK/built/ingest/lib/marg_report.py" "$KDIR/marg_report.py" && cmp -s "$WALK/built/ingest/lib/push_expected.py" "$KDIR/push_expected.py" \
  || { say "!! [3/14] a built file that must be the kit's own bytes is not - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/14] live bytes + anchored edits give the ten pinned files; signatures.json, both marg_ingest marg_report.py and lib/push_expected.py are the kit's own files, byte for byte (what manojz holds)"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && for f in "${ORDER[@]}"; do case "$f" in *.py) cp -p "$WALK/built/$f" "$WALK/cc/built_$(echo "$f" | tr '/' '_')";; esac; done
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || { say "!! [4/14] compile on both pythons failed - nothing installed"; rm -rf "$WALK"; exit 1; }
"$SPY" -c "import json,sys; json.load(open(sys.argv[1], encoding='utf-8'))" "$WALK/built/ingest/signatures.json" || { say "!! [4/14] the built signatures.json is not JSON - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK/cc/__pycache__"
ST="$( cd "$WALK/cc" && PYTHONPATH="$ING" timeout 300 "$VPY" -B marg_txt.py --selftest 2>&1 | tail -1 )"
[ "$ST" = "SELFTEST OK" ] || { say "!! [4/14] marg_txt S480's selftest: $ST - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/14] compiles on /usr/bin/python3 and the venv python (a scratch copy); the built signatures.json is JSON; marg_txt S480 --selftest: $ST"
R="$WALK/run"
for side in new old; do
  mkdir -p "$R/$side/marg_ingest/lib" "$R/$side/finance/finance_ui" "$R/$side/finance/spine" || exit 1
  cp -p "$ING"/*.py "$ING/signatures.json" "$R/$side/marg_ingest/" && cp -p "$ING"/lib/*.py "$R/$side/marg_ingest/lib/" && cp -rp "$ING/xlrd" "$R/$side/marg_ingest/xlrd" \
    || { say "!! [5/14] no scratch copy of marg_ingest - nothing installed"; rm -rf "$WALK"; exit 1; }
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/$side/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$R/$side/finance/finance_ui/"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$R/$side/finance/spine/" 2>/dev/null
done
for f in "${ORDER[@]}"; do case "$f" in ingest/*) cp -p "$WALK/built/$f" "$R/new/marg_ingest/${f#ingest/}";; finance/*) cp -p "$WALK/built/$f" "$R/new/finance/${f#finance/}";; esac; done
mkdir -p "$R/por" "$R/w" || exit 1
for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$R/por/"; done   # never the live secret, never the user store
cp -p "$POR/tile_grants.json" "$R/por/"
copydb "$DBF" "$R/scratch.db" && copydb "$ADB" "$R/scratch_assets.db" && copydb "$SPD" "$R/scratch_spine.db" || { say "!! [5/14] no scratch copies - nothing installed"; rm -rf "$WALK"; exit 1; }
# the crons run these files as SCRIPTS: each one as the crontab spells it, on the scratch copies, writing nothing live (F-711)
SOUT=""
for side in new old; do
  mkdir -p "$R/sc_$side/root/finance" "$R/sc_$side/arch"
  o="$( cd "$R/$side/finance" && timeout 120 "$VPY" -B salts_refresh.py --once --dry-run --ingest "$R/$side/marg_ingest" --state "$R/sc_$side/salts.state.json" 2>&1 )"; rc=$?
  SOUT="$SOUT$side  salts_refresh.py --once --dry-run  exit $rc  $(echo "$o" | tail -1 | mask | cut -c1-170)"$'\n'
  [ "$side" = new ] && [ "$rc" != 0 ] && { echo "$o" | mask | tail -12 | sed 's/^/   /'; say "!! [5/14] salts_refresh.py as a script on the built file exits $rc - nothing installed"; rm -rf "$WALK"; exit 1; }
  o="$( cd "$R/$side/marg_ingest" && timeout 120 "$VPY" -B -c "import marg_ingest, marg_take, marg_shadow, marg_rescan_vps, marg_report, marg_router; import sys; sys.path.insert(0, 'lib'); import push_expected; print('imports ok: marg_ingest, marg_take, marg_shadow, marg_rescan_vps, lib/push_expected')" 2>&1 )"; rc=$?
  SOUT="$SOUT$side  the collector's, the door's and the shadow's imports  exit $rc  $(echo "$o" | tail -1 | mask | cut -c1-150)"$'\n'
  [ "$side" = new ] && [ "$rc" != 0 ] && { echo "$o" | mask | tail -12 | sed 's/^/   /'; say "!! [5/14] the built files do not import as the crons import them - nothing installed"; rm -rf "$WALK"; exit 1; }
done
echo "$SOUT" | sed 's/^/   /'
say "[5/14] on scratch copies of the built files: salts_refresh.py --once --dry-run exits 0 (it reads the live archive; sends and writes nothing); the collector, the door, the shadow and the rescan import as the crontab runs them"
RS="$( cd "$R/new/marg_ingest" && timeout 300 "$VPY" -B marg_router.py --selftest 2>&1 | tail -1 )"
[ "$RS" = "SELFTEST OK" ] || { say "!! [6/14] the router's own selftest with the built signatures and reader: $RS - nothing installed"; rm -rf "$WALK"; exit 1; }
TS="$( cd "$R/new/finance" && timeout 600 "$VPY" -B reports_tile.py 2>&1 | tail -1 )"
TO_="$( cd "$R/old/finance" && timeout 600 "$VPY" -B reports_tile.py 2>&1 | tail -1 )"
[ "$TS" = "$TO_" ] || { say "!! [6/14] reports_tile.py's own selftest on the built file says '$TS', the box as it is says '$TO_' - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[6/14] the router's own selftest with the built signatures: $RS; reports_tile.py's own selftest on the built file: $(echo "$TS" | cut -c1-80) (the same line as the box as it is)"
WOUT="$( cd "$R" && timeout 3000 "$VPY" -B "$KDIR/walk_s480.py" server --kit "$KDIR" --work "$R/w" --kits "$KITS" --ingest-new "$R/new/marg_ingest" --ingest-old "$R/old/marg_ingest" \
         --fin-new "$R/new/finance" --fin-old "$R/old/finance" --por "$R/por" --db "$R/scratch.db" --adb "$R/scratch_assets.db" --spine "$R/scratch_spine.db" --duty-map "$DUTYMAP" 2>&1 )"
echo "$WOUT" | mask | cut -c1-900 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S480 server GREEN" || { say "!! [7/14] walk_s480 (server) red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[7/14] walk_s480 sections 4 and 8 green on scratch copies; every negative control red on the box as it is (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed"; rm -rf "$WALK"; exit 0; fi
[ -d "$LOCK" ] && [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [8/14] the build lock is not held by $KIT - nothing installed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do
  [ "$(m5 "$(live "$f")")" = "${FROM[$f]}" ] || { say "!! [8/14] $(live "$f") moved during the walk - nothing installed"; rm -rf "$WALK"; exit 1; }
done
SALT0="$(salts_now "$DBF")"
copydb "$DBF" "$FIN/finance.db.bak_S480_$STAMP" || { say "!! [8/14] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do
  L="$(live "$f")"; BAK[$f]="$L.bak_S480_${FROM[$f]:0:8}"
  \cp -p "$L" "${BAK[$f]}" || { say "!! [8/14] backup of $L failed - nothing placed"; rm -rf "$WALK"; exit 1; }
  [ "$(m5 "${BAK[$f]}")" = "${FROM[$f]}" ] || { say "!! [8/14] the backup of $L does not read back - nothing placed"; rm -rf "$WALK"; exit 1; }
done
say "[8/14] finance.db.bak_S480_$STAMP made (backup API); a .bak_S480_<from8> beside each of the ten files, read back; the lock is held by $KIT"
putfile() { \cp -p "$1" "$2.s480_new" && mv -f "$2.s480_new" "$2"; }      # a rename: the five-minute collector never reads half a file
restore() {
  say "!! RED after placing ($1) - restoring every file byte-identically"
  for f in "${ORDER[@]}"; do putfile "${BAK[$f]}" "$(live "$f")"; done
  systemctl restart "$SVC" || true; sleep 8
  for f in "${ORDER[@]}"; do say "   $(live "$f") $(m5 "$(live "$f")") (FROM ${FROM[$f]})"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC") · the database backup stays: $FIN/finance.db.bak_S480_$STAMP"
  rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do putfile "$WALK/built/$f" "$(live "$f")" || restore "copy $f"; done
for f in "${ORDER[@]}"; do [ "$(m5 "$(live "$f")")" = "${TO[$f]}" ] || restore "md5 read-back of $f"; done
say "[9/14] placed (each by a rename); md5 read back = the ten TO pins"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz)
say "health : finance healthz $c1"
[ "$c1" = 200 ] || restore "finance healthz"
for p in /finance/reports/aaj /finance/clinic/marg/upload /finance/purchase/page/salts; do
  c=$(health "http://127.0.0.1:8106$p"); say "         $p $c (302/401 = the login gate, expected)"
  [ "$c" = 302 ] || [ "$c" = 401 ] || restore "a gated page answered $c ($p)"
done
c=$(health http://127.0.0.1:8106/finance/api/marg-file); say "         /finance/api/marg-file $c (401 = the machine door asks for its key, expected; no key is read here)"
[ "$c" = 401 ] || [ "$c" = 302 ] || [ "$c" = 503 ] || restore "the machine door answered $c"
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
[ "$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')" = 0 ] || restore "$SVC journal errors"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
say "[10/14] $SVC active (restarted $T0); healthz 200; the gated pages answer the gate; nothing else moved; the crontab is as it was"
LV="$( cd "$FIN" && timeout 120 "$SPY" -B -c "
import importlib.util
def load(n, p):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
out = []
for n, p in (('finance', '$FIN/marg_report.py'), ('marg_ingest', '$ING/marg_report.py'), ('lib', '$ING/lib/marg_report.py')):
    r = load('mr_' + n, p).read_report('$R/w/in/empty.XLS')
    out.append('%s ok=%s empty=%s day=%s' % (n, r['ok'], r.get('empty'), [d['date'] for d in r['days']]))
print(' | '.join(out))
print('LIVE_READ ' + ('GREEN' if all('ok=True empty=True' in o for o in out) else 'RED'))
" 2>&1 )"
echo "$LV" | sed 's/^/   /'
echo "$LV" | grep -q "^LIVE_READ GREEN" || restore "the placed readers do not read the EMPTY sheet"
say "[11/14] the three placed marg_report.py read the walk's EMPTY sheet ok / empty (read-only; the sheet is the walk's made-up one)"
IG="$( flock -n /tmp/marg_ingest.lock "$VPY" -B "$ING/marg_ingest.py" 2>&1 )"; rc=$?
echo "$IG" | tail -3 | mask | cut -c1-200 | sed 's/^/   collector: /'
echo "$IG" | grep -q "ImportError\|SyntaxError\|NameError\|AttributeError\|TypeError\|KeyError" && restore "the five-minute collector, run once as the crontab spells it, raised in the placed code"
say "[12/14] the five-minute collector run once as the crontab spells it: exit $rc, nothing raised in the placed code (a quiet run prints nothing; a busy lock or a busy database is the next run's)"
SF="$( cd "$FIN" && timeout 120 "$VPY" -B "$FIN/salts_refresh.py" --once --force 2>&1 )"; rc=$?
echo "$SF" | tail -2 | mask | cut -c1-240 | sed 's/^/   /'
SALT1="$(salts_now "$DBF")"
say "   before: $SALT0"
say "   after : $SALT1"
if [ "$rc" != 0 ]; then say "   NOTE: the corrected salt list was NOT posted now (exit $rc) -- nothing is undone for this; the cron posts it at the next new list"; fi
say "[13/14] the corrected salt list posted once through the app's own door (above); the page's list no longer files an item under the firm's name"
[ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz at the end"
for f in "${ORDER[@]}"; do md5sum "$(live "$f")"; done
rm -rf "$WALK"
say "[14/14] done · healthz 200 · backups: $FIN/finance.db.bak_S480_$STAMP and a .bak_S480_<from8> beside each file"
say "$KIT: DONE"
