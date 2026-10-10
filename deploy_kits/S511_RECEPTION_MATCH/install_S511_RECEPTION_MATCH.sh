#!/bin/bash
# =============================================================================
# install_S511_RECEPTION_MATCH.sh -- session 304 (parent), 10-Oct-2026 -- Club F (1): the reception login's tiles, Morning match
#  THE OWNER'S LIST (S302 close, item 7 -- CLUB 3 a): the shared 'reception' login lacked Docterz daily collection, Morning match
#  and Check karein; Morning match landed on yesterday only; its verdict said the bank agrees while the bank had not answered (F-796).
#  EDITED, each gated on the md5 of the file it replaces (the 10-Oct 01:35 bundle's bytes), built by make_s511.py on this box:
#     /root/portal/tile_grants.json   64f8b049 (v33) -> v34: the three tiles granted to 'reception' by name (alisha, shivani and
#                                                     shavez already have them; the login already holds the roles the pages ask)
#     /root/finance/clinic_money.py   683f7511        -> Morning match opens on the list of October working days still waiting for
#                                                     a first pass, OLDEST FIRST (one day goes straight to it; none goes to
#                                                     yesterday); the named checker's list adds the days waiting for his check;
#                                                     the verdict names only the parts that have answered
#  No data step. Restarts clinic-finance and clinic-portal ONLY. Walked first on a scratch copy; the SAME walk on the live files
#  must end RED.   FD (default /root)  FINDB  FINURL  PORURL  LOCK  TMPBASE  SPY_SVC  SPY_VENV  SYSTEMCTL  CURL  JOURNALCTL  WAIT
# =============================================================================
set -u
KIT="S511_RECEPTION_MATCH"
KDIR="$(cd "$(dirname "$0")" && pwd)"
FD="${FD:-/root}"
PORURL="${PORURL:-http://127.0.0.1:8099}"
FINDB="${FINDB:-$FD/finance/finance.db}"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
TMPBASE="${TMPBASE:-/tmp}"
SPY_SVC="${SPY_SVC:-/usr/bin/python3}"
SPY_VENV="${SPY_VENV:-/root/wa/venv/bin/python3}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
CURL="${CURL:-curl}"
JOURNALCTL="${JOURNALCTL:-journalctl}"
WAIT="${WAIT:-3}"
TABLE="finance/clinic_money.py|make_s511.py|683f75112920adb17c0a077602f4f9ec|b3ddc8d2ac884b4d92058c588c3378b3
portal/tile_grants.json|make_s511.py|64f8b04937e8841c405cb9070b604aad|5d9fd791084eedd728d5cca4c50d2528"
READPINS="portal/portal.py|f8b059f61fa8b885f024f4f4ce73e4f2"
SCR=""; PLACED=0; HAVE_LOCK=0; T0=""; RED=""; DBBAK=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { "$CURL" -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
rows() { echo "$TABLE" | while IFS='|' read -r f mk from to; do echo "$f $mk $from $to"; done; }
clean() {
  [ -n "$SCR" ] && rm -rf "$SCR"
  rows | while read -r f mk from to; do rm -f "$(dirname "$FD/$f")/.$(basename "$f").s511"; done
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
}
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - restoring"
  PLACED=0
  rows | while read -r f mk from to; do
    \cp -p "$FD/$f.bak_S511_$(echo "$from" | cut -c1-8)" "$FD/$f"
    if [ "$(m5 "$FD/$f")" = "$from" ]; then say "   $f back at its old bytes ($from)"; else say "   !! $f is NOT its old bytes - put its .bak_S511_ copy back by hand"; fi
  done
  "$SYSTEMCTL" restart clinic-finance clinic-portal 2>/dev/null || true
  for _w in 1 2 3 4 5 6 7 8 9 10 11 12; do sleep "$WAIT"; [ "$(health "$FINURL/finance/healthz")" = 200 ] && break; done
  HR="$(health "$FINURL/finance/healthz")"
  if [ "$HR" = 200 ] && "$SYSTEMCTL" is-active --quiet clinic-finance; then
    say "   after the restore: finance healthz 200 . clinic-finance active -- the box is as it was before this run"
  else
    say "   !! after the restore: finance healthz $HR . clinic-finance $("$SYSTEMCTL" is-active clinic-finance 2>/dev/null)"
    say "   !! THE OLD FILES ARE BACK BUT THE SERVICE IS NOT UP - tell the assistant now"
  fi
  say "   NOTHING of $KIT is live. finance.db was not touched (the data step runs only after a green placing)."
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

# ------------------------------------------------------------------------------------------- [1/7] the kit's own gates
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
BAD=0
while read -r f mk from to; do [ "$(m5 "$(basename "$f")")" = "$to" ] || { say "!! [1/7] the kit's $f is not the one this installer names"; BAD=1; }; done < <(rows)
[ "$BAD" = 0 ] || { say "   nothing installed"; exit 1; }
for p in "$SPY_VENV" "$SPY_SVC"; do [ -x "$p" ] || { say "!! [1/7] no python at $p - nothing installed"; exit 1; }; done
WPY=""
for p in "$SPY_SVC" "$SPY_VENV"; do "$p" -c "import flask, sqlite3" 2>/dev/null && { WPY="$p"; break; }; done
[ -n "$WPY" ] || { say "!! [1/7] neither python has Flask (the walk needs it) - nothing installed"; exit 1; }
say "[1/7] kit gates green (SUMS, KIT_ID, each file's own md5; the walk runs under $WPY)"

# ------------------------------------------------------------------------------------------- [2/7] the live files' pins
ALL_TO=1; BAD=0
while read -r f mk from to; do
  h="$(m5 "$FD/$f")"
  [ "$h" = "$to" ] || ALL_TO=0
  [ "$h" = "$from" ] || [ "$h" = "$to" ] || { say "!! [2/7] $FD/$f is ${h:-not there}, not $from - it changed after this kit was built."; BAD=1; }
done < <(rows)
if [ "$ALL_TO" = 1 ]; then
  say "-- ALREADY INSTALLED: the two files are at the kit's pins; nothing changed. clinic-finance $("$SYSTEMCTL" is-active clinic-finance 2>/dev/null)"
  clean; exit 0
fi
while IFS='|' read -r f pin; do
  [ "$(m5 "$FD/$f")" = "$pin" ] || { say "!! [2/7] $FD/$f is $(m5 "$FD/$f"), not $pin - this kit was built reading that file."; BAD=1; }
done < <(echo "$READPINS")
while read -r f mk from to; do [ "$(m5 "$FD/$f")" = "$from" ] || { say "!! [2/7] $FD/$f is half-way (neither the old nor the new bytes)"; BAD=1; }; done < <(rows)
[ "$BAD" = 0 ] || { say "   REFUSED: nothing placed, nothing restarted. Tell the assistant; the kit is rebuilt on the new file."; clean; exit 1; }
say "[2/7] the two files, and portal.py beside them, are at the pins this kit was built on"
mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
if [ "$HAVE_LOCK" != 1 ]; then
  say "!! [2/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
SCR="$(mktemp -d "$TMPBASE/s511_scratch_XXXXXXXX")" || { say "!! [2/7] no scratch folder - nothing installed"; exit 1; }
chmod 700 "$SCR"

# ------------------------------------------------------------------------------------------- [3/7] compile; rebuild from the live bytes
for p in "$SPY_SVC" "$SPY_VENV"; do
  ( cd "$KDIR" && "$p" -W ignore -B -c "
for f in ('clinic_money.py', 'walk_s511.py', 'make_s511.py'):
    compile(open(f, encoding='utf-8').read(), f, 'exec')
" ) 2>"$SCR/compile.err" || { say "!! [3/7] compile failed under $p: $(tail -1 "$SCR/compile.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
done
BAD=0
mkdir -p "$SCR/lv" && \cp -p "$FD/finance/clinic_money.py" "$FD/portal/tile_grants.json" "$SCR/lv/" && ( cd "$SCR" && "$SPY_VENV" -W ignore -B "$KDIR/make_s511.py" "$SCR/lv" "$SCR/rb" ) >"$SCR/make.out" 2>&1 || { say "!! [3/7] the builder refused on this box's live bytes: $(tail -1 "$SCR/make.out" | cut -c1-200)"; BAD=1; }
while read -r f mk from to; do
  [ "$(m5 "$SCR/rb/$(basename "$f")")" = "$to" ] || { say "!! [3/7] $f rebuilt here from this box's live bytes is NOT the kit's"; BAD=1; }
done < <(rows)
[ "$BAD" = 0 ] || { say "   nothing installed"; clean; exit 1; }
say "[3/7] the kit compiles under $SPY_SVC and $SPY_VENV; rebuilt here from this box's live bytes, each of the two is the kit's file, byte for byte"

# ------------------------------------------------------------------------------------------- [4/7] the walk, and its control
unchanged() { while read -r f mk from to; do [ "$(m5 "$FD/$f")" = "$from" ] || return 1; done < <(rows); return 0; }
WOUT="$( cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 timeout 1200 "$WPY" -W ignore -B "$KDIR/walk_s511.py" --kit "$KDIR" --fin "$FD/finance" --portal "$FD/portal" --db "$FINDB" --venv "$SPY_VENV" 2>&1 )"
echo "$WOUT" | grep -E '^  |^WALK_S511' | cut -c1-200 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S511 GREEN" || { say "!! [4/7] the walk is red - nothing installed. Tell the assistant with this output."; echo "$WOUT" | tail -15 | cut -c1-300; clean; exit 1; }
COUT="$( cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 timeout 1200 "$WPY" -W ignore -B "$KDIR/walk_s511.py" --kit "$KDIR" --fin "$FD/finance" --portal "$FD/portal" --db "$FINDB" --venv "$SPY_VENV" --control 2>&1 | tail -1 )"
echo "$COUT" | grep -q "^WALK_S511 RED" || { say "!! [4/7] the SAME walk on the live files did not go red ($COUT): it cannot tell old from new - nothing installed."; clean; exit 1; }
unchanged || { say "!! [4/7] a live file changed during the walk - nothing installed"; clean; exit 1; }
say "[4/7] walked on a scratch copy of finance.db: $(echo "$WOUT" | tail -1) . the same walk on the live files: $(echo "$COUT" | cut -c1-90)... (the negative control)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

# ------------------------------------------------------------------------------------------- [5/7] backups
BAD=0
while read -r f mk from to; do
  b="$FD/$f.bak_S511_$(echo "$from" | cut -c1-8)"
  \cp -p "$FD/$f" "$b" && [ "$(m5 "$b")" = "$from" ] || BAD=1
done < <(rows)
[ "$BAD" = 0 ] || { say "!! [5/7] a backup failed - nothing placed"; clean; exit 1; }
DBBAK="$FINDB.bak_S511_$(date +%Y%m%d_%H%M%S)"
"$SPY_VENV" -B -c "
import sqlite3, sys
a = sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True, timeout=60); b = sqlite3.connect(sys.argv[2])
a.backup(b); b.close(); a.close()
c = sqlite3.connect('file:%s?mode=ro' % sys.argv[2], uri=True); assert c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'; c.close()
" "$FINDB" "$DBBAK" 2>"$SCR/dbbak.err" && chmod 600 "$DBBAK" || { say "!! [5/7] the finance.db backup failed: $(tail -1 "$SCR/dbbak.err" | cut -c1-200) - nothing placed"; rm -f "$DBBAK"; clean; exit 1; }
say "[5/7] backups made: the two files as .bak_S511_<old md5> beside them . finance.db as $(basename "$DBBAK")"

# ------------------------------------------------------------------------------------------- [6/7] place, read back, restart, health
BAD=0
while read -r f mk from to; do
  \cp -p "$FD/$f" "$(dirname "$FD/$f")/.$(basename "$f").s511" && cat "$KDIR/$(basename "$f")" > "$(dirname "$FD/$f")/.$(basename "$f").s511" && [ "$(m5 "$(dirname "$FD/$f")/.$(basename "$f").s511")" = "$to" ] || BAD=1
done < <(rows)
[ "$BAD" = 0 ] || { say "!! [6/7] could not stage the files - nothing placed"; clean; exit 1; }
PLACED=1
while read -r f mk from to; do mv -f "$(dirname "$FD/$f")/.$(basename "$f").s511" "$FD/$f" || restore "placing $f"; done < <(rows)
while read -r f mk from to; do [ "$(m5 "$FD/$f")" = "$to" ] || restore "md5 read-back of $f"; done < <(rows)
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart clinic-finance || restore "clinic-finance restart"
"$SYSTEMCTL" restart clinic-portal || restore "clinic-portal restart"
for _w in 1 2 3 4 5 6 7 8 9 10 11 12; do sleep "$WAIT"; [ "$(health "$FINURL/finance/healthz")" = 200 ] && break; done
post_checks() {
  RED=""
  "$SYSTEMCTL" is-active --quiet clinic-finance || { RED="clinic-finance not active"; return 1; }
  c=$(health "$FINURL/finance/healthz"); [ "$c" = 200 ] || { RED="finance healthz $c"; return 1; }
  "$SYSTEMCTL" is-active --quiet clinic-portal || { RED="clinic-portal not active"; return 1; }
  c=$(health "$PORURL/portal/health"); [ "$c" = 200 ] || { RED="portal health $c"; return 1; }
  c=$(health "$FINURL/finance/clinic/match"); case "$c" in 302|401) ;; *) RED="/finance/clinic/match answered $c without a login"; return 1;; esac
  for u in /finance/packs /finance/packs/api/state /finance/packs/checklist; do
    c=$(health "$FINURL$u"); case "$c" in 302|401) ;; *) RED="$u answered $c without a login (it must be behind the login gate)"; return 1;; esac
  done
  c=$("$CURL" -s -o /dev/null -m 10 -w '%{http_code}' -X POST -H 'Content-Type: application/json' --data-binary '{}' "$FINURL/finance/packs/api/set-aside")
  case "$c" in 302|401|403) ;; *) RED="/finance/packs/api/set-aside answered $c to a POST with no login (it must turn him away)"; return 1;; esac
  JR="$("$JOURNALCTL" -u clinic-finance -u clinic-portal --since "$T0" --no-pager 2>/dev/null | grep -c -i 'Traceback\|ModuleNotFoundError\|ImportError\|SyntaxError\|NameError')"
  [ "${JR:-0}" = 0 ] || { RED="journal: $JR error line(s) since the restart"; return 1; }
  ( cd "$FD/finance" && "$SPY_SVC" -W ignore -B -c "import json, clinic_money; assert hasattr(clinic_money, 'waiting_days'); g = json.load(open('$FD/portal/tile_grants.json')); assert g['version'] == 34 and 'Morning match' in g['users']['reception']['extra']" ) 2>/dev/null \
    || { RED="the placed programs do not load under $SPY_SVC"; return 1; }
  return 0
}
post_checks || restore "$RED"
PLACED=0
say "[6/7] placed; md5 read back = the kit's pins . clinic-finance and clinic-portal restarted (nothing else), active, healthy . Morning match behind the login . journal clean"

# ------------------------------------------------------------------------------------------- [7/7] what reception sees now
( cd "$FD/finance" && FINANCE_DB="$FINDB" "$SPY_SVC" -W ignore -B -c "
import sqlite3, clinic_money as CM
c = sqlite3.connect('$FINDB', timeout=60); c.row_factory = sqlite3.Row
w = CM.waiting_days(c, False)
print('   Morning match, as reception: %d October day(s) still waiting for a first pass%s' % (len(w), (' -- oldest ' + w[0][0]) if w else ''))
" ) 2>&1 | tail -2
say "   the reception login now shows: Docterz daily collection . Morning match . Check karein"
clean
say "all green -- $KIT: DONE.  For the record:"
while read -r f mk from to; do
  g="$(m5 "$FD/$f")"
  if [ "$g" = "$to" ]; then say "   md5 read back  $g  $FD/$f  = the kit's TO pin"; else say "   !! md5 read back  $g  $FD/$f  is NOT the kit's TO pin $to"; fi
done < <(rows)
say "   restarted: clinic-finance and clinic-portal only. Undo: the README's one line."
exit 0
