#!/bin/bash
# =====================================================================
#  S193_UX · readability + Darpan-page fixes, patched IN PLACE on the
#  two served pages (their live bytes live only on the box, not the repo).
#
#  Darpan (finance_entry.html): money boxes no longer start on a stuck "0";
#    tapping a box selects it so typing replaces; after a scan you return to
#    where you were instead of the top.
#  Your Hub (finance_approvals.html): every card collapses (tap its title,
#    noisy ones start closed); cash-custody reads "Held now · total" with
#    conduits shown as "passed on"; the review link is renamed
#    "Review & month close".
#
#  Fail-loud: each edit must match its anchor exactly once or the whole run
#  refuses and restores. Smoke-gated (555/555) with rollback. Verified
#  offline against the live page source: node syntax OK, 0 smoke regressions.
# =====================================================================
set -u
cd "$(dirname "$0")"
ENTRY=/root/finance/finance_ui/finance_entry.html
HUB=/root/finance/finance_ui/finance_approvals.html
SVC=clinic-finance.service
echo "==============================================================="
echo " S193_UX · entry-page fixes + Hub readability"
echo "==============================================================="
echo "[1/6] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "      KIT_ID : $(cat KIT_ID.txt)"
echo "[2/6] both served pages present?"
[ -f "$ENTRY" ] && [ -f "$HUB" ] || { echo '*** RED: a served page is missing. STOP.'; exit 1; }
TS=$(date +%Y%m%d_%H%M%S); BK=/root/finance/_backup_S193_UX_$TS; mkdir -p "$BK"
echo "[3/6] backup -> $BK"; cp -p "$ENTRY" "$BK/"; cp -p "$HUB" "$BK/"
echo "[4/6] baseline smoke (expect 555/555)"
CUR=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE ")
echo "      $CUR"; echo "$CUR" | grep -q "SMOKE 555/555" || { echo '*** RED: baseline not 555/555. STOP (nothing changed).'; exit 1; }
echo "[5/6] patch in place (fail-loud per anchor)"
python3 ./patch_pages.py "$ENTRY" "$HUB" || {
  echo "*** RED: an anchor did not match. Restoring, nothing changed.";
  cp -p "$BK/finance_entry.html" "$ENTRY"; cp -p "$BK/finance_approvals.html" "$HUB"; exit 1; }
echo "[6/6] verify smoke still 555/555 (now serving the patched pages)"
NEW=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE ")
echo "      $NEW"; echo "$NEW" | grep -q "SMOKE 555/555" || {
  echo "*** RED — ROLLING BACK BOTH PAGES.";
  cp -p "$BK/finance_entry.html" "$ENTRY"; cp -p "$BK/finance_approvals.html" "$HUB"; exit 1; }
systemctl restart $SVC >/dev/null 2>&1; sleep 1
echo "==============================================================="
echo " GREEN.  S193_UX is live."
echo "   finance_entry.html       $(md5sum "$ENTRY"|cut -d' ' -f1)"
echo "   finance_approvals.html   $(md5sum "$HUB"|cut -d' ' -f1)"
echo " Refresh both pages in the browser (Ctrl-Shift-R) to see the changes."
echo " Darpan: empty money boxes, tap-to-select, scan keeps your place."
echo " You: tap any card title to open/close it; custody now says who HOLDS"
echo "   cash now vs who passed it on; the review tab is renamed."
echo "==============================================================="
