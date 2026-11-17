#!/bin/bash
# =============================================================================
#  install_S854_LAB_NO_ID.sh · kit S854 (the parent, S477, 17-Nov-2026) · D979/D980, S450 study item 10
#  Lab reports mailed with no clinic ID: suggested patients, best first, one tap each (a blood slip 0-3 days before, then a
#  visit in the 7 days before, then the patient list by the same name), every unplaced one listed (not only the last week);
#  the ones that filed themselves on his "Filed by themselves" with "Wrong patient? Move". The automatic rule is unchanged.
#   1. /root/finance/slip_log.py      FROM 231aebde -> TO
#   2. /root/finance/check_screens.py FROM ac0e890a -> TO      clinic-finance restarted.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s854kit && cp -rp /root/deploy/repo/deploy_kits/S854_LAB_NO_ID /tmp/s854kit && bash /tmp/s854kit/install_S854_LAB_NO_ID.sh
#  DRY=1 before bash: every gate, the walks, the control and the live shape; nothing live changes.  --undo: both files back.
# =============================================================================
set -u
KIT="S854_LAB_NO_ID"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"; DMAP="${DMAP:-$ROOT/deploy/repo/claude_code_briefs/DUTY_MAP.json}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="slip_log.py check_screens.py"
from_of() { case "$1" in slip_log.py) echo 231aebde;; check_screens.py) echo ac0e890a;; esac; }
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s854_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
m8() { m5 "$1" | cut -c1-8; }
say() { echo "$@"; }
bak() { echo "$ROOT/finance/$1.bak_S854_$(from_of "$1")"; }
fget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fget /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES; do rm -f "$ROOT/finance/.$n.s854"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the files back"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/finance/$n"; done
  "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do say "   $n $(m8 "$ROOT/finance/$n") (expected $(from_of "$n"))"; done
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."; release_lock; exit 1; }
mkfin() { rm -rf "$SCR/fin_$1"; mkdir -p "$SCR/fin_$1" && find "$ROOT/finance" -maxdepth 1 -type f -name '*.py' -exec cp -p {} "$SCR/fin_$1/" \; && [ -f "$SCR/fin_$1/records.py" ]; }
pya() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 600 "$APY" -W ignore -s -B "$@" 2>&1); }

if [ "${1:-}" = "--undo" ]; then
  U=1; for n in $NAMES; do [ "$(m8 "$ROOT/finance/$n")" = "$(from_of "$n")" ] || U=0; done
  [ "$U" = 1 ] && { say "-- $KIT is not installed (both files at their FROM pins) - nothing to undo."; exit 0; }
  for n in $NAMES; do b=$(bak "$n"); [ -f "$b" ] && [ "$(m8 "$b")" = "$(from_of "$n")" ] || { say "!! no good backup $b - nothing undone"; exit 1; }; done
  for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || { say "!! $ROOT/finance/$n is $(m8 "$ROOT/finance/$n"), not this kit's - a later change is on it: nothing undone. Tell Claude."; exit 1; }; done
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/finance/$n"; done; "$SYSTEMCTL" restart "$FSVC"
  for n in $NAMES; do say "   $n $(m8 "$ROOT/finance/$n") (expected $(from_of "$n"))"; done
  h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but finance healthz is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE ($FSVC restarted, finance healthz 200)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES; do [ "$(m5 "$KDIR/$n")" = "$(to_of "$n")" ] || { say "!! [1/5] the kit's $n is not as built - nothing installed"; exit 1; }; done
