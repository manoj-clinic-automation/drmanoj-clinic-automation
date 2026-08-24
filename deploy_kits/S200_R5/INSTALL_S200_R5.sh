#!/usr/bin/env bash
# =====================================================================
#  S200_R5 — D346: THE GO-LIVE ENGINE. Three files, gated/backed/rolled TOGETHER.
#    /root/staff_register/salary_policy.py   dfe67285... -> 4521f1a6...  (v1.4)
#    /root/staff_register/staff_register.py  7d62435a... -> 40efbac3...  (v0.11)
#    /root/att_month_report.py               9ab98313... -> 0184cb13...  (v2.7)
#  Rules shipped: D341 derived Sunday weight (pay) · D341b roster gated ·
#  D342a suspended hold cancel/COLLECT · D342b/D345b exempt outside the loop ·
#  D343 divisor 30.5 · D345 ramp fine. No schema change; settings file is
#  UPDATED IN PLACE with a backup (day_divisor 30->30.5, dead keys dropped).
# =====================================================================
set -u
KIT="$(cd "$(dirname "$0")" && pwd)"
SPF=/root/staff_register/salary_policy.py;  SP_B=dfe67285944ec72fa2fb698651d160bd; SP_N=4521f1a6320893ac24039dce5861131f
SRF=/root/staff_register/staff_register.py; SR_B=7d62435a3a6caf5260bfc93eaf99257f; SR_N=40efbac35393b1c358b3509eb806870e
AMR=/root/att_month_report.py;              AM_B=9ab98313bbda7ae5555fb4b5a5a82c4b; AM_N=0184cb139907ee11adcc78c1ecab2daa
PY=/root/wa/venv/bin/python3
SET=/root/staff_register/salary_policy_settings.json
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
cd "$KIT" || exit 1
echo "[1/7] kit bytes"; md5sum -c SUMS.md5 || { echo "*** RED. STOP."; exit 1; }
echo "[2/7] currency gates (three live files)"
a=$(md5of "$SPF"); b=$(md5of "$SRF"); c=$(md5of "$AMR")
echo "      salary_policy    : $a"; echo "      staff_register   : $b"; echo "      att_month_report : $c"
if [ "$a" = "$SP_N" ] && [ "$b" = "$SR_N" ] && [ "$c" = "$AM_N" ]; then echo "      already new — nothing to do."; exit 0; fi
[ "$a" = "$SP_B" ] || { echo "*** RED: salary_policy expected $SP_B. STOP — tell Claude this hash."; exit 1; }
[ "$b" = "$SR_B" ] || { echo "*** RED: staff_register expected $SR_B. STOP — tell Claude this hash."; exit 1; }
[ "$c" = "$AM_B" ] || { echo "*** RED: att_month_report expected $AM_B. STOP — tell Claude this hash."; exit 1; }
TS="$(date +%Y%m%d_%H%M%S)"
echo "[3/7] backups (.bak_S200_R5_$TS)"
cp -p "$SPF" "$SPF.bak_S200_R5_$TS" && cp -p "$SRF" "$SRF.bak_S200_R5_$TS" && cp -p "$AMR" "$AMR.bak_S200_R5_$TS" || exit 1
[ -f "$SET" ] && cp -p "$SET" "$SET.bak_S200_R5_$TS" && echo "      settings backed up too"
rollback(){ echo "*** RED -- ROLLBACK (all files)."
  cp -p "$SPF.bak_S200_R5_$TS" "$SPF"; cp -p "$SRF.bak_S200_R5_$TS" "$SRF"; cp -p "$AMR.bak_S200_R5_$TS" "$AMR"
  [ -f "$SET.bak_S200_R5_$TS" ] && cp -p "$SET.bak_S200_R5_$TS" "$SET"
  systemctl restart staff-register >/dev/null 2>&1; sleep 2; systemctl is-active staff-register; exit 1; }
echo "[4/7] swap + payload md5s + py_compile"
cp "$KIT/salary_policy.py" "$SPF" && cp "$KIT/staff_register.py" "$SRF" && cp "$KIT/att_month_report.py" "$AMR" || rollback
[ "$(md5of "$SPF")" = "$SP_N" ] && [ "$(md5of "$SRF")" = "$SR_N" ] && [ "$(md5of "$AMR")" = "$AM_N" ] || rollback
"$PY" -c "import py_compile; [py_compile.compile(p, doraise=True) for p in ('$SPF','$SRF','$AMR')]" || rollback
echo "[5/7] settings file: divisor 30->30.5, dead keys out (backup kept)"
"$PY" - <<PYS || rollback
import json, os
p = "$SET"
if os.path.exists(p):
    d = json.load(open(p))
    ch = []
    if float(d.get("day_divisor", 0) or 0) == 30: d["day_divisor"] = 30.5; ch.append("day_divisor 30->30.5")
    for k in ("fine_excess", "excess_free_days"):
        if k in d: d.pop(k); ch.append("dropped " + k)
    if ch:
        json.dump(d, open(p, "w"), indent=1)
        print("      settings:", "; ".join(ch))
    else:
        print("      settings: nothing to change")
else:
    print("      no saved settings file — defaults (30.5, ramp 10) apply")
PYS
echo "[6/7] selftests ON THE BOX"
"$PY" "$SPF" --selftest >/tmp/s200_r5_pol.log 2>&1 && echo "      policy   SELFTEST OK" || { tail -5 /tmp/s200_r5_pol.log; rollback; }
( cd /root && "$PY" "$AMR" --selftest >/tmp/s200_r5_amr.log 2>&1 ) && echo "      att      SELFTEST OK" || { tail -5 /tmp/s200_r5_amr.log; rollback; }
"$PY" "$SRF" --selftest >/tmp/s200_r5_reg.log 2>&1 && echo "      register SELFTEST OK" || { tail -5 /tmp/s200_r5_reg.log; rollback; }
echo "[7/7] restart + probe"
systemctl restart staff-register || rollback
sleep 2
systemctl is-active --quiet staff-register || rollback
code=$(curl -s -o /dev/null -m 6 -w '%{http_code}' http://127.0.0.1:8044/register/health)
echo "      /register/health -> $code"; [ "$code" = "200" ] || rollback
echo "==============================================================="
echo " GREEN.  salary_policy=$(md5of $SPF)"
echo "         staff_register=$(md5of $SRF)"
echo "         att_month_report=$(md5of $AMR)"
echo " NEXT (July go-live, in order):"
echo "   1. VERIFY: run the July dump (Claude has the command) — the numbers"
echo "      must match the workbook to the paisa BEFORE any lock."
echo "   2. Settings page -> ENFORCE FROM = 2026-07 (your deliberate switch)."
echo "   3. Month-end flow 2026-07 -> approve Sheet 1 + Sheet 2 -> LOCK."
echo "      The lock writes the FINAL sheets and records every suspended"
echo "      charge for August's improvement test."
echo "==============================================================="
