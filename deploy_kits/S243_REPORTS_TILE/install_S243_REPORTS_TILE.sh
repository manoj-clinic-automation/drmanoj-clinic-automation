#!/bin/bash
# =============================================================================
#  install_S243_REPORTS_TILE.sh -- kit S243_REPORTS_TILE -- "Aaj ki reports": the Marg report
#  generator's morning page (owner's ruling 13-Sep-2026: Shavez generates the Marg reports).
#
#  Run by:  bash /root/deploy/repo/deploy_kits/S243_REPORTS_TILE/install_S243_REPORTS_TILE.sh
#
#  FINANCE (clinic-finance.service)
#  A  NEW file into /root/finance:   reports_tile.py
#  B  finance_app.py                 patched ON THIS BOX by patch_finance_app_reports_s243.py: one
#                                    anchor (the __main__ block at the very end), exactly once, else
#                                    REFUSED and nothing changes.  Guarded mount (S209 lesson).
#  C  finance_ui/finance_approvals.html
#                                    patched ON THIS BOX by the same patcher: one line under
#                                    "Pushed reports" on the Marg card -- "Today's reports: 2 of 3
#                                    arrived" -- with its loader and call.  Three anchors.
#  D  finance.db                     seed_reports_role_s243.py: unit_role(medical, shavez, viewer)
#                                    ONLY if he holds no active medical role (idempotent).
#  PORTAL (clinic-portal.service)
#  E  portal.py                      patched ON THIS BOX by patch_portal_reports_tile_s243.py on a
#                                    COPY, then placed: the tile "Aaj ki reports" + its group row.
#  F  tile_grants.json               v12 -> v13 (the kit's full file): granted by name to shavez, amir.
#
#  Pins this kit was built on (the 13-Sep capture):
#      finance_app.py            f002defb9f4a5d35028c051462225def  -- OR any file carrying the
#                                S243_SCREEN_FIXES and/or S243_DARPAN_KAL mark (those kits install
#                                first); the patcher's count==1 anchor is the real guard; the ACTUAL
#                                from-pin is recorded in the .bak name and the printout
#      finance_approvals.html    cc349dd00d0a2f861ec54242c9551557  -- OR carrying the DARPAN_KAL mark
#      portal.py                 d08721f69bc7c3e3a79a50192b20affb  -> 4bb6bde0e2e07033ac0e0f5d7a7daaf6
#      tile_grants.json          7e7445a37ace9ea7c8218d598a05b81d (v12) -> c9ee95c39bb805086b79d95327b2b626 (v13)
#
#  Gates: SUMS + KIT_ID -> live pins -> patcher selftest on the live bytes -> every patch to .new /
#  a copy BEFORE anything is placed -> .bak_S243_<pin8> of every changed file -> place -> py_compile
#  -> import smoke of BOTH apps under their own environment -> seed -> restart both services ->
#  healthz within 20 s each.  Any RED after placing: every file restored, the new file removed if
#  this run created it, services restarted if they were restarted, exit 1.  Re-run when already
#  installed: ALREADY INSTALLED.
#
#  ROOT=<dir> prefixes every absolute path (mock test only).  MOCK_FA_PIN / MOCK_HUB_PIN /
#  MOCK_PORTAL_PIN / MOCK_GRANTS_PIN / PY / PY_SMOKE / UNIT_FILE exist for the same mock and print
#  loudly when used.
#
#  AFTER INSTALL: nothing is left for the owner.  Shavez opens the portal, taps "Aaj ki reports".
# =============================================================================
set -e
set -u
set -o pipefail
KIT="S243_REPORTS_TILE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-}"
FIN="$ROOT/root/finance"
FAF="$FIN/finance_app.py"
HUBF="$FIN/finance_ui/finance_approvals.html"
PORTAL_DIR="$ROOT/root/portal"
PF="$PORTAL_DIR/portal.py"
GF="$PORTAL_DIR/tile_grants.json"
SVC_FIN="clinic-finance.service"
SVC_POR="clinic-portal.service"
UNIT_FILE="${UNIT_FILE:-$ROOT/etc/systemd/system/clinic-finance.service}"
HZ_FIN="http://127.0.0.1:8106/finance/healthz"
HZ_POR="http://127.0.0.1:8099/portal/health"

