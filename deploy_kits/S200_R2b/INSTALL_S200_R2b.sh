#!/bin/bash
# =====================================================================
#  S200_R2b — phase 1b of the portal-PWA unification.
#  ONE file: /root/portal/portal.py
#    ab019dda3ac68e566de017c5ae536a6b  ->  a48f418961c950f42de744d3729d91bd
#  Three links go SAME-ORIGIN (/register/...): the Staff Register tile,
#  the Salary tile, the "Register to enter" health chip. Nothing else.
#  Requires S200_R2a green (the /register proxy on the followup vhost).
# =====================================================================
set -u
cd "$(dirname "$0")"
POR=/root/portal/portal.py
PSVC=clinic-portal.service
PY=/root/wa/venv/bin/python3
WANT=ab019dda3ac68e566de017c5ae536a6b
NEW=a48f418961c950f42de744d3729d91bd
md5of(){ md5sum "$1" | awk '{print $1}'; }
echo "==============================================================="
echo " S200_R2b · register tiles same-origin (stay inside the PWA)"
echo "==============================================================="
echo "[1/6] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "[2/6] prerequisite: the R2a proxy must be answering"
code=$(curl -s -k -m 6 -o /dev/null -w '%{http_code}' -H "Host: followup.dr-manoj.in" https://127.0.0.1/register/health)
echo "      followup /register/health -> $code"
[ "$code" = "200" ] || { echo "*** RED: R2a proxy not live — install S200_R2a first. STOP."; exit 1; }
echo "[3/6] currency gate on the live portal"
H=$(md5of "$POR"); echo "      portal : $H"
if [ "$H" = "$NEW" ]; then echo "      already the new build — nothing to do."; exit 0; fi
[ "$H" = "$WANT" ] || { echo "*** RED: expected $WANT. STOP — tell Claude this hash."; exit 1; }
TS=$(date +%Y%m%d_%H%M%S); BK=/root/deploy/_backup_S200_R2b_$TS; mkdir -p "$BK"
echo "[4/6] backup -> $BK"; cp -p "$POR" "$BK/portal.py"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/portal.py" "$POR"; systemctl restart $PSVC; sleep 2; exit 1; }
echo "[5/6] swap + payload md5 + py_compile"
cp portal.py "$POR" || rollback
[ "$(md5of $POR)" = "$NEW" ] || rollback
"$PY" -c "import py_compile; py_compile.compile('$POR',doraise=True); print('      portal OK')" || rollback
echo "[6/6] restart + probes"
systemctl restart $PSVC || rollback
sleep 2
systemctl is-active --quiet $PSVC || rollback
pcode=$(curl -s -k -m 6 -o /dev/null -w '%{http_code}' -H "Host: followup.dr-manoj.in" https://127.0.0.1/portal)
echo "      /portal -> $pcode"
case "$pcode" in 200|301|302) : ;; *) rollback ;; esac
echo "==============================================================="
echo " GREEN.  portal.py $(md5of $POR)"
echo " Open the installed portal app: the Staff Register and Salary"
echo " tiles (and the Register chip) now stay inside the app."
echo "==============================================================="
