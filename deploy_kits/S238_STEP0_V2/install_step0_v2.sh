#!/usr/bin/env bash
# =============================================================================
#  install_step0_v2.sh · kit S238_STEP0_V2
#  Run by:  bash /root/deploy/vps_deploy.sh S238_STEP0_V2
#  ONE file:  /root/staff_register/staff_register.py  v0.17 (2904a118) -> v0.18
#  The owner, on the first real print (3 pages): Step 0 condensed -- three dates
#  per row, tighter rows, the two explanatory paragraphs removed. Page layout
#  only: no figure anywhere changes. Red path: restores the file, restarts.
# =============================================================================
set -u
KIT="S238_STEP0_V2"
KDIR="$(cd "$(dirname "$0")" && pwd)"
DIR="${SR_DIR:-/root/staff_register}"
SRF="$DIR/staff_register.py"; B=2904a11845d7ea9565cca403c5b16ae0
PY="${PY:-/root/wa/venv/bin/python3}"
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/6] SUMS.md5 gate failed — nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { echo "!! [1/6] KIT_ID names another kit — nothing installed"; exit 1; }
N="$(awk 'NR==1{print $2}' KIT_ID.txt)"
[ "$N" = "$(md5of staff_register.py)" ] || { echo "!! [1/6] KIT_ID does not match the kit's file — nothing installed"; exit 1; }
echo "[1/6] kit gates green"
systemctl show -p ExecStart staff-register 2>/dev/null | grep -q "staff_register" \
  || { echo "!! [2/6] staff-register does not run staff_register.py — nothing installed"; exit 1; }
c="$(md5of "$SRF")"
[ "$c" = "$N" ] && { echo "already installed — nothing to do."; exit 0; }
[ "$c" = "$B" ] || { echo "!! [2/6] CURRENCY GATE — $SRF is $c, expected v0.17 $B. Nothing installed."; exit 1; }
echo "[2/6] the live file is the pinned version"
PR=/tmp/s238_step0_probe; rm -rf "$PR"; mkdir -p "$PR" && chmod 700 "$PR" || { echo "!! cannot make $PR"; exit 1; }
cp staff_register.py "$PR/"; cp "$DIR/salary_policy.py" "$PR/" 2>/dev/null
( cd "$PR" && "$PY" -B staff_register.py --selftest ) >"$PR/r.log" 2>&1 && grep -q "SELFTEST OK" "$PR/r.log" \
  || { echo "!! [3/6] staff_register selftest failed — nothing installed"; tail -5 "$PR/r.log"; rm -rf "$PR"; exit 1; }
rm -rf "$PR"
echo "[3/6] new file: staff_register selftest OK"
TS=$(date +%Y%m%d_%H%M%S); K="$SRF.bak_${KIT}_$TS"
cp -p "$SRF" "$K" || { echo "!! [4/6] backup failed — nothing installed"; exit 1; }
echo "[4/6] backup: $K"
rollback(){ echo "!! RED — restoring the file"; cp -p "$K" "$SRF"; systemctl restart staff-register >/dev/null 2>&1; sleep 2
            echo "   now: $(md5of "$SRF")"; exit 1; }
cp staff_register.py "$SRF" || rollback
[ "$(md5of "$SRF")" = "$N" ] || rollback
systemctl restart staff-register || rollback
sleep 2; systemctl is-active --quiet staff-register || rollback
code=$(curl -s -o /dev/null -m 6 -w '%{http_code}' http://127.0.0.1:8044/register/health)
[ "$code" = "200" ] || { echo "!! [5/6] /register/health -> $code"; rollback; }
echo "[5/6] installed $N · staff-register restarted · /register/health -> 200"
echo "[6/6] GREEN"
echo
echo "  Step 0:  https://followup.dr-manoj.in/register/salary/flow/verify?ym=2026-08"
echo "  PIN:     $(md5sum "$SRF")"
echo "  Reverse: \\cp -p $K $SRF && systemctl restart staff-register"
