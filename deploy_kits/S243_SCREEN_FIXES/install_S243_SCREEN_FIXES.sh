#!/bin/bash
# =============================================================================
#  install_S243_SCREEN_FIXES.sh -- kit S243_SCREEN_FIXES -- two screen fixes, no gate change
#
#  Run by:  bash /root/deploy/repo/deploy_kits/S243_SCREEN_FIXES/install_S243_SCREEN_FIXES.sh
#
#  A  purchase_app.py  the bare /finance/purchase (with or without the slash) answered 404;
#                      one new rule sends it to /finance/purchase/page/hub. Shipped as the
#                      full file (rev 14 over rev 13 8090ca20), placed via .new + md5 + mv.
#  B  finance_app.py   /finance/daily bounced the doctor (medical CHECKER) to /portal with
#                      no word. A checker is now sent to /finance/review; the maker gate is
#                      NOT widened. The live file is not in the repo, so it is patched ON
#                      THIS BOX by patch_finance_daily_s243.py (anchor must occur once).
#
#  Gates: SUMS + KIT_ID -> live pins are the ones this kit was built on -> .bak_S243_<pin8>
#  of both -> place -> py_compile both -> import smoke with the unit's own environment ->
#  restart -> healthz within 20 s. finance_app.py from-pin: f002defb (S243_AUTOAPPLY, installed 13-Sep). Any RED after placing: both files restored, service
#  restarted if it was restarted, exit 1. Re-run when already installed: ALREADY INSTALLED.
#
#  ROOT=<dir> prefixes every absolute path (mock test only). MOCK_FA_PIN8 / PY / PY_SMOKE /
#  UNIT_FILE exist for the same mock and print loudly when used.
# =============================================================================
set -e
set -u
set -o pipefail
KIT="S243_SCREEN_FIXES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-}"
FIN="$ROOT/root/finance"
SVC="clinic-finance.service"
UNIT_FILE="${UNIT_FILE:-$ROOT/etc/systemd/system/clinic-finance.service}"
HZ_URL="http://127.0.0.1:8106/finance/healthz"

PA_FROM="8090ca2041574e25be39682dd5555ffe"      # purchase_app.py rev 13, S240_SANJEEVNI_123
PA_TO="$(awk 'NR==1{print $2}' "$KDIR/KIT_ID.txt")"
FA_FROM_PIN8_LIST="${MOCK_FA_PIN8:-f002defb}"   # S243_AUTOAPPLY pin (13-Sep); history 81db4854 (S240) -> 72bc8323 (S241) -> f002defb
FA_MARK="S243: a checker (the doctor) lands on his Review console"

# python for py_compile: the venv first (house rule), /usr/bin/python3 as the fallback
if [ -z "${PY:-}" ]; then
  if [ -x "$ROOT/root/wa/venv/bin/python3" ]; then PY="$ROOT/root/wa/venv/bin/python3"; else PY="/usr/bin/python3"; fi
fi
# python for the import smoke: the one the unit's ExecStart runs (gunicorn under /usr/bin/python3)
PY_SMOKE="${PY_SMOKE:-/usr/bin/python3}"
if [ -n "$ROOT" ]; then echo "-- MOCK: ROOT=$ROOT PY=$PY PY_SMOKE=$PY_SMOKE"; fi
if [ -n "${MOCK_FA_PIN8:-}" ]; then echo "-- MOCK: finance_app pin override ${MOCK_FA_PIN8}"; fi

PA_BAK=""; FA_BAK=""; RESTARTED=0; PLACED_PA=0; PLACED_FA=0
m5() { md5sum "$1" | awk '{print $1}'; }

