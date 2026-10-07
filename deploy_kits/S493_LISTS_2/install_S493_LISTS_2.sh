#!/bin/bash
# =============================================================================
# install_S493_LISTS_2.sh -- session 298, 07-Oct-2026 -- the staff's 'Aaj ka kaam' lists, rebuilt to the owner's rulings
#  THE OWNER, 06-Oct: the lists are "confusing and complicated for the staff" -- a switch for each person and each line,
#  nothing before 1 October, one line = one job (no counts, no 'late'); 07-Oct: "i need one where I can edit these", and,
#  the mock-up edited by his own hand, "Build the lists". Plus a task section, and September for him only.
#  REPLACED WHOLE (both the parent's own, S487):
#         /root/finance/aaj_kaam.py     d65e0bf4 -> the kit's   the engine: a floor under 22 dated tables and a second guard,
#                                                                the panel's documents (table aaj_cfg), tasks, the same five doors
#         /root/finance/aaj_kaam.html   03ccc58e -> the kit's   the staff's page
#  NEW:   /root/finance/aaj_seed.py     the owner's mock-up exactly as he left it, and each line's working
#         /root/finance/aaj_panel.html  his panel (https://followup.dr-manoj.in/finance/aaj, the owner only)
#  NOT TOUCHED: finance_app.py, owner_console.py/.html, portal.py, aaj_duties.json, DUTY_MAP.json, the crontab, every other
#  page. No table and no setting is written by this installer: THE LISTS STAY OFF until the owner presses Start on his panel
#  (the tables aaj_cfg / aaj_task are made by his first change / first task).
# Walked first, on this box (walk_s493.py): on a made-up clinic, and read-only on a copy of finance.db -- every floor view
# laid on the real tables, every line read, the owner's own lines counted against 1.0's, the console's own builder run with
# the new engine. Restarts clinic-finance only (about 10 seconds); red after placing -> everything is put back as it was.
# DRY=1 places nothing. NEEDS the build lock free (F-694).
# =============================================================================
set -u
KIT="S493_LISTS_2"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
DB="${FINANCE_DB:-$FIN/finance.db}"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
DUTYMAP="${DUTY_MAP_JSON:-/root/deploy/repo/claude_code_briefs/DUTY_MAP.json}"
PY_FROM=d65e0bf4360f2ac2a6d4b3f6dd851dde; HT_FROM=03ccc58e6a55c445570046558f485feb
PY_TO=e8517623d1b8946eb7b7779e83f817ad; HT_TO=d7c9c38bbf3f96beba9d6167b1bd466e; SEED=e13d03d06bf6a2bc53c9bb129e2a5206; PANEL=898c42e14b142e06f2800d83aaaf01ca
V_LIST="S493 2.0"
SCR=""; PLACED=0; HAVE_LOCK=0; HAD_SEED=0; HAD_PANEL=0; B_PY=""; B_HT=""; T0=""; RED=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() {
  [ -n "$SCR" ] && rm -rf "$SCR"
  rm -f "$FIN/.aaj_kaam.py.s493" "$FIN/.aaj_kaam.html.s493" "$FIN/.aaj_seed.py.s493" "$FIN/.aaj_panel.html.s493"
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
}
back() {  # $1 = backup, $2 = live file, $3 = its old md5, $4 = its name
  \cp -p "$1" "$2"
  if [ "$(m5 "$2")" = "$3" ]; then say "   $4 back at $3"; else say "   !! $4 is $(m5 "$2"), NOT its old $3 - put $1 back by hand"; fi
}
restore() {
  trap '' INT TERM HUP                                   # nothing interrupts the putting back
  say "!! RED after placing ($1) - restoring"
  PLACED=0
  back "$B_PY" "$FIN/aaj_kaam.py" "$PY_FROM" aaj_kaam.py
  back "$B_HT" "$FIN/aaj_kaam.html" "$HT_FROM" aaj_kaam.html
  [ "$HAD_SEED" = 0 ] && rm -f "$FIN/aaj_seed.py" && say "   aaj_seed.py removed"
  [ "$HAD_PANEL" = 0 ] && rm -f "$FIN/aaj_panel.html" && say "   aaj_panel.html removed"
  systemctl restart clinic-finance 2>/dev/null || true; sleep 9
  say "   finance healthz $(health "$FINURL/finance/healthz") · the lists: $(switch_words)"
  clean; exit 1
}
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
on_signal() {
  trap '' INT TERM HUP
  say ""; say "!! interrupted"
  if [ "$PLACED" = 1 ]; then restore "the run was interrupted after placing"; fi
  clean; exit 130
}
switch_words() {  # the lists' switch, read through a read-only door; words only
  "$SPY" -B - "$DB" <<'PY' 2>/dev/null || echo "the switch could not be read"
import sqlite3, sys
con = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True, timeout=5)
try:
    r = con.execute("SELECT value FROM setting WHERE key='aaj.staff_on'").fetchone()
