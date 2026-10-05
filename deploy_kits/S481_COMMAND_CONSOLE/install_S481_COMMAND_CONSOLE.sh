#!/bin/bash
# =============================================================================
# install_S481_COMMAND_CONSOLE.sh -- session 294, 05-Oct-2026 -- the owner's Today tile and command console
#  WHAT IT IS FOR. The owner asked for one big tile at the top of his Clinic app that shows the day at a glance and opens a
#  command console: the day's revenues, what waits for him, who did which export and entry and when, attendance, Sanjeevni,
#  scans and papers, the system -- each section collapsed to a count, expandable, each line opening the page that owns it.
#  PLACES  /root/finance/owner_console.py     NEW   the reader: three doors for the owner only, and a builder that runs as a
#                    SEPARATE SHORT PROCESS on a COPY of finance.db (the owning modules' own functions, the duty map's own
#                    due_sql) and writes one json file. Nothing reads through the live connection but PRAGMA database_list.
#          /root/finance/owner_console.html   NEW   the page; it only draws the reading.
#  EDITS, by apply_s481.py (exact anchors on the real bytes; every anchor exactly once; both verified before either is written):
#          /root/finance/finance_app.py   47a83382 -> ef1382d2   one guarded mount block after packs; the health row
#                    'Parts of the finance app that did not load' learns the part and counts 28.
#          /root/portal/portal.py         d9b7685f -> 10a675e7   the Today tile above the doctor-only strip, hidden until the
#                    console's own tile door answers (so for every login but the owner's the home is exactly as before).
#  NOT TOUCHED: every other page and door, TILES, tile_grants.json, the crontab, any table. No timer job is added: a reading
#  older than five minutes is replaced in the background when the tile or the page asks.
#  HOW IT IS PROVEN BEFORE ANYTHING IS PLACED. The walk copies this box's own finance code, the two files and finance.db
#  into a private scratch folder and works only there: every figure is compared with the owning module's own answer, made-up
#  rows must move the reading by exactly that, a made-up patient name must appear in no reading, and the database the builder
#  read must be byte-identical afterwards. Then ONE READING OF THE REAL BOX is made the same way (read-only) and said here.
#  Only then: backups, place, restart clinic-finance and clinic-portal (about 15 seconds), the after-placing checks, and the
#  first real reading through the placed code. Red after placing -> the two files are put back, the two new files and the
#  reading removed, both services restarted. Run again on an installed box it repeats the after-placing checks.
#  DRY=1 places nothing. NEEDS the build lock free (F-694).
# =============================================================================
set -u
KIT="S481_COMMAND_CONSOLE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; POR="$ROOT/portal"
DB="${FINANCE_DB:-$FIN/finance.db}"
FINURL="${FINURL:-http://127.0.0.1:8106}"; PORURL="${PORURL:-http://127.0.0.1:8099}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
DUTYMAP="${DUTY_MAP_JSON:-/root/deploy/repo/claude_code_briefs/DUTY_MAP.json}"
ATTCORE="${ATTCORE:-$ROOT/att_core.py}"
FA_FROM=47a83382595c59f42b80d2f72831837d; FA_TO=ef1382d2ce26d13d3c8388fdeb85e867
PO_FROM=d9b7685f75926164df34a10eca5dcb77; PO_TO=10a675e750086b4bffc6b1b1e41ea8de
OC_PY=be5558160aebd4f58a159d50740c11c5; OC_HTML=75b5d01735c555a57d5be6ad75fffc07
VERSION="S481 1.0"
SCR=""; PLACED=0; HAVE_LOCK=0; NEW_PY=0; NEW_HTML=0; B_FA=""; B_PO=""; T0=""; RED=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() {
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  [ -n "$SCR" ] && rm -rf "$SCR"
  rm -f "$FIN/.finance_app.py.s481" "$FIN/.owner_console.py.s481" "$FIN/.owner_console.html.s481" "$POR/.portal.py.s481"
}
reading_files() { echo "$FIN/console_reading.dat $FIN/console_reading.dat.lock $FIN/console_reading.dat.err $FIN/console_build.log"; }
restore() {
  trap '' INT TERM HUP                                   # nothing interrupts the putting back
  say "!! RED after placing ($1) - restoring"
  PLACED=0
  \cp -p "$B_FA" "$FIN/finance_app.py"; \cp -p "$B_PO" "$POR/portal.py"
  [ "$NEW_PY" = 1 ] && rm -f "$FIN/owner_console.py"
  [ "$NEW_HTML" = 1 ] && rm -f "$FIN/owner_console.html"
  systemctl restart clinic-finance 2>/dev/null || true; systemctl restart clinic-portal 2>/dev/null || true; sleep 8
  rm -f $(reading_files)                                 # after the restart: no builder of the placed code is left to write one
  if [ "$(m5 "$FIN/finance_app.py")" = "$FA_FROM" ]; then say "   finance_app.py back at $FA_FROM"; else say "   !! finance_app.py is $(m5 "$FIN/finance_app.py"), NOT its old $FA_FROM - put $B_FA back by hand"; fi
  if [ "$(m5 "$POR/portal.py")" = "$PO_FROM" ]; then say "   portal.py back at $PO_FROM"; else say "   !! portal.py is $(m5 "$POR/portal.py"), NOT its old $PO_FROM - put $B_PO back by hand"; fi
  [ "$NEW_PY" = 1 ] && { [ -e "$FIN/owner_console.py" ] && say "   !! owner_console.py is still there - remove it by hand" || say "   owner_console.py removed"; }
  [ "$NEW_HTML" = 1 ] && { [ -e "$FIN/owner_console.html" ] && say "   !! owner_console.html is still there - remove it by hand" || say "   owner_console.html removed"; }
  say "   finance healthz $(health "$FINURL/finance/healthz") · portal health $(health "$PORURL/portal/health")"
  clean; exit 1
}
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
on_signal() {
  # the line was cut (Ctrl-C, a dropped connection): never leave the box half placed
  trap '' INT TERM HUP
  say ""; say "!! interrupted"
  if [ "$PLACED" = 1 ]; then restore "the run was interrupted after placing"; fi
  clean; exit 130
}
trap on_exit EXIT
trap on_signal INT TERM HUP
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }

