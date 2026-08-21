#!/bin/bash
# =====================================================================
#  S195_HEALTH — system health page + portal-tile warning
#
#  WHY: on 21-08-2026 the Marg push began failing at 20:51 with HTTP 401
#  and nobody noticed for over an hour. The sender said REFUSED on a
#  screen no one was watching; the Hub looked normal. This makes the
#  answer to "is anything wrong right now?" visible.
#
#  ADDS (one file, finance_app.py):
#    GET /finance/health       a status page  (checker only)
#    GET /finance/api/health   the same as JSON
#    tile-meta: when something is wrong, the CHECKER's portal tile
#      subtitle says so -- so the warning reaches the portal home with
#      NO change to the portal itself.
#
#  CHECKS: last Marg push + pending applies · days filed vs missing
#  (Sundays skipped) · books vs last physical count · flags in 30 days ·
#  newest verified backup.  Read-only; no schema change.
#
#  Currency-gated to the live S195_NCSCAN build. Backs up, py_compiles,
#  runs the app's own --selftest (must stay ALL-GREEN and not shrink),
#  restarts, and ROLLS BACK on any red.
# =====================================================================
set -u
cd "$(dirname "$0")"
LIVE=/root/finance/finance_app.py
SVC=clinic-finance.service
WANT=89ab3e8eeb6b527f9a8e82f47b4746c4

echo "==============================================================="
echo " S195_HEALTH · system health page + tile warning"
echo "==============================================================="
echo "[1/8] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }

echo "[2/8] currency gate"
[ -f "$LIVE" ] || { echo "*** RED: $LIVE missing."; exit 1; }
H=$(md5sum "$LIVE"|cut -d' ' -f1); echo "      finance_app : $H"
[ "$H" = "$WANT" ] || { echo "*** RED: not the expected build ($WANT). STOP -- tell Cowork this hash."; exit 1; }

echo "[3/8] baseline smoke"
CUR=$(cd /root/finance && python3 finance_app.py --selftest 2>&1|grep -m1 "SMOKE "); echo "      $CUR"
CUR_T=$(echo "$CUR"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
CUR_OK=$(echo "$CUR"|sed -n 's#.*SMOKE \([0-9]*\)/[0-9]*.*#\1#p')
# The live baseline is 570/573. Three checks assert a FROZEN non-cash total
# ("350.00", exactly 2 heads) that only held while no real no-payment bills
# existed. Darpan filed the first real ones on 20-08-2026, so they went red with
# no code change -- the F-106 shape. This kit FIXES those three to assert the
# rule instead of the snapshot, so we do NOT demand a green baseline here; we
# demand a green result AFTER the swap, which is the stronger proof.
if [ "$CUR_OK" != "$CUR_T" ]; then
  echo "      baseline is red ($CUR_OK/$CUR_T). Expected -- the three frozen"
  echo "      non-cash assertions. This kit fixes them; step 7 must come back"
  echo "      ALL-GREEN or we roll back."
  cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep "FAIL:" | sed 's/^/        /'
  cd - >/dev/null
fi

TS=$(date +%Y%m%d_%H%M%S); BK=/root/finance/_backup_S195_HEALTH_$TS; mkdir -p "$BK"
echo "[4/8] backup -> $BK"; cp -p "$LIVE" "$BK/"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/finance_app.py" "$LIVE"; systemctl restart $SVC; sleep 2; echo "   service: $(systemctl is-active $SVC)"; exit 1; }

echo "[5/8] swap"; cp finance_app.py "$LIVE" || rollback
echo "[6/8] py_compile"; python3 -c "import py_compile; py_compile.compile('$LIVE',doraise=True); print('      OK')" || rollback

echo "[7/8] smoke — ALL-GREEN, not shrunk"
NEW=$(cd /root/finance && python3 finance_app.py --selftest 2>&1|grep -m1 "SMOKE "); echo "      $NEW"
echo "$NEW"|grep -Eq "SMOKE ([0-9]+)/\1 " || { echo "*** RED: still not all-green after the fix."; cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep "FAIL:" | sed 's/^/        /'; rollback; }
NEW_T=$(echo "$NEW"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
[ "$NEW_T" -ge "$CUR_T" ] || { echo "*** RED: smoke shrank ($CUR_T -> $NEW_T)."; rollback; }

echo "[8/8] restart + verify"; systemctl restart $SVC; sleep 2; systemctl is-active --quiet $SVC || rollback

echo "==============================================================="
echo " GREEN.  Open  https://followup.dr-manoj.in/finance/health"
echo " finance_app.py $(md5sum $LIVE|cut -d' ' -f1)  smoke $NEW_T (was $CUR_T)"
echo " Backup: $BK"
echo "==============================================================="
