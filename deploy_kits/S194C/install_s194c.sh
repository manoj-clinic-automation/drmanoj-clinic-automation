#!/bin/bash
# =====================================================================
#  S194C · put Darpan on the new Daily Sale v2 page by default.
#
#   * /finance/ (his landing) and his portal tile now open the NEW
#     two-stage page (finance_daily.html); /finance/entry stays live
#     as the classic fallback.
#   * the scanner returns to /finance/daily now, and the daily page
#     RELOADS the saved day on return + on date change — so a scan
#     round-trip can never come back to a blank form and wipe expenses
#     on re-save (the D330 hazard).
#
#  Payloads: finance_app.py (swap) · finance_ui/finance_daily.html
#  (swap — adds loadDay/date-reload). No DB change.
#  3-file smoke: currency gates, ALL-GREEN + ZERO-delta smoke, rollback.
# =====================================================================
set -u
cd "$(dirname "$0")"

LIVE_FIN=/root/finance/finance_app.py
LIVE_DAILY=/root/finance/finance_ui/finance_daily.html
SVC_F=clinic-finance.service

FIN_WANT=43d2b84515790b93279a91bd1a65a104       # current live (S194B / ⭐4)
DAILY_WANT=e1092757bcad6cfbc74473422741af8e     # current live daily page (S194)

echo "==============================================================="
echo " S194C · Darpan's default page -> Daily Sale v2"
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

TS=$(date +%Y%m%d_%H%M%S); BK=/root/finance/_backup_S194C_$TS; mkdir -p "$BK/finance_ui"
echo "[4/9] backup -> $BK"; cp -p "$LIVE_FIN" "$BK/"; cp -p "$LIVE_DAILY" "$BK/finance_ui/"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/finance_app.py" "$LIVE_FIN"; cp -p "$BK/finance_ui/finance_daily.html" "$LIVE_DAILY"; systemctl restart $SVC_F; exit 1; }

echo "[5/9] swap finance_app.py + daily page"
cp finance_app_S194C.py "$LIVE_FIN" || rollback
cp finance_ui/finance_daily.html "$LIVE_DAILY" || rollback

echo "[6/9] py_compile"; python3 -c "import py_compile; py_compile.compile('$LIVE_FIN',doraise=True); print('      OK')" || rollback

echo "[7/9] new smoke — ALL-GREEN and ZERO delta (switch adds no checks)"
NEW=$(cd /root/finance && python3 finance_app.py --selftest 2>&1|grep -m1 "SMOKE "); echo "      $NEW"
echo "$NEW"|grep -Eq "SMOKE ([0-9]+)/\1 " || rollback
NEW_T=$(echo "$NEW"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
[ "$NEW_T" = "$CUR_T" ] || { echo "*** RED: smoke count changed ($CUR_T -> $NEW_T)."; rollback; }

echo "[8/9] sanity — root serves the daily page + tile points at it"
grep -q 'else "finance_daily.html"' "$LIVE_FIN" && grep -q 'else "/finance/daily"' "$LIVE_FIN" \
  && grep -q 'function loadDay' "$LIVE_DAILY" || rollback
echo "      OK"

echo "[9/9] restart + verify"; systemctl restart $SVC_F; sleep 2; systemctl is-active --quiet $SVC_F || rollback

echo "==============================================================="
echo " GREEN.  Darpan now lands on the Daily Sale v2 page."
echo "   finance_app.py    $(md5sum $LIVE_FIN   | cut -d' ' -f1)"
echo "   finance_daily.html$(md5sum $LIVE_DAILY | cut -d' ' -f1)"
echo "   smoke unchanged   : $NEW_T"
echo "---------------------------------------------------------------"
echo " His tile + /finance/ open /finance/daily; /finance/entry is the"
echo " classic fallback. Hard-refresh once. Pin the 2 md5s."
echo "==============================================================="
