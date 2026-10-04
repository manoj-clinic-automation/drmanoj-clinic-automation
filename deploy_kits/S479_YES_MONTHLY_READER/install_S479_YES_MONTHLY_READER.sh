#!/bin/bash
# =============================================================================
# install_S479_YES_MONTHLY_READER.sh -- session 294, 04-Oct-2026 -- F-725
#  WHAT IT IS FOR. Yes Bank mails every account its month as a locked PDF in a layout neither Yes Bank reader knows ('YOUR
#  ACCOUNT STATEMENT FROM .. TO ..'). The shelf opens it with the owner's password; the identifier then took its bank from a
#  narration and gave it no period, and the net-banking reader refused it. Three such statements sit opened and refused on the
#  shelf (Sanjeevni Medicos, September; the HUF, August and September), so September's shelf reads 11 of 15 and the pharmacy's
#  bank cell is empty.
#  PLACES  /root/finance/yes_monthly.py        NEW        a4270bb3   the reader of that layout, with the proofs of S360 / S433.
#  EDITS, by apply_s479.py (exact anchors on the real bytes; every anchor exactly once; all three verified before any is written):
#          /root/finance/packs.py              1bc18b26 -> 9f897eeb   the identifier names the layout; the reader is chosen by
#                    layout; the shelf row says what was written and what another file held; the accountants' attachment, the
#                    owner's preview and Amir's pack take the UNLOCKED copy of a statement the shelf opened.
#          /root/finance/finance_yesbank.py    3509f728 -> 01b70e2b   ONE LINE ONCE toward the other two layouts: a row the monthly
#          /root/finance/yes_branch.py         fec5c520 -> e06ff505   statement or the branch's print (or, for the branch reader,
#                    any other layout) already put on the table -- date + withdrawal + deposit + cash flag, counted -- is not written again.
#                    Their parsing, their proofs and the cash check are not touched.
#  NOT TOUCHED: stmt_shelf.py, the tables' shape, the cells' rules, the password card, every page.
#  Walked first, on this box, hermetically (F-709: made-up statements, an empty database, nothing live opened). THEN THE REAL
#  SHELF, BEFORE ANYTHING IS PLACED (shelf_dry_s479.py; it writes nothing -- the database is copied into memory): every row that
#  carries the refusal is opened from the copy the shelf reads; one that is the monthly layout and that the new reader cannot
#  prove is a RED and nothing is installed; the ones it proves go through the shelf's own pass on the memory copy and the kit
#  says where each lands and how many lines are new. Only then: backups, place, restart clinic-finance (about 8 seconds), the
#  after-placing checks, and the same rows given back to the shelf for real (one shelf run, as the 05:40 cron runs it).
#  Red after placing -> the three files are put back, yes_monthly.py removed, the service restarted. Run again on an installed
#  box it repeats the after-placing checks and reads any refused monthly statement still waiting. DRY=1 places nothing.
#  NEEDS the build lock free (F-694).
# =============================================================================
set -u
KIT="S479_YES_MONTHLY_READER"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
DB="${FINANCE_DB:-$FIN/finance.db}"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FILES="packs.py finance_yesbank.py yes_branch.py"
declare -A FROM=( [packs.py]=1bc18b263af7e652a8d093e29e018ea8 [finance_yesbank.py]=3509f7285fbae0d40fcb2daadb3a5b9f [yes_branch.py]=fec5c520bfc4f563439d8f2dd6b24105 )
declare -A TO=( [packs.py]=9f897eeb70bc65d1414985058e378310 [finance_yesbank.py]=01b70e2b67bb70fde55e9dbfdf16b0ba [yes_branch.py]=e06ff5055c2927545701cd6cf8985ed4 )
TO_READER=a4270bb3aa12f7c6235167a8cd86a0b3
READER_VERSION="S479 1.2"
SCR=""; NEW_READER=0; PLACED=0; HAVE_LOCK=0
declare -A BAK
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() {
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  [ -n "$SCR" ] && rm -rf "$SCR"
  for f in $FILES yes_monthly.py; do rm -f "$FIN/.$f.s479"; done
}
restore() {
  trap '' INT TERM HUP                                   # nothing interrupts the putting back
  say "!! RED after placing ($1) - restoring"
  PLACED=0
  for f in $FILES; do \cp -p "${BAK[$f]}" "$FIN/$f"; done
  [ "$NEW_READER" = 1 ] && rm -f "$FIN/yes_monthly.py"
  systemctl restart clinic-finance 2>/dev/null || true; sleep 7
  for f in $FILES; do
    if [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ]; then say "   $f back at ${FROM[$f]}"; else say "   !! $f is $(m5 "$FIN/$f"), NOT its old ${FROM[$f]} - put ${BAK[$f]} back by hand"; fi
  done
  [ "$NEW_READER" = 1 ] && { [ -e "$FIN/yes_monthly.py" ] && say "   !! yes_monthly.py is still there - remove it by hand" || say "   yes_monthly.py removed"; }
  say "   finance healthz $(health "$FINURL/finance/healthz")"
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
[ "$(m5 yes_monthly.py)" = "$TO_READER" ] || { say "!! [1/7] the kit's yes_monthly.py is not the reader this installer names - nothing installed"; exit 1; }
"$SPY" -c "import flask, werkzeug" 2>/dev/null || { say "!! [1/7] $SPY lacks flask (the walk mounts the packs page) - nothing installed"; exit 1; }
command -v pdftotext >/dev/null 2>&1 || { say "!! [1/7] pdftotext is not on this box (every statement reader needs it) - nothing installed"; exit 1; }
[ -x "$VPY" ] || { say "!! [1/7] $VPY is not there (the shelf's own python) - nothing installed"; exit 1; }
mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
if [ "$HAVE_LOCK" != 1 ]; then
  say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
SCR="$(mktemp -d "/tmp/s479_scratch_XXXXXXXX")" || { say "!! [1/7] no scratch folder - nothing installed"; exit 1; }
say "[1/7] kit gates green (SUMS, KIT_ID, the reader's own md5, flask, pdftotext, the shelf's python); the build lock is taken"

road_now() {
  ( cd "$FIN" && "$SPY" -B - "$DB" <<'PY'
import sqlite3, sys
import packs
con = sqlite3.connect(sys.argv[1], timeout=60); con.row_factory = sqlite3.Row
r = packs.statement_road(con)
print("   the road says: %s | %s" % (r["state"], r["text"]))
PY
  ) 2>&1 | tail -1 | cut -c1-300
}

T0=""
post_checks() {
  # every check made after placing; RED carries the first reason. Runs in this shell (never in a subshell), so the caller decides.
  RED=""
  systemctl is-active --quiet clinic-finance || { RED="clinic-finance not active"; return 1; }
  c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || { RED="finance healthz $c1"; return 1; }
  c2=$(health "$FINURL/finance/packs"); case "$c2" in 302|401) ;; *) RED="/finance/packs answered $c2 without a login"; return 1;; esac
  c3=$(health "$FINURL/finance/packs/file/1"); case "$c3" in 302|401|403) ;; *) RED="the preview door answered $c3 without a login"; return 1;; esac
  D1="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
  echo "$D1" | grep -q '"NOT_YOU"' || { RED="the heartbeat door no longer refuses an unsigned heartbeat: $(echo "$D1" | cut -c1-160)"; return 1; }
  if [ -n "$T0" ]; then
    if journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted"; then RED="a module NOT mounted"; return 1; fi
    JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
    [ "${JR:-0}" = 0 ] || { RED="clinic-finance journal: $JR error line(s)"; return 1; }
  fi
  ( cd "$FIN" && "$SPY" -B -c "import packs, yes_monthly, yes_branch, finance_yesbank; assert yes_monthly.VERSION == '$READER_VERSION' and callable(packs._best_path)" ) 2>/dev/null || { RED="the placed files do not load together under $SPY"; return 1; }
  ( cd "$FIN" && "$SPY" -B finance_yesbank.py 2>&1 | tail -1 | grep -q '^SELFTEST GREEN$' ) || { RED="finance_yesbank.py's own selftest is not green as placed"; return 1; }
  R1="$(road_now)"
  echo "$R1" | grep -q "the road says: \(ok\|info\|warn\) | ." || { RED="packs.py no longer answers on the live database: $(echo "$R1" | cut -c1-200)"; return 1; }
  if echo "$R1" | grep -q "could not be read"; then RED="the statement road could not be read on the live database: $(echo "$R1" | cut -c1-200)"; return 1; fi
  return 0
}
POST_OK="clinic-finance active · healthz 200 · /finance/packs and the preview door behind the login gate · the heartbeat door as before · the four files load together · finance_yesbank's own selftest green"

