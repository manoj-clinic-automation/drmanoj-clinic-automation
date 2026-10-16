#!/bin/bash
# rehearse_s568.sh -- the S568 installer rehearsed on a made-up root under /tmp/s568reh/root (BUILD_NORM_v1 s3, S566's shape with
# S560's packs.py). A copy of the scan app's files (with S563's five backups and the pre-S559 widget, which the walks compare
# against), of the finance folder's program files (with packs.py before S560) and of the scan app's database (SQLite's backup API)
# are put there; every S568_* setting points there (the earlier kits are read, never written, from S568_KITS_DIR); both restarts are
# `true`, the services are faked by a stand-in (a small python3 server on a free port: /healthz 200, /finance/healthz 200, /desk and
# /stationery 302 -- the login gate, as the live app answers a plain request), the journal is a made-up stub. The build lock is a
# made-up path. Nothing live is placed or restarted.
# Outcomes: 1 green (the data step's four tables and one column, nothing else in the database's shape); 2 ALREADY INSTALLED;
# 3 a forced red after placing restores every file (stationery.py removed); 4 /desk not answering (404) restores; 5 /desk answering
# 200 (a login gate open) restores -- 302 only; 6 /stationery not answering (404: stationery.py did not mount) restores; 7 a live
# file not at its FROM pin is REFUSED before anything is placed; 8 a read-only file moved (asset_machine.py) is REFUSED before
# anything is placed; 9 a stationery.py already there with other bytes is REFUSED before anything is placed; 10 packs.py moved by
# another kit: THAT FILE STOPPED (left as it is, not backed up, not placed; clinic-finance not restarted), the rest installed, said.
# Run as root on the VPS: S568_KITS_DIR=/root/deploy/repo/deploy_kits bash rehearse_s568.sh   (KEEP=1 keeps the made-up root)
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT=/tmp/s568reh/root
LIVE_APP=/root/assetapp
LIVE_FIN=/root/finance
LIVE_SHARED=/root/shared
EDITED="sorting_desk.py clinic_papers.py asset_register.py"
COPY="$EDITED asset_machine.py scanner_widget.js claude_reader.py claude_reread.py scanner_widget.js.bak_S559_1143c77b"
COPY="$COPY sorting_desk.py.bak_S563_a4623438 clinic_papers.py.bak_S563_88963eac asset_register.py.bak_S563_9daed9ea asset_machine.py.bak_S563_0caec41e scanner_widget.js.bak_S563_1128ac97"
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1"; }
base(){ local b="${1%.py}"; echo "${b%.js}"; }
fail(){ echo "REHEARSAL RED: $*"; [ -n "${HPID:-}" ] && kill "$HPID" 2>/dev/null; exit 1; }
at_from(){ for f in $EDITED; do [ "$(md5 "$ROOT/app/$f")" = "$(pin PIN_FROM_$(base "$f").txt)" ] || return 1; done; [ ! -e "$ROOT/app/stationery.py" ] || return 1
           [ "$(md5 "$ROOT/finance/packs.py")" = "$(pin PIN_FROM_packs.txt)" ] || return 1; }
at_to(){ for f in $EDITED; do [ "$(md5 "$ROOT/app/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] || return 1; done
         [ "$(md5 "$ROOT/app/stationery.py")" = "$(pin PIN_TO_stationery.txt)" ] || return 1; }
reset_root(){ for f in $EDITED asset_machine.py; do cp "$ROOT/orig/$f" "$ROOT/app/$f"; done; rm -f "$ROOT/app/stationery.py"; cp "$ROOT/orig/packs.py" "$ROOT/finance/packs.py"
              cp "$ROOT/orig/assets.db" "$ROOT/app/assets.db"; rm -f "$ROOT/app/"*.bak_S568_* "$ROOT/finance/"*.bak_S568_*; rm -rf "$ROOT/lock"; }
shape(){ python3 -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); print(sorted((r[0], r[1]) for r in c.execute('SELECT type, name FROM sqlite_master')), sorted(r[1] for r in c.execute('PRAGMA table_info(bills)')))" "$1"; }
[ -n "${S568_KITS_DIR:-}" ] && [ -f "$S568_KITS_DIR/S566_SCANAPP_LAST_FIXES/walk_s566.py" ] || fail "set S568_KITS_DIR to the folder holding the earlier kits (read only)"

