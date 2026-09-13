#!/bin/bash
# =============================================================================
#  install_S243_AUTOAPPLY.sh -- kit S243_AUTOAPPLY -- a pushed sale report applies itself
#
#  Run by:  bash /root/deploy/repo/deploy_kits/S243_AUTOAPPLY/install_S243_AUTOAPPLY.sh
#
#  A  finance_app.py               patched ON THIS BOX by patch_marg_autoapply_s243.py:
#                                  four anchors, each exactly once, else REFUSED and nothing
#                                  changes.  Newest export wins; older pending superseded;
#                                  "older than applied" put aside; audit by 'auto'.
#  B  finance_ui/finance_approvals.html
#                                  patched ON THIS BOX by patch_hub_autoapply_s243.py:
#                                  an auto-applied row reads "applied automatically <time>".
#
#  OFF switch, any time, no restart:   touch /root/finance/AUTOAPPLY_OFF
#  ON again:                           rm /root/finance/AUTOAPPLY_OFF
#
#  Gates: SUMS + KIT_ID -> live pins are the ones this kit was built on -> .bak_S243_<pin8>
#  of both -> patch to .new -> py_compile -> import smoke under the unit's own environment ->
#  restart -> healthz within 20 s.  Any RED after placing: both files restored, service
#  restarted if it was restarted, exit 1.  Re-run when already installed: ALREADY INSTALLED.
#
#  ROOT=<dir> prefixes every absolute path (mock test only).  MOCK_FA_PIN8 / MOCK_HUB_PIN /
#  PY / PY_SMOKE / UNIT_FILE exist for the same mock and print loudly when used.
# =============================================================================
set -e
set -u
set -o pipefail
KIT="S243_AUTOAPPLY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-}"
FIN="$ROOT/root/finance"
HUBF="$FIN/finance_ui/finance_approvals.html"
SVC="clinic-finance.service"
UNIT_FILE="${UNIT_FILE:-$ROOT/etc/systemd/system/clinic-finance.service}"
HZ_URL="http://127.0.0.1:8106/finance/healthz"

FA_FROM_PIN8_LIST="${MOCK_FA_PIN8:-81db4854 72bc8323}"   # S240 close pin; S241 mount pin (README)
FA_MARK="S243 AUTO-APPLY -- newest export wins"
FA_SIBLING_MARK="S243: a checker (the doctor) lands on his Review console"   # kit S243_SCREEN_FIXES
HUB_FROM_PIN="${MOCK_HUB_PIN:-e1652297a1ed5b81a0fcfedd2662f047}"          # S220 hub pin, unchanged since
HUB_MARK="S243 auto-apply"

if [ -z "${PY:-}" ]; then
  if [ -x "$ROOT/root/wa/venv/bin/python3" ]; then PY="$ROOT/root/wa/venv/bin/python3"; else PY="/usr/bin/python3"; fi
fi
PY_SMOKE="${PY_SMOKE:-/usr/bin/python3}"
if [ -n "$ROOT" ]; then echo "-- MOCK: ROOT=$ROOT PY=$PY PY_SMOKE=$PY_SMOKE"; fi
if [ -n "${MOCK_FA_PIN8:-}" ]; then echo "-- MOCK: finance_app pin override ${MOCK_FA_PIN8}"; fi
if [ -n "${MOCK_HUB_PIN:-}" ]; then echo "-- MOCK: hub pin override ${MOCK_HUB_PIN}"; fi

FA_BAK=""; HUB_BAK=""; RESTARTED=0; PLACED_FA=0; PLACED_HUB=0
m5() { md5sum "$1" | awk '{print $1}'; }

