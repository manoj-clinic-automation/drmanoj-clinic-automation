#!/bin/bash
# =============================================================================
#  install_S402_SALECHECK_RETURNS.sh · kit S402_SALECHECK_RETURNS (session 283, Sanjeevni, 25-Sep-2026)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S402_SALECHECK_RETURNS/install_S402_SALECHECK_RETURNS.sh
#
#  THE OWNER (25-Sep-2026): Bhati sees the day's sale returns at a glance -- collapsible: count and total; expand to bill
#  no, name, amount. No more detail than that. Label: the English words "Sale return".
#
#  PATCHED ON THE BOX from the live bytes (make_s402.py; every anchor exactly once; FROM -> TO pins checked):
#          /root/finance/sale_check.py     81cccad3 (S400) -> 92ca5cb2d3a4388bbf6a29e35af2d492
#          /root/finance/sale_check.html   4202d11b (S400) -> 9c70af26456092285a9545083365bfff
#  Restarts clinic-finance only. finance.db backed up first (rule 6); nothing in it changes.
#  The walk: walk_s402.py on a scratch copy, then S400's own walk re-run on the patched files (must stay green).
# =============================================================================
set -u
KIT="S402_SALECHECK_RETURNS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
K400="$(cd "$KDIR/../S400_MEDICAL_SALE_CHECK" 2>/dev/null && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"
DBF="${FINANCE_DB:-$FIN/finance.db}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s402_walk_$STAMP"
declare -A FROM=( [sale_check.py]=81cccad3c48a894298b3694a7b3b5118 [sale_check.html]=4202d11baee4c9309a518e3aed8cf817 )
declare -A TO=( [sale_check.py]=92ca5cb2d3a4388bbf6a29e35af2d492 [sale_check.html]=9c70af26456092285a9545083365bfff )
ORDER=(sale_check.py sale_check.html)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$K400" ] && [ -f "$K400/walk_s400.py" ] && [ -f "$K400/seed_s400.py" ] || { say "!! [1/8] the S400 kit (its walk) must sit beside this kit - nothing installed"; exit 1; }
say "[1/8] kit gates green (S400's walk found at $K400)"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED (both files at their S402 pins). Nothing to do."; exit 0; fi
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/8] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }; done
say "[2/8] both live files at their FROM pins (S400)"
mkdir -p "$WALK/built" "$WALK/new/finance_ui" "$WALK/old/finance_ui" "$WALK/old0/finance_ui" "$WALK/pnew" "$WALK/pold" "$WALK/uploads" "$WALK/stub" || exit 1
"$SPY" -B make_s402.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /' || { say "!! [3/8] the build from the live bytes stopped - nothing installed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/8] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
say "[3/8] live bytes + anchored edits give exactly the kit's two files (pins match)"
( "$SPY" -m py_compile make_s402.py walk_s402.py "$WALK/built/sale_check.py" && "$VPY" -m py_compile "$WALK/built/sale_check.py" ) \
  || { say "!! [4/8] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
find "$KDIR" "$K400" "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[4/8] compiles on /usr/bin/python3 and the venv python"
for side in new old old0; do
  cp -p "$FIN"/*.py "$WALK/$side/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/"
done
cp -p "$WALK/built/sale_check.py" "$WALK/built/sale_check.html" "$WALK/new/"
# old0 = the box BEFORE S400 (its .bak_S400 files), the negative control S400's own walk expects
for pair in "finance_app.py:70cff498" "sanjeevni_day.py:5d16eff5" "sanjeevni_approvals.py:7ab5fec6"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S400_$h" "$WALK/old0/$f" || { say "!! [5/8] $f.bak_S400_$h missing - cannot rebuild the pre-S400 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/finance_ui/finance_approvals.html.bak_S400_750f89e0" "$WALK/old0/finance_ui/finance_approvals.html" || { rm -rf "$WALK"; exit 1; }
rm -f "$WALK/old0/sale_check.py" "$WALK/old0/sale_check.html"
cp -p "$POR"/*.py "$WALK/pnew/"; cp -p "$POR/tile_grants.json" "$WALK/pnew/"
cp -p "$POR"/*.py "$WALK/pold/"; cp -p "$POR/portal.py.bak_S400_80d6dc44" "$WALK/pold/portal.py"; cp -p "$POR/tile_grants.json.bak_S400_7d195476" "$WALK/pold/tile_grants.json"
copydb "$DBF" "$WALK/scratch1.db" && copydb "$DBF" "$WALK/scratch2.db" || { say "!! [5/8] no scratch copy - nothing installed"; rm -rf "$WALK"; exit 1; }
WENV="FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR=$POR PETTY_UPLOAD_DIR=$WALK/uploads RECORDS_DRIVE_STUB=$WALK/stub"
WOUT="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch1.db" timeout 600 "$VPY" -B "$KDIR/walk_s402.py" --app "$WALK/new" --old "$WALK/old" --db "$WALK/scratch1.db" 2>&1 )"
echo "$WOUT" | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S402 GREEN" || { say "!! [5/8] walk red - nothing installed"; find "$KDIR" "$K400" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$WALK"; exit 1; }
say "[5/8] walk_s402 green on a scratch copy of the live database (above)"
W400="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch2.db" timeout 600 "$VPY" -B "$K400/walk_s400.py" --app "$WALK/new" --old "$WALK/old0" --db "$WALK/scratch2.db" --portal-new "$WALK/pnew" --portal-old "$WALK/pold" 2>&1 )"
echo "$W400" | grep -E '^(WALK_S400|  FAIL|-- )' | sed 's/^/   /'
echo "$W400" | grep -q "^WALK_S400 GREEN" || { say "!! [6/8] S400's walk went red on the patched files - nothing installed"; echo "$W400" | tail -20; find "$KDIR" "$K400" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$WALK"; exit 1; }
find "$KDIR" "$K400" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[6/8] S400's own walk re-run on the patched files: still green (above)"
copydb "$DBF" "$FIN/finance.db.bak_S402_$STAMP" || { say "!! [7/8] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do BAK[$f]="$FIN/$f.bak_S402_$(m5 "$FIN/$f" | cut -c1-8)"; \cp -p "$FIN/$f" "${BAK[$f]}" || { say "!! [7/8] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }; done
restore() {
  say "!! RED after placing - restoring both files byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "$FIN/$f"; done
  systemctl restart clinic-finance || true; sleep 4
  for f in "${ORDER[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f")"; done
  say "   healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz) · the database backup stays: $FIN/finance.db.bak_S402_$STAMP"
  rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do \cp -p "$WALK/built/$f" "$FIN/$f" && chmod 644 "$FIN/$f" || restore; done
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore; done
say "[7/8] finance.db.bak_S402_$STAMP made; .bak_S402_<from8> beside both files; placed; md5 read back = the kit's pins"
systemctl restart clinic-finance || restore
sleep 5
systemctl is-active --quiet clinic-finance || restore
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/salecheck)
say "health : finance healthz $c2 · /finance/salecheck without a login $c4 (302 = the login gate, expected)"
[ "$c2" = 200 ] && { [ "$c4" = 302 ] || [ "$c4" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore
say "[8/8] clinic-finance active, healthz 200, nothing 'NOT mounted'"
rm -rf "$WALK"
for f in "${ORDER[@]}"; do md5sum "$FIN/$f"; done
say "$KIT: DONE -- https://followup.dr-manoj.in/finance/salecheck"
