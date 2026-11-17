#!/bin/bash
# =============================================================================
#  install_S852_SMALL_FIXES.sh · kit S852 (the parent, S474, 17-Nov-2026) · AF-41, F-1430, F-1418
#  1. his console: the "days to approve" line says how long the oldest medical day has waited, and names a day passed over
#     while later days were approved (it turns red)                                     owner_console.py fe5e915c -> TO
#  2. the slips' radd door refuses a name typed as the clinic ID, as the other doors do  parchi_desk.py   de24e3a4 -> TO
#  3. the month page's Scan App groups: a receipt, statement or summary is not money; a challan only when final; a joined
#     page once; a credit note LESS, from the group of the bill it is against          month_read.py    b2d30289 -> TO
#  clinic-finance restarted.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s852kit && cp -rp /root/deploy/repo/deploy_kits/S852_SMALL_FIXES /tmp/s852kit && bash /tmp/s852kit/install_S852_SMALL_FIXES.sh
#  DRY=1 before bash: every gate, the walks, the control and the live shape; nothing live changes. --undo: the three back.
# =============================================================================
set -u
KIT="S852_SMALL_FIXES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="owner_console.py parchi_desk.py month_read.py"
ADB="${ADB:-$ROOT/assetapp/assets.db}"; DUTY="${DUTY:-/root/deploy/repo/claude_code_briefs/DUTY_MAP.json}"
from_of() { case "$1" in owner_console.py) echo fe5e915cd2b0329e5949748e102386e6;; parchi_desk.py) echo de24e3a480f7101e0dfebc95af329ae4;;
  month_read.py) echo b2d30289fc109f1d919757a432c68079;; esac; }
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s852_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { local f; f=$(from_of "$1"); echo "$ROOT/finance/$1.bak_S852_${f:0:8}"; }
aside() { echo "$ROOT/finance/$1.undone_S852"; }
fget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fget /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES; do rm -f "$ROOT/finance/.$n.s852"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the files back"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/finance/$n"; done
  "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do f=$(from_of "$n"); say "   $n $(m5 "$ROOT/finance/$n" | cut -c1-8) (expected ${f:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
mkfin() { rm -rf "$SCR/fin_$1"; mkdir -p "$SCR/fin_$1" && find "$ROOT/finance" -maxdepth 1 -type f -name '*.py' -exec cp -p {} "$SCR/fin_$1/" \; && find "$ROOT/finance" -maxdepth 1 -type f -name '*.html' -exec cp -p {} "$SCR/fin_$1/" \; && [ -f "$SCR/fin_$1/records.py" ]; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -s -B "$@" 2>&1); }

if [ "${1:-}" = "--undo" ]; then
  U=1; for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(from_of "$n")" ] || U=0; done;
  [ "$U" = 1 ] && { say "-- $KIT is not installed (the three at their FROM pins) - nothing to undo."; exit 0; }
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
[ -f "$ADB" ] || stop "!! [2/5] $ADB missing - nothing installed"; [ -f "$DUTY" ] || stop "!! [2/5] $DUTY missing - nothing installed"
say "[2/5] the live pins exact; the three files compile on both pythons"
"$VPY" -c "import sqlite3,sys;s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=30);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close()" "$DB" "$SCR/finance.db" || stop "!! [3/5] could not copy the database for the walks - nothing installed"
"$VPY" -c "import sqlite3,sys;s=sqlite3.connect(sys.argv[1]);d=sqlite3.connect(sys.argv[2])
for (q,) in s.execute(\"select sql from sqlite_master where sql is not null and name not like 'sqlite_%'\"): d.execute(q)
d.commit()" "$SCR/finance.db" "$SCR/schema.db" || stop "!! [3/5] could not make the empty schema copy - nothing installed"
"$VPY" -c "import sqlite3,sys;s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=30);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close()" "$ADB" "$SCR/assets.db" || stop "!! [3/5] could not copy the Scan App's database for the live shape - nothing installed"
{ mkfin old && mkfin new && for n in $NAMES; do \cp -p "$KDIR/$n" "$SCR/fin_new/$n" || exit 9; done; } || stop "!! [3/5] could not lay out the walks - nothing installed"
R1=$(py "$KDIR/walk_s852.py" "$SCR/fin_new" "$SCR/schema.db" "$SCR/w_new" "$DUTY" | tail -1)
case "$R1" in "WALK 18/18") ;; *) stop "!! [3/5] walk_s852 (made-up root) on the new files: $R1 - nothing installed";; esac
R1c=$(py "$KDIR/walk_s852.py" "$SCR/fin_old" "$SCR/schema.db" "$SCR/w_old" "$DUTY" | tail -1)
case "$R1c" in "WALK 18/18") stop "!! [3/5] walk_s852's control (the live files) did not go red - nothing installed";; esac
RS=$(py "$KDIR/shape_s852.py" "$SCR/fin_new" "$SCR/fin_old" "$SCR/finance.db" "$SCR/assets.db" "$SCR/shape" "$DUTY")
RSL=$(echo "$RS" | tail -1); RSN=$(echo "$RS" | grep "no longer counted" | sed 's/^ *//')
case "$RSL" in "SHAPE OK "*) ;; *) stop "!! [3/5] the live shape on copies of the databases: $RSL - nothing installed";; esac
R6=$(py "$KDIR/walk_s846.py" "$SCR/fin_new" "$SCR/fin_new" "$SCR/schema.db" "$SCR/w846" | tail -1)
case "$R6" in "WALK 42/42") ;; *) stop "!! [3/5] walk_s846 (S846's slips page) on the new files: $R6 - nothing installed";; esac
R5=$(py "$KDIR/walk_s851.py" "$SCR/fin_new" "$SCR/fin_new" "$SCR/schema.db" "$SCR/w851" | tail -1)
case "$R5" in "WALK 34/34") ;; *) stop "!! [3/5] walk_s851 (the Patients page) on the new files: $R5 - nothing installed";; esac
mkdir -p "$SCR/k844" && \cp -p "$KDIR/parchi_desk.py" "$SCR/k844/" || stop "!! [3/5] could not lay out walk_s844 - nothing installed"
R4=$(py "$KDIR/walk_s844.py" "$SCR/k844" "$SCR/fin_old" "$SCR/finance.db" | tail -1)
case "$R4" in "WALK OK 31/31") ;; *) stop "!! [3/5] walk_s844 (S844's desk) on the new parchi_desk: $R4 - nothing installed";; esac
say "[3/5] walk_s852 $R1 (made-up root; control red: ${R1c:-crashed}); live shape $RSL ($RSN); walk_s846 $R6; walk_s851 $R5; walk_s844 $R4"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks, the control and the live shape green; nothing live changed"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$ROOT/finance/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
REF="$ROOT/finance/owner_console.py"
for n in $NAMES; do st="$ROOT/finance/.$n.s852"
  { cat "$KDIR/$n" > "$st" && chmod --reference="$REF" "$st" 2>/dev/null; chown --reference="$REF" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
for n in $NAMES; do mv -f "$ROOT/finance/.$n.s852" "$ROOT/finance/$n" || restore "the rename of $n"; done
for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
pg=$(fget /finance/console); case "$pg" in 200|302|303|401|403) ;; *) restore "his console answered $pg";; esac
ap=$(fget /finance/slips); case "$ap" in 200|302|303|401|403) ;; *) restore "the slips page answered $ap";; esac
release_lock
say "[4/5] placed and read back: three files at their TO pins; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the console answers $pg, the slips page $ap"
say "[5/5] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""
say "$KIT: DONE. Your console's 'days to approve' line now says how long the oldest day has waited: https://followup.dr-manoj.in/finance/console"
exit 0