IDS=""; DLAST=""
shelf_dry() {
  # $1 = the folder the four modules are loaded from. Sets IDS; returns 1 on a red. Writes nothing.
  DOUT="$( cd /tmp && timeout 300 "$SPY" -B "$KDIR/shelf_dry_s479.py" dry "$1" "$FIN" "$DB" 2>&1 )"
  echo "$DOUT" | grep -v '^DRY ' | cut -c1-320
  DLAST="$(echo "$DOUT" | tail -1)"
  case "$DLAST" in
    "DRY OK ids="*) IDS="${DLAST#DRY OK ids=}"; echo "$IDS" | grep -q '^[0-9][0-9,]*$' || { IDS=""; return 1; }; return 0;;
    "DRY NONE") IDS=""; return 0;;
    *) IDS=""; return 1;;
  esac
}
give_back() {
  # the rows the dry run proved, given back to the shelf for real (read_status cleared; the slot and the file stay)
  N="$("$SPY" -B - "$DB" "$IDS" <<'PY'
import sqlite3, sys
ids = [int(x) for x in sys.argv[2].split(",")]
con = sqlite3.connect(sys.argv[1], timeout=60)
cur = con.execute("UPDATE stmt_file SET read_status=NULL, matched_status=NULL WHERE id IN (%s) AND read_status LIKE 'refused: this PDF does not print%%'" % ",".join("?" * len(ids)), ids)
con.commit(); print(cur.rowcount)
PY
)"
  WANT="$(echo "$IDS" | tr ',' '\n' | grep -c .)"
  say "   $N shelf row(s) given back to the reader$([ "$N" = "$WANT" ] || echo " -- NOT the $WANT the dry run proved; the report below says how each stands")"
}
shelf_run() {
  # $1 = the ids to report. One shelf run (fetch + identify), as the 05:40 cron runs it; then the rows as they stand, and the month's cells.
  ( cd "$FIN" && FINANCE_DB="$DB" timeout 900 "$VPY" -B "$FIN/stmt_shelf.py" run >> "$FIN/stmt_shelf.log" 2>&1 ); RC=$?
  say "   stmt_shelf.py run: rc $RC"
  ROUT="$( cd /tmp && timeout 300 "$SPY" -B "$KDIR/shelf_dry_s479.py" report "$FIN" "$FIN" "$DB" "$1" 2>&1 )"
  echo "$ROUT" | grep -v '^REPORT ' | cut -c1-320
  echo "$ROUT" | tail -1 | grep -q '^REPORT OK$'
}
NOT_READ_1="!! after the shelf run a row above is not read. One that says 'waiting' stays given back: the 05:40 run reads it, and pasting"
NOT_READ_2="   the same line again runs the shelf once more. One that says 'refused' the reader refused. Tell the assistant with this output."