rm -rf "$ROOT"; mkdir -p "$ROOT/app/uploads" "$ROOT/shared" "$ROOT/orig" "$ROOT/web" "$ROOT/finance" || fail "no made-up root"
SVC_ENV="$(systemctl show assetapp -p Environment --value 2>/dev/null || true)"
LDB="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"; LDB="${LDB:-$LIVE_APP/assets.db}"; unset SVC_ENV
for f in $COPY; do cp -p "$LIVE_APP/$f" "$ROOT/app/" || fail "copy $f"; done
[ -e "$LIVE_APP/stationery.py" ] && fail "the live scan app already holds a stationery.py -- nothing to rehearse"
for f in "$LIVE_FIN"/*.py "$LIVE_FIN"/*.html; do case "$f" in *.bak*) ;; *) [ -f "$f" ] && cp "$f" "$ROOT/finance/";; esac; done   # program files only
cp -p "$LIVE_FIN/packs.py.bak_S560_d86d351a" "$ROOT/finance/"                                                                  # S560's pack walk compares against it
for f in $EDITED asset_machine.py; do cp "$ROOT/app/$f" "$ROOT/orig/$f"; done; cp "$ROOT/finance/packs.py" "$ROOT/orig/packs.py"
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
        code = 200 if p in ("/healthz", "/finance/healthz") else (int(mode("desk_mode", "404")) if p == "/desk" else
                                                                  (int(mode("st_mode", "404")) if p == "/stationery" else 404))
        self.send_response(code)
        if code == 302:
            self.send_header("Location", "/login?next=" + p)
        self.send_header("Content-Length", "0")
        self.end_headers()
    def log_message(self, *a):
        pass
http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
PYEOF
printf '#!/bin/sh\nexit 0\n' > "$ROOT/web/journal_stub"; chmod +x "$ROOT/web/journal_stub"
echo 302 > "$ROOT/web/desk_mode"; echo 302 > "$ROOT/web/st_mode"
PORT="$(python3 -c "import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); print(s.getsockname()[1]); s.close()")"
python3 -B "$ROOT/web/standin.py" "$PORT" >/dev/null 2>&1 & HPID=$!
sleep 1

export S568_APP_DIR="$ROOT/app" S568_FIN_DIR="$ROOT/finance" S568_SERVICE="s568-rehearsal-made-up" S568_FIN_SERVICE="s568-rehearsal-finance-made-up"
export S568_DB="$ROOT/app/assets.db" S568_HEALTH_URL="http://127.0.0.1:$PORT/healthz" S568_FIN_HEALTH_URL="http://127.0.0.1:$PORT/finance/healthz"
export S568_RESTART_CMD="true" S568_FIN_RESTART_CMD="true" S568_SHARED_DIR="$ROOT/shared" S568_HEALTH_TRIES=3 S568_LOCK="$ROOT/lock"
export S568_PYTHON="python3" S568_PYTHON_VENV="/usr/bin/python3" S568_W559_FROM="$ROOT/app/scanner_widget.js.bak_S559_1143c77b"
export S568_PACK_BEFORE="$ROOT/finance/packs.py.bak_S560_d86d351a" S568_JOURNAL_CMD="$ROOT/web/journal_stub" S568_KITS_DIR
for v in S568_APP_DIR S568_FIN_DIR S568_DB S568_SHARED_DIR S568_PYTHON_VENV S568_LOCK S568_W559_FROM S568_PACK_BEFORE S568_JOURNAL_CMD; do
  p="$(readlink -m "${!v}")"; case "$p" in /root/*) [ "$v" = S568_PYTHON_VENV ] || fail "$v resolves to $p -- the rehearsal never touches /root";; esac
done
case "$S568_RESTART_CMD $S568_FIN_RESTART_CMD" in *systemctl*) fail "a restart command contains systemctl";; esac
case "$S568_HEALTH_URL $S568_FIN_HEALTH_URL" in *:8030*|*:8106*) fail "a health URL is a live service's";; esac
[ "$(curl -s -o /dev/null -w '%{http_code}' "$S568_HEALTH_URL")" = "200" ] || fail "the stand-in health answer is not up"
[ "$(curl -s -o /dev/null -w '%{http_code}' "$S568_FIN_HEALTH_URL")" = "200" ] || fail "the stand-in finance health answer is not up"
[ "$(curl -s -o /dev/null -w '%{http_code}' "${S568_HEALTH_URL%/healthz}/desk")" = "302" ] || fail "the stand-in /desk does not answer 302"
echo "made-up root $ROOT; stand-in on port $PORT (/healthz 200, /finance/healthz 200, /desk and /stationery 302); both restarts = true; the journal a stub; the lock made-up; the earlier kits read from $S568_KITS_DIR"
LIVE_BEFORE="$(cd "$LIVE_APP" && md5sum $EDITED asset_machine.py scanner_widget.js | md5sum)"; LIVE_LS="$(ls "$LIVE_APP" | md5sum)"
LIVE_FIN_BEFORE="$(md5 "$LIVE_FIN/packs.py")"; LIVE_FIN_LS="$(ls "$LIVE_FIN" | md5sum)"
SHAPE0="$(shape "$ROOT/orig/assets.db")"

echo "=== outcome 1: a fresh install (green) ==="
bash "$HERE/install_s568.sh" > "$ROOT/run1.txt" 2>&1; R1=$?
grep -E '^\[|DONE|REFUSED|NOT INSTALLED|walk|control|CONTROL|TIDY|counts|answer|healthz|PINS|rebuilt|tidy comparison|present|absent' "$ROOT/run1.txt" | cut -c1-330 | sed 's/^/  /'
[ "$R1" = 0 ] && grep -q "S568_STATIONERY_STOCK: DONE." "$ROOT/run1.txt" || fail "outcome 1 was not green (exit $R1)"
at_to || fail "outcome 1: the placed files are not at the TO pins"
[ "$(md5 "$ROOT/finance/packs.py")" = "$(pin PIN_TO_packs.txt)" ] || fail "outcome 1: packs.py is not at its TO pin"
for f in $EDITED; do ls "$ROOT/app/" | grep -q "^$f.bak_S568_" || fail "outcome 1: no backup beside $f"; done
ls "$ROOT/finance/" | grep -q "^packs.py.bak_S568_048d2ad8$" || fail "outcome 1: no packs.py.bak_S568_048d2ad8"
ls "$ROOT/app/" | grep -q "assets.db.bak_S568_" || fail "outcome 1: no database backup"
[ "$(md5 "$ROOT/app/asset_machine.py")" = "$(pin PIN_READ_asset_machine.txt)" ] || fail "outcome 1: asset_machine.py was touched"
[ "$(shape "$(ls "$ROOT/app/"assets.db.bak_S568_* | head -1)")" = "$SHAPE0" ] || fail "outcome 1: the database backup was not taken BEFORE the data step"
python3 - "$ROOT/app/assets.db" "$ROOT/orig/assets.db" <<'PYEOF' || fail "outcome 1: the database's shape changed by more than the four tables, one index and bills.mixed -- or a row changed"
import sqlite3, sys
a, b = sqlite3.connect(sys.argv[1]), sqlite3.connect(sys.argv[2])
sa = {(r[0], r[1]) for r in a.execute("SELECT type, name FROM sqlite_master")}
sb = {(r[0], r[1]) for r in b.execute("SELECT type, name FROM sqlite_master")}
new = sa - sb
want = {("table", "stationery_item"), ("table", "stationery_line"), ("table", "stationery_move"), ("table", "stationery_count"), ("index", "stationery_line_bill")}
ca = [r[1] for r in a.execute("PRAGMA table_info(bills)")]
cb = [r[1] for r in b.execute("PRAGMA table_info(bills)")]
same_rows = all(a.execute("SELECT COUNT(*) FROM %s" % t).fetchone() == b.execute("SELECT COUNT(*) FROM %s" % t).fetchone() for _k, t in sb if _k == "table" and not t.startswith("sqlite_"))
bills_same = list(a.execute("SELECT %s FROM bills ORDER BY id" % ",".join(cb))) == list(b.execute("SELECT %s FROM bills ORDER BY id" % ",".join(cb)))
print("  database: new %s; bills columns added %s; every old table's row count kept %s; every bills row unchanged %s" % (sorted(n for _t, n in new), [c for c in ca if c not in cb], same_rows, bills_same))
sys.exit(0 if (new == want and not (sb - sa) and ca == cb + ["mixed"] and same_rows and bills_same) else 1)
PYEOF
grep -q "UNDO (one line): \\\\cp -p " "$ROOT/run1.txt" && grep -q "stationery.py.off_S568" "$ROOT/run1.txt" || fail "outcome 1: the undo line does not start with \\cp -p or does not move stationery.py aside"
[ ! -d "$ROOT/lock" ] || fail "outcome 1: the build lock was not released"
echo "  made-up root after outcome 1: the four scan-app files and packs.py at the TO pins; backups beside them; the database backed up before the data step, its shape grown by exactly four tables, one index and bills.mixed, no row changed; the lock released"

echo "=== outcome 2: the same line again (ALREADY INSTALLED) ==="
bash "$HERE/install_s568.sh" > "$ROOT/run2.txt" 2>&1; R2=$?
sed 's/^/  /' "$ROOT/run2.txt" | tail -2 | cut -c1-300
[ "$R2" = 0 ] && grep -q "ALREADY INSTALLED" "$ROOT/run2.txt" || fail "outcome 2 did not say ALREADY INSTALLED"

for oc in "3:forced" "4:desk404" "5:desk200" "6:st404"; do
  n=${oc%%:*}; k=${oc##*:}
  reset_root; echo 302 > "$ROOT/web/desk_mode"; echo 302 > "$ROOT/web/st_mode"
  case "$k" in
    forced) echo "=== outcome 3: a forced red after placing (restores every file) ==="; export S568_FORCE_RED=1;;
    desk404) echo "=== outcome 4: healthz 200 but /desk does not answer (404) -> restores ==="; echo 404 > "$ROOT/web/desk_mode";;
    desk200) echo "=== outcome 5: /desk answers 200 -- a login gate open is not accepted -> restores ==="; echo 200 > "$ROOT/web/desk_mode";;
    st404) echo "=== outcome 6: /stationery does not answer (404: stationery.py did not mount) -> restores ==="; echo 404 > "$ROOT/web/st_mode";;
  esac
  bash "$HERE/install_s568.sh" > "$ROOT/run$n.txt" 2>&1; RR=$?; unset S568_FORCE_RED
  grep -E 'forced|RESTOR|/desk|/stationery|NOT INSTALLED|DONE|files back' "$ROOT/run$n.txt" | cut -c1-260 | sed 's/^/  /'
  [ "$RR" = 1 ] && grep -q "NOT INSTALLED (restored" "$ROOT/run$n.txt" || fail "outcome $n did not restore (exit $RR)"
  at_from || fail "outcome $n: the files are not back at the FROM pins (or stationery.py is still there, or packs.py moved)"
done
grep -q "/desk answered 404, not 302" "$ROOT/run4.txt" && grep -q "/desk answered 200, not 302" "$ROOT/run5.txt" && grep -q "/stationery answered 404, not 302" "$ROOT/run6.txt" || fail "outcomes 4-6 did not restore for the right reason"

echo "=== outcome 7: a live file not at its FROM pin (another kit moved it) -> REFUSED before anything is placed ==="
reset_root; echo 302 > "$ROOT/web/desk_mode"; echo 302 > "$ROOT/web/st_mode"
printf '\n# made-up change\n' >> "$ROOT/app/clinic_papers.py"
bash "$HERE/install_s568.sh" > "$ROOT/run7.txt" 2>&1; R7=$?
grep -E 'REFUSED|NOT INSTALLED' "$ROOT/run7.txt" | sed 's/^/  /'
[ "$R7" = 1 ] && grep -q "REFUSED: clinic_papers.py is" "$ROOT/run7.txt" && grep -q "NOT INSTALLED (nothing was placed)" "$ROOT/run7.txt" || fail "outcome 7 was not refused (exit $R7)"
ls "$ROOT/app/" "$ROOT/finance/" | grep -q "\.bak_S568_" && fail "outcome 7: a backup was made -- the refusal came too late"
[ ! -e "$ROOT/app/stationery.py" ] && [ ! -d "$ROOT/lock" ] || fail "outcome 7: stationery.py placed or the lock kept"

echo "=== outcome 8: a read-only file moved (asset_machine.py) -> REFUSED before anything is placed ==="
reset_root
printf '\n# made-up change\n' >> "$ROOT/app/asset_machine.py"
bash "$HERE/install_s568.sh" > "$ROOT/run8.txt" 2>&1; R8=$?
grep -E 'REFUSED|NOT INSTALLED' "$ROOT/run8.txt" | sed 's/^/  /'
[ "$R8" = 1 ] && grep -q "REFUSED: asset_machine.py (read only) is" "$ROOT/run8.txt" || fail "outcome 8 was not refused (exit $R8)"
ls "$ROOT/app/" "$ROOT/finance/" | grep -q "\.bak_S568_" && fail "outcome 8: a backup was made -- the refusal came too late"
at_from || fail "outcome 8: an edited file was touched"

echo "=== outcome 9: a stationery.py already there with other bytes -> REFUSED before anything is placed ==="
reset_root
printf '# made-up stationery.py, not this kit'"'"'s\n' > "$ROOT/app/stationery.py"
bash "$HERE/install_s568.sh" > "$ROOT/run9.txt" 2>&1; R9=$?
grep -E 'REFUSED|NOT INSTALLED' "$ROOT/run9.txt" | sed 's/^/  /'
[ "$R9" = 1 ] && grep -q "REFUSED: stationery.py is already in" "$ROOT/run9.txt" || fail "outcome 9 was not refused (exit $R9)"
ls "$ROOT/app/" "$ROOT/finance/" | grep -q "\.bak_S568_" && fail "outcome 9: a backup was made -- the refusal came too late"
grep -q "made-up stationery.py" "$ROOT/app/stationery.py" || fail "outcome 9: the other stationery.py was touched"
rm -f "$ROOT/app/stationery.py"; at_from || fail "outcome 9: an edited file was touched"

echo "=== outcome 10: packs.py moved by another kit -> THAT FILE STOPPED, the rest installed and said ==="
reset_root
printf '\n# made-up change by another kit\n' >> "$ROOT/finance/packs.py"; PKM="$(md5 "$ROOT/finance/packs.py")"
bash "$HERE/install_s568.sh" > "$ROOT/run10.txt" 2>&1; R10=$?
grep -E 'packs.py|I8|DONE|STOPPED|not restarted|REFUSED' "$ROOT/run10.txt" | cut -c1-260 | sed 's/^/  /'
[ "$R10" = 0 ] && grep -q "S568_STATIONERY_STOCK: DONE. (packs.py STOPPED" "$ROOT/run10.txt" || fail "outcome 10 was not green-with-packs-stopped (exit $R10)"
at_to || fail "outcome 10: the scan-app files are not at the TO pins"
[ "$(md5 "$ROOT/finance/packs.py")" = "$PKM" ] || fail "outcome 10: the moved packs.py was touched"
ls "$ROOT/finance/" | grep -q "\.bak_S568_" && fail "outcome 10: packs.py was backed up -- it was to be left alone"
grep -q "s568-rehearsal-finance-made-up not restarted" "$ROOT/run10.txt" || fail "outcome 10: clinic-finance was not left alone"

kill "$HPID" 2>/dev/null
[ "$(cd "$LIVE_APP" && md5sum $EDITED asset_machine.py scanner_widget.js | md5sum)" = "$LIVE_BEFORE" ] && [ "$(ls "$LIVE_APP" | md5sum)" = "$LIVE_LS" ] || fail "the live scan app folder changed during the rehearsal"
[ "$(md5 "$LIVE_FIN/packs.py")" = "$LIVE_FIN_BEFORE" ] && [ "$(ls "$LIVE_FIN" | md5sum)" = "$LIVE_FIN_LS" ] || fail "the live finance folder changed during the rehearsal"
echo "REHEARSAL GREEN: fresh install green; ALREADY INSTALLED; forced red restored; /desk 404, /desk 200 and /stationery 404 restored (302 only); a moved file, a moved read-only file and a foreign stationery.py refused before placing; a moved packs.py stopped alone, the rest installed. The services faked; nothing live was placed or restarted; the live scan app and finance folders read back unchanged."
[ -n "${KEEP:-}" ] || rm -rf "$ROOT"
exit 0
