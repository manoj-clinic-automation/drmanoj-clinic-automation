#!/bin/bash
# =============================================================================
#  install_S330_BLOOD_TEST.sh · kit S330_BLOOD_TEST (session 271, 19-Sep-2026)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S330_BLOOD_TEST/install_S330_BLOOD_TEST.sh
#
#  THE OWNER, 19-Sep-2026: blood tests, minimum taps. The chamber logs "blood test ordered" for a
#  patient (menu -> Blood test: pick from today's OPD, one tap). The lab's report e-mail (clinic ID in
#  the subject) reaches this server through the mailbox's Apps Script (VPS_Push_Lab.gs, in this kit)
#  and lands in reception's Docterz-upload list. NOTHING is asked during patient flow: at upload time an
#  order from an earlier day with no report asks once -- "Test nahi karaya" or "Sample diya, email nahi
#  aaya" (the lab sends by hand and can miss one). A late report closes the order by itself. The doctors'
#  and Shavez's report lists who took the slip and never got tested, and what the lab has not e-mailed.
#
#  FILES:  /root/finance/slip_log.py   S329 3bf78bda (or earlier S32x builds) -> (TO below)
#          portal.py / tile_grants.json: S329's (4085b767 / v22 fe38b974) -- set if not already
#          /root/finance/finance_app.py must be 41e0ffb4 (S324) -- checked, not changed
#  DATA:   tables blood_order, lab_report, created on first use. fix_s327.py re-run (idempotent).
#  NEW DOOR: POST /finance/slips/api/lab-report, X-Finance-Cron (the token the Gmail pushes already use).
# =============================================================================
set -u
KIT="S330_BLOOD_TEST"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"
DBF="${FINANCE_DB:-$FIN/finance.db}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s330_walk_$STAMP"
FA=41e0ffb4ce8c94a76c251294ef3e5d31
SL_FROM_OK="3bf78bda82c3720e466ac2745cbdb5e1 ae445164c8974b2d8371ed16c99d35fa 36cb57671a730c868b2371625aa70810 630adb8b045b89197e1f403a68b30b4c 6d825d918bb4ddfd471f64e526a0e758"
PO_FROM_OK="bac9a4928bbd23fde2410f74a8bf8f03 4085b76781696f80f64283aa1eef57bb"
TG_FROM_OK="fe38b97494ee7a43091323dfd64e7836 cb9ff9048cacde3d0083fa426734b242 223d67d9716eb50294c240590073034d"
declare -A TO=( [slip_log.py]=0b3195d2610e64a4b637e0ed89eb8454 [portal.py]=4085b76781696f80f64283aa1eef57bb [tile_grants.json]=fe38b97494ee7a43091323dfd64e7836 )
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
case " $PO_FROM_OK " in *" $(m5 "${DEST[portal.py]}") "*) ;; *) say "!! [2/8] portal.py is $(m5 "${DEST[portal.py]}"), not S324/S328 - nothing installed"; exit 1;; esac
case " $TG_FROM_OK " in *" $(m5 "${DEST[tile_grants.json]}") "*) ;; *) say "!! [2/8] tile_grants.json is $(m5 "${DEST[tile_grants.json]}"), not v20/v21/v22 - nothing installed"; exit 1;; esac
[ "$(m5 "$FIN/finance_app.py")" = "$FA" ] || { say "!! [2/8] finance_app.py is not the S324 pin - nothing installed"; exit 1; }
say "[2/8] live pins exact"
"$SPY" -m py_compile slip_log.py fix_s327.py && "$VPY" -m py_compile portal.py \
  && "$VPY" -c "import json; assert json.load(open('tile_grants.json',encoding='utf-8'))['version']==22" \
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
         FINANCE_SSO_DIR="$POR" PETTY_UPLOAD_DIR="$WALK/uploads" timeout 170 "$SPY" -B "$KDIR/walk_s330.py" "$WALK/app" 2>&1 | tail -1 )"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [4/8] walk red: $WOUT - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[4/8] $WOUT"
declare -A BAK
for f in "${ORDER[@]}"; do
  BAK[$f]="${DEST[$f]}.bak_S330_$(m5 "${DEST[$f]}" | cut -c1-8)"
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
say "[5/8] placed, backups beside each file (.bak_S330_<from8>)"
"$SPY" -B fix_s327.py "$DBF" || restore
say "[6/8] one-time clean-up checked"
systemctl restart clinic-finance || restore
systemctl restart clinic-portal || restore
sleep 4
for s in clinic-finance clinic-portal; do systemctl is-active --quiet "$s" || restore; done
say "[7/8] clinic-finance, clinic-portal active"
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8099/portal)
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/slips)
say "health : finance $c2 · portal $c3 · /finance/slips without a login $c4 (302 expected)"
[ "$c2" = 200 ] && { [ "$c3" = 200 ] || [ "$c3" = 302 ]; } && { [ "$c4" = 302 ] || [ "$c4" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore
say "[8/8] all green"
for f in "${ORDER[@]}"; do md5sum "${DEST[$f]}"; done
say "$KIT: DONE"
