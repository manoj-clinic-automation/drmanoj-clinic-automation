#!/bin/bash
# =============================================================================
#  install_S444_STAFF_SAFE.sh · kit S444_STAFF_SAFE (session 283, 01-Oct-2026, D647 · D648 · F-669 F-670 F-671 F-672)
#  Sanjeevni + the portal (PARENT'S, declared: clinic_sso.py, portal.py, tile_grants.json)
#
#  Run by (one line on the VPS, holding the build lock /root/deploy/.claude_code_build.lock with owner S444_STAFF_SAFE):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S444_STAFF_SAFE/install_S444_STAFF_SAFE.sh
#  (DRY=1 runs every gate, the build and every walk on scratch copies, and places nothing. KITS=<dir> names the folder holding the
#   earlier kits when this kit runs from a copy; DUTYMAP=<file> the DUTY_MAP.json when it is not at ../../claude_code_briefs.
#   NOPIN=1, with DRY=1 only, prints the built md5s instead of refusing on a TO mismatch.)
#
#  THE OWNER, 01-Oct: "Staff tend to forget things and then issues crop up again and again -- rectify this properly."
#   * One sign-in name whatever is typed ('Amir', 'AMIR', ' amir ' -> amir), and every session already issued reads the same way.
#   * A one-job login opens on its job (amir -> /finance/amir); a login with no work set is told so in Hindi, with Sign out.
#   * Amir's bill line shows Marg's amount beside the paper's; "Meri entry galat thi" raises no claim and clears itself.
#   * The salt list cannot be silently forgotten; the count's vouchers stand on every step of Amir's day ("Marg sudhar").
#   * Every slip becomes one line for the owner (Needs-you), each gone by itself when put right; the duty map's orphan duties too.
#
#  PATCHED ON THE BOX from the live bytes (make_s444.py; every anchor exactly once; FROM -> TO pins checked):
#     /root/portal/clinic_sso.py   /root/portal/portal.py   /root/portal/tile_grants.json      (PARENT'S, declared)
#     /root/finance/amir_day.py  amir_salts.py  reports_tile.py  sanjeevni_approvals.py  stock_app.py  porders.py
#  DATA (finance.db, backed up first): four settings rows (INSERT OR IGNORE); KEDAR 195 (27-Sep) by the owner's ruling -- claim #1
#     settled 'amir_own_entry', the answer 'self'; two additive tables made on first use (amir_self_wait, stock_board_open).
#  RESTARTS every service that imports clinic_sso: clinic-portal, clinic-finance, assetapp, attendance-dashboard, staff-register,
#     staff-ledger. purchase_app.py is READ ONLY (its read-only door to assets.db). Nothing else is touched.
# =============================================================================
set -u
KIT="S444_STAFF_SAFE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
KITS="${KITS:-$KDIR/..}"
DUTYMAP="${DUTYMAP:-$KDIR/../../claude_code_briefs/DUTY_MAP.json}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"; AST="$ROOT/assetapp"; SHR="$ROOT/shared"
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s444_walk_$STAMP"
declare -A FROM=( [clinic_sso.py]=2bc6ba15e52512d3f866536e758079ed [portal.py]=626838cdf624446f90ac3061a79b6523
                  [tile_grants.json]=acc9cc1bad61b3f9a77f6f4f56b15476 [amir_day.py]=068a3988e296f6579e2e780b2e4f623b
                  [amir_salts.py]=8d6ef482573e56ae8676712a82a2a563 [reports_tile.py]=2798436712be69eb3c4486a0913e38f4
                  [sanjeevni_approvals.py]=3999c4ced7aaf098eeeb00d696014cab [stock_app.py]=4f2625c0a88e450c88e0b23d499d6fa8
                  [porders.py]=af4a6f57b6c7522784fdb53d6233d50b )
