#!/bin/bash
# =============================================================================
# install_S487_AAJ_KA_KAAM.sh -- session 294, 05-Oct-2026 -- the staff's own daily list ("Aaj ka kaam"), D679
#  WHAT IT IS FOR. The owner's word, 05-Oct: "Start staff lists build now, dont populate old stale data, use from current
#  month only, and the leftovers of September." Each person gets one screen, in Roman Hinglish, of what is theirs to do
#  today: the duty map's own lines (claude_code_briefs/DUTY_MAP.json, D648) plus the parent's daily / weekly / monthly lines,
#  NOTHING OLDER THAN 01-SEP-2026 SHOWN OR COUNTED. The owner's console reads the very same lines.
#  IT INSTALLS SWITCHED OFF FOR STAFF. The owner opens each person's list from his console, and turns the lists on with one
#  tap there when the wording is right. Until then the staff's home page is exactly as before.
#  PLACES  /root/finance/aaj_kaam.py      NEW   the list engine (read-only door, the floor laid as TEMP views under the map's
#                    SQL so the map is not edited) and five doors under /finance/aaj
#          /root/finance/aaj_kaam.html    NEW   the staff's page; it only draws the list
#          /root/finance/aaj_duties.json  NEW   the floor, who works which queue, and the parent's extra lines
#          /root/finance/owner_console.py    be555816 -> 4819eceb   1.1: the staff section and the owner's own lines are cut
#          /root/finance/owner_console.html  75b5d017 -> e6d35d88  from the list engine, on the floor; the on/off switch
#  EDITS, by apply_s487.py (exact anchors on the real bytes; every anchor exactly once; both verified before either is written):
#          /root/finance/finance_app.py   ef1382d2 -> bff362c3   the list's five doors need a signed-in login only; one guarded
#                    mount; the health row learns the part and counts 29
#          /root/portal/portal.py         10a675e7 -> 63df9d49   the staff's "Aaj ka kaam" tile, hidden until its door says show
#  WRITES NOTHING AT INSTALL: no table, no setting, no unit row, no timer job. The switch is one setting (aaj.staff_on) written
#  by the owner's tap; the tap table (duty_tick) is made on the first staff tap.
#  HOW IT IS PROVEN BEFORE ANYTHING IS PLACED. The walk copies this box's own finance code, the two files and finance.db into
#  a private scratch folder and works only there, inside the WHOLE edited finance app: the floor against a copy with the old
#  rows DELETED, who sees which queue, off / on / the switch, a tap (own line, once, the first stands), the weekly and monthly
#  start rule, the console against the owning modules as in S481, no patient in any list or reading. Then the REAL box is read
#  once, read-only: the console's reading as today and as the 15th, and each person's list as counts.
#  Only then: backups, place, restart clinic-finance and clinic-portal (about 15 seconds), the after-placing checks. Red after
#  placing -> the four files are put back, the three new files and the reading removed, both services restarted.
#  DRY=1 places nothing. NEEDS the build lock free (F-694).
# =============================================================================
set -u
KIT="S487_AAJ_KA_KAAM"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; POR="$ROOT/portal"
DB="${FINANCE_DB:-$FIN/finance.db}"
FINURL="${FINURL:-http://127.0.0.1:8106}"; PORURL="${PORURL:-http://127.0.0.1:8099}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
DUTYMAP="${DUTY_MAP_JSON:-/root/deploy/repo/claude_code_briefs/DUTY_MAP.json}"
ATTCORE="${ATTCORE:-$ROOT/att_core.py}"
FA_FROM=ef1382d2ce26d13d3c8388fdeb85e867; FA_TO=bff362c38ec61526ea0047fd136df826
PO_FROM=10a675e750086b4bffc6b1b1e41ea8de; PO_TO=63df9d49672e19e878245b30c0455bef
OP_FROM=be5558160aebd4f58a159d50740c11c5; OP_TO=4819eceb527e2a62b9d17984d90b71c5
OH_FROM=75b5d01735c555a57d5be6ad75fffc07; OH_TO=e6d35d88b87890911124b9778a43c5d2
AK_PY=d65e0bf4360f2ac2a6d4b3f6dd851dde; AK_HTML=03ccc58e6a55c445570046558f485feb; AK_JSON=7aa29bef179bcbb4526c72c26fb58f17
V_CONSOLE="S487 1.1"; V_LIST="S487 1.0"
SCR=""; PLACED=0; HAVE_LOCK=0; N_PY=0; N_HT=0; N_JS=0; B_FA=""; B_PO=""; B_OP=""; B_OH=""; T0=""; RED=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() {
  [ -n "$SCR" ] && rm -rf "$SCR"
  rm -f "$FIN/.finance_app.py.s487" "$FIN/.owner_console.py.s487" "$FIN/.owner_console.html.s487" "$FIN/.aaj_kaam.py.s487" "$FIN/.aaj_kaam.html.s487" "$FIN/.aaj_duties.json.s487" "$POR/.portal.py.s487"
}
reading_files() { echo "$FIN/console_reading.dat $FIN/console_reading.dat.lock $FIN/console_reading.dat.err"; }
back() {  # $1 = backup, $2 = live file, $3 = its old md5, $4 = its name
  \cp -p "$1" "$2"
  if [ "$(m5 "$2")" = "$3" ]; then say "   $4 back at $3"; else say "   !! $4 is $(m5 "$2"), NOT its old $3 - put $1 back by hand"; fi
}
gone() {  # $1 = was it new (1), $2 = the file
  [ "$1" = 1 ] || return 0
  rm -f "$2"; [ -e "$2" ] && say "   !! $2 is still there - remove it by hand" || say "   $(basename "$2") removed"
}
restore() {
  trap '' INT TERM HUP                                   # nothing interrupts the putting back
  say "!! RED after placing ($1) - restoring"
  PLACED=0
  back "$B_FA" "$FIN/finance_app.py" "$FA_FROM" finance_app.py
  back "$B_PO" "$POR/portal.py" "$PO_FROM" portal.py
  back "$B_OP" "$FIN/owner_console.py" "$OP_FROM" owner_console.py
  back "$B_OH" "$FIN/owner_console.html" "$OH_FROM" owner_console.html
  gone "$N_PY" "$FIN/aaj_kaam.py"; gone "$N_HT" "$FIN/aaj_kaam.html"; gone "$N_JS" "$FIN/aaj_duties.json"
  systemctl restart clinic-finance 2>/dev/null || true; systemctl restart clinic-portal 2>/dev/null || true; sleep 8
  rm -f $(reading_files)                                 # after the restart: the console as it was makes its own reading when asked
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
[ "$(m5 owner_console.py)" = "$OP_TO" ] && [ "$(m5 owner_console.html)" = "$OH_TO" ] && [ "$(m5 aaj_kaam.py)" = "$AK_PY" ] && [ "$(m5 aaj_kaam.html)" = "$AK_HTML" ] && [ "$(m5 aaj_duties.json)" = "$AK_JSON" ] \
  || { say "!! [1/7] the kit's five whole files are not the ones this installer names - nothing installed"; exit 1; }
"$SPY" -c "import flask, jinja2, sqlite3" 2>/dev/null || { say "!! [1/7] $SPY lacks flask or jinja2 (the walk and the builder need them) - nothing installed"; exit 1; }
mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
if [ "$HAVE_LOCK" != 1 ]; then
  say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
SCR="$(mktemp -d "/tmp/s487_scratch_XXXXXXXX")" || { say "!! [1/7] no scratch folder - nothing installed"; exit 1; }
chmod 700 "$SCR"
say "[1/7] kit gates green (SUMS, KIT_ID, the five whole files' own md5, flask and jinja2); the build lock is taken"

switch_words() {  # the lists' switch and the tap table, read through a read-only door; words only
  "$SPY" -B - "$DB" <<'PY' 2>/dev/null || echo "the switch could not be read"
import sqlite3, sys
con = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True, timeout=5)
try:
    r = con.execute("SELECT value FROM setting WHERE key='aaj.staff_on'").fetchone()
except sqlite3.Error:
    r = None
v = str((r[0] if r else "") or "")
t = con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='duty_tick'").fetchone()[0]
n = con.execute("SELECT COUNT(*) FROM duty_tick").fetchone()[0] if t else 0
print(("the lists are ON for staff since %s (turned on by %s)" % (v.split("|")[0].replace("T", " ")[:16], v.split("|")[1]) if "|" in v else "the lists are OFF for staff")
      + (" · %d tap(s) recorded" % n if t else " · no tap table yet (it is made on the first tap)"))
PY
}
post_checks() {
  # every check made after placing; RED carries the first reason. Runs in this shell (never in a subshell), so the caller decides.
  RED=""
  for s in clinic-finance clinic-portal; do systemctl is-active --quiet "$s" || { RED="$s not active"; return 1; }; done
  c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || { RED="finance healthz $c1"; return 1; }
  p1=$(health "$PORURL/portal/health"); [ "$p1" = 200 ] || { RED="portal /portal/health $p1"; return 1; }
  p2=$(health "$PORURL/portal/login"); case "$p2" in 200|302) ;; *) RED="portal /portal/login $p2"; return 1;; esac
  for u in /finance/console /finance/console/api/state /finance/console/api/tile /finance/aaj /finance/aaj/api/list /finance/aaj/api/line /finance/aaj/api/switch /finance/approvals; do
    c=$(health "$FINURL$u"); case "$c" in 302|401) ;; *) RED="$u answered $c without a login (it must be behind the login gate)"; return 1;; esac
  done
  for u in /finance/aaj/api/tick /finance/aaj/api/switch; do
    c=$(health -X POST --data-binary '{}' -H 'Content-Type: application/json' "$FINURL$u"); case "$c" in 302|401) ;; *) RED="a POST to $u answered $c without a login"; return 1;; esac
  done
  D1="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
  echo "$D1" | grep -q '"NOT_YOU"' || { RED="the heartbeat door no longer refuses an unsigned heartbeat: $(echo "$D1" | cut -c1-160)"; return 1; }
  if [ -n "$T0" ]; then
    if journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted"; then RED="a part of the finance app did NOT mount"; return 1; fi
    for s in clinic-finance clinic-portal; do
      JR="$(journalctl -u "$s" --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
      [ "${JR:-0}" = 0 ] || { RED="$s journal: $JR error line(s)"; return 1; }
    done
  fi
  ( cd "$FIN" && "$SPY" -B -c "import owner_console, aaj_kaam; assert owner_console.VERSION == '$V_CONSOLE' and aaj_kaam.VERSION == '$V_LIST' and callable(aaj_kaam.init)" ) 2>/dev/null || { RED="the placed owner_console.py / aaj_kaam.py do not load under $SPY"; return 1; }
  # the first real reading, through the placed files, exactly as the service's builder runs it (same user, same files)
  ( cd "$FIN" && FINANCE_DB="$DB" DUTY_MAP_JSON="$DUTYMAP" timeout 150 "$SPY" -B "$FIN/owner_console.py" --build --db "$DB" --out "$FIN/console_reading.dat" > "$SCR/first_reading.log" 2>&1 ) || { RED="the placed builder did not make a reading: $(tail -1 "$SCR/first_reading.log" | cut -c1-200)"; return 1; }
  MOUT="$( cd /tmp && TMPDIR="$SCR" DUTY_MAP_JSON="$DUTYMAP" timeout 120 "$SPY" -B "$KDIR/reading_s487.py" mounted "$FIN" "$DB" 2>&1 | tail -1 )"
  echo "$MOUT" | grep -q '^MOUNT OK' || { RED="the placed app does not carry the list: $(echo "$MOUT" | cut -c1-250)"; return 1; }
  ROUT="$("$SPY" -B "$KDIR/reading_s487.py" show "$FIN/console_reading.dat" 2>&1)"
  echo "$ROUT" | grep -v '^READING ' | cut -c1-330
  echo "$ROUT" | tail -1 | grep -q '^READING OK' || { RED="the first reading is not sound: $(echo "$ROUT" | tail -1 | cut -c1-250)"; return 1; }
  [ "$(stat -c '%a' "$FIN/console_reading.dat" 2>/dev/null)" = 600 ] || { RED="the reading file is not readable by its owner only"; return 1; }
  LOUT="$( cd /tmp && DUTY_MAP_JSON="$DUTYMAP" timeout 60 "$SPY" -B "$KDIR/reading_s487.py" lists "$FIN" "$DB" 2>&1 )"
  echo "$LOUT" | tail -1 | grep -q '^LISTS OK' || { RED="the placed list engine did not read the lists: $(echo "$LOUT" | tail -1 | cut -c1-250)"; return 1; }
  say "   $(switch_words)"
  return 0
}
POST_OK="both services active · finance healthz 200 · portal health and login as before · the console's doors and the list's five doors behind the login gate · the heartbeat door as before · the placed app, loaded as the builder loads it, has the list's five doors among its routes and every part mounted · a reading made by the placed builder from the list engine · the placed engine reads every list"
POST_NEW="every part mounted and both journals clean since the restart"

