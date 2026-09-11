#!/bin/bash
# =============================================================================
#  install_S240_DAY_PHONE.sh · kit S240_DAY_PHONE · the owner's report of 11-Sep
#
#  Run by:  bash /root/deploy/vps_deploy.sh S240_DAY_PHONE
#
#  finance_clinic_day.py over the S225 MPR line 713bdf3a. ONE change, CSS + a scroll wrapper:
#  on a phone the Docterz Revenue tables were squeezed to the screen width until the day,
#  the bill count and the money printed over each other. Now a table wider than the screen
#  scrolls sideways inside its card, the month table's Day column stays pinned, and the
#  patient column on the day page wraps. Desktop screen and the A4 print are unchanged.
#  RED after the restart -> 713bdf3a restored, service restarted, exit 1.
# =============================================================================
set -u
KIT="S240_DAY_PHONE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="/usr/bin/python3"
FIN="${FINANCE_DIR:-/root/finance}"
F="finance_clinic_day.py"
LIVE_EXPECT="713bdf3a9c1a8dafe076be1feb32219a"
BAK=""; RESTARTED=0
red() { echo "!! RED -- $*"
  if [ -n "$BAK" ] && [ -f "$BAK" ] && [ "$RESTARTED" -eq 1 ]; then
    \cp -f "$BAK" "$FIN/$F" && echo "   restored $F from $BAK"
    systemctl restart clinic-finance.service; sleep 4
    systemctl is-active --quiet clinic-finance.service && echo "   service back up on 713bdf3a"
  fi; exit 1; }

cd "$KDIR" || red "cannot enter the kit folder"
md5sum -c SUMS.md5 >/dev/null 2>&1 || red "SUMS.md5 gate failed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || red "KIT_ID names a different kit"
NEW="$(md5sum $F | awk '{print $1}')"
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$NEW" ] || red "KIT_ID does not match $F (F-88)"
LIVE="$(md5sum $FIN/$F | awk '{print $1}')"
if [ "$LIVE" != "$NEW" ] && [ "$LIVE" != "$LIVE_EXPECT" ]; then
  red "live $F is $LIVE, not $LIVE_EXPECT -- it moved since this kit was built; NOTHING changed"
fi
echo "-- gates green; live $F ${LIVE:0:8}"
$PY -m py_compile $F || red "py_compile"
if [ "$LIVE" != "$NEW" ]; then
  BAK="$FIN/$F.bak_S240day_${LIVE:0:8}"
  \cp -f "$FIN/$F" "$BAK" || red "could not back up $F"
  \cp -f $F "$FIN/$F"
fi
[ "$(md5sum $FIN/$F | awk '{print $1}')" = "$NEW" ] || red "$F did not land"
RESTARTED=1
systemctl restart clinic-finance.service; sleep 4
systemctl is-active --quiet clinic-finance.service || red "clinic-finance.service did not come back"
HZ="$(curl -s -o /dev/null -w '%{http_code}' localhost:8106/finance/healthz)"
DAY="$(curl -s -o /dev/null -w '%{http_code}' localhost:8106/finance/clinic/day)"
echo "-- healthz $HZ · Docterz Revenue page anonymous $DAY (302/401/403 = login gate, route mounted)"
[ "$HZ" = "200" ] || red "healthz is not 200"
case "$DAY" in 302|401|403) ;; *) red "the Docterz Revenue page answered $DAY";; esac
cd "$FIN" && $PY - <<'PYEOF' || red "the page did not render"
import sys; sys.path.insert(0, ".")
import finance_clinic_day as CD
h = CD._shell("t", "<div class='card'><div class='tscroll'><table class='grid month'></table></div></div>")
assert ".tscroll{overflow-x:auto" in h and "max-width:900px" in h and "@page{size:A4 portrait" in h
print("-- page shell renders with the phone rules and the A4 print rules")
PYEOF
RESTARTED=2
echo ""
echo "PINS  $F $(md5sum $FIN/$F | awk '{print $1}')"
echo ""
echo "$KIT GREEN -- open Docterz Revenue on a phone: the table now scrolls sideways, Day pinned."
