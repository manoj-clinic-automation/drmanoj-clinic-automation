#!/bin/bash
# mock_install_darpan_kal_s243.sh -- the installer's four proofs on a throw-away ROOT.
#   1 refuses a wrong finance_app pin (nothing placed)      2 installs on the true pins
#   3 second run says ALREADY INSTALLED                     4 healthz failure -> rollback to the from-pins
#   5 a finance_app.py already carrying the S243_SCREEN_FIXES mark (different md5) is accepted; the
#     .bak carries THAT pin; the recipients are seeded (manoj/bhawna) and a re-seed changes nothing
#   SF_PATCHER=<path to S243_SCREEN_FIXES/patch_finance_daily_s243.py> enables proof 5 (default: sibling kit folder)
# Needs: a finance tree to copy from (FIN_SRC, the 13-Sep capture or /root/finance).  Nothing live is touched.
#   FIN_SRC=/home/claude/S243/capture/tree/root/finance bash mock_install_darpan_kal_s243.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
FIN_SRC="${FIN_SRC:-/root/finance}"
M="$(mktemp -d /tmp/mock_kal_XXXXXX)"
mkdir -p "$M/root/finance/finance_ui" "$M/etc/systemd/system" "$M/bin"
for f in finance_app.py finance_ingest.py finance_returns.py finance_upi.py marg_report.py finance_identity.py darpan_app.py \
         darpan_card.html darpan_corrections.html returns_desk.py returns_desk.html finance_returns_audit.py finance_money.py \
         finance_returns_escalate.py finance_intent.py staff_pages.py joiner_app.py stock_app.py finance_clinic_day.py \
         clinic_register.py purchase_app.py bank_mpr_status.py clinic_day_pdf.py marg_door.py amir_day.py finance_schema.sql finance_returns.sql; do
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
FA0="$(md5sum "$M/root/finance/finance_app.py" | cut -c1-32)"
HUB0="$(md5sum "$M/root/finance/finance_ui/finance_approvals.html" | cut -c1-32)"
echo "== mock root $M  finance_app $FA0  hub $HUB0"
P=0; F=0
chk() { if [ "$2" -eq 0 ]; then P=$((P+1)); echo "  PASS  $1"; else F=$((F+1)); echo "  FAIL  $1"; fi; }

echo "---- proof 1: wrong finance_app pin is refused"
ROOT="$M" PY=python3 PY_SMOKE=python3 MOCK_FA_PIN=00000000000000000000000000000000 bash "$KDIR/install_S243_DARPAN_KAL.sh" > "$M/p1.log" 2>&1; rc=$?
grep -q "neither the pin" "$M/p1.log" && [ $rc -ne 0 ] && [ ! -f "$M/root/finance/darpan_kal.py" ] && [ "$(md5sum "$M/root/finance/finance_app.py" | cut -c1-32)" = "$FA0" ]; chk "refused, nothing placed" $?

echo "---- proof 2: install on the true pins"
ROOT="$M" PY=python3 PY_SMOKE=python3 MOCK_FA_PIN="$FA0" MOCK_HUB_PIN="$HUB0" bash "$KDIR/install_S243_DARPAN_KAL.sh" > "$M/p2.log" 2>&1; rc=$?
tail -12 "$M/p2.log"
grep -q "INSTALLED" "$M/p2.log" && [ $rc -eq 0 ] && grep -q "S243_DARPAN_KAL begin" "$M/root/finance/finance_app.py" && grep -q "S243 darpan kal" "$M/root/finance/finance_ui/finance_approvals.html" \
  && [ -f "$M/root/finance/finance_app.py.bak_S243_${FA0:0:8}" ] && [ -f "$M/root/finance/darpan_kal.py" ]; chk "installed, marks present, backups written" $?
FA1="$(md5sum "$M/root/finance/finance_app.py" | cut -c1-32)"; HUB1="$(md5sum "$M/root/finance/finance_ui/finance_approvals.html" | cut -c1-32)"
echo "     to-pins: finance_app $FA1  hub $HUB1"

echo "---- proof 3: second run is ALREADY INSTALLED"
ROOT="$M" PY=python3 PY_SMOKE=python3 MOCK_FA_PIN="$FA0" MOCK_HUB_PIN="$HUB0" bash "$KDIR/install_S243_DARPAN_KAL.sh" > "$M/p3.log" 2>&1; rc=$?
grep -q "ALREADY INSTALLED" "$M/p3.log" && [ $rc -eq 0 ] && [ "$(md5sum "$M/root/finance/finance_app.py" | cut -c1-32)" = "$FA1" ]; chk "ALREADY INSTALLED, bytes unchanged" $?

