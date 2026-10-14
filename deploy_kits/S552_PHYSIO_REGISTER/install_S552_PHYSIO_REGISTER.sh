#!/bin/bash
# =============================================================================
#  install_S552_PHYSIO_REGISTER.sh · kit S552 (session 313, 14-Oct-2026) · D646
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S552_PHYSIO_REGISTER/install_S552_PHYSIO_REGISTER.sh
#  (DRY=1 before bash: every gate and the walk, nothing written.)
#
#  THE OWNER, 13-Oct 14:16-14:42 IST and 14-Oct 04:32: Bhati's own physio register -- the clinic's numbered physio slips entered
#  by him and matched against reception's daily figures (differences flagged), and his home visits (Rs 500 a visit, "Payment
#  received", his own money: a separate report, never in the accountants' income).
#   /root/finance/finance_app.py   0d713b14 -> APP_TO   one guarded mount block beside S408's (make_s552.py, 1 counted edit)
#   /root/finance/clinic_money.py  b0408f82 -> CM_TO    one link at the top of the Physiotherapy page (1 counted edit)
#   /root/finance/physio_book.py   NEW                 the register, the home visits, the owner's report, the switch
#  Data step (seed_s552.py, idempotent): four physio_* tables + the one-live-entry-per-slip index; settings physio_book.on = 0,
#  clinic_rate_p 25000, home_rate_p 50000 (INSERT OR IGNORE); unit 'physiobook': bhati maker, manoj + bhawna checker (if absent).
#  NEVER: clinic_physio_day written, a tile granted or withdrawn, packs / day revenue / morning match touched, crontab.
#  Restarts clinic-finance only.
#  ORDER: gates -> pins (ALREADY first) -> compile (both pythons) -> rebuild from the live bytes -> walk on scratch copies
#  (new green; old files red; old clinic_money alone red on the link) -> DRY stops -> backups (db + .bak_S552_<from8>) -> place
#  -> md5 read-back -> data step -> restart -> health 200, three pages 302 -> as manoj on a copy: report + Bhati's page -> undo line.
#  Red after placing: every file put back byte-identically, physio_book.py taken out, restart, health; the db backup stays.
# =============================================================================
set -u
KIT="S552_PHYSIO_REGISTER"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"                      # the service's python
VPY="${VPY:-/root/wa/venv/bin/python3}"             # the jobs' python: every file must compile on both
FIN="${FIN:-/root/finance}"
POR="${POR:-/root/portal}"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
EDITED="finance_app.py clinic_money.py"
declare -A FROM TO
FROM[finance_app.py]=0d713b14570384e0de07ac93a3b113db;  TO[finance_app.py]=87cc4266f9cd05f3633f23e1f36488a0
FROM[clinic_money.py]=b0408f82ec104e2170ccc069d0ec6450; TO[clinic_money.py]=0a2085ca5392646521fc9796485ae5f0
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s552_inst_$STAMP"
HAVE_LOCK=0; PLACED=0
DBBAK="$FIN/finance.db.bak_S552_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S552_${FROM[$1]:0:8}"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; rm -rf "$SCR"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting every file back"
  for n in $EDITED; do [ -f "$(bak $n)" ] && \cp -p "$(bak $n)" "$FIN/$n"; done
  rm -f "$FIN/physio_book.py" "$FIN"/.*.s552
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"); [ "$h" = 200 ] && break; done
  for n in $EDITED; do say "   $FIN/$n $(m5 "$FIN/$n") (expected ${FROM[$n]})"; done
  say "   physio_book.py present: $([ -f "$FIN/physio_book.py" ] && echo yes || echo no) · healthz $h"
  say "   the database backup stays: $DBBAK (the new physio_* tables and physiobook rows, if made, are additive and unused without the module)"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl timeout grep tail sleep find; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
command -v "$SYSTEMCTL" >/dev/null 2>&1 || { say "!! preflight: $SYSTEMCTL missing - nothing installed"; exit 1; }
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/9] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/9] KIT_ID.txt names another kit - nothing installed"; exit 1; }
if [ "${LOCK_HELD:-0}" = 1 ]; then
  grep -q "$KIT" "$LOCK/owner" 2>/dev/null || { say "!! [1/9] LOCK_HELD=1 but $LOCK/owner does not name $KIT - nothing installed"; exit 3; }
else
  mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
  if [ "$HAVE_LOCK" != 1 ]; then
    say "!! [1/9] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Paste the line again when it is free."
    exit 3
  fi
  echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
fi
say "[1/9] kit gates green; the build lock is ours"

