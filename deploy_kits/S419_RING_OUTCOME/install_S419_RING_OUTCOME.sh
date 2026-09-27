#!/bin/bash
# install_S419_RING_OUTCOME.sh -- session 284, 27-Sep-2026 -- D590 steps 2-3: the outcome at hang-up, the
# 10-minute reminder, the per-person counts. Places ring_outcome.py (NEW), ring_hook.py and portal_push.py
# (full files from the live bytes); portal.py is NOT touched. Restarts ring-hook and clinic-portal.
# Proven first on a scratch copy (py_compile + walk_s419.py, no network) and by a READ-ONLY look at the
# tracker sheet through the venv's gspread. Every check is named; RED after placing = restore + exit 1.
set -u
KIT="S419_RING_OUTCOME"; KDIR="$(cd "$(dirname "$0")" && pwd)"; VPY="${VPY:-/root/wa/venv/bin/python3}"; PD="${PD:-/root/portal}"
PORTAL_PORT="${PORTAL_PORT:-8099}"; STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s419_walk_$STAMP"
RH_FROM=a3cd0466fc500c444f958fc83c8d9e42; RH_TO=ccbec2304e8038e4353ece70d84a38d2
PP_FROM=576ae269e7136261f47c1de2314f67b7; PP_TO=73c5c7d7804ccff14ddf961fa36e4c8a
RC_LIVE=4344b59277d94b2d11d8d7cc23328677; RO_TO=495b0ada681cda359a1a621a22f4efa5
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }; say() { echo "$@"; }
cd "$KDIR" || exit 1
say "[1/7] kit gates"
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit"; exit 1; }
[ "$(m5 ring_hook.py)" = "$RH_TO" ] && [ "$(m5 portal_push.py)" = "$PP_TO" ] && [ "$(m5 ring_outcome.py)" = "$RO_TO" ] || { say "!! [1/7] kit files not at their pins"; exit 1; }
say "      green"
if [ "$(m5 "$PD/ring_hook.py")" = "$RH_TO" ] && [ "$(m5 "$PD/portal_push.py")" = "$PP_TO" ] && [ "$(m5 "$PD/ring_outcome.py")" = "$RO_TO" ]; then say "-- ALREADY INSTALLED. Nothing to do."; exit 0; fi
say "[2/7] live pins"
[ "$(m5 "$PD/ring_hook.py")" = "$RH_FROM" ] || { say "!! [2/7] live ring_hook.py is $(m5 "$PD/ring_hook.py"), not the S366 pin - nothing installed"; exit 1; }
[ "$(m5 "$PD/portal_push.py")" = "$PP_FROM" ] || { say "!! [2/7] live portal_push.py is $(m5 "$PD/portal_push.py"), not the S370 pin - nothing installed"; exit 1; }
[ "$(m5 "$PD/ring_common.py")" = "$RC_LIVE" ] || { say "!! [2/7] live ring_common.py is $(m5 "$PD/ring_common.py"), not the S366 pin - nothing installed"; exit 1; }
[ -e "$PD/ring_outcome.py" ] && { say "!! [2/7] $PD/ring_outcome.py already exists ($(m5 "$PD/ring_outcome.py")) - nothing installed"; exit 1; }
say "      exact"
say "[3/7] the scratch walk (no network)"
mkdir -p "$WALK/app" && \cp -p ring_hook.py portal_push.py ring_outcome.py "$WALK/app/" && \cp -p "$PD/ring_common.py" "$WALK/app/" || { say "!! [3/7] scratch copy failed"; rm -rf "$WALK"; exit 1; }
"$VPY" -B -m py_compile "$WALK/app/ring_hook.py" "$WALK/app/portal_push.py" "$WALK/app/ring_outcome.py" || { say "!! [3/7] py_compile failed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd /tmp && timeout 150 "$VPY" -B "$KDIR/walk_s419.py" "$WALK/app" 2>&1 | tail -1 )"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [3/7] walk red: $WOUT - nothing installed"; rm -rf "$WALK"; exit 1; }
say "      $WOUT"
say "[4/7] the tracker sheet, read-only, through the venv (key found by content, id from push_followups_vps.py; nothing printed)"
PROBE="$( cd "$WALK/app" && RING_PORTAL_DIR="$PD" "$VPY" -B - <<'PY' 2>&1
import sys
sys.path.insert(0, "/root/portal")
import ring_outcome as ro
import glob, os
keys = [p for p in glob.glob(os.path.join(ro.KEY_DIR, "*.json"))]
k = ro._find_key(); sid = ro._sheet_id()
print("keys-by-content:", 1 if k else 0, "sheet-id:", "yes" if sid else "no")
if not (k and sid):
    print("PROBE RED"); sys.exit(1)
sh = ro.open_sheet()
ws = sh.worksheet(ro.OUTCOMES_TAB)
head = ws.row_values(1)
print("Followup_Outcomes rows:", ws.row_count, "header-cols:", len(head), "header-matches:", head[:18] == ro.FU_OUTCOME_HEADERS)
ag = sh.worksheet(ro.AGENTS_TAB).get_all_values()
print("Agents tab rows:", max(0, len(ag) - 1))
print("PROBE OK" if head[:18] == ro.FU_OUTCOME_HEADERS else "PROBE RED header")
PY
)"; rm -rf "$WALK"
echo "$PROBE" | sed 's/^/      /'
echo "$PROBE" | grep -q "^PROBE OK" || { say "!! [4/7] the sheet probe is red - nothing installed"; exit 1; }
say "[5/7] backup + place"
BAK1="$PD/ring_hook.py.bak_S419_a3cd0466"; BAK2="$PD/portal_push.py.bak_S419_576ae269"
\cp -p "$PD/ring_hook.py" "$BAK1" && \cp -p "$PD/portal_push.py" "$BAK2" || { say "!! [5/7] backup failed"; exit 1; }
restore() { say "!! RED after placing ($1) - restoring"; \cp -p "$BAK1" "$PD/ring_hook.py"; \cp -p "$BAK2" "$PD/portal_push.py"; rm -f "$PD/ring_outcome.py"; systemctl restart ring-hook clinic-portal || true; sleep 4; say "   ring_hook.py $(m5 "$PD/ring_hook.py") portal_push.py $(m5 "$PD/portal_push.py")"; exit 1; }
\cp -p ring_outcome.py "$PD/ring_outcome.py" && \cp -p ring_hook.py "$PD/ring_hook.py" && \cp -p portal_push.py "$PD/portal_push.py" && chmod 600 "$PD/ring_outcome.py" || restore "copy"
[ "$(m5 "$PD/ring_hook.py")" = "$RH_TO" ] && [ "$(m5 "$PD/portal_push.py")" = "$PP_TO" ] && [ "$(m5 "$PD/ring_outcome.py")" = "$RO_TO" ] || restore "placed bytes"
say "[6/7] restart ring-hook + clinic-portal, then the probes"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart ring-hook || restore "ring-hook restart"; systemctl restart clinic-portal || restore "portal restart"
sleep 5; systemctl is-active --quiet ring-hook || restore "ring-hook not active"; systemctl is-active --quiet clinic-portal || restore "portal not active"
RP="$(grep -m1 '^RING_HOOK_PORT=' "$PD/ring_hook.env" 2>/dev/null | cut -d= -f2)"; RP="${RP:-8110}"
RH="$(curl -s -m 8 "http://127.0.0.1:$RP/ring-hook/health")"; PH="$(curl -s -m 8 "http://127.0.0.1:$PORTAL_PORT/portal/health")"
OP="$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORTAL_PORT/portal/ring/outcome?s=x")"
CP="$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORTAL_PORT/portal/ring/counts")"
SW="$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORTAL_PORT/portal/sw.js")"
say "      ring-hook health: $(echo "$RH" | tr -d '\n' | cut -c1-120)"
say "      portal health $(echo "$PH" | tr -d '\n' | cut -c1-60) · outcome page without login $OP · counts without login $CP · sw.js $SW (302/302/200 expected)"
echo "$RH" | grep -q '"status": *"ok"' || restore "ring-hook health"
echo "$PH" | grep -q '"status": *"ok"' || restore "portal health"
{ [ "$OP" = 302 ] || [ "$OP" = 401 ]; } && { [ "$CP" = 302 ] || [ "$CP" = 401 ]; } && [ "$SW" = 200 ] || restore "route probes"
JR="$(journalctl -u ring-hook -u clinic-portal --since "$T0" --no-pager 2>/dev/null | grep -c -i 'Traceback\|ModuleNotFoundError\|ImportError')"
[ "$JR" = "0" ] || { journalctl -u ring-hook -u clinic-portal --since "$T0" --no-pager | grep -i -B2 -A6 'Traceback\|Error' | head -40; restore "journal: $JR error line(s) since the restart"; }
say "      journal since restart: clean"
say "[7/7] all green -- $KIT: DONE"
say "      backups: $BAK1 · $BAK2"
md5sum "$PD/ring_hook.py" "$PD/portal_push.py" "$PD/ring_outcome.py" "$PD/ring_common.py" "$PD/portal.py"
