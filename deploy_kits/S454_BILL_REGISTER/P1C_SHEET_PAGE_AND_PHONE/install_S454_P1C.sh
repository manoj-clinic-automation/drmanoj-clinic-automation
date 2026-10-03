#!/bin/bash
# =============================================================================
#  install_S454_P1C.sh · kit S454_BILL_REGISTER, part 1C (session 283, 03-Oct-2026; S454 section 17, D666 / D669)
#  The printed order sheet carries the whole open order and nothing prints over another column; the owner's "Reception phone" card and its
#  test message; the phone-setup page's steps as the macro was built; the phone counted alive for 720 minutes; "1 medicine";
#  message 1 put back to waiting (17.9).
#
#  Run by (on the VPS, holding the build lock /root/deploy/.claude_code_build.lock with owner S454_BILL_REGISTER):
#    bash <kit>/P1C_SHEET_PAGE_AND_PHONE/install_S454_P1C.sh          (DRY=1: every gate, the build and the walk on scratch copies; nothing placed)
#
#  PATCHED ON THE BOX from the live bytes (make_s454p1c.py; every anchor exactly once; FROM -> TO pinned):
#     /root/finance/supplier_msg.py  porders_s454.py  order_sheet.py ;  order_sheet_pdf.py replaced whole by the kit's v1.1 (FROM pin checked)
#  DATA (finance.db, backed up first; data_s454p1c.py): supplier_msg id 1 back to waiting ONLY if it still reads sent at 15:00:27 by
#     reception-phone (audited); setting order.phone_alive_min = 720 (audited). No payment message is held, skipped or re-queued otherwise.
#  RESTARTS clinic-finance only. Not touched: finance_app.py, portal.py, tile_grants.json, porders.py, order_rules.py, purchase_app.py, the
#  marg_ingest files, the crontab.
# =============================================================================
set -u
KIT="S454_BILL_REGISTER"
PART="P1C_SHEET_PAGE_AND_PHONE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; POR=/root/portal; AST=/root/assetapp; MRG=/root/marg_ingest
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s454p1c_walk_$STAMP"
declare -A FROM=( [supplier_msg.py]=fc6c1724d6da4e1d04897b60d61c13b8 [porders_s454.py]=05716f3c040478d09fd2016561c7c99c
                  [order_sheet.py]=93f55d87730e749d78ea5561de38266f [order_sheet_pdf.py]=9c28df38435a25d7e1d65c34b8d43ec9 )
declare -A TO=( [supplier_msg.py]=2f43af754a160376cec955f92f3aa43a [porders_s454.py]=c2608914e56b0f7ce049d93aeed23d39
                [order_sheet.py]=cffbeef3f4405132ab1861ffc146bea9 [order_sheet_pdf.py]=6e7a5e1a7ae68cb4548c8c8f15cf27cb )
ORDER=(supplier_msg.py porders_s454.py order_sheet.py order_sheet_pdf.py)
NOTT=("$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json" "$FIN/porders.py" "$FIN/order_rules.py" "$FIN/purchase_app.py"
      "$FIN/sanjeevni_approvals.py" "$MRG/marg_take.py" "$MRG/signatures.json" "$FIN/amir_day.py" "$FIN/reports_tile.py")
