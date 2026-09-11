#!/bin/bash
# =============================================================================
#  install_S240_SANJEEVNI.sh · kit S240_SANJEEVNI_123 · Sanjeevni plan items 1, 2, 3
#
#  Run by:  bash /root/deploy/vps_deploy.sh S240_SANJEEVNI_123
#
#  1  export_watch.py   the missed-export check keyed to Amir's punches (cron 23:40 + 10:45)
#  2  spine_cadence.py  the item spine refreshes itself, with a "what changed" report
#                       (cron every 30 min 09-23 if its sources moved, and 23:50 always)
#  3  sale_bill_door.py the sale bill's money row arrives from manojz through the EXISTING
#                       purchase door (/finance/purchase/api/push, type SALE_BILL)
#     purchase_app.py   rev 13 over rev 12 3adad7f9: the SALE_BILL branch + the red line on
#                       the hub (English) and on Amir's salt page (Hinglish). Nothing else.
#
#  Gates: SUMS + KIT_ID -> live pins must be the ones this kit was built on -> a dated copy of
#  finance.db -> every selftest on the box -> place -> restart -> healthz + gate probe.
#  RED after the restart -> purchase_app.py restored, service restarted, exit 1.
#  finance_app.py is NOT touched. No gate change. No existing table altered.
# =============================================================================
set -u
KIT="S240_SANJEEVNI_123"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="/usr/bin/python3"
FIN="${FINANCE_DIR:-/root/finance}"
DB="$FIN/finance.db"
STAMP="$(date +%Y%m%d-%H%M%S)"
PA_LIVE_EXPECT="3adad7f983228ea3bbb5ea635c8ce872"
SB_LIVE_EXPECT="16469968f68ebc6e0a9e23a3bb9001f4"
PA_BAK=""
RESTARTED=0

red() { echo "!! RED -- $*"
  if [ -n "$PA_BAK" ] && [ -f "$PA_BAK" ] && [ "$RESTARTED" -eq 1 ]; then
    \cp -f "$PA_BAK" "$FIN/purchase_app.py" && echo "   restored purchase_app.py from $PA_BAK"
    systemctl restart clinic-finance.service; sleep 4
    systemctl is-active --quiet clinic-finance.service && echo "   service back up on the old purchase_app.py"
  fi
  echo "   (any new file already placed beside it is inert: nothing imports it without rev 13)"; exit 1; }

cd "$KDIR" || red "cannot enter the kit folder"
md5sum -c SUMS.md5 >/dev/null 2>&1 || red "SUMS.md5 gate failed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || red "KIT_ID names a different kit"
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum purchase_app.py | awk '{print $1}')" ] || red "KIT_ID does not match purchase_app.py (F-88)"
echo "-- gates green: SUMS.md5 and KIT_ID.txt"

# ---- the live pins this kit was built on
LIVE_PA="$(md5sum $FIN/purchase_app.py | awk '{print $1}')"
NEW_PA="$(md5sum purchase_app.py | awk '{print $1}')"
if [ "$LIVE_PA" != "$NEW_PA" ] && [ "$LIVE_PA" != "$PA_LIVE_EXPECT" ]; then
  red "live purchase_app.py is $LIVE_PA, not rev 12 $PA_LIVE_EXPECT -- it moved since this kit was built; NOTHING changed"
fi
[ -f "$FIN/sale_bill.py" ] || red "$FIN/sale_bill.py is absent (S237 was expected installed)"
[ "$(md5sum $FIN/sale_bill.py | awk '{print $1}')" = "$SB_LIVE_EXPECT" ] || red "live sale_bill.py is not the S237 copy $SB_LIVE_EXPECT"
[ -f "$FIN/purchase_schema.sql" ] || red "$FIN/purchase_schema.sql missing"
echo "-- live pins as expected: purchase_app.py ${LIVE_PA:0:8} · sale_bill.py ${SB_LIVE_EXPECT:0:8}"

# ---- selftests, on the box, before anything is placed
for t in "sale_bill_door.py --selftest" "export_watch.py --selftest" "marg_spine.py --selftest" "spine_cadence.py --selftest"; do
  OUT="$(cd "$KDIR" && PYTHONPATH="$KDIR:$FIN" $PY -B $t 2>&1)" || red "selftest failed: $t
$OUT"
  echo "-- $(echo "$OUT" | tail -1)"
done
for f in purchase_app.py sale_bill_door.py export_watch.py spine_cadence.py marg_spine.py; do
  $PY -m py_compile "$f" || red "py_compile $f"
done
echo "-- py_compile clean"

# ---- a dated copy of the database first
BK="${BACKUP_DIR:-/root/backups/finance}"; mkdir -p "$BK"
$PY - "$DB" "$BK/finance_preS240_$STAMP.db" <<'PYEOF' || red "database backup failed"
import sqlite3, sys
s = sqlite3.connect(sys.argv[1]); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close()
c = sqlite3.connect(sys.argv[2]); assert c.execute("pragma quick_check").fetchone()[0] == "ok"
print("-- database copied and checked: " + sys.argv[2])
PYEOF

# ---- place (new files beside; purchase_app.py over rev 12 with a backup)
for f in sale_bill_door.py export_watch.py spine_cadence.py marg_spine.py marg_spine_schema.sql; do
  if [ -f "$FIN/$f" ] && ! cmp -s "$f" "$FIN/$f"; then \cp -f "$FIN/$f" "$FIN/$f.bak_S240_$STAMP"; echo "-- kept the previous $f as .bak_S240_$STAMP"; fi
  \cp -f "$f" "$FIN/$f"
  [ "$(md5sum "$FIN/$f" | awk '{print $1}')" = "$(md5sum "$f" | awk '{print $1}')" ] || red "$f did not land"
