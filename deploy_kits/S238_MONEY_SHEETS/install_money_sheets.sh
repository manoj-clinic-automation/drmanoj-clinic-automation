#!/usr/bin/env bash
# =============================================================================
#  install_money_sheets.sh · kit S238_MONEY_SHEETS
#  Run by:  bash /root/deploy/vps_deploy.sh S238_MONEY_SHEETS
#
#  TWO files, installed together or not at all:
#    /root/staff_register/salary_policy.py   v1.7 (7c0cfb94) -> v1.8
#    /root/staff_register/staff_register.py  v0.12 (f85a4b06) -> v0.13
#  WHAT CHANGES (the owner, 10-Sep-2026):
#    + the Advance column deducts EXACTLY what the staff ledger recorded for the
#      month — never a second sum from today's balances (D349/D442). August 2026
#      would otherwise take Darpan Rs 29,000 (his record: 20,000) and Surendra 0
#      (his record: 7,000), and three others' carried advances early.
#    + the Lock refuses until the ledger has closed the month.
#    + Sheet 1 prints as two A4 pages: the grid (every day) · the month summary.
#    + Sheet 2: advances taken this month without reversed entries, and HOW each
#      recovers; the open position AS AT THE MONTH'S END; what happened to last
#      month's hold, in words; every section whole on one A4 sheet.
#  BEFORE ANYTHING IS REPLACED it computes the month with the live AND the new
#  engine (read-only, as the salary page does) and prints both, person by person.
#  Red path: restores both files and restarts staff-register.
# =============================================================================
set -u
KIT="S238_MONEY_SHEETS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
DIR="${SR_DIR:-/root/staff_register}"
SPF="$DIR/salary_policy.py";  B1=7c0cfb940df2b542d1c4eb849ee3f924
SRF="$DIR/staff_register.py"; B2=f85a4b0663ee0028c967cefec716bd12
PY="${PY:-/root/wa/venv/bin/python3}"
MONTH="${MONTH:-2026-08}"
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/8] SUMS.md5 gate failed — nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { echo "!! [1/8] KIT_ID names another kit — nothing installed"; exit 1; }
N1="$(awk 'NR==1{print $2}' KIT_ID.txt)"; N2=d217f3f0091a570e2b8da41e6c937785   # staff_register.py v0.13
[ "$N1" = "$(md5of salary_policy.py)" ] && [ "$N2" = "$(md5of staff_register.py)" ] \
  || { echo "!! [1/8] KIT_ID does not match the kit's files — nothing installed"; exit 1; }
echo "[1/8] kit gates green"
systemctl show -p ExecStart staff-register 2>/dev/null | grep -q "staff_register" \
  || { echo "!! [2/8] staff-register does not run staff_register.py — nothing installed"; exit 1; }
c1="$(md5of "$SPF")"; c2="$(md5of "$SRF")"
[ "$c1" = "$N1" ] && [ "$c2" = "$N2" ] && { echo "already installed — nothing to do."; exit 0; }
[ "$c1" = "$B1" ] || { echo "!! [2/8] CURRENCY GATE — $SPF is $c1, expected v1.7 $B1. Nothing installed."; exit 1; }
[ "$c2" = "$B2" ] || { echo "!! [2/8] CURRENCY GATE — $SRF is $c2, expected v0.12 $B2. Nothing installed."; exit 1; }
echo "[2/8] both live files are the pinned versions"
PR=/tmp/s238_money_probe; rm -rf "$PR"; mkdir -p "$PR" && chmod 700 "$PR" || { echo "!! cannot make $PR"; exit 1; }
cp salary_policy.py staff_register.py probe_money.py "$PR/"
( cd "$PR" && "$PY" -B salary_policy.py --selftest ) >"$PR/p.log" 2>&1 && grep -q PASS "$PR/p.log" \
  || { echo "!! [3/8] salary_policy selftest failed — nothing installed"; tail -5 "$PR/p.log"; rm -rf "$PR"; exit 1; }
( cd "$PR" && "$PY" -B staff_register.py --selftest ) >"$PR/r.log" 2>&1 && grep -q "SELFTEST OK" "$PR/r.log" \
  || { echo "!! [3/8] staff_register selftest failed — nothing installed"; tail -5 "$PR/r.log"; rm -rf "$PR"; exit 1; }
echo "[3/8] new files: salary_policy selftest PASS · staff_register selftest OK"
echo "[4/8] $MONTH computed with the LIVE engine and the NEW one (read-only):"
( cd "$PR" && "$PY" -B probe_money.py "$PR/salary_policy.py" "$SPF" "$MONTH" ) \
  || { echo "!! [4/8] the money probe failed — nothing installed"; rm -rf "$PR"; exit 1; }
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
echo "  Sheet 2:  https://followup.dr-manoj.in/register/salary/flow/sheet2?ym=$MONTH"
echo "  PINS:"
md5sum "$SPF" "$SRF"
echo "  Reverse:  \\cp -p $K1 $SPF && \\cp -p $K2 $SRF && systemctl restart staff-register"
