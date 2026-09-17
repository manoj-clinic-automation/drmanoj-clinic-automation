#!/bin/bash
# =============================================================================
#  install_S295_FOUR_ITEMS.sh · kit S295_FOUR_ITEMS (session 265, 17-Sep-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S295_FOUR_ITEMS/install_S295_FOUR_ITEMS.sh
#
#  THE OWNER, 17-Sep-2026: "activate the staff attendance tile for all my staff who have the PWA ... then
#  roll out to the remaining staff as they are listed", and complete the three open items.
#   A  portal tile 'Meri attendance' (/register/me) by ROLE for staff and manager; bhati masked.
#      portal.py afb415b8 -> c14c2c64 · tile_grants.json v18 23dba543 -> v19 85a6e067
#   B  the bank's morning SMS figure on the morning match and on Darpan's day card while the MPR waits.
#      clinic_money.py 14e96b76 -> a92fc4c6 · darpan_app.py c98f0c24 -> f98004c9 · darpan_card.html 4a31f14e -> 572fb019
#   C  petty photos backed up nightly to Drive (slots created by S265 in FinanceDB_Backups).
#      /root/state_backup/petty_backup.py NEW 10b1ecbf · crontab +1 line 02:40 (S295_PETTY_BACKUP)
#   D  docterz_ingest.py 3809f046 -> d2102bb7: the two June workbooks with no Day Revenue sheet are
#      remembered instead of failed every ten minutes.
#  NEEDS (refuses otherwise): S290 live (finance_app 8dc77ef4 + bank_sms.py), S287 live (assetapp_backup b816504c).
#  Gates: SUMS/KIT_ID -> pins -> compile -> petty_backup selftest -> docterz no-sheet test -> THE WALK
#  (16 checks, scratch copy) -> backups -> place -> crontab -> restart clinic-finance + clinic-portal ->
#  health -> one real petty backup run (Drive slots proven) -> the attendance map (read-only).
#  Any red after placing: every file and the crontab restored, both services restarted.
# =============================================================================
set -u
KIT="S295_FOUR_ITEMS"; KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"; SPY="${SPY:-/usr/bin/python3}"; ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"; SB="$ROOT/state_backup"; DBF="${FINANCE_DB:-$FIN/finance.db}"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s295_walk_$STAMP"; CRONBAK="$FIN/crontab.bak_S295"
CRON_LINE='40 2 * * * /root/wa/venv/bin/python3 -B /root/state_backup/petty_backup.py >> /root/backups/petty_backup.log 2>&1 # S295_PETTY_BACKUP'
declare -A FROM=( [portal.py]=afb415b83921ef8fe118c6e55634e5a2 [tile_grants.json]=23dba5438a35789a0773f850efe7ad24
                  [clinic_money.py]=14e96b76230f25eccac2bcb28e741ea4 [darpan_app.py]=c98f0c2422d7943d09933a39e886ff63
                  [darpan_card.html]=4a31f14eb19ca752c6b6fea1f430eb8d [docterz_ingest.py]=3809f046e4b33d834e164c5320d91b4c )
declare -A DEST=( [portal.py]="$POR/portal.py" [tile_grants.json]="$POR/tile_grants.json"
                  [clinic_money.py]="$FIN/clinic_money.py" [darpan_app.py]="$FIN/darpan_app.py"
                  [darpan_card.html]="$FIN/darpan_card.html" [docterz_ingest.py]="$FIN/docterz_ingest.py"
                  [petty_backup.py]="$SB/petty_backup.py" )
ORDER=(portal.py tile_grants.json clinic_money.py darpan_app.py darpan_card.html docterz_ingest.py petty_backup.py)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/10] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { echo "!! [1/10] KIT_ID names another kit - nothing installed"; exit 1; }
echo "[1/10] kit gates green"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "$(m5 "$f")" ] || ALL=0; done
if [ "$ALL" = 1 ] && crontab -l 2>/dev/null | grep -q "S295_PETTY_BACKUP"; then
  echo "-- ALREADY INSTALLED. The attendance map (read-only):"; "$SPY" -B attendance_map_s295.py "$POR/clinic_users.json" "$ROOT/staff_register/staff_register.db" 2>&1; exit 0; fi
[ "$(m5 "$FIN/finance_app.py")" = "8dc77ef48c96bec7382f1c8aaf40f38e" ] && [ -f "$FIN/bank_sms.py" ] || { echo "!! [2/10] S290 is not live (finance_app.py / bank_sms.py) - nothing installed"; exit 1; }
[ "$(m5 "$SB/assetapp_backup.py")" = "b816504c89fa127b7519d29a77e54658" ] || { echo "!! [2/10] S287's assetapp_backup.py is not at its pin - nothing installed"; exit 1; }
for f in "${ORDER[@]}"; do
  if [ "$f" = petty_backup.py ]; then [ -e "${DEST[$f]}" ] && { echo "!! [2/10] ${DEST[$f]} exists but is not this kit's - nothing installed"; exit 1; }; continue; fi
  [ "$(m5 "${DEST[$f]}")" = "${FROM[$f]}" ] || { echo "!! [2/10] ${DEST[$f]} is $(m5 "${DEST[$f]}"), expected ${FROM[$f]} - nothing installed"; exit 1; }
done
echo "[2/10] every live pin exact; S290 and S287 present"
"$SPY" -m py_compile clinic_money.py darpan_app.py docterz_ingest.py && "$VPY" -m py_compile portal.py petty_backup.py docterz_ingest.py \
  && "$VPY" -c "import json; json.load(open('tile_grants.json',encoding='utf-8'))" || { echo "!! [3/10] compile failed - nothing installed"; exit 1; }
