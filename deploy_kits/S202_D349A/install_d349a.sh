#!/bin/bash
# =============================================================================
#  install_d349a.sh · kit S202_D349A — D349 on the finance side.
#
#  ONE rule for what a day's difference MEANS, and the exceptions card rebuilt
#  as the reconciliation table the owner asked for:
#    "a clear intuitive table format, with reconcilation there only as inbuilt
#     flow, no page hopping"
#
#  WHY
#    S201 renamed this on /finance/health -- "variance" and "low confidence"
#    retired for the owner's own words (D348). The exceptions card kept saying
#    "variance", because nobody realised the two surfaces showed the SAME rows.
#    One rename, two screens, one missed.
#
#    Worse than the word: the card mixed FIVE days whose only difference is
#    bills not yet matched to a patient -- where, under D313, nothing is wrong --
#    with FOUR genuinely unexplained ones, including a NEGATIVE row open since
#    S186. The harmless rows were hiding the real ones.
#
#  WHAT CHANGES
#    finance_app.py            difference_meaning() -- ONE definition, classified
#                              from DATA, never from the description text (a text
#                              parse would just be a third copy of the rule).
#                              /finance/api/approvals now carries each row's id,
#                              meaning and reason, split into needs-you vs
#                              awaiting-names, and the UPI rows carry DIRECTION
#                              plus a net -- because the direction decides who is
#                              out of pocket, and the page never said so.
#    finance_approvals.html    the card becomes two tables. Each row closes
#                              WHERE IT IS SHOWN via the existing
#                              /finance/api/exception/<id>/resolve (no new write
#                              path, and it still demands a reason). The harmless
#                              population is folded into a <details>, present but
#                              not shouting.
#
#  NO MONEY PATH IS ADDED. Closing an exception records a judgement with a
#  reason; it books nothing. Any cash correction stays a separate deliberate
#  entry.
#
#  v2 (S202): the FIRST install was REFUSED by this installer's own gate at
#      698/701, and the gate was right. Three D330 ceiling checks build their
#      fixture from the LIVE store and assumed the month's advances leave room
#      under Darpan's Rs 15,000 ceiling. Kit S202_DARPAN20K had just recorded the
#      Rs 20,000 that genuinely left his drawer -- money proven by a physical
#      count -- so August went OVER the ceiling, _room_p turned NEGATIVE, and the
#      test posted a negative rupee amount. The endpoint rightly answered
#      not_a_number. THE BOOKS WERE CORRECT AND THE TEST WAS WRONG: F-106's exact
#      shape, recurring. Reproduced offline (645 -> 642 on the UNPATCHED app,
#      purely by applying the migration) before anything was changed, then the
#      three checks were made state-adaptive -- 3 checks in BOTH branches, so the
#      total stays deterministic. Nothing about D349 itself changed in v2.
#
#  PROVEN OFFLINE, on a harness rebuilt from LIVE BYTES ONLY (every module
#  recovered by md5, D188 -- the S189 method, because F-87 forbids shipping into
#  a suite that cannot be run):
#      SMOKE 693 -> 701, +8 exactly (projection written before measuring)
#      FAIL SET BYTE-IDENTICAL (48 -> 48, same rows -- the known harness gap;
#      finance_entry.html's live bytes exist only on the box, F-169)
# =============================================================================
set -u
KIT_NAME="S202_D349A"
APP=/root/finance/finance_app.py
HTML=/root/finance/finance_ui/finance_approvals.html
APP_MD5_EXPECTED=3f72e9ad16d915fe5ced45c4e28a2248
HTML_MD5_EXPECTED=402fa7b263b86f75bfccc122f1a0ca37
APP_MD5_NEW=eca3723ee5cc391abfbfb0747f375618
HTML_MD5_NEW=89e02711061f473c5e2e118fe50aa1aa
PY=/usr/bin/python3
SVC=clinic-finance.service

