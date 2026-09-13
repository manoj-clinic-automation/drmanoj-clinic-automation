#!/bin/bash
# mock_install_reports_tile_s243.sh -- the installer's proofs on a throw-away ROOT.  Nothing live is touched.
#   1 refuses a wrong finance_app pin (nothing placed)        2 installs on the true pins (both services)
#   3 second run says ALREADY INSTALLED                       4 healthz failure -> rollback of all five files
#   5 lineage: finance_app already carrying S243_SCREEN_FIXES + S243_DARPAN_KAL, hub carrying DARPAN_KAL
#     -> accepted; the .bak names carry THOSE pins; the seed adds shavez once and a re-run changes nothing
#   6 refuses a wrong portal.py pin (nothing placed, finance untouched)
# Needs the 13-Sep capture (FIN_SRC / MI_SRC / PORTAL_SRC) and, for proof 5, the sibling kits (SF_PATCHER, KAL_KIT).
#   FIN_SRC=/home/claude/S243/capture/tree/root/finance PORTAL_SRC=/home/claude/S243/capture/tree/root/portal \
#   MI_SRC=/home/claude/S243/capture/tree/root/marg_ingest bash mock_install_reports_tile_s243.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
FIN_SRC="${FIN_SRC:-/root/finance}"
PORTAL_SRC="${PORTAL_SRC:-/root/portal}"
MI_SRC="${MI_SRC:-/root/marg_ingest}"
SF_PATCHER="${SF_PATCHER:-$(dirname "$KDIR")/S243_SCREEN_FIXES/patch_finance_daily_s243.py}"
KAL_KIT="${KAL_KIT:-$(dirname "$KDIR")/S243_DARPAN_KAL}"
P=0; F=0
chk() { if [ "$2" -eq 0 ]; then P=$((P+1)); echo "  PASS  $1"; else F=$((F+1)); echo "  FAIL  $1"; fi; }

build_root() {   # $1 = root dir
  local M="$1"
  mkdir -p "$M/root/finance/finance_ui" "$M/root/portal" "$M/root/marg_ingest" "$M/etc/systemd/system" "$M/bin"
  for f in finance_app.py finance_ingest.py finance_returns.py finance_upi.py marg_report.py finance_identity.py darpan_app.py \
           darpan_card.html darpan_corrections.html returns_desk.py returns_desk.html finance_returns_audit.py finance_money.py \
           finance_returns_escalate.py finance_intent.py staff_pages.py joiner_app.py stock_app.py finance_clinic_day.py \
           clinic_register.py purchase_app.py bank_mpr_status.py clinic_day_pdf.py marg_door.py amir_day.py amir_salts.py \
           export_watch.py marg_take.py marg_spine.py sale_bill.py docterz_ingest.py docterz_day.py \
           finance_schema.sql finance_returns.sql purchase_schema.sql; do
    [ -f "$FIN_SRC/$f" ] && cp "$FIN_SRC/$f" "$M/root/finance/$f"
  done
  cp "$FIN_SRC/finance_ui/finance_approvals.html" "$M/root/finance/finance_ui/"
  for f in finance_daily.html finance_review.html finance_entry.html finance_workbench.html finance_entry_clinic.html; do echo stub > "$M/root/finance/finance_ui/$f"; done
  cp "$PORTAL_SRC/portal.py" "$PORTAL_SRC/tile_grants.json" "$M/root/portal/"
  for f in marg_ingest.py marg_router.py xlsx_stdlib.py signatures.json; do [ -f "$MI_SRC/$f" ] && cp "$MI_SRC/$f" "$M/root/marg_ingest/$f"; done
  python3 - "$M/root/finance" <<'EOF'
import sqlite3, sys
d = sys.argv[1]
con = sqlite3.connect(d + "/finance.db")
con.executescript(open(d + "/finance_schema.sql").read()); con.executescript(open(d + "/finance_returns.sql").read()); con.commit()
EOF
  cat > "$M/etc/systemd/system/clinic-finance.service" <<EOF
[Service]
Environment=FINANCE_DB=$M/root/finance/finance.db
Environment=FINANCE_UI_DIR=$M/root/finance/finance_ui
Environment=FINANCE_ALLOW_HEADER_AUTH=1
Environment=FINANCE_PORTAL_LOGIN=/portal
Environment=FINANCE_MARG_TOKEN=DUMMY-TOKEN-PUT-HERE
Environment=FINANCE_SCAN_DIR=$M/scans
Environment=FINANCE_UPI_DIR=$M/upi
EOF
  cat > "$M/bin/systemctl" <<'EOF'
#!/bin/bash
echo "[mock systemctl] $*" >&2
case "$1" in show) exit 0;; is-active) exit 0;; *) exit 0;; esac
EOF
  cat > "$M/bin/curl" <<'EOF'
#!/bin/bash
if [ -n "${MOCK_HZ_FAIL:-}" ]; then printf '000'; else printf '200'; fi
EOF
  chmod +x "$M/bin/systemctl" "$M/bin/curl"
}

