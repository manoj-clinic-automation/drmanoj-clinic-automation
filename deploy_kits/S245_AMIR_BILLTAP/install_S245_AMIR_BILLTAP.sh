#!/bin/bash
# =============================================================================
#  install_S245_AMIR_BILLTAP.sh -- kit S245_AMIR_BILLTAP
#  Amir's step 4: processing -> processing done -> what is still to be made.
#
#  Run by:  bash /root/deploy/repo/deploy_kits/S245_AMIR_BILLTAP/install_S245_AMIR_BILLTAP.sh
#
#  A  /root/finance/amir_day.py   FULL-FILE replacement.  Refuses unless the live file is
#                                 EXACTLY the S244_AMIR_PROCESSING pin aad400fa...  The kit's file
#                                 is patch(live): the patcher's selftest proves that byte for
#                                 byte on THIS box before anything is placed.
#
#  Nothing else is touched.  amir_day has been mounted in finance_app.py since S241; no new
#  route, no new table, no schema change, no cron, no service file.
#
#  Gates: SUMS + KIT_ID -> live pin -> patcher selftest on the LIVE bytes -> the kit's own
#  two walks (S245's 53 checks and S244's 62-check regression suite) against the kit file
#  ON THIS BOX -> .bak_S245_<pin8> -> place -> py_compile
#  -> import smoke under the unit's own environment -> restart -> healthz within 20 s.
#  Any RED after placing: the file is restored, the service restarted, exit 1.
#  Re-run when already installed: ALREADY INSTALLED, nothing changed.
#
#  ROOT=<dir> prefixes every absolute path (mock test only).  MOCK_AD_PIN / PY / PY_SMOKE /
#  UNIT_FILE / SKIP_SVC exist for the same mock and print loudly when used.
# =============================================================================
set -e
set -u
set -o pipefail
KIT="S245_AMIR_BILLTAP"
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-}"
FIN="$ROOT/root/finance"
ADF="$FIN/amir_day.py"
SVC="clinic-finance.service"
UNIT_FILE="${UNIT_FILE:-$ROOT/etc/systemd/system/clinic-finance.service}"
HZ_URL="http://127.0.0.1:8106/finance/healthz"

AD_FROM_PIN="${MOCK_AD_PIN:-aad400fa9c4b7804229c9f175c86533b}"
AD_MARK="S245_AMIR_BILLTAP"

if [ -z "${PY:-}" ]; then
  if [ -x "$ROOT/root/wa/venv/bin/python3" ]; then PY="$ROOT/root/wa/venv/bin/python3"; else PY="/usr/bin/python3"; fi
fi
PY_SMOKE="${PY_SMOKE:-/usr/bin/python3}"
SKIP_SVC="${SKIP_SVC:-0}"
if [ -n "$ROOT" ]; then echo "-- MOCK: ROOT=$ROOT PY=$PY PY_SMOKE=$PY_SMOKE SKIP_SVC=$SKIP_SVC"; fi
if [ -n "${MOCK_AD_PIN:-}" ]; then echo "-- MOCK: amir_day pin override ${MOCK_AD_PIN}"; fi

AD_BAK=""; RESTARTED=0; PLACED_AD=0
m5() { md5sum "$1" | awk '{print $1}'; }

rollback() {
  if [ "$PLACED_AD" -eq 1 ] && [ -n "$AD_BAK" ] && [ -f "$AD_BAK" ]; then
    \cp -f "$AD_BAK" "$ADF" && echo "   restored amir_day.py from $AD_BAK ($(m5 "$ADF" | cut -c1-8))"
  fi
  rm -rf "$FIN/__pycache__/amir_day".*.pyc 2>/dev/null || true
  if [ "$RESTARTED" -eq 1 ] && [ "$SKIP_SVC" != "1" ]; then
    systemctl restart "$SVC" || true; sleep 3
    if systemctl is-active --quiet "$SVC"; then echo "   service back up on the restored file"; else echo "   !! service did not come back after the restore -- check: systemctl status $SVC"; fi
  fi
}
red() { echo "!! RED -- $*"; rollback; echo "!! $KIT NOT installed"; exit 1; }
trap 'red "unexpected error at line $LINENO"' ERR

cd "$KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || red "SUMS.md5 gate failed -- the kit folder is not what was published"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || red "KIT_ID names a different kit"
echo "-- gates green: SUMS.md5 and KIT_ID.txt ($KIT)"

[ -f "$ADF" ] || red "$ADF is absent"
LIVE_AD="$(m5 "$ADF")"
KIT_AD="$(m5 "$KDIR/amir_day.py")"
if [ "$LIVE_AD" = "$KIT_AD" ]; then
  echo "-- ALREADY INSTALLED: amir_day.py ${LIVE_AD:0:8} is the kit's file. Nothing changed."
  exit 0
