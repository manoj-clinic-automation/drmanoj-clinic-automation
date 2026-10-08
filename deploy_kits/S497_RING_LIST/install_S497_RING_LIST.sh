#!/bin/bash
# =============================================================================
# install_S497_RING_LIST.sh -- session 302 (parent), 08-Oct-2026 -- the after-call list (tile 'Call ke baad'), D693
#  THE OWNER, 07-Oct: "what happens after they click the book appointment button is nowhere visible to them" ...
#  "tabular ... updated from the Docterz exports confirming that these patient turned up, and persist for the no shows
#  distinctly" ... "full mobile numbers, weekdays in english, leave scope for whatsaap" ... "it is final".
#  WHOLE-FILE REPLACEMENTS, each gated on the md5 of the file it replaces (the 08-Oct 01:35 bundle's bytes):
#     /root/portal/ring_outcome.py   495b0ada -> the list (/portal/ring/list: Nahi aaye . Aane baaki . Aa gaye), the one
#                                                optional day on the card after 'Appointment book ho gaya', the two
#                                                buttons, his switch and two settings; F-797 mended. The tap, the mirror
#                                                into the tracker, the sweeper and the counts are byte for byte as live.
#     /root/portal/portal.py         63df9d49 -> one tile, 'Call ke baad', in Clinic, right after Call Tracker; drawn for
#                                                staff only once the list is on.
#  EDITED BY SCRIPT (apply_s497.py, exact text, its own from/to md5):
#     /root/portal/tile_grants.json  f9441311 v32 -> v33: the tile by name to alisha, shivani, shavez, reception.
#  NOT TOUCHED: ring_common.py, ring_hook.py, portal_push.py, finance.db (opened read-only by the list, never written).
#  THE LIST IS INSTALLED OFF FOR STAFF: the doctor opens /portal/ring/list and turns it on there. From that day on it
#  follows appointments booked that day or later (he may move the date earlier on his box, back to 01-Oct-2026).
#  SECOND BUILD (08-Oct): the two reviews' findings B1 B2 S1-S7 M1-M4 are mended; the last lines of a green run print
#  the md5 read-backs, the day Docterz visits reach, the row counts, the switch state and what was restarted.
#  The ring store (ring_outcomes.db) gains eleven columns on `outcome` and two small tables the first time the new code
#  runs; nothing that is there is changed. It is backed up first (sqlite backup API).
# Walked first, on this box (walk_s497.py, under each python that has Flask): the kit's two programs on a made-up day,
# signed in as each login on the walk's own user store; the SAME walk on the live files must end RED (negative
# control); then a copy of the real ring store, counts only.
# Restarts ring-hook and clinic-portal ONLY (a few seconds each). Red after placing -> the three files are put back
# byte for byte, both services restarted, health confirmed, exit 1.
# DRY=1 places nothing.  NEEDS the build lock free (F-694).
# Every path and command can be given by the environment, so the whole run can be rehearsed against a made-up root:
#   PD  FINDB  PORURL  RINGURL  LOCK  TMPBASE  SPY_SVC  SPY_VENV  SYSTEMCTL  CURL  JOURNALCTL  WAIT
# =============================================================================
set -u
KIT="S497_RING_LIST"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PD="${PD:-/root/portal}"
FINDB="${FINDB:-/root/finance/finance.db}"
PORURL="${PORURL:-http://127.0.0.1:8099}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
TMPBASE="${TMPBASE:-/tmp}"
SPY_SVC="${SPY_SVC:-/usr/bin/python3}"
SPY_VENV="${SPY_VENV:-/root/wa/venv/bin/python3}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
CURL="${CURL:-curl}"
JOURNALCTL="${JOURNALCTL:-journalctl}"
WAIT="${WAIT:-2}"
RO_FROM=495b0ada681cda359a1a621a22f4efa5; RO_TO=7cb60aad2df80f87fdc4a674ebe7ee45
PO_FROM=63df9d49672e19e878245b30c0455bef; PO_TO=f8b059f61fa8b885f024f4f4ce73e4f2
TG_FROM=f9441311cd413bc4c12e9d4e23feb791; TG_TO=64f8b04937e8841c405cb9070b604aad
RC_PIN=4344b59277d94b2d11d8d7cc23328677
B_RO="$PD/ring_outcome.py.bak_S497_$(echo "$RO_FROM" | cut -c1-8)"
B_PO="$PD/portal.py.bak_S497_$(echo "$PO_FROM" | cut -c1-8)"
B_TG="$PD/tile_grants.json.bak_S497_$(echo "$TG_FROM" | cut -c1-8)"
SCR=""; PLACED=0; HAVE_LOCK=0; T0=""; RED=""; WPY=""; FACTS=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { "$CURL" -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() {
  [ -n "$SCR" ] && rm -rf "$SCR"
  rm -f "$PD/.ring_outcome.py.s497" "$PD/.portal.py.s497" "$PD/.tile_grants.json.s497"
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
}
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - restoring"
  PLACED=0
  \cp -p "$B_RO" "$PD/ring_outcome.py"; \cp -p "$B_PO" "$PD/portal.py"; \cp -p "$B_TG" "$PD/tile_grants.json"
  for x in "ring_outcome.py:$RO_FROM" "portal.py:$PO_FROM" "tile_grants.json:$TG_FROM"; do
    f="${x%%:*}"; h="${x##*:}"
    if [ "$(m5 "$PD/$f")" = "$h" ]; then say "   $f back at its old bytes ($h)"; else say "   !! $f is NOT its old bytes - put its .bak_S497_ copy back by hand"; fi
  done
  "$SYSTEMCTL" restart ring-hook clinic-portal 2>/dev/null || true
  for _w in 1 2 3 4 5 6 7 8 9 10; do sleep "$WAIT"; [ "$(health "$PORURL/portal/health")" = 200 ] && break; done
  HR="$(health "$PORURL/portal/health")"
  if [ "$HR" = 200 ] && "$SYSTEMCTL" is-active --quiet clinic-portal && "$SYSTEMCTL" is-active --quiet ring-hook; then
    say "   after the restore: portal health 200 . clinic-portal active . ring-hook active -- the box is as it was before this run"
  else
    say "   !! after the restore: portal health $HR . clinic-portal $("$SYSTEMCTL" is-active clinic-portal 2>/dev/null) . ring-hook $("$SYSTEMCTL" is-active ring-hook 2>/dev/null)"
    say "   !! THE OLD FILES ARE BACK BUT A SERVICE IS NOT UP - tell the assistant now (systemctl status clinic-portal ring-hook)"
  fi
  say "   NOTHING of $KIT is live. The ring store may have gained its new, empty columns; the old program reads it as before (walked)."
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

# ---------------------------------------------------------------------------------------------- [1/8] the kit's own gates
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 ring_outcome.py)" = "$RO_TO" ] && [ "$(m5 portal.py)" = "$PO_TO" ] || { say "!! [1/8] the kit's two programs are not the ones this installer names - nothing installed"; exit 1; }
for p in "$SPY_VENV" "$SPY_SVC"; do
  [ -x "$p" ] || { say "!! [1/8] no python at $p - nothing installed"; exit 1; }
