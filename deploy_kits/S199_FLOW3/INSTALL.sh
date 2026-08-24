#!/usr/bin/env bash
# S199_FLOW3 — THE LOCK DESK (owner rulings S199-D):
#  /register/salary rebuilt on the NEW engine: big buttons, readiness checklist
#  (dates / Sheet1+2 / enforcement / month-end), summary identical to Sheet 3.
#  The LOCK records NEW-model numbers, stores the FINAL sheets, writes the hold
#  ledger (re-lock-safe), and REFUSES any month not covered by ENFORCE FROM.
#  Incentive -> the Diwali pot (not in monthly NET), per S163 kept.
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
SRF="/root/staff_register/staff_register.py";  SR_BASE="d5819b954d23b79a28fa568ea63cc4ff"; SR_NEW="124c6eb2c5dc03055c70ac427c8347bb"
SPF="/root/staff_register/salary_policy.py";   SP_BASE="8cba90f4e08f677dc5329794857dcbed"; SP_NEW="7f86cc8702b9fa48940e31a5ed2869d4"
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
TS="$(date +%Y%m%d_%H%M%S)"
gate(){ cur="$(md5of "$1" || true)"
  if [ "$cur" = "$3" ]; then echo "$1 already new — skip"; return 0; fi
  [ "$cur" = "$2" ] || { echo "REFUSE: $1 unknown bytes ($cur vs $2)."; exit 1; }
  cp -p "$1" "$1.bak_S199_FLOW3_$TS"; cp "$KIT/$4" "$1"
  [ "$(md5of "$1")" = "$3" ] || { echo "FAIL $1 — restoring"; cp -p "$1.bak_S199_FLOW3_$TS" "$1"; exit 1; }
  echo "$1 -> $3"; }
gate "$SPF" "$SP_BASE" "$SP_NEW" salary_policy.py
gate "$SRF" "$SR_BASE" "$SR_NEW" staff_register.py
/root/wa/venv/bin/python3 -c "import py_compile; [py_compile.compile(p, doraise=True) for p in ('$SRF','$SPF')]" || { echo COMPILE-FAIL; exit 1; }
/root/wa/venv/bin/python3 "$SPF" --selftest || { echo "policy selftest FAILED"; exit 1; }
/root/wa/venv/bin/python3 "$SRF" --selftest >/tmp/flow3_reg.log 2>&1 && echo "register SELFTEST OK" \
  || { echo "register selftest FAILED — restoring"; cp -p "$SRF.bak_S199_FLOW3_$TS" "$SRF" 2>/dev/null||true; cp -p "$SPF.bak_S199_FLOW3_$TS" "$SPF" 2>/dev/null||true; tail -5 /tmp/flow3_reg.log; exit 1; }
systemctl restart staff-register && sleep 2 && systemctl is-active staff-register
echo "== DONE. Open portal -> Salary: the LOCK DESK =="
echo "pins: staff_register=$SR_NEW salary_policy=$SP_NEW"
