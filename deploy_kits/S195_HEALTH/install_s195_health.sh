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
WANT=f25ed48923a5647ba1f6111bad0737d3

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
echo "$CUR"|grep -Eq "SMOKE ([0-9]+)/\1 " || { echo '*** RED: baseline not all-green. STOP.'; exit 1; }
CUR_T=$(echo "$CUR"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')

TS=$(date +%Y%m%d_%H%M%S); BK=/root/finance/_backup_S195_HEALTH_$TS; mkdir -p "$BK"
echo "[4/8] backup -> $BK"; cp -p "$LIVE" "$BK/"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/finance_app.py" "$LIVE"; systemctl restart $SVC; sleep 2; echo "   service: $(systemctl is-active $SVC)"; exit 1; }

echo "[5/8] swap"; cp finance_app.py "$LIVE" || rollback
echo "[6/8] py_compile"; python3 -c "import py_compile; py_compile.compile('$LIVE',doraise=True); print('      OK')" || rollback

echo "[7/8] smoke — ALL-GREEN, not shrunk"
NEW=$(cd /root/finance && python3 finance_app.py --selftest 2>&1|grep -m1 "SMOKE "); echo "      $NEW"
echo "$NEW"|grep -Eq "SMOKE ([0-9]+)/\1 " || rollback
NEW_T=$(echo "$NEW"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
[ "$NEW_T" -ge "$CUR_T" ] || { echo "*** RED: smoke shrank ($CUR_T -> $NEW_T)."; rollback; }

echo "[8/8] restart + verify"; systemctl restart $SVC; sleep 2; systemctl is-active --quiet $SVC || rollback

echo "==============================================================="
echo " GREEN.  Open  https://followup.dr-manoj.in/finance/health"
echo " finance_app.py $(md5sum $LIVE|cut -d' ' -f1)  smoke $NEW_T (was $CUR_T)"
echo " Backup: $BK"
echo "==============================================================="
