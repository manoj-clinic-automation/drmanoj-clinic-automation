#!/usr/bin/env bash
# =====================================================================
#  S200_R3 — D339: the month FIX-ABSENTS desk + Sundays visible on Sheet 1.
#  TWO files, both in /root/staff_register/:
#    staff_register.py  e13059023b7b57fba170cb29db933119 -> 582e17145c74e7b0cf30162658cc953c
#    salary_policy.py   7f86cc8702b9fa48940e31a5ed2869d4 -> dfe67285944ec72fa2fb698651d160bd
#  No schema change, no migration, no data write at install.
#  Both files are gated, backed up and rolled back TOGETHER.
# =====================================================================
set -u
KIT="$(cd "$(dirname "$0")" && pwd)"
SRF="/root/staff_register/staff_register.py"
SPF="/root/staff_register/salary_policy.py"
SR_BASE="e13059023b7b57fba170cb29db933119"; SR_NEW="582e17145c74e7b0cf30162658cc953c"
SP_BASE="7f86cc8702b9fa48940e31a5ed2869d4"; SP_NEW="dfe67285944ec72fa2fb698651d160bd"
PY=/root/wa/venv/bin/python3
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
cd "$KIT" || exit 1

echo "[1/6] kit bytes"; md5sum -c SUMS.md5 || { echo "*** RED. STOP."; exit 1; }

echo "[2/6] currency gates"
cur_sr="$(md5of "$SRF")"; cur_sp="$(md5of "$SPF")"
echo "      staff_register : $cur_sr"
echo "      salary_policy  : $cur_sp"
if [ "$cur_sr" = "$SR_NEW" ] && [ "$cur_sp" = "$SP_NEW" ]; then
  echo "      already the new build — nothing to do."; exit 0
fi
[ "$cur_sr" = "$SR_BASE" ] || { echo "*** RED: staff_register expected $SR_BASE. STOP — tell Claude this hash."; exit 1; }
[ "$cur_sp" = "$SP_BASE" ] || { echo "*** RED: salary_policy expected $SP_BASE. STOP — tell Claude this hash."; exit 1; }

TS="$(date +%Y%m%d_%H%M%S)"
echo "[3/6] backups (suffix .bak_S200_R3_$TS)"
cp -p "$SRF" "$SRF.bak_S200_R3_$TS" || exit 1
cp -p "$SPF" "$SPF.bak_S200_R3_$TS" || exit 1
rollback(){ echo "*** RED -- ROLLBACK (both files)."
            cp -p "$SRF.bak_S200_R3_$TS" "$SRF"
            cp -p "$SPF.bak_S200_R3_$TS" "$SPF"
            systemctl restart staff-register >/dev/null 2>&1
            sleep 2; systemctl is-active staff-register; exit 1; }

echo "[4/6] swap + payload md5s + py_compile"
cp "$KIT/staff_register.py" "$SRF" || rollback
cp "$KIT/salary_policy.py"  "$SPF" || rollback
[ "$(md5of "$SRF")" = "$SR_NEW" ] || rollback
[ "$(md5of "$SPF")" = "$SP_NEW" ] || rollback
"$PY" -c "import py_compile; [py_compile.compile(p, doraise=True) for p in ('$SRF','$SPF')]" || rollback

echo "[5/6] selftests ON THE BOX"
"$PY" "$SPF" --selftest >/tmp/s200_r3_pol.log 2>&1 && echo "      policy   SELFTEST OK" \
  || { echo "policy selftest FAILED"; tail -5 /tmp/s200_r3_pol.log; rollback; }
"$PY" "$SRF" --selftest >/tmp/s200_r3_reg.log 2>&1 && echo "      register SELFTEST OK" \
  || { echo "register selftest FAILED"; tail -5 /tmp/s200_r3_reg.log; rollback; }

echo "[6/6] restart + probes"
systemctl restart staff-register || rollback
sleep 2
systemctl is-active --quiet staff-register || rollback
code=$(curl -s -o /dev/null -m 6 -w '%{http_code}' http://127.0.0.1:8044/register/health)
echo "      /register/health -> $code"
[ "$code" = "200" ] || rollback
echo "==============================================================="
echo " GREEN."
echo "   staff_register.py $(md5of "$SRF")"
echo "   salary_policy.py  $(md5of "$SPF")"
echo " Fix-absents desk : /register/fixabsents?ym=2026-07"
echo " (also linked from the top of Sheet 1)"
echo " Sheet 1 now marks Sunday columns (purple SUN)."
echo "==============================================================="
