#!/bin/bash
# S193_CUST2 · fix custody balances (comma-string parse). In-place html patch.
set -u
cd "$(dirname "$0")"
LIVE_HTML=/root/finance/finance_ui/finance_approvals.html
SVC_F=clinic-finance.service
HTML_WANT=2e3b40cc5fc51ad54de2382548a6cdf5      # after S193_CUST, current live
echo "==============================================================="
echo " S193_CUST2 · custody balances now parse (were comma strings)"
echo "==============================================================="
echo "[1/6] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "[2/6] currency gate"
H=$(md5sum "$LIVE_HTML" | cut -d' ' -f1); echo "      approvals html : $H"
[ "$H" = "$HTML_WANT" ] || { echo '*** RED: approvals html not the expected build. STOP.'; exit 1; }
TS=$(date +%Y%m%d_%H%M%S)
echo "[3/6] backup"
BK=/root/finance/_backup_S193_CUST2_$TS; mkdir -p "$BK/finance_ui"; cp -p "$LIVE_HTML" "$BK/finance_ui/"; echo "      -> $BK"
rollback(){ echo "*** RED -- ROLLING BACK."; cp -p "$BK/finance_ui/finance_approvals.html" "$LIVE_HTML"; systemctl restart $SVC_F; exit 1; }
echo "[4/6] in-place patch"
python3 patch_custody_fix.py || rollback
echo "[5/6] sanity: hooks still present"
grep -q 'id="custHeld"' "$LIVE_HTML" && grep -q 'function loadCustody' "$LIVE_HTML" || rollback
echo "      hooks OK"
echo "[6/6] restart + verify"
systemctl restart $SVC_F; sleep 2; systemctl is-active --quiet $SVC_F || rollback
echo "==============================================================="
echo " GREEN.  S193_CUST2 is live.  approvals html $(md5sum $LIVE_HTML | cut -d' ' -f1)"
echo " Hard-refresh the Hub (Ctrl-Shift-R): custody now shows the total"
echo " Rs 1,75,198 and each hand's figure. Pin the new md5."
echo "==============================================================="
