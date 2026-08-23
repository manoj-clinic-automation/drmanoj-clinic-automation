#!/bin/bash
# =====================================================================
#  S198_P5 — remove the duplicate Payment Register tile (owner, 23-Aug):
#  the Inbox Janitor tile already opens the same sheet. Janitor desc now
#  says what it opens. ONE file: portal.py  e2484429... -> 43ec35b1...
# =====================================================================
set -u
cd "$(dirname "$0")"
POR=/root/portal/portal.py
PSVC=clinic-portal.service
PY=/root/wa/venv/bin/python3
WANT_POR=e2484429cfb0217cb6b8d6f3a44ce5c8
NEW_POR=43ec35b1e87075ef942946e918db82f9
md5of(){ md5sum "$1" | awk '{print $1}'; }
echo "==============================================================="
echo " S198_P5 · duplicate tile removed"
echo "==============================================================="
echo "[1/5] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "[2/5] currency gate"
H=$(md5of "$POR"); echo "      portal : $H"
[ "$H" = "$WANT_POR" ] || { echo "*** RED: expected $WANT_POR. STOP — tell Claude this hash."; exit 1; }
echo "[3/5] gate on the candidate"
"$PY" gate_S198_P5.py ./portal.py --baseline "$POR" || { echo "*** RED. STOP."; exit 1; }
TS=$(date +%Y%m%d_%H%M%S); BK=/root/deploy/_backup_S198_P5_$TS; mkdir -p "$BK"
echo "[4/5] backup + swap + compile"; cp -p "$POR" "$BK/portal.py"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/portal.py" "$POR"; systemctl restart $PSVC; sleep 2; exit 1; }
cp portal.py "$POR" || rollback
[ "$(md5of $POR)" = "$NEW_POR" ] || rollback
"$PY" -c "import py_compile; py_compile.compile('$POR',doraise=True); print('      portal OK')" || rollback
echo "[5/5] restart + render check"
systemctl restart $PSVC || rollback
sleep 2
systemctl is-active --quiet $PSVC || rollback
"$PY" - <<'PYEOF' || rollback
import importlib.util
spec = importlib.util.spec_from_file_location("lp", "/root/portal/portal.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m._usable = lambda: True; m._authed = lambda r: True; m._sso_ready = lambda: True
m._sso_user = lambda r: {"user": "manoj", "role": "doctor"}
m._is_clinic_pc = lambda r: False
with m.app.test_client() as c:
    h = c.get("/portal").get_data(as_text=True)
assert 'nm">Payment Register</div>' not in h and 'nm">Inbox Janitor</div>' in h
print("      duplicate gone; Janitor + Renewals stand")
PYEOF
echo "==============================================================="
echo " GREEN.  portal.py $(md5of $POR)   Backup: $BK"
echo "==============================================================="
