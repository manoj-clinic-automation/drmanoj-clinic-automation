#!/bin/bash
# =============================================================================
#  install_S324_SLIP_LOG.sh · kit S324_SLIP_LOG (session 271, 19-Sep-2026)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S324_SLIP_LOG/install_S324_SLIP_LOG.sh
#
#  THE OWNER, 19-Sep-2026: a dedicated tile 'OPD & X-ray/Proc Slips'. The chamber assistant logs every
#  slip's number (prompted from the running series) and the clinic ID; a known patient autofills, a new
#  one is saved as new today, a person with no clinic ID by name; X-ray and procedure are separate
#  dropdowns from his own rate page (several X-rays, up to 3 procedures, Other); the room ticks Paid and
#  Done whenever convenient, never blocking; the report matches the slips against Docterz in slip order,
#  OPD and X-ray/Proc apart, ALONGSIDE the current report. Back button on top; sections collapsed, only
#  the top one open, so the flow fits one screen.
#
#  FILES (each from an exact live pin, each backed up beside itself):
#    /root/finance/finance_app.py   0191de01 -> 41e0ffb4  PATCHED ON THE BOX (F-185): unit 'slips' + guarded mount
#    /root/finance/slip_log.py      NEW       f4dc7110
#    /root/portal/portal.py         4b365709 -> 4085b767  tile 'OPD & X-ray/Proc Slips' (roles doctor; section Clinic)
#    /root/portal/tile_grants.json  v19 85a6e067 -> v20 223d67d9  the tile to shavez, alisha, shivani, bhati, awdhesh
#  DATA: seed_s324.py -- business_unit 'slips' and seven unit_role rows (insert-if-absent). The three
#        slip_* tables are created on first use (IF NOT EXISTS). Nothing existing is altered.
#
#  Gates in order: kit SUMS + KIT_ID -> every live pin exact (or ALREADY INSTALLED) -> the patcher on
#  the live bytes == predicted -> py_compile -> THE WALK ON THIS BOX (the real patched app over a scratch
#  copy of the live finance.db) -> backups -> place -> seed -> restart clinic-finance, clinic-portal ->
#  health and the new address behind the login. Any red after placing: EVERY file restored, both restarted.
#
#  Nothing on manojz or the medical PC. No cron line. No scheduled job touched, so no switch needed.
# =============================================================================
set -u
KIT="S324_SLIP_LOG"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"                     # clinic-finance runs on the system python
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"
DBF="${FINANCE_DB:-$FIN/finance.db}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s324_walk_$STAMP"

declare -A FROM=( [finance_app.py]=0191de01e569edc32b8d7c2d67f53471
                  [portal.py]=4b3657091c8a6620192424dd67c801aa
                  [tile_grants.json]=85a6e0674906fad9c538883ac0e3ead1 )
declare -A TO=(   [finance_app.py]=41e0ffb4ce8c94a76c251294ef3e5d31
                  [slip_log.py]=f4dc7110a19258dea6a7473bfbb994a9
                  [portal.py]=4085b76781696f80f64283aa1eef57bb
                  [tile_grants.json]=223d67d9716eb50294c240590073034d )
declare -A DEST=( [finance_app.py]="$FIN/finance_app.py"
                  [slip_log.py]="$FIN/slip_log.py"
                  [portal.py]="$POR/portal.py"
                  [tile_grants.json]="$POR/tile_grants.json" )
ORDER=(finance_app.py slip_log.py portal.py tile_grants.json)
FA_NEW="/tmp/s324_finance_app_$STAMP.py"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp date systemctl curl timeout; do
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
  "$SPY" -B seed_s324.py "$DBF"; exit 0
fi
for f in "${ORDER[@]}"; do
  if [ "$f" = slip_log.py ]; then
    [ -e "${DEST[$f]}" ] && { say "!! [2/9] ${DEST[$f]} already exists but is not this kit's - nothing installed"; exit 1; }
    continue
  fi
  have="$(m5 "${DEST[$f]}")"
  [ "$have" = "${FROM[$f]}" ] || { say "!! [2/9] ${DEST[$f]} is ${have:-missing}, expected ${FROM[$f]} - nothing installed"; exit 1; }
done
say "[2/9] every live pin exact"

# ---- [3] the patcher on the live bytes ----------------------------------------------------------
"$SPY" -B patch_finance_app_s324.py --file "$FIN/finance_app.py" --from "${FROM[finance_app.py]}" --out "$FA_NEW" \
  || { say "!! [3/9] patcher refused - nothing installed"; rm -f "$FA_NEW"; exit 1; }
[ "$(m5 "$FA_NEW")" = "${TO[finance_app.py]}" ] || { say "!! [3/9] patched finance_app.py is $(m5 "$FA_NEW"), predicted ${TO[finance_app.py]} - nothing installed"; rm -f "$FA_NEW"; exit 1; }
for f in slip_log.py portal.py tile_grants.json; do
  [ "$(m5 "$f")" = "${TO[$f]}" ] || { say "!! [3/9] kit file $f is not its predicted md5 - nothing installed"; rm -f "$FA_NEW"; exit 1; }
