#!/bin/bash
# =====================================================================
#  S194E · Marg AUTO-REPLAY  (the switch + hardened daily page are already
#  live from S194C; this adds only the auto-replay to finance_app.py).
#
#  AUTO-REPLAY: the moment a day is filed/saved, any PENDING Marg push
#  that carries that day is ingested automatically (payload kept for
#  exactly this, F-155). A report pushed BEFORE the day was filed no
#  longer strands its bills. (17/18/19 Aug predate this and their
#  payloads were already pruned — re-load those once from the exports.)
#
#  ONE file: finance_app.py (swap). No DB change, no page change.
#  Currency gate, ALL-GREEN smoke that GREW (the 2 auto-replay checks),
#  rollback on any red.
# =====================================================================
set -u
cd "$(dirname "$0")"

LIVE_FIN=/root/finance/finance_app.py
SVC_F=clinic-finance.service

FIN_WANT=45845f6c68ccca26fffaa80652503875       # current live = S194C (the switch)

echo "==============================================================="
echo " S194E · Marg auto-replay"
echo "==============================================================="

echo "[1/8] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "      KIT_ID : $(cat KIT_ID.txt)"

echo "[2/8] currency gate"
H=$(md5sum "$LIVE_FIN"|cut -d' ' -f1); echo "      finance_app : $H"
[ "$H" = "$FIN_WANT" ] || { echo "*** RED: finance_app is not the S194C build. STOP."; echo "   (if it is something else, tell me the hash and I reissue.)"; exit 1; }

echo "[3/8] baseline smoke"
CUR=$(cd /root/finance && python3 finance_app.py --selftest 2>&1|grep -m1 "SMOKE "); echo "      $CUR"
echo "$CUR"|grep -Eq "SMOKE ([0-9]+)/\1 " || { echo '*** RED. STOP.'; exit 1; }
CUR_T=$(echo "$CUR"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')

TS=$(date +%Y%m%d_%H%M%S); BK=/root/finance/_backup_S194E_$TS; mkdir -p "$BK"
echo "[4/8] backup -> $BK"; cp -p "$LIVE_FIN" "$BK/"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/finance_app.py" "$LIVE_FIN"; systemctl restart $SVC_F; exit 1; }

echo "[5/8] swap finance_app.py"; cp finance_app_S194E.py "$LIVE_FIN" || rollback
echo "[6/8] py_compile"; python3 -c "import py_compile; py_compile.compile('$LIVE_FIN',doraise=True); print('      OK')" || rollback

echo "[7/8] new smoke — ALL-GREEN and grown (auto-replay checks ran)"
NEW=$(cd /root/finance && python3 finance_app.py --selftest 2>&1|grep -m1 "SMOKE "); echo "      $NEW"
echo "$NEW"|grep -Eq "SMOKE ([0-9]+)/\1 " || rollback
NEW_T=$(echo "$NEW"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
[ "$NEW_T" -gt "$CUR_T" ] || { echo "*** RED: auto-replay checks did not run ($CUR_T -> $NEW_T)."; rollback; }
grep -q 'def _replay_pending_marg_for_day' "$LIVE_FIN" || rollback

echo "[8/8] restart + verify"; systemctl restart $SVC_F; sleep 2; systemctl is-active --quiet $SVC_F || rollback

echo "==============================================================="
echo " GREEN.  Marg auto-replay live.  finance_app.py $(md5sum $LIVE_FIN|cut -d' ' -f1)  smoke $NEW_T (was $CUR_T)"
echo " From now on, filing a day auto-loads any Marg pushed before it was filed."
echo " Pin the new finance_app.py md5."
echo "==============================================================="
