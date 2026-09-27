#!/bin/bash
# install_S426_VITALS_ARCHIVE_IN.sh -- session 284, 27-Sep-2026 -- the July Vitals & Plan sheets exist only on the clinic
# PC. vitals_portal.py b234627a (S423) -> db170077 (full file) adds ONE doctor-only route, /portal/vitals/archive,
# through which the assistant carries the PC's plan_archive in from the owner's signed-in browser: strict folder and
# name patterns, %PDF only, never overwrites. Nothing on Drive, nothing in the repository. portal.py is NOT touched.
# Restarts clinic-portal. Proven on a scratch copy first; RED after placing = restore.
set -u
KIT="S426_VITALS_ARCHIVE_IN"; KDIR="$(cd "$(dirname "$0")" && pwd)"; VPY="${VPY:-/root/wa/venv/bin/python3}"; PD="${PD:-/root/portal}"
PORTAL_PORT="${PORTAL_PORT:-8099}"; FROM=b234627a456c0d1be0550f7c1b963dcc; TO=db170077dce3cd82b8c1f859b76763db
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }; say() { echo "$@"; }
cd "$KDIR" || exit 1
say "[1/6] kit gates"
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit"; exit 1; }
[ "$(m5 vitals_portal.py)" = "$TO" ] || { say "!! [1/6] vitals_portal.py not at its pin"; exit 1; }
say "      green"
say "[2/6] the live file"
V0="$(m5 "$PD/vitals_portal.py")"
[ "$V0" = "$TO" ] && { say "-- ALREADY INSTALLED. Nothing to do."; exit 0; }
[ "$V0" = "$FROM" ] || { say "!! [2/6] live vitals_portal.py is $V0, not the S423 bytes $FROM - nothing installed"; exit 1; }
say "      exact (S423)"
say "[3/6] scratch: py_compile + walk (no network)"
W="/tmp/s426_walk_$(date +%Y%m%d_%H%M%S)"; mkdir -p "$W/app" && \cp -p vitals_portal.py "$W/app/" || { say "!! [3/6] scratch copy failed"; exit 1; }
"$VPY" -B -m py_compile "$W/app/vitals_portal.py" || { say "!! [3/6] py_compile failed"; rm -rf "$W"; exit 1; }
WOUT="$( cd /tmp && timeout 120 "$VPY" -B "$KDIR/walk_s426.py" "$W/app" 2>&1 | tail -1 )"; rm -rf "$W"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [3/6] walk red: $WOUT - nothing installed"; exit 1; }
say "      $WOUT"
say "[4/6] backup + place"
BAK="$PD/vitals_portal.py.bak_S426_b234627a"
\cp -p "$PD/vitals_portal.py" "$BAK" || { say "!! [4/6] backup failed"; exit 1; }
restore() { say "!! RED after placing ($1) - restoring"; \cp -p "$BAK" "$PD/vitals_portal.py"; systemctl restart clinic-portal || true; sleep 4; say "   vitals_portal.py $(m5 "$PD/vitals_portal.py")"; exit 1; }
\cp vitals_portal.py "$PD/vitals_portal.py" && chmod 600 "$PD/vitals_portal.py" || restore "copy"
[ "$(m5 "$PD/vitals_portal.py")" = "$TO" ] || restore "placed bytes"
say "[5/6] restart clinic-portal, then the probes"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-portal || restore "restart"; sleep 5; systemctl is-active --quiet clinic-portal || restore "not active"
PH="$(curl -s -m 8 "http://127.0.0.1:$PORTAL_PORT/portal/health")"
A1="$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORTAL_PORT/portal/vitals/archive")"
A2="$(curl -s -o /dev/null -m 8 -w '%{http_code}' -X POST "http://127.0.0.1:$PORTAL_PORT/portal/vitals/archive")"
V1="$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORTAL_PORT/portal/vitals")"
say "      portal health $(echo "$PH" | tr -d '\n' | cut -c1-60) · archive GET $A1 · archive POST $A2 · /portal/vitals $V1 without login (302 each expected)"
echo "$PH" | grep -q '"status": *"ok"' || restore "portal health"
for c in "$A1" "$A2" "$V1"; do { [ "$c" = 302 ] || [ "$c" = 401 ] || [ "$c" = 403 ]; } || restore "a vitals route answered $c without login"; done
JR="$(journalctl -u clinic-portal --since "$T0" --no-pager 2>/dev/null | grep -c -i 'Traceback\|ModuleNotFoundError\|ImportError')"
[ "$JR" = "0" ] || { journalctl -u clinic-portal --since "$T0" --no-pager | grep -i -A6 'Traceback\|Error' | head -30; restore "journal: $JR error line(s)"; }
say "      journal since restart: clean"
say "[6/6] all green -- $KIT: DONE"
say "      backup: $BAK"
md5sum "$PD/vitals_portal.py" "$PD/portal.py"
