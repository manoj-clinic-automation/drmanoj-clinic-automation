#!/bin/bash
# rehearse_s601.sh -- the S601 installer rehearsed on a made-up root under /tmp/s601reh/root (BUILD_NORM_v1 s3, S585's shape). A copy of the
# scan app's files (with S563's five backups, the pre-S559 widget and batteries.py before S582, which the earlier walks compare against), of
# the finance folder's program files (with packs.py before S560 and before S568), of /root/shared and of the scan app's database (SQLite's
# backup API) are put there; every S601_* setting points there (the earlier kits are read, never written, from S601_KITS_DIR); the key file
# is a MADE-UP one in the root (never the live key); the restart is `true`; the service is faked by a stand-in (a small python3 server on a
# free port: /healthz 200, /admin and /bills 302 -- the login gate, as the live app answers a plain request). The build lock is a made-up
# path. Nothing live is placed, restarted or written.
# Outcomes: 1 green (the two files at their TO pins, their backups beside them, the database backed up first and equal to the database
# before; the setting read.sarvam = off written and NOTHING else in the database changed; the lock kept); 2 ALREADY INSTALLED; 3 a forced red
# after placing restores both files (the setting NOT written); 4 /admin 404, 5 /admin 200 (a login gate open), 6 /bills 404 -- each
# restores (302 only); 7 a forced red data step restores (the setting not written); 8 asset_register.py not at its FROM pin, 9 a read-only
# file moved (claude_reader.py), 10 read.claude = off in the database (claude_reader.state is not on), 11 the key file empty -- each REFUSED
# before anything is placed.
# The end guard compares PROGRAM FILES only: (cd "$LIVE_APP" && md5sum -- *.py *.js) | md5sum, and the same over the live finance folder's
# *.py *.html and /root/shared/*.py -- never a directory listing.
# Run as root on the VPS: S601_KITS_DIR=/root/deploy/repo/deploy_kits bash rehearse_s601.sh   (KEEP=1 keeps the made-up root)
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT=/tmp/s601reh/root
LIVE_APP=/root/assetapp
LIVE_FIN=/root/finance
LIVE_SHARED=/root/shared
EDITED="asset_register.py claude_reread.py"
RO="claude_reader.py sorting_desk.py clinic_papers.py batteries.py stationery.py xray_costs.py asset_machine.py scanner_widget.js"
COPY="$EDITED $RO scanner_widget.js.bak_S559_1143c77b batteries.py.bak_S582_40eb8a91"
COPY="$COPY sorting_desk.py.bak_S563_a4623438 clinic_papers.py.bak_S563_88963eac asset_register.py.bak_S563_9daed9ea asset_machine.py.bak_S563_0caec41e scanner_widget.js.bak_S563_1128ac97"
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1"; }
base(){ local b="${1%.py}"; echo "${b%.js}"; }
fail(){ echo "REHEARSAL RED: $*"; [ -n "${HPID:-}" ] && kill "$HPID" 2>/dev/null; exit 1; }
at_from(){ for f in $EDITED; do [ -f "$ROOT/app/$f" ] && [ "$(md5 "$ROOT/app/$f")" = "$(pin PIN_FROM_$(base "$f").txt)" ] || return 1; done; }
at_to(){ for f in $EDITED; do [ -f "$ROOT/app/$f" ] && [ "$(md5 "$ROOT/app/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] || return 1; done; }
ro_ok(){ for f in $RO; do [ "$(md5 "$ROOT/app/$f")" = "$(pin PIN_READ_$(base "$f").txt)" ] || return 1; done; [ "$(md5 "$ROOT/shared/sarvam_ocr.py")" = "$(pin PIN_READ_sarvam_ocr.txt)" ]; }
nobak(){ ! ls "$ROOT/app/" "$ROOT/finance/" | grep -q "\.bak_S601_"; }
reset_root(){ for f in $EDITED $RO; do cp "$ROOT/orig/$f" "$ROOT/app/$f"; done; cp "$ROOT/orig/packs.py" "$ROOT/finance/packs.py"; cp "$ROOT/orig/sarvam_ocr.py" "$ROOT/shared/sarvam_ocr.py"
              cp "$ROOT/orig/assets.db" "$ROOT/app/assets.db"; rm -f "$ROOT/app/"*.bak_S601_* "$ROOT/finance/"*.bak_S601_*; rm -rf "$ROOT/lock"
              printf 'sk-ant-made-up-rehearsal-key-%s\n' "000000000000" > "$ROOT/key/anthropic.key"; }