M="$(mktemp -d /tmp/mock_rpt_XXXXXX)"
build_root "$M"
export PATH="$M/bin:$PATH"
FA0="$(md5sum "$M/root/finance/finance_app.py" | cut -c1-32)"
HUB0="$(md5sum "$M/root/finance/finance_ui/finance_approvals.html" | cut -c1-32)"
P0="$(md5sum "$M/root/portal/portal.py" | cut -c1-32)"
G0="$(md5sum "$M/root/portal/tile_grants.json" | cut -c1-32)"
echo "== mock root $M  finance_app $FA0  hub $HUB0  portal $P0  grants $G0"
unchanged() { [ "$(md5sum "$M/root/finance/finance_app.py" | cut -c1-32)" = "$FA0" ] && [ "$(md5sum "$M/root/finance/finance_ui/finance_approvals.html" | cut -c1-32)" = "$HUB0" ] \
  && [ "$(md5sum "$M/root/portal/portal.py" | cut -c1-32)" = "$P0" ] && [ "$(md5sum "$M/root/portal/tile_grants.json" | cut -c1-32)" = "$G0" ] && [ ! -f "$M/root/finance/reports_tile.py" ]; }

echo "---- proof 1: wrong finance_app pin is refused"
ROOT="$M" PY=python3 PY_SMOKE=python3 MOCK_FA_PIN=00000000000000000000000000000000 bash "$KDIR/install_S243_REPORTS_TILE.sh" > "$M/p1.log" 2>&1; rc=$?
grep -q "neither the pin" "$M/p1.log" && [ $rc -ne 0 ] && unchanged; chk "refused, nothing placed" $?

echo "---- proof 6: wrong portal.py pin is refused"
ROOT="$M" PY=python3 PY_SMOKE=python3 MOCK_PORTAL_PIN=00000000000000000000000000000000 bash "$KDIR/install_S243_REPORTS_TILE.sh" > "$M/p6.log" 2>&1; rc=$?
grep -q "live portal.py is" "$M/p6.log" && [ $rc -ne 0 ] && unchanged; chk "refused, nothing placed (finance untouched too)" $?

echo "---- proof 2: install on the true pins"
ROOT="$M" PY=python3 PY_SMOKE=python3 bash "$KDIR/install_S243_REPORTS_TILE.sh" > "$M/p2.log" 2>&1; rc=$?
[ $rc -eq 0 ] && grep -q "INSTALLED" "$M/p2.log"; chk "installer exit 0, INSTALLED" $?
grep -qF "S243_REPORTS_TILE begin" "$M/root/finance/finance_app.py" && grep -qF "S243 reports tile" "$M/root/finance/finance_ui/finance_approvals.html" \
  && grep -qF '"name": "Aaj ki reports"' "$M/root/portal/portal.py" && [ "$(md5sum "$M/root/portal/tile_grants.json" | cut -c1-32)" = "c9ee95c39bb805086b79d95327b2b626" ]; chk "all four files carry the change; grants v13" $?
[ -f "$M/root/finance/finance_app.py.bak_S243_${FA0:0:8}" ] && [ -f "$M/root/finance/finance_ui/finance_approvals.html.bak_S243_${HUB0:0:8}" ] \
  && [ -f "$M/root/portal/portal.py.bak_S243_${P0:0:8}" ] && [ -f "$M/root/portal/tile_grants.json.bak_S243_${G0:0:8}" ]; chk "four .bak_S243_<pin8> backups" $?
[ "$(md5sum "$M/root/portal/portal.py" | cut -c1-32)" = "4bb6bde0e2e07033ac0e0f5d7a7daaf6" ]; chk "portal.py landed as the predicted pin 4bb6bde0" $?
grep -q "smoke finance: import ok: reports_tile mounted" "$M/p2.log" && grep -q "smoke portal: import ok" "$M/p2.log"; chk "both import smokes green" $?
grep -q "added unit_role medical/shavez = viewer" "$M/p2.log"; chk "shavez seeded a medical viewer row" $?
grep -q "mock systemctl\] restart clinic-finance" "$M/p2.log" && grep -q "mock systemctl\] restart clinic-portal" "$M/p2.log"; chk "both services restarted" $?
FA1="$(md5sum "$M/root/finance/finance_app.py" | cut -c1-32)"
echo "     finance_app now $FA1 (from $FA0)"

echo "---- proof 3: second run is ALREADY INSTALLED"
ROOT="$M" PY=python3 PY_SMOKE=python3 bash "$KDIR/install_S243_REPORTS_TILE.sh" > "$M/p3.log" 2>&1; rc=$?
[ $rc -eq 0 ] && grep -q "ALREADY INSTALLED" "$M/p3.log" && [ "$(md5sum "$M/root/finance/finance_app.py" | cut -c1-32)" = "$FA1" ]; chk "ALREADY INSTALLED, nothing moved" $?