done
[ "$("$SPY_VENV" -B apply_s497.py --pins 2>/dev/null)" = "$TG_FROM $TG_TO" ] || { say "!! [1/8] the applier does not name the pins this installer names - nothing installed"; exit 1; }
[ "$("$SPY_VENV" -B make_s497.py --pins 2>/dev/null | tr '\n' ' ')" = "ring_outcome.py $RO_FROM $RO_TO portal.py $PO_FROM $PO_TO " ] \
  || { say "!! [1/8] the builder does not name the pins this installer names - nothing installed"; exit 1; }
WPYS=""
for p in "$SPY_VENV" "$SPY_SVC"; do "$p" -c "import flask, sqlite3" 2>/dev/null && WPYS="$WPYS $p"; done
[ -n "$WPYS" ] || { say "!! [1/8] neither python has Flask (the walk needs it) - nothing installed"; exit 1; }
say "[1/8] kit gates green (SUMS, KIT_ID, each program's own md5, the applier's and the builder's pins; Flask under:$WPYS)"

# ---------------------------------------------------------------------------------------------- [2/8] the live files' pins
H_RO="$(m5 "$PD/ring_outcome.py")"; H_PO="$(m5 "$PD/portal.py")"; H_TG="$(m5 "$PD/tile_grants.json")"
if [ "$H_RO" = "$RO_TO" ] && [ "$H_PO" = "$PO_TO" ] && [ "$H_TG" = "$TG_TO" ]; then
  say "-- ALREADY INSTALLED: the three files are at the kit's pins; nothing changed. clinic-portal $("$SYSTEMCTL" is-active clinic-portal 2>/dev/null) . ring-hook $("$SYSTEMCTL" is-active ring-hook 2>/dev/null)"
  clean; exit 0