KPB="$(m5 physio_book.py)"
for n in $EDITED; do [ -f "$FIN/$n" ] || { say "!! [2/9] $FIN/$n is not there - nothing installed"; exit 1; }; done
if [ "$(m5 "$FIN/finance_app.py")" = "${TO[finance_app.py]}" ] && [ "$(m5 "$FIN/clinic_money.py")" = "${TO[clinic_money.py]}" ] && [ "$(m5 "$FIN/physio_book.py")" = "$KPB" ]; then
  say "-- ALREADY INSTALLED: finance_app.py, clinic_money.py and physio_book.py are the kit's. Nothing written."; exit 0
fi
for n in $EDITED; do C="$(m5 "$FIN/$n")"; [ "$C" = "${FROM[$n]}" ] || { say "!! [2/9] $FIN/$n is $C, expected ${FROM[$n]} - STOP, nothing installed"; exit 1; }; done
if [ -e "$FIN/physio_book.py" ] && [ "$(m5 "$FIN/physio_book.py")" != "$KPB" ]; then say "!! [2/9] $FIN/physio_book.py exists and is not this kit's - STOP, nothing installed"; exit 1; fi
[ -f "$DB" ] || { say "!! [2/9] $DB is not there - nothing installed"; exit 1; }
[ -f "$POR/portal.py" ] && [ -f "$POR/tile_grants.json" ] || { say "!! [2/9] $POR/portal.py or tile_grants.json missing (the staff-eye walk reads them) - nothing installed"; exit 1; }
say "[2/9] live pins exact (finance_app 0d713b14, clinic_money b0408f82); physio_book.py not yet there"

mkdir -p "$SCR/built" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONDONTWRITEBYTECODE=1
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile physio_book.py make_s552.py seed_s552.py walk_s552.py probe_s552.py \
    || { say "!! [3/9] compile failed on $py - nothing installed"; exit 1; }
done
say "[3/9] the kit's five python files compile on $APY and $VPY"

"$APY" -B make_s552.py "$FIN/finance_app.py" "$SCR/built/finance_app.py" "$FIN/clinic_money.py" "$SCR/built/clinic_money.py" >/dev/null \
  || { say "!! [4/9] the builder refused a live file - nothing installed"; exit 1; }