ALL=1; ANY=0; for f in $FILES; do if [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ]; then ANY=1; else ALL=0; fi; done
RD="$(m5 "$FIN/yes_monthly.py")"
if [ "$ALL" = 1 ] && [ "$RD" = "$TO_READER" ]; then
  say "-- ALREADY INSTALLED: the three files and yes_monthly.py at the kit's pins. The after-placing checks, again:"
  post_checks || { say "!! installed, but a check is RED: $RED"; say "   Nothing was changed by this run. Tell the assistant; the undo line is in the kit's README."; clean; exit 1; }
  say "   $POST_OK"
  shelf_dry "$FIN" || { say "!! the shelf's dry run is RED: $(echo "$DLAST" | cut -c1-300)"; say "   Nothing was changed by this run. Tell the assistant."; clean; exit 1; }
  WLAST="$( cd /tmp && timeout 300 "$SPY" -B "$KDIR/shelf_dry_s479.py" waiting "$FIN" "$FIN" "$DB" 2>&1 | tail -1 )"
  case "$WLAST" in
    "WAITING NONE") WIDS="";;
    "WAITING "[0-9]*) WIDS="${WLAST#WAITING }"; echo "$WIDS" | grep -q '^[0-9][0-9,]*$' || { say "!! the waiting rows could not be read: $(echo "$WLAST" | cut -c1-200). Nothing was changed by this run. Tell the assistant."; clean; exit 1; };;
    *) say "!! the waiting rows could not be read: $(echo "$WLAST" | cut -c1-200). Nothing was changed by this run. Tell the assistant."; clean; exit 1;;
  esac
  if [ -z "$IDS" ] && [ -z "$WIDS" ]; then say "   no refused monthly statement waits on the shelf -- nothing to read again"; clean; exit 0; fi
  ALLIDS="$IDS${IDS:+${WIDS:+,}}$WIDS"
  if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: file $ALLIDS would be read; nothing changed"; clean; exit 0; fi
  [ -z "$IDS" ] || { say "   file $IDS is refused and proves -- given back to the shelf now:"; give_back; }
  [ -z "$WIDS" ] || say "   file $WIDS was given back earlier and still waits for the shelf"
  shelf_run "$ALLIDS" || { say "$NOT_READ_1"; say "$NOT_READ_2"; clean; exit 1; }
  say "all green -- $KIT: the waiting statements are read."
  clean; exit 0
