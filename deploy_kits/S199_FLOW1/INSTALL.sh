#!/usr/bin/env bash
# S199_FLOW1 — THE MONTH-END FLOW: salary_policy engine (progressive late +
# hold + settings) · Sheet1/Sheet2 pack with doors · approval-gated lock ·
# policy-settings page · Yes/No dress dropdowns + Aug data migration ·
# /me/month staff view. PREVIEW is standard: nothing touches pay.
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
SR="/root/staff_register/staff_register.py";  SR_BASE="c1fede9f723454d4fe8e01e1a45cc111"; SR_BASE2="0b73ee545a1719981db6f90a646bfac4"; SR_NEW="c9fd063dd3ef53d3eda681aaa344a318"
SP="/root/staff_register/salary_policy.py";   SP_NEW="e8cdd22307a59bf6850b43a39680ebd2"
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
TS="$(date +%Y%m%d_%H%M%S)"

echo "== dependency currency (refuse on drift) =="
[ "$(md5of /root/att_scenario.py)" = "4dcd19bc02675a07cf0a77fadff6605b" ] || { echo "REFUSE: att_scenario.py is not v2"; exit 1; }
[ "$(md5of /root/att_month_report.py)" = "9ab98313bbda7ae5555fb4b5a5a82c4b" ] || { echo "REFUSE: att_month_report.py drifted"; exit 1; }
[ "$(md5of /root/staff_register/salary_engine.py)" = "ca37c615a421d984bb2d8a2f89782ca2" ] || { echo "REFUSE: salary_engine.py drifted"; exit 1; }

echo "== staff_register gate =="
cur="$(md5of "$SR" || true)"
if [ "$cur" = "$SR_NEW" ]; then echo "staff_register already v0.6 — skip";
elif [ "$cur" = "$SR_BASE" ] || [ "$cur" = "$SR_BASE2" ]; then
  cp -p "$SR" "$SR.bak_S199_FLOW1_$TS"; cp "$KIT/staff_register.py" "$SR"
  [ "$(md5of "$SR")" = "$SR_NEW" ] || { echo FAIL; cp -p "$SR.bak_S199_FLOW1_$TS" "$SR"; exit 1; }
  echo "staff_register.py -> $SR_NEW"
else echo "REFUSE: $SR unknown bytes ($cur). Nothing changed."; exit 1; fi

echo "== salary_policy (new file) =="
curp="$(md5of "$SP" || true)"
if [ -n "$curp" ] && [ "$curp" != "$SP_NEW" ]; then cp -p "$SP" "$SP.bak_S199_FLOW1_$TS"; fi
cp "$KIT/salary_policy.py" "$SP"
[ "$(md5of "$SP")" = "$SP_NEW" ] || { echo "FAIL: salary_policy hash"; exit 1; }

echo "== compile + selftests on the box =="
/root/wa/venv/bin/python3 -c "import py_compile; py_compile.compile('$SR', doraise=True); py_compile.compile('$SP', doraise=True)" \
  || { echo "COMPILE FAILED — restoring"; cp -p "$SR.bak_S199_FLOW1_$TS" "$SR" 2>/dev/null||true; exit 1; }
/root/wa/venv/bin/python3 "$SP" --selftest || { echo "policy selftest FAILED — restoring"; cp -p "$SR.bak_S199_FLOW1_$TS" "$SR" 2>/dev/null||true; exit 1; }
/root/wa/venv/bin/python3 "$SR" --selftest >/tmp/flow1_selftest.log 2>&1 \
  && echo "register SELFTEST OK" \
  || { echo "register selftest FAILED — restoring"; cp -p "$SR.bak_S199_FLOW1_$TS" "$SR"; tail -5 /tmp/flow1_selftest.log; exit 1; }

echo "== August dress/i-card migration (owner ruling: ticks meant YES) =="
/root/wa/venv/bin/python3 "$KIT/migrate_dress_S199.py"

systemctl restart staff-register && sleep 2 && systemctl is-active staff-register

echo "== July + August preview files (smoke) =="
cd /root/staff_register && /root/wa/venv/bin/python3 salary_policy.py 2026-07 && /root/wa/venv/bin/python3 salary_policy.py 2026-08

echo "== DONE. Portal -> Salary -> 'Month-end flow' pill. Settings: /register/salary/policy-settings =="
echo "pins: staff_register.py=$SR_NEW salary_policy.py=$SP_NEW"
