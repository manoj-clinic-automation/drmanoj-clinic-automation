#!/bin/bash
# =============================================================================
#  install_S243_DARPAN_KAL.sh -- kit S243_DARPAN_KAL -- Darpan's morning page ("Kal ka hisaab")
#
#  Run by:  bash /root/deploy/repo/deploy_kits/S243_DARPAN_KAL/install_S243_DARPAN_KAL.sh
#
#  A  NEW files into /root/finance:  darpan_kal.py  darpan_kal_schema.sql  darpan_kal.html
#  B  finance_app.py                 patched ON THIS BOX by patch_finance_app_darpan_kal_s243.py:
#                                    one anchor (the S241_AMIR_DAY end line), exactly once, else
#                                    REFUSED and nothing changes.  Guarded mount (S209 lesson).
#  C  finance_ui/finance_approvals.html
#                                    patched ON THIS BOX by the same patcher: the card
#                                    "Darpan -- needs you" + its tab + loader.  Four anchors.
#
#  Pins this kit was built on (the 13-Sep capture):
#      finance_app.py            f002defb9f4a5d35028c051462225def  -- OR any file carrying the
#                                S243_SCREEN_FIXES mark (that kit installs first); the patcher's
#                                count==1 anchor is the real guard; the ACTUAL from-pin is recorded
#      finance_approvals.html    cc349dd00d0a2f861ec54242c9551557
#
#  Gates: SUMS + KIT_ID -> live pins -> .bak_S243_<pin8> of both patched files -> patch to .new
#  -> py_compile -> import smoke under the unit's own environment (the blueprint must be
#  registered) -> restart -> healthz within 20 s.  Any RED after placing: both files restored,
#  the three new files removed if this run created them, service restarted if it was restarted,
#  exit 1.  Re-run when already installed: ALREADY INSTALLED.
#
#  ROOT=<dir> prefixes every absolute path (mock test only).  MOCK_FA_PIN / MOCK_HUB_PIN /
#  PY / PY_SMOKE / UNIT_FILE exist for the same mock and print loudly when used.
#
#  AFTER INSTALL (one owner step, GUI): Darpan's portal tile -> https://<portal>/finance/darpan/kal
#  (the recipients manoj/bhawna are seeded by this installer; nothing else is left to do).
# =============================================================================
set -e
set -u
set -o pipefail
KIT="S243_DARPAN_KAL"
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-}"
FIN="$ROOT/root/finance"
FAF="$FIN/finance_app.py"
HUBF="$FIN/finance_ui/finance_approvals.html"
SVC="clinic-finance.service"
UNIT_FILE="${UNIT_FILE:-$ROOT/etc/systemd/system/clinic-finance.service}"
HZ_URL="http://127.0.0.1:8106/finance/healthz"

FA_FROM_PIN="${MOCK_FA_PIN:-f002defb9f4a5d35028c051462225def}"
FA_SIBLING_MARK="S243: a checker (the doctor) lands on his Review console"   # kit S243_SCREEN_FIXES installs first and moves the pin
HUB_FROM_PIN="${MOCK_HUB_PIN:-cc349dd00d0a2f861ec54242c9551557}"
FA_MARK="S243_DARPAN_KAL begin"
HUB_MARK="S243 darpan kal"
NEWFILES="darpan_kal.py darpan_kal_schema.sql darpan_kal.html"

if [ -z "${PY:-}" ]; then
  if [ -x "$ROOT/root/wa/venv/bin/python3" ]; then PY="$ROOT/root/wa/venv/bin/python3"; else PY="/usr/bin/python3"; fi
fi
PY_SMOKE="${PY_SMOKE:-/usr/bin/python3}"
if [ -n "$ROOT" ]; then echo "-- MOCK: ROOT=$ROOT PY=$PY PY_SMOKE=$PY_SMOKE"; fi
if [ -n "${MOCK_FA_PIN:-}" ]; then echo "-- MOCK: finance_app pin override ${MOCK_FA_PIN}"; fi
if [ -n "${MOCK_HUB_PIN:-}" ]; then echo "-- MOCK: hub pin override ${MOCK_HUB_PIN}"; fi

FA_BAK=""; HUB_BAK=""; RESTARTED=0; PLACED_FA=0; PLACED_HUB=0; CREATED=""
m5() { md5sum "$1" | awk '{print $1}'; }

