#!/bin/bash
# =============================================================================
#  install_uifix.sh · kit S208_UIFIX — two live pages, finally readable, fixed
#
#  HOW THESE FILES WERE OBTAINED (F-169 closed the honest way): the live HTML
#  existed only on this box. The owner signed the assistant's browser into the
#  portal (30-Aug-2026); the pages were fetched IN THE BROWSER from this very
#  server, patched in the page with every edit asserted to match exactly once,
#  and downloaded straight onto manojz -- verified by sha256 in both places.
#  finance_approvals.LIVE.html md5 89e02711... equals what the S202_D349A
#  installer recorded as deployed: independent proof of provenance.
#
#  WHAT CHANGES
#    finance_review.html     the nine KPI tiles become doors (owner: "top
#                            tiles are not clickable") -- Last filed opens the
#                            day, cash tiles go to Parked, month tiles to the
#                            grid, approvals/flags to their lists. Cursor +
#                            hover so they LOOK clickable too.
#    finance_approvals.html  nav gains Corrections / Pipeline / Staff links,
#                            and each NOT-FILED flag (the 2026-06-12 case)
#                            gets an owner remove (reason required; the
#                            server-side dismiss is owner-gated and audited).
#  No python changes. No restart needed -- both pages are served from disk
#  per request.
# =============================================================================
set -u
FIN=/root/finance
UI="$FIN/finance_ui"
RV="$UI/finance_review.html"
AP="$UI/finance_approvals.html"
RV_LIVE_MD5=ddd3d5f61fb2f41950b1a63aa3480650
AP_LIVE_MD5=89e02711061f473c5e2e118fe50aa1aa
RV_NEW_MD5=d67b0169fbbd2a1a3c30cadbfb0fde48
AP_NEW_MD5=b93eed72ea08c78ed58ce2b6c082e6ae
HERE="$(cd "$(dirname "$0")" && pwd)"
echo "== S208_UIFIX =="
cd "$HERE" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! kit SUMS mismatch — refusing"; exit 1; }
A="$(md5sum "$RV" | awk '{print $1}')"; B="$(md5sum "$AP" | awk '{print $1}')"
if [ "$A" = "$RV_NEW_MD5" ] && [ "$B" = "$AP_NEW_MD5" ]; then
  echo "already installed — nothing to do"; exit 0; fi
if [ "$A" != "$RV_LIVE_MD5" ] || [ "$B" != "$AP_LIVE_MD5" ]; then
  echo "!! LIVE-FILE CURRENCY — refusing. review=$A approvals=$B"
  echo "   expected $RV_LIVE_MD5 / $AP_LIVE_MD5 (captured from this very"
  echo "   server, signed in, 30-Aug). A page changed since. Tell Claude."
  exit 1
fi
STAMP="$(date +%Y%m%d_%H%M%S)"
cp -f "$RV" "$RV.bak_S208_UIFIX_$STAMP" && cp -f "$AP" "$AP.bak_S208_UIFIX_$STAMP" || {
  echo "!! backup failed"; exit 1; }
cp -f "$HERE/finance_review.html" "$RV" && cp -f "$HERE/finance_approvals.html" "$AP"
[ "$(md5sum "$RV" | awk '{print $1}')" = "$RV_NEW_MD5" ] && \
[ "$(md5sum "$AP" | awk '{print $1}')" = "$AP_NEW_MD5" ] || {
  cp -f "$RV.bak_S208_UIFIX_$STAMP" "$RV"; cp -f "$AP.bak_S208_UIFIX_$STAMP" "$AP"
  echo "!! did not land intact — restored"; exit 1; }
echo "GREEN. Refresh /finance/review — the tiles are doors now."
echo "Reverse: cp -f $RV.bak_S208_UIFIX_$STAMP $RV && cp -f $AP.bak_S208_UIFIX_$STAMP $AP"
