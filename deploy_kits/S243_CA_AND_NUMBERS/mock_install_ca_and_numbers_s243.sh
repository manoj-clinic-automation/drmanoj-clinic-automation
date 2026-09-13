#!/bin/bash
# mock_install_ca_and_numbers_s243.sh -- the installer's proofs on a throw-away ROOT. Nothing live is touched.
#   1 refuses a wrong finance_app pin (nothing placed)        2 installs on the true pins
#   3 second run says ALREADY INSTALLED                       4 healthz failure -> every file back on its from-pin
#   5 a finance_app.py / hub already carrying the S243_SCREEN_FIXES + S243_DARPAN_KAL marks (different md5)
#     is accepted; the .bak carries THAT pin; both kits' marks survive beside this one
#   FIN_SRC=/home/claude/S243/capture/tree/root/finance bash mock_install_ca_and_numbers_s243.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
FIN_SRC="${FIN_SRC:-/root/finance}"
SIB="$(dirname "$KDIR")"
M="$(mktemp -d /tmp/mock_ca_XXXXXX)"
mkdir -p "$M/root/finance/finance_ui" "$M/etc/systemd/system" "$M/bin"
for f in finance_app.py finance_ingest.py finance_returns.py finance_upi.py marg_report.py finance_identity.py darpan_app.py \
         darpan_card.html darpan_corrections.html returns_desk.py returns_desk.html finance_returns_audit.py finance_money.py \
         finance_returns_escalate.py finance_intent.py staff_pages.py joiner_app.py stock_app.py finance_clinic_day.py \
         clinic_register.py purchase_app.py bank_mpr_status.py clinic_day_pdf.py marg_door.py amir_day.py finance_schema.sql \
         finance_returns.sql padwriter.py padreader.py bank_match.py finance_patient_match.py marg_take.py marg_spine.py sale_bill.py \
         amir_salts.py docterz_ingest.py docterz_day.py pipeline_status.html staff_manage.html stock_desk.html stock_amir.html stock_pad.html; do
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
Environment=FINANCE_AUTOAPPLY_OFF=$M/AUTOAPPLY_OFF
EOF
cat > "$M/bin/systemctl" <<'EOF'
#!/bin/bash
echo "[mock systemctl] $*" >&2
exit 0
EOF
cat > "$M/bin/curl" <<'EOF'
#!/bin/bash
if [ -n "${MOCK_HZ_FAIL:-}" ]; then printf '000'; else printf '200'; fi
EOF
chmod +x "$M/bin/systemctl" "$M/bin/curl"
export PATH="$M/bin:$PATH"
F="$M/root/finance"
FA0="$(md5sum "$F/finance_app.py" | cut -c1-32)"; HUB0="$(md5sum "$F/finance_ui/finance_approvals.html" | cut -c1-32)"
RD0="$(md5sum "$F/returns_desk.py" | cut -c1-32)"; RDH0="$(md5sum "$F/returns_desk.html" | cut -c1-32)"; COR0="$(md5sum "$F/darpan_corrections.html" | cut -c1-32)"
echo "== mock root $M  finance_app $FA0  hub $HUB0  desk $RD0/$RDH0  corrections $COR0"
P=0; FL=0
chk() { if [ "$2" -eq 0 ]; then P=$((P+1)); echo "  PASS  $1"; else FL=$((FL+1)); echo "  FAIL  $1"; fi; }
PINS="MOCK_FA_PIN=$FA0 MOCK_HUB_PIN=$HUB0 MOCK_RD_PIN=$RD0 MOCK_RDH_PIN=$RDH0 MOCK_COR_PIN=$COR0"
run() { env ROOT="$M" PY=python3 PY_SMOKE=python3 $PINS "$@" bash "$KDIR/install_S243_CA_AND_NUMBERS.sh"; }

echo "---- proof 1: wrong finance_app pin is refused"
env ROOT="$M" PY=python3 PY_SMOKE=python3 MOCK_FA_PIN=00000000000000000000000000000000 MOCK_HUB_PIN="$HUB0" MOCK_RD_PIN="$RD0" MOCK_RDH_PIN="$RDH0" MOCK_COR_PIN="$COR0" \
  bash "$KDIR/install_S243_CA_AND_NUMBERS.sh" > "$M/p1.log" 2>&1; rc=$?
grep -q "neither the pin" "$M/p1.log" && [ $rc -ne 0 ] && [ ! -f "$F/accountant_upi_cash.py" ] && [ "$(md5sum "$F/finance_app.py" | cut -c1-32)" = "$FA0" ] \
  && [ "$(md5sum "$F/darpan_corrections.html" | cut -c1-32)" = "$COR0" ]; chk "refused, nothing placed" $?

echo "---- proof 2: install on the true pins"
run > "$M/p2.log" 2>&1; rc=$?
tail -10 "$M/p2.log"
grep -q "INSTALLED" "$M/p2.log" && [ $rc -eq 0 ] && grep -q "S243_CA_AND_NUMBERS begin" "$F/finance_app.py" && grep -q "S243 ca accountant report" "$F/finance_ui/finance_approvals.html" \
  && grep -q "S243_CA_AND_NUMBERS: full number" "$F/returns_desk.py" && grep -q "S243 full number" "$F/returns_desk.html" \
  && grep -q "Ab Marg me sudhaar nahi karna hai" "$F/darpan_corrections.html" \
  && [ -f "$F/finance_app.py.bak_S243_${FA0:0:8}" ] && [ -f "$F/returns_desk.py.bak_S243_${RD0:0:8}" ] && [ -f "$F/darpan_corrections.html.bak_S243_${COR0:0:8}" ] \
  && [ -f "$F/accountant_upi_cash.py" ]; chk "installed, marks present, backups written" $?
