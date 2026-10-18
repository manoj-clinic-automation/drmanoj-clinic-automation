#!/bin/bash
# rehearse_s575.sh -- the S575 installer rehearsed on a made-up root under /tmp/s575reh/root (BUILD_NORM_v1 s3, S571's shape). A copy
# of the scan app's files (with S563's five backups and the pre-S559 widget, which the earlier walks compare against), of the finance
# folder's program files (with packs.py before S560 and before S568) and of the scan app's database (SQLite's backup API) are put
# there; every S575_* setting points there (the earlier kits are read, never written, from S575_KITS_DIR); the restart is `true`, the
# service is faked by a stand-in (a small python3 server on a free port: /healthz 200, /desk and /batteries 302 -- the login gate, as
# the live app answers a plain request). The build lock is a made-up path. Nothing live is placed or restarted.
# Outcomes: 1 green (no data step: every table's rows and every setting read back unchanged; the backup taken); 2 ALREADY INSTALLED;
# 3 a forced red after placing restores batteries.py; 4 /desk not answering (404) restores; 5 /desk answering 200 (a login gate open)
# restores -- 302 only; 6 /batteries not answering (404) restores; 7 batteries.py not at its FROM pin is REFUSED before anything is
# placed; 8 a read-only file moved (sorting_desk.py) is REFUSED before anything is placed; 9 no batteries.py (S571 not installed) is
# REFUSED; 10 the parent's packs.py moved by another kit is REFUSED before anything is placed (S575 never places it).
# The end guard compares PROGRAM FILES only (S568 K2): (cd "$LIVE_FIN" && md5sum -- *.py *.html 2>/dev/null) | md5sum, and the same
# over the live scan app's *.py *.js -- never a directory listing (the live apps' own logs and journals come and go).
# Run as root on the VPS: S575_KITS_DIR=/root/deploy/repo/deploy_kits bash rehearse_s575.sh   (KEEP=1 keeps the made-up root)
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT=/tmp/s575reh/root
LIVE_APP=/root/assetapp
LIVE_FIN=/root/finance
LIVE_SHARED=/root/shared
F="batteries.py"
RO="sorting_desk.py asset_register.py clinic_papers.py stationery.py asset_machine.py scanner_widget.js claude_reader.py claude_reread.py"
COPY="$F $RO scanner_widget.js.bak_S559_1143c77b"
COPY="$COPY sorting_desk.py.bak_S563_a4623438 clinic_papers.py.bak_S563_88963eac asset_register.py.bak_S563_9daed9ea asset_machine.py.bak_S563_0caec41e scanner_widget.js.bak_S563_1128ac97"
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1"; }
base(){ local b="${1%.py}"; echo "${b%.js}"; }
fail(){ echo "REHEARSAL RED: $*"; [ -n "${HPID:-}" ] && kill "$HPID" 2>/dev/null; exit 1; }
at_from(){ [ -f "$ROOT/app/$F" ] && [ "$(md5 "$ROOT/app/$F")" = "$(pin PIN_FROM_batteries.txt)" ]; }
at_to(){ [ -f "$ROOT/app/$F" ] && [ "$(md5 "$ROOT/app/$F")" = "$(pin PIN_TO_batteries.txt)" ]; }
ro_ok(){ for f in $RO; do [ "$(md5 "$ROOT/app/$f")" = "$(pin PIN_READ_$(base "$f").txt)" ] || return 1; done; }
reset_root(){ for f in $F sorting_desk.py; do cp "$ROOT/orig/$f" "$ROOT/app/$f"; done; cp "$ROOT/orig/packs.py" "$ROOT/finance/packs.py"
              cp "$ROOT/orig/assets.db" "$ROOT/app/assets.db"; rm -f "$ROOT/app/"*.bak_S575_* "$ROOT/finance/"*.bak_S575_*; rm -rf "$ROOT/lock"; }
progs(){ (cd "$1" && md5sum -- $2 2>/dev/null) | md5sum; }
[ -n "${S575_KITS_DIR:-}" ] && [ -f "$S575_KITS_DIR/S571_BATTERIES/walk_s571.py" ] || fail "set S575_KITS_DIR to the folder holding the earlier kits (read only)"

