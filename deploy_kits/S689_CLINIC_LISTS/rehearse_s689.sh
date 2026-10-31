#!/bin/bash
# rehearse_s689.sh -- kit S689_CLINIC_LISTS. The installer on a MADE-UP server root, never the box:
#   bash rehearse_s689.sh <step> <work dir> <from root> <database copy>
#   steps: setup | dry | red | journalred | offon | install | again | stalelock | changed
# <from root> holds finance/... at this kit's FROM (the nightly code bundle's root/finance with S687's and S688's TO files over it)
# and portal/... (the bundle's root/portal); <database copy> is a COPY of finance.db (copied again into the made-up root).
# A stand-in answers 200 on /finance/healthz and /portal/health and 302 elsewhere; SYSTEMCTL and JOURNALCTL are 'true'.
# The install window is skipped (SKIP_WINDOW=1): the rehearsal may run at any hour. Each step prints what it saw.
set -u
STEP="$1"; W="$2"; B="$3"; D="$4"
KDIR="$(cd "$(dirname "$0")" && pwd)"
R="$W/root"; F="$R/finance"; P="$R/portal"; PORT="${PORT:-18689}"
export ROOT="$R" LOCK="$W/lock" OFFSW="$W/off/DOCTOR_AUTO_OFF" TMPW="$W/tmp" APY="${APY:-$(command -v python3)}" VPY="${VPY:-$(command -v python3)}"
export SYSTEMCTL=true JOURNALCTL=true FIN_PORT="$PORT" PPORT="$PORT" SKIP_WINDOW=1
mkdir -p "$W/tmp"
hz_on() {
  cat > "$W/fakehz.py" <<'EOF2'
import http.server, sys
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/finance/healthz", "/portal/health"):
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
        else:
            self.send_response(302); self.send_header("Location", "/portal"); self.end_headers()
    def log_message(self, *a):
        pass
http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
EOF2
  "$APY" "$W/fakehz.py" "$PORT" > /dev/null 2>&1 & HZ=$!; sleep 1
  echo "stand-in health: $(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:$PORT/finance/healthz) $(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:$PORT/portal/health)"
}
hz_off() { kill "$HZ" 2>/dev/null; }
pins() { printf 'finance_app.py=%s portal.py=%s clinic_lists.py=%s off=%s lock=%s\n' "$(md5sum "$F/finance_app.py" 2>/dev/null | cut -c1-8)" \
  "$(md5sum "$P/portal.py" 2>/dev/null | cut -c1-8)" "$(md5sum "$F/clinic_lists.py" 2>/dev/null | cut -c1-8)" \
  "$([ -e "$OFFSW" ] && echo present || echo absent)" "$([ -e "$LOCK" ] && echo held || echo free)"; }
case "$STEP" in
  setup)
    rm -rf "$R"; mkdir -p "$F" "$P"
    cp -rp "$B/finance/." "$F/"; cp -rp "$B/portal/." "$P/"; rm -f "$F"/*.db "$F"/*.db-* 2>/dev/null
    "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$D" "$F/finance.db"
    echo "setup: made-up root $R; $(pins)";;
  dry)
    hz_on; DRY=1 bash "$KDIR/install_S689_CLINIC_LISTS.sh"; echo "exit $? · $(pins)"; hz_off;;
  red)
    hz_on; REHEARSE_RED_AT=8 bash "$KDIR/install_S689_CLINIC_LISTS.sh"; echo "exit $? · $(pins)"; hz_off
    for f in "$F"/*.bak_S689_* "$P"/*.bak_S689_*; do echo "  $(basename "$f") $(md5sum "$f" | cut -c1-8)"; done;;
  journalred)
    printf '#!/bin/sh\necho "gunicorn[1]: clinic_lists NOT mounted: ImportError(rehearsal)"\n' > "$W/fakejournal"; chmod +x "$W/fakejournal"
    hz_on; JOURNALCTL="$W/fakejournal" bash "$KDIR/install_S689_CLINIC_LISTS.sh"; echo "exit $? · $(pins)"; hz_off;;
  install|again)
    hz_on; bash "$KDIR/install_S689_CLINIC_LISTS.sh"; echo "exit $? · $(pins)"; hz_off;;
  changed)
    cp -p "$B/finance/finance_app.py" "$F/finance_app.py"; cp -p "$B/portal/portal.py" "$P/portal.py"; rm -f "$F/clinic_lists.py"
    printf '\n# a change made on the box after the kit was built\n' >> "$P/portal.py"
    hz_on; bash "$KDIR/install_S689_CLINIC_LISTS.sh"; echo "exit $? · $(pins)"; hz_off
    cp -p "$B/portal/portal.py" "$P/portal.py";;
  offon)               # DOCTOR_AUTO_OFF already set by someone else: the install leaves it in place
    mkdir -p "$(dirname "$OFFSW")"; echo "someone else's switch" > "$OFFSW"
    hz_on; bash "$KDIR/install_S689_CLINIC_LISTS.sh"; echo "exit $? · $(pins) · switch text: $(cat "$OFFSW" 2>/dev/null)"; hz_off
    rm -f "$OFFSW";;
  stalelock)           # a run killed outright left its lock and switch: the next run (here: ALREADY INSTALLED) clears both
    mkdir -p "$LOCK" "$(dirname "$OFFSW")"; echo "S689_CLINIC_LISTS 999999 2026-11-01 00:00:00" > "$LOCK/owner"; echo "S689_CLINIC_LISTS killed run" > "$OFFSW"
    hz_on; bash "$KDIR/install_S689_CLINIC_LISTS.sh"; echo "exit $? · $(pins)"; hz_off;;
  *) echo "steps: setup | dry | red | journalred | offon | install | again | stalelock | changed"; exit 2;;
esac
