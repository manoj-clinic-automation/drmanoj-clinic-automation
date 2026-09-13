#!/bin/bash
# =============================================================================
#  install_S243_AMIR_VISIT.sh -- kit S243_AMIR_VISIT -- the salt-list prompt + "Amir's visit -- what was done"
#
#  Run by:  bash /root/deploy/repo/deploy_kits/S243_AMIR_VISIT/install_S243_AMIR_VISIT.sh
#
#  A  /root/finance/amir_day.py            FULL-FILE replacement.  Refuses unless the live file is
#                                          EXACTLY the S241_AMIR_SALTS pin ae2c8939... (the 13-Sep
#                                          capture).  The kit's file is patch(live) -- the patcher's
#                                          selftest proves that byte-for-byte on this box before
#                                          anything is placed.  Adds: the SALT WISE ITEM LIST prompt
#                                          (red to Amir until the list arrives), the owner's visit
#                                          summary (/finance/amir/day + /finance/amir/day/api/visit-summary),
#                                          and the export-stamp fix the walk found (step 4 could never verify).
#  B  finance_ui/finance_approvals.html    patched ON THIS BOX by patch_hub_amir_visit_s243.py: a collapsed
#                                          "Amir's visit -- what was done" block inside the Marg card.
#                                          Three anchors, each exactly once, else REFUSED.
#
#  Pins this kit was built on (the 13-Sep capture):
#      amir_day.py                ae2c89398e3c1fa63f9dadcff9e69d84  (exact; full-file replacement)
#      finance_approvals.html     cc349dd00d0a2f861ec54242c9551557  -- OR any page carrying the
#                                 S243_DARPAN_KAL mark (that kit installs first); the patcher's
#                                 count==1 anchors are the real guard; the ACTUAL from-pin is recorded
#      finance_app.py             NOT touched (amir_day is mounted since S241; the new route rides on it)
#
#  Gates: SUMS + KIT_ID -> live pins -> patcher selftests on the LIVE bytes -> hub patch to .new
#  -> .bak_S243_<pin8> of both files -> place -> py_compile -> import smoke under the unit's own
#  environment (the amir_day blueprint and the new route must be registered) -> restart -> healthz
#  within 20 s.  Any RED after placing: both files restored, service restarted if it was, exit 1.
#  Re-run when already installed: ALREADY INSTALLED.
#
#  ROOT=<dir> prefixes every absolute path (mock test only).  MOCK_AD_PIN / MOCK_HUB_PIN / PY /
#  PY_SMOKE / UNIT_FILE exist for the same mock and print loudly when used.
# =============================================================================
set -e
set -u
set -o pipefail
KIT="S243_AMIR_VISIT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-}"
FIN="$ROOT/root/finance"
ADF="$FIN/amir_day.py"
HUBF="$FIN/finance_ui/finance_approvals.html"
SVC="clinic-finance.service"
UNIT_FILE="${UNIT_FILE:-$ROOT/etc/systemd/system/clinic-finance.service}"
HZ_URL="http://127.0.0.1:8106/finance/healthz"

AD_FROM_PIN="${MOCK_AD_PIN:-ae2c89398e3c1fa63f9dadcff9e69d84}"
HUB_FROM_PIN="${MOCK_HUB_PIN:-cc349dd00d0a2f861ec54242c9551557}"
HUB_SIBLING_MARK="S243 darpan kal"          # kit S243_DARPAN_KAL installs first and moves the hub pin
AD_MARK="S243_AMIR_VISIT"
HUB_MARK="S243 amir visit"

if [ -z "${PY:-}" ]; then
  if [ -x "$ROOT/root/wa/venv/bin/python3" ]; then PY="$ROOT/root/wa/venv/bin/python3"; else PY="/usr/bin/python3"; fi
fi
PY_SMOKE="${PY_SMOKE:-/usr/bin/python3}"
if [ -n "$ROOT" ]; then echo "-- MOCK: ROOT=$ROOT PY=$PY PY_SMOKE=$PY_SMOKE"; fi
if [ -n "${MOCK_AD_PIN:-}" ]; then echo "-- MOCK: amir_day pin override ${MOCK_AD_PIN}"; fi
if [ -n "${MOCK_HUB_PIN:-}" ]; then echo "-- MOCK: hub pin override ${MOCK_HUB_PIN}"; fi