H_FA="$(m5 "$FIN/finance_app.py")"; H_PO="$(m5 "$POR/portal.py")"; H_OP="$(m5 "$FIN/owner_console.py")"; H_OH="$(m5 "$FIN/owner_console.html")"
H_PY="$(m5 "$FIN/aaj_kaam.py")"; H_HT="$(m5 "$FIN/aaj_kaam.html")"; H_JS="$(m5 "$FIN/aaj_duties.json")"
if [ "$H_FA" = "$FA_TO" ] && [ "$H_PO" = "$PO_TO" ] && [ "$H_OP" = "$OP_TO" ] && [ "$H_OH" = "$OH_TO" ] && [ "$H_PY" = "$AK_PY" ] && [ "$H_HT" = "$AK_HTML" ] && [ "$H_JS" = "$AK_JSON" ]; then
  say "-- ALREADY INSTALLED: the seven files at the kit's pins. The after-placing checks, again (the journals are read only at an install):"
  post_checks || { say "!! installed, but a check is RED: $RED"; say "   No file was changed by this run (the console's reading was made again). Tell the assistant; the undo line is in the kit's README."; clean; exit 1; }
  say "   $POST_OK"
  clean; exit 0
fi
if [ "$H_FA" = "$FA_TO" ] || [ "$H_PO" = "$PO_TO" ] || [ "$H_OP" = "$OP_TO" ] || [ "$H_OH" = "$OH_TO" ]; then
  say "!! [2/7] one of the four changed files is already at the kit's pin and the rest is not - a half state. Nothing installed; tell the assistant."
  say "   finance_app.py $H_FA · portal.py $H_PO · owner_console.py $H_OP · owner_console.html $H_OH · aaj_kaam.py ${H_PY:-absent} · aaj_kaam.html ${H_HT:-absent} · aaj_duties.json ${H_JS:-absent}"; clean; exit 1
