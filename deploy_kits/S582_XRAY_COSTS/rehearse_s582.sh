#!/bin/bash
# rehearse_s582.sh -- the S582 installer rehearsed on a made-up root under /tmp/s582reh/root (BUILD_NORM_v1 s3, S575's shape). A copy of
# the scan app's files (with S563's five backups and the pre-S559 widget, which the earlier walks compare against), of the finance folder's
# program files (with packs.py before S560 and before S568) and of the scan app's database (SQLite's backup API) are put there; every
# S582_* setting points there (the earlier kits are read, never written, from S582_KITS_DIR); the restart is `true`; the service is faked by
# a stand-in (a small python3 server on a free port: /healthz 200, /desk, /batteries and /xray 302 -- the login gate, as the live app
# answers a plain request). The build lock is a made-up path. Nothing live is placed or restarted.
# Outcomes: 1 green (the data step on the made-up root's copy: only the table xray_mark, its index and its seed rows + their audit lines
# added; every other table's rows unchanged; the backup taken and equal to the database before); 2 ALREADY INSTALLED; 3 a forced red after
# placing restores batteries.py and takes xray_costs.py out; 4 /desk 404, 5 /desk 200 (a login gate open), 6 /xray 404 -- each restores
# (302 only); 7 batteries.py not at its FROM pin, 8 a read-only file moved (sorting_desk.py), 9 no batteries.py, 10 the parent's packs.py
# moved, 11 an xray_costs.py already in the folder (not this kit's), 12 a half install (batteries.py at the TO pin, no xray_costs.py) --
# each REFUSED before anything is placed.
# The end guard compares PROGRAM FILES only: (cd "$LIVE_FIN" && md5sum -- *.py *.html) | md5sum, and the same over the live scan app's
# *.py *.js -- never a directory listing.
# Run as root on the VPS: S582_KITS_DIR=/root/deploy/repo/deploy_kits bash rehearse_s582.sh   (KEEP=1 keeps the made-up root)
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT=/tmp/s582reh/root
LIVE_APP=/root/assetapp
LIVE_FIN=/root/finance
LIVE_SHARED=/root/shared
F="batteries.py"
N="xray_costs.py"
RO="sorting_desk.py asset_register.py clinic_papers.py stationery.py asset_machine.py scanner_widget.js claude_reader.py claude_reread.py"
COPY="$F $RO scanner_widget.js.bak_S559_1143c77b"
COPY="$COPY sorting_desk.py.bak_S563_a4623438 clinic_papers.py.bak_S563_88963eac asset_register.py.bak_S563_9daed9ea asset_machine.py.bak_S563_0caec41e scanner_widget.js.bak_S563_1128ac97"
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1"; }
base(){ local b="${1%.py}"; echo "${b%.js}"; }
fail(){ echo "REHEARSAL RED: $*"; [ -n "${HPID:-}" ] && kill "$HPID" 2>/dev/null; exit 1; }
at_from(){ [ -f "$ROOT/app/$F" ] && [ "$(md5 "$ROOT/app/$F")" = "$(pin PIN_FROM_batteries.txt)" ] && [ ! -e "$ROOT/app/$N" ]; }
at_to(){ [ -f "$ROOT/app/$F" ] && [ "$(md5 "$ROOT/app/$F")" = "$(pin PIN_TO_batteries.txt)" ] && [ "$(md5 "$ROOT/app/$N")" = "$(pin PIN_TO_xray_costs.txt)" ]; }
ro_ok(){ for f in $RO; do [ "$(md5 "$ROOT/app/$f")" = "$(pin PIN_READ_$(base "$f").txt)" ] || return 1; done; }
nobak(){ ! ls "$ROOT/app/" "$ROOT/finance/" | grep -q "\.bak_S582_"; }
reset_root(){ for f in $F sorting_desk.py; do cp "$ROOT/orig/$f" "$ROOT/app/$f"; done; cp "$ROOT/orig/packs.py" "$ROOT/finance/packs.py"
              cp "$ROOT/orig/assets.db" "$ROOT/app/assets.db"; rm -f "$ROOT/app/"*.bak_S582_* "$ROOT/finance/"*.bak_S582_* "$ROOT/app/$N" "$ROOT/app/$N.undone_S582"; rm -rf "$ROOT/lock"; }
