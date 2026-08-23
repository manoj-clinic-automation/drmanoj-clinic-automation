#!/usr/bin/env bash
# S199_SCEN2 — wire the Deduction Scenario into the Staff Register salary page.
# Read-only feature. Updates TWO files, both behind a currency gate (D317):
#   /root/staff_register/staff_register.py   (Register-pinned live app; +1 route, +1 pill)
#   /root/att_scenario.py                    (v1.0 -> v1.1; adds render_document())
# Refuses to touch anything if the box does not hold the exact bytes we built on.
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"

SR_LIVE="/root/staff_register/staff_register.py"
SR_BASE="9087954c8a4a891e8cdd848d6a9d48b2"   # the S196 live pin we built on
SR_NEW="c1fede9f723454d4fe8e01e1a45cc111"    # this kit's staff_register.py

AS_LIVE="/root/att_scenario.py"
AS_BASE="4dc05e332cec8b713f77efb3e284ca18"   # att_scenario v1.0 (S199_SCEN1)
AS_NEW="5c4ff00910fcc1cbdcc92e6dc63eb7ff"    # this kit's att_scenario.py v1.1

md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
TS="$(date +%Y%m%d_%H%M%S)"

echo "== S199_SCEN2 currency gate =="
# --- att_scenario ---
cur="$(md5of "$AS_LIVE" || true)"
if [ "$cur" = "$AS_NEW" ]; then echo "att_scenario.py already v1.1 — skip";
elif [ "$cur" = "$AS_BASE" ] || [ -z "$cur" ]; then
  [ -n "$cur" ] && cp -p "$AS_LIVE" "$AS_LIVE.bak_S199_SCEN2_$TS"
  cp "$KIT/att_scenario.py" "$AS_LIVE"
  [ "$(md5of "$AS_LIVE")" = "$AS_NEW" ] || { echo "FAIL: att_scenario post-copy hash wrong"; exit 1; }
  echo "att_scenario.py -> v1.1 OK"
else echo "REFUSE: $AS_LIVE is unknown bytes ($cur). Expected v1.0 $AS_BASE. Nothing changed."; exit 1; fi

# --- staff_register (Register-pinned) ---
cur="$(md5of "$SR_LIVE" || true)"
if [ "$cur" = "$SR_NEW" ]; then echo "staff_register.py already at the new pin — skip";
elif [ "$cur" = "$SR_BASE" ]; then
  cp -p "$SR_LIVE" "$SR_LIVE.bak_S199_SCEN2_$TS"
  cp "$KIT/staff_register.py" "$SR_LIVE"
  [ "$(md5of "$SR_LIVE")" = "$SR_NEW" ] || { echo "FAIL: staff_register post-copy hash wrong — restoring"; cp -p "$SR_LIVE.bak_S199_SCEN2_$TS" "$SR_LIVE"; exit 1; }
  echo "staff_register.py -> $SR_NEW OK (backup: $SR_LIVE.bak_S199_SCEN2_$TS)"
else echo "REFUSE: $SR_LIVE is NOT the S196 live pin ($cur vs $SR_BASE). Nothing changed."; exit 1; fi

echo "== self-test (offline, on the box) =="
/root/wa/venv/bin/python3 "$SR_LIVE" --selftest >/tmp/scen2_selftest.log 2>&1 \
  && echo "SELFTEST OK" || { echo "SELFTEST FAILED — see /tmp/scen2_selftest.log; restoring staff_register"; \
       cp -p "$SR_LIVE.bak_S199_SCEN2_$TS" "$SR_LIVE" 2>/dev/null || true; tail -5 /tmp/scen2_selftest.log; exit 1; }

echo "== restart service =="
systemctl restart staff-register && sleep 2 && systemctl is-active staff-register

echo "== DONE. Open your portal -> Salary -> the 'Deduction scenario' pill, or /register/salary/scenario =="
echo "new pins: staff_register.py=$SR_NEW  att_scenario.py=$AS_NEW"
