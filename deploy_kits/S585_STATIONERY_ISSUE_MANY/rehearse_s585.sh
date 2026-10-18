#!/bin/bash
# rehearse_s585.sh -- the S585 installer rehearsed on a made-up root under /tmp/s585reh/root (BUILD_NORM_v1 s3, S582's shape). A copy of
# the scan app's files (with S563's five backups, the pre-S559 widget and batteries.py before S582, which the earlier walks compare
# against), of the finance folder's program files (with packs.py before S560 and before S568) and of the scan app's database (SQLite's
# backup API) are put there; every S585_* setting points there (the earlier kits are read, never written, from S585_KITS_DIR); the restart
# is `true`; the service is faked by a stand-in (a small python3 server on a free port: /healthz 200, /stationery and /stationery/diya
# 302 -- the login gate, as the live app answers a plain request). The build lock is a made-up path. Nothing live is placed or restarted.
# Outcomes: 1 green (the data step on the made-up root's copy of the live database: only stationery_move gains Shavez's lines -- each 1 s
# before its item's opening count -- settings gains the key, desk_audit one line; every other row unchanged; the switch stationery.many
# NOT written; the backup taken and equal to the database before; a second data-step run writes nothing); 2 ALREADY INSTALLED; 3 a forced
# red after placing restores stationery.py; 4 /stationery 404, 5 /stationery 200 (a login gate open), 6 /stationery/diya 404 -- each
# restores (302 only); 7 a forced red data step restores (nothing of it written); 8 stationery.py not at its FROM pin, 9 a read-only file
# moved (sorting_desk.py), 10 S582 not installed (batteries.py before S582, no xray_costs.py), 11 the parent's packs.py moved -- each
# REFUSED before anything is placed.
# The end guard compares PROGRAM FILES only: (cd "$LIVE_FIN" && md5sum -- *.py *.html) | md5sum, and the same over the live scan app's
# *.py *.js -- never a directory listing.
# Run as root on the VPS: S585_KITS_DIR=/root/deploy/repo/deploy_kits bash rehearse_s585.sh   (KEEP=1 keeps the made-up root)
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT=/tmp/s585reh/root
LIVE_APP=/root/assetapp
LIVE_FIN=/root/finance
LIVE_SHARED=/root/shared
F="stationery.py"
RO="sorting_desk.py asset_register.py clinic_papers.py batteries.py xray_costs.py asset_machine.py scanner_widget.js claude_reader.py claude_reread.py"
COPY="$F $RO scanner_widget.js.bak_S559_1143c77b batteries.py.bak_S582_40eb8a91"
COPY="$COPY sorting_desk.py.bak_S563_a4623438 clinic_papers.py.bak_S563_88963eac asset_register.py.bak_S563_9daed9ea asset_machine.py.bak_S563_0caec41e scanner_widget.js.bak_S563_1128ac97"
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1"; }
base(){ local b="${1%.py}"; echo "${b%.js}"; }
fail(){ echo "REHEARSAL RED: $*"; [ -n "${HPID:-}" ] && kill "$HPID" 2>/dev/null; exit 1; }
at_from(){ [ -f "$ROOT/app/$F" ] && [ "$(md5 "$ROOT/app/$F")" = "$(pin PIN_FROM_stationery.txt)" ]; }
at_to(){ [ -f "$ROOT/app/$F" ] && [ "$(md5 "$ROOT/app/$F")" = "$(pin PIN_TO_stationery.txt)" ]; }
ro_ok(){ for f in $RO; do [ "$(md5 "$ROOT/app/$f")" = "$(pin PIN_READ_$(base "$f").txt)" ] || return 1; done; }
nobak(){ ! ls "$ROOT/app/" "$ROOT/finance/" | grep -q "\.bak_S585_"; }
reset_root(){ for f in $F sorting_desk.py batteries.py xray_costs.py; do cp "$ROOT/orig/$f" "$ROOT/app/$f"; done; cp "$ROOT/orig/packs.py" "$ROOT/finance/packs.py"
              cp "$ROOT/orig/assets.db" "$ROOT/app/assets.db"; rm -f "$ROOT/app/"*.bak_S585_* "$ROOT/finance/"*.bak_S585_*; rm -rf "$ROOT/lock"; }
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
[ -n "${S585_KITS_DIR:-}" ] && [ -f "$S585_KITS_DIR/S582_XRAY_COSTS/walk_s582.py" ] || fail "set S585_KITS_DIR to the folder holding the earlier kits, S582 among them (read only)"

