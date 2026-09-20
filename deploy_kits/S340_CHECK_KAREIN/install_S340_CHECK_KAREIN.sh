#!/bin/bash
# =============================================================================
#  install_S340_CHECK_KAREIN.sh · kit S340_CHECK_KAREIN (session 273, 20-Sep-2026)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S340_CHECK_KAREIN/install_S340_CHECK_KAREIN.sh
#
#  THE OWNER (S271_BUILD_BRIEF §2.5, step 3): one reception queue, "Check karein" (Shavez the checker) --
#  one-tap answers with who and when, oldest first -- and the doctors' ONE collapsed line on the records
#  page: "Patient records: all clear" / "4 need a look · oldest 2 days". Items now: blood test ordered with
#  no report after 2 days · lab report for an ID the clinic never issued · lab e-mail with no PDF.
#
#  FILES:  /root/finance/records.py       S335 dcb49d8c -> (TO below)
#          /root/finance/finance_app.py   S332 3a871f53 -> 7866b1ee, patched ON THE BOX (unit 'checks')
#          /root/portal/portal.py         S339 b7b0e43c -> d9a9dc40, rebuilt from the live bytes and compared
#          /root/portal/tile_grants.json  v22 fe38b974 -> v23 a5f8b3b1 (the tile to alisha, shivani, shavez)
#  DATA:   unit 'checks' (makers alisha, shivani, reception, shavez; checkers manoj, bhawna); table record_check.
# =============================================================================
set -u
KIT="S340_CHECK_KAREIN"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"
DBF="${FINANCE_DB:-$FIN/finance.db}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s340_walk_$STAMP"
declare -A FROM=( [records.py]=dcb49d8cc425b52b2f79d940c2baf7fe [finance_app.py]=3a871f53b5208edf8f218baeaa6c2882 [portal.py]=b7b0e43ccb4d6b012b38b9016f3f6f0c [tile_grants.json]=fe38b97494ee7a43091323dfd64e7836 )
declare -A TO=( [records.py]=0f3e48caa2aa0b7200c54fe2be4bbb4d [finance_app.py]=7866b1ee6e70d19b5c096ef1b0099bd3 [portal.py]=d9a9dc409b203a4d8dcdd623aa54565f [tile_grants.json]=a5f8b3b1ef40047052b65d9735f02e3f )
declare -A DEST=( [records.py]="$FIN/records.py" [finance_app.py]="$FIN/finance_app.py" [portal.py]="$POR/portal.py" [tile_grants.json]="$POR/tile_grants.json" )
ORDER=(records.py finance_app.py portal.py tile_grants.json)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in records.py portal.py tile_grants.json; do [ "$(m5 "$f")" = "${TO[$f]}" ] || { say "!! [1/8] kit $f is not its pin - nothing installed"; exit 1; }; done
say "[1/8] kit gates green"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED. Seed re-checked:"; "$SPY" -B seed_s340.py "$DBF"; exit 0; fi
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${FROM[$f]}" ] || { say "!! [2/8] ${DEST[$f]} is $(m5 "${DEST[$f]}"), not ${FROM[$f]} - nothing installed"; exit 1; }; done
mkdir -p "$WALK/app" "$WALK/stub" || exit 1
"$SPY" -B patch_finance_app_s340.py --file "$FIN/finance_app.py" --from "${FROM[finance_app.py]}" --out "$WALK/finance_app.py" >/dev/null
"$SPY" -B patch_portal_s340.py --file "$POR/portal.py" --from "${FROM[portal.py]}" --out "$WALK/portal.py" >/dev/null
[ "$(m5 "$WALK/finance_app.py")" = "${TO[finance_app.py]}" ] && [ "$(m5 "$WALK/portal.py")" = "${TO[portal.py]}" ] \
  || { say "!! [2/8] the live bytes + patches do not give the kit's files - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[2/8] live pins exact; live bytes + patches give exactly the kit's files"
"$SPY" -m py_compile records.py seed_s340.py walk_s340.py "$WALK/finance_app.py" && "$VPY" -m py_compile portal.py \
  && "$VPY" -c "import json; assert json.load(open('tile_grants.json',encoding='utf-8'))['version']==23" \
  || { say "!! [3/8] compile/json failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/8] py_compile + json green"
cp -p "$FIN"/*.py "$WALK/app/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/app/" 2>/dev/null
[ -d "$FIN/finance_ui" ] && cp -rp "$FIN/finance_ui" "$WALK/app/"
cp -p "$WALK/finance_app.py" "$WALK/app/finance_app.py"; cp -p records.py "$WALK/app/records.py"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
  || { say "!! [4/8] no scratch copy - nothing installed"; rm -rf "$WALK"; exit 1; }
"$SPY" -B seed_s340.py "$WALK/walk.db" >/dev/null || { say "!! [4/8] seed on the scratch copy failed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd "$WALK/app" && FINANCE_DB="$WALK/walk.db" FINANCE_ALLOW_HEADER_AUTH=1 RECORDS_DRIVE_STUB="$WALK/stub" \
         FINANCE_SSO_DIR="$POR" PETTY_UPLOAD_DIR="$WALK/uploads" timeout 170 "$VPY" -B "$KDIR/walk_s340.py" "$WALK/app" 2>&1 | tail -1 )"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [4/8] walk red: $WOUT - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/8] $WOUT"
declare -A BAK
for f in "${ORDER[@]}"; do BAK[$f]="${DEST[$f]}.bak_S340_$(m5 "${DEST[$f]}" | cut -c1-8)"; \cp -p "${DEST[$f]}" "${BAK[$f]}" || { say "!! [5/8] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }; done
restore() {
  say "!! RED after placing - restoring every file byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "${DEST[$f]}"; done
  systemctl restart clinic-finance clinic-portal || true; sleep 3
  for f in "${ORDER[@]}"; do say "   ${DEST[$f]} $(m5 "${DEST[$f]}")"; done
  exit 1
}
\cp -p records.py "$FIN/records.py" || restore
\cp -p "$WALK/finance_app.py" "$FIN/finance_app.py" || restore
\cp -p portal.py "$POR/portal.py" || restore
\cp -p tile_grants.json "$POR/tile_grants.json" || restore
rm -rf "$WALK"
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || restore; done
say "[5/8] placed, backups beside each file (.bak_S340_<from8>)"
"$SPY" -B seed_s340.py "$DBF" || restore
say "[6/8] checks unit seeded"
systemctl restart clinic-finance || restore
systemctl restart clinic-portal || restore
sleep 4
for s in clinic-finance clinic-portal; do systemctl is-active --quiet "$s" || restore; done
say "[7/8] clinic-finance, clinic-portal active"
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8099/portal)
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/checks)
say "health : finance $c2 · portal $c3 · /finance/checks without a login $c4 (302 expected)"
[ "$c2" = 200 ] && { [ "$c3" = 200 ] || [ "$c3" = 302 ]; } && { [ "$c4" = 302 ] || [ "$c4" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore
say "[8/8] all green"
for f in "${ORDER[@]}"; do md5sum "${DEST[$f]}"; done
say "$KIT: DONE"
