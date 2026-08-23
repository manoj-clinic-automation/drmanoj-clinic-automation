#!/bin/bash
# =====================================================================
#  S198_H1 — A2: every health section becomes a DOOR.
#
#  ONE file: finance_app.py  388c8ac0... -> 4ae49536...
#   * /finance/health: each check row with a fix place renders as a LINK
#     landing on the exact Hub card that fixes it (#margCard, #pendCard,
#     #cashPosCard, #stripCard, #monthCard) or the correction checklist;
#     non-ok mapped rows carry a standing plain-English action line.
#   * backup + renewals rows deliberately NOT links (no in-app fix).
#   * _health_state and /finance/api/health byte-untouched -- the tile
#     headline wire (S196_HLT2) and the hero (S198_P1) see no change.
#   * +6 selftest checks. Offline differential on the seeded live-shape
#     store: 557/667 -> 563/673, +6 exactly, fail set byte-identical.
# =====================================================================
set -u
cd "$(dirname "$0")"
FIN=/root/finance/finance_app.py
FSVC=clinic-finance.service
WANT_FIN=388c8ac0fdfecdee6029c0033b9b0ef8
NEW_FIN=4ae49536309dad169441f7dc8fed7012
LOG=/tmp/s198_h1_smoke.$$

md5of(){ md5sum "$1" | awk '{print $1}'; }
show(){ echo "      ---- last 40 lines ----"; tail -40 "$1" | sed 's/^/      /'; echo "      -----------------------"; }

echo "==============================================================="
echo " S198_H1 · the health page becomes clickable"
echo "==============================================================="
echo "[1/8] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }

echo "[2/8] currency gate (live finance_app.py)"
H=$(md5of "$FIN"); echo "      finance_app : $H"
[ "$H" = "$WANT_FIN" ] || { echo "*** RED: expected $WANT_FIN. STOP — tell Claude this hash."; exit 1; }

echo "[3/8] baseline finance smoke"
(cd /root/finance && python3 finance_app.py --selftest) >"$LOG" 2>&1
CUR=$(grep -m1 "SMOKE " "$LOG"); echo "      ${CUR:-<no SMOKE line>}"
echo "${CUR:-}"|grep -Eq "SMOKE ([0-9]+)/\1 " || { echo '*** RED: baseline not all-green.'; grep "FAIL:" "$LOG"|sed 's/^/        /'; show "$LOG"; exit 1; }
CUR_T=$(echo "$CUR"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')

TS=$(date +%Y%m%d_%H%M%S); BK=/root/deploy/_backup_S198_H1_$TS; mkdir -p "$BK"
echo "[4/8] backup -> $BK"; cp -p "$FIN" "$BK/finance_app.py"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/finance_app.py" "$FIN"; systemctl restart $FSVC; sleep 2; echo "   finance: $(systemctl is-active $FSVC)"; echo "   log kept at $LOG"; exit 1; }

echo "[5/8] swap + payload md5"
cp finance_app.py "$FIN" || rollback
[ "$(md5of $FIN)" = "$NEW_FIN" ] || { echo "*** RED: finance bytes wrong"; rollback; }

echo "[6/8] py_compile"
python3 -c "import py_compile; py_compile.compile('$FIN',doraise=True); print('      finance OK')" || rollback

echo "[7/8] finance smoke — ALL-GREEN and GROWN (projection: $CUR_T -> +6)"
(cd /root/finance && python3 finance_app.py --selftest) >"$LOG" 2>&1
NEW=$(grep -m1 "SMOKE " "$LOG"); echo "      ${NEW:-<no SMOKE line>}"
echo "${NEW:-}"|grep -Eq "SMOKE ([0-9]+)/\1 " || { grep "FAIL:" "$LOG"|sed 's/^/        /'; show "$LOG"; rollback; }
NEW_T=$(echo "$NEW"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
[ "$NEW_T" -eq $((CUR_T + 6)) ] || { echo "*** RED: expected exactly +6 checks ($CUR_T -> $NEW_T)."; rollback; }

echo "[8/8] the doors are in the installed bytes + restart"
grep -q "finance/approvals#margCard" "$FIN" || { echo "*** RED: links missing"; rollback; }
grep -q "class=act" "$FIN" || { echo "*** RED: action lines missing"; rollback; }
systemctl restart $FSVC || rollback
sleep 2
systemctl is-active --quiet $FSVC || rollback
# informational only (the probe rule from S198_P1): a code is printed, never judged
curl -s -o /dev/null -w "      /finance/healthz -> HTTP %{http_code} (informational)\n" -m 5 http://127.0.0.1:8106/finance/healthz || true

rm -f "$LOG"
echo "==============================================================="
echo " GREEN.  finance_app.py $(md5of $FIN)  smoke $NEW_T (was $CUR_T)"
echo " Open the Portal Health hero (or /finance/health): every row that"
echo " has a fix place is now a door -- tap it and you land there."
echo " Backup: $BK"
echo "==============================================================="