for f in "$DB" "$ROOT/finance/slip_log.py" "$ROOT/finance/check_screens.py" "$DMAP"; do [ -f "$f" ] || { say "!! [1/5] $f missing - nothing installed"; exit 1; }; done
ALL=1; for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do fr=$(from_of "$n"); [ "$(m8 "$ROOT/finance/$n")" = "$fr" ] || stop "!! [2/5] $ROOT/finance/$n is $(m8 "$ROOT/finance/$n"), expected $fr - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do for n in $NAMES; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/$n" || stop "!! [2/5] $n does not compile on $p - nothing installed"; done; done
say "[2/5] the live pins exact; both files compile on both pythons"
"$APY" -c "import sqlite3,sys;s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=30);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close()" "$DB" "$SCR/finance.db" || stop "!! [3/5] could not copy the database - nothing installed"
{ mkfin old && mkfin new && for n in $NAMES; do \cp -p "$KDIR/$n" "$SCR/fin_new/$n" || exit 9; done; } || stop "!! [3/5] could not lay out the walks - nothing installed"
R1=$(pya "$KDIR/walk_s854.py" "$SCR/fin_new" "$SCR/fin_new" "$SCR/finance.db" | tail -1)
case "$R1" in "WALK OK 28/28") ;; *) stop "!! [3/5] walk_s854 (made-up patients on a copy) on the new files: $R1 - nothing installed";; esac
R1c=$(pya "$KDIR/walk_s854.py" "$SCR/fin_old" "$SCR/fin_old" "$SCR/finance.db" --control | tail -1)
case "$R1c" in "CONTROL: red "*) ;; *) stop "!! [3/5] walk_s854's control (the live files) did not go red: $R1c - nothing installed";; esac
W4n=$(pya "$KDIR/walk_s834.py" "$SCR/fin_new" "$DMAP" "$SCR/finance.db" | tail -1); W4o=$(pya "$KDIR/walk_s834.py" "$SCR/fin_old" "$DMAP" "$SCR/finance.db" | tail -1)
{ [ "$W4n" = "S834 walk: 34 green, 0 red" ] && [ "$W4o" = "$W4n" ]; } || stop "!! [3/5] S834's walk: new files '$W4n', live files '$W4o' (both must be 34 green) - nothing installed"
W6E="BAD E1 BAD E4 BAD E6 WALK RED 3 of 40"          # its three wording checks were superseded by S839 ("Free X-ray"); nothing else red
W6n=$(pya "$KDIR/walk_s836.py" "$SCR/fin_new" "$SCR/finance.db" | grep -E '^BAD|^WALK' | sed -E 's/^(BAD [A-Z0-9]+).*/\1/' | tr '\n' ' ' | sed 's/ *$//')
W6o=$(pya "$KDIR/walk_s836.py" "$SCR/fin_old" "$SCR/finance.db" | grep -E '^BAD|^WALK' | sed -E 's/^(BAD [A-Z0-9]+).*/\1/' | tr '\n' ' ' | sed 's/ *$//')
{ [ "$W6n" = "$W6E" ] && [ "$W6o" = "$W6E" ]; } || stop "!! [3/5] S836's walk: new files '$W6n', live files '$W6o' (expected '$W6E') - nothing installed"
\cp -p "$SCR/finance.db" "$SCR/shape.db"
RS=$(pya "$KDIR/shape_s854.py" "$SCR/fin_new" "$SCR/fin_old" "$SCR/fin_old" "$SCR/shape.db")
echo "$RS" | grep -E '^  ' | sed 's/^/      /'
RSL=$(echo "$RS" | tail -1)
case "$RSL" in "SHAPE OK "*) ;; *) echo "$RS" | grep -E '^FAIL' | sed 's/^/      /'; stop "!! [3/5] the live shape on a copy of the database: $RSL - nothing installed";; esac
say "[3/5] walk_s854 $R1 (control: $R1c); S834's walk the same on old and new ($W4n); S836's walk the same on old and new; live shape $RSL"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks, the control and the live shape green; nothing live changed"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$ROOT/finance/$n" "$b" && [ "$(m8 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
for n in $NAMES; do st="$ROOT/finance/.$n.s854"
  { cat "$KDIR/$n" > "$st" && chmod --reference="$ROOT/finance/$n" "$st" 2>/dev/null; chown --reference="$ROOT/finance/$n" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
for n in $NAMES; do mv -f "$ROOT/finance/.$n.s854" "$ROOT/finance/$n" || restore "the rename of $n"; done
for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
pg=$(fget /finance/slips/pending); case "$pg" in 200|302|303|401|403) ;; *) restore "Report baaki answered $pg";; esac
cp=$(fget /finance/records/xray-check); case "$cp" in 200|302|303|401|403) ;; *) restore "his Check karein page answered $cp";; esac
release_lock
say "[4/5] placed and read back: both files at their TO pins; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, Report baaki $pg, his Check karein $cp"
say "[5/5] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""
say "$KIT: DONE."
exit 0
