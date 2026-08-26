#!/bin/bash
# =============================================================================
#  install_d349b.sh · kit S202_D349B — D349: ONE lane rule, shared by the close
#                                      and every screen that describes it.
#
#  THE FAULT
#    /ledger/statement told the owner that Darpan's Rs 20,000 SPECIAL
#    "recovers in full at the 2026-08 close". IT DOES NOT. The close's
#    SCHEDULE lane runs first and takes Rs 8,000, then 4,000 x 3.
#
#    The test for "is this a quota advance" existed TWICE. In close_month() the
#    schedule check is IMPLICIT IN THE ORDERING -- the schedule lane removes its
#    advances from the working set before the quota test runs. The statement
#    page had no such ordering, copied the quota test literally, and so was
#    wrong about EVERY scheduled advance ever issued.
#
#    A display fault, not a money fault: no rupee moves either way. But Darpan
#    can read that page, and it told him his entire month's salary was going.
#
#  THE FIX (D349)
#    advance_lane() -- one function, one definition. close_month() partitions by
#    it; the statement card describes it. Precedence matches the close EXACTLY
#    (schedule before interest), because this function must describe what the
#    code does, not what would be tidier. A scheduled advance now shows its real
#    plan: "by agreed schedule - 2026-08: Rs 8000 -> 2026-09: Rs 4000 ...".
#
#  BEHAVIOUR CHANGE TO THE CLOSE: NONE. The partition is provably identical --
#  the schedule lane already ran first, so the quota test could never see a
#  scheduled advance. Only the WORDS on a page change.
#
#  PROVEN BEFORE DELIVERY
#    offline selftest 294 -> 301, +7 exactly (projection written before measuring)
#    and the 7 new checks were run against the UNFIXED file, where they go RED on
#    the exact sentence that was wrong. They are not vacuous.
#    Selftest isolation proven with a canary data dir: nothing written outside it
#    (the S200 "a selftest that writes a live store is itself a live event" rule).
# =============================================================================
set -u
KIT_NAME="S202_D349B"
LIVE=/root/staff_ledger.py
LIVE_MD5_EXPECTED=eaa305cb1f04fd4e20a350626ff84aa6
NEW_MD5_EXPECTED=9e764f807ad2012537c29fdb8ed6f124
PY=/root/wa/venv/bin/python3
SVC=staff-ledger.service
PROBE=/tmp/d349b_probe

echo "=============================================================="
echo "  $KIT_NAME — D349: one lane rule, one place"
echo "=============================================================="

for c in md5sum awk cp date systemctl; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — refusing"; exit 1; }
done
[ -x "$PY" ]   || { echo "!! preflight: $PY not executable — refusing"; exit 1; }
[ -f "$LIVE" ] || { echo "!! preflight: $LIVE not found — refusing"; exit 1; }
echo "[1/8] preflight ok"

md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [2/8] kit SUMS mismatch — refusing"; exit 1; }
echo "[2/8] kit integrity ok"

ACTUAL="$(md5sum "$LIVE" | awk '{print $1}')"
if [ "$ACTUAL" != "$LIVE_MD5_EXPECTED" ]; then
  echo "!! [3/8] LIVE CODE CURRENCY GATE — refusing."
  echo "   $LIVE is $ACTUAL"
  echo "   this kit was built against $LIVE_MD5_EXPECTED"
  echo "   The patch is a full-file replacement. Installing over a file that has"
  echo "   moved would silently discard whatever moved it."
  exit 1
fi
echo "[3/8] live-code currency gate ok"

rm -rf "$PROBE"; mkdir -p "$PROBE/data" || { echo "!! [4/8] cannot make probe dir"; exit 1; }
cp -f staff_ledger.py "$PROBE/staff_ledger.py"
echo "[4/8] probing the NEW file in isolation (LEDGER_DIR=$PROBE/data — the live"
echo "      store is never opened; S200 rule)"
OUT="$(cd "$PROBE" && LEDGER_DIR="$PROBE/data" "$PY" staff_ledger.py --selftest 2>&1)"
# match on ASCII only -- the pass line contains an em dash, and a gate that
# refuses on a locale/encoding quirk is a false alarm, not a safeguard
if ! { echo "$OUT" | grep -q "SELFTEST PASSED" && echo "$OUT" | grep -qE "(^|[^0-9])301([^0-9]|$)"; }; then
  echo "!! [5/8] the new file did NOT report 301 — refusing, nothing installed"
  echo "$OUT" | tail -12
  exit 1
fi
echo "[5/8] new file selftest: 301 ✓  (was 294)"

BAK="${LIVE}.bak_${KIT_NAME}_$(date +%Y%m%d_%H%M%S)"
cp -f "$LIVE" "$BAK" || { echo "!! [6/8] backup failed — refusing"; exit 1; }
echo "[6/8] backup: $BAK"

cp -f staff_ledger.py "$LIVE" || { echo "!! install copy failed — restoring"; cp -f "$BAK" "$LIVE"; exit 1; }
INST="$(md5sum "$LIVE" | awk '{print $1}')"
if [ "$INST" != "$NEW_MD5_EXPECTED" ]; then
  echo "!! [7/8] installed bytes are $INST, expected $NEW_MD5_EXPECTED — restoring"
  cp -f "$BAK" "$LIVE"; exit 1
fi
systemctl restart "$SVC" || { echo "!! restart failed — restoring"; cp -f "$BAK" "$LIVE"; systemctl restart "$SVC"; exit 1; }
sleep 2
echo "[7/8] installed ($NEW_MD5_EXPECTED) and $SVC restarted"

if ! systemctl is-active --quiet "$SVC"; then
  echo "!! [8/8] $SVC is NOT active — restoring"
  cp -f "$BAK" "$LIVE"; systemctl restart "$SVC"
  echo "   restored from $BAK"; exit 1
fi
echo "[8/8] $SVC active"

echo
echo "=============================================================="
echo "  GREEN. Open Darpan's statement:"
echo "    https://followup.dr-manoj.in/ledger/statement?staff=Darpan"
echo
echo "  His Rs 20,000 card must now read:"
echo "    'by agreed schedule — 2026-08: Rs 8000 → 2026-09: Rs 4000 → ...'"
echo "  and must NO LONGER say 'recovers in full at the 2026-08 close'."
echo
echo "  No money moved. The close always took 8,000; only the page was wrong."
echo
echo "  Reverse:  cp -f $BAK $LIVE && systemctl restart $SVC"
echo "=============================================================="