FA_FROM_PIN="${MOCK_FA_PIN:-f002defb9f4a5d35028c051462225def}"
FA_SIBLING_MARK_1="S243: a checker (the doctor) lands on his Review console"   # S243_SCREEN_FIXES
FA_SIBLING_MARK_2="S243_DARPAN_KAL begin"                                        # S243_DARPAN_KAL
HUB_FROM_PIN="${MOCK_HUB_PIN:-cc349dd00d0a2f861ec54242c9551557}"
HUB_SIBLING_MARK="S243 darpan kal"                                               # S243_DARPAN_KAL
PORTAL_FROM_PIN="${MOCK_PORTAL_PIN:-d08721f69bc7c3e3a79a50192b20affb}"
PORTAL_TO_PIN="4bb6bde0e2e07033ac0e0f5d7a7daaf6"
GRANTS_FROM_PIN="${MOCK_GRANTS_PIN:-7e7445a37ace9ea7c8218d598a05b81d}"
GRANTS_TO_PIN="c9ee95c39bb805086b79d95327b2b626"
FA_MARK="S243_REPORTS_TILE begin"
HUB_MARK="S243 reports tile"
PORTAL_MARK='"name": "Aaj ki reports"'
NEWFILE="reports_tile.py"

if [ -z "${PY:-}" ]; then
  if [ -x "$ROOT/root/wa/venv/bin/python3" ]; then PY="$ROOT/root/wa/venv/bin/python3"; else PY="/usr/bin/python3"; fi
fi
PY_SMOKE="${PY_SMOKE:-/usr/bin/python3}"
if [ -n "$ROOT" ]; then echo "-- MOCK: ROOT=$ROOT PY=$PY PY_SMOKE=$PY_SMOKE"; fi
for v in MOCK_FA_PIN MOCK_HUB_PIN MOCK_PORTAL_PIN MOCK_GRANTS_PIN; do
  if [ -n "${!v:-}" ]; then echo "-- MOCK: $v override ${!v}"; fi
done

FA_BAK=""; HUB_BAK=""; P_BAK=""; G_BAK=""
PLACED_FA=0; PLACED_HUB=0; PLACED_P=0; PLACED_G=0; CREATED=""; RESTARTED_FIN=0; RESTARTED_POR=0
m5() { md5sum "$1" | awk '{print $1}'; }

rollback() {
  if [ "$PLACED_FA" -eq 1 ] && [ -n "$FA_BAK" ] && [ -f "$FA_BAK" ]; then
    \cp -f "$FA_BAK" "$FAF" && echo "   restored finance_app.py from $FA_BAK ($(m5 "$FAF" | cut -c1-8))"
  fi
  if [ "$PLACED_HUB" -eq 1 ] && [ -n "$HUB_BAK" ] && [ -f "$HUB_BAK" ]; then
    \cp -f "$HUB_BAK" "$HUBF" && echo "   restored finance_approvals.html from $HUB_BAK ($(m5 "$HUBF" | cut -c1-8))"
  fi
  if [ "$PLACED_P" -eq 1 ] && [ -n "$P_BAK" ] && [ -f "$P_BAK" ]; then
    \cp -f "$P_BAK" "$PF" && echo "   restored portal.py from $P_BAK ($(m5 "$PF" | cut -c1-8))"
  fi
  if [ "$PLACED_G" -eq 1 ] && [ -n "$G_BAK" ] && [ -f "$G_BAK" ]; then
    \cp -f "$G_BAK" "$GF" && echo "   restored tile_grants.json from $G_BAK ($(m5 "$GF" | cut -c1-8))"
  fi
  for f in $CREATED; do rm -f "$FIN/$f" && echo "   removed $FIN/$f (this run created it)"; done
  rm -rf "$PORTAL_DIR/__pycache__" 2>/dev/null || true
  if [ "$RESTARTED_FIN" -eq 1 ]; then
    systemctl restart "$SVC_FIN" || true; sleep 3
    if systemctl is-active --quiet "$SVC_FIN"; then echo "   $SVC_FIN back up on the restored files"; else echo "   !! $SVC_FIN did not come back after the restore -- check: systemctl status $SVC_FIN"; fi
  fi
  if [ "$RESTARTED_POR" -eq 1 ]; then
    systemctl restart "$SVC_POR" || true; sleep 3
    if systemctl is-active --quiet "$SVC_POR"; then echo "   $SVC_POR back up on the restored files"; else echo "   !! $SVC_POR did not come back after the restore -- check: systemctl status $SVC_POR"; fi
  fi
}
red() { echo "!! RED -- $*"; rollback; echo "!! $KIT NOT installed"; exit 1; }
trap 'red "unexpected error at line $LINENO"' ERR