progs(){ (cd "$1" && md5sum -- $2 2>/dev/null) | md5sum; }
[ -n "${S582_KITS_DIR:-}" ] && [ -f "$S582_KITS_DIR/S575_BATTERY_SETUP/walk_s575.py" ] || fail "set S582_KITS_DIR to the folder holding the earlier kits (read only)"

rm -rf "$ROOT"; mkdir -p "$ROOT/app/uploads" "$ROOT/shared" "$ROOT/orig" "$ROOT/web" "$ROOT/finance" || fail "no made-up root"
SVC_ENV="$(systemctl show assetapp -p Environment --value 2>/dev/null || true)"
LDB="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"; LDB="${LDB:-$LIVE_APP/assets.db}"; unset SVC_ENV
for f in $COPY; do cp -p "$LIVE_APP/$f" "$ROOT/app/" || fail "copy $f"; done
[ -e "$LIVE_APP/$N" ] && fail "the live scan app already has $N -- nothing to rehearse"
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
                                            (int(mode("bt_mode", "404")) if p == "/batteries" else
                                             (int(mode("xr_mode", "404")) if p == "/xray" else 404)))
        self.send_response(code)
        if code == 302:
            self.send_header("Location", "/login?next=" + p)
        self.send_header("Content-Length", "0")
        self.end_headers()
    def log_message(self, *a):
        pass
http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
PYEOF
modes(){ echo "$1" > "$ROOT/web/desk_mode"; echo "$2" > "$ROOT/web/bt_mode"; echo "$3" > "$ROOT/web/xr_mode"; }
modes 302 302 302
PORT="$(python3 -c "import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); print(s.getsockname()[1]); s.close()")"
python3 -B "$ROOT/web/standin.py" "$PORT" >/dev/null 2>&1 & HPID=$!
sleep 1

