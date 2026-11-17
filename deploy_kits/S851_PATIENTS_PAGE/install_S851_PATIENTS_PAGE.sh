#!/bin/bash
# =============================================================================
#  install_S851_PATIENTS_PAGE.sh · kit S851 (the parent, S474, 17-Nov-2026) · D939 Part 1 (mock-up v16)
#  His Patients page on the console: at a glance, readings and suggestions, month by month (new / seen before,
#  back within 30 days), the follow-ups he gave (kept / medicines / late / open / neither), by diagnosis group,
#  late returners, how much the diagnoses cover. Every number taps open its list of patients.
#   1. NEW /root/finance/patients_page.py and /root/finance/patients_page.html
#   2. /root/finance/owner_console.py  FROM 9f4b284d -> TO (the routes + one line in the month section).  clinic-finance restarted.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s851kit && cp -rp /root/deploy/repo/deploy_kits/S851_PATIENTS_PAGE /tmp/s851kit && bash /tmp/s851kit/install_S851_PATIENTS_PAGE.sh
#  DRY=1 before bash: every gate, the walk, its control and the live shape; nothing live changes.
#  --undo: owner_console back, the two new files set aside (the reading file patients_reading.dat stays; nothing reads it).
# =============================================================================
set -u
KIT="S851_PATIENTS_PAGE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="owner_console.py"
NEW="patients_page.py patients_page.html"
from_of() { case "$1" in owner_console.py) echo 9f4b284d9d4ac0702b03dd2fb3acd271;; esac; }
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s851_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { local f; f=$(from_of "$1"); echo "$ROOT/finance/$1.bak_S851_${f:0:8}"; }
aside() { echo "$ROOT/finance/$1.undone_S851"; }
fget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fget /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES $NEW; do rm -f "$ROOT/finance/.$n.s851"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the files back"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/finance/$n"; done
  for n in $NEW; do [ -f "$ROOT/finance/$n" ] && mv -f "$ROOT/finance/$n" "$(aside "$n")"; done
  "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do f=$(from_of "$n"); say "   $n $(m5 "$ROOT/finance/$n" | cut -c1-8) (expected ${f:0:8})"; done
  say "   the two new files set aside; $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
mkfin() { rm -rf "$SCR/fin_$1"; mkdir -p "$SCR/fin_$1" && find "$ROOT/finance" -maxdepth 1 -type f -name '*.py' -exec cp -p {} "$SCR/fin_$1/" \; && [ -f "$SCR/fin_$1/records.py" ]; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -s -B "$@" 2>&1); }

if [ "${1:-}" = "--undo" ]; then
  U=1; for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(from_of "$n")" ] || U=0; done; for n in $NEW; do [ -e "$ROOT/finance/$n" ] && U=0; done
  [ "$U" = 1 ] && { say "-- $KIT is not installed (owner_console at its FROM pin, the new files absent) - nothing to undo."; exit 0; }
  for n in $NAMES; do b=$(bak "$n"); [ -f "$b" ] && [ "$(m5 "$b")" = "$(from_of "$n")" ] || { say "!! no good backup $b - nothing undone"; exit 1; }; done
  for n in $NAMES $NEW; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || { say "!! $ROOT/finance/$n is $(m5 "$ROOT/finance/$n" | cut -c1-8), not this kit's - a later change is on it: nothing undone. Tell Claude."; exit 1; }; done
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/finance/$n"; done; for n in $NEW; do mv -f "$ROOT/finance/$n" "$(aside "$n")"; done; "$SYSTEMCTL" restart "$FSVC"
  for n in $NAMES; do say "   $n $(m5 "$ROOT/finance/$n" | cut -c1-8) (expected $(from_of "$n" | cut -c1-8))"; done
  say "   patients_page.py and .html set aside as *.undone_S851 (patients_reading.dat stays; nothing reads it)"
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
for n in $NEW; do [ -e "$ROOT/finance/$n" ] && stop "!! [2/5] $ROOT/finance/$n already exists and is not this kit's - STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do for n in owner_console.py patients_page.py; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/$n" || stop "!! [2/5] $n does not compile on $p - nothing installed"; done; done
say "[2/5] the live pin exact; the new files absent; both .py files compile on both pythons"
"$VPY" -c "import sqlite3,sys;s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=30);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close()" "$DB" "$SCR/finance.db" || stop "!! [3/5] could not copy the database for the walks - nothing installed"
"$VPY" -c "import sqlite3,sys;s=sqlite3.connect(sys.argv[1]);d=sqlite3.connect(sys.argv[2])
for (q,) in s.execute(\"select sql from sqlite_master where sql is not null and name not like 'sqlite_%'\"): d.execute(q)
d.commit()" "$SCR/finance.db" "$SCR/schema.db" || stop "!! [3/5] could not make the empty schema copy - nothing installed"
{ mkfin old && mkfin new && for n in $NAMES $NEW; do \cp -p "$KDIR/$n" "$SCR/fin_new/$n" || exit 9; done; } || stop "!! [3/5] could not lay out the walks - nothing installed"
R1=$(py "$KDIR/walk_s851.py" "$SCR/fin_new" "$SCR/fin_new" "$SCR/schema.db" "$SCR/w_new" | tail -1)
case "$R1" in "WALK 34/34") ;; *) stop "!! [3/5] walk_s851 (made-up root) on the new files: $R1 - nothing installed";; esac
R1c=$(py "$KDIR/walk_s851.py" "$SCR/fin_old" "$SCR/fin_old" "$SCR/schema.db" "$SCR/w_old" | tail -1)
case "$R1c" in "WALK 34/34") stop "!! [3/5] walk_s851's control (the live files) did not go red - nothing installed";; esac
RS=$(py "$KDIR/shape_s851.py" "$SCR/fin_new" "$SCR/fin_old" "$SCR/finance.db" "$SCR/shape" | tail -1)
case "$RS" in "SHAPE OK "*) ;; *) stop "!! [3/5] the live shape on a copy of the database: $RS - nothing installed";; esac
say "[3/5] walk_s851 $R1 (made-up root; control red: ${R1c:-crashed}); live shape $RS"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk, its control and the live shape green; nothing live changed"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$ROOT/finance/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
REF="$ROOT/finance/owner_console.py"
for n in $NAMES $NEW; do st="$ROOT/finance/.$n.s851"
  { cat "$KDIR/$n" > "$st" && chmod --reference="$REF" "$st" 2>/dev/null; chown --reference="$REF" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
for n in $NEW; do mv -f "$ROOT/finance/.$n.s851" "$ROOT/finance/$n" || restore "the rename of $n"; done
for n in $NAMES; do mv -f "$ROOT/finance/.$n.s851" "$ROOT/finance/$n" || restore "the rename of $n"; done
for n in $NAMES $NEW; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
pg=$(fget /finance/console/patients); case "$pg" in 200|302|303|401|403) ;; *) restore "his page answered $pg";; esac
ap=$(fget /finance/console/api/patients); case "$ap" in 200|302|303|401|403) ;; *) restore "the page's reading answered $ap";; esac
release_lock
say "[4/5] placed and read back: three files at their TO pins; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the page answers $pg, its reading $ap"
say "[5/5] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""
say "$KIT: DONE. Your page: https://followup.dr-manoj.in/finance/console/patients (also from the console's month section)."
exit 0
