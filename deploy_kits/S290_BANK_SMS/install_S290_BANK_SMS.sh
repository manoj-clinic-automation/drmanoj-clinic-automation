#!/bin/bash
# =============================================================================
#  install_S290_BANK_SMS.sh · kit S290_BANK_SMS (session 265, 17-Sep-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S290_BANK_SMS/install_S290_BANK_SMS.sh
#
#  THE OWNER, 17-Sep-2026: the bank's morning settlement SMS reaches the server from his phone through
#  MacroDroid ("we need our own MacroDroid to make it proper"; the Apps Script log is to be discarded).
#  Proved first on his own log: each SMS on day D equals the MPR total of D-1 to the rupee (23 of 23).
#
#  FILES
#    /root/finance/finance_app.py   ac61df70 (S289) -> 8dc77ef4   PATCHED ON THE BOX (F-185): the phone's door on the
#                                                                  gate's public list + the guarded mount
#    /root/finance/bank_sms.py      NEW
#    /root/finance/bank_sms.key     NEW, 0600, created once here; shown only on the doctors' signed-in page
#  DATA: table bank_sms_settlement, created on first use.
#  Gates: SUMS + KIT_ID -> live pin -> patcher == predicted -> py_compile -> THE WALK ON THIS BOX (29 checks,
#  scratch copy) -> backup -> place -> key -> restart clinic-finance -> health, the door answers 401 without a
#  key, the module mounted. Any red after placing: finance_app.py restored, bank_sms.py moved aside, restart.
# =============================================================================
set -u
KIT="S290_BANK_SMS"; KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"; ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; DBF="${FINANCE_DB:-$FIN/finance.db}"
FA_FROM=ac61df70f80a4a57d8eebd7e997593bd; FA_TO=8dc77ef48c96bec7382f1c8aaf40f38e; BS_TO=3a8f0a8863942cde3fce2d0294a86769
KEYF="${BANK_SMS_KEY_FILE:-$FIN/bank_sms.key}"
STAMP="$(date +%Y%m%d_%H%M%S)"; FA_NEW="/tmp/s290_finance_app_$STAMP.py"; WALK="/tmp/s290_walk_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { echo "!! [1/8] KIT_ID names another kit - nothing installed"; exit 1; }
echo "[1/8] kit gates green"
if [ "$(m5 "$FIN/finance_app.py")" = "$FA_TO" ] && [ "$(m5 "$FIN/bank_sms.py")" = "$BS_TO" ] && [ -s "$KEYF" ]; then
  echo "-- ALREADY INSTALLED (finance_app.py $FA_TO, bank_sms.py $BS_TO, key present)"; exit 0; fi