export S582_APP_DIR="$ROOT/app" S582_FIN_DIR="$ROOT/finance" S582_SERVICE="s582-rehearsal-made-up"
export S582_DB="$ROOT/app/assets.db" S582_HEALTH_URL="http://127.0.0.1:$PORT/healthz"
export S582_RESTART_CMD="true" S582_SHARED_DIR="$ROOT/shared" S582_HEALTH_TRIES=3 S582_LOCK="$ROOT/lock"
export S582_PYTHON="python3" S582_PYTHON_VENV="/usr/bin/python3" S582_W559_FROM="$ROOT/app/scanner_widget.js.bak_S559_1143c77b"
export S582_PACK_BEFORE="$ROOT/finance/packs.py.bak_S560_d86d351a" S582_PACK_BEFORE_S568="$ROOT/finance/packs.py.bak_S568_048d2ad8" S582_KITS_DIR
for v in S582_APP_DIR S582_FIN_DIR S582_DB S582_SHARED_DIR S582_PYTHON_VENV S582_LOCK S582_W559_FROM S582_PACK_BEFORE S582_PACK_BEFORE_S568; do
  p="$(readlink -m "${!v}")"; case "$p" in /root/*) [ "$v" = S582_PYTHON_VENV ] || fail "$v resolves to $p -- the rehearsal never touches /root";; esac
done
case "$S582_RESTART_CMD" in *systemctl*) fail "the restart command contains systemctl";; esac
case "$S582_HEALTH_URL" in *:8030*|*:8106*) fail "the health URL is a live service's";; esac
[ "$(curl -s -o /dev/null -w '%{http_code}' "$S582_HEALTH_URL")" = "200" ] || fail "the stand-in health answer is not up"
[ "$(curl -s -o /dev/null -w '%{http_code}' "${S582_HEALTH_URL%/healthz}/xray")" = "302" ] || fail "the stand-in /xray does not answer 302"
echo "made-up root $ROOT; stand-in on port $PORT (/healthz 200, /desk, /batteries and /xray 302); the restart = true; the lock made-up; the earlier kits read from $S582_KITS_DIR"
LIVE_BEFORE="$(progs "$LIVE_APP" '*.py *.js')"; LIVE_FIN_BEFORE="$(progs "$LIVE_FIN" '*.py *.html')"

echo "=== outcome 1: a fresh install (green) ==="
bash "$HERE/install_s582.sh" > "$ROOT/run1.txt" 2>&1; R1=$?
grep -E '^\[|DONE|REFUSED|NOT INSTALLED|walk|control|CONTROL|TIDY|copy|answer|healthz|PINS|rebuilt|tidy comparison|placed|bak_S582|seed:|xray_costs S582|= the kit' "$ROOT/run1.txt" | cut -c1-330 | sed 's/^/  /'
[ "$R1" = 0 ] && grep -q "S582_XRAY_COSTS: DONE." "$ROOT/run1.txt" || fail "outcome 1 was not green (exit $R1)"
at_to || fail "outcome 1: batteries.py / xray_costs.py are not at the TO pins"
ls "$ROOT/app/" | grep -q "^$F.bak_S582_40eb8a91$" || fail "outcome 1: no backup batteries.py.bak_S582_40eb8a91"
[ "$(md5 "$ROOT/app/$F.bak_S582_40eb8a91")" = "$(pin PIN_FROM_batteries.txt)" ] || fail "outcome 1: the backup is not the FROM bytes"
ls "$ROOT/app/" | grep -q "assets.db.bak_S582_" || fail "outcome 1: no database backup"
ro_ok || fail "outcome 1: a read-only file was touched"
[ "$(md5 "$ROOT/finance/packs.py")" = "$(pin PIN_READ_packs.txt)" ] || fail "outcome 1: packs.py was touched"
ls "$ROOT/finance/" | grep -q "\.bak_S582_" && fail "outcome 1: something in the finance folder was backed up -- S582 touches nothing there"
python3 - "$ROOT/app/assets.db" "$ROOT/orig/assets.db" "$(ls "$ROOT/app/"assets.db.bak_S582_* | head -1)" <<'PYEOF' || fail "outcome 1: the database changed beyond the new table and its seed -- or the backup differs"
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
    ra, rb = rows(a, t, cols), rows(b, t, cols)
    if t == "desk_audit":
        old =sorted(map(repr, a.execute('SELECT %s FROM desk_audit WHERE id <= ?' % ",".join('"%s"' % x for x in cols),
                                         (b.execute("SELECT COALESCE(MAX(id),0) FROM desk_audit").fetchone()[0],))))
        new_acts = [r[0] for r in a.execute("SELECT action FROM desk_audit WHERE id > ?", (b.execute("SELECT COALESCE(MAX(id),0) FROM desk_audit").fetchone()[0],))]
        if old != rb or any(x != "xray_mark_seed" for x in new_acts):
            same = False; print("  desk_audit differs beyond the seed's lines")
        print("  desk_audit: the seed added %d line(s) (xray_mark_seed); every earlier line unchanged %s" % (len(new_acts), old == rb))
        continue
    if ra != rb or rows(k, t, cols) != rb:
        same = False; print("  table %s differs" % t)
added = sa - sb
marks = [tuple(r) for r in a.execute("SELECT kind, by_whom FROM xray_mark WHERE removed_at=''")] if ("table", "xray_mark") in sa else []
print("  database: objects added %s; every row of the %d earlier tables unchanged (settings included; desk_audit only appended) %s; the backup "
      "equal to the database before %s; live marks after the data step %d (%s)" % (sorted(n for _k, n in added), nt, same, sk == sb, len(marks),
                                                                                 ", ".join(sorted(set(k_ for k_, _w in marks))) or "none"))
sys.exit(0 if (added == {("table", "xray_mark"), ("index", "xray_mark_live")} and sk == sb and same and all(w == "S582 seed" for _k, w in marks)) else 1)
PYEOF
grep -q "UNDO (one line): \\\\cp -p .*batteries.py.bak_S582_40eb8a91 .*batteries.py && mv -f .*xray_costs.py .*xray_costs.py.undone_S582 && systemctl restart s582-rehearsal-made-up$" "$ROOT/run1.txt" || fail "outcome 1: the undo line does not put back batteries.py.bak_S582_40eb8a91 and take xray_costs.py out, or restarts more than the scan app"
grep -q "clinic-finance" "$ROOT/run1.txt" && fail "outcome 1: the finance service was named -- S582 restarts assetapp only"
[ ! -d "$ROOT/lock" ] || fail "outcome 1: the build lock was not released"
ls -d /tmp/s582_install_* >/dev/null 2>&1 && fail "outcome 1: the installer's scratch under /tmp/s582_install_* was not removed"
echo "  made-up root after outcome 1: batteries.py and xray_costs.py at the TO pins, batteries.py.bak_S582_40eb8a91 beside them (the FROM bytes); the read-only files and packs.py untouched; the database backed up first; only the new table and its seed added; the lock released; the installer's /tmp scratch removed"

echo "=== outcome 2: the same line again (ALREADY INSTALLED) ==="
bash "$HERE/install_s582.sh" > "$ROOT/run2.txt" 2>&1; R2=$?
sed 's/^/  /' "$ROOT/run2.txt" | tail -2 | cut -c1-300
[ "$R2" = 0 ] && grep -q "ALREADY INSTALLED" "$ROOT/run2.txt" || fail "outcome 2 did not say ALREADY INSTALLED"
at_to || fail "outcome 2: a file moved"

for oc in "3:forced" "4:desk404" "5:desk200" "6:xr404"; do
  n=${oc%%:*}; k=${oc##*:}
  reset_root; modes 302 302 302
  case "$k" in
    forced) echo "=== outcome 3: a forced red after placing (restores batteries.py, takes xray_costs.py out) ==="; export S582_FORCE_RED=1;;
    desk404) echo "=== outcome 4: healthz 200 but /desk does not answer (404) -> restores ==="; modes 404 302 302;;
    desk200) echo "=== outcome 5: /desk answers 200 -- a login gate open is not accepted -> restores ==="; modes 200 302 302;;
    xr404) echo "=== outcome 6: /xray does not answer (404) -> restores ==="; modes 302 302 404;;
  esac
  bash "$HERE/install_s582.sh" > "$ROOT/run$n.txt" 2>&1; RR=$?; unset S582_FORCE_RED
  grep -E 'forced|RESTOR|/desk|/xray|NOT INSTALLED|DONE|back at' "$ROOT/run$n.txt" | cut -c1-260 | sed 's/^/  /'
  [ "$RR" = 1 ] && grep -q "NOT INSTALLED (restored" "$ROOT/run$n.txt" || fail "outcome $n did not restore (exit $RR)"
  at_from || fail "outcome $n: batteries.py is not back at the FROM pin, or xray_costs.py is still in place"
  [ -f "$ROOT/app/$N.undone_S582" ] || fail "outcome $n: xray_costs.py was not kept aside as .undone_S582"
  ro_ok || fail "outcome $n: a read-only file was touched"
done
grep -q "/desk answered 404, not 302" "$ROOT/run4.txt" && grep -q "/desk answered 200, not 302" "$ROOT/run5.txt" && grep -q "/xray answered 404, not 302" "$ROOT/run6.txt" || fail "outcomes 4-6 did not restore for the right reason"

refused(){ # n, what, the grep for its reason
  bash "$HERE/install_s582.sh" > "$ROOT/run$1.txt" 2>&1; RX=$?
  grep -E 'REFUSED|NOT INSTALLED' "$ROOT/run$1.txt" | cut -c1-260 | sed 's/^/  /'
  [ "$RX" = 1 ] && grep -q "$3" "$ROOT/run$1.txt" && grep -q "NOT INSTALLED (nothing was placed)" "$ROOT/run$1.txt" || fail "outcome $1 ($2) was not refused (exit $RX)"
  nobak || fail "outcome $1: a backup was made -- the refusal came too late"
  [ ! -d "$ROOT/lock" ] || fail "outcome $1: the lock was kept"
}
echo "=== outcome 7: batteries.py not at its FROM pin (another kit moved it) -> REFUSED before anything is placed ==="
reset_root; modes 302 302 302
printf '\n# made-up change\n' >> "$ROOT/app/$F"; BM="$(md5 "$ROOT/app/$F")"
refused 7 "batteries moved" "REFUSED: batteries.py is"
[ "$(md5 "$ROOT/app/$F")" = "$BM" ] && [ ! -e "$ROOT/app/$N" ] || fail "outcome 7: the moved batteries.py was touched or xray_costs.py placed"

echo "=== outcome 8: a read-only file moved (sorting_desk.py) -> REFUSED before anything is placed ==="
reset_root
printf '\n# made-up change\n' >> "$ROOT/app/sorting_desk.py"
refused 8 "read-only moved" "REFUSED: sorting_desk.py (read only) is"
at_from || fail "outcome 8: batteries.py was touched"

echo "=== outcome 9: no batteries.py (S571 / S575 not installed) -> REFUSED before anything is placed ==="
reset_root
rm -f "$ROOT/app/$F"
refused 9 "no batteries.py" "REFUSED: .*batteries.py is missing"
[ ! -e "$ROOT/app/$F" ] && [ ! -e "$ROOT/app/$N" ] || fail "outcome 9: a file was placed"

echo "=== outcome 10: the parent's packs.py moved by another kit -> REFUSED before anything is placed (S582 never places it) ==="
reset_root
printf '\n# made-up change by another kit\n' >> "$ROOT/finance/packs.py"; PKM="$(md5 "$ROOT/finance/packs.py")"
refused 10 "packs moved" "REFUSED: packs.py (the parent's, read only) is"
[ "$(md5 "$ROOT/finance/packs.py")" = "$PKM" ] || fail "outcome 10: the moved packs.py was touched"
at_from || fail "outcome 10: batteries.py was touched"

echo "=== outcome 11: an xray_costs.py already in the folder (not this kit's) -> REFUSED before anything is placed ==="
reset_root
printf '# a made-up xray_costs.py from somewhere else\n' > "$ROOT/app/$N"; XM="$(md5 "$ROOT/app/$N")"
refused 11 "foreign xray_costs.py" "REFUSED: .*xray_costs.py is already there"
[ "$(md5 "$ROOT/app/$N")" = "$XM" ] && [ "$(md5 "$ROOT/app/$F")" = "$(pin PIN_FROM_batteries.txt)" ] || fail "outcome 11: a file was touched"

echo "=== outcome 12: a half install (batteries.py at the TO pin, no xray_costs.py) -> REFUSED, never 'ALREADY INSTALLED' ==="
reset_root
python3 -B "$HERE/make_s582.py" "$ROOT/app" "$ROOT/half" >/dev/null && cp "$ROOT/half/$F" "$ROOT/app/$F" && rm -rf "$ROOT/half" || fail "outcome 12: could not make the half state"
refused 12 "half install" "REFUSED: batteries.py is at the kit's TO pin but xray_costs.py is missing"
grep -q "ALREADY INSTALLED" "$ROOT/run12.txt" && fail "outcome 12: a half install was taken for installed"

kill "$HPID" 2>/dev/null
[ "$(progs "$LIVE_APP" '*.py *.js')" = "$LIVE_BEFORE" ] || fail "the live scan app's program files changed during the rehearsal"
[ "$(progs "$LIVE_FIN" '*.py *.html')" = "$LIVE_FIN_BEFORE" ] || fail "the live finance folder's program files changed during the rehearsal"
[ "$(md5 "$LIVE_APP/$F")" = "$LIVE_BT" ] || fail "the live batteries.py changed"
[ -e "$LIVE_APP/$N" ] && fail "an xray_costs.py appeared in the live scan app"
ls "$LIVE_APP/" | grep -q "\.bak_S582_" && fail "a .bak_S582_ file appeared in the live scan app"
echo "REHEARSAL GREEN: fresh install green (the data step: only the new table, its index and the seed's rows); ALREADY INSTALLED; forced red restored; /desk 404, /desk 200 and /xray 404 restored (302 only); a moved batteries.py, a moved read-only file, a missing batteries.py, a moved packs.py, a foreign xray_costs.py and a half install refused before placing. The service faked; nothing live was placed or restarted; the live scan app's and finance folder's program files read back unchanged."
[ -n "${KEEP:-}" ] || rm -rf "$ROOT"
exit 0
