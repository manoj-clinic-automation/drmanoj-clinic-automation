#!/bin/bash
# =============================================================================
#  install_S243_CA_AND_NUMBERS.sh -- kit S243_CA_AND_NUMBERS -- two owner rulings of 13-Sep-2026
#
#  Run by:  bash /root/deploy/repo/deploy_kits/S243_CA_AND_NUMBERS/install_S243_CA_AND_NUMBERS.sh
#
#  RULING A (the chartered accountant): no cash/UPI correction in Marg any more; the record becomes
#           the MONTHLY accountant report.
#  RULING B: full phone numbers on the returns desk (where the master carries the number).
#
#  A  NEW file into /root/finance:      accountant_upi_cash.py   (/finance/accountant/upi-cash/<yyyy-mm>)
#  B  REPLACED (full file, .bak kept):  darpan_corrections.html  (read-only record page, Hindi header)
#  C  PATCHED ON THIS BOX by patch_ca_and_numbers_s243.py, every anchor exactly once or REFUSED:
#        finance_app.py                      mount + health info line + links + selftest wording
#        finance_ui/finance_approvals.html   the Cash<->UPI card links the report; tab "Accountant"
#        returns_desk.py                     /api/search returns and searches the full number
#        returns_desk.html                   picker and chosen line show it
#
#  Pins this kit was built on (the 13-Sep capture):
#      finance_app.py            f002defb9f4a5d35028c051462225def  -- OR a file carrying the S243_SCREEN_FIXES
#                                or S243_DARPAN_KAL mark (those kits install first and move the pin; the
#                                patcher's count==1 anchors are the real guard; the ACTUAL from-pin is recorded)
#      finance_approvals.html    cc349dd00d0a2f861ec54242c9551557  -- OR carrying the S243 darpan kal mark
#      returns_desk.py           dface15bd886774c59d5c88034619650
#      returns_desk.html         77e754e9b072eb78033affd5e8505b2a
#      darpan_corrections.html   26b1defeb0333fb8642a7abf95a93e5b
#
#  Gates: SUMS + KIT_ID -> live pins / lineage -> patcher selftest on the LIVE bytes -> all four patches
#  to .new BEFORE anything is placed -> py_compile -> place (backups .bak_S243_<pin8>) -> import smoke under
#  the unit's own environment (the accountant_upi_cash blueprint must be registered) -> restart -> healthz
#  within 20 s. Any RED after placing: every file restored, the new file removed if this run created it,
#  service restarted if it was restarted, exit 1. Re-run when already installed: ALREADY INSTALLED.
#
#  INSTALL ORDER: after S243_SCREEN_FIXES and S243_DARPAN_KAL (their gates accept only the older pins; this
#  kit's gate accepts theirs). tile_grants.json is NOT touched (S243_REPORTS_TILE owns it -- see README).
#
#  ROOT=<dir> prefixes every absolute path (mock test only). MOCK_*_PIN / PY / PY_SMOKE / UNIT_FILE exist
#  for the same mock and print loudly when used.
# =============================================================================
set -e
set -u
set -o pipefail
KIT="S243_CA_AND_NUMBERS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-}"
FIN="$ROOT/root/finance"
FAF="$FIN/finance_app.py"
HUBF="$FIN/finance_ui/finance_approvals.html"
RDF="$FIN/returns_desk.py"
RDHF="$FIN/returns_desk.html"
CORF="$FIN/darpan_corrections.html"
NEWF="accountant_upi_cash.py"
SVC="clinic-finance.service"
UNIT_FILE="${UNIT_FILE:-$ROOT/etc/systemd/system/clinic-finance.service}"
HZ_URL="http://127.0.0.1:8106/finance/healthz"