cd "$KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || red "SUMS.md5 gate failed -- the kit folder is not what was published"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || red "KIT_ID names a different kit"
[ "$(m5 "$KDIR/tile_grants.json")" = "$GRANTS_TO_PIN" ] || red "the kit's tile_grants.json is not $GRANTS_TO_PIN"
echo "-- gates green: SUMS.md5 and KIT_ID.txt ($KIT); grants v13 $GRANTS_TO_PIN"

for f in "$FAF" "$HUBF" "$PF" "$GF"; do [ -f "$f" ] || red "$f is absent"; done
LIVE_FA="$(m5 "$FAF")"; LIVE_HUB="$(m5 "$HUBF")"; LIVE_P="$(m5 "$PF")"; LIVE_G="$(m5 "$GF")"
FA_DONE=0; HUB_DONE=0; P_DONE=0; G_DONE=0; FILE_DONE=0
grep -qF "$FA_MARK" "$FAF" && FA_DONE=1
grep -qF "$HUB_MARK" "$HUBF" && HUB_DONE=1
grep -qF "$PORTAL_MARK" "$PF" && P_DONE=1
[ "$LIVE_G" = "$GRANTS_TO_PIN" ] && G_DONE=1
[ -f "$FIN/$NEWFILE" ] && [ "$(m5 "$FIN/$NEWFILE")" = "$(m5 "$KDIR/$NEWFILE")" ] && FILE_DONE=1
if [ "$FA_DONE" -eq 1 ] && [ "$HUB_DONE" -eq 1 ] && [ "$P_DONE" -eq 1 ] && [ "$G_DONE" -eq 1 ] && [ "$FILE_DONE" -eq 1 ]; then
  echo "-- ALREADY INSTALLED: finance_app.py ${LIVE_FA:0:8}, finance_approvals.html ${LIVE_HUB:0:8}, portal.py ${LIVE_P:0:8} carry the S243 marks; tile_grants.json is v13; reports_tile.py is the kit's bytes. Nothing changed."
  exit 0
fi
if [ "$FA_DONE" -eq 0 ]; then
  if [ "$LIVE_FA" = "$FA_FROM_PIN" ]; then
    echo "-- finance_app.py is the build pin ${FA_FROM_PIN:0:8}"
  elif grep -qF "$FA_SIBLING_MARK_1" "$FAF" || grep -qF "$FA_SIBLING_MARK_2" "$FAF"; then
    echo "-- finance_app.py ${LIVE_FA:0:8} carries a S243 sibling mark (SCREEN_FIXES / DARPAN_KAL installed first): lineage accepted; the patcher's anchor count is the guard"
  else
    red "live finance_app.py is ${LIVE_FA} -- neither the pin ${FA_FROM_PIN:0:8} this kit was built on nor a S243-sibling-patched file; NOTHING changed"
  fi
fi
if [ "$HUB_DONE" -eq 0 ]; then
  if [ "$LIVE_HUB" = "$HUB_FROM_PIN" ]; then
    echo "-- finance_approvals.html is the build pin ${HUB_FROM_PIN:0:8}"
  elif grep -qF "$HUB_SIBLING_MARK" "$HUBF"; then
    echo "-- finance_approvals.html ${LIVE_HUB:0:8} carries the S243_DARPAN_KAL mark: lineage accepted; the patcher's anchor count is the guard"
  else
    red "live finance_approvals.html is ${LIVE_HUB} -- neither the pin ${HUB_FROM_PIN:0:8} nor a DARPAN_KAL-patched page; NOTHING changed"
  fi