done
say "[3/9] patched finance_app.py == ${TO[finance_app.py]}; kit files at their pins"

# ---- [4] compile --------------------------------------------------------------------------------
"$SPY" -m py_compile "$FA_NEW" slip_log.py && "$VPY" -m py_compile portal.py \
  && "$VPY" -c "import json; d=json.load(open('tile_grants.json',encoding='utf-8')); assert d['version']==20" \
  || { say "!! [4/9] compile/json failed - nothing installed"; rm -f "$FA_NEW"; exit 1; }
say "[4/9] py_compile + json green"

# ---- [5] the walk on this box -----------------------------------------------------------------------
mkdir -p "$WALK/app" || exit 1
cp -p "$FIN"/*.py "$WALK/app/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/app/" 2>/dev/null
[ -d "$FIN/finance_ui" ] && cp -rp "$FIN/finance_ui" "$WALK/app/"
cp -p "$FA_NEW" "$WALK/app/finance_app.py"; cp -p slip_log.py "$WALK/app/slip_log.py"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
  || { say "!! [5/9] could not take the scratch copy - nothing installed"; rm -rf "$WALK" "$FA_NEW"; exit 1; }
"$SPY" -B seed_s324.py "$WALK/walk.db" >/dev/null || { say "!! [5/9] seed on the scratch copy failed - nothing installed"; rm -rf "$WALK" "$FA_NEW"; exit 1; }
WOUT="$( cd "$WALK/app" && FINANCE_DB="$WALK/walk.db" FINANCE_ALLOW_HEADER_AUTH=1 \
         SLIP_NOW="$(date +%Y-%m-%dT%H:%M:%S)" FINANCE_SCAN_DIR="$WALK/scans" FINANCE_SSO_DIR="$POR" \
         PETTY_UPLOAD_DIR="$WALK/uploads" timeout 170 "$SPY" -B "$KDIR/walk_s324.py" "$WALK/app" 2>&1 | tail -1 )"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [5/9] walk red: $WOUT - nothing installed"; rm -rf "$WALK" "$FA_NEW"; exit 1; }
rm -rf "$WALK"
say "[5/9] $WOUT"

# ---- [6] backups ----------------------------------------------------------------------------------------
declare -A BAK
for f in finance_app.py portal.py tile_grants.json; do
  BAK[$f]="${DEST[$f]}.bak_S324_${FROM[$f]:0:8}"
  \cp -p "${DEST[$f]}" "${BAK[$f]}" || { say "!! [6/9] backup of ${DEST[$f]} failed - nothing placed"; rm -f "$FA_NEW"; exit 1; }
done
say "[6/9] backups beside each file (.bak_S324_<from8>)"
restore() {
  say "!! RED after placing - restoring every file byte-identically"
  for f in finance_app.py portal.py tile_grants.json; do \cp -p "${BAK[$f]}" "${DEST[$f]}"; done
  mv -f "${DEST[slip_log.py]}" "${DEST[slip_log.py]}.removed_S324_$STAMP" 2>/dev/null || true
  systemctl restart clinic-finance clinic-portal || true
  sleep 3
  for f in finance_app.py portal.py tile_grants.json; do say "   ${DEST[$f]} $(m5 "${DEST[$f]}")"; done
  say "   (the slips unit rows stay; with the old files nothing reads them)"
  exit 1
}

# ---- [7] place ---------------------------------------------------------------------------------------------
\cp -p slip_log.py "${DEST[slip_log.py]}" || restore
\cp -p "$FA_NEW" "${DEST[finance_app.py]}" || restore
\cp -p portal.py "${DEST[portal.py]}" || restore
\cp -p tile_grants.json "${DEST[tile_grants.json]}" || restore
rm -f "$FA_NEW"
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || { say "!! [7/9] ${DEST[$f]} did not land at its pin"; restore; }; done
say "[7/9] placed"

# ---- [8] seed + restart ----------------------------------------------------------------------------------
"$SPY" -B seed_s324.py "$DBF" || restore
systemctl restart clinic-finance || restore
systemctl restart clinic-portal || restore
sleep 4
for s in clinic-finance clinic-portal; do systemctl is-active --quiet "$s" || { say "!! $s not active"; restore; }; done
say "[8/9] seeded; clinic-finance, clinic-portal active"

# ---- [9] health ------------------------------------------------------------------------------------------
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8099/portal)
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/slips)
c5=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/petty)
say "health : finance $c2 · portal $c3 · /finance/slips without a login $c4 · /finance/petty without a login $c5 (302 expected)"
[ "$c2" = 200 ] && { [ "$c3" = 200 ] || [ "$c3" = 302 ]; } && { [ "$c4" = 302 ] || [ "$c4" = 401 ]; } && { [ "$c5" = 302 ] || [ "$c5" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && { say "!! a module did not mount"; restore; }
say "[9/9] all green"
say "md5 of the installed files:"
for f in "${ORDER[@]}"; do md5sum "${DEST[$f]}"; done
say "$KIT: DONE"
