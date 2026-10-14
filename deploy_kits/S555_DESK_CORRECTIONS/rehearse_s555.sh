#!/bin/bash
# rehearse_s555.sh -- the S555 installer rehearsed on a made-up root under /tmp/s555dev/root (BUILD_NORM_v1 s3, S551's shape).
# A copy of the app's files and of its database (SQLite's backup API) are put there; every S555_* setting points there; the
# restart is `true` and the answers come from a stand-in (a small python3 server on a free port: /healthz 200, /desk 302 --
# the login gate, as the live app answers a plain request). Nothing live is placed or restarted.
# Outcomes: 1 green; 2 ALREADY INSTALLED; 3 a forced red after placing restores; 4 /desk not answering (404) restores;
# 5 /desk answering 200 (a login gate open) restores -- item 7: the installer accepts 302 only.
# Run as root on the VPS: bash rehearse_s555.sh            (the made-up root is removed at the end; KEEP=1 keeps it)
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT=/tmp/s555dev/root
LIVE_APP=/root/assetapp
LIVE_SHARED=/root/shared
FILES="sorting_desk.py claude_reread.py asset_register.py"
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1"; }
base(){ echo "${1%.py}"; }
fail(){ echo "REHEARSAL RED: $*"; [ -n "${HPID:-}" ] && kill "$HPID" 2>/dev/null; exit 1; }
at_pins(){ for f in $FILES; do [ "$(md5 "$ROOT/app/$f")" = "$(pin PIN_${1}_$(base "$f").txt)" ] || return 1; done; return 0; }
reset_root(){ for f in $FILES; do cp "$ROOT/orig/$f" "$ROOT/app/$f"; done; rm -f "$ROOT/app/"*.bak_S555_*; }
schema(){ python3 -c "import sqlite3,sys,hashlib; c=sqlite3.connect(sys.argv[1]); print(hashlib.md5(repr(c.execute('SELECT type,name,sql FROM sqlite_master ORDER BY name').fetchall()).encode()).hexdigest())" "$1"; }