rm -rf "$ROOT"; mkdir -p "$ROOT/app/uploads" "$ROOT/shared" "$ROOT/orig" "$ROOT/web" "$ROOT/finance" || fail "no made-up root"
SVC_ENV="$(systemctl show assetapp -p Environment --value 2>/dev/null || true)"
LDB="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"; LDB="${LDB:-$LIVE_APP/assets.db}"; unset SVC_ENV
for f in $COPY; do cp -p "$LIVE_APP/$f" "$ROOT/app/" || fail "copy $f"; done
LIVE_BT="$(md5 "$LIVE_APP/$F")"
for f in "$LIVE_FIN"/*.py "$LIVE_FIN"/*.html; do case "$f" in *.bak*) ;; *) [ -f "$f" ] && cp "$f" "$ROOT/finance/";; esac; done   # program files only
cp -p "$LIVE_FIN/packs.py.bak_S560_d86d351a" "$LIVE_FIN/packs.py.bak_S568_048d2ad8" "$ROOT/finance/"                          # the earlier walks compare against them
for f in $F sorting_desk.py; do cp "$ROOT/app/$f" "$ROOT/orig/$f"; done; cp "$ROOT/finance/packs.py" "$ROOT/orig/packs.py"
cp "$LIVE_SHARED"/*.py "$ROOT/shared/"
python3 -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LDB" "$ROOT/app/assets.db" || fail "database copy"
cp "$ROOT/app/assets.db" "$ROOT/orig/assets.db"
at_from || fail "the live batteries.py is not at the kit's FROM pin -- nothing to rehearse"
cat > "$ROOT/web/standin.py" <<'PYEOF'
import http.server, os, sys
WEB = os.path.dirname(os.path.abspath(__file__))
def mode(n, d):
    p = os.path.join(WEB, n)
    return open(p).read().strip() if os.path.exists(p) else d
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = self.path.split("?")[0]
        code = 200 if p == "/healthz" else (int(mode("desk_mode", "404")) if p == "/desk" else
                                            (int(mode("bt_mode", "404")) if p == "/batteries" else 404))
        self.send_response(code)
        if code == 302:
            self.send_header("Location", "/login?next=" + p)
        self.send_header("Content-Length", "0")
        self.end_headers()
    def log_message(self, *a):
        pass
http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
PYEOF
echo 302 > "$ROOT/web/desk_mode"; echo 302 > "$ROOT/web/bt_mode"
PORT="$(python3 -c "import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); print(s.getsockname()[1]); s.close()")"
python3 -B "$ROOT/web/standin.py" "$PORT" >/dev/null 2>&1 & HPID=$!
sleep 1

export S575_APP_DIR="$ROOT/app" S575_FIN_DIR="$ROOT/finance" S575_SERVICE="s575-rehearsal-made-up"
export S575_DB="$ROOT/app/assets.db" S575_HEALTH_URL="http://127.0.0.1:$PORT/healthz"
export S575_RESTART_CMD="true" S575_SHARED_DIR="$ROOT/shared" S575_HEALTH_TRIES=3 S575_LOCK="$ROOT/lock"
export S575_PYTHON="python3" S575_PYTHON_VENV="/usr/bin/python3" S575_W559_FROM="$ROOT/app/scanner_widget.js.bak_S559_1143c77b"
export S575_PACK_BEFORE="$ROOT/finance/packs.py.bak_S560_d86d351a" S575_PACK_BEFORE_S568="$ROOT/finance/packs.py.bak_S568_048d2ad8" S575_KITS_DIR
for v in S575_APP_DIR S575_FIN_DIR S575_DB S575_SHARED_DIR S575_PYTHON_VENV S575_LOCK S575_W559_FROM S575_PACK_BEFORE S575_PACK_BEFORE_S568; do
  p="$(readlink -m "${!v}")"; case "$p" in /root/*) [ "$v" = S575_PYTHON_VENV ] || fail "$v resolves to $p -- the rehearsal never touches /root";; esac
done
case "$S575_RESTART_CMD" in *systemctl*) fail "the restart command contains systemctl";; esac
case "$S575_HEALTH_URL" in *:8030*|*:8106*) fail "the health URL is a live service's";; esac
[ "$(curl -s -o /dev/null -w '%{http_code}' "$S575_HEALTH_URL")" = "200" ] || fail "the stand-in health answer is not up"
[ "$(curl -s -o /dev/null -w '%{http_code}' "${S575_HEALTH_URL%/healthz}/desk")" = "302" ] || fail "the stand-in /desk does not answer 302"
echo "made-up root $ROOT; stand-in on port $PORT (/healthz 200, /desk and /batteries 302); the restart = true; the lock made-up; the earlier kits read from $S575_KITS_DIR"
LIVE_BEFORE="$(progs "$LIVE_APP" '*.py *.js')"; LIVE_FIN_BEFORE="$(progs "$LIVE_FIN" '*.py *.html')"

echo "=== outcome 1: a fresh install (green) ==="
bash "$HERE/install_s575.sh" > "$ROOT/run1.txt" 2>&1; R1=$?
grep -E '^\[|DONE|REFUSED|NOT INSTALLED|walk|control|CONTROL|TIDY|copy|answer|healthz|PINS|rebuilt|tidy comparison|placed|bak_S575' "$ROOT/run1.txt" | cut -c1-330 | sed 's/^/  /'
[ "$R1" = 0 ] && grep -q "S575_BATTERY_SETUP: DONE." "$ROOT/run1.txt" || fail "outcome 1 was not green (exit $R1)"
at_to || fail "outcome 1: batteries.py is not at the TO pin"
ls "$ROOT/app/" | grep -q "^$F.bak_S575_9a0054ac$" || fail "outcome 1: no backup batteries.py.bak_S575_9a0054ac"
[ "$(md5 "$ROOT/app/$F.bak_S575_9a0054ac")" = "$(pin PIN_FROM_batteries.txt)" ] || fail "outcome 1: the backup is not the FROM bytes"
ls "$ROOT/app/" | grep -q "assets.db.bak_S575_" || fail "outcome 1: no database backup"
ro_ok || fail "outcome 1: a read-only file was touched"
[ "$(md5 "$ROOT/finance/packs.py")" = "$(pin PIN_READ_packs.txt)" ] || fail "outcome 1: packs.py was touched"
ls "$ROOT/finance/" | grep -q "\.bak_S575_" && fail "outcome 1: something in the finance folder was backed up -- S575 touches nothing there"
python3 - "$ROOT/app/assets.db" "$ROOT/orig/assets.db" "$(ls "$ROOT/app/"assets.db.bak_S575_* | head -1)" <<'PYEOF' || fail "outcome 1: the database changed (S575 has no data step) -- or the backup differs"
import sqlite3, sys
a, b, k = sqlite3.connect(sys.argv[1]), sqlite3.connect(sys.argv[2]), sqlite3.connect(sys.argv[3])
def objs(c):
    return {(r[0], r[1]) for r in c.execute("SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}
def rows(c, t, cols):
    return sorted(map(repr, c.execute('SELECT %s FROM "%s"' % (",".join('"%s"' % x for x in cols), t))))
sa, sb, sk = objs(a), objs(b), objs(k)
same, nt = True, 0
for kind, t in sorted(sb):
    if kind != "table":
        continue
    nt += 1
    cols = [r[1] for r in b.execute('PRAGMA table_info("%s")' % t)]
    if rows(a, t, cols) != rows(b, t, cols) or rows(k, t, cols) != rows(b, t, cols):
        same = False; print("  table %s differs" % t)
print("  database: objects the same %s; every row of the %d tables unchanged (settings included) %s; the backup the same %s"
      % (sa == sb, nt, same, sk == sb))
sys.exit(0 if (sa == sb and sk == sb and same) else 1)
PYEOF
grep -q "UNDO (one line): \\\\cp -p .*batteries.py.bak_S575_9a0054ac .*batteries.py && systemctl restart s575-rehearsal-made-up$" "$ROOT/run1.txt" || fail "outcome 1: the undo line does not put back batteries.py.bak_S575_9a0054ac, or restarts more than the scan app"
grep -q "clinic-finance" "$ROOT/run1.txt" && fail "outcome 1: the finance service was named -- S575 restarts assetapp only"
[ ! -d "$ROOT/lock" ] || fail "outcome 1: the build lock was not released"
echo "  made-up root after outcome 1: batteries.py at the TO pin, batteries.py.bak_S575_9a0054ac beside it (the FROM bytes); the read-only files and packs.py untouched; the database backed up and not changed (no data step); the lock released"

echo "=== outcome 2: the same line again (ALREADY INSTALLED) ==="
bash "$HERE/install_s575.sh" > "$ROOT/run2.txt" 2>&1; R2=$?
sed 's/^/  /' "$ROOT/run2.txt" | tail -2 | cut -c1-300
[ "$R2" = 0 ] && grep -q "ALREADY INSTALLED" "$ROOT/run2.txt" || fail "outcome 2 did not say ALREADY INSTALLED"
at_to || fail "outcome 2: batteries.py moved"

for oc in "3:forced" "4:desk404" "5:desk200" "6:bt404"; do
  n=${oc%%:*}; k=${oc##*:}
  reset_root; echo 302 > "$ROOT/web/desk_mode"; echo 302 > "$ROOT/web/bt_mode"
  case "$k" in
    forced) echo "=== outcome 3: a forced red after placing (restores the file) ==="; export S575_FORCE_RED=1;;
    desk404) echo "=== outcome 4: healthz 200 but /desk does not answer (404) -> restores ==="; echo 404 > "$ROOT/web/desk_mode";;
    desk200) echo "=== outcome 5: /desk answers 200 -- a login gate open is not accepted -> restores ==="; echo 200 > "$ROOT/web/desk_mode";;
    bt404) echo "=== outcome 6: /batteries does not answer (404) -> restores ==="; echo 404 > "$ROOT/web/bt_mode";;
  esac
  bash "$HERE/install_s575.sh" > "$ROOT/run$n.txt" 2>&1; RR=$?; unset S575_FORCE_RED
  grep -E 'forced|RESTOR|/desk|/batteries|NOT INSTALLED|DONE|back at' "$ROOT/run$n.txt" | cut -c1-260 | sed 's/^/  /'
  [ "$RR" = 1 ] && grep -q "NOT INSTALLED (restored" "$ROOT/run$n.txt" || fail "outcome $n did not restore (exit $RR)"
  at_from || fail "outcome $n: batteries.py is not back at the FROM pin"
  ro_ok || fail "outcome $n: a read-only file was touched"
done
grep -q "/desk answered 404, not 302" "$ROOT/run4.txt" && grep -q "/desk answered 200, not 302" "$ROOT/run5.txt" && grep -q "/batteries answered 404, not 302" "$ROOT/run6.txt" || fail "outcomes 4-6 did not restore for the right reason"

echo "=== outcome 7: batteries.py not at its FROM pin (another kit moved it) -> REFUSED before anything is placed ==="
reset_root; echo 302 > "$ROOT/web/desk_mode"; echo 302 > "$ROOT/web/bt_mode"
printf '\n# made-up change\n' >> "$ROOT/app/$F"; BM="$(md5 "$ROOT/app/$F")"
bash "$HERE/install_s575.sh" > "$ROOT/run7.txt" 2>&1; R7=$?
grep -E 'REFUSED|NOT INSTALLED' "$ROOT/run7.txt" | sed 's/^/  /'
[ "$R7" = 1 ] && grep -q "REFUSED: batteries.py is" "$ROOT/run7.txt" && grep -q "NOT INSTALLED (nothing was placed)" "$ROOT/run7.txt" || fail "outcome 7 was not refused (exit $R7)"
ls "$ROOT/app/" "$ROOT/finance/" | grep -q "\.bak_S575_" && fail "outcome 7: a backup was made -- the refusal came too late"
[ "$(md5 "$ROOT/app/$F")" = "$BM" ] && [ ! -d "$ROOT/lock" ] || fail "outcome 7: the moved batteries.py was touched or the lock kept"

echo "=== outcome 8: a read-only file moved (sorting_desk.py) -> REFUSED before anything is placed ==="
reset_root
printf '\n# made-up change\n' >> "$ROOT/app/sorting_desk.py"
bash "$HERE/install_s575.sh" > "$ROOT/run8.txt" 2>&1; R8=$?
grep -E 'REFUSED|NOT INSTALLED' "$ROOT/run8.txt" | sed 's/^/  /'
[ "$R8" = 1 ] && grep -q "REFUSED: sorting_desk.py (read only) is" "$ROOT/run8.txt" || fail "outcome 8 was not refused (exit $R8)"
ls "$ROOT/app/" "$ROOT/finance/" | grep -q "\.bak_S575_" && fail "outcome 8: a backup was made -- the refusal came too late"
at_from || fail "outcome 8: batteries.py was touched"

echo "=== outcome 9: no batteries.py (S571 not installed) -> REFUSED before anything is placed ==="
reset_root
rm -f "$ROOT/app/$F"
bash "$HERE/install_s575.sh" > "$ROOT/run9.txt" 2>&1; R9=$?
grep -E 'REFUSED|NOT INSTALLED' "$ROOT/run9.txt" | sed 's/^/  /'
[ "$R9" = 1 ] && grep -q "REFUSED: .*batteries.py is missing -- S571 is not installed" "$ROOT/run9.txt" || fail "outcome 9 was not refused (exit $R9)"
ls "$ROOT/app/" "$ROOT/finance/" | grep -q "\.bak_S575_" && fail "outcome 9: a backup was made -- the refusal came too late"
[ ! -e "$ROOT/app/$F" ] || fail "outcome 9: a batteries.py was placed"

echo "=== outcome 10: the parent's packs.py moved by another kit -> REFUSED before anything is placed (S575 never places it) ==="
reset_root
printf '\n# made-up change by another kit\n' >> "$ROOT/finance/packs.py"; PKM="$(md5 "$ROOT/finance/packs.py")"
bash "$HERE/install_s575.sh" > "$ROOT/run10.txt" 2>&1; R10=$?
grep -E 'REFUSED|NOT INSTALLED' "$ROOT/run10.txt" | sed 's/^/  /'
[ "$R10" = 1 ] && grep -q "REFUSED: packs.py (the parent's, read only) is" "$ROOT/run10.txt" || fail "outcome 10 was not refused (exit $R10)"
[ "$(md5 "$ROOT/finance/packs.py")" = "$PKM" ] || fail "outcome 10: the moved packs.py was touched"
ls "$ROOT/app/" "$ROOT/finance/" | grep -q "\.bak_S575_" && fail "outcome 10: a backup was made -- the refusal came too late"
at_from || fail "outcome 10: batteries.py was touched"

kill "$HPID" 2>/dev/null
[ "$(progs "$LIVE_APP" '*.py *.js')" = "$LIVE_BEFORE" ] || fail "the live scan app's program files changed during the rehearsal"
[ "$(progs "$LIVE_FIN" '*.py *.html')" = "$LIVE_FIN_BEFORE" ] || fail "the live finance folder's program files changed during the rehearsal"
[ "$(md5 "$LIVE_APP/$F")" = "$LIVE_BT" ] || fail "the live batteries.py changed"
ls "$LIVE_APP/" | grep -q "\.bak_S575_" && fail "a .bak_S575_ file appeared in the live scan app"
echo "REHEARSAL GREEN: fresh install green (no data step: the database read back unchanged); ALREADY INSTALLED; forced red restored; /desk 404, /desk 200 and /batteries 404 restored (302 only); a moved batteries.py, a moved read-only file, a missing batteries.py and a moved packs.py refused before placing. The service faked; nothing live was placed or restarted; the live scan app's and finance folder's program files read back unchanged."
[ -n "${KEEP:-}" ] || rm -rf "$ROOT"
exit 0
