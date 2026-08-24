#!/usr/bin/env bash
# S199_FLOW2 — the owner's first-preview review: large-font redesigned sheets,
# half-month attendance blocks with visible punch times, today excluded,
# Darpan's separate money page (+outstation), night-duty/duty-credit columns,
# leaves/absent columns + no totals on Sheet 2, min-charge threshold, month-in-
# words captions ("MACHINE DATA" vs "FINAL"), sticky nav on every sheet, and
# the salary landing page's shadow/delta columns + parity banner REMOVED
# (Ledger fold -> "Ledger money", Pro-rate -> "Partial month adj.").
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
SRF="/root/staff_register/staff_register.py";  SR_BASE="c9fd063dd3ef53d3eda681aaa344a318"; SR_NEW="d5819b954d23b79a28fa568ea63cc4ff"
SPF="/root/staff_register/salary_policy.py";   SP_BASE="e8cdd22307a59bf6850b43a39680ebd2"; SP_NEW="8cba90f4e08f677dc5329794857dcbed"
SEF="/root/staff_register/salary_engine.py";   SE_BASE="ca37c615a421d984bb2d8a2f89782ca2"; SE_NEW="bedd468ee7b89b8f0c130d215a42b6d1"
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
TS="$(date +%Y%m%d_%H%M%S)"
gate(){ # $1 live $2 base $3 new $4 kitfile
  cur="$(md5of "$1" || true)"
  if [ "$cur" = "$3" ]; then echo "$1 already new — skip"; return 0; fi
  [ "$cur" = "$2" ] || { echo "REFUSE: $1 unknown bytes ($cur vs $2). Nothing changed."; exit 1; }
  cp -p "$1" "$1.bak_S199_FLOW2_$TS"
  cp "$KIT/$4" "$1"
  [ "$(md5of "$1")" = "$3" ] || { echo "FAIL hash $1 — restoring"; cp -p "$1.bak_S199_FLOW2_$TS" "$1"; exit 1; }
  echo "$1 -> $3"
}
gate "$SPF" "$SP_BASE" "$SP_NEW" salary_policy.py
gate "$SEF" "$SE_BASE" "$SE_NEW" salary_engine.py
gate "$SRF" "$SR_BASE" "$SR_NEW" staff_register.py
echo "== compile + selftests on the box =="
/root/wa/venv/bin/python3 -c "import py_compile; [py_compile.compile(p, doraise=True) for p in ('$SRF','$SPF','$SEF')]" || { echo COMPILE-FAIL; exit 1; }
/root/wa/venv/bin/python3 "$SPF" --selftest || { echo "policy selftest FAILED"; exit 1; }
/root/wa/venv/bin/python3 "$SEF" --selftest >/tmp/flow2_engine.log 2>&1 && echo "engine SELFTEST OK" || { echo "engine selftest FAILED"; tail -5 /tmp/flow2_engine.log; exit 1; }
/root/wa/venv/bin/python3 "$SRF" --selftest >/tmp/flow2_reg.log 2>&1 && echo "register SELFTEST OK" || { echo "register selftest FAILED — restoring all"; for p in "$SRF" "$SPF" "$SEF"; do cp -p "$p.bak_S199_FLOW2_$TS" "$p" 2>/dev/null||true; done; tail -5 /tmp/flow2_reg.log; exit 1; }
systemctl restart staff-register && sleep 2 && systemctl is-active staff-register
echo "== DONE. Reload the Month-end flow pages =="
echo "pins: staff_register=$SR_NEW salary_policy=$SP_NEW salary_engine=$SE_NEW"
