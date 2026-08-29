#!/bin/bash
# =============================================================================
#  install_darpan.sh · kit S208_DARPAN — Sprint 2 on the clinic server
#
#  WHAT THIS IS
#      Darpan's day card, exceptions-first (owner spec §0d, 29-Aug-2026, final):
#      evening = ONE number (the drawer count); morning = a card assembled from
#      the two truths, in HIS convention — day sale net of returns with CN
#      bills · UPI with its matched bills · net cash = sale − UPI − home −
#      procedure · categories expandable to detail · bank MPR collapsed ·
#      exceptions with two-tap answers · drawer at Rs 50 tolerance. Plus the
#      owner's corrections page with tick-off and audit, the duplicate-filing
#      guard (re-file only by an owner grant), the money-received-bill-later
#      log, and the flag-dismiss / staged-reject tools (the 2026-06-12 case).
#
#  WHAT CHANGES ON THIS SERVER
#      finance_app.py    ONE block added before __main__, by program, byte-
#                        exactly reversible. The stock-ledger block is left
#                        completely alone. No gate edit: darpan_app installs
#                        its own before_request guard at init.
#      new files         darpan_app.py · darpan_card.html ·
#                        darpan_corrections.html · selftest_darpan.py ·
#                        patch_finance_app_darpan.py
#      finance.db        five darpan_* tables, created on first touch.
#                        NOTHING EXISTING ALTERED OR DROPPED.
#
#  Pages after install:
#      staff   https://followup.dr-manoj.in/finance/darpan
#      owner   https://followup.dr-manoj.in/finance/darpan/corrections
# =============================================================================
set -u
KIT_NAME="S208_DARPAN"
FIN=/root/finance
APP="$FIN/finance_app.py"
PY=/usr/bin/python3
SVC=clinic-finance.service
APP_MD5_EXPECTED=ada47c79e21f92772d960d5270e7eec0
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "=============================================================="
echo "  $KIT_NAME — Darpan's day card, exceptions first"
echo "=============================================================="

# ---------------------------------------------------------------- [1] preflight
for c in md5sum awk cp date systemctl; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! [1/8] '$c' missing — refusing"; exit 1; }
done
[ -f "$APP" ] || { echo "!! [1/8] $APP not found — refusing"; exit 1; }
[ -f "$FIN/bank_match.py" ] || { echo "!! [1/8] bank_match.py not on this server —"
  echo "   install S208_BANKMATCH first; the card is built on its tables."; exit 1; }
echo "[1/8] preflight ok"

# ---------------------------------------------------------------- [2] kit gate
cd "$HERE" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [2/8] kit SUMS mismatch — refusing"; exit 1; }
echo "[2/8] kit integrity ok"

# ---------------------------------------------------------------- [3] currency
LIVE="$(md5sum "$APP" | awk '{print $1}')"
if [ "$LIVE" != "$APP_MD5_EXPECTED" ]; then
  echo "!! [3/8] LIVE-FILE CURRENCY GATE — refusing. finance_app.py is $LIVE,"
  echo "   this kit was cut against $APP_MD5_EXPECTED (the S204_C2 file with"
  echo "   the stock-ledger block installed). NOTHING WAS WRITTEN — tell"
  echo "   Claude the md5 above."
  exit 1
fi
echo "[3/8] live-file currency ok"

# ---------------------------------------------------------------- [4] baseline
echo "[4/8] measuring the CURRENT smoke suite before touching anything"
BASE_OUT="$(cd "$FIN" && "$PY" finance_app.py --selftest 2>&1)"
BASE_N="$(echo "$BASE_OUT" | grep -oE 'SMOKE [0-9]+' | head -1 | awk '{print $2}')"
[ -n "${BASE_N:-}" ] || { echo "!! [4/8] could not read a baseline SMOKE count — refusing"
                          echo "$BASE_OUT" | tail -5; exit 1; }
echo "      baseline: SMOKE $BASE_N"

# ---------------------------------------------------------------- [5] backup+copy
STAMP="$(date +%Y%m%d_%H%M%S)"
BAK="${APP}.bak_${KIT_NAME}_${STAMP}"
cp -f "$APP" "$BAK" || { echo "!! [5/8] backup failed — refusing"; exit 1; }
echo "[5/8] backup: $BAK"

