#!/bin/bash
# =============================================================================
#  install_S328_EMR_UPLOAD.sh · kit S328_EMR_UPLOAD (session 271, 19-Sep-2026)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S328_EMR_UPLOAD/install_S328_EMR_UPLOAD.sh
#
#  THE OWNER, 19-Sep-2026: X-rays go from the X-ray PC by pen drive to reception, who upload each one
#  into the patient's Docterz record -- next afternoon for the previous evening and that morning; the
#  backlog must stay visible, "so everybody knows which are pending and which are done".
#  NEW tile 'X-ray EMR upload' (/finance/slips/emr) for alisha, shivani, shavez: pending X-rays by day,
#  oldest first, one tap "Upload ho gaya", undo, "all of this day". Its list comes from the slip tile's
#  X-ray/Proc slips and, where no slip covers a patient-day, from Docterz's own X-ray lines (from 18-Sep).
#  The doctors' slip report shows how many are waiting.
#  Carries S327 too (X-ray room work, amount, Start new book, the one-time clean-up to 1136) if it was
#  not installed yet -- fix_s327.py is idempotent.
#
#  FILES:  /root/finance/slip_log.py      S327 (6d825d91, or its earlier builds) -> ae445164
#          /root/portal/portal.py         4085b767 -> bac9a492  tile 'X-ray EMR upload'
#          /root/portal/tile_grants.json  v20 223d67d9 -> v21 cb9ff904
#          /root/finance/finance_app.py   must be 41e0ffb4 (S324) -- checked, not changed
#  DATA:   table emr_upload, created on first use. fix_s327.py (idempotent).
# =============================================================================
set -u
KIT="S328_EMR_UPLOAD"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"
DBF="${FINANCE_DB:-$FIN/finance.db}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s328_walk_$STAMP"
FA=41e0ffb4ce8c94a76c251294ef3e5d31
SL_FROM_OK="36cb57671a730c868b2371625aa70810 630adb8b045b89197e1f403a68b30b4c 6d825d918bb4ddfd471f64e526a0e758"
declare -A FROM=( [portal.py]=4085b76781696f80f64283aa1eef57bb [tile_grants.json]=223d67d9716eb50294c240590073034d )
declare -A TO=( [slip_log.py]=ae445164c8974b2d8371ed16c99d35fa [portal.py]=bac9a4928bbd23fde2410f74a8bf8f03 [tile_grants.json]=cb9ff9048cacde3d0083fa426734b242 )
declare -A DEST=( [slip_log.py]="$FIN/slip_log.py" [portal.py]="$POR/portal.py" [tile_grants.json]="$POR/tile_grants.json" )
ORDER=(slip_log.py portal.py tile_grants.json)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in "${ORDER[@]}"; do [ "$(m5 "$f")" = "${TO[$f]}" ] || { say "!! [1/8] kit $f is not its pin - nothing installed"; exit 1; }; done
say "[1/8] kit gates green"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED. Re-running fix_s327 (idempotent):"; "$SPY" -B fix_s327.py "$DBF"; exit 0; fi
have="$(m5 "${DEST[slip_log.py]}")"
case " $SL_FROM_OK " in *" $have "*) ;; *) say "!! [2/8] slip_log.py is $have, not an S326/S327 build - nothing installed"; exit 1;; esac
for f in portal.py tile_grants.json; do
  [ "$(m5 "${DEST[$f]}")" = "${FROM[$f]}" ] || { say "!! [2/8] ${DEST[$f]} is $(m5 "${DEST[$f]}"), expected ${FROM[$f]} - nothing installed"; exit 1; }
done
[ "$(m5 "$FIN/finance_app.py")" = "$FA" ] || { say "!! [2/8] finance_app.py is not the S324 pin - nothing installed"; exit 1; }
say "[2/8] live pins exact"
"$SPY" -m py_compile slip_log.py fix_s327.py && "$VPY" -m py_compile portal.py \
  && "$VPY" -c "import json; assert json.load(open('tile_grants.json',encoding='utf-8'))['version']==21" \
  || { say "!! [3/8] compile/json failed - nothing installed"; exit 1; }
say "[3/8] py_compile + json green"
mkdir -p "$WALK/app" || exit 1
cp -p "$FIN"/*.py "$WALK/app/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/app/" 2>/dev/null
[ -d "$FIN/finance_ui" ] && cp -rp "$FIN/finance_ui" "$WALK/app/"
cp -p slip_log.py "$WALK/app/slip_log.py"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
  || { say "!! [4/8] no scratch copy - nothing installed"; rm -rf "$WALK"; exit 1; }
"$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); [c.execute('DROP TABLE IF EXISTS '+t) for t in ('slip_item','slip','slip_book','emr_upload')]; c.commit()" "$WALK/walk.db"
"$SPY" -B seed_s324.py "$WALK/walk.db" >/dev/null || { say "!! [4/8] seed on the scratch copy failed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd "$WALK/app" && FINANCE_DB="$WALK/walk.db" FINANCE_ALLOW_HEADER_AUTH=1 SLIP_NOW="$(date +%Y-%m-%dT%H:%M:%S)" \
         FINANCE_SSO_DIR="$POR" PETTY_UPLOAD_DIR="$WALK/uploads" timeout 170 "$SPY" -B "$KDIR/walk_s328.py" "$WALK/app" 2>&1 | tail -1 )"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [4/8] walk red: $WOUT - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[4/8] $WOUT"
declare -A BAK
for f in "${ORDER[@]}"; do
  BAK[$f]="${DEST[$f]}.bak_S328_$(m5 "${DEST[$f]}" | cut -c1-8)"
  \cp -p "${DEST[$f]}" "${BAK[$f]}" || { say "!! [5/8] backup failed - nothing placed"; exit 1; }
done
restore() {
  say "!! RED after placing - restoring every file byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "${DEST[$f]}"; done
  systemctl restart clinic-finance clinic-portal || true; sleep 3
  for f in "${ORDER[@]}"; do say "   ${DEST[$f]} $(m5 "${DEST[$f]}")"; done
  exit 1
}
for f in "${ORDER[@]}"; do \cp -p "$f" "${DEST[$f]}" || restore; [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || restore; done
say "[5/8] placed, backups beside each file (.bak_S328_<from8>)"
"$SPY" -B fix_s327.py "$DBF" || restore
say "[6/8] one-time clean-up checked"
systemctl restart clinic-finance || restore
systemctl restart clinic-portal || restore
sleep 4
for s in clinic-finance clinic-portal; do systemctl is-active --quiet "$s" || restore; done
say "[7/8] clinic-finance, clinic-portal active"
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8099/portal)
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/slips/emr)
say "health : finance $c2 · portal $c3 · /finance/slips/emr without a login $c4 (302 expected)"
[ "$c2" = 200 ] && { [ "$c3" = 200 ] || [ "$c3" = 302 ]; } && { [ "$c4" = 302 ] || [ "$c4" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore
say "[8/8] all green"
for f in "${ORDER[@]}"; do md5sum "${DEST[$f]}"; done
say "$KIT: DONE"