fi
if [ "$P_DONE" -eq 0 ]; then
  [ "$LIVE_P" = "$PORTAL_FROM_PIN" ] || red "live portal.py is ${LIVE_P} -- not the pin ${PORTAL_FROM_PIN:0:8} this kit was built on; NOTHING changed"
fi
if [ "$G_DONE" -eq 0 ]; then
  [ "$LIVE_G" = "$GRANTS_FROM_PIN" ] || red "live tile_grants.json is ${LIVE_G} -- not the v12 ${GRANTS_FROM_PIN:0:8} this kit was built on; NOTHING changed"
fi
echo "-- live pins: finance_app.py ${LIVE_FA:0:8} | finance_approvals.html ${LIVE_HUB:0:8} | portal.py ${LIVE_P:0:8} | tile_grants.json ${LIVE_G:0:8} (as expected)"

# ---- the kit's own proofs, before anything is placed
"$PY" -m py_compile "$KDIR/reports_tile.py" || red "py_compile reports_tile.py"
"$PY" -B "$KDIR/reports_tile.py" >/dev/null 2>&1 || red "reports_tile.py selftest failed"
"$PY" -B "$KDIR/patch_finance_app_reports_s243.py" --selftest "$FAF" "$HUBF" >/dev/null 2>&1 || \
  { [ "$FA_DONE" -eq 1 ] || [ "$HUB_DONE" -eq 1 ] || red "the patcher's selftest against the LIVE bytes failed; NOTHING changed"; }

# ---- every patch to .new / a copy, BEFORE anything is placed; the anchor count is the real guard
if [ "$FA_DONE" -eq 0 ]; then
  rm -f "$FAF.new"
  FA_PATH="$FAF" "$PY" -B "$KDIR/patch_finance_app_reports_s243.py" fa || red "the finance_app patcher refused -- the anchor is not exactly once in the live file; NOTHING changed"
  [ -f "$FAF.new" ] || red "the patcher wrote no finance_app.py.new"
  grep -qF "$FA_MARK" "$FAF.new" || red "the .new does not carry the S243 mark"
  "$PY" -m py_compile "$FAF.new" || red "py_compile finance_app.py.new"
fi
if [ "$HUB_DONE" -eq 0 ]; then
  rm -f "$HUBF.new"
  HUB_PATH="$HUBF" "$PY" -B "$KDIR/patch_finance_app_reports_s243.py" hub || red "the hub patcher refused -- an anchor is not exactly once in the live page; NOTHING changed"
  [ -f "$HUBF.new" ] || red "the hub patcher wrote no .new"
  grep -qF "$HUB_MARK" "$HUBF.new" || red "the hub .new does not carry the S243 mark"
fi
W="$(mktemp -d)"
if [ "$P_DONE" -eq 0 ]; then
  \cp -f "$PF" "$W/portal.py"
  ( cd "$W" && "$PY" -B "$KDIR/patch_portal_reports_tile_s243.py" ./portal.py "$LIVE_P" >/dev/null ) || { rm -rf "$W"; red "the portal patcher refused on a copy of this box's portal.py -- NOTHING changed"; }
  [ "$(m5 "$W/portal.py")" = "$PORTAL_TO_PIN" ] || { rm -rf "$W"; red "patching a copy of portal.py did not produce $PORTAL_TO_PIN -- NOTHING changed"; }
  "$PY" -m py_compile "$W/portal.py" || { rm -rf "$W"; red "py_compile of the patched portal.py copy"; }
fi
echo "-- prepared: finance_app.py.new $([ "$FA_DONE" -eq 0 ] && m5 "$FAF.new" | cut -c1-8 || echo '(already)') | finance_approvals.html.new $([ "$HUB_DONE" -eq 0 ] && m5 "$HUBF.new" | cut -c1-8 || echo '(already)') | portal.py copy $([ "$P_DONE" -eq 0 ] && echo "${PORTAL_TO_PIN:0:8}" || echo '(already)') | py_compile clean with $PY"

# ---- the module file (new; an existing different copy is kept as .bak_S243)
if [ -f "$FIN/$NEWFILE" ]; then
  if [ "$(m5 "$FIN/$NEWFILE")" != "$(m5 "$KDIR/$NEWFILE")" ]; then \cp -f "$FIN/$NEWFILE" "$FIN/$NEWFILE.bak_S243_$(m5 "$FIN/$NEWFILE" | cut -c1-8)"; fi
