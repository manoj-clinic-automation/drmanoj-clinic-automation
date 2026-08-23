#!/bin/bash
# =====================================================================
#  S198_P4 — A4: the portal as a phone app (PWA).
#  ONE file: portal.py  40b10a8b... -> e2484429...
#  The S196_ATT2 pattern on the portal itself: manifest + the two REAL
#  clinic-logo icons (byte-identical to ATT2's), head links on every
#  portal page (login included). NO service worker (ATT2 ruling kept:
#  nothing cached, every view live). scope "/" keeps finance pages
#  inside the app window. ZERO tile changes (gate-proven).
# =====================================================================
set -u
cd "$(dirname "$0")"
POR=/root/portal/portal.py
PSVC=clinic-portal.service
PY=/root/wa/venv/bin/python3
WANT_POR=40b10a8b7993176cb0469537060e7a43
NEW_POR=e2484429cfb0217cb6b8d6f3a44ce5c8

md5of(){ md5sum "$1" | awk '{print $1}'; }
echo "==============================================================="
echo " S198_P4 · the portal becomes an installable app"
echo "==============================================================="
echo "[1/6] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "[2/6] currency gate"
H=$(md5of "$POR"); echo "      portal : $H"
[ "$H" = "$WANT_POR" ] || { echo "*** RED: expected $WANT_POR. STOP — tell Claude this hash."; exit 1; }
echo "[3/6] gate on the candidate"
"$PY" gate_S198_P4.py ./portal.py --baseline "$POR" || { echo "*** RED. STOP."; exit 1; }
TS=$(date +%Y%m%d_%H%M%S); BK=/root/deploy/_backup_S198_P4_$TS; mkdir -p "$BK"
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
import importlib.util, json
spec = importlib.util.spec_from_file_location("lp", "/root/portal/portal.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
with m.app.test_client() as c:
    r = c.get("/portal/manifest.webmanifest")
    assert r.status_code == 200 and json.loads(r.get_data(as_text=True))["start_url"] == "/portal"
    assert c.get("/portal/pwa-icon-192.png").data[:4] == b"\x89PNG"
print("      installed bytes serve the manifest + icons OK")
PYEOF
echo "==============================================================="
echo " GREEN.  portal.py $(md5of $POR)"
echo ""
echo " STAFF PHONES (once per phone, the same drill as the biometric app):"
echo "   open  followup.dr-manoj.in/portal  in Chrome -> sign in ->"
echo "   menu (three dots) -> 'Add to Home screen' / 'Install app'."
echo " The clinic-logo icon opens the portal full-screen; each person"
echo " sees only their own role's tiles. Backup: $BK"
echo "==============================================================="
