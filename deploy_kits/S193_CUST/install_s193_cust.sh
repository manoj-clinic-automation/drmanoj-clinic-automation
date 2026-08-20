#!/bin/bash
# =====================================================================
#  S193_CUST · clearer, expandable Cash-custody box (Hub).
#  In-place patch to finance_approvals.html — client render only, no
#  number changes. Self-gating on the live html hash, rolls back on red.
# =====================================================================
set -u
cd "$(dirname "$0")"
LIVE_HTML=/root/finance/finance_ui/finance_approvals.html
SVC_F=clinic-finance.service
HTML_WANT=ea874fec873e282c5e3c38c74bd4582e     # after S193_DISC, current live

echo "==============================================================="
echo " S193_CUST · cash-custody at a glance + expandable"
echo "==============================================================="
echo "[1/6] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "[2/6] currency gate"
H=$(md5sum "$LIVE_HTML" | cut -d' ' -f1); echo "      approvals html : $H"
[ "$H" = "$HTML_WANT" ] || { echo '*** RED: approvals html is not the expected build. STOP.'; exit 1; }
TS=$(date +%Y%m%d_%H%M%S)
echo "[3/6] backup"
BK=/root/finance/_backup_S193_CUST_$TS; mkdir -p "$BK/finance_ui"; cp -p "$LIVE_HTML" "$BK/finance_ui/"
echo "      -> $BK"
rollback(){ echo "*** RED -- ROLLING BACK."; cp -p "$BK/finance_ui/finance_approvals.html" "$LIVE_HTML"; systemctl restart $SVC_F; exit 1; }
echo "[4/6] in-place patch"
python3 patch_custody_ui.py || rollback
echo "[5/6] sanity: the two custody hooks still present"
grep -q 'id="custHeld"' "$LIVE_HTML" && grep -q 'loadCustody' "$LIVE_HTML" || rollback
echo "      hooks OK"
echo "[6/6] restart + verify"
systemctl restart $SVC_F; sleep 2; systemctl is-active --quiet $SVC_F || rollback
echo "==============================================================="
echo " GREEN.  S193_CUST is live."
echo "   approvals html  $(md5sum $LIVE_HTML | cut -d' ' -f1)"
echo " Refresh the Hub -> Cash custody now shows every hand's figure at a"
echo " glance; tap a name to expand its movements. Pin the new md5."
echo "==============================================================="
