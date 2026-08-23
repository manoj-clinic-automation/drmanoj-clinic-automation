#!/bin/bash
# =====================================================================
#  S198_P3 — the Renewals tile (owner priority, 23-Aug).
#  ONE file: portal.py  2a162ec4... -> 40b10a8b...
#  ONE tile added (doctor-only, Personal & Health): "Renewals" -> the
#  Renewals Master v2 sheet the Inbox Janitor's digest nags from.
#  Nothing else moves (gate proves exactly one tile row added).
# =====================================================================
set -u
cd "$(dirname "$0")"
POR=/root/portal/portal.py
PSVC=clinic-portal.service
PY=/root/wa/venv/bin/python3
WANT_POR=2a162ec49bec4bf111a11dfb97e8d398
NEW_POR=40b10a8b7993176cb0469537060e7a43

md5of(){ md5sum "$1" | awk '{print $1}'; }
echo "==============================================================="
echo " S198_P3 · Renewals tile"
echo "==============================================================="
echo "[1/6] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "[2/6] currency gate"
H=$(md5of "$POR"); echo "      portal : $H"
[ "$H" = "$WANT_POR" ] || { echo "*** RED: expected $WANT_POR. STOP — tell Claude this hash."; exit 1; }
echo "[3/6] gate on the candidate"
"$PY" gate_S198_P3.py ./portal.py --baseline "$POR" || { echo "*** RED. STOP."; exit 1; }
TS=$(date +%Y%m%d_%H%M%S); BK=/root/deploy/_backup_S198_P3_$TS; mkdir -p "$BK"
echo "[4/6] backup -> $BK"; cp -p "$POR" "$BK/portal.py"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/portal.py" "$POR"; systemctl restart $PSVC; sleep 2; exit 1; }
echo "[5/6] swap + md5 + compile"
cp portal.py "$POR" || rollback
[ "$(md5of $POR)" = "$NEW_POR" ] || rollback
"$PY" -c "import py_compile; py_compile.compile('$POR',doraise=True); print('      portal OK')" || rollback
echo "[6/6] restart + render check"
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
assert 'nm">Renewals</div>' in h, "tile missing"
print("      installed bytes render the Renewals tile OK")
PYEOF
echo "==============================================================="
echo " GREEN.  portal.py $(md5of $POR)"
echo " The Renewals tile opens the Master v2 sheet directly."
echo " Backup: $BK"
echo "==============================================================="
