#!/bin/bash
# =====================================================================
#  S196_HLT3 — F-162: the A4 month-vs-Marg health check, ALIVE for the
#  first time. `today()` was shadowed by _health_state's local date, so
#  BOTH A4 cards ("This month vs Marg" + "Marg days never filed") died
#  into their except on every render since S195. One line fixed; one new
#  smoke check refuses the whole swallowed-exception class. 667 -> 668.
# =====================================================================
set -u
cd "$(dirname "$0")"
LIVE=/root/finance/finance_app.py
SVC=clinic-finance.service
WANT=6fc3becc92c2f28f9f5533611e5c1af7
NEWH=388c8ac0fdfecdee6029c0033b9b0ef8
LOG=/tmp/s196_hlt3_smoke.$$
md5of(){ md5sum "$1" | awk '{print $1}'; }
show(){ echo "      ---- last 40 lines ----"; tail -40 "$1" | sed 's/^/      /'; echo "      -----------------------"; }

echo "[1/7] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "[2/7] currency gate"
H=$(md5of "$LIVE"); echo "      finance_app : $H"
[ "$H" = "$WANT" ] || { echo "*** RED: expected $WANT (HLT2 must be live). STOP."; exit 1; }
echo "[3/7] baseline smoke"
(cd /root/finance && python3 finance_app.py --selftest) >"$LOG" 2>&1
CUR=$(grep -m1 "SMOKE " "$LOG"); echo "      ${CUR:-<no SMOKE line>}"
echo "${CUR:-}"|grep -Eq "SMOKE ([0-9]+)/\1 " || { echo '*** RED: baseline not all-green.'; grep "FAIL:" "$LOG"|sed 's/^/        /'; show "$LOG"; exit 1; }
CUR_T=$(echo "$CUR"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
TS=$(date +%Y%m%d_%H%M%S); BK=/root/finance/_backup_S196_HLT3_$TS; mkdir -p "$BK"
echo "[4/7] backup -> $BK"; cp -p "$LIVE" "$BK/"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/finance_app.py" "$LIVE"; systemctl restart $SVC; sleep 2; echo "   service: $(systemctl is-active $SVC)"; echo "   log kept at $LOG"; exit 1; }
echo "[5/7] swap + md5 + compile"
cp finance_app.py "$LIVE" || rollback
[ "$(md5of $LIVE)" = "$NEWH" ] || { echo "*** RED: bytes wrong"; rollback; }
python3 -c "import py_compile; py_compile.compile('$LIVE',doraise=True); print('      OK')" || rollback
echo "[6/7] smoke — ALL-GREEN and GROWN (projection: $CUR_T -> 668)"
(cd /root/finance && python3 finance_app.py --selftest) >"$LOG" 2>&1
NEW=$(grep -m1 "SMOKE " "$LOG"); echo "      ${NEW:-<no SMOKE line>}"
echo "${NEW:-}"|grep -Eq "SMOKE ([0-9]+)/\1 " || { grep "FAIL:" "$LOG"|sed 's/^/        /'; show "$LOG"; rollback; }
NEW_T=$(echo "$NEW"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
[ "$NEW_T" -gt "$CUR_T" ] || { echo "*** RED: new checks did not run."; rollback; }
echo "[7/7] restart"; systemctl restart $SVC; sleep 2; systemctl is-active --quiet $SVC || rollback
rm -f "$LOG"
echo "==============================================================="
echo " GREEN.  finance_app.py $(md5of $LIVE)  smoke $NEW_T (was $CUR_T)"
echo " Refresh /finance/health — 'This month vs Marg' now shows REAL"
echo " figures (or a real red), and 'Marg days never filed' can appear."
echo "==============================================================="
