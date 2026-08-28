#!/bin/bash
# =============================================================================
#  install_stock_ledger.sh · kit S208_STOCK_LEDGER
#
#  The stock loop on the clinic server:
#      expected (Marg) -> counted (staff) -> difference -> cause -> closed
#
#  WHAT THIS IS, AND WHY IT IS NOT THE S207 KIT
#      S207 staged the same feature and it could not have worked. push_snapshot
#      sent the MARG token in the CRON header, to a path the Marg token was not
#      allowed to open, so the front gate refused every real push 401 before the
#      route ran. Differences would have been raised correctly and NEVER closed
#      -- and the symptom of that is "some differences are still open", which
#      for weeks is indistinguishable from a shop that has open differences.
#      Nobody would have looked.
#
#      Neither proof the kit carried could catch it: --dry-run returns before
#      the network call, and the 37 selftests drive a bare app with no gate.
#      This kit adds selftest_gate_join.py, which drives the real header through
#      the real gate into the real route, and fails if any of the three change.
#
#  WHAT IT CHANGES ON THIS SERVER
#      finance_app.py    two edits, both by program, both reversible:
#                          - the front gate lets the pharmacy sender's token
#                            open ONE more path, /stock/api/snapshot, exactly
#                            as it already opens /finance/api/marg-push
#                          - the blueprint is mounted, before __main__, so
#                            gunicorn sees it at import
#      new files         stock_app.py · stock_schema.sql · the two selftests ·
#                        patch_finance_app.py
#      finance.db        five new tables, created on first touch, idempotent.
#                        NOTHING EXISTING IS ALTERED OR DROPPED.
#
#  IT REFUSES RATHER THAN GUESSES. Every anchor must occur exactly once; the
#  existing smoke suite must not lose a single check; the service must come
#  back up and the route must answer. Any red and it puts the old file back and
#  restarts. Nothing is left half-installed.
# =============================================================================
set -u
KIT_NAME="S208_STOCK_LEDGER"
FIN=/root/finance
APP="$FIN/finance_app.py"
PY=/usr/bin/python3
SVC=clinic-finance.service
PORT="${FINANCE_PORT:-8106}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "=============================================================="
echo "  $KIT_NAME — the stock ledger, and the fix that makes it close"
echo "=============================================================="

# ---------------------------------------------------------------- [1] preflight
for c in md5sum awk cp date systemctl; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! [1/9] '$c' missing — refusing"; exit 1; }
done
[ -x "$PY" ] || { echo "!! [1/9] $PY not executable — refusing"; exit 1; }
[ -f "$APP" ] || { echo "!! [1/9] $APP not found — refusing"; exit 1; }
"$PY" -c "import flask" 2>/dev/null || { echo "!! [1/9] flask not importable — refusing"; exit 1; }
echo "[1/9] preflight ok"

# ---------------------------------------------------------------- [2] kit gate
cd "$HERE" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [2/9] kit SUMS mismatch — refusing"; exit 1; }
echo "[2/9] kit integrity ok"

# ---------------------------------------------------------------- [3] anchors
"$PY" patch_finance_app.py --check "$APP" || {
  echo "!! [3/9] the live finance_app.py is not the shape this patch expects."
  echo "   NOTHING WAS WRITTEN. Send the lines above to Claude — do not edit by hand."
  exit 1; }
echo "[3/9] anchors ok — the live file is the shape expected"

# ---------------------------------------------------------------- [4] baseline
echo "[4/9] measuring the CURRENT smoke suite before touching anything"
BASE_OUT="$(cd "$FIN" && "$PY" finance_app.py --selftest 2>&1)"
BASE_N="$(echo "$BASE_OUT" | grep -oE 'SMOKE [0-9]+' | head -1 | awk '{print $2}')"
[ -n "${BASE_N:-}" ] || { echo "!! [4/9] could not read a baseline SMOKE count — refusing"
                          echo "$BASE_OUT" | tail -5; exit 1; }
echo "      baseline: SMOKE $BASE_N"

# ---------------------------------------------------------------- [5] backup
STAMP="$(date +%Y%m%d_%H%M%S)"
BAK="${APP}.bak_${KIT_NAME}_${STAMP}"
cp -f "$APP" "$BAK" || { echo "!! [5/9] backup failed — refusing"; exit 1; }
echo "[5/9] backup: $BAK"

restore(){
  cp -f "$BAK" "$APP"
  systemctl restart "$SVC" >/dev/null 2>&1
  echo "   RESTORED finance_app.py from the backup and restarted $SVC."
  echo "   The new files are still in $FIN but nothing calls them."
}

