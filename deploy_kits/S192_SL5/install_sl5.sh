#!/bin/bash
# =====================================================================
#  S192_SL5 · D332 — the WAIVER instrument, policy-date SETTINGS, and
#             the F-151 attendance-wording fix
#
#  THREE things land, all in staff_ledger.py, no schema/migration:
#
#  (A) WAIVE (D332 §2.8) — a checker on the ACTIVE waiver-authority list
#      forgives a derived deduction. Scopes LINE / STAFF_MONTH /
#      ALL_MONTH; a written reason is compulsory; the amount is DERIVED
#      at compute time, never frozen; append-only, contra-reversed; its
#      own +waived column on the salary table and breakdown. Authority
#      is seeded Dr Manoj ACTIVE, Dr Bhawna scoped-in but INACTIVE.
#      Owner ruling (S192): a waiver may forgive ANY deduction line —
#      an attendance deduction OR a ledger debit (advance / loan / fine).
#
#  (B) SETTINGS (D332 §2.7 / F-150) — a new ledger_settings.json the
#      ledger reads. attendance_enforce_from is the NOTICE-SERVED month.
#      Until it is set, EVERY month is PREVIEW-ONLY: attendance-policy
#      deductions (marks, early, early-big, uninformed, excess) are
#      shown struck-through but DO NOT reduce NET. July AND August are
#      therefore preview until the owner sets the date in /ledger/settings.
#      Ledger money (advances, loan instalments) always applies — it is
#      owed, not a policy penalty.
#
#  (C) F-151 — every rendered "fine" for an ATTENDANCE deduction becomes
#      "attendance deduction" (the salary column header, the two
#      statement rows, the help text). The uniform / i-card / ad-hoc
#      ledger charges keep their names; the att-report CSV headers are
#      untouched.
#
#  The approval token now covers the waivers and the settings, so a
#  stale preview refuses to approve after either changes.
#
#  D317 chain. Projection: current 218 -> new 240 (+22: settings default
#  + preview gate + preview-not-applied NET + wording + enforced NET +
#  authority/reason/scope validation + LINE/STAFF_MONTH/ALL_MONTH/ledger
#  waivers + reversal + token coverage + route smoke), written before
#  measuring.
# =====================================================================
set -u
cd "$(dirname "$0")"
WANT_LIVE=470bb1133046d9076de5a2edd413f66c    # S190_SL4, Register-pinned live
LIVE=/root/staff_ledger.py
PY=/root/wa/venv/bin/python3
SVC=staff-ledger.service
echo "==============================================================="
echo " S192_SL5 · D332 waiver + preview settings + F-151 wording"
echo "==============================================================="
echo "[1/6] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "      KIT_ID : $(cat KIT_ID.txt)"
echo "[2/6] currency gate"
H=$(md5sum $LIVE | cut -d' ' -f1); echo "      live : $H"
[ "$H" = "$WANT_LIVE" ] || { echo '*** RED: live is not the SL4 build. STOP.'; exit 1; }
echo "[3/6] PROJECTION: current 218 -> new 240 (+22)."
CUR=$($PY $LIVE --selftest 2>&1 | tail -1); echo "      $CUR"
echo "$CUR" | grep -q "PASSED — 218 " || { echo '*** RED. STOP.'; exit 1; }
NEW=$($PY ./staff_ledger_SL5.py --selftest 2>&1 | tail -1); echo "      $NEW"
echo "$NEW" | grep -q "PASSED — 240 " || { echo '*** RED. STOP.'; exit 1; }
TS=$(date +%Y%m%d_%H%M%S); BAK=/root/staff_ledger.py.bak_S192_SL5_$TS
echo "[4/6] backup: $BAK"; cp -p $LIVE $BAK || exit 1
echo "[5/6] swap"; cp staff_ledger_SL5.py $LIVE
POST=$($PY $LIVE --selftest 2>&1 | tail -1); echo "      $POST"
echo "$POST" | grep -q "PASSED — 240 " || {
  echo "*** RED — ROLLING BACK."; cp -p $BAK $LIVE; systemctl restart $SVC; exit 1; }
echo "[6/6] restart"; systemctl restart $SVC; sleep 2
systemctl is-active --quiet $SVC && echo "      $SVC : active" || {
  echo "*** RED — ROLLING BACK."; cp -p $BAK $LIVE; systemctl restart $SVC; exit 1; }
echo "==============================================================="
echo " GREEN.  S192_SL5 is live."
echo "   staff_ledger.py  $(md5sum $LIVE | cut -d' ' -f1)"
echo "   selftest 218 -> 240  (+22 checks, 0 failures)"
echo " NOW LOOK (the F-132 rule):"
echo "   /ledger/salary  — a preview month shows attendance deductions"
echo "                     struck-through, a +waived column, and a"
echo "                     '7 · Waivers (D332)' card."
echo "   /ledger/settings — set the notice-served month there to switch"
echo "                     attendance enforcement ON (leave blank = preview)."
echo " Attendance stays PREVIEW-ONLY until you set that date — so July"
echo " and August do not deduct attendance penalties yet (D332 §2.7)."
echo "==============================================================="
