#!/bin/bash
# =====================================================================
#  S194D · Daily-page switch  +  Marg auto-replay.   (supersedes S194C)
#
#   * SWITCH: /finance/ and Darpan's tile now open the NEW two-stage
#     Daily Sale page (finance_daily.html); /finance/entry stays as the
#     classic fallback. The daily page reloads a saved day on return +
#     on date change, so a scan round-trip can never blank the form and
#     wipe expenses on re-save (the D330 hazard).
#
#   * AUTO-REPLAY: the moment a day is filed/saved, any PENDING Marg
#     push that carries that day is ingested automatically (its payload
#     was kept for exactly this, F-155). A report pushed BEFORE the day
#     was filed no longer strands its bills — which is what left 17/18/19
#     Aug short. (Those three predate this and their payloads were already
#     pruned, so re-load them once from the exports; every day going
#     forward self-heals.)
#
#  Payloads: finance_app.py (swap) · finance_ui/finance_daily.html (swap).
#  No DB change. Currency gates, ALL-GREEN smoke that GREW (the auto-replay
#  checks ran), rollback on any red.
#
#  NOTE: if you already installed S194C, that's fine — this gate expects
#  the pre-S194C finance_app (43d2b845). If S194C IS live, tell me and I
#  reissue against its hash; do NOT force past a red gate.
# =====================================================================
set -u
cd "$(dirname "$0")"

LIVE_FIN=/root/finance/finance_app.py
LIVE_DAILY=/root/finance/finance_ui/finance_daily.html
SVC_F=clinic-finance.service

FIN_WANT=43d2b84515790b93279a91bd1a65a104       # current live (S194B / ⭐4)
DAILY_WANT=e1092757bcad6cfbc74473422741af8e     # current live daily page (S194)

echo "==============================================================="
echo " S194D · Daily-page switch + Marg auto-replay"
echo "==============================================================="

echo "[1/9] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "      KIT_ID : $(cat KIT_ID.txt)"

echo "[2/9] currency gates"
gate(){ local h; h=$(md5sum "$1"|cut -d' ' -f1); echo "      $2 : $h";
        [ "$h" = "$3" ] || { echo "*** RED: $2 not the expected build. STOP."; exit 1; }; }
gate "$LIVE_FIN"   "finance_app  " "$FIN_WANT"
gate "$LIVE_DAILY" "daily page   " "$DAILY_WANT"

echo "[3/9] baseline smoke"
CUR=$(cd /root/finance && python3 finance_app.py --selftest 2>&1|grep -m1 "SMOKE "); echo "      $CUR"
echo "$CUR"|grep -Eq "SMOKE ([0-9]+)/\1 " || { echo '*** RED. STOP.'; exit 1; }
CUR_T=$(echo "$CUR"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')

TS=$(date +%Y%m%d_%H%M%S); BK=/root/finance/_backup_S194D_$TS; mkdir -p "$BK/finance_ui"
echo "[4/9] backup -> $BK"; cp -p "$LIVE_FIN" "$BK/"; cp -p "$LIVE_DAILY" "$BK/finance_ui/"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/finance_app.py" "$LIVE_FIN"; cp -p "$BK/finance_ui/finance_daily.html" "$LIVE_DAILY"; systemctl restart $SVC_F; exit 1; }

echo "[5/9] swap finance_app.py + daily page"
cp finance_app_S194D.py "$LIVE_FIN" || rollback
cp finance_ui/finance_daily.html "$LIVE_DAILY" || rollback

echo "[6/9] py_compile"; python3 -c "import py_compile; py_compile.compile('$LIVE_FIN',doraise=True); print('      OK')" || rollback

echo "[7/9] new smoke — ALL-GREEN and grown (the auto-replay checks ran)"
NEW=$(cd /root/finance && python3 finance_app.py --selftest 2>&1|grep -m1 "SMOKE "); echo "      $NEW"
echo "$NEW"|grep -Eq "SMOKE ([0-9]+)/\1 " || rollback
NEW_T=$(echo "$NEW"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
[ "$NEW_T" -gt "$CUR_T" ] || { echo "*** RED: auto-replay checks did not run ($CUR_T -> $NEW_T)."; rollback; }
echo "      smoke grew $CUR_T -> $NEW_T"

echo "[8/9] sanity — switch + auto-replay present"
grep -q 'else "finance_daily.html"' "$LIVE_FIN" && grep -q 'else "/finance/daily"' "$LIVE_FIN" \
  && grep -q 'def _replay_pending_marg_for_day' "$LIVE_FIN" \
  && grep -q 'function loadDay' "$LIVE_DAILY" || rollback
echo "      OK"

echo "[9/9] restart + verify"; systemctl restart $SVC_F; sleep 2; systemctl is-active --quiet $SVC_F || rollback

echo "==============================================================="
echo " GREEN.  S194D live."
echo "   finance_app.py    $(md5sum $LIVE_FIN   | cut -d' ' -f1)"
echo "   finance_daily.html$(md5sum $LIVE_DAILY | cut -d' ' -f1)"
echo "   smoke             : $NEW_T (was $CUR_T)"
echo "---------------------------------------------------------------"
echo " Darpan lands on /finance/daily. From now on, filing a day auto-"
echo " loads any Marg pushed before it was filed — no more manual re-load."
echo " (17/18/19 Aug still need a one-time re-load from the exports.)"
echo " Pin the 2 md5s."
echo "==============================================================="
