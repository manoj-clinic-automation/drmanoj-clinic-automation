#!/bin/bash
# =====================================================================
#  S195_NCSCAN — Daily Sale v2: no-payment bills entry + per-bill scan,
#  compact mobile layout, prominent live drawer, loud confirmations,
#  submit-with-attachments list.
#
#  Two files: finance_app.py (backend: noncash bill uid + noncash_attachment
#  table + /finance/scan-noncash host page + upload endpoint + day-read
#  has_file, mirroring the proven expense-scan) and finance_ui/finance_daily.html
#  (the compact page). No data change beyond additive DDL (a nullable column +
#  a new table), created lazily.
#
#  Currency-gated to the live S194E build. Backs up BOTH files, runs the app's
#  own --selftest (must stay ALL-GREEN and not shrink), restarts, and ROLLS
#  BACK BOTH on any red.
# =====================================================================
set -u
cd "$(dirname "$0")"
FIN=/root/finance/finance_app.py
HTML=/root/finance/finance_ui/finance_daily.html
SVC=clinic-finance.service
FIN_WANT=d2863c30ed0d3cc23126c7da13d9fe9b     # live = S194E

echo "==============================================================="
echo " S195_NCSCAN · no-payment bills + per-bill scan (Daily Sale v2)"
echo "==============================================================="
echo "[1/8] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }

echo "[2/8] currency gate (finance_app.py must be live S194E)"
[ -f "$FIN" ] || { echo "*** RED: $FIN missing."; exit 1; }
[ -f "$HTML" ] || { echo "*** RED: $HTML missing."; exit 1; }
H=$(md5sum "$FIN"|cut -d' ' -f1); echo "      finance_app : $H"
[ "$H" = "$FIN_WANT" ] || { echo "*** RED: finance_app is not S194E ($FIN_WANT). STOP. Tell Cowork this hash."; exit 1; }

echo "[3/8] baseline smoke"
CUR=$(cd /root/finance && python3 finance_app.py --selftest 2>&1|grep -m1 "SMOKE "); echo "      $CUR"
echo "$CUR"|grep -Eq "SMOKE ([0-9]+)/\1 " || { echo '*** RED: baseline not all-green. STOP.'; exit 1; }
CUR_T=$(echo "$CUR"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')

TS=$(date +%Y%m%d_%H%M%S); BK=/root/finance/_backup_S195_NCSCAN_$TS; mkdir -p "$BK"
echo "[4/8] backup -> $BK"; cp -p "$FIN" "$BK/finance_app.py"; cp -p "$HTML" "$BK/finance_daily.html"
rollback(){ echo "*** RED -- ROLLBACK (both files)."; cp -p "$BK/finance_app.py" "$FIN"; cp -p "$BK/finance_daily.html" "$HTML"; systemctl restart $SVC; sleep 2; echo "   service: $(systemctl is-active $SVC)"; exit 1; }

echo "[5/8] swap both files"
cp finance_app.py "$FIN" || rollback
cp finance_daily.html "$HTML" || rollback
echo "[6/8] py_compile"; python3 -c "import py_compile; py_compile.compile('$FIN',doraise=True); print('      OK')" || rollback

echo "[7/8] new smoke — ALL-GREEN, not shrunk"
NEW=$(cd /root/finance && python3 finance_app.py --selftest 2>&1|grep -m1 "SMOKE "); echo "      $NEW"
echo "$NEW"|grep -Eq "SMOKE ([0-9]+)/\1 " || rollback
NEW_T=$(echo "$NEW"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
[ "$NEW_T" -ge "$CUR_T" ] || { echo "*** RED: smoke shrank ($CUR_T -> $NEW_T)."; rollback; }

echo "[8/8] restart + verify"; systemctl restart $SVC; sleep 2; systemctl is-active --quiet $SVC || rollback

echo "==============================================================="
echo " GREEN.  Daily Sale v2 now has no-payment bills + per-bill scan."
echo " finance_app.py $(md5sum $FIN|cut -d' ' -f1)  smoke $NEW_T (was $CUR_T)"
echo " Backup: $BK .  Pin the new md5."
echo "==============================================================="
