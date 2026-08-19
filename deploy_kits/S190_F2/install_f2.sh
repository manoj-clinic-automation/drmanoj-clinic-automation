#!/bin/bash
# =====================================================================
#  S190_F2 · D331 plumbing: the Sanjeevni ceiling reads the salary book
#
#  The owner's September device (S190): an advance may be posted in the
#  Staff Ledger AGAINST a future month's salary. From this kit the
#  Sanjeevni page's inline line and the server's refusal COUNT those
#  forward-attributed rows for the month — so when the ledger says
#  "Rs 5,000 against September", the drawer offers Darpan Rs 10,000 in
#  September, not Rs 15,000.
#
#  WHY ONLY FORWARD-ATTRIBUTED ROWS: a drawer draw is never forward-
#  attributed, so the same rupee can never be counted in both books —
#  the double-count the retired D329 LINK machinery existed to prevent,
#  solved structurally. Known, documented blind spot: a same-month
#  DIRECT pipeline advance is not netted from the drawer limit (rare by
#  flow; the checker sees both books).
#
#  FAIL-SOFT (the D283/D322 pattern): ledger unreadable => the gate
#  degrades to Sanjeevni-book-only and the page SAYS SO inline —
#  degraded, never silent, never a crash.
#
#  D317 chain. Projections: current 542 -> staged 547 (+5 exactly).
#  Offline: 547 on the base shape, 547 on the month-at-ceiling shape
#  (which caught a negative-room formatting bug in the new checks
#  themselves — fixed before this kit was cut), 547 on a double run.
# =====================================================================
set -u
cd "$(dirname "$0")"

WANT_APP=ccc12afc54a0878e7b808c62034eb027
WANT_PAGE=b411269fd75bfcde3160b78dc28d6c77
LIVE_APP=/root/finance/finance_app.py
LIVE_PAGE=/root/finance/finance_ui/finance_entry.html
CUR_APP=02062855ccd97056c2be64ce04d606cb     # S190_E2, Register-pinned
CUR_PAGE=f819bdf95de14fc331428cf6bea4c37e    # S190_E2, Register-pinned
SVC=clinic-finance.service

echo "==============================================================="
echo " S190_F2 · D331: the drawer limit reads the salary book"
echo "==============================================================="
echo "[1/7] kit bytes"
md5sum -c SUMS.md5 || { echo '*** RED: kit bytes do not match. STOP.'; exit 1; }
echo "      KIT_ID : $(cat KIT_ID.txt)"

echo "[2/7] currency gate"
HA=$(md5sum $LIVE_APP  | cut -d' ' -f1); echo "      live app  : $HA"
HP=$(md5sum $LIVE_PAGE | cut -d' ' -f1); echo "      live page : $HP"
[ "$HA" = "$CUR_APP" ] && [ "$HP" = "$CUR_PAGE" ] || {
  echo "*** RED: the live files are not the S190_E2 build this kit was made on."
  echo "*** Nothing has been changed. STOP."; exit 1; }

echo "[3/7] THE PROJECTION — written before anything is measured:"
echo "      (a) current live smoke: 542/542.  (b) staged: 547/547 (+5)."

echo "[4/7] current smoke"
CUR=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | tail -1)
echo "      $CUR"; echo "$CUR" | grep -q "SMOKE 542/542" || {
  echo '*** RED: current smoke is not 542/542. STOP.'; exit 1; }

echo "[5/7] staged smoke (new app + new page, against a copy of the live store)"
STAGE=$(mktemp -d); cp finance_app_F2.py $STAGE/finance_app.py
mkdir -p $STAGE/finance_ui
cp /root/finance/finance_ui/*.html $STAGE/finance_ui/ 2>/dev/null
cp finance_ui/finance_entry.html.new $STAGE/finance_ui/finance_entry.html
cp /root/finance/finance_ingest.py /root/finance/finance_upi.py \
   /root/finance/finance_identity.py /root/finance/finance_returns.py \
   /root/finance/finance_yesbank.py /root/finance/marg_report.py $STAGE/ 2>/dev/null
cp /root/finance/finance.db $STAGE/finance.db
NEW=$(cd $STAGE && python3 finance_app.py --selftest 2>&1 | tail -1)
rm -rf $STAGE
echo "      $NEW"; echo "$NEW" | grep -q "SMOKE 547/547" || {
  echo '*** RED: staged smoke did not land on 547/547. Nothing swapped. STOP.'; exit 1; }

TS=$(date +%Y%m%d_%H%M%S); BAK=/root/finance/_backup_S190_F2_$TS
echo "[6/7] backup: $BAK"
mkdir -p $BAK && cp -p $LIVE_APP $LIVE_PAGE $BAK/ || { echo '*** RED: backup failed.'; exit 1; }

echo "[7/7] swap + live verify"
cp finance_app_F2.py $LIVE_APP
cp finance_ui/finance_entry.html.new $LIVE_PAGE
POST=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | tail -1)
echo "      $POST"; echo "$POST" | grep -q "SMOKE 547/547" || {
  echo "*** RED: live smoke failed — ROLLING BACK."
  cp -p $BAK/finance_app.py $LIVE_APP; cp -p $BAK/finance_entry.html $LIVE_PAGE
  systemctl restart $SVC; echo "*** restored."; exit 1; }
systemctl restart $SVC; sleep 2
systemctl is-active --quiet $SVC && echo "      $SVC : active" || {
  echo "*** RED: service down — ROLLING BACK."
  cp -p $BAK/finance_app.py $LIVE_APP; cp -p $BAK/finance_entry.html $LIVE_PAGE
  systemctl restart $SVC; exit 1; }
echo "==============================================================="
echo " GREEN.  S190_F2 is live."
echo "   finance_app.py       $(md5sum $LIVE_APP  | cut -d' ' -f1)"
echo "   finance_entry.html   $(md5sum $LIVE_PAGE | cut -d' ' -f1)"
echo "   smoke 542/542 -> 547/547  (+5 checks, 0 failures)"
echo " Pin both md5s into the KB Register as they stand (D321(d))."
echo "==============================================================="
