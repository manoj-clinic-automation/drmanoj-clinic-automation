#!/bin/bash
# rehearse_s682.sh -- kit S682_IPD_IMPLANT_BILLS. The installer on a MADE-UP server root, never the box:
#   bash rehearse_s682.sh <step> <work dir> <from root> <database copy>
#   steps: setup | dry | red | install | again | changed
# <from root> holds finance/... at this kit's FROM (the nightly code bundle's root/finance with S689's and S691's TO files over it);
# <database copy> is a COPY of finance.db (copied again into the made-up root). A stand-in answers 200 on /finance/healthz and 302
# elsewhere; SYSTEMCTL and JOURNALCTL are 'true'. The install window is skipped (SKIP_WINDOW=1).
set -u
STEP="$1"; W="$2"; B="$3"; D="$4"
KDIR="$(cd "$(dirname "$0")" && pwd)"
R="$W/root"; F="$R/finance"; PORT="${PORT:-18682}"
export ROOT="$R" LOCK="$W/lock" OFFSW="$W/off/DOCTOR_AUTO_OFF" TMPW="$W/tmp" APY="${APY:-$(command -v python3)}" VPY="${VPY:-$(command -v python3)}"
export SYSTEMCTL=true JOURNALCTL=true FIN_PORT="$PORT" SKIP_WINDOW=1
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
pins() { printf 'surgery_cases=%s off=%s lock=%s dbbak=%s\n' "$(md5sum "$F/surgery_cases.py" 2>/dev/null | cut -c1-8)" \
  "$([ -e "$OFFSW" ] && echo present || echo absent)" "$([ -e "$LOCK" ] && echo held || echo free)" "$(ls "$F"/finance.db.bak_S682_* 2>/dev/null | wc -l)"; }
I="$KDIR/install_S682_IPD_IMPLANT_BILLS.sh"
case "$STEP" in
  setup)
    rm -rf "$R"; mkdir -p "$F"
    cp -rp "$B/finance/." "$F/"; rm -f "$F"/*.db "$F"/*.db-* "$F"/*.bak_* 2>/dev/null
    "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$D" "$F/finance.db"
    echo "setup: made-up root $R; $(pins)";;
  dry)
    hz_on; DRY=1 bash "$I"; echo "exit $? · $(pins)"; hz_off;;
  red)
    hz_on; REHEARSE_RED_AT=8 bash "$I"; echo "exit $? · $(pins)"; hz_off;;
  install|again)
    hz_on; bash "$I"; echo "exit $? · $(pins)"; hz_off;;
  changed)
    cp -p "$B/finance/surgery_cases.py" "$F/surgery_cases.py"
    printf '\n# a change made on the box after the kit was built\n' >> "$F/surgery_cases.py"
    hz_on; bash "$I"; echo "exit $? · $(pins)"; hz_off
    cp -p "$B/finance/surgery_cases.py" "$F/surgery_cases.py";;
  *) echo "steps: setup | dry | red | install | again | changed"; exit 2;;
esac