FA_FROM_PIN="${MOCK_FA_PIN:-f002defb9f4a5d35028c051462225def}"
FA_SIBLING_MARKS="S243: a checker (the doctor) lands on his Review console|S243_DARPAN_KAL begin"
HUB_FROM_PIN="${MOCK_HUB_PIN:-cc349dd00d0a2f861ec54242c9551557}"
HUB_SIBLING_MARK="S243 darpan kal"
RD_FROM_PIN="${MOCK_RD_PIN:-dface15bd886774c59d5c88034619650}"
RDH_FROM_PIN="${MOCK_RDH_PIN:-77e754e9b072eb78033affd5e8505b2a}"
COR_FROM_PIN="${MOCK_COR_PIN:-26b1defeb0333fb8642a7abf95a93e5b}"
FA_MARK="S243_CA_AND_NUMBERS begin"
HUB_MARK="S243 ca accountant report"
RD_MARK="S243_CA_AND_NUMBERS: full number"
RDH_MARK="S243 full number"
COR_MARK="Ab Marg me sudhaar nahi karna hai"

if [ -z "${PY:-}" ]; then
  if [ -x "$ROOT/root/wa/venv/bin/python3" ]; then PY="$ROOT/root/wa/venv/bin/python3"; else PY="/usr/bin/python3"; fi
fi
PY_SMOKE="${PY_SMOKE:-/usr/bin/python3}"
if [ -n "$ROOT" ]; then echo "-- MOCK: ROOT=$ROOT PY=$PY PY_SMOKE=$PY_SMOKE"; fi
for v in MOCK_FA_PIN MOCK_HUB_PIN MOCK_RD_PIN MOCK_RDH_PIN MOCK_COR_PIN; do
  if [ -n "${!v:-}" ]; then echo "-- MOCK: $v override ${!v}"; fi
done

FA_BAK=""; HUB_BAK=""; RD_BAK=""; RDH_BAK=""; COR_BAK=""; RESTARTED=0
PLACED_FA=0; PLACED_HUB=0; PLACED_RD=0; PLACED_RDH=0; PLACED_COR=0; CREATED=""
m5() { md5sum "$1" | awk '{print $1}'; }

rollback() {
  [ "$PLACED_FA" -eq 1 ] && [ -n "$FA_BAK" ] && [ -f "$FA_BAK" ] && \cp -f "$FA_BAK" "$FAF" && echo "   restored finance_app.py from $FA_BAK ($(m5 "$FAF" | cut -c1-8))"
  [ "$PLACED_HUB" -eq 1 ] && [ -n "$HUB_BAK" ] && [ -f "$HUB_BAK" ] && \cp -f "$HUB_BAK" "$HUBF" && echo "   restored finance_approvals.html from $HUB_BAK"
  [ "$PLACED_RD" -eq 1 ] && [ -n "$RD_BAK" ] && [ -f "$RD_BAK" ] && \cp -f "$RD_BAK" "$RDF" && echo "   restored returns_desk.py from $RD_BAK"
  [ "$PLACED_RDH" -eq 1 ] && [ -n "$RDH_BAK" ] && [ -f "$RDH_BAK" ] && \cp -f "$RDH_BAK" "$RDHF" && echo "   restored returns_desk.html from $RDH_BAK"
  [ "$PLACED_COR" -eq 1 ] && [ -n "$COR_BAK" ] && [ -f "$COR_BAK" ] && \cp -f "$COR_BAK" "$CORF" && echo "   restored darpan_corrections.html from $COR_BAK"
  for f in $CREATED; do rm -f "$FIN/$f" && echo "   removed $FIN/$f (this run created it)"; done
  if [ "$RESTARTED" -eq 1 ]; then
    systemctl restart "$SVC" || true; sleep 3
    if systemctl is-active --quiet "$SVC"; then echo "   service back up on the restored files"; else echo "   !! service did not come back after the restore -- check: systemctl status $SVC"; fi
  fi
  return 0
}
red() { echo "!! RED -- $*"; rollback; echo "!! $KIT NOT installed"; exit 1; }
trap 'red "unexpected error at line $LINENO"' ERR

cd "$KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || red "SUMS.md5 gate failed -- the kit folder is not what was published"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || red "KIT_ID names a different kit"
echo "-- gates green: SUMS.md5 and KIT_ID.txt ($KIT)"