fi
drift() { say "!! [2/7] $1 is $2, not $3 - another kit changed it after this one was built. Nothing installed; tell the assistant, the kit is rebuilt on the new file."; clean; exit 1; }
[ "$H_FA" = "$FA_FROM" ] || drift "$FIN/finance_app.py" "$H_FA" "$FA_FROM"
[ "$H_PO" = "$PO_FROM" ] || drift "$POR/portal.py" "$H_PO" "$PO_FROM"
[ "$H_OP" = "$OP_FROM" ] || drift "$FIN/owner_console.py" "${H_OP:-absent}" "$OP_FROM"
[ "$H_OH" = "$OH_FROM" ] || drift "$FIN/owner_console.html" "${H_OH:-absent}" "$OH_FROM"
foreign() { say "!! [2/7] a different $1 ($2) is already there - nothing installed; tell the assistant."; clean; exit 1; }
if [ -e "$FIN/aaj_kaam.py" ]; then [ "$H_PY" = "$AK_PY" ] || foreign "$FIN/aaj_kaam.py" "$H_PY"; else N_PY=1; fi
if [ -e "$FIN/aaj_kaam.html" ]; then [ "$H_HT" = "$AK_HTML" ] || foreign "$FIN/aaj_kaam.html" "$H_HT"; else N_HT=1; fi
if [ -e "$FIN/aaj_duties.json" ]; then [ "$H_JS" = "$AK_JSON" ] || foreign "$FIN/aaj_duties.json" "$H_JS"; else N_JS=1; fi
[ -f "$DB" ] || { say "!! [2/7] $DB is not there - nothing installed"; clean; exit 1; }
[ -f "$ATTCORE" ] || { say "!! [2/7] $ATTCORE (the attendance engine) is not there - nothing installed; tell the assistant."; clean; exit 1; }
[ -f "$DUTYMAP" ] || { say "!! [2/7] $DUTYMAP (the duty map) is not there - nothing installed; tell the assistant."; clean; exit 1; }
N_GR="$(m5 "$POR/tile_grants.json")"; N_CR="$(crontab -l 2>/dev/null | md5sum | awk '{print $1}')"
say "[2/7] the four files to change are at the pins this kit was built on; the three new files $([ "$N_PY$N_HT$N_JS" = 111 ] && echo "not there yet (they are new)" || echo "already the kit's where present"); the database, the attendance engine and the duty map in place"

