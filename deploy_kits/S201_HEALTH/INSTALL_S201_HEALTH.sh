#!/bin/bash
# =====================================================================
#  S201_HEALTH - "This month vs Marg" compared the whole day against
#  attributed-only lines, so it could never go green; the differing-day
#  list truncated at five in silence; and the review queue was never
#  named. ONE file: finance_app.py d930b6b5... -> 024399775bfd14844f299b3dfac4bb47   smoke +7.
# =====================================================================
set -u
cd "$(dirname "$0")"
FIN=/root/finance/finance_app.py
FSVC=clinic-finance.service
WANT_FIN=d930b6b5bca59e7f52ce46f6b88332fd
NEW_FIN=024399775bfd14844f299b3dfac4bb47
LOG=/tmp/s201_health_smoke.$$
md5of(){ md5sum "$1" | awk '{print $1}'; }
show(){ echo "      ---- last 40 lines ----"; tail -40 "$1" | sed 's/^/      /'; echo "      -----------------------"; }
echo "==============================================================="
echo " S201_HEALTH · the month row can go green, and names the queue"
echo "==============================================================="
echo "[1/7] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "[2/7] currency gate"
H=$(md5of "$FIN"); echo "      finance_app : $H"
[ "$H" = "$WANT_FIN" ] || { echo "*** RED: expected $WANT_FIN. STOP - tell Claude this hash."; exit 1; }
echo "[3/7] baseline smoke"
(cd /root/finance && python3 finance_app.py --selftest) >"$LOG" 2>&1
CUR=$(grep -m1 "SMOKE " "$LOG"); echo "      ${CUR:-<no SMOKE line>}"
echo "${CUR:-}"|grep -Eq "SMOKE ([0-9]+)/\1 " || { echo '*** RED: baseline not all-green.'; grep "FAIL:" "$LOG"|sed 's/^/        /'; show "$LOG"; exit 1; }
CUR_T=$(echo "$CUR"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
TS=$(date +%Y%m%d_%H%M%S); BK=/root/deploy/_backup_S201_HEALTH_$TS; mkdir -p "$BK"
echo "[4/7] backup -> $BK"; cp -p "$FIN" "$BK/finance_app.py"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/finance_app.py" "$FIN"; systemctl restart $FSVC; sleep 2; echo "   log kept at $LOG"; exit 1; }
echo "[5/7] swap + payload md5 + py_compile"
cp finance_app.py "$FIN" || rollback
[ "$(md5of $FIN)" = "$NEW_FIN" ] || rollback
python3 -c "import py_compile; py_compile.compile('$FIN',doraise=True); print('      finance OK')" || rollback
echo "[6/7] smoke - ALL-GREEN and GROWN (projection: $CUR_T -> +7)"
(cd /root/finance && python3 finance_app.py --selftest) >"$LOG" 2>&1
NEW=$(grep -m1 "SMOKE " "$LOG"); echo "      ${NEW:-<no SMOKE line>}"
echo "${NEW:-}"|grep -Eq "SMOKE ([0-9]+)/\1 " || { grep "FAIL:" "$LOG"|sed 's/^/        /'; show "$LOG"; rollback; }
NEW_T=$(echo "$NEW"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
[ "$NEW_T" -eq $((CUR_T + 7)) ] || { echo "*** RED: expected exactly +7 ($CUR_T -> $NEW_T)."; rollback; }
echo "[7/7] the fixes are in the installed bytes + restart"
grep -q 'margqueue' "$FIN" || rollback
grep -q 'Sale bills without a clinic ID' "$FIN" || rollback
grep -q 'accounted_p = marg_p + review_p' "$FIN" || rollback
grep -q 'and %d more' "$FIN" || rollback
systemctl restart $FSVC || rollback
sleep 2
systemctl is-active --quiet $FSVC || rollback
curl -s -o /dev/null -w "      /finance/healthz -> HTTP %{http_code} (informational)\n" -m 5 http://127.0.0.1:8106/finance/healthz || true
rm -f "$LOG"
echo "==============================================================="
echo " GREEN.  finance_app.py $(md5of $FIN)  smoke $NEW_T (was $CUR_T)"
echo " The month row now compares like with like and can go green."
echo " The queue has its own INFO row and no longer drives the tile."
echo " Backup: $BK"
echo "==============================================================="