for n in $EDITED; do
  [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || { say "!! [4/9] rebuilt from the live bytes, $n is $(m5 "$SCR/built/$n"), not ${TO[$n]} - nothing installed"; exit 1; }
done
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/finance_app.py" "$SCR/built/clinic_money.py" || { say "!! [4/9] a rebuilt file does not compile on $py - nothing installed"; exit 1; }
done
say "[4/9] rebuilt from the live bytes (1 + 1 counted edits): finance_app ${TO[finance_app.py]:0:8}, clinic_money ${TO[clinic_money.py]:0:8} - compile on both pythons"

mkscratch() {   # $1 = side folder: a copy of the live finance code (never the database, never a backup)
  mkdir -p "$1/finance_ui" "$1/spine"
  cp -p "$FIN"/*.py "$1/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$1/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$1/finance_ui/" 2>/dev/null; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$1/spine/" 2>/dev/null
  return 0
}
for side in new old mix; do mkscratch "$SCR/$side"; copydb "$DB" "$SCR/$side.db" || { say "!! [5/9] no scratch copy of the database - nothing installed"; exit 1; }; done
cp -p "$SCR/built/finance_app.py" "$SCR/built/clinic_money.py" physio_book.py "$SCR/new/"
cp -p "$SCR/built/finance_app.py" physio_book.py "$SCR/mix/"        # mix: everything new except clinic_money.py (the old one)
mkdir -p "$SCR/por"; for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$SCR/por/"; done; cp -p "$POR/tile_grants.json" "$SCR/por/"
WOUT="$( cd /tmp && timeout 900 "$APY" -B "$KDIR/walk_s552.py" --fin "$SCR/new" --db "$SCR/new.db" --portal "$SCR/por" --kit "$KDIR" 2>&1 )"; WRC=$?
ROUT="$( cd /tmp && timeout 900 "$APY" -B "$KDIR/walk_s552.py" --fin "$SCR/old" --db "$SCR/old.db" --portal "$SCR/por" --kit "$KDIR" --expect-red 2>&1 )"; RRC=$?
MOUT="$( cd /tmp && timeout 900 "$APY" -B "$KDIR/walk_s552.py" --fin "$SCR/mix" --db "$SCR/mix.db" --portal "$SCR/por" --kit "$KDIR" --expect-red 2>&1 )"; MRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | sed 's/^/   /'
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK"; then say "!! [5/9] the walk is RED on this box (exit $WRC) - nothing installed"; exit 1; fi
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK negative control"; then say "!! [5/9] the negative control did not go red on the old files - the walk proves nothing; nothing installed"; echo "$ROUT" | tail -5; exit 1; fi
if [ "$MRC" != 0 ] || ! echo "$MOUT" | grep -q "^WALK OK negative control"; then say "!! [5/9] the old clinic_money.py alone did not go red on the link - nothing installed"; echo "$MOUT" | tail -5; exit 1; fi
say "[5/9] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "      negative control, the old files: $(echo "$ROUT" | grep "^WALK OK" | tail -1 | cut -c27-)"
say "      negative control, only clinic_money.py old: $(echo "$MOUT" | grep "^WALK OK" | tail -1 | cut -c27-)"
rm -rf "$SCR/old" "$SCR/mix" "$SCR"/*.db
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

copydb "$DB" "$DBBAK" || { say "!! [6/9] database backup failed - nothing placed"; exit 1; }
for n in $EDITED; do
  \cp -p "$FIN/$n" "$(bak $n)" || { say "!! [6/9] backup of $n failed - nothing placed"; exit 1; }
  [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ] || { say "!! [6/9] the backup of $n is not the live file - nothing placed"; exit 1; }
done
say "[6/9] backups: $(basename "$DBBAK") (sqlite backup API); $(basename "$(bak finance_app.py)"), $(basename "$(bak clinic_money.py)")"

for n in $EDITED; do \cp -p "$SCR/built/$n" "$FIN/.$n.s552" || { rm -f "$FIN"/.*.s552; say "!! [7/9] could not stage $n - nothing placed"; exit 1; }; done
\cp -p physio_book.py "$FIN/.physio_book.py.s552" || { rm -f "$FIN"/.*.s552; say "!! [7/9] could not stage physio_book.py - nothing placed"; exit 1; }
PLACED=1
mv -f "$FIN/.physio_book.py.s552" "$FIN/physio_book.py" || restore "placing physio_book.py"
chmod 644 "$FIN/physio_book.py"
for n in $EDITED; do mv -f "$FIN/.$n.s552" "$FIN/$n" || restore "placing $n"; done
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || restore "$n did not land at its pin"; done
[ "$(m5 "$FIN/physio_book.py")" = "$KPB" ] || restore "physio_book.py did not land at the kit's md5"
say "[7/9] placed; md5 read back: finance_app $(m5 "$FIN/finance_app.py") · clinic_money $(m5 "$FIN/clinic_money.py") · physio_book $(m5 "$FIN/physio_book.py")"

SOUT="$("$APY" -B seed_s552.py "$DB" "$KDIR/physio_book.py" 2>&1)" || { echo "$SOUT"; restore "the data step"; }
say "[8/9] $SOUT"

"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"); [ "$c1" = 200 ] && break; done
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/physio/book")
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/physio/book/report")
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/physio/book/home/1")
c5=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/physio")
"$SYSTEMCTL" is-active --quiet "$SVC" || restore "$SVC is not active"
{ [ "$c1" = 200 ] && [ "$c2" = 302 ] && [ "$c3" = 302 ] && [ "$c4" = 302 ] && [ "$c5" = 302 ]; } \
  || restore "health $c1 / register $c2 / report $c3 / home page $c4 / physiotherapy page $c5 (302 expected without a login)"
MF=""
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  MF="$("$JOURNALCTL" -u "$SVC" --since "-3 min" --no-pager 2>/dev/null | grep -E "(physio_book|clinic_money) NOT mounted" | head -1)"
fi
[ -z "$MF" ] || restore "a module did not mount: $MF"
mkscratch "$SCR/placed"; copydb "$DB" "$SCR/placed.db" || restore "no copy of the database for the look as manoj"
POUT="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/probe_s552.py" --fin "$SCR/placed" --db "$SCR/placed.db" 2>&1 )"; PRC=$?
echo "$POUT" | sed 's/^/   /'
[ "$PRC" = 0 ] && echo "$POUT" | grep -q "^PROBE OK" || restore "the look as manoj on a copy is red"
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0
say "[9/9] $SVC restarted and active - health $c1 - /finance/physio/book $c2, /report $c3, /home/1 $c4, /finance/physio $c5 without a login (302 = the login gate, expected) - physio_book mounted"
for n in $EDITED physio_book.py; do md5sum "$FIN/$n"; done
say "$KIT: DONE - installed SWITCHED OFF for Bhati (physio_book.on = 0); the doctors see it now"
say "read next: https://followup.dr-manoj.in/finance/physio/book/report"
say "undo: \\cp -p $(bak finance_app.py) $FIN/finance_app.py && \\cp -p $(bak clinic_money.py) $FIN/clinic_money.py && rm -f $FIN/physio_book.py && $SYSTEMCTL restart $SVC"
