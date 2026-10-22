#!/bin/bash
# rehearse_s624.sh -- S624's installer on a MADE-UP root (never the live box): a copy of the kit, a folder holding the FROM bytes of the
# three files and of the read-only files, no service (restart = true, health faked).
#   bash rehearse_s624.sh <folder with the FROM batteries.py, asset_machine.py, stationery.py, sorting_desk.py, xray_costs.py,
#                          clinic_papers.py and an asset_register.py>
# The rehearsal's own copy of the kit pins the given asset_register.py (the live one is S618's TO, in no bundle yet).
# R1 DRY=1 nothing placed . R2 DONE: the three files at their TO pins, backups beside them, the lock released . R3 ALREADY INSTALLED .
# R4 a FROM file of other bytes: REFUSED, nothing placed . R5 another build's lock: REFUSED, left in place . R6 health red after placing:
# the three files back byte-identically, NOT INSTALLED.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${1:?the folder with the FROM files}"
PY="${S624_PYTHON:-python3}"
R="$(mktemp -d /tmp/s624reh.XXXXXX)"; trap 'rm -rf "$R"' EXIT
OK=0; BAD=0
ok(){ if [ "$1" = 0 ]; then OK=$((OK+1)); echo "GREEN $2"; else BAD=$((BAD+1)); echo "RED   $2"; tail -6 "$R/out.txt"; fi; }
cp -r "$HERE" "$R/kit"; md5sum "$SRC/asset_register.py" | cut -c1-32 > "$R/kit/PIN_READ_asset_register.txt"
mk(){ rm -rf "$R/app" "$R/lockdir"; mkdir -p "$R/app" "$R/lockdir"; for f in batteries.py asset_machine.py stationery.py sorting_desk.py xray_costs.py clinic_papers.py asset_register.py; do cp -p "$SRC/$f" "$R/app/"; done
      "$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('CREATE TABLE made_up(x)'); c.commit()" "$R/app/assets.db"; }
inst(){ env S624_APP_DIR="$R/app" S624_DB="$R/app/assets.db" S624_LOCK="$R/lockdir/lock" S624_HOST="$(hostname)" S624_REHEARSAL=1 S624_RESTART_CMD=true S624_SLEEP=0 \
        S624_HEALTH_TRIES=2 S624_FAKE_HEALTH=200 S624_PYTHON="$PY" "$@" bash "$R/kit/install_s624.sh" > "$R/out.txt" 2>&1; }
at(){ for f in batteries asset_machine stationery; do [ "$(md5sum "$R/app/$f.py" | cut -c1-32)" = "$(tr -d ' \r\n' < "$R/kit/PIN_$1_$f.txt")" ] || return 1; done; }

mk; inst DRY=1; grep -q "DRY RUN" "$R/out.txt" && at FROM; ok $? "R1 DRY=1: rebuilt, walked and controlled, then stops -- the three files untouched"
inst; grep -q "S624_SCANAPP_SMALL_FIXES: DONE" "$R/out.txt" && at TO && [ "$(ls "$R/app" | grep -c '\.bak_S624_')" = 3 ] && [ ! -e "$R/lockdir/lock" ]
ok $? "R2 the install: DONE, the three files at their TO pins, three backups, the lock released"
inst; grep -q "ALREADY INSTALLED" "$R/out.txt" && at TO; ok $? "R3 a second run: ALREADY INSTALLED"
mk; echo "# other bytes" >> "$R/app/stationery.py"; inst; grep -q "REFUSED: stationery.py is" "$R/out.txt" && ! ls "$R/app" | grep -q bak_S624; ok $? "R4 a FROM file of other bytes: REFUSED, nothing placed"
mk; mkdir -p "$R/lockdir/lock"; echo other > "$R/lockdir/lock/owner"; inst; grep -q "another build holds the lock" "$R/out.txt" && [ -f "$R/lockdir/lock/owner" ] && at FROM
ok $? "R5 another build's lock: REFUSED, its lock left in place"
mk; inst S624_FAKE_HEALTH=500; grep -q "NOT INSTALLED (restored)" "$R/out.txt" && at FROM; ok $? "R6 health red after placing: the three files back byte-identically, NOT INSTALLED"
echo "REHEARSAL S624: $OK green, $BAD red"
[ "$BAD" = 0 ]