fi
BAD=0
[ "$H_RO" = "$RO_FROM" ] || { say "!! [2/8] $PD/ring_outcome.py is ${H_RO:-not there}, not $RO_FROM - it changed after this kit was built."; BAD=1; }
[ "$H_PO" = "$PO_FROM" ] || { say "!! [2/8] $PD/portal.py is ${H_PO:-not there}, not $PO_FROM - it changed after this kit was built."; BAD=1; }
[ "$H_TG" = "$TG_FROM" ] || { say "!! [2/8] $PD/tile_grants.json is ${H_TG:-not there}, not $TG_FROM (v32) - it changed after this kit was built."; BAD=1; }
[ "$(m5 "$PD/ring_common.py")" = "$RC_PIN" ] || { say "!! [2/8] $PD/ring_common.py is $(m5 "$PD/ring_common.py"), not $RC_PIN - the list was built reading that file."; BAD=1; }
[ -f "$PD/portal_push.py" ] || { say "!! [2/8] $PD/portal_push.py is not there - it is what mounts the list's routes."; BAD=1; }
[ "$BAD" = 0 ] || { say "   REFUSED: nothing placed, nothing restarted. Tell the assistant; the kit is rebuilt on the new file."; clean; exit 1; }
say "[2/8] the three files, and ring_common.py beside them, are at the pins this kit was built on"

mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
if [ "$HAVE_LOCK" != 1 ]; then
  say "!! [2/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
SCR="$(mktemp -d "$TMPBASE/s497_scratch_XXXXXXXX")" || { say "!! [2/8] no scratch folder - nothing installed"; exit 1; }
chmod 700 "$SCR"

# ---------------------------------------------------------------------------------------------- [3/8] compile; rebuild; the grants
mkdir -p "$SCR/c" && \cp -p "$KDIR/ring_outcome.py" "$KDIR/portal.py" "$KDIR/apply_s497.py" "$KDIR/make_s497.py" "$KDIR/walk_s497.py" "$SCR/c/" \
  && \cp -p "$PD/tile_grants.json" "$SCR/c/tile_grants.json" || { say "!! [3/8] no scratch copy - nothing installed"; clean; exit 1; }
