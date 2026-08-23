#!/usr/bin/env bash
# S199_SALFIX — re-align salary_engine.py's SALARY_EXCLUDED with the ledger.
# Adds the two Rs 0 marker categories D332/SL6 put in the ledger at S192
# (ADVANCE_DEFER, CAPACITY_HOLD) so the drift guard passes again and the
# net / old-shadow / delta columns compute. No money changes (both are Rs 0).
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
LIVE="/root/staff_register/salary_engine.py"
BASE="5514918067243e3f39e7074144ee7db4"   # live pin we built on
NEW="ca37c615a421d984bb2d8a2f89782ca2"
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
TS="$(date +%Y%m%d_%H%M%S)"
cur="$(md5of "$LIVE" || true)"
if [ "$cur" = "$NEW" ]; then echo "salary_engine.py already patched — nothing to do"; exit 0; fi
[ "$cur" = "$BASE" ] || { echo "REFUSE: $LIVE is not the expected live bytes ($cur vs $BASE). Nothing changed."; exit 1; }
cp -p "$LIVE" "$LIVE.bak_S199_SALFIX_$TS"
cp "$KIT/salary_engine.py" "$LIVE"
[ "$(md5of "$LIVE")" = "$NEW" ] || { echo "FAIL: post-copy hash wrong — restoring"; cp -p "$LIVE.bak_S199_SALFIX_$TS" "$LIVE"; exit 1; }
echo "salary_engine.py -> $NEW OK (backup: $LIVE.bak_S199_SALFIX_$TS)"
echo "== self-test on the box (real ledger) =="
/root/wa/venv/bin/python3 "$LIVE" --selftest >/tmp/salfix_selftest.log 2>&1 \
  && echo "SELFTEST OK" \
  || { echo "SELFTEST FAILED — restoring; see /tmp/salfix_selftest.log"; cp -p "$LIVE.bak_S199_SALFIX_$TS" "$LIVE"; tail -8 /tmp/salfix_selftest.log; exit 1; }
systemctl restart staff-register && sleep 2 && systemctl is-active staff-register
echo "== DONE. Reopen your portal -> Salary: net / old(shadow) / delta will now show =="
echo "new pin: salary_engine.py=$NEW"
