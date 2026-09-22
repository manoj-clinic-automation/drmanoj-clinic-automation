#!/bin/bash
# =============================================================================
#  install_S371_PURCHASE_WRONG_RESOLVE.sh · kit S371_PURCHASE_WRONG_RESOLVE (session 281, Sanjeevni, 22-Sep-2026)
#  F-614: a purchase bill marked WRONG could never be cleared once Marg re-exported the right amount -- the Correct
#  button left with the disagreement, and the month could never finalise. Now a WRONG bill resolves itself when
#  Marg's next bill-wise / supplier-wise export carries the amount marked right, and keeps its Correct button
#  until the month is final. The owner's August: bills 148 (Kedar, 4,608) and 67025 (L.K. Drug House, 1,862).
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S371_PURCHASE_WRONG_RESOLVE/install_S371_PURCHASE_WRONG_RESOLVE.sh
#
#    /root/finance/purchase_app.py  d1476f80 (S255) -> TO (apply_s371.py, anchored edits)
#    clinic-finance RESTARTED -- DECLARED. finance.db: the resolver then clears the WRONG bills Marg has answered
#    (an audit row each), after a backup.
# =============================================================================
set -u
KIT="S371_PURCHASE_WRONG_RESOLVE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; FIN="${FIN:-/root/finance}"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s371_walk_$STAMP"
FROM=d1476f80836e8b68fae2da1855c7105f
TO=8788962a463a9d1fe65a17e193395645
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
say "[1/7] kit gates green"
if [ "$(m5 "$FIN/purchase_app.py")" = "$TO" ]; then
  say "-- ALREADY INSTALLED; the resolver, once more:"; FINANCE_APP_DIR="$FIN" "$VPY" -B resolve_now.py; exit 0; fi
[ "$(m5 "$FIN/purchase_app.py")" = "$FROM" ] || { say "!! [2/7] $FIN/purchase_app.py is not its pin ${FROM:0:8} - nothing installed"; exit 1; }
say "[2/7] live purchase_app.py at its pin"
mkdir -p "$WALK/app/finance_ui" "$WALK/kit" || exit 1
cp -p apply_s371.py walk_s371.py resolve_now.py "$WALK/kit/" || exit 1
for p in "$FIN"/*.py "$FIN"/*.json "$FIN"/*.sql "$FIN"/*.html "$FIN"/*.txt; do [ -f "$p" ] && cp -p "$p" "$WALK/app/"; done
cp -p "$FIN"/finance_ui/* "$WALK/app/finance_ui/" 2>/dev/null
( cd "$WALK/kit" && "$SPY" -B apply_s371.py --dir "$FIN" --out "$WALK/app" ) | sed 's/^/   /'
[ "$(m5 "$WALK/app/purchase_app.py")" = "$TO" ] || { say "!! [3/7] the patch does not produce the predicted purchase_app.py - nothing installed"; rm -rf "$WALK"; exit 1; }
( cd "$WALK/app" && "$SPY" -m py_compile purchase_app.py && "$VPY" -m py_compile purchase_app.py ) || { say "!! [3/7] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
find "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the patch produces exactly the predicted bytes; compiles on both pythons"
"$SPY" - "$FIN/finance.db" "$WALK/scratch.db" <<'PYEOF' || { say "!! [4/7] could not copy the database - nothing installed"; rm -rf "$WALK"; exit 1; }
import sqlite3, sys
s = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close()
PYEOF
WOUT="$( cd "$WALK/kit" && timeout 600 "$SPY" -B walk_s371.py --app "$WALK/app" --db "$WALK/scratch.db" 2>&1 )"
echo "$WOUT" | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S371 GREEN" || { say "!! [4/7] walk red - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[4/7] walk green on a scratch copy of the live database (above)"
restore() {
  say "!! RED after placing - restoring byte-identically"
  [ -f "$FIN/purchase_app.py.bak_S371_${FROM:0:8}" ] && \cp -p "$FIN/purchase_app.py.bak_S371_${FROM:0:8}" "$FIN/purchase_app.py"
  systemctl restart clinic-finance 2>/dev/null; sleep 3
  say "   purchase_app.py $(m5 "$FIN/purchase_app.py") · healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)"
  exit 1
}
"$SPY" - "$FIN/finance.db" "$FIN/finance.db.bak_S371_$STAMP" <<'PYEOF' || { say "!! [5/7] database backup failed - nothing installed"; exit 1; }
import sqlite3, sys
s = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close()
PYEOF
\cp -p "$FIN/purchase_app.py" "$FIN/purchase_app.py.bak_S371_${FROM:0:8}" || restore
( cd "$KDIR" && "$SPY" -B apply_s371.py --dir "$FIN" ) | sed 's/^/   /'
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
[ "$(m5 "$FIN/purchase_app.py")" = "$TO" ] || restore
say "[5/7] database backed up (finance.db.bak_S371_$STAMP); .bak_S371_${FROM:0:8} beside the file; placed; md5 read back = the kit"
systemctl restart clinic-finance || restore
sleep 3
systemctl is-active --quiet clinic-finance || restore
HC=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
[ "$HC" = "200" ] || restore
say "[6/7] clinic-finance up, healthz $HC"
( cd "$KDIR" && FINANCE_APP_DIR="$FIN" "$VPY" -B resolve_now.py ) | sed 's/^/   /'
md5sum "$FIN/purchase_app.py"
say "[7/7] $KIT: DONE -- open August's purchase page: the resolved bills read Correct with Marg's re-export named; FINALISE is yours."
