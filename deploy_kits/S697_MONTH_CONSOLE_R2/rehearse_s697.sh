#!/bin/bash
# rehearse_s697.sh -- kit S697_MONTH_CONSOLE_R2. The installer on a MADE-UP server root, never the box:
#   bash rehearse_s697.sh <step> <work dir> <from root> <database copy>
#   steps: setup | dry | red | journalred | offon | install | again | stalelock | changed | half | corrupt
# <from root> holds finance/... at this kit's FROM (the live box's five files: S696's owner_console.py, month_read.py,
# month_page.html, the bundle's owner_console.html, S691's xray_film.py); <database copy> is a COPY of finance.db (copied again
# into the made-up root). A stand-in answers 200 on /finance/healthz and 302 elsewhere; SYSTEMCTL and JOURNALCTL are 'true'.
# The install window is skipped (SKIP_WINDOW=1). Each step prints what it saw.
set -u
STEP="$1"; W="$2"; B="$3"; D="$4"
KDIR="$(cd "$(dirname "$0")" && pwd)"
R="$W/root"; F="$R/finance"; PORT="${PORT:-18697}"
export ROOT="$R" LOCK="$W/lock" OFFSW="$W/off/DOCTOR_AUTO_OFF" TMPW="$W/tmp" APY="${APY:-$(command -v python3)}" VPY="${VPY:-$(command -v python3)}"
export SYSTEMCTL=true JOURNALCTL=true FIN_PORT="$PORT" SKIP_WINDOW=1 SNAPF="$W/root/finance/console_reading.dat"
mkdir -p "$W/tmp"
ALL="owner_console.py owner_console.html month_read.py month_page.html xray_film.py"
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
pins() { for n in $ALL; do printf '%s=%s ' "${n%%.*}" "$(md5sum "$F/$n" 2>/dev/null | cut -c1-8)"; done
  printf 'snap=%s off=%s lock=%s\n' "$([ -e "$SNAPF" ] && echo present || echo absent)" "$([ -e "$OFFSW" ] && echo present || echo absent)" "$([ -e "$LOCK" ] && echo held || echo free)"; }
I="$KDIR/install_S697_MONTH_CONSOLE_R2.sh"
case "$STEP" in
  setup)
    rm -rf "$R"; mkdir -p "$F"
    cp -rp "$B/finance/." "$F/"; rm -f "$F"/*.db "$F"/*.db-* "$F"/console_reading.dat* "$F"/*.bak_* 2>/dev/null
    "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$D" "$F/finance.db"
    echo "setup: made-up root $R; $(pins)";;
  dry)
    hz_on; DRY=1 bash "$I"; echo "exit $? · $(pins)"; hz_off;;
  red)
    hz_on; REHEARSE_RED_AT=7 bash "$I"; echo "exit $? · $(pins)"; hz_off
    for f in "$F"/*.bak_S697_*; do echo "  $(basename "$f") $(md5sum "$f" | cut -c1-8)"; done;;
  journalred)
    printf '#!/bin/sh\necho "Starting gunicorn 21.2.0"\necho "gunicorn[1]: owner_console NOT mounted: ImportError(rehearsal)"\n' > "$W/fakejournal"; chmod +x "$W/fakejournal"
    hz_on; JOURNALCTL="$W/fakejournal" bash "$I"; echo "exit $? · $(pins)"; hz_off;;
  oldmaster)           # S375's lesson: the OLD master's shutdown traceback before the new 'Starting gunicorn' line is not this kit's red
    printf '#!/bin/sh\necho "--- Logging error ---"\necho "Traceback (most recent call last): reentrant call (the old master)"\necho "Starting gunicorn 21.2.0"\necho "Listening at: http://127.0.0.1:8106"\necho "Booting worker with pid: 1"\n' > "$W/fakejournal"; chmod +x "$W/fakejournal"
    hz_on; JOURNALCTL="$W/fakejournal" bash "$I"; echo "exit $? · $(pins)"; hz_off;;
  install|again)
    hz_on; bash "$I"; echo "exit $? · $(pins)"; hz_off;;
  changed)
    for n in $ALL; do cp -p "$B/finance/$n" "$F/$n"; done
    printf '\n# a change made on the box after the kit was built\n' >> "$F/month_read.py"
    hz_on; bash "$I"; echo "exit $? · $(pins)"; hz_off
    cp -p "$B/finance/month_read.py" "$F/month_read.py";;
  half)                # two of the five already the kit's, the rest not: HALF PLACED, nothing done
    for n in $ALL; do cp -p "$B/finance/$n" "$F/$n"; done; cp -p "$KDIR/month_read.py" "$KDIR/month_page.html" "$F/"
    hz_on; bash "$I"; echo "exit $? · $(pins)"; hz_off
    cp -p "$B/finance/month_read.py" "$B/finance/month_page.html" "$F/";;
  corrupt)             # a kit file changed after SUMS.md5: the gate refuses
    cp -rp "$KDIR" "$W/badkit"; printf '\n' >> "$W/badkit/month_read.py"
    hz_on; bash "$W/badkit/install_S697_MONTH_CONSOLE_R2.sh"; echo "exit $? · $(pins)"; hz_off; rm -rf "$W/badkit";;
  offon)
    mkdir -p "$(dirname "$OFFSW")"; echo "someone else's switch" > "$OFFSW"
    hz_on; bash "$I"; echo "exit $? · $(pins) · switch text: $(cat "$OFFSW" 2>/dev/null)"; hz_off
    rm -f "$OFFSW";;
  stalelock)
    mkdir -p "$LOCK" "$(dirname "$OFFSW")"; echo "S697_MONTH_CONSOLE_R2 999999 2026-11-01 00:00:00" > "$LOCK/owner"; echo "S697_MONTH_CONSOLE_R2 killed run" > "$OFFSW"
    hz_on; bash "$I"; echo "exit $? · $(pins)"; hz_off;;
  *) echo "steps: setup | dry | red | journalred | oldmaster | offon | install | again | stalelock | changed | half | corrupt"; exit 2;;
esac
