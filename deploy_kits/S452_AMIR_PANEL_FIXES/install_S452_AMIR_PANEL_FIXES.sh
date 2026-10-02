#!/bin/bash
# =============================================================================
#  install_S452_AMIR_PANEL_FIXES.sh · kit S452_AMIR_PANEL_FIXES (session 283, 02-Oct-2026, F-686 · F-687; D650 / D648 served)
#  Sanjeevni: what the live walk of Amir's panel found on 02-Oct, and the owner's rulings of that evening
#
#  Run by (on the VPS, holding the build lock /root/deploy/.claude_code_build.lock with owner S452_AMIR_PANEL_FIXES):
#    bash <kit>/install_S452_AMIR_PANEL_FIXES.sh
#  (DRY=1 runs every gate, the build and every walk on scratch copies, and places nothing. KITS=<dir> names the folder holding the
#   earlier kits when this kit runs from a copy; DUTYMAP_OLD=<file> the duty map now in claude_code_briefs (the earlier walks' baseline).
#   NOPIN=1, with DRY=1 only, prints the built md5s instead of refusing on a TO mismatch.)
#
#   * Step 2 lists only the scanned bills Marg does not have (S440's "Marg ka intezaar", a known supplier); the rest are counted as held
#     for reception; file names start with the stamp; a download guard; the owner's Scan links line.
#   * The reception phone's setup page is the owner's and a checker's; the key shows each time, audited; a NEW key at install.
#   * Step 7 and the board in Roman Hindi; "Rate daalo" on his card; step 6's heading once; a salt line done in Marg leaves the board.
#   * NEFT for Amir: one line and the paid sheet as a PDF, only once confirmed (the bank SMS read, or the owner's entry).
#   * Medicine vouchers 12 a visit, "Aur voucher kholiye" for more, each tap audited.
#
#  PATCHED ON THE BOX from the live bytes (make_s452.py; every anchor exactly once; FROM -> TO pins checked):
#     /root/finance/purchase_app.py  amir_day.py  supplier_msg.py  stock_app.py  stock_amir.html  (Sanjeevni's)
#     /root/finance/packs.py  (THE PARENT'S, declared: ONE anchored edit -- Amir's NEFT route)
#  READ ONLY: porders.py (S440's groups), the asset store (assets.db and its uploads).
#  DATA (finance.db, backed up first): amir.vouchers_per_visit 5 -> 12 (only if it still reads 5); a new reception-phone key; one additive
#     table made on first use, stock_rate_marg (Marg's own S.RATE / MRP of the items on the rate list, read from the spine, read only).
#  RESTARTS clinic-finance only. Not touched: porders.py, portal.py, clinic_sso.py, tile_grants.json, finance_app.py,
#  sanjeevni_approvals.py, darpan_kal.py, crontab, the medical PC.
# =============================================================================
set -u
KIT="S452_AMIR_PANEL_FIXES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
KITS="${KITS:-$KDIR/..}"
DUTYMAP="$KDIR/DUTY_MAP.json"
DUTYMAP_OLD="${DUTYMAP_OLD:-$KDIR/../../claude_code_briefs/DUTY_MAP.json}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"; AST="$ROOT/assetapp"; SHR="$ROOT/shared"; MRG="$ROOT/marg_ingest"
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s452_walk_$STAMP"
declare -A FROM=( [purchase_app.py]=176fc6eac35c7a3e7d052cba96ca873e [amir_day.py]=cd8f4659cb828c09e9455d1b7543cfbd
                  [supplier_msg.py]=02b4a9edc4ff6bc42ed896e7f260be72 [stock_app.py]=ec6b1ce80d46b808d034b23cab032dc9
                  [stock_amir.html]=1ec8663dbbad397fe46f093966352e0a [packs.py]=6a1cf6ceec4a58260df7352e48cdefe5 )
declare -A TO=( [purchase_app.py]=341c663e52076f0ee264c356b49cf49e [amir_day.py]=85f208d0d64def40fb5a02e02c531284
                [supplier_msg.py]=5cc35d2af444b5ab1996f636db8e54cf [stock_app.py]=f14a1cfaf9a47b1199a0763ac47d1006
                [stock_amir.html]=2e41e406e3b2ef9d7ed75f9f24b923b8 [packs.py]=23fda41a19a6d4be398922e906d06702 )
