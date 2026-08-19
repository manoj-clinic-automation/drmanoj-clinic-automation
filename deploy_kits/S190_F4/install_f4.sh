#!/bin/bash
# =====================================================================
#  S190_F4 · the approved-day gate reads the UNIT role, not the broker
#
#  FOUND BY THE OWNER on the real 31-July screen: "This day is already
#  approved — only the doctor can change it" — shown to THE DOCTOR.
#  Via SSO his broker role is "doctor"; the medical save's locked-day
#  gate tested u["role"] != "checker" (legacy header semantics) instead
#  of the UNIT roles require() already computes. The clinic save has
#  carried the correct form since S182; the medical side never did, and
#  no one had ever re-edited an approved medical day until today.
#  The F-84 family: identity taken from the wrong layer.
#
#  ONE functional line changed. Two new checks reproduce the owner's
#  exact shape (dev role "doctor" + a unit_role checker row): the
#  checker now edits the approved day; a maker is still refused.
#
#  Projection: 549 (547 + 2), written before measuring. Offline: 549
#  on the base shape AND the month-at-ceiling shape.
# =====================================================================
set -u
cd "$(dirname "$0")"
WANT_APP=f95cc4911cb8f1218a19b691f9a3b686
CUR_APP=7445d20dc87a2650ab21144558a2aebf     # S190_F3, Register-pinned
LIVE_APP=/root/finance/finance_app.py
SVC=clinic-finance.service
echo "==============================================================="
echo " S190_F4 · the unit role decides, never the broker role"
echo "==============================================================="
echo "[1/6] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "      KIT_ID : $(cat KIT_ID.txt)"
echo "[2/6] currency gate"
HA=$(md5sum $LIVE_APP | cut -d' ' -f1); echo "      live app : $HA"
[ "$HA" = "$CUR_APP" ] || { echo '*** RED: live is not the F3 build. STOP.'; exit 1; }
echo "[3/6] PROJECTION: current 547 -> staged 549 (+2)."
CUR=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE ")
echo "      $CUR"; echo "$CUR" | grep -q "SMOKE 547/547" || { echo '*** RED. STOP.'; exit 1; }
STAGE=$(mktemp -d); mkdir -p $STAGE/finance_ui
cp /root/finance/*.py $STAGE/ 2>/dev/null
cp /root/finance/finance_ui/*.html $STAGE/finance_ui/
cp finance_app_F4.py $STAGE/finance_app.py
cp /root/finance/finance.db $STAGE/finance.db
NEW=$(cd $STAGE && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE ")
rm -rf $STAGE
echo "      $NEW"; echo "$NEW" | grep -q "SMOKE 549/549" || { echo '*** RED. STOP.'; exit 1; }
TS=$(date +%Y%m%d_%H%M%S); BAK=/root/finance/_backup_S190_F4_$TS
echo "[4/6] backup: $BAK"; mkdir -p $BAK && cp -p $LIVE_APP $BAK/ || exit 1
echo "[5/6] swap + live verify"
cp finance_app_F4.py $LIVE_APP
POST=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE ")
echo "      $POST"; echo "$POST" | grep -q "SMOKE 549/549" || {
  echo "*** RED — ROLLING BACK."; cp -p $BAK/finance_app.py $LIVE_APP
  systemctl restart $SVC; exit 1; }
echo "[6/6] restart"; systemctl restart $SVC; sleep 2
systemctl is-active --quiet $SVC && echo "      $SVC : active" || {
  echo "*** RED — ROLLING BACK."; cp -p $BAK/finance_app.py $LIVE_APP
  systemctl restart $SVC; exit 1; }
echo "==============================================================="
echo " GREEN.  S190_F4 is live."
echo "   finance_app.py  $(md5sum $LIVE_APP | cut -d' ' -f1)"
echo "   smoke 547/547 -> 549/549  (+2 checks, 0 failures)"
echo " NOW: reload the 31-July page and File again — it will accept."
echo " Pin the md5 into the KB Register as it stands (D321(d))."
echo "==============================================================="
