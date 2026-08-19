#!/bin/bash
# =====================================================================
#  S192_SL7 · D332 §2.9 — the per-staff PERKS view (closes F-149)
#
#  A perk is a RECORD of a benefit paid, not money owed: it carries no
#  approval chain and is excluded from salary by design. The gap: it
#  could be ENTERED and then never READ. Perks sat in the ledger with
#  nowhere to see them — F-149, "the perks route is unreachable".
#
#  This kit adds /ledger/perks (checker-only, in the nav):
#    * an index of every staff member's NET perk total, tap for detail
#    * a per-staff view with the LIFETIME total and a YEAR filter
#    * append-only honesty — a contra'd perk nets to zero and BOTH rows
#      stay visible, greyed, exactly like the rest of the ledger
#
#  No schema change, no migration, no money touched. Read-only surface.
#
#  D317 chain. Projection: current 274 -> new 287 (+13), counted from
#  the test block itself before measuring.
# =====================================================================
set -u
cd "$(dirname "$0")"
WANT_LIVE=0279540ed8e6fe8ebd75781544ffc209    # S192_SL6, the current live build
LIVE=/root/staff_ledger.py
PY=/root/wa/venv/bin/python3
SVC=staff-ledger.service
echo "==============================================================="
echo " S192_SL7 · the per-staff Perks view (F-149)"
echo "==============================================================="
echo "[1/6] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "      KIT_ID : $(cat KIT_ID.txt)"
echo "[2/6] currency gate"
H=$(md5sum $LIVE | cut -d' ' -f1); echo "      live : $H"
[ "$H" = "$WANT_LIVE" ] || { echo '*** RED: live is not the SL6 build. STOP.'; exit 1; }
echo "[3/6] PROJECTION: current 274 -> new 287 (+13)."
CUR=$($PY $LIVE --selftest 2>&1 | tail -1); echo "      $CUR"
echo "$CUR" | grep -q "PASSED — 274 " || { echo '*** RED. STOP.'; exit 1; }
NEW=$($PY ./staff_ledger_SL7.py --selftest 2>&1 | tail -1); echo "      $NEW"
echo "$NEW" | grep -q "PASSED — 287 " || { echo '*** RED. STOP.'; exit 1; }
TS=$(date +%Y%m%d_%H%M%S); BAK=/root/staff_ledger.py.bak_S192_SL7_$TS
echo "[4/6] backup: $BAK"; cp -p $LIVE $BAK || exit 1
echo "[5/6] swap"; cp staff_ledger_SL7.py $LIVE
POST=$($PY $LIVE --selftest 2>&1 | tail -1); echo "      $POST"
echo "$POST" | grep -q "PASSED — 287 " || {
  echo "*** RED — ROLLING BACK."; cp -p $BAK $LIVE; systemctl restart $SVC; exit 1; }
echo "[6/6] restart"; systemctl restart $SVC; sleep 2
systemctl is-active --quiet $SVC && echo "      $SVC : active" || {
  echo "*** RED — ROLLING BACK."; cp -p $BAK $LIVE; systemctl restart $SVC; exit 1; }
echo "==============================================================="
echo " GREEN.  S192_SL7 is live."
echo "   staff_ledger.py  $(md5sum $LIVE | cut -d' ' -f1)"
echo "   selftest 274 -> 287  (+13 checks, 0 failures)"
echo " NOW LOOK (the F-132 rule): a new 'Perks' link in the top nav."
echo "   It lists each staff member's net perk total; tap a name for"
echo "   the lifetime figure, the year filter and every line."
echo " Darpan's migrated perks (school fees etc, entered with the S155"
echo " loan migration) should appear there for the first time."
echo "==============================================================="
