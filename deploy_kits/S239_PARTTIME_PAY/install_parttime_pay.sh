#!/usr/bin/env bash
# install_parttime_pay.sh · kit S239_PARTTIME_PAY      Run by:  bash /root/deploy/vps_deploy.sh S239_PARTTIME_PAY
# ONE file: /root/staff_register/salary_policy.py  v1.15 (d42a688f) -> v1.16
# The owner, 11-Sep-2026 ("1"): part-time staff (Amir Sohail) pay NO leave charge. Only his leave amount,
# absence fines and net may move -- the probe proves it, and that the net rises by exactly that.
set -u
KIT="S239_PARTTIME_PAY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPF="/root/staff_register/salary_policy.py"; B1=d42a688f4275483523c07a97d8c4dc24; N1=c7577174f35b30d8ab7fd42e163d9e4e
PY="/root/wa/venv/bin/python3"; MONTH="${MONTH:-2026-08}"
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
cd "$KDIR" || exit 1
[ "$(md5of salary_policy.py)" = "$N1" ] || { echo "!! [1/6] kit file is not the one built -- nothing installed"; exit 1; }
c1="$(md5of "$SPF")"
[ "$c1" = "$N1" ] && { echo "already installed -- nothing to do."; exit 0; }
[ "$c1" = "$B1" ] || { echo "!! [2/6] CURRENCY GATE -- $SPF is $c1, expected v1.15 $B1. Nothing installed."; exit 1; }
echo "[2/6] live file is v1.15"
PR=/tmp/s239_ptpay_probe; rm -rf "$PR"; mkdir -p "$PR" && chmod 700 "$PR"; cp salary_policy.py probe_parttime_pay.py "$PR/"
( cd "$PR" && "$PY" -B salary_policy.py --selftest ) >"$PR/p.log" 2>&1 && grep -q PASS "$PR/p.log" \
  || { echo "!! [3/6] selftest failed -- nothing installed"; tail -5 "$PR/p.log"; rm -rf "$PR"; exit 1; }
echo "[3/6] selftest PASS"
echo "[4/6] $MONTH with the LIVE engine and the NEW one (read-only, live settings):"
( cd "$PR" && "$PY" -B probe_parttime_pay.py "$PR/salary_policy.py" "$SPF" "$MONTH" ) || { echo "!! [4/6] probe RED -- nothing installed"; rm -rf "$PR"; exit 1; }
rm -rf "$PR"
TS=$(date +%Y%m%d_%H%M%S); K1="$SPF.bak_${KIT}_$TS"
cp -p "$SPF" "$K1" || { echo "!! [5/6] backup failed -- nothing installed"; exit 1; }
rollback(){ echo "!! RED -- restoring"; cp -p "$K1" "$SPF"; systemctl restart staff-register >/dev/null 2>&1; sleep 2; echo "   now: $(md5of "$SPF")"; exit 1; }
cp salary_policy.py "$SPF" && [ "$(md5of "$SPF")" = "$N1" ] || rollback
systemctl restart staff-register || rollback
sleep 2; systemctl is-active --quiet staff-register || rollback
code=$(curl -s -o /dev/null -m 6 -w '%{http_code}' http://127.0.0.1:8044/register/health)
[ "$code" = "200" ] || { echo "!! /register/health -> $code"; rollback; }
echo "[5/6] installed $N1 · backup $K1 · staff-register restarted · health 200"
echo "[6/6] GREEN -- reload the Money page for $MONTH"
echo "  Reverse:  \\cp -p $K1 $SPF && systemctl restart staff-register"
