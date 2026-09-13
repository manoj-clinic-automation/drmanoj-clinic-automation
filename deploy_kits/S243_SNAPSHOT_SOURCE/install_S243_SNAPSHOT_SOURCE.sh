#!/bin/bash
# =============================================================================
#  install_S243_SNAPSHOT_SOURCE.sh
#
#  KIT   S243_SNAPSHOT_SOURCE -- the computed stock feed stops overwriting
#        Marg's closing stock in stock_snapshot.
#  RUN   bash /root/deploy/repo/deploy_kits/S243_SNAPSHOT_SOURCE/install_S243_SNAPSHOT_SOURCE.sh
#
#  WHAT CHANGES
#    REPLACE  /root/finance/stock_app.py
#             0b965da40816079a60c49a20946832b3 -> aa6d9cd9afbe5c7a2e44315678f58de3
#    NEW TABLE stock_expected in /root/finance/finance.db (CREATE IF NOT EXISTS,
#             idempotent; the app creates it on first computed push anyway).
#    NO other file. finance_app.py is NOT touched. No URL changes.
#
#  WHAT IT DOES NOT DO
#    It does NOT move the computed rows already sitting in stock_snapshot. It
#    only PRINTS what the migration would do (--dry-run). The move is a separate,
#    explicit line -- see README: migrate_stock_expected_s243.py --apply.
#
#  IT REFUSES unless the box is on the from-pin, restarts the service only after
#  the new file imports cleanly, and puts the old file back (and restarts again)
#  if healthz does not answer 200 within 20 s.
#
#  For a mock run: ROOT=/some/dir (so FIN=$ROOT/root/finance), and a PATH that
#  carries a fake systemctl and curl. No test hook lives in this script.
# =============================================================================
set -u

KIT="S243_SNAPSHOT_SOURCE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-}"
APY="${APP_PY:-/usr/bin/python3}"
FIN="${FINANCE_DIR:-$ROOT/root/finance}"
APP="$FIN/stock_app.py"
DB="$FIN/finance.db"
SVC="${FIN_SVC:-clinic-finance.service}"
HZ_URL="${FIN_HEALTHZ:-http://127.0.0.1:8106/finance/healthz}"
FROM="0b965da40816079a60c49a20946832b3"
TO="aa6d9cd9afbe5c7a2e44315678f58de3"

RESTARTED=0
BAK=""

red() {
  echo "!! RED -- $*"
  if [ -n "$BAK" ] && [ -f "$BAK" ]; then
    \cp -f "$BAK" "$APP"
    echo "   stock_app.py put back from $BAK ($(md5sum "$APP" | awk '{print $1}'))"
    if [ "$RESTARTED" = "1" ]; then
      systemctl restart "$SVC" >/dev/null 2>&1
      sleep 3
      if systemctl is-active --quiet "$SVC"; then
        echo "   the service is up again on the old file"
      else
        echo "   !! the service is NOT active after the rollback -- look at: journalctl -u $SVC -n 50"
      fi
    fi
  fi
  exit 1
}

cd "$KDIR" || red "cannot enter the kit folder"

# -- gates, all from INSIDE this folder ---------------------------------------
md5sum -c SUMS.md5 >/dev/null 2>&1 || red "SUMS.md5 gate failed (run md5sum -c SUMS.md5 here to see which row)"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || red "KIT_ID names a different kit"
NEWSUM="$(md5sum stock_app.py | awk '{print $1}')"
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$NEWSUM" ] || red "KIT_ID does not match stock_app.py (F-88)"
[ "$NEWSUM" = "$TO" ] || red "the payload is $NEWSUM, not the $TO this installer was written for"
[ -x "$APY" ] || red "$APY is not there"
"$APY" -c "import flask" >/dev/null 2>&1 || red "$APY cannot import flask"
[ -f "$APP" ] || red "$APP is not there -- this kit replaces it, it does not create it"
[ -f "$DB" ] || red "$DB is not there"

