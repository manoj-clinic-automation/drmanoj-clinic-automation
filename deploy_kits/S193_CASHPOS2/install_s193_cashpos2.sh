#!/bin/bash
# S193_CASHPOS2 · cash-position day-wise drawer starts at the last clearing
# (reserve date), so it shows 17/18/19 Aug cleanly instead of 30 days of
# July with false negatives. finance_app.py swap only. Zero-delta smoke gate.
set -u
cd "$(dirname "$0")"
LIVE_FIN=/root/finance/finance_app.py
SVC_F=clinic-finance.service
FIN_WANT=fa87fd40446957224b4aa39915beb4c2      # S193_CASHPOS, current live
echo "==============================================================="
echo " S193_CASHPOS2 · drawer day-wise since last clearing"
echo "==============================================================="
echo "[1/8] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "[2/8] currency gate"
H=$(md5sum "$LIVE_FIN"|cut -d' ' -f1); echo "      finance_app : $H"
[ "$H" = "$FIN_WANT" ] || { echo '*** RED: finance_app not the expected build. STOP.'; exit 1; }
echo "[3/8] baseline smoke"
CUR=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE "); echo "      $CUR"
echo "$CUR" | grep -Eq "SMOKE ([0-9]+)/\1 " || { echo '*** RED. STOP.'; exit 1; }
CUR_N=$(echo "$CUR" | sed -n 's/.*SMOKE \([0-9]*\/[0-9]*\).*/\1/p')
TS=$(date +%Y%m%d_%H%M%S); BK=/root/finance/_backup_S193_CASHPOS2_$TS; mkdir -p "$BK"
echo "[4/8] backup -> $BK"; cp -p "$LIVE_FIN" "$BK/"
rollback(){ echo "*** RED -- ROLLING BACK."; cp -p "$BK/finance_app.py" "$LIVE_FIN"; systemctl restart $SVC_F; exit 1; }
echo "[5/8] swap"; cp finance_app_S193.py "$LIVE_FIN" || rollback
echo "[6/8] py_compile"; python3 -c "import py_compile; py_compile.compile('$LIVE_FIN',doraise=True); print('      OK')" || rollback
echo "[7/8] new smoke (zero delta)"
NEW=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE "); echo "      $NEW"
echo "$NEW" | grep -Eq "SMOKE ([0-9]+)/\1 " || rollback
NEW_N=$(echo "$NEW" | sed -n 's/.*SMOKE \([0-9]*\/[0-9]*\).*/\1/p')
[ "$NEW_N" = "$CUR_N" ] || { echo "*** RED: smoke changed."; rollback; }
echo "[8/8] restart + verify"; systemctl restart $SVC_F; sleep 2; systemctl is-active --quiet $SVC_F || rollback
echo "==============================================================="
echo " GREEN.  finance_app.py $(md5sum $LIVE_FIN|cut -d' ' -f1)  smoke $NEW_N"
echo " Hard-refresh the Hub; 'drawer day by day' now shows 17/18/19 Aug only."
echo " Pin the new md5."
echo "==============================================================="