for f in "$FAF" "$HUBF" "$RDF" "$RDHF" "$CORF"; do [ -f "$f" ] || red "$f is absent"; done
LIVE_FA="$(m5 "$FAF")"; LIVE_HUB="$(m5 "$HUBF")"; LIVE_RD="$(m5 "$RDF")"; LIVE_RDH="$(m5 "$RDHF")"; LIVE_COR="$(m5 "$CORF")"
FA_DONE=0; HUB_DONE=0; RD_DONE=0; RDH_DONE=0; COR_DONE=0; NEW_DONE=0
grep -qF "$FA_MARK" "$FAF" && FA_DONE=1
grep -qF "$HUB_MARK" "$HUBF" && HUB_DONE=1
grep -qF "$RD_MARK" "$RDF" && RD_DONE=1
grep -qF "$RDH_MARK" "$RDHF" && RDH_DONE=1
grep -qF "$COR_MARK" "$CORF" && [ "$LIVE_COR" = "$(m5 "$KDIR/darpan_corrections.html")" ] && COR_DONE=1
[ -f "$FIN/$NEWF" ] && [ "$(m5 "$FIN/$NEWF")" = "$(m5 "$KDIR/$NEWF")" ] && NEW_DONE=1
if [ "$FA_DONE$HUB_DONE$RD_DONE$RDH_DONE$COR_DONE$NEW_DONE" = "111111" ]; then
  echo "-- ALREADY INSTALLED: every file carries the S243_CA_AND_NUMBERS mark / the kit's bytes (finance_app ${LIVE_FA:0:8}, hub ${LIVE_HUB:0:8}, desk ${LIVE_RD:0:8}/${LIVE_RDH:0:8}). Nothing changed."
  exit 0
fi

# ---- lineage
if [ "$FA_DONE" -eq 0 ]; then
  if [ "$LIVE_FA" = "$FA_FROM_PIN" ]; then echo "-- finance_app.py is the build pin ${FA_FROM_PIN:0:8}"
  elif grep -qE "$FA_SIBLING_MARKS" "$FAF"; then echo "-- finance_app.py ${LIVE_FA:0:8} carries a S243 sibling mark (SCREEN_FIXES / DARPAN_KAL installed first): lineage accepted; the patcher's anchor count is the guard"
  else red "live finance_app.py is ${LIVE_FA} -- neither the pin ${FA_FROM_PIN:0:8} nor a S243 sibling-patched file; NOTHING changed"; fi
fi
if [ "$HUB_DONE" -eq 0 ]; then
  if [ "$LIVE_HUB" = "$HUB_FROM_PIN" ]; then echo "-- finance_approvals.html is the build pin ${HUB_FROM_PIN:0:8}"
  elif grep -qF "$HUB_SIBLING_MARK" "$HUBF"; then echo "-- finance_approvals.html ${LIVE_HUB:0:8} carries the S243_DARPAN_KAL mark: lineage accepted"
  else red "live finance_approvals.html is ${LIVE_HUB} -- neither the pin ${HUB_FROM_PIN:0:8} nor DARPAN_KAL-patched; NOTHING changed"; fi
fi
[ "$RD_DONE" -eq 1 ] || [ "$LIVE_RD" = "$RD_FROM_PIN" ] || red "live returns_desk.py is ${LIVE_RD} -- not the pin ${RD_FROM_PIN:0:8}; NOTHING changed"
[ "$RDH_DONE" -eq 1 ] || [ "$LIVE_RDH" = "$RDH_FROM_PIN" ] || red "live returns_desk.html is ${LIVE_RDH} -- not the pin ${RDH_FROM_PIN:0:8}; NOTHING changed"
[ "$COR_DONE" -eq 1 ] || [ "$LIVE_COR" = "$COR_FROM_PIN" ] || red "live darpan_corrections.html is ${LIVE_COR} -- not the pin ${COR_FROM_PIN:0:8}; NOTHING changed"
echo "-- live pins: finance_app ${LIVE_FA:0:8} | hub ${LIVE_HUB:0:8} | returns_desk.py ${LIVE_RD:0:8} | returns_desk.html ${LIVE_RDH:0:8} | darpan_corrections.html ${LIVE_COR:0:8} (as expected)"
[ -f "$FIN/padwriter.py" ] || echo "-- NOTE: $FIN/padwriter.py is absent -- the .xlsx download will answer 503; the page and JSON still work"

