#!/bin/bash
# S193_CASHPOS4 · restore loud stat tiles for each cash-position line (still tap-to-expand).
set -u
cd "$(dirname "$0")"
LIVE_HTML=/root/finance/finance_ui/finance_approvals.html
SVC_F=clinic-finance.service
HTML_WANT=44a0401fe7b47073fc80d39e476a4f60      # S193_CASHPOS3, current live
echo "=== S193_CASHPOS4 · loud cash-position tiles ==="
echo "[1/6] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "[2/6] gate"; H=$(md5sum "$LIVE_HTML"|cut -d' ' -f1); echo "      html : $H"
[ "$H" = "$HTML_WANT" ] || { echo '*** RED: html not expected. STOP.'; exit 1; }
TS=$(date +%Y%m%d_%H%M%S); BK=/root/finance/_backup_S193_CASHPOS4_$TS; mkdir -p "$BK/finance_ui"
echo "[3/6] backup -> $BK"; cp -p "$LIVE_HTML" "$BK/finance_ui/"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/finance_ui/finance_approvals.html" "$LIVE_HTML"; systemctl restart $SVC_F; exit 1; }
echo "[4/6] patch"; python3 patch_cashpos4_hub.py || rollback
echo "[5/6] sanity"; grep -q 'id="cashPos"' "$LIVE_HTML" && grep -q 'function loadCashPos' "$LIVE_HTML" || rollback; echo "      OK"
echo "[6/6] restart"; systemctl restart $SVC_F; sleep 2; systemctl is-active --quiet $SVC_F || rollback
echo "=== GREEN. html $(md5sum $LIVE_HTML|cut -d' ' -f1). Refresh once; each line is a loud tile you can tap to expand. Pin the md5. ==="
