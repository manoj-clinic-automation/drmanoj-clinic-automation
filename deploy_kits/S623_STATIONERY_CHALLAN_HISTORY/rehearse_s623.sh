#!/bin/bash
# rehearse_s623.sh -- S623's installer rehearsed on a MADE-UP root (never the live box's files or database).
#   bash rehearse_s623.sh <folder holding the live stationery.py and sorting_desk.py bytes>
# R1 DRY=1 stops before the backup, nothing written . R2 the install says DONE and verify is green . R3 a second run says ALREADY
# INSTALLED . R4 a stationery.py of other bytes is REFUSED . R5 a lock held by another build is REFUSED (and left in place) .
# R6 a database where no paper can be written: the rehearsal on the copy refuses, nothing written, the key not set.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FROM="${1:?the folder with the live stationery.py and sorting_desk.py}"
PY="${S623_PYTHON:-python3}"
R="$(mktemp -d /tmp/s623reh.XXXXXX)"; trap 'rm -rf "$R"' EXIT
OK=0; BAD=0
ok(){ if [ "$1" = 0 ]; then OK=$((OK+1)); echo "GREEN $2"; else BAD=$((BAD+1)); echo "RED   $2"; tail -5 "$R/out.txt"; fi; }
mk(){ rm -rf "$R/app" "$R/lock"; mkdir -p "$R/app" "$R/lockdir"; cp -p "$FROM/stationery.py" "$FROM/sorting_desk.py" "$R/app/"
      "$PY" -B "$HERE/walk_s623.py" --app "$R/app" --kit "$HERE" --make-db "$R/app/assets.db" >/dev/null; }
inst(){ env S623_APP_DIR="$R/app" S623_DB="$R/app/assets.db" S623_LOCK="$R/lockdir/lock" S623_HOST="$(hostname)" S623_REHEARSAL=1 \
        S623_HEALTH_URL=skip S623_PYTHON="$PY" "$@" bash "$HERE/install_s623.sh" > "$R/out.txt" 2>&1; }
lines(){ "$PY" -c "import sqlite3,sys; print(sqlite3.connect(sys.argv[1]).execute('SELECT COUNT(*), COALESCE(SUM(qty),0) FROM stationery_line WHERE voided_at=\'\'').fetchone())" "$R/app/assets.db"; }
key(){ "$PY" -c "import sqlite3,sys; print(1 if sqlite3.connect(sys.argv[1]).execute(\"SELECT 1 FROM settings WHERE key='stationery.history_s623'\").fetchone() else 0)" "$R/app/assets.db"; }

mk; b="$(lines)"
inst DRY=1; grep -q "DRY RUN" "$R/out.txt" && [ "$(lines)" = "$b" ] && [ "$(key)" = 0 ]; ok $? "R1 DRY=1: the walk and the rehearsal on a copy, then stops -- nothing written ($(grep -c '^GREEN' "$R/out.txt") green lines)"
inst; grep -q "S623_STATIONERY_CHALLAN_HISTORY: DONE" "$R/out.txt" && [ "$(key)" = 1 ] && "$PY" -B "$HERE/history_s623.py" --verify "$R/app/assets.db" --app "$R/app" >/dev/null; ok $? "R2 the install: DONE, the key set, verify green"
[ ! -e "$R/lockdir/lock" ]; ok $? "R2b the build lock released after the install"
ls "$R/app/" | grep -q '^assets.db.bak_S623_'; ok $? "R2c the database backup beside it"
a="$(lines)"; inst; grep -q "ALREADY INSTALLED" "$R/out.txt" && [ "$(lines)" = "$a" ]; ok $? "R3 a second run: ALREADY INSTALLED, nothing written"
mk; echo "# other bytes" >> "$R/app/stationery.py"; b="$(lines)"; inst; grep -q "REFUSED: stationery.py is" "$R/out.txt" && [ "$(lines)" = "$b" ]; ok $? "R4 stationery.py of other bytes: REFUSED, nothing written"
mk; mkdir -p "$R/lockdir/lock"; echo "another build" > "$R/lockdir/lock/owner"; b="$(lines)"; inst; grep -q "another build holds the lock" "$R/out.txt" && [ "$(lines)" = "$b" ] && [ -f "$R/lockdir/lock/owner" ]; ok $? "R5 a lock held by another build: REFUSED, the other build's lock left in place"
rm -rf "$R/lockdir/lock"
mk; "$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute(\"UPDATE bills SET subgroup='other' WHERE id IN (3,13,109,114,133,163)\"); c.commit()" "$R/app/assets.db"
b="$(lines)"; inst; grep -q "REFUSED: the step REFUSED on the scratch copy" "$R/out.txt" && [ "$(lines)" = "$b" ] && [ "$(key)" = 0 ] && ! ls "$R/app/" | grep -q '^assets.db.bak_S623_'; ok $? "R6 no paper can be written: REFUSED at the rehearsal on the copy, nothing written, no backup, the key not set"
echo "REHEARSAL S623: $OK green, $BAD red"
[ "$BAD" = 0 ]
