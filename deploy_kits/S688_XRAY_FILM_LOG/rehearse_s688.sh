#!/bin/bash
# rehearse_s688.sh -- kit S688_XRAY_FILM_LOG. The installer on a MADE-UP server root, never the box:
#   bash rehearse_s688.sh <step> <work dir> <from root> <database copy>
#   steps: setup | dry | red | journalred | panelred | install | again | dmap | changed
# <from root> holds finance/... at this kit's FROM (the nightly code bundle's root/finance with S687's four TO files over it);
# <database copy> is a COPY of finance.db (it is copied again into the made-up root). A stand-in healthz answers 200 on
# /finance/healthz and 302 elsewhere; SYSTEMCTL and JOURNALCTL are 'true'. K687 (env) names S687's kit folder (its walk is run
# on the files); DUTY_MAP (env) the duty map. Each step prints what it saw; the work dir is the rehearsal's only output.
set -u
STEP="$1"; W="$2"; B="$3"; D="$4"
KDIR="$(cd "$(dirname "$0")" && pwd)"
R="$W/root"; F="$R/finance"; PORT="${PORT:-18688}"
export ROOT="$R" LOCK="$W/lock" TMPW="$W/tmp" APY="${APY:-$(command -v python3)}" VPY="${VPY:-$(command -v python3)}" SYSTEMCTL=true JOURNALCTL=true FIN_PORT="$PORT"
export DUTY_MAP="${DUTY_MAP:-${DUTY_MAP_JSON:-/root/deploy/repo/claude_code_briefs/DUTY_MAP.json}}"
export K687="${K687:-/root/deploy/repo/deploy_kits/S687_DARPAN_MONTH_JOBS}"
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
panels() {     # the saved panels of shavez and reception -- their whole lines and 'removed' lists -- as one line of JSON
  "$APY" -c "import json,sqlite3,sys; c=sqlite3.connect(sys.argv[1]); print(json.dumps({k: [json.loads(d)['lines'], json.loads(d).get('removed')] for k, d in c.execute(\"SELECT person, doc FROM aaj_cfg WHERE person IN ('shavez','reception') ORDER BY person\")}, sort_keys=True))" "$F/finance.db"
}
pins() { for n in finance_app.py aaj_duties.json aaj_seed.py xray_film.py month_jobs.py; do printf '%s=%s ' "$n" "$(md5sum "$F/$n" 2>/dev/null | cut -c1-8)"; done; echo; }
case "$STEP" in
  setup)
    rm -rf "$R"; mkdir -p "$F"
    cp -rp "$B/finance/." "$F/"; rm -f "$F"/*.db "$F"/*.db-* 2>/dev/null
    "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$D" "$F/finance.db"
    echo "setup: made-up root $R; $(pins)";;
  dry)
    hz_on; DRY=1 SKIP_WINDOW=1 bash "$KDIR/install_S688_XRAY_FILM_LOG.sh"; echo "exit $? · $(pins)"; hz_off;;
  red)
    hz_on; REHEARSE_RED_AT=8 bash "$KDIR/install_S688_XRAY_FILM_LOG.sh"; echo "exit $? · $(pins)"; hz_off
    for f in "$F"/*.bak_S688_*; do echo "  $(stat -c %a "$f") $(basename "$f")"; done;;
  journalred)          # the live process's journal names the module: red after placing, everything back
    printf '#!/bin/sh\necho "gunicorn[1]: xray_film NOT mounted: ImportError(rehearsal)"\n' > "$W/fakejournal"; chmod +x "$W/fakejournal"
    hz_on; JOURNALCTL="$W/fakejournal" bash "$KDIR/install_S688_XRAY_FILM_LOG.sh"; echo "exit $? · $(pins)"; hz_off;;
  panelred)            # saved panels for shavez and reception: the data step appends its lines, a red at [8/9] takes exactly those off
    "$APY" - "$F" <<'EOF3'
import json, os, sqlite3, sys
fin = sys.argv[1]
sys.path.insert(0, fin)
import aaj_seed
con = sqlite3.connect(os.path.join(fin, "finance.db"))
con.execute("CREATE TABLE IF NOT EXISTS aaj_cfg (person TEXT PRIMARY KEY, doc TEXT NOT NULL, edited_at TEXT NOT NULL, edited_by TEXT NOT NULL)")
for k in ("shavez", "reception"):
    p = [x for x in aaj_seed.PEOPLE if x["key"] == k][0]
    doc = dict(on=True, note="", first_on=None, removed=[],
               lines=[dict(id=l["id"], hi=l["hi"], en=l.get("en", ""), when=l["when"], on=l["on"]) for l in p["lines"]])
    con.execute("INSERT OR REPLACE INTO aaj_cfg VALUES (?,?,?,?)", (k, json.dumps(doc), "2026-10-30T10:00:00", "manoj"))
con.commit()
EOF3
    P0="$(panels)"; echo "saved panels before: $(echo "$P0" | md5sum | cut -c1-8); the retired weekly line on Reception's: $(echo "$P0" | grep -c week_film_stock)"
    hz_on; REHEARSE_RED_AT=8 bash "$KDIR/install_S688_XRAY_FILM_LOG.sh"; echo "exit $? · $(pins)"; hz_off
    P1="$(panels)"
    [ "$P0" = "$P1" ] && echo "panels after the red: EXACTLY as before (the added lines off, the retired line back in its place)" || echo "panels after the red: DIFFERENT -- $P1"
    "$APY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute(\"DELETE FROM aaj_cfg WHERE person IN ('shavez','reception')\"); c.commit()" "$F/finance.db"
    echo "the made-up panels taken out again";;
  install|again)
    hz_on; bash "$KDIR/install_S688_XRAY_FILM_LOG.sh"; echo "exit $? · $(pins)"; hz_off;;
  dmap)                # the duty map changed after the kit was built (a git pull): refused, nothing written
    cp -p "$DUTY_MAP" "$W/dmap_changed.json"; printf ' ' >> "$W/dmap_changed.json"
    hz_on; DUTY_MAP="$W/dmap_changed.json" bash "$KDIR/install_S688_XRAY_FILM_LOG.sh"; echo "exit $? · $(pins)"; hz_off;;
  changed)             # a live file changed after the kit was built: refused, nothing written
    for n in finance_app.py aaj_duties.json aaj_seed.py; do cp -p "$B/finance/$n" "$F/$n"; done; rm -f "$F/xray_film.py"
    printf '\n# a change made on the box after the kit was built\n' >> "$F/aaj_seed.py"
    hz_on; bash "$KDIR/install_S688_XRAY_FILM_LOG.sh"; echo "exit $? · $(pins)"; hz_off;;
  *) echo "unknown step $STEP"; exit 2;;
esac
