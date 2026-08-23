#!/bin/bash
# =====================================================================
#  S198_G1 — A5: the Gist filled (the buildable slice of D241).
#  TWO files:
#    /root/wa/portal_gist.py   55e111d71e95032c21234ae540a49431 -> ef3ad196a00c2df44a7770553237a0e6
#      (cron builder gains console.db read-only: judgment funnel ·
#       staff-vs-AI · leads; selftest 21 -> 27; conversion/reputation/
#       ROI stay deferred WITH REASONS in the header)
#    /root/portal/portal.py    43ec35b1e87075ef942946e918db82f9 -> ab019dda3ac68e566de017c5ae536a6b
#      (three new Gist cards; fail-loud 'unavailable', never zero)
# =====================================================================
set -u
cd "$(dirname "$0")"
GIST=/root/wa/portal_gist.py
POR=/root/portal/portal.py
PSVC=clinic-portal.service
PY=/root/wa/venv/bin/python3
WANT_GIST=55e111d71e95032c21234ae540a49431
WANT_POR=43ec35b1e87075ef942946e918db82f9
NEW_GIST=ef3ad196a00c2df44a7770553237a0e6
NEW_POR=ab019dda3ac68e566de017c5ae536a6b
md5of(){ md5sum "$1" | awk '{print $1}'; }
echo "==============================================================="
echo " S198_G1 · the Gist filled (funnel · staff-vs-AI · leads)"
echo "==============================================================="
echo "[1/8] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "[2/8] currency gates (both live files)"
H=$(md5of "$GIST"); echo "      portal_gist : $H"
[ "$H" = "$WANT_GIST" ] || { echo "*** RED: expected $WANT_GIST. STOP — tell Claude this hash."; exit 1; }
H=$(md5of "$POR"); echo "      portal      : $H"
[ "$H" = "$WANT_POR" ] || { echo "*** RED: expected $WANT_POR. STOP — tell Claude this hash."; exit 1; }
echo "[3/8] gate on the candidates"
"$PY" gate_S198_G1.py ./portal.py ./portal_gist.py --baseline "$POR" || { echo "*** RED. STOP."; exit 1; }
TS=$(date +%Y%m%d_%H%M%S); BK=/root/deploy/_backup_S198_G1_$TS; mkdir -p "$BK"
echo "[4/8] backups -> $BK"; cp -p "$GIST" "$BK/portal_gist.py"; cp -p "$POR" "$BK/portal.py"
rollback(){ echo "*** RED -- ROLLBACK (both files)."; cp -p "$BK/portal_gist.py" "$GIST"; cp -p "$BK/portal.py" "$POR"; systemctl restart $PSVC; sleep 2; exit 1; }
echo "[5/8] swap + payload md5s + py_compile"
cp portal_gist.py "$GIST" || rollback
cp portal.py "$POR" || rollback
[ "$(md5of $GIST)" = "$NEW_GIST" ] || rollback
[ "$(md5of $POR)" = "$NEW_POR" ] || rollback
"$PY" -c "import py_compile; py_compile.compile('$GIST',doraise=True); print('      gist OK')" || rollback
"$PY" -c "import py_compile; py_compile.compile('$POR',doraise=True); print('      portal OK')" || rollback
echo "[6/8] gist selftest ON THE BOX (venv python; expect 27, 0 failed)"
"$PY" "$GIST" --selftest | tail -1
"$PY" "$GIST" --selftest 2>/dev/null | grep -q "27 checks, 0 failed" || rollback
echo "[7/8] LIVE dry-run — real console.db, writes NOTHING"
"$PY" "$GIST" --dry-run > /tmp/gist_dryrun.$$ 2>&1 || { echo "*** RED: dry-run crashed"; tail -20 /tmp/gist_dryrun.$$; rollback; }
grep -q '"funnel"' /tmp/gist_dryrun.$$ || { echo "*** RED: no funnel block in dry-run"; rollback; }
grep -o '"funnel": {[^}]*}' /tmp/gist_dryrun.$$ | head -1 | sed 's/^/      /'
rm -f /tmp/gist_dryrun.$$
echo "[8/8] restart portal + render check"
systemctl restart $PSVC || rollback
sleep 2
systemctl is-active --quiet $PSVC || rollback
echo "==============================================================="
echo " GREEN.  portal_gist.py $(md5of $GIST)"
echo "         portal.py      $(md5of $POR)"
echo " The next cron rebuild (every 30 min) writes the new blocks;"
echo " the Gist page shows them then. 'unavailable' before that is"
echo " the fail-loud contract working, not a fault."
echo " Backups: $BK"
echo "==============================================================="
