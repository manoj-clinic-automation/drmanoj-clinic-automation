#!/bin/bash
# =====================================================================
#  S190_SL4 · the quota lane — a quota advance never waits for the loan
#
#  SEEN BY THE OWNER on Darpan's statement, minutes after the three
#  advances went in: Rs 10,000 · Rs 15,000 · Rs 5,000 all read
#  "(waiting for the loan to clear)" — the D250 waterfall queues every
#  interest-free advance behind Rs 3.59 lakh of loan book. Correct for
#  legacy tranches; WRONG for a month's own salary advance. OWNER
#  RULING "A": the ledger's own close recovers them — August's close
#  takes the Rs 10,000 + Rs 15,000, September's the Rs 5,000. No
#  manual workbook squaring.
#
#  THE LANE: at close, an advance with an explicit against_month (a
#  D331-era row), NOT interest-bearing, taken with the default
#  recover-fully instalment (instalment == amount), recovers IN FULL
#  in its own lane, beside the waterfall — never inside its queue.
#  A deliberately PARTIAL instalment opts back into the waterfall.
#  A loan Skip pauses ONLY the waterfall; the quota lane always
#  collects. The waterfall's order and arithmetic are byte-untouched.
#  Statement cards on quota rows now say "recovers in full at the
#  <month> close (quota lane)" instead of the waiting line.
#
#  D317 chain. Projection: current 214 -> new 218 (+4: full recovery
#  beside an open loan · the same close still runs the waterfall ·
#  partial instalment waits in the waterfall · a skip month pauses
#  only the waterfall), written before measuring.
# =====================================================================
set -u
cd "$(dirname "$0")"
WANT_LIVE=3b09073a3dd0142a61c80d5a6d7aa711    # S190_SL3, Register-pinned
LIVE=/root/staff_ledger.py
PY=/root/wa/venv/bin/python3
SVC=staff-ledger.service
echo "==============================================================="
echo " S190_SL4 · the quota lane: this month's advance recovers now"
echo "==============================================================="
echo "[1/6] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "      KIT_ID : $(cat KIT_ID.txt)"
echo "[2/6] currency gate"
H=$(md5sum $LIVE | cut -d' ' -f1); echo "      live : $H"
[ "$H" = "$WANT_LIVE" ] || { echo '*** RED: live is not the SL3 build. STOP.'; exit 1; }
echo "[3/6] PROJECTION: current 214 -> new 218 (+4)."
CUR=$($PY $LIVE --selftest 2>&1 | tail -1); echo "      $CUR"
echo "$CUR" | grep -q "PASSED — 214 " || { echo '*** RED. STOP.'; exit 1; }
NEW=$($PY ./staff_ledger_SL4.py --selftest 2>&1 | tail -1); echo "      $NEW"
echo "$NEW" | grep -q "PASSED — 218 " || { echo '*** RED. STOP.'; exit 1; }
TS=$(date +%Y%m%d_%H%M%S); BAK=/root/staff_ledger.py.bak_S190_SL4_$TS
echo "[4/6] backup: $BAK"; cp -p $LIVE $BAK || exit 1
echo "[5/6] swap"; cp staff_ledger_SL4.py $LIVE
POST=$($PY $LIVE --selftest 2>&1 | tail -1); echo "      $POST"
echo "$POST" | grep -q "PASSED — 218 " || {
  echo "*** RED — ROLLING BACK."; cp -p $BAK $LIVE; systemctl restart $SVC; exit 1; }
echo "[6/6] restart"; systemctl restart $SVC; sleep 2
systemctl is-active --quiet $SVC && echo "      $SVC : active" || {
  echo "*** RED — ROLLING BACK."; cp -p $BAK $LIVE; systemctl restart $SVC; exit 1; }
echo "==============================================================="
echo " GREEN.  S190_SL4 is live."
echo "   staff_ledger.py  $(md5sum $LIVE | cut -d' ' -f1)"
echo "   selftest 214 -> 218  (+4 checks, 0 failures)"
echo " NOW LOOK (the F-132 rule): Darpan's statement — the Rs 15,000"
echo " and Rs 10,000 cards must now read:"
echo "   recovers in full at the 2026-08 close (quota lane, against"
echo "   2026-08 / 2026-07 salary)"
echo " and the Rs 5,000 card:  ... at the 2026-09 close."
echo " The Rs 1,80,000 tranche STILL says 'waiting for the loan to"
echo " clear' — that one is legacy and genuinely waits (D250)."
echo "==============================================================="
