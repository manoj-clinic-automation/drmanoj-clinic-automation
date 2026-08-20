#!/bin/bash
# =====================================================================
#  S194B · ⭐4 — hand-overs to Dr Bhawna / Dr Manoj track LIVE
#
#  Until now the reserve (Dr Bhawna) and cash-with-Dr-Manoj were frozen
#  to the 17-Aug counted position (cash_custody_event only). A hand-over
#  recorded through the daily flow as a cash_movement (party dr_bhawna /
#  dr_manoj) reduced the drawer but did NOT raise the reserve, and it
#  wrongly reduced "unbanked".
#
#  After this: cash-position folds live doctor cash_movements on top of
#  the counted baseline —
#    reserve = counted(dr_bhawna) + net dr_bhawna movements
#    manoj   = counted(dr_manoj)  + net dr_manoj  movements
#    drawer  = closing - counted-baseline
#    unbanked = drawer + reserve + manoj   (a HAND-OVER leaves it
#               unchanged; only a BANK deposit reduces it)
#  The Hub Cash-position card and Darpan's Daily page drawer both track
#  live automatically (endpoint-only change; it also now returns numeric
#  *_p fields). ONE file: finance_app.py.
#
#  Self-gating (1 currency hash), ALL-GREEN smoke that grows (the ⭐4
#  checks run), rollback on any red.
# =====================================================================
set -u
cd "$(dirname "$0")"
LIVE_FIN=/root/finance/finance_app.py
SVC_F=clinic-finance.service
FIN_WANT=87cf456866237c2634c405e3dc3b8a61      # current live (S194)

echo "==============================================================="
echo " S194B · ⭐4 live doctor hand-overs (reserve / drawer / unbanked)"
echo "==============================================================="
echo "[1/8] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "      KIT_ID : $(cat KIT_ID.txt)"
echo "[2/8] currency gate"
HF=$(md5sum "$LIVE_FIN"|cut -d' ' -f1); echo "      finance_app : $HF"
[ "$HF" = "$FIN_WANT" ] || { echo '*** RED: finance_app not the expected S194 build. STOP.'; exit 1; }
echo "[3/8] baseline smoke"
CUR=$(cd /root/finance && python3 finance_app.py --selftest 2>&1|grep -m1 "SMOKE "); echo "      $CUR"
echo "$CUR"|grep -Eq "SMOKE ([0-9]+)/\1 " || { echo '*** RED baseline. STOP.'; exit 1; }
CUR_T=$(echo "$CUR"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
TS=$(date +%Y%m%d_%H%M%S); BK=/root/finance/_backup_S194B_$TS; mkdir -p "$BK"
echo "[4/8] backup -> $BK"; cp -p "$LIVE_FIN" "$BK/"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/finance_app.py" "$LIVE_FIN"; systemctl restart $SVC_F; exit 1; }
echo "[5/8] swap finance_app.py"; cp finance_app_S194B.py "$LIVE_FIN" || rollback
echo "[6/8] py_compile"; python3 -c "import py_compile;py_compile.compile('$LIVE_FIN',doraise=True);print('      OK')" || rollback
echo "[7/8] new smoke — ALL-GREEN and grown (the ⭐4 checks ran)"
NEW=$(cd /root/finance && python3 finance_app.py --selftest 2>&1|grep -m1 "SMOKE "); echo "      $NEW"
echo "$NEW"|grep -Eq "SMOKE ([0-9]+)/\1 " || rollback
NEW_T=$(echo "$NEW"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
[ "$NEW_T" -gt "$CUR_T" ] || { echo "*** RED: ⭐4 checks did not run ($CUR_T -> $NEW_T)."; rollback; }
grep -q '_mv_net' "$LIVE_FIN" && grep -q 'drawer_p' "$LIVE_FIN" || rollback
echo "      smoke grew $CUR_T -> $NEW_T"
echo "[8/8] restart + verify"; systemctl restart $SVC_F; sleep 2; systemctl is-active --quiet $SVC_F || rollback
echo "==============================================================="
echo " GREEN.  ⭐4 live.  finance_app.py $(md5sum $LIVE_FIN|cut -d' ' -f1)  smoke $NEW_T (was $CUR_T)"
echo " Record a hand-over on Darpan's page (Dr Bhawna / Dr Manoj) and the"
echo " Hub Cash-position card now moves it drawer -> reserve, live."
echo " Pin the new finance_app.py md5 into the KB Register."
echo "==============================================================="