echo "=============================================================="
echo "  $KIT_NAME — D349: one difference-rule, and the table"
echo "=============================================================="
for c in md5sum awk cp date systemctl; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — refusing"; exit 1; }
done
[ -x "$PY" ] || { echo "!! preflight: $PY not executable — refusing"; exit 1; }
echo "[1/8] preflight ok"

md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [2/8] kit SUMS mismatch — refusing"; exit 1; }
echo "[2/8] kit integrity ok"

A="$(md5sum "$APP"  | awk '{print $1}')"
H="$(md5sum "$HTML" | awk '{print $1}')"
if [ "$A" != "$APP_MD5_EXPECTED" ] || [ "$H" != "$HTML_MD5_EXPECTED" ]; then
  echo "!! [3/8] LIVE CODE CURRENCY GATE — refusing. Both files are full replacements."
  [ "$A" != "$APP_MD5_EXPECTED" ]  && echo "   finance_app.py       is $A, expected $APP_MD5_EXPECTED"
  [ "$H" != "$HTML_MD5_EXPECTED" ] && echo "   finance_approvals.html is $H, expected $HTML_MD5_EXPECTED"
  exit 1
fi
echo "[3/8] live-code currency gate ok (both files)"

BAKA="${APP}.bak_${KIT_NAME}_$(date +%Y%m%d_%H%M%S)"
BAKH="${HTML}.bak_${KIT_NAME}_$(date +%Y%m%d_%H%M%S)"
cp -f "$APP" "$BAKA" && cp -f "$HTML" "$BAKH" || { echo "!! [4/8] backup failed — refusing"; exit 1; }
echo "[4/8] backups: $BAKA"
echo "                $BAKH"

restore(){ cp -f "$BAKA" "$APP"; cp -f "$BAKH" "$HTML"; systemctl restart "$SVC" >/dev/null 2>&1; echo "   restored both files and restarted $SVC"; }

cp -f finance_app.py "$APP" && cp -f finance_ui/finance_approvals.html "$HTML" || { echo "!! [5/8] copy failed"; restore; exit 1; }
GA="$(md5sum "$APP" | awk '{print $1}')"; GH="$(md5sum "$HTML" | awk '{print $1}')"
if [ "$GA" != "$APP_MD5_NEW" ] || [ "$GH" != "$HTML_MD5_NEW" ]; then
  echo "!! [5/8] installed bytes do not match the kit — restoring"; restore; exit 1; fi
echo "[5/8] installed"

systemctl restart "$SVC" || { echo "!! [6/8] restart failed — restoring"; restore; exit 1; }
sleep 2
systemctl is-active --quiet "$SVC" || { echo "!! [6/8] $SVC not active — restoring"; restore; exit 1; }
echo "[6/8] $SVC restarted and active"

echo "[7/8] running the live smoke suite (throwaway copy; finance.db untouched)"
OUT="$(cd /root/finance && "$PY" finance_app.py --selftest 2>&1)"
SUM="$(echo "$OUT" | head -1)"
echo "      $SUM"
if ! echo "$SUM" | grep -qE "(^|[^0-9])701/701([^0-9]|$)"; then
  echo "!! the suite did not report 701/701 — restoring"
  echo "$OUT" | grep "FAIL" | head -12
  restore; exit 1
fi
echo "[7/8] smoke 701/701 ✓  (was 693/693)"
echo "[8/8] done"

echo
echo "=============================================================="
echo "  GREEN.  https://followup.dr-manoj.in/finance/approvals#exCard"
echo
echo "  The card should now show:"
echo "    ⚠ Needs you — 4 day(s)      12-Jun -8,487 · 3-May 34,245 · 2-Jun 690 · 9-May 665"
echo "    Bank vs entered — 8 day(s)  net 241.00 (4 short, 4 over)"
echo "    ⓘ 5 day(s) waiting for patient names — 49,443.00   (folded, nothing wrong)"
echo
echo "  Each row closes where it is shown. A reason is required."
echo
echo "  Reverse:  cp -f $BAKA $APP && cp -f $BAKH $HTML && systemctl restart $SVC"
echo "=============================================================="
