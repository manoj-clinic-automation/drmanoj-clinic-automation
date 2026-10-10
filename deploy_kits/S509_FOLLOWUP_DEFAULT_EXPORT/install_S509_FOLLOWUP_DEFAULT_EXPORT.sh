#!/bin/bash
# =============================================================================
# install_S509_FOLLOWUP_DEFAULT_EXPORT.sh -- session 304 (parent), 10-Oct-2026 -- the follow-up log exported as Docterz shows it
#  THE OWNER, 10-Oct 22:38: "we simply open the follow-up logs in Docterz and it shows the default from date as the current date
#  until one month and we export it as such ... no date fields need to be altered while exporting the follow-up logs."
#  EDITED, each gated on the md5 of the file it replaces (S507's bytes, live since 10-Oct 22:3x IST), built by make_s509.py:
#     /root/finance/docterz_pickup.py  b54ce6af -> a follow-up log's day is the IST day it was EXPORTED (before 13:00: the
#                                                  previous working day, the morning catch-up), not its earliest due date
#                                                  minus one -- so Docterz's default export (today .. one month) is tonight's log
#     /root/finance/aaj_seed.py        bb6bf911 -> the hint under reception's two lines: leave Docterz's dates as they are
#  READ, NOT CHANGED (pinned): aaj_duties.json 2d6d30eb (S507) . aaj_kaam.py cd232b1c (S508). No data step: the logs already
#  kept keep their day. Restarts clinic-finance ONLY. Walked first on a scratch copy (walk_s509.py, made-up logs dated 2031);
#  the SAME walk on the live files must end RED.
#   FD  FINDB  FINURL  LOCK  TMPBASE  SPY_SVC  SPY_VENV  SYSTEMCTL  CURL  JOURNALCTL  WAIT
# =============================================================================
set -u
KIT="S509_FOLLOWUP_DEFAULT_EXPORT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
FD="${FD:-/root/finance}"
FINDB="${FINDB:-/root/finance/finance.db}"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
TMPBASE="${TMPBASE:-/tmp}"
SPY_SVC="${SPY_SVC:-/usr/bin/python3}"
SPY_VENV="${SPY_VENV:-/root/wa/venv/bin/python3}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
CURL="${CURL:-curl}"
JOURNALCTL="${JOURNALCTL:-journalctl}"
WAIT="${WAIT:-3}"
TABLE="docterz_pickup.py|make_s509.py|b54ce6af3bb597cfc7942f6231962cf2|f8cb978e8d29a03d931b4e4a2d01ce6e
aaj_seed.py|make_s509.py|bb6bf911e87622ef410814a7952990ac|156ded1ee17b852b4a30e94be453ca61"
READPINS="aaj_duties.json|2d6d30ebe73ff721d5591743c86eebb1
aaj_kaam.py|cd232b1c987417aa07d341d498c5effc"
SCR=""; PLACED=0; HAVE_LOCK=0; T0=""; RED=""; DBBAK=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { "$CURL" -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
rows() { echo "$TABLE" | while IFS='|' read -r f mk from to; do echo "$f $mk $from $to"; done; }
clean() {
  [ -n "$SCR" ] && rm -rf "$SCR"
  rows | while read -r f mk from to; do rm -f "$FD/.$f.s509"; done
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
}
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - restoring"
  PLACED=0
  rows | while read -r f mk from to; do
    \cp -p "$FD/$f.bak_S509_$(echo "$from" | cut -c1-8)" "$FD/$f"
    if [ "$(m5 "$FD/$f")" = "$from" ]; then say "   $f back at its old bytes ($from)"; else say "   !! $f is NOT its old bytes - put its .bak_S509_ copy back by hand"; fi
  done
  "$SYSTEMCTL" restart clinic-finance 2>/dev/null || true
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
while read -r f mk from to; do [ "$(m5 "$f")" = "$to" ] || { say "!! [1/7] the kit's $f is not the one this installer names"; BAD=1; }; done < <(rows)
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
say "[2/7] the two files, and aaj_duties.json and aaj_kaam.py beside them, are at the pins this kit was built on"
mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
if [ "$HAVE_LOCK" != 1 ]; then
  say "!! [2/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
SCR="$(mktemp -d "$TMPBASE/s509_scratch_XXXXXXXX")" || { say "!! [2/7] no scratch folder - nothing installed"; exit 1; }
chmod 700 "$SCR"

# ------------------------------------------------------------------------------------------- [3/7] compile; rebuild from the live bytes
for p in "$SPY_SVC" "$SPY_VENV"; do
  ( cd "$KDIR" && "$p" -W ignore -B -c "
for f in ('docterz_pickup.py', 'aaj_seed.py', 'walk_s509.py', 'make_s509.py'):
    compile(open(f, encoding='utf-8').read(), f, 'exec')
" ) 2>"$SCR/compile.err" || { say "!! [3/7] compile failed under $p: $(tail -1 "$SCR/compile.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
done
BAD=0
( cd "$SCR" && "$SPY_VENV" -W ignore -B "$KDIR/make_s509.py" "$FD" "$SCR/rb" ) >"$SCR/make.out" 2>&1 || { say "!! [3/7] the builder refused on this box's live bytes: $(tail -1 "$SCR/make.out" | cut -c1-200)"; BAD=1; }
while read -r f mk from to; do
  [ "$(m5 "$SCR/rb/$f")" = "$to" ] || { say "!! [3/7] $f rebuilt here from this box's live bytes is NOT the kit's"; BAD=1; }
done < <(rows)
[ "$BAD" = 0 ] || { say "   nothing installed"; clean; exit 1; }
say "[3/7] the kit compiles under $SPY_SVC and $SPY_VENV; rebuilt here from this box's live bytes, each of the two is the kit's file, byte for byte"

# ------------------------------------------------------------------------------------------- [4/7] the walk, and its control
unchanged() { while read -r f mk from to; do [ "$(m5 "$FD/$f")" = "$from" ] || return 1; done < <(rows); return 0; }
WOUT="$( cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 timeout 1200 "$WPY" -W ignore -B "$KDIR/walk_s509.py" --kit "$KDIR" --fin "$FD" --db "$FINDB" --venv "$SPY_VENV" 2>&1 )"
echo "$WOUT" | grep -E '^  |^WALK_S509' | cut -c1-200 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S509 GREEN" || { say "!! [4/7] the walk is red - nothing installed. Tell the assistant with this output."; echo "$WOUT" | tail -15 | cut -c1-300; clean; exit 1; }
COUT="$( cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 timeout 1200 "$WPY" -W ignore -B "$KDIR/walk_s509.py" --kit "$KDIR" --fin "$FD" --db "$FINDB" --venv "$SPY_VENV" --control 2>&1 | tail -1 )"
echo "$COUT" | grep -q "^WALK_S509 RED" || { say "!! [4/7] the SAME walk on the live files did not go red ($COUT): it cannot tell old from new - nothing installed."; clean; exit 1; }
unchanged || { say "!! [4/7] a live file changed during the walk - nothing installed"; clean; exit 1; }
say "[4/7] walked on a scratch copy of finance.db: $(echo "$WOUT" | tail -1) . the same walk on the live files: $(echo "$COUT" | cut -c1-90)... (the negative control)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

# ------------------------------------------------------------------------------------------- [5/7] backups
BAD=0
while read -r f mk from to; do
  b="$FD/$f.bak_S509_$(echo "$from" | cut -c1-8)"
  \cp -p "$FD/$f" "$b" && [ "$(m5 "$b")" = "$from" ] || BAD=1
done < <(rows)
[ "$BAD" = 0 ] || { say "!! [5/7] a backup failed - nothing placed"; clean; exit 1; }
DBBAK="$FINDB.bak_S509_$(date +%Y%m%d_%H%M%S)"
"$SPY_VENV" -B -c "
import sqlite3, sys
a = sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True, timeout=60); b = sqlite3.connect(sys.argv[2])
a.backup(b); b.close(); a.close()
c = sqlite3.connect('file:%s?mode=ro' % sys.argv[2], uri=True); assert c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'; c.close()
" "$FINDB" "$DBBAK" 2>"$SCR/dbbak.err" && chmod 600 "$DBBAK" || { say "!! [5/7] the finance.db backup failed: $(tail -1 "$SCR/dbbak.err" | cut -c1-200) - nothing placed"; rm -f "$DBBAK"; clean; exit 1; }
say "[5/7] backups made: the two files as .bak_S509_<old md5> beside them . finance.db as $(basename "$DBBAK")"

# ------------------------------------------------------------------------------------------- [6/7] place, read back, restart, health
BAD=0
while read -r f mk from to; do
  \cp -p "$FD/$f" "$FD/.$f.s509" && cat "$KDIR/$f" > "$FD/.$f.s509" && [ "$(m5 "$FD/.$f.s509")" = "$to" ] || BAD=1
done < <(rows)
[ "$BAD" = 0 ] || { say "!! [6/7] could not stage the files - nothing placed"; clean; exit 1; }
PLACED=1
while read -r f mk from to; do mv -f "$FD/.$f.s509" "$FD/$f" || restore "placing $f"; done < <(rows)
while read -r f mk from to; do [ "$(m5 "$FD/$f")" = "$to" ] || restore "md5 read-back of $f"; done < <(rows)
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart clinic-finance || restore "clinic-finance restart"
for _w in 1 2 3 4 5 6 7 8 9 10 11 12; do sleep "$WAIT"; [ "$(health "$FINURL/finance/healthz")" = 200 ] && break; done
post_checks() {
  RED=""
  "$SYSTEMCTL" is-active --quiet clinic-finance || { RED="clinic-finance not active"; return 1; }
  c=$(health "$FINURL/finance/healthz"); [ "$c" = 200 ] || { RED="finance healthz $c"; return 1; }
  for u in /finance/packs /finance/packs/api/state /finance/packs/checklist; do
    c=$(health "$FINURL$u"); case "$c" in 302|401) ;; *) RED="$u answered $c without a login (it must be behind the login gate)"; return 1;; esac
  done
  c=$("$CURL" -s -o /dev/null -m 10 -w '%{http_code}' -X POST -H 'Content-Type: application/json' --data-binary '{}' "$FINURL/finance/packs/api/set-aside")
  case "$c" in 302|401|403) ;; *) RED="/finance/packs/api/set-aside answered $c to a POST with no login (it must turn him away)"; return 1;; esac
  JR="$("$JOURNALCTL" -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c -i 'Traceback\|ModuleNotFoundError\|ImportError\|SyntaxError\|NameError')"
  [ "${JR:-0}" = 0 ] || { RED="journal: $JR error line(s) since the restart"; return 1; }
  ( cd "$FD" && "$SPY_SVC" -W ignore -B -c "import docterz_pickup, aaj_seed, aaj_kaam; assert hasattr(docterz_pickup, 'export_day') and 'date badalne ki zaroorat nahin' in aaj_seed.ENGINE['reception.night_exports']['how']" ) 2>/dev/null \
    || { RED="the placed programs do not load under $SPY_SVC"; return 1; }
  return 0
}
post_checks || restore "$RED"
PLACED=0
say "[6/7] placed; md5 read back = the kit's pins . clinic-finance restarted (nothing else), active, healthz 200 . the packs pages behind the login . the set-aside door still turns a stranger away . journal clean"

# ------------------------------------------------------------------------------------------- [7/7] what reception reads now
( cd "$FD" && "$SPY_SVC" -W ignore -B -c "
import aaj_seed
print('   reception reads under the two lines: ' + aaj_seed.ENGINE['reception.night_exports']['how'][:160])
" ) 2>&1 | tail -2
clean
say "all green -- $KIT: DONE.  For the record:"
while read -r f mk from to; do
  g="$(m5 "$FD/$f")"
  if [ "$g" = "$to" ]; then say "   md5 read back  $g  $FD/$f  = the kit's TO pin"; else say "   !! md5 read back  $g  $FD/$f  is NOT the kit's TO pin $to"; fi
done < <(rows)
say "   restarted: clinic-finance only. Undo: the README's one line."
exit 0
