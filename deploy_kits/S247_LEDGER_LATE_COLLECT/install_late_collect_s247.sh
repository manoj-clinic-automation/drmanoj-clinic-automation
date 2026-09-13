#!/bin/bash
# =============================================================================
#  install_late_collect_s247.sh · kit S247_LEDGER_LATE_COLLECT · staff_ledger.py v3.8
#
#  Run by:
#    bash /root/deploy/repo/deploy_kits/S247_LEDGER_LATE_COLLECT/install_late_collect_s247.sh
#
#  THE OWNER, 13-Sep-2026, on Alisha's Rs 5,000 of 25-Aug: "which was made against the
#  August month, has been marked for September in your salary sheet. I want it deducted
#  in the August month salary payment only. I cannot find any flow for that."
#
#  There was none. August's close was pressed on the 20th; the advance came on the 25th;
#  a close is never repeated, so the collection fell to the next close, and DEFER — the
#  one control on the card — only moves it further away.
#
#  WHAT CHANGES: one new control on an open advance — "collect against a month that is
#  already closed" — which writes ONE ADVANCE_INSTALMENT row stamped to that month: the
#  same row the close itself writes, with the name of the person who decided it and a
#  written reason. Narrow on purpose: the month must already be closed, never earlier
#  than the month the advance counts against, never twice for the same advance and
#  month, never more than the balance.
#
#  close_month(), the waterfall, the quota lane, the capacity rule, interest and
#  schedules are NOT changed by one line. The ledger stays append-only.
#
#  PROVEN BEFORE DELIVERY: the module's own selftest still 323; a 55-check live-shape
#  walk; and a probe that performs the collection on a COPY of the real ledger.
#  ON THE BOX, BEFORE ANYTHING IS REPLACED: all three again.
#  Red path: the previous file is restored and the service restarted. The live ledger
#  store is never opened for writing by this script.
# =============================================================================
set -u
KIT="S247_LEDGER_LATE_COLLECT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
LIVE="${SL_LIVE:-/root/staff_ledger.py}"
LIVE_MD5_EXPECTED=49b13f42d3a923c5bb2e34230c80e6e8        # v3.7-S238-CLOSE-GUARD
LDIR="${LEDGER_DIR:-/root/staff_ledger}"
PY="${PY:-/root/wa/venv/bin/python3}"
SVC="${SL_SVC:-staff-ledger.service}"
PROBE=/tmp/s247_late_collect_probe
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

ACTUAL="$(md5sum "$LIVE" | awk '{print $1}')"
if [ "$ACTUAL" = "$NEW_MD5" ]; then
  echo "-- ALREADY INSTALLED: $LIVE is this kit's file ($NEW_MD5). Nothing changed."
  exit 0
fi
systemctl show -p ExecStart "$SVC" 2>/dev/null | grep -q "$LIVE" \
  || { echo "!! [2/9] $SVC does not run $LIVE — read its ExecStart; nothing installed"; exit 1; }
[ "$ACTUAL" = "$LIVE_MD5_EXPECTED" ] \
  || { echo "!! [2/9] LIVE CODE CURRENCY GATE — $LIVE is $ACTUAL, this kit was built against $LIVE_MD5_EXPECTED. Nothing installed."; exit 1; }
echo "[2/9] the service runs $LIVE and it is the pinned v3.7"

rm -rf "$PROBE"; mkdir -p "$PROBE/st" && chmod 700 "$PROBE" || { echo "!! [3/9] cannot make $PROBE"; exit 1; }
cp -f staff_ledger.py "$PROBE/st/"
OUT="$(cd "$PROBE/st" && LEDGER_DIR="$PROBE/st" "$PY" -B staff_ledger.py --selftest 2>&1)"
echo "$OUT" | grep -q "SELFTEST PASSED — 323 " \
  || { echo "!! [3/9] the new file did NOT report the module's 323 checks — nothing installed"; echo "$OUT" | tail -6; rm -rf "$PROBE"; exit 1; }
echo "[3/9] new file: the module's own selftest, 323 checks ✓ (unchanged by this kit)"

OUT_W="$("$PY" -B walk_late_collect_s247.py "$PROBE/st/staff_ledger.py" 2>&1)"
echo "$OUT_W" | grep -q "WALK GREEN" \
  || { echo "!! [4/9] the kit's own walk failed ON THIS BOX — nothing installed"; echo "$OUT_W" | tail -12; rm -rf "$PROBE"; exit 1; }
echo "[4/9] $(echo "$OUT_W" | grep -E '^== [0-9]+ checks' | tail -1)"

OUT2="$("$PY" -B probe_live_shape_s247.py "$PROBE/st/staff_ledger.py" "$PROBE/copy" "$LDIR" 2>&1)"
echo "$OUT2" | grep -q " 0 failures" \
  || { echo "!! [5/9] the live-shape probe failed on a COPY of the real ledger — nothing installed"; echo "$OUT2" | tail -10; rm -rf "$PROBE"; exit 1; }
echo "[5/9] $OUT2"
rm -rf "$PROBE"

BAK="${LIVE}.bak_${KIT}_${STAMP}"
cp -f "$LIVE" "$BAK" || { echo "!! [6/9] backup failed — nothing installed"; exit 1; }
echo "[6/9] backup: $BAK"
restore() { echo "   restoring $BAK"; cp -f "$BAK" "$LIVE"; systemctl restart "$SVC"; sleep 2
            echo "   now running: $(md5sum "$LIVE" | awk '{print $1}') (expected $LIVE_MD5_EXPECTED)"; exit 1; }
cp -f staff_ledger.py "$LIVE" || { echo "!! [7/9] copy failed"; restore; }
[ "$(md5sum "$LIVE" | awk '{print $1}')" = "$NEW_MD5" ] || { echo "!! [7/9] installed bytes differ"; restore; }
echo "[7/9] installed $NEW_MD5"
systemctl restart "$SVC" || { echo "!! [8/9] restart failed"; restore; }
sleep 2
systemctl is-active --quiet "$SVC" || { echo "!! [8/9] $SVC is NOT active"; restore; }
CODE="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:${LEDGER_PORT:-8043}/ledger/advances)"
[ "$CODE" = "302" ] || { echo "!! [8/9] /ledger/advances answered $CODE, expected 302 (the login redirect)"; restore; }
PAGE="$(curl -s http://127.0.0.1:${LEDGER_PORT:-8043}/ledger/login)"
echo "$PAGE" | grep -q "3.8-S247-LATE-COLLECT" || { echo "!! [8/9] the running service does not report v3.8"; restore; }
echo "[8/9] live: /ledger/advances -> 302 behind the login, and the service reports v3.8-S247-LATE-COLLECT"
echo "[9/9] GREEN"
echo
echo "=============================================================="
echo "  GREEN — an advance can now be collected against a month that"
echo "  is already closed."
echo
echo "  DO THIS ONE THING NEXT:"
echo "    https://followup.dr-manoj.in/ledger/advances"
echo "    Alisha's card -> month 2026-08, amount 5000, reason, Collect."
echo "  Then reload the August money sheet."
echo
echo "  PIN:"
md5sum "$LIVE"
echo "  Reverse:  \\cp -f $BAK $LIVE && systemctl restart $SVC"
echo "=============================================================="
