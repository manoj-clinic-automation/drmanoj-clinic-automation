#!/bin/bash
# =============================================================================
#  install_S446_AMIR_STAGES_BILLS.sh · kit S446_AMIR_STAGES_BILLS (session 283, 02-Oct-2026, D649 · D650 · F-673 F-674 F-679 F-680)
#  Sanjeevni: what S444 did not carry -- the count in gated stages, packs by state, the scanned bills as files, the doors
#
#  Run by (one line on the VPS, holding the build lock /root/deploy/.claude_code_build.lock with owner S446_AMIR_STAGES_BILLS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S446_AMIR_STAGES_BILLS/install_S446_AMIR_STAGES_BILLS.sh
#  (DRY=1 runs every gate, the build and every walk on scratch copies, and places nothing. KITS=<dir> names the folder holding the
#   earlier kits when this kit runs from a copy; DUTYMAP=<file> the DUTY_MAP.json when it is not at ../../claude_code_briefs.
#   NOPIN=1, with DRY=1 only, prints the built md5s instead of refusing on a TO mismatch.)
#
#   * Amir's count corrections come in stages: A the 7 orthotic vouchers (proved on the next export, orthotic lines only), B the
#     renames (shown only once A is proved), C the medicine vouchers 5 a visit (amir.vouchers_per_visit). Never blocks Din band.
#   * Packs by state: every month of the last three that is ready and not yet "dekh liya", in the card; the foot card goes.
#   * The scanned bills to put into Marg are files on step 2 (<SUPPLIER>_<billno>_<dd-mm-yyyy>.pdf, today's as one zip), Amir and the
#     owner only; Sarvam is compared field by field with Marg until purchase.sarvam_trial_until (Marg overrules).
#   * Doors: Darpan answers Amir's claims on Kal ka hisaab; Shavez's Vendor payments names last month's unsent messages; the owner's
#     counter-returns line counts every open month.
#
#  PATCHED ON THE BOX from the live bytes (make_s446.py; every anchor exactly once; FROM -> TO pins checked):
#     /root/finance/amir_day.py  stock_app.py  sanjeevni_approvals.py  purchase_app.py  darpan_kal.py  darpan_kal.html
#  READ ONLY: packs.py (pinned), stock_watch.py, supplier_msg.py, the asset store (assets.db and its uploads).
#  DATA (finance.db, backed up first): three settings rows (INSERT OR IGNORE); two additive tables made on first use
#     (stock_stage_event, purchase_sarvam_check); the first Sarvam-against-Marg comparison.
#  RESTARTS clinic-finance only. Not touched: porders.py, portal.py, clinic_sso.py, tile_grants.json, crontab.
#  The medical PC's reader fix (medical/) travels by the Drive kit route (ToMedical\_kit), not by this script.
# =============================================================================
set -u
KIT="S446_AMIR_STAGES_BILLS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
KITS="${KITS:-$KDIR/..}"
DUTYMAP="${DUTYMAP:-$KDIR/../../claude_code_briefs/DUTY_MAP.json}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"; AST="$ROOT/assetapp"; SHR="$ROOT/shared"; MRG="$ROOT/marg_ingest"
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s446_walk_$STAMP"
declare -A FROM=( [amir_day.py]=2b497142efdb1a3d1b84e9f05cbf59ac [stock_app.py]=c0120fb67c78105fe797982fcb6ab644
                  [sanjeevni_approvals.py]=d2c550401ebfb7716126d24a09fae78f [purchase_app.py]=a51fe90eaa2922ba4e2b4db6388f797a
                  [darpan_kal.py]=803970bd04c7203632b98d9659923b3b [darpan_kal.html]=a4eecb21a88f793ab5c81b75dab20a51 )
declare -A TO=( [amir_day.py]=cd8f4659cb828c09e9455d1b7543cfbd [stock_app.py]=ec6b1ce80d46b808d034b23cab032dc9
                [sanjeevni_approvals.py]=792f4a9af1728c76e8d5a656f5662421 [purchase_app.py]=176fc6eac35c7a3e7d052cba96ca873e
                [darpan_kal.py]=377ffd63786261cef4a6113482d43bb5 [darpan_kal.html]=9269afb04a454b626895a27666032752 )
