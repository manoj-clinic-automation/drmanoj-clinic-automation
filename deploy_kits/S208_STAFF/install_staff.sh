#!/bin/bash
# =============================================================================
#  install_staff.sh · kit S208_STAFF — the joiner/exit register, with faces
#
#  "All is final and prepared already" (owner, 30-Aug) — and it very nearly
#  was. The S207 register (65 checks) is reused with ONE one-line fix and one
#  adapter, both found by walking it against the LIVE app's shapes:
#    * require() returns a user DICT live; the register binds the value into
#      SQL -> its first /open would have crashed. Fixed by an adapter in
#      staff_pages.py; joiner_app's logic untouched.
#    * HARD_REQUIRES was kind-blind: an EXIT's final step demanded BIOMETRIC,
#      a step exits do not have -> NO EXIT COULD EVER COMPLETE. One line in
#      joiner_app.py (S208.1); the original 65 checks still pass.
#
#  WHAT CHANGES
#      finance_app.py    one block before __main__ (anchor-gated, reversible)
#      new files         joiner_app.py (S208.1) · joiner_schema.sql ·
#                        staff_pages.py · staff_manage.html ·
#                        seed_codes_from_vps.py · the two selftests · patcher
#      finance.db        joiner tables on first touch. Nothing existing altered.
#
#  Page after install:  https://followup.dr-manoj.in/finance/staff
#  (point the portal's user-manage tile at it — one link, owner's action)
# =============================================================================
set -u
KIT_NAME="S208_STAFF"
FIN=/root/finance
APP="$FIN/finance_app.py"
PY=/usr/bin/python3
SVC=clinic-finance.service
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "=============================================================="
echo "  $KIT_NAME — jodna aur vidaai, guided"
echo "=============================================================="

for c in md5sum awk cp date systemctl; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! [1/7] '$c' missing — refusing"; exit 1; }
done
[ -f "$APP" ] || { echo "!! [1/7] $APP not found — refusing"; exit 1; }
echo "[1/7] preflight ok"

cd "$HERE" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [2/7] kit SUMS mismatch — refusing"; exit 1; }
echo "[2/7] kit integrity ok"

echo "[3/7] live finance_app.py is $(md5sum "$APP" | awk '{print $1}') -- gating on anchors"
"$PY" "$HERE/patch_finance_app_staff.py" --check "$APP" || {
  echo "!! [3/7] the live finance_app.py is not the shape this patch expects."
  echo "   NOTHING WAS WRITTEN. Send the lines above to Claude."; exit 1; }
echo "      anchors ok"

echo "[4/7] measuring the CURRENT smoke suite"
BASE_OUT="$(cd "$FIN" && "$PY" finance_app.py --selftest 2>&1)"
BASE_N="$(echo "$BASE_OUT" | grep -oE 'SMOKE [0-9]+' | head -1 | awk '{print $2}')"
[ -n "${BASE_N:-}" ] || { echo "!! [4/7] no baseline — refusing"; exit 1; }
echo "      baseline: SMOKE $BASE_N"

STAMP="$(date +%Y%m%d_%H%M%S)"
BAK="${APP}.bak_${KIT_NAME}_${STAMP}"
cp -f "$APP" "$BAK" || { echo "!! [5/7] backup failed"; exit 1; }
echo "[5/7] backup: $BAK"
restore(){ cp -f "$BAK" "$APP"; systemctl restart "$SVC" >/dev/null 2>&1
  echo "   RESTORED finance_app.py and restarted $SVC."; }

for f in joiner_app.py joiner_schema.sql staff_pages.py staff_manage.html \
         seed_codes_from_vps.py selftest_joiner_app.py selftest_staff_pages.py \
         patch_finance_app_staff.py; do
  cp -f "$HERE/$f" "$FIN/$f" || { echo "!! [5/7] copy of $f failed"; restore; exit 1; }
  A="$(md5sum "$HERE/$f" | awk '{print $1}')"; B="$(md5sum "$FIN/$f" | awk '{print $1}')"
  [ "$A" = "$B" ] || { echo "!! [5/7] $f did not land intact"; restore; exit 1; }
done

"$PY" "$FIN/patch_finance_app_staff.py" --apply "$APP" >/dev/null || {
  echo "!! [6/7] the patch refused — restoring"; restore; exit 1; }
"$PY" -m py_compile "$APP" "$FIN/joiner_app.py" "$FIN/staff_pages.py" || {
  echo "!! [6/7] does not compile — restoring"; restore; exit 1; }

OUT="$(cd "$FIN" && "$PY" selftest_joiner_app.py 2>&1)"
echo "$OUT" | grep -qE "^65 passed, 0 failed" || {
  echo "!! [6/7] the register's own 65 checks failed — restoring"
  echo "$OUT" | grep -E "FAIL|passed" | tail -6; restore; exit 1; }
OUT="$(cd "$FIN" && "$PY" selftest_staff_pages.py 2>&1)"
echo "$OUT" | grep -qE "^23 passed, 0 failed" || {
  echo "!! [6/7] the guided-flow walk failed — restoring"
  echo "$OUT" | grep -E "FAIL|passed" | tail -6; restore; exit 1; }
echo "[6/7] register 65/65 ✓ · guided walk 23/23 ✓"
OUT="$(cd "$FIN" && "$PY" finance_app.py --selftest 2>&1)"
N="$(echo "$OUT" | grep -oE 'SMOKE [0-9]+' | head -1 | awk '{print $2}')"
if [ -z "${N:-}" ] || [ "$N" -lt "$BASE_N" ] || echo "$OUT" | grep -q "  FAIL:"; then
  echo "!!      smoke went from $BASE_N to ${N:-?} — restoring"
  echo "$OUT" | grep "FAIL" | head -6; restore; exit 1; fi
echo "      smoke suite $N (was $BASE_N) ✓  nothing lost"

systemctl restart "$SVC" || { echo "!! [7/7] restart failed — restoring"; restore; exit 1; }
sleep 3
systemctl is-active --quiet "$SVC" || { echo "!! [7/7] not active — restoring"; restore; exit 1; }
MOUNTED="$(cd "$FIN" && "$PY" - <<'PYEOF' 2>&1 | tail -1
import sys
try:
    import finance_app
    rules = [str(r) for r in finance_app.app.url_map.iter_rules()]
except Exception as e:                                         # noqa: BLE001
    print("IMPORT_FAILED %s: %s" % (e.__class__.__name__, e)); sys.exit(0)
need = ["/finance/staff", "/finance/staff/api/healthz", "/finance/darpan",
        "/finance/pipeline", "/finance/stock/api/healthz"]
missing = [p for p in need if p not in rules]
print("YES" if not missing else "MISSING " + " ".join(missing))
PYEOF
)"
[ "$MOUNTED" = "YES" ] || { echo "!! [7/7] routes: $MOUNTED — restoring"; restore; exit 1; }
echo "[7/7] $SVC restarted · staff page + every earlier route present ✓"

echo
echo "=============================================================="
echo "  GREEN.  https://followup.dr-manoj.in/finance/staff"
echo "  Point the portal's user-manage tile at that address — one link."
echo
echo "  BEFORE Amir's BIOMETRIC step: seed the code register once —"
echo "    cd $FIN && $PY seed_codes_from_vps.py --dry"
echo "  (punches.csv + roster; a gap is somebody's code, never reused)"
echo
echo "  Reverse:  cp -f $BAK $APP && systemctl restart $SVC"
echo "=============================================================="