for p in "$SPY_SVC" "$SPY_VENV"; do
  ( cd "$SCR/c" && "$p" -W ignore -B -c "
import sys
for f in ('ring_outcome.py', 'portal.py', 'apply_s497.py', 'make_s497.py', 'walk_s497.py'):
    compile(open(f, encoding='utf-8').read(), f, 'exec')
" ) 2>"$SCR/compile.err" || { say "!! [3/8] compile failed under $p: $(tail -1 "$SCR/compile.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
done
( cd "$SCR" && "$SPY_VENV" -W ignore -B "$KDIR/make_s497.py" --check "$PD" "$KDIR" ) >"$SCR/make.out" 2>&1 \
  || { say "!! [3/8] the kit's two programs are NOT what the builder makes from this box's live files: $(tail -2 "$SCR/make.out" | tr '\n' ' ' | cut -c1-300) - nothing installed"; clean; exit 1; }
( cd "$SCR" && "$SPY_VENV" -B "$KDIR/apply_s497.py" "$SCR/c/tile_grants.json" ) >"$SCR/apply.out" 2>&1 && [ "$(m5 "$SCR/c/tile_grants.json")" = "$TG_TO" ] \
  || { say "!! [3/8] the grants edit did not give v33 on a scratch copy: $(tail -1 "$SCR/apply.out" | cut -c1-200) - nothing installed"; clean; exit 1; }
say "[3/8] the kit's programs compile under $SPY_SVC and $SPY_VENV; rebuilt here from this box's live bytes they are the kit's files, byte for byte; the grants edit gives v33 at its pin on a scratch copy"

# ---------------------------------------------------------------------------------------------- [4/8] the walk, and its control
unchanged() { [ "$(m5 "$PD/ring_outcome.py")" = "$RO_FROM" ] && [ "$(m5 "$PD/portal.py")" = "$PO_FROM" ] && [ "$(m5 "$PD/tile_grants.json")" = "$TG_FROM" ]; }
DBARG=""; [ -f "$PD/ring_outcomes.db" ] && DBARG="--db $PD/ring_outcomes.db --finance-db $FINDB"
for WPY in $WPYS; do
  WOUT="$( cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 timeout 900 "$WPY" -W ignore -B "$KDIR/walk_s497.py" --kit "$KDIR" --portal "$PD" $DBARG 2>&1 )"
  echo "$WOUT" | grep -E '^  FAIL|^  note|^WALK_S497|^PART R|^  pass (aaj|7|30): |^  pass the real store' | cut -c1-400 | sed 's/^/   /'
  echo "$WOUT" | tail -1 | grep -q "^WALK_S497 GREEN" || { say "!! [4/8] the walk is red under $WPY - nothing installed. Tell the assistant with this output."; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
  COUT="$( cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 timeout 900 "$WPY" -W ignore -B "$KDIR/walk_s497.py" --kit "$KDIR" --portal "$PD" --control 2>&1 | tail -1 )"
  echo "$COUT" | grep -q "^WALK_S497 RED" || { say "!! [4/8] the SAME walk on the live files did not go red under $WPY ($COUT): it cannot tell old from new - nothing installed."; clean; exit 1; }
  say "   under $WPY: $(echo "$WOUT" | tail -1) . the same walk on the live files: $COUT (the negative control)"
done
unchanged || { say "!! [4/8] a live file changed during the walk - nothing installed"; clean; exit 1; }
say "[4/8] walked on this box: each login's home and page, the three parts, the card, the two buttons, the no-show rule, the India-time clock, Docterz read-only, WhatsApp sending nothing"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

# ---------------------------------------------------------------------------------------------- [5/8] backups
\cp -p "$PD/ring_outcome.py" "$B_RO" && [ "$(m5 "$B_RO")" = "$RO_FROM" ] && \cp -p "$PD/portal.py" "$B_PO" && [ "$(m5 "$B_PO")" = "$PO_FROM" ] \
  && \cp -p "$PD/tile_grants.json" "$B_TG" && [ "$(m5 "$B_TG")" = "$TG_FROM" ] || { say "!! [5/8] a backup failed - nothing placed"; clean; exit 1; }
DBBAK="(no ring store yet)"
if [ -f "$PD/ring_outcomes.db" ]; then
  DBBAK="$PD/ring_outcomes.db.bak_S497_$(date +%Y%m%d_%H%M%S)"
  "$SPY_VENV" -B -c "
import sqlite3, sys
a = sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True, timeout=30); b = sqlite3.connect(sys.argv[2])
a.backup(b); b.close(); a.close()
c = sqlite3.connect('file:%s?mode=ro' % sys.argv[2], uri=True); assert c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'; c.close()
" "$PD/ring_outcomes.db" "$DBBAK" 2>"$SCR/dbbak.err" && chmod 600 "$DBBAK" || { say "!! [5/8] the ring store's backup failed: $(tail -1 "$SCR/dbbak.err" | cut -c1-200) - nothing placed"; rm -f "$DBBAK"; clean; exit 1; }
fi
say "[5/8] backups made: $(basename "$B_RO") . $(basename "$B_PO") . $(basename "$B_TG") . the ring store: $(basename "$DBBAK")"

# ---------------------------------------------------------------------------------------------- [6/8] place, read back, restart
\cp -p "$PD/ring_outcome.py" "$PD/.ring_outcome.py.s497" && cat "$KDIR/ring_outcome.py" > "$PD/.ring_outcome.py.s497" && [ "$(m5 "$PD/.ring_outcome.py.s497")" = "$RO_TO" ] \
  && \cp -p "$PD/portal.py" "$PD/.portal.py.s497" && cat "$KDIR/portal.py" > "$PD/.portal.py.s497" && [ "$(m5 "$PD/.portal.py.s497")" = "$PO_TO" ] \
  && \cp -p "$PD/tile_grants.json" "$PD/.tile_grants.json.s497" && cat "$SCR/c/tile_grants.json" > "$PD/.tile_grants.json.s497" && [ "$(m5 "$PD/.tile_grants.json.s497")" = "$TG_TO" ] \
  || { say "!! [6/8] could not stage the files - nothing placed"; clean; exit 1; }
PLACED=1
mv -f "$PD/.ring_outcome.py.s497" "$PD/ring_outcome.py" || restore "placing ring_outcome.py"
mv -f "$PD/.portal.py.s497" "$PD/portal.py" || restore "placing portal.py"
mv -f "$PD/.tile_grants.json.s497" "$PD/tile_grants.json" || restore "placing tile_grants.json"
[ "$(m5 "$PD/ring_outcome.py")" = "$RO_TO" ] && [ "$(m5 "$PD/portal.py")" = "$PO_TO" ] && [ "$(m5 "$PD/tile_grants.json")" = "$TG_TO" ] || restore "md5 read-back"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart ring-hook || restore "ring-hook restart"
"$SYSTEMCTL" restart clinic-portal || restore "clinic-portal restart"
for _w in 1 2 3 4 5 6 7 8 9 10; do sleep "$WAIT"; [ "$(health "$PORURL/portal/health")" = 200 ] && break; done
sleep "$WAIT"
say "[6/8] placed; md5 read back = the kit's pins; ring-hook and clinic-portal restarted (nothing else)"

# ---------------------------------------------------------------------------------------------- [7/8] is it well?
post_checks() {
  RED=""
  "$SYSTEMCTL" is-active --quiet clinic-portal || { RED="clinic-portal not active"; return 1; }
  "$SYSTEMCTL" is-active --quiet ring-hook || { RED="ring-hook not active"; return 1; }
  PH="$("$CURL" -s -m 8 "$PORURL/portal/health")"
  echo "$PH" | grep -q '"status": *"ok"' || { RED="portal health: $(echo "$PH" | tr -d '\n' | cut -c1-80)"; return 1; }
  RP="$(grep -m1 '^RING_HOOK_PORT=' "$PD/ring_hook.env" 2>/dev/null | cut -d= -f2)"; RP="${RP:-8110}"
  RH="$("$CURL" -s -m 8 "${RINGURL:-http://127.0.0.1:$RP}/ring-hook/health")"
  echo "$RH" | grep -q '"status": *"ok"' || { RED="ring-hook health: $(echo "$RH" | tr -d '\n' | cut -c1-80)"; return 1; }
  # a page behind the login answers 302 to a caller with no login: that is EXPECTED, never a failure (rule 5)
  for u in /portal/ring/list "/portal/ring/list?d=aaj" "/portal/ring/outcome?s=x" /portal/ring/counts /portal; do
    c=$(health "$PORURL$u"); case "$c" in 302|401) ;; *) RED="$u answered $c without a login (it must send a stranger to the login)"; return 1;; esac
  done
  for u in /portal/ring/list/act /portal/ring/appt /portal/ring/list/switch /portal/ring/list/setting; do
    c=$("$CURL" -s -o /dev/null -m 10 -w '%{http_code}' -X POST -H 'Content-Type: application/json' --data-binary '{}' "$PORURL$u")
    case "$c" in 302|401) ;; *) RED="$u answered $c to a POST with no login (it must turn him away)"; return 1;; esac
  done
  c=$(health "$PORURL/portal/login"); case "$c" in 200|302) ;; *) RED="/portal/login answered $c"; return 1;; esac
  c=$(health "$PORURL/portal/sw.js"); [ "$c" = 200 ] || { RED="/portal/sw.js answered $c"; return 1; }
  JR="$("$JOURNALCTL" -u ring-hook -u clinic-portal --since "$T0" --no-pager 2>/dev/null | grep -c -i 'Traceback\|ModuleNotFoundError\|ImportError\|AssertionError\|SyntaxError\|NameError')"
  [ "${JR:-0}" = 0 ] || { RED="journal: $JR error line(s) since the restart"; return 1; }
  FACTS="$( cd "$PD" && FINANCE_DB="$FINDB" "$SPY_VENV" -W ignore -B -c "