ORDER=(amir_day.py stock_app.py sanjeevni_approvals.py purchase_app.py darpan_kal.py darpan_kal.html)
declare -A RO=( [packs.py]=6a1cf6ceec4a58260df7352e48cdefe5 )
NOTT=("$FIN/porders.py" "$POR/portal.py" "$POR/clinic_sso.py" "$POR/tile_grants.json" "$FIN/finance_app.py")
SVC=clinic-finance
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" "$KITS" "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/10] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/10] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$VPY" -c "import flask" 2>/dev/null || { say "!! [1/10] the venv python lacks flask; nothing installed"; exit 1; }
for k in "$KITS/S437_COUNT_PAGES_FINAL/walk_s437.py" "$KITS/S437_COUNT_PAGES_FINAL/walk_s436_s437.py" "$KITS/S437_COUNT_PAGES_FINAL/seed_s437.py" \
         "$KITS/S436_STAFF_PAGES_CLEAN/seed_s436.py" "$KITS/S444_STAFF_SAFE/walk_s444.py" "$DUTYMAP" "$DBF" "$ADB" "$FIN/spine/spine.db" \
         "$FIN/finance.db.bak_S436_20260928_130938"; do
  [ -f "$k" ] || { say "!! [1/10] $k must be reachable (KITS=$KITS, DUTYMAP=$DUTYMAP) - nothing installed"; exit 1; }
done
"$SPY" -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); assert d.get('kit')=='$KIT'" "$DUTYMAP" \
  || { say "!! [1/10] $DUTYMAP is not this kit's duty map - nothing installed"; exit 1; }
say "[1/10] kit gates green (SUMS, KIT_ID, the venv's flask, the earlier walks and their controls, DUTY_MAP.json of $KIT, the databases)"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then
  say "-- ALREADY INSTALLED: the six files are at the kit's pins; $SVC $(systemctl is-active "$SVC") · finance healthz $(health http://127.0.0.1:8106/finance/healthz)"
  exit 0
fi
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/10] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }; done
for f in "${!RO[@]}"; do [ "$(m5 "$FIN/$f")" = "${RO[$f]}" ] || { say "!! [2/10] $FIN/$f (read only) is $(m5 "$FIN/$f"), not ${RO[$f]} - the card reads it; nothing installed"; exit 1; }; done
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
say "[2/10] the six live files at their FROM pins; packs.py (read only) at its pin"
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s446.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /'
for f in "${ORDER[@]}"; do [ -s "$WALK/built/$f" ] || { say "!! [3/10] the build wrote no $f - nothing installed"; rm -rf "$WALK"; exit 1; }; done
if [ "${DRY:-0}" = 1 ] && [ "${NOPIN:-0}" = 1 ]; then
  for f in "${ORDER[@]}"; do say "   built $f $(m5 "$WALK/built/$f")"; done
else
  for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/10] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
  say "[3/10] live bytes + anchored edits give exactly the kit's files (six pins match)"
