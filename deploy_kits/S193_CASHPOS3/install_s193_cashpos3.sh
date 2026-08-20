#!/bin/bash
# S193_CASHPOS3 · Cash position: every line clickable-to-expand + cache-busted
# fetch (fixes stale-cache display). finance_app swap + html patch.
set -u
cd "$(dirname "$0")"
LIVE_FIN=/root/finance/finance_app.py
LIVE_HTML=/root/finance/finance_ui/finance_approvals.html
SVC_F=clinic-finance.service
FIN_WANT=18d2f8a754312af006787a3867d9ca5c      # S193_CASHPOS2
HTML_WANT=0a786f206306a0878d7c9998178d986f     # S193_CASHPOS
echo "==============================================================="
echo " S193_CASHPOS3 · expandable cash-position lines + cache-bust"
echo "==============================================================="
echo "[1/10] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "[2/10] gates"
HF=$(md5sum "$LIVE_FIN"|cut -d' ' -f1); echo "      finance_app : $HF"
[ "$HF" = "$FIN_WANT" ] || { echo '*** RED: finance_app not expected. STOP.'; exit 1; }
HH=$(md5sum "$LIVE_HTML"|cut -d' ' -f1); echo "      html        : $HH"
[ "$HH" = "$HTML_WANT" ] || { echo '*** RED: html not expected. STOP.'; exit 1; }
echo "[3/10] baseline smoke"
CUR=$(cd /root/finance && python3 finance_app.py --selftest 2>&1|grep -m1 "SMOKE "); echo "      $CUR"
echo "$CUR"|grep -Eq "SMOKE ([0-9]+)/\1 " || { echo '*** RED. STOP.'; exit 1; }
CUR_N=$(echo "$CUR"|sed -n 's/.*SMOKE \([0-9]*\/[0-9]*\).*/\1/p')
TS=$(date +%Y%m%d_%H%M%S); BK=/root/finance/_backup_S193_CASHPOS3_$TS; mkdir -p "$BK/finance_ui"
echo "[4/10] backup -> $BK"; cp -p "$LIVE_FIN" "$BK/"; cp -p "$LIVE_HTML" "$BK/finance_ui/"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/finance_app.py" "$LIVE_FIN"; cp -p "$BK/finance_ui/finance_approvals.html" "$LIVE_HTML"; systemctl restart $SVC_F; exit 1; }
echo "[5/10] swap finance_app"; cp finance_app_S193.py "$LIVE_FIN" || rollback
echo "[6/10] patch html"; python3 patch_cashpos3_hub.py || rollback
echo "[7/10] py_compile"; python3 -c "import py_compile; py_compile.compile('$LIVE_FIN',doraise=True); print('      OK')" || rollback
echo "[8/10] new smoke (zero delta)"
NEW=$(cd /root/finance && python3 finance_app.py --selftest 2>&1|grep -m1 "SMOKE "); echo "      $NEW"
echo "$NEW"|grep -Eq "SMOKE ([0-9]+)/\1 " || rollback
NEW_N=$(echo "$NEW"|sed -n 's/.*SMOKE \([0-9]*\/[0-9]*\).*/\1/p'); [ "$NEW_N" = "$CUR_N" ] || { echo "*** RED smoke changed."; rollback; }
echo "[9/10] sanity"; grep -q 'reserve_detail' "$LIVE_FIN" && grep -q 'no-store' "$LIVE_HTML" || rollback; echo "      OK"
echo "[10/10] restart"; systemctl restart $SVC_F; sleep 2; systemctl is-active --quiet $SVC_F || rollback
echo "==============================================================="
echo " GREEN.  finance_app $(md5sum $LIVE_FIN|cut -d' ' -f1)  html $(md5sum $LIVE_HTML|cut -d' ' -f1)  smoke $NEW_N"
echo " Hard-refresh once. Every Cash-position line now expands on tap;"
echo " the fetch is cache-busted so it can never show stale data again."
echo "==============================================================="