else
  CREATED="$CREATED $NEWFILE"
fi
\cp -f "$KDIR/$NEWFILE" "$FIN/$NEWFILE"
[ "$(m5 "$FIN/$NEWFILE")" = "$(m5 "$KDIR/$NEWFILE")" ] || red "$NEWFILE did not land"
echo "-- placed: $NEWFILE -> $FIN"

# ---- backups, then place the patched files
if [ "$FA_DONE" -eq 0 ]; then
  FA_BAK="$FAF.bak_S243_${LIVE_FA:0:8}"; \cp -f "$FAF" "$FA_BAK"
  FA_NEW_MD5="$(m5 "$FAF.new")"; mv -f "$FAF.new" "$FAF"; PLACED_FA=1
  [ "$(m5 "$FAF")" = "$FA_NEW_MD5" ] || red "finance_app.py did not land"
fi
if [ "$HUB_DONE" -eq 0 ]; then
  HUB_BAK="$HUBF.bak_S243_${LIVE_HUB:0:8}"; \cp -f "$HUBF" "$HUB_BAK"
  HUB_NEW_MD5="$(m5 "$HUBF.new")"; mv -f "$HUBF.new" "$HUBF"; PLACED_HUB=1
  [ "$(m5 "$HUBF")" = "$HUB_NEW_MD5" ] || red "finance_approvals.html did not land"
fi
if [ "$P_DONE" -eq 0 ]; then
  P_BAK="$PF.bak_S243_${LIVE_P:0:8}"; \cp -f "$PF" "$P_BAK"
  \cp -f "$W/portal.py" "$PF"; PLACED_P=1
  [ "$(m5 "$PF")" = "$PORTAL_TO_PIN" ] || red "portal.py did not land as $PORTAL_TO_PIN"
fi
rm -rf "$W"
if [ "$G_DONE" -eq 0 ]; then
  G_BAK="$GF.bak_S243_${LIVE_G:0:8}"; \cp -f "$GF" "$G_BAK"
  \cp -f "$KDIR/tile_grants.json" "$GF"; PLACED_G=1
  [ "$(m5 "$GF")" = "$GRANTS_TO_PIN" ] || red "tile_grants.json did not land as $GRANTS_TO_PIN"
fi
rm -rf "$PORTAL_DIR/__pycache__" 2>/dev/null || true
echo "-- placed: finance_app.py ${LIVE_FA:0:8} -> $(m5 "$FAF" | cut -c1-8) | finance_approvals.html ${LIVE_HUB:0:8} -> $(m5 "$HUBF" | cut -c1-8) | portal.py ${LIVE_P:0:8} -> $(m5 "$PF" | cut -c1-8) | tile_grants.json ${LIVE_G:0:8} -> $(m5 "$GF" | cut -c1-8) | backups .bak_S243_<pin8>"

# ---- import smoke, finance: the unit's own environment; the blueprint must be REGISTERED
SMOKE_ENV="$(systemctl show -p Environment --value "$SVC_FIN" 2>/dev/null || true)"
if [ -z "$SMOKE_ENV" ] && [ -f "$UNIT_FILE" ]; then
  SMOKE_ENV="$( { cat "$UNIT_FILE"; cat "${UNIT_FILE}.d"/*.conf 2>/dev/null || true; } | sed -n 's/^Environment=//p' | tr '\n' ' ')"
fi
[ -n "$SMOKE_ENV" ] || red "could not read the finance service environment (systemctl show / $UNIT_FILE)"
SMOKE_RC=0
SMOKE_OUT="$(cd "$FIN" && env -i PATH="$PATH" HOME="${HOME:-/root}" $SMOKE_ENV "$PY_SMOKE" -c "import finance_app; assert 'reports_tile' in finance_app.app.blueprints, 'reports_tile blueprint NOT registered (see journal line reports_tile NOT mounted)'; print('import ok: reports_tile mounted')" 2>&1)" || SMOKE_RC=$?
[ "$SMOKE_RC" -eq 0 ] || red "finance import smoke failed under the service environment:
$(echo "$SMOKE_OUT" | tail -8)"
echo "-- smoke finance: $(echo "$SMOKE_OUT" | tail -1) ($PY_SMOKE, env from the unit)"

