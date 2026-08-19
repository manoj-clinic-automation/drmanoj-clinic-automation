#!/bin/bash
# =====================================================================
#  S190_SL2 · D331: the staff advance policy — ceiling · special ·
#  the signed application · month attribution
#
#  OWNER RULINGS (S190, all in the signed contract
#  S190_Staff_Advance_Policy_D331.md):
#    · every staff member sees, inline, the month's advance total beside
#      the maximum permissible — 50% of base salary floored to Rs 100,
#      Darpan 75% (advance_pct.json; the base from staff_master.csv, the
#      file /salary already reads — derived, never typed, F-136)
#    · above the ceiling = a SPECIAL advance: maker may draft it, and it
#      is NEVER direct — even a checker's own entry goes PENDING, because
#      approval REFUSES until the signed written application (Dr Manoj /
#      Dr Bhawna) is uploaded against the row. No escape hatch.
#    · an advance may be attributed AGAINST a future month's salary (the
#      17-Aug Rs 5,000 device): it counts against THAT month's quota and
#      the close recovers it only from that month. The waterfall's order
#      and arithmetic are byte-untouched — only snapshot eligibility.
#    · base salary missing => the gate stands down VISIBLY (inline note),
#      never freezes advances on a data gap.
#
#  D250 close engine arithmetic: untouched. Interest, skips,
#  capitalisation, tranche order: untouched. Applies from AUGUST.
#
#  D317 chain: verify kit bytes -> currency gate on the live file ->
#  current selftest green (190) -> new selftest green (212, projection
#  +22 written before measuring; offline 212 exact, seventh consecutive
#  projection to land) -> backup -> swap -> selftest again -> restart.
# =====================================================================
set -u
cd "$(dirname "$0")"

WANT_LIVE=92665b64f015fee9302ac3da6100f5c8    # Register-pinned, service-verified S189
LIVE=/root/staff_ledger.py
PY=/root/wa/venv/bin/python3
SVC=staff-ledger.service

echo "==============================================================="
echo " S190_SL2 · D331: ceiling · special · application · month"
echo "==============================================================="

echo "[1/7] kit bytes"
md5sum -c SUMS.md5 || { echo '*** RED: kit bytes do not match SUMS.md5. STOP.'; exit 1; }
echo "      KIT_ID : $(cat KIT_ID.txt)"

echo "[2/7] currency gate"
H=$(md5sum $LIVE | cut -d' ' -f1)
echo "      live staff_ledger.py : $H"
if [ "$H" != "$WANT_LIVE" ]; then
  echo "*** RED: the live ledger is not the build this kit was made on. STOP."
  echo "*** Nothing has been changed."
  exit 1
fi

echo "[3/7] THE PROJECTION — written down BEFORE anything is measured."
echo "      (a) the CURRENT ledger selftest: PASSED with exactly 190 checks."
echo "      (b) the NEW build's selftest: PASSED with exactly 212 (+22)."
echo "      Either failing is a RED and nothing is swapped."

echo "[4/7] current selftest"
CUR=$($PY $LIVE --selftest 2>&1 | tail -1)
echo "      $CUR"
echo "$CUR" | grep -q "SELFTEST PASSED — 190 " || {
  echo "*** RED: the current ledger does not pass its own suite at 190. STOP."; exit 1; }

echo "[5/7] new build selftest (staged)"
NEW=$($PY ./staff_ledger_SL2.py --selftest 2>&1 | tail -1)
echo "      $NEW"
echo "$NEW" | grep -q "SELFTEST PASSED — 212 " || {
  echo "*** RED: the new build does not land on the projection (212). STOP."; exit 1; }

TS=$(date +%Y%m%d_%H%M%S)
BAK=/root/staff_ledger.py.bak_S190_SL2_$TS
echo "[6/7] backup: $BAK"
cp -p $LIVE $BAK || { echo '*** RED: backup failed. STOP.'; exit 1; }

echo "[7/7] swap + verify + restart"
cp staff_ledger_SL2.py $LIVE
NEWH=$(md5sum $LIVE | cut -d' ' -f1)
POST=$($PY $LIVE --selftest 2>&1 | tail -1)
echo "      installed md5 : $NEWH"
echo "      $POST"
echo "$POST" | grep -q "SELFTEST PASSED — 212 " || {
  echo "*** RED: post-swap selftest failed — ROLLING BACK."
  cp -p $BAK $LIVE; systemctl restart $SVC
  echo "*** restored $(md5sum $LIVE | cut -d' ' -f1); nothing live changed."; exit 1; }
# seed the pct file only if absent — never overwrite a live setting
if [ ! -f /root/staff_ledger/advance_pct.json ]; then
  printf '{"Darpan": 75}\n' > /root/staff_ledger/advance_pct.json
  chmod 600 /root/staff_ledger/advance_pct.json
  echo "      advance_pct.json seeded: {\"Darpan\": 75} (default 50 for everyone else)"
else
  echo "      advance_pct.json already exists — left untouched"
fi
systemctl restart $SVC
sleep 2
systemctl is-active --quiet $SVC && echo "      $SVC : active" || {
  echo "*** RED: service did not come back — ROLLING BACK."
  cp -p $BAK $LIVE; systemctl restart $SVC; exit 1; }
echo "==============================================================="
echo " GREEN.  S190_SL2 is live."
echo "   staff_ledger.py  $NEWH"
echo "   selftest 190 -> 212  (+22 checks, 0 failures)"
echo " DARPAN'S DERIVED CEILING, from the box's own staff_master.csv:"
$PY - <<PYEOF
import sys; sys.path.insert(0, "/root")
import staff_ledger as sl
c = sl.advance_ceiling("Darpan")
print("   Rs %d  (pct %d)" % (c, sl.advance_pct("Darpan")))
if c != 15000:
    print("   *** NOTE: expected Rs 15000 (75%% of a Rs 20,000 base).")
    print("   *** The gate works off THIS number — if it is wrong, fix")
    print("   *** base_salary in /root/staff_master.csv (the open Q, D331 s5.3).")
PYEOF
echo " Pin the new md5 into the KB Register as it stands (D321(d))."
echo "==============================================================="
