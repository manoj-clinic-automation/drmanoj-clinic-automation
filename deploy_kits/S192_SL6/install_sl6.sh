#!/bin/bash
# =====================================================================
#  S192_SL6 · D332 — the SCHEDULE lane, DEFER, and the CAPACITY rule
#
#  (A) THE SCHEDULE (§4). An advance is an amount PLUS a repayment
#      schedule, defined at approval. Default stays uniform (the named
#      instalment); the owner may set an uneven distribution — the
#      17-Aug Rs 20,000 as 8,000 (Aug) + 4,000 x 3 (Sep/Oct/Nov). The
#      close collects the CURRENT month's scheduled amount in its own
#      lane, beside the waterfall, never queued behind the loan book.
#      A schedule must add to the advance exactly or it is refused —
#      a schedule with a silent gap is a promise the close cannot keep.
#      SL4's recover-in-full and a uniform instalment are both special
#      cases of a schedule: one generalisation subsumes all three.
#
#  (B) DEFER replaces SKIP as the owner-facing verb (§2.1). The whole
#      instalment shifts one month and the schedule EXTENDS by one —
#      the tail is never swallowed. No automatic capitalisation:
#      interest rides inside each collected instalment, so deferring
#      leaves total loan interest unchanged. The 2/FY discipline
#      survives as a WAIVABLE PENALTY on interest-bearing loans only —
#      first two defers of the FY free, from the 3rd a Rs 1000 penalty
#      capitalises unless the owner ticks waive and gives a reason.
#      Interest-free advances defer penalty-free, always. A reason is
#      compulsory on every defer. LOAN_SKIP is untouched for history.
#
#  (C) CAPACITY (F-147). Nothing recovers that the salary cannot bear.
#      One budget per staff per month = base - other debits already
#      booked - the protected minimum take-home (setting, default 0),
#      spent by every lane in order. What cannot be taken is recorded
#      as a CAPACITY_HOLD line and STAYS OWED — never silently dropped.
#      No base salary on file DISABLES the gate rather than freezing
#      recovery (the D331 fail-open design), and says so.
#
#  (D) LOUD SURFACES. The Advances card shows amount · schedule ·
#      recovered · months left · next collection, a red DEFERRED band
#      naming every deferred month, and the defer tap with its FY
#      counter. The salary table and full report gain a "deferred"
#      column beside +waived.
#
#  D317 chain. Projection: current 240 -> new 274 (+34), written before
#  measuring and reconciled against the block's own check count.
# =====================================================================
set -u
cd "$(dirname "$0")"
WANT_LIVE=0ed19495e026d9629b75294f39075dc2    # S192_SL5, the current live build
LIVE=/root/staff_ledger.py
PY=/root/wa/venv/bin/python3
SVC=staff-ledger.service
echo "==============================================================="
echo " S192_SL6 · schedule lane + DEFER + capacity rule"
echo "==============================================================="
echo "[1/6] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "      KIT_ID : $(cat KIT_ID.txt)"
echo "[2/6] currency gate"
H=$(md5sum $LIVE | cut -d' ' -f1); echo "      live : $H"
[ "$H" = "$WANT_LIVE" ] || { echo '*** RED: live is not the SL5 build. STOP.'; exit 1; }
echo "[3/6] PROJECTION: current 240 -> new 274 (+34)."
CUR=$($PY $LIVE --selftest 2>&1 | tail -1); echo "      $CUR"
echo "$CUR" | grep -q "PASSED — 240 " || { echo '*** RED. STOP.'; exit 1; }
NEW=$($PY ./staff_ledger_SL6.py --selftest 2>&1 | tail -1); echo "      $NEW"
echo "$NEW" | grep -q "PASSED — 274 " || { echo '*** RED. STOP.'; exit 1; }
TS=$(date +%Y%m%d_%H%M%S); BAK=/root/staff_ledger.py.bak_S192_SL6_$TS
echo "[4/6] backup: $BAK"; cp -p $LIVE $BAK || exit 1
echo "[5/6] swap"; cp staff_ledger_SL6.py $LIVE
POST=$($PY $LIVE --selftest 2>&1 | tail -1); echo "      $POST"
echo "$POST" | grep -q "PASSED — 274 " || {
  echo "*** RED — ROLLING BACK."; cp -p $BAK $LIVE; systemctl restart $SVC; exit 1; }
echo "[6/6] restart"; systemctl restart $SVC; sleep 2
systemctl is-active --quiet $SVC && echo "      $SVC : active" || {
  echo "*** RED — ROLLING BACK."; cp -p $BAK $LIVE; systemctl restart $SVC; exit 1; }
echo "==============================================================="
echo " GREEN.  S192_SL6 is live."
echo "   staff_ledger.py  $(md5sum $LIVE | cut -d' ' -f1)"
echo "   selftest 240 -> 274  (+34 checks, 0 failures)"
echo " NOW LOOK (the F-132 rule): /ledger/advances"
echo "   Every open advance should show its schedule line (or 'no"
echo "   schedule — recovering by instalment'), and a 'Defer this"
echo "   month' box asking for a reason. Darpan's Rs 1,80,000 loan"
echo "   should show 'defers used FY2026-27: 0/2 free'."
echo " NOTHING CHANGED IN THE BOOKS — this kit adds machinery only."
echo " Existing advances carry no schedule, so they recover exactly"
echo " as they did before until you give one a schedule."
echo "==============================================================="