import sqlite3
import ring_outcome as ro
assert ro.LIST_TILE == 'Call ke baad' and ro.WA_ENABLED is False and hasattr(ro, 'render_list') and hasattr(ro, 'render_appt_card')
h = sorted(ro.list_holders())
assert h == ['alisha', 'reception', 'shavez', 'shivani'], h
ro.init_db()
d = ro.list_data('30')
assert d['store_ok']
hard = ro._day(ro.HARD_FLOOR)
e = ro.list_data('30', floor=hard, everything=True)
c = sqlite3.connect('file:%s?mode=ro' % ro.DB_FILE, uri=True)
n_all = c.execute('SELECT COUNT(*) FROM outcome WHERE code=?', (ro.APPT_CODE,)).fetchone()[0]
n_new = c.execute('SELECT COUNT(*) FROM outcome WHERE code=? AND substr(when_ist, 1, 10) >= ?', (ro.APPT_CODE, ro.HARD_FLOOR)).fetchone()[0]
c.close()
t = d['visits_through']
hw = '%s-%d' % (ro._dm(hard), hard.year)
print('   Docterz: visits on file up to %s' % ((ro._dm_dow(t) + ' ' + str(t.year)) if t else 'NOT READABLE just now -- nobody will be shown as Nahi aaye until they are'))
print('   rows: %d appointments in the ring store, %d of them booked on or after %s' % (n_all, n_new, hw))
print('   rows the list holds now (booked on or after %s): %d Nahi aaye . %d Aane baaki . %d Aa gaye' % (ro._dm_dow(d['follow_from']), len(d['noshow']), len(d['due']), len(d['came'])))
print('   rows it would hold if he took the follow-from date back to %s: %d Nahi aaye . %d Aane baaki . %d Aa gaye' % (hw, len(e['noshow']), len(e['due']), len(e['came'])))
on = ro.list_on()
print('   the switch: %s for staff%s (the tile is granted to %s; wait %d days when no day is written)' % (
    'ON' if on else 'OFF', ' -- it was turned on before this run' if on else ' -- he turns it on at /portal/ring/list', ', '.join(h), d['wait_days']))