SVC=clinic-finance
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/9] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] && grep -q "part $PART" KIT_ID.txt || { say "!! [1/9] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$VPY" -c "import flask" 2>/dev/null || { say "!! [1/9] the venv python lacks flask; nothing installed"; exit 1; }
for k in "$DBF" "$ADB"; do [ -f "$k" ] || { say "!! [1/9] $k must be there - nothing installed"; exit 1; }; done
say "[1/9] kit gates green (SUMS, KIT_ID part 1C, the venv's flask, the databases)"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the four files are at the kit's pins"; exit 0; fi
for f in "${ORDER[@]}"; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/9] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since part 1; nothing installed"; exit 1; }
done
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
say "[2/9] the four live files at their FROM pins (part 1 / 1B's TO)"
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s454p1c.py --finance "$FIN" --kit "$KDIR" --out "$WALK/built" | sed 's/^/   /'
for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/9] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
say "[3/9] live bytes + anchored edits (and the kit's v1.1 sheet) give exactly the kit's files (four pins match)"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && for f in "${ORDER[@]}"; do cp -p "$WALK/built/$f" "$WALK/cc/built_$f"; done
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || { say "!! [4/9] compile on both pythons failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/9] compiles on /usr/bin/python3 and the venv python (in a scratch copy)"
R="$WALK/run"
mkdir -p "$R/fin_new/finance_ui" "$R/fin_new/spine" "$R/fin_old/finance_ui" "$R/fin_old/spine" "$R/por" "$R/w" "$R/pictures" || exit 1
for side in fin_new fin_old; do
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$R/$side/finance_ui/"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$R/$side/spine/" 2>/dev/null
done
for f in "${ORDER[@]}"; do cp -p "$WALK/built/$f" "$R/fin_new/$f"; done
for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$R/por/"; done   # never the live secret, never the user store
cp -p "$POR/tile_grants.json" "$R/por/"
copydb "$DBF" "$R/scratch.db" && copydb "$ADB" "$R/scratch_assets.db" || { say "!! [5/9] no scratch copies - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd "$R" && timeout 2400 "$VPY" -B "$KDIR/walk_s454p1c.py" --fin-new "$R/fin_new" --fin-old "$R/fin_old" --por "$R/por" --db "$R/scratch.db" \
         --adb "$R/scratch_assets.db" --work "$R/w" --data-mod "$KDIR/data_s454p1c.py" --pictures "$R/pictures" 2>&1 )"
echo "$WOUT" | mask | cut -c1-900 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S454P1C GREEN" || { say "!! [5/9] walk_s454p1c red - nothing installed"; rm -rf "$WALK"; exit 1; }
[ -n "${PICS_OUT:-}" ] && mkdir -p "$PICS_OUT" && cp -p "$R/pictures"/* "$PICS_OUT/" 2>/dev/null
say "[5/9] walk_s454p1c green on scratch copies of finance.db and assets.db; its negative controls red on the box as it is (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed"; rm -rf "$WALK"; exit 0; fi
[ -d "$LOCK" ] && [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [6/9] the build lock is not held by $KIT - nothing installed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [6/9] $FIN/$f moved during the walk - nothing installed"; rm -rf "$WALK"; exit 1; }; done
copydb "$DBF" "$FIN/finance.db.bak_S454_$STAMP" || { say "!! [6/9] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do
  BAK[$f]="$FIN/$f.bak_S454_${FROM[$f]:0:8}"
  if [ -e "${BAK[$f]}" ]; then BAK[$f]="$FIN/$f.bak_S454P1C_${FROM[$f]:0:8}"; fi
  \cp -p "$FIN/$f" "${BAK[$f]}" || { say "!! [6/9] backup of $f failed - nothing placed"; rm -rf "$WALK"; exit 1; }
done
say "[6/9] finance.db.bak_S454_$STAMP made (backup API); a .bak beside each of the four files; the lock is held by $KIT"
restore() {
  say "!! RED after placing ($1) - restoring the four files byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "$FIN/$f"; done
  systemctl restart "$SVC" || true; sleep 8
  for f in "${ORDER[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f") (FROM ${FROM[$f]})"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC") · the database backup stays: $FIN/finance.db.bak_S454_$STAMP"
  rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do \cp "$WALK/built/$f" "$FIN/$f" || restore "copy $f"; done
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore "md5 read-back of $f"; done
say "[7/9] placed; md5 read back = the four TO pins"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz); c2=$(health http://127.0.0.1:8106/finance/porders); c3=$(health http://127.0.0.1:8106/finance/porders/s454/sheet.pdf)
c4=$(health http://127.0.0.1:8106/finance/purchase/page/phone-setup)
say "health : finance healthz $c1 · /finance/porders $c2 · the printed sheet $c3 · phone-setup $c4 (302/401 = the login gate, expected)"
[ "$c1" = 200 ] || restore "finance healthz"
for c in "$c2" "$c3" "$c4"; do [ "$c" = 302 ] || [ "$c" = 401 ] || restore "a gated page answered $c"; done
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
[ "$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')" = 0 ] || restore "$SVC journal errors"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
DOUT="$( cd "$FIN" && "$VPY" -B "$KDIR/data_s454p1c.py" --db "$DBF" --finance "$FIN" 2>&1 )"
echo "$DOUT" | mask | sed 's/^/   /'
echo "$DOUT" | grep -q "^S454 P1C data done" || restore "the data step"
[ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz after the data step"
for f in "${ORDER[@]}"; do md5sum "$FIN/$f"; done
rm -rf "$WALK"
say "[9/9] $SVC active; healthz 200; nothing else moved; the data steps done (above)"
say "$KIT part 1C: DONE"
