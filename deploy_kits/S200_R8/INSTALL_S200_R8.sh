#!/usr/bin/env bash
# =====================================================================
#  S200_R8 — phase 2 of the PWA unification + sheet polish.
#   1. followup vhost += /ledger -> 127.0.0.1:8043  (append, like R2a)
#   2. /root/portal/portal.py               a48f4189... -> 24ea2c0b...  (ledger tiles same-origin)
#   3. /root/staff_register/salary_policy.py c9dd846e... -> 73aca693...  (v1.6: back buttons, 16px bold sheets, month nav)
#  Everything gated; vhost restored + both files rolled back on failure.
# =====================================================================
set -u
KIT="$(cd "$(dirname "$0")" && pwd)"
VH="/usr/local/lsws/conf/vhosts/followup.dr-manoj.in/vhost.conf"
LSWSCTRL="/usr/local/lsws/bin/lswsctrl"
POR=/root/portal/portal.py;                PO_B=a48f418961c950f42de744d3729d91bd; PO_N=24ea2c0b44bad08fbce71908a5019ecc
SPF=/root/staff_register/salary_policy.py; SP_B=c9dd846ef5bc971b905ac33e2ad6eded; SP_N=73aca693e28c4670af74c0c016643af9
BLOCK="$KIT/ledger_proxy.block"; BLOCK_MD5=cb0a5ded860929e93c8ccbb354aee7fa
PY=/root/wa/venv/bin/python3
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
probe(){ curl -s -k -o /dev/null -m 6 -w '%{http_code}' -H "Host: followup.dr-manoj.in" "https://127.0.0.1$1" 2>/dev/null || echo 000; }
bad(){ case "$1" in 000|404|502|503) return 0;; *) return 1;; esac; }
cd "$KIT" || exit 1
echo "[1/7] kit bytes"; md5sum -c SUMS.md5 || { echo "*** RED. STOP."; exit 1; }
[ "$(md5of "$BLOCK")" = "$BLOCK_MD5" ] || { echo "*** RED: block bytes"; exit 1; }
echo "[2/7] currency gates"
a=$(md5of "$POR"); b=$(md5of "$SPF")
echo "      portal        : $a"; echo "      salary_policy : $b"
if [ "$a" = "$PO_N" ] && [ "$b" = "$SP_N" ] && grep -qE '^[[:space:]]*context[[:space:]]+/ledger\b' "$VH"; then
  echo "      already new — nothing to do."; exit 0; fi
[ "$a" = "$PO_B" ] || { echo "*** RED: portal expected $PO_B. STOP — tell Claude this hash."; exit 1; }
[ "$b" = "$SP_B" ] || { echo "*** RED: salary_policy expected $SP_B. STOP — tell Claude this hash."; exit 1; }
lc=$(curl -s -o /dev/null -m 5 -w '%{http_code}' http://127.0.0.1:8043/ledger/login 2>/dev/null)
case "$lc" in 200|301|302) : ;; *) echo "*** RED: ledger backend 8043 not healthy ($lc). STOP."; exit 1;; esac
pre_por="$(probe /portal)"; pre_reg="$(probe /register/health)"
echo "      pre: /portal=$pre_por /register/health=$pre_reg"
if bad "$pre_por" || bad "$pre_reg"; then echo "*** RED: an existing path already failing. STOP."; exit 1; fi
TS="$(date +%Y%m%d_%H%M%S)"
echo "[3/7] backups"
cp -p "$VH" "$VH.bak_S200_R8_$TS" && cp -p "$POR" "$POR.bak_S200_R8_$TS" && cp -p "$SPF" "$SPF.bak_S200_R8_$TS" || exit 1
rollback(){ echo "*** RED -- ROLLBACK (vhost + both files)."
  cp -p "$VH.bak_S200_R8_$TS" "$VH"; cp -p "$POR.bak_S200_R8_$TS" "$POR"; cp -p "$SPF.bak_S200_R8_$TS" "$SPF"
  "$LSWSCTRL" restart >/dev/null 2>&1; systemctl restart clinic-portal staff-register >/dev/null 2>&1
  sleep 3; exit 1; }
echo "[4/7] vhost append (skipped if /ledger already present)"
if ! grep -qE '^[[:space:]]*context[[:space:]]+/ledger\b' "$VH"; then
  printf '\n' >> "$VH"; cat "$BLOCK" >> "$VH"
fi
echo "[5/7] swap + md5 + compile"
cp "$KIT/portal.py" "$POR" && cp "$KIT/salary_policy.py" "$SPF" || rollback
[ "$(md5of "$POR")" = "$PO_N" ] && [ "$(md5of "$SPF")" = "$SP_N" ] || rollback
"$PY" -c "import py_compile; [py_compile.compile(p, doraise=True) for p in ('$POR','$SPF')]" || rollback
"$PY" "$SPF" --selftest >/tmp/s200_r8_pol.log 2>&1 && echo "      policy SELFTEST OK" || { tail -5 /tmp/s200_r8_pol.log; rollback; }
echo "[6/7] restarts"
"$LSWSCTRL" restart >/tmp/s200_r8_lsws.log 2>&1 || true
systemctl restart clinic-portal staff-register || rollback
sleep 3
systemctl is-active --quiet clinic-portal || rollback
systemctl is-active --quiet staff-register || rollback
echo "[7/7] probes"
led="$(probe /ledger/login)"; por="$(probe /portal)"; reg="$(probe /register/health)"
echo "      post: /ledger/login=$led /portal=$por /register/health=$reg"
ok=0; case "$led" in 200|301|302) ok=1;; esac
if [ "$ok" = 1 ] && ! bad "$por" && ! bad "$reg"; then
  echo "==============================================================="
  echo " GREEN. The ledger lives under the portal domain — every Sheet-2"
  echo " ledger door now opens. Portal tiles point same-origin."
  echo " Sheets: 16px bold cells, real Back buttons, month arrows in the nav."
  echo "==============================================================="
else
  echo "PROBE FAILED — rolling back."; rollback
fi
