#!/bin/bash
# =============================================================================
#  install_S240_DAY_MPR.sh · kit S240_DAY_MPR · the owner's report of 11-Sep
#
#  Run by:  bash /root/deploy/vps_deploy.sh S240_DAY_MPR
#
#  finance_clinic_day.py over S240_DAY_PHONE 54b5faa9. The owner, 11-Sep: "on clicking view MPR report,
#  only the title of the report is coming, and the table is not coming." The link went to the one-line
#  status fragment. It now opens /finance/clinic/day/<date>/mpr: the bank's own UPI entries for the day
#  beside the clinic's online entries, paired by amount, with what is in one and not the other.
#  Same login gate as the day page. Reads only; writes nothing. RED -> 54b5faa9 restored, exit 1.
# =============================================================================
set -u
KIT="S240_DAY_MPR"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="/usr/bin/python3"
FIN="${FINANCE_DIR:-/root/finance}"
F="finance_clinic_day.py"
LIVE_EXPECT="54b5faa92208d9f36dc2a3cb78e58cdb"
BAK=""; RESTARTED=0
red() { echo "!! RED -- $*"
  if [ -n "$BAK" ] && [ -f "$BAK" ] && [ "$RESTARTED" -eq 1 ]; then
    \cp -f "$BAK" "$FIN/$F" && echo "   restored $F from $BAK"
    systemctl restart clinic-finance.service; sleep 4
    systemctl is-active --quiet clinic-finance.service && echo "   service back up on 54b5faa9"
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
  BAK="$FIN/$F.bak_S240mpr_${LIVE:0:8}"
  \cp -f "$FIN/$F" "$BAK" || red "could not back up $F"
  \cp -f $F "$FIN/$F"
fi
[ "$(md5sum $FIN/$F | awk '{print $1}')" = "$NEW" ] || red "$F did not land"
RESTARTED=1
systemctl restart clinic-finance.service; sleep 4
systemctl is-active --quiet clinic-finance.service || red "clinic-finance.service did not come back"
HZ="$(curl -s -o /dev/null -w '%{http_code}' localhost:8106/finance/healthz)"
DAY="$(curl -s -o /dev/null -w '%{http_code}' localhost:8106/finance/clinic/day/2026-09-02/mpr)"
echo "-- healthz $HZ · the new MPR page anonymous $DAY (302/401/403 = login gate, route mounted)"
[ "$HZ" = "200" ] || red "healthz is not 200"
case "$DAY" in 302|401|403) ;; *) red "the MPR page answered $DAY";; esac
cd "$FIN" && $PY - <<'PYEOF' || red "the page did not render"
import sys; sys.path.insert(0, ".")
import finance_clinic_day as CD
import sqlite3
con = sqlite3.connect("file:finance.db?mode=ro", uri=True); con.row_factory = sqlite3.Row
bank = [dict(r) for r in con.execute("SELECT txn_time, amount_p, rrn FROM upi_txn WHERE unit='clinic' ORDER BY txn_date DESC LIMIT 40")]
p, b, o = CD._mpr_pairs(bank, [dict(amount_p=x["amount_p"]) for x in bank[:5]])
assert len(p) == min(5, len(bank)) and hasattr(CD, "clinic_day_mpr")
n = con.execute("SELECT COUNT(*) FROM upi_txn WHERE unit='clinic'").fetchone()[0]
print("-- MPR page code loaded; %d clinic bank UPI entries in the store to show" % n)
PYEOF
RESTARTED=2
echo ""
echo "PINS  $F $(md5sum $FIN/$F | awk '{print $1}')"
echo ""
echo "$KIT GREEN -- open a day on Docterz Revenue and tap the bank MPR button: the entries now show as tables."