CUR="$(md5sum "$APP" | awk '{print $1}')"
if [ "$CUR" = "$TO" ]; then
  echo "ALREADY INSTALLED -- $APP is already $TO; nothing to do"
  echo "   (the migration is still a separate line: see README)"
  exit 0
fi
[ "$CUR" = "$FROM" ] || red "$APP is $CUR, expected $FROM. The box is not where this kit was built against -- read the pin and stop. NOTHING changed."
echo "-- gates green; the box is on the from-pin ${FROM:0:8}"
echo "-- predicted after: $TO"

# -- the walk, on THIS box, before anything is copied --------------------------
# base = the live file (just proven to be the from-pin). Run from inside the kit
# folder (python -B, no __pycache__) so the sibling kits' schema files are found
# the way the S226-S240 walks find them; the live folder is the fallback.
FINANCE_DIR="$FIN" "$APY" -B "$KDIR/walk_snapshot_source_s243.py" --base "$APP" --new "$KDIR/stock_app.py" \
  || red "the live-shape walk failed on this box -- nothing was changed"
echo "-- walked on this box with this box's python: green"

# -- the table, first (idempotent) ----------------------------------------------
"$APY" - "$DB" "$KDIR/stock_expected_schema.sql" <<'PYEOF' || red "could not apply stock_expected_schema.sql"
import io, sqlite3, sys
con = sqlite3.connect(sys.argv[1])
con.executescript(io.open(sys.argv[2], encoding="utf-8").read())
con.commit()
n = con.execute("SELECT COUNT(*) FROM stock_expected").fetchone()[0]
print("-- stock_expected table present (%d rows)" % n)
PYEOF

# -- lay the file down: .new -> verify -> .bak -> mv ---------------------------
\cp -f stock_app.py "$APP.new" || red "could not write $APP.new"
[ "$(md5sum "$APP.new" | awk '{print $1}')" = "$TO" ] || { rm -f "$APP.new"; red "$APP.new did not verify"; }
BAK="$APP.bak_S243_${CUR:0:8}"
\cp -f "$APP" "$BAK" || red "could not back up stock_app.py"
mv -f "$APP.new" "$APP" || red "could not move the new file into place"
ACT="$(md5sum "$APP" | awk '{print $1}')"
[ "$ACT" = "$TO" ] || red "stock_app.py did not land ($ACT)"
rm -rf "$FIN/__pycache__" 2>/dev/null

# -- smoke BEFORE the restart ---------------------------------------------------
"$APY" -m py_compile "$APP" || red "py_compile stock_app.py failed"
( cd "$FIN" && "$APY" -B -c "import stock_app" ) || red "import stock_app failed from $FIN -- not restarting"
echo "-- py_compile + import stock_app: green"

# -- restart, then poll healthz up to 20 s -------------------------------------
systemctl restart "$SVC" || red "the service would not restart"
RESTARTED=1
HZ=""
for i in $(seq 1 20); do
  sleep 1
  HZ="$(curl -s -o /dev/null -w '%{http_code}' "$HZ_URL" 2>/dev/null)"
  [ "$HZ" = "200" ] && break
done
[ "$HZ" = "200" ] || red "healthz answered '$HZ', not 200, within 20 s"
systemctl is-active --quiet "$SVC" || red "healthz answered but the service is not active"
RESTARTED=2
echo "-- $SVC restarted; healthz 200 after ${i}s"

# -- what the migration WOULD do (read only) -----------------------------------
echo ""
echo "================ MIGRATION DRY RUN (nothing written) ================"
"$APY" -B "$KDIR/migrate_stock_expected_s243.py" --db "$DB" --dry-run || echo "   (dry run exited non-zero -- read the lines above)"
echo "======================================================================"

echo ""
echo "PINS  stock_app.py predicted $TO"
echo "      stock_app.py actual    $(md5sum "$APP" | awk '{print $1}')"
echo "      was $FROM   backup $BAK"
echo "$KIT GREEN -- from now the computed feed lands in stock_expected; stock_snapshot is Marg's."
echo "NEXT (separate, explicit, after reading the dry run above):"
echo "  $APY $KDIR/migrate_stock_expected_s243.py --db $DB --apply"
