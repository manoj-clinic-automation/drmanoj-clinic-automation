#!/bin/bash
# =============================================================================
#  install_s225_loans.sh · kit S225_LOANS_VIEW rev 2 — D371: the Loans view, and the
#  REV 2 (14:55 IST): the 'current position' box on the New-entry page was a light box with
#  light text (unreadable, pre-existing since S200) -- now the theme's dark card with a blue
#  edge, and it links to the Loans view. Currency gate moved to rev 1's pin e5910152.
#  schedule field on the entry form.
#
#  THE OWNER, 04-Sep-2026: "staff advance ledger has all entries and it's confusing,
#  so the data should clearly display actual loans — tranches with details and
#  instalments due — and the ledger should be clear of the extra entries, as we
#  don't cancel any; then only we can plan which view to share with staff on PWA."
#
#  WHAT CHANGES
#    + /ledger/loans (checker: everyone or one person, any month; a linked maker:
#      own only, as "My loans"). One table per person: taken · amount · kind ·
#      how it recovers (advance_lane, the D349 rule) · recovered · balance · next
#      collection · status. System rows, contras and reversed pairs are summed,
#      never listed. Nothing in the ledger file is touched.
#    + the New-entry form gains an "agreed schedule" box for an advance
#      (2026-09:5000 one step per line, must add up) — make_entry always accepted
#      it; the form never sent it (the gap found at S225).
#    + nav link "Loans" / "My loans". APP_VERSION 3.5-S225-LOANS.
#  BEHAVIOUR CHANGE TO THE CLOSE: NONE. Not one line of close_month moved.
#
#  PROVEN BEFORE DELIVERY: the module's own selftest 301/301 unchanged; the kit's
#  selftest_loans_view_s225.py 35/35 on a synthetic ledger through the real app.
# =============================================================================
set -u
KIT_NAME="S225_LOANS_VIEW_r2"
LIVE=/root/staff_ledger.py
LIVE_MD5_EXPECTED=e5910152602e1b5a635819bad08355b7
NEW_MD5_EXPECTED=e2a10ee63c34eb441ac5dadf83ec079c
PY=/root/wa/venv/bin/python3
SVC=staff-ledger.service
PROBE=/tmp/s225loans_probe

echo "=============================================================="
echo "  $KIT_NAME — D371: the Loans view"
echo "=============================================================="
for c in md5sum awk cp date systemctl curl; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — refusing"; exit 1; }
done
[ -x "$PY" ]   || { echo "!! preflight: $PY not executable — refusing"; exit 1; }
[ -f "$LIVE" ] || { echo "!! preflight: $LIVE not found — refusing"; exit 1; }
echo "[1/9] preflight ok"
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [2/9] kit SUMS mismatch — refusing"; exit 1; }
echo "[2/9] kit integrity ok"
ACTUAL="$(md5sum "$LIVE" | awk '{print $1}')"
if [ "$ACTUAL" != "$LIVE_MD5_EXPECTED" ]; then
  echo "!! [3/9] LIVE CODE CURRENCY GATE — refusing. $LIVE is $ACTUAL; this kit was built against $LIVE_MD5_EXPECTED."
  exit 1
fi
echo "[3/9] live-code currency gate ok"
rm -rf "$PROBE"; mkdir -p "$PROBE/data" || { echo "!! [4/9] cannot make probe dir"; exit 1; }
cp -f staff_ledger.py selftest_loans_view_s225.py "$PROBE/"
echo "[4/9] probing the NEW file in isolation (LEDGER_DIR=$PROBE/data — the live store is never opened)"
OUT="$(cd "$PROBE" && LEDGER_DIR="$PROBE/data" "$PY" -B staff_ledger.py --selftest 2>&1)"
if ! { echo "$OUT" | grep -q "SELFTEST PASSED" && echo "$OUT" | grep -qE "(^|[^0-9])301([^0-9]|$)"; }; then
  echo "!! [5/9] the new file did NOT report 301 — refusing, nothing installed"; echo "$OUT" | tail -8; exit 1
fi
OUT2="$(cd "$PROBE" && "$PY" -B selftest_loans_view_s225.py 2>&1)"
if ! echo "$OUT2" | grep -q "35 PASS  0 FAIL"; then
  echo "!! [5/9] the loans selftest did NOT report 35/35 on the box — refusing, nothing installed"; echo "$OUT2" | grep -v "^  PASS" | tail -12; exit 1
fi
echo "[5/9] new file: module selftest 301 ✓ (unchanged) · loans selftest 35/35 ✓"
BAK="${LIVE}.bak_${KIT_NAME}_$(date +%Y%m%d_%H%M%S)"
cp -f "$LIVE" "$BAK" || { echo "!! [6/9] backup failed — refusing"; exit 1; }
echo "[6/9] backup: $BAK"
cp -f staff_ledger.py "$LIVE" || { echo "!! install copy failed — restoring"; cp -f "$BAK" "$LIVE"; exit 1; }
INST="$(md5sum "$LIVE" | awk '{print $1}')"
if [ "$INST" != "$NEW_MD5_EXPECTED" ]; then echo "!! [7/9] installed bytes are $INST, expected $NEW_MD5_EXPECTED — restoring"; cp -f "$BAK" "$LIVE"; exit 1; fi
systemctl restart "$SVC" || { echo "!! restart failed — restoring"; cp -f "$BAK" "$LIVE"; systemctl restart "$SVC"; exit 1; }
sleep 2
echo "[7/9] installed ($NEW_MD5_EXPECTED) and $SVC restarted"
if ! systemctl is-active --quiet "$SVC"; then
  echo "!! [8/9] $SVC is NOT active — restoring"; cp -f "$BAK" "$LIVE"; systemctl restart "$SVC"; echo "   restored from $BAK"; exit 1
fi
echo "[8/9] $SVC active"
CODE="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:${LEDGER_PORT:-8043}/ledger/loans)"
if [ "$CODE" != "302" ]; then
  echo "!! [9/9] the live-shape walk: /ledger/loans answered $CODE, expected 302 (login redirect) — restoring"
  cp -f "$BAK" "$LIVE"; systemctl restart "$SVC"; echo "   restored from $BAK"; exit 1
fi
echo "[9/9] live-shape walk: /ledger/loans -> 302 (the route is live behind the login)"
echo
echo "=============================================================="
echo "  GREEN.  Open:  https://followup.dr-manoj.in/ledger/loans"
echo "  PIN (A0 — the close records THIS line):"
md5sum "$LIVE"
echo "  Reverse:  cp -f $BAK $LIVE && systemctl restart $SVC"
echo "=============================================================="
