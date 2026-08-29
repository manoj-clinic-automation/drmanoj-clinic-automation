#!/bin/bash
# =============================================================================
#  install_bankmatch.sh · kit S208_BANKMATCH — Sprint 1 on the clinic server
#
#  WHAT THIS FIXES
#      The bank parser has been reading every settled transaction -- amount,
#      RRN, mode, time -- and keeping only the daily total. That one line is
#      why no page could ever show WHICH payment was WHICH bill, and why the
#      UPI difference could never be explained, only stared at. From today the
#      detail is kept, the history is rebuilt from the statement files already
#      stored on this server, and a matcher ties every settled payment to its
#      sale bill each morning.
#
#  WHAT CHANGES ON THIS SERVER
#      finance_upi.py    FULL-FILE replacement (v2). Adds the upi_txn store and
#                        the backfill; reconciliation now compares the bank's
#                        all-modes settled against the day's whole non-cash --
#                        like for like -- instead of UPI-only, which made a
#                        phantom difference the day a card was ever swiped.
#      bank_match.py     NEW. The 09:45 + every-15-min matcher. Writes
#                        upi_match / upi_match_day. Cron installed here.
#      orthotics.vocab   seeded (only if empty) from Marg's own orthopaedic
#                        category -- 31 keywords covering all 81 items -- so
#                        the dead orthotics card has data to stand on.
#      finance.db        two new tables. NOTHING EXISTING ALTERED OR DROPPED.
#
#  GATES, in order -- any red restores the old file and restarts:
#      kit SUMS -> live-file currency md5 -> backup -> copy -> py_compile ->
#      matcher selftest (21) -> finance_upi selftest (9 + db checks) ->
#      the app's own smoke suite must not lose a single check -> restart ->
#      import check -> backfill -> first match -> cron.
# =============================================================================
set -u
KIT_NAME="S208_BANKMATCH"
FIN=/root/finance
UPI="$FIN/finance_upi.py"
PY=/usr/bin/python3
SVC=clinic-finance.service
DB="$FIN/finance.db"
UPI_DIR="${FINANCE_UPI_DIR:-$FIN/upi_statements}"
UPI_MD5_EXPECTED=3f5016f0c64f12b91ab55c18252705c1
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "=============================================================="
echo "  $KIT_NAME — keep the bank detail, match it every morning"
echo "=============================================================="

# ---------------------------------------------------------------- [1] preflight
for c in md5sum awk cp date systemctl sqlite3 crontab; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! [1/9] '$c' missing — refusing"; exit 1; }
done
[ -f "$UPI" ] || { echo "!! [1/9] $UPI not found — refusing"; exit 1; }
[ -f "$DB" ]  || { echo "!! [1/9] $DB not found — refusing"; exit 1; }
"$PY" -c "import openpyxl" 2>/dev/null || { echo "!! [1/9] openpyxl not importable — refusing"; exit 1; }
echo "[1/9] preflight ok"

# ---------------------------------------------------------------- [2] kit gate
cd "$HERE" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [2/9] kit SUMS mismatch — refusing"; exit 1; }
echo "[2/9] kit integrity ok"

# ---------------------------------------------------------------- [3] currency
LIVE="$(md5sum "$UPI" | awk '{print $1}')"
if [ "$LIVE" != "$UPI_MD5_EXPECTED" ]; then
  echo "!! [3/9] LIVE-FILE CURRENCY GATE — refusing. finance_upi.py is $LIVE,"
  echo "   this kit was built against $UPI_MD5_EXPECTED. The file has moved"
  echo "   since the kit was cut. NOTHING WAS WRITTEN — tell Claude the md5."
  exit 1
fi
echo "[3/9] live-file currency ok"

# ---------------------------------------------------------------- [4] baseline
echo "[4/9] measuring the CURRENT smoke suite before touching anything"
BASE_OUT="$(cd "$FIN" && "$PY" finance_app.py --selftest 2>&1)"
BASE_N="$(echo "$BASE_OUT" | grep -oE 'SMOKE [0-9]+' | head -1 | awk '{print $2}')"
[ -n "${BASE_N:-}" ] || { echo "!! [4/9] could not read a baseline SMOKE count — refusing"
                          echo "$BASE_OUT" | tail -5; exit 1; }
echo "      baseline: SMOKE $BASE_N"

# ---------------------------------------------------------------- [5] backup+copy
STAMP="$(date +%Y%m%d_%H%M%S)"
BAK="${UPI}.bak_${KIT_NAME}_${STAMP}"
cp -f "$UPI" "$BAK" || { echo "!! [5/9] backup failed — refusing"; exit 1; }
echo "[5/9] backup: $BAK"

restore(){
  cp -f "$BAK" "$UPI"
  systemctl restart "$SVC" >/dev/null 2>&1
  echo "   RESTORED finance_upi.py and restarted $SVC. New files remain in"
  echo "   $FIN but nothing calls them; the upi_txn table, if created, is"
  echo "   harmless and empty of meaning until this kit is installed."
}

for f in finance_upi.py bank_match.py selftest_bankmatch.py; do
  cp -f "$HERE/$f" "$FIN/$f" || { echo "!! [5/9] copy of $f failed"; restore; exit 1; }
  A="$(md5sum "$HERE/$f" | awk '{print $1}')"; B="$(md5sum "$FIN/$f" | awk '{print $1}')"
  [ "$A" = "$B" ] || { echo "!! [5/9] $f did not land intact"; restore; exit 1; }
