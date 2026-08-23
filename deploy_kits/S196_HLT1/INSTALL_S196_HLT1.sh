#!/bin/bash
# =====================================================================
#  S196_HLT1 — the renewals line on the health page (Task #8, S195 ⭐2)
#
#  finance_app.py df750243... -> cfacce27...
#    * POST /finance/api/renewals-push — the personal Inbox-Janitor GAS
#      pushes its RENEWALS list daily; ONE-path token (marg-push pattern),
#      NEW token FINANCE_RENEWALS_TOKEN, fail-closed until set.
#      Stores dates in a JSON file — no DB row, no schema change.
#    * Health card 6 "Renewals": days recomputed from dates at render.
#      OVERDUE = bad · feed stale >72h = warn · inside 7 days = warn
#      (reaches the portal tile line) · inside 30 = info ("N inside 30
#      days · nearest: ...") · no feed yet = quiet info.
#  11 new smoke checks. Projection: 654 -> 665, all green.
#
#  S195_SIGN chain: baseline smoke -> swap -> compile -> grown smoke ->
#  restart; rollback on any red.
# =====================================================================
set -u
cd "$(dirname "$0")"
LIVE=/root/finance/finance_app.py
SVC=clinic-finance.service
WANT=df75024392e31ae99bb3fde9fab24062
NEWH=cfacce276153e7ff83c58e0fc2e7ddc7
LOG=/tmp/s196_hlt1_smoke.$$

show(){ echo "      ---- last 40 lines ----"; tail -40 "$1" | sed 's/^/      /'
        echo "      -----------------------"; }

echo "==============================================================="
echo " S196_HLT1 · renewals line on the health page"
echo "==============================================================="
echo "[1/8] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }

echo "[2/8] currency gate"
H=$(md5sum "$LIVE" 2>/dev/null|cut -d' ' -f1); echo "      finance_app : $H"
[ "$H" = "$WANT" ] || { echo "*** RED: expected $WANT. STOP — tell Claude this hash."; exit 1; }

echo "[3/8] baseline smoke"
(cd /root/finance && python3 finance_app.py --selftest) >"$LOG" 2>&1
CUR=$(grep -m1 "SMOKE " "$LOG"); echo "      ${CUR:-<no SMOKE line — the suite crashed>}"
echo "${CUR:-}"|grep -Eq "SMOKE ([0-9]+)/\1 " || { echo '*** RED: baseline not all-green.'; grep "FAIL:" "$LOG"|sed 's/^/        /'; show "$LOG"; exit 1; }
CUR_T=$(echo "$CUR"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')

TS=$(date +%Y%m%d_%H%M%S); BK=/root/finance/_backup_S196_HLT1_$TS; mkdir -p "$BK"
echo "[4/8] backup -> $BK"; cp -p "$LIVE" "$BK/"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/finance_app.py" "$LIVE"; systemctl restart $SVC; sleep 2; echo "   service: $(systemctl is-active $SVC)"; echo "   log kept at $LOG"; exit 1; }

echo "[5/8] swap + payload md5"
cp finance_app.py "$LIVE" || rollback
H2=$(md5sum "$LIVE"|cut -d' ' -f1)
[ "$H2" = "$NEWH" ] || { echo "*** RED: installed bytes are $H2, expected $NEWH"; rollback; }

echo "[6/8] py_compile"; python3 -c "import py_compile; py_compile.compile('$LIVE',doraise=True); print('      OK')" || rollback

echo "[7/8] smoke — ALL-GREEN and GROWN (projection: $CUR_T -> 665)"
(cd /root/finance && python3 finance_app.py --selftest) >"$LOG" 2>&1
NEW=$(grep -m1 "SMOKE " "$LOG"); echo "      ${NEW:-<no SMOKE line — the suite crashed>}"
echo "${NEW:-}"|grep -Eq "SMOKE ([0-9]+)/\1 " || { grep "FAIL:" "$LOG"|sed 's/^/        /'; show "$LOG"; rollback; }
NEW_T=$(echo "$NEW"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
[ "$NEW_T" -gt "$CUR_T" ] || { echo "*** RED: the new checks did not run ($CUR_T -> $NEW_T)."; rollback; }

echo "[8/8] restart + verify"; systemctl restart $SVC; sleep 2; systemctl is-active --quiet $SVC || rollback

rm -f "$LOG"
echo "==============================================================="
echo " GREEN.  finance_app.py $(md5sum $LIVE|cut -d' ' -f1)  smoke $NEW_T (was $CUR_T)"
echo ""
echo " The push surface is FAIL-CLOSED until you set its token. Two"
echo " commands on this box (the token never enters any chat):"
echo "   TOK=\$(openssl rand -hex 24) && echo \"copy this into the GAS"
echo "   Script Property RENEWALS_PUSH_TOKEN: \$TOK\" && systemctl edit"
echo "   $SVC   # add under [Service]:  Environment=FINANCE_RENEWALS_TOKEN=\$TOK"
echo "   then: systemctl daemon-reload && systemctl restart $SVC"
echo " GAS side: paste Renewal_Nag_v2.gs over Renewal_Nag.gs in the"
echo " personal Inbox Janitor project, set the Script Property, run"
echo " pushRenewalsToVPS() once — expect 'pushed: N item(s)'. Then open"
echo " /finance/health: the Renewals card goes live."
echo "==============================================================="
