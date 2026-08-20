#!/bin/bash
# =====================================================================
#  S193_F155 · a Marg push can no longer show green "applied" while its
#  day holds no bills.  A run that ingests NOTHING (day not filed yet)
#  now STAYS pending and KEEPS its payload, so it re-applies once the day
#  is filed -- instead of the report's data being lost (the 17-Aug loss).
#  The pushed-reports card reads the truth (ingested_count): "loaded",
#  "waiting - day not filed", or "loaded nothing - re-load from Marg".
#
#  finance_app.py: full-file replacement (gated on the current live hash).
#  finance_approvals.html: one fail-loud in-place badge patch.
#  Projection: finance smoke 555 -> 557 (+2, F-155). Verified offline,
#  differential, 0 regressions; hub JS node-checked.
# =====================================================================
set -u
cd "$(dirname "$0")"
CUR_APP=9b1afe4f13bec91bc9bb83e8f818a76b     # S193_F6, current live
LIVE_APP=/root/finance/finance_app.py
HUB=/root/finance/finance_ui/finance_approvals.html
SVC=clinic-finance.service
echo "==============================================================="
echo " S193_F155 · truthful Marg 'applied' status"
echo "==============================================================="
echo "[1/7] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "      KIT_ID : $(cat KIT_ID.txt)"
echo "[2/7] currency gate (finance_app == S193_F6)"
HA=$(md5sum $LIVE_APP | cut -d' ' -f1); echo "      live app : $HA"
[ "$HA" = "$CUR_APP" ] || { echo '*** RED: finance_app is not the S193_F6 build. STOP.'; exit 1; }
[ -f "$HUB" ] || { echo '*** RED: hub page missing. STOP.'; exit 1; }
echo "[3/7] baseline smoke (expect 555/555)"
CF=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE ")
echo "      $CF"; echo "$CF" | grep -q "SMOKE 555/555" || { echo '*** RED: baseline not 555. STOP.'; exit 1; }
TS=$(date +%Y%m%d_%H%M%S); BK=/root/finance/_backup_S193_F155_$TS; mkdir -p "$BK"
echo "[4/7] backup -> $BK"; cp -p "$LIVE_APP" "$BK/"; cp -p "$HUB" "$BK/"
rollback(){ echo "*** RED — ROLLING BACK."; cp -p "$BK/finance_app.py" "$LIVE_APP"; cp -p "$BK/finance_approvals.html" "$HUB"; systemctl restart $SVC >/dev/null 2>&1; exit 1; }
echo "[5/7] swap finance_app + patch the hub badge (fail-loud)"
cp finance_app_F155.py "$LIVE_APP"
python3 ./patch_f155.py "$HUB" || rollback
echo "[6/7] verify smoke 555 -> 557 (serving the patched page)"
NF=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE ")
echo "      $NF"; echo "$NF" | grep -q "SMOKE 557/557" || rollback
echo "[7/7] restart"; systemctl restart $SVC >/dev/null 2>&1; sleep 1
systemctl is-active --quiet $SVC || rollback
echo "==============================================================="
echo " GREEN.  S193_F155 is live."
echo "   finance_app.py         $(md5sum "$LIVE_APP"|cut -d' ' -f1)   (555 -> 557)"
echo "   finance_approvals.html $(md5sum "$HUB"|cut -d' ' -f1)"
echo " The pushed-reports card now tells the truth. Refresh the Hub."
echo " NOTE: 17-Aug's report was pruned before this fix, so it still needs a"
echo " manual re-export from Marg; from now on skipped days keep their data."
echo "==============================================================="