fi
if grep -qF "$AD_MARK" "$ADF"; then
  red "live amir_day.py ${LIVE_AD} already carries the $AD_MARK mark but is NOT this kit's file (${KIT_AD:0:8}) -- a different build is live; NOTHING changed"
fi
[ "$LIVE_AD" = "$AD_FROM_PIN" ] || red "live amir_day.py is ${LIVE_AD} -- not the pin ${AD_FROM_PIN:0:8} this kit was built on (full-file replacement needs the exact pin); NOTHING changed"
echo "-- live pin: amir_day.py ${LIVE_AD:0:8} (as expected)"

# ---- the kit's own proofs, on THIS box, before anything is placed
"$PY" -m py_compile "$KDIR/amir_day.py" || red "py_compile amir_day.py (kit file)"
rm -rf "$KDIR/__pycache__"
"$PY" -B "$KDIR/patch_amir_day_billtap_s245.py" --selftest "$ADF" "$KDIR/amir_day.py" >/dev/null 2>&1 || \
  red "the patcher's selftest against the LIVE bytes failed -- patch(live) is not the kit's file; NOTHING changed"
echo "-- proof: patch(live amir_day.py ${LIVE_AD:0:8}) == kit amir_day.py ${KIT_AD:0:8}, byte for byte"

for W in walk_amir_billtap_s245.py walk_amir_processing_s244.py; do
  WALK_RC=0
  WALK_OUT="$("$PY" -B "$KDIR/$W" "$KDIR/amir_day.py" 2>&1)" || WALK_RC=$?
  [ "$WALK_RC" -eq 0 ] || red "$W failed ON THIS BOX; NOTHING changed:
$(echo "$WALK_OUT" | tail -12)"
  echo "-- $W on this box: $(echo "$WALK_OUT" | grep -E '^== [0-9]+ checks' | tail -1)"
done

# ---- backup, then place
AD_BAK="$ADF.bak_S245_${LIVE_AD:0:8}"
\cp -f "$ADF" "$AD_BAK"
\cp -f "$KDIR/amir_day.py" "$ADF"; PLACED_AD=1
[ "$(m5 "$ADF")" = "$KIT_AD" ] || red "amir_day.py did not land"
rm -rf "$FIN/__pycache__/amir_day".*.pyc 2>/dev/null || true
echo "-- placed: amir_day.py ${LIVE_AD:0:8} -> $(m5 "$ADF" | cut -c1-8) | backup $AD_BAK"

# ---- py_compile in place, then the import smoke with the unit's own environment
"$PY" -m py_compile "$ADF" || red "py_compile of the placed amir_day.py"
if [ "$SKIP_SVC" = "1" ]; then
  echo "-- MOCK: service smoke, restart and healthz skipped"
  echo ""
  echo "== $KIT INSTALLED (mock)"
  echo "   amir_day.py  was ${LIVE_AD}  now $(m5 "$ADF")"
  exit 0
fi
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
for need in ('/finance/amir', '/finance/amir/step/<int:n>', '/finance/amir/day',
             '/finance/amir/day/api/visit-summary'):
    assert need in rules, 'route gone: ' + need
assert amir_day.GATE_STEPS == (2, 4, 5, 6), 'GATE_STEPS moved'
assert 1 <= amir_day.EXPORT_GRACE_MIN <= 60, 'EXPORT_GRACE_MIN out of range'
assert [c for c, _l in amir_day.REASONS] == ['ok', 'short', 'nodeal', 'discount', 'other'], 'REASONS moved'
import re as _re
assert _re.match(r'^\\d{4}-\\d{2}-\\d{2}$', amir_day.BILLS_FROM), 'BILLS_FROM is not a date'
print('import ok: amir_day mounted, routes registered, grace %d min, bills from %s' % (amir_day.EXPORT_GRACE_MIN, amir_day.BILLS_FROM))" 2>&1)" || SMOKE_RC=$?
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
AMIR="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:8106/finance/amir/step/4" 2>/dev/null || true)"
AHZ="$(curl -s "http://127.0.0.1:8106/finance/amir/api/healthz" 2>/dev/null | head -c 120 || true)"
RESTARTED=2
echo "-- healthz 200 after ${i}s | anonymous /finance/amir/step/4 $AMIR (302 = the login gate, as designed)"
echo "-- amir healthz: $AHZ"
echo ""
echo "== $KIT INSTALLED"
echo "   amir_day.py  was ${LIVE_AD}  now $(m5 "$ADF")  (record this pin)"
echo "   backup: $AD_BAK    rollback: \\cp -f $AD_BAK $ADF && systemctl restart $SVC"
echo "   read next: Amir's bill list at /finance/amir/step/5 -- one tap per bill, reasons only when he says not-ok"
exit 0
