#!/bin/bash
# =============================================================================
#  install_S242_REGISTER_TODAY.sh
#
#  KIT   S242_REGISTER_TODAY -- the daily register opens on TODAY, not on the
#        newest day Docterz happens to have sent.
#  RUN   bash /root/deploy/vps_deploy.sh S242_REGISTER_TODAY
#
#  WHAT CHANGES
#    REPLACE  /root/finance/clinic_register.py
#             93a31e68234df066776b7b80ef65ffbd -> c6b87682ccbfb03734a39ad33c26f2a3
#    NO database change. NO new table. NO other file. finance_app.py is NOT
#    touched -- the blueprint mount is unchanged.
#
#  IT REFUSES unless the box is on the from-pin, and it puts the old file back
#  if the service does not come up on the new one.
# =============================================================================
set -u

KIT="S242_REGISTER_TODAY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APP_PY:-/usr/bin/python3}"
FIN="${FINANCE_DIR:-/root/finance}"
REG="$FIN/clinic_register.py"
SVC="${FIN_SVC:-clinic-finance.service}"
PORT="${FIN_PORT:-8106}"
FROM="93a31e68234df066776b7b80ef65ffbd"
TO="c6b87682ccbfb03734a39ad33c26f2a3"

RESTARTED=0
BAK=""

red() {
  if [ -n "$BAK" ] && [ -f "$BAK" ]; then
    \cp -f "$BAK" "$REG"
    echo "   clinic_register.py put back from $BAK"
    if [ "$RESTARTED" = "1" ]; then
      systemctl restart "$SVC" >/dev/null 2>&1
      echo "   the service is up again on the old file"
    fi
  fi
  echo "!! RED -- $*"
  exit 1
}

cd "$KDIR" || red "cannot enter the kit folder"

# -- gates, all from INSIDE this folder --------------------------------------
md5sum -c SUMS.md5 >/dev/null 2>&1 || red "SUMS.md5 gate failed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || red "KIT_ID names a different kit"
NEWSUM="$(md5sum clinic_register.py | awk '{print $1}')"
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$NEWSUM" ] || red "KIT_ID does not match clinic_register.py (F-88)"
[ "$NEWSUM" = "$TO" ] || red "the payload is $NEWSUM, not the $TO this installer was written for"

[ -x "$APY" ] || red "$APY is not there"
[ -f "$REG" ] || red "$REG is not there -- this kit replaces it, it does not create it"
"$APY" -c "import flask" >/dev/null 2>&1 || red "$APY cannot import flask"

CUR="$(md5sum "$REG" | awk '{print $1}')"
if [ "$CUR" = "$TO" ]; then
  echo "ALREADY INSTALLED -- $REG is already $TO; nothing to do"
  exit 0
fi
[ "$CUR" = "$FROM" ] || red "$REG is $CUR, expected $FROM. The box is not where this kit was built against -- read the pin and stop."
echo "-- gates green; the box is on the from-pin $FROM"

# -- the walk, on THIS box, before anything is copied ------------------------
W="$(mktemp -d)"
\cp -f clinic_register.py walk_register_today_s242.py "$W"/
( cd "$W" && "$APY" -B walk_register_today_s242.py ) || { rm -rf "$W"; red "the register walk failed on this box -- nothing was changed"; }
rm -rf "$W"
echo "-- walked on this box with this box's python: green"

# -- lay the file down -------------------------------------------------------
BAK="$REG.bak_${KIT}_$(date +%Y%m%d_%H%M%S)"
\cp -f "$REG" "$BAK"
\cp -f clinic_register.py "$REG"
"$APY" -m py_compile "$REG" || red "py_compile clinic_register.py"
rm -rf "$FIN/__pycache__" 2>/dev/null

systemctl restart "$SVC" || red "the service would not restart"
RESTARTED=1
sleep 4
systemctl is-active --quiet "$SVC" || red "the service is not active after the restart"

HZ="$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:$PORT/finance/healthz")"
[ "$HZ" = "200" ] || red "healthz answered $HZ, not 200"
for P in /finance/clinic/register /finance/clinic/register/list; do
  CODE="$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:$PORT$P")"
  case "$CODE" in
    302|303) echo "-- $P anonymous $CODE (login gate, route mounted)" ;;
    *) red "$P answered $CODE; 302 was expected" ;;
  esac
done

RESTARTED=2
echo ""
echo "PINS  clinic_register.py $(md5sum "$REG" | awk '{print $1}')"
echo "      was $FROM   backup $BAK"
echo "$KIT GREEN -- the register now opens on today:"
echo "https://followup.dr-manoj.in/finance/clinic/register"