\cp -p "$FIN/finance_app.py" "$SCR/finance_app.py" && \cp -p "$POR/portal.py" "$SCR/portal.py" || { say "!! [3/7] no scratch copy - nothing installed"; clean; exit 1; }
"$SPY" -B apply_s487.py "$SCR/finance_app.py" "$SCR/portal.py" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/7] the edits did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
[ "$(m5 "$SCR/finance_app.py")" = "$FA_TO" ] && [ "$(m5 "$SCR/portal.py")" = "$PO_TO" ] || { say "!! [3/7] the edited scratch copies are not their predicted bytes - nothing installed"; clean; exit 1; }
"$SPY" -B -c "
import json, sys
for p in sys.argv[2:]:
    compile(open(p, encoding='utf-8').read(), p, 'exec')
json.load(open(sys.argv[1], encoding='utf-8'))
" aaj_duties.json apply_s487.py walk_s487.py reading_s487.py owner_console.py aaj_kaam.py "$SCR/finance_app.py" "$SCR/portal.py" 2>"$SCR/compile.err" || { say "!! [3/7] compile failed: $(tail -1 "$SCR/compile.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
say "[3/7] the six edits apply to scratch copies and give the predicted bytes; everything compiles"

WOUT="$( cd /tmp && TMPDIR="$SCR" timeout 900 "$SPY" -B "$KDIR/walk_s487.py" --kit "$KDIR" --finance "$FIN" --portal "$POR/portal.py" --db "$DB" --attcore "$ATTCORE" --dutymap "$DUTYMAP" --full-app ${WALK_EXTRA:-} 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^  note|^WALK_S487' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S487 GREEN" || { say "!! [4/7] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
unchanged() { [ "$(m5 "$FIN/finance_app.py")" = "$FA_FROM" ] && [ "$(m5 "$POR/portal.py")" = "$PO_FROM" ] && [ "$(m5 "$FIN/owner_console.py")" = "$OP_FROM" ] && [ "$(m5 "$FIN/owner_console.html")" = "$OH_FROM" ]; }
unchanged || { say "!! [4/7] a file changed during the walk - nothing installed"; clean; exit 1; }
say "[4/7] walk green on copies of this box (its own code, its own database, made-up rows, the whole edited finance app). Now THE REAL BOX, read-only:"
real_reading() {  # $1 = words for the line, $2 = a PACKS_TODAY to read as (or nothing)
  ROUT="$( cd /tmp && env TMPDIR="$SCR" FINANCE_DB="$DB" DUTY_MAP_JSON="$DUTYMAP" ${2:+PACKS_TODAY=$2} timeout 200 "$SPY" -B "$KDIR/reading_s487.py" build "$KDIR" "$FIN" "$DB" "$SCR/real_reading.dat" 2>&1 )"
  echo "$ROUT" | grep '^   ' | cut -c1-330
  echo "$ROUT" | tail -1 | grep -q '^READING OK' || { say "!! [4/7] the reading of the real box ($1) is RED: $(echo "$ROUT" | tail -1 | cut -c1-300)"; say "   Nothing installed. Tell the assistant with this output."; echo "$ROUT" | tail -12 | cut -c1-300; clean; exit 1; }
}
real_reading "as today" ""
say "      and once more as the 15th of the month would read:"
real_reading "as the 15th" "$(date '+%Y-%m-15')"
LOUT="$( cd /tmp && DUTY_MAP_JSON="$DUTYMAP" timeout 60 "$SPY" -B "$KDIR/reading_s487.py" lists "$KDIR" "$DB" 2>&1 )"
echo "$LOUT" | grep '^   ' | cut -c1-330
echo "$LOUT" | tail -1 | grep -q '^LISTS OK' || { say "!! [4/7] the lists of the real box are RED: $(echo "$LOUT" | tail -1 | cut -c1-300)"; say "   Nothing installed. Tell the assistant with this output."; clean; exit 1; }
unchanged || { say "!! [4/7] a file changed during the reading - nothing installed"; clean; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the real box's readings green; NOTHING placed, nothing restarted"; clean; exit 0; fi

B_FA="$FIN/finance_app.py.bak_S487_$(echo "$FA_FROM" | cut -c1-8)"; B_PO="$POR/portal.py.bak_S487_$(echo "$PO_FROM" | cut -c1-8)"
B_OP="$FIN/owner_console.py.bak_S487_$(echo "$OP_FROM" | cut -c1-8)"; B_OH="$FIN/owner_console.html.bak_S487_$(echo "$OH_FROM" | cut -c1-8)"
\cp -p "$FIN/finance_app.py" "$B_FA" && \cp -p "$POR/portal.py" "$B_PO" && \cp -p "$FIN/owner_console.py" "$B_OP" && \cp -p "$FIN/owner_console.html" "$B_OH" \
  && [ "$(m5 "$B_FA")" = "$FA_FROM" ] && [ "$(m5 "$B_PO")" = "$PO_FROM" ] && [ "$(m5 "$B_OP")" = "$OP_FROM" ] && [ "$(m5 "$B_OH")" = "$OH_FROM" ] || { say "!! [5/7] a backup failed - nothing placed"; clean; exit 1; }
say "[5/7] backups: $B_FA $B_PO $B_OP $B_OH"
stage() {  # $1 = the live file whose owner and mode are kept, $2 = the new bytes, $3 = the staged name, $4 = its md5
  \cp -p "$1" "$3" && cat "$2" > "$3" && [ "$(m5 "$3")" = "$4" ]
}
stage "$FIN/finance_app.py" "$SCR/finance_app.py" "$FIN/.finance_app.py.s487" "$FA_TO" && stage "$POR/portal.py" "$SCR/portal.py" "$POR/.portal.py.s487" "$PO_TO" \
  && stage "$FIN/owner_console.py" "$KDIR/owner_console.py" "$FIN/.owner_console.py.s487" "$OP_TO" && stage "$FIN/owner_console.html" "$KDIR/owner_console.html" "$FIN/.owner_console.html.s487" "$OH_TO" \
  && stage "$FIN/owner_console.py" "$KDIR/aaj_kaam.py" "$FIN/.aaj_kaam.py.s487" "$AK_PY" && stage "$FIN/owner_console.html" "$KDIR/aaj_kaam.html" "$FIN/.aaj_kaam.html.s487" "$AK_HTML" \
  && stage "$FIN/owner_console.html" "$KDIR/aaj_duties.json" "$FIN/.aaj_duties.json.s487" "$AK_JSON" \
  || { say "!! [6/7] could not stage the files - nothing placed"; clean; exit 1; }
PLACED=1
mv -f "$FIN/.aaj_duties.json.s487" "$FIN/aaj_duties.json" || restore "placing aaj_duties.json"
mv -f "$FIN/.aaj_kaam.html.s487" "$FIN/aaj_kaam.html" || restore "placing aaj_kaam.html"
mv -f "$FIN/.aaj_kaam.py.s487" "$FIN/aaj_kaam.py" || restore "placing aaj_kaam.py"
mv -f "$FIN/.owner_console.html.s487" "$FIN/owner_console.html" || restore "placing owner_console.html"
mv -f "$FIN/.owner_console.py.s487" "$FIN/owner_console.py" || restore "placing owner_console.py"
mv -f "$FIN/.finance_app.py.s487" "$FIN/finance_app.py" || restore "placing finance_app.py"
mv -f "$POR/.portal.py.s487" "$POR/portal.py" || restore "placing portal.py"
[ "$(m5 "$FIN/finance_app.py")" = "$FA_TO" ] && [ "$(m5 "$POR/portal.py")" = "$PO_TO" ] && [ "$(m5 "$FIN/owner_console.py")" = "$OP_TO" ] && [ "$(m5 "$FIN/owner_console.html")" = "$OH_TO" ] \
  && [ "$(m5 "$FIN/aaj_kaam.py")" = "$AK_PY" ] && [ "$(m5 "$FIN/aaj_kaam.html")" = "$AK_HTML" ] && [ "$(m5 "$FIN/aaj_duties.json")" = "$AK_JSON" ] || restore "md5 read-back"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
systemctl restart clinic-portal || restore "restart clinic-portal"
for _w in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do                      # up to 45 s for both to answer; the checks below decide
  sleep 3
  [ "$(health "$FINURL/finance/healthz")" = 200 ] && [ "$(health "$PORURL/portal/health")" = 200 ] && break
done
sleep 3
post_checks || restore "$RED"
[ "$(m5 "$POR/tile_grants.json")" = "$N_GR" ] && [ "$(crontab -l 2>/dev/null | md5sum | awk '{print $1}')" = "$N_CR" ] || restore "tile_grants.json or the crontab moved during the install"
PLACED=0
say "[6/7] placed, md5 read back = the kit's pins · $POST_OK · $POST_NEW"
say "[7/7] nothing else moved (tile_grants.json, the crontab; no table, no setting written). The staff see nothing new until the owner's tap:"
say "      open the console -> Today's work -> 'List' beside a name opens that person's list as they will see it; 'Turn on' is on the Staff lists line."
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/finance_app.py" "$POR/portal.py" "$FIN/owner_console.py" "$FIN/owner_console.html" "$FIN/aaj_kaam.py" "$FIN/aaj_kaam.html" "$FIN/aaj_duties.json"
exit 0
