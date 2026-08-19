#!/bin/bash
# =====================================================================
#  S190_F3 · the inline bill flow (owner ruling, from first live use)
#
#  "Better flow is inline attachment of bill, not after save." From this
#  kit the bill is CHOSEN inline in the expense row — a file input right
#  under Details — and uploads automatically the moment the day is
#  saved. Filing with bills still pending becomes draft-save -> upload
#  -> File, so the evidence gate never refuses a day whose bills were
#  chosen but not yet sent. The full-screen scanner stays as the
#  "camera now" path. Both units. Server routes byte-unchanged; the app
#  changes only inside --selftest (two page checks REPLACED, count
#  equal), so this is a COUNT-EQUAL kit proven by REPRODUCTION:
#  offline, the new app against the LIVE pages fails exactly the two
#  F3 checks (545/547, both naming F3), and 547/547 with the new pages.
#
#  Projection: 547 -> 547, count equal, reproduction as the proof.
# =====================================================================
set -u
cd "$(dirname "$0")"
WANT_APP=7445d20dc87a2650ab21144558a2aebf
CUR_APP=ccc12afc54a0878e7b808c62034eb027     # S190_F2, Register-pinned
CUR_PAGE=b411269fd75bfcde3160b78dc28d6c77    # S190_F2
CUR_CPAGE=1c930a3ec71873ce774770dab524ba0e   # S190_E2
LIVE_APP=/root/finance/finance_app.py
LIVE_PAGE=/root/finance/finance_ui/finance_entry.html
LIVE_CPAGE=/root/finance/finance_ui/finance_entry_clinic.html
SVC=clinic-finance.service
echo "==============================================================="
echo " S190_F3 · the inline bill flow"
echo "==============================================================="
echo "[1/7] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "      KIT_ID : $(cat KIT_ID.txt)"
echo "[2/7] currency gate"
HA=$(md5sum $LIVE_APP | cut -d' ' -f1); HP=$(md5sum $LIVE_PAGE | cut -d' ' -f1)
HC=$(md5sum $LIVE_CPAGE | cut -d' ' -f1)
echo "      app $HA / page $HP / clinic $HC"
[ "$HA" = "$CUR_APP" ] && [ "$HP" = "$CUR_PAGE" ] && [ "$HC" = "$CUR_CPAGE" ] || {
  echo '*** RED: live files are not the F2/E2 builds. STOP.'; exit 1; }
echo "[3/7] PROJECTION: current 547 -> staged 547 (count-equal; the"
echo "      REPRODUCTION below is the proof, per the W1b rule)."
echo "[4/7] current smoke"
CUR=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | tail -1)
echo "      $CUR"; echo "$CUR" | grep -q "SMOKE 547/547" || { echo '*** RED. STOP.'; exit 1; }
echo "[5/7] REPRODUCTION + staged smoke"
STAGE=$(mktemp -d); mkdir -p $STAGE/finance_ui
cp finance_app_F3.py $STAGE/finance_app.py
cp /root/finance/finance_ui/*.html $STAGE/finance_ui/
cp /root/finance/*.py $STAGE/ 2>/dev/null; rm -f $STAGE/finance_app.py
cp finance_app_F3.py $STAGE/finance_app.py
cp /root/finance/finance.db $STAGE/finance.db
R=$(cd $STAGE && python3 finance_app.py --selftest 2>&1 | tail -1)
echo "      new app + LIVE pages : $R   (expect 545/547 — the two F3 checks)"
echo "$R" | grep -q "545/547" || { rm -rf $STAGE
  echo '*** RED: the reproduction did not reproduce. STOP.'; exit 1; }
cp finance_ui/finance_entry.html.new $STAGE/finance_ui/finance_entry.html
cp finance_ui/finance_entry_clinic.html.new $STAGE/finance_ui/finance_entry_clinic.html
N=$(cd $STAGE && python3 finance_app.py --selftest 2>&1 | tail -1)
rm -rf $STAGE
echo "      new app + NEW pages  : $N"
echo "$N" | grep -q "SMOKE 547/547" || { echo '*** RED. STOP.'; exit 1; }
TS=$(date +%Y%m%d_%H%M%S); BAK=/root/finance/_backup_S190_F3_$TS
echo "[6/7] backup: $BAK"
mkdir -p $BAK && cp -p $LIVE_APP $LIVE_PAGE $LIVE_CPAGE $BAK/ || exit 1
echo "[7/7] swap + live verify"
cp finance_app_F3.py $LIVE_APP
cp finance_ui/finance_entry.html.new $LIVE_PAGE
cp finance_ui/finance_entry_clinic.html.new $LIVE_CPAGE
POST=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | tail -1)
echo "      $POST"; echo "$POST" | grep -q "SMOKE 547/547" || {
  echo "*** RED — ROLLING BACK."
  cp -p $BAK/finance_app.py $LIVE_APP; cp -p $BAK/finance_entry.html $LIVE_PAGE
  cp -p $BAK/finance_entry_clinic.html $LIVE_CPAGE; systemctl restart $SVC; exit 1; }
systemctl restart $SVC; sleep 2
systemctl is-active --quiet $SVC && echo "      $SVC : active" || {
  echo "*** RED — ROLLING BACK."
  cp -p $BAK/finance_app.py $LIVE_APP; cp -p $BAK/finance_entry.html $LIVE_PAGE
  cp -p $BAK/finance_entry_clinic.html $LIVE_CPAGE; systemctl restart $SVC; exit 1; }
echo "==============================================================="
echo " GREEN.  S190_F3 is live."
echo "   finance_app.py               $(md5sum $LIVE_APP   | cut -d' ' -f1)"
echo "   finance_entry.html           $(md5sum $LIVE_PAGE  | cut -d' ' -f1)"
echo "   finance_entry_clinic.html    $(md5sum $LIVE_CPAGE | cut -d' ' -f1)"
echo "   smoke 547/547 (count-equal, reproduction-proven)"
echo " Pin the three md5s into the KB Register as they stand (D321(d))."
echo "==============================================================="