rollback() {
  if [ "$PLACED_FA" -eq 1 ] && [ -n "$FA_BAK" ] && [ -f "$FA_BAK" ]; then
    \cp -f "$FA_BAK" "$FIN/finance_app.py" && echo "   restored finance_app.py from $FA_BAK ($(m5 "$FIN/finance_app.py" | cut -c1-8))"
  fi
  if [ "$PLACED_HUB" -eq 1 ] && [ -n "$HUB_BAK" ] && [ -f "$HUB_BAK" ]; then
    \cp -f "$HUB_BAK" "$HUBF" && echo "   restored finance_approvals.html from $HUB_BAK ($(m5 "$HUBF" | cut -c1-8))"
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
echo "-- gates green: SUMS.md5 and KIT_ID.txt ($KIT)"

[ -f "$FIN/finance_app.py" ] || red "$FIN/finance_app.py is absent"
[ -f "$HUBF" ] || red "$HUBF is absent"
LIVE_FA="$(m5 "$FIN/finance_app.py")"
LIVE_HUB="$(m5 "$HUBF")"
FA_DONE=0; HUB_DONE=0
if grep -qF "$FA_MARK" "$FIN/finance_app.py"; then FA_DONE=1; fi
if grep -qF "$HUB_MARK" "$HUBF"; then HUB_DONE=1; fi
if [ "$FA_DONE" -eq 1 ] && [ "$HUB_DONE" -eq 1 ]; then
  echo "-- ALREADY INSTALLED: finance_app.py ${LIVE_FA:0:8} and finance_approvals.html ${LIVE_HUB:0:8} both carry the S243 marks. Nothing changed."
  exit 0
fi
if [ "$FA_DONE" -eq 0 ]; then
  OK=0; for p in $FA_FROM_PIN8_LIST; do case "$LIVE_FA" in "$p"*) OK=1;; esac; done
  if [ "$OK" -eq 0 ] && grep -qF "$FA_SIBLING_MARK" "$FIN/finance_app.py"; then
    # the sibling kit S243_SCREEN_FIXES patched this file first; its backup proves the lineage
    for p in $FA_FROM_PIN8_LIST; do [ -f "$FIN/finance_app.py.bak_S243_$p" ] && OK=2; done
    [ "$OK" -eq 2 ] && echo "-- live finance_app.py ${LIVE_FA:0:8} carries the S243_SCREEN_FIXES mark and its .bak_S243_<pin8> is one of (${FA_FROM_PIN8_LIST}): lineage accepted"
  fi
  [ "$OK" -ne 0 ] || red "live finance_app.py is ${LIVE_FA} -- not one of the pins this kit expects (${FA_FROM_PIN8_LIST}); NOTHING changed"
fi
if [ "$HUB_DONE" -eq 0 ]; then
  [ "$LIVE_HUB" = "$HUB_FROM_PIN" ] || red "live finance_approvals.html is ${LIVE_HUB} -- not the S220 pin ${HUB_FROM_PIN:0:8} this kit was built on; NOTHING changed"
fi
echo "-- live pins: finance_app.py ${LIVE_FA:0:8} | finance_approvals.html ${LIVE_HUB:0:8} (as expected)"

# ---- both patches to .new, BEFORE anything is placed; the anchor count is the real guard
if [ "$FA_DONE" -eq 0 ]; then
  rm -f "$FIN/finance_app.py.new"
  FA_PATH="$FIN/finance_app.py" "$PY" -B "$KDIR/patch_marg_autoapply_s243.py" || red "patch_marg_autoapply_s243.py refused -- an anchor is not exactly once in the live file; NOTHING changed"
  [ -f "$FIN/finance_app.py.new" ] || red "the patcher wrote no finance_app.py.new"
  grep -qF "$FA_MARK" "$FIN/finance_app.py.new" || red "the .new does not carry the S243 mark"
  "$PY" -m py_compile "$FIN/finance_app.py.new" || red "py_compile finance_app.py.new"
fi
if [ "$HUB_DONE" -eq 0 ]; then
  rm -f "$HUBF.new"
  HUB_PATH="$HUBF" "$PY" -B "$KDIR/patch_hub_autoapply_s243.py" || red "patch_hub_autoapply_s243.py refused -- an anchor is not exactly once in the live page; NOTHING changed"
  [ -f "$HUBF.new" ] || red "the hub patcher wrote no .new"
  grep -qF "$HUB_MARK" "$HUBF.new" || red "the hub .new does not carry the S243 mark"
