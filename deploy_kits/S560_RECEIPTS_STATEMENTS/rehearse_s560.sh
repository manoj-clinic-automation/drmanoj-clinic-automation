#!/bin/bash
# rehearse_s560.sh -- the S560 installer rehearsed on a made-up root under /tmp/s560dev/root (BUILD_NORM_v1 s3, S559's shape).
# A copy of the scan app's files, of the finance folder's program files and of the scan app's database (SQLite's backup API)
# are put there; every S560_* setting points there; BOTH restarts are `true` and BOTH services are faked by one stand-in (a
# small python3 server on a free port: /healthz 200, /desk 302 -- the login gate, as the live app answers a plain request --
# and /finance/healthz 200). The build lock is a made-up path. Nothing live is placed or restarted.
# Outcomes: 1 green; 2 ALREADY INSTALLED; 3 a forced red after placing restores; 4 /desk not answering (404) restores;
# 5 /desk answering 200 (a login gate open) restores -- 302 only; 6 (FIX1 C2) /finance/healthz 200 but the finance journal
# saying "packs NOT mounted" (a made-up journal stub, S560_JOURNAL_CMD) restores.
# Run as root on the VPS: bash rehearse_s560.sh            (the made-up root is removed at the end; KEEP=1 keeps it)
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT=/tmp/s560dev/root
LIVE_APP=/root/assetapp
LIVE_FIN=/root/finance
LIVE_SHARED=/root/shared
EDITED="sorting_desk.py clinic_papers.py asset_register.py"
COPY="$EDITED asset_machine.py scanner_widget.js claude_reader.py claude_reread.py scanner_widget.js.bak_S559_1143c77b"
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1"; }
base(){ local b="${1%.py}"; echo "${b%.js}"; }
fail(){ echo "REHEARSAL RED: $*"; [ -n "${HPID:-}" ] && kill "$HPID" 2>/dev/null; exit 1; }
at_from(){ for f in $EDITED; do [ "$(md5 "$ROOT/app/$f")" = "$(pin PIN_FROM_$(base "$f").txt)" ] || return 1; done; [ "$(md5 "$ROOT/finance/packs.py")" = "$(pin PIN_FROM_packs.txt)" ]; }
at_to(){ for f in $EDITED; do [ "$(md5 "$ROOT/app/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] || return 1; done; [ "$(md5 "$ROOT/finance/packs.py")" = "$(pin PIN_TO_packs.txt)" ]; }
reset_root(){ for f in $EDITED; do cp "$ROOT/orig/$f" "$ROOT/app/$f"; done; cp "$ROOT/orig/packs.py" "$ROOT/finance/packs.py"; [ "${1:-}" = keepdb ] || cp "$ROOT/orig/assets.db" "$ROOT/app/assets.db"
              rm -f "$ROOT/app/"*.bak_S560_* "$ROOT/finance/"*.bak_S560_*; rm -rf "$ROOT/lock"; }

