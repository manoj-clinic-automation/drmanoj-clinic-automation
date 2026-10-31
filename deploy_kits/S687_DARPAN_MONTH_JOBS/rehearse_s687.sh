#!/bin/bash
# rehearse_s687.sh -- kit S687_DARPAN_MONTH_JOBS. The installer on a MADE-UP server root, never the box:
#   bash rehearse_s687.sh <step> <work dir> <bundle root> <database copy>
#   steps: setup | dry | red | journalred | install | again | dmap | changed
# <bundle root> holds finance/... (the nightly code bundle's root/); <database copy> is a COPY of finance.db (it is copied
# again into the made-up root). A stand-in healthz answers 200 on /finance/healthz and 302 elsewhere; SYSTEMCTL and
# JOURNALCTL are 'true'. Each step prints what it saw; the work dir is the rehearsal's only output.
set -u
STEP="$1"; W="$2"; B="$3"; D="$4"
KDIR="$(cd "$(dirname "$0")" && pwd)"
R="$W/root"; F="$R/finance"; PORT="${PORT:-18687}"
export ROOT="$R" LOCK="$W/lock" TMPW="$W/tmp" APY="${APY:-$(command -v python3)}" VPY="${VPY:-$(command -v python3)}" SYSTEMCTL=true JOURNALCTL=true FIN_PORT="$PORT"
export DUTY_MAP="${DUTY_MAP:-${DUTY_MAP_JSON:-/root/deploy/repo/claude_code_briefs/DUTY_MAP.json}}"
mkdir -p "$W/tmp"
hz_on() {      # the stand-in healthz, started inside this same call (a process left behind by an earlier call is gone)
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
  echo "stand-in healthz: $(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:$PORT/finance/healthz)"
}
hz_off() { kill "$HZ" 2>/dev/null; }
pins() { for n in finance_app.py aaj_duties.json aaj_seed.py month_jobs.py; do printf '%s=%s ' "$n" "$(md5sum "$F/$n" 2>/dev/null | cut -c1-8)"; done; echo; }
case "$STEP" in
  setup)
    rm -rf "$R"; mkdir -p "$F"
    cp -rp "$B/finance/." "$F/"; rm -f "$F"/*.db "$F"/*.db-* 2>/dev/null
    "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$D" "$F/finance.db"
    echo "setup: made-up root $R; $(pins)";;
  dry)
    hz_on; DRY=1 SKIP_WINDOW=1 bash "$KDIR/install_S687_DARPAN_MONTH_JOBS.sh"; echo "exit $? · $(pins)"; hz_off;;
  red)
    hz_on; REHEARSE_RED_AT=8 bash "$KDIR/install_S687_DARPAN_MONTH_JOBS.sh"; echo "exit $? · $(pins)"; hz_off
    for f in "$F"/*.bak_S687_*; do echo "  $(stat -c %a "$f") $(basename "$f")"; done;;
  journalred)          # the live process's journal names the module: red after placing, everything back
    printf '#!/bin/sh\necho "gunicorn[1]: month_jobs NOT mounted: ImportError(rehearsal)"\n' > "$W/fakejournal"; chmod +x "$W/fakejournal"
    hz_on; JOURNALCTL="$W/fakejournal" bash "$KDIR/install_S687_DARPAN_MONTH_JOBS.sh"; echo "exit $? · $(pins)"; hz_off;;
  install|again)
    hz_on; bash "$KDIR/install_S687_DARPAN_MONTH_JOBS.sh"; echo "exit $? · $(pins)"; hz_off;;
  dmap)                # the duty map changed after the kit was built (a git pull): refused, nothing written
    cp -p "$DUTY_MAP" "$W/dmap_changed.json"; printf ' ' >> "$W/dmap_changed.json"
    hz_on; DUTY_MAP="$W/dmap_changed.json" bash "$KDIR/install_S687_DARPAN_MONTH_JOBS.sh"; echo "exit $? · $(pins)"; hz_off;;
  changed)
    for n in finance_app.py aaj_duties.json aaj_seed.py; do cp -p "$B/finance/$n" "$F/$n"; done; rm -f "$F/month_jobs.py"
    printf '\n# a change made on the box after the kit was built\n' >> "$F/aaj_seed.py"
    hz_on; bash "$KDIR/install_S687_DARPAN_MONTH_JOBS.sh"; echo "exit $? · $(pins)"; hz_off;;
  *) echo "unknown step $STEP"; exit 2;;
esac
