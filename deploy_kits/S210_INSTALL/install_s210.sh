#!/bin/bash
# install_s210.sh -- S210: the whole evening install in ONE command.
# Idempotent: every patch says "already patched" on a re-run; the page copy
# and baseline are safe to repeat. Stops at the FIRST failure and says where.
set -u
PY=/root/wa/venv/bin/python3
REPO=/root/deploy/repo
FIN=/root/finance
step(){ echo; echo "== $1"; }
fail(){ echo; echo "!! STOPPED at: $1 -- nothing after this ran. Paste this output to Claude."; exit 1; }

step "1/6 ruled words on read (finance_app)"
$PY $REPO/deploy_kits/S210_RULEDWORDS/patch_finance_app_ruledwords.py $FIN/finance_app.py || fail "ruledwords patch"

step "2/6 Darpan handover route (darpan_app)"
$PY $REPO/deploy_kits/S210_HANDOVER/patch_darpan_app_handover.py $FIN/darpan_app.py || fail "handover patch"

step "3/6 backup of darpan_card.html"
\cp $FIN/darpan_card.html $FIN/darpan_card.html.bak_S210_HO_$(date +%Y%m%d_%H%M%S) || fail "backup"

step "4/6 new darpan_card.html"
\cp $REPO/deploy_kits/S210_HANDOVER/darpan_card.html $FIN/darpan_card.html || fail "page copy"

step "5/6 restart"
systemctl restart clinic-finance.service && sleep 3 && systemctl is-active clinic-finance.service || fail "restart"

step "6/6 sweep baseline"
$PY $REPO/deploy_kits/S210_SWEEP/sweep_daily.py $FIN --baseline /root/deploy/sweep_baseline.txt --write || fail "sweep baseline"

echo
echo "=========================================="
echo " S210 INSTALL COMPLETE -- all six steps OK"
echo "=========================================="
