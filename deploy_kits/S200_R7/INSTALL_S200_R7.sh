#!/usr/bin/env bash
# =====================================================================
#  S200_R7 — the month-end flow, made yours: approve WHERE you read,
#  bigger fonts, expandable fix-absents, explained what-if, July manual
#  advances on Sheet 2, Darpan's full picture + ledger doors.
#    /root/staff_register/salary_policy.py   9b14c340... -> c9dd846e...  (v1.5)
#    /root/staff_register/staff_register.py  40efbac3... -> f85a4b06...  (v0.12)
#  (July's manual-advances data file travels OUTSIDE git — D320/F-31: salary
#   figures never enter the repo. Claude gives a paste-block for the box.)
# =====================================================================
set -u
KIT="$(cd "$(dirname "$0")" && pwd)"
SPF=/root/staff_register/salary_policy.py;  SP_B=9b14c340530826563dafb7ea84e8cc93; SP_N=c9dd846ef5bc971b905ac33e2ad6eded
SRF=/root/staff_register/staff_register.py; SR_B=40efbac35393b1c358b3509eb806870e; SR_N=f85a4b0663ee0028c967cefec716bd12
PY=/root/wa/venv/bin/python3
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
cd "$KIT" || exit 1
echo "[1/6] kit bytes"; md5sum -c SUMS.md5 || { echo "*** RED. STOP."; exit 1; }
echo "[2/6] currency gates"
a=$(md5of "$SPF"); b=$(md5of "$SRF")
echo "      salary_policy  : $a"; echo "      staff_register : $b"
if [ "$a" = "$SP_N" ] && [ "$b" = "$SR_N" ]; then echo "      already new — nothing to do."; exit 0; fi
[ "$a" = "$SP_B" ] || { echo "*** RED: salary_policy expected $SP_B. STOP — tell Claude this hash."; exit 1; }
[ "$b" = "$SR_B" ] || { echo "*** RED: staff_register expected $SR_B. STOP — tell Claude this hash."; exit 1; }
TS="$(date +%Y%m%d_%H%M%S)"
echo "[3/6] backups (.bak_S200_R7_$TS)"
cp -p "$SPF" "$SPF.bak_S200_R7_$TS" && cp -p "$SRF" "$SRF.bak_S200_R7_$TS" || exit 1
rollback(){ echo "*** RED -- ROLLBACK (both)."
  cp -p "$SPF.bak_S200_R7_$TS" "$SPF"; cp -p "$SRF.bak_S200_R7_$TS" "$SRF"
  systemctl restart staff-register >/dev/null 2>&1; sleep 2; exit 1; }
echo "[4/6] swap + payload md5s + py_compile"
cp "$KIT/salary_policy.py" "$SPF" && cp "$KIT/staff_register.py" "$SRF" || rollback
[ "$(md5of "$SPF")" = "$SP_N" ] && [ "$(md5of "$SRF")" = "$SR_N" ] || rollback
"$PY" -c "import py_compile; [py_compile.compile(p, doraise=True) for p in ('$SPF','$SRF')]" || rollback
echo "[5/6] selftests ON THE BOX"
"$PY" "$SPF" --selftest >/tmp/s200_r7_pol.log 2>&1 && echo "      policy   SELFTEST OK" || { tail -5 /tmp/s200_r7_pol.log; rollback; }
"$PY" "$SRF" --selftest >/tmp/s200_r7_reg.log 2>&1 && echo "      register SELFTEST OK" || { tail -5 /tmp/s200_r7_reg.log; rollback; }
echo "[6/6] restart + probe"
systemctl restart staff-register || rollback
sleep 2
systemctl is-active --quiet staff-register || rollback
code=$(curl -s -o /dev/null -m 6 -w '%{http_code}' http://127.0.0.1:8044/register/health)
echo "      /register/health -> $code"; [ "$code" = "200" ] || rollback
echo "==============================================================="
echo " GREEN.  salary_policy=$(md5of $SPF)"
echo "         staff_register=$(md5of $SRF)"
echo " Open Sheet 1 — approve at the top of the page itself."
echo " Sheet 2 shows July's outside-ledger advances once the data file is"
echo " placed (paste-block from Claude, NOT via git — D320)."
echo " The lock desk shows both, with open-&-approve doors."
echo "==============================================================="