md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 owner_console.py)" = "$OC_PY" ] && [ "$(m5 owner_console.html)" = "$OC_HTML" ] || { say "!! [1/7] the kit's owner_console files are not the ones this installer names - nothing installed"; exit 1; }
"$SPY" -c "import flask, jinja2, sqlite3" 2>/dev/null || { say "!! [1/7] $SPY lacks flask or jinja2 (the walk and the builder need them) - nothing installed"; exit 1; }
mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
if [ "$HAVE_LOCK" != 1 ]; then
  say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
SCR="$(mktemp -d "/tmp/s481_scratch_XXXXXXXX")" || { say "!! [1/7] no scratch folder - nothing installed"; exit 1; }
chmod 700 "$SCR"
say "[1/7] kit gates green (SUMS, KIT_ID, the two new files' own md5, flask and jinja2); the build lock is taken"

post_checks() {
  # every check made after placing; RED carries the first reason. Runs in this shell (never in a subshell), so the caller decides.
  RED=""
  for s in clinic-finance clinic-portal; do systemctl is-active --quiet "$s" || { RED="$s not active"; return 1; }; done
  c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || { RED="finance healthz $c1"; return 1; }
  p1=$(health "$PORURL/portal/health"); [ "$p1" = 200 ] || { RED="portal /portal/health $p1"; return 1; }
  p2=$(health "$PORURL/portal/login"); case "$p2" in 200|302) ;; *) RED="portal /portal/login $p2"; return 1;; esac
  for u in /finance/console /finance/console/api/state /finance/console/api/tile; do
    c=$(health "$FINURL$u"); case "$c" in 302|401) ;; *) RED="$u answered $c without a login (it must be behind the login gate)"; return 1;; esac
  done
  c5=$(health "$FINURL/finance/approvals"); case "$c5" in 302|401) ;; *) RED="/finance/approvals answered $c5 without a login"; return 1;; esac
  D1="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
  echo "$D1" | grep -q '"NOT_YOU"' || { RED="the heartbeat door no longer refuses an unsigned heartbeat: $(echo "$D1" | cut -c1-160)"; return 1; }
  if [ -n "$T0" ]; then
    if journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted"; then RED="a part of the finance app did NOT mount"; return 1; fi
    for s in clinic-finance clinic-portal; do
      JR="$(journalctl -u "$s" --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
      [ "${JR:-0}" = 0 ] || { RED="$s journal: $JR error line(s)"; return 1; }
    done
  fi
  ( cd "$FIN" && "$SPY" -B -c "import owner_console; assert owner_console.VERSION == '$VERSION' and callable(owner_console.init)" ) 2>/dev/null || { RED="the placed owner_console.py does not load under $SPY"; return 1; }
  # the first real reading, through the placed file, exactly as the service's builder runs it (same user, same file)
  ( cd "$FIN" && FINANCE_DB="$DB" DUTY_MAP_JSON="$DUTYMAP" timeout 150 "$SPY" -B "$FIN/owner_console.py" --build --db "$DB" --out "$FIN/console_reading.dat" > "$SCR/first_reading.log" 2>&1 ) || { RED="the placed builder did not make a reading: $(tail -1 "$SCR/first_reading.log" | cut -c1-200)"; return 1; }
  ROUT="$("$SPY" -B "$KDIR/reading_s481.py" show "$FIN/console_reading.dat" 2>&1)"
  echo "$ROUT" | grep -v '^READING ' | cut -c1-330
  echo "$ROUT" | tail -1 | grep -q '^READING OK' || { RED="the first reading is not sound: $(echo "$ROUT" | tail -1 | cut -c1-250)"; return 1; }
  [ "$(stat -c '%a' "$FIN/console_reading.dat" 2>/dev/null)" = 600 ] || { RED="the reading file is not readable by its owner only"; return 1; }
  return 0
}
POST_OK="both services active · finance healthz 200 · portal health and login as before · the console's page and its two doors behind the login gate · the heartbeat door as before · every part mounted · both journals clean · the first real reading made by the placed builder"

