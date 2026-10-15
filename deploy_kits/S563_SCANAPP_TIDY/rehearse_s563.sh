#!/bin/bash
# rehearse_s563.sh -- the S563 installer rehearsed on a made-up root under /tmp/s563dev/root (BUILD_NORM_v1 s3, S560's shape).
# A copy of the scan app's files, of the finance folder's program files (read only for the pack walks) and of the scan app's
# database (SQLite's backup API) are put there; every S563_* setting points there; the restart is `true` and the service is
# faked by a stand-in (a small python3 server on a free port: /healthz 200, /desk 302 -- the login gate, as the live app
# answers a plain request -- and /scan/widget.js = the made-up root's widget). The build lock is a made-up path. The builders'
# old scratch (item 13) is a made-up folder with made-up copies of the seven names -- one holding a made-up x.db, which must be
# left and named -- so the real /tmp list is never touched. Nothing live is placed or restarted.
# Outcomes: 1 green (and item 13 on the made-up scratch); 2 ALREADY INSTALLED; 3 a forced red after placing restores; 4 /desk
# not answering (404) restores; 5 /desk answering 200 (a login gate open) restores -- 302 only; 6 a live file not at its FROM
# pin is REFUSED before anything is placed.
# Run as root on the VPS: bash rehearse_s563.sh            (the made-up root is removed at the end; KEEP=1 keeps it)
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT=/tmp/s563dev/root
LIVE_APP=/root/assetapp
LIVE_FIN=/root/finance
LIVE_SHARED=/root/shared
EDITED="sorting_desk.py clinic_papers.py asset_machine.py scanner_widget.js asset_register.py"
COPY="$EDITED claude_reader.py claude_reread.py scanner_widget.js.bak_S559_1143c77b"
OLD_SCRATCH="s560fix1a s560fix1b s560fix1probe s560fix2a s560fix2_pins.sh s554kit s554probe"
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1"; }
base(){ local b="${1%.py}"; echo "${b%.js}"; }
fail(){ echo "REHEARSAL RED: $*"; [ -n "${HPID:-}" ] && kill "$HPID" 2>/dev/null; exit 1; }
at_from(){ for f in $EDITED; do [ "$(md5 "$ROOT/app/$f")" = "$(pin PIN_FROM_$(base "$f").txt)" ] || return 1; done; }
at_to(){ for f in $EDITED; do [ "$(md5 "$ROOT/app/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] || return 1; done; }
reset_root(){ for f in $EDITED; do cp "$ROOT/orig/$f" "$ROOT/app/$f"; done; cp "$ROOT/orig/assets.db" "$ROOT/app/assets.db"
              rm -f "$ROOT/app/"*.bak_S563_*; rm -rf "$ROOT/lock"; }
make_scratch(){ rm -rf "$ROOT/scratch"; mkdir -p "$ROOT/scratch"
  for n in $OLD_SCRATCH; do case "$n" in *.sh) echo "# made-up" > "$ROOT/scratch/$n";; *) mkdir -p "$ROOT/scratch/$n/sub"; echo "made-up log" > "$ROOT/scratch/$n/sub/run.txt";; esac; done
  echo "made-up, not a database" > "$ROOT/scratch/s560fix1b/x.db"; }

