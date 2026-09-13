#!/bin/bash
# mock_install_amir_visit_s243.sh -- the installer's proofs on a throw-away ROOT.  Nothing live is touched.
#   1 refuses a wrong amir_day pin (nothing placed)       2 installs on the true pins (hub = cc349dd0 direct)
#   3 second run says ALREADY INSTALLED                    4 healthz failure -> rollback to the from-pins
#   5 a hub already carrying the S243_DARPAN_KAL mark (different md5) is accepted; the .bak carries THAT pin
#   6 a hub that is neither the pin nor DARPAN_KAL lineage is refused (nothing placed)
# Needs: a finance tree to copy from (FIN_SRC: the 13-Sep capture or /root/finance) and the sibling kit
# S243_DARPAN_KAL for proof 5 (KAL_KIT, default: the kit folder's sibling).
#   FIN_SRC=/home/claude/S243/capture/tree/root/finance bash mock_install_amir_visit_s243.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
FIN_SRC="${FIN_SRC:-/root/finance}"
KAL_KIT="${KAL_KIT:-$(dirname "$KDIR")/S243_DARPAN_KAL}"
M="$(mktemp -d /tmp/mock_amir_visit_XXXXXX)"
mkdir -p "$M/root/finance/finance_ui" "$M/etc/systemd/system" "$M/bin"
for f in finance_app.py finance_ingest.py finance_returns.py finance_upi.py marg_report.py finance_identity.py darpan_app.py \
         darpan_card.html darpan_corrections.html returns_desk.py returns_desk.html finance_returns_audit.py finance_money.py \
         finance_returns_escalate.py finance_intent.py staff_pages.py joiner_app.py stock_app.py finance_clinic_day.py \
         clinic_register.py purchase_app.py bank_mpr_status.py clinic_day_pdf.py marg_door.py amir_day.py amir_salts.py \
         padwriter.py padreader.py finance_schema.sql finance_returns.sql purchase_schema.sql; do
  [ -f "$FIN_SRC/$f" ] && cp "$FIN_SRC/$f" "$M/root/finance/$f"
done
cp "$FIN_SRC/finance_ui/finance_approvals.html" "$M/root/finance/finance_ui/"
for f in finance_daily.html finance_review.html finance_entry.html finance_workbench.html finance_entry_clinic.html; do echo stub > "$M/root/finance/finance_ui/$f"; done
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
export PATH="$M/bin:$PATH"
AD0="$(md5sum "$M/root/finance/amir_day.py" | cut -c1-32)"
HUB0="$(md5sum "$M/root/finance/finance_ui/finance_approvals.html" | cut -c1-32)"
KITAD="$(md5sum "$KDIR/amir_day.py" | cut -c1-32)"
echo "== mock root $M  amir_day $AD0  hub $HUB0  kit amir_day $KITAD"
P=0; F=0
chk() { if [ "$2" -eq 0 ]; then P=$((P+1)); echo "  PASS  $1"; else F=$((F+1)); echo "  FAIL  $1"; fi; }
cur_ad() { md5sum "$M/root/finance/amir_day.py" | cut -c1-32; }
cur_hub() { md5sum "$M/root/finance/finance_ui/finance_approvals.html" | cut -c1-32; }

echo "---- proof 1: wrong amir_day pin is refused"
ROOT="$M" PY=python3 PY_SMOKE=python3 MOCK_AD_PIN=00000000000000000000000000000000 bash "$KDIR/install_S243_AMIR_VISIT.sh" > "$M/p1.log" 2>&1; rc=$?
grep -q "not the pin 00000000" "$M/p1.log" && [ $rc -ne 0 ] && [ "$(cur_ad)" = "$AD0" ] && [ "$(cur_hub)" = "$HUB0" ] && [ ! -f "$M/root/finance/finance_ui/finance_approvals.html.new" ]; chk "refused, nothing placed, no .new left" $?

echo "---- proof 2: install on the true pins"
ROOT="$M" PY=python3 PY_SMOKE=python3 bash "$KDIR/install_S243_AMIR_VISIT.sh" > "$M/p2.log" 2>&1; rc=$?
[ $rc -eq 0 ] && grep -q "INSTALLED" "$M/p2.log" && [ "$(cur_ad)" = "$KITAD" ] && grep -q "S243 amir visit" "$M/root/finance/finance_ui/finance_approvals.html"; chk "installed: kit amir_day placed, hub carries the mark" $?
[ -f "$M/root/finance/amir_day.py.bak_S243_${AD0:0:8}" ] && [ -f "$M/root/finance/finance_ui/finance_approvals.html.bak_S243_${HUB0:0:8}" ]; chk "backups named by the from-pins" $?
grep -q "import ok: amir_day mounted, visit-summary route registered" "$M/p2.log"; chk "import smoke under the unit env: route registered" $?
grep -q "byte for byte" "$M/p2.log"; chk "patch(live) == kit file proven before placing" $?
HUB2="$(cur_hub)"

