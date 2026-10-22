#!/bin/bash
# rehearse_s627.sh -- S627's installer on a MADE-UP root: copies of this kit and of S624 and S625 beside it, a folder holding the app's
# FROM code (after S624 and S625), a made-up database.   bash rehearse_s627.sh <that folder>
# R1 DRY=1 nothing placed . R2 DONE: both files at their TO pins, two backups, the data step run, the lock released . R3 ALREADY INSTALLED . R4 a FROM
# file of other bytes: REFUSED . R5 S625 not installed (clinic_papers.py at another byte): REFUSED . R6 health red after placing:
# both files back byte-identically, NOT INSTALLED.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${1:?the folder with the FROM code}"
PY="${S627_PYTHON:-python3}"
R="$(mktemp -d /tmp/s627reh.XXXXXX)"; trap 'rm -rf "$R"' EXIT
OK=0; BAD=0
ok(){ if [ "$1" = 0 ]; then OK=$((OK+1)); echo "GREEN $2"; else BAD=$((BAD+1)); echo "RED   $2"; tail -8 "$R/out.txt"; fi; }
mkdir -p "$R/kits"; for k in S627_LATE_FOLLOWS_MONTH S624_SCANAPP_SMALL_FIXES S625_MONTH_AND_DAY; do cp -r "$HERE/../$k" "$R/kits/"; done
mk(){ rm -rf "$R/app" "$R/lockdir"; mkdir -p "$R/app" "$R/lockdir"; cp -p "$SRC"/*.py "$R/app/"
      "$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT)'); c.commit()" "$R/app/assets.db"; }
inst(){ env S627_APP_DIR="$R/app" S627_DB="$R/app/assets.db" S627_LOCK="$R/lockdir/lock" S627_HOST="$(hostname)" S627_REHEARSAL=1 S627_RESTART_CMD=true \
        S627_SLEEP=0 S627_HEALTH_TRIES=2 S627_FAKE_HEALTH=200 S627_PYTHON="$PY" "$@" bash "$R/kits/S627_LATE_FOLLOWS_MONTH/install_s627.sh" > "$R/out.txt" 2>&1; }
at(){ for f in asset_register sorting_desk; do [ "$(md5sum "$R/app/$f.py" | cut -c1-32)" = "$(tr -d ' \r\n' < "$HERE/PIN_$1_$f.txt")" ] || return 1; done; }
mk; inst DRY=1; grep -q "DRY RUN" "$R/out.txt" && at FROM; ok $? "R1 DRY=1: rebuilt, the real-app walk + control and S624's and S625's walks run, then stops -- nothing placed"
inst; grep -q "S627_LATE_FOLLOWS_MONTH: DONE" "$R/out.txt" && at TO && [ "$(ls "$R/app" | grep -c '\.py\.bak_S627_')" = 2 ] && [ ! -e "$R/lockdir/lock" ]  && grep -q "heal: the month rule is off" "$R/out.txt"
ok $? "R2 the install: DONE, both files at their TO pins, two backups, the data step run, the lock released"
inst; grep -q "ALREADY INSTALLED" "$R/out.txt"; ok $? "R3 a second run: ALREADY INSTALLED"
mk; echo "# other bytes" >> "$R/app/sorting_desk.py"; inst; grep -q "REFUSED: sorting_desk.py is" "$R/out.txt" && ! ls "$R/app" | grep -q bak_S627; ok $? "R4 a FROM file of other bytes: REFUSED, nothing placed"
mk; echo "# S625 not installed" >> "$R/app/clinic_papers.py"; inst; grep -q "REFUSED: clinic_papers.py is" "$R/out.txt"; ok $? "R5 S625 not installed first: REFUSED"
mk; inst S627_FAKE_HEALTH=500; grep -q "NOT INSTALLED (restored)" "$R/out.txt" && at FROM; ok $? "R6 health red after placing: both files back byte-identically, NOT INSTALLED"
echo "REHEARSAL S627: $OK green, $BAD red"
[ "$BAD" = 0 ]
