#!/bin/bash
# =============================================================================
#  install_S316_SHEETS_SEEDED.sh · kit S316_SHEETS_SEEDED (session 269, 18-Sep-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S316_SHEETS_SEEDED/install_S316_SHEETS_SEEDED.sh
#
#  THE OWNER, 18-Sep, on the S315 page: "the form you made me fill is not the proper one -- extract
#  the x-rays from the excel sheet, remove the X-ray part from the item name, do your own spelling
#  corrections, make a list ... I will only edit those or approve those or reject those or maybe add
#  some. Similarly for procedures, I shared a list with you previously. No backfill."
#   A  owner_sheets.py 2520564c -> PREDICTED BELOW: both lists arrive already written; each line waits
#      for approve / reject / a corrected name; a price is optional; past amounts are a pricing hint only.
#   B  xray_seed.json  NEW — the S223 extraction of the clinic's own X-RAY DETAIL REGISTER (6,177
#      entries, 1,197 typed forms -> 19 studies, spellings corrected, PROSISER removed as a procedure).
#   C  proc_seed.json  NEW — his own rulings of 04-Sep (11 cast/slab sites, 5 ILI sites, dressing) with
#      the consumables exactly as he set them.
#  The S315 tables MIGRATE IN PLACE: new columns are added, nothing of his is rewritten or deleted.
#  Gates: SUMS/KIT_ID -> live pin -> compile -> migration test -> walk 33 on a scratch copy of the live
#  finance.db -> backup -> place -> restart -> health -> seed the live tables and print the counts.
#  Any red after placing: owner_sheets.py restored from its backup, the seeds removed, service restarted.
# =============================================================================
set -u
KIT="S316_SHEETS_SEEDED"; KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"; ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
DBF="${FINANCE_DB:-$FIN/finance.db}"
FROM_OS="2520564cec778c84b1fd506aadd05e74"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s316_walk_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { echo "!! [1/8] KIT_ID names another kit - nothing installed"; exit 1; }
TO_OS="$(m5 owner_sheets.py)"
echo "[1/8] kit gates green"
if [ "$(m5 "$FIN/owner_sheets.py")" = "$TO_OS" ] && [ "$(m5 "$FIN/xray_seed.json")" = "$(m5 xray_seed.json)" ] \
   && [ "$(m5 "$FIN/proc_seed.json")" = "$(m5 proc_seed.json)" ]; then
  echo "-- ALREADY INSTALLED: owner_sheets $TO_OS with both seeds."
  "$SPY" -B seed_live_s316.py "$FIN" "$DBF"
  exit 0; fi
[ "$(m5 "$FIN/owner_sheets.py")" = "$FROM_OS" ] || { echo "!! [2/8] owner_sheets.py is $(m5 "$FIN/owner_sheets.py"), expected the S315 file $FROM_OS - nothing installed"; exit 1; }
echo "[2/8] the live pin is exact (S315 is what is running)"
"$SPY" -m py_compile owner_sheets.py walk_s316.py test_migration_s316.py seed_live_s316.py || { echo "!! [3/8] compile failed - nothing installed"; exit 1; }
"$SPY" -c "import json,sys; [json.load(open(f)) for f in ('xray_seed.json','proc_seed.json')]" || { echo "!! [3/8] a seed file is not valid JSON - nothing installed"; exit 1; }
echo "[3/8] py_compile + both seed files parse"
mkdir -p "$WALK/app" && cp -p owner_sheets.py walk_s316.py test_migration_s316.py xray_seed.json proc_seed.json "$WALK/app/" || exit 1
( cd "$WALK/app" && "$SPY" -B test_migration_s316.py "$FIN/owner_sheets.py" "$WALK/app" 2>&1 | tail -1 | grep -q "^TEST OK" ) || { echo "!! [4/8] the migration test is red - nothing installed"; rm -rf "$WALK"; exit 1; }
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d)" "$DBF" "$WALK/walk.db" || { echo "!! [4/8] scratch copy of finance.db failed - nothing installed"; rm -rf "$WALK"; exit 1; }
W="$("$SPY" -B "$WALK/app/walk_s316.py" "$WALK/app" "$WALK/walk.db" 2>&1 | tail -1)"
rm -rf "$WALK"
[ "${W#WALK OK}" != "$W" ] || { echo "!! [4/8] walk red: $W - nothing installed"; exit 1; }
echo "[4/8] migration test OK · $W (on a scratch copy of the live finance.db)"
B="$FIN/owner_sheets.py.bak_S316_${FROM_OS:0:8}"
restore() { echo "!! RED - restoring"; [ -f "$B" ] && \cp -p "$B" "$FIN/owner_sheets.py"
  rm -f "$FIN/xray_seed.json" "$FIN/proc_seed.json"; systemctl restart clinic-finance || true; sleep 3
  echo "!! restored: owner_sheets $(m5 "$FIN/owner_sheets.py") · clinic-finance $(systemctl is-active clinic-finance)"; exit 1; }
\cp -p "$FIN/owner_sheets.py" "$B"
for f in owner_sheets.py xray_seed.json proc_seed.json; do \cp -p "$f" "$FIN/$f" || restore; [ "$(m5 "$FIN/$f")" = "$(m5 "$f")" ] || restore; done
echo "[5/8] placed; every md5 = the kit's own (backup $B)"
"$SPY" -m py_compile "$FIN/owner_sheets.py" || restore
systemctl restart clinic-finance || restore; sleep 4
systemctl is-active --quiet clinic-finance || restore
c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/clinic/sheets)
echo "      health : finance $c1 · the sheets page $c3 (302 = the login gate)"
[ "$c1" = 200 ] || restore
{ [ "$c3" = 302 ] || [ "$c3" = 200 ] || [ "$c3" = 403 ]; } || restore
echo "[6/8] clinic-finance restarted and answering"
OUT="$("$SPY" -B seed_live_s316.py "$FIN" "$DBF" 2>&1 | tail -1)"
echo "$OUT" | grep -q "^SEEDED" || restore
echo "[7/8] $OUT"
echo "[8/8] open it at https://followup.dr-manoj.in/finance/clinic/sheets — approve · rename · reject · add"
echo "== S316_SHEETS_SEEDED INSTALLED =="