fi
[ "$ANY" = 0 ] || { say "!! [2/7] some of the kit's files are already at its pins and some are not - a half state. Nothing installed; tell the assistant."; for f in $FILES yes_monthly.py; do say "   $f $(m5 "$FIN/$f")"; done; clean; exit 1; }
for f in $FILES; do
  H="$(m5 "$FIN/$f")"
  [ "$H" = "${FROM[$f]}" ] || { say "!! [2/7] $FIN/$f is $H, not ${FROM[$f]} - another kit changed it after this one was built. Nothing installed; tell the assistant, the kit is rebuilt on the new file."; clean; exit 1; }
done
if [ -e "$FIN/yes_monthly.py" ]; then
  [ "$RD" = "$TO_READER" ] || { say "!! [2/7] a different $FIN/yes_monthly.py ($RD) is already there - nothing installed; tell the assistant."; clean; exit 1; }
else
  NEW_READER=1
fi
[ -f "$FIN/stmt_shelf.py" ] || { say "!! [2/7] $FIN/stmt_shelf.py is not there - nothing installed"; clean; exit 1; }
[ -f "$DB" ] || { say "!! [2/7] $DB is not there - nothing installed"; clean; exit 1; }
say "[2/7] the three files at the pins this kit was built on; yes_monthly.py $([ "$NEW_READER" = 1 ] && echo "not there yet (it is new)" || echo "already the kit's"); the shelf and the database in place"

