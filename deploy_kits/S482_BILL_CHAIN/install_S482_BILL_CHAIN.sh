#!/bin/bash
# =============================================================================
#  install_S482_BILL_CHAIN.sh · kit S482_BILL_CHAIN (Sanjeevni, session 295, 05-Oct-2026; D675 b, D676; F-731, F-732, F-733)
#  The SERVER part: the chain of Marg's bill numbers says what is missing (mi_bill_chain; one line per gap on Shavez's reports tile
#  and in the owner's English line); the rename list carries the D676 spellings; the spine's reader and the Drive collector know the
#  empty day. No staff screen's layout changes.
#
#  Run by (on the VPS, holding the build lock /root/deploy/.claude_code_build.lock with owner S482_BILL_CHAIN):
#    bash <kit>/install_S482_BILL_CHAIN.sh       (DRY=1: every gate, the build, both compiles and the whole walk; nothing placed.
#                                                 KITS=<dir> the folder of the earlier kits when this kit runs from a copy -- the walk
#                                                 makes its made-up sheets with S480's marg_txt.py;
#                                                 DUTYMAP=<file> the duty map the walk reads -- default: this kit's own DUTY_MAP.json (v6);
#                                                 EXPECT_GAP='A..,CN..|day|day' the live gap the chat measured -- empty: shown, not compared.)
#
#  PATCHED ON THE BOX from the live bytes (make_s482.py; every anchor exactly once; FROM -> TO pinned), four files:
#     /root/marg_ingest/marg_take.py  /root/marg_ingest/marg_ingest.py  /root/finance/reports_tile.py  /root/finance/spine/marg_read.py
#  RESTARTS clinic-finance only.
#  DATA (finance.db, backed up by the backup API first): seven rows of marg_item_rename (renames_s482.py, keyed by id AND old_name) --
#  the FIRST live write, before any file is placed; the new table mi_bill_chain, filled once after the service is healthy.
#  ONE READING: /root/finance/spine/readings/<the 04-10 EMPTY sheet>.json (two failed checks, written by the old reader) is removed
#  with a .bak_S482 copy beside it, and spine_evidence.py is run once as the crontab spells it so the new reader writes it again.
#  NOT TOUCHED (md5 before = after, or the install is undone): stock_app.py, amir_day.py, item_alias.py, purchase_app.py,
#  marg_router.py, the three marg_report.py, signatures.json, spine_evidence.py, spine_build.py, finance_app.py, portal.py,
#  tile_grants.json, the crontab.
# =============================================================================
set -u
KIT="S482_BILL_CHAIN"
KDIR="$(cd "$(dirname "$0")" && pwd)"
KITS="${KITS:-$KDIR/..}"
DUTYMAP="${DUTYMAP:-$KDIR/DUTY_MAP.json}"
EXPECT_GAP="${EXPECT_GAP-A003478,CN00203|2026-09-08|2026-09-09}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; ING=/root/marg_ingest; POR=/root/portal; AST=/root/assetapp
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"; SPD="$FIN/spine/spine.db"
READING_MD5=15495622be4e21b5daa8d1d7580fc6db          # the 04-10 EMPTY sheet (its md5 is its name in the evidence store)
RD="$FIN/spine/readings/$READING_MD5.json"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s482_walk_$STAMP"
SVC=clinic-finance
ORDER=(ingest/marg_take.py ingest/marg_ingest.py finance/reports_tile.py finance/spine/marg_read.py)
declare -A FROM=( [ingest/marg_take.py]=3ac9bbe03abf5c01c4ebc1bfffd30da2 [ingest/marg_ingest.py]=7f6b4dc25d1c247c8b45f05108e600ca
                  [finance/reports_tile.py]=406e452b2e3cf5991e89100ee867e1d6 [finance/spine/marg_read.py]=7ec9b325687de465ea6942affb25dec1 )
