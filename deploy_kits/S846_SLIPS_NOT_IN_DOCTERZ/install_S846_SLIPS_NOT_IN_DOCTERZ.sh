#!/bin/bash
# =============================================================================
#  install_S846_SLIPS_NOT_IN_DOCTERZ.sh · kit S846 (the parent, S471 -> S474, 17-Nov-2026) · D994, A-D63
#  His page "Slips not in Docterz": every slip since 23-Sep whose patient Docterz does not carry that day, with the FULL mobile
#  and four taps (Entered in Docterz / Not entering in Docterz / Free-staff-home / Wrong slip), each undoable. The day check,
#  the money match, his console and the slips desk read his answers.
#   1. NEW /root/finance/not_in_docterz.py
#   2. /root/finance/day_check.py, clinic_money.py, owner_console.py, parchi_desk.py  FROM -> TO pins.  clinic-finance restarted.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s846kit && cp -rp /root/deploy/repo/deploy_kits/S846_SLIPS_NOT_IN_DOCTERZ /tmp/s846kit && bash /tmp/s846kit/install_S846_SLIPS_NOT_IN_DOCTERZ.sh
#  DRY=1 before bash: every gate, the walks and the controls; nothing live changes. --undo: the four back, the new file set aside.
# =============================================================================
set -u
KIT="S846_SLIPS_NOT_IN_DOCTERZ"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="day_check.py clinic_money.py owner_console.py parchi_desk.py"
NEW="not_in_docterz.py"
from_of() { case "$1" in
  day_check.py) echo c23e3f2f318fafa58582a9d3b19c91db;; clinic_money.py) echo f8a64266158cdaae45ec4067ab84006a;;
  owner_console.py) echo 72da1da887a5f79c741137af44c8fe8b;; parchi_desk.py) echo 32f085230c2483544dfa354606aa962f;; esac; }
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s846_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { local f; f=$(from_of "$1"); echo "$ROOT/finance/$1.bak_S846_${f:0:8}"; }
NEWASIDE="$ROOT/finance/$NEW.undone_S846"
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
fpage() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/clinic/not-in-docterz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/clinic/not-in-docterz"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES $NEW; do rm -f "$ROOT/finance/.$n.s846"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the files back"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/finance/$n"; done
  [ -f "$ROOT/finance/$NEW" ] && mv -f "$ROOT/finance/$NEW" "$NEWASIDE"
  "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do f=$(from_of "$n"); say "   $n $(m5 "$ROOT/finance/$n" | cut -c1-8) (expected ${f:0:8})"; done
  say "   $NEW set aside; $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
mkfin() { rm -rf "$SCR/fin_$1"; mkdir -p "$SCR/fin_$1" && find "$ROOT/finance" -maxdepth 1 -type f -name '*.py' -exec cp -p {} "$SCR/fin_$1/" \; && [ -f "$SCR/fin_$1/records.py" ]; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -s -B "$@" 2>&1); }

if [ "${1:-}" = "--undo" ]; then
  U=1; for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(from_of "$n")" ] || U=0; done; [ -e "$ROOT/finance/$NEW" ] && U=0
  [ "$U" = 1 ] && { say "-- $KIT is not installed (the four at their FROM pins, $NEW absent) - nothing to undo."; exit 0; }
  for n in $NAMES; do b=$(bak "$n"); [ -f "$b" ] && [ "$(m5 "$b")" = "$(from_of "$n")" ] || { say "!! no good backup $b - nothing undone"; exit 1; }; done
  for n in $NAMES $NEW; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || { say "!! $ROOT/finance/$n is $(m5 "$ROOT/finance/$n" | cut -c1-8), not this kit's - a later change is on it: nothing undone. Tell Claude."; exit 1; }; done
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/finance/$n"; done; mv -f "$ROOT/finance/$NEW" "$NEWASIDE"; "$SYSTEMCTL" restart "$FSVC"
  for n in $NAMES; do say "   $n $(m5 "$ROOT/finance/$n" | cut -c1-8) (expected $(from_of "$n" | cut -c1-8))"; done
  say "   $NEW set aside as $NEWASIDE (its table nid_mark stays; nothing reads it)"
  h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but finance healthz is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE ($FSVC restarted, finance healthz 200)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES $NEW; do [ "$(m5 "$KDIR/$n")" = "$(to_of "$n")" ] || { say "!! [1/5] the kit's $n is not as built - nothing installed"; exit 1; }; done
