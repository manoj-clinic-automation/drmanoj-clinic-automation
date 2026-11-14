#!/bin/bash
# rehearse_s833.sh -- S833's installer on a MADE-UP root (never the live box): a copy of the kit, a folder holding the FROM files
# (claude_reader.py, clinic_papers.py) and the read-only files at their pins (and the app's other top-level code files), a made-up
# database, a crontab FILE, the watcher's message to a stub, no service (restart = true, health faked).
#   bash rehearse_s833.sh <folder with the FROM files>
# R1 DRY=1 nothing placed . R2 DONE: the two files and the new one at their TO pins, backups, the cron line, the proof message, the lock
# released . R3 ALREADY INSTALLED . R4 a FROM file of other bytes: REFUSED . R5 another build's lock: REFUSED . R6 health red after
# placing: both files back byte-identically, the new one taken off, the cron line gone, NOT INSTALLED . R7 a read-only file of other
# bytes: REFUSED.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${1:?the folder with the FROM files}"
PY="${S833_PYTHON:-python3}"
R="$(mktemp -d /tmp/s833reh.XXXXXX)"; trap 'rm -rf "$R"' EXIT
OK=0; BAD=0
ok(){ if [ "$1" = 0 ]; then OK=$((OK+1)); echo "GREEN $2"; else BAD=$((BAD+1)); echo "RED   $2"; tail -14 "$R/out.txt"; fi; }
cp -r "$HERE" "$R/kit"
mk(){ rm -rf "$R/app" "$R/lockdir" "$R/cron.txt" "$R/stub"; mkdir -p "$R/app" "$R/lockdir"; for f in "$SRC"/*.py "$SRC"/*.js "$SRC"/*.json; do [ -f "$f" ] && cp -p "$f" "$R/app/"; done
      rm -f "$R/app/reader_watch.py"; echo "30 2 * * * true # another job" > "$R/cron.txt"
      "$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('CREATE TABLE made_up(x)'); c.execute('CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT)'); c.commit()" "$R/app/assets.db"; }
inst(){ env S833_APP_DIR="$R/app" S833_DB="$R/app/assets.db" S833_LOCK="$R/lockdir/lock" S833_HOST="$(hostname)" S833_REHEARSAL=1 S833_RESTART_CMD=true S833_SLEEP=0 \
        S833_HEALTH_TRIES=2 S833_FAKE_HEALTH=200 S833_PYTHON="$PY" S833_VENV="$(command -v "$PY")" S833_CRON_FILE="$R/cron.txt" READER_WATCH_STUB="$R/stub" \
        READER_WATCH_STATE="$R/rw_state.json" READER_WATCH_ALL_OFF="$R/no_all_off" "$@" bash "$R/kit/install_s833.sh" > "$R/out.txt" 2>&1; }
pinof(){ tr -d ' \r\n' < "$R/kit/PIN_$1.txt"; }
at(){ for f in claude_reader clinic_papers; do [ "$(md5sum "$R/app/$f.py" | cut -c1-32)" = "$(pinof $1_$f)" ] || return 1; done; return 0; }

mk; inst DRY=1; grep -q "DRY RUN" "$R/out.txt" && at FROM && [ ! -e "$R/app/reader_watch.py" ]; ok $? "R1 DRY=1: walked and controlled, then stops -- nothing placed"
inst; grep -q "S833_READER_TOLD: DONE" "$R/out.txt" && at TO && [ "$(md5sum "$R/app/reader_watch.py" | cut -c1-32)" = "$(pinof TO_reader_watch)" ] \
  && [ "$(ls "$R/app" | grep -c '\.py\.bak_S833_')" = 2 ] && [ "$(ls "$R/app" | grep -c 'assets\.db\.bak_S833_')" = 1 ] && [ ! -e "$R/lockdir/lock" ] \
  && grep -q "S833_READER_WATCH" "$R/cron.txt" && grep -q "another job" "$R/cron.txt" && grep -q "test: SENT" "$R/out.txt" && grep -q "reader watch on" "$R/stub"
ok $? "R2 the install: DONE, the three files at their TO pins, two backups and the database's, the cron line beside the others, the proof message sent, the lock released"
inst; grep -q "ALREADY INSTALLED" "$R/out.txt" && at TO && [ "$(grep -c S833_READER_WATCH "$R/cron.txt")" = 1 ]; ok $? "R3 a second run: ALREADY INSTALLED (one cron line)"
mk; echo "# other bytes" >> "$R/app/clinic_papers.py"; inst; grep -q "REFUSED: clinic_papers.py is" "$R/out.txt" && ! ls "$R/app" | grep -q bak_S833 && [ ! -e "$R/app/reader_watch.py" ]
ok $? "R4 a FROM file of other bytes: REFUSED, nothing placed"
mk; mkdir -p "$R/lockdir/lock"; echo other > "$R/lockdir/lock/owner"; inst; grep -q "another build holds the lock" "$R/out.txt" && [ -f "$R/lockdir/lock/owner" ] && at FROM
ok $? "R5 another build's lock: REFUSED, its lock left in place"
mk; inst S833_FAKE_HEALTH=500; grep -q "NOT INSTALLED (restored)" "$R/out.txt" && at FROM && [ ! -e "$R/app/reader_watch.py" ] && ! grep -q S833_READER_WATCH "$R/cron.txt" && grep -q "another job" "$R/cron.txt"
ok $? "R6 health red after placing: both files back byte-identically, the watcher taken off, no cron line (the others kept), NOT INSTALLED"
mk; echo "# other bytes" >> "$R/app/sorting_desk.py"; inst; grep -q "REFUSED: sorting_desk.py is" "$R/out.txt" && at FROM && ! ls "$R/app" | grep -q bak_S833
ok $? "R7 a read-only file (the desk) of other bytes: REFUSED, nothing placed"
echo "REHEARSAL S833: $OK green, $BAD red"
[ "$BAD" = 0 ]