FA1="$(md5sum "$F/finance_app.py" | cut -c1-32)"; HUB1="$(md5sum "$F/finance_ui/finance_approvals.html" | cut -c1-32)"
echo "     to-pins: finance_app $FA1  hub $HUB1  returns_desk.py $(md5sum "$F/returns_desk.py" | cut -c1-8)  returns_desk.html $(md5sum "$F/returns_desk.html" | cut -c1-8)"

echo "---- proof 3: second run is ALREADY INSTALLED"
run > "$M/p3.log" 2>&1; rc=$?
grep -q "ALREADY INSTALLED" "$M/p3.log" && [ $rc -eq 0 ] && [ "$(md5sum "$F/finance_app.py" | cut -c1-32)" = "$FA1" ]; chk "ALREADY INSTALLED, bytes unchanged" $?

echo "---- proof 4: healthz failure rolls back every file to its from-pin"
cp "$F/finance_app.py.bak_S243_${FA0:0:8}" "$F/finance_app.py"; cp "$F/finance_ui/finance_approvals.html.bak_S243_${HUB0:0:8}" "$F/finance_ui/finance_approvals.html"
cp "$F/returns_desk.py.bak_S243_${RD0:0:8}" "$F/returns_desk.py"; cp "$F/returns_desk.html.bak_S243_${RDH0:0:8}" "$F/returns_desk.html"
cp "$F/darpan_corrections.html.bak_S243_${COR0:0:8}" "$F/darpan_corrections.html"; rm -f "$F/accountant_upi_cash.py"
MOCK_HZ_FAIL=1 run > "$M/p4.log" 2>&1; rc=$?
tail -8 "$M/p4.log"
grep -q "healthz answered" "$M/p4.log" && [ $rc -ne 0 ] && [ "$(md5sum "$F/finance_app.py" | cut -c1-32)" = "$FA0" ] \
  && [ "$(md5sum "$F/finance_ui/finance_approvals.html" | cut -c1-32)" = "$HUB0" ] && [ "$(md5sum "$F/returns_desk.py" | cut -c1-32)" = "$RD0" ] \
  && [ "$(md5sum "$F/returns_desk.html" | cut -c1-32)" = "$RDH0" ] && [ "$(md5sum "$F/darpan_corrections.html" | cut -c1-32)" = "$COR0" ] \
  && [ ! -f "$F/accountant_upi_cash.py" ]; chk "RED on healthz, five files back on the from-pins, new file removed" $?

echo "---- proof 5: a finance_app/hub already patched by SCREEN_FIXES + DARPAN_KAL is accepted (lineage), marks coexist"
if [ -f "$SIB/S243_SCREEN_FIXES/patch_finance_daily_s243.py" ] && [ -f "$SIB/S243_DARPAN_KAL/patch_finance_app_darpan_kal_s243.py" ]; then
  FA_PATH="$F/finance_app.py" FA_FROM_PIN8= python3 -B "$SIB/S243_SCREEN_FIXES/patch_finance_daily_s243.py" >/dev/null 2>&1 && mv -f "$F/finance_app.py.new" "$F/finance_app.py"
  FA_PATH="$F/finance_app.py" HUB_PATH="$F/finance_ui/finance_approvals.html" python3 -B "$SIB/S243_DARPAN_KAL/patch_finance_app_darpan_kal_s243.py" both >/dev/null 2>&1 \
    && mv -f "$F/finance_app.py.new" "$F/finance_app.py" && mv -f "$F/finance_ui/finance_approvals.html.new" "$F/finance_ui/finance_approvals.html"
  for f in darpan_kal.py darpan_kal_schema.sql darpan_kal.html; do cp "$SIB/S243_DARPAN_KAL/$f" "$F/$f"; done
  FA5="$(md5sum "$F/finance_app.py" | cut -c1-32)"; HUB5="$(md5sum "$F/finance_ui/finance_approvals.html" | cut -c1-32)"
  echo "     sibling-patched pins: finance_app $FA5  hub $HUB5"
  env ROOT="$M" PY=python3 PY_SMOKE=python3 MOCK_FA_PIN="$FA0" MOCK_HUB_PIN="$HUB0" MOCK_RD_PIN="$RD0" MOCK_RDH_PIN="$RDH0" MOCK_COR_PIN="$COR0" \
    bash "$KDIR/install_S243_CA_AND_NUMBERS.sh" > "$M/p5.log" 2>&1; rc=$?
  tail -9 "$M/p5.log"
  grep -q "lineage accepted" "$M/p5.log" && grep -q "INSTALLED" "$M/p5.log" && [ $rc -eq 0 ] && [ -f "$F/finance_app.py.bak_S243_${FA5:0:8}" ] \
    && [ -f "$F/finance_ui/finance_approvals.html.bak_S243_${HUB5:0:8}" ] \
    && grep -q "S243_CA_AND_NUMBERS begin" "$F/finance_app.py" && grep -q "S243_DARPAN_KAL begin" "$F/finance_app.py" \
    && grep -q "S243: a checker (the doctor) lands on his Review console" "$F/finance_app.py" \
    && grep -q "S243 darpan kal" "$F/finance_ui/finance_approvals.html" && grep -q "S243 ca accountant report" "$F/finance_ui/finance_approvals.html"; chk "sibling lineage accepted, .bak carries the sibling pin, all three kits' marks coexist" $?
  echo "     final pins: finance_app $(md5sum "$F/finance_app.py" | cut -c1-32)  hub $(md5sum "$F/finance_ui/finance_approvals.html" | cut -c1-32)"
else
  echo "  SKIP  sibling kits not beside this one"
fi

echo ""
echo "== mock proofs: $P passed, $FL failed  (root $M)"
[ "$FL" -eq 0 ]
