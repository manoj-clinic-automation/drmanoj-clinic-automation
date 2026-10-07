#!/bin/bash
# =============================================================================
# install_S495_LIST_PAGE_FLOORS.sh -- session 298, 07-Oct-2026 -- the lists' floor, on the pages the lists open
#  THE OWNER, 06-Oct: the staff's lists start from 1 October, and staff must not see September "on the list or on the page
#  a line opens". S493 laid the floor under the lists; this lays the same floor on four pages of the parent's.
#  NEW:   /root/finance/aaj_floor.py     floor_for(con, require): the day, or None for the owner / while the lists are not
#                                         started / whenever it cannot be told. Reads two setting rows; writes nothing.
#  EDITED by apply_s495.py (exact anchors on the real bytes; each result is the kit's own md5):
#         /root/finance/clinic_register.py  eaaea278 -> the counter sheet's list of days            (2 places, 1 helper)
#         /root/finance/records.py          6492135c -> Check karein's open items                   (1 place,  1 helper)
#         /root/finance/slip_log.py         caef39f6 -> Report baaki's four lists                   (1 place,  1 helper)
#         /root/finance/petty_book.py       698c988e -> the physiotherapy tick card's 14 days       (1 place)
#  Each place is ONE guarded call: without the helper, or if it fails, the page is byte for byte what it is today.
#  NOT TOUCHED: any money figure, the doctors' own line and counts, any write path, a day or an item opened by its own
#  address, finance_app.py, the database. WHILE THE LISTS ARE NOT STARTED EVERY PAGE IS EXACTLY WHAT IT IS TODAY.
# Walked first, on this box (walk_s495.py): each page asked of the live file and of the edited file on one database and the
# two answers compared -- on a made-up clinic, and on a copy of finance.db with the lists marked started on the copy.
# Restarts clinic-finance only (about 10 seconds); red after placing -> all five files are put back as they were.
# DRY=1 places nothing. NEEDS the build lock free (F-694).
# =============================================================================
set -u
KIT="S495_LIST_PAGE_FLOORS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
DB="${FINANCE_DB:-$FIN/finance.db}"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
NAMES="clinic_register.py records.py slip_log.py petty_book.py"
FLOOR=1f53b8dad8be65e0c507efdd38464eb8
SCR=""; PLACED=0; HAVE_LOCK=0; HAD_FLOOR=0; T0=""; RED=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
PINS=""                                                 # the applier's own FROM -> TO lines, read once at the first gate
pin() { echo "$PINS" | awk -v f="$1" -v c="$2" '$1==f{print (c=="from")?$2:$4}'; }
clean() {
  [ -n "$SCR" ] && rm -rf "$SCR"
  for f in $NAMES aaj_floor.py; do rm -f "$FIN/.$f.s495"; done
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
}
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - restoring"
  PLACED=0
  for f in $NAMES; do
    b="$FIN/$f.bak_S495_$(pin "$f" from | cut -c1-8)"
    \cp -p "$b" "$FIN/$f"
    if [ "$(m5 "$FIN/$f")" = "$(pin "$f" from)" ]; then say "   $f back at its old bytes"; else say "   !! $f is NOT its old bytes - put $b back by hand"; fi
  done
  [ "$HAD_FLOOR" = 0 ] && rm -f "$FIN/aaj_floor.py" && say "   aaj_floor.py removed"
  systemctl restart clinic-finance 2>/dev/null || true; sleep 9
  say "   finance healthz $(health "$FINURL/finance/healthz")"
  clean; exit 1
}
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
on_signal() {
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
[ "$(m5 aaj_floor.py)" = "$FLOOR" ] || { say "!! [1/7] the kit's aaj_floor.py is not the one this installer names - nothing installed"; exit 1; }
"$SPY" -c "import flask, sqlite3" 2>/dev/null || { say "!! [1/7] $SPY lacks flask (the walk needs it) - nothing installed"; exit 1; }
PINS="$("$SPY" -B "$KDIR/apply_s495.py" --pins 2>/dev/null)"
[ "$(echo "$PINS" | grep -c ' -> [0-9a-f]\{32\}$')" = 4 ] || { say "!! [1/7] the applier does not name its four pins - nothing installed"; exit 1; }
mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
if [ "$HAVE_LOCK" != 1 ]; then
  say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
SCR="$(mktemp -d "/tmp/s495_scratch_XXXXXXXX")" || { say "!! [1/7] no scratch folder - nothing installed"; exit 1; }
chmod 700 "$SCR"
say "[1/7] kit gates green (SUMS, KIT_ID, aaj_floor.py's own md5, flask); the build lock is taken"

[ -f "$FIN/aaj_floor.py" ] && HAD_FLOOR=1
AT_TO=1; AT_FROM=1
for f in $NAMES; do
  h="$(m5 "$FIN/$f")"
  [ "$h" = "$(pin "$f" to)" ] || AT_TO=0
  [ "$h" = "$(pin "$f" from)" ] || AT_FROM=0
done
if [ "$AT_TO" = 1 ] && [ "$(m5 "$FIN/aaj_floor.py")" = "$FLOOR" ]; then say "-- ALREADY INSTALLED: the five files are at the kit's pins; clinic-finance $(systemctl is-active clinic-finance 2>/dev/null)"; clean; exit 0; fi
if [ "$AT_FROM" != 1 ]; then
  for f in $NAMES; do h="$(m5 "$FIN/$f")"; [ "$h" = "$(pin "$f" from)" ] || say "!! [2/7] $FIN/$f is $h, not $(pin "$f" from) - another kit changed it after this one was built."; done
  say "   Nothing installed; tell the assistant, the kit is rebuilt on the new file."; clean; exit 1
fi
if [ "$HAD_FLOOR" = 1 ] && [ "$(m5 "$FIN/aaj_floor.py")" != "$FLOOR" ]; then say "!! [2/7] $FIN/aaj_floor.py is already there and is not this kit's file - nothing installed; tell the assistant."; clean; exit 1; fi
# this kit is the second half of S493_LISTS_2: it is placed only on a box that has the first half
if ! { [ -f "$FIN/aaj_seed.py" ] && grep -q '^VERSION = "S493 2' "$FIN/aaj_kaam.py" 2>/dev/null; }; then
  say "!! [2/7] S493_LISTS_2 is not installed on this box (no aaj_seed.py, or aaj_kaam.py is not 2.x) - nothing installed. Run S493's installer first."; clean; exit 1
fi
say "[2/7] the four files at the pins this kit was built on; no other aaj_floor.py in the way; S493_LISTS_2 is on this box"

mkdir -p "$SCR/fin" || { say "!! [3/7] no scratch copy - nothing installed"; clean; exit 1; }
for f in $NAMES; do \cp -p "$FIN/$f" "$SCR/fin/$f" || { say "!! [3/7] no scratch copy of $f - nothing installed"; clean; exit 1; }; done
"$SPY" -B apply_s495.py "$SCR/fin" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/7] the edits did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-220) - nothing installed"; clean; exit 1; }
for f in $NAMES; do [ "$(m5 "$SCR/fin/$f")" = "$(pin "$f" to)" ] || { say "!! [3/7] the edited scratch copy of $f is not the kit's bytes - nothing installed"; clean; exit 1; }; done
"$SPY" -m py_compile aaj_floor.py apply_s495.py walk_s495.py "$SCR/fin/clinic_register.py" "$SCR/fin/records.py" "$SCR/fin/slip_log.py" "$SCR/fin/petty_book.py" 2>"$SCR/compile.err" \
  || { say "!! [3/7] compile failed: $(tail -1 "$SCR/compile.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the edits apply to scratch copies and give the kit's own bytes; everything compiles"

unchanged() { for f in $NAMES; do [ "$(m5 "$FIN/$f")" = "$(pin "$f" from)" ] || return 1; done; return 0; }
WOUT="$( cd /tmp && TMPDIR="$SCR" timeout 900 "$SPY" -B "$KDIR/walk_s495.py" --kit "$KDIR" --finance "$FIN" --code "$FIN" --code "$ROOT/marg_ingest" --db "$DB" ${WALK_EXTRA:-} 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^  note|^WALK_S495' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S495 GREEN" || { say "!! [4/7] walk red - nothing installed. Tell the assistant with this output."; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
unchanged || { say "!! [4/7] a file changed during the walk - nothing installed"; clean; exit 1; }
say "[4/7] walk green on this box: each page asked of the live file and of the edited file and compared -- on a made-up clinic and on a copy of the real database (staff: nothing before the floor; the owner, and everyone while the lists are not started: byte for byte today's page)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

for f in $NAMES; do
  b="$FIN/$f.bak_S495_$(pin "$f" from | cut -c1-8)"
  \cp -p "$FIN/$f" "$b" && [ "$(m5 "$b")" = "$(pin "$f" from)" ] || { say "!! [5/7] the backup of $f failed - nothing placed"; clean; exit 1; }
done
say "[5/7] backups made beside each file (.bak_S495_<its old md5>)"
for f in $NAMES; do
  \cp -p "$FIN/$f" "$FIN/.$f.s495" && cat "$SCR/fin/$f" > "$FIN/.$f.s495" && [ "$(m5 "$FIN/.$f.s495")" = "$(pin "$f" to)" ] || { say "!! [6/7] could not stage $f - nothing placed"; clean; exit 1; }
done
\cp -p "$FIN/petty_book.py" "$FIN/.aaj_floor.py.s495" && cat "$KDIR/aaj_floor.py" > "$FIN/.aaj_floor.py.s495" && [ "$(m5 "$FIN/.aaj_floor.py.s495")" = "$FLOOR" ] || { say "!! [6/7] could not stage aaj_floor.py - nothing placed"; clean; exit 1; }
PLACED=1
mv -f "$FIN/.aaj_floor.py.s495" "$FIN/aaj_floor.py" || restore "placing aaj_floor.py"
for f in $NAMES; do mv -f "$FIN/.$f.s495" "$FIN/$f" || restore "placing $f"; done
for f in $NAMES; do [ "$(m5 "$FIN/$f")" = "$(pin "$f" to)" ] || restore "md5 read-back of $f"; done
[ "$(m5 "$FIN/aaj_floor.py")" = "$FLOOR" ] || restore "md5 read-back of aaj_floor.py"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
for _w in 1 2 3 4 5 6 7 8 9 10 11 12; do sleep 3; [ "$(health "$FINURL/finance/healthz")" = 200 ] && break; done
sleep 3
post_checks() {
  RED=""
  systemctl is-active --quiet clinic-finance || { RED="clinic-finance not active"; return 1; }
  c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || { RED="finance healthz $c1"; return 1; }
  for u in /finance/clinic/register /finance/clinic/register/list /finance/checks /finance/slips/pending /finance/petty /finance/aaj /finance/console; do
    c=$(health "$FINURL$u"); case "$c" in 302|401) ;; *) RED="$u answered $c without a login (it must be behind the login gate)"; return 1;; esac
  done
  D1="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
  echo "$D1" | grep -q '"NOT_YOU"' || { RED="the heartbeat door no longer refuses an unsigned heartbeat: $(echo "$D1" | cut -c1-160)"; return 1; }
  if journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted"; then RED="a part of the finance app did NOT mount"; return 1; fi
  JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
  [ "${JR:-0}" = 0 ] || { RED="clinic-finance journal: $JR error line(s)"; return 1; }
  ( cd "$FIN" && "$SPY" -B -c "
import sqlite3, aaj_floor as f
con = sqlite3.connect('file:$DB?mode=ro', uri=True, timeout=5)
print('   on this box: the lists are %s; the floor for a staff login %s' % (('STARTED', 'is ' + f.day(con)) if f.started(con) else ('not started', 'will be ' + f.day(con) + ' from the day they are')))
assert f.VERSION == 'S495 1.0'
" ) || { RED="the placed aaj_floor.py does not load under $SPY"; return 1; }
  return 0
}
post_checks || restore "$RED"
PLACED=0
say "[6/7] placed, md5 read back = the kit's pins · clinic-finance active · healthz 200 · the four pages behind the login gate as before · the heartbeat door as before · every part mounted · journal clean"
say "[7/7] the four pages are today's pages until the lists are started; from then a staff login sees nothing on them from before the floor, and the owner sees everything"
clean
say "all green -- $KIT: DONE."
( cd "$FIN" && md5sum $NAMES aaj_floor.py )
exit 0
