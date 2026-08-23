#!/bin/bash
# =====================================================================
#  S198_P1 v2 — the portal HOME page revamp (owner-approved; v2 = dark theme kept, calls together, GMB up, Case Pack down, back-to-top; v1 never installed).
#
#  ONE file: portal.py  ee749cd9... -> dc093f1f...
#   * DARK scheme kept (owner ruling 23-Aug) with the new compact layout;
#     PAGE_HEAD untouched: login/console/gist/digest keep their look
#   * 46px floating back-to-top; calls sit together, GMB up, Case Pack down
#   * Portal Health hero + 3 live chips (doctor only, fail-soft, reuses
#     the existing checker-only tile-summary + review-counts fetches)
#   * compact half-height tiles; all sections one screen on a PC
#   * NEW groups: Staff (attendance family together) · Personal & Health
#   * Clinic-PC tools render as the migration-queue chip row (pc gating
#     unchanged); stale held tiles retired (Ayushman/Estimate -> Case
#     Pack; WABA Send = Send WhatsApp; Nutrition folded into Vitals)
#   * NEW tiles: Payment Register (capability URL, MANUAL until set)
#     and Forms & Downloads (held, flips at A3)
#   * roles, masks, URLs, fetch hooks all preserved (gate 127/127 + the
#     URL-preservation block against the live baseline)
# =====================================================================
set -u
cd "$(dirname "$0")"
POR=/root/portal/portal.py
PSVC=clinic-portal.service
PY=/root/wa/venv/bin/python3
WANT_POR=ee749cd9f3ac1294aab0d13ce069efc1
NEW_POR=dc093f1f83598b4e1927c2caee639fc7

md5of(){ md5sum "$1" | awk '{print $1}'; }

echo "==============================================================="
echo " S198_P1 · portal home revamp"
echo "==============================================================="
echo "[1/8] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }

echo "[2/8] currency gate (live portal.py)"
H=$(md5of "$POR"); echo "      portal : $H"
[ "$H" = "$WANT_POR" ] || { echo "*** RED: expected $WANT_POR. STOP — tell Claude this hash."; exit 1; }

echo "[3/8] the served-HTML gate, on the CANDIDATE, before anything moves"
"$PY" gate_S198_P1.py ./portal.py --baseline "$POR" || { echo "*** RED: gate refused the candidate. STOP."; exit 1; }

TS=$(date +%Y%m%d_%H%M%S); BK=/root/deploy/_backup_S198_P1_$TS; mkdir -p "$BK"
echo "[4/8] backup -> $BK"; cp -p "$POR" "$BK/portal.py"
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK/portal.py" "$POR"; systemctl restart $PSVC; sleep 2; echo "   portal: $(systemctl is-active $PSVC)"; exit 1; }

echo "[5/8] swap + payload md5"
cp portal.py "$POR" || rollback
[ "$(md5of $POR)" = "$NEW_POR" ] || { echo "*** RED: portal bytes wrong"; rollback; }

echo "[6/8] py_compile"
"$PY" -c "import py_compile; py_compile.compile('$POR',doraise=True); print('      portal OK')" || rollback

echo "[7/8] restart"
systemctl restart $PSVC || rollback
sleep 2
systemctl is-active --quiet $PSVC || rollback
# informational only -- this box answers 301 to plain-HTTP probes on 8090
# (measured at the v2 install, old AND new bytes alike; the S196 installer
# printed the same and never gated on it). A code is printed, never judged.
curl -s -o /dev/null -w "      /portal/health -> HTTP %{http_code} (informational)\n" -m 5 http://127.0.0.1:8090/portal/health || true

echo "[8/8] the INSTALLED bytes serve the new page (app render path, no network shape assumed)"
"$PY" - <<'PYEOF' || rollback
import importlib.util
spec = importlib.util.spec_from_file_location("live_portal", "/root/portal/portal.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m._usable = lambda: True; m._authed = lambda r: True; m._sso_ready = lambda: True
m._sso_user = lambda r: {"user": "manoj", "role": "doctor"}
m._is_clinic_pc = lambda r: False
with m.app.test_client() as c:
    h = c.get("/portal").get_data(as_text=True)
assert "--bg:#0f2233" in h, "dark scheme missing"
assert 'id="toTop"' in h, "back-to-top missing"
assert 'id="healthHero"' in h, "health hero missing"
assert h.index('nm">Call Console<') < h.index('nm">Call Tracker<'), "tile order wrong"
print("      installed bytes render the v2 home page OK")
PYEOF

echo "==============================================================="
echo " GREEN.  portal.py $(md5of $POR)"
echo ""
echo " ONE follow-up, when convenient (lights the Payment Register tile):"
echo "   1. open the 'Payment Register' Google Sheet in your PERSONAL"
echo "      Drive and copy its URL"
echo "   2. add ONE line to /root/portal/portal_config.py :"
echo "        PAYMENT_REGISTER_URL = \"https://docs.google.com/...\""
echo "   3. systemctl restart clinic-portal.service"
echo " Until then the tile shows MANUAL and everything else is live."
echo " Backup: $BK"
echo "==============================================================="
