#!/bin/bash
# =============================================================================
#  install_close_guard.sh · kit S238_CLOSE_GUARD — staff_ledger.py v3.7
#  Run by:  bash /root/deploy/vps_deploy.sh S238_CLOSE_GUARD
#
#  THE OWNER, 10-Sep-2026 (D447): "the close should be after the calendar month is
#  over and only when I manually do it, because corrections have to be done in the
#  attendance and other things also."
#
#  WHAT CHANGES
#    + the monthly close is offered ONLY from the 1st of the following month, and
#      only by a checker's own press; the route and the CLI refuse an earlier one.
#      (Nothing ever closed a month automatically — August's close of 20-Aug was a
#      press of the Salary page's step-5 button, which then allowed any day.)
#    + the close refuses while any of the month's entries is still PENDING, unless
#      the checker ticks "close anyway" — and then names them.
#    + after the close it says, by name, what it did not collect (close_report_<month>.txt).
#    + a duplicate entry (same person, category, date, amount) is refused with a
#      one-click "save it as a separate entry".
#    + a SPECIAL advance needs a narration.
#  close_month() — the engine — is NOT changed by one line.
#
#  PROVEN BEFORE DELIVERY: module selftest 301 -> 323 (the 21 new checks counted,
#  four sabotages each caught); live-shape walk on the owner's own 58 rows 20/20.
#  ON THE BOX, BEFORE ANYTHING IS REPLACED: the selftest again, and a probe of the
#  new file against a COPY of the real ledger rendering every page the owner uses.
#
#  Red path: restores the previous file and restarts the service. The ledger itself
#  is never opened for writing by this script.
# =============================================================================
set -u
KIT="S238_CLOSE_GUARD"
KDIR="$(cd "$(dirname "$0")" && pwd)"
LIVE="${SL_LIVE:-/root/staff_ledger.py}"
LIVE_MD5_EXPECTED=802577112e6db82bcf763d142efcd00c        # v3.6-S225-LOANS-D374 rev 3
LDIR="${LEDGER_DIR:-/root/staff_ledger}"
PY="${PY:-/root/wa/venv/bin/python3}"
SVC=staff-ledger.service
PROBE=/tmp/s238_close_guard_probe
STAMP="$(date +%Y%m%d_%H%M%S)"
BAK=""

cd "$KDIR" || { echo "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp date systemctl curl; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — nothing installed"; exit 1; }
done
[ -x "$PY" ] || { echo "!! preflight: $PY not executable — nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/9] SUMS.md5 gate failed — kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { echo "!! [1/9] KIT_ID.txt names another kit — nothing installed"; exit 1; }
NEW_MD5="$(awk 'NR==1{print $2}' KIT_ID.txt)"
[ "$NEW_MD5" = "$(md5sum staff_ledger.py | awk '{print $1}')" ] || { echo "!! [1/9] KIT_ID does not match staff_ledger.py (F-88) — nothing installed"; exit 1; }
echo "[1/9] kit gates green"
systemctl show -p ExecStart "$SVC" 2>/dev/null | grep -q "$LIVE" \
  || { echo "!! [2/9] $SVC does not run $LIVE — read its ExecStart; nothing installed"; exit 1; }
ACTUAL="$(md5sum "$LIVE" | awk '{print $1}')"
[ "$ACTUAL" = "$LIVE_MD5_EXPECTED" ] \
  || { echo "!! [2/9] LIVE CODE CURRENCY GATE — $LIVE is $ACTUAL, this kit was built against $LIVE_MD5_EXPECTED. Nothing installed."; exit 1; }
echo "[2/9] the service runs $LIVE and it is the pinned v3.6 rev 3"
rm -rf "$PROBE"; mkdir -p "$PROBE/st" && chmod 700 "$PROBE" || { echo "!! [3/9] cannot make $PROBE"; exit 1; }
cp -f staff_ledger.py "$PROBE/st/"
OUT="$(cd "$PROBE/st" && LEDGER_DIR="$PROBE/st" "$PY" -B staff_ledger.py --selftest 2>&1)"
echo "$OUT" | grep -q "SELFTEST PASSED — 323 " \
  || { echo "!! [3/9] the new file did NOT report 323 — nothing installed"; echo "$OUT" | tail -6; rm -rf "$PROBE"; exit 1; }
echo "[3/9] new file: module selftest 323 ✓"
OUT2="$("$PY" -B probe_live_shape.py "$PROBE/st/staff_ledger.py" "$PROBE/copy" "$LDIR" 2>&1)"
echo "$OUT2" | grep -q " 0 failures" \
  || { echo "!! [4/9] the live-shape probe failed on a copy of the real ledger — nothing installed"; echo "$OUT2" | tail -8; rm -rf "$PROBE"; exit 1; }
echo "[4/9] $OUT2"
rm -rf "$PROBE"
BAK="${LIVE}.bak_${KIT}_${STAMP}"
cp -f "$LIVE" "$BAK" || { echo "!! [5/9] backup failed — nothing installed"; exit 1; }
echo "[5/9] backup: $BAK"
restore() { echo "   restoring $BAK"; cp -f "$BAK" "$LIVE"; systemctl restart "$SVC"; sleep 2
            echo "   now running: $(md5sum "$LIVE" | awk '{print $1}') (expected $LIVE_MD5_EXPECTED)"; exit 1; }
cp -f staff_ledger.py "$LIVE" || { echo "!! [6/9] copy failed"; restore; }
[ "$(md5sum "$LIVE" | awk '{print $1}')" = "$NEW_MD5" ] || { echo "!! [6/9] installed bytes differ"; restore; }
echo "[6/9] installed $NEW_MD5"
systemctl restart "$SVC" || { echo "!! [7/9] restart failed"; restore; }
sleep 2
systemctl is-active --quiet "$SVC" || { echo "!! [7/9] $SVC is NOT active"; restore; }
echo "[7/9] $SVC restarted and active"
CODE="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:${LEDGER_PORT:-8043}/ledger/salary)"
[ "$CODE" = "302" ] || { echo "!! [8/9] /ledger/salary answered $CODE, expected 302 (the login redirect)"; restore; }
PAGE="$(curl -s http://127.0.0.1:${LEDGER_PORT:-8043}/ledger/login)"
echo "$PAGE" | grep -q "3.7-S238-CLOSE-GUARD" || { echo "!! [8/9] the running service does not report v3.7"; restore; }
echo "[8/9] live: /ledger/salary -> 302 behind the login, and the service reports v3.7-S238-CLOSE-GUARD"
echo "[9/9] GREEN"
echo
echo "=============================================================="
echo "  GREEN — the close now opens only after the month has ended."
echo "  See it:  https://followup.dr-manoj.in/ledger/salary"
echo "  PIN (the close records this line):"
md5sum "$LIVE"
echo "  Reverse:  \\cp -f $BAK $LIVE && systemctl restart $SVC"
echo "=============================================================="
