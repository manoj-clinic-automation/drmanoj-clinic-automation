#!/bin/bash
# =============================================================================
#  install_S289_PWA_EXIT_AND_PETTY.sh · kit S289_PWA_EXIT_AND_PETTY (session 265, 17-Sep-2026)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S289_PWA_EXIT_AND_PETTY/install_S289_PWA_EXIT_AND_PETTY.sh
#
#  THE OWNER, 17-Sep-2026: (1) staff who leave late when the punch machine cannot be reached raise
#  "Mark my exit" on their own page at the moment of leaving; the doctor approves at once or later;
#  the self page stays today-only. (2) Manoj Bhati -- an associate, not an employee -- gets his own
#  login scope: availability, the Shavez/Darpan diaries topped up, renovation payees, Rahul's
#  monthly Rs 5,000, his own loan, the physiotherapy tick; tap-only, Hinglish; the doctors' check
#  page in English; reception sees one line (is he coming today). Totally separate from Sanjeevni
#  and clinic money.
#
#  FILES (each from an exact live pin, each backed up beside itself):
#    /root/staff_register/staff_register.py  b9a72d1a -> 13a26205  exit_request + /me/exit + review card
#    /root/att_month_report.py               0184cb13 -> ce72c323  approved exits fold as punch-outs
#    /root/finance/finance_app.py            a4201e9f -> ac61df70  PATCHED ON THE BOX (F-185): unit 'petty' + guarded mount
#    /root/finance/petty_book.py             NEW       53f7e65d
#    /root/portal/portal.py                  4974209b -> afb415b8  tiles 'Petty book' + 'Bhati aaj'
#    /root/portal/tile_grants.json           v17 2eb2f271 -> v18 23dba543
#  DATA: seed_s289.py -- business_unit 'petty' and six unit_role rows (INSERT OR IGNORE). Tables of
#        the new module and the new exit_request table are created on first use (IF NOT EXISTS).
#
#  Gates in order: kit SUMS + KIT_ID -> every live pin exact (or ALREADY INSTALLED) -> the patcher on
#  the live bytes == predicted -> py_compile of every file with the python that runs it -> the staff
#  register's own selftest and the month report's own selftest (kit copies) -> THE WALK ON THIS BOX
#  (the real patched app over a scratch copy of the live finance.db, 70 checks) -> backups -> place
#  -> seed -> restart staff-register, clinic-finance, clinic-portal -> health of all three and the new
#  address behind the login. Any red after placing: EVERY file restored, all three restarted.
#
#  Nothing on manojz or the medical PC. No cron line. No scheduled job touched, so no switch needed.
# =============================================================================
set -u
KIT="S289_PWA_EXIT_AND_PETTY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"                     # clinic-finance runs on the system python
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"; SRD="$ROOT/staff_register"
DBF="${FINANCE_DB:-$FIN/finance.db}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s289_walk_$STAMP"

declare -A FROM=( [staff_register.py]=b9a72d1a35f3a71f2cbb518b4fb7698c
                  [att_month_report.py]=0184cb139907ee11adcc78c1ecab2daa
                  [finance_app.py]=a4201e9fc52c25528ba3b92db403101f
                  [portal.py]=4974209bfd2a66510294d8adf8712523
                  [tile_grants.json]=2eb2f2714091d97ae8f53a80902c913f )
declare -A TO=(   [staff_register.py]=13a262059c9108f9f67b653c28998c10
                  [att_month_report.py]=ce72c323a597ffef3f52b010b8e0d958
                  [finance_app.py]=ac61df70f80a4a57d8eebd7e997593bd
                  [petty_book.py]=53f7e65df20e139cd7e5b09a4ecd9738
                  [portal.py]=afb415b83921ef8fe118c6e55634e5a2
                  [tile_grants.json]=23dba5438a35789a0773f850efe7ad24 )
declare -A DEST=( [staff_register.py]="$SRD/staff_register.py"
                  [att_month_report.py]="$ROOT/att_month_report.py"
                  [finance_app.py]="$FIN/finance_app.py"
                  [petty_book.py]="$FIN/petty_book.py"
                  [portal.py]="$POR/portal.py"
                  [tile_grants.json]="$POR/tile_grants.json" )