declare -A TO
live() { case "$1" in ingest/*) echo "$ING/${1#ingest/}";; finance/*) echo "$FIN/${1#finance/}";; esac; }
# read only -- the brief's pins; the walk reads them, nothing edits them
declare -A RO=( [$FIN/stock_app.py]=7e159de737c0ec03cea890053f1bcd58 [$FIN/amir_day.py]=709f20c1078cbcb36fc1108e452c40c1
                [$FIN/item_alias.py]=5168c3c05df63a674a8dcab59f74365f [$ING/marg_router.py]=318086e36b0088f2da57b95d19a86b98
                [$FIN/spine/spine_evidence.py]=0fcf6c6419d5a69d7314e152421a2aa7 )
NOTT=("$FIN/stock_app.py" "$FIN/amir_day.py" "$FIN/item_alias.py" "$FIN/purchase_app.py" "$ING/marg_router.py" "$ING/marg_report.py"
      "$ING/lib/marg_report.py" "$FIN/marg_report.py" "$ING/signatures.json" "$FIN/spine/spine_evidence.py" "$FIN/spine/spine_build.py"
      "$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
reading_now() { "$SPY" -c "
import json,sys
try:
    d=json.load(open(sys.argv[1]))
    print('ok=%s failed=%s empty=%s day=%s read_at=%s' % (d.get('ok'), d.get('failed'), (d.get('data') or {}).get('empty'), (d.get('data') or {}).get('date_from'), d.get('read_at')))
except Exception as e:
    print('absent (%s)' % e.__class__.__name__)
" "$1"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/13] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/13] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$VPY" -c "import flask" 2>/dev/null || { say "!! [1/13] the venv python lacks flask; nothing installed"; exit 1; }
for k in "$DUTYMAP" "$DBF" "$ADB" "$SPD" "$ING/xlrd/__init__.py" "$KITS/S480_MARG_TEXT_READERS/marg_txt.py"; do
  [ -f "$k" ] || { say "!! [1/13] $k must be reachable (KITS=$KITS, DUTYMAP=$DUTYMAP) - nothing installed"; exit 1; }
done
. "$KDIR/PINS.sh" || { say "!! [1/13] PINS.sh missing - nothing installed"; exit 1; }
for f in "${!RO[@]}"; do
  [ "$(m5 "$f")" = "${RO[$f]}" ] || { say "!! [1/13] $f is $(m5 "$f"), not the brief's pin ${RO[$f]} (read only here; this kit was walked against that file) - nothing installed"; exit 1; }
done
say "[1/13] kit gates green (SUMS, KIT_ID, the venv's flask, the duty map v6 of this kit, the databases, S480's marg_txt.py for the walk's made-up sheets, the five read-only files at the brief's pins)"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "$(live "$f")")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the four files are at the kit's pins; $SVC $(systemctl is-active "$SVC"); healthz $(health http://127.0.0.1:8106/finance/healthz); the 04-10 reading: $(reading_now "$RD")"; exit 0; fi
for f in "${ORDER[@]}"; do
  [ "$(m5 "$(live "$f")")" = "${FROM[$f]}" ] || { say "!! [2/13] $(live "$f") is $(m5 "$(live "$f")"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }
done
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"
say "[2/13] the four live files at their FROM pins (the brief's section 8)"
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s482.py --server --ingest "$ING" --finance "$FIN" --out "$WALK/built" | sed 's/^/   /'
for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/13] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
say "[3/13] live bytes + anchored edits give the four pinned files"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && for f in "${ORDER[@]}"; do cp -p "$WALK/built/$f" "$WALK/cc/built_$(echo "$f" | tr '/' '_')"; done
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || { say "!! [4/13] compile on both pythons failed - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK/cc/__pycache__"
say "[4/13] compiles on /usr/bin/python3 and the venv python (a scratch copy)"
R="$WALK/run"
for side in new old; do
  mkdir -p "$R/$side/marg_ingest/lib" "$R/$side/finance/finance_ui" "$R/$side/finance/spine" || exit 1
  cp -p "$ING"/*.py "$ING/signatures.json" "$R/$side/marg_ingest/" && cp -p "$ING"/lib/*.py "$R/$side/marg_ingest/lib/" && cp -rp "$ING/xlrd" "$R/$side/marg_ingest/xlrd" \
    || { say "!! [5/13] no scratch copy of marg_ingest - nothing installed"; rm -rf "$WALK"; exit 1; }
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/$side/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$R/$side/finance/finance_ui/"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$R/$side/finance/spine/" 2>/dev/null
done
for f in "${ORDER[@]}"; do case "$f" in ingest/*) cp -p "$WALK/built/$f" "$R/new/marg_ingest/${f#ingest/}";; finance/*) cp -p "$WALK/built/$f" "$R/new/finance/${f#finance/}";; esac; done
mkdir -p "$R/por" "$R/w" || exit 1
for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$R/por/"; done   # never the live secret, never the user store
cp -p "$POR/tile_grants.json" "$R/por/"
copydb "$DBF" "$R/scratch.db" && copydb "$ADB" "$R/scratch_assets.db" && copydb "$SPD" "$R/scratch_spine.db" || { say "!! [5/13] no scratch copies - nothing installed"; rm -rf "$WALK"; exit 1; }
# the crons and the service import these files: each side as it is imported, on the scratch copies, writing nothing live (F-711)
SOUT=""
for side in new old; do
  o="$( cd "$R/$side/marg_ingest" && timeout 120 "$VPY" -B -c "import marg_ingest, marg_take, marg_shadow, marg_rescan_vps, marg_report, marg_router; print('imports ok: marg_ingest, marg_take, marg_shadow, marg_rescan_vps; chain: %s' % hasattr(marg_take, 'rebuild_chain'))" 2>&1 )"; rc=$?
  SOUT="$SOUT$side  the collector's, the door's, the shadow's and the rescan's imports  exit $rc  $(echo "$o" | tail -1 | mask | cut -c1-150)"$'\n'
  [ "$side" = new ] && [ "$rc" != 0 ] && { echo "$o" | mask | tail -12 | sed 's/^/   /'; say "!! [5/13] the built files do not import as the crons import them - nothing installed"; rm -rf "$WALK"; exit 1; }
  o="$( cd "$R/$side/finance/spine" && timeout 120 "$VPY" -B -c "import spine_evidence, marg_read; print('imports ok: spine_evidence -> marg_read %s' % marg_read.READER_VERSION)" 2>&1 )"; rc=$?
  SOUT="$SOUT$side  the spine's evidence job and its reader  exit $rc  $(echo "$o" | tail -1 | mask | cut -c1-150)"$'\n'
  [ "$side" = new ] && [ "$rc" != 0 ] && { echo "$o" | mask | tail -12 | sed 's/^/   /'; say "!! [5/13] the built marg_read.py does not import as the spine imports it - nothing installed"; rm -rf "$WALK"; exit 1; }
done
echo "$SOUT" | sed 's/^/   /'
TS="$( cd "$R/new/finance" && timeout 600 "$VPY" -B reports_tile.py 2>&1 | tail -1 )"
TO_="$( cd "$R/old/finance" && timeout 600 "$VPY" -B reports_tile.py 2>&1 | tail -1 )"
[ "$TS" = "$TO_" ] || { say "!! [5/13] reports_tile.py's own selftest on the built file says '$TS', the box as it is says '$TO_' - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[5/13] on scratch copies: the built files import as the crontab and the service import them; reports_tile.py's own selftest on the built file: $(echo "$TS" | cut -c1-80) (the same line as the box as it is)"
WOUT="$( cd "$R" && timeout 3000 "$VPY" -B "$KDIR/walk_s482.py" server --kit "$KDIR" --work "$R/w" --kits "$KITS" --ingest-new "$R/new/marg_ingest" --ingest-old "$R/old/marg_ingest" \
         --fin-new "$R/new/finance" --fin-old "$R/old/finance" --por "$R/por" --db "$R/scratch.db" --adb "$R/scratch_assets.db" --spine "$R/scratch_spine.db" --duty-map "$DUTYMAP" \
         --expect "$EXPECT_GAP" 2>&1 )"
echo "$WOUT" | mask | cut -c1-1400 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S482 server GREEN" || { say "!! [6/13] walk_s482 (server) red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[6/13] walk_s482 sections 1, 2, 3, 4 and the staff-eye walk green on scratch copies; every negative control red on the box as it is (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed, nothing written"; rm -rf "$WALK"; exit 0; fi
[ -d "$LOCK" ] && [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/13] the build lock is not held by $KIT - nothing installed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do
  [ "$(m5 "$(live "$f")")" = "${FROM[$f]}" ] || { say "!! [7/13] $(live "$f") moved during the walk - nothing installed"; rm -rf "$WALK"; exit 1; }
done
copydb "$DBF" "$FIN/finance.db.bak_S482_$STAMP" || { say "!! [7/13] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
[ -s "$FIN/finance.db.bak_S482_$STAMP" ] || { say "!! [7/13] the database backup is empty - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[7/13] the lock is held by $KIT; finance.db.bak_S482_$STAMP made (backup API)"
# ---- Part B first (D676): Amir's list may open any hour -- the one data write, before any file is placed
RN="$( "$SPY" -B "$WALK/cc/renames_s482.py" "$DBF" 2>&1 )"; rc=$?
echo "$RN" | sed 's/^/   /'
echo "$RN" | grep -q "^RENAMES_S482 \(OK\|PART\)" && [ "$rc" = 0 ] || { say "!! [8/13] the renames were NOT written (above) - nothing placed; the database is as it was (the backup stays)"; rm -rf "$WALK"; exit 1; }
say "[8/13] Part B: marg_item_rename carries the D676 spellings (keyed by id AND old_name; the other rows unchanged cell for cell)"
declare -A BAK
for f in "${ORDER[@]}"; do
  L="$(live "$f")"; BAK[$f]="$L.bak_S482_${FROM[$f]:0:8}"
  \cp -p "$L" "${BAK[$f]}" || { say "!! [9/13] backup of $L failed - no file placed (the renames of step 8 stay: they are right on their own)"; rm -rf "$WALK"; exit 1; }
  [ "$(m5 "${BAK[$f]}")" = "${FROM[$f]}" ] || { say "!! [9/13] the backup of $L does not read back - no file placed"; rm -rf "$WALK"; exit 1; }
done
putfile() { \cp -p "$1" "$2.s482_new" && mv -f "$2.s482_new" "$2"; }      # a rename: the five-minute collector never reads half a file
RD_MOVED=0
restore() {
  say "!! RED after placing ($1) - restoring every file byte-identically"
  for f in "${ORDER[@]}"; do putfile "${BAK[$f]}" "$(live "$f")"; done
  if [ "$RD_MOVED" = 1 ] && [ ! -f "$RD" ] && [ -f "$RD.bak_S482" ]; then \cp -p "$RD.bak_S482" "$RD"; say "   the 04-10 reading put back as it was"; fi
  systemctl restart "$SVC" || true; sleep 8
  for f in "${ORDER[@]}"; do say "   $(live "$f") $(m5 "$(live "$f")") (FROM ${FROM[$f]})"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC")"
  say "   DATA: the seven renames of step 8 STAY (right on their own; undo only from $FIN/finance.db.bak_S482_$STAMP, said first); a mi_bill_chain table, if it was made, stays and is read by nothing"
  rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do putfile "$WALK/built/$f" "$(live "$f")" || restore "copy $f"; done
for f in "${ORDER[@]}"; do [ "$(m5 "$(live "$f")")" = "${TO[$f]}" ] || restore "md5 read-back of $f"; done
say "[9/13] a .bak_S482_<from8> beside each of the four files, read back; placed (each by a rename); md5 read back = the four TO pins"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz)
say "health : finance healthz $c1"
[ "$c1" = 200 ] || restore "finance healthz"
for p in /finance/reports/aaj /finance/stock/page/amir /finance/clinic/marg/upload; do
  c=$(health "http://127.0.0.1:8106$p"); say "         $p $c (302/401 = the login gate, expected)"
  [ "$c" = 302 ] || [ "$c" = 401 ] || restore "a gated page answered $c ($p)"
done
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
[ "$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')" = 0 ] || restore "$SVC journal errors"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
say "[10/13] $SVC active (restarted $T0); healthz 200; the gated pages answer the gate; nothing else moved; the crontab is as it was"
IG="$( flock -n /tmp/marg_ingest.lock "$VPY" -B "$ING/marg_ingest.py" 2>&1 )"; rc=$?
echo "$IG" | tail -3 | mask | cut -c1-200 | sed 's/^/   collector: /'
echo "$IG" | grep -q "ImportError\|SyntaxError\|NameError\|AttributeError\|TypeError\|KeyError" && restore "the five-minute collector, run once as the crontab spells it, raised in the placed code"
say "[11/13] the five-minute collector run once as the crontab spells it: exit $rc, nothing raised in the placed code (a quiet run prints nothing; a busy lock or a busy database is the next run's)"
# ---- the chain on the live table, once (under the collector's own lock); then the tile's lines exactly as the placed page words them
CH="$( cd "$ING" && FIN="$FIN" DBF="$DBF" flock -w 90 /tmp/marg_ingest.lock "$VPY" -B - <<'PYEOF' 2>&1
import os, sqlite3, sys
sys.path.insert(0, os.getcwd())
import marg_take as MT
con = MT._connect(os.environ["DBF"])
n = MT.rebuild_chain(con)
st = MT.chain_state(con)
con.close()
print("mi_bill_chain: %d rows written; built %s; complete %s; last %s" % (n, st["built"], st["complete"], st["last"]))
for g in st["gaps"]:
    print("gap: %s missing %s between %s and %s%s (n %d)" % (g["series"], ",".join(g["missing"]), g["between"][0], g["between"][1],
                                                              (" via the empty day(s) %s" % g["via_empty"]) if g["via_empty"] else "", g["n"]))
try:
    sys.path.insert(0, os.environ["FIN"])
    os.chdir(os.environ["FIN"])
    import reports_tile as RT
    for l in RT._s482_lines(st):
        print("TILE HI: " + l["text_hi"])
        print("TILE EN: " + l["text_en"])
    cx = sqlite3.connect("file:%s?mode=ro" % os.environ["DBF"], uri=True)       # read only: the page is built, nothing is written
    cx.row_factory = sqlite3.Row
    s = RT.status(cx)
    print("OWNER LINE: " + s["line"])
    print("CARD ON THE PAGE: %s" % ("yes" if "id=s482chain" in RT.render(s) else "no"))
except Exception as e:
    print("NOTE: the page was not rendered here (%s: %s) -- the walk rendered it on the copy" % (e.__class__.__name__, str(e)[:120]))
print("CHAIN_LIVE OK")
PYEOF
)"
echo "$CH" | mask | cut -c1-600 | sed 's/^/   /'
echo "$CH" | grep -q "^CHAIN_LIVE OK" || restore "the chain could not be built or read on the live table"
say "[12/13] the chain lives in mi_bill_chain (built once here; from now on rewritten whenever a sale report or an EMPTY day lands); the tile's lines are above, as the placed page words them"
# ---- the one reading the old reader wrote for the 04-10 EMPTY sheet: removed with a copy beside it, then written again by the new reader
say "   the 04-10 reading before: $(reading_now "$RD")"
if [ -f "$RD" ] && "$SPY" -c "import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if (d.get('ok') is False and d.get('family')=='SALE_BILLWISE' and not (d.get('data') or {}).get('bills')) else 1)" "$RD"; then
  say "   its md5 before removal: $(m5 "$RD")"
  \cp -p "$RD" "$RD.bak_S482" && [ "$(m5 "$RD.bak_S482")" = "$(m5 "$RD")" ] && rm -f "$RD" && RD_MOVED=1 || restore "the 04-10 reading could not be set aside"
  SE="$( cd "$FIN/spine" && flock -w 120 /tmp/spine.lock "$VPY" -B spine_evidence.py 2>&1 )"; rc=$?
  echo "$SE" | tail -3 | mask | cut -c1-220 | sed 's/^/   spine_evidence: /'
  say "   the 04-10 reading after : $(reading_now "$RD")"
  [ -f "$RD" ] || say "   NOTE: spine_evidence did not write it now (exit $rc: a busy lock or Drive) -- the next 10-minute run writes it; the old one is $RD.bak_S482"
else
  say "   it is not the failed reading of the old reader (or is absent) -- left as it is"
fi
[ "$(m5 "$FIN/spine/spine_evidence.py")" = "${RO[$FIN/spine/spine_evidence.py]}" ] || restore "spine_evidence.py moved"
[ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz at the end"
for f in "${ORDER[@]}"; do md5sum "$(live "$f")"; done
rm -rf "$WALK"
say "[13/13] done · healthz 200 · backups: $FIN/finance.db.bak_S482_$STAMP, a .bak_S482_<from8> beside each file, $RD.bak_S482"
say "$KIT: DONE"