for f in $FILES; do \cp -p "$FIN/$f" "$SCR/$f" || { say "!! [3/7] no scratch copy - nothing installed"; clean; exit 1; }; done
\cp -p yes_monthly.py "$SCR/yes_monthly.py" || { say "!! [3/7] no scratch copy - nothing installed"; clean; exit 1; }
"$SPY" -B apply_s479.py "$SCR/packs.py" "$SCR/finance_yesbank.py" "$SCR/yes_branch.py" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/7] the edits did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
for f in $FILES; do [ "$(m5 "$SCR/$f")" = "${TO[$f]}" ] || { say "!! [3/7] the edited scratch copy of $f is not its predicted bytes - nothing installed"; clean; exit 1; }; done
"$SPY" -m py_compile apply_s479.py walk_s479.py shelf_dry_s479.py "$SCR/packs.py" "$SCR/finance_yesbank.py" "$SCR/yes_branch.py" "$SCR/yes_monthly.py" 2>/dev/null || { say "!! [3/7] compile failed - nothing installed"; clean; exit 1; }
( cd "$SCR" && "$SPY" -B finance_yesbank.py 2>&1 | tail -1 | grep -q '^SELFTEST GREEN$' ) || { say "!! [3/7] finance_yesbank.py's own selftest is not green on the edited copy - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the twelve edits apply to scratch copies and give the predicted bytes; everything compiles; finance_yesbank's own selftest green on its edited copy"

WOUT="$( cd /tmp && timeout 600 "$SPY" -B "$KDIR/walk_s479.py" --apply "$KDIR/apply_s479.py" --reader "$KDIR/yes_monthly.py" --finance "$FIN" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^  note|^WALK_S479' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S479 GREEN" || { say "!! [4/7] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
for f in $FILES; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [4/7] $f changed during the walk - nothing installed"; clean; exit 1; }; done
say "[4/7] walk green on this box (made-up statements). Now the real shelf, on a copy in memory -- nothing is written:"
shelf_dry "$SCR" || { say "!! [4/7] the real shelf's dry run is RED: $(echo "$DLAST" | cut -c1-300)"; say "   Nothing installed. Tell the assistant with this output."; clean; exit 1; }
if [ -n "$IDS" ]; then say "      every refused monthly statement proves and is read on the copy (file $IDS)"; else say "      no refused monthly statement is on the shelf today -- the reader is placed for the next one"; fi
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the real shelf's dry run green; NOTHING placed, nothing restarted"; clean; exit 0; fi

for f in $FILES; do
  B="$FIN/$f.bak_S479_$(echo "${FROM[$f]}" | cut -c1-8)"
  \cp -p "$FIN/$f" "$B" && [ "$(m5 "$B")" = "${FROM[$f]}" ] || { say "!! [5/7] the backup of $f failed - nothing placed"; clean; exit 1; }
  BAK[$f]="$B"
done
say "[5/7] backups: $(for f in $FILES; do echo -n "${BAK[$f]} "; done)"
for f in $FILES yes_monthly.py; do
  T="${TO[$f]:-$TO_READER}"
  \cp -p "$FIN/packs.py" "$FIN/.$f.s479" && cat "$SCR/$f" > "$FIN/.$f.s479" && [ "$(m5 "$FIN/.$f.s479")" = "$T" ] || { say "!! [6/7] could not stage $f - nothing placed"; clean; exit 1; }
done
PLACED=1
mv -f "$FIN/.yes_monthly.py.s479" "$FIN/yes_monthly.py" || restore "placing yes_monthly.py"
for f in $FILES; do mv -f "$FIN/.$f.s479" "$FIN/$f" || restore "placing $f"; done
for f in $FILES; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore "md5 read-back of $f"; done
[ "$(m5 "$FIN/yes_monthly.py")" = "$TO_READER" ] || restore "md5 read-back of yes_monthly.py"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
sleep 8
post_checks || restore "$RED"
PLACED=0
say "[6/7] placed, md5 read back = the kit's pins · $POST_OK · every part mounted · journal clean"
if [ -z "$IDS" ]; then
  say "[7/7] nothing to read again today."
  clean
  say "all green -- $KIT: DONE."
  for f in $FILES yes_monthly.py; do md5sum "$FIN/$f"; done
  exit 0
fi
say "[7/7] the same rows, given back to the shelf for real:"
give_back
if shelf_run "$IDS"; then
  clean
  say "all green -- $KIT: DONE."
  for f in $FILES yes_monthly.py; do md5sum "$FIN/$f"; done
  exit 0
fi
clean
say "!! INSTALLED, and the code is sound (every check at [6/7] was green) -- but that is not what the dry run on the copy said."
say "   Nothing is put back: a row the shelf has read is already on the table."
say "$NOT_READ_1"; say "$NOT_READ_2"
for f in $FILES yes_monthly.py; do md5sum "$FIN/$f"; done
exit 1