" )" || { RED="the placed ring_outcome.py does not load, or the grants are not the four, or the store cannot be read"; return 1; }
  [ -n "$FACTS" ] || { RED="the placed ring_outcome.py answered nothing about this box"; return 1; }
  return 0
}
post_checks || restore "$RED"
PLACED=0
say "[7/8] clinic-portal and ring-hook active and healthy . the list, the card and the counts behind the login (302 to a stranger) . the four new POST doors turn a stranger away . journal clean"
say "[8/8] the tile 'Call ke baad' is on the doctor's portal now. For alisha, shivani, shavez and reception it stays hidden, and their card after the tap stays as it was, until he turns the list on at /portal/ring/list"
clean
say "all green -- $KIT: DONE.  For the record:"
for x in "ring_outcome.py:$RO_TO" "portal.py:$PO_TO" "tile_grants.json:$TG_TO"; do
  f="${x%%:*}"; h="${x##*:}"; g="$(m5 "$PD/$f")"
  if [ "$g" = "$h" ]; then say "   md5 read back  $g  $PD/$f  = the kit's TO pin"; else say "   !! md5 read back  $g  $PD/$f  is NOT the kit's TO pin $h"; fi
done
echo "$FACTS"
say "   restarted: ring-hook (it loads ring_outcome.py too) and clinic-portal -- both active and healthy; nothing else was restarted"
exit 0