echo "[3/10] py_compile + json green"
T="/tmp/s295_tests_$STAMP"; mkdir -p "$T" && cp -p petty_backup.py docterz_ingest.py test_docterz_s295.py "$T/" && cp -p "$FIN/docterz_day.py" "$T/"
( cd "$T" && "$VPY" -B petty_backup.py --selftest --asset-module "$SB/assetapp_backup.py" 2>&1 | tail -1 | grep -q "^SELFTEST OK" ) || { echo "!! [4/10] petty_backup selftest red - nothing installed"; rm -rf "$T"; exit 1; }
( cd "$T" && "$VPY" -B test_docterz_s295.py "$T" 2>&1 | tail -1 | grep -q "^TEST OK" ) || { echo "!! [4/10] docterz no-sheet test red - nothing installed"; rm -rf "$T"; exit 1; }
rm -rf "$T"; echo "[4/10] petty_backup selftest OK · docterz no-sheet test OK"
mkdir -p "$WALK/app" && cp -p "$FIN"/*.py "$WALK/app/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/app/" 2>/dev/null
cp -p clinic_money.py darpan_app.py darpan_card.html "$WALK/app/"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" || { echo "!! [5/10] scratch copy failed"; rm -rf "$WALK"; exit 1; }
echo "walk-key-s295-$STAMP" > "$WALK/walk.key"
WOUT="$( cd "$WALK/app" && FINANCE_DB="$WALK/walk.db" FINANCE_ALLOW_HEADER_AUTH=1 BANK_SMS_KEY_FILE="$WALK/walk.key" PETTY_UPLOAD_DIR="$WALK/up" \
         FINANCE_SCAN_DIR="$WALK/scans" FINANCE_SSO_DIR="$POR" timeout 170 "$SPY" -B "$KDIR/walk_s295.py" "$WALK/app" 2>&1 | tail -1 )"
echo "$WOUT" | grep -q "^WALK OK" || { echo "!! [5/10] walk red: $WOUT - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"; echo "[5/10] $WOUT"
declare -A BAK
for f in "${ORDER[@]}"; do [ "$f" = petty_backup.py ] && continue; BAK[$f]="${DEST[$f]}.bak_S295_${FROM[$f]:0:8}"; \cp -p "${DEST[$f]}" "${BAK[$f]}" || { echo "!! [6/10] backup failed - nothing placed"; exit 1; }; done
crontab -l > "$CRONBAK" 2>/dev/null || { echo "!! [6/10] cannot read crontab - nothing placed"; exit 1; }
restore() { echo "!! RED after placing - restoring every file and the crontab"
  for f in "${ORDER[@]}"; do if [ "$f" = petty_backup.py ]; then mv -f "${DEST[$f]}" "${DEST[$f]}.removed_S295_$STAMP" 2>/dev/null || true; else \cp -p "${BAK[$f]}" "${DEST[$f]}"; fi; done
  crontab "$CRONBAK"; systemctl restart clinic-finance clinic-portal || true; sleep 3
  for f in "${ORDER[@]}"; do [ "$f" = petty_backup.py ] || echo "   ${DEST[$f]} $(m5 "${DEST[$f]}")"; done; exit 1; }
for f in "${ORDER[@]}"; do \cp -p "$f" "${DEST[$f]}" || restore; [ "$(m5 "${DEST[$f]}")" = "$(m5 "$f")" ] || restore; done
echo "[6/10] placed; backups .bak_S295_<from8>; crontab backup $CRONBAK"
if ! grep -q "S295_PETTY_BACKUP" "$CRONBAK"; then ( cat "$CRONBAK"; echo "$CRON_LINE" ) > "/tmp/s295_cron_$STAMP" && crontab "/tmp/s295_cron_$STAMP" || restore; rm -f "/tmp/s295_cron_$STAMP"; fi
[ "$(crontab -l | grep -c S295_PETTY_BACKUP)" = 1 ] || restore
echo "[7/10] crontab: one S295_PETTY_BACKUP line (02:40)"
systemctl restart clinic-finance || restore; systemctl restart clinic-portal || restore; sleep 4
for s in clinic-finance clinic-portal; do systemctl is-active --quiet "$s" || { echo "!! $s not active"; restore; }; done
c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz); c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8099/portal)
echo "health : finance $c1 · portal $c2"
[ "$c1" = 200 ] && { [ "$c2" = 200 ] || [ "$c2" = 302 ]; } || restore
echo "[8/10] both services active and answering"
echo "[9/10] one real petty backup run now (ships to the Drive slots):"
mkdir -p "$ROOT/backups"
"$VPY" -B "$SB/petty_backup.py" --uploads "$FIN/petty_uploads" --dest "$ROOT/backups" --asset-module "$SB/assetapp_backup.py" 2>&1 | tee -a "$ROOT/backups/petty_backup.log" | tail -1
echo "[10/10] the attendance map (read-only) -- who opens 'Meri attendance':"
"$SPY" -B attendance_map_s295.py "$POR/clinic_users.json" "$ROOT/staff_register/staff_register.db" 2>&1 | tail -30
echo "docterz reader, one read-only pass:"
flock -n /tmp/docterz_ingest.lock "$VPY" -B "$FIN/docterz_ingest.py" --dry-run 2>&1 | tail -1
echo "md5 of the installed files:"; for f in "${ORDER[@]}"; do md5sum "${DEST[$f]}"; done
echo "$KIT: DONE"