declare -A TO=( [clinic_sso.py]=6344e09c07c0506924d19824d5604b3a [portal.py]=ba61e35a9a2a2722d19304d791e255ca [tile_grants.json]=392e6d89b09bcc7127cc541224771206
                [amir_day.py]=2b497142efdb1a3d1b84e9f05cbf59ac [amir_salts.py]=d8d9ba772650a4d804add6953790d14d [reports_tile.py]=8a9870414cf299b0396bec4bc937ef04
                [sanjeevni_approvals.py]=d2c550401ebfb7716126d24a09fae78f [stock_app.py]=c0120fb67c78105fe797982fcb6ab644 [porders.py]=3620b374a8fb3ac4988b8e6525795f84 )
declare -A DIR=( [clinic_sso.py]="$POR" [portal.py]="$POR" [tile_grants.json]="$POR" [amir_day.py]="$FIN" [amir_salts.py]="$FIN"
                 [reports_tile.py]="$FIN" [sanjeevni_approvals.py]="$FIN" [stock_app.py]="$FIN" [porders.py]="$FIN" )
ORDER=(amir_day.py amir_salts.py reports_tile.py sanjeevni_approvals.py stock_app.py porders.py tile_grants.json clinic_sso.py portal.py)
FINF=(amir_day.py amir_salts.py reports_tile.py sanjeevni_approvals.py stock_app.py porders.py)
SVCS=(clinic-portal clinic-finance assetapp attendance-dashboard staff-register staff-ledger)
declare -A PORT=( [attendance-dashboard]=8042 [staff-register]=8044 [staff-ledger]=8043 )
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/10] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/10] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$VPY" -c "import flask" 2>/dev/null || { say "!! [1/10] the venv python lacks flask; nothing installed"; exit 1; }
for k in "$KITS/S246_AMIR_LIST_REOPEN/walk_amir_reopen_s246.py" "$KITS/S243_AMIR_VISIT/walk_amir_visit_s243.py" "$KITS/S241_AMIR_SALTS/selftest_amir_day.py" \
         "$KITS/S440_SCAN_FLOW/walk_s440.py" "$DUTYMAP" "$DBF" "$ADB"; do
  [ -f "$k" ] || { say "!! [1/10] $k must be reachable (KITS=$KITS, DUTYMAP=$DUTYMAP) - nothing installed"; exit 1; }
done
say "[1/10] kit gates green (SUMS, KIT_ID, the venv's flask, the earlier walks, DUTY_MAP.json, finance.db, assets.db)"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "${DIR[$f]}/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then
  say "-- ALREADY INSTALLED: the nine files are at the kit's pins; $(for s in "${SVCS[@]}"; do printf '%s %s · ' "$s" "$(systemctl is-active "$s")"; done)finance healthz $(health http://127.0.0.1:8106/finance/healthz)"
  exit 0
fi
for f in "${ORDER[@]}"; do [ "$(m5 "${DIR[$f]}/$f")" = "${FROM[$f]}" ] || { say "!! [2/10] ${DIR[$f]}/$f is $(m5 "${DIR[$f]}/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }; done
say "[2/10] the nine live files at their FROM pins"
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s444.py --portal "$POR" --finance "$FIN" --out "$WALK/built" | sed 's/^/   /' || { say "!! [3/10] the build from the live bytes stopped - nothing installed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do [ -s "$WALK/built/$f" ] || { say "!! [3/10] the build wrote no $f - nothing installed"; rm -rf "$WALK"; exit 1; }; done
if [ "${DRY:-0}" = 1 ] && [ "${NOPIN:-0}" = 1 ]; then
  for f in "${ORDER[@]}"; do say "   built $f $(m5 "$WALK/built/$f")"; done
else
  for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/10] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
  say "[3/10] live bytes + anchored edits give exactly the kit's files (nine pins match)"
fi
"$SPY" -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); assert d['version']==31 and d['users']['amir']['home']=='/finance/amir'" "$WALK/built/tile_grants.json" \
  || { say "!! [4/10] the built tile_grants.json is not v31 with amir's home - nothing installed"; rm -rf "$WALK"; exit 1; }
