#!/bin/bash
# =============================================================================
#  install_S240_STOCK_GATE_R2.sh · kit S240_STOCK_GATE_R2 · the owner's correction of 11-Sep
#
#  Run by:  bash /root/deploy/vps_deploy.sh S240_STOCK_GATE_R2
#
#  stock_app.py over the S240 gate 5227c1d1. ONE change, the owner's correction ("Ravi bill date is 6 but it
#  arrived late, don't confuse, the physical stock was the actual inventory at that time"):
#    a purchase bill keyed after the stock export is NAMED (amber, COUNT CHECK line) -- no longer a refusal,
#    because its invoice date is not the day the goods arrived. The other two refusals stand: no Marg stock
#    closing for the day, and purchases not exported up to the stock day.
#  RED after the restart -> 5227c1d1 restored, service restarted, exit 1.
# =============================================================================
set -u
KIT="S240_STOCK_GATE_R2"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="/usr/bin/python3"
FIN="${FINANCE_DIR:-/root/finance}"
DB="$FIN/finance.db"
LIVE_EXPECT="5227c1d16cfdd8288a1783557f5dddb2"
BAK=""; RESTARTED=0
red() { echo "!! RED -- $*"
  if [ -n "$BAK" ] && [ -f "$BAK" ] && [ "$RESTARTED" -eq 1 ]; then
    \cp -f "$BAK" "$FIN/stock_app.py" && echo "   restored stock_app.py from $BAK"
    systemctl restart clinic-finance.service; sleep 4
    systemctl is-active --quiet clinic-finance.service && echo "   service back up on 5227c1d1"
  fi; exit 1; }

cd "$KDIR" || red "cannot enter the kit folder"
md5sum -c SUMS.md5 >/dev/null 2>&1 || red "SUMS.md5 gate failed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || red "KIT_ID names a different kit"
NEW="$(md5sum stock_app.py | awk '{print $1}')"
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$NEW" ] || red "KIT_ID does not match stock_app.py (F-88)"
LIVE="$(md5sum $FIN/stock_app.py | awk '{print $1}')"
if [ "$LIVE" != "$NEW" ] && [ "$LIVE" != "$LIVE_EXPECT" ]; then
  red "live stock_app.py is $LIVE, not $LIVE_EXPECT -- it moved since this kit was built; NOTHING changed"
fi
echo "-- gates green; live stock_app.py ${LIVE:0:8}"
$PY -m py_compile stock_app.py || red "py_compile"
if [ "$LIVE" != "$NEW" ]; then
  BAK="$FIN/stock_app.py.bak_S240R2_${LIVE:0:8}"
  \cp -f "$FIN/stock_app.py" "$BAK" || red "could not back up stock_app.py"
  \cp -f stock_app.py "$FIN/stock_app.py"
fi
[ "$(md5sum $FIN/stock_app.py | awk '{print $1}')" = "$NEW" ] || red "stock_app.py did not land"
RESTARTED=1
systemctl restart clinic-finance.service; sleep 4
systemctl is-active --quiet clinic-finance.service || red "clinic-finance.service did not come back"
HZ="$(curl -s -o /dev/null -w '%{http_code}' localhost:8106/finance/healthz)"
CNT="$(curl -s -o /dev/null -w '%{http_code}' localhost:8106/finance/stock/page/count)"
echo "-- healthz $HZ · count page anonymous $CNT (302 = login gate, route mounted)"
[ "$HZ" = "200" ] && [ "$CNT" = "302" ] || red "the app did not answer as expected"
RESTARTED=2
echo ""
echo "================ THE GATE ON TODAY'S DATA (read only) ================"
cd "$FIN" && $PY - "$DB" "$FIN" <<'PYEOF'
import sqlite3, sys
sys.path.insert(0, sys.argv[2])
import stock_app as S
c = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
g = S.stock_gate(c)
print("  newest stock day %s (Marg export reached here %s): %s" % (g["as_on"], g["stock_at"] or "never", g["verdict"].upper()))
for r in g["reasons"]:
    print("   - " + r)
for n in g["notes"]:
    print("   . " + n)
for d in ("05-09-2026", "06-09-2026"):
    x = S.stock_gate(c, d)
    msg = (x["reasons"] or x["notes"] or [""])[0]
    print("  %s: %s%s" % (d, x["verdict"].upper(), (" -- " + msg[:110]) if msg else ""))
PYEOF
echo "======================================================================"
echo ""
echo "PINS  stock_app.py $(md5sum $FIN/stock_app.py | awk '{print $1}')"
echo ""
echo "$KIT GREEN -- a late-keyed bill is now named, not a refusal."
