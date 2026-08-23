#!/bin/bash
# =====================================================================
#  S196_HLT2 — the health headline reaches the PORTAL TILE.
#
#  After the 21-08 Marg-401 crisis, S195 built /finance/health AND a
#  _health_headline() helper "for the portal tile" — and nothing ever
#  consumed it: the page went red while the tile looked innocent. This
#  kit is the missing wire, two small changes:
#    finance_app.py  cfacce27... -> (payload)  tile-summary now carries
#                    health_line (None when all is well). +2 smoke: 665->667.
#    portal.py       ff089807... -> (payload)  the Sanjeevni tile shows
#                    that line FIRST, fail-soft as ever.
# =====================================================================
set -u
cd "$(dirname "$0")"
FIN=/root/finance/finance_app.py
POR=/root/portal/portal.py
FSVC=clinic-finance.service
PSVC=clinic-portal.service
WANT_FIN=cfacce276153e7ff83c58e0fc2e7ddc7
WANT_POR=ff08980737c107c3babb78b0c5c169c2
NEW_FIN=6fc3becc92c2f28f9f5533611e5c1af7
NEW_POR=ee749cd9f3ac1294aab0d13ce069efc1
LOG=/tmp/s196_hlt2_smoke.$$

md5of(){ md5sum "$1" | awk '{print $1}'; }
show(){ echo "      ---- last 40 lines ----"; tail -40 "$1" | sed 's/^/      /'; echo "      -----------------------"; }

echo "==============================================================="
echo " S196_HLT2 · the health headline reaches the portal tile"
echo "==============================================================="
echo "[1/9] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }

echo "[2/9] currency gates (both live files)"
H=$(md5of "$FIN"); echo "      finance_app : $H"
[ "$H" = "$WANT_FIN" ] || { echo "*** RED: expected $WANT_FIN (install S196_HLT1 first?). STOP."; exit 1; }
H=$(md5of "$POR"); echo "      portal      : $H"
[ "$H" = "$WANT_POR" ] || { echo "*** RED: expected $WANT_POR. STOP — tell Claude this hash."; exit 1; }

echo "[3/9] baseline finance smoke"
(cd /root/finance && python3 finance_app.py --selftest) >"$LOG" 2>&1
CUR=$(grep -m1 "SMOKE " "$LOG"); echo "      ${CUR:-<no SMOKE line>}"
echo "${CUR:-}"|grep -Eq "SMOKE ([0-9]+)/\1 " || { echo '*** RED: baseline not all-green.'; grep "FAIL:" "$LOG"|sed 's/^/        /'; show "$LOG"; exit 1; }
CUR_T=$(echo "$CUR"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')

TS=$(date +%Y%m%d_%H%M%S); BK=/root/deploy/_backup_S196_HLT2_$TS; mkdir -p "$BK"
echo "[4/9] backups -> $BK"; cp -p "$FIN" "$BK/finance_app.py"; cp -p "$POR" "$BK/portal.py"
rollback(){ echo "*** RED -- ROLLBACK (both files)."; cp -p "$BK/finance_app.py" "$FIN"; cp -p "$BK/portal.py" "$POR"; systemctl restart $FSVC $PSVC; sleep 2; echo "   finance: $(systemctl is-active $FSVC) · portal: $(systemctl is-active $PSVC)"; echo "   log kept at $LOG"; exit 1; }

echo "[5/9] swap + payload md5s"
cp finance_app.py "$FIN" || rollback
cp portal.py "$POR" || rollback
[ "$(md5of $FIN)" = "$NEW_FIN" ] || { echo "*** RED: finance bytes wrong"; rollback; }
[ "$(md5of $POR)" = "$NEW_POR" ] || { echo "*** RED: portal bytes wrong"; rollback; }

echo "[6/9] py_compile both"
python3 -c "import py_compile; py_compile.compile('$FIN',doraise=True); print('      finance OK')" || rollback
python3 -c "import py_compile; py_compile.compile('$POR',doraise=True); print('      portal OK')" || rollback

echo "[7/9] finance smoke — ALL-GREEN and GROWN (projection: $CUR_T -> 667)"
(cd /root/finance && python3 finance_app.py --selftest) >"$LOG" 2>&1
NEW=$(grep -m1 "SMOKE " "$LOG"); echo "      ${NEW:-<no SMOKE line>}"
echo "${NEW:-}"|grep -Eq "SMOKE ([0-9]+)/\1 " || { grep "FAIL:" "$LOG"|sed 's/^/        /'; show "$LOG"; rollback; }
NEW_T=$(echo "$NEW"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
[ "$NEW_T" -gt "$CUR_T" ] || { echo "*** RED: new checks did not run ($CUR_T -> $NEW_T)."; rollback; }

echo "[8/9] the wire itself, gated on the installed BYTES"
grep -q "health_line" "$FIN" || { echo "*** RED: finance missing the field"; rollback; }
grep -q "d.health_line" "$POR" || { echo "*** RED: portal missing the wire"; rollback; }
echo "      OK — both ends present."

echo "[9/9] restart both + probes"
systemctl restart $FSVC $PSVC || rollback
sleep 2
systemctl is-active --quiet $FSVC || rollback
systemctl is-active --quiet $PSVC || rollback
curl -s -o /dev/null -w "      /finance/healthz -> HTTP %{http_code}\n" -m 5 http://127.0.0.1:8106/finance/healthz
curl -s -o /dev/null -w "      /portal/health   -> HTTP %{http_code}\n" -m 5 http://127.0.0.1:8090/portal/health

rm -f "$LOG"
echo "==============================================================="
echo " GREEN.  finance_app.py $(md5of $FIN)  smoke $NEW_T (was $CUR_T)"
echo "         portal.py      $(md5of $POR)"
echo " From now on: anything the health page calls WRONG shows up as"
echo " the FIRST line on the Sanjeevni tile itself. All clear = tile"
echo " unchanged. Backups: $BK"
echo "==============================================================="
