#!/usr/bin/env bash
# S200_R10 — the owner-record July advances now DEDUCT in the compute, so
# Sheet 3/4 and the lock total equal the money actually left to hand over.
# ONE file: /root/staff_register/salary_policy.py
#   73aca693e28c4670af74c0c016643af9 (v1.6) -> 7c0cfb940df2b542d1c4eb849ee3f924 (v1.7)
set -u
KIT="$(cd "$(dirname "$0")" && pwd)"
SPF=/root/staff_register/salary_policy.py
B=73aca693e28c4670af74c0c016643af9; N=7c0cfb940df2b542d1c4eb849ee3f924
PY=/root/wa/venv/bin/python3
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
cd "$KIT" || exit 1
md5sum -c SUMS.md5 || { echo "*** RED. STOP."; exit 1; }
cur=$(md5of "$SPF"); echo "live: $cur"
[ "$cur" = "$N" ] && { echo "already new — nothing to do."; exit 0; }
[ "$cur" = "$B" ] || { echo "*** RED: expected $B. STOP — tell Claude this hash."; exit 1; }
[ -f /root/staff_register/manual_advances_2026-07.json ] \
  && echo "July advances file present — will deduct." \
  || echo "NOTE: no July advances file — paste it (Claude's block) for the deduction to appear."
TS=$(date +%Y%m%d_%H%M%S); cp -p "$SPF" "$SPF.bak_S200_R10_$TS" || exit 1
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$SPF.bak_S200_R10_$TS" "$SPF"
            systemctl restart staff-register >/dev/null 2>&1; sleep 2; exit 1; }
cp "$KIT/salary_policy.py" "$SPF" || rollback
[ "$(md5of "$SPF")" = "$N" ] || rollback
"$PY" -c "import py_compile; py_compile.compile('$SPF', doraise=True)" || rollback
"$PY" "$SPF" --selftest >/tmp/s200_r10.log 2>&1 && echo "policy SELFTEST OK" || { tail -5 /tmp/s200_r10.log; rollback; }
systemctl restart staff-register || rollback
sleep 2; systemctl is-active --quiet staff-register || rollback
code=$(curl -s -o /dev/null -m 6 -w '%{http_code}' http://127.0.0.1:8044/register/health)
echo "/register/health -> $code"; [ "$code" = "200" ] || rollback
echo "GREEN. salary_policy=$(md5of $SPF)"
echo " Reload the Salary sheets: Advance ded. carries the July advances;"
echo " Sheet 4 signature amounts = money actually left to hand over."
echo " Expected July lock total: Rs 59,163 (was 114,193 before advances)."
