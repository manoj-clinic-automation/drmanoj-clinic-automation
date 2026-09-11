#!/usr/bin/env bash
# =============================================================================
#  install_sheets_v4.sh · kit S238_SHEETS_V4
#  Run by:  bash /root/deploy/vps_deploy.sh S238_SHEETS_V4
#
#  TWO files, installed together or not at all:
#    /root/staff_register/salary_policy.py   v1.10 (2e3fe9fb) -> v1.11
#    /root/staff_register/staff_register.py  v0.15 (f7cbfe3e) -> v0.16
#  WHAT CHANGES (the owner, 11-Sep-2026):
#    + Step 0 is a proper A4 document: a row per date, P/L/A tick boxes, Sundays
#      shaded, the header repeated on every page, a signature line.
#    + Amir Sohail (setting dates_only_staff) leaves the grid: only his punch dates.
#    + Overtime on an extra-duty (cover) day counts only after the cover ends
#      (setting cover_end, 21:00) -- Shivani's cover hours are her extra duty.
#    + OVERTIME IS PAID (owner ruling): ot_pay = 1 through the audited settings
#      door. An optional daily threshold is on the settings page, OFF by default.
#  The probe proves every net moves by exactly the overtime paid, nothing else.
#  Red path: restores both files and the settings, restarts staff-register.
# =============================================================================
set -u
KIT="S238_SHEETS_V4"
KDIR="$(cd "$(dirname "$0")" && pwd)"
DIR="${SR_DIR:-/root/staff_register}"
SPF="$DIR/salary_policy.py";  B1=2e3fe9fb22cbd5a918115db7c5963e0c
SRF="$DIR/staff_register.py"; B2=f7cbfe3ee4150d84f5013703c686c05b
SET="$DIR/salary_policy_settings.json"; AUD="$DIR/salary_policy_settings_audit.jsonl"
PY="${PY:-/root/wa/venv/bin/python3}"
MONTH="${MONTH:-2026-08}"
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/8] SUMS.md5 gate failed — nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { echo "!! [1/8] KIT_ID names another kit — nothing installed"; exit 1; }
N1="$(awk 'NR==1{print $2}' KIT_ID.txt)"; N2=b6da7c8d56b74daee7e96f94fa84ea9f   # staff_register.py v0.16
[ "$N1" = "$(md5of salary_policy.py)" ] && [ "$N2" = "$(md5of staff_register.py)" ] \
  || { echo "!! [1/8] KIT_ID does not match the kit's files — nothing installed"; exit 1; }
echo "[1/8] kit gates green"
systemctl show -p ExecStart staff-register 2>/dev/null | grep -q "staff_register" \
  || { echo "!! [2/8] staff-register does not run staff_register.py — nothing installed"; exit 1; }
c1="$(md5of "$SPF")"; c2="$(md5of "$SRF")"
if [ "$c1" = "$N1" ] && [ "$c2" = "$N2" ]; then echo "files already installed."; "$PY" -B set_ot.py "$DIR"; exit $?; fi
[ "$c1" = "$B1" ] || { echo "!! [2/8] CURRENCY GATE — $SPF is $c1, expected v1.10 $B1. Nothing installed."; exit 1; }
[ "$c2" = "$B2" ] || { echo "!! [2/8] CURRENCY GATE — $SRF is $c2, expected v0.15 $B2. Nothing installed."; exit 1; }
echo "[2/8] both live files are the pinned versions"
PR=/tmp/s238_v4_probe; rm -rf "$PR"; mkdir -p "$PR" && chmod 700 "$PR" || { echo "!! cannot make $PR"; exit 1; }
cp salary_policy.py staff_register.py probe_sheets4.py "$PR/"
( cd "$PR" && "$PY" -B salary_policy.py --selftest ) >"$PR/p.log" 2>&1 && grep -q PASS "$PR/p.log" \
  || { echo "!! [3/8] salary_policy selftest failed — nothing installed"; tail -5 "$PR/p.log"; rm -rf "$PR"; exit 1; }
( cd "$PR" && "$PY" -B staff_register.py --selftest ) >"$PR/r.log" 2>&1 && grep -q "SELFTEST OK" "$PR/r.log" \
  || { echo "!! [3/8] staff_register selftest failed — nothing installed"; tail -5 "$PR/r.log"; rm -rf "$PR"; exit 1; }
echo "[3/8] new files: salary_policy selftest PASS · staff_register selftest OK"
echo "[4/8] $MONTH computed with the LIVE engine and the NEW one (read-only, separate processes, live settings):"
( cd "$PR" && "$PY" -B probe_sheets4.py "$PR/salary_policy.py" "$SPF" "$MONTH" ) \
  || { echo "!! [4/8] the probe failed — nothing installed"; rm -rf "$PR"; exit 1; }
rm -rf "$PR"
TS=$(date +%Y%m%d_%H%M%S); K1="$SPF.bak_${KIT}_$TS"; K2="$SRF.bak_${KIT}_$TS"
K3="$SET.bak_${KIT}_$TS"; K4="$AUD.bak_${KIT}_$TS"
cp -p "$SPF" "$K1" && cp -p "$SRF" "$K2" || { echo "!! [5/8] backup failed — nothing installed"; exit 1; }
HAVESET=0; [ -f "$SET" ] && { cp -p "$SET" "$K3" || { echo "!! [5/8] settings backup failed"; exit 1; }; HAVESET=1; }
HAVEAUD=0; [ -f "$AUD" ] && { cp -p "$AUD" "$K4" || { echo "!! [5/8] audit backup failed"; exit 1; }; HAVEAUD=1; }
echo "[5/8] backups: $K1 · $K2$( [ $HAVESET = 1 ] && echo " · $K3" )"
rollback(){ echo "!! RED — restoring both files and the settings"; cp -p "$K1" "$SPF"; cp -p "$K2" "$SRF"
            if [ $HAVESET = 1 ]; then cp -p "$K3" "$SET"; else rm -f "$SET"; fi
            if [ $HAVEAUD = 1 ]; then cp -p "$K4" "$AUD"; else rm -f "$AUD"; fi
            systemctl restart staff-register >/dev/null 2>&1; sleep 2
            echo "   now: $(md5of "$SPF") / $(md5of "$SRF")"; exit 1; }
cp salary_policy.py "$SPF" && cp staff_register.py "$SRF" || rollback
[ "$(md5of "$SPF")" = "$N1" ] && [ "$(md5of "$SRF")" = "$N2" ] || rollback
echo "[6/8] installed $N1 · $N2"
"$PY" -B set_ot.py "$DIR" || rollback
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
