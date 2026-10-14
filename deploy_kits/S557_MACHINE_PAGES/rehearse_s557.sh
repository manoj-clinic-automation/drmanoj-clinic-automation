#!/bin/bash
# rehearse_s557.sh -- the S557 installer rehearsed on a made-up root under /tmp/s557dev/root (BUILD_NORM_v1 s3, S555's shape).
# A copy of the app's files and of its database (SQLite's backup API) are put there; every S557_* setting points there; the
# restart is `true` and the answers come from a stand-in (a small python3 server on a free port: /healthz 200, /desk 302 --
# the login gate, as the live app answers a plain request). Nothing live is placed or restarted.
# Outcomes: 1 green (the additive tables and column made on the made-up copy); 2 ALREADY INSTALLED; 3 a forced red after
# placing restores; 4 /desk not answering (404) restores; 5 /desk answering 200 (a login gate open) restores -- 302 only.
# Run as root on the VPS: bash rehearse_s557.sh            (the made-up root is removed at the end; KEEP=1 keeps it)
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT=/tmp/s557dev/root
LIVE_APP=/root/assetapp
LIVE_SHARED=/root/shared
EDITED="sorting_desk.py asset_register.py"
COPY="sorting_desk.py asset_register.py clinic_papers.py claude_reader.py claude_reread.py"
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1"; }
base(){ echo "${1%.py}"; }
fail(){ echo "REHEARSAL RED: $*"; [ -n "${HPID:-}" ] && kill "$HPID" 2>/dev/null; exit 1; }
at_from(){ for f in $EDITED; do [ "$(md5 "$ROOT/app/$f")" = "$(pin PIN_FROM_$(base "$f").txt)" ] || return 1; done; [ ! -e "$ROOT/app/asset_machine.py" ]; }
at_to(){ for f in $EDITED asset_machine.py; do [ "$(md5 "$ROOT/app/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] || return 1; done; return 0; }
reset_root(){ for f in $EDITED; do cp "$ROOT/orig/$f" "$ROOT/app/$f"; done; rm -f "$ROOT/app/"*.bak_S557_* "$ROOT/app/asset_machine.py" "$ROOT/app/asset_machine.py."*; }
tables(){ python3 -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); t={r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")}; s={r[1] for r in c.execute('PRAGMA table_info(service_logs)')}; print('asset_part' in t, 'asset_cover' in t, 'bill_id' in s)" "$1"; }