rm -rf "$ROOT"; mkdir -p "$ROOT/app/uploads" "$ROOT/shared" "$ROOT/orig" "$ROOT/web" || fail "no made-up root"
SVC_ENV="$(systemctl show assetapp -p Environment --value 2>/dev/null || true)"
LDB="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"; LDB="${LDB:-$LIVE_APP/assets.db}"; unset SVC_ENV
cp "$LIVE_APP/sorting_desk.py" "$LIVE_APP/asset_register.py" "$LIVE_APP/claude_reread.py" "$LIVE_APP/clinic_papers.py" "$LIVE_APP/claude_reader.py" "$ROOT/app/"
for f in $FILES; do cp "$ROOT/app/$f" "$ROOT/orig/$f"; done
cp "$LIVE_SHARED"/*.py "$ROOT/shared/"
python3 -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LDB" "$ROOT/app/assets.db" || fail "database copy"
at_pins FROM || fail "the live files are not at the kit's FROM pins -- nothing to rehearse"
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

export S555_APP_DIR="$ROOT/app" S555_SERVICE="s555-rehearsal-made-up" S555_DB="$ROOT/app/assets.db" S555_UPLOADS="$ROOT/app/uploads"
export S555_HEALTH_URL="http://127.0.0.1:$PORT/healthz" S555_RESTART_CMD="true" S555_SHARED_DIR="$ROOT/shared" S555_HEALTH_TRIES=3
export S555_PYTHON="python3" S555_PYTHON_VENV="/usr/bin/python3"
for v in S555_APP_DIR S555_DB S555_UPLOADS S555_SHARED_DIR S555_PYTHON_VENV; do
  p="$(readlink -m "${!v}")"; case "$p" in /root/*) fail "$v resolves to $p -- the rehearsal never touches /root";; esac
done
case "$S555_RESTART_CMD" in *systemctl*) fail "the restart command contains systemctl";; esac
case "$S555_HEALTH_URL" in *:8030*) fail "the health URL is the live service's";; esac
[ "$(curl -s -o /dev/null -w '%{http_code}' "$S555_HEALTH_URL")" = "200" ] || fail "the stand-in health answer is not up"
[ "$(curl -s -o /dev/null -w '%{http_code}' "${S555_HEALTH_URL%/healthz}/desk")" = "302" ] || fail "the stand-in /desk does not answer 302"
echo "made-up root $ROOT; stand-in on port $PORT (/healthz 200, /desk 302); restart = true"
SCH0="$(schema "$ROOT/app/assets.db")"

echo "=== outcome 1: a fresh install (green) ==="
bash "$HERE/install_s555.sh" > "$ROOT/run1.txt" 2>&1; R1=$?
grep -E '^\[|DONE|REFUSED|NOT INSTALLED|walk:|control|CONTROL|/desk answer|PINS|rebuilt|SIZES' "$ROOT/run1.txt" | sed 's/^/  /'
[ "$R1" = 0 ] && grep -q "S555_DESK_CORRECTIONS: DONE." "$ROOT/run1.txt" || fail "outcome 1 was not green (exit $R1)"
at_pins TO || fail "outcome 1: the placed files are not at the TO pins"
for f in $FILES; do ls "$ROOT/app/" | grep -q "^$f.bak_S555_" || fail "outcome 1: no backup beside $f"; done
ls "$ROOT/app/" | grep -q "assets.db.bak_S555_" || fail "outcome 1: no database backup"
[ "$(schema "$ROOT/app/assets.db")" = "$SCH0" ] || fail "outcome 1: the database's tables changed (this kit makes no database change)"
echo "  made-up root after outcome 1: the three files at the TO pins; backups beside them; the database's tables unchanged"

echo "=== outcome 2: the same line again (ALREADY INSTALLED) ==="
bash "$HERE/install_s555.sh" > "$ROOT/run2.txt" 2>&1; R2=$?
sed 's/^/  /' "$ROOT/run2.txt" | tail -3
[ "$R2" = 0 ] && grep -q "ALREADY INSTALLED" "$ROOT/run2.txt" || fail "outcome 2 did not say ALREADY INSTALLED"

echo "=== outcome 3: a forced red after placing (restores) ==="
reset_root
S555_FORCE_RED=1 bash "$HERE/install_s555.sh" > "$ROOT/run3.txt" 2>&1; R3=$?
grep -E 'forced|RESTOR|healthz|NOT INSTALLED|DONE|files back' "$ROOT/run3.txt" | sed 's/^/  /'
[ "$R3" = 1 ] && grep -q "NOT INSTALLED (restored" "$ROOT/run3.txt" || fail "outcome 3 did not restore (exit $R3)"
at_pins FROM || fail "outcome 3: the files are not back at the FROM pins"

echo "=== outcome 4: healthz 200 but /desk does not answer (404: the desk did not mount) -> restores ==="
reset_root
echo 404 > "$ROOT/web/desk_mode"
[ "$(curl -s -o /dev/null -w '%{http_code}' "${S555_HEALTH_URL%/healthz}/desk")" = "404" ] || fail "outcome 4: the stand-in still answers /desk"
bash "$HERE/install_s555.sh" > "$ROOT/run4.txt" 2>&1; R4=$?
grep -E '/desk|RESTOR|healthz|NOT INSTALLED|DONE|files back' "$ROOT/run4.txt" | sed 's/^/  /'
[ "$R4" = 1 ] && grep -q "not 302" "$ROOT/run4.txt" && grep -q "NOT INSTALLED (restored" "$ROOT/run4.txt" || fail "outcome 4 did not restore when /desk did not answer (exit $R4)"
at_pins FROM || fail "outcome 4: the files are not back at the FROM pins"

echo "=== outcome 5 (item 7): /desk answers 200 -- a login gate open is not accepted -> restores ==="
reset_root
echo 200 > "$ROOT/web/desk_mode"
[ "$(curl -s -o /dev/null -w '%{http_code}' "${S555_HEALTH_URL%/healthz}/desk")" = "200" ] || fail "outcome 5: the stand-in does not answer 200"
bash "$HERE/install_s555.sh" > "$ROOT/run5.txt" 2>&1; R5=$?
grep -E '/desk|RESTOR|healthz|NOT INSTALLED|DONE|files back' "$ROOT/run5.txt" | sed 's/^/  /'
[ "$R5" = 1 ] && grep -q "answered 200, not 302" "$ROOT/run5.txt" && grep -q "NOT INSTALLED (restored" "$ROOT/run5.txt" || fail "outcome 5 did not restore on a 200 (exit $R5)"
at_pins FROM || fail "outcome 5: the files are not back at the FROM pins"

kill "$HPID" 2>/dev/null
echo "REHEARSAL GREEN: fresh install green; ALREADY INSTALLED; forced red restored to the FROM pins; /desk 404 restored; /desk 200 restored (302 only). Nothing live was placed or restarted."
[ -n "${KEEP:-}" ] || rm -rf "$ROOT"
exit 0