PYS="make_s444.py walk_s444.py walk_old_s444.py walk_s440_s444.py names_s444.py apply_s444.py"
for f in "${ORDER[@]}"; do case "$f" in *.py) PYS="$PYS $WALK/built/$f";; esac; done
( "$SPY" -m py_compile $PYS 2>/dev/null && "$VPY" -m py_compile $PYS 2>/dev/null ) || { say "!! [4/10] compile on both pythons failed - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
"$SPY" -B "$WALK/built/clinic_sso.py" --selftest | sed 's/^/   /'
"$SPY" -B "$WALK/built/clinic_sso.py" --selftest | grep -q "PASSED" || { say "!! [4/10] clinic_sso selftest red - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
( cd "$WALK/built" && "$VPY" -B -c "import sys; sys.path.insert(0,'.'); import reports_tile; sys.exit(reports_tile.selftest())" > "$WALK/rt.txt" 2>&1 ) \
  || { tail -5 "$WALK/rt.txt"; say "!! [4/10] reports_tile's own selftest red on the built file - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
say "   $(tail -1 "$WALK/rt.txt")"
clean
say "[4/10] compiles on /usr/bin/python3 and the venv python; clinic_sso's selftest and reports_tile's own selftest green on the built files"
NOUT="$("$SPY" -B names_s444.py --portal "$POR" --finance-db "$DBF" --assets-db "$ADB" 2>&1)"; NRC=$?
echo "$NOUT" | sed 's/^/   /'
[ "$NRC" = 0 ] || { say "!! [5/10] a live name is not small letters (above) - STOP, nothing installed"; rm -rf "$WALK"; exit 1; }
say "[5/10] the name check on the live stores: every name already small letters"
for side in fin_new fin_old; do
  mkdir -p "$WALK/$side/finance_ui" "$WALK/$side/spine"
  cp -p "$FIN"/*.py "$WALK/$side/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$WALK/$side/spine/" 2>/dev/null
done
for side in por_new por_old; do
  mkdir -p "$WALK/$side"
  for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$WALK/$side/"; done   # never the live secret, never the user store
  cp -p "$POR/tile_grants.json" "$WALK/$side/"
done
for f in "${FINF[@]}"; do cp -p "$WALK/built/$f" "$WALK/fin_new/$f"; done
for f in clinic_sso.py portal.py tile_grants.json; do cp -p "$WALK/built/$f" "$WALK/por_new/$f"; done
mkdir -p "$WALK/ast" "$WALK/shared"; cp -p "$AST"/*.py "$AST"/*.js "$WALK/ast/"; cp -p "$SHR"/*.py "$WALK/shared/" 2>/dev/null
copydb "$DBF" "$WALK/scratch.db" && copydb "$ADB" "$WALK/scratch_assets.db" || { say "!! [6/10] no scratch copies - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd "$WALK" && timeout 1800 "$VPY" -B "$KDIR/walk_s444.py" --fin-new "$WALK/fin_new" --fin-old "$WALK/fin_old" --por-new "$WALK/por_new" --por-old "$WALK/por_old" \
         --ast "$WALK/ast" --shared "$WALK/shared" --db "$WALK/scratch.db" --adb "$WALK/scratch_assets.db" --kit "$KDIR" --duty-map "$DUTYMAP" \
         --live-portal "$POR" --live-db "$DBF" --live-adb "$ADB" 2>&1 )"
echo "$WOUT" | sed -E 's/[0-9]{10,}/##########/g' | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S444 GREEN" || { say "!! [6/10] walk_s444 red - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[6/10] walk_s444 green on scratch copies of finance.db and assets.db, its negative control red on the box as it is (above)"
OOUT="$( cd "$WALK" && timeout 1800 "$VPY" -B "$KDIR/walk_old_s444.py" --live "$WALK/fin_old" --new "$WALK/fin_new" --kits "$KITS" --work "$WALK/old" 2>&1 )"
echo "$OOUT" | sed -E 's/[0-9]{10,}/##########/g' | cut -c1-400 | sed 's/^/   /'
echo "$OOUT" | grep -q "^WALK_OLD_S444 GREEN" || { say "!! [7/10] an earlier Amir walk is red on the patched files - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
# S440's walk: the box + S444 against S440's own control (its .bak_S440 files), on fresh scratch copies
W4="$WALK/w440"; mkdir -p "$W4/new" "$W4/old" "$W4/ast_old" "$W4/uploads" "$W4/stub" || exit 1
cp -rp "$WALK/fin_new/." "$W4/new/"; cp -rp "$WALK/fin_old/." "$W4/old/"
for p in porders.py:64465af0 porders.html:124c4d41 purchase_app.py:ebe38c68; do n="${p%%:*}"; h="${p##*:}"; cp -p "$FIN/$n.bak_S440_$h" "$W4/old/$n" || { say "!! [7/10] $n.bak_S440_$h missing - S440's control cannot be rebuilt"; rm -rf "$WALK"; exit 1; }; done
cp -p "$AST"/*.py "$AST"/*.js "$W4/ast_old/"; cp -p "$AST/asset_register.py.bak_S440_1f80773b" "$W4/ast_old/asset_register.py" || { say "!! [7/10] asset_register.py.bak_S440_1f80773b missing"; rm -rf "$WALK"; exit 1; }
copydb "$DBF" "$W4/scratch440.db" && copydb "$ADB" "$W4/assets_scratch440.db" || { rm -rf "$WALK"; exit 1; }
[ -f "$FIN/spine/spine.db" ] && copydb "$FIN/spine/spine.db" "$W4/spine_scratch.db"
W440="$( cd "$W4" && env FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR="$WALK/por_new" PETTY_UPLOAD_DIR="$W4/uploads" RECORDS_DRIVE_STUB="$W4/stub" MARG_ARCHIVE="$ROOT/marg_ingest/archive" \
         SPINE_DB="$W4/spine_scratch.db" FINANCE_DB="$W4/scratch440.db" PYTHONPATH="$WALK/shared" timeout 1800 "$VPY" -B "$KDIR/walk_s440_s444.py" --k440 "$KITS/S440_SCAN_FLOW" --work "$W4/run" -- \
         --app "$W4/new" --old "$W4/old" --assets-new "$WALK/ast" --assets-old "$W4/ast_old" --db "$W4/scratch440.db" --assets-db "$W4/assets_scratch440.db" 2>&1 )"
echo "$W440" | grep -E '^(WALK_S440|  FAIL|-- S440)' | sed -E 's/[0-9]{10,}/##########/g' | cut -c1-400 | sed 's/^/   /'
echo "$W440" | grep -q "^WALK_S440 GREEN" || { say "!! [7/10] S440's walk (two assertions adjusted, A8 A9) red on the patched files - nothing installed"; echo "$W440" | tail -15; clean; rm -rf "$WALK"; exit 1; }
clean
say "[7/10] re-run on the patched files: S246 / S245 / S244, S243 and S241's walks (adjustments A1-A7 named; S241's selftest: the same eight superseded asserts as before S444, no other), S440's walk (A8 A9 named): green"
if [ "${DRY:-0}" = 1 ]; then
  say "-- DRY RUN: every gate, the build and every walk green; NOTHING placed, nothing restarted"; clean; rm -rf "$WALK"; exit 0
fi
[ -d "$LOCK" ] && [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [8/10] the build lock $LOCK is not held by $KIT - nothing installed (CLAUDE.md: one build at a time)"; rm -rf "$WALK"; exit 1; }
declare -A HB
for s in "${!PORT[@]}"; do HB[$s]="$(health "http://127.0.0.1:${PORT[$s]}/")"; done
copydb "$DBF" "$FIN/finance.db.bak_S444_$STAMP" || { say "!! [8/10] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do BAK[$f]="${DIR[$f]}/$f.bak_S444_$(m5 "${DIR[$f]}/$f" | cut -c1-8)"; \cp -p "${DIR[$f]}/$f" "${BAK[$f]}" || { say "!! [8/10] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }; done
say "[8/10] finance.db.bak_S444_$STAMP made (backup API); .bak_S444_<from8> beside the nine files; the lock is held by $KIT"
restore() {
  say "!! RED after placing ($1) - restoring the nine files byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "${DIR[$f]}/$f"; done
  for s in "${SVCS[@]}"; do systemctl restart "$s" || true; done; sleep 7
  for f in "${ORDER[@]}"; do say "   ${DIR[$f]}/$f $(m5 "${DIR[$f]}/$f")"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $(for s in "${SVCS[@]}"; do printf '%s %s · ' "$s" "$(systemctl is-active "$s")"; done)the database backup stays: $FIN/finance.db.bak_S444_$STAMP"
  clean; rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do \cp "$WALK/built/$f" "${DIR[$f]}/$f" || restore "copy"; done
for f in "${ORDER[@]}"; do [ "$(m5 "${DIR[$f]}/$f")" = "${TO[$f]}" ] || restore "md5 read-back"; done
say "[9/10] placed; all nine md5s read back = the kit's pins"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
for s in "${SVCS[@]}"; do systemctl restart "$s" || restore "restart $s"; done
sleep 8
for s in "${SVCS[@]}"; do systemctl is-active --quiet "$s" || restore "$s not active"; done
c1=$(health http://127.0.0.1:8106/finance/healthz); c2=$(health http://127.0.0.1:8106/finance/amir); c3=$(health http://127.0.0.1:8106/finance/porders)
p1=$(health http://127.0.0.1:8099/portal/health); p2=$(health http://127.0.0.1:8099/portal); p3=$(health http://127.0.0.1:8099/portal/login)
a1=$(health http://127.0.0.1:8030/login); a2=$(health http://127.0.0.1:8030/intake)
say "health : finance healthz $c1 · /finance/amir $c2 · /finance/porders $c3 (302/401 = the login gate, expected) · portal /portal/health $p1 · /portal $p2 (302) · /portal/login $p3"
say "         asset app login $a1 · /intake $a2 (302) · $(for s in "${!PORT[@]}"; do printf '%s :%s / %s (was %s) · ' "$s" "${PORT[$s]}" "$(health "http://127.0.0.1:${PORT[$s]}/")" "${HB[$s]}"; done)"
[ "$c1" = 200 ] && { [ "$c2" = 302 ] || [ "$c2" = 401 ]; } && { [ "$c3" = 302 ] || [ "$c3" = 401 ]; } || restore "finance health"
[ "$p1" = 200 ] && [ "$p2" = 302 ] && [ "$p3" = 200 ] || restore "portal health"
[ "$a1" = 200 ] && [ "$a2" = 302 ] || restore "asset app health"
for s in "${!PORT[@]}"; do [ "$(health "http://127.0.0.1:${PORT[$s]}/")" = "${HB[$s]}" ] || restore "$s answers differently after the restart"; done
journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
for s in clinic-portal assetapp attendance-dashboard staff-register staff-ledger; do
  JR="$(journalctl -u "$s" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')"
  [ "$JR" = 0 ] || { journalctl -u "$s" --since "$T0" --no-pager | grep -i -A6 'Traceback\|Error' | head -30; restore "$s journal: $JR error line(s)"; }
done
say "[10/10] the six services active; healthz 200; the pages behind their gates; nothing 'NOT mounted'; no traceback in any journal"
AOUT="$( cd "$FIN" && FINANCE_DB="$DBF" DUTY_MAP_JSON="$DUTYMAP" "$VPY" -B "$KDIR/apply_s444.py" --finance "$FIN" --db "$DBF" 2>&1 )" || { echo "$AOUT" | tail -20; restore "the data step"; }
echo "$AOUT" | sed 's/^/   /'
echo "$AOUT" | grep -q "^S444 apply done" || restore "the data step"
say "-- the data step ran on the live database (above): the settings, KEDAR 195 by the owner's ruling, and what Amir and the owner now see"
clean; rm -rf "$WALK"
for f in "${ORDER[@]}"; do md5sum "${DIR[$f]}/$f"; done
say "$KIT: DONE -- https://followup.dr-manoj.in/portal · https://followup.dr-manoj.in/finance/amir/day · https://followup.dr-manoj.in/finance/approvals"