rollback() {
  if [ "$PLACED_PA" -eq 1 ] && [ -n "$PA_BAK" ] && [ -f "$PA_BAK" ]; then
    \cp -f "$PA_BAK" "$FIN/purchase_app.py" && echo "   restored purchase_app.py from $PA_BAK ($(m5 "$FIN/purchase_app.py" | cut -c1-8))"
  fi
  if [ "$PLACED_FA" -eq 1 ] && [ -n "$FA_BAK" ] && [ -f "$FA_BAK" ]; then
    \cp -f "$FA_BAK" "$FIN/finance_app.py" && echo "   restored finance_app.py from $FA_BAK ($(m5 "$FIN/finance_app.py" | cut -c1-8))"
  fi
  if [ "$RESTARTED" -eq 1 ]; then
    systemctl restart "$SVC" || true; sleep 3
      if systemctl is-active --quiet "$SVC"; then echo "   service back up on the restored files"; else echo "   !! service did not come back after the restore -- check: systemctl status $SVC"; fi
  fi
}
red() { echo "!! RED -- $*"; rollback; echo "!! $KIT NOT installed"; exit 1; }
trap 'red "unexpected error at line $LINENO"' ERR

cd "$KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || red "SUMS.md5 gate failed -- the kit folder is not what was published"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || red "KIT_ID names a different kit"
[ "$(m5 purchase_app.py)" = "$PA_TO" ] || red "KIT_ID does not match purchase_app.py (F-88)"
echo "-- gates green: SUMS.md5 and KIT_ID.txt ($KIT -> purchase_app.py ${PA_TO:0:8})"

[ -f "$FIN/purchase_app.py" ] || red "$FIN/purchase_app.py is absent"
[ -f "$FIN/finance_app.py" ] || red "$FIN/finance_app.py is absent"
LIVE_PA="$(m5 "$FIN/purchase_app.py")"
LIVE_FA="$(m5 "$FIN/finance_app.py")"
PA_DONE=0; FA_DONE=0
if [ "$LIVE_PA" = "$PA_TO" ]; then PA_DONE=1; fi
if grep -qF "$FA_MARK" "$FIN/finance_app.py"; then FA_DONE=1; fi
if [ "$PA_DONE" -eq 1 ] && [ "$FA_DONE" -eq 1 ]; then
  echo "-- ALREADY INSTALLED: purchase_app.py ${LIVE_PA:0:8} = kit; finance_app.py ${LIVE_FA:0:8} carries the S243 mark. Nothing changed."
  exit 0
fi
if [ "$PA_DONE" -eq 0 ] && [ "$LIVE_PA" != "$PA_FROM" ]; then
  red "live purchase_app.py is ${LIVE_PA} -- not rev 13 ${PA_FROM:0:8} this kit was built on; NOTHING changed"
fi
if [ "$FA_DONE" -eq 0 ]; then
  OK=0; for p in $FA_FROM_PIN8_LIST; do case "$LIVE_FA" in "$p"*) OK=1;; esac; done
  [ "$OK" -eq 1 ] || red "live finance_app.py is ${LIVE_FA} -- not one of the pins this kit expects (${FA_FROM_PIN8_LIST}); NOTHING changed"
fi
echo "-- live pins: purchase_app.py ${LIVE_PA:0:8} | finance_app.py ${LIVE_FA:0:8} (as expected)"

# ---- the on-box patch for finance_app.py, to .new, BEFORE anything is placed
if [ "$FA_DONE" -eq 0 ]; then
  rm -f "$FIN/finance_app.py.new"
  FA_PATH="$FIN/finance_app.py" FA_FROM_PIN8= "$PY" -B "$KDIR/patch_finance_daily_s243.py" || red "patch_finance_daily_s243.py refused -- the anchor is not exactly once in the live file; NOTHING changed"
  [ -f "$FIN/finance_app.py.new" ] || red "the patcher wrote no .new"
  grep -qF "$FA_MARK" "$FIN/finance_app.py.new" || red "the .new does not carry the S243 mark"
  "$PY" -m py_compile "$FIN/finance_app.py.new" || red "py_compile finance_app.py.new"
fi
\cp -f "$KDIR/purchase_app.py" "$FIN/purchase_app.py.new"
[ "$(m5 "$FIN/purchase_app.py.new")" = "$PA_TO" ] || red "purchase_app.py.new did not land intact"
"$PY" -m py_compile "$FIN/purchase_app.py.new" || red "py_compile purchase_app.py.new"
echo "-- prepared: purchase_app.py.new ${PA_TO:0:8} | finance_app.py.new $([ "$FA_DONE" -eq 0 ] && m5 "$FIN/finance_app.py.new" | cut -c1-8 || echo '(already patched)') | py_compile clean with $PY"