rm -rf "$ROOT"; mkdir -p "$ROOT/app/uploads" "$ROOT/shared" "$ROOT/orig" "$ROOT/web" "$ROOT/finance" || fail "no made-up root"
SVC_ENV="$(systemctl show assetapp -p Environment --value 2>/dev/null || true)"
LDB="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"; LDB="${LDB:-$LIVE_APP/assets.db}"; unset SVC_ENV
for f in $COPY; do cp -p "$LIVE_APP/$f" "$ROOT/app/"; done
for f in "$LIVE_FIN"/*.py "$LIVE_FIN"/*.html; do case "$f" in *.bak*) ;; *) [ -f "$f" ] && cp "$f" "$ROOT/finance/";; esac; done   # program files only
for f in $EDITED; do cp "$ROOT/app/$f" "$ROOT/orig/$f"; done; cp "$ROOT/finance/packs.py" "$ROOT/orig/packs.py"
cp "$LIVE_SHARED"/*.py "$ROOT/shared/"
python3 -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LDB" "$ROOT/app/assets.db" || fail "database copy"
cp "$ROOT/app/assets.db" "$ROOT/orig/assets.db"
at_from || fail "the live files are not at the kit's FROM pins -- nothing to rehearse"
cat > "$ROOT/web/standin.py" <<'PYEOF'
import http.server, os, sys
WEB = os.path.dirname(os.path.abspath(__file__))
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = self.path.split("?")[0]
        mode = open(os.path.join(WEB, "desk_mode")).read().strip() if os.path.exists(os.path.join(WEB, "desk_mode")) else "404"
        code = 200 if p in ("/healthz", "/finance/healthz") else (int(mode) if p == "/desk" else 404)
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

export S560_APP_DIR="$ROOT/app" S560_FIN_DIR="$ROOT/finance" S560_SERVICE="s560-rehearsal-made-up" S560_FIN_SERVICE="s560-rehearsal-finance-made-up"
export S560_DB="$ROOT/app/assets.db" S560_HEALTH_URL="http://127.0.0.1:$PORT/healthz" S560_FIN_HEALTH_URL="http://127.0.0.1:$PORT/finance/healthz"
export S560_RESTART_CMD="true" S560_FIN_RESTART_CMD="true" S560_SHARED_DIR="$ROOT/shared" S560_HEALTH_TRIES=3 S560_LOCK="$ROOT/lock"
export S560_PYTHON="python3" S560_PYTHON_VENV="/usr/bin/python3" S560_W559_FROM="$ROOT/app/scanner_widget.js.bak_S559_1143c77b"
for v in S560_APP_DIR S560_FIN_DIR S560_DB S560_SHARED_DIR S560_PYTHON_VENV S560_LOCK S560_W559_FROM; do
  p="$(readlink -m "${!v}")"; case "$p" in /root/*) fail "$v resolves to $p -- the rehearsal never touches /root";; esac
done
case "$S560_RESTART_CMD $S560_FIN_RESTART_CMD" in *systemctl*) fail "a restart command contains systemctl";; esac
case "$S560_HEALTH_URL $S560_FIN_HEALTH_URL" in *:8030*|*:8106*) fail "a health URL is a live service's";; esac
[ "$(curl -s -o /dev/null -w '%{http_code}' "$S560_HEALTH_URL")" = "200" ] || fail "the stand-in health answer is not up"
[ "$(curl -s -o /dev/null -w '%{http_code}' "$S560_FIN_HEALTH_URL")" = "200" ] || fail "the stand-in finance health answer is not up"
[ "$(curl -s -o /dev/null -w '%{http_code}' "${S560_HEALTH_URL%/healthz}/desk")" = "302" ] || fail "the stand-in /desk does not answer 302"
echo "made-up root $ROOT; stand-in on port $PORT (/healthz 200, /desk 302, /finance/healthz 200); both restarts = true; the lock made-up"

echo "=== outcome 1: a fresh install (green) ==="
bash "$HERE/install_s560.sh" > "$ROOT/run1.txt" 2>&1; R1=$?
grep -E '^\[|DONE|REFUSED|NOT INSTALLED|walk|control|CONTROL|/desk answer|healthz|PINS|rebuilt|SIZES|LIVE-STAMPS|before |data step|present' "$ROOT/run1.txt" | sed 's/^/  /'
[ "$R1" = 0 ] && grep -q "S560_RECEIPTS_STATEMENTS: DONE." "$ROOT/run1.txt" || fail "outcome 1 was not green (exit $R1)"
at_to || fail "outcome 1: the placed files are not at the TO pins"
for f in $EDITED; do ls "$ROOT/app/" | grep -q "^$f.bak_S560_" || fail "outcome 1: no backup beside $f"; done
ls "$ROOT/finance/" | grep -q "^packs.py.bak_S560_" || fail "outcome 1: no backup beside packs.py"
ls "$ROOT/app/" | grep -q "assets.db.bak_S560_" || fail "outcome 1: no database backup"
python3 -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); t={r[0] for r in c.execute(\"SELECT name FROM sqlite_master\")}; b=sqlite3.connect(sys.argv[2]); tb={r[0] for r in b.execute(\"SELECT name FROM sqlite_master\")}; sys.exit(0 if 'paper_payment' in t and 'paper_payment' not in tb else 1)" "$ROOT/app/assets.db" "$(ls "$ROOT/app/"assets.db.bak_S560_* | head -1)" || fail "outcome 1: the database backup was not taken BEFORE the data step"
grep -q "UNDO (one line): \\\\cp -p " "$ROOT/run1.txt" || fail "outcome 1: the undo line does not start with \\cp -p"
[ ! -d "$ROOT/lock" ] || fail "outcome 1: the build lock was not released"
echo "  made-up root after outcome 1: the four files at the TO pins; backups beside them; the database backed up before the data step; the lock released"

echo "=== outcome 2: the same line again (ALREADY INSTALLED) ==="
bash "$HERE/install_s560.sh" > "$ROOT/run2.txt" 2>&1; R2=$?
sed 's/^/  /' "$ROOT/run2.txt" | tail -3
[ "$R2" = 0 ] && grep -q "ALREADY INSTALLED" "$ROOT/run2.txt" || fail "outcome 2 did not say ALREADY INSTALLED"

echo "=== outcome 3: a forced red after placing (restores) -- on the database outcome 1 left (its two tables and column kept, as after a real restore) ==="
reset_root keepdb
S560_FORCE_RED=1 bash "$HERE/install_s560.sh" > "$ROOT/run3.txt" 2>&1; R3=$?
grep -E 'forced|RESTOR|healthz|NOT INSTALLED|DONE|files back' "$ROOT/run3.txt" | sed 's/^/  /'
[ "$R3" = 1 ] && grep -q "NOT INSTALLED (restored" "$ROOT/run3.txt" || fail "outcome 3 did not restore (exit $R3)"
at_from || fail "outcome 3: the files are not back at the FROM pins"

echo "=== outcome 4: healthz 200 but /desk does not answer (404: the app did not mount) -> restores ==="
reset_root
echo 404 > "$ROOT/web/desk_mode"
[ "$(curl -s -o /dev/null -w '%{http_code}' "${S560_HEALTH_URL%/healthz}/desk")" = "404" ] || fail "outcome 4: the stand-in still answers /desk"
bash "$HERE/install_s560.sh" > "$ROOT/run4.txt" 2>&1; R4=$?
grep -E '/desk|RESTOR|healthz|NOT INSTALLED|DONE|files back' "$ROOT/run4.txt" | sed 's/^/  /'
[ "$R4" = 1 ] && grep -q "not 302" "$ROOT/run4.txt" && grep -q "NOT INSTALLED (restored" "$ROOT/run4.txt" || fail "outcome 4 did not restore when /desk did not answer (exit $R4)"
at_from || fail "outcome 4: the files are not back at the FROM pins"

echo "=== outcome 5: /desk answers 200 -- a login gate open is not accepted -> restores ==="
reset_root
echo 200 > "$ROOT/web/desk_mode"
[ "$(curl -s -o /dev/null -w '%{http_code}' "${S560_HEALTH_URL%/healthz}/desk")" = "200" ] || fail "outcome 5: the stand-in does not answer 200"
bash "$HERE/install_s560.sh" > "$ROOT/run5.txt" 2>&1; R5=$?
grep -E '/desk|RESTOR|healthz|NOT INSTALLED|DONE|files back' "$ROOT/run5.txt" | sed 's/^/  /'
[ "$R5" = 1 ] && grep -q "answered 200, not 302" "$ROOT/run5.txt" && grep -q "NOT INSTALLED (restored" "$ROOT/run5.txt" || fail "outcome 5 did not restore on a 200 (exit $R5)"
at_from || fail "outcome 5: the files are not back at the FROM pins"

echo "=== outcome 6: /finance/healthz 200 but the finance journal says 'packs NOT mounted' (FIX1 C2) -> restores ==="
reset_root
echo 302 > "$ROOT/web/desk_mode"
cat > "$ROOT/web/journal_stub.sh" <<'SHEOF'
#!/bin/bash
# a made-up journal: what finance_app.py writes when packs.py fails to import (the made-up unit's only line)
echo "Oct 15 10:00:00 made-up gunicorn[1]: packs NOT mounted: ImportError('made-up for the rehearsal')"
SHEOF
chmod +x "$ROOT/web/journal_stub.sh"
S560_JOURNAL_CMD="$ROOT/web/journal_stub.sh" bash "$HERE/install_s560.sh" > "$ROOT/run6.txt" 2>&1; R6=$?
grep -E 'packs|RESTOR|healthz|NOT INSTALLED|DONE|files back' "$ROOT/run6.txt" | grep -v '^\[' | sed 's/^/  /'
[ "$R6" = 1 ] && grep -q "packs.py did not load" "$ROOT/run6.txt" && grep -q "NOT INSTALLED (restored" "$ROOT/run6.txt" || fail "outcome 6 did not restore when packs.py did not load (exit $R6)"
at_from || fail "outcome 6: the files are not back at the FROM pins"
grep -q "packs.py loaded" "$ROOT/run1.txt" || fail "outcome 1 did not read the finance journal"

kill "$HPID" 2>/dev/null
echo "REHEARSAL GREEN: fresh install green; ALREADY INSTALLED; forced red restored to the FROM pins; /desk 404 restored; /desk 200 restored (302 only); the pack not mounted restored. Both services faked; nothing live was placed or restarted."
[ -n "${KEEP:-}" ] || rm -rf "$ROOT"
exit 0
