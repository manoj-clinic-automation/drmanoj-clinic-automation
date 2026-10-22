#!/bin/bash
# rehearse_s625.sh -- S625's installer on a MADE-UP root: a copy of this kit and of S624 beside it, a folder holding the app's FROM
# code (asset_register.py at S618's TO, clinic_papers.py, sorting_desk.py, xray_costs.py, and S624's TO three), a made-up database.
#   bash rehearse_s625.sh <that folder>
# R1 DRY=1 nothing placed . R2 DONE: both files at their TO pins, two file backups and the database's, the switch-on row, the lock released . R3 ALREADY
# INSTALLED . R4 a FROM file of other bytes: REFUSED . R5 S624 not installed (batteries.py at its FROM): REFUSED . R6 health red after
# placing: both files back byte-identically, no switch-on row, NOT INSTALLED . R7 the row's write fails, the re-run finishes it.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${1:?the folder with the FROM code}"
PY="${S625_PYTHON:-python3}"
R="$(mktemp -d /tmp/s625reh.XXXXXX)"; trap 'rm -rf "$R"' EXIT
OK=0; BAD=0
ok(){ if [ "$1" = 0 ]; then OK=$((OK+1)); echo "GREEN $2"; else BAD=$((BAD+1)); echo "RED   $2"; tail -8 "$R/out.txt"; fi; }
mkdir -p "$R/kits"; cp -r "$HERE" "$R/kits/S625_MONTH_AND_DAY"; cp -r "$HERE/../S624_SCANAPP_SMALL_FIXES" "$R/kits/"
mk(){ rm -rf "$R/app" "$R/lockdir"; mkdir -p "$R/app" "$R/lockdir"; cp -p "$SRC"/*.py "$R/app/"
      "$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT)'); c.commit()" "$R/app/assets.db"; }
inst(){ env S625_APP_DIR="$R/app" S625_DB="$R/app/assets.db" S625_LOCK="$R/lockdir/lock" S625_HOST="$(hostname)" S625_REHEARSAL=1 S625_RESTART_CMD=true \
        S625_SLEEP=0 S625_HEALTH_TRIES=2 S625_FAKE_HEALTH=200 S625_PYTHON="$PY" "$@" bash "$R/kits/S625_MONTH_AND_DAY/install_s625.sh" > "$R/out.txt" 2>&1; }
at(){ for f in clinic_papers asset_register; do [ "$(md5sum "$R/app/$f.py" | cut -c1-32)" = "$(tr -d ' \r\n' < "$HERE/PIN_$1_$f.txt")" ] || return 1; done; }
key(){ "$PY" -c "import sqlite3,sys; r=sqlite3.connect(sys.argv[1]).execute(\"SELECT value FROM settings WHERE key='papers.month_from_bill_date'\").fetchone(); print(r[0] if r else '')" "$R/app/assets.db"; }
mk; inst DRY=1; grep -q "DRY RUN" "$R/out.txt" && at FROM && [ -z "$(key)" ]; ok $? "R1 DRY=1: rebuilt, both real-app walks and the control run, then stops -- nothing placed, no row"
inst; grep -q "S625_MONTH_AND_DAY: DONE" "$R/out.txt" && at TO && [ "$(ls "$R/app" | grep -c '\.py\.bak_S625_')" = 2 ] && ls "$R/app" | grep -q '^assets.db.bak_S625_' && [ -n "$(key)" ] && [ ! -e "$R/lockdir/lock" ]
ok $? "R2 the install: DONE, both files at their TO pins, two file backups and the database's, the switch-on row ($(key) UTC), the lock released"
inst; grep -q "ALREADY INSTALLED" "$R/out.txt"; ok $? "R3 a second run: ALREADY INSTALLED"
mk; echo "# other bytes" >> "$R/app/clinic_papers.py"; inst; grep -q "REFUSED: clinic_papers.py is" "$R/out.txt" && ! ls "$R/app" | grep -q bak_S625; ok $? "R4 a FROM file of other bytes: REFUSED, nothing placed"
mk; echo "# S624 not installed" >> "$R/app/batteries.py"; inst; grep -q "S624 must be installed FIRST" "$R/out.txt"; ok $? "R5 S624 not installed first: REFUSED"
mk; inst S625_FAKE_HEALTH=500; grep -q "NOT INSTALLED (restored)" "$R/out.txt" && at FROM && [ -z "$(key)" ]; ok $? "R6 health red after placing: both files back byte-identically, no switch-on row, NOT INSTALLED"
mk; rm -f "$R/app/assets.db"; "$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('CREATE TABLE made_up(x)'); c.commit()" "$R/app/assets.db"
inst; F1="$(grep -c 'the switch-on row could not be written' "$R/out.txt")"; at TO; A1=$?
"$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT)'); c.commit()" "$R/app/assets.db"
inst; grep -q "doing it now" "$R/out.txt" && grep -q "S625_MONTH_AND_DAY: DONE" "$R/out.txt" && [ "$F1" = 1 ] && [ "$A1" = 0 ] && [ -n "$(key)" ] && ls "$R/app" | grep -q 'assets.db.bak_S625_'
ok $? "R7 the switch-on row fails to write (the code in place, the old rule stands); the re-run goes straight to the data step: DONE, the row, a database backup first"
echo "REHEARSAL S625: $OK green, $BAD red"
[ "$BAD" = 0 ]