restore(){
  cp -f "$BAK" "$APP"
  systemctl restart "$SVC" >/dev/null 2>&1
  echo "   RESTORED finance_app.py and restarted $SVC. New files remain in"
  echo "   $FIN but nothing calls them."
}

for f in darpan_app.py darpan_card.html darpan_corrections.html \
         selftest_darpan.py patch_finance_app_darpan.py; do
  cp -f "$HERE/$f" "$FIN/$f" || { echo "!! [5/8] copy of $f failed"; restore; exit 1; }
  A="$(md5sum "$HERE/$f" | awk '{print $1}')"; B="$(md5sum "$FIN/$f" | awk '{print $1}')"
  [ "$A" = "$B" ] || { echo "!! [5/8] $f did not land intact"; restore; exit 1; }
done
echo "      five files copied and verified byte for byte"

# ---------------------------------------------------------------- [6] patch+prove
"$PY" "$FIN/patch_finance_app_darpan.py" --apply "$APP" >/dev/null || {
  echo "!! [6/8] the patch refused — restoring"; restore; exit 1; }
"$PY" -m py_compile "$APP" "$FIN/darpan_app.py" || {
  echo "!! [6/8] does not compile — restoring"; restore; exit 1; }

OUT="$(cd "$FIN" && "$PY" selftest_darpan.py 2>&1)"
echo "$OUT" | grep -qE "^37 passed, 0 failed" || {
  echo "!! [6/8] the darpan selftest did not report 37 passed — restoring"
  echo "$OUT" | grep -E "FAIL|passed" | tail -8; restore; exit 1; }
echo "[6/8] darpan selftest 37/37 ✓"

OUT="$(cd "$FIN" && "$PY" finance_app.py --selftest 2>&1)"
N="$(echo "$OUT" | grep -oE 'SMOKE [0-9]+' | head -1 | awk '{print $2}')"
if [ -z "${N:-}" ] || [ "$N" -lt "$BASE_N" ] || echo "$OUT" | grep -q "  FAIL:"; then
  echo "!!      the smoke suite went from $BASE_N to ${N:-?} — restoring"
  echo "$OUT" | grep "FAIL" | head -8; restore; exit 1; fi
echo "      existing smoke suite $N (was $BASE_N) ✓  nothing lost"

# ---------------------------------------------------------------- [7] restart
systemctl restart "$SVC" || { echo "!! [7/8] restart failed — restoring"; restore; exit 1; }
sleep 3
systemctl is-active --quiet "$SVC" || { echo "!! [7/8] $SVC not active — restoring"
                                        restore; exit 1; }
MOUNTED="$(cd "$FIN" && "$PY" - <<'PYEOF' 2>&1 | tail -1
import sys
try:
    import finance_app
    rules = [str(r) for r in finance_app.app.url_map.iter_rules()]
except Exception as e:                                         # noqa: BLE001
    print("IMPORT_FAILED %s: %s" % (e.__class__.__name__, e)); sys.exit(0)
need = ["/finance/darpan", "/finance/darpan/api/card",
        "/finance/darpan/corrections", "/finance/stock/api/healthz"]
missing = [p for p in need if p not in rules]
print("YES" if not missing else "MISSING " + " ".join(missing))
PYEOF
)"
[ "$MOUNTED" = "YES" ] || { echo "!! [7/8] routes not mounted: $MOUNTED — restoring"
                            restore; exit 1; }
echo "[7/8] $SVC restarted · day card, corrections AND the stock routes all present ✓"

echo "[8/8] done"
echo
echo "=============================================================="
echo "  GREEN. Two new pages, one guard:"
echo "    staff  : https://followup.dr-manoj.in/finance/darpan"
echo "    owner  : https://followup.dr-manoj.in/finance/darpan/corrections"
echo "  A second form for an already-filed day is now refused — the grant"
echo "  lives on your corrections page API (refile-grant)."
echo
echo "  Reverse:  cp -f $BAK $APP && systemctl restart $SVC"
echo "=============================================================="