rm -rf "$ROOT"; mkdir -p "$ROOT/app/uploads" "$ROOT/shared" "$ROOT/orig" "$ROOT/web" || fail "no made-up root"
SVC_ENV="$(systemctl show assetapp -p Environment --value 2>/dev/null || true)"
LDB="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"; LDB="${LDB:-$LIVE_APP/assets.db}"; unset SVC_ENV
for f in $COPY; do cp "$LIVE_APP/$f" "$ROOT/app/"; done
for f in $EDITED; do cp "$ROOT/app/$f" "$ROOT/orig/$f"; done
cp "$LIVE_SHARED"/*.py "$ROOT/shared/"
python3 -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LDB" "$ROOT/app/assets.db" || fail "database copy"
at_from || fail "the live files are not at the kit's FROM pins -- nothing to rehearse"
cat > "$ROOT/web/standin.py" <<'PYEOF'
import http.server, os, sys
WEB = os.path.dirname(os.path.abspath(__file__))
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = self.path.split("?")[0]
        mode = open(os.path.join(WEB, "desk_mode")).read().strip() if os.path.exists(os.path.join(WEB, "desk_mode")) else "404"
        code = 200 if p == "/healthz" else (int(mode) if p == "/desk" else 404)
        self.send_response(code)
        if code == 302:
            self.send_header("Location", "/login?next=/desk")
        self.send_header("Content-Length", "0")
        self.end_headers()
    def log_message(self, *a):
        pass
http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
PYEOF
echo 302 > "$ROOT/web/desk_mode"
PORT="$(python3 -c "import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); print(s.getsockname()[1]); s.close()")"
python3 -B "$ROOT/web/standin.py" "$PORT" >/dev/null 2>&1 & HPID=$!
sleep 1

export S557_APP_DIR="$ROOT/app" S557_SERVICE="s557-rehearsal-made-up" S557_DB="$ROOT/app/assets.db" S557_UPLOADS="$ROOT/app/uploads"
export S557_HEALTH_URL="http://127.0.0.1:$PORT/healthz" S557_RESTART_CMD="true" S557_SHARED_DIR="$ROOT/shared" S557_HEALTH_TRIES=3
export S557_PYTHON="python3" S557_PYTHON_VENV="/usr/bin/python3"
for v in S557_APP_DIR S557_DB S557_UPLOADS S557_SHARED_DIR S557_PYTHON_VENV; do
  p="$(readlink -m "${!v}")"; case "$p" in /root/*) fail "$v resolves to $p -- the rehearsal never touches /root";; esac
done
case "$S557_RESTART_CMD" in *systemctl*) fail "the restart command contains systemctl";; esac
case "$S557_HEALTH_URL" in *:8030*) fail "the health URL is the live service's";; esac
[ "$(curl -s -o /dev/null -w '%{http_code}' "$S557_HEALTH_URL")" = "200" ] || fail "the stand-in health answer is not up"
[ "$(curl -s -o /dev/null -w '%{http_code}' "${S557_HEALTH_URL%/healthz}/desk")" = "302" ] || fail "the stand-in /desk does not answer 302"
echo "made-up root $ROOT; stand-in on port $PORT (/healthz 200, /desk 302); restart = true"
echo "  the made-up copy's tables before: $(tables "$ROOT/app/assets.db") (asset_part, asset_cover, service_logs.bill_id)"

echo "=== outcome 1: a fresh install (green) ==="
bash "$HERE/install_s557.sh" > "$ROOT/run1.txt" 2>&1; R1=$?
grep -E '^\[|DONE|REFUSED|NOT INSTALLED|walk|control|CONTROL|/desk answer|PINS|rebuilt|SIZES|machine.on|asset_machine S557|healed' "$ROOT/run1.txt" | sed 's/^/  /'
[ "$R1" = 0 ] && grep -q "S557_MACHINE_PAGES: DONE." "$ROOT/run1.txt" || fail "outcome 1 was not green (exit $R1)"
at_to || fail "outcome 1: the placed files are not at the TO pins"
for f in $EDITED; do ls "$ROOT/app/" | grep -q "^$f.bak_S557_" || fail "outcome 1: no backup beside $f"; done
ls "$ROOT/app/" | grep -q "assets.db.bak_S557_" || fail "outcome 1: no database backup"
[ "$(tables "$ROOT/app/assets.db")" = "True True True" ] || fail "outcome 1: the additive tables / column were not made"
grep -q "machine.on: absent" "$ROOT/run1.txt" || fail "outcome 1: machine.on was not left absent"
grep -q "UNDO (one line): \\\\cp -p " "$ROOT/run1.txt" || fail "outcome 1: the undo line does not start with \\cp -p"
echo "  made-up root after outcome 1: the three files at the TO pins; backups beside them; asset_part, asset_cover, service_logs.bill_id made; machine.on absent"

echo "=== outcome 2: the same line again (ALREADY INSTALLED) ==="
bash "$HERE/install_s557.sh" > "$ROOT/run2.txt" 2>&1; R2=$?
sed 's/^/  /' "$ROOT/run2.txt" | tail -3
[ "$R2" = 0 ] && grep -q "ALREADY INSTALLED" "$ROOT/run2.txt" || fail "outcome 2 did not say ALREADY INSTALLED"

echo "=== outcome 3: a forced red after placing (restores) ==="
reset_root
S557_FORCE_RED=1 bash "$HERE/install_s557.sh" > "$ROOT/run3.txt" 2>&1; R3=$?
grep -E 'forced|RESTOR|healthz|NOT INSTALLED|DONE|files back' "$ROOT/run3.txt" | sed 's/^/  /'
[ "$R3" = 1 ] && grep -q "NOT INSTALLED (restored" "$ROOT/run3.txt" || fail "outcome 3 did not restore (exit $R3)"
at_from || fail "outcome 3: the files are not back at the FROM pins (or asset_machine.py was not set aside)"

echo "=== outcome 4: healthz 200 but /desk does not answer (404: the app did not mount) -> restores ==="
reset_root
echo 404 > "$ROOT/web/desk_mode"
[ "$(curl -s -o /dev/null -w '%{http_code}' "${S557_HEALTH_URL%/healthz}/desk")" = "404" ] || fail "outcome 4: the stand-in still answers /desk"
bash "$HERE/install_s557.sh" > "$ROOT/run4.txt" 2>&1; R4=$?
grep -E '/desk|RESTOR|healthz|NOT INSTALLED|DONE|files back' "$ROOT/run4.txt" | sed 's/^/  /'
[ "$R4" = 1 ] && grep -q "not 302" "$ROOT/run4.txt" && grep -q "NOT INSTALLED (restored" "$ROOT/run4.txt" || fail "outcome 4 did not restore when /desk did not answer (exit $R4)"
at_from || fail "outcome 4: the files are not back at the FROM pins"

echo "=== outcome 5: /desk answers 200 -- a login gate open is not accepted -> restores ==="
reset_root
echo 200 > "$ROOT/web/desk_mode"
[ "$(curl -s -o /dev/null -w '%{http_code}' "${S557_HEALTH_URL%/healthz}/desk")" = "200" ] || fail "outcome 5: the stand-in does not answer 200"
bash "$HERE/install_s557.sh" > "$ROOT/run5.txt" 2>&1; R5=$?
grep -E '/desk|RESTOR|healthz|NOT INSTALLED|DONE|files back' "$ROOT/run5.txt" | sed 's/^/  /'
[ "$R5" = 1 ] && grep -q "answered 200, not 302" "$ROOT/run5.txt" && grep -q "NOT INSTALLED (restored" "$ROOT/run5.txt" || fail "outcome 5 did not restore on a 200 (exit $R5)"
at_from || fail "outcome 5: the files are not back at the FROM pins"

kill "$HPID" 2>/dev/null
echo "REHEARSAL GREEN: fresh install green; ALREADY INSTALLED; forced red restored to the FROM pins; /desk 404 restored; /desk 200 restored (302 only). Nothing live was placed or restarted."
[ -n "${KEEP:-}" ] || rm -rf "$ROOT"
exit 0