# ---- the kit's own proofs, before anything is placed
"$PY" -m py_compile "$KDIR/$NEWF" || red "py_compile $NEWF"
SELF_ARGS=""
[ "$FA_DONE" -eq 0 ] && SELF_ARGS="$SELF_ARGS $FAF"
[ "$HUB_DONE" -eq 0 ] && SELF_ARGS="$SELF_ARGS $HUBF"
[ "$RD_DONE" -eq 0 ] && SELF_ARGS="$SELF_ARGS $RDF"
[ "$RDH_DONE" -eq 0 ] && SELF_ARGS="$SELF_ARGS $RDHF"
if [ -n "$SELF_ARGS" ]; then
  "$PY" -B "$KDIR/patch_ca_and_numbers_s243.py" --selftest $SELF_ARGS >/dev/null 2>&1 || red "the patcher's selftest against the LIVE bytes failed; NOTHING changed"
fi

# ---- every patch to .new BEFORE anything is placed
prep() {  # $1 which  $2 file  $3 mark
  rm -f "$2.new"
  FA_PATH="$FAF" HUB_PATH="$HUBF" RD_PATH="$RDF" RDH_PATH="$RDHF" "$PY" -B "$KDIR/patch_ca_and_numbers_s243.py" "$1" || red "the patcher refused $1 -- an anchor is not exactly once in the live file; NOTHING changed"
  [ -f "$2.new" ] || red "the patcher wrote no $2.new"
  grep -qF "$3" "$2.new" || red "$2.new does not carry the S243 mark"
  case "$2" in *.py) "$PY" -m py_compile "$2.new" || red "py_compile $2.new";; esac
}
[ "$FA_DONE" -eq 0 ] && prep fa "$FAF" "$FA_MARK"
[ "$HUB_DONE" -eq 0 ] && prep hub "$HUBF" "$HUB_MARK"
[ "$RD_DONE" -eq 0 ] && prep rd "$RDF" "$RD_MARK"
[ "$RDH_DONE" -eq 0 ] && prep rdh "$RDHF" "$RDH_MARK"
echo "-- prepared every .new; py_compile clean with $PY"

# ---- place: the new module, the replaced page, then the four patched files (backups first)
if [ "$NEW_DONE" -eq 0 ]; then
  if [ -f "$FIN/$NEWF" ]; then \cp -f "$FIN/$NEWF" "$FIN/$NEWF.bak_S243_$(m5 "$FIN/$NEWF" | cut -c1-8)"; else CREATED="$CREATED $NEWF"; fi
  \cp -f "$KDIR/$NEWF" "$FIN/$NEWF"
  [ "$(m5 "$FIN/$NEWF")" = "$(m5 "$KDIR/$NEWF")" ] || red "$NEWF did not land"
fi
if [ "$COR_DONE" -eq 0 ]; then
  COR_BAK="$CORF.bak_S243_${LIVE_COR:0:8}"; \cp -f "$CORF" "$COR_BAK"
  \cp -f "$KDIR/darpan_corrections.html" "$CORF"; PLACED_COR=1
  [ "$(m5 "$CORF")" = "$(m5 "$KDIR/darpan_corrections.html")" ] || red "darpan_corrections.html did not land"
