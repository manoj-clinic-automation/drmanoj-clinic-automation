#!/bin/bash
# rehearse_s571.sh -- the S571 installer rehearsed on a made-up root under /tmp/s571reh/root (BUILD_NORM_v1 s3, S568's shape). A copy
# of the scan app's files (with S563's five backups and the pre-S559 widget, which the earlier walks compare against), of the finance
# folder's program files (with packs.py before S560 and before S568) and of the scan app's database (SQLite's backup API) are put
# there; every S571_* setting points there (the earlier kits are read, never written, from S571_KITS_DIR); the restart is `true`, the
# service is faked by a stand-in (a small python3 server on a free port: /healthz 200, /desk and /batteries 302 -- the login gate, as
# the live app answers a plain request). The build lock is a made-up path. Nothing live is placed or restarted.
# Outcomes: 1 green (the data step's three tables, two indexes, 15 seeded places and one setting -- nothing else in the database
# changed); 2 ALREADY INSTALLED; 3 a forced red after placing restores every file (batteries.py removed); 4 /desk not answering (404)
# restores; 5 /desk answering 200 (a login gate open) restores -- 302 only; 6 /batteries not answering (404: batteries.py did not
# mount) restores; 7 a live file not at its FROM pin is REFUSED before anything is placed; 8 a read-only file moved (stationery.py)
# is REFUSED before anything is placed; 9 a batteries.py already there with other bytes is REFUSED before anything is placed;
# 10 the parent's packs.py moved by another kit is REFUSED before anything is placed (S571 never places it).
# The end guard compares PROGRAM FILES only (S568 K2 N2): (cd "$LIVE_FIN" && md5sum -- *.py *.html 2>/dev/null) | md5sum, and the
# same over the live scan app's *.py *.js -- never a directory listing (the live apps' own logs and journals come and go).
# Run as root on the VPS: S571_KITS_DIR=/root/deploy/repo/deploy_kits bash rehearse_s571.sh   (KEEP=1 keeps the made-up root)
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT=/tmp/s571reh/root
LIVE_APP=/root/assetapp
LIVE_FIN=/root/finance
LIVE_SHARED=/root/shared
EDITED="sorting_desk.py asset_register.py"
RO="clinic_papers.py stationery.py asset_machine.py scanner_widget.js claude_reader.py claude_reread.py"
COPY="$EDITED $RO scanner_widget.js.bak_S559_1143c77b"
COPY="$COPY sorting_desk.py.bak_S563_a4623438 clinic_papers.py.bak_S563_88963eac asset_register.py.bak_S563_9daed9ea asset_machine.py.bak_S563_0caec41e scanner_widget.js.bak_S563_1128ac97"
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1"; }
base(){ local b="${1%.py}"; echo "${b%.js}"; }
fail(){ echo "REHEARSAL RED: $*"; [ -n "${HPID:-}" ] && kill "$HPID" 2>/dev/null; exit 1; }
at_from(){ for f in $EDITED; do [ "$(md5 "$ROOT/app/$f")" = "$(pin PIN_FROM_$(base "$f").txt)" ] || return 1; done; [ ! -e "$ROOT/app/batteries.py" ] || return 1; }
at_to(){ for f in $EDITED; do [ "$(md5 "$ROOT/app/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] || return 1; done
         [ "$(md5 "$ROOT/app/batteries.py")" = "$(pin PIN_TO_batteries.txt)" ] || return 1; }
reset_root(){ for f in $EDITED stationery.py; do cp "$ROOT/orig/$f" "$ROOT/app/$f"; done; rm -f "$ROOT/app/batteries.py"; cp "$ROOT/orig/packs.py" "$ROOT/finance/packs.py"
              cp "$ROOT/orig/assets.db" "$ROOT/app/assets.db"; rm -f "$ROOT/app/"*.bak_S571_* "$ROOT/finance/"*.bak_S571_*; rm -rf "$ROOT/lock"; }
