#!/usr/bin/env bash
# S199_SCEN3 — Scenario v2: three systems side by side, rewards first,
# enforcement-status banner, per-staff allowed_offs, extra-leaves C-model,
# old-system-as-practiced (validated on the July sheet), optional AS-PAID
# overlay. ONE file; the portal page picks it up immediately (no app change,
# no service restart needed — the route imports it per request... it does not:
# python caches the module, so we DO restart staff-register).
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
LIVE="/root/att_scenario.py"
BASE_V11="5c4ff00910fcc1cbdcc92e6dc63eb7ff"   # v1.1 (S199_SCEN2)
NEW="4dcd19bc02675a07cf0a77fadff6605b"
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
TS="$(date +%Y%m%d_%H%M%S)"
cur="$(md5of "$LIVE" || true)"
if [ "$cur" = "$NEW" ]; then echo "att_scenario.py already v2 — nothing to do"; exit 0; fi
[ "$cur" = "$BASE_V11" ] || { echo "REFUSE: $LIVE is not the v1.1 bytes ($cur vs $BASE_V11). Nothing changed."; exit 1; }
cp -p "$LIVE" "$LIVE.bak_S199_SCEN3_$TS"
cp "$KIT/att_scenario.py" "$LIVE"
[ "$(md5of "$LIVE")" = "$NEW" ] || { echo "FAIL: post-copy hash wrong — restoring"; cp -p "$LIVE.bak_S199_SCEN3_$TS" "$LIVE"; exit 1; }
/root/wa/venv/bin/python3 -c "import py_compile; py_compile.compile('/root/att_scenario.py', doraise=True)" \
  || { echo "COMPILE FAILED — restoring"; cp -p "$LIVE.bak_S199_SCEN3_$TS" "$LIVE"; exit 1; }
/root/wa/venv/bin/python3 /root/att_scenario.py --selftest \
  || { echo "SELFTEST FAILED — restoring"; cp -p "$LIVE.bak_S199_SCEN3_$TS" "$LIVE"; exit 1; }
systemctl restart staff-register && sleep 2 && systemctl is-active staff-register
echo "== DONE. att_scenario.py v2 = $NEW (backup $LIVE.bak_S199_SCEN3_$TS) =="
echo "Open: portal -> Salary -> Deduction scenario. Try ?ym=2026-07 and ?ym=2026-08."