AD_BAK=""; HUB_BAK=""; RESTARTED=0; PLACED_AD=0; PLACED_HUB=0
m5() { md5sum "$1" | awk '{print $1}'; }

rollback() {
  if [ "$PLACED_AD" -eq 1 ] && [ -n "$AD_BAK" ] && [ -f "$AD_BAK" ]; then
    \cp -f "$AD_BAK" "$ADF" && echo "   restored amir_day.py from $AD_BAK ($(m5 "$ADF" | cut -c1-8))"
  fi
  if [ "$PLACED_HUB" -eq 1 ] && [ -n "$HUB_BAK" ] && [ -f "$HUB_BAK" ]; then
    \cp -f "$HUB_BAK" "$HUBF" && echo "   restored finance_approvals.html from $HUB_BAK ($(m5 "$HUBF" | cut -c1-8))"
  fi
  rm -rf "$FIN/__pycache__/amir_day".*.pyc 2>/dev/null || true
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

[ -f "$ADF" ] || red "$ADF is absent"
[ -f "$HUBF" ] || red "$HUBF is absent"
LIVE_AD="$(m5 "$ADF")"
LIVE_HUB="$(m5 "$HUBF")"
KIT_AD="$(m5 "$KDIR/amir_day.py")"
AD_DONE=0; HUB_DONE=0
if [ "$LIVE_AD" = "$KIT_AD" ]; then AD_DONE=1; fi
if grep -qF "$HUB_MARK" "$HUBF"; then HUB_DONE=1; fi
if [ "$AD_DONE" -eq 1 ] && [ "$HUB_DONE" -eq 1 ]; then
  echo "-- ALREADY INSTALLED: amir_day.py ${LIVE_AD:0:8} is the kit's file and finance_approvals.html ${LIVE_HUB:0:8} carries the S243 mark. Nothing changed."
  exit 0
fi
if [ "$AD_DONE" -eq 0 ]; then
  if grep -qF "$AD_MARK" "$ADF"; then
    red "live amir_day.py ${LIVE_AD} already carries the $AD_MARK mark but is NOT this kit's file (${KIT_AD:0:8}) -- a different build is live; NOTHING changed"
  fi
  [ "$LIVE_AD" = "$AD_FROM_PIN" ] || red "live amir_day.py is ${LIVE_AD} -- not the pin ${AD_FROM_PIN:0:8} this kit was built on (full-file replacement needs the exact pin); NOTHING changed"
fi
if [ "$HUB_DONE" -eq 0 ]; then
  if [ "$LIVE_HUB" = "$HUB_FROM_PIN" ]; then
    echo "-- finance_approvals.html is the build pin ${HUB_FROM_PIN:0:8}"
  elif grep -qF "$HUB_SIBLING_MARK" "$HUBF"; then
    echo "-- finance_approvals.html ${LIVE_HUB:0:8} carries the S243_DARPAN_KAL mark (that kit installed first): lineage accepted; the patcher's anchor count is the guard"
  else
    red "live finance_approvals.html is ${LIVE_HUB} -- neither the pin ${HUB_FROM_PIN:0:8} this kit was built on nor a S243_DARPAN_KAL-patched page; NOTHING changed"
  fi
fi
echo "-- live pins: amir_day.py ${LIVE_AD:0:8} | finance_approvals.html ${LIVE_HUB:0:8} (as expected)"

# ---- the kit's own proofs on the LIVE bytes, before anything is placed
"$PY" -m py_compile "$KDIR/amir_day.py" || red "py_compile amir_day.py (kit file)"
rm -rf "$KDIR/__pycache__"
if [ "$AD_DONE" -eq 0 ]; then
  "$PY" -B "$KDIR/patch_amir_day_salt_prompt_s243.py" --selftest "$ADF" "$KDIR/amir_day.py" >/dev/null 2>&1 || \
    red "the amir_day patcher's selftest against the LIVE bytes failed -- patch(live) is not the kit's file; NOTHING changed"
  echo "-- proof: patch(live amir_day.py ${LIVE_AD:0:8}) == kit amir_day.py ${KIT_AD:0:8}, byte for byte"
fi
if [ "$HUB_DONE" -eq 0 ]; then
  "$PY" -B "$KDIR/patch_hub_amir_visit_s243.py" --selftest "$HUBF" >/dev/null 2>&1 || \
    red "the hub patcher's selftest against the LIVE page failed; NOTHING changed"
  rm -f "$HUBF.new"
  HUB_PATH="$HUBF" "$PY" -B "$KDIR/patch_hub_amir_visit_s243.py" || red "the hub patcher refused -- an anchor is not exactly once in the live page; NOTHING changed"
  [ -f "$HUBF.new" ] || red "the hub patcher wrote no .new"
  grep -qF "$HUB_MARK" "$HUBF.new" || red "the hub .new does not carry the S243 mark"
  echo "-- prepared: finance_approvals.html.new $(m5 "$HUBF.new" | cut -c1-8)"
fi

# ---- backups, then place
if [ "$AD_DONE" -eq 0 ]; then
  AD_BAK="$ADF.bak_S243_${LIVE_AD:0:8}"
  \cp -f "$ADF" "$AD_BAK"
  \cp -f "$KDIR/amir_day.py" "$ADF"; PLACED_AD=1
  [ "$(m5 "$ADF")" = "$KIT_AD" ] || red "amir_day.py did not land"
  rm -rf "$FIN/__pycache__/amir_day".*.pyc 2>/dev/null || true
fi
if [ "$HUB_DONE" -eq 0 ]; then
  HUB_BAK="$HUBF.bak_S243_${LIVE_HUB:0:8}"
  \cp -f "$HUBF" "$HUB_BAK"
  HUB_NEW_MD5="$(m5 "$HUBF.new")"
  mv -f "$HUBF.new" "$HUBF"; PLACED_HUB=1
  [ "$(m5 "$HUBF")" = "$HUB_NEW_MD5" ] || red "finance_approvals.html did not land"
fi
echo "-- placed: amir_day.py ${LIVE_AD:0:8} -> $(m5 "$ADF" | cut -c1-8) | finance_approvals.html ${LIVE_HUB:0:8} -> $(m5 "$HUBF" | cut -c1-8) | backups .bak_S243_<pin8>"

# ---- py_compile in place, then the import smoke with the unit's own environment
"$PY" -m py_compile "$ADF" || red "py_compile of the placed amir_day.py"
SMOKE_ENV="$(systemctl show -p Environment --value "$SVC" 2>/dev/null || true)"
if [ -z "$SMOKE_ENV" ] && [ -f "$UNIT_FILE" ]; then
  SMOKE_ENV="$( { cat "$UNIT_FILE"; cat "${UNIT_FILE}.d"/*.conf 2>/dev/null || true; } | sed -n 's/^Environment=//p' | tr '\n' ' ')"
fi
[ -n "$SMOKE_ENV" ] || red "could not read the service environment (systemctl show / $UNIT_FILE)"
SMOKE_RC=0
SMOKE_OUT="$(cd "$FIN" && env -i PATH="$PATH" HOME="${HOME:-/root}" $SMOKE_ENV "$PY_SMOKE" -B -c "
import finance_app, amir_day
assert 'amir_day' in finance_app.app.blueprints, 'amir_day blueprint NOT registered'
rules = {r.rule for r in finance_app.app.url_map.iter_rules()}
assert '/finance/amir/day/api/visit-summary' in rules, 'visit-summary route NOT registered'
assert '/finance/amir/step/<int:n>' in rules and '/finance/amir/day' in rules, 'the S241 routes are gone'
assert amir_day.GATE_STEPS == (2, 4, 5, 6), 'GATE_STEPS moved'
print('import ok: amir_day mounted, visit-summary route registered')" 2>&1)" || SMOKE_RC=$?
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
DAY="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:8106/finance/amir/day" 2>/dev/null || true)"
VS="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:8106/finance/amir/day/api/visit-summary" 2>/dev/null || true)"
echo "-- healthz 200 after ${i}s | anonymous /finance/amir/day $DAY and /finance/amir/day/api/visit-summary $VS (302 = the login gate, as designed)"
RESTARTED=2
echo ""
echo "== $KIT INSTALLED"
echo "   amir_day.py                was ${LIVE_AD}  now $(m5 "$ADF")  (the kit's file; record this pin)"
echo "   finance_approvals.html     was ${LIVE_HUB}  now $(m5 "$HUBF")  (patched on this box)"
echo "   backups: ${AD_BAK:-"(amir_day.py was already the kit's)"}  ${HUB_BAK:-"(hub already carried the mark)"}  (rollback line in README)"
echo "   read next: https://<portal>/finance/amir/day  and the hub's Marg card, block 'Amir's visit -- what was done'"
exit 0