rm -rf "$ROOT"; mkdir -p "$ROOT/app/uploads" "$ROOT/shared" "$ROOT/orig" "$ROOT/web" "$ROOT/finance" || fail "no made-up root"
SVC_ENV="$(systemctl show assetapp -p Environment --value 2>/dev/null || true)"
LDB="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"; LDB="${LDB:-$LIVE_APP/assets.db}"; unset SVC_ENV
for f in $COPY; do cp -p "$LIVE_APP/$f" "$ROOT/app/" || fail "copy $f"; done
LIVE_ST="$(md5 "$LIVE_APP/$F")"
for f in "$LIVE_FIN"/*.py "$LIVE_FIN"/*.html; do case "$f" in *.bak*) ;; *) [ -f "$f" ] && cp "$f" "$ROOT/finance/";; esac; done   # program files only
cp -p "$LIVE_FIN/packs.py.bak_S560_d86d351a" "$LIVE_FIN/packs.py.bak_S568_048d2ad8" "$ROOT/finance/"                          # the earlier walks compare against them
for f in $F sorting_desk.py batteries.py xray_costs.py; do cp "$ROOT/app/$f" "$ROOT/orig/$f"; done; cp "$ROOT/finance/packs.py" "$ROOT/orig/packs.py"
cp "$LIVE_SHARED"/*.py "$ROOT/shared/"
python3 -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LDB" "$ROOT/app/assets.db" || fail "database copy"
cp "$ROOT/app/assets.db" "$ROOT/orig/assets.db"
at_from || fail "the live stationery.py is not at the kit's FROM pin -- nothing to rehearse"
ro_ok || fail "a live read-only file (S582's batteries.py / xray_costs.py among them) is not at this kit's pin -- nothing to rehearse"
cat > "$ROOT/web/standin.py" <<'PYEOF'
import http.server, os, sys
WEB = os.path.dirname(os.path.abspath(__file__))
def mode(n, d):
    p = os.path.join(WEB, n)
    return open(p).read().strip() if os.path.exists(p) else d
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = self.path.split("?")[0]
        code = 200 if p == "/healthz" else (int(mode("st_mode", "404")) if p == "/stationery" else
                                            (int(mode("diya_mode", "404")) if p == "/stationery/diya" else 404))
        self.send_response(code)
        if code == 302:
            self.send_header("Location", "/login?next=" + p)
        self.send_header("Content-Length", "0")
        self.end_headers()
    def log_message(self, *a):
        pass
http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
PYEOF
modes(){ echo "$1" > "$ROOT/web/st_mode"; echo "$2" > "$ROOT/web/diya_mode"; }
modes 302 302
PORT="$(python3 -c "import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); print(s.getsockname()[1]); s.close()")"
python3 -B "$ROOT/web/standin.py" "$PORT" >/dev/null 2>&1 & HPID=$!
sleep 1

export S585_APP_DIR="$ROOT/app" S585_FIN_DIR="$ROOT/finance" S585_SERVICE="s585-rehearsal-made-up"
export S585_DB="$ROOT/app/assets.db" S585_HEALTH_URL="http://127.0.0.1:$PORT/healthz"
export S585_RESTART_CMD="true" S585_SHARED_DIR="$ROOT/shared" S585_HEALTH_TRIES=3 S585_LOCK="$ROOT/lock" S585_KEEP_SCRATCH=1
export S585_PYTHON="python3" S585_PYTHON_VENV="/usr/bin/python3" S585_W559_FROM="$ROOT/app/scanner_widget.js.bak_S559_1143c77b"
export S585_PACK_BEFORE="$ROOT/finance/packs.py.bak_S560_d86d351a" S585_PACK_BEFORE_S568="$ROOT/finance/packs.py.bak_S568_048d2ad8"
export S585_BATTERIES_BEFORE_S582="$ROOT/app/batteries.py.bak_S582_40eb8a91" S585_KITS_DIR
for v in S585_APP_DIR S585_FIN_DIR S585_DB S585_SHARED_DIR S585_PYTHON_VENV S585_LOCK S585_W559_FROM S585_PACK_BEFORE S585_PACK_BEFORE_S568 S585_BATTERIES_BEFORE_S582; do
  p="$(readlink -m "${!v}")"; case "$p" in /root/*) [ "$v" = S585_PYTHON_VENV ] || fail "$v resolves to $p -- the rehearsal never touches /root";; esac
done
case "$S585_RESTART_CMD" in *systemctl*) fail "the restart command contains systemctl";; esac
case "$S585_HEALTH_URL" in *:8030*|*:8106*) fail "the health URL is a live service's";; esac
[ "$(curl -s -o /dev/null -w '%{http_code}' "$S585_HEALTH_URL")" = "200" ] || fail "the stand-in health answer is not up"
[ "$(curl -s -o /dev/null -w '%{http_code}' "${S585_HEALTH_URL%/healthz}/stationery/diya")" = "302" ] || fail "the stand-in /stationery/diya does not answer 302"
echo "made-up root $ROOT; stand-in on port $PORT (/healthz 200, /stationery and /stationery/diya 302); the restart = true; the lock made-up; the earlier kits read from $S585_KITS_DIR"
LIVE_BEFORE="$(progs "$LIVE_APP" '*.py *.js')"; LIVE_FIN_BEFORE="$(progs "$LIVE_FIN" '*.py *.html')"

echo "=== outcome 1: a fresh install (green) ==="
bash "$HERE/install_s585.sh" > "$ROOT/run1.txt" 2>&1; R1=$?
grep -E '^\[|DONE|REFUSED|NOT INSTALLED|walk|control|CONTROL|TIDY|copy|answer|healthz|PINS|rebuilt|tidy comparison|placed|bak_S585|history|stock:|rehearsal|SWITCH|OFF now|= the kit' "$ROOT/run1.txt" | cut -c1-330 | sed 's/^/  /'
[ "$R1" = 0 ] && grep -q "S585_STATIONERY_ISSUE_MANY: DONE." "$ROOT/run1.txt" || fail "outcome 1 was not green (exit $R1)"
at_to || fail "outcome 1: stationery.py is not at the TO pin"
ls "$ROOT/app/" | grep -q "^$F.bak_S585_d11d7183$" || fail "outcome 1: no backup stationery.py.bak_S585_d11d7183"
[ "$(md5 "$ROOT/app/$F.bak_S585_d11d7183")" = "$(pin PIN_FROM_stationery.txt)" ] || fail "outcome 1: the backup is not the FROM bytes"
ls "$ROOT/app/" | grep -q "assets.db.bak_S585_" || fail "outcome 1: no database backup"
ro_ok || fail "outcome 1: a read-only file was touched"
[ "$(md5 "$ROOT/finance/packs.py")" = "$(pin PIN_READ_packs.txt)" ] || fail "outcome 1: packs.py was touched"
ls "$ROOT/finance/" | grep -q "\.bak_S585_" && fail "outcome 1: something in the finance folder was backed up -- S585 touches nothing there"
grep -q "OFF now (stationery.many: absent)" "$ROOT/run1.txt" || fail "outcome 1: the switch stationery.many is not absent after the install"
python3 - "$ROOT/app/assets.db" "$ROOT/orig/assets.db" "$(ls "$ROOT/app/"assets.db.bak_S585_* | head -1)" <<'PYEOF' || fail "outcome 1: the database changed beyond Shavez's lines, the key and one audit line -- or the backup differs"
import sqlite3, sys
a, b, k = sqlite3.connect(sys.argv[1]), sqlite3.connect(sys.argv[2]), sqlite3.connect(sys.argv[3])
HB = "history (Shavez sheet)"
def objs(c):
    return {(r[0], r[1]) for r in c.execute("SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}
def rows(c, t, cols, where=""):
    return sorted(map(repr, c.execute('SELECT %s FROM "%s" %s' % (",".join('"%s"' % x for x in cols), t, where))))
sa, sb, sk = objs(a), objs(b), objs(k)
same, nt = True, 0
for kind, t in sorted(sb):
    if kind != "table":
        continue
    nt += 1
    cols = [r[1] for r in b.execute('PRAGMA table_info("%s")' % t)]
    if rows(k, t, cols) != rows(b, t, cols):
        same = False; print("  the backup's table %s differs from the database before" % t)
    if t == "desk_audit":
        mx = b.execute("SELECT COALESCE(MAX(id),0) FROM desk_audit").fetchone()[0]
        old = rows(a, t, cols, "WHERE id <= %d" % mx)
        new_acts = [r[0] for r in a.execute("SELECT action FROM desk_audit WHERE id > ?", (mx,))]
        if old != rows(b, t, cols) or new_acts != ["stationery_history_s585"]:
            same = False; print("  desk_audit differs beyond the data step's one line (%s)" % new_acts)
        continue
    if t == "settings":
        new = {r[0]: r[1] for r in a.execute("SELECT key, value FROM settings")}
        old = {r[0]: r[1] for r in b.execute("SELECT key, value FROM settings")}
        added = {x: v for x, v in new.items() if x not in old}
        if any(new.get(x) != v for x, v in old.items()) or sorted(added) != ["stationery.history_s585"] or "stationery.many" in new:
            same = False; print("  settings differ beyond the key (%s)" % sorted(added))
        print("  settings: added %s = %r; stationery.many %s" % (sorted(added), list(added.values()), new.get("stationery.many", "absent")))
        continue
    if t == "stationery_move":
        mx = b.execute("SELECT COALESCE(MAX(id),0) FROM stationery_move").fetchone()[0]
        if rows(a, t, cols, "WHERE id <= %d" % mx) != rows(b, t, cols):
            same = False; print("  an earlier stationery_move row changed")
        new = a.execute("SELECT m.id, m.item_id, m.qty, m.place, m.day, m.ts, m.stock_before, m.by_whom, i.name, "
                        "(SELECT ts FROM stationery_count c WHERE c.item_id=m.item_id AND c.opening=1 ORDER BY ts, id LIMIT 1), "
                        "(SELECT day FROM stationery_count c WHERE c.item_id=m.item_id AND c.opening=1 ORDER BY ts, id LIMIT 1) "
                        "FROM stationery_move m JOIN stationery_item i ON i.id=m.item_id WHERE m.id > ? ORDER BY m.id", (mx,)).fetchall()
        for r in new:
            print("  new move: %s %g -> %s, day %s, ts = opening count - %.3f s, stock_before %s, by %r" % (r[8], r[2], r[3], r[4], r[9] - r[5], r[6], r[7]))
        if not new or any(r[7] != HB or r[6] is not None or abs((r[9] - r[5]) - 1.0) > 1e-6 or r[4] != r[10] for r in new):
            same = False; print("  the new moves are not Shavez's lines 1 s before their opening counts")
        print("  stationery_move: %d new line(s), all Shavez's, each 1 s before its item's opening count" % len(new))
        continue
    if rows(a, t, cols) != rows(b, t, cols):
        same = False; print("  table %s differs" % t)
print("  database: objects added %s; every row of the %d earlier tables unchanged beyond the data step %s; the backup equal to the database "
      "before %s" % (sorted(n for _k, n in sa - sb), nt, same, sk == sb))
sys.exit(0 if (sa == sb and sk == sb and same) else 1)
PYEOF
python3 -B "$ROOT/app/$F" --history "$ROOT/app/assets.db" > "$ROOT/run1b.txt" 2>&1 || fail "outcome 1: the data step's second run failed"
sed 's/^/  second data-step run: /' "$ROOT/run1b.txt"
grep -q "already done" "$ROOT/run1b.txt" || fail "outcome 1: the data step's second run did not say 'already done'"
grep -q "UNDO (one line): \\\\cp -p .*stationery.py.bak_S585_d11d7183 .*stationery.py && systemctl restart s585-rehearsal-made-up$" "$ROOT/run1.txt" || fail "outcome 1: the undo line does not put back stationery.py.bak_S585_d11d7183, or restarts more than the scan app"
grep -q "clinic-finance" "$ROOT/run1.txt" && fail "outcome 1: the finance service was named -- S585 restarts assetapp only"
[ ! -d "$ROOT/lock" ] || fail "outcome 1: the build lock was not released"
ls -d /tmp/s585_install_* >/dev/null 2>&1 && fail "outcome 1: the installer's scratch under /tmp/s585_install_* was not removed"
echo "  made-up root after outcome 1: stationery.py at the TO pin, stationery.py.bak_S585_d11d7183 beside it (the FROM bytes); the read-only files and packs.py untouched; the database backed up first; only Shavez's lines, the key and one audit line added; the switch absent (OFF); the lock released; the installer's /tmp scratch removed"
cp "$ROOT/run1.txt" "$ROOT/../run1_kept.txt" 2>/dev/null

echo "=== outcome 2: the same line again (ALREADY INSTALLED) ==="
bash "$HERE/install_s585.sh" > "$ROOT/run2.txt" 2>&1; R2=$?
sed 's/^/  /' "$ROOT/run2.txt" | tail -2 | cut -c1-300
[ "$R2" = 0 ] && grep -q "ALREADY INSTALLED" "$ROOT/run2.txt" || fail "outcome 2 did not say ALREADY INSTALLED"
grep -q "history key stationery.history_s585 set" "$ROOT/run2.txt" || fail "outcome 2: the history key is not read back as set"
at_to || fail "outcome 2: the file moved"

for oc in "3:forced" "4:st404" "5:st200" "6:diya404" "7:data"; do
  n=${oc%%:*}; k=${oc##*:}
  reset_root; modes 302 302
  case "$k" in
    forced) echo "=== outcome 3: a forced red after placing (restores stationery.py) ==="; export S585_FORCE_RED=1;;
    st404) echo "=== outcome 4: healthz 200 but /stationery does not answer (404) -> restores ==="; modes 404 302;;
    st200) echo "=== outcome 5: /stationery answers 200 -- a login gate open is not accepted -> restores ==="; modes 200 302;;
    diya404) echo "=== outcome 6: /stationery/diya does not answer (404) -> restores ==="; modes 302 404;;
    data) echo "=== outcome 7: a forced red data step -> restores (nothing of it written) ==="; export S585_FORCE_DATA_RED=1;;
  esac
  bash "$HERE/install_s585.sh" > "$ROOT/run$n.txt" 2>&1; RR=$?; unset S585_FORCE_RED S585_FORCE_DATA_RED
  grep -E 'forced|RESTOR|/stationery|NOT INSTALLED|DONE|back at' "$ROOT/run$n.txt" | cut -c1-260 | sed 's/^/  /'
  [ "$RR" = 1 ] && grep -q "NOT INSTALLED (restored" "$ROOT/run$n.txt" || fail "outcome $n did not restore (exit $RR)"
  at_from || fail "outcome $n: stationery.py is not back at the FROM pin"
  ro_ok || fail "outcome $n: a read-only file was touched"
  db_same || fail "outcome $n: the database changed"
done
grep -q "/stationery answered 404, not 302" "$ROOT/run4.txt" && grep -q "/stationery answered 200, not 302" "$ROOT/run5.txt" && grep -q "/stationery/diya answered 404, not 302" "$ROOT/run6.txt" && grep -q "the data step is forced red" "$ROOT/run7.txt" || fail "outcomes 4-7 did not restore for the right reason"

refused(){ # n, what, the grep for its reason
  bash "$HERE/install_s585.sh" > "$ROOT/run$1.txt" 2>&1; RX=$?
  grep -E 'REFUSED|NOT INSTALLED' "$ROOT/run$1.txt" | cut -c1-260 | sed 's/^/  /'
  [ "$RX" = 1 ] && grep -q "$3" "$ROOT/run$1.txt" && grep -q "NOT INSTALLED (nothing was placed)" "$ROOT/run$1.txt" || fail "outcome $1 ($2) was not refused (exit $RX)"
  nobak || fail "outcome $1: a backup was made -- the refusal came too late"
  [ ! -d "$ROOT/lock" ] || fail "outcome $1: the lock was kept"
  db_same || fail "outcome $1: the database changed"
}
echo "=== outcome 8: stationery.py not at its FROM pin (a wrong FROM byte) -> REFUSED before anything is placed ==="
reset_root; modes 302 302
printf '\n# made-up change\n' >> "$ROOT/app/$F"; SM="$(md5 "$ROOT/app/$F")"
refused 8 "stationery moved" "REFUSED: stationery.py is"
[ "$(md5 "$ROOT/app/$F")" = "$SM" ] || fail "outcome 8: the moved stationery.py was touched"

echo "=== outcome 9: a read-only file moved (sorting_desk.py) -> REFUSED before anything is placed ==="
reset_root
printf '\n# made-up change\n' >> "$ROOT/app/sorting_desk.py"
refused 9 "read-only moved" "REFUSED: sorting_desk.py (read only) is"
at_from || fail "outcome 9: stationery.py was touched"

echo "=== outcome 10: S582 not installed (batteries.py before S582, no xray_costs.py) -> REFUSED before anything is placed ==="
reset_root
cp "$ROOT/app/batteries.py.bak_S582_40eb8a91" "$ROOT/app/batteries.py"; rm -f "$ROOT/app/xray_costs.py"
refused 10 "S582 not installed" "S582 is not installed"
at_from || fail "outcome 10: stationery.py was touched"

echo "=== outcome 11: the parent's packs.py moved by another kit -> REFUSED before anything is placed (S585 never places it) ==="
reset_root
printf '\n# made-up change by another kit\n' >> "$ROOT/finance/packs.py"; PKM="$(md5 "$ROOT/finance/packs.py")"
refused 11 "packs moved" "REFUSED: packs.py (the parent's, read only) is"
[ "$(md5 "$ROOT/finance/packs.py")" = "$PKM" ] || fail "outcome 11: the moved packs.py was touched"
at_from || fail "outcome 11: stationery.py was touched"

kill "$HPID" 2>/dev/null
[ "$(progs "$LIVE_APP" '*.py *.js')" = "$LIVE_BEFORE" ] || fail "the live scan app's program files changed during the rehearsal"
[ "$(progs "$LIVE_FIN" '*.py *.html')" = "$LIVE_FIN_BEFORE" ] || fail "the live finance folder's program files changed during the rehearsal"
[ "$(md5 "$LIVE_APP/$F")" = "$LIVE_ST" ] || fail "the live stationery.py changed"
ls "$LIVE_APP/" | grep -q "\.bak_S585_" && fail "a .bak_S585_ file appeared in the live scan app"
echo "REHEARSAL GREEN: fresh install green (the data step: only Shavez's lines, each 1 s before its opening count, the key and one audit line; a second run writes nothing; the switch left OFF); ALREADY INSTALLED; forced red restored; /stationery 404, /stationery 200, /stationery/diya 404 and a forced red data step restored (302 only); a moved stationery.py, a moved read-only file, S582 not installed and a moved packs.py refused before placing. The service faked; nothing live was placed or restarted; the live scan app's and finance folder's program files read back unchanged."
[ -n "${KEEP:-}" ] || rm -rf "$ROOT"
exit 0
