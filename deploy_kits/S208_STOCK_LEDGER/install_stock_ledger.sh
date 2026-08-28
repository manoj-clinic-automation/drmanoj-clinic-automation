#!/bin/bash
# =============================================================================
#  install_stock_ledger.sh · kit S208_STOCK_LEDGER · v3
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

# IS THE ROUTE ACTUALLY THERE?
#
# v2, 28-Aug-2026. The first version asked the app over HTTP and expected 401.
# The live app answers 302 -- it REDIRECTS a signed-out request to the portal
# login -- so the check refused a perfectly good install and restored. It was
# right to refuse something it did not recognise; it was wrong to be asking
# that question at all.
#
# The deeper problem: the fail-closed gate runs BEFORE routing, so an UNMOUNTED
# path answers 302 exactly like a mounted one. Signed out, over HTTP, the two
# cases are indistinguishable. So mounting is now proved the only honest way --
# by importing the module the same way gunicorn imports it and asking the app
# which routes it actually has. HTTP is kept, but only to answer "is the
# service answering at all", which is all it can honestly say.
MOUNTED="$(cd "$FIN" && "$PY" - <<'ROUTES_EOF' 2>&1 | tail -1
import sys
try:
    import finance_app
    rules = [str(r) for r in finance_app.app.url_map.iter_rules()]
except Exception as e:                                         # noqa: BLE001
    print("IMPORT_FAILED %s: %s" % (e.__class__.__name__, e))
    sys.exit(0)
print("YES" if "/finance/stock/api/healthz" in rules else "NO - %d routes" % len(rules))
ROUTES_EOF
)"
case "$MOUNTED" in
  YES) echo "[8/9] the app itself reports /finance/stock/api/healthz among its routes" ;;
  NO*) echo "!! [8/9] the app came up WITHOUT the stock routes -- $MOUNTED"
       echo "   Restoring."
       restore; exit 1 ;;
  *)   echo "!! [8/9] could not ask the app which routes it has:"
       echo "   $MOUNTED"
       echo "   Restoring -- an install that cannot be verified is not an install."
       restore; exit 1 ;;
esac

# And is the service answering? 302 is NORMAL here: signed out, the gate sends
# a browser to the portal login. 404 would mean the URL is unknown.
CODE="$("$PY" - "$PORT" <<'HTTP_EOF'
import sys, urllib.request, urllib.error


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


op = urllib.request.build_opener(NoRedirect)
try:
    print(op.open("http://127.0.0.1:%s/finance/stock/api/healthz" % sys.argv[1],
                  timeout=10).status)
except urllib.error.HTTPError as e:
    print(e.code)
except Exception:
    print(0)
HTTP_EOF
)"
case "$CODE" in
  200|301|302|303|307|308|401|403)
        echo "      service answering on port $PORT (HTTP $CODE)" ;;
  404)  echo "!! [8/9] port $PORT answers 404 for the stock page -- restoring"
        restore; exit 1 ;;
  0)    echo "!! [8/9] nothing answered on port $PORT -- restoring"
        restore; exit 1 ;;
  *)    echo "      service answered HTTP $CODE on port $PORT -- unusual, not fatal."
        echo "      The route is mounted (proved above). Mention this to Claude." ;;
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