H_FA="$(m5 "$FIN/finance_app.py")"; H_PO="$(m5 "$POR/portal.py")"; H_PY="$(m5 "$FIN/owner_console.py")"; H_HT="$(m5 "$FIN/owner_console.html")"
if [ "$H_FA" = "$FA_TO" ] && [ "$H_PO" = "$PO_TO" ] && [ "$H_PY" = "$OC_PY" ] && [ "$H_HT" = "$OC_HTML" ]; then
  say "-- ALREADY INSTALLED: the four files at the kit's pins. The after-placing checks, again:"
  post_checks || { say "!! installed, but a check is RED: $RED"; say "   Nothing was changed by this run. Tell the assistant; the undo line is in the kit's README."; clean; exit 1; }
  say "   $POST_OK"
  clean; exit 0
fi
if [ "$H_FA" = "$FA_TO" ] || [ "$H_PO" = "$PO_TO" ]; then
  say "!! [2/7] one of the two edited files is already at the kit's pin and the rest is not - a half state. Nothing installed; tell the assistant."
  say "   finance_app.py $H_FA · portal.py $H_PO · owner_console.py ${H_PY:-absent} · owner_console.html ${H_HT:-absent}"; clean; exit 1
fi
[ "$H_FA" = "$FA_FROM" ] || { say "!! [2/7] $FIN/finance_app.py is $H_FA, not $FA_FROM - another kit changed it after this one was built. Nothing installed; tell the assistant, the kit is rebuilt on the new file."; clean; exit 1; }
[ "$H_PO" = "$PO_FROM" ] || { say "!! [2/7] $POR/portal.py is $H_PO, not $PO_FROM - another kit changed it after this one was built. Nothing installed; tell the assistant, the kit is rebuilt on the new file."; clean; exit 1; }
if [ -e "$FIN/owner_console.py" ]; then [ "$H_PY" = "$OC_PY" ] || { say "!! [2/7] a different $FIN/owner_console.py ($H_PY) is already there - nothing installed; tell the assistant."; clean; exit 1; }; else NEW_PY=1; fi
if [ -e "$FIN/owner_console.html" ]; then [ "$H_HT" = "$OC_HTML" ] || { say "!! [2/7] a different $FIN/owner_console.html ($H_HT) is already there - nothing installed; tell the assistant."; clean; exit 1; }; else NEW_HTML=1; fi
[ -f "$DB" ] || { say "!! [2/7] $DB is not there - nothing installed"; clean; exit 1; }
[ -f "$ATTCORE" ] || { say "!! [2/7] $ATTCORE (the attendance engine) is not there - nothing installed; tell the assistant."; clean; exit 1; }
[ -f "$DUTYMAP" ] || { say "!! [2/7] $DUTYMAP (the duty map) is not there - nothing installed; tell the assistant."; clean; exit 1; }
N_GR="$(m5 "$POR/tile_grants.json")"; N_CR="$(crontab -l 2>/dev/null | md5sum | awk '{print $1}')"
say "[2/7] finance_app.py and portal.py at the pins this kit was built on; the two new files $([ "$NEW_PY$NEW_HTML" = 11 ] && echo "not there yet (they are new)" || echo "already the kit's"); the database, the attendance engine and the duty map in place"

