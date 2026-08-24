#!/usr/bin/env bash
# =====================================================================
#  S200_R6 — the Staff Ledger revamp + cover duty.
#    /root/staff_ledger.py                     acd7b538... -> 18052621...  (v3.3-S200-SL6)
#    /root/staff_register/salary_policy.py     260944bf... -> 9b14c340...
#  COVER_DUTY (Rs 200/day credit, narration required, maker_full+checker) ·
#  uniform/I-card fine rates FOLLOW the salary-policy settings (D336 Rs 15;
#  the ledger's Rs 20 was wrong) · dark mobile-first UI in the clinic colours.
#  Both files gated, backed up, rolled back TOGETHER.
# =====================================================================
set -u
KIT="$(cd "$(dirname "$0")" && pwd)"
SLF=/root/staff_ledger.py;                 SL_B=acd7b538ec9476f86e243c73eec3d3fd; SL_N=18052621e60c0840c3f736355947e589
SPF=/root/staff_register/salary_policy.py; SP_B=260944bf8493783ec102cbdd286db8c6; SP_N=9b14c340530826563dafb7ea84e8cc93
PY=/root/wa/venv/bin/python3
SVC_L=staff-ledger
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
cd "$KIT" || exit 1
echo "[1/6] kit bytes"; md5sum -c SUMS.md5 || { echo "*** RED. STOP."; exit 1; }
echo "[2/6] currency gates"
a=$(md5of "$SLF"); b=$(md5of "$SPF")
echo "      staff_ledger  : $a"; echo "      salary_policy : $b"
if [ "$a" = "$SL_N" ] && [ "$b" = "$SP_N" ]; then echo "      already new — nothing to do."; exit 0; fi
[ "$a" = "$SL_B" ] || { echo "*** RED: staff_ledger expected $SL_B. STOP — tell Claude this hash."; exit 1; }
[ "$b" = "$SP_B" ] || { echo "*** RED: salary_policy expected $SP_B. STOP — tell Claude this hash."; exit 1; }
TS="$(date +%Y%m%d_%H%M%S)"
echo "[3/6] backups (.bak_S200_R6_$TS)"
cp -p "$SLF" "$SLF.bak_S200_R6_$TS" && cp -p "$SPF" "$SPF.bak_S200_R6_$TS" || exit 1
rollback(){ echo "*** RED -- ROLLBACK (both)."
  cp -p "$SLF.bak_S200_R6_$TS" "$SLF"; cp -p "$SPF.bak_S200_R6_$TS" "$SPF"
  systemctl restart $SVC_L staff-register >/dev/null 2>&1; sleep 2; exit 1; }
echo "[4/6] swap + payload md5s + py_compile"
cp "$KIT/staff_ledger.py" "$SLF" && cp "$KIT/salary_policy.py" "$SPF" || rollback
[ "$(md5of "$SLF")" = "$SL_N" ] && [ "$(md5of "$SPF")" = "$SP_N" ] || rollback
"$PY" -c "import py_compile; [py_compile.compile(p, doraise=True) for p in ('$SLF','$SPF')]" || rollback
echo "[5/6] selftests ON THE BOX"
"$PY" "$SLF" --selftest >/tmp/s200_r6_led.log 2>&1 && echo "      ledger SELFTEST OK ($(tail -1 /tmp/s200_r6_led.log | cut -c1-40)...)" \
  || { tail -5 /tmp/s200_r6_led.log; rollback; }
"$PY" "$SPF" --selftest >/tmp/s200_r6_pol.log 2>&1 && echo "      policy SELFTEST OK" || { tail -5 /tmp/s200_r6_pol.log; rollback; }
echo "[6/6] restarts + probes"
systemctl restart $SVC_L staff-register || rollback
sleep 2
systemctl is-active --quiet $SVC_L || rollback
systemctl is-active --quiet staff-register || rollback
lcode=$(curl -s -o /dev/null -m 6 -w '%{http_code}' http://127.0.0.1:8043/ledger/login 2>/dev/null)
[ "$lcode" = "200" ] || lcode=$(curl -s -o /dev/null -m 6 -w '%{http_code}' http://127.0.0.1:8043/ledger/)
rcode=$(curl -s -o /dev/null -m 6 -w '%{http_code}' http://127.0.0.1:8044/register/health)
echo "      ledger -> $lcode · register -> $rcode"
case "$lcode" in 200|301|302) : ;; *) rollback ;; esac
[ "$rcode" = "200" ] || rollback
echo "==============================================================="
echo " GREEN.  staff_ledger=$(md5of $SLF)"
echo "         salary_policy=$(md5of $SPF)"
echo " New-entry form: dark, compact, paired rows, mobile-first."
echo " 'Cover duty (Rs 200/day)' in the category list (narration = who"
echo " was covered). Uniform/I-card fines now Rs 15 — from the policy"
echo " settings, changing there changes here."
echo "==============================================================="