# ---- import smoke, portal: the tile exists, is grouped (portal's own assert), the grants file is v13
SMOKE_RC=0
SMOKE_OUT="$(cd "$PORTAL_DIR" && TILE_GRANTS_FILE="$GF" PORTAL_PIN_SALT="${PORTAL_PIN_SALT:-smoke}" PORTAL_TOKEN_SEED="${PORTAL_TOKEN_SEED:-smoke}" "$PY" -B -c "import portal; assert any(t['name']=='Aaj ki reports' and t['url']=='/finance/reports/aaj' for t in portal.TILES), 'tile absent'; g=portal._tile_grants(); assert g and g.get('version')==13, 'grants not v13'; assert 'Aaj ki reports' in [t['name'] for _g,items in portal._visible_sections('manager', False, 'shavez') for t in items], 'shavez not shown the tile'; print('import ok: tile present, grants v13, shavez sees it')" 2>&1)" || SMOKE_RC=$?
rm -rf "$PORTAL_DIR/__pycache__" 2>/dev/null || true
[ "$SMOKE_RC" -eq 0 ] || red "portal import smoke failed:
$(echo "$SMOKE_OUT" | tail -8)"
echo "-- smoke portal: $(echo "$SMOKE_OUT" | tail -1)"

# ---- the gate row for shavez (idempotent; never removes or downgrades)
if [ -f "$FIN/finance.db" ]; then
  "$PY" -B "$KDIR/seed_reports_role_s243.py" "$FIN/finance.db" || red "seed_reports_role_s243.py failed"
else
  echo "-- NOTE: $FIN/finance.db absent -- role not seeded (run seed_reports_role_s243.py by hand)"
fi

# ---- restart and prove, both services
RESTARTED_FIN=1
systemctl restart "$SVC_FIN" || red "systemctl restart $SVC_FIN failed"
HZ=""; i=0
while [ $i -lt 20 ]; do
  HZ="$(curl -s -o /dev/null -w '%{http_code}' "$HZ_FIN" 2>/dev/null || true)"
  if [ "$HZ" = "200" ]; then break; fi
  sleep 1; i=$((i+1))
done
[ "$HZ" = "200" ] || red "finance healthz answered '$HZ' after 20 s"
systemctl is-active --quiet "$SVC_FIN" || red "$SVC_FIN is not active"
RPT="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:8106/finance/reports/aaj" 2>/dev/null || true)"
echo "-- finance healthz 200 after ${i}s | anonymous /finance/reports/aaj $RPT (302/401 = the login gate, as designed)"

RESTARTED_POR=1
systemctl restart "$SVC_POR" || red "systemctl restart $SVC_POR failed"
HZ=""; j=0
while [ $j -lt 20 ]; do
  HZ="$(curl -s -o /dev/null -w '%{http_code}' "$HZ_POR" 2>/dev/null || true)"
  if [ "$HZ" = "200" ]; then break; fi
  sleep 1; j=$((j+1))
done
[ "$HZ" = "200" ] || red "portal health answered '$HZ' after 20 s"
systemctl is-active --quiet "$SVC_POR" || red "$SVC_POR is not active"
echo "-- portal health 200 after ${j}s"
RESTARTED_FIN=2; RESTARTED_POR=2
echo ""
echo "== $KIT INSTALLED"
echo "   finance_app.py             was ${LIVE_FA}  actual $(m5 "$FAF")  (patched on this box; record this pin)"
echo "   finance_approvals.html     was ${LIVE_HUB}  actual $(m5 "$HUBF")"
echo "   portal.py                  was ${LIVE_P}  actual $(m5 "$PF")"
echo "   tile_grants.json           was ${LIVE_G}  actual $(m5 "$GF")  (v12 -> v13)"
echo "   $FIN/$NEWFILE  $(m5 "$FIN/$NEWFILE")"
echo "   backups: $FA_BAK  $HUB_BAK  $P_BAK  $G_BAK  (rollback line in README)"
echo "   Shavez's tile: Aaj ki reports -> https://followup.dr-manoj.in/finance/reports/aaj"
exit 0
