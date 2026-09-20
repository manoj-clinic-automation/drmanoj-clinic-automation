#!/bin/bash
# =============================================================================
#  install_S339_RECORDS_TILE.sh · kit S339_RECORDS_TILE (session 273, 20-Sep-2026)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S339_RECORDS_TILE/install_S339_RECORDS_TILE.sh
#
#  THE OWNER, 20-Sep-2026: "do these two small items first".
#   1. the portal tile 'Patient records' (/finance/records), section Clinic, roles ['doctor'] -- the owner
#      and Dr Bhawna by role; no grant by name; tile_grants.json untouched.
#   2. the read-only Drive proof S335's installer printed wrongly: the venv's Google library writes a
#      warning to stderr, and S335 merged stderr into what it read (2>&1). Here stderr is kept apart.
#
#  FILES:  /root/portal/portal.py   4085b767 (S329) -> (TO below), two additive anchored edits
#  CHECKS: /root/finance/records.py dcb49d8c, records_drive.py 83a7171f (S335) -- read, not changed
# =============================================================================
set -u
KIT="S339_RECORDS_TILE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"
DBF="${FINANCE_DB:-$FIN/finance.db}"
PO_FROM=4085b76781696f80f64283aa1eef57bb
PO_TO=b7b0e43ccb4d6b012b38b9016f3f6f0c
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 portal.py)" = "$PO_TO" ] || { say "!! [1/6] kit portal.py is not its pin - nothing installed"; exit 1; }
"$SPY" -B patch_portal_s339.py --file "$POR/portal.py" --from "$PO_FROM" --out /tmp/s339_portal.py >/dev/null 2>&1
if [ "$(m5 "$POR/portal.py")" = "$PO_TO" ]; then say "-- ALREADY INSTALLED (portal.py $PO_TO)"; SKIP=1
else
  SKIP=0
  [ "$(m5 "$POR/portal.py")" = "$PO_FROM" ] || { say "!! [2/6] portal.py is $(m5 "$POR/portal.py"), not S329 - nothing installed"; exit 1; }
  [ "$(m5 /tmp/s339_portal.py)" = "$PO_TO" ] || { say "!! [2/6] rebuilding from the live bytes did not give the kit's file - nothing installed"; exit 1; }
fi
rm -f /tmp/s339_portal.py
say "[1/6] kit gates green · [2/6] live pin exact, and the live bytes + patch give exactly the kit's file"
if [ "$SKIP" = 0 ]; then
  "$VPY" -m py_compile portal.py || { say "!! [3/6] compile failed - nothing installed"; exit 1; }
  say "[3/6] py_compile green"
  BAK="$POR/portal.py.bak_S339_4085b767"
  \cp -p "$POR/portal.py" "$BAK" || { say "!! [4/6] backup failed - nothing placed"; exit 1; }
  restore() { say "!! RED after placing - restoring byte-identically"; \cp -p "$BAK" "$POR/portal.py"; systemctl restart clinic-portal || true; sleep 3; say "   $POR/portal.py $(m5 "$POR/portal.py")"; exit 1; }
  \cp -p portal.py "$POR/portal.py" && [ "$(m5 "$POR/portal.py")" = "$PO_TO" ] || restore
  say "[4/6] placed; backup $BAK"
  systemctl restart clinic-portal || restore
  sleep 4
  systemctl is-active --quiet clinic-portal || restore
  c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8099/portal)
  say "[5/6] clinic-portal active · /portal answers $c3 (200 or 302 expected)"
  { [ "$c3" = 200 ] || [ "$c3" = 302 ]; } || restore
fi
XT="$("$SPY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); r=c.execute(\"SELECT value FROM record_setting WHERE key='xray_test_id'\").fetchone(); print(r[0] if r else '')" "$DBF" 2>/dev/null)"
RF="$("$SPY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); r=c.execute(\"SELECT drive_id FROM record_file WHERE drive_id<>'' ORDER BY id DESC LIMIT 1\").fetchone(); print(r[0] if r else '')" "$DBF" 2>/dev/null)"
N="$("$VPY" -B "$FIN/records_drive.py" list "$XT" 2>/dev/null | "$SPY" -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null)"
H="$("$VPY" -B "$FIN/records_drive.py" media "$RF" 2>/dev/null | head -c 5)"
say "[6/6] Drive proof (read-only): X-ray test folder ${N:-NOT READ} file(s) · one filed report starts with ${H:-NOT READ}"
md5sum "$POR/portal.py" "$FIN/records.py" "$FIN/records_drive.py"
say "$KIT: DONE"
