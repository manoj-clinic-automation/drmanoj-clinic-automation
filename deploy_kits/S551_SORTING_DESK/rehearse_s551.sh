#!/bin/bash
# rehearse_s551.sh -- the S551 installer rehearsed on a made-up root under /tmp/s551dev/root (BUILD_NORM_v1 s3).
# A copy of the app's files and of its database (SQLite's backup API) are put there; every S551_* setting points there; the
# restart is `true` and the health answer comes from a stand-in (python3 -m http.server serving a file named healthz on a free
# port). Nothing live is placed or restarted. Three outcomes: green; ALREADY INSTALLED; a forced red after placing that restores.
# Run as root on the VPS: bash rehearse_s551.sh            (the made-up root is removed at the end; KEEP=1 keeps it)
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT=/tmp/s551dev/root
LIVE_APP=/root/assetapp
LIVE_SHARED=/root/shared
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1"; }
fail(){ echo "REHEARSAL RED: $*"; [ -n "${HPID:-}" ] && kill "$HPID" 2>/dev/null; exit 1; }

rm -rf "$ROOT"; mkdir -p "$ROOT/app/uploads" "$ROOT/shared" "$ROOT/web" "$ROOT/orig" || fail "no made-up root"
SVC_ENV="$(systemctl show assetapp -p Environment --value 2>/dev/null || true)"
LDB="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"; LDB="${LDB:-$LIVE_APP/assets.db}"; unset SVC_ENV
cp "$LIVE_APP/asset_register.py" "$LIVE_APP/clinic_papers.py" "$LIVE_APP/claude_reader.py" "$LIVE_APP/claude_reread.py" "$ROOT/app/"
cp "$ROOT/app/asset_register.py" "$ROOT/app/clinic_papers.py" "$ROOT/orig/"
cp "$LIVE_SHARED"/*.py "$ROOT/shared/"
python3 -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LDB" "$ROOT/app/assets.db" || fail "database copy"
echo ok > "$ROOT/web/healthz"
PORT="$(python3 -c "import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); print(s.getsockname()[1]); s.close()")"
( cd "$ROOT/web" && exec python3 -m http.server "$PORT" --bind 127.0.0.1 >/dev/null 2>&1 ) & HPID=$!
sleep 1

export S551_APP_DIR="$ROOT/app" S551_SERVICE="s551-rehearsal-made-up" S551_DB="$ROOT/app/assets.db" S551_UPLOADS="$ROOT/app/uploads"
export S551_HEALTH_URL="http://127.0.0.1:$PORT/healthz" S551_RESTART_CMD="true" S551_SHARED_DIR="$ROOT/shared" S551_HEALTH_TRIES=3
export S551_PYTHON="python3" S551_PYTHON_VENV="/usr/bin/python3"
for v in S551_APP_DIR S551_DB S551_UPLOADS S551_SHARED_DIR S551_PYTHON_VENV; do
  p="$(readlink -m "${!v}")"; case "$p" in /root/*) fail "$v resolves to $p -- the rehearsal never touches /root";; esac
done
case "$S551_RESTART_CMD" in *systemctl*) fail "the restart command contains systemctl";; esac
case "$S551_HEALTH_URL" in *:8030*) fail "the health URL is the live service's";; esac
[ "$(curl -s -o /dev/null -w '%{http_code}' "$S551_HEALTH_URL")" = "200" ] || fail "the stand-in health answer is not up"
echo "made-up root $ROOT; stand-in health on port $PORT; restart = true"

echo "=== outcome 1: a fresh install (green) ==="
bash "$HERE/install_s551.sh" > "$ROOT/run1.txt" 2>&1; R1=$?
grep -E '^\[|DONE|REFUSED|NOT INSTALLED|walk:|control|PINS' "$ROOT/run1.txt" | sed 's/^/  /'
[ "$R1" = 0 ] && grep -q "S551_SORTING_DESK: DONE." "$ROOT/run1.txt" || fail "outcome 1 was not green (exit $R1)"
[ "$(md5 "$ROOT/app/asset_register.py")" = "$(pin PIN_TO_asset_register.txt)" ] && [ "$(md5 "$ROOT/app/clinic_papers.py")" = "$(pin PIN_TO_clinic_papers.txt)" ] \
  && [ "$(md5 "$ROOT/app/sorting_desk.py")" = "$(pin PIN_TO_sorting_desk.txt)" ] || fail "outcome 1: the placed files are not at the TO pins"
FL="$(python3 -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); print(c.execute(\"SELECT COALESCE((SELECT value FROM settings WHERE key='desk.floor'),'-')||'/'||COALESCE((SELECT value FROM settings WHERE key='desk.on'),'absent')||'/'||(SELECT COUNT(*) FROM sqlite_master WHERE name IN ('challan_supplier','implant_payment','implant_check','desk_audit'))\").fetchone()[0])" "$ROOT/app/assets.db")"
echo "  made-up root after outcome 1: desk.floor/desk.on/new tables = $FL"
case "$FL" in ????-??-??/absent/4) ;; *) fail "outcome 1: the data step did not leave desk.floor set, desk.on absent and the four tables";; esac
ls "$ROOT/app/" | grep -q "asset_register.py.bak_S551_" && ls "$ROOT/app/" | grep -q "assets.db.bak_S551_" || fail "outcome 1: the backups are not beside the files"

echo "=== outcome 2: the same line again (ALREADY INSTALLED) ==="
bash "$HERE/install_s551.sh" > "$ROOT/run2.txt" 2>&1; R2=$?
sed 's/^/  /' "$ROOT/run2.txt" | tail -3
[ "$R2" = 0 ] && grep -q "ALREADY INSTALLED" "$ROOT/run2.txt" || fail "outcome 2 did not say ALREADY INSTALLED"

echo "=== outcome 3: a forced red after placing (restores) ==="
cp "$ROOT/orig/asset_register.py" "$ROOT/orig/clinic_papers.py" "$ROOT/app/" && rm -f "$ROOT/app/sorting_desk.py" "$ROOT/app/"*.bak_S551_*
S551_FORCE_RED=1 bash "$HERE/install_s551.sh" > "$ROOT/run3.txt" 2>&1; R3=$?
grep -E 'forced|RESTOR|healthz|NOT INSTALLED|DONE' "$ROOT/run3.txt" | sed 's/^/  /'
[ "$R3" = 1 ] && grep -q "NOT INSTALLED (restored" "$ROOT/run3.txt" || fail "outcome 3 did not restore (exit $R3)"
[ "$(md5 "$ROOT/app/asset_register.py")" = "$(pin PIN_FROM_asset_register.txt)" ] && [ "$(md5 "$ROOT/app/clinic_papers.py")" = "$(pin PIN_FROM_clinic_papers.txt)" ] \
  && [ ! -e "$ROOT/app/sorting_desk.py" ] || fail "outcome 3: the files are not back at the FROM pins"

kill "$HPID" 2>/dev/null
echo "REHEARSAL GREEN: fresh install green; ALREADY INSTALLED; forced red restored to the FROM pins. Nothing live was placed or restarted."
[ -n "${KEEP:-}" ] || rm -rf "$ROOT"
exit 0
