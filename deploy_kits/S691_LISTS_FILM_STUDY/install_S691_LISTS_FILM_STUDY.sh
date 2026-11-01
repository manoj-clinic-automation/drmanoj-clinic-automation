#!/bin/bash
# =============================================================================
#  install_S691_LISTS_FILM_STUDY.sh · kit S691 (01-Nov-2026, the parent, session 374) · the owner's words 06:32-06:56 IST
#  1 his X-ray & procedures page reads Paid from Docterz (the room's tick retired on 24-Oct, D775) · 2 "films", plural
#  3 film size and films per study on his X-rays & procedures rate page (the Add row and every X-ray line; a new X-ray needs a
#    size) -- one store, the film log's xf_study · 4 the film log's bills: this financial year, "N film bills since 1 Apr",
#    a link to the Scan App · 5 the film log counts every billed X-ray slip again (it counted only ticked slips: none since 28-Oct)
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s691kit && cp -rp /root/deploy/repo/deploy_kits/S691_LISTS_FILM_STUDY /tmp/s691kit && bash /tmp/s691kit/install_S691_LISTS_FILM_STUDY.sh
#  (DRY=1 before bash: every gate, the rebuild, the walk and the control; nothing written.)
#   /root/finance/owner_sheets.py   baa7ccc4 -> TO   the film on every X-ray line; the Add row asks the film size
#   /root/finance/xray_film.py      c08a1016 -> TO   set_study, docterz_paid, fy_start; every ok slip counted; the bills card
#   /root/finance/clinic_lists.py   6118ef4d -> TO   Paid from Docterz; "films"; size-not-set links to the rate page
#  No data step, no new table, no portal change. Restarts clinic-finance only.
#  ORDER: gates -> pins -> rebuild from the live bytes (both pythons compile) -> walk on scratch copies + the control on the live
#  files -> file backups -> DOCTOR_AUTO_OFF -> stage + atomic move -> restart clinic-finance -> healthz 200, the journal names no
#  module of this kit / ImportError / 'NOT mounted' -> the walk on the placed files. Red after placing: ALL THREE files back.
# =============================================================================
set -u
KIT="S691_LISTS_FILM_STUDY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
ALL="owner_sheets.py xray_film.py clinic_lists.py"
declare -A FROM=( [owner_sheets.py]=baa7ccc405a78bdbbd8b2485c00dc9a0 [xray_film.py]=c08a10163295d5ab5919472e01977c12 [clinic_lists.py]=6118ef4da88ada966752a8c0340828a7 )
declare -A TO
for n in $ALL; do TO[$n]="$(awk -v f="$n" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s691_inst_$STAMP"
PLACED=0; TOOK_LOCK=0; OFF_MINE=0
GREEN="66 of 66 green"
CONTROL="25 S691 check(s) red . 9 green"
GREEN_PLACED="44 of 44 green"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S691_${FROM[$1]:0:8}"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
fhz() { hcode "http://127.0.0.1:$FIN_PORT/finance/healthz"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
off_clear() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$APY" -B "$KDIR/walk_s691.py" "$@" 2>&1); }
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
  for n in $ALL; do \cp -p "$(bak $n)" "$FIN/$n" || say "   !! could not put back $FIN/$n"; done
  rm -f "$FIN"/.*.s691
  "$SYSTEMCTL" restart "$FSVC" || true
  for n in $ALL; do say "   $FIN/$n $(m5 "$FIN/$n" | cut -c1-8) (expected ${FROM[$n]:0:8})"; done
  say "   finance healthz $(wait200 fhz). Send a photo of this screen to Claude."
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
  || { say "!! [1/8] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $ALL; do [ -n "${TO[$n]}" ] || { say "!! [1/8] TO_PINS.md5 does not name $n - nothing installed"; exit 1; }; done
for n in $ALL; do [ -f "$FIN/$n" ] || { say "!! [1/8] $FIN/$n is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/8] $DB is missing - nothing installed"; exit 1; }
AT=0; for n in $ALL; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] && AT=$((AT+1)); done
lock_pid() { awk -v k="$KIT" '$1==k{print $2}' "$LOCK/owner" 2>/dev/null; }
lock_stale() { local p; p="$(lock_pid)"; [ -n "$p" ] && ! kill -0 "$p" 2>/dev/null; }      # held by this kit, its run gone
if [ "$AT" = 3 ]; then
  STALE=0
  if [ -d "$LOCK" ] && lock_stale; then rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null; STALE=1; say "   (a build lock left by an earlier $KIT run that was stopped was released)"; fi
  if [ -e "$OFFSW" ] && [ "$(awk 'NR==1{print $1}' "$OFFSW" 2>/dev/null)" = "$KIT" ] && ! [ -d "$LOCK" ]; then
    rm -f "$OFFSW"; STALE=1; say "   (a DOCTOR_AUTO_OFF left by an earlier $KIT run that was stopped was removed)"
  fi
  if [ "$STALE" = 1 ] && [ "${DRY:-0}" != 1 ]; then
    "$SYSTEMCTL" restart "$FSVC" || true
    say "   clinic-finance restarted after the stopped run: healthz $(wait200 fhz) (anything but 200: send a photo of this screen to Claude)"
  fi
  say "-- ALREADY INSTALLED: the three files are the kit's. Nothing written. finance healthz $(fhz)"; exit 0
fi
if [ "$AT" != 0 ]; then
  say "!! [1/8] $AT of the three files are already at the kit's TO and the rest are not - HALF PLACED: nothing installed. Tell Claude."; exit 1
fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/8] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/8] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif lock_stale; then
  TOOK_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/8] kit gates green; the build lock left by an earlier $KIT run that was stopped is taken over"
