#!/usr/bin/env bash
# =============================================================================
#  install_sheet2_review.sh · kit S238_SHEET2_REVIEW
#  Run by:  bash /root/deploy/vps_deploy.sh S238_SHEET2_REVIEW
#
#  TWO files, installed together or not at all, plus ONE setting:
#    /root/staff_register/salary_policy.py   v1.8 (4136e7ae) -> v1.9
#    /root/staff_register/staff_register.py  v0.13 (d217f3f0) -> v0.14
#    salary_policy_settings.json             improve_pct -> 20 (audited door)
#  WHAT CHANGES (the owner's review, 10-Sep-2026 night):
#    + STEP 0 of the month-end flow: machine-absent days, staff-wise, printable for
#      checking against the physical register; the Fix-absents desk one click away.
#    + Sheet 2: advances booked against a LATER month are flagged; the second table
#      says per advance: recovered in one go (how much, which salary) or on
#      instalments (how much a month, from when, till when) — worked out with the
#      ledger close's own rules; the fines table spells out the days; A4 landscape.
#    + the ENFORCED/PREVIEW line never prints.
#    + holds: marked, not withheld; a 20% improvement cancels last month's hold.
#  The Advance figures do not change: the probe proves it, each engine in its own
#  process (F-414), BEFORE anything is replaced.
#  Red path: restores both files and the settings file, restarts staff-register.
# =============================================================================
set -u
KIT="S238_SHEET2_REVIEW"
KDIR="$(cd "$(dirname "$0")" && pwd)"
DIR="${SR_DIR:-/root/staff_register}"
SPF="$DIR/salary_policy.py";  B1=4136e7ae857d8dcbb8f7f987df5faa59
SRF="$DIR/staff_register.py"; B2=d217f3f0091a570e2b8da41e6c937785
SET="$DIR/salary_policy_settings.json"; AUD="$DIR/salary_policy_settings_audit.jsonl"
PY="${PY:-/root/wa/venv/bin/python3}"
MONTH="${MONTH:-2026-08}"
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/9] SUMS.md5 gate failed — nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { echo "!! [1/9] KIT_ID names another kit — nothing installed"; exit 1; }
N1="$(awk 'NR==1{print $2}' KIT_ID.txt)"; N2=794afc2661ae5931f8e3a380401af3e8   # staff_register.py v0.14
[ "$N1" = "$(md5of salary_policy.py)" ] && [ "$N2" = "$(md5of staff_register.py)" ] \
  || { echo "!! [1/9] KIT_ID does not match the kit's files — nothing installed"; exit 1; }
echo "[1/9] kit gates green"
systemctl show -p ExecStart staff-register 2>/dev/null | grep -q "staff_register" \
  || { echo "!! [2/9] staff-register does not run staff_register.py — nothing installed"; exit 1; }
c1="$(md5of "$SPF")"; c2="$(md5of "$SRF")"
if [ "$c1" = "$N1" ] && [ "$c2" = "$N2" ]; then
  echo "files already installed."; "$PY" -B set_improve.py "$DIR"; exit $?
fi
[ "$c1" = "$B1" ] || { echo "!! [2/9] CURRENCY GATE — $SPF is $c1, expected v1.8 $B1. Nothing installed."; exit 1; }
[ "$c2" = "$B2" ] || { echo "!! [2/9] CURRENCY GATE — $SRF is $c2, expected v0.13 $B2. Nothing installed."; exit 1; }
echo "[2/9] both live files are the pinned versions"
PR=/tmp/s238_sheet2_probe; rm -rf "$PR"; mkdir -p "$PR" && chmod 700 "$PR" || { echo "!! cannot make $PR"; exit 1; }
cp salary_policy.py staff_register.py probe_sheet2.py "$PR/"
( cd "$PR" && "$PY" -B salary_policy.py --selftest ) >"$PR/p.log" 2>&1 && grep -q PASS "$PR/p.log" \
  || { echo "!! [3/9] salary_policy selftest failed — nothing installed"; tail -5 "$PR/p.log"; rm -rf "$PR"; exit 1; }
( cd "$PR" && "$PY" -B staff_register.py --selftest ) >"$PR/r.log" 2>&1 && grep -q "SELFTEST OK" "$PR/r.log" \
  || { echo "!! [3/9] staff_register selftest failed — nothing installed"; tail -5 "$PR/r.log"; rm -rf "$PR"; exit 1; }
echo "[3/9] new files: salary_policy selftest PASS · staff_register selftest OK"
echo "[4/9] $MONTH computed with the LIVE engine and the NEW one (read-only, separate processes):"
( cd "$PR" && "$PY" -B probe_sheet2.py "$PR/salary_policy.py" "$SPF" "$MONTH" ) \
  || { echo "!! [4/9] the probe failed — nothing installed"; rm -rf "$PR"; exit 1; }
rm -rf "$PR"
TS=$(date +%Y%m%d_%H%M%S); K1="$SPF.bak_${KIT}_$TS"; K2="$SRF.bak_${KIT}_$TS"
K3="$SET.bak_${KIT}_$TS"; K4="$AUD.bak_${KIT}_$TS"
cp -p "$SPF" "$K1" && cp -p "$SRF" "$K2" || { echo "!! [5/9] backup failed — nothing installed"; exit 1; }
HAVESET=0; [ -f "$SET" ] && { cp -p "$SET" "$K3" || { echo "!! [5/9] settings backup failed"; exit 1; }; HAVESET=1; }
HAVEAUD=0; [ -f "$AUD" ] && { cp -p "$AUD" "$K4" || { echo "!! [5/9] audit backup failed"; exit 1; }; HAVEAUD=1; }
echo "[5/9] backups: $K1 · $K2$( [ $HAVESET = 1 ] && echo " · $K3" )"
rollback(){ echo "!! RED — restoring both files and the settings"; cp -p "$K1" "$SPF"; cp -p "$K2" "$SRF"
            if [ $HAVESET = 1 ]; then cp -p "$K3" "$SET"; else rm -f "$SET"; fi
            if [ $HAVEAUD = 1 ]; then cp -p "$K4" "$AUD"; else rm -f "$AUD"; fi
            systemctl restart staff-register >/dev/null 2>&1; sleep 2
            echo "   now: $(md5of "$SPF") / $(md5of "$SRF")"; exit 1; }
cp salary_policy.py "$SPF" && cp staff_register.py "$SRF" || rollback
[ "$(md5of "$SPF")" = "$N1" ] && [ "$(md5of "$SRF")" = "$N2" ] || rollback
echo "[6/9] installed $N1 · $N2"
"$PY" -B set_improve.py "$DIR" || rollback
echo "[7/9] hold threshold set through the audited settings door"
systemctl restart staff-register || rollback
sleep 2; systemctl is-active --quiet staff-register || rollback
code=$(curl -s -o /dev/null -m 6 -w '%{http_code}' http://127.0.0.1:8044/register/health)
[ "$code" = "200" ] || { echo "!! [8/9] /register/health -> $code"; rollback; }
echo "[8/9] staff-register restarted · /register/health -> 200"
echo "[9/9] GREEN"
echo
echo "  Month-end flow:  https://followup.dr-manoj.in/register/salary/flow?ym=$MONTH"
echo "  PINS:"
md5sum "$SPF" "$SRF"
echo "  Reverse:  \\cp -p $K1 $SPF && \\cp -p $K2 $SRF && systemctl restart staff-register"
