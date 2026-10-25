#!/bin/bash
# rehearse_s651.sh -- S651's installer on a MADE-UP root (never the live box): a copy of the kit, an app folder holding the FROM
# asset_register.py and sorting_desk.py with the read-only files at their pins (and the app's other top-level code files), a shared
# folder with the FROM scan_checks_s441.py, a made-up database, no service (restart = true, health faked).
#   bash rehearse_s651.sh <app folder with the FROM files> <folder with the FROM scan_checks_s441.py>
# R1 DRY=1 nothing placed . R2 DONE: the three at their TO pins, their backups and the database's, the lock released, no traceback .
# R3 ALREADY INSTALLED . R4 a FROM file of other bytes (the shared one): REFUSED, nothing placed . R5 another build's lock: REFUSED,
# left in place . R6 health red after placing: all three back byte-identically, NOT INSTALLED . R7 a read-only file of other bytes
# (the reader): REFUSED, nothing placed . R8 an unknown *scan* column in the finance database: REFUSED, nothing placed.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${1:?the app folder}"; SSRC="${2:?the shared folder}"
PY="${S651_PYTHON:-python3}"
R="$(mktemp -d /tmp/s651reh.XXXXXX)"; trap 'rm -rf "$R"' EXIT
OK=0; BAD=0
ok(){ if [ "$1" = 0 ]; then OK=$((OK+1)); echo "GREEN $2"; else BAD=$((BAD+1)); echo "RED   $2"; tail -14 "$R/out.txt"; fi; }
cp -r "$HERE" "$R/kit"
mk(){ rm -rf "$R/app" "$R/shared" "$R/lockdir"; mkdir -p "$R/app" "$R/shared" "$R/lockdir"; for f in "$SRC"/*.py "$SRC"/*.js "$SRC"/*.json; do [ -f "$f" ] && cp -p "$f" "$R/app/"; done
      cp -p "$SSRC/scan_checks_s441.py" "$R/shared/"
      "$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('CREATE TABLE made_up(x)'); c.commit()" "$R/app/assets.db"
      rm -f "$R/fin.db"; "$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('CREATE TABLE order_scan_tie(id INTEGER, asset_bill_id INTEGER, stamp TEXT, scan_at TEXT)'); c.commit()" "$R/fin.db"; }
inst(){ env S651_APP_DIR="$R/app" S651_SHARED_DIR="$R/shared" S651_DB="$R/app/assets.db" S651_LOCK="$R/lockdir/lock" S651_HOST="$(hostname)" S651_REHEARSAL=1 \
        S651_RESTART_CMD=true S651_SLEEP=0 S651_HEALTH_TRIES=2 S651_FAKE_HEALTH=200 S651_PYTHON="$PY" S651_FIN_DB="$R/fin.db" "$@" bash "$R/kit/install_s651.sh" > "$R/out.txt" 2>&1; }
pinof(){ tr -d ' \r\n' < "$R/kit/PIN_$1.txt"; }
at(){ [ "$(md5sum "$R/shared/scan_checks_s441.py" | cut -c1-32)" = "$(pinof $1_scan_checks_s441)" ] && [ "$(md5sum "$R/app/asset_register.py" | cut -c1-32)" = "$(pinof $1_asset_register)" ] \
      && [ "$(md5sum "$R/app/sorting_desk.py" | cut -c1-32)" = "$(pinof $1_sorting_desk)" ]; }
nobak(){ ! ls "$R/app" "$R/shared" | grep -q bak_S651; }

mk; inst DRY=1; grep -q "DRY RUN" "$R/out.txt" && at FROM && nobak; ok $? "R1 DRY=1: both walks and the control, then stops -- the files untouched"
inst; grep -q "S651_CLEARER_DUPLICATE: DONE" "$R/out.txt" && at TO && [ "$(ls "$R/app" "$R/shared" | grep -c '\.py\.bak_S651_')" = 3 ] \
  && [ "$(ls "$R/app" | grep -c 'assets\.db\.bak_S651_')" = 1 ] && [ ! -e "$R/lockdir/lock" ] && ! grep -qE "Traceback|SyntaxError" "$R/out.txt"
ok $? "R2 the install: DONE, the three at their TO pins, their backups and the database's, the lock released, no traceback"
inst; grep -q "ALREADY INSTALLED" "$R/out.txt" && at TO; ok $? "R3 a second run: ALREADY INSTALLED"
mk; echo "# other bytes" >> "$R/shared/scan_checks_s441.py"; inst; grep -q "REFUSED: scan_checks_s441.py is" "$R/out.txt" && nobak
ok $? "R4 a FROM file of other bytes (the shared one): REFUSED, nothing placed"
mk; mkdir -p "$R/lockdir/lock"; echo other > "$R/lockdir/lock/owner"; inst; grep -q "another build holds the lock" "$R/out.txt" && [ -f "$R/lockdir/lock/owner" ] && at FROM
ok $? "R5 another build's lock: REFUSED, its lock left in place"
mk; inst S651_FAKE_HEALTH=500; grep -q "NOT INSTALLED (restored)" "$R/out.txt" && at FROM
ok $? "R6 health red after placing: all three back byte-identically, NOT INSTALLED"
mk; echo "# other bytes" >> "$R/app/claude_reader.py"; inst; grep -q "REFUSED: claude_reader.py is" "$R/out.txt" && at FROM && nobak
ok $? "R7 a read-only file (the reader) of other bytes: REFUSED, nothing placed"
mk; "$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('CREATE TABLE made_up_link(id INTEGER, scan_owner INTEGER)'); c.commit()" "$R/fin.db"
inst; grep -q "REFUSED: the finance database has a column named" "$R/out.txt" && at FROM && nobak
ok $? "R8 the finance database has a column named *scan* the rule does not know: REFUSED, nothing placed"
echo "REHEARSAL S651: $OK green, $BAD red"
[ "$BAD" = 0 ]