ORDER=(purchase_app.py amir_day.py supplier_msg.py stock_app.py stock_amir.html packs.py)
NOTT=("$FIN/porders.py" "$POR/portal.py" "$POR/clinic_sso.py" "$POR/tile_grants.json" "$FIN/finance_app.py" "$FIN/sanjeevni_approvals.py" "$FIN/darpan_kal.py")
SVC=clinic-finance
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" "$KITS" "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
stubcfg() { printf "# S452 walk only -- never the live secret\nCLINIC_SSO_SECRET = '%s'\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = 's452-walk'\n" "$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')" > "$1/portal_config.py"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/10] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/10] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$VPY" -c "import flask, openpyxl" 2>/dev/null || { say "!! [1/10] the venv python lacks flask / openpyxl; nothing installed"; exit 1; }
for k in "$KITS/S446_AMIR_STAGES_BILLS/walk_s446.py" "$KITS/S444_STAFF_SAFE/walk_s444.py" "$KITS/S444_STAFF_SAFE/apply_s444.py" \
         "$KITS/S407_NEFT_MESSAGES/walk_s407.py" "$KITS/S407_NEFT_MESSAGES/seed_s407.py" "$KITS/S408_MONTH_END_PACKS/walk_s408.py" "$KITS/S408_MONTH_END_PACKS/seed_s408.py" \
         "$KITS/S434_PACKS_FIXES/walk_s434.py" "$DUTYMAP" "$DUTYMAP_OLD" "$DBF" "$ADB" "$FIN/spine/spine.db"; do
  [ -f "$k" ] || { say "!! [1/10] $k must be reachable (KITS=$KITS, DUTYMAP_OLD=$DUTYMAP_OLD) - nothing installed"; exit 1; }
done
"$SPY" -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); assert d.get('kit')=='$KIT' and d.get('version')==3" "$DUTYMAP" \
  || { say "!! [1/10] $DUTYMAP is not this kit's duty map - nothing installed"; exit 1; }
say "[1/10] kit gates green (SUMS, KIT_ID, the venv's flask, the earlier walks, the kit's DUTY_MAP.json v3, the databases)"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then
  say "-- ALREADY INSTALLED: the six files are at the kit's pins; $SVC $(systemctl is-active "$SVC") · finance healthz $(health http://127.0.0.1:8106/finance/healthz)"
  exit 0
fi
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/10] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }; done
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
say "[2/10] the six live files at their FROM pins (packs.py, the parent's, among them)"
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s452.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /'
for f in "${ORDER[@]}"; do [ -s "$WALK/built/$f" ] || { say "!! [3/10] the build wrote no $f - nothing installed"; rm -rf "$WALK"; exit 1; }; done
if [ "${DRY:-0}" = 1 ] && [ "${NOPIN:-0}" = 1 ]; then
  for f in "${ORDER[@]}"; do say "   built $f $(m5 "$WALK/built/$f")"; done
else
  for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/10] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
  say "[3/10] live bytes + anchored edits give exactly the kit's files (six pins match)"
fi
PYS="make_s452.py walk_s452.py walks_old_s452.py plan_old_s452.py apply_s452.py"
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
WOUT="$( cd "$WALK" && timeout 2700 "$VPY" -B "$KDIR/walk_s452.py" --fin-new "$WALK/fin_new" --fin-old "$WALK/fin_old" --por "$WALK/por" --ast "$WALK/ast" \
         --shared "$WALK/shared" --db "$WALK/scratch.db" --adb "$WALK/scratch_assets.db" --kit "$KDIR" --duty-map "$DUTYMAP" --uploads "$AST/uploads" --spine "$FIN/spine/spine.db" 2>&1 )"
