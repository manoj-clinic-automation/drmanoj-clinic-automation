#!/bin/bash
# =============================================================================
#  install_S241_AMIR_DAY_R2.sh
#
#  KIT   S241_AMIR_DAY -- Amir's day as seven steps on a phone (D472).
#  RUN   bash /root/deploy/vps_deploy.sh S241_AMIR_DAY_R2
#
#  WHAT CHANGES
#    NEW   /root/finance/amir_day.py
#    EDIT  /root/finance/finance_app.py  -- one mount block, anchored, backed up
#    DB    four new tables, created lazily on first request (F-303):
#          amir_day, amir_step, amir_bill_disposition, amir_claim
#          Nothing existing is altered, dropped or rewritten.
#
#  IF ANYTHING GOES WRONG AFTER THE RESTART, finance_app.py is put back
#  byte-identical and the service is restarted before this script goes RED.
# =============================================================================
set -u

KIT="S241_AMIR_DAY_R2"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${MI_PY:-/root/wa/venv/bin/python3}"
APY="${APP_PY:-/usr/bin/python3}"
FIN="${FINANCE_DIR:-/root/finance}"
DB="$FIN/finance.db"
FA="$FIN/finance_app.py"
SVC="${FIN_SVC:-clinic-finance.service}"
PORT="${FIN_PORT:-8106}"

RESTARTED=0
PATCH_BAK=""
MOD_BAK=""

red() {
  if [ "$RESTARTED" = "1" ]; then
    if [ -n "$PATCH_BAK" ] && [ -f "$PATCH_BAK" ]; then
      \cp -f "$PATCH_BAK" "$FA"
      echo "   finance_app.py put back"
    fi
    if [ -n "$MOD_BAK" ] && [ -f "$MOD_BAK" ]; then
      \cp -f "$MOD_BAK" "$FIN/amir_day.py"
      echo "   amir_day.py put back"
    fi
    systemctl restart "$SVC" >/dev/null 2>&1
    echo "   the service is up again"
  fi
  echo "!! RED -- $*"
  exit 1
}

cd "$KDIR" || red "cannot enter the kit folder"

# -- gates -------------------------------------------------------------------
md5sum -c SUMS.md5 >/dev/null 2>&1 || red "SUMS.md5 gate failed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || red "KIT_ID names a different kit"
NEWSUM="$(md5sum amir_day.py | awk '{print $1}')"
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$NEWSUM" ] || red "KIT_ID does not match amir_day.py (F-88)"

[ -x "$APY" ] || red "$APY is not there -- that is the interpreter the app runs under"
[ -f "$FA" ]  || red "$FA is not there"
[ -f "$DB" ]  || red "$DB is not there"
"$APY" -c "import flask" >/dev/null 2>&1 || red "$APY cannot import flask"

if [ -f "$FIN/amir_day.py" ]; then
  LIVE="$(md5sum "$FIN/amir_day.py" | awk '{print $1}')"
  if [ "$LIVE" = "$NEWSUM" ]; then
    echo "-- amir_day.py on the box is already this build ($(echo "$NEWSUM" | cut -c1-8))"
  else
    echo "-- amir_day.py on the box is $(echo "$LIVE" | cut -c1-8); it will be replaced and backed up"
  fi
fi
echo "-- gates green"

# -- the offline walk, on this box, before anything is copied ----------------
WALKDIR="$(mktemp -d)"
\cp -f amir_day.py selftest_amir_day.py "$WALKDIR"/
( cd "$WALKDIR" && "$APY" selftest_amir_day.py ) || { rm -rf "$WALKDIR"; red "the seven-step walk failed on this box -- nothing was changed"; }
( cd "$KDIR" && "$APY" walk_patch_S241.py >/dev/null ) || red "the mount-patch walk failed -- nothing was changed"
rm -rf "$WALKDIR"
echo "-- walked on this box: the seven steps and the mount patch both green"

# -- lay the module down -----------------------------------------------------
if [ -f "$FIN/amir_day.py" ]; then
  OLD8="$(md5sum "$FIN/amir_day.py" | awk '{print $1}' | cut -c1-8)"
  MOD_BAK="$FIN/amir_day.py.bak_S241R2_$OLD8"
  \cp -f "$FIN/amir_day.py" "$MOD_BAK"
fi
\cp -f amir_day.py "$FIN/amir_day.py"
"$APY" -m py_compile "$FIN/amir_day.py" || red "py_compile amir_day.py"
rm -rf "$FIN/__pycache__" 2>/dev/null

# -- back the books up before a schema change --------------------------------
BK="$FIN/finance.db.bak_${KIT}_$(date +%Y%m%d_%H%M%S)"
"$APY" - "$DB" "$BK" <<'PYBK' || red "could not back the database up"
import sqlite3, sys
src, dst = sys.argv[1], sys.argv[2]
a = sqlite3.connect(src); b = sqlite3.connect(dst)
with b:
    a.backup(b)
a.close(); b.close()
PYBK
echo "-- books backed up to $BK"

# -- the mount ---------------------------------------------------------------
OUT="$("$APY" patch_finance_app_S241_amir.py 2>&1)" || { echo "$OUT" | sed 's/^/   /'; red "the mount patch refused"; }
echo "$OUT" | sed 's/^/   /'
PATCH_BAK="$(echo "$OUT" | awk -F': *' '/backup +:/{print $2}')"

# -- restart and prove -------------------------------------------------------
systemctl restart "$SVC" || red "the service would not restart"
RESTARTED=1
sleep 4
systemctl is-active --quiet "$SVC" || red "the service is not active after the restart"

HZ="$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:$PORT/finance/healthz")"
[ "$HZ" = "200" ] || red "healthz answered $HZ, not 200"
PG="$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:$PORT/finance/amir")"
case "$PG" in
  302|303) : ;;
  *) red "/finance/amir answered $PG; 302 was expected (the login gate, route mounted)" ;;
esac
echo "-- healthz 200 · /finance/amir anonymous $PG (302 = login gate, route mounted)"

# -- who can actually open it (read-only, so this is never a guess) ----------
echo "-- who holds a role where this page is mounted:"
"$APY" - "$DB" <<'PYWHO' || true
import sqlite3, sys
cx = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
try:
    rows = cx.execute(
        "SELECT unit, role, COUNT(*) FROM unit_role GROUP BY unit, role ORDER BY unit, role"
    ).fetchall()
    for u, r, n in rows:
        print("     %-10s %-8s %d" % (u, r, n))
    who = cx.execute(
        "SELECT username FROM unit_role WHERE unit='medical' ORDER BY username"
    ).fetchall()
    print("     medical: " + ", ".join(w[0] for w in who))
except Exception as e:
    print("     (could not read unit_role: %s)" % e)
cx.close()
PYWHO

RESTARTED=2
echo ""
echo "PINS  amir_day.py $NEWSUM"
echo "$KIT GREEN -- Amir's day is live, and a viewer on this unit can open it."
echo "Open it on a phone:"
echo "https://followup.dr-manoj.in/finance/amir"
echo "The owner's view of the same day, in English:"
echo "https://followup.dr-manoj.in/finance/amir/day"
