#!/bin/bash
# =============================================================================
#  install_S689_CLINIC_LISTS.sh · kit S689 (01-Nov-2026, the parent, session 373) · D812: the owner's X-ray & procedures page
#  One page for Dr Manoj alone: the procedures list and the X-ray list from 1-Oct-2026, amounts, a month or a from-to range, a
#  search box (patient, clinic ID, slip no., procedure / X-ray), Docterz-only charges, Excel; a tile in his Patients folder.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s689kit && cp -rp /root/deploy/repo/deploy_kits/S689_CLINIC_LISTS /tmp/s689kit && bash /tmp/s689kit/install_S689_CLINIC_LISTS.sh
#  (DRY=1 before bash: every gate, the rebuild, the walk and the control; nothing written.)
#   /root/finance/finance_app.py    2f604fee -> TO   ONE inserted mount block (clinic_lists), after S688's
#   /root/finance/clinic_lists.py   NEW      -> TO   the page (/finance/slips/lists/...); writes nothing, no table
#   /root/portal/portal.py          1a9b3a1b -> TO   ONE tile "X-ray & procedures" (roles doctor, group Patients) + its group line
#  Read, never changed: /root/portal/tile_grants.json (Dr Bhawna's "only" list keeps the tile off her home), the database.
#  ORDER: gates -> pins -> rebuild from the live bytes (both pythons compile) -> walk on scratch copies + the control on the live
#  files -> file backups -> DOCTOR_AUTO_OFF -> stage + atomic move -> restart clinic-finance, then clinic-portal -> healthz 200,
#  portal health 200, the journal names no clinic_lists / ImportError / 'NOT mounted' -> the walk on the placed files.
#  Red after placing: ALL THREE files back (clinic_lists.py removed), both services restarted.
# =============================================================================
set -u
KIT="S689_CLINIC_LISTS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; PD="$ROOT/portal"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
EDITED="finance/finance_app.py portal/portal.py"
ALL="$EDITED finance/clinic_lists.py"
declare -A FROM=( [finance/finance_app.py]=2f604fee8ae7e69af670c55a13592fce [portal/portal.py]=1a9b3a1b7460cf11171d5f6b6e376a48 )
declare -A TO
for n in $ALL; do TO[$n]="$(awk -v f="$n" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s689_inst_$STAMP"
PLACED=0; TOOK_LOCK=0; OFF_MINE=0
GREEN="68 of 68 green"
CONTROL="37 S689 check(s) red . 8 green"
GREEN_PLACED="45 of 45 green"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S689_${FROM[$1]:0:8}"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
fhz() { hcode "http://127.0.0.1:$FIN_PORT/finance/healthz"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
off_clear() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$APY" -B "$KDIR/walk_s689.py" "$@" 2>&1); }
mkscratch() {   # $1 = a folder: a copy of the live finance CODE (never the database, never a backup)
  mkdir -p "$1/finance_ui" "$1/spine"
  cp -p "$FIN"/*.py "$1/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$1/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$1/finance_ui/" 2>/dev/null; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$1/spine/" 2>/dev/null
  rm -f "$1"/*.bak_* 2>/dev/null; return 0
}
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting ALL THREE files back"
  PLACED=2
  for n in $EDITED; do \cp -p "$(bak $n)" "$ROOT/$n" || say "   !! could not put back $ROOT/$n"; done
  rm -f "$FIN/clinic_lists.py" "$FIN"/.*.s689 "$PD"/.*.s689
  "$SYSTEMCTL" restart "$FSVC" || true
  "$SYSTEMCTL" restart "$PSVC" || true
  for n in $EDITED; do say "   $ROOT/$n $(m5 "$ROOT/$n" | cut -c1-8) (expected ${FROM[$n]:0:8})"; done
  [ -e "$FIN/clinic_lists.py" ] && say "   !! $FIN/clinic_lists.py is still there" || say "   $FIN/clinic_lists.py removed"
  say "   finance healthz $(wait200 fhz) · portal health $(wait200 phz). Send a photo of this screen to Claude."
  off_clear; release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; off_clear; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop_unlocked() { say "$1"; off_clear; release_lock; exit "${2:-1}"; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout sleep; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${SKIP_WINDOW:-0}" = 1 ] || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/9] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/9] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/9] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $ALL; do [ -n "${TO[$n]}" ] || { say "!! [1/9] TO_PINS.md5 does not name $n - nothing installed"; exit 1; }; done
for n in $EDITED; do [ -f "$ROOT/$n" ] || { say "!! [1/9] $ROOT/$n is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/9] $DB is missing - nothing installed"; exit 1; }
AT=0; for n in $ALL; do [ "$(m5 "$ROOT/$n")" = "${TO[$n]}" ] && AT=$((AT+1)); done
lock_pid() { awk -v k="$KIT" '$1==k{print $2}' "$LOCK/owner" 2>/dev/null; }
lock_stale() { local p; p="$(lock_pid)"; [ -n "$p" ] && ! kill -0 "$p" 2>/dev/null; }      # held by this kit, its run gone
if [ "$AT" = 3 ]; then
  STALE=0
  if [ -d "$LOCK" ] && lock_stale; then rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null; STALE=1; say "   (a build lock left by an earlier $KIT run that was stopped was released)"; fi
  if [ -e "$OFFSW" ] && [ "$(awk 'NR==1{print $1}' "$OFFSW" 2>/dev/null)" = "$KIT" ] && ! [ -d "$LOCK" ]; then
    rm -f "$OFFSW"; STALE=1; say "   (a DOCTOR_AUTO_OFF left by an earlier $KIT run that was stopped was removed)"
  fi
  if [ "$STALE" = 1 ] && [ "${DRY:-0}" != 1 ]; then      # that run may have stopped before its restarts: restart both now (review 3)
    "$SYSTEMCTL" restart "$FSVC" || true; "$SYSTEMCTL" restart "$PSVC" || true
    say "   both services restarted after the stopped run: finance healthz $(wait200 fhz) · portal health $(wait200 phz) (anything but 200 200: send a photo of this screen to Claude)"
  fi
  say "-- ALREADY INSTALLED: the three files are the kit's. Nothing written. finance healthz $(fhz) · portal health $(phz)"; exit 0
fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/9] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/9] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif lock_stale; then
  TOOK_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/9] kit gates green; the build lock left by an earlier $KIT run that was stopped is taken over"
elif [ -n "$(lock_pid)" ]; then
  say "!! [1/9] another $KIT run (process $(lock_pid)) is still going - nothing installed. Wait for it to finish."
  exit 3
else
  say "!! [1/9] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."
  exit 3
fi
# Holding the lock proves no live run of this kit is going: a DOCTOR_AUTO_OFF naming this kit was left by a killed run -- ours to clear
# on every exit from here on (review 3).
if [ "$TOOK_LOCK" = 1 ] && [ -e "$OFFSW" ] && [ "$(awk 'NR==1{print $1}' "$OFFSW" 2>/dev/null)" = "$KIT" ]; then
  OFF_MINE=1; say "      a DOCTOR_AUTO_OFF left by an earlier $KIT run that was stopped is this run's to clear"
fi
for n in $EDITED; do
  C=$(m5 "$ROOT/$n"); [ "$C" = "${FROM[$n]}" ] || stop_unlocked "!! [2/9] $ROOT/$n is ${C:0:8}, expected ${FROM[$n]:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
done
[ -e "$FIN/clinic_lists.py" ] && stop_unlocked "!! [2/9] $FIN/clinic_lists.py is already there ($(m5 "$FIN/clinic_lists.py" | cut -c1-8)) - STOP, nothing installed"
say "[2/9] live pins exact: finance_app.py ${FROM[finance/finance_app.py]:0:8}, portal.py ${FROM[portal/portal.py]:0:8}; clinic_lists.py not there yet"

mkdir -p "$SCR/built" "$SCR/pyc" && chmod 700 "$SCR" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s689.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/9] the builder refused the live files - nothing installed"; }
for n in $ALL; do
  [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || stop_unlocked "!! [3/9] rebuilt, $n is $(m5 "$SCR/built/$n" | cut -c1-8), not ${TO[$n]:0:8} - nothing installed"
done
for py in "$APY" "$VPY"; do for n in $ALL; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" || stop_unlocked "!! [3/9] $n does not compile on $py - nothing installed"
done; done
say "[3/9] rebuilt here from this box's live bytes ($(grep -c '^edit ok' "$SCR/make.txt") counted edits): all three at their TO pins; they compile under both pythons"

mkscratch "$SCR/old"; mkscratch "$SCR/new"
\cp -p "$SCR/built/finance/finance_app.py" "$SCR/new/finance_app.py"; \cp -p "$SCR/built/finance/clinic_lists.py" "$SCR/new/clinic_lists.py"
mkdir -p "$SCR/pnew/portal" "$SCR/root/finance" "$SCR/root/portal"
\cp -p "$SCR/built/portal/portal.py" "$SCR/pnew/portal/portal.py"
\cp -p "$FIN/finance_app.py" "$SCR/root/finance/finance_app.py"; \cp -p "$PD/portal.py" "$SCR/root/portal/portal.py"
copydb "$DB" "$SCR/walk.db" || stop_unlocked "!! [4/9] no copy of the database - nothing installed"
WOUT="$(walk --new "$SCR/new" --portal "$SCR/pnew" --base "$ROOT" --db "$SCR/walk.db" --scratch "$SCR/w1" --kit "$KDIR" --root "$SCR/root")"; R="$(echo "$WOUT" | tail -1)"
[ "$R" = "$GREEN" ] || { echo "$WOUT" | grep -E '^  RED' | head -12; stop_unlocked "!! [4/9] the walk on the rebuilt files is not green ($R) - nothing installed"; }
COUT="$(walk --control "$SCR/old" --portal "$ROOT" --base "$ROOT" --db "$SCR/walk.db" --scratch "$SCR/w0" --kit "$KDIR")"; R0="$(echo "$COUT" | tail -1)"
[ "$R0" = "$CONTROL" ] || stop_unlocked "!! [4/9] the control on the live files is not as expected ($R0) - nothing installed"
for n in $EDITED; do [ "$(m5 "$ROOT/$n")" = "${FROM[$n]}" ] || stop_unlocked "!! [4/9] $ROOT/$n changed during the walk - nothing installed"; done
f0=$(fhz); p0=$(phz); [ "$f0" = 200 ] && [ "$p0" = 200 ] || stop_unlocked "!! [4/9] finance healthz $f0 / portal health $p0 before the install - nothing installed"
rm -f "$SCR/walk.db"
say "[4/9] the walk on a copy of the database: $GREEN (who reaches what, every row rule, the search, the dates, the Excel, nothing written, October against an independent count, every home's tiles, the builder, 19 mutants caught); the control on the live files: $R0; finance $f0, portal $p0"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the rebuild, the walk and the control green; NOTHING written"; exit 0; fi

for n in $EDITED; do
  [ -e "$(bak $n)" ] && [ "$(m5 "$(bak $n)")" != "${FROM[$n]}" ] && stop_unlocked "!! [5/9] a backup $(bak $n) is there and is not the FROM bytes - left as it is; nothing placed. Tell Claude."
  { \cp -p "$ROOT/$n" "$(bak $n)" && [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ]; } || stop_unlocked "!! [5/9] could not write the backup $(bak $n) - nothing placed"
done
if [ -e "$OFFSW" ] && [ "$(awk 'NR==1{print $1}' "$OFFSW" 2>/dev/null)" = "$KIT" ]; then
  OFF_MINE=1; say "[5/9] DOCTOR_AUTO_OFF was left by an earlier $KIT run that was stopped - this run takes it as its own and removes it at the end"
elif [ -e "$OFFSW" ]; then
  say "[5/9] DOCTOR_AUTO_OFF is already on ($(head -c 120 "$OFFSW" 2>/dev/null)) - left exactly as it is; this kit will not remove it"
else
  mkdir -p "$(dirname "$OFFSW")" || stop_unlocked "!! [5/9] could not make the folder of $OFFSW - nothing placed"
  if (set -o noclobber; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restarts below are this kit's" > "$OFFSW") 2>/dev/null; then
    OFF_MINE=1
  elif [ -e "$OFFSW" ] && [ "$(awk 'NR==1{print $1}' "$OFFSW" 2>/dev/null)" = "$KIT" ]; then
    OFF_MINE=1; stop_unlocked "!! [5/9] could not finish writing $OFFSW - nothing placed"
  else
    stop_unlocked "!! [5/9] could not write $OFFSW (or someone else set it just now) - nothing placed"
  fi
fi
for n in $ALL; do
  d="$(dirname "$ROOT/$n")"; STG="$d/.$(basename "$n").s689"
  { cat "$SCR/built/$n" > "$STG" && [ "$(m5 "$STG")" = "${TO[$n]}" ]; } || { rm -f "$FIN"/.*.s689 "$PD"/.*.s689; stop_unlocked "!! [5/9] could not stage $n - nothing placed"; }
  ref="$FIN/finance_app.py"; [ "$n" = portal/portal.py ] && ref="$PD/portal.py"
  chmod --reference="$ref" "$STG" 2>/dev/null; chown --reference="$ref" "$STG" 2>/dev/null
done
PLACED=1
for n in finance/clinic_lists.py finance/finance_app.py portal/portal.py; do
  d="$(dirname "$ROOT/$n")"; mv -f "$d/.$(basename "$n").s689" "$ROOT/$n" || restore "the rename of $n"
done
for n in $ALL; do [ "$(m5 "$ROOT/$n")" = "${TO[$n]}" ] || restore "read back $n"; done
say "[5/9] placed and read back: $(for n in $ALL; do printf '%s %s  ' "$(basename "$n")" "${TO[$n]:0:8}"; done)(backups *.bak_S689_*)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(hcode "http://127.0.0.1:$FIN_PORT/finance/slips/lists"); case "$c2" in 302|401|303) ;; *) restore "/finance/slips/lists answered $c2 without a login";; esac
say "[6/9] $FSVC restarted at $T0: healthz $c1; /finance/slips/lists $c2 without a login (the gate)"
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
c3=$(wait200 phz); [ "$c3" = 200 ] || restore "portal health $c3"
command -v "$JOURNALCTL" >/dev/null 2>&1 || restore "no $JOURNALCTL to read the services' own word on the mount"
sleep 2
JL="$("$JOURNALCTL" -u "$FSVC" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -c -i -E 'clinic_lists|NOT mounted|ImportError|ModuleNotFoundError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'clinic_lists|NOT mounted|ImportError|ModuleNotFoundError|Traceback' | head -5; restore "journal: $JR line(s) naming clinic_lists, an import error, a traceback or a part NOT mounted since the restart"; }
say "[7/9] $PSVC restarted: health $c3; the journal of both since $T0 ($(printf '%s\n' "$JL" | grep -c .) line(s)) names no clinic_lists, import error, traceback or 'NOT mounted'"

mkscratch "$SCR/placed"
mkdir -p "$SCR/pplaced/portal"; \cp -p "$PD/portal.py" "$SCR/pplaced/portal/portal.py"
copydb "$DB" "$SCR/walk2.db" || restore "no copy of the database for the walk on the placed files"
POUT="$(walk --new "$SCR/placed" --portal "$SCR/pplaced" --base "$ROOT" --db "$SCR/walk2.db" --scratch "$SCR/w2" --kit "$KDIR" --only inner)"; R="$(echo "$POUT" | tail -1)"
rm -f "$SCR/walk2.db"
[ "${REHEARSE_RED_AT:-}" = 8 ] && R="rehearsal: a forced red at [8/9]"      # the rehearsal's hook only; unset on a real install
[ "$R" = "$GREEN_PLACED" ] || { echo "$POUT" | grep -E '^  RED' | head -8; restore "the walk on the placed files: $R"; }
say "[8/9] the walk on the placed files (the real app and the real portal as they now stand, on a copy): $R"
PLACED=3                                                   # verified: a signal from here on must not undo it (review 3)
off_clear; release_lock
say "[9/9] DOCTOR_AUTO_OFF removed if this kit set it; the build lock released"
say "undo (one line): \\cp -p $(bak finance/finance_app.py) $FIN/finance_app.py && \\cp -p $(bak portal/portal.py) $PD/portal.py && rm -f $FIN/clinic_lists.py && $SYSTEMCTL restart $FSVC && $SYSTEMCTL restart $PSVC"
say ""
say "$KIT: DONE. Your X-ray & procedures page is the new tile in your Patients folder: /finance/slips/lists"
exit 0
