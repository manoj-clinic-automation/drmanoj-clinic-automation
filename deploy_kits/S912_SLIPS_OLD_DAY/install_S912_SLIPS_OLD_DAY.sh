#!/bin/bash
# =============================================================================
#  install_S912_SLIPS_OLD_DAY.sh · kit S912 (the parent, S496, 21-Nov-2026) · Shavez's missed older-day parchi
#  1. WRITING a missed parchi reaches a month back (was 7 days); edits, removals and radd stay at 7 days        slip_log.py c2cf351a -> TO
#  2. an old day's form opens with the number box EMPTY ('us din ki parchi ka number'), never today's next number
#  3. a number Shavez marked Radd on that OLD day, his radd ask still pending, can be written as the parchi it was; the ask is
#     set aside (kept, 'replaced'); Kharab, an approved radd or a radd with no ask stay refused; 'already written' names its day
#  4. the desk: on an old day the number boxes start empty                                             parchi_desk.py 548d68ca -> TO
#  clinic-finance restarted.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s912kit && cp -rp /root/deploy/repo/deploy_kits/S912_SLIPS_OLD_DAY /tmp/s912kit && bash /tmp/s912kit/install_S912_SLIPS_OLD_DAY.sh
#  DRY=1 before bash: every gate and walk, nothing changed. --undo: the two files back.
# =============================================================================
set -u
KIT="S912_SLIPS_OLD_DAY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="slip_log.py parchi_desk.py"
from_of() { case "$1" in slip_log.py) echo c2cf351a74b983e883be6bed1e5d918b;; parchi_desk.py) echo 548d68ca9776ab5a97b6590dbdea3fdd;; esac; }
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s912_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { local f; f=$(from_of "$1"); echo "$ROOT/finance/$1.bak_S912_${f:0:8}"; }
fget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fget /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES; do rm -f "$ROOT/finance/.$n.s912"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the files back"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/finance/$n"; done
  "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do f=$(from_of "$n"); say "   $n $(m5 "$ROOT/finance/$n" | cut -c1-8) (expected ${f:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
mkfin() { rm -rf "$SCR/fin_$1"; mkdir -p "$SCR/fin_$1" && find "$ROOT/finance" -maxdepth 1 -type f -name '*.py' -exec cp -p {} "$SCR/fin_$1/" \; && find "$ROOT/finance" -maxdepth 1 -type f -name '*.html' -exec cp -p {} "$SCR/fin_$1/" \; && [ -f "$SCR/fin_$1/slip_log.py" ]; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$@" 2>&1); }

if [ "${1:-}" = "--undo" ]; then
  U=1; for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(from_of "$n")" ] || U=0; done;
  [ "$U" = 1 ] && { say "-- $KIT is not installed (the two at their FROM pins) - nothing to undo."; exit 0; }
  for n in $NAMES; do b=$(bak "$n"); [ -f "$b" ] && [ "$(m5 "$b")" = "$(from_of "$n")" ] || { say "!! no good backup $b - nothing undone"; exit 1; }; done
  for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || { say "!! $ROOT/finance/$n is $(m5 "$ROOT/finance/$n" | cut -c1-8), not this kit's - a later change is on it: nothing undone. Tell Claude."; exit 1; }; done
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/finance/$n"; done; "$SYSTEMCTL" restart "$FSVC"
  for n in $NAMES; do say "   $n $(m5 "$ROOT/finance/$n" | cut -c1-8) (expected $(from_of "$n" | cut -c1-8))"; done
  h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but finance healthz is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE ($FSVC restarted, finance healthz 200)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES; do [ "$(m5 "$KDIR/$n")" = "$(to_of "$n")" ] || { say "!! [1/5] the kit's $n is not as built - nothing installed"; exit 1; }; done
for n in $NAMES; do [ -f "$ROOT/finance/$n" ] || { say "!! [1/5] $ROOT/finance/$n missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/5] $DB missing - nothing installed"; exit 1; }
ALL=1; for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do fr=$(from_of "$n"); [ "$(m5 "$ROOT/finance/$n")" = "$fr" ] || stop "!! [2/5] $ROOT/finance/$n is $(m5 "$ROOT/finance/$n" | cut -c1-8), expected ${fr:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do for n in $NAMES; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/$n" || stop "!! [2/5] $n does not compile on $p - nothing installed"; done; done
say "[2/5] the live pins exact; the two files compile on both pythons"
"$VPY" -c "import sqlite3,sys;s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=30);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close()" "$DB" "$SCR/finance.db" || stop "!! [3/5] could not copy the database for the walks - nothing installed"
\cp -p "$SCR/finance.db" "$SCR/f_old.db" && \cp -p "$SCR/finance.db" "$SCR/f_new.db" && \cp -p "$SCR/finance.db" "$SCR/f_844.db" || stop "!! [3/5] could not copy the database for the walks - nothing installed"
{ mkfin old && mkfin new && for n in $NAMES; do \cp -p "$KDIR/$n" "$SCR/fin_new/$n" || exit 9; done; } || stop "!! [3/5] could not lay out the walks - nothing installed"
R1=$(py "$KDIR/walk_s912.py" "$SCR/fin_new" "$SCR/w_new" | tail -1)
case "$R1" in "WALK 29/29") ;; *) py "$KDIR/walk_s912.py" "$SCR/fin_new" "$SCR/w_new2" | grep '^FAIL' | cut -c1-160 | head -6 | sed 's/^/      /'; stop "!! [3/5] walk_s912 (made-up root) on the new files: $R1 - nothing installed";; esac
R1c=$(py "$KDIR/walk_s912.py" "$SCR/fin_old" "$SCR/w_old" | tail -1)
case "$R1c" in "WALK 29/29") stop "!! [3/5] walk_s912's control (the live files) did not go red - nothing installed";; esac
R2n=$(py "$KDIR/walk_s840.py" "$SCR/fin_new" "$SCR/f_new.db" | tail -1); R2o=$(py "$KDIR/walk_s840.py" "$SCR/fin_old" "$SCR/f_old.db" | tail -1)
[ "$R2n" = "$R2o" ] || stop "!! [3/5] walk_s840 (the desk) differs: new '$R2n', live '$R2o' - nothing installed"
mkdir -p "$SCR/k844" && \cp -p "$KDIR/parchi_desk.py" "$SCR/k844/" || stop "!! [3/5] could not lay out walk_s844 - nothing installed"
R4=$(py "$KDIR/walk_s844.py" "$SCR/k844" "$SCR/fin_new" "$SCR/f_844.db" | tail -1)
case "$R4" in "WALK OK 31/31") ;; *) stop "!! [3/5] walk_s844 (S844's desk) on the new files: $R4 - nothing installed";; esac
say "[3/5] walk_s912 $R1 (made-up root; control red: ${R1c:-crashed}); walk_s840 '$R2n' (live files the same); walk_s844 $R4"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks and the control green; nothing live changed"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$ROOT/finance/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
REF="$ROOT/finance/slip_log.py"
for n in $NAMES; do st="$ROOT/finance/.$n.s912"
  { cat "$KDIR/$n" > "$st" && chmod --reference="$REF" "$st" 2>/dev/null; chown --reference="$REF" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
for n in $NAMES; do mv -f "$ROOT/finance/.$n.s912" "$ROOT/finance/$n" || restore "the rename of $n"; done
for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
ap=$(fget /finance/slips); case "$ap" in 200|302|303|401|403) ;; *) restore "the slips page answered $ap";; esac
dk=$(fget /finance/slips/desk); case "$dk" in 200|302|303|401|403) ;; *) restore "the desk answered $dk";; esac
release_lock
say "[4/5] placed and read back: two files at their TO pins; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the slips page $ap, the desk $dk"
say "[5/5] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""
say "$KIT: DONE."
exit 0