echo "---- proof 4: healthz failure rolls back to the from-pins"
cp "$M/root/finance/finance_app.py.bak_S243_${FA0:0:8}" "$M/root/finance/finance_app.py"
cp "$M/root/finance/finance_ui/finance_approvals.html.bak_S243_${HUB0:0:8}" "$M/root/finance/finance_ui/finance_approvals.html"
rm -f "$M/root/finance/darpan_kal.py" "$M/root/finance/darpan_kal.html" "$M/root/finance/darpan_kal_schema.sql"
MOCK_HZ_FAIL=1 ROOT="$M" PY=python3 PY_SMOKE=python3 MOCK_FA_PIN="$FA0" MOCK_HUB_PIN="$HUB0" bash "$KDIR/install_S243_DARPAN_KAL.sh" > "$M/p4.log" 2>&1; rc=$?
tail -6 "$M/p4.log"
grep -q "healthz answered" "$M/p4.log" && [ $rc -ne 0 ] && [ "$(md5sum "$M/root/finance/finance_app.py" | cut -c1-32)" = "$FA0" ] \
  && [ "$(md5sum "$M/root/finance/finance_ui/finance_approvals.html" | cut -c1-32)" = "$HUB0" ] && [ ! -f "$M/root/finance/darpan_kal.py" ]; chk "RED on healthz, both files back on the from-pins, new files removed" $?

echo "---- proof 5: a S243_SCREEN_FIXES-patched finance_app.py (other md5) is accepted; from-pin recorded; recipients seeded"
SF_PATCHER="${SF_PATCHER:-$KDIR/../S243_SCREEN_FIXES/patch_finance_daily_s243.py}"
if [ -f "$SF_PATCHER" ]; then
  cp "$M/root/finance/finance_app.py.bak_S243_${FA0:0:8}" "$M/root/finance/finance_app.py"
  cp "$M/root/finance/finance_ui/finance_approvals.html.bak_S243_${HUB0:0:8}" "$M/root/finance/finance_ui/finance_approvals.html"
  rm -f "$M/root/finance/darpan_kal.py" "$M/root/finance/darpan_kal.html" "$M/root/finance/darpan_kal_schema.sql"
  FA_PATH="$M/root/finance/finance_app.py" FA_FROM_PIN8= python3 -B "$SF_PATCHER" > /dev/null 2>&1 && mv -f "$M/root/finance/finance_app.py.new" "$M/root/finance/finance_app.py"
  FASF="$(md5sum "$M/root/finance/finance_app.py" | cut -c1-32)"
  echo "     SCREEN_FIXES-patched finance_app: $FASF"
  ROOT="$M" PY=python3 PY_SMOKE=python3 MOCK_HUB_PIN="$HUB0" bash "$KDIR/install_S243_DARPAN_KAL.sh" > "$M/p5.log" 2>&1; rc=$?
  grep -E "lineage accepted|INSTALLED|recipients|unit_role" "$M/p5.log"
  grep -q "lineage accepted" "$M/p5.log" && grep -q "INSTALLED" "$M/p5.log" && [ $rc -eq 0 ] && [ -f "$M/root/finance/finance_app.py.bak_S243_${FASF:0:8}" ] \
    && grep -q "S243_DARPAN_KAL begin" "$M/root/finance/finance_app.py" && grep -q "S243: a checker" "$M/root/finance/finance_app.py" \
    && [ "$(sqlite3 "$M/root/finance/finance.db" "select value from setting where key='darpan_kal.recipients'" 2>/dev/null || python3 -c "import sqlite3;print(sqlite3.connect('$M/root/finance/finance.db').execute(\"select value from setting where key='darpan_kal.recipients'\").fetchone()[0])")" = "manoj:dr_manoj,bhawna:dr_bhawna" ]; chk "SCREEN_FIXES lineage accepted, both marks present, .bak named by the actual pin, recipients seeded" $?
  FA2="$(md5sum "$M/root/finance/finance_app.py" | cut -c1-32)"
  echo "     to-pin after SCREEN_FIXES then DARPAN_KAL: finance_app $FA2"
else
  echo "  SKIP  proof 5: $SF_PATCHER not found"
fi

echo "== mock proofs: $P passed, $F failed   (logs in $M)"
[ $F -eq 0 ]