\cp -p "$FIN/finance_app.py" "$SCR/finance_app.py" && \cp -p "$POR/portal.py" "$SCR/portal.py" || { say "!! [3/7] no scratch copy - nothing installed"; clean; exit 1; }
"$SPY" -B apply_s481.py "$SCR/finance_app.py" "$SCR/portal.py" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/7] the edits did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
[ "$(m5 "$SCR/finance_app.py")" = "$FA_TO" ] && [ "$(m5 "$SCR/portal.py")" = "$PO_TO" ] || { say "!! [3/7] the edited scratch copies are not their predicted bytes - nothing installed"; clean; exit 1; }
"$SPY" -B -c "
import sys
for p in sys.argv[1:]:
    compile(open(p, encoding='utf-8').read(), p, 'exec')
" apply_s481.py walk_s481.py reading_s481.py owner_console.py "$SCR/finance_app.py" "$SCR/portal.py" 2>"$SCR/compile.err" || { say "!! [3/7] compile failed: $(tail -1 "$SCR/compile.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
say "[3/7] the five edits apply to scratch copies and give the predicted bytes; everything compiles"

WOUT="$( cd /tmp && TMPDIR="$SCR" timeout 900 "$SPY" -B "$KDIR/walk_s481.py" --kit "$KDIR" --finance "$FIN" --portal "$POR/portal.py" --db "$DB" --attcore "$ATTCORE" --dutymap "$DUTYMAP" ${WALK_EXTRA:-} 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^  note|^WALK_S481' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S481 GREEN" || { say "!! [4/7] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
[ "$(m5 "$FIN/finance_app.py")" = "$FA_FROM" ] && [ "$(m5 "$POR/portal.py")" = "$PO_FROM" ] || { say "!! [4/7] a file changed during the walk - nothing installed"; clean; exit 1; }
say "[4/7] walk green on copies of this box (its own code, its own database, made-up rows). Now ONE READING OF THE REAL BOX, read-only:"
real_reading() {  # $1 = words for the line, $2 = a PACKS_TODAY to read as (or nothing)
  ROUT="$( cd /tmp && env TMPDIR="$SCR" FINANCE_DB="$DB" DUTY_MAP_JSON="$DUTYMAP" ${2:+PACKS_TODAY=$2} timeout 200 "$SPY" -B "$KDIR/reading_s481.py" build "$KDIR" "$FIN" "$DB" "$SCR/real_reading.dat" 2>&1 )"
  echo "$ROUT" | grep '^   ' | cut -c1-330
  echo "$ROUT" | tail -1 | grep -q '^READING OK' || { say "!! [4/7] the reading of the real box ($1) is RED: $(echo "$ROUT" | tail -1 | cut -c1-300)"; say "   Nothing installed. Tell the assistant with this output."; echo "$ROUT" | tail -12 | cut -c1-300; clean; exit 1; }
}
real_reading "as today" ""
say "      and once more as the 15th of the month would read (from the 10th the month-end list takes its long road):"
real_reading "as the 15th" "$(date '+%Y-%m-15')"
[ "$(m5 "$FIN/finance_app.py")" = "$FA_FROM" ] && [ "$(m5 "$POR/portal.py")" = "$PO_FROM" ] || { say "!! [4/7] a file changed during the reading - nothing installed"; clean; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the real box's reading green; NOTHING placed, nothing restarted"; clean; exit 0; fi

B_FA="$FIN/finance_app.py.bak_S481_$(echo "$FA_FROM" | cut -c1-8)"; B_PO="$POR/portal.py.bak_S481_$(echo "$PO_FROM" | cut -c1-8)"
\cp -p "$FIN/finance_app.py" "$B_FA" && \cp -p "$POR/portal.py" "$B_PO" && [ "$(m5 "$B_FA")" = "$FA_FROM" ] && [ "$(m5 "$B_PO")" = "$PO_FROM" ] || { say "!! [5/7] a backup failed - nothing placed"; clean; exit 1; }
say "[5/7] backups: $B_FA $B_PO"
stage() {  # $1 = the live file whose owner and mode are kept, $2 = the new bytes, $3 = the staged name, $4 = its md5
  \cp -p "$1" "$3" && cat "$2" > "$3" && [ "$(m5 "$3")" = "$4" ]
}
stage "$FIN/finance_app.py" "$SCR/finance_app.py" "$FIN/.finance_app.py.s481" "$FA_TO" && stage "$FIN/finance_app.py" "$KDIR/owner_console.py" "$FIN/.owner_console.py.s481" "$OC_PY" \
  && stage "$FIN/finance_app.py" "$KDIR/owner_console.html" "$FIN/.owner_console.html.s481" "$OC_HTML" && stage "$POR/portal.py" "$SCR/portal.py" "$POR/.portal.py.s481" "$PO_TO" \
  || { say "!! [6/7] could not stage the files - nothing placed"; clean; exit 1; }
PLACED=1
mv -f "$FIN/.owner_console.html.s481" "$FIN/owner_console.html" || restore "placing owner_console.html"
mv -f "$FIN/.owner_console.py.s481" "$FIN/owner_console.py" || restore "placing owner_console.py"
mv -f "$FIN/.finance_app.py.s481" "$FIN/finance_app.py" || restore "placing finance_app.py"
mv -f "$POR/.portal.py.s481" "$POR/portal.py" || restore "placing portal.py"
[ "$(m5 "$FIN/finance_app.py")" = "$FA_TO" ] && [ "$(m5 "$POR/portal.py")" = "$PO_TO" ] && [ "$(m5 "$FIN/owner_console.py")" = "$OC_PY" ] && [ "$(m5 "$FIN/owner_console.html")" = "$OC_HTML" ] || restore "md5 read-back"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
systemctl restart clinic-portal || restore "restart clinic-portal"
sleep 9
post_checks || restore "$RED"
[ "$(m5 "$POR/tile_grants.json")" = "$N_GR" ] && [ "$(crontab -l 2>/dev/null | md5sum | awk '{print $1}')" = "$N_CR" ] || restore "tile_grants.json or the crontab moved during the install"
PLACED=0
say "[6/7] placed, md5 read back = the kit's pins · $POST_OK"
say "[7/7] nothing else moved (tile_grants.json, the crontab). Open the Clinic app: the Today tile is at the top of the home page."
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/finance_app.py" "$POR/portal.py" "$FIN/owner_console.py" "$FIN/owner_console.html"
exit 0