elif [ -n "$(lock_pid)" ]; then
  say "!! [1/8] another $KIT run (process $(lock_pid)) is still going - nothing installed. Wait for it to finish."
  exit 3
else
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."
  exit 3
fi
if [ "$TOOK_LOCK" = 1 ] && [ -e "$OFFSW" ] && [ "$(awk 'NR==1{print $1}' "$OFFSW" 2>/dev/null)" = "$KIT" ]; then
  OFF_MINE=1; say "      a DOCTOR_AUTO_OFF left by an earlier $KIT run that was stopped is this run's to clear"
fi
for n in $ALL; do
  C=$(m5 "$FIN/$n"); [ "$C" = "${FROM[$n]}" ] || stop_unlocked "!! [2/8] $FIN/$n is ${C:0:8}, expected ${FROM[$n]:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
done
say "[2/8] live pins exact: owner_sheets.py ${FROM[owner_sheets.py]:0:8}, xray_film.py ${FROM[xray_film.py]:0:8}, clinic_lists.py ${FROM[clinic_lists.py]:0:8}"

mkdir -p "$SCR/built" "$SCR/pyc" "$SCR/root" && chmod 700 "$SCR" || stop_unlocked "!! cannot make $SCR - nothing installed"
for n in $ALL; do \cp -p "$FIN/$n" "$SCR/root/$n"; done
"$APY" -B make_s691.py "$SCR/root" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/8] the builder refused the live files - nothing installed"; }
for n in $ALL; do
  [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || stop_unlocked "!! [3/8] rebuilt, $n is $(m5 "$SCR/built/$n" | cut -c1-8), not ${TO[$n]:0:8} - nothing installed"
done
for py in "$APY" "$VPY"; do for n in $ALL; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" || stop_unlocked "!! [3/8] $n does not compile on $py - nothing installed"
done; done
say "[3/8] rebuilt here from this box's live bytes (57 counted edits): all three at their TO pins; they compile under both pythons"

mkscratch "$SCR/old"; mkscratch "$SCR/new"
for n in $ALL; do \cp -p "$SCR/built/$n" "$SCR/new/$n"; done
copydb "$DB" "$SCR/walk.db" || stop_unlocked "!! [4/8] no copy of the database - nothing installed"
WOUT="$(walk --new "$SCR/new" --db "$SCR/walk.db" --scratch "$SCR/w1" --kit "$KDIR" --root "$SCR/root")"; R="$(echo "$WOUT" | tail -1)"
[ "$R" = "$GREEN" ] || { echo "$WOUT" | grep -E '^  RED' | head -12; stop_unlocked "!! [4/8] the walk on the rebuilt files is not green ($R) - nothing installed"; }
COUT="$(walk --control "$SCR/old" --db "$SCR/walk.db" --scratch "$SCR/w0" --kit "$KDIR")"; R0="$(echo "$COUT" | tail -1)"
[ "$R0" = "$CONTROL" ] || stop_unlocked "!! [4/8] the control on the live files is not as expected ($R0) - nothing installed"
for n in $ALL; do [ "$(m5 "$FIN/$n")" = "${FROM[$n]}" ] || stop_unlocked "!! [4/8] $FIN/$n changed during the walk - nothing installed"; done
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/8] finance healthz $f0 before the install - nothing installed"
rm -f "$SCR/walk.db"
say "[4/8] the walk on a copy of the database: $GREEN (Paid from Docterz, films, the rate page's film, the film log's count and bills, the builder, 19 mutants caught); the control on the live files: $R0; finance $f0"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the rebuild, the walk and the control green; NOTHING written"; exit 0; fi

