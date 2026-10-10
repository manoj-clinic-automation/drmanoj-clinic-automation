#!/bin/bash
# =============================================================================
# install_S503_PACKS_STATEMENTS.sh -- session 304 (parent), 10-Oct-2026 -- the statements and packs page (Club A)
#  THE OWNER, 09/10-Oct: the Yes Bank statements are in the mail and the passwords are right, yet they are not read;
#  "seven locked statements which I do not know"; "a field to set their password in our own page so that we are not
#  dependent upon any external source"; ICICI "shd read both types, branch and system and store and display both
#  together, and use any one for accountant and amir packs"; the quarterly statement "is not required".
#  WHOLE-FILE REPLACEMENTS, each gated on the md5 of the file it replaces (the 10-Oct 01:35 bundle's bytes):
#     /root/finance/yes_monthly.py  a4270bb3 -> also reads Yes Bank's CONSOLIDATED monthly e-statement (all accounts of
#                                              one customer in one PDF, withdrawals-first or deposits-first columns)
#     /root/finance/packs.py        9f897eeb -> a password box per ICICI account and per card; every closed locked file
#                                              named in words; 'set aside' / 'put back'; a refusal is retried by itself
#                                              when a reader is newer; ICICI's two kinds of copy kept and shown together,
#                                              a line never written twice; a card original opened by the shelf itself
#     /root/finance/packs.html      73ff8c2f -> the page: the locked files by name with 'Set aside -- not needed', the
#                                              set-aside list with 'put back', 'also on the shelf' under each account
#     /root/finance/stmt_shelf.py   52a5fb07 -> leaves set-aside files alone; fetches All_Transactions.xlsx again
#                                              whenever Drive's copy changed
#  READ, NOT CHANGED (pinned): yes_branch.py e06ff505 . finance_yesbank.py 01b70e2b . finance_icici.py 7ace56b7
#  ONE-TIME DATA STEP, after a green placing: the Yes Bank quarterly statement (file 124, if it is still the closed
#  quarterly) is set aside in the owner's name; then the 05:40 cron line's own command runs once, so the five refused
#  Yes Bank statements are read now, not tomorrow. finance.db is backed up first (sqlite backup API).
# Walked first, on this box (walk_s503.py): a scratch copy of finance.db, the kit's four over a scratch copy of
# /root/finance, process_inbox as the cron runs it, then the page's routes signed in as the doctor; the SAME walk on
# the live files must end RED (negative control). Restarts clinic-finance ONLY. Red after placing -> the four files
# are put back byte for byte, clinic-finance restarted, health confirmed, exit 1.
# DRY=1 places nothing.  NEEDS the build lock free (F-694).
# Every path and command can be given by the environment:
#   FD  FINDB  FINURL  LOCK  TMPBASE  SPY_SVC  SPY_VENV  SYSTEMCTL  CURL  JOURNALCTL  WAIT
# =============================================================================
set -u
KIT="S503_PACKS_STATEMENTS"
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
TABLE="yes_monthly.py|make_yes_monthly.py|a4270bb3aa12f7c6235167a8cd86a0b3|366f3032252d9a3a4bd47b2a9a1af45c
packs.py|make_packs.py|9f897eeb70bc65d1414985058e378310|484dce36777aa8e5e9afeb22fc7ba143
packs.html|make_packs_html.py|73ff8c2f06a6e070c0ff293afb2e3ff6|c857718c75b594f30419220f5a535432
stmt_shelf.py|make_stmt_shelf.py|52a5fb07339e12d6a875b6fbdb6acddc|78549727848fdb670ff1ebc7724bded9"
READPINS="yes_branch.py|e06ff5055c2927545701cd6cf8985ed4
finance_yesbank.py|01b70e2b67bb70fde55e9dbfdf16b0ba
finance_icici.py|7ace56b77cd87d29352acb2d0f6cbe48"
SCR=""; PLACED=0; HAVE_LOCK=0; T0=""; RED=""; DBBAK=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { "$CURL" -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
rows() { echo "$TABLE" | while IFS='|' read -r f mk from to; do echo "$f $mk $from $to"; done; }
clean() {
  [ -n "$SCR" ] && rm -rf "$SCR"
  rows | while read -r f mk from to; do rm -f "$FD/.$f.s503"; done
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
}
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - restoring"
  PLACED=0
  rows | while read -r f mk from to; do
    \cp -p "$FD/$f.bak_S503_$(echo "$from" | cut -c1-8)" "$FD/$f"
    if [ "$(m5 "$FD/$f")" = "$from" ]; then say "   $f back at its old bytes ($from)"; else say "   !! $f is NOT its old bytes - put its .bak_S503_ copy back by hand"; fi
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
"$SPY_VENV" -c "import pypdf" 2>/dev/null || { say "!! [1/7] pypdf is not under $SPY_VENV (the shelf opens the locked files with it) - nothing installed"; exit 1; }
say "[1/7] kit gates green (SUMS, KIT_ID, each file's own md5; the walk runs under $WPY; pypdf under the venv)"

# ------------------------------------------------------------------------------------------- [2/7] the live files' pins
ALL_TO=1; BAD=0
while read -r f mk from to; do
  h="$(m5 "$FD/$f")"
  [ "$h" = "$to" ] || ALL_TO=0
  [ "$h" = "$from" ] || [ "$h" = "$to" ] || { say "!! [2/7] $FD/$f is ${h:-not there}, not $from - it changed after this kit was built."; BAD=1; }
done < <(rows)
if [ "$ALL_TO" = 1 ]; then
  say "-- ALREADY INSTALLED: the four files are at the kit's pins; nothing changed. clinic-finance $("$SYSTEMCTL" is-active clinic-finance 2>/dev/null)"
  clean; exit 0
fi
while IFS='|' read -r f pin; do
  [ "$(m5 "$FD/$f")" = "$pin" ] || { say "!! [2/7] $FD/$f is $(m5 "$FD/$f"), not $pin - this kit was built reading that file."; BAD=1; }
done < <(echo "$READPINS")
while read -r f mk from to; do [ "$(m5 "$FD/$f")" = "$from" ] || { say "!! [2/7] $FD/$f is half-way (neither the old nor the new bytes)"; BAD=1; }; done < <(rows)
[ "$BAD" = 0 ] || { say "   REFUSED: nothing placed, nothing restarted. Tell the assistant; the kit is rebuilt on the new file."; clean; exit 1; }
say "[2/7] the four files, and the three readers beside them, are at the pins this kit was built on"
mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
if [ "$HAVE_LOCK" != 1 ]; then
  say "!! [2/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
SCR="$(mktemp -d "$TMPBASE/s503_scratch_XXXXXXXX")" || { say "!! [2/7] no scratch folder - nothing installed"; exit 1; }
chmod 700 "$SCR"

# ------------------------------------------------------------------------------------------- [3/7] compile; rebuild from the live bytes
for p in "$SPY_SVC" "$SPY_VENV"; do
  ( cd "$KDIR" && "$p" -W ignore -B -c "
for f in ('yes_monthly.py', 'packs.py', 'stmt_shelf.py', 'walk_s503.py', 'make_yes_monthly.py', 'make_packs.py', 'make_packs_html.py', 'make_stmt_shelf.py'):
    compile(open(f, encoding='utf-8').read(), f, 'exec')
" ) 2>"$SCR/compile.err" || { say "!! [3/7] compile failed under $p: $(tail -1 "$SCR/compile.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
done
BAD=0
while read -r f mk from to; do
  ( cd "$SCR" && "$SPY_VENV" -W ignore -B "$KDIR/$mk" "$FD/$f" "$SCR/rb_$f" ) >"$SCR/make.out" 2>&1 && [ "$(m5 "$SCR/rb_$f")" = "$to" ] \
    || { say "!! [3/7] $f rebuilt here from this box's live bytes is NOT the kit's: $(tail -1 "$SCR/make.out" | cut -c1-200)"; BAD=1; }
done < <(rows)
[ "$BAD" = 0 ] || { say "   nothing installed"; clean; exit 1; }
say "[3/7] the kit compiles under $SPY_SVC and $SPY_VENV; rebuilt here from this box's live bytes, each of the four is the kit's file, byte for byte"

# ------------------------------------------------------------------------------------------- [4/7] the walk, and its control
unchanged() { while read -r f mk from to; do [ "$(m5 "$FD/$f")" = "$from" ] || return 1; done < <(rows); return 0; }
WOUT="$( cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 timeout 1200 "$WPY" -W ignore -B "$KDIR/walk_s503.py" --kit "$KDIR" --fin "$FD" --db "$FINDB" --venv "$SPY_VENV" 2>&1 )"
echo "$WOUT" | grep -E '^  |^WALK_S503' | cut -c1-200 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S503 GREEN" || { say "!! [4/7] the walk is red - nothing installed. Tell the assistant with this output."; echo "$WOUT" | tail -15 | cut -c1-300; clean; exit 1; }
COUT="$( cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 timeout 1200 "$WPY" -W ignore -B "$KDIR/walk_s503.py" --kit "$KDIR" --fin "$FD" --db "$FINDB" --venv "$SPY_VENV" --control 2>&1 | tail -1 )"
echo "$COUT" | grep -q "^WALK_S503 RED" || { say "!! [4/7] the SAME walk on the live files did not go red ($COUT): it cannot tell old from new - nothing installed."; clean; exit 1; }
unchanged || { say "!! [4/7] a live file changed during the walk - nothing installed"; clean; exit 1; }
say "[4/7] walked on a scratch copy of finance.db: $(echo "$WOUT" | tail -1) . the same walk on the live files: $(echo "$COUT" | cut -c1-90)... (the negative control)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

# ------------------------------------------------------------------------------------------- [5/7] backups
BAD=0
while read -r f mk from to; do
  b="$FD/$f.bak_S503_$(echo "$from" | cut -c1-8)"
  \cp -p "$FD/$f" "$b" && [ "$(m5 "$b")" = "$from" ] || BAD=1
done < <(rows)
[ "$BAD" = 0 ] || { say "!! [5/7] a backup failed - nothing placed"; clean; exit 1; }
DBBAK="$FINDB.bak_S503_$(date +%Y%m%d_%H%M%S)"
"$SPY_VENV" -B -c "
import sqlite3, sys
a = sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True, timeout=60); b = sqlite3.connect(sys.argv[2])
a.backup(b); b.close(); a.close()
c = sqlite3.connect('file:%s?mode=ro' % sys.argv[2], uri=True); assert c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'; c.close()
" "$FINDB" "$DBBAK" 2>"$SCR/dbbak.err" && chmod 600 "$DBBAK" || { say "!! [5/7] the finance.db backup failed: $(tail -1 "$SCR/dbbak.err" | cut -c1-200) - nothing placed"; rm -f "$DBBAK"; clean; exit 1; }
say "[5/7] backups made: the four files as .bak_S503_<old md5> beside them . finance.db as $(basename "$DBBAK")"

# ------------------------------------------------------------------------------------------- [6/7] place, read back, restart, health
BAD=0
while read -r f mk from to; do
  \cp -p "$FD/$f" "$FD/.$f.s503" && cat "$KDIR/$f" > "$FD/.$f.s503" && [ "$(m5 "$FD/.$f.s503")" = "$to" ] || BAD=1
done < <(rows)
[ "$BAD" = 0 ] || { say "!! [6/7] could not stage the files - nothing placed"; clean; exit 1; }
PLACED=1
while read -r f mk from to; do mv -f "$FD/.$f.s503" "$FD/$f" || restore "placing $f"; done < <(rows)
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
  ( cd "$FD" && "$SPY_SVC" -W ignore -B -c "import packs, stmt_shelf, yes_monthly; assert packs.SET_ASIDE == 'set aside' and hasattr(packs, 'set_aside') and hasattr(yes_monthly, 'CONS_HEAD_RE')" ) 2>/dev/null \
    || { RED="the placed programs do not load under $SPY_SVC"; return 1; }
  return 0
}
post_checks || restore "$RED"
PLACED=0
say "[6/7] placed; md5 read back = the kit's pins . clinic-finance restarted (nothing else), active, healthz 200 . the packs pages behind the login . the new set-aside door turns a stranger away . journal clean"

# ------------------------------------------------------------------------------------------- [7/7] the one-time data step
( cd "$FD" && FINANCE_DB="$FINDB" "$SPY_SVC" -W ignore -B -c "
import sqlite3, packs
c = sqlite3.connect('$FINDB', timeout=60)
r = c.execute('SELECT id, name, folder, locked, unlocked_path, read_status FROM stmt_file WHERE id=124').fetchone()
if r and packs._copy_kind(r[1], r[2]) == 'Yes Bank quarterly statement' and r[3] and not r[4] and r[5] != packs.SET_ASIDE:
    b, code = packs.set_aside(c, 124, False, 'manoj (said in chat 09-Oct; set by the S503 installer)', 'quarterly not required -- the monthly statements carry it')
    print('   file 124, the Yes Bank quarterly statement: %s' % ('set aside' if b.get('ok') else 'NOT set aside (%s)' % b.get('error')))
else:
    print('   file 124: left as it is (%s)' % ('already set aside' if r and r[5] == packs.SET_ASIDE else 'not the closed quarterly statement' if r else 'not on the shelf'))
" ) 2>&1 | tail -2
say "   running the 05:40 cron line's own command once (fetch + read), so the refused statements are read now ..."
( cd "$FD" && FINANCE_DIR="$FD" FINANCE_DB="$FINDB" timeout 900 "$SPY_VENV" -B "$FD/stmt_shelf.py" run >> "$FD/stmt_shelf.log" 2>&1 ); RC=$?
say "   stmt_shelf.py run: exit $RC (its lines are in $FD/stmt_shelf.log)"
( cd "$FD" && FINANCE_DB="$FINDB" "$SPY_SVC" -W ignore -B -c "
import sqlite3, packs
c = sqlite3.connect('$FINDB', timeout=60); c.row_factory = sqlite3.Row
m = packs._prev_month(packs._today().strftime('%Y-%m'))
s = packs.secret_state(c)
ref = c.execute(\"SELECT COUNT(*) FROM stmt_file WHERE read_status LIKE 'refused%'\").fetchone()[0]
print('   the shelf now: %d refused . %d locked file(s) waiting for a password, each named on the page . %d set aside' % (ref, len(s['locked_files']), len(s['set_aside'])))
print('   %s, account by account:' % packs._month_name(m))
for x in packs.cells(c, m):
    print('     %-48s %s%s' % ((x.get('label') or '')[:48], x.get('state') or '', (' . also on the shelf: %d' % len(x['copies'])) if x.get('copies') else ''))
" ) 2>&1 | tail -25
clean
say "all green -- $KIT: DONE.  For the record:"
while read -r f mk from to; do
  g="$(m5 "$FD/$f")"
  if [ "$g" = "$to" ]; then say "   md5 read back  $g  $FD/$f  = the kit's TO pin"; else say "   !! md5 read back  $g  $FD/$f  is NOT the kit's TO pin $to"; fi
done < <(rows)
say "   restarted: clinic-finance only. Undo: the README's one line."
exit 0
