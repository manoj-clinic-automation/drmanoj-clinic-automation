#!/usr/bin/env bash
# S200_R9 — advances grouped per staff (expandable, perks+pending+interest legend);
# the retired old salary computation DISARMED (its lock button removed, banner + doors
# to the register Lock desk). ONE file:
#   /root/staff_ledger.py  18052621e60c0840c3f736355947e589 -> eaa305cb1f04fd4e20a350626ff84aa6
set -u
KIT="$(cd "$(dirname "$0")" && pwd)"
SLF=/root/staff_ledger.py
B=18052621e60c0840c3f736355947e589; N=eaa305cb1f04fd4e20a350626ff84aa6
PY=/root/wa/venv/bin/python3
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
cd "$KIT" || exit 1
md5sum -c SUMS.md5 || { echo "*** RED. STOP."; exit 1; }
cur=$(md5of "$SLF"); echo "live: $cur"
[ "$cur" = "$N" ] && { echo "already new — nothing to do."; exit 0; }
[ "$cur" = "$B" ] || { echo "*** RED: expected $B. STOP — tell Claude this hash."; exit 1; }
TS=$(date +%Y%m%d_%H%M%S); cp -p "$SLF" "$SLF.bak_S200_R9_$TS" || exit 1
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$SLF.bak_S200_R9_$TS" "$SLF"
            systemctl restart staff-ledger >/dev/null 2>&1; sleep 2; exit 1; }
cp "$KIT/staff_ledger.py" "$SLF" || rollback
[ "$(md5of "$SLF")" = "$N" ] || rollback
"$PY" -c "import py_compile; py_compile.compile('$SLF', doraise=True)" || rollback
"$PY" "$SLF" --selftest >/tmp/s200_r9.log 2>&1 && echo "ledger SELFTEST OK" || { tail -5 /tmp/s200_r9.log; rollback; }
systemctl restart staff-ledger || rollback
sleep 2; systemctl is-active --quiet staff-ledger || rollback
code=$(curl -s -o /dev/null -m 6 -w '%{http_code}' http://127.0.0.1:8043/ledger/login)
echo "/ledger/login -> $code"
case "$code" in 200|301|302) : ;; *) rollback ;; esac
echo "GREEN. staff_ledger=$(md5of $SLF)"
echo " Advances: one expandable card per staff (perks, pending, interest legends)."
echo " /ledger/salary: old computation banner-retired; lock lives at the register desk."