fi
place() {  # $1 file  $2 live md5  -> sets nothing; caller sets PLACED flag
  local nm; nm="$(m5 "$1.new")"
  mv -f "$1.new" "$1"
  [ "$(m5 "$1")" = "$nm" ] || red "$1 did not land"
}
if [ "$FA_DONE" -eq 0 ]; then FA_BAK="$FAF.bak_S243_${LIVE_FA:0:8}"; \cp -f "$FAF" "$FA_BAK"; place "$FAF"; PLACED_FA=1; fi
if [ "$HUB_DONE" -eq 0 ]; then HUB_BAK="$HUBF.bak_S243_${LIVE_HUB:0:8}"; \cp -f "$HUBF" "$HUB_BAK"; place "$HUBF"; PLACED_HUB=1; fi
if [ "$RD_DONE" -eq 0 ]; then RD_BAK="$RDF.bak_S243_${LIVE_RD:0:8}"; \cp -f "$RDF" "$RD_BAK"; place "$RDF"; PLACED_RD=1; fi
if [ "$RDH_DONE" -eq 0 ]; then RDH_BAK="$RDHF.bak_S243_${LIVE_RDH:0:8}"; \cp -f "$RDHF" "$RDH_BAK"; place "$RDHF"; PLACED_RDH=1; fi
echo "-- placed: finance_app ${LIVE_FA:0:8} -> $(m5 "$FAF" | cut -c1-8) | hub ${LIVE_HUB:0:8} -> $(m5 "$HUBF" | cut -c1-8) | returns_desk.py ${LIVE_RD:0:8} -> $(m5 "$RDF" | cut -c1-8) | returns_desk.html ${LIVE_RDH:0:8} -> $(m5 "$RDHF" | cut -c1-8) | darpan_corrections.html ${LIVE_COR:0:8} -> $(m5 "$CORF" | cut -c1-8) | $NEWF $(m5 "$FIN/$NEWF" | cut -c1-8)"

# ---- import smoke with the unit's own environment: the blueprint must be REGISTERED
SMOKE_ENV="$(systemctl show -p Environment --value "$SVC" 2>/dev/null || true)"
if [ -z "$SMOKE_ENV" ] && [ -f "$UNIT_FILE" ]; then
  SMOKE_ENV="$( { cat "$UNIT_FILE"; cat "${UNIT_FILE}.d"/*.conf 2>/dev/null || true; } | sed -n 's/^Environment=//p' | tr '\n' ' ')"
fi
[ -n "$SMOKE_ENV" ] || red "could not read the service environment (systemctl show / $UNIT_FILE)"
SMOKE_RC=0
SMOKE_OUT="$(cd "$FIN" && env -i PATH="$PATH" HOME="${HOME:-/root}" $SMOKE_ENV "$PY_SMOKE" -c "import finance_app; assert 'accountant_upi_cash' in finance_app.app.blueprints, 'accountant_upi_cash blueprint NOT registered (see journal line accountant_upi_cash NOT mounted)'; import returns_desk; print('import ok: accountant_upi_cash mounted, returns_desk imports')" 2>&1)" || SMOKE_RC=$?
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
ACU="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:8106/finance/accountant/upi-cash" 2>/dev/null || true)"
COR="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:8106/finance/darpan/corrections" 2>/dev/null || true)"
echo "-- healthz 200 after ${i}s | anonymous /finance/accountant/upi-cash $ACU and /finance/darpan/corrections $COR (302/401/403 = the login gate, as before)"
RESTARTED=2
echo ""
echo "== $KIT INSTALLED"
echo "   finance_app.py             was ${LIVE_FA}  actual $(m5 "$FAF")  (patched on this box; record this pin)"
echo "   finance_approvals.html     was ${LIVE_HUB}  actual $(m5 "$HUBF")"
echo "   returns_desk.py            was ${LIVE_RD}  actual $(m5 "$RDF")"
echo "   returns_desk.html          was ${LIVE_RDH}  actual $(m5 "$RDHF")"
echo "   darpan_corrections.html    was ${LIVE_COR}  actual $(m5 "$CORF")"
echo "   $FIN/$NEWF  $(m5 "$FIN/$NEWF")"
echo "   backups: .bak_S243_<pin8> beside each file (rollback line in README)"
echo "   next: open https://<portal>/finance/accountant/upi-cash as the owner; the corrections tile for Darpan is a tile_grants.json edit left to S243_REPORTS_TILE (README)"
exit 0