for n in $NAMES; do [ -f "$ROOT/finance/$n" ] || { say "!! [1/5] $ROOT/finance/$n missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/5] $DB missing - nothing installed"; exit 1; }
ALL=1; for n in $NAMES $NEW; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do fr=$(from_of "$n"); [ "$(m5 "$ROOT/finance/$n")" = "$fr" ] || stop "!! [2/5] $ROOT/finance/$n is $(m5 "$ROOT/finance/$n" | cut -c1-8), expected ${fr:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
[ -e "$ROOT/finance/$NEW" ] && stop "!! [2/5] $ROOT/finance/$NEW already exists and is not this kit's - STOP, nothing installed. Tell Claude."
for p in "$APY" "$VPY"; do for n in $NAMES $NEW; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/$n" || stop "!! [2/5] $n does not compile on $p - nothing installed"; done; done
say "[2/5] the live pins exact; $NEW absent; the five files compile on both pythons"
"$VPY" -c "import sqlite3,sys;s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=30);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close()" "$DB" "$SCR/finance.db" || stop "!! [3/5] could not copy the database for the walks - nothing installed"
"$VPY" -c "import sqlite3,sys;s=sqlite3.connect(sys.argv[1]);d=sqlite3.connect(sys.argv[2])
for (q,) in s.execute(\"select sql from sqlite_master where sql is not null and name not like 'sqlite_%'\"): d.execute(q)
d.commit()" "$SCR/finance.db" "$SCR/schema.db" || stop "!! [3/5] could not make the empty schema copy - nothing installed"
{ mkfin old && mkfin new && for n in $NAMES $NEW; do \cp -p "$KDIR/$n" "$SCR/fin_new/$n" || exit 9; done; } || stop "!! [3/5] could not lay out the walks - nothing installed"
R6=$(py "$KDIR/walk_s846.py" "$SCR/fin_new" "$SCR/fin_new" "$SCR/schema.db" "$SCR/w_new" | tail -1)
case "$R6" in "WALK 42/42") ;; *) stop "!! [3/5] walk_s846 (made-up root) on the new files: $R6 - nothing installed";; esac
R6c=$(py "$KDIR/walk_s846.py" "$SCR/fin_old" "$SCR/fin_old" "$SCR/schema.db" "$SCR/w_old" | tail -1)
case "$R6c" in "WALK 42/42") stop "!! [3/5] walk_s846's control (the live files) did not go red - nothing installed";; esac
RS=$(py "$KDIR/shape_s846.py" "$SCR/fin_new" "$SCR/fin_old" "$SCR/fin_old" "$SCR/finance.db" 14 | grep -E "^days the same" )
case "$RS" in "days the same: 14/14") ;; *) stop "!! [3/5] the live shape (14 days, no answer marked) differs from the live files: $RS - nothing installed";; esac
R0=$(py "$KDIR/walk_s840.py" "$SCR/fin_new" "$SCR/finance.db" | tail -1)
case "$R0" in "WALK OK "*) ;; *) stop "!! [3/5] walk_s840 (the desk as S840 left it) on the new files: $R0 - nothing installed";; esac
R4=$(py "$KDIR/walk_s844.py" "$KDIR" "$SCR/fin_old" "$SCR/finance.db" | tail -1)
case "$R4" in "WALK OK 31/31") ;; *) stop "!! [3/5] walk_s844 (S844's desk) on the new parchi_desk: $R4 - nothing installed";; esac
say "[3/5] walk_s846 $R6 (made-up root; control red: ${R6c:-crashed}); live shape $RS; walk_s840 $R0; walk_s844 $R4"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks and the control green; nothing live changed"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$ROOT/finance/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
REF="$ROOT/finance/day_check.py"
for n in $NAMES $NEW; do st="$ROOT/finance/.$n.s846"
  { cat "$KDIR/$n" > "$st" && chmod --reference="$REF" "$st" 2>/dev/null; chown --reference="$REF" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
mv -f "$ROOT/finance/.$NEW.s846" "$ROOT/finance/$NEW" || restore "the rename of $NEW"
for n in $NAMES; do mv -f "$ROOT/finance/.$n.s846" "$ROOT/finance/$n" || restore "the rename of $n"; done
for n in $NAMES $NEW; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
pg=$(fpage); case "$pg" in 200|302|303|401|403) ;; *) restore "his page answered $pg";; esac
release_lock
say "[4/5] placed and read back: five files at their TO pins; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the page answers $pg"
say "[5/5] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""
say "$KIT: DONE. Your page: https://followup.dr-manoj.in/finance/clinic/not-in-docterz (also from the console's Needs-you line)."
exit 0
