#!/bin/bash
# install_S423_VITALS_VPS.sh -- session 284, 27-Sep-2026 -- F-598 / D589: Vitals & Plan on the server.
# Places vitals_portal.py (NEW) + the PC's own engine and font (from the repository's clinic_writer/, pinned) in
# /root/portal, the PC's page in /root/wa/vitals (0700, PHI store), and three anchored edits to portal.py (read
# whole at S284). Restarts clinic-portal. Proven on scratch copies first; RED after placing = restore.
set -u
KIT="S423_VITALS_VPS"; KDIR="$(cd "$(dirname "$0")" && pwd)"; VPY="${VPY:-/root/wa/venv/bin/python3}"; PD="${PD:-/root/portal}"
REPO="${REPO:-/root/deploy/repo}"; VD="${VD:-/root/wa/vitals}"; PORTAL_PORT="${PORTAL_PORT:-8099}"
P_FROM=912a1d8299c01b1b11f4ca81bef52482; P_TO=626838cdf624446f90ac3061a79b6523; VP_TO=b234627a456c0d1be0550f7c1b963dcc
CW_PIN=0ad6d9f449addd03de40b0bfbacca659; PAGE_PIN=fcedae303b620f3e5199f4b1e4766510; FONT_PIN=f4ae6809bd8c31573370e8da72514012
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }; say() { echo "$@"; }
cd "$KDIR" || exit 1
say "[1/7] kit gates"
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit"; exit 1; }
[ "$(m5 vitals_portal.py)" = "$VP_TO" ] || { say "!! [1/7] vitals_portal.py not at its pin"; exit 1; }
CWS="$REPO/clinic_writer"
[ "$(m5 "$CWS/clinic_writer.py")" = "$CW_PIN" ] && [ "$(m5 "$CWS/vitals_page.html")" = "$PAGE_PIN" ] && [ "$(m5 "$CWS/NotoSansDevanagari-Regular.ttf")" = "$FONT_PIN" ] || { say "!! [1/7] the repository's clinic_writer/ files are not the PC's pinned bytes - nothing installed"; exit 1; }
say "      green (engine, page and font = the clinic PC's own bytes)"
if [ "$(m5 "$PD/portal.py")" = "$P_TO" ] && [ "$(m5 "$PD/vitals_portal.py")" = "$VP_TO" ]; then say "-- ALREADY INSTALLED. Nothing to do."; exit 0; fi
say "[2/7] live pins"
[ "$(m5 "$PD/portal.py")" = "$P_FROM" ] || { say "!! [2/7] live portal.py is $(m5 "$PD/portal.py"), not the bytes read whole at S284 - nothing installed"; exit 1; }
for f in vitals_portal.py clinic_writer.py NotoSansDevanagari-Regular.ttf; do [ -e "$PD/$f" ] && { say "!! [2/7] $PD/$f already exists - nothing installed"; exit 1; }; done
say "      exact"
say "[3/7] reportlab in the portal's python (the engine's PDFs need it)"
if ! "$VPY" -c "import reportlab" 2>/dev/null; then say "      not installed -- installing into the venv"; "$VPY" -m pip install -q reportlab 2>&1 | tail -2; fi
"$VPY" -c "import reportlab; print('      reportlab', reportlab.Version)" || { say "!! [3/7] reportlab could not be installed - nothing installed"; exit 1; }
say "[4/7] scratch: patch a copy of portal.py + the walk (no network, fake patient stores)"
W="/tmp/s423_walk_$(date +%Y%m%d_%H%M%S)"; mkdir -p "$W/app" && \cp -p vitals_portal.py "$CWS/clinic_writer.py" "$CWS/NotoSansDevanagari-Regular.ttf" "$W/app/" && \cp -p "$PD/portal.py" "$W/portal.py" || { say "!! [4/7] scratch copy failed"; rm -rf "$W"; exit 1; }
"$VPY" -B apply_s423_portal.py "$W/portal.py" >/dev/null && [ "$(m5 "$W/portal.py")" = "$P_TO" ] || { say "!! [4/7] the patched copy is not the predicted bytes - nothing installed"; rm -rf "$W"; exit 1; }
"$VPY" -B -m py_compile "$W/portal.py" "$W/app/vitals_portal.py" || { say "!! [4/7] py_compile failed"; rm -rf "$W"; exit 1; }
WOUT="$( cd /tmp && timeout 150 "$VPY" -B "$KDIR/walk_s423.py" "$W/app" "$CWS/vitals_page.html" "$W/portal.py" 2>&1 | tail -1 )"; rm -rf "$W"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [4/7] walk red: $WOUT - nothing installed"; exit 1; }
say "      $WOUT"
say "[5/7] backup + place"
BAK="$PD/portal.py.bak_S423_912a1d82"; \cp -p "$PD/portal.py" "$BAK" || { say "!! [5/7] backup failed"; exit 1; }
restore() { say "!! RED after placing ($1) - restoring"; \cp -p "$BAK" "$PD/portal.py"; rm -f "$PD/vitals_portal.py" "$PD/clinic_writer.py" "$PD/NotoSansDevanagari-Regular.ttf"; systemctl restart clinic-portal || true; sleep 4; say "   portal.py $(m5 "$PD/portal.py")"; exit 1; }
mkdir -p "$VD" && chmod 700 "$VD" || restore "mkdir $VD"
[ -e "$VD/vitals_page.html" ] || { \cp "$CWS/vitals_page.html" "$VD/vitals_page.html" && chmod 600 "$VD/vitals_page.html"; } || restore "page"
\cp vitals_portal.py "$PD/vitals_portal.py" && \cp "$CWS/clinic_writer.py" "$PD/clinic_writer.py" && \cp "$CWS/NotoSansDevanagari-Regular.ttf" "$PD/NotoSansDevanagari-Regular.ttf" || restore "copy"
"$VPY" -B apply_s423_portal.py "$PD/portal.py" | sed 's/^/      /'
[ "$(m5 "$PD/portal.py")" = "$P_TO" ] && [ "$(m5 "$PD/vitals_portal.py")" = "$VP_TO" ] && [ "$(m5 "$PD/clinic_writer.py")" = "$CW_PIN" ] || restore "placed bytes"
say "[6/7] restart clinic-portal, then the probes"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-portal || restore "restart"; sleep 5; systemctl is-active --quiet clinic-portal || restore "not active"
PH="$(curl -s -m 8 "http://127.0.0.1:$PORTAL_PORT/portal/health")"
V1="$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORTAL_PORT/portal/vitals")"
V2="$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORTAL_PORT/portal/vitals/lookup?clinic_id=1")"
V3="$(curl -s -o /dev/null -m 8 -w '%{http_code}' -X POST "http://127.0.0.1:$PORTAL_PORT/portal/vitals/save")"
say "      portal health $(echo "$PH" | tr -d '\n' | cut -c1-60) · /portal/vitals $V1 · lookup $V2 · save $V3 without login (302 each expected)"
echo "$PH" | grep -q '"status": *"ok"' || restore "portal health"
for c in "$V1" "$V2" "$V3"; do { [ "$c" = 302 ] || [ "$c" = 401 ] || [ "$c" = 403 ]; } || restore "a vitals route answered $c without login"; done
JR="$(journalctl -u clinic-portal --since "$T0" --no-pager 2>/dev/null | grep -c -i 'Traceback\|ModuleNotFoundError\|ImportError\|failed to load')"
[ "$JR" = 0 ] || { journalctl -u clinic-portal --since "$T0" --no-pager | grep -i -A6 'Traceback\|Error' | head -30; restore "journal: $JR error line(s)"; }
say "      journal since restart: clean"
say "[7/7] all green -- $KIT: DONE   (the 14 + 14 July records are carried from the PC by the assistant, once, next)"
say "      backup: $BAK"
md5sum "$PD/portal.py" "$PD/vitals_portal.py" "$PD/clinic_writer.py" "$VD/vitals_page.html"