db_same(){ python3 - "$ROOT/app/assets.db" "$ROOT/orig/assets.db" <<'PYEOF'
import sqlite3, sys
a, b = sqlite3.connect(sys.argv[1]), sqlite3.connect(sys.argv[2])
for (t,) in b.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
    if sorted(map(repr, a.execute('SELECT * FROM "%s"' % t))) != sorted(map(repr, b.execute('SELECT * FROM "%s"' % t))):
        print("  table %s differs" % t); sys.exit(1)
sys.exit(0)
PYEOF
}
progs(){ (cd "$1" && md5sum -- $2 2>/dev/null) | md5sum; }
[ -n "${S601_KITS_DIR:-}" ] && [ -f "$S601_KITS_DIR/S585_STATIONERY_ISSUE_MANY/walk_s585.py" ] || fail "set S601_KITS_DIR to the folder holding the earlier kits, S585 among them (read only)"

rm -rf "$ROOT"; mkdir -p "$ROOT/app/uploads" "$ROOT/shared" "$ROOT/orig" "$ROOT/web" "$ROOT/finance" "$ROOT/key" || fail "no made-up root"
SVC_ENV="$(systemctl show assetapp -p Environment --value 2>/dev/null || true)"
LDB="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"; LDB="${LDB:-$LIVE_APP/assets.db}"; unset SVC_ENV
for f in $COPY; do cp -p "$LIVE_APP/$f" "$ROOT/app/" || fail "copy $f"; done
LIVE_AR="$(md5 "$LIVE_APP/asset_register.py")"; LIVE_RR="$(md5 "$LIVE_APP/claude_reread.py")"
for f in "$LIVE_FIN"/*.py "$LIVE_FIN"/*.html; do case "$f" in *.bak*) ;; *) [ -f "$f" ] && cp "$f" "$ROOT/finance/";; esac; done   # program files only
cp -p "$LIVE_FIN/packs.py.bak_S560_d86d351a" "$LIVE_FIN/packs.py.bak_S568_048d2ad8" "$ROOT/finance/"                          # the earlier walks compare against them
cp "$LIVE_SHARED"/*.py "$ROOT/shared/"
for f in $EDITED $RO; do cp "$ROOT/app/$f" "$ROOT/orig/$f"; done; cp "$ROOT/finance/packs.py" "$ROOT/orig/packs.py"; cp "$ROOT/shared/sarvam_ocr.py" "$ROOT/orig/sarvam_ocr.py"
python3 -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LDB" "$ROOT/app/assets.db" || fail "database copy"
cp "$ROOT/app/assets.db" "$ROOT/orig/assets.db"
printf 'sk-ant-made-up-rehearsal-key-%s\n' "000000000000" > "$ROOT/key/anthropic.key"
at_from || fail "the live asset_register.py / claude_reread.py are not at the kit's FROM pins -- nothing to rehearse"
ro_ok || fail "a live read-only file is not at this kit's pin -- nothing to rehearse"
cat > "$ROOT/web/standin.py" <<'PYEOF'
import http.server, os, sys
WEB = os.path.dirname(os.path.abspath(__file__))
def mode(n, d):
    p = os.path.join(WEB, n)
    return open(p).read().strip() if os.path.exists(p) else d
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = self.path.split("?")[0]
        code = 200 if p == "/healthz" else (int(mode("admin_mode", "404")) if p == "/admin" else (int(mode("bills_mode", "404")) if p == "/bills" else 404))
        self.send_response(code)
        if code == 302:
            self.send_header("Location", "/login?next=" + p)
        self.send_header("Content-Length", "0")
        self.end_headers()
    def log_message(self, *a):
        pass
http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
PYEOF
modes(){ echo "$1" > "$ROOT/web/admin_mode"; echo "$2" > "$ROOT/web/bills_mode"; }
modes 302 302
PORT="$(python3 -c "import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); print(s.getsockname()[1]); s.close()")"
python3 -B "$ROOT/web/standin.py" "$PORT" >/dev/null 2>&1 & HPID=$!
sleep 1

export S601_APP_DIR="$ROOT/app" S601_FIN_DIR="$ROOT/finance" S601_SHARED_DIR="$ROOT/shared" S601_SERVICE="s601-rehearsal-made-up"
export S601_DB="$ROOT/app/assets.db" S601_UPLOADS="$ROOT/app/uploads" S601_KEY_FILE="$ROOT/key/anthropic.key" S601_HEALTH_URL="http://127.0.0.1:$PORT/healthz"
export S601_RESTART_CMD="true" S601_HEALTH_TRIES=3 S601_LOCK="$ROOT/lock" S601_KEEP_SCRATCH=1
export S601_PYTHON="/usr/bin/python3" S601_PYTHON_VENV="/usr/bin/python3" S601_W559_FROM="$ROOT/app/scanner_widget.js.bak_S559_1143c77b"
export S601_PACK_BEFORE="$ROOT/finance/packs.py.bak_S560_d86d351a" S601_PACK_BEFORE_S568="$ROOT/finance/packs.py.bak_S568_048d2ad8"
export S601_BATTERIES_BEFORE_S582="$ROOT/app/batteries.py.bak_S582_40eb8a91" S601_KITS_DIR
for v in S601_APP_DIR S601_FIN_DIR S601_SHARED_DIR S601_DB S601_UPLOADS S601_KEY_FILE S601_LOCK S601_W559_FROM S601_PACK_BEFORE S601_PACK_BEFORE_S568 S601_BATTERIES_BEFORE_S582; do
  p="$(readlink -m "${!v}")"; case "$p" in /root/*) fail "$v resolves to $p -- the rehearsal never touches /root";; esac
done
case "$S601_RESTART_CMD" in *systemctl*) fail "the restart command contains systemctl";; esac
case "$S601_HEALTH_URL" in *:8030*|*:8106*) fail "the health URL is a live service's";; esac
[ "$(curl -s -o /dev/null -w '%{http_code}' "$S601_HEALTH_URL")" = "200" ] || fail "the stand-in health answer is not up"
[ "$(curl -s -o /dev/null -w '%{http_code}' "${S601_HEALTH_URL%/healthz}/admin")" = "302" ] || fail "the stand-in /admin does not answer 302"
echo "made-up root $ROOT; stand-in on port $PORT (/healthz 200, /admin and /bills 302); the restart = true; the key file made-up; the lock made-up; the earlier kits read from $S601_KITS_DIR"
LIVE_BEFORE="$(progs "$LIVE_APP" '*.py *.js')"; LIVE_FIN_BEFORE="$(progs "$LIVE_FIN" '*.py *.html')"; LIVE_SH_BEFORE="$(progs "$LIVE_SHARED" '*.py')"

echo "=== outcome 1: a fresh install (green) ==="
bash "$HERE/install_s601.sh" > "$ROOT/run1.txt" 2>&1; R1=$?
grep -E '^\[|DONE|REFUSED|NOT INSTALLED|control|walk|CONTROL|rebuilt|placed|bak_S601|rehearsal|read.sarvam|healthz|answers|STATE|claude_reader|PINS' "$ROOT/run1.txt" | cut -c1-330 | sed 's/^/  /'
[ "$R1" = 0 ] && grep -q "S601_PHARMACY_BILLS_READ_BY_CLAUDE: DONE." "$ROOT/run1.txt" || fail "outcome 1 was not green (exit $R1)"
at_to || fail "outcome 1: the files are not at their TO pins"
for f in $EDITED; do p="$(pin PIN_FROM_$(base "$f").txt)"; [ -f "$ROOT/app/$f.bak_S601_${p:0:8}" ] && [ "$(md5 "$ROOT/app/$f.bak_S601_${p:0:8}")" = "$p" ] || fail "outcome 1: no backup $f.bak_S601_${p:0:8} with the FROM bytes"; done
ls "$ROOT/app/" | grep -q "assets.db.bak_S601_" || fail "outcome 1: no database backup"
ro_ok || fail "outcome 1: a read-only file was touched"
[ "$(md5 "$ROOT/finance/packs.py")" = "$(pin PIN_READ_packs.txt)" ] || fail "outcome 1: packs.py was touched"
ls "$ROOT/finance/" | grep -q "\.bak_S601_" && fail "outcome 1: something in the finance folder was backed up -- S601 touches nothing there"
[ -d "$ROOT/lock" ] || fail "outcome 1: the build lock was not kept until the report (CLAUDE.md)"
python3 - "$ROOT/app/assets.db" "$ROOT/orig/assets.db" "$(ls "$ROOT/app/"assets.db.bak_S601_* | head -1)" <<'PYEOF' || fail "outcome 1: the database changed beyond the setting read.sarvam = off -- or the backup differs from the database before"
import sqlite3, sys
a, b, k = sqlite3.connect(sys.argv[1]), sqlite3.connect(sys.argv[2]), sqlite3.connect(sys.argv[3])
def objs(c):
    return {(r[0], r[1]) for r in c.execute("SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}
def rows(c, t):
    return sorted(map(repr, c.execute('SELECT * FROM "%s"' % t)))
sa, sb, sk = objs(a), objs(b), objs(k)
same, nt = True, 0
for kind, t in sorted(sb):
    if kind != "table":
        continue
    nt += 1
    if rows(k, t) != rows(b, t):
        same = False; print("  the backup's table %s differs from the database before" % t)
    if t == "settings":
        new = {r[0]: r[1] for r in a.execute("SELECT key, value FROM settings")}
        old = {r[0]: r[1] for r in b.execute("SELECT key, value FROM settings")}
        added = {x: v for x, v in new.items() if x not in old}
        changed = {x: (old[x], new.get(x)) for x in old if new.get(x) != old[x]}
        if changed or sorted(added) != ["read.sarvam"] or added.get("read.sarvam") != "off":
            same = False; print("  settings differ beyond read.sarvam = off: added %s changed %s" % (sorted(added), changed))
        print("  settings: added %s; changed %s" % (added, changed))
        continue
    if rows(a, t) != rows(b, t):
        same = False; print("  table %s differs" % t)
print("  database: objects added %s; every row of the %d tables unchanged but the one setting %s; the backup equal to the database before %s" % (sorted(n for _k, n in sa - sb), nt, same, sk == sb))
sys.exit(0 if (sa == sb and sk == sb and same) else 1)
PYEOF
grep -q "UNDO (one line): \\\\cp -p .*asset_register.py.bak_S601_c39c084e .*asset_register.py && \\\\cp -p .*claude_reread.py.bak_S601_d9b75e78 .*claude_reread.py && systemctl restart s601-rehearsal-made-up$" "$ROOT/run1.txt" || fail "outcome 1: the undo line does not put back both backups, or restarts more than the scan app"
grep -q "clinic-finance" "$ROOT/run1.txt" && fail "outcome 1: the finance service was named -- S601 restarts assetapp only"
grep -q "Claude: ON" "$ROOT/run1.txt" && grep -q "Sarvam: OFF" "$ROOT/run1.txt" || fail "outcome 1: the state after does not read Claude ON / Sarvam OFF"
echo "  made-up root after outcome 1: both files at their TO pins, their .bak_S601_ beside them (the FROM bytes); the read-only files, sarvam_ocr.py and packs.py untouched; the database backed up first; only read.sarvam = off added; the lock kept"
cp "$ROOT/run1.txt" "$ROOT/../run1_kept.txt" 2>/dev/null

echo "=== outcome 2: the same line again (ALREADY INSTALLED) ==="
rm -rf "$ROOT/lock"
bash "$HERE/install_s601.sh" > "$ROOT/run2.txt" 2>&1; R2=$?
sed 's/^/  /' "$ROOT/run2.txt" | tail -3 | cut -c1-300
[ "$R2" = 0 ] && grep -q "ALREADY INSTALLED" "$ROOT/run2.txt" || fail "outcome 2 did not say ALREADY INSTALLED"
grep -q "read.sarvam = off" "$ROOT/run2.txt" || fail "outcome 2: the setting is not read back as off"
at_to || fail "outcome 2: the files moved"

for oc in "3:forced" "4:adm404" "5:adm200" "6:bills404" "7:data"; do
  n=${oc%%:*}; k=${oc##*:}
  reset_root; modes 302 302
  case "$k" in
    forced) echo "=== outcome 3: a forced red after placing (restores both files; the setting not written) ==="; export S601_FORCE_RED=1;;
    adm404) echo "=== outcome 4: healthz 200 but /admin does not answer (404) -> restores ==="; modes 404 302;;
    adm200) echo "=== outcome 5: /admin answers 200 -- a login gate open is not accepted -> restores ==="; modes 200 302;;
    bills404) echo "=== outcome 6: /bills does not answer (404) -> restores ==="; modes 302 404;;
    data) echo "=== outcome 7: a forced red data step -> restores (the setting not written) ==="; export S601_FORCE_DATA_RED=1;;
  esac
  bash "$HERE/install_s601.sh" > "$ROOT/run$n.txt" 2>&1; RR=$?; unset S601_FORCE_RED S601_FORCE_DATA_RED
  grep -E 'forced|RESTOR|/admin|/bills|NOT INSTALLED|DONE|back at' "$ROOT/run$n.txt" | cut -c1-260 | sed 's/^/  /'
  [ "$RR" = 1 ] && grep -q "NOT INSTALLED (restored" "$ROOT/run$n.txt" || fail "outcome $n did not restore (exit $RR)"
  at_from || fail "outcome $n: the files are not back at their FROM pins"
  ro_ok || fail "outcome $n: a read-only file was touched"
  db_same || fail "outcome $n: the database changed (the setting must not be written on a red)"
  rm -rf "$ROOT/lock"
done
grep -q "/admin answered 404, not 302" "$ROOT/run4.txt" && grep -q "/admin answered 200, not 302" "$ROOT/run5.txt" && grep -q "/bills answered 404, not 302" "$ROOT/run6.txt" && grep -q "the data step is forced red" "$ROOT/run7.txt" || fail "outcomes 4-7 did not restore for the right reason"

refused(){ # n, what, the grep for its reason
  bash "$HERE/install_s601.sh" > "$ROOT/run$1.txt" 2>&1; RX=$?
  grep -E 'REFUSED|NOT INSTALLED' "$ROOT/run$1.txt" | cut -c1-260 | sed 's/^/  /'
  [ "$RX" = 1 ] && grep -q "$3" "$ROOT/run$1.txt" && grep -q "NOT INSTALLED (nothing was placed)" "$ROOT/run$1.txt" || fail "outcome $1 ($2) was not refused (exit $RX)"
  nobak || fail "outcome $1: a backup was made -- the refusal came too late"
  [ ! -d "$ROOT/lock" ] || fail "outcome $1: the lock was kept"
  db_same || fail "outcome $1: the database changed"
}
echo "=== outcome 8: asset_register.py not at its FROM pin (a wrong FROM byte) -> REFUSED before anything is placed ==="
reset_root; modes 302 302
printf '\n# made-up change\n' >> "$ROOT/app/asset_register.py"; SM="$(md5 "$ROOT/app/asset_register.py")"
refused 8 "asset_register moved" "REFUSED: asset_register.py is"
[ "$(md5 "$ROOT/app/asset_register.py")" = "$SM" ] || fail "outcome 8: the moved asset_register.py was touched"

echo "=== outcome 9: a read-only file moved (claude_reader.py) -> REFUSED before anything is placed ==="
reset_root
printf '\n# made-up change\n' >> "$ROOT/app/claude_reader.py"
refused 9 "read-only moved" "REFUSED: claude_reader.py (read only) is"
at_from || fail "outcome 9: the two files were touched"

echo "=== outcome 10: read.claude = off in the database (claude_reader.state is not on) -> REFUSED before anything is placed ==="
reset_root
python3 -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute(\"INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')\"); c.commit(); c.close()" "$ROOT/app/assets.db"
cp "$ROOT/app/assets.db" "$ROOT/orig/assets.db.off" && cp "$ROOT/orig/assets.db" "$ROOT/orig/assets.db.keep" && cp "$ROOT/orig/assets.db.off" "$ROOT/orig/assets.db"
refused 10 "Claude off" "claude_reader.state is 'off', not 'on': STOP"
cp "$ROOT/orig/assets.db.keep" "$ROOT/orig/assets.db"; rm -f "$ROOT/orig/assets.db.off" "$ROOT/orig/assets.db.keep"
at_from || fail "outcome 10: the two files were touched"

echo "=== outcome 11: the key file empty -> REFUSED before anything is placed ==="
reset_root
: > "$ROOT/key/anthropic.key"
refused 11 "no key" "the Claude key file is absent or empty"
at_from || fail "outcome 11: the two files were touched"

kill "$HPID" 2>/dev/null
[ "$(progs "$LIVE_APP" '*.py *.js')" = "$LIVE_BEFORE" ] || fail "the live scan app's program files changed during the rehearsal"
[ "$(progs "$LIVE_FIN" '*.py *.html')" = "$LIVE_FIN_BEFORE" ] || fail "the live finance folder's program files changed during the rehearsal"
[ "$(progs "$LIVE_SHARED" '*.py')" = "$LIVE_SH_BEFORE" ] || fail "the live /root/shared changed during the rehearsal"
[ "$(md5 "$LIVE_APP/asset_register.py")" = "$LIVE_AR" ] && [ "$(md5 "$LIVE_APP/claude_reread.py")" = "$LIVE_RR" ] || fail "a live file changed"
ls "$LIVE_APP/" | grep -q "\.bak_S601_" && fail "a .bak_S601_ file appeared in the live scan app"
echo "REHEARSAL GREEN: fresh install green (the two files placed, their backups beside them, the database backed up first, only read.sarvam = off written, the lock kept); ALREADY INSTALLED; forced red restored (the setting not written); /admin 404, /admin 200, /bills 404 and a forced red data step restored (302 only); a moved asset_register.py, a moved read-only file, Claude off and an empty key file refused before placing. The service faked; nothing live was placed, restarted or written; the live scan app's, finance folder's and /root/shared's program files read back unchanged."
[ -n "${KEEP:-}" ] || rm -rf "$ROOT"
exit 0
