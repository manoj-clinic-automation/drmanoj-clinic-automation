#!/bin/bash
# rehearse_s649.sh -- S649's installer on a MADE-UP root (never the live box): a copy of the kit, a folder holding the FROM
# claude_reader.py (the live 10118909), the read-only files at their pins and the app's other top-level code files, a made-up
# database, no service (restart = true, health faked).
#   bash rehearse_s649.sh <folder with the FROM files> <service python: flask, NO Pillow> <turn python: with Pillow>
# R1 DRY=1 nothing placed . R2 DONE: claude_reader.py at its TO pin, its backup, the lock released . R3 ALREADY INSTALLED .
# R4 a FROM file of other bytes: REFUSED, nothing placed . R5 another build's lock: REFUSED, left in place . R6 health red after
# placing: the file back byte-identically, NOT INSTALLED . R7 a read-only file (the desk) of other bytes: REFUSED, nothing placed .
# R8 no venv python: REFUSED, nothing placed.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${1:?the folder with the FROM files}"; SPY="${2:?the service python}"; TPY="${3:?the python with Pillow}"
R="$(mktemp -d /tmp/s649reh.XXXXXX)"; trap 'rm -rf "$R"' EXIT
OK=0; BAD=0
ok(){ if [ "$1" = 0 ]; then OK=$((OK+1)); echo "GREEN $2"; else BAD=$((BAD+1)); echo "RED   $2"; tail -12 "$R/out.txt"; fi; }
cp -r "$HERE" "$R/kit"
mk(){ rm -rf "$R/app" "$R/lockdir"; mkdir -p "$R/app" "$R/lockdir"; for f in "$SRC"/*.py "$SRC"/*.js "$SRC"/*.json; do [ -f "$f" ] && cp -p "$f" "$R/app/"; done
      "$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('CREATE TABLE made_up(x)'); c.execute('CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT)'); c.commit()" "$R/app/assets.db"; }
inst(){ env S649_APP_DIR="$R/app" S649_DB="$R/app/assets.db" S649_LOCK="$R/lockdir/lock" S649_HOST="$(hostname)" S649_REHEARSAL=1 S649_RESTART_CMD=true S649_SLEEP=0 \
        S649_HEALTH_TRIES=2 S649_FAKE_HEALTH=200 S649_PYTHON="$SPY" S649_TURN_PY="$TPY" "$@" bash "$R/kit/install_s649.sh" > "$R/out.txt" 2>&1; }
pinof(){ tr -d ' \r\n' < "$R/kit/PIN_$1.txt"; }
at(){ [ "$(md5sum "$R/app/claude_reader.py" | cut -c1-32)" = "$(pinof $1_claude_reader)" ]; }

mk; inst DRY=1; grep -q "DRY RUN" "$R/out.txt" && at FROM; ok $? "R1 DRY=1: both walks and the control, then stops -- the file untouched"
inst; grep -q "S649_READER_PHOTO_SIZE: DONE" "$R/out.txt" && at TO && [ "$(ls "$R/app" | grep -c '\.py\.bak_S649_')" = 1 ] && [ ! -e "$R/lockdir/lock" ] \
  && grep -q "the placed reader: WALK S649 READER: 10 green, 0 red" "$R/out.txt" && ! grep -qE "Traceback|SyntaxError" "$R/out.txt" \
  && grep -q "the papers Claude could not read so far" "$R/out.txt"
ok $? "R2 the install: DONE, claude_reader.py at its TO pin, its backup, the placed reader walked green, the evidence line printed, no traceback, the lock released"
inst; grep -q "ALREADY INSTALLED" "$R/out.txt" && at TO; ok $? "R3 a second run: ALREADY INSTALLED"
mk; echo "# other bytes" >> "$R/app/claude_reader.py"; inst; grep -q "REFUSED: claude_reader.py is" "$R/out.txt" && ! ls "$R/app" | grep -q bak_S649
ok $? "R4 a FROM file of other bytes: REFUSED, nothing placed"
mk; mkdir -p "$R/lockdir/lock"; echo other > "$R/lockdir/lock/owner"; inst; grep -q "another build holds the lock" "$R/out.txt" && [ -f "$R/lockdir/lock/owner" ] && at FROM
ok $? "R5 another build's lock: REFUSED, its lock left in place"
mk; inst S649_FAKE_HEALTH=500; grep -q "NOT INSTALLED (restored)" "$R/out.txt" && at FROM
ok $? "R6 health red after placing: the file back byte-identically, NOT INSTALLED"
mk; echo "# other bytes" >> "$R/app/sorting_desk.py"; inst; grep -q "REFUSED: sorting_desk.py is" "$R/out.txt" && at FROM && ! ls "$R/app" | grep -q bak_S649
ok $? "R7 a read-only file (the desk) of other bytes: REFUSED, nothing placed"
mk; inst S649_TURN_PY="$R/no_such_python"; grep -q "REFUSED: no venv python" "$R/out.txt" && at FROM && ! ls "$R/app" | grep -q bak_S649
ok $? "R8 no venv python: REFUSED, nothing placed"
echo "REHEARSAL S649: $OK green, $BAD red"
[ "$BAD" = 0 ]
