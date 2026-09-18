#!/bin/bash
# =============================================================================
#  install_S315_OWNER_SHEETS.sh · kit S315_OWNER_SHEETS (session 269, 18-Sep-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S315_OWNER_SHEETS/install_S315_OWNER_SHEETS.sh
#
#  THE OWNER, 18-Sep: "I need the procedure consumable sheet, x-ray prices ... give me those
#  somewhere where I can work — that is the system tile you had made."  So the sheet is a page.
#   A  /root/finance/owner_sheets.py NEW — the X-ray price list and the procedure → consumables map
#      at /finance/clinic/sheets (D546). Seeded from the amounts his own Docterz days actually carry
#      (clinic_day_line) and from the pharmacy's item master, both READ-ONLY. Own two tables.
#   B  finance_app.py 8dc77ef4 -> c9f73b18 (guarded mount, patched on the box)
#   C  portal.py     e13adbd6 -> 4b365709 (one doctor-only tile 'Procedures & prices')
#  Gates: SUMS/KIT_ID -> live pins -> compile -> walk 25 checks over a scratch copy of the live
#  finance.db (negative controls proved offline) -> backups -> place+patch -> restart -> health.
#  Any red after placing: all three files restored from their backups and both services restarted.
# =============================================================================
set -u
KIT="S315_OWNER_SHEETS"; KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"; DBF="${FINANCE_DB:-$FIN/finance.db}"
FROM_FA="8dc77ef48c96bec7382f1c8aaf40f38e"; TO_FA="c9f73b181d3b28b93d71aa3781addb61"
FROM_PO="e13adbd65d82ba9015fcbb1b24d832c3"; TO_PO="4b3657091c8a6620192424dd67c801aa"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s315_walk_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { echo "!! [1/8] KIT_ID names another kit - nothing installed"; exit 1; }
echo "[1/8] kit gates green"
if [ "$(m5 "$FIN/finance_app.py")" = "$TO_FA" ] && [ "$(m5 "$POR/portal.py")" = "$TO_PO" ] && [ "$(m5 "$FIN/owner_sheets.py")" = "$(m5 owner_sheets.py)" ]; then
  echo "-- ALREADY INSTALLED: finance_app $TO_FA · portal $TO_PO · owner_sheets $(m5 owner_sheets.py)"; exit 0; fi
[ "$(m5 "$FIN/finance_app.py")" = "$FROM_FA" ] || { echo "!! [2/8] finance_app.py is $(m5 "$FIN/finance_app.py"), expected $FROM_FA - nothing installed"; exit 1; }
[ "$(m5 "$POR/portal.py")" = "$FROM_PO" ] || { echo "!! [2/8] portal.py is $(m5 "$POR/portal.py"), expected $FROM_PO - nothing installed"; exit 1; }
[ -e "$FIN/owner_sheets.py" ] && { echo "!! [2/8] $FIN/owner_sheets.py already exists and is not this kit's - nothing installed"; exit 1; }
echo "[2/8] every live pin exact; the new file's name is free"
"$SPY" -m py_compile owner_sheets.py walk_s315.py patch_finance_app_s315.py patch_portal_s315.py || { echo "!! [3/8] compile failed - nothing installed"; exit 1; }
"$VPY" -m py_compile owner_sheets.py || { echo "!! [3/8] venv compile failed - nothing installed"; exit 1; }
echo "[3/8] py_compile green (system + venv)"
mkdir -p "$WALK/app" && cp -p owner_sheets.py walk_s315.py "$WALK/app/" || exit 1
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d)" "$DBF" "$WALK/walk.db" || { echo "!! [4/8] scratch copy of finance.db failed - nothing installed"; rm -rf "$WALK"; exit 1; }
W="$("$SPY" -B "$WALK/app/walk_s315.py" "$WALK/app" "$WALK/walk.db" 2>&1 | tail -1)"
rm -rf "$WALK"
[ "${W#WALK OK}" != "$W" ] || { echo "!! [4/8] walk red: $W - nothing installed"; exit 1; }
echo "[4/8] $W (on a scratch copy of the live finance.db)"
BF="$FIN/finance_app.py.bak_S315_${FROM_FA:0:8}"; BP="$POR/portal.py.bak_S315_${FROM_PO:0:8}"
restore() { echo "!! RED - restoring"; [ -f "$BF" ] && \cp -p "$BF" "$FIN/finance_app.py"; [ -f "$BP" ] && \cp -p "$BP" "$POR/portal.py"
  rm -f "$FIN/owner_sheets.py"; systemctl restart clinic-finance clinic-portal || true; sleep 4
  echo "!! restored: finance_app $(m5 "$FIN/finance_app.py") · portal $(m5 "$POR/portal.py") · clinic-finance $(systemctl is-active clinic-finance)"; exit 1; }
\cp -p "$FIN/finance_app.py" "$BF"; \cp -p "$POR/portal.py" "$BP"
\cp -p owner_sheets.py "$FIN/owner_sheets.py" || restore
[ "$(m5 "$FIN/owner_sheets.py")" = "$(m5 owner_sheets.py)" ] || restore
"$SPY" -B patch_finance_app_s315.py "$FIN/finance_app.py" || restore
"$SPY" -B patch_portal_s315.py "$POR/portal.py" || restore
[ "$(m5 "$FIN/finance_app.py")" = "$TO_FA" ] || { echo "!! finance_app is $(m5 "$FIN/finance_app.py"), predicted $TO_FA"; restore; }
[ "$(m5 "$POR/portal.py")" = "$TO_PO" ] || { echo "!! portal is $(m5 "$POR/portal.py"), predicted $TO_PO"; restore; }
echo "[5/8] placed and patched; every md5 = predicted (backups $BF · $BP)"
"$SPY" -m py_compile "$FIN/finance_app.py" "$FIN/owner_sheets.py" || restore
"$VPY" -m py_compile "$POR/portal.py" || restore
echo "[6/8] the placed files compile on the box"
systemctl restart clinic-finance || restore; systemctl restart clinic-portal || restore; sleep 4
for s in clinic-finance clinic-portal; do systemctl is-active --quiet "$s" || { echo "!! $s not active"; restore; }; done
c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8099/portal)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/clinic/sheets)
echo "      health : finance $c1 · portal $c2 · the sheets page $c3 (302 = the login gate, as it must)"
[ "$c1" = 200 ] || restore
{ [ "$c2" = 200 ] || [ "$c2" = 302 ]; } || restore
{ [ "$c3" = 302 ] || [ "$c3" = 200 ] || [ "$c3" = 403 ]; } || restore
echo "[7/8] both services restarted and answering"
grep -q "owner_sheets NOT mounted" /var/log/syslog 2>/dev/null && echo "      (note: check the service log if the page 500s)"
echo "[8/8] done. The tile 'Procedures & prices' is on the doctor's portal; the page is /finance/clinic/sheets"
echo "== S315_OWNER_SHEETS INSTALLED =="
