#!/bin/bash
# =============================================================================
#  install_S400_MEDICAL_SALE_CHECK.sh · kit S400_MEDICAL_SALE_CHECK (session 283, Sanjeevni, 25-Sep-2026, D616)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S400_MEDICAL_SALE_CHECK/install_S400_MEDICAL_SALE_CHECK.sh
#
#  THE OWNER (25-Sep-2026): Bhati becomes the checker of the Sanjeevni days -- next morning he gets the days not yet
#  approved, checks Darpan's paper copy and the Marg sheet against the system, flags whether Darpan did his job,
#  enters ONLY the cash Darpan handed (Dr Bhawna by default, one tap for Dr Manoj, date = the sale date). Tile
#  'Medical sale check'. He sees no month total, no other cash part. The owner stays the approver.
#
#  NEW:    /root/finance/sale_check.py + sale_check.html  (unit 'salecheck': maker bhati, checker manoj -- seeded)
#  PATCHED ON THE BOX from the live bytes (make_s400.py; every anchor exactly once; FROM -> TO pins checked):
#          /root/finance/finance_app.py                 70cff498 -> d7ee72c5   (unit map + mount)
#          /root/finance/sanjeevni_day.py               5d16eff5 -> 22a38006   (day panel Checks)
#          /root/finance/sanjeevni_approvals.py         7ab5fec6 -> 5fdfa364   (days API mark; Needs you line)
#          /root/finance/finance_ui/finance_approvals.html 750f89e0 -> 6622587e (one small line per day row)
#          /root/portal/portal.py                       80d6dc44 -> 592ccf99   (the tile)
#          /root/portal/tile_grants.json                7d195476 -> 9231cefa   (v25 -> v26, the tile to bhati)
#  Restarts clinic-finance and clinic-portal only. finance.db backed up first; the seed adds 1 unit + 2 role rows.
# =============================================================================
set -u
KIT="S400_MEDICAL_SALE_CHECK"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"
DBF="${FINANCE_DB:-$FIN/finance.db}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s400_walk_$STAMP"
declare -A FROM=( [finance_app.py]=70cff4981c2ebf554308545fb071f0d4 [sanjeevni_day.py]=5d16eff5b6e2f0fd561e22d91e4794ab
                  [sanjeevni_approvals.py]=7ab5fec63db83af3e11c6ac08599be93 [finance_approvals.html]=750f89e008a89a372af25cf7898a7d17
                  [portal.py]=80d6dc44acc07ebb0b974fb792507fee [tile_grants.json]=7d1954760181b4e36e732a974599fd35 )
declare -A TO=( [finance_app.py]=d7ee72c51564a397f4e847e98eb80ddc [sanjeevni_day.py]=22a38006a4e3be59b47ea091ea1f971f
                [sanjeevni_approvals.py]=5fdfa364dee3dd9dcef9ad5fed3233d9 [finance_approvals.html]=6622587e47faff016bf280d380bd4564
                [portal.py]=592ccf99d02c361d4d5eb580995599c3 [tile_grants.json]=9231cefad0897a64aa127ce4a448f4fe )
declare -A DEST=( [finance_app.py]="$FIN/finance_app.py" [sanjeevni_day.py]="$FIN/sanjeevni_day.py"
                  [sanjeevni_approvals.py]="$FIN/sanjeevni_approvals.py" [finance_approvals.html]="$FIN/finance_ui/finance_approvals.html"
                  [portal.py]="$POR/portal.py" [tile_grants.json]="$POR/tile_grants.json" )