rm -rf "$ROOT"; mkdir -p "$ROOT/app/uploads" "$ROOT/shared" "$ROOT/orig" "$ROOT/web" "$ROOT/finance" || fail "no made-up root"
SVC_ENV="$(systemctl show assetapp -p Environment --value 2>/dev/null || true)"
LDB="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"; LDB="${LDB:-$LIVE_APP/assets.db}"; unset SVC_ENV
for f in $COPY; do cp -p "$LIVE_APP/$f" "$ROOT/app/"; done
for f in "$LIVE_FIN"/*.py "$LIVE_FIN"/*.html; do case "$f" in *.bak*) ;; *) [ -f "$f" ] && cp "$f" "$ROOT/finance/";; esac; done   # program files only
cp -p "$LIVE_FIN/packs.py.bak_S560_d86d351a" "$ROOT/finance/"                                                                  # S560's pack walk compares against it
for f in $EDITED; do cp "$ROOT/app/$f" "$ROOT/orig/$f"; done
cp "$LIVE_SHARED"/*.py "$ROOT/shared/"
python3 -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LDB" "$ROOT/app/assets.db" || fail "database copy"
cp "$ROOT/app/assets.db" "$ROOT/orig/assets.db"
at_from || fail "the live files are not at the kit's FROM pins -- nothing to rehearse"
cat > "$ROOT/web/standin.py" <<'PYEOF'
import http.server, os, sys
WEB = os.path.dirname(os.path.abspath(__file__))
APPW = os.path.join(os.path.dirname(WEB), "app", "scanner_widget.js")
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = self.path.split("?")[0]
        mode = open(os.path.join(WEB, "desk_mode")).read().strip() if os.path.exists(os.path.join(WEB, "desk_mode")) else "404"
        body = b""
        if p == "/scan/widget.js":
            code, body = 200, open(APPW, "rb").read()
        else:
            code = 200 if p == "/healthz" else (int(mode) if p == "/desk" else 404)
        self.send_response(code)
        if code == 302:
            self.send_header("Location", "/login?next=/desk")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a):
        pass
http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
PYEOF
echo 302 > "$ROOT/web/desk_mode"
PORT="$(python3 -c "import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); print(s.getsockname()[1]); s.close()")"
python3 -B "$ROOT/web/standin.py" "$PORT" >/dev/null 2>&1 & HPID=$!
sleep 1

export S563_APP_DIR="$ROOT/app" S563_FIN_DIR="$ROOT/finance" S563_SERVICE="s563-rehearsal-made-up" S563_DB="$ROOT/app/assets.db"
export S563_HEALTH_URL="http://127.0.0.1:$PORT/healthz" S563_RESTART_CMD="true" S563_SHARED_DIR="$ROOT/shared" S563_HEALTH_TRIES=3
export S563_LOCK="$ROOT/lock" S563_PYTHON="python3" S563_PYTHON_VENV="/usr/bin/python3" S563_W559_FROM="$ROOT/app/scanner_widget.js.bak_S559_1143c77b"
export S563_PACK_BEFORE="$ROOT/finance/packs.py.bak_S560_d86d351a" S563_SCRATCH_ROOT="$ROOT/scratch"
for v in S563_APP_DIR S563_FIN_DIR S563_DB S563_SHARED_DIR S563_PYTHON_VENV S563_LOCK S563_W559_FROM S563_PACK_BEFORE S563_SCRATCH_ROOT; do
  p="$(readlink -m "${!v}")"; case "$p" in /root/*) [ "$v" = S563_PYTHON_VENV ] || fail "$v resolves to $p -- the rehearsal never touches /root";; esac
done
case "$(readlink -m "$S563_SCRATCH_ROOT")" in /tmp) fail "the scratch root is the real /tmp";; /tmp/s563dev/root/*) ;; *) fail "the scratch root is not inside the made-up root";; esac
case "$S563_RESTART_CMD" in *systemctl*) fail "the restart command contains systemctl";; esac
case "$S563_HEALTH_URL" in *:8030*|*:8106*) fail "the health URL is a live service's";; esac
[ "$(curl -s -o /dev/null -w '%{http_code}' "$S563_HEALTH_URL")" = "200" ] || fail "the stand-in health answer is not up"
[ "$(curl -s -o /dev/null -w '%{http_code}' "${S563_HEALTH_URL%/healthz}/desk")" = "302" ] || fail "the stand-in /desk does not answer 302"
echo "made-up root $ROOT; stand-in on port $PORT (/healthz 200, /desk 302, /scan/widget.js); the restart = true; the lock and the scratch made-up"
echo "the real $(ls -d /tmp/s560fix* /tmp/s554* 2>/dev/null | wc -l) old scratch names under /tmp before the rehearsal (listed only, never touched): $(ls -d /tmp/s560fix* /tmp/s554* 2>/dev/null | tr '\n' ' ')"
REAL_BEFORE="$(ls -d /tmp/s560fix* /tmp/s554* 2>/dev/null | md5sum)"

echo "=== outcome 1: a fresh install (green), then item 13 on the made-up scratch ==="
make_scratch
bash "$HERE/install_s563.sh" > "$ROOT/run1.txt" 2>&1; R1=$?
grep -E '^\[|DONE|REFUSED|NOT INSTALLED|walk|control|CONTROL|TIDY|/desk answer|healthz|PINS|rebuilt|widget|removed|left|not there' "$ROOT/run1.txt" | sed 's/^/  /'
[ "$R1" = 0 ] && grep -q "S563_SCANAPP_TIDY: DONE." "$ROOT/run1.txt" || fail "outcome 1 was not green (exit $R1)"
at_to || fail "outcome 1: the placed files are not at the TO pins"
for f in $EDITED; do ls "$ROOT/app/" | grep -q "^$f.bak_S563_" || fail "outcome 1: no backup beside $f"; done
ls "$ROOT/app/" | grep -q "assets.db.bak_S563_" || fail "outcome 1: no database backup"
python3 -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); b=sqlite3.connect(sys.argv[2]); q='SELECT name, sql FROM sqlite_master ORDER BY name'; sys.exit(0 if list(c.execute(q)) == list(b.execute(q)) else 1)" "$ROOT/app/assets.db" "$ROOT/orig/assets.db" || fail "outcome 1: the database's tables / columns changed (no data step was to run)"
grep -q "UNDO (one line): \\\\cp -p " "$ROOT/run1.txt" || fail "outcome 1: the undo line does not start with \\cp -p"
[ ! -d "$ROOT/lock" ] || fail "outcome 1: the build lock was not released"
[ -d "$ROOT/scratch/s560fix1b" ] && [ -f "$ROOT/scratch/s560fix1b/x.db" ] || fail "outcome 1: the scratch folder holding a database was removed"
grep -q "left $ROOT/scratch/s560fix1b: it holds a database / JSON file (x.db)" "$ROOT/run1.txt" || fail "outcome 1: the left folder was not named"
for n in s560fix1a s560fix1probe s560fix2a s560fix2_pins.sh s554kit s554probe; do [ ! -e "$ROOT/scratch/$n" ] || fail "outcome 1: $n was not removed"; done
[ "$(ls -d /tmp/s560fix* /tmp/s554* 2>/dev/null | md5sum)" = "$REAL_BEFORE" ] || fail "the real /tmp scratch list changed"
echo "  made-up root after outcome 1: the five files at the TO pins; backups beside them; the database unchanged in shape; the lock released;"
echo "  item 13: six made-up names removed, the one holding x.db left and named; the real /tmp list untouched"

echo "=== outcome 2: the same line again (ALREADY INSTALLED) ==="
bash "$HERE/install_s563.sh" > "$ROOT/run2.txt" 2>&1; R2=$?
sed 's/^/  /' "$ROOT/run2.txt" | tail -2
[ "$R2" = 0 ] && grep -q "ALREADY INSTALLED" "$ROOT/run2.txt" || fail "outcome 2 did not say ALREADY INSTALLED"

echo "=== outcome 3: a forced red after placing (restores) ==="
reset_root
S563_FORCE_RED=1 bash "$HERE/install_s563.sh" > "$ROOT/run3.txt" 2>&1; R3=$?
grep -E 'forced|RESTOR|healthz|NOT INSTALLED|DONE|files back' "$ROOT/run3.txt" | sed 's/^/  /'
[ "$R3" = 1 ] && grep -q "NOT INSTALLED (restored" "$ROOT/run3.txt" || fail "outcome 3 did not restore (exit $R3)"
at_from || fail "outcome 3: the files are not back at the FROM pins"

echo "=== outcome 4: healthz 200 but /desk does not answer (404: the app did not mount) -> restores ==="
reset_root
echo 404 > "$ROOT/web/desk_mode"
bash "$HERE/install_s563.sh" > "$ROOT/run4.txt" 2>&1; R4=$?
grep -E '/desk|RESTOR|healthz|NOT INSTALLED|DONE|files back' "$ROOT/run4.txt" | sed 's/^/  /'
[ "$R4" = 1 ] && grep -q "not 302" "$ROOT/run4.txt" && grep -q "NOT INSTALLED (restored" "$ROOT/run4.txt" || fail "outcome 4 did not restore when /desk did not answer (exit $R4)"
at_from || fail "outcome 4: the files are not back at the FROM pins"

echo "=== outcome 5: /desk answers 200 -- a login gate open is not accepted -> restores ==="
reset_root
echo 200 > "$ROOT/web/desk_mode"
bash "$HERE/install_s563.sh" > "$ROOT/run5.txt" 2>&1; R5=$?
grep -E '/desk|RESTOR|healthz|NOT INSTALLED|DONE|files back' "$ROOT/run5.txt" | sed 's/^/  /'
[ "$R5" = 1 ] && grep -q "answered 200, not 302" "$ROOT/run5.txt" && grep -q "NOT INSTALLED (restored" "$ROOT/run5.txt" || fail "outcome 5 did not restore on a 200 (exit $R5)"
at_from || fail "outcome 5: the files are not back at the FROM pins"

echo "=== outcome 6: a live file not at its FROM pin (another kit moved it) -> REFUSED before anything is placed ==="
reset_root
echo 302 > "$ROOT/web/desk_mode"
printf '\n# made-up change\n' >> "$ROOT/app/asset_machine.py"
bash "$HERE/install_s563.sh" > "$ROOT/run6.txt" 2>&1; R6=$?
grep -E 'REFUSED|NOT INSTALLED' "$ROOT/run6.txt" | sed 's/^/  /'
[ "$R6" = 1 ] && grep -q "REFUSED: asset_machine.py is" "$ROOT/run6.txt" && grep -q "NOT INSTALLED (nothing was placed)" "$ROOT/run6.txt" || fail "outcome 6 was not refused (exit $R6)"
ls "$ROOT/app/" | grep -q "\.bak_S563_" && fail "outcome 6: a backup was made -- the refusal came too late"
for f in sorting_desk.py clinic_papers.py scanner_widget.js asset_register.py; do [ "$(md5 "$ROOT/app/$f")" = "$(pin PIN_FROM_$(base "$f").txt)" ] || fail "outcome 6: $f was touched"; done
[ ! -d "$ROOT/lock" ] || fail "outcome 6: the build lock was not released"

kill "$HPID" 2>/dev/null
echo "REHEARSAL GREEN: fresh install green (item 13 on made-up scratch: six removed, the one with a database left and named); ALREADY INSTALLED; forced red restored to the FROM pins; /desk 404 restored; /desk 200 restored (302 only); a moved file refused before placing. The service faked; nothing live was placed or restarted; the real /tmp scratch untouched."
[ -n "${KEEP:-}" ] || rm -rf "$ROOT"
exit 0
