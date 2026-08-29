#!/bin/bash
# =============================================================================
#  install_ledger3.sh · kit S208_LEDGER3 — Sprint 3 on the clinic server
#
#  WHAT THIS IS
#      1. THE LEDGERS, DIAGNOSED AND REPAIRABLE. Reserve (Dr Bhawna), Dr
#         Manoj's cash and the drawer all read through v_cash_custody_balance,
#         a VIEW created by the S186 migration -- not by the schema file. If
#         it is absent, all three ledgers freeze at once, which is exactly the
#         owner's complaint. New owner tools on the darpan blueprint:
#           GET  /finance/darpan/api/ledger-check?date=2026-08-27
#                the raw rows and the named fault, before anything is touched
#           POST /finance/darpan/api/ledger-repair-view
#                creates the view if absent (the migration's own SQL, additive)
#           POST /finance/darpan/api/transfer
#                perform/repair a transfer as a custody event -- dated, noted,
#                owner-only, audited; never moves money, records custody
#      2. ONE PREDICATE for "is this day's Marg export in": a pushed report
#         still in staging covers the day as truly as an applied one, so
#         pendCard stops calling an approved day "not filed". Anchored patch;
#         if the live text has drifted it SKIPS WITH A WARNING -- display
#         honesty, not money, so it never blocks the ledger repairs.
#
#  WHAT CHANGES
#      darpan_app.py     FULL replacement of the S208_DARPAN file (this kit's
#                        own file -- md5-gated against the exact bytes shipped)
#      finance_app.py    the one-clause pendCard patch, soft (skip on drift)
#      finance.db        nothing until the owner calls a repair
# =============================================================================
set -u
KIT_NAME="S208_LEDGER3"
FIN=/root/finance
APP="$FIN/finance_app.py"
DAR="$FIN/darpan_app.py"
PY=/usr/bin/python3
SVC=clinic-finance.service
DAR_MD5_EXPECTED=c787456ddd595150996f84e00fb1fd2f
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "=============================================================="
echo "  $KIT_NAME — the ledgers, diagnosed; one predicate for pendCard"
echo "=============================================================="

# ---------------------------------------------------------------- [1] preflight
for c in md5sum awk cp date systemctl; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! [1/7] '$c' missing — refusing"; exit 1; }
done
[ -f "$DAR" ] || { echo "!! [1/7] darpan_app.py not on this server — install"
  echo "   S208_DARPAN first."; exit 1; }
echo "[1/7] preflight ok"

# ---------------------------------------------------------------- [2] kit gate
cd "$HERE" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [2/7] kit SUMS mismatch — refusing"; exit 1; }
echo "[2/7] kit integrity ok"

# ---------------------------------------------------------------- [3] currency
LIVE="$(md5sum "$DAR" | awk '{print $1}')"
if [ "$LIVE" != "$DAR_MD5_EXPECTED" ]; then
  echo "!! [3/7] darpan_app.py on this server is $LIVE, expected"
  echo "   $DAR_MD5_EXPECTED (the exact S208_DARPAN file). It has been edited"
  echo "   since — NOTHING WAS WRITTEN; tell Claude the md5."
  exit 1
fi
echo "[3/7] darpan_app.py currency ok (this kit's own file, exact bytes)"

# ---------------------------------------------------------------- [4] baseline
echo "[4/7] measuring the CURRENT smoke suite before touching anything"
BASE_OUT="$(cd "$FIN" && "$PY" finance_app.py --selftest 2>&1)"
BASE_N="$(echo "$BASE_OUT" | grep -oE 'SMOKE [0-9]+' | head -1 | awk '{print $2}')"
[ -n "${BASE_N:-}" ] || { echo "!! [4/7] no baseline SMOKE count — refusing"
                          echo "$BASE_OUT" | tail -5; exit 1; }
echo "      baseline: SMOKE $BASE_N"

# ---------------------------------------------------------------- [5] backup+copy
STAMP="$(date +%Y%m%d_%H%M%S)"
BAKD="${DAR}.bak_${KIT_NAME}_${STAMP}"
BAKA="${APP}.bak_${KIT_NAME}_${STAMP}"
cp -f "$DAR" "$BAKD" && cp -f "$APP" "$BAKA" || {
  echo "!! [5/7] backup failed — refusing"; exit 1; }
echo "[5/7] backups: $BAKD"
echo "               $BAKA"