[ "$(m5 "$FIN/finance_app.py")" = "$FA_FROM" ] || { echo "!! [2/8] finance_app.py is $(m5 "$FIN/finance_app.py"), expected $FA_FROM (S289) - nothing installed"; exit 1; }
[ -e "$FIN/bank_sms.py" ] && { echo "!! [2/8] $FIN/bank_sms.py exists but is not this kit's - nothing installed"; exit 1; }
[ "$(m5 bank_sms.py)" = "$BS_TO" ] || { echo "!! [2/8] kit bank_sms.py not at its pin - nothing installed"; exit 1; }
echo "[2/8] live pin exact"
"$SPY" -B patch_finance_app_s290.py --file "$FIN/finance_app.py" --from "$FA_FROM" --out "$FA_NEW" || { echo "!! [3/8] patcher refused"; rm -f "$FA_NEW"; exit 1; }
[ "$(m5 "$FA_NEW")" = "$FA_TO" ] || { echo "!! [3/8] patched is $(m5 "$FA_NEW"), predicted $FA_TO - nothing installed"; rm -f "$FA_NEW"; exit 1; }
"$SPY" -m py_compile "$FA_NEW" bank_sms.py || { echo "!! [3/8] compile failed"; rm -f "$FA_NEW"; exit 1; }
echo "[3/8] patched finance_app.py == $FA_TO; py_compile green"
mkdir -p "$WALK/app" && cp -p "$FIN"/*.py "$WALK/app/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/app/" 2>/dev/null
cp -p "$FA_NEW" "$WALK/app/finance_app.py"; cp -p bank_sms.py "$WALK/app/bank_sms.py"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" || { echo "!! [4/8] scratch copy failed"; rm -rf "$WALK" "$FA_NEW"; exit 1; }
"$SPY" -c "import secrets; print('-'.join(''.join(secrets.choice('abcdefghjkmnpqrstuvwxyz23456789') for _ in range(4)) for _ in range(5)))" > "$WALK/walk.key"
WOUT="$( cd "$WALK/app" && FINANCE_DB="$WALK/walk.db" FINANCE_ALLOW_HEADER_AUTH=1 BANK_SMS_KEY_FILE="$WALK/walk.key" PETTY_UPLOAD_DIR="$WALK/up" \
         FINANCE_SCAN_DIR="$WALK/scans" FINANCE_SSO_DIR="$ROOT/portal" timeout 170 "$SPY" -B "$KDIR/walk_s290.py" "$WALK/app" 2>&1 | tail -1 )"
echo "$WOUT" | grep -q "^WALK OK" || { echo "!! [4/8] walk red: $WOUT - nothing installed"; rm -rf "$WALK" "$FA_NEW"; exit 1; }
rm -rf "$WALK"; echo "[4/8] $WOUT"
BAK="$FIN/finance_app.py.bak_S290_${FA_FROM:0:8}"
\cp -p "$FIN/finance_app.py" "$BAK" || { echo "!! [5/8] backup failed - nothing placed"; rm -f "$FA_NEW"; exit 1; }
restore() { echo "!! RED after placing - restoring"; \cp -p "$BAK" "$FIN/finance_app.py"; mv -f "$FIN/bank_sms.py" "$FIN/bank_sms.py.removed_S290_$STAMP" 2>/dev/null
  systemctl restart clinic-finance || true; sleep 3; echo "   finance_app.py $(m5 "$FIN/finance_app.py")"; exit 1; }
\cp -p "$FA_NEW" "$FIN/finance_app.py" || restore; rm -f "$FA_NEW"
\cp -p bank_sms.py "$FIN/bank_sms.py" || restore
[ "$(m5 "$FIN/finance_app.py")" = "$FA_TO" ] && [ "$(m5 "$FIN/bank_sms.py")" = "$BS_TO" ] || restore
echo "[5/8] placed; backup $BAK"
if [ ! -s "$KEYF" ]; then
  ( umask 077; "$SPY" -c "import secrets; print('-'.join(''.join(secrets.choice('abcdefghjkmnpqrstuvwxyz23456789') for _ in range(4)) for _ in range(5)))" > "$KEYF" ) || restore
  chmod 600 "$KEYF"; echo "[6/8] key created (not shown here; it is on the doctors' page)"
else
  echo "[6/8] key already present - kept"
fi
systemctl restart clinic-finance || restore; sleep 4
systemctl is-active --quiet clinic-finance || restore
c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' -X POST -d 'text=hello' http://127.0.0.1:8106/finance/api/bank-sms)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/bank-sms)
echo "health : finance $c1 · the door without a key $c2 (401 expected) · the page without a login $c3 (302 expected)"
[ "$c1" = 200 ] && [ "$c2" = 401 ] && [ "$c3" = 302 ] || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "bank_sms NOT mounted" && { echo "!! bank_sms did not mount"; restore; }
echo "[7/8] clinic-finance active, door closed to strangers, module mounted"
md5sum "$FIN/finance_app.py" "$FIN/bank_sms.py"
echo "[8/8] $KIT: DONE"
echo "read next (on your phone, signed in): https://followup.dr-manoj.in/finance/bank-sms"
