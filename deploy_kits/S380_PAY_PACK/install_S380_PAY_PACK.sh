#!/bin/bash
# =============================================================================
#  install_S380_PAY_PACK.sh · kit S380_PAY_PACK (session 281, Sanjeevni, 23-Sep-2026) · F-616 · D605
#  The owner finalised August and printed it: one paper came out, five blank pages behind it, no covering
#  letter, no signature block. Now ONE button prints the month's pack -- the covering letter (portrait), the
#  annexure the bank gets (landscape), the payment sheet (portrait) -- each on its own sheet, the last two
#  signed For SANJEEVNI MEDICOS / Authorized Signatory / <name>. The pay page's own print gives the annexure
#  alone, one sheet, nothing blank. The letter's date, cheque number and the name stay typable after FINAL.
#  The email file is named by the month it is PAID in (August's -> NEFT ADVICE SEPTEMBER 2026.xlsx).
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S380_PAY_PACK/install_S380_PAY_PACK.sh
#
#    /root/finance/purchase_app.py  8788962a (S371) -> 9ad50878 (apply_s380.py, anchored edits)
#    clinic-finance RESTARTED -- DECLARED. finance.db: no row is written by the install.
# =============================================================================
set -u
KIT="S380_PAY_PACK"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; FIN="${FIN:-/root/finance}"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s380_walk_$STAMP"
FROM=8788962a463a9d1fe65a17e193395645
TO=9ad508789e2821c284b48ef6a4446cfa
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
say "[1/6] kit gates green"
if [ "$(m5 "$FIN/purchase_app.py")" = "$TO" ]; then say "-- ALREADY INSTALLED (purchase_app.py ${TO:0:8})"; exit 0; fi
[ "$(m5 "$FIN/purchase_app.py")" = "$FROM" ] || { say "!! [2/6] $FIN/purchase_app.py is not its pin ${FROM:0:8} - nothing installed"; exit 1; }
say "[2/6] live purchase_app.py at its pin"
mkdir -p "$WALK/app/finance_ui" "$WALK/kit" || exit 1
cp -p apply_s380.py walk_s380.py "$WALK/kit/" || exit 1
for p in "$FIN"/*.py "$FIN"/*.json "$FIN"/*.sql "$FIN"/*.html "$FIN"/*.txt; do [ -f "$p" ] && cp -p "$p" "$WALK/app/"; done
cp -p "$FIN"/finance_ui/* "$WALK/app/finance_ui/" 2>/dev/null
( cd "$WALK/kit" && "$SPY" -B apply_s380.py --dir "$FIN" --out "$WALK/app" ) | sed 's/^/   /'
[ "$(m5 "$WALK/app/purchase_app.py")" = "$TO" ] || { say "!! [3/6] the patch does not produce the predicted purchase_app.py - nothing installed"; rm -rf "$WALK"; exit 1; }
( cd "$WALK/app" && "$SPY" -m py_compile purchase_app.py && "$VPY" -m py_compile purchase_app.py ) || { say "!! [3/6] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
find "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/6] the patch produces exactly the predicted bytes; compiles on both pythons"
"$SPY" - "$FIN/finance.db" "$WALK/scratch.db" <<'PYEOF' || { say "!! [4/6] could not copy the database - nothing installed"; rm -rf "$WALK"; exit 1; }
import sqlite3, sys
s = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close()
PYEOF
WOUT="$( cd "$WALK/kit" && timeout 600 "$SPY" -B walk_s380.py --app "$WALK/app" --db "$WALK/scratch.db" 2>&1 )"
echo "$WOUT" | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S380 GREEN" || { say "!! [4/6] walk red - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[4/6] walk green on a scratch copy of the live database (above)"
restore() {
  say "!! RED after placing - restoring byte-identically"
  [ -f "$FIN/purchase_app.py.bak_S380_${FROM:0:8}" ] && \cp -p "$FIN/purchase_app.py.bak_S380_${FROM:0:8}" "$FIN/purchase_app.py"
  systemctl restart clinic-finance 2>/dev/null; sleep 3
  say "   purchase_app.py $(m5 "$FIN/purchase_app.py") · healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)"
  exit 1
}
\cp -p "$FIN/purchase_app.py" "$FIN/purchase_app.py.bak_S380_${FROM:0:8}" || restore
( cd "$KDIR" && "$SPY" -B apply_s380.py --dir "$FIN" ) | sed 's/^/   /'
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
[ "$(m5 "$FIN/purchase_app.py")" = "$TO" ] || restore
say "[5/6] .bak_S380_${FROM:0:8} beside the file; placed; md5 read back = the kit"
systemctl restart clinic-finance || restore
sleep 3
systemctl is-active --quiet clinic-finance || restore
HC=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
[ "$HC" = "200" ] || restore
md5sum "$FIN/purchase_app.py"
say "[6/6] $KIT: DONE -- clinic-finance up, healthz $HC. Open the payment sheet for August: type the cheque number and your signature name under '5 · The covering letter', save, then 'Print the bank pack'."