ORDER=(staff_register.py att_month_report.py finance_app.py petty_book.py portal.py tile_grants.json)
FA_NEW="/tmp/s289_finance_app_$STAMP.py"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp date systemctl curl; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
[ -x "$VPY" ] || { say "!! preflight: $VPY not executable - nothing installed"; exit 1; }
[ -x "$SPY" ] || { say "!! preflight: $SPY not executable - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/9] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/9] KIT_ID.txt names another kit - nothing installed"; exit 1; }
say "[1/9] kit gates green"

# ---- [2] live pins ------------------------------------------------------------------------------
ALL_TO=1
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then
  say "-- ALREADY INSTALLED: every file carries this kit. Re-seeding (idempotent):"
  "$SPY" -B seed_s289.py "$DBF"; exit 0
fi
for f in "${ORDER[@]}"; do
  [ "$f" = petty_book.py ] && { [ -e "${DEST[$f]}" ] && { say "!! [2/9] ${DEST[$f]} already exists but is not this kit's - nothing installed"; exit 1; }; continue; }
  have="$(m5 "${DEST[$f]}")"
  [ "$have" = "${FROM[$f]}" ] || { say "!! [2/9] ${DEST[$f]} is ${have:-missing}, expected ${FROM[$f]} - nothing installed"; exit 1; }
done
say "[2/9] every live pin exact"

# ---- [3] the patcher on the live bytes ----------------------------------------------------------
"$SPY" -B patch_finance_app_s289.py --file "$FIN/finance_app.py" --from "${FROM[finance_app.py]}" --out "$FA_NEW" \
  || { say "!! [3/9] patcher refused - nothing installed"; rm -f "$FA_NEW"; exit 1; }
[ "$(m5 "$FA_NEW")" = "${TO[finance_app.py]}" ] || { say "!! [3/9] patched finance_app.py is $(m5 "$FA_NEW"), predicted ${TO[finance_app.py]} - nothing installed"; rm -f "$FA_NEW"; exit 1; }
for f in staff_register.py att_month_report.py petty_book.py portal.py tile_grants.json; do
  [ "$(m5 "$f")" = "${TO[$f]}" ] || { say "!! [3/9] kit file $f is not its predicted md5 - nothing installed"; rm -f "$FA_NEW"; exit 1; }
done
say "[3/9] patched finance_app.py == ${TO[finance_app.py]}; kit files at their pins"

# ---- [4] compile --------------------------------------------------------------------------------
"$SPY" -m py_compile "$FA_NEW" petty_book.py && "$VPY" -m py_compile staff_register.py att_month_report.py portal.py \
  && "$VPY" -c "import json,sys; json.load(open('tile_grants.json',encoding='utf-8'))" \
  || { say "!! [4/9] compile/json failed - nothing installed"; rm -f "$FA_NEW"; exit 1; }
say "[4/9] py_compile + json green"

# ---- [5] own selftests (kit copies, throwaway stores) ----------------------------------------------
ST="/tmp/s289_selftest_$STAMP"; mkdir -p "$ST" && cp -p staff_register.py att_month_report.py "$ST/"   # never run inside the clone
( cd "$ST" && "$VPY" -B staff_register.py --selftest 2>&1 | tail -1 | grep -q "SELFTEST OK" ) \
  || { say "!! [5/9] staff_register selftest red - nothing installed"; rm -rf "$ST" "$FA_NEW"; exit 1; }
( cd "$ST" && PYTHONPATH="$ST:$ROOT" "$VPY" -B att_month_report.py --selftest 2>&1 | tail -1 | grep -q "SELFTEST PASSED" ) \
  || { say "!! [5/9] att_month_report selftest red - nothing installed"; rm -rf "$ST" "$FA_NEW"; exit 1; }
rm -rf "$ST"
say "[5/9] staff register selftest OK (incl. S289 exit) · month report selftest PASSED (incl. S289 punch-out)"