done
echo "      three files copied and verified byte for byte"

# ---------------------------------------------------------------- [6] prove
"$PY" -m py_compile "$FIN/finance_upi.py" "$FIN/bank_match.py" || {
  echo "!! [6/9] does not compile — restoring"; restore; exit 1; }

OUT="$(cd "$FIN" && "$PY" selftest_bankmatch.py 2>&1)"
echo "$OUT" | grep -qE "^21 passed, 0 failed" || {
  echo "!! [6/9] matcher selftest did not report 21 passed — restoring"
  echo "$OUT" | grep -E "FAIL|passed" | tail -6; restore; exit 1; }
echo "[6/9] matcher selftest 21/21 ✓"

OUT="$(cd "$FIN" && "$PY" finance_upi.py 2>&1)"
echo "$OUT" | grep -qE "UPI [0-9]+/[0-9]+ passed" && ! echo "$OUT" | grep -q "FAIL:" || {
  echo "!!      finance_upi selftest failed — restoring"
  echo "$OUT" | tail -6; restore; exit 1; }
echo "      finance_upi selftest ✓  ($(echo "$OUT" | grep -oE 'UPI [0-9]+/[0-9]+ passed'))"

OUT="$(cd "$FIN" && "$PY" finance_app.py --selftest 2>&1)"
N="$(echo "$OUT" | grep -oE 'SMOKE [0-9]+' | head -1 | awk '{print $2}')"
if [ -z "${N:-}" ] || [ "$N" -lt "$BASE_N" ] || echo "$OUT" | grep -q "  FAIL:"; then
  echo "!!      the smoke suite went from $BASE_N to ${N:-?} — restoring"
  echo "$OUT" | grep "FAIL" | head -6; restore; exit 1; fi
echo "      existing smoke suite $N (was $BASE_N) ✓  nothing lost"

# ---------------------------------------------------------------- [7] restart
systemctl restart "$SVC" || { echo "!! [7/9] restart failed — restoring"; restore; exit 1; }
sleep 3
systemctl is-active --quiet "$SVC" || { echo "!! [7/9] $SVC not active — restoring"
                                        restore; exit 1; }
IMP="$(cd "$FIN" && "$PY" - <<'PYEOF' 2>&1 | tail -1
try:
    import finance_app
    print("YES")
except Exception as e:                                         # noqa: BLE001
    print("IMPORT_FAILED %s: %s" % (e.__class__.__name__, e))
PYEOF
)"
[ "$IMP" = "YES" ] || { echo "!! [7/9] the app no longer imports: $IMP — restoring"
                        restore; exit 1; }
echo "[7/9] $SVC restarted, app imports ✓"

# ---------------------------------------------------------------- [8] data
echo "[8/9] backfilling the transaction detail from the stored statements"
( cd "$FIN" && FINANCE_DB="$DB" FINANCE_UPI_DIR="$UPI_DIR" "$PY" finance_upi.py --backfill )

echo "      seeding orthotics.vocab (only if empty)"
VOCAB="$(cat "$HERE/ortho_vocab.txt")"
HAVE="$(sqlite3 "$DB" "SELECT COALESCE(value,'') FROM setting WHERE key='orthotics.vocab'" 2>/dev/null || true)"
if [ -z "$HAVE" ]; then
  sqlite3 "$DB" "INSERT OR REPLACE INTO setting (key, value) VALUES ('orthotics.vocab', '$VOCAB')"
  echo "      seeded: 31 keywords, from Marg's own orthopaedic category"
else
  echo "      already set — left exactly as it is"
fi

echo "      first match, yesterday:"
( cd "$FIN" && FINANCE_DB="$DB" "$PY" bank_match.py --final ) || true

# ---------------------------------------------------------------- [9] cron
MARK="# S208_BANKMATCH"
( crontab -l 2>/dev/null | grep -v "$MARK" ;
  echo "45 9 * * * cd $FIN && FINANCE_DB=$DB $PY bank_match.py >> $FIN/bank_match.log 2>&1 $MARK" ;
  echo "0,15,30,45 10-11 * * * cd $FIN && FINANCE_DB=$DB $PY bank_match.py >> $FIN/bank_match.log 2>&1 $MARK" ;
  echo "0 12 * * * cd $FIN && FINANCE_DB=$DB $PY bank_match.py --final >> $FIN/bank_match.log 2>&1 $MARK" ) | crontab -
echo "[9/9] cron installed: 09:45, every 15 min to 11:45, closing attempt 12:00."
echo "      Every run appends to $FIN/bank_match.log — evidence, not a console."

echo
echo "=============================================================="
echo "  GREEN. The bank detail is kept, the history is loaded, and the"
echo "  matcher runs tomorrow at 09:45."
echo
echo "  See a day now:   sqlite3 $DB \"SELECT * FROM upi_match_day;\""
echo "  A day's list:    sqlite3 $DB \"SELECT status,bill_no,txn_amount_p,rrn"
echo "                   FROM upi_match WHERE business_date='2026-08-27';\""
echo
echo "  Reverse:  cp -f $BAK $UPI && systemctl restart $SVC"
echo "            (and: crontab -e, delete the three $MARK lines)"
echo "=============================================================="