fi
PYS="make_s446.py walk_s446.py walks_old_s446.py plan_old_s446.py apply_s446.py"
for f in "${ORDER[@]}"; do case "$f" in *.py) PYS="$PYS $WALK/built/$f";; esac; done
( "$SPY" -m py_compile $PYS 2>/dev/null && "$VPY" -m py_compile $PYS 2>/dev/null ) || { say "!! [4/10] compile on both pythons failed - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[4/10] compiles on /usr/bin/python3 and the venv python"
for side in fin_new fin_old; do
  mkdir -p "$WALK/$side/finance_ui" "$WALK/$side/spine"
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$WALK/$side/spine/" 2>/dev/null
done
for f in "${ORDER[@]}"; do cp -p "$WALK/built/$f" "$WALK/fin_new/$f"; done
mkdir -p "$WALK/por" "$WALK/ast" "$WALK/shared"
for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$WALK/por/"; done   # never the live secret, never the user store
cp -p "$POR/tile_grants.json" "$WALK/por/"; cp -p "$SHR"/*.py "$WALK/shared/" 2>/dev/null
copydb "$DBF" "$WALK/scratch.db" && copydb "$ADB" "$WALK/scratch_assets.db" || { say "!! [5/10] no scratch copies - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd "$WALK" && timeout 1800 "$VPY" -B "$KDIR/walk_s446.py" --fin-new "$WALK/fin_new" --fin-old "$WALK/fin_old" --por "$WALK/por" --ast "$WALK/ast" \
         --shared "$WALK/shared" --db "$WALK/scratch.db" --adb "$WALK/scratch_assets.db" --kit "$KDIR" --duty-map "$DUTYMAP" 2>&1 )"
echo "$WOUT" | sed -E 's/[0-9]{10,}/##########/g' | cut -c1-600 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S446 GREEN" || { say "!! [5/10] walk_s446 red - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[5/10] walk_s446 green on scratch copies of finance.db and assets.db (stages, packs, files, Sarvam, doors, the staff-eye walk), its negative control red on the box as it is (above)"
O="$WALK/wo"; mkdir -p "$O/uploads" "$O/stub" "$O/work" || exit 1
for side in old437 old436 old444; do mkdir -p "$O/$side"; cp -rp "$WALK/fin_old/." "$O/$side/"; done
bk() { for p in "$@"; do n="${p%%:*}"; h="${p##*:}"; cp -p "$FIN/$n.bak_${SK}_$h" "$O/$SD/$n" || { say "!! [6/10] $n.bak_${SK}_$h missing - that kit's control cannot be rebuilt"; rm -rf "$WALK"; exit 1; }; done; }
SK=S437; SD=old437; bk stock_amir.html:d32f39fa stockmatch.html:bdfb25e3 loss_piles.py:47d6acb3 qty_words.py:f4c15d7e stock_app.py:ec9abc48 stock_statement.py:24a040b1 stock_hub.html:7b2ea506 stock_loss.html:5ead2a32
SK=S436; SD=old436; bk stockmatch.py:df5501ea stockmatch.html:4ddf0073 stock_amir.html:3cf1f73e loss_piles.py:2501b55a stock_watch.py:5114e01f stock_app.py:02ad3d6a stock_hub.html:38e0537c stock_statement.py:05c63235
SK=S444; SD=old444; bk amir_day.py:068a3988 amir_salts.py:8d6ef482 reports_tile.py:27984367 sanjeevni_approvals.py:3999c4ce stock_app.py:4f2625c0 porders.py:af4a6f57
for s in b p; do
  copydb "$DBF" "$O/s437_$s.db" && copydb "$FIN/finance.db.bak_S436_20260928_130938" "$O/s436_$s.db" && copydb "$FIN/spine/spine.db" "$O/sp437_$s.db" \
    && copydb "$FIN/spine/spine.db" "$O/sp436_$s.db" && copydb "$DBF" "$O/s444_$s.db" && copydb "$ADB" "$O/a444_$s.db" || { say "!! [6/10] no scratch copies for the earlier walks"; rm -rf "$WALK"; exit 1; }
  P4="$O/p444_$s"; mkdir -p "$P4/por_new" "$P4/por_old" "$P4/ast" "$P4/shared"
  for d in por_new por_old; do for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$P4/$d/"; done; cp -p "$POR/tile_grants.json" "$P4/$d/"; done
  for p in clinic_sso.py:2bc6ba15 portal.py:626838cd tile_grants.json:acc9cc1b; do n="${p%%:*}"; h="${p##*:}"; cp -p "$POR/$n.bak_S444_$h" "$P4/por_old/$n" || { say "!! [6/10] $n.bak_S444_$h missing"; rm -rf "$WALK"; exit 1; }; done
  cp -p "$AST"/*.py "$AST"/*.js "$P4/ast/"; cp -p "$SHR"/*.py "$P4/shared/" 2>/dev/null
done
"$SPY" -B plan_old_s446.py --work "$O" --fin-new "$WALK/fin_new" --fin-old "$WALK/fin_old" --kits "$KITS" --por "$POR" --mrg "$MRG" --duty-map "$DUTYMAP" --out "$O/plan.json" | sed 's/^/   /'
OOUT="$( cd "$O" && timeout 5400 "$VPY" -B "$KDIR/walks_old_s446.py" --plan "$O/plan.json" 2>&1 )"
echo "$OOUT" | sed -E 's/[0-9]{10,}/##########/g' | cut -c1-400 | sed 's/^/   /'
echo "$OOUT" | grep -q "^WALKS_OLD_S446 GREEN" || { say "!! [6/10] an earlier walk is red on the patched files beyond its named reds - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[6/10] re-run on the patched files: S437's and S436's walks on the board (D1 D2 named), S444's walk (B1-B3 named): green but for the named reds of today's data, each red on the box as it is too"
if [ "${DRY:-0}" = 1 ]; then
  say "-- DRY RUN: every gate, the build and every walk green; NOTHING placed, nothing restarted"; clean; rm -rf "$WALK"; exit 0
fi
[ -d "$LOCK" ] && [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/10] the build lock $LOCK is not held by $KIT - nothing installed (CLAUDE.md: one build at a time)"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [7/10] $FIN/$f moved during the walks - nothing installed"; rm -rf "$WALK"; exit 1; }; done
copydb "$DBF" "$FIN/finance.db.bak_S446_$STAMP" || { say "!! [7/10] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do BAK[$f]="$FIN/$f.bak_S446_$(m5 "$FIN/$f" | cut -c1-8)"; \cp -p "$FIN/$f" "${BAK[$f]}" || { say "!! [7/10] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }; done
say "[7/10] finance.db.bak_S446_$STAMP made (backup API); .bak_S446_<from8> beside the six files; the lock is held by $KIT"
restore() {
  say "!! RED after placing ($1) - restoring the six files byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "$FIN/$f"; done
  systemctl restart "$SVC" || true; sleep 7
  for f in "${ORDER[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f")"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC") · the database backup stays: $FIN/finance.db.bak_S446_$STAMP"
  clean; rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do \cp "$WALK/built/$f" "$FIN/$f" || restore "copy"; done
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore "md5 read-back"; done
say "[8/10] placed; all six md5s read back = the kit's pins"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart $SVC"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz); c2=$(health http://127.0.0.1:8106/finance/amir/day); c3=$(health http://127.0.0.1:8106/finance/approvals)
c4=$(health http://127.0.0.1:8106/finance/darpan/kal); c5=$(health http://127.0.0.1:8106/finance/purchase/page/pay); c6=$(health http://127.0.0.1:8106/finance/purchase/api/scan-files/today.zip)
say "health : finance healthz $c1 · /finance/amir/day $c2 · /finance/approvals $c3 · /finance/darpan/kal $c4 · /finance/purchase/page/pay $c5 · scan-files zip $c6 (302/401 = the login gate, expected)"
gate() { [ "$1" = 302 ] || [ "$1" = 401 ]; }
[ "$c1" = 200 ] && gate "$c2" && gate "$c3" && gate "$c4" && gate "$c5" && gate "$c6" || restore "finance health"
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
JR="$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')"
[ "$JR" = 0 ] || { journalctl -u "$SVC" --since "$T0" --no-pager | grep -i -A6 'Traceback\|Error' | head -30; restore "$SVC journal: $JR error line(s)"; }
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
say "[9/10] $SVC active; healthz 200; the pages behind their gates; nothing 'NOT mounted'; no traceback; porders/portal/clinic_sso/tile_grants/finance_app untouched"
AOUT="$( cd "$FIN" && FINANCE_DB="$DBF" "$VPY" -B "$KDIR/apply_s446.py" --finance "$FIN" --db "$DBF" 2>&1 )" || { echo "$AOUT" | tail -20; restore "the data step"; }
echo "$AOUT" | sed -E 's/[0-9]{10,}/##########/g' | sed 's/^/   /'
echo "$AOUT" | grep -q "^S446 apply done" || restore "the data step"
say "[10/10] the data step ran on the live database (above): the settings, the first Sarvam comparison, and what Amir and the owner now see"
clean; rm -rf "$WALK"
for f in "${ORDER[@]}"; do md5sum "$FIN/$f"; done
say "$KIT: DONE -- https://followup.dr-manoj.in/finance/amir/day · https://followup.dr-manoj.in/finance/approvals"