# ---- [6] the walk on this box -----------------------------------------------------------------------
mkdir -p "$WALK/app" "$WALK/uploads" || exit 1
cp -p "$FIN"/*.py "$WALK/app/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/app/" 2>/dev/null
cp -p "$FA_NEW" "$WALK/app/finance_app.py"; cp -p petty_book.py "$WALK/app/petty_book.py"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
  || { say "!! [6/9] could not take the scratch copy - nothing installed"; rm -rf "$WALK" "$FA_NEW"; exit 1; }
"$SPY" -B seed_s289.py "$WALK/walk.db" >/dev/null || { say "!! [6/9] seed on the scratch copy failed - nothing installed"; rm -rf "$WALK" "$FA_NEW"; exit 1; }
WOUT="$( cd "$WALK/app" && FINANCE_DB="$WALK/walk.db" FINANCE_ALLOW_HEADER_AUTH=1 PETTY_UPLOAD_DIR="$WALK/uploads" \
         PETTY_NOW="$(date +%Y-%m-%dT%H:%M:%S)" FINANCE_SCAN_DIR="$WALK/scans" FINANCE_SSO_DIR="$POR" \
         timeout 170 "$SPY" -B "$KDIR/walk_s289.py" "$WALK/app" 2>&1 | tail -1 )"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [6/9] walk red: $WOUT - nothing installed"; rm -rf "$WALK" "$FA_NEW"; exit 1; }
rm -rf "$WALK"
say "[6/9] $WOUT"

# ---- [7] backups + place ------------------------------------------------------------------------------
declare -A BAK
for f in "${ORDER[@]}"; do
  [ "$f" = petty_book.py ] && continue
  BAK[$f]="${DEST[$f]}.bak_S289_${FROM[$f]:0:8}"
  \cp -p "${DEST[$f]}" "${BAK[$f]}" || { say "!! [7/9] backup of ${DEST[$f]} failed - nothing placed"; rm -f "$FA_NEW"; exit 1; }
done
restore() {
  say "!! RED after placing - restoring every file byte-identically"
  for f in "${ORDER[@]}"; do
    if [ "$f" = petty_book.py ]; then mv -f "${DEST[$f]}" "${DEST[$f]}.removed_S289_$STAMP" 2>/dev/null || true
    else \cp -p "${BAK[$f]}" "${DEST[$f]}"; fi
  done
  systemctl restart staff-register clinic-finance clinic-portal || true
  sleep 3
  for f in "${ORDER[@]}"; do [ "$f" = petty_book.py ] || say "   ${DEST[$f]} $(m5 "${DEST[$f]}")"; done
  say "   (the petty unit rows stay; with the old files nothing reads them)"
  exit 1
}
\cp -p staff_register.py "${DEST[staff_register.py]}" || restore
\cp -p att_month_report.py "${DEST[att_month_report.py]}" || restore
\cp -p "$FA_NEW" "${DEST[finance_app.py]}" || restore
\cp -p petty_book.py "${DEST[petty_book.py]}" || restore
\cp -p portal.py "${DEST[portal.py]}" || restore
\cp -p tile_grants.json "${DEST[tile_grants.json]}" || restore
rm -f "$FA_NEW"
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || { say "!! [7/9] ${DEST[$f]} did not land at its pin"; restore; }; done
say "[7/9] placed, backups beside each file (.bak_S289_<from8>)"

# ---- [8] seed + restart ----------------------------------------------------------------------------------
"$SPY" -B seed_s289.py "$DBF" || restore
systemctl restart staff-register || restore
systemctl restart clinic-finance || restore
systemctl restart clinic-portal || restore
sleep 4
for s in staff-register clinic-finance clinic-portal; do systemctl is-active --quiet "$s" || { say "!! $s not active"; restore; }; done
say "[8/9] seeded; staff-register, clinic-finance, clinic-portal active"

# ---- [9] health ------------------------------------------------------------------------------------------
c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8044/register/health)
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8099/portal)
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/petty)
say "health : register $c1 · finance $c2 · portal $c3 · /finance/petty without a login $c4 (302 expected)"
[ "$c1" = 200 ] && [ "$c2" = 200 ] && { [ "$c3" = 200 ] || [ "$c3" = 302 ]; } && { [ "$c4" = 302 ] || [ "$c4" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "petty_book NOT mounted" && { say "!! petty_book did not mount"; restore; }
say "[9/9] all green"
say "md5 of the installed files:"
for f in "${ORDER[@]}"; do md5sum "${DEST[$f]}"; done
say "$KIT: DONE"
say "read next: https://followup.dr-manoj.in/finance/petty"
