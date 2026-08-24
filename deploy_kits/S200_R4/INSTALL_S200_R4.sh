#!/usr/bin/env bash
# =====================================================================
#  S200_R4 — D339b: the reason survives a submit · corrections listed · UNDO.
#  ONE file: /root/staff_register/staff_register.py
#    582e17145c74e7b0cf30162658cc953c (v0.9) -> 7d62435a3a6caf5260bfc93eaf99257f (v0.10)
#  No schema change, no migration, no data write at install.
# =====================================================================
set -u
KIT="$(cd "$(dirname "$0")" && pwd)"
SRF="/root/staff_register/staff_register.py"
BASE="582e17145c74e7b0cf30162658cc953c"; NEW="7d62435a3a6caf5260bfc93eaf99257f"
PY=/root/wa/venv/bin/python3
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
cd "$KIT" || exit 1

echo "[1/5] kit bytes"; md5sum -c SUMS.md5 || { echo "*** RED. STOP."; exit 1; }

echo "[2/5] currency gate"
cur="$(md5of "$SRF")"; echo "      staff_register : $cur"
[ "$cur" = "$NEW" ] && { echo "      already the new build — nothing to do."; exit 0; }
[ "$cur" = "$BASE" ] || { echo "*** RED: expected $BASE. STOP — tell Claude this hash."; exit 1; }

TS="$(date +%Y%m%d_%H%M%S)"; BK="$SRF.bak_S200_R4_$TS"
echo "[3/5] backup -> $BK"; cp -p "$SRF" "$BK" || exit 1
rollback(){ echo "*** RED -- ROLLBACK."; cp -p "$BK" "$SRF"
            systemctl restart staff-register >/dev/null 2>&1; sleep 2
            systemctl is-active staff-register; exit 1; }

echo "[4/5] swap + payload md5 + py_compile + selftest"
cp "$KIT/staff_register.py" "$SRF" || rollback
[ "$(md5of "$SRF")" = "$NEW" ] || rollback
"$PY" -c "import py_compile; py_compile.compile('$SRF', doraise=True)" || rollback
"$PY" "$SRF" --selftest >/tmp/s200_r4_reg.log 2>&1 && echo "      register SELFTEST OK" \
  || { echo "register selftest FAILED"; tail -5 /tmp/s200_r4_reg.log; rollback; }

echo "[5/5] restart + probe"
systemctl restart staff-register || rollback
sleep 2
systemctl is-active --quiet staff-register || rollback
code=$(curl -s -o /dev/null -m 6 -w '%{http_code}' http://127.0.0.1:8044/register/health)
echo "      /register/health -> $code"
[ "$code" = "200" ] || rollback
echo "==============================================================="
echo " GREEN.  staff_register.py $(md5of "$SRF")"
echo " Desk: /register/fixabsents?ym=2026-07"
echo "   · Reason is pre-filled and kept after every save."
echo "   · 'Corrections already made' lists what you have marked present."
echo "   · Tick there + Undo to put a day back to absent."
echo "==============================================================="