rollback() {
  if [ "$PLACED_FA" -eq 1 ] && [ -n "$FA_BAK" ] && [ -f "$FA_BAK" ]; then
    \cp -f "$FA_BAK" "$FAF" && echo "   restored finance_app.py from $FA_BAK ($(m5 "$FAF" | cut -c1-8))"
  fi
  if [ "$PLACED_HUB" -eq 1 ] && [ -n "$HUB_BAK" ] && [ -f "$HUB_BAK" ]; then
    \cp -f "$HUB_BAK" "$HUBF" && echo "   restored finance_approvals.html from $HUB_BAK ($(m5 "$HUBF" | cut -c1-8))"
  fi
  for f in $CREATED; do rm -f "$FIN/$f" && echo "   removed $FIN/$f (this run created it)"; done
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

[ -f "$FAF" ] || red "$FAF is absent"
[ -f "$HUBF" ] || red "$HUBF is absent"
LIVE_FA="$(m5 "$FAF")"
LIVE_HUB="$(m5 "$HUBF")"
FA_DONE=0; HUB_DONE=0; FILES_DONE=1
if grep -qF "$FA_MARK" "$FAF"; then FA_DONE=1; fi
if grep -qF "$HUB_MARK" "$HUBF"; then HUB_DONE=1; fi
for f in $NEWFILES; do
  if [ ! -f "$FIN/$f" ] || [ "$(m5 "$FIN/$f")" != "$(m5 "$KDIR/$f")" ]; then FILES_DONE=0; fi
done
if [ "$FA_DONE" -eq 1 ] && [ "$HUB_DONE" -eq 1 ] && [ "$FILES_DONE" -eq 1 ]; then
  echo "-- ALREADY INSTALLED: finance_app.py ${LIVE_FA:0:8} and finance_approvals.html ${LIVE_HUB:0:8} carry the S243 marks; the three module files are the kit's bytes. Nothing changed."
  exit 0
fi
if [ "$FA_DONE" -eq 0 ]; then
  if [ "$LIVE_FA" = "$FA_FROM_PIN" ]; then
    echo "-- finance_app.py is the build pin ${FA_FROM_PIN:0:8}"
  elif grep -qF "$FA_SIBLING_MARK" "$FAF"; then
    echo "-- finance_app.py ${LIVE_FA:0:8} carries the S243_SCREEN_FIXES mark (that kit installed first): lineage accepted; the patcher's anchor count is the guard"
  else
    red "live finance_app.py is ${LIVE_FA} -- neither the pin ${FA_FROM_PIN:0:8} this kit was built on nor a S243_SCREEN_FIXES-patched file; NOTHING changed"
  fi
fi
if [ "$HUB_DONE" -eq 0 ]; then
  [ "$LIVE_HUB" = "$HUB_FROM_PIN" ] || red "live finance_approvals.html is ${LIVE_HUB} -- not the pin ${HUB_FROM_PIN:0:8} this kit was built on; NOTHING changed"
fi
echo "-- live pins: finance_app.py ${LIVE_FA:0:8} | finance_approvals.html ${LIVE_HUB:0:8} (as expected)"

# ---- the kit's own proofs, before anything is placed
"$PY" -m py_compile "$KDIR/darpan_kal.py" || red "py_compile darpan_kal.py"
"$PY" -B "$KDIR/patch_finance_app_darpan_kal_s243.py" --selftest "$FAF" "$HUBF" >/dev/null 2>&1 || \
  { [ "$FA_DONE" -eq 1 ] || [ "$HUB_DONE" -eq 1 ] || red "the patcher's selftest against the LIVE bytes failed; NOTHING changed"; }

# ---- both patches to .new, BEFORE anything is placed; the anchor count is the real guard
if [ "$FA_DONE" -eq 0 ]; then
  rm -f "$FAF.new"
  FA_PATH="$FAF" "$PY" -B "$KDIR/patch_finance_app_darpan_kal_s243.py" fa || red "the finance_app patcher refused -- the anchor is not exactly once in the live file; NOTHING changed"
  [ -f "$FAF.new" ] || red "the patcher wrote no finance_app.py.new"
  grep -qF "$FA_MARK" "$FAF.new" || red "the .new does not carry the S243 mark"
  "$PY" -m py_compile "$FAF.new" || red "py_compile finance_app.py.new"
fi
if [ "$HUB_DONE" -eq 0 ]; then
  rm -f "$HUBF.new"
  HUB_PATH="$HUBF" "$PY" -B "$KDIR/patch_finance_app_darpan_kal_s243.py" hub || red "the hub patcher refused -- an anchor is not exactly once in the live page; NOTHING changed"
  [ -f "$HUBF.new" ] || red "the hub patcher wrote no .new"
  grep -qF "$HUB_MARK" "$HUBF.new" || red "the hub .new does not carry the S243 mark"
fi
echo "-- prepared: finance_app.py.new $([ "$FA_DONE" -eq 0 ] && m5 "$FAF.new" | cut -c1-8 || echo '(already patched)') | finance_approvals.html.new $([ "$HUB_DONE" -eq 0 ] && m5 "$HUBF.new" | cut -c1-8 || echo '(already patched)') | py_compile clean with $PY"

# ---- the three module files (new; an existing different copy is kept as .bak_S243)
for f in $NEWFILES; do
  if [ -f "$FIN/$f" ]; then
    if [ "$(m5 "$FIN/$f")" != "$(m5 "$KDIR/$f")" ]; then \cp -f "$FIN/$f" "$FIN/$f.bak_S243_$(m5 "$FIN/$f" | cut -c1-8)"; fi
  else
    CREATED="$CREATED $f"
  fi
  \cp -f "$KDIR/$f" "$FIN/$f"
  [ "$(m5 "$FIN/$f")" = "$(m5 "$KDIR/$f")" ] || red "$f did not land"
done
echo "-- placed: $NEWFILES -> $FIN"

# ---- backups, then place the patched files
if [ "$FA_DONE" -eq 0 ]; then
  FA_BAK="$FAF.bak_S243_${LIVE_FA:0:8}"
  \cp -f "$FAF" "$FA_BAK"
  FA_NEW_MD5="$(m5 "$FAF.new")"
  mv -f "$FAF.new" "$FAF"; PLACED_FA=1
  [ "$(m5 "$FAF")" = "$FA_NEW_MD5" ] || red "finance_app.py did not land"
fi
if [ "$HUB_DONE" -eq 0 ]; then
  HUB_BAK="$HUBF.bak_S243_${LIVE_HUB:0:8}"
  \cp -f "$HUBF" "$HUB_BAK"
  HUB_NEW_MD5="$(m5 "$HUBF.new")"
  mv -f "$HUBF.new" "$HUBF"; PLACED_HUB=1
  [ "$(m5 "$HUBF")" = "$HUB_NEW_MD5" ] || red "finance_approvals.html did not land"
fi
echo "-- placed: finance_app.py ${LIVE_FA:0:8} -> $(m5 "$FAF" | cut -c1-8) | finance_approvals.html ${LIVE_HUB:0:8} -> $(m5 "$HUBF" | cut -c1-8) | backups .bak_S243_<pin8>"

# ---- import smoke with the unit's own environment: the blueprint must be REGISTERED
SMOKE_ENV="$(systemctl show -p Environment --value "$SVC" 2>/dev/null || true)"
if [ -z "$SMOKE_ENV" ] && [ -f "$UNIT_FILE" ]; then
  SMOKE_ENV="$( { cat "$UNIT_FILE"; cat "${UNIT_FILE}.d"/*.conf 2>/dev/null || true; } | sed -n 's/^Environment=//p' | tr '\n' ' ')"
fi
[ -n "$SMOKE_ENV" ] || red "could not read the service environment (systemctl show / $UNIT_FILE)"
SMOKE_RC=0
SMOKE_OUT="$(cd "$FIN" && env -i PATH="$PATH" HOME="${HOME:-/root}" $SMOKE_ENV "$PY_SMOKE" -c "import finance_app; assert 'darpan_kal' in finance_app.app.blueprints, 'darpan_kal blueprint NOT registered (see journal line darpan_kal NOT mounted)'; print('import ok: darpan_kal mounted')" 2>&1)" || SMOKE_RC=$?
[ "$SMOKE_RC" -eq 0 ] || red "import smoke failed under the service environment:
$(echo "$SMOKE_OUT" | tail -8)"
echo "-- smoke: $(echo "$SMOKE_OUT" | tail -1) ($PY_SMOKE, env from the unit)"

# ---- the recipients: owner `manoj` -> dr_manoj, Dr Bhawna `bhawna` -> dr_bhawna (idempotent; never overwrites a hand edit)
if [ -f "$FIN/finance.db" ]; then
  "$PY" -B "$KDIR/seed_kal_recipients_s243.py" "$FIN/finance.db" || red "seed_kal_recipients_s243.py failed"
else
  echo "-- NOTE: $FIN/finance.db absent -- recipients not seeded (run seed_kal_recipients_s243.py by hand)"
fi

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
KAL="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:8106/finance/darpan/kal" 2>/dev/null || true)"
OLD="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:8106/finance/darpan" 2>/dev/null || true)"
echo "-- healthz 200 after ${i}s | anonymous /finance/darpan/kal $KAL and /finance/darpan $OLD (302/401 = the login gate, as before)"
RESTARTED=2
echo ""
echo "== $KIT INSTALLED"
echo "   finance_app.py             was ${LIVE_FA}  actual $(m5 "$FAF")  (patched on this box; record this pin)"
echo "   finance_approvals.html     was ${LIVE_HUB}  actual $(m5 "$HUBF")"
for f in $NEWFILES; do echo "   $FIN/$f  $(m5 "$FIN/$f")"; done
echo "   backups: $FA_BAK  $HUB_BAK  (rollback line in README)"
echo "   from-pin recorded in the .bak name; recipients seeded (manoj -> dr_manoj, bhawna -> dr_bhawna, viewer role for bhawna)"
echo "   next (GUI, owner): point Darpan's portal tile at /finance/darpan/kal"
exit 0
