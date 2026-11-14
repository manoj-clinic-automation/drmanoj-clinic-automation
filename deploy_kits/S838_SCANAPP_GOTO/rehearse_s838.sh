#!/bin/bash
# rehearse_s838.sh -- S838's installer on a MADE-UP root (never the live box): a copy of the kit, a folder holding the app's files at
# their pins (the four FROM files and the read-only ones), the live shared folder's copy, a made-up database, no service (restart =
# true, health faked).      bash rehearse_s838.sh <folder with the app's files> <the shared folder>
# R1 DRY=1 nothing placed . R2 DONE: sorting_desk.py at its TO pin, its backup and the database's, the lock
# released . R3 ALREADY INSTALLED . R4 a FROM file of other bytes: REFUSED, nothing placed . R5 another build's lock: REFUSED, left in
# place . R6 health red after placing: every file back byte-identically, NOT INSTALLED . R7 a read-only file of other bytes: REFUSED.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${1:?the folder with the app files}"; SHD="${2:?the shared folder}"; ONLY=" ${3:-1 2 3 4 5 6 7} "   # a part of the steps (each needs its own fresh call)
want(){ case "$ONLY" in *" $1 "*) return 0;; *) return 1;; esac; }
PY="${S838_PYTHON:-python3}"
R="$(mktemp -d /tmp/s838reh.XXXXXX)"; trap 'rm -rf "$R"' EXIT
OK=0; BAD=0
ok(){ [ -n "${REH_SHOW:-}" ] && sed "s/^/      /" "$R/out.txt" | cut -c1-150; if [ "$1" = 0 ]; then OK=$((OK+1)); echo "GREEN $2"; else BAD=$((BAD+1)); echo "RED   $2"; tail -12 "$R/out.txt"; fi; }
cp -r "$HERE" "$R/kit"
mk(){ rm -rf "$R/app" "$R/lockdir"; mkdir -p "$R/app" "$R/lockdir"; for f in "$SRC"/*.py "$SRC"/*.js "$SRC"/*.json; do [ -f "$f" ] && cp -p "$f" "$R/app/"; done
      "$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('CREATE TABLE bills(id INTEGER PRIMARY KEY, created_at TEXT)'); c.execute('CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT)'); c.commit()" "$R/app/assets.db"; }
inst(){ env S838_APP_DIR="$R/app" S838_SHARED_DIR="$SHD" S838_DB="$R/app/assets.db" S838_LOCK="$R/lockdir/lock" S838_HOST="$(hostname)" S838_REHEARSAL=1 \
        S838_RESTART_CMD=true S838_SLEEP=0 S838_HEALTH_TRIES=2 S838_FAKE_HEALTH=200 S838_PYTHON="$PY" "$@" bash "$R/kit/install_s838.sh" > "$R/out.txt" 2>&1; }
pinof(){ tr -d ' \r\n' < "$R/kit/PIN_$1.txt"; }
at(){ for f in sorting_desk; do [ "$(md5sum "$R/app/$f.py" | cut -c1-32)" = "$(pinof $1_$f)" ] || return 1; done; }
cn(){ "$PY" -c "import sqlite3,sys; sys.exit(0 if sqlite3.connect(sys.argv[1]).execute(\"SELECT 1 FROM sqlite_master WHERE name='credit_note'\").fetchone() else 1)" "$R/app/assets.db"; }

want 1 && { mk; inst DRY=1; grep -q "DRY RUN" "$R/out.txt" && at FROM; ok $? "R1 DRY=1: walked and controlled, then stops -- the files untouched"; }
want 2 && { mk; inst; grep -q "S838_SCANAPP_GOTO: DONE" "$R/out.txt" && at TO && [ "$(ls "$R/app" | grep -c '\.py\.bak_S838_')" = 1 ] \
  && [ "$(ls "$R/app" | grep -c 'assets\.db\.bak_S838_')" = 1 ] && [ ! -e "$R/lockdir/lock" ]
ok $? "R2 the install: DONE, sorting_desk.py at its TO pin, its backup and the database's, the lock released"; }
want 3 && { inst; grep -q "ALREADY INSTALLED" "$R/out.txt" && at TO; ok $? "R3 a second run: ALREADY INSTALLED"; }
want 4 && { mk; echo "# other bytes" >> "$R/app/sorting_desk.py"; inst; grep -q "REFUSED: sorting_desk.py is" "$R/out.txt" && ! ls "$R/app" | grep -q bak_S838
ok $? "R4 a FROM file of other bytes: REFUSED, nothing placed"; }
want 5 && { mk; mkdir -p "$R/lockdir/lock"; echo other > "$R/lockdir/lock/owner"; inst; grep -q "another build holds the lock" "$R/out.txt" && [ -f "$R/lockdir/lock/owner" ] && at FROM
ok $? "R5 another build's lock: REFUSED, its lock left in place"; }
want 6 && { mk; inst S838_FAKE_HEALTH=500; grep -q "NOT INSTALLED (restored)" "$R/out.txt" && at FROM
ok $? "R6 health red after placing: every file back byte-identically, NOT INSTALLED"; }
want 7 && { mk; echo "# other bytes" >> "$R/app/procroom.py"; inst; grep -q "REFUSED: procroom.py is" "$R/out.txt" && at FROM && ! ls "$R/app" | grep -q bak_S838
ok $? "R7 a read-only file (procroom) of other bytes: REFUSED, nothing placed"; }
echo "REHEARSAL S838: $OK green, $BAD red"
[ "$BAD" = 0 ]
