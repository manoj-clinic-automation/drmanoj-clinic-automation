#!/bin/bash
# =============================================================================
#  install_console.sh · kit S208_CONSOLE — the page becomes the owner's console
#
#  OWNER SPEC (30-Aug, ~03:10): "make this page my console for the updated
#  view — every section expandable to the granular level. Status must be the
#  UPDATED one, not stale; the flags confused me."
#
#  WHAT CHANGES
#    darpan_app.py           v4 (this project's own file): three endpoints —
#      /api/coverage   one verdict per day, COMPUTED NOW (filed? report in?
#                      applied?). A data_flag is a RECORD (F-113) and is shown
#                      WITH today's truth: on an OK day it says STALE with its
#                      dismiss right there. Ends the records-read-as-status
#                      confusion, including the 2026-06-12 case.
#      /api/cn-detail  a credit note is a SALES RETURN (owner-ruled): each is
#                      verified against the SAME PATIENT'S earlier sale bill
#                      carrying that item -- shown with bill number and date.
#                      A CN with no traceable sale is NOT ENTERTAINED without
#                      the owner (his ruling: everything since 1-Apr-2026 is on
#                      this server) -- it opens a pending approval on the card:
#                      approve with a note, or reject with a mandatory reason,
#                      named and dated. /api/cn-approve, owner-only.
#      /api/idlookup   short clinic IDs answered from patient_ref — 842 is a
#                      real patient, and the page now says so. The full
#                      patient master ON this server is the Sprint-5 feed.
#    finance_approvals.html  margCard: the two confusing lines replaced by the
#      live coverage table (clean days summarised, only problems listed), plus
#      the CN drill-down and the ID checker. Nothing else touched.
# =============================================================================
set -u
FIN=/root/finance
DAR="$FIN/darpan_app.py"
AP="$FIN/finance_ui/finance_approvals.html"
PY=/usr/bin/python3
SVC=clinic-finance.service
DAR_LIVE_MD5=8b1e06531bb61da0cb4bd3fc23ff32cf
AP_LIVE_MD5=b93eed72ea08c78ed58ce2b6c082e6ae
HERE="$(cd "$(dirname "$0")" && pwd)"
echo "== S208_CONSOLE =="
cd "$HERE" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! kit SUMS mismatch — refusing"; exit 1; }
DA="$(md5sum "$DAR" | awk '{print $1}')"; AA="$(md5sum "$AP" | awk '{print $1}')"
KD="$(md5sum "$HERE/darpan_app.py" | awk '{print $1}')"
KA="$(md5sum "$HERE/finance_approvals.html" | awk '{print $1}')"
[ "$DA" = "$KD" ] && [ "$AA" = "$KA" ] && { echo "already installed"; exit 0; }
if [ "$DA" != "$DAR_LIVE_MD5" ] || [ "$AA" != "$AP_LIVE_MD5" ]; then
  echo "!! LIVE-FILE CURRENCY — refusing. darpan=$DA approvals=$AA"
  echo "   expected $DAR_LIVE_MD5 / $AP_LIVE_MD5 (the S208_LEDGER3 and"
  echo "   S208_UIFIX files as installed). Something moved — tell Claude."
  exit 1
fi
echo "[1/4] currency ok"
BASE_OUT="$(cd "$FIN" && "$PY" finance_app.py --selftest 2>&1)"
BASE_N="$(echo "$BASE_OUT" | grep -oE 'SMOKE [0-9]+' | head -1 | awk '{print $2}')"
[ -n "${BASE_N:-}" ] || { echo "!! no baseline"; exit 1; }
STAMP="$(date +%Y%m%d_%H%M%S)"
cp -f "$DAR" "$DAR.bak_S208_CONSOLE_$STAMP" && cp -f "$AP" "$AP.bak_S208_CONSOLE_$STAMP" || {
  echo "!! backup failed"; exit 1; }
restore(){ cp -f "$DAR.bak_S208_CONSOLE_$STAMP" "$DAR"
  cp -f "$AP.bak_S208_CONSOLE_$STAMP" "$AP"
  systemctl restart "$SVC" >/dev/null 2>&1; echo "   RESTORED both."; }
cp -f "$HERE/darpan_app.py" "$DAR" && cp -f "$HERE/finance_approvals.html" "$AP" && \
cp -f "$HERE/selftest_darpan.py" "$FIN/selftest_darpan.py" || { echo "!! copy failed"; restore; exit 1; }
echo "[2/4] copied"
"$PY" -m py_compile "$DAR" || { echo "!! compile — restoring"; restore; exit 1; }
OUT="$(cd "$FIN" && "$PY" selftest_darpan.py 2>&1)"
echo "$OUT" | grep -qE "^74 passed, 0 failed" || {
  echo "!! selftest not 74/74 — restoring"; echo "$OUT" | grep -E "FAIL|passed" | tail -6
  restore; exit 1; }
OUT="$(cd "$FIN" && "$PY" finance_app.py --selftest 2>&1)"
N="$(echo "$OUT" | grep -oE 'SMOKE [0-9]+' | head -1 | awk '{print $2}')"
if [ -z "${N:-}" ] || [ "$N" -lt "$BASE_N" ] || echo "$OUT" | grep -q "  FAIL:"; then
  echo "!! smoke $BASE_N -> ${N:-?} — restoring"; restore; exit 1; fi
echo "[3/4] selftest 74/74 ✓ · smoke $N (was $BASE_N) ✓"
systemctl restart "$SVC" && sleep 3 && systemctl is-active --quiet "$SVC" || {
  echo "!! restart — restoring"; restore; exit 1; }
echo "[4/4] restarted"
echo "GREEN. Refresh /finance/approvals — the Marg card now computes its"
echo "verdicts live; stale flags carry their own remove; credit notes and"
echo "clinic-IDs open to the last detail."
echo "Reverse: cp -f $DAR.bak_S208_CONSOLE_$STAMP $DAR && cp -f $AP.bak_S208_CONSOLE_$STAMP $AP && systemctl restart $SVC"
