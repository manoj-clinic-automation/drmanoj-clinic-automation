#!/bin/bash
# =====================================================================
#  S193_CASHPOS · Cash position (drawer day-wise + parked + banked),
#  reconciled, for BOTH Darpan and the owner. Also folds in the custody
#  comma-string parse fix (supersedes S193_CUST2 — run this, not that).
#   * finance_app.py  -> new /finance/api/cash-position endpoint
#   * finance_approvals.html -> custody fix + "Cash position" card
#  Self-gating, measured ZERO-delta smoke, rolls back on any red.
# =====================================================================
set -u
cd "$(dirname "$0")"
LIVE_FIN=/root/finance/finance_app.py
LIVE_HTML=/root/finance/finance_ui/finance_approvals.html
SVC_F=clinic-finance.service
FIN_WANT=51245f8ba598fd5603b88fa90b0ca945      # after S193_STALE, current live
HTML_WANT=2e3b40cc5fc51ad54de2382548a6cdf5     # after S193_CUST, current live (pre-CUST2)

echo "==============================================================="
echo " S193_CASHPOS · cash position + custody parse fix"
echo "==============================================================="
echo "[1/10] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "[2/10] currency gates"
HF=$(md5sum "$LIVE_FIN"|cut -d' ' -f1); echo "      finance_app : $HF"
[ "$HF" = "$FIN_WANT" ] || { echo '*** RED: finance_app not the expected build (did S193_CUST2 already run? tell Claude). STOP.'; exit 1; }
HH=$(md5sum "$LIVE_HTML"|cut -d' ' -f1); echo "      approvals html: $HH"
[ "$HH" = "$HTML_WANT" ] || { echo '*** RED: approvals html not the expected build. STOP.'; exit 1; }
echo "[3/10] baseline smoke"
CUR=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE "); echo "      $CUR"
echo "$CUR" | grep -Eq "SMOKE ([0-9]+)/\1 " || { echo '*** RED: baseline not green. STOP.'; exit 1; }
CUR_N=$(echo "$CUR" | sed -n 's/.*SMOKE \([0-9]*\/[0-9]*\).*/\1/p')
TS=$(date +%Y%m%d_%H%M%S)
echo "[4/10] backup"
BK=/root/finance/_backup_S193_CASHPOS_$TS; mkdir -p "$BK/finance_ui"
cp -p "$LIVE_FIN" "$BK/"; cp -p "$LIVE_HTML" "$BK/finance_ui/"; echo "      -> $BK"
rollback(){ echo "*** RED -- ROLLING BACK BOTH."; cp -p "$BK/finance_app.py" "$LIVE_FIN"; cp -p "$BK/finance_ui/finance_approvals.html" "$LIVE_HTML"; systemctl restart $SVC_F; exit 1; }
echo "[5/10] swap finance_app.py"
cp finance_app_S193.py "$LIVE_FIN" || rollback
echo "[6/10] patch finance_approvals.html"
python3 patch_cashpos_hub.py || rollback
echo "[7/10] py_compile"
python3 -c "import py_compile; py_compile.compile('$LIVE_FIN',doraise=True); print('      compile OK')" || rollback
echo "[8/10] new smoke — green + zero delta"
NEW=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE "); echo "      $NEW"
echo "$NEW" | grep -Eq "SMOKE ([0-9]+)/\1 " || rollback
NEW_N=$(echo "$NEW" | sed -n 's/.*SMOKE \([0-9]*\/[0-9]*\).*/\1/p')
[ "$NEW_N" = "$CUR_N" ] || { echo "*** RED: smoke changed ($CUR_N -> $NEW_N)."; rollback; }
echo "[9/10] sanity: endpoint + card present"
grep -q 'def api_cash_position' "$LIVE_FIN" && grep -q 'id="cashPosCard"' "$LIVE_HTML" || rollback
echo "      hooks OK"
echo "[10/10] restart + verify"
systemctl restart $SVC_F; sleep 2; systemctl is-active --quiet $SVC_F || rollback
echo "==============================================================="
echo " GREEN.  S193_CASHPOS is live."
echo "   finance_app.py  $(md5sum $LIVE_FIN|cut -d' ' -f1)"
echo "   approvals html  $(md5sum $LIVE_HTML|cut -d' ' -f1)"
echo "   smoke unchanged : $NEW_N"
echo " Hard-refresh the Hub (Ctrl-Shift-R). New 'Cash position' card shows"
echo " Darpan drawer Rs 65,697 (tap 'drawer day by day'), reserve Rs 1,56,235,"
echo " Dr Manoj Rs 18,963, unbanked Rs 2,40,895, banked Rs 15,70,600."
echo " Pin both new md5s. (Darpan's own page panel is the next kit.)"
echo "==============================================================="