done
if [ "$LIVE_PA" != "$NEW_PA" ]; then
  PA_BAK="$FIN/purchase_app.py.bak_S240_${LIVE_PA:0:8}"
  \cp -f "$FIN/purchase_app.py" "$PA_BAK" || red "could not back up purchase_app.py"
  \cp -f purchase_app.py "$FIN/purchase_app.py"
fi
[ "$(md5sum $FIN/purchase_app.py | awk '{print $1}')" = "$NEW_PA" ] || red "purchase_app.py did not land"
echo "-- placed and md5-verified: 5 new files + purchase_app.py ${LIVE_PA:0:8} -> ${NEW_PA:0:8}"

# ---- the empty tables, so the freshness legs read NEVER (not ERROR) until the first row
$PY - "$DB" "$FIN" <<'PYEOF' || red "could not create the S240 tables"
import sqlite3, sys
sys.path.insert(0, sys.argv[2])
import sale_bill_door, export_watch, sale_bill
c = sqlite3.connect(sys.argv[1], timeout=30)
c.executescript(sale_bill_door.LEDGER); sale_bill.ensure_schema(c); c.executescript(export_watch.SCHEMA); c.commit()
print("-- tables ready: sale_bill, sale_bill_push, export_watch (created if absent; nothing altered)")
PYEOF

# ---- restart and prove
RESTARTED=1
systemctl restart clinic-finance.service; sleep 4
systemctl is-active --quiet clinic-finance.service || red "clinic-finance.service did not come back"
HZ="$(curl -s -o /dev/null -w '%{http_code}' localhost:8106/finance/healthz)"
PHZ="$(curl -s -o /dev/null -w '%{http_code}' localhost:8106/finance/purchase/api/healthz)"
GATE="$(curl -s -o /dev/null -w '%{http_code}' -X POST -H 'X-Finance-Marg: wrong' -H 'Content-Type: application/json' -d '{"type":"SALE_BILL"}' localhost:8106/finance/purchase/api/push)"
HUB="$(curl -s -o /dev/null -w '%{http_code}' localhost:8106/finance/purchase/page/hub)"
echo "-- healthz $HZ · purchase healthz $PHZ · push with a wrong token $GATE (401 = gate alive) · hub anonymous $HUB (302 = login gate)"
[ "$HZ" = "200" ] && [ "$PHZ" = "200" ] && [ "$GATE" = "401" ] || red "the app did not answer as expected after the restart"
RESTARTED=2

# ---- cron (idempotent; every S240 line carries the tag)
TMPC="$(mktemp)"; crontab -l 2>/dev/null | grep -v '# S240_SANJEEVNI' > "$TMPC"
cat >> "$TMPC" <<'CRON'
*/30 9-23 * * * cd /root/finance && /usr/bin/python3 -B spine_cadence.py --db /root/finance/finance.db --if-changed >> /root/finance/spine_cadence.log 2>&1 # S240_SANJEEVNI
50 23 * * * cd /root/finance && /usr/bin/python3 -B spine_cadence.py --db /root/finance/finance.db --trigger nightly >> /root/finance/spine_cadence.log 2>&1 # S240_SANJEEVNI
40 23 * * * cd /root/finance && /usr/bin/python3 -B export_watch.py --day today >> /root/finance/export_watch.log 2>&1 # S240_SANJEEVNI
45 10 * * * cd /root/finance && /usr/bin/python3 -B export_watch.py --day yesterday --notify >> /root/finance/export_watch.log 2>&1 # S240_SANJEEVNI
CRON
crontab "$TMPC" && rm -f "$TMPC"
echo "-- cron: $(crontab -l | grep -c '# S240_SANJEEVNI') S240 lines"

# ---- freshness: three legs added if absent (backup first)
LEGS="$FIN/freshness_legs.json"
if [ -f "$LEGS" ]; then
  \cp -f "$LEGS" "$LEGS.bak_S240_$STAMP"
  $PY - "$LEGS" "$KDIR/legs_add_s240.json" <<'PYEOF'
import json, sys
p, add = sys.argv[1], json.load(open(sys.argv[2]))["legs"]
d = json.load(open(p)); names = {l.get("name") for l in d["legs"]}
new = [l for l in add if l["name"] not in names]; d["legs"].extend(new)
json.dump(d, open(p, "w"), indent=1, ensure_ascii=False)
print("-- freshness legs: %d added, now %d" % (len(new), len(d["legs"])))
PYEOF
else echo "-- freshness_legs.json not found; legs not added (nothing else depends on them)"; fi

# ---- first spine run, and today's export check (read only)
echo ""
echo "================ ITEM SPINE -- first cadence run ================"
cd "$FIN" && $PY -B spine_cadence.py --db "$DB" --trigger install 2>&1 | tail -8
echo "================ AMIR'S EXPORTS -- today and yesterday (nothing written) ================"
$PY -B export_watch.py --db "$DB" --day yesterday --dry-run 2>&1 | head -1
$PY -B export_watch.py --db "$DB" --day today --dry-run 2>&1 | head -1
echo "=================================================================="
echo ""
echo "PINS  purchase_app.py $(md5sum $FIN/purchase_app.py | awk '{print $1}')"
for f in sale_bill_door.py export_watch.py spine_cadence.py marg_spine.py; do echo "PINS  $f $(md5sum $FIN/$f | awk '{print $1}')"; done
echo ""
echo "$KIT GREEN -- installed, service up, gate proven. Next: the manojz one line sends the sale bills."