restore(){
  cp -f "$BAKD" "$DAR"; cp -f "$BAKA" "$APP"
  systemctl restart "$SVC" >/dev/null 2>&1
  echo "   RESTORED both files and restarted $SVC."
}

for f in darpan_app.py selftest_darpan.py patch_finance_app_pend.py; do
  cp -f "$HERE/$f" "$FIN/$f" || { echo "!! [5/7] copy of $f failed"; restore; exit 1; }
  A="$(md5sum "$HERE/$f" | awk '{print $1}')"; B="$(md5sum "$FIN/$f" | awk '{print $1}')"
  [ "$A" = "$B" ] || { echo "!! [5/7] $f did not land intact"; restore; exit 1; }
done

PEND="skipped"
if "$PY" "$FIN/patch_finance_app_pend.py" --check "$APP" >/dev/null 2>&1; then
  "$PY" "$FIN/patch_finance_app_pend.py" --apply "$APP" >/dev/null && PEND="applied"
fi
if [ "$PEND" = "applied" ]; then
  echo "      pendCard predicate: APPLIED"
else
  echo "      ⚠ pendCard predicate: SKIPPED — the live query text has drifted"
  echo "        from the copy this patch was cut against. The ledger tools"
  echo "        install regardless; the approved-vs-not-filed fix waits for a"
  echo "        look at the live file. Not a failure."
fi

# ---------------------------------------------------------------- [6] prove
"$PY" -m py_compile "$APP" "$FIN/darpan_app.py" || {
  echo "!! [6/7] does not compile — restoring"; restore; exit 1; }
OUT="$(cd "$FIN" && "$PY" selftest_darpan.py 2>&1)"
echo "$OUT" | grep -qE "^50 passed, 0 failed" || {
  echo "!! [6/7] selftest did not report 50 passed — restoring"
  echo "$OUT" | grep -E "FAIL|passed" | tail -8; restore; exit 1; }
echo "[6/7] selftest 50/50 ✓"
OUT="$(cd "$FIN" && "$PY" finance_app.py --selftest 2>&1)"
N="$(echo "$OUT" | grep -oE 'SMOKE [0-9]+' | head -1 | awk '{print $2}')"
if [ -z "${N:-}" ] || [ "$N" -lt "$BASE_N" ] || echo "$OUT" | grep -q "  FAIL:"; then
  echo "!!      smoke went from $BASE_N to ${N:-?} — restoring"
  echo "$OUT" | grep "FAIL" | head -8; restore; exit 1; fi
echo "      existing smoke suite $N (was $BASE_N) ✓  nothing lost"

# ---------------------------------------------------------------- [7] restart
systemctl restart "$SVC" || { echo "!! [7/7] restart failed — restoring"; restore; exit 1; }
sleep 3
systemctl is-active --quiet "$SVC" || { echo "!! [7/7] $SVC not active — restoring"
                                        restore; exit 1; }
MOUNTED="$(cd "$FIN" && "$PY" - <<'PYEOF' 2>&1 | tail -1
import sys
try:
    import finance_app
    rules = [str(r) for r in finance_app.app.url_map.iter_rules()]
except Exception as e:                                         # noqa: BLE001
    print("IMPORT_FAILED %s: %s" % (e.__class__.__name__, e)); sys.exit(0)
need = ["/finance/darpan/api/ledger-check", "/finance/darpan/api/transfer",
        "/finance/darpan", "/finance/stock/api/healthz"]
missing = [p for p in need if p not in rules]
print("YES" if not missing else "MISSING " + " ".join(missing))
PYEOF
)"
[ "$MOUNTED" = "YES" ] || { echo "!! [7/7] routes not mounted: $MOUNTED — restoring"
                            restore; exit 1; }
echo "[7/7] $SVC restarted · ledger tools, day card AND stock routes present ✓"

echo
echo "=============================================================="
echo "  GREEN. pendCard predicate: $PEND."
echo
echo "  NOW, from your signed-in browser (console, F12) — the diagnosis:"
echo "    fetch('/finance/darpan/api/ledger-check?date=2026-08-27')"
echo "      .then(r=>r.json()).then(j=>console.log(j.problems, j))"
echo "  It names the fault. If it says the view is missing:"
echo "    fetch('/finance/darpan/api/ledger-repair-view',{method:'POST',"
echo "      headers:{'Content-Type':'application/json'},body:'{}'})"
echo "  Then reload the cash-position page — the three ledgers should move."
echo
echo "  Reverse:  cp -f $BAKD $DAR && cp -f $BAKA $APP && systemctl restart $SVC"
echo "=============================================================="