fi
echo "-- prepared: finance_app.py.new $([ "$FA_DONE" -eq 0 ] && m5 "$FIN/finance_app.py.new" | cut -c1-8 || echo '(already patched)') | finance_approvals.html.new $([ "$HUB_DONE" -eq 0 ] && m5 "$HUBF.new" | cut -c1-8 || echo '(already patched)') | py_compile clean with $PY"

# ---- backups, then place
if [ "$FA_DONE" -eq 0 ]; then
  FA_BAK="$FIN/finance_app.py.bak_S243_${LIVE_FA:0:8}"
  \cp -f "$FIN/finance_app.py" "$FA_BAK"
  FA_NEW_MD5="$(m5 "$FIN/finance_app.py.new")"
  mv -f "$FIN/finance_app.py.new" "$FIN/finance_app.py"; PLACED_FA=1
  [ "$(m5 "$FIN/finance_app.py")" = "$FA_NEW_MD5" ] || red "finance_app.py did not land"
fi
if [ "$HUB_DONE" -eq 0 ]; then
  HUB_BAK="$HUBF.bak_S243_${LIVE_HUB:0:8}"
  \cp -f "$HUBF" "$HUB_BAK"
  HUB_NEW_MD5="$(m5 "$HUBF.new")"
  mv -f "$HUBF.new" "$HUBF"; PLACED_HUB=1
  [ "$(m5 "$HUBF")" = "$HUB_NEW_MD5" ] || red "finance_approvals.html did not land"
fi
echo "-- placed: finance_app.py ${LIVE_FA:0:8} -> $(m5 "$FIN/finance_app.py" | cut -c1-8) | finance_approvals.html ${LIVE_HUB:0:8} -> $(m5 "$HUBF" | cut -c1-8) | backups .bak_S243_<pin8>"

# ---- import smoke with the unit's own environment (drop-ins included; nothing is printed)
SMOKE_ENV="$(systemctl show -p Environment --value "$SVC" 2>/dev/null || true)"
if [ -z "$SMOKE_ENV" ] && [ -f "$UNIT_FILE" ]; then
  SMOKE_ENV="$( { cat "$UNIT_FILE"; cat "${UNIT_FILE}.d"/*.conf 2>/dev/null; } | sed -n 's/^Environment=//p' | tr '\n' ' ')"
fi
[ -n "$SMOKE_ENV" ] || red "could not read the service environment (systemctl show / $UNIT_FILE)"
SMOKE_RC=0
SMOKE_OUT="$(cd "$FIN" && env -i PATH="$PATH" HOME="${HOME:-/root}" $SMOKE_ENV "$PY_SMOKE" -c "import finance_app; assert callable(finance_app._marg_autoapply_s243) and callable(finance_app._marg_apply_core_s243); print('import ok:', finance_app.app.name)" 2>&1)" || SMOKE_RC=$?
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
LST="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:8106/finance/api/marg-push/list" 2>/dev/null || true)"
PSH="$(curl -s -o /dev/null -w '%{http_code}' -X POST "http://127.0.0.1:8106/finance/api/marg-push" 2>/dev/null || true)"
echo "-- healthz 200 after ${i}s | anonymous marg-push/list $LST (302/401 = the login gate, as before) | tokenless POST marg-push $PSH (401 = the sender gate, as before)"
RESTARTED=2
echo ""
echo "== $KIT INSTALLED"
echo "   finance_app.py             was ${LIVE_FA}  actual $(m5 "$FIN/finance_app.py")  (patched on this box; record this pin)"
echo "   finance_approvals.html     was ${LIVE_HUB}  actual $(m5 "$HUBF")"
echo "   backups: $FA_BAK  $HUB_BAK  (rollback line in README)"
echo "   OFF switch (no restart needed):  touch $FIN/AUTOAPPLY_OFF     ON again:  rm $FIN/AUTOAPPLY_OFF"
if [ -f "$FIN/AUTOAPPLY_OFF" ]; then echo "   !! NOTE: $FIN/AUTOAPPLY_OFF EXISTS -- the automatic apply is OFF until it is removed"; fi
exit 0