for n in $ALL; do
  [ -e "$(bak $n)" ] && [ "$(m5 "$(bak $n)")" != "${FROM[$n]}" ] && stop_unlocked "!! [5/8] a backup $(bak $n) is there and is not the FROM bytes - left as it is; nothing placed. Tell Claude."
  { \cp -p "$FIN/$n" "$(bak $n)" && [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ]; } || stop_unlocked "!! [5/8] could not write the backup $(bak $n) - nothing placed"
done
if [ -e "$OFFSW" ] && [ "$(awk 'NR==1{print $1}' "$OFFSW" 2>/dev/null)" = "$KIT" ]; then
  OFF_MINE=1; say "[5/8] DOCTOR_AUTO_OFF was left by an earlier $KIT run that was stopped - this run takes it as its own and removes it at the end"
elif [ -e "$OFFSW" ]; then
  say "[5/8] DOCTOR_AUTO_OFF is already on ($(head -c 120 "$OFFSW" 2>/dev/null)) - left exactly as it is; this kit will not remove it"
else
  mkdir -p "$(dirname "$OFFSW")" || stop_unlocked "!! [5/8] could not make the folder of $OFFSW - nothing placed"
  if (set -o noclobber; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's" > "$OFFSW") 2>/dev/null; then
    OFF_MINE=1
  else
    stop_unlocked "!! [5/8] could not write $OFFSW (or someone else set it just now) - nothing placed"
  fi
fi
for n in $ALL; do
  STG="$FIN/.$n.s691"
  { cat "$SCR/built/$n" > "$STG" && [ "$(m5 "$STG")" = "${TO[$n]}" ]; } || { rm -f "$FIN"/.*.s691; stop_unlocked "!! [5/8] could not stage $n - nothing placed"; }
  chmod --reference="$FIN/$n" "$STG" 2>/dev/null; chown --reference="$FIN/$n" "$STG" 2>/dev/null
done
PLACED=1
for n in xray_film.py clinic_lists.py owner_sheets.py; do mv -f "$FIN/.$n.s691" "$FIN/$n" || restore "the rename of $n"; done
for n in $ALL; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || restore "read back $n"; done
say "[5/8] placed and read back: $(for n in $ALL; do printf '%s %s  ' "$n" "${TO[$n]:0:8}"; done)(backups *.bak_S691_*)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(hcode "http://127.0.0.1:$FIN_PORT/finance/slips/lists"); case "$c2" in 302|401|303) ;; *) restore "/finance/slips/lists answered $c2 without a login";; esac
command -v "$JOURNALCTL" >/dev/null 2>&1 || restore "no $JOURNALCTL to read the service's own word on the mount"
sleep 2
JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -c -i -E 'clinic_lists|xray_film|owner_sheets|NOT mounted|ImportError|ModuleNotFoundError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'clinic_lists|xray_film|owner_sheets|NOT mounted|ImportError|ModuleNotFoundError|Traceback' | head -5; restore "journal: $JR line(s) naming a module of this kit, an import error, a traceback or a part NOT mounted since the restart"; }
say "[6/8] $FSVC restarted at $T0: healthz $c1; /finance/slips/lists $c2 without a login (the gate); the journal ($(printf '%s\n' "$JL" | grep -c .) line(s)) names no module of this kit, import error, traceback or 'NOT mounted'"

mkscratch "$SCR/placed"
copydb "$DB" "$SCR/walk2.db" || restore "no copy of the database for the walk on the placed files"
POUT="$(walk --new "$SCR/placed" --db "$SCR/walk2.db" --scratch "$SCR/w2" --kit "$KDIR" --only inner)"; R="$(echo "$POUT" | tail -1)"
rm -f "$SCR/walk2.db"
[ "${REHEARSE_RED_AT:-}" = 7 ] && R="rehearsal: a forced red at [7/8]"      # the rehearsal's hook only; unset on a real install
[ "$R" = "$GREEN_PLACED" ] || { echo "$POUT" | grep -E '^  RED' | head -8; restore "the walk on the placed files: $R"; }
say "[7/8] the walk on the placed files (the real app as it now stands, on a copy): $R"
PLACED=3
off_clear; release_lock
say "[8/8] DOCTOR_AUTO_OFF removed if this kit set it; the build lock released"
say "undo (one line): \\cp -p $(bak owner_sheets.py) $FIN/owner_sheets.py && \\cp -p $(bak xray_film.py) $FIN/xray_film.py && \\cp -p $(bak clinic_lists.py) $FIN/clinic_lists.py && $SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. Film size and films are on your X-rays & procedures page; Paid on your lists page comes from Docterz; the film log counts every billed X-ray."
exit 0