echo "$WOUT" | sed -E 's/[0-9]{10,}/##########/g' | cut -c1-700 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S452 GREEN" || { say "!! [5/10] walk_s452 red - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[5/10] walk_s452 green on scratch copies of finance.db and assets.db (the list, the key, step 7, the board, NEFT, Stage C, the staff-eye walk), its negative control red on the box as it is (above)"
O="$WALK/wo"; mkdir -p "$O/uploads" "$O/stub" "$O/work" || exit 1
for side in old446 old444; do mkdir -p "$O/$side"; cp -rp "$WALK/fin_old/." "$O/$side/"; done
bk() { for p in "$@"; do n="${p%%:*}"; h="${p##*:}"; cp -p "$FIN/$n.bak_${SK}_$h" "$O/$SD/$n" || { say "!! [6/10] $n.bak_${SK}_$h missing - that kit's control cannot be rebuilt"; rm -rf "$WALK"; exit 1; }; done; }
SK=S446; SD=old446; bk amir_day.py:2b497142 stock_app.py:c0120fb6 sanjeevni_approvals.py:d2c55040 purchase_app.py:a51fe90e darpan_kal.py:803970bd darpan_kal.html:a4eecb21
SK=S444; SD=old444; bk amir_day.py:068a3988 amir_salts.py:8d6ef482 reports_tile.py:27984367 sanjeevni_approvals.py:3999c4ce stock_app.py:4f2625c0 porders.py:af4a6f57
for s in b p; do
  copydb "$DBF" "$O/s446_$s.db" && copydb "$ADB" "$O/a446_$s.db" && copydb "$DBF" "$O/s444_$s.db" && copydb "$ADB" "$O/a444_$s.db" \
    && copydb "$DBF" "$O/s407_$s.db" && copydb "$DBF" "$O/s434_$s.db" && mkdir -p "$O/r408_$s" "$O/w434_$s" "$O/k434_$s" \
    && copydb "$DBF" "$O/r408_$s/scratch.db" && copydb "$ADB" "$O/r408_$s/assets.db" || { say "!! [6/10] no scratch copies for the earlier walks"; rm -rf "$WALK"; exit 1; }
  for d in "p446_$s/por" "p446_$s/ast" "p446_$s/shared" "p444_$s/por_new" "p444_$s/por_old" "p444_$s/ast" "p444_$s/shared"; do mkdir -p "$O/$d"; done
  for d in "p446_$s/por" "p444_$s/por_new" "p444_$s/por_old"; do for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$O/$d/"; done; cp -p "$POR/tile_grants.json" "$O/$d/"; done
  for p in clinic_sso.py:2bc6ba15 portal.py:626838cd tile_grants.json:acc9cc1b; do n="${p%%:*}"; h="${p##*:}"; cp -p "$POR/$n.bak_S444_$h" "$O/p444_$s/por_old/$n" || { say "!! [6/10] $n.bak_S444_$h missing"; rm -rf "$WALK"; exit 1; }; done
  for d in "p446_$s/ast" "p444_$s/ast"; do cp -p "$AST"/*.py "$AST"/*.js "$O/$d/" 2>/dev/null; done
  for d in "p446_$s/shared" "p444_$s/shared"; do cp -p "$SHR"/*.py "$O/$d/" 2>/dev/null; done
done
cp -p "$FIN/packs.py" "$FIN/packs.html" "$O/k434_b/"; cp -p "$WALK/built/packs.py" "$FIN/packs.html" "$O/k434_p/"
mkdir -p "$O/p408"; for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$O/p408/"; done; cp -p "$POR/tile_grants.json" "$O/p408/"; stubcfg "$O/p408"
"$SPY" -B plan_old_s452.py --work "$O" --fin-new "$WALK/fin_new" --fin-old "$WALK/fin_old" --kits "$KITS" --kit "$KDIR" --por "$POR" --mrg "$MRG" \
  --duty-map-old "$DUTYMAP_OLD" --duty-map "$DUTYMAP" --py "$VPY" --out "$O/plan.json" | sed 's/^/   /'
OOUT="$( cd "$O" && timeout 6000 "$VPY" -B "$KDIR/walks_old_s452.py" --plan "$O/plan.json" 2>&1 )"
echo "$OOUT" | sed -E 's/[0-9]{10,}/##########/g' | cut -c1-800 | sed 's/^/   /'
echo "$OOUT" | grep -q "^WALKS_OLD_S452 GREEN" || { say "!! [6/10] an earlier walk is red on the patched files beyond its named reds - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[6/10] re-run on the patched files: S446's, S444's, S407's, S408's and S434's walks -- green but for the named reds, each red on the box as it is too"
if [ "${DRY:-0}" = 1 ]; then
  say "-- DRY RUN: every gate, the build and every walk green; NOTHING placed, nothing restarted"; clean; rm -rf "$WALK"; exit 0
fi
[ -d "$LOCK" ] && [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/10] the build lock $LOCK is not held by $KIT - nothing installed (CLAUDE.md: one build at a time)"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [7/10] $FIN/$f moved during the walks - nothing installed"; rm -rf "$WALK"; exit 1; }; done
copydb "$DBF" "$FIN/finance.db.bak_S452_$STAMP" || { say "!! [7/10] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do BAK[$f]="$FIN/$f.bak_S452_$(m5 "$FIN/$f" | cut -c1-8)"; \cp -p "$FIN/$f" "${BAK[$f]}" || { say "!! [7/10] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }; done
say "[7/10] finance.db.bak_S452_$STAMP made (backup API); .bak_S452_<from8> beside the six files; the lock is held by $KIT"
restore() {
  say "!! RED after placing ($1) - restoring the six files byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "$FIN/$f"; done
  systemctl restart "$SVC" || true; sleep 7
  for f in "${ORDER[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f")"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC") · the database backup stays: $FIN/finance.db.bak_S452_$STAMP"
  clean; rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do \cp "$WALK/built/$f" "$FIN/$f" || restore "copy"; done
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore "md5 read-back"; done
say "[8/10] placed; all six md5s read back = the kit's pins"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart $SVC"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz); c2=$(health http://127.0.0.1:8106/finance/amir/day); c3=$(health http://127.0.0.1:8106/finance/purchase/page/phone-setup)
c4=$(health http://127.0.0.1:8106/finance/stock/page/amir); c5=$(health http://127.0.0.1:8106/finance/amir/pack/2026-08/neft); c6=$(health http://127.0.0.1:8106/finance/purchase/api/scan-files/today.zip)
say "health : finance healthz $c1 · /finance/amir/day $c2 · phone-setup $c3 · /finance/stock/page/amir $c4 · Amir's NEFT route $c5 · scan-files zip $c6 (302/401 = the login gate, expected)"
gate() { [ "$1" = 302 ] || [ "$1" = 401 ]; }
[ "$c1" = 200 ] && gate "$c2" && gate "$c3" && gate "$c4" && gate "$c5" && gate "$c6" || restore "finance health"
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
JR="$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')"
[ "$JR" = 0 ] || { journalctl -u "$SVC" --since "$T0" --no-pager | grep -i -A6 'Traceback\|Error' | head -30; restore "$SVC journal: $JR error line(s)"; }
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
say "[9/10] $SVC active; healthz 200; the pages behind their gates; nothing 'NOT mounted'; no traceback; porders/portal/clinic_sso/tile_grants/finance_app/approvals/darpan_kal untouched"
AOUT="$( cd "$FIN" && FINANCE_DB="$DBF" "$VPY" -B "$KDIR/apply_s452.py" --finance "$FIN" --db "$DBF" 2>&1 )" || { echo "$AOUT" | tail -20; restore "the data step"; }
echo "$AOUT" | sed -E 's/[0-9]{10,}/##########/g' | sed 's/^/   /'
echo "$AOUT" | grep -q "^S452 apply done" || restore "the data step"
KCH="$("$SPY" -c "import sqlite3,sys; q=lambda p: (sqlite3.connect('file:%s?mode=ro'%p,uri=True).execute(\"SELECT value FROM setting WHERE key='supplier_msg.phone_token'\").fetchone() or [''])[0]; print('changed' if q(sys.argv[1]) and q(sys.argv[1]) != q(sys.argv[2]) else 'NOT changed')" "$DBF" "$FIN/finance.db.bak_S452_$STAMP")"
say "[10/10] the data step ran on the live database (above); the phone's key against the backup's: $KCH (compared, never shown)"
[ "$KCH" = changed ] || restore "the phone's key did not change"
clean; rm -rf "$WALK"
for f in "${ORDER[@]}"; do md5sum "$FIN/$f"; done
say "$KIT: DONE -- https://followup.dr-manoj.in/finance/amir/day · https://followup.dr-manoj.in/finance/purchase/page/phone-setup"
