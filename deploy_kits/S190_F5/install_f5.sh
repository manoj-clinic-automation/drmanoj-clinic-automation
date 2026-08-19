#!/bin/bash
# =====================================================================
#  S190_F5 · an edited day is an APP entry — the queue sees it
#
#  FOUND BY THE OWNER: his edited 31-July day vanished from the
#  approvals queue while its Rs 10,000 already counted in the drawer.
#  The day was imported (source='legacy_sheet', the pre-15-Aug era) and
#  the queue deliberately hides legacy days so the bulk import cannot
#  flood it — but an EDITED legacy day needs the queue. From this kit a
#  correction re-marks the day source='app' (both units); the
#  day_revision keeps the legacy original verbatim. One check proves an
#  edited legacy day surfaces in the queue.
#
#  Projection: 549 -> 550 (+1), written before measuring. Offline: 550
#  on the base shape AND the month-at-ceiling shape.
# =====================================================================
set -u
cd "$(dirname "$0")"
WANT_APP=17e6b84ce90ca7d7a0a9ba0c668ab15f
CUR_APP=f95cc4911cb8f1218a19b691f9a3b686     # S190_F4, Register-pinned
LIVE_APP=/root/finance/finance_app.py
SVC=clinic-finance.service
echo "==============================================================="
echo " S190_F5 · an edited day is an app entry"
echo "==============================================================="
echo "[1/6] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "      KIT_ID : $(cat KIT_ID.txt)"
echo "[2/6] currency gate"
HA=$(md5sum $LIVE_APP | cut -d' ' -f1); echo "      live app : $HA"
[ "$HA" = "$CUR_APP" ] || { echo '*** RED: live is not the F4 build. STOP.'; exit 1; }
echo "[3/6] PROJECTION: current 549 -> staged 550 (+1)."
CUR=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE ")
echo "      $CUR"; echo "$CUR" | grep -q "SMOKE 549/549" || { echo '*** RED. STOP.'; exit 1; }
STAGE=$(mktemp -d); mkdir -p $STAGE/finance_ui
cp /root/finance/*.py $STAGE/ 2>/dev/null
cp /root/finance/finance_ui/*.html $STAGE/finance_ui/
cp finance_app_F5.py $STAGE/finance_app.py
cp /root/finance/finance.db $STAGE/finance.db
NEW=$(cd $STAGE && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE ")
rm -rf $STAGE
echo "      $NEW"; echo "$NEW" | grep -q "SMOKE 550/550" || { echo '*** RED. STOP.'; exit 1; }
TS=$(date +%Y%m%d_%H%M%S); BAK=/root/finance/_backup_S190_F5_$TS
echo "[4/6] backup: $BAK"; mkdir -p $BAK && cp -p $LIVE_APP $BAK/ || exit 1
echo "[5/6] swap + live verify"
cp finance_app_F5.py $LIVE_APP
POST=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE ")
echo "      $POST"; echo "$POST" | grep -q "SMOKE 550/550" || {
  echo "*** RED — ROLLING BACK."; cp -p $BAK/finance_app.py $LIVE_APP
  systemctl restart $SVC; exit 1; }
echo "[6/6] restart"; systemctl restart $SVC; sleep 2
systemctl is-active --quiet $SVC && echo "      $SVC : active" || {
  echo "*** RED — ROLLING BACK."; cp -p $BAK/finance_app.py $LIVE_APP
  systemctl restart $SVC; exit 1; }
echo "==============================================================="
echo " GREEN.  S190_F5 is live."
echo "   finance_app.py  $(md5sum $LIVE_APP | cut -d' ' -f1)"
echo "   smoke 549/549 -> 550/550  (+1 check, 0 failures)"
echo " NOTE: your 31-July edit predates this kit, so it stays hidden"
echo " from the queue ONE more time — either approve it on /finance/review"
echo " or open the day and press File once more (this save re-marks it)."
echo " Pin the md5 into the KB Register as it stands (D321(d))."
echo "==============================================================="
