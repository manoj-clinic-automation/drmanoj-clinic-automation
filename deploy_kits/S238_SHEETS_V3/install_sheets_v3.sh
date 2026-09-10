#!/usr/bin/env bash
# =============================================================================
#  install_sheets_v3.sh · kit S238_SHEETS_V3
#  Run by:  bash /root/deploy/vps_deploy.sh S238_SHEETS_V3
#
#  TWO files, installed together or not at all:
#    /root/staff_register/salary_policy.py   v1.9 (e848c81f) -> v1.10
#    /root/staff_register/staff_register.py  v0.14 (794afc26) -> v0.15
#  WHAT CHANGES (the owner's third review, 10-Sep-2026 late night):
#    + Sheet 1 month summary: days not punched (total / sanctioned leave /
#      outstation / absent) WITH THEIR DATES, Sundays marked, for the physical-
#      register check; late fine in total; OT minutes and OT payable. A4 landscape.
#    + Sheet 2 fines table and Sheet 3: last month's hold 'deducted now' and
#      'written off' columns. Sheet 3 prints A4 landscape with every column.
#    + OT is SHOWN, not paid, until the setting ot_pay = 1 (settings page).
#  The probe runs the live and the new engine in separate processes, BOTH reading
#  the live settings and hold ledger (F-414 fixed): nets must be identical.
#  Red path: restores both files and restarts staff-register.
# =============================================================================
set -u
KIT="S238_SHEETS_V3"
KDIR="$(cd "$(dirname "$0")" && pwd)"
DIR="${SR_DIR:-/root/staff_register}"
SPF="$DIR/salary_policy.py";  B1=e848c81f14d3a01b5311d218e2a1ee35
SRF="$DIR/staff_register.py"; B2=794afc2661ae5931f8e3a380401af3e8
PY="${PY:-/root/wa/venv/bin/python3}"
MONTH="${MONTH:-2026-08}"
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/8] SUMS.md5 gate failed — nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { echo "!! [1/8] KIT_ID names another kit — nothing installed"; exit 1; }
N1="$(awk 'NR==1{print $2}' KIT_ID.txt)"; N2=f7cbfe3ee4150d84f5013703c686c05b   # staff_register.py v0.15
[ "$N1" = "$(md5of salary_policy.py)" ] && [ "$N2" = "$(md5of staff_register.py)" ] \
  || { echo "!! [1/8] KIT_ID does not match the kit's files — nothing installed"; exit 1; }
echo "[1/8] kit gates green"
systemctl show -p ExecStart staff-register 2>/dev/null | grep -q "staff_register" \
  || { echo "!! [2/8] staff-register does not run staff_register.py — nothing installed"; exit 1; }
c1="$(md5of "$SPF")"; c2="$(md5of "$SRF")"
[ "$c1" = "$N1" ] && [ "$c2" = "$N2" ] && { echo "already installed — nothing to do."; exit 0; }
[ "$c1" = "$B1" ] || { echo "!! [2/8] CURRENCY GATE — $SPF is $c1, expected v1.9 $B1. Nothing installed."; exit 1; }
[ "$c2" = "$B2" ] || { echo "!! [2/8] CURRENCY GATE — $SRF is $c2, expected v0.14 $B2. Nothing installed."; exit 1; }
echo "[2/8] both live files are the pinned versions"
PR=/tmp/s238_v3_probe; rm -rf "$PR"; mkdir -p "$PR" && chmod 700 "$PR" || { echo "!! cannot make $PR"; exit 1; }
cp salary_policy.py staff_register.py probe_sheets3.py "$PR/"
( cd "$PR" && "$PY" -B salary_policy.py --selftest ) >"$PR/p.log" 2>&1 && grep -q PASS "$PR/p.log" \
  || { echo "!! [3/8] salary_policy selftest failed — nothing installed"; tail -5 "$PR/p.log"; rm -rf "$PR"; exit 1; }
( cd "$PR" && "$PY" -B staff_register.py --selftest ) >"$PR/r.log" 2>&1 && grep -q "SELFTEST OK" "$PR/r.log" \
  || { echo "!! [3/8] staff_register selftest failed — nothing installed"; tail -5 "$PR/r.log"; rm -rf "$PR"; exit 1; }
echo "[3/8] new files: salary_policy selftest PASS · staff_register selftest OK"
echo "[4/8] $MONTH computed with the LIVE engine and the NEW one (read-only, separate processes, live settings):"
( cd "$PR" && "$PY" -B probe_sheets3.py "$PR/salary_policy.py" "$SPF" "$MONTH" ) \
  || { echo "!! [4/8] the probe failed — nothing installed"; rm -rf "$PR"; exit 1; }
rm -rf "$PR"
TS=$(date +%Y%m%d_%H%M%S); K1="$SPF.bak_${KIT}_$TS"; K2="$SRF.bak_${KIT}_$TS"
cp -p "$SPF" "$K1" && cp -p "$SRF" "$K2" || { echo "!! [5/8] backup failed — nothing installed"; exit 1; }
echo "[5/8] backups: $K1 · $K2"
rollback(){ echo "!! RED — restoring both files"; cp -p "$K1" "$SPF"; cp -p "$K2" "$SRF"
            systemctl restart staff-register >/dev/null 2>&1; sleep 2
            echo "   now: $(md5of "$SPF") / $(md5of "$SRF")"; exit 1; }
cp salary_policy.py "$SPF" && cp staff_register.py "$SRF" || rollback
[ "$(md5of "$SPF")" = "$N1" ] && [ "$(md5of "$SRF")" = "$N2" ] || rollback
echo "[6/8] installed $N1 · $N2"
systemctl restart staff-register || rollback
sleep 2; systemctl is-active --quiet staff-register || rollback
code=$(curl -s -o /dev/null -m 6 -w '%{http_code}' http://127.0.0.1:8044/register/health)
[ "$code" = "200" ] || { echo "!! [7/8] /register/health -> $code"; rollback; }
echo "[7/8] staff-register restarted · /register/health -> 200"
echo "[8/8] GREEN"
echo
echo "  Sheet 1:  https://followup.dr-manoj.in/register/salary/flow/sheet1?ym=$MONTH"
echo "  PINS:"
md5sum "$SPF" "$SRF"
echo "  Reverse:  \\cp -p $K1 $SPF && \\cp -p $K2 $SRF && systemctl restart staff-register"
