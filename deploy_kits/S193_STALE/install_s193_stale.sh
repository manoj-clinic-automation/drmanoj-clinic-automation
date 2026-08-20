#!/bin/bash
# =====================================================================
#  S193_STALE · hide stale "NOT-FILED at push time" flags on the Hub.
#
#  One in-place patch to finance_app.py: the not-filed note now hides a
#  day that already has a successful Marg batch (self-healing), so 17-Aug
#  drops off while a genuinely empty day (19-Aug pre-export) stays.
#
#  Self-gating on the live finance_app hash, measured ZERO-delta smoke,
#  rolls back on any red.
# =====================================================================
set -u
cd "$(dirname "$0")"

LIVE_FIN=/root/finance/finance_app.py
SVC_F=clinic-finance.service
FIN_WANT=d86745b70347f47127b2fa0f933ea364      # S193_DISC, current live

echo "==============================================================="
echo " S193_STALE · self-healing not-filed flag"
echo "==============================================================="
echo "[1/7] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }

echo "[2/7] currency gate"
H=$(md5sum "$LIVE_FIN" | cut -d' ' -f1); echo "      finance_app : $H"
[ "$H" = "$FIN_WANT" ] || { echo '*** RED: finance_app is not the S193_DISC build. STOP.'; exit 1; }

echo "[3/7] baseline smoke"
CUR=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE ")
echo "      $CUR"
echo "$CUR" | grep -Eq "SMOKE ([0-9]+)/\1 " || { echo '*** RED: baseline not green. STOP.'; exit 1; }
CUR_N=$(echo "$CUR" | sed -n 's/.*SMOKE \([0-9]*\/[0-9]*\).*/\1/p')

TS=$(date +%Y%m%d_%H%M%S)
echo "[4/7] backup"
BK=/root/finance/_backup_S193_STALE_$TS; mkdir -p "$BK"; cp -p "$LIVE_FIN" "$BK/"
echo "      -> $BK"
rollback(){ echo "*** RED -- ROLLING BACK."; cp -p "$BK/finance_app.py" "$LIVE_FIN"; systemctl restart $SVC_F; exit 1; }

echo "[5/7] in-place patch"
python3 patch_stale_flag.py || rollback
python3 -c "import py_compile; py_compile.compile('$LIVE_FIN',doraise=True); print('      compile OK')" || rollback

echo "[6/7] new smoke — require green + zero delta"
NEW=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE ")
echo "      $NEW"
echo "$NEW" | grep -Eq "SMOKE ([0-9]+)/\1 " || rollback
NEW_N=$(echo "$NEW" | sed -n 's/.*SMOKE \([0-9]*\/[0-9]*\).*/\1/p')
[ "$NEW_N" = "$CUR_N" ] || { echo "*** RED: smoke changed ($CUR_N -> $NEW_N)."; rollback; }

echo "[7/7] restart + verify"
systemctl restart $SVC_F; sleep 2; systemctl is-active --quiet $SVC_F || rollback

echo "==============================================================="
echo " GREEN.  S193_STALE is live."
echo "   finance_app.py  $(md5sum $LIVE_FIN | cut -d' ' -f1)"
echo "   smoke unchanged : $NEW_N"
echo " Refresh the Hub — 17-Aug should drop off the not-filed note;"
echo " 19-Aug stays until its Marg export is pushed. Pin the new md5."
echo "==============================================================="