progs(){ (cd "$1" && md5sum -- $2 2>/dev/null) | md5sum; }
[ -n "${S571_KITS_DIR:-}" ] && [ -f "$S571_KITS_DIR/S568_STATIONERY_STOCK/walk_s568.py" ] || fail "set S571_KITS_DIR to the folder holding the earlier kits (read only)"

rm -rf "$ROOT"; mkdir -p "$ROOT/app/uploads" "$ROOT/shared" "$ROOT/orig" "$ROOT/web" "$ROOT/finance" || fail "no made-up root"
SVC_ENV="$(systemctl show assetapp -p Environment --value 2>/dev/null || true)"
LDB="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"; LDB="${LDB:-$LIVE_APP/assets.db}"; unset SVC_ENV
for f in $COPY; do cp -p "$LIVE_APP/$f" "$ROOT/app/" || fail "copy $f"; done
[ -e "$LIVE_APP/batteries.py" ] && fail "the live scan app already holds a batteries.py -- nothing to rehearse"
for f in "$LIVE_FIN"/*.py "$LIVE_FIN"/*.html; do case "$f" in *.bak*) ;; *) [ -f "$f" ] && cp "$f" "$ROOT/finance/";; esac; done   # program files only
cp -p "$LIVE_FIN/packs.py.bak_S560_d86d351a" "$LIVE_FIN/packs.py.bak_S568_048d2ad8" "$ROOT/finance/"                          # the earlier walks compare against them
for f in $EDITED stationery.py; do cp "$ROOT/app/$f" "$ROOT/orig/$f"; done; cp "$ROOT/finance/packs.py" "$ROOT/orig/packs.py"
cp "$LIVE_SHARED"/*.py "$ROOT/shared/"
python3 -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LDB" "$ROOT/app/assets.db" || fail "database copy"
cp "$ROOT/app/assets.db" "$ROOT/orig/assets.db"
at_from || fail "the live files are not at the kit's FROM pins -- nothing to rehearse"
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

export S571_APP_DIR="$ROOT/app" S571_FIN_DIR="$ROOT/finance" S571_SERVICE="s571-rehearsal-made-up"
export S571_DB="$ROOT/app/assets.db" S571_HEALTH_URL="http://127.0.0.1:$PORT/healthz"
export S571_RESTART_CMD="true" S571_SHARED_DIR="$ROOT/shared" S571_HEALTH_TRIES=3 S571_LOCK="$ROOT/lock"
export S571_PYTHON="python3" S571_PYTHON_VENV="/usr/bin/python3" S571_W559_FROM="$ROOT/app/scanner_widget.js.bak_S559_1143c77b"
export S571_PACK_BEFORE="$ROOT/finance/packs.py.bak_S560_d86d351a" S571_PACK_BEFORE_S568="$ROOT/finance/packs.py.bak_S568_048d2ad8" S571_KITS_DIR
for v in S571_APP_DIR S571_FIN_DIR S571_DB S571_SHARED_DIR S571_PYTHON_VENV S571_LOCK S571_W559_FROM S571_PACK_BEFORE S571_PACK_BEFORE_S568; do
  p="$(readlink -m "${!v}")"; case "$p" in /root/*) [ "$v" = S571_PYTHON_VENV ] || fail "$v resolves to $p -- the rehearsal never touches /root";; esac
done
case "$S571_RESTART_CMD" in *systemctl*) fail "the restart command contains systemctl";; esac
case "$S571_HEALTH_URL" in *:8030*|*:8106*) fail "the health URL is a live service's";; esac
[ "$(curl -s -o /dev/null -w '%{http_code}' "$S571_HEALTH_URL")" = "200" ] || fail "the stand-in health answer is not up"
[ "$(curl -s -o /dev/null -w '%{http_code}' "${S571_HEALTH_URL%/healthz}/desk")" = "302" ] || fail "the stand-in /desk does not answer 302"
echo "made-up root $ROOT; stand-in on port $PORT (/healthz 200, /desk and /batteries 302); the restart = true; the lock made-up; the earlier kits read from $S571_KITS_DIR"
LIVE_BEFORE="$(progs "$LIVE_APP" '*.py *.js')"; LIVE_FIN_BEFORE="$(progs "$LIVE_FIN" '*.py *.html')"

echo "=== outcome 1: a fresh install (green) ==="
bash "$HERE/install_s571.sh" > "$ROOT/run1.txt" 2>&1; R1=$?
grep -E '^\[|DONE|REFUSED|NOT INSTALLED|walk|control|CONTROL|TIDY|answer|healthz|PINS|rebuilt|tidy comparison|present|absent|battery|second run' "$ROOT/run1.txt" | cut -c1-330 | sed 's/^/  /'
[ "$R1" = 0 ] && grep -q "S571_BATTERIES: DONE." "$ROOT/run1.txt" || fail "outcome 1 was not green (exit $R1)"
at_to || fail "outcome 1: the placed files are not at the TO pins"
for f in $EDITED; do ls "$ROOT/app/" | grep -q "^$f.bak_S571_" || fail "outcome 1: no backup beside $f"; done
ls "$ROOT/app/" | grep -q "assets.db.bak_S571_" || fail "outcome 1: no database backup"
for f in $RO; do [ "$(md5 "$ROOT/app/$f")" = "$(pin PIN_READ_$(base "$f").txt)" ] || fail "outcome 1: $f (read only) was touched"; done
[ "$(md5 "$ROOT/finance/packs.py")" = "$(pin PIN_READ_packs.txt)" ] || fail "outcome 1: packs.py was touched"
ls "$ROOT/finance/" | grep -q "\.bak_S571_" && fail "outcome 1: something in the finance folder was backed up -- S571 touches nothing there"
python3 - "$ROOT/app/assets.db" "$ROOT/orig/assets.db" "$(ls "$ROOT/app/"assets.db.bak_S571_* | head -1)" <<'PYEOF' || fail "outcome 1: the database changed by more than the three tables, two indexes, the seeded places and batteries.since -- or a row changed, or the backup was not taken before the data step"
import sqlite3, sys
a, b, k = sqlite3.connect(sys.argv[1]), sqlite3.connect(sys.argv[2]), sqlite3.connect(sys.argv[3])
def objs(c):
    return {(r[0], r[1]) for r in c.execute("SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}
sa, sb, sk = objs(a), objs(b), objs(k)
new = sa - sb
want = {("table", "battery_place"), ("table", "battery_fit"), ("table", "battery_upkeep"), ("index", "battery_place_asset"), ("index", "battery_fit_place")}
same_rows = True
for kind, t in sb:
    if kind != "table":
        continue
    cols = [r[1] for r in b.execute('PRAGMA table_info("%s")' % t)]
    q = 'SELECT %s FROM "%s"' % (",".join('"%s"' % c for c in cols), t)
    ra, rb = sorted(map(repr, a.execute(q))), sorted(map(repr, b.execute(q)))
    if t == "settings":
        extra = sorted(set(ra) - set(rb)); gone = sorted(set(rb) - set(ra))
        if gone or len(extra) != 1 or "batteries.since" not in extra[0]:
            same_rows = False; print("  settings differ: gone %d, added %d" % (len(gone), len(extra)))
    elif ra != rb:
        same_rows = False; print("  table %s differs" % t)
seeded = a.execute("SELECT COUNT(*) FROM battery_place WHERE seed_key IS NOT NULL").fetchone()[0]
print("  database: new %s; every old row unchanged (settings: only batteries.since added) %s; seeded places %d; the backup has the old shape %s"
      % (sorted(n for _t, n in new), same_rows, seeded, sk == sb))
sys.exit(0 if (new == want and not (sb - sa) and same_rows and seeded == 15 and sk == sb) else 1)
PYEOF
grep -q "a second run: batteries S571: tables ready (battery_place, battery_fit, battery_upkeep); battery places 15" "$ROOT/run1.txt" || fail "outcome 1: the data step's second run did not leave 15 places (not idempotent)"
grep -q "UNDO (one line): \\\\cp -p " "$ROOT/run1.txt" && grep -q "batteries.py.off_S571 && systemctl restart s571-rehearsal-made-up" "$ROOT/run1.txt" || fail "outcome 1: the undo line does not start with \\cp -p, does not take batteries.py out, or restarts more than the scan app"
grep -q "clinic-finance" "$ROOT/run1.txt" && fail "outcome 1: the finance service was named -- S571 restarts assetapp only"
[ ! -d "$ROOT/lock" ] || fail "outcome 1: the build lock was not released"
echo "  made-up root after outcome 1: the three scan-app files at the TO pins; backups beside them; the read-only files and packs.py untouched; the database backed up before the data step, grown by exactly three tables, two indexes, the 15 seeded places and batteries.since, no other row changed; the lock released"

echo "=== outcome 2: the same line again (ALREADY INSTALLED) ==="
bash "$HERE/install_s571.sh" > "$ROOT/run2.txt" 2>&1; R2=$?
sed 's/^/  /' "$ROOT/run2.txt" | tail -2 | cut -c1-300
[ "$R2" = 0 ] && grep -q "ALREADY INSTALLED" "$ROOT/run2.txt" || fail "outcome 2 did not say ALREADY INSTALLED"
N2="$(python3 -c "import sqlite3,sys; print(sqlite3.connect(sys.argv[1]).execute('SELECT COUNT(*) FROM battery_place').fetchone()[0])" "$ROOT/app/assets.db")"
[ "$N2" = 15 ] || fail "outcome 2: a second run changed the places ($N2)"

for oc in "3:forced" "4:desk404" "5:desk200" "6:bt404"; do
  n=${oc%%:*}; k=${oc##*:}
  reset_root; echo 302 > "$ROOT/web/desk_mode"; echo 302 > "$ROOT/web/bt_mode"
  case "$k" in
    forced) echo "=== outcome 3: a forced red after placing (restores every file) ==="; export S571_FORCE_RED=1;;
    desk404) echo "=== outcome 4: healthz 200 but /desk does not answer (404) -> restores ==="; echo 404 > "$ROOT/web/desk_mode";;
    desk200) echo "=== outcome 5: /desk answers 200 -- a login gate open is not accepted -> restores ==="; echo 200 > "$ROOT/web/desk_mode";;
    bt404) echo "=== outcome 6: /batteries does not answer (404: batteries.py did not mount) -> restores ==="; echo 404 > "$ROOT/web/bt_mode";;
  esac
  bash "$HERE/install_s571.sh" > "$ROOT/run$n.txt" 2>&1; RR=$?; unset S571_FORCE_RED
  grep -E 'forced|RESTOR|/desk|/batteries|NOT INSTALLED|DONE|files back' "$ROOT/run$n.txt" | cut -c1-260 | sed 's/^/  /'
  [ "$RR" = 1 ] && grep -q "NOT INSTALLED (restored" "$ROOT/run$n.txt" || fail "outcome $n did not restore (exit $RR)"
  at_from || fail "outcome $n: the files are not back at the FROM pins (or batteries.py is still there)"
done
grep -q "/desk answered 404, not 302" "$ROOT/run4.txt" && grep -q "/desk answered 200, not 302" "$ROOT/run5.txt" && grep -q "/batteries answered 404, not 302" "$ROOT/run6.txt" || fail "outcomes 4-6 did not restore for the right reason"

echo "=== outcome 7: a live file not at its FROM pin (another kit moved it) -> REFUSED before anything is placed ==="
reset_root; echo 302 > "$ROOT/web/desk_mode"; echo 302 > "$ROOT/web/bt_mode"
printf '\n# made-up change\n' >> "$ROOT/app/sorting_desk.py"
bash "$HERE/install_s571.sh" > "$ROOT/run7.txt" 2>&1; R7=$?
grep -E 'REFUSED|NOT INSTALLED' "$ROOT/run7.txt" | sed 's/^/  /'
[ "$R7" = 1 ] && grep -q "REFUSED: sorting_desk.py is" "$ROOT/run7.txt" && grep -q "NOT INSTALLED (nothing was placed)" "$ROOT/run7.txt" || fail "outcome 7 was not refused (exit $R7)"
ls "$ROOT/app/" "$ROOT/finance/" | grep -q "\.bak_S571_" && fail "outcome 7: a backup was made -- the refusal came too late"
[ ! -e "$ROOT/app/batteries.py" ] && [ ! -d "$ROOT/lock" ] || fail "outcome 7: batteries.py placed or the lock kept"

echo "=== outcome 8: a read-only file moved (stationery.py) -> REFUSED before anything is placed ==="
reset_root
printf '\n# made-up change\n' >> "$ROOT/app/stationery.py"
bash "$HERE/install_s571.sh" > "$ROOT/run8.txt" 2>&1; R8=$?
grep -E 'REFUSED|NOT INSTALLED' "$ROOT/run8.txt" | sed 's/^/  /'
[ "$R8" = 1 ] && grep -q "REFUSED: stationery.py (read only) is" "$ROOT/run8.txt" || fail "outcome 8 was not refused (exit $R8)"
ls "$ROOT/app/" "$ROOT/finance/" | grep -q "\.bak_S571_" && fail "outcome 8: a backup was made -- the refusal came too late"
at_from || fail "outcome 8: an edited file was touched"

echo "=== outcome 9: a batteries.py already there with other bytes -> REFUSED before anything is placed ==="
reset_root
printf '# made-up batteries.py, not this kit'"'"'s\n' > "$ROOT/app/batteries.py"
bash "$HERE/install_s571.sh" > "$ROOT/run9.txt" 2>&1; R9=$?
grep -E 'REFUSED|NOT INSTALLED' "$ROOT/run9.txt" | sed 's/^/  /'
[ "$R9" = 1 ] && grep -q "REFUSED: batteries.py is already in" "$ROOT/run9.txt" || fail "outcome 9 was not refused (exit $R9)"
ls "$ROOT/app/" "$ROOT/finance/" | grep -q "\.bak_S571_" && fail "outcome 9: a backup was made -- the refusal came too late"
grep -q "made-up batteries.py" "$ROOT/app/batteries.py" || fail "outcome 9: the other batteries.py was touched"
rm -f "$ROOT/app/batteries.py"; at_from || fail "outcome 9: an edited file was touched"

echo "=== outcome 10: the parent's packs.py moved by another kit -> REFUSED before anything is placed (S571 never places it) ==="
reset_root
printf '\n# made-up change by another kit\n' >> "$ROOT/finance/packs.py"; PKM="$(md5 "$ROOT/finance/packs.py")"
bash "$HERE/install_s571.sh" > "$ROOT/run10.txt" 2>&1; R10=$?
grep -E 'REFUSED|NOT INSTALLED' "$ROOT/run10.txt" | sed 's/^/  /'
[ "$R10" = 1 ] && grep -q "REFUSED: packs.py (the parent's, read only) is" "$ROOT/run10.txt" || fail "outcome 10 was not refused (exit $R10)"
[ "$(md5 "$ROOT/finance/packs.py")" = "$PKM" ] || fail "outcome 10: the moved packs.py was touched"
ls "$ROOT/app/" "$ROOT/finance/" | grep -q "\.bak_S571_" && fail "outcome 10: a backup was made -- the refusal came too late"
at_from || fail "outcome 10: an edited file was touched"

kill "$HPID" 2>/dev/null
[ "$(progs "$LIVE_APP" '*.py *.js')" = "$LIVE_BEFORE" ] || fail "the live scan app's program files changed during the rehearsal"
[ "$(progs "$LIVE_FIN" '*.py *.html')" = "$LIVE_FIN_BEFORE" ] || fail "the live finance folder's program files changed during the rehearsal"
[ ! -e "$LIVE_APP/batteries.py" ] || fail "a batteries.py appeared in the live scan app"
echo "REHEARSAL GREEN: fresh install green; ALREADY INSTALLED; forced red restored; /desk 404, /desk 200 and /batteries 404 restored (302 only); a moved file, a moved read-only file, a foreign batteries.py and a moved packs.py refused before placing. The service faked; nothing live was placed or restarted; the live scan app's and finance folder's program files read back unchanged."
[ -n "${KEEP:-}" ] || rm -rf "$ROOT"
exit 0
