#!/bin/bash
# =====================================================================
#  S201_UI - /finance/health migrated to Clinic Design Language v1, and
#  the nested-<a> fault fixed. The Correction-checklist row wrapped the
#  whole row in an anchor while its hint carried a second anchor inside
#  it; nested <a> is invalid, every browser un-nests it, and the row
#  rendered broken on the live page. ONE file: finance_app.py
#  024399775bfd14844f299b3dfac4bb47 -> 3f72e9ad16d915fe5ced45c4e28a2248   smoke +3.
# =====================================================================
set -u
cd "$(dirname "$0")"
FIN=/root/finance/finance_app.py
FSVC=clinic-finance.service
WANT_FIN=024399775bfd14844f299b3dfac4bb47
NEW_FIN=3f72e9ad16d915fe5ced45c4e28a2248
LOG=/tmp/s201_ui_smoke.$$
md5of(){ md5sum "$1" | awk '{print $1}'; }
show(){ echo "      ---- last 40 lines ----"; tail -40 "$1" | sed 's/^/      /'; echo "      -----------------------"; }
echo "==============================================================="
echo " S201_UI · health page redesign + the nested-anchor fix"
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
TS=$(date +%Y%m%d_%H%M%S); BK=/root/deploy/_backup_S201_UI_$TS; mkdir -p "$BK"
echo "[4/7] backup -> $BK"; cp -p "$FIN" "$BK/finance_app.py"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/finance_app.py" "$FIN"; systemctl restart $FSVC; sleep 2; echo "   log kept at $LOG"; exit 1; }
echo "[5/7] swap + payload md5 + py_compile"
cp finance_app.py "$FIN" || rollback
[ "$(md5of $FIN)" = "$NEW_FIN" ] || rollback
python3 -c "import py_compile; py_compile.compile('$FIN',doraise=True); print('      finance OK')" || rollback
echo "[6/7] smoke - ALL-GREEN and GROWN (projection: $CUR_T -> +3)"
(cd /root/finance && python3 finance_app.py --selftest) >"$LOG" 2>&1
NEW=$(grep -m1 "SMOKE " "$LOG"); echo "      ${NEW:-<no SMOKE line>}"
echo "${NEW:-}"|grep -Eq "SMOKE ([0-9]+)/\1 " || { grep "FAIL:" "$LOG"|sed 's/^/        /'; show "$LOG"; rollback; }
NEW_T=$(echo "$NEW"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
[ "$NEW_T" -eq $((CUR_T + 3)) ] || { echo "*** RED: expected exactly +3 ($CUR_T -> $NEW_T)."; rollback; }
echo "[7/7] the design + the fix are in the installed bytes + restart"
grep -q -- '--surface-page:#f3f2ee' "$FIN" || rollback
grep -q 'id="toTop"'                 "$FIN" || rollback
grep -q 'class="kick"'               "$FIN" || rollback
grep -q 'details class="help"'       "$FIN" || rollback
grep -q '_delink'                    "$FIN" || rollback
grep -q 'Sale bills without a clinic ID' "$FIN" || rollback
systemctl restart $FSVC || rollback
sleep 2
systemctl is-active --quiet $FSVC || rollback
curl -s -o /dev/null -w "      /finance/healthz -> HTTP %{http_code} (informational)\n" -m 5 http://127.0.0.1:8106/finance/healthz || true
rm -f "$LOG"
echo "==============================================================="
echo " GREEN.  finance_app.py $(md5of $FIN)  smoke $NEW_T (was $CUR_T)"
echo " /finance/health now follows Clinic Design Language v1 and is"
echo " REGISTERED in the F-130 table, so it cannot revert silently."
echo " The Correction-checklist row renders correctly again."
echo " Backup: $BK"
echo "==============================================================="
