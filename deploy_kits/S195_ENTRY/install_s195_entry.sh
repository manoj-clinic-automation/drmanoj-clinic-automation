#!/bin/bash
# =====================================================================
#  S195_ENTRY — /finance/entry redirects to the live page
#
#  Reception hitting the OLD /finance/entry URL directly (typed/bookmark)
#  saw the outdated single-page screen. This makes /finance/entry redirect
#  by role: maker -> /finance/daily (v2), checker -> /finance/review. The
#  old page stays reachable ONLY via /finance/entry?legacy=1. The app's
#  own selftest fetches that carry the old page's body were repointed to
#  ?legacy=1 so SMOKE stays ALL-GREEN. ONE file: finance_app.py.
#
#  Currency-gated to the live S194E build. Backs up, py_compiles, runs the
#  built-in --selftest (must be ALL-GREEN and not shrink), restarts, and
#  ROLLS BACK automatically on any red.
# =====================================================================
set -u
cd "$(dirname "$0")"
LIVE_FIN=/root/finance/finance_app.py
SVC=clinic-finance.service
FIN_WANT=d2863c30ed0d3cc23126c7da13d9fe9b     # live = S194E

echo "==============================================================="
echo " S195_ENTRY · /finance/entry -> live page redirect"
echo "==============================================================="

echo "[1/8] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }

echo "[2/8] currency gate"
[ -f "$LIVE_FIN" ] || { echo "*** RED: $LIVE_FIN missing."; exit 1; }
H=$(md5sum "$LIVE_FIN"|cut -d' ' -f1); echo "      finance_app : $H"
[ "$H" = "$FIN_WANT" ] || { echo "*** RED: finance_app is not the S194E build (expected $FIN_WANT). STOP."; echo "   (tell Cowork this hash and it reissues.)"; exit 1; }

echo "[3/8] baseline smoke (--selftest)"
CUR=$(cd /root/finance && python3 finance_app.py --selftest 2>&1|grep -m1 "SMOKE "); echo "      $CUR"
echo "$CUR"|grep -Eq "SMOKE ([0-9]+)/\1 " || { echo '*** RED: baseline not all-green. STOP.'; exit 1; }
CUR_T=$(echo "$CUR"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')

TS=$(date +%Y%m%d_%H%M%S); BK=/root/finance/_backup_S195_ENTRY_$TS; mkdir -p "$BK"
echo "[4/8] backup -> $BK"; cp -p "$LIVE_FIN" "$BK/"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/finance_app.py" "$LIVE_FIN"; systemctl restart $SVC; sleep 2; echo "   service: $(systemctl is-active $SVC)"; exit 1; }

echo "[5/8] swap finance_app.py"; cp finance_app.py "$LIVE_FIN" || rollback
echo "[6/8] py_compile"; python3 -c "import py_compile; py_compile.compile('$LIVE_FIN',doraise=True); print('      OK')" || rollback

echo "[7/8] new smoke — ALL-GREEN, not shrunk"
NEW=$(cd /root/finance && python3 finance_app.py --selftest 2>&1|grep -m1 "SMOKE "); echo "      $NEW"
echo "$NEW"|grep -Eq "SMOKE ([0-9]+)/\1 " || rollback
NEW_T=$(echo "$NEW"|sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
[ "$NEW_T" -ge "$CUR_T" ] || { echo "*** RED: smoke shrank ($CUR_T -> $NEW_T)."; rollback; }

echo "[8/8] restart + verify"; systemctl restart $SVC; sleep 2; systemctl is-active --quiet $SVC || rollback

echo "==============================================================="
echo " GREEN.  /finance/entry now redirects (maker->/finance/daily,"
echo " checker->/finance/review).  Old page: /finance/entry?legacy=1 ."
echo " finance_app.py $(md5sum $LIVE_FIN|cut -d' ' -f1)  smoke $NEW_T (was $CUR_T)"
echo " Backup: $BK .  Pin the new md5."
echo "==============================================================="
