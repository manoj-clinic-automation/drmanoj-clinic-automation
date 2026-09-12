#!/bin/bash
# =============================================================================
#  install_S241_AMIR_SALTS.sh
#
#  KIT   S241_AMIR_SALTS -- the salt list as a sheet Amir can carry:
#        download, copy the exact names into Marg, upload the same file back.
#  RUN   bash /root/deploy/vps_deploy.sh S241_AMIR_SALTS
#
#  WHAT CHANGES
#    NEW      /root/finance/amir_salts.py
#    REPLACE  /root/finance/amir_day.py  (step 6 now opens the sheet; the salt
#             page rides on the SAME mount, so finance_app.py is NOT touched)
#    DB       one new table, lazily: amir_salt_upload.  Ticks are written into
#             purchase_salt_task -- the same table his existing salts page
#             ticks -- so the two can never disagree.
#
#  IT NEEDS padwriter.py and padreader.py already beside the finance app.
#  They are the stock pad's own stdlib writer/reader. This kit does NOT ship
#  or overwrite them; if they are not there it goes RED and changes nothing.
# =============================================================================
set -u

KIT="S241_AMIR_SALTS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APP_PY:-/usr/bin/python3}"
FIN="${FINANCE_DIR:-/root/finance}"
DB="$FIN/finance.db"
FA="$FIN/finance_app.py"
SVC="${FIN_SVC:-clinic-finance.service}"
PORT="${FIN_PORT:-8106}"

RESTARTED=0
DAY_BAK=""
SALT_EXISTED=0

red() {
  if [ "$RESTARTED" = "1" ]; then
    if [ -n "$DAY_BAK" ] && [ -f "$DAY_BAK" ]; then
      \cp -f "$DAY_BAK" "$FIN/amir_day.py"
      echo "   amir_day.py put back"
    fi
    if [ "$SALT_EXISTED" = "0" ] && [ -f "$FIN/amir_salts.py" ]; then
      rm -f "$FIN/amir_salts.py"
      echo "   amir_salts.py removed again"
    fi
    systemctl restart "$SVC" >/dev/null 2>&1
    echo "   the service is up again"
  fi
  echo "!! RED -- $*"
  exit 1
}

cd "$KDIR" || red "cannot enter the kit folder"

md5sum -c SUMS.md5 >/dev/null 2>&1 || red "SUMS.md5 gate failed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || red "KIT_ID names a different kit"
NEWSUM="$(md5sum amir_salts.py | awk '{print $1}')"
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$NEWSUM" ] || red "KIT_ID does not match amir_salts.py (F-88)"

[ -x "$APY" ] || red "$APY is not there"
[ -f "$FA" ]  || red "$FA is not there"
[ -f "$DB" ]  || red "$DB is not there"
[ -f "$FIN/amir_day.py" ] || red "S241_AMIR_DAY is not installed -- install it first"
[ -f "$FIN/padwriter.py" ] || red "padwriter.py is not beside the finance app; this kit writes the sheet with it and will not guess a substitute"
[ -f "$FIN/padreader.py" ] || red "padreader.py is not beside the finance app; this kit reads the sheet back with it"
"$APY" -c "import flask" >/dev/null 2>&1 || red "$APY cannot import flask"
[ -f "$FIN/amir_salts.py" ] && SALT_EXISTED=1
echo "-- gates green; padwriter and padreader are both in $FIN"

# -- both walks, on this box, before anything is copied ----------------------
W="$(mktemp -d)"
\cp -f amir_day.py amir_salts.py selftest_amir_day.py selftest_amir_salts.py "$W"/
\cp -f "$FIN/padwriter.py" "$FIN/padreader.py" "$W"/
( cd "$W" && "$APY" selftest_amir_day.py ) || { rm -rf "$W"; red "the seven-step walk failed on this box -- nothing was changed"; }
( cd "$W" && "$APY" selftest_amir_salts.py ) || { rm -rf "$W"; red "the salt-sheet round trip failed on this box -- nothing was changed"; }
rm -rf "$W"
echo "-- walked on this box against THIS box's padwriter/padreader: both green"

# -- lay the files down ------------------------------------------------------
OLD8="$(md5sum "$FIN/amir_day.py" | awk '{print $1}' | cut -c1-8)"
DAY_BAK="$FIN/amir_day.py.bak_S241salts_$OLD8"
\cp -f "$FIN/amir_day.py" "$DAY_BAK"
\cp -f amir_day.py "$FIN/amir_day.py"
\cp -f amir_salts.py "$FIN/amir_salts.py"
"$APY" -m py_compile "$FIN/amir_day.py" || red "py_compile amir_day.py"
"$APY" -m py_compile "$FIN/amir_salts.py" || red "py_compile amir_salts.py"
rm -rf "$FIN/__pycache__" 2>/dev/null

BK="$FIN/finance.db.bak_${KIT}_$(date +%Y%m%d_%H%M%S)"
"$APY" - "$DB" "$BK" <<'PYBK' || red "could not back the database up"
import sqlite3, sys
a = sqlite3.connect(sys.argv[1]); b = sqlite3.connect(sys.argv[2])
with b:
    a.backup(b)
a.close(); b.close()
PYBK
echo "-- books backed up to $BK"

OUT="$("$APY" patch_finance_app_S241_amir.py 2>&1)" || { echo "$OUT" | sed 's/^/   /'; red "the mount check refused"; }
echo "$OUT" | sed 's/^/   /'

systemctl restart "$SVC" || red "the service would not restart"
RESTARTED=1
sleep 4
systemctl is-active --quiet "$SVC" || red "the service is not active after the restart"

HZ="$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:$PORT/finance/healthz")"
[ "$HZ" = "200" ] || red "healthz answered $HZ, not 200"
for P in /finance/amir /finance/amir/salts /finance/amir/salts.xlsx; do
  CODE="$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:$PORT$P")"
  case "$CODE" in
    302|303) echo "-- $P anonymous $CODE (login gate, route mounted)" ;;
    *) red "$P answered $CODE; 302 was expected" ;;
  esac
done

echo "-- how much work the sheet will carry today:"
"$APY" - "$DB" <<'PYN' || true
import sqlite3, sys
cx = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
try:
    for sec, n in cx.execute(
        "SELECT section, COUNT(*) FROM purchase_salt_task "
        "WHERE COALESCE(done,0)=0 GROUP BY section ORDER BY section"):
        print("     %-10s %d still open" % (sec, n))
except Exception as e:
    print("     (could not read purchase_salt_task: %s)" % e)
cx.close()
PYN

RESTARTED=2
echo ""
echo "PINS  amir_salts.py $NEWSUM"
echo "PINS  amir_day.py   $(md5sum "$FIN/amir_day.py" | awk '{print $1}')"
echo "$KIT GREEN -- the salt sheet is live. Amir opens it at step 6, or directly:"
echo "https://followup.dr-manoj.in/finance/amir/salts"
