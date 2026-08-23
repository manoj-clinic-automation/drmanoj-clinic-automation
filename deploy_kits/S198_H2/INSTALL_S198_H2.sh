#!/bin/bash
# =====================================================================
#  S198_H2 — the owner's three health-page findings (23-Aug):
#   1. worst-first was CLAIMED and never sorted -> sorted for real, and
#      the hero now NAMES the culprit checks ("Something is wrong -> X").
#   2. the Marg-push age counted Sunday as an open day -> Sunday-aware
#      (each closed Sunday buys the sender 24 quiet hours; D322).
#   3. the Renewals row is now a door to the Renewals Master v2 sheet.
#  ONE file: finance_app.py  4ae49536309dad169441f7dc8fed7012 -> 2c99b2c6c719091deada5603fc295c90   smoke +6.
# =====================================================================
set -u
cd "$(dirname "$0")"
FIN=/root/finance/finance_app.py
FSVC=clinic-finance.service
WANT_FIN=4ae49536309dad169441f7dc8fed7012
NEW_FIN=2c99b2c6c719091deada5603fc295c90
LOG=/tmp/s198_h2_smoke.$$
md5of(){ md5sum "$1" | awk '{print $1}'; }
show(){ echo "      ---- last 40 lines ----"; tail -40 "$1" | sed 's/^/      /'; echo "      -----------------------"; }
echo "==============================================================="
echo " S198_H2 · health page: worst-first + Sunday-aware + renewals door"
echo "==============================================================="
echo "[1/7] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "[2/7] currency gate"
H=$(md5of "$FIN"); echo "      finance_app : $H"
[ "$H" = "$WANT_FIN" ] || { echo "*** RED: expected $WANT_FIN. STOP — tell Claude this hash."; exit 1; }
echo "[3/7] baseline smoke"
(cd /root/finance && python3 finance_app.py --selftest) >"$LOG" 2>&1
CUR=$(grep -m1 "SMOKE " "$LOG"); echo "      ${CUR:-<no SMOKE line>}"
echo "${CUR:-}"|grep -Eq "SMOKE ([0-9]+)/\1 " || { echo '*** RED: baseline not all-green.'; grep "FAIL:" "$LOG"|sed 's/^/        /'; show "$LOG"; exit 1; }
CUR_T=$(echo "$CUR"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
TS=$(date +%Y%m%d_%H%M%S); BK=/root/deploy/_backup_S198_H2_$TS; mkdir -p "$BK"
echo "[4/7] backup -> $BK"; cp -p "$FIN" "$BK/finance_app.py"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/finance_app.py" "$FIN"; systemctl restart $FSVC; sleep 2; echo "   log kept at $LOG"; exit 1; }
echo "[5/7] swap + payload md5 + py_compile"
cp finance_app.py "$FIN" || rollback
[ "$(md5of $FIN)" = "$NEW_FIN" ] || rollback
python3 -c "import py_compile; py_compile.compile('$FIN',doraise=True); print('      finance OK')" || rollback
echo "[6/7] smoke — ALL-GREEN and GROWN (projection: $CUR_T -> +6)"
(cd /root/finance && python3 finance_app.py --selftest) >"$LOG" 2>&1
NEW=$(grep -m1 "SMOKE " "$LOG"); echo "      ${NEW:-<no SMOKE line>}"
echo "${NEW:-}"|grep -Eq "SMOKE ([0-9]+)/\1 " || { grep "FAIL:" "$LOG"|sed 's/^/        /'; show "$LOG"; rollback; }
NEW_T=$(echo "$NEW"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
[ "$NEW_T" -eq $((CUR_T + 6)) ] || { echo "*** RED: expected exactly +6 ($CUR_T -> $NEW_T)."; rollback; }
echo "[7/7] the fixes are in the installed bytes + restart"
grep -q "_sundays_between" "$FIN" || rollback
grep -q "1OB70_Mapuugc33zkfFevwnrS0e8s1NdWzsrzJDqO38E" "$FIN" || rollback
systemctl restart $FSVC || rollback
sleep 2
systemctl is-active --quiet $FSVC || rollback
curl -s -o /dev/null -w "      /finance/healthz -> HTTP %{http_code} (informational)\n" -m 5 http://127.0.0.1:8106/finance/healthz || true
rm -f "$LOG"
echo "==============================================================="
echo " GREEN.  finance_app.py $(md5of $FIN)  smoke $NEW_T (was $CUR_T)"
echo " The health page now: red rows FIRST, the hero names the culprit,"
echo " Sundays don't cry wolf, and Renewals opens its master sheet."
echo " Backup: $BK"
echo "==============================================================="
