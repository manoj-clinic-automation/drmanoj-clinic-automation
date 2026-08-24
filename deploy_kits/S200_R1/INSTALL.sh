#!/usr/bin/env bash
# S200_R1 — D338: past-day presence correction (approver-only door).
#  Staff self-requests stay today-only (D334). This kit adds the APPROVER's
#  door: on the day page (/register/?d=YYYY-MM-DD) a "Past-day presence
#  correction" card for machine-absent staff — in-time (prefilled with the
#  shift start, editable) + compulsory reason -> an already-approved
#  present_request row, which every existing reader treats as a synthetic
#  punch (grid pill, att_month_report v2.6, the salary engine, Sheet 1's *).
#  NO schema change, NO migration, NO data write at install.
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
SRF="/root/staff_register/staff_register.py"
SR_BASE="124c6eb2c5dc03055c70ac427c8347bb"   # v0.7 — the S199 close pin
SR_NEW="e13059023b7b57fba170cb29db933119"    # v0.8 — S200_R1
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
TS="$(date +%Y%m%d_%H%M%S)"
cur="$(md5of "$SRF" || true)"
if [ "$cur" = "$SR_NEW" ]; then echo "$SRF already new — nothing to do"; exit 0; fi
[ "$cur" = "$SR_BASE" ] || { echo "REFUSE: $SRF unknown bytes ($cur vs $SR_BASE)."; exit 1; }
cp -p "$SRF" "$SRF.bak_S200_R1_$TS"
cp "$KIT/staff_register.py" "$SRF"
[ "$(md5of "$SRF")" = "$SR_NEW" ] || { echo "FAIL copy — restoring"; cp -p "$SRF.bak_S200_R1_$TS" "$SRF"; exit 1; }
/root/wa/venv/bin/python3 -c "import py_compile; py_compile.compile('$SRF', doraise=True)" \
  || { echo "COMPILE-FAIL — restoring"; cp -p "$SRF.bak_S200_R1_$TS" "$SRF"; exit 1; }
/root/wa/venv/bin/python3 "$SRF" --selftest >/tmp/s200_r1_reg.log 2>&1 && echo "register SELFTEST OK" \
  || { echo "register selftest FAILED — restoring"; cp -p "$SRF.bak_S200_R1_$TS" "$SRF"; tail -5 /tmp/s200_r1_reg.log; exit 1; }
systemctl restart staff-register && sleep 2 && systemctl is-active staff-register
echo "== DONE. Day page (?d=<date>) now carries the D338 correction card for approvers =="
echo "pin: staff_register=$SR_NEW (was $SR_BASE)"