echo "---- proof 4: healthz fails -> full rollback"
M4="$(mktemp -d /tmp/mock_rpt4_XXXXXX)"; build_root "$M4"
ROOT="$M4" PY=python3 PY_SMOKE=python3 MOCK_HZ_FAIL=1 bash "$KDIR/install_S243_REPORTS_TILE.sh" > "$M4/p4.log" 2>&1; rc=$?
[ $rc -ne 0 ] && grep -q "RED" "$M4/p4.log" && [ "$(md5sum "$M4/root/finance/finance_app.py" | cut -c1-32)" = "$FA0" ] \
  && [ "$(md5sum "$M4/root/finance/finance_ui/finance_approvals.html" | cut -c1-32)" = "$HUB0" ] \
  && [ "$(md5sum "$M4/root/portal/portal.py" | cut -c1-32)" = "$P0" ] && [ "$(md5sum "$M4/root/portal/tile_grants.json" | cut -c1-32)" = "$G0" ] \
  && [ ! -f "$M4/root/finance/reports_tile.py" ]; chk "RED, all files back to the from-pins, module removed" $?
grep -q "restored finance_app.py" "$M4/p4.log" && grep -q "restored portal.py" "$M4/p4.log"; chk "rollback named what it restored" $?

echo "---- proof 5: lineage -- SCREEN_FIXES + DARPAN_KAL already on the box"
M5="$(mktemp -d /tmp/mock_rpt5_XXXXXX)"; build_root "$M5"
if [ -f "$SF_PATCHER" ] && [ -f "$KAL_KIT/patch_finance_app_darpan_kal_s243.py" ]; then
  FA_PATH="$M5/root/finance/finance_app.py" python3 -B "$SF_PATCHER" > /dev/null && mv -f "$M5/root/finance/finance_app.py.new" "$M5/root/finance/finance_app.py"
  FA_PATH="$M5/root/finance/finance_app.py" HUB_PATH="$M5/root/finance/finance_ui/finance_approvals.html" python3 -B "$KAL_KIT/patch_finance_app_darpan_kal_s243.py" both > /dev/null \
    && mv -f "$M5/root/finance/finance_app.py.new" "$M5/root/finance/finance_app.py" && mv -f "$M5/root/finance/finance_ui/finance_approvals.html.new" "$M5/root/finance/finance_ui/finance_approvals.html"
  for f in darpan_kal.py darpan_kal_schema.sql darpan_kal.html; do cp "$KAL_KIT/$f" "$M5/root/finance/$f"; done
  FA5="$(md5sum "$M5/root/finance/finance_app.py" | cut -c1-32)"; HUB5="$(md5sum "$M5/root/finance/finance_ui/finance_approvals.html" | cut -c1-32)"
  echo "     finance_app after the siblings: $FA5   hub: $HUB5"
  [ "$FA5" = "f93f7430b5c36449d520d41b6012ec3d" ] && [ "$HUB5" = "7dbb5e56a6564abbfebaa6f94cee484c" ]; chk "the sibling kits reproduce their predicted pins (f93f7430 / 7dbb5e56)" $?
  ROOT="$M5" PY=python3 PY_SMOKE=python3 bash "$KDIR/install_S243_REPORTS_TILE.sh" > "$M5/p5.log" 2>&1; rc=$?
  [ $rc -eq 0 ] && grep -q "lineage accepted" "$M5/p5.log" && grep -q "INSTALLED" "$M5/p5.log"; chk "installed on the sibling lineage" $?
  [ -f "$M5/root/finance/finance_app.py.bak_S243_${FA5:0:8}" ] && [ -f "$M5/root/finance/finance_ui/finance_approvals.html.bak_S243_${HUB5:0:8}" ]; chk "the .bak names carry the ACTUAL from-pins" $?
  [ "$(md5sum "$M5/root/finance/finance_app.py" | cut -c1-32)" = "dae5fd906c1528ea625f4bad6809bd57" ] && [ "$(md5sum "$M5/root/finance/finance_ui/finance_approvals.html" | cut -c1-32)" = "b8578b8d613b046d21047484b32b9076" ]; chk "to-pins as predicted (finance_app dae5fd90, hub b8578b8d)" $?
  grep -qF "S243_DARPAN_KAL begin" "$M5/root/finance/finance_app.py" && grep -qF "S243 darpan kal" "$M5/root/finance/finance_ui/finance_approvals.html"; chk "the DARPAN_KAL marks survive beside ours" $?
  python3 -B "$KDIR/seed_reports_role_s243.py" "$M5/root/finance/finance.db" | grep -q "NOT changed"; chk "a re-seed changes nothing" $?
  echo "     $(tail -1 "$M5/p5.log")"
else
  echo "  SKIP  proof 5 (sibling kits not found: $SF_PATCHER / $KAL_KIT)"
fi

echo ""
echo "MOCK INSTALL: $P passed, $F failed   (logs under $M, $M4, $M5)"
[ $F -eq 0 ]
