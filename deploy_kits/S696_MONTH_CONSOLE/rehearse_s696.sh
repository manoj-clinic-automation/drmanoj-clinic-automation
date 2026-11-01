#!/bin/bash
# rehearse_s696.sh -- kit S696_MONTH_CONSOLE. The installer on a MADE-UP server root, never the box:
#   bash rehearse_s696.sh <step> <work dir> <from root> <database copy>
#   steps: setup | dry | red | journalred | offon | install | again | stalelock | changed | half | corrupt
# <from root> holds finance/... at this kit's FROM (the nightly code bundle's root/finance with S691's TO files over it);
# <database copy> is a COPY of finance.db (copied again into the made-up root). A stand-in answers 200 on /finance/healthz and 302
# elsewhere; SYSTEMCTL and JOURNALCTL are 'true'. The install window is skipped (SKIP_WINDOW=1). Each step prints what it saw.
# PYTHONPATH may carry a flask stand-in where flask is not installed (the VM); on the box it is empty.
set -u
STEP="$1"; W="$2"; B="$3"; D="$4"
KDIR="$(cd "$(dirname "$0")" && pwd)"
R="$W/root"; F="$R/finance"; PORT="${PORT:-18696}"
export ROOT="$R" LOCK="$W/lock" OFFSW="$W/off/DOCTOR_AUTO_OFF" TMPW="$W/tmp" APY="${APY:-$(command -v python3)}" VPY="${VPY:-$(command -v python3)}"
export SYSTEMCTL=true JOURNALCTL=true FIN_PORT="$PORT" SKIP_WINDOW=1 SNAPF="$W/root/finance/console_reading.dat"
mkdir -p "$W/tmp"
hz_on() {
  cat > "$W/fakehz.py" <<'EOF2'
import http.server, sys
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/finance/healthz":
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
        else:
            self.send_response(302); self.send_header("Location", "/portal"); self.end_headers()
    def log_message(self, *a):
        pass
http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
EOF2
  "$APY" "$W/fakehz.py" "$PORT" > /dev/null 2>&1 & HZ=$!; sleep 1
  echo "stand-in health: $(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:$PORT/finance/healthz)"
}
hz_off() { kill "$HZ" 2>/dev/null; }
pins() { printf 'owner_console=%s month_read=%s month_page=%s snap=%s off=%s lock=%s\n' "$(md5sum "$F/owner_console.py" 2>/dev/null | cut -c1-8)" \
  "$([ -e "$F/month_read.py" ] && md5sum "$F/month_read.py" | cut -c1-8 || echo absent)" "$([ -e "$F/month_page.html" ] && md5sum "$F/month_page.html" | cut -c1-8 || echo absent)" \
  "$([ -e "$SNAPF" ] && echo present || echo absent)" "$([ -e "$OFFSW" ] && echo present || echo absent)" "$([ -e "$LOCK" ] && echo held || echo free)"; }
I="$KDIR/install_S696_MONTH_CONSOLE.sh"
case "$STEP" in
  setup)
    rm -rf "$R"; mkdir -p "$F"
    cp -rp "$B/finance/." "$F/"; rm -f "$F"/*.db "$F"/*.db-* "$F"/month_read.py "$F"/month_page.html "$F"/console_reading.dat* 2>/dev/null
    "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$D" "$F/finance.db"
    echo "setup: made-up root $R; $(pins)";;
  dry)
    hz_on; DRY=1 bash "$I"; echo "exit $? · $(pins)"; hz_off;;
  red)
    hz_on; REHEARSE_RED_AT=7 bash "$I"; echo "exit $? · $(pins)"; hz_off
    for f in "$F"/*.bak_S696_*; do echo "  $(basename "$f") $(md5sum "$f" | cut -c1-8)"; done;;
  journalred)
    printf '#!/bin/sh\necho "gunicorn[1]: owner_console NOT mounted: ImportError(rehearsal)"\n' > "$W/fakejournal"; chmod +x "$W/fakejournal"
    hz_on; JOURNALCTL="$W/fakejournal" bash "$I"; echo "exit $? · $(pins)"; hz_off;;
  install|again)
    hz_on; bash "$I"; echo "exit $? · $(pins)"; hz_off;;
  changed)
    cp -p "$B/finance/owner_console.py" "$F/owner_console.py"; rm -f "$F/month_read.py" "$F/month_page.html"
    printf '\n# a change made on the box after the kit was built\n' >> "$F/owner_console.py"
    hz_on; bash "$I"; echo "exit $? · $(pins)"; hz_off
    cp -p "$B/finance/owner_console.py" "$F/owner_console.py";;
  half)                # the two new files already there, owner_console.py not: HALF PLACED, nothing done
    cp -p "$B/finance/owner_console.py" "$F/owner_console.py"; cp -p "$KDIR/month_read.py" "$KDIR/month_page.html" "$F/"
    hz_on; bash "$I"; echo "exit $? · $(pins)"; hz_off
    rm -f "$F/month_read.py" "$F/month_page.html";;
  corrupt)             # a kit file changed after SUMS.md5: the gate refuses
    cp -rp "$KDIR" "$W/badkit"; printf '\n' >> "$W/badkit/month_read.py"
    hz_on; bash "$W/badkit/install_S696_MONTH_CONSOLE.sh"; echo "exit $? · $(pins)"; hz_off; rm -rf "$W/badkit";;
  offon)
    mkdir -p "$(dirname "$OFFSW")"; echo "someone else's switch" > "$OFFSW"
    hz_on; bash "$I"; echo "exit $? · $(pins) · switch text: $(cat "$OFFSW" 2>/dev/null)"; hz_off
    rm -f "$OFFSW";;
  stalelock)
    mkdir -p "$LOCK" "$(dirname "$OFFSW")"; echo "S696_MONTH_CONSOLE 999999 2026-11-01 00:00:00" > "$LOCK/owner"; echo "S696_MONTH_CONSOLE killed run" > "$OFFSW"
    hz_on; bash "$I"; echo "exit $? · $(pins)"; hz_off;;
  *) echo "steps: setup | dry | red | journalred | offon | install | again | stalelock | changed | half | corrupt"; exit 2;;
esac
