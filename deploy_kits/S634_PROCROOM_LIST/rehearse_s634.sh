#!/bin/bash
# rehearse_s634.sh -- S634's installer on a MADE-UP root (never the live box): a copy of the kit, a folder holding the FROM
# sorting_desk.py and asset_register.py and the read-only files at their pins (and the app's other top-level code files), a made-up
# database, no service (restart = true, health faked).
#   bash rehearse_s634.sh <folder with the FROM files>
# R1 DRY=1 nothing placed . R2 DONE: the two files at their TO pins, procroom.py placed, two backups and the database's, the list seeded
# (30 products), the lock released . R3 ALREADY INSTALLED . R4 a FROM file of other bytes: REFUSED, nothing placed . R5 another build's
# lock: REFUSED, left in place . R6 health red after placing: the files back byte-identically, procroom.py moved aside, NOT INSTALLED .
# R7 a read-only file of other bytes: REFUSED, nothing placed . R8 a procroom.py already there (other bytes): REFUSED, nothing placed.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${1:?the folder with the FROM files}"
PY="${S634_PYTHON:-python3}"
R="$(mktemp -d /tmp/s634reh.XXXXXX)"; trap 'rm -rf "$R"' EXIT
OK=0; BAD=0
ok(){ if [ "$1" = 0 ]; then OK=$((OK+1)); echo "GREEN $2"; else BAD=$((BAD+1)); echo "RED   $2"; tail -12 "$R/out.txt"; fi; }
cp -r "$HERE" "$R/kit"
mk(){ rm -rf "$R/app" "$R/lockdir"; mkdir -p "$R/app" "$R/lockdir"; for f in "$SRC"/*.py "$SRC"/*.js "$SRC"/*.json; do [ -f "$f" ] && cp -p "$f" "$R/app/"; done
      rm -f "$R/app/procroom.py"
      "$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('CREATE TABLE made_up(x)'); c.execute('CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT)'); c.commit()" "$R/app/assets.db"; }
inst(){ env S634_APP_DIR="$R/app" S634_DB="$R/app/assets.db" S634_LOCK="$R/lockdir/lock" S634_HOST="$(hostname)" S634_REHEARSAL=1 S634_RESTART_CMD=true S634_SLEEP=0 \
        S634_HEALTH_TRIES=2 S634_FAKE_HEALTH=200 S634_PYTHON="$PY" "$@" bash "$R/kit/install_s634.sh" > "$R/out.txt" 2>&1; }
pinof(){ tr -d ' \r\n' < "$R/kit/PIN_$1.txt"; }
at(){ [ "$(md5sum "$R/app/sorting_desk.py" | cut -c1-32)" = "$(pinof $1_sorting_desk)" ] && [ "$(md5sum "$R/app/asset_register.py" | cut -c1-32)" = "$(pinof $1_asset_register)" ]; }
seeded(){ "$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); n=c.execute('SELECT COUNT(*) FROM proc_item').fetchone()[0]; sys.exit(0 if n==30 else 1)" "$R/app/assets.db" 2>/dev/null; }

mk; inst DRY=1; grep -q "DRY RUN" "$R/out.txt" && at FROM && [ ! -e "$R/app/procroom.py" ]; ok $? "R1 DRY=1: rebuilt, walked and controlled, then stops -- the files untouched, procroom.py not placed"
inst; grep -q "S634_PROCROOM_LIST: DONE" "$R/out.txt" && at TO && [ "$(md5sum "$R/app/procroom.py" | cut -c1-32)" = "$(pinof TO_procroom)" ] \
  && [ "$(ls "$R/app" | grep -c '\.py\.bak_S634_')" = 2 ] && [ "$(ls "$R/app" | grep -c 'assets\.db\.bak_S634_')" = 1 ] && seeded && grep -q "seed: 30 product(s) written" "$R/out.txt" && [ ! -e "$R/lockdir/lock" ]
ok $? "R2 the install: DONE, the two files at their TO pins, procroom.py placed, two backups and the database's, the list seeded (30), the lock released"
inst; grep -q "ALREADY INSTALLED" "$R/out.txt" && at TO && seeded; ok $? "R3 a second run: ALREADY INSTALLED (the list still 30)"
mk; echo "# other bytes" >> "$R/app/sorting_desk.py"; inst; grep -q "REFUSED: sorting_desk.py is" "$R/out.txt" && ! ls "$R/app" | grep -q bak_S634 && [ ! -e "$R/app/procroom.py" ]
ok $? "R4 a FROM file of other bytes: REFUSED, nothing placed"
mk; mkdir -p "$R/lockdir/lock"; echo other > "$R/lockdir/lock/owner"; inst; grep -q "another build holds the lock" "$R/out.txt" && [ -f "$R/lockdir/lock/owner" ] && at FROM
ok $? "R5 another build's lock: REFUSED, its lock left in place"
mk; inst S634_FAKE_HEALTH=500; grep -q "NOT INSTALLED (restored)" "$R/out.txt" && at FROM && [ ! -e "$R/app/procroom.py" ] && [ -e "$R/app/procroom.py.off_S634" ]
ok $? "R6 health red after placing: the files back byte-identically, procroom.py moved aside, NOT INSTALLED"
mk; echo "# other bytes" >> "$R/app/stationery.py"; inst; grep -q "REFUSED: stationery.py is" "$R/out.txt" && at FROM && ! ls "$R/app" | grep -q bak_S634
ok $? "R7 a read-only file of other bytes: REFUSED, nothing placed"
mk; echo "# someone's" > "$R/app/procroom.py"; inst; grep -q "REFUSED: .*procroom.py is already there" "$R/out.txt" && at FROM && ! ls "$R/app" | grep -q bak_S634
ok $? "R8 a procroom.py already there (other bytes): REFUSED, nothing placed"
echo "REHEARSAL S634: $OK green, $BAD red"
[ "$BAD" = 0 ]
