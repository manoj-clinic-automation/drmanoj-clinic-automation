#!/bin/bash
# =====================================================================
#  S195_A123 — the three checks from the drawer investigation
#
#  A1  TOTAL vs MARG, at save time.
#      18-08-2026 was entered as 23,879 when the report AND the counter
#      copy both said 25,176 — cash short by Rs 1,297. Nothing compared
#      the two, so it surfaced three days later through a drawer that
#      would not balance. Now the save warns on screen and raises a
#      TOTAL_VS_MARG flag for the checker. It never BLOCKS.
#
#  A2  CASH POSITION, stated honestly.
#      The health page showed the RAW ledger closing (1,93,904) as if it
#      were the counter's drawer. It is not — it includes cash parked
#      with the doctors. It now shows counter / parked / unbanked, using
#      the same reconciliation /finance/api/cash-position already used.
#
#  A3  UPI EVIDENCE.
#      Cash is DERIVED (total − UPI) and UPI is typed by hand off the
#      machine — Marg labels every bill .CASH. A day whose UPI is not
#      matched to the bank now says so.
#
#  Also adds 5 selftests for the health endpoints, so the smoke count
#  GROWS with the feature (owed from the last kit).
#
#  Currency-gated. Backup, py_compile, --selftest ALL-GREEN and grown,
#  restart, rollback on any red.
# =====================================================================
set -u
cd "$(dirname "$0")"
LIVE=/root/finance/finance_app.py
SVC=clinic-finance.service
WANT=e3a4ba79c2e060bcebe11c075bdbbc7b

echo "==============================================================="
echo " S195_A123 · total-vs-Marg · cash position · UPI evidence"
echo "==============================================================="
echo "[1/8] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }

echo "[2/8] currency gate"
[ -f "$LIVE" ] || { echo "*** RED: $LIVE missing."; exit 1; }
H=$(md5sum "$LIVE"|cut -d' ' -f1); echo "      finance_app : $H"
[ "$H" = "$WANT" ] || { echo "*** RED: not the expected build ($WANT). STOP — tell Cowork this hash."; exit 1; }

echo "[3/8] baseline smoke"
CUR=$(cd /root/finance && python3 finance_app.py --selftest 2>&1|grep -m1 "SMOKE "); echo "      $CUR"
echo "$CUR"|grep -Eq "SMOKE ([0-9]+)/\1 " || { echo '*** RED: baseline not all-green. STOP.'; cd /root/finance && python3 finance_app.py --selftest 2>&1|grep "FAIL:"|sed 's/^/        /'; exit 1; }
CUR_T=$(echo "$CUR"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')

TS=$(date +%Y%m%d_%H%M%S); BK=/root/finance/_backup_S195_A123_$TS; mkdir -p "$BK"
echo "[4/8] backup -> $BK"; cp -p "$LIVE" "$BK/"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/finance_app.py" "$LIVE"; systemctl restart $SVC; sleep 2; echo "   service: $(systemctl is-active $SVC)"; exit 1; }

echo "[5/8] swap"; cp finance_app.py "$LIVE" || rollback
echo "[6/8] py_compile"; python3 -c "import py_compile; py_compile.compile('$LIVE',doraise=True); print('      OK')" || rollback

echo "[7/8] smoke — ALL-GREEN and GROWN (the 5 new health checks must run)"
NEW=$(cd /root/finance && python3 finance_app.py --selftest 2>&1|grep -m1 "SMOKE "); echo "      $NEW"
echo "$NEW"|grep -Eq "SMOKE ([0-9]+)/\1 " || { cd /root/finance && python3 finance_app.py --selftest 2>&1|grep "FAIL:"|sed 's/^/        /'; rollback; }
NEW_T=$(echo "$NEW"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
[ "$NEW_T" -gt "$CUR_T" ] || { echo "*** RED: the new checks did not run ($CUR_T -> $NEW_T)."; rollback; }

echo "[8/8] restart + verify"; systemctl restart $SVC; sleep 2; systemctl is-active --quiet $SVC || rollback

echo "==============================================================="
echo " GREEN.  finance_app.py $(md5sum $LIVE|cut -d' ' -f1)  smoke $NEW_T (was $CUR_T)"
echo " Health page: https://followup.dr-manoj.in/finance/health"
echo " Backup: $BK"
echo "==============================================================="