except sqlite3.Error:
    r = None
v = str((r[0] if r else "") or "")
t = con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='aaj_cfg'").fetchone()[0]
print(("ON for staff since %s (started by %s)" % (v.split("|")[0].replace("T", " ")[:16], v.split("|")[1]) if "|" in v else "OFF for staff")
      + (" · the owner has saved changes on his panel" if t else " · the panel is as the kit seeds it (nothing saved yet)"))
PY
}
trap on_exit EXIT
trap on_signal INT TERM HUP
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }

md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 aaj_kaam.py)" = "$PY_TO" ] && [ "$(m5 aaj_kaam.html)" = "$HT_TO" ] && [ "$(m5 aaj_seed.py)" = "$SEED" ] && [ "$(m5 aaj_panel.html)" = "$PANEL" ] \
  || { say "!! [1/7] the kit's four files are not the ones this installer names - nothing installed"; exit 1; }
"$SPY" -c "import flask, sqlite3" 2>/dev/null || { say "!! [1/7] $SPY lacks flask (the walk needs it) - nothing installed"; exit 1; }
mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
if [ "$HAVE_LOCK" != 1 ]; then
  say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
SCR="$(mktemp -d "/tmp/s493_scratch_XXXXXXXX")" || { say "!! [1/7] no scratch folder - nothing installed"; exit 1; }
chmod 700 "$SCR"
say "[1/7] kit gates green (SUMS, KIT_ID, the four files' own md5, flask); the build lock is taken"

H_PY="$(m5 "$FIN/aaj_kaam.py")"; H_HT="$(m5 "$FIN/aaj_kaam.html")"
[ -f "$FIN/aaj_seed.py" ] && HAD_SEED=1; [ -f "$FIN/aaj_panel.html" ] && HAD_PANEL=1
if [ "$H_PY" = "$PY_TO" ] && [ "$H_HT" = "$HT_TO" ] && [ "$(m5 "$FIN/aaj_seed.py")" = "$SEED" ] && [ "$(m5 "$FIN/aaj_panel.html")" = "$PANEL" ]; then
  say "-- ALREADY INSTALLED: the four files are at the kit's pins; clinic-finance $(systemctl is-active clinic-finance 2>/dev/null); the lists: $(switch_words)"; clean; exit 0
fi
[ "$H_PY" = "$PY_FROM" ] || { say "!! [2/7] $FIN/aaj_kaam.py is $H_PY, not $PY_FROM (S487) - another kit changed it after this one was built. Nothing installed; tell the assistant."; clean; exit 1; }
[ "$H_HT" = "$HT_FROM" ] || { say "!! [2/7] $FIN/aaj_kaam.html is $H_HT, not $HT_FROM (S487) - another kit changed it after this one was built. Nothing installed; tell the assistant."; clean; exit 1; }
if [ "$HAD_SEED" = 1 ] && [ "$(m5 "$FIN/aaj_seed.py")" != "$SEED" ]; then say "!! [2/7] $FIN/aaj_seed.py is already there and is not this kit's file - nothing installed; tell the assistant."; clean; exit 1; fi
if [ "$HAD_PANEL" = 1 ] && [ "$(m5 "$FIN/aaj_panel.html")" != "$PANEL" ]; then say "!! [2/7] $FIN/aaj_panel.html is already there and is not this kit's file - nothing installed; tell the assistant."; clean; exit 1; fi
[ -f "$FIN/aaj_duties.json" ] && [ -f "$DUTYMAP" ] && [ -f "$FIN/owner_console.py" ] && [ -f "$DB" ] || { say "!! [2/7] aaj_duties.json, the duty map, owner_console.py or finance.db is not where it should be - nothing installed"; clean; exit 1; }
say "[2/7] aaj_kaam.py and aaj_kaam.html at their S487 pins; nothing in the way of the two new files; the lists are $(switch_words)"