# ---- backups, then place
if [ "$PA_DONE" -eq 0 ]; then
  PA_BAK="$FIN/purchase_app.py.bak_S243_${LIVE_PA:0:8}"
  \cp -f "$FIN/purchase_app.py" "$PA_BAK"
  mv -f "$FIN/purchase_app.py.new" "$FIN/purchase_app.py"; PLACED_PA=1
  [ "$(m5 "$FIN/purchase_app.py")" = "$PA_TO" ] || red "purchase_app.py did not land"
else
  rm -f "$FIN/purchase_app.py.new"
fi
if [ "$FA_DONE" -eq 0 ]; then
  FA_BAK="$FIN/finance_app.py.bak_S243_${LIVE_FA:0:8}"
  \cp -f "$FIN/finance_app.py" "$FA_BAK"
  FA_NEW_MD5="$(m5 "$FIN/finance_app.py.new")"
  mv -f "$FIN/finance_app.py.new" "$FIN/finance_app.py"; PLACED_FA=1
  [ "$(m5 "$FIN/finance_app.py")" = "$FA_NEW_MD5" ] || red "finance_app.py did not land"
fi
echo "-- placed: purchase_app.py ${LIVE_PA:0:8} -> $(m5 "$FIN/purchase_app.py" | cut -c1-8) | finance_app.py ${LIVE_FA:0:8} -> $(m5 "$FIN/finance_app.py" | cut -c1-8) | backups .bak_S243_<pin8>"

# ---- import smoke with the unit's own environment (drop-ins included; nothing is printed)
SMOKE_ENV="$(systemctl show -p Environment --value "$SVC" 2>/dev/null || true)"
if [ -z "$SMOKE_ENV" ] && [ -f "$UNIT_FILE" ]; then
  SMOKE_ENV="$( { cat "$UNIT_FILE"; cat "${UNIT_FILE}.d"/*.conf 2>/dev/null; } | sed -n 's/^Environment=//p' | tr '\n' ' ')"
fi
[ -n "$SMOKE_ENV" ] || red "could not read the service environment (systemctl show / $UNIT_FILE)"
SMOKE_RC=0
SMOKE_OUT="$(cd "$FIN" && env -i PATH="$PATH" HOME="${HOME:-/root}" $SMOKE_ENV "$PY_SMOKE" -c "import finance_app; print('import ok:', finance_app.app.name)" 2>&1)" || SMOKE_RC=$?
[ "$SMOKE_RC" -eq 0 ] || red "import smoke failed under the service environment:
$(echo "$SMOKE_OUT" | tail -8)"
echo "-- smoke: $(echo "$SMOKE_OUT" | tail -1) ($PY_SMOKE, env from the unit)"

# ---- restart and prove
RESTARTED=1
systemctl restart "$SVC" || red "systemctl restart $SVC failed"
HZ=""; i=0
while [ $i -lt 20 ]; do
  HZ="$(curl -s -o /dev/null -w '%{http_code}' "$HZ_URL" 2>/dev/null || true)"
  if [ "$HZ" = "200" ]; then break; fi
  sleep 1; i=$((i+1))
done
[ "$HZ" = "200" ] || red "healthz answered '$HZ' after 20 s"
systemctl is-active --quiet "$SVC" || red "$SVC is not active"
HUB="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:8106/finance/purchase/" 2>/dev/null || true)"
DLY="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:8106/finance/daily" 2>/dev/null || true)"
echo "-- healthz 200 after ${i}s | anonymous /finance/purchase/ $HUB | anonymous /finance/daily $DLY (302 = the login gate, as before; the signed-in checks are the owner's browser)"
RESTARTED=2
echo ""
echo "== $KIT INSTALLED"
echo "   purchase_app.py  predicted ${PA_TO}  actual $(m5 "$FIN/purchase_app.py")"
echo "   finance_app.py   was ${LIVE_FA}  actual $(m5 "$FIN/finance_app.py")  (patched on this box; record this pin)"
echo "   backups: $PA_BAK  $FA_BAK  (rollback line in README)"
exit 0