ORDER=(finance_app.py sanjeevni_day.py sanjeevni_approvals.py finance_approvals.html portal.py tile_grants.json)
NEWF=(sale_check.py sale_check.html)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/9] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/9] KIT_ID.txt names another kit - nothing installed"; exit 1; }
say "[1/9] kit gates green"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || ALL=0; done
for f in "${NEWF[@]}"; do [ "$(m5 "$FIN/$f")" = "$(m5 "$f")" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED. Seed re-checked:"; "$SPY" -B seed_s400.py "$DBF"; exit 0; fi
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${FROM[$f]}" ] || { say "!! [2/9] ${DEST[$f]} is $(m5 "${DEST[$f]}"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }; done
say "[2/9] every live file at its FROM pin"
mkdir -p "$WALK/built" "$WALK/new/finance_ui" "$WALK/old/finance_ui" "$WALK/pnew" "$WALK/pold" "$WALK/uploads" "$WALK/stub" || exit 1
"$SPY" -B make_s400.py --finance "$FIN" --portal "$POR" --out "$WALK/built" | sed 's/^/   /' || { say "!! [3/9] the build from the live bytes stopped - nothing installed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/9] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
say "[3/9] live bytes + anchored edits give exactly the kit's six files (pins match)"
( "$SPY" -m py_compile sale_check.py seed_s400.py make_s400.py walk_s400.py "$WALK/built/finance_app.py" "$WALK/built/sanjeevni_day.py" "$WALK/built/sanjeevni_approvals.py" \
  && "$VPY" -m py_compile sale_check.py "$WALK/built/finance_app.py" "$WALK/built/sanjeevni_day.py" "$WALK/built/sanjeevni_approvals.py" "$WALK/built/portal.py" 2>/dev/null \
  && "$VPY" -c "import json,sys; assert json.load(open(sys.argv[1],encoding='utf-8'))['version']==26" "$WALK/built/tile_grants.json" ) \
  || { say "!! [4/9] compile on both pythons / json failed - nothing installed"; rm -rf "$WALK"; exit 1; }
find "$KDIR" "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[4/9] compiles on /usr/bin/python3 and the venv python; grants v26"
for side in new old; do
  cp -p "$FIN"/*.py "$WALK/$side/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/"
done
cp -p "$WALK/built/finance_app.py" "$WALK/built/sanjeevni_day.py" "$WALK/built/sanjeevni_approvals.py" "$WALK/new/"
cp -p "$WALK/built/finance_approvals.html" "$WALK/new/finance_ui/"
cp -p sale_check.py sale_check.html "$WALK/new/"
cp -p "$POR"/*.py "$WALK/pold/"; cp -p "$POR/tile_grants.json" "$WALK/pold/"
cp -p "$POR"/*.py "$WALK/pnew/"; cp -p "$WALK/built/portal.py" "$WALK/built/tile_grants.json" "$WALK/pnew/"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/scratch.db" \
  || { say "!! [5/9] no scratch copy of the database - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd "$WALK" && FINANCE_DB="$WALK/scratch.db" FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR="$POR" PETTY_UPLOAD_DIR="$WALK/uploads" RECORDS_DRIVE_STUB="$WALK/stub" \
         timeout 600 "$VPY" -B "$KDIR/walk_s400.py" --app "$WALK/new" --old "$WALK/old" --db "$WALK/scratch.db" --portal-new "$WALK/pnew" --portal-old "$WALK/pold" 2>&1 )"
echo "$WOUT" | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S400 GREEN" || { say "!! [5/9] walk red - nothing installed"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$WALK"; exit 1; }
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[5/9] walk green on a scratch copy of the live database (above)"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$FIN/finance.db.bak_S400_$STAMP" \
  || { say "!! [6/9] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do BAK[$f]="${DEST[$f]}.bak_S400_$(m5 "${DEST[$f]}" | cut -c1-8)"; \cp -p "${DEST[$f]}" "${BAK[$f]}" || { say "!! [6/9] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }; done
say "[6/9] finance.db.bak_S400_$STAMP made; .bak_S400_<from8> beside each of the six files"
restore() {
  say "!! RED after placing - restoring every file byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "${DEST[$f]}"; done
  rm -f "$FIN/sale_check.py" "$FIN/sale_check.html"
  systemctl restart clinic-finance clinic-portal || true; sleep 4
  for f in "${ORDER[@]}"; do say "   ${DEST[$f]} $(m5 "${DEST[$f]}")"; done
  say "   healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz) · the database backup stays: $FIN/finance.db.bak_S400_$STAMP"
  rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do \cp -p "$WALK/built/$f" "${DEST[$f]}" || restore; done
\cp -p sale_check.py "$FIN/sale_check.py" && \cp -p sale_check.html "$FIN/sale_check.html" && chmod 644 "$FIN/sale_check.py" "$FIN/sale_check.html" || restore
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || restore; done
for f in "${NEWF[@]}"; do [ "$(m5 "$FIN/$f")" = "$(m5 "$f")" ] || restore; done
say "[7/9] placed; every md5 read back = the kit's pin"
"$SPY" -B seed_s400.py "$DBF" || restore
say "[8/9] salecheck unit seeded (bhati maker, manoj checker; bhati has no medical row)"
systemctl restart clinic-finance || restore
systemctl restart clinic-portal || restore
sleep 5
for s in clinic-finance clinic-portal; do systemctl is-active --quiet "$s" || restore; done
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8099/portal)
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/salecheck)
say "health : finance healthz $c2 · portal $c3 · /finance/salecheck without a login $c4 (302 = the login gate, expected)"
[ "$c2" = 200 ] && { [ "$c3" = 200 ] || [ "$c3" = 302 ]; } && { [ "$c4" = 302 ] || [ "$c4" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore
say "[9/9] clinic-finance + clinic-portal active, healthz 200, nothing 'NOT mounted'"
rm -rf "$WALK"
for f in "${ORDER[@]}"; do md5sum "${DEST[$f]}"; done
for f in "${NEWF[@]}"; do md5sum "$FIN/$f"; done
say "$KIT: DONE -- https://followup.dr-manoj.in/finance/salecheck (tile 'Medical sale check' for bhati and the owner)"