"$SPY" -m py_compile aaj_kaam.py aaj_seed.py walk_s493.py 2>"$SCR/compile.err" || { say "!! [3/7] compile failed: $(tail -1 "$SCR/compile.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the kit compiles under $SPY"

unchanged() { [ "$(m5 "$FIN/aaj_kaam.py")" = "$PY_FROM" ] && [ "$(m5 "$FIN/aaj_kaam.html")" = "$HT_FROM" ]; }
WOUT="$( cd /tmp && TMPDIR="$SCR" timeout 900 "$SPY" -B "$KDIR/walk_s493.py" --kit "$KDIR" --finance "$FIN" --dutymap "$DUTYMAP" --code "$FIN" --code "$ROOT/marg_ingest" --old "$FIN/aaj_kaam.py" --console "$FIN/owner_console.py" --db "$DB" ${WALK_EXTRA:-} 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^  note|^WALK_S493' | cut -c1-600 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S493 GREEN" || { say "!! [4/7] walk red - nothing installed. Tell the assistant with this output."; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
unchanged || { say "!! [4/7] a file changed during the walk - nothing installed"; clean; exit 1; }
say "[4/7] walk green on this box: a made-up clinic, then a copy of the real database read-only (every floor view laid, every line read, the owner's own lines as 1.0 counts them, the console's builder run with the new engine)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

B_PY="$FIN/aaj_kaam.py.bak_S493_$(echo "$PY_FROM" | cut -c1-8)"; B_HT="$FIN/aaj_kaam.html.bak_S493_$(echo "$HT_FROM" | cut -c1-8)"
\cp -p "$FIN/aaj_kaam.py" "$B_PY" && \cp -p "$FIN/aaj_kaam.html" "$B_HT" && [ "$(m5 "$B_PY")" = "$PY_FROM" ] && [ "$(m5 "$B_HT")" = "$HT_FROM" ] || { say "!! [5/7] a backup failed - nothing placed"; clean; exit 1; }
say "[5/7] backups: $B_PY $B_HT"
stage() {  # $1 = a live file whose owner and mode are kept, $2 = the new bytes, $3 = the staged name, $4 = its md5
  \cp -p "$1" "$3" && cat "$2" > "$3" && [ "$(m5 "$3")" = "$4" ]
}
stage "$FIN/aaj_kaam.py" "$KDIR/aaj_seed.py" "$FIN/.aaj_seed.py.s493" "$SEED" && stage "$FIN/aaj_kaam.html" "$KDIR/aaj_panel.html" "$FIN/.aaj_panel.html.s493" "$PANEL" \
  && stage "$FIN/aaj_kaam.html" "$KDIR/aaj_kaam.html" "$FIN/.aaj_kaam.html.s493" "$HT_TO" && stage "$FIN/aaj_kaam.py" "$KDIR/aaj_kaam.py" "$FIN/.aaj_kaam.py.s493" "$PY_TO" \
  || { say "!! [6/7] could not stage the files - nothing placed"; clean; exit 1; }
PLACED=1
mv -f "$FIN/.aaj_seed.py.s493" "$FIN/aaj_seed.py" || restore "placing aaj_seed.py"
mv -f "$FIN/.aaj_panel.html.s493" "$FIN/aaj_panel.html" || restore "placing aaj_panel.html"
mv -f "$FIN/.aaj_kaam.html.s493" "$FIN/aaj_kaam.html" || restore "placing aaj_kaam.html"
mv -f "$FIN/.aaj_kaam.py.s493" "$FIN/aaj_kaam.py" || restore "placing aaj_kaam.py"
[ "$(m5 "$FIN/aaj_kaam.py")" = "$PY_TO" ] && [ "$(m5 "$FIN/aaj_kaam.html")" = "$HT_TO" ] && [ "$(m5 "$FIN/aaj_seed.py")" = "$SEED" ] && [ "$(m5 "$FIN/aaj_panel.html")" = "$PANEL" ] || restore "md5 read-back"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
for _w in 1 2 3 4 5 6 7 8 9 10 11 12; do sleep 3; [ "$(health "$FINURL/finance/healthz")" = 200 ] && break; done
sleep 3
post_checks() {
  RED=""
  systemctl is-active --quiet clinic-finance || { RED="clinic-finance not active"; return 1; }
  c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || { RED="finance healthz $c1"; return 1; }
  for u in /finance/console /finance/console/api/state /finance/aaj /finance/aaj/api/list /finance/aaj/api/line /finance/aaj/api/switch "/finance/aaj/api/switch?panel=1" /finance/approvals; do
    c=$(health "$FINURL$u"); case "$c" in 302|401) ;; *) RED="$u answered $c without a login (it must be behind the login gate)"; return 1;; esac
  done
  for u in /finance/aaj/api/tick /finance/aaj/api/switch; do
    c=$(health -X POST --data-binary '{"on":true}' -H 'Content-Type: application/json' "$FINURL$u"); case "$c" in 302|401) ;; *) RED="a POST to $u answered $c without a login"; return 1;; esac
  done
  D1="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
  echo "$D1" | grep -q '"NOT_YOU"' || { RED="the heartbeat door no longer refuses an unsigned heartbeat: $(echo "$D1" | cut -c1-160)"; return 1; }
  if journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted"; then RED="a part of the finance app did NOT mount"; return 1; fi
  JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
  [ "${JR:-0}" = 0 ] || { RED="clinic-finance journal: $JR error line(s)"; return 1; }
  ( cd "$FIN" && DUTY_MAP_JSON="$DUTYMAP" "$SPY" -B -c "
import aaj_kaam as a
assert a.VERSION == '$V_LIST' and a.SEED is not None and a.SEED_ERR is None and callable(a.init)
r = a.Reader('$DB')
try:
    assert not r.defs_err(), r.defs_err()
    assert not r.info['bad'], r.info['bad']
    assert len(r.people) == 6
    print('   on this box: the floor %s on %d tables; the panel seeded: %s' % (r.info['floor'], len(r.info['views']), ', '.join('%s %s' % (p['name'], 'on' if p['on'] else 'off') for p in r.people.values())))
finally:
    r.close()
" ) || { RED="the placed aaj_kaam.py does not read the lists under $SPY"; return 1; }
  # the console's own builder, exactly as the service runs it, through the placed files -- its reading goes to the scratch folder
  ( cd "$FIN" && TMPDIR="$SCR" FINANCE_DB="$DB" DUTY_MAP_JSON="$DUTYMAP" timeout 150 "$SPY" -B "$FIN/owner_console.py" --build --db "$DB" --out "$SCR/reading.dat" > "$SCR/reading.log" 2>&1 ) \
    || { RED="the console's builder did not make a reading with the placed engine: $(tail -1 "$SCR/reading.log" | cut -c1-200)"; return 1; }
  "$SPY" -B -c "
import json
s = json.load(open('$SCR/reading.dat', encoding='utf-8')); l = s.get('lists') or {}
assert l.get('engine') is True and not l.get('err'), l
assert 'work' not in (s.get('failed') or []) and 'needs' not in (s.get('failed') or []), s.get('failed')
print('   the console reads the lists by the new engine (floor %s); sections not read: %s' % (l.get('floor'), ', '.join(s.get('failed') or []) or 'none'))
" || { RED="the console's reading does not carry the new engine"; return 1; }
  return 0
}
post_checks || restore "$RED"
PLACED=0
say "[6/7] placed, md5 read back = the kit's pins · clinic-finance active · healthz 200 · the console's doors and the lists' five doors behind the login gate · the heartbeat door as before · every part mounted · journal clean · the console's own builder made a reading with the new engine"
say "[7/7] THE LISTS ARE $(switch_words)."
say "      Nothing shows to any staff member until the owner presses Start on his panel: https://followup.dr-manoj.in/finance/aaj"
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/aaj_kaam.py" "$FIN/aaj_kaam.html" "$FIN/aaj_seed.py" "$FIN/aaj_panel.html"
exit 0
