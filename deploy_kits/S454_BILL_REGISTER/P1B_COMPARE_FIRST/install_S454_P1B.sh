#!/bin/bash
# =============================================================================
#  install_S454_P1B.sh · kit S454_BILL_REGISTER, part 1B (session 283, 03-Oct-2026; D666)
#  The comparison of a sheet loaded "as already ordered" is made before its own paper orders; the 02-Oct figure made again
#
#  Run by (on the VPS, holding the build lock /root/deploy/.claude_code_build.lock with owner S454_BILL_REGISTER):
#    SHEET=/tmp/s454p1/MARG_ORDER_SHEET_02-10-2026.txt bash <kit>/P1B_COMPARE_FIRST/install_S454_P1B.sh
#  (DRY=1: every gate, the build and the walk on scratch copies; nothing placed.)
#
#  PATCHED ON THE BOX from the live bytes (make_s454p1b.py; the anchor exactly once; FROM -> TO pinned): /root/finance/order_sheet.py
#  DATA (finance.db, backed up first): order_sheet.cmp of the sheet(s) part 1 loaded as already ordered whose figure is still part 1's
#     (recompute_s454p1b.py, computed on a scratch copy; one audit row each).
#  RESTARTS clinic-finance only. Nothing else is touched.
# =============================================================================
set -u
KIT="S454_BILL_REGISTER"
PART="P1B_COMPARE_FIRST"
KDIR="$(cd "$(dirname "$0")" && pwd)"
P1="$KDIR/../P1_ORDER_SHEET_RECEPTION"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; MRG=/root/marg_ingest
DBF="${FINANCE_DB:-$FIN/finance.db}"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s454p1b_walk_$STAMP"
F=order_sheet.py
FROM=4cf2f231ef026904d1ae42754846aea7
TO=93f55d87730e749d78ea5561de38266f
SVC=clinic-finance
NOTT=("$FIN/finance_app.py" "/root/portal/portal.py" "/root/portal/tile_grants.json" "$FIN/porders.py" "$FIN/order_rules.py" "$FIN/porders_s454.py"
      "$FIN/supplier_msg.py" "$FIN/purchase_app.py" "$MRG/marg_take.py" "$MRG/signatures.json")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] && grep -q "part $PART" KIT_ID.txt || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in "$P1/first_load_s454.py" "$P1/medical/marg_txt.py" "$DBF" "${SHEET:-/nonexistent}"; do
  [ -f "$k" ] || { say "!! [1/8] $k must be there (SHEET = Darpan's sheet of 02-Oct in /tmp) - nothing installed"; exit 1; }
done
say "[1/8] kit gates green (SUMS, KIT_ID part 1B, part 1's first-load helper and reader beside it, the sheet)"
if [ "$(m5 "$FIN/$F")" = "$TO" ]; then say "-- ALREADY INSTALLED: $FIN/$F is at the kit's pin"; exit 0; fi
[ "$(m5 "$FIN/$F")" = "$FROM" ] || { say "!! [2/8] $FIN/$F is $(m5 "$FIN/$F"), not its FROM pin $FROM - nothing installed"; exit 1; }
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
say "[2/8] $FIN/$F at its FROM pin (part 1's TO)"
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s454p1b.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /'
[ "$(m5 "$WALK/built/$F")" = "$TO" ] || { say "!! [3/8] built $F is $(m5 "$WALK/built/$F"), not the kit's pin $TO - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/8] live bytes + the anchored edit give exactly the kit's file ($TO)"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && cp -p "$WALK/built/$F" "$WALK/cc/built_$F"
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || { say "!! [4/8] compile on both pythons failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/8] compiles on /usr/bin/python3 and the venv python (in a scratch copy)"
R="$WALK/run"
for side in fin_new fin_old; do
  mkdir -p "$R/$side/finance_ui" "$R/$side/spine" || exit 1
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$R/$side/finance_ui/"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$R/$side/spine/" 2>/dev/null
done
cp -p "$WALK/built/$F" "$R/fin_new/$F"
WOUT="$( cd "$R" && timeout 1500 "$VPY" -B "$KDIR/walk_s454p1b.py" --fin-new "$R/fin_new" --fin-old "$R/fin_old" --marg "$MRG" --db "$DBF" \
         --reader "$P1/medical/marg_txt.py" --sheet "$SHEET" --first-load "$P1/first_load_s454.py" --work "$R/w" 2>&1 )"
echo "$WOUT" | mask | cut -c1-700 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S454P1B GREEN" || { say "!! [5/8] walk_s454p1b red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[5/8] walk_s454p1b green on scratch copies; its negative control red on the box as it is (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed"; rm -rf "$WALK"; exit 0; fi
[ -d "$LOCK" ] && [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [6/8] the build lock is not held by $KIT - nothing installed"; rm -rf "$WALK"; exit 1; }
[ "$(m5 "$FIN/$F")" = "$FROM" ] || { say "!! [6/8] $FIN/$F moved during the walk - nothing installed"; rm -rf "$WALK"; exit 1; }
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" \
  "$DBF" "$FIN/finance.db.bak_S454_$STAMP" || { say "!! [6/8] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
BAK="$FIN/$F.bak_S454_${FROM:0:8}"
\cp -p "$FIN/$F" "$BAK" || { say "!! [6/8] backup of $F failed - nothing placed"; rm -rf "$WALK"; exit 1; }
say "[6/8] finance.db.bak_S454_$STAMP made (backup API); $(basename "$BAK") beside the file; the lock is held by $KIT"
restore() {
  say "!! RED after placing ($1) - restoring $F byte-identically"
  \cp -p "$BAK" "$FIN/$F"; systemctl restart "$SVC" || true; sleep 8
  say "   $FIN/$F $(m5 "$FIN/$F") · finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC") · the database backup stays: $FIN/finance.db.bak_S454_$STAMP"
  rm -rf "$WALK"; exit 1
}
\cp "$WALK/built/$F" "$FIN/$F" || restore "copy"
[ "$(m5 "$FIN/$F")" = "$TO" ] || restore "md5 read-back"
say "[7/8] placed; md5 read back = $TO"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz); c2=$(health http://127.0.0.1:8106/finance/porders); c3=$(health http://127.0.0.1:8106/finance/porders/s454/order)
say "health : finance healthz $c1 · /finance/porders $c2 · Order karna hai $c3 (302/401 = the login gate, expected)"
[ "$c1" = 200 ] && { [ "$c2" = 302 ] || [ "$c2" = 401 ]; } && { [ "$c3" = 302 ] || [ "$c3" = 401 ]; } || restore "finance health"
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
[ "$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')" = 0 ] || restore "$SVC journal errors"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
AOUT="$( cd "$FIN" && "$VPY" -B "$KDIR/recompute_s454p1b.py" --db "$DBF" --finance "$FIN" --marg "$MRG" --work "$WALK/recompute" 2>&1 )"
echo "$AOUT" | mask | sed 's/^/   /'
echo "$AOUT" | grep -q "^S454 P1B recompute done" || restore "the recompute"
[ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz after the data step"
md5sum "$FIN/$F"
rm -rf "$WALK"
say "[8/8] $SVC active; healthz 200; nothing else moved; the 02-Oct comparison made again (above)"
say "$KIT part 1B: DONE"