# ---------------------------------------------------------------- [6] copy
for f in stock_app.py stock_schema.sql selftest_stock_app.py \
         selftest_gate_join.py push_snapshot.py patch_finance_app.py; do
  cp -f "$HERE/$f" "$FIN/$f" || { echo "!! [6/9] copy of $f failed"; restore; exit 1; }
  A="$(md5sum "$HERE/$f" | awk '{print $1}')"
  B="$(md5sum "$FIN/$f"  | awk '{print $1}')"
  [ "$A" = "$B" ] || { echo "!! [6/9] $f did not land intact"; restore; exit 1; }
done
echo "[6/9] six files copied and verified byte for byte"

# ---------------------------------------------------------------- [7] patch+prove
"$PY" "$FIN/patch_finance_app.py" --apply "$APP" >/dev/null || {
  echo "!! [7/9] the patch refused — restoring"; restore; exit 1; }
"$PY" -m py_compile "$APP" || { echo "!! [7/9] patched file does not compile — restoring"
                                restore; exit 1; }

OUT="$(cd "$FIN" && "$PY" selftest_stock_app.py 2>&1)"
echo "$OUT" | grep -qE "^44 passed, 0 failed" || {
  echo "!! [7/9] the stock selftest did not report 44 passed, 0 failed — restoring"
  echo "$OUT" | grep -E "FAIL|passed" | tail -8; restore; exit 1; }
echo "[7/9] stock selftest 44/44 ✓"

OUT="$(cd "$FIN" && "$PY" selftest_gate_join.py 2>&1)"
echo "$OUT" | grep -qE "^14 passed, 0 failed" || {
  echo "!!      the gate-join proof failed — this is the S207 fault itself. Restoring."
  echo "$OUT" | grep -E "FAIL|passed" | tail -8; restore; exit 1; }
echo "      gate join 14/14 ✓  (real header -> real gate -> real route)"

OUT="$(cd "$FIN" && "$PY" finance_app.py --selftest 2>&1)"
N="$(echo "$OUT" | grep -oE 'SMOKE [0-9]+' | head -1 | awk '{print $2}')"
if [ -z "${N:-}" ] || [ "$N" -lt "$BASE_N" ] || echo "$OUT" | grep -q "  FAIL:"; then
  echo "!!      the existing smoke suite went from $BASE_N to ${N:-?} — restoring"
  echo "$OUT" | grep "FAIL" | head -8; restore; exit 1; fi
echo "      existing smoke suite $N (was $BASE_N) ✓  nothing lost"

# ---------------------------------------------------------------- [8] restart
systemctl restart "$SVC" || { echo "!! [8/9] restart failed — restoring"; restore; exit 1; }
sleep 3
systemctl is-active --quiet "$SVC" || { echo "!! [8/9] $SVC not active — restoring"
                                        restore; exit 1; }

# Is the route actually there? 401 is the RIGHT answer: it means the route
# exists and the fail-closed gate is doing its job. 404 means the blueprint
# never mounted, which is the whole thing we are installing.
CODE="$("$PY" - "$PORT" <<'PYEOF'
import sys, urllib.request, urllib.error
try:
    urllib.request.urlopen("http://127.0.0.1:%s/stock/api/healthz" % sys.argv[1], timeout=10)
    print(200)
except urllib.error.HTTPError as e:
    print(e.code)
except Exception:
    print(0)
PYEOF
)"
case "$CODE" in
  401|403) echo "[8/9] $SVC up · /stock/api/healthz answers $CODE — mounted and gated ✓" ;;
  404)     echo "!! [8/9] /stock/api/healthz answers 404 — the blueprint did not mount. Restoring."
           restore; exit 1 ;;
  200)     echo "[8/9] $SVC up · /stock/api/healthz answers 200 — mounted, but NOT gated."
           echo "      Tell Claude before anyone uses it." ;;
  *)       echo "!! [8/9] could not reach the app on port $PORT (got '$CODE') — restoring"
           restore; exit 1 ;;
esac

# ---------------------------------------------------------------- [9] done
echo "[9/9] done"
echo
echo "=============================================================="
echo "  GREEN. The stock ledger is live on this server."
echo
echo "  NEXT, ON MANOJZ — this proves the nightly push can get in:"
echo "      python push_snapshot.py --verify"
echo "  Expect: GREEN -- the server accepted this machine's token."
echo "  It sends an empty body, so it writes nothing."
echo
echo "  Then:   python push_snapshot.py --dry-run     (shows what would go)"
echo "          python push_snapshot.py               (sends it)"
echo
echo "  Reverse, if you ever want it off:"
echo "      cp -f $BAK $APP && systemctl restart $SVC"
echo "  The five stock tables stay in finance.db, empty and harmless."
echo "=============================================================="
