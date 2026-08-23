#!/bin/bash
# =====================================================================
#  S198_P2 — A3: Forms & Downloads on the portal.
#
#  ONE file: portal.py  dc093f1f... -> 2a162ec4...
#   * NEW /portal/forms: print-ready clinic forms. Anyone logged in can
#     Open/Print and Download; ONLY a proven doctor (F-98 gate) can add
#     or remove — upload happens on the page itself.
#   * Files live at /root/portal/forms/ ONLY — never in the PUBLIC repo
#     (D320). Names sanitised hard (basename + charset + extension
#     allowlist); traversal is a 404 by construction.
#   * The Forms & Downloads tile flips LIVE for doctor+manager+staff.
#   * Everything else byte-preserved (gate 20/20 incl. URL-preservation
#     against the live baseline; only the Forms tile row changed).
# =====================================================================
set -u
cd "$(dirname "$0")"
POR=/root/portal/portal.py
PSVC=clinic-portal.service
PY=/root/wa/venv/bin/python3
WANT_POR=dc093f1f83598b4e1927c2caee639fc7
NEW_POR=2a162ec49bec4bf111a11dfb97e8d398

md5of(){ md5sum "$1" | awk '{print $1}'; }

echo "==============================================================="
echo " S198_P2 · Forms & Downloads"
echo "==============================================================="
echo "[1/7] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }

echo "[2/7] currency gate (live portal.py)"
H=$(md5of "$POR"); echo "      portal : $H"
[ "$H" = "$WANT_POR" ] || { echo "*** RED: expected $WANT_POR. STOP — tell Claude this hash."; exit 1; }

echo "[3/7] the behaviour gate, on the CANDIDATE, before anything moves"
"$PY" gate_S198_P2.py ./portal.py --baseline "$POR" || { echo "*** RED: gate refused the candidate. STOP."; exit 1; }

TS=$(date +%Y%m%d_%H%M%S); BK=/root/deploy/_backup_S198_P2_$TS; mkdir -p "$BK"
echo "[4/7] backup -> $BK"; cp -p "$POR" "$BK/portal.py"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/portal.py" "$POR"; systemctl restart $PSVC; sleep 2; echo "   portal: $(systemctl is-active $PSVC)"; exit 1; }

echo "[5/7] swap + payload md5 + the forms folder"
cp portal.py "$POR" || rollback
[ "$(md5of $POR)" = "$NEW_POR" ] || { echo "*** RED: portal bytes wrong"; rollback; }
mkdir -p /root/portal/forms && chmod 700 /root/portal/forms

echo "[6/7] py_compile + restart"
"$PY" -c "import py_compile; py_compile.compile('$POR',doraise=True); print('      portal OK')" || rollback
systemctl restart $PSVC || rollback
sleep 2
systemctl is-active --quiet $PSVC || rollback

echo "[7/7] the INSTALLED bytes serve the forms page (app render path)"
"$PY" - <<'PYEOF' || rollback
import importlib.util
spec = importlib.util.spec_from_file_location("live_portal", "/root/portal/portal.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m._usable = lambda: True; m._authed = lambda r: True; m._sso_ready = lambda: True
m._sso_user = lambda r: {"user": "manoj", "role": "doctor"}
m._is_doctor = lambda r: True; m._is_clinic_pc = lambda r: False
with m.app.test_client() as c:
    h = c.get("/portal/forms").get_data(as_text=True)
    assert "Forms" in h and "/portal/forms/upload" in h, "forms page wrong"
    hh = c.get("/portal").get_data(as_text=True)
    assert 'href="/portal/forms"' in hh, "tile not live"
print("      installed bytes serve /portal/forms OK; tile live")
PYEOF

echo "==============================================================="
echo " GREEN.  portal.py $(md5of $POR)"
echo " Open the Forms & Downloads tile and upload your first form —"
echo " PDF prints best. Staff see every form; only you can add/remove."
echo " Backup: $BK"
echo "==============================================================="
