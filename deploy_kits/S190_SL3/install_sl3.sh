#!/bin/bash
# =====================================================================
#  S190_SL3 · the quota fix that unblocks the sitting + Advances page
#
#  FOUND BY THE OWNER on the live entry page, minutes after SL2: the
#  inline line read "Taken against 2026-08: Rs 3,63,000 of Rs 15,000"
#  for Darpan. His S155 migration rows (years of loan history) are
#  DATED August 2026, and SL2's month-counter counted every
#  ADVANCE_ISSUE row by month. Left alone, tomorrow's ordinary Rs 15,000
#  entry would have been refused. OWNER RULING: the quota counts from
#  the D331 install forward — pre-install rows are grandfathered
#  (visible in the position card and statement, recovering as normal,
#  never eating the month), and interest-bearing loans NEVER consume
#  the ordinary quota (they are the parallel D250 instrument and now
#  BYPASS the quota gate to match). The Advances page gains the D331
#  facts: against-month, SPECIAL badge, application link.
#
#  D317 chain. Projection: current 212 -> new 214 (+2: the legacy-row
#  exclusion check · the loan exclusion check), written before measuring.
# =====================================================================
set -u
cd "$(dirname "$0")"
WANT_LIVE=0408bbbe9d31fc17c144a601dcd7d9b0    # S190_SL2, Register-pinned
LIVE=/root/staff_ledger.py
PY=/root/wa/venv/bin/python3
SVC=staff-ledger.service
echo "==============================================================="
echo " S190_SL3 · the quota counts from the install; loans never"
echo "==============================================================="
echo "[1/6] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "      KIT_ID : $(cat KIT_ID.txt)"
echo "[2/6] currency gate"
H=$(md5sum $LIVE | cut -d' ' -f1); echo "      live : $H"
[ "$H" = "$WANT_LIVE" ] || { echo '*** RED: live is not the SL2 build. STOP.'; exit 1; }
echo "[3/6] PROJECTION: current 212 -> new 214 (+2)."
CUR=$($PY $LIVE --selftest 2>&1 | tail -1); echo "      $CUR"
echo "$CUR" | grep -q "PASSED — 212 " || { echo '*** RED. STOP.'; exit 1; }
NEW=$($PY ./staff_ledger_SL3.py --selftest 2>&1 | tail -1); echo "      $NEW"
echo "$NEW" | grep -q "PASSED — 214 " || { echo '*** RED. STOP.'; exit 1; }
TS=$(date +%Y%m%d_%H%M%S); BAK=/root/staff_ledger.py.bak_S190_SL3_$TS
echo "[4/6] backup: $BAK"; cp -p $LIVE $BAK || exit 1
echo "[5/6] swap"; cp staff_ledger_SL3.py $LIVE
POST=$($PY $LIVE --selftest 2>&1 | tail -1); echo "      $POST"
echo "$POST" | grep -q "PASSED — 214 " || {
  echo "*** RED — ROLLING BACK."; cp -p $BAK $LIVE; systemctl restart $SVC; exit 1; }
echo "[6/6] restart"; systemctl restart $SVC; sleep 2
systemctl is-active --quiet $SVC && echo "      $SVC : active" || {
  echo "*** RED — ROLLING BACK."; cp -p $BAK $LIVE; systemctl restart $SVC; exit 1; }
echo "==============================================================="
echo " GREEN.  S190_SL3 is live."
echo "   staff_ledger.py  $(md5sum $LIVE | cut -d' ' -f1)"
echo "   selftest 212 -> 214  (+2 checks, 0 failures)"
echo " NOW LOOK (the F-132 rule): the entry page, Advance issued,"
echo " staff Darpan — the line must read:"
echo "   Taken against 2026-08: Rs 0 of Rs 15000 max (75% of base)."
echo "==============================================================="