echo "---- proof 3: second run is ALREADY INSTALLED"
ROOT="$M" PY=python3 PY_SMOKE=python3 bash "$KDIR/install_S243_AMIR_VISIT.sh" > "$M/p3.log" 2>&1; rc=$?
[ $rc -eq 0 ] && grep -q "ALREADY INSTALLED" "$M/p3.log" && [ "$(cur_ad)" = "$KITAD" ] && [ "$(cur_hub)" = "$HUB2" ]; chk "ALREADY INSTALLED, nothing moved" $?

echo "---- proof 4: healthz failure rolls back to the from-pins"
cp "$M/root/finance/amir_day.py.bak_S243_${AD0:0:8}" "$M/root/finance/amir_day.py"
cp "$M/root/finance/finance_ui/finance_approvals.html.bak_S243_${HUB0:0:8}" "$M/root/finance/finance_ui/finance_approvals.html"
rm -f "$M/root/finance/amir_day.py.bak_S243_"* "$M/root/finance/finance_ui/finance_approvals.html.bak_S243_"*
MOCK_HZ_FAIL=1 ROOT="$M" PY=python3 PY_SMOKE=python3 bash "$KDIR/install_S243_AMIR_VISIT.sh" > "$M/p4.log" 2>&1; rc=$?
[ $rc -ne 0 ] && grep -q "healthz answered" "$M/p4.log" && grep -q "restored amir_day.py" "$M/p4.log" && [ "$(cur_ad)" = "$AD0" ] && [ "$(cur_hub)" = "$HUB0" ]; chk "RED on healthz -> both files restored to the from-pins" $?

echo "---- proof 5: a hub already patched by S243_DARPAN_KAL is accepted by lineage"
rm -f "$M/root/finance/amir_day.py.bak_S243_"* "$M/root/finance/finance_ui/finance_approvals.html.bak_S243_"*
if [ -f "$KAL_KIT/patch_finance_app_darpan_kal_s243.py" ]; then
  HUB_PATH="$M/root/finance/finance_ui/finance_approvals.html" python3 -B "$KAL_KIT/patch_finance_app_darpan_kal_s243.py" hub > "$M/p5a.log" 2>&1 && mv -f "$M/root/finance/finance_ui/finance_approvals.html.new" "$M/root/finance/finance_ui/finance_approvals.html"
  HUBK="$(cur_hub)"
  [ "$HUBK" != "$HUB0" ] && grep -q "S243 darpan kal" "$M/root/finance/finance_ui/finance_approvals.html"; chk "mock hub now carries the DARPAN_KAL mark ($HUBK)" $?
  ROOT="$M" PY=python3 PY_SMOKE=python3 bash "$KDIR/install_S243_AMIR_VISIT.sh" > "$M/p5.log" 2>&1; rc=$?
  [ $rc -eq 0 ] && grep -q "lineage accepted" "$M/p5.log" && grep -q "INSTALLED" "$M/p5.log" && [ -f "$M/root/finance/finance_ui/finance_approvals.html.bak_S243_${HUBK:0:8}" ]; chk "accepted by lineage; the .bak carries the DARPAN_KAL pin ${HUBK:0:8}" $?
  grep -q 'id="kalCard"' "$M/root/finance/finance_ui/finance_approvals.html" && grep -q 'id="amirVisitBox"' "$M/root/finance/finance_ui/finance_approvals.html" && grep -q "loadStaffCards(); loadKal();" "$M/root/finance/finance_ui/finance_approvals.html" && grep -q "loadAmirVisit(); loadHomeMed();" "$M/root/finance/finance_ui/finance_approvals.html"; chk "both kits' blocks, loaders and calls coexist in the page" $?
else
  echo "  SKIP  S243_DARPAN_KAL not found at $KAL_KIT"
fi

echo "---- proof 6: a stranger hub is refused"
cp "$FIN_SRC/amir_day.py" "$M/root/finance/amir_day.py"
echo "<html>stranger</html>" > "$M/root/finance/finance_ui/finance_approvals.html"
ROOT="$M" PY=python3 PY_SMOKE=python3 bash "$KDIR/install_S243_AMIR_VISIT.sh" > "$M/p6.log" 2>&1; rc=$?
[ $rc -ne 0 ] && grep -q "neither the pin" "$M/p6.log" && [ "$(cur_ad)" = "$AD0" ]; chk "refused: hub is neither the pin nor DARPAN_KAL lineage; amir_day untouched" $?

echo ""
echo "mock: $P passed, $F failed   (root $M)"
find "$M" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
[ $F -eq 0 ] && rm -rf "$M"
exit $F
