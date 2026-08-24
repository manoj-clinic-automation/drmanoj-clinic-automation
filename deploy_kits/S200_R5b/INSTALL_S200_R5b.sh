#!/usr/bin/env bash
# S200_R5b — the settings validator accepts -1 (derive) for sunday_weight_override.
# ONE file: /root/staff_register/salary_policy.py 4521f1a6... -> 756fb451...
set -u
KIT="$(cd "$(dirname "$0")" && pwd)"
SPF=/root/staff_register/salary_policy.py
B=4521f1a6320893ac24039dce5861131f; N=260944bf8493783ec102cbdd286db8c6
PY=/root/wa/venv/bin/python3
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
cd "$KIT" || exit 1
md5sum -c SUMS.md5 || { echo "*** RED. STOP."; exit 1; }
cur=$(md5of "$SPF"); echo "live: $cur"
[ "$cur" = "$N" ] && { echo "already new — nothing to do."; exit 0; }
[ "$cur" = "$B" ] || { echo "*** RED: expected $B. STOP — tell Claude this hash."; exit 1; }
TS=$(date +%Y%m%d_%H%M%S); cp -p "$SPF" "$SPF.bak_S200_R5b_$TS" || exit 1
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$SPF.bak_S200_R5b_$TS" "$SPF"
            systemctl restart staff-register >/dev/null 2>&1; sleep 2; exit 1; }
cp "$KIT/salary_policy.py" "$SPF" || rollback
[ "$(md5of "$SPF")" = "$N" ] || rollback
"$PY" -c "import py_compile; py_compile.compile('$SPF', doraise=True)" || rollback
"$PY" "$SPF" --selftest >/tmp/s200_r5b.log 2>&1 && echo "policy SELFTEST OK" || { tail -5 /tmp/s200_r5b.log; rollback; }
systemctl restart staff-register || rollback
sleep 2; systemctl is-active --quiet staff-register || rollback
code=$(curl -s -o /dev/null -m 6 -w '%{http_code}' http://127.0.0.1:8044/register/health)
echo "/register/health -> $code"; [ "$code" = "200" ] || rollback
echo "GREEN. salary_policy=$(md5of $SPF) — now save the settings page again (ENFORCE FROM 2026-07)."
