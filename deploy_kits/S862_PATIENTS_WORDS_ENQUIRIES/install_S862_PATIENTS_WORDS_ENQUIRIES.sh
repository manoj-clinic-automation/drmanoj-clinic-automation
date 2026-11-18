#!/bin/bash
# =============================================================================
#  install_S862_PATIENTS_WORDS_ENQUIRIES.sh · kit S862 (the parent, S480, 18-Nov-2026) · his "go" 07:59
#  His Patients page, the last pieces but Google's mail:
#   * Diagnosis words to place -- each unrecognised word with the group the page suggests; Place writes his choice to
#     dx_term_map (dx_feed.py's own table) and every visit is re-read; Undo takes it back.
#   * At the front desk -- "Enquiry callers who became patients", month by month, each figure opening its clinic IDs.
#   1. /root/finance/patients_page.py   FROM 561c6bf4 -> TO
#   2. /root/finance/patients_page.html FROM 62e5dc88 -> TO
#   3. /root/finance/patients_part2.py  FROM 0277cb5c -> TO
#   The old reading (patients_reading.dat) is set aside so the first open builds the new one. clinic-finance restarted.
#   It READS /root/wa/console.db and /root/portal/calls_console.py; the only new write is his own tap (dx_term_map + the
#   re-read of dx_visit by dx_feed.reclassify).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s862kit && cp -rp /root/deploy/repo/deploy_kits/S862_PATIENTS_WORDS_ENQUIRIES /tmp/s862kit && bash /tmp/s862kit/install_S862_PATIENTS_WORDS_ENQUIRIES.sh
#  DRY=1 before bash: every gate, the walks, the control and the live shape; nothing live changes.
#  --undo: the three files back (a word he placed stays placed: dx_term_map is his record, dx_feed keeps using it).
# =============================================================================
set -u
KIT="S862_PATIENTS_WORDS_ENQUIRIES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
CONDB="${CONDB:-$ROOT/wa/console.db}"; CCPY="${CCPY:-$ROOT/portal/calls_console.py}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NODE="${NODE:-$(command -v node 2>/dev/null || true)}"
NAMES="patients_page.py patients_page.html patients_part2.py"
READING="$ROOT/finance/patients_reading.dat"
from_of() { case "$1" in patients_page.py) echo 561c6bf442c3bc40dde695e96d88bddc;; patients_page.html) echo 62e5dc884c30a83ae0e3314b4ea1003b;; patients_part2.py) echo 0277cb5cb32f3b95c420ca6745e19e7e;; esac; }
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s862_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { local f; f=$(from_of "$1"); echo "$ROOT/finance/$1.bak_S862_${f:0:8}"; }
fget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fget /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES; do rm -f "$ROOT/finance/.$n.s862"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the files back"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/finance/$n"; done
  rm -f "$READING"; [ -f "$READING.pre_S862" ] && mv -f "$READING.pre_S862" "$READING"
  "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do f=$(from_of "$n"); say "   $n $(m5 "$ROOT/finance/$n" | cut -c1-8) (expected ${f:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
mkfin() { rm -rf "$SCR/fin_$1"; mkdir -p "$SCR/fin_$1" && find "$ROOT/finance" -maxdepth 1 -type f \( -name '*.py' -o -name '*.html' \) -exec cp -p {} "$SCR/fin_$1/" \; && [ -f "$SCR/fin_$1/dx_feed.py" ] && [ -f "$SCR/fin_$1/diagnosis_normalizer.py" ]; }
pya() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 600 "$APY" -W ignore -B "$@" 2>&1); }   # as the app runs: its user site included (flask) -- no -s (F-1444)
cpdb() { [ -f "$1" ] || return 1; "$APY" -c "import sqlite3,sys;s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=30);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close()" "$1" "$2"; }

if [ "${1:-}" = "--undo" ]; then
  U=1; for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(from_of "$n")" ] || U=0; done
  [ "$U" = 1 ] && { say "-- $KIT is not installed (the three files at their FROM pins) - nothing to undo."; exit 0; }
  for n in $NAMES; do b=$(bak "$n"); [ -f "$b" ] && [ "$(m5 "$b")" = "$(from_of "$n")" ] || { say "!! no good backup $b - nothing undone"; exit 1; }; done
  for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || { say "!! $ROOT/finance/$n is $(m5 "$ROOT/finance/$n" | cut -c1-8), not this kit's - a later change is on it: nothing undone. Tell Claude."; exit 1; }; done
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/finance/$n"; done
  rm -f "$READING" "$READING.pre_S862"; "$SYSTEMCTL" restart "$FSVC"
  for n in $NAMES; do say "   $n $(m5 "$ROOT/finance/$n" | cut -c1-8) (expected $(from_of "$n" | cut -c1-8))"; done
  h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but finance healthz is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE ($FSVC restarted, finance healthz 200). Words you placed stay placed."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES; do [ "$(m5 "$KDIR/$n")" = "$(to_of "$n")" ] || { say "!! [1/5] the kit's $n is not as built - nothing installed"; exit 1; }; done
for n in $NAMES; do [ -f "$ROOT/finance/$n" ] || { say "!! [1/5] $ROOT/finance/$n missing - nothing installed"; exit 1; }; done
for f in "$DB" "$CONDB" "$CCPY"; do [ -f "$f" ] || { say "!! [1/5] $f missing - nothing installed"; exit 1; }; done
ALL=1; for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do fr=$(from_of "$n"); [ "$(m5 "$ROOT/finance/$n")" = "$fr" ] || stop "!! [2/5] $ROOT/finance/$n is $(m5 "$ROOT/finance/$n" | cut -c1-8), expected ${fr:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do for n in patients_page.py patients_part2.py; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/$n" || stop "!! [2/5] $n does not compile on $p - nothing installed"; done; done
say "[2/5] the live pins exact; both .py files compile on both pythons"
cpdb "$DB" "$SCR/finance.db" || stop "!! [3/5] could not copy the database for the walks - nothing installed"
"$APY" -c "import sqlite3,sys;s=sqlite3.connect(sys.argv[1]);d=sqlite3.connect(sys.argv[2])
for (q,) in s.execute(\"select sql from sqlite_master where sql is not null and name not like 'sqlite_%'\"): d.execute(q)
d.commit()" "$SCR/finance.db" "$SCR/schema.db" || stop "!! [3/5] could not make the empty schema copy - nothing installed"
cpdb "$CONDB" "$SCR/console.db" || stop "!! [3/5] could not copy the call record - nothing installed"
{ mkfin old && mkfin new && for n in $NAMES; do \cp -p "$KDIR/$n" "$SCR/fin_new/$n" || exit 9; done; } || stop "!! [3/5] could not lay out the walks - nothing installed"
R1A=$(pya "$KDIR/walk_s862.py" "$SCR/fin_new" "$CCPY" "$SCR/w862_new" "$NODE"); R1=$(echo "$R1A" | tail -1)
case "$R1" in "WALK 55/55"|"WALK 47/47") ;; *) echo "$R1A" | grep -E '^FAIL|Error|error' | cut -c1-160 | head -8 | sed 's/^/      /'; stop "!! [3/5] walk_s862 (made-up root) on the new files: $R1 - nothing installed";; esac
R1c=$(pya "$KDIR/walk_s862.py" "$SCR/fin_old" "$CCPY" "$SCR/w862_old" "$NODE" | tail -1)
case "$R1c" in "WALK 55/55"|"WALK 47/47") stop "!! [3/5] walk_s862's control (the live files) did not go red - nothing installed";; esac
R2=$(pya "$KDIR/walk_s853.py" "$SCR/fin_new" "$CCPY" "$SCR/w853_new" | tail -1)
case "$R2" in "WALK 39/39") ;; *) stop "!! [3/5] S853's walk on the new files: $R2 - nothing installed";; esac
R3=$(PATIENTS_CONSOLE_DB=/nonexistent/c.db PATIENTS_GMB_DB=/nonexistent/g.db pya "$KDIR/walk_s851.py" "$SCR/fin_new" "$SCR/fin_new" "$SCR/schema.db" "$SCR/w851_new" | tail -1)
case "$R3" in "WALK 34/34") ;; *) stop "!! [3/5] S851's walk on the new files: $R3 - nothing installed";; esac
RS=$(pya "$KDIR/shape_s862.py" "$SCR/fin_new" "$SCR/fin_old" "$SCR/finance.db" "$SCR/console.db" "$CCPY")
echo "$RS" | grep -E '^  ' | sed 's/^/      /'
RSL=$(echo "$RS" | tail -1)
case "$RSL" in "SHAPE OK"*) ;; *) stop "!! [3/5] the live shape on copies of the stores: $RSL - nothing installed";; esac
say "[3/5] walk_s862 $R1 (made-up root; control red: ${R1c:-crashed}); S853's walk $R2, S851's walk $R3 on the new files; live shape $RSL"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks, the control and the live shape green; nothing live changed"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$ROOT/finance/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
REF="$ROOT/finance/patients_page.py"
for n in $NAMES; do st="$ROOT/finance/.$n.s862"
  { cat "$KDIR/$n" > "$st" && chmod --reference="$REF" "$st" 2>/dev/null; chown --reference="$REF" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
for n in patients_part2.py patients_page.py patients_page.html; do mv -f "$ROOT/finance/.$n.s862" "$ROOT/finance/$n" || restore "the rename of $n"; done
for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
[ -f "$READING" ] && mv -f "$READING" "$READING.pre_S862"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
pg=$(fget /finance/console/patients); case "$pg" in 200|302|303|401|403) ;; *) restore "his page answered $pg";; esac
ap=$(fget /finance/console/api/patients); case "$ap" in 200|302|303|401|403) ;; *) restore "the page's reading answered $ap";; esac
rm -f "$READING.pre_S862"
release_lock
say "[4/5] placed and read back: three files at their TO pins; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the page answers $pg, its reading $ap"
say "[5/5] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""
say "$KIT: DONE. Your page: https://followup.dr-manoj.in/finance/console/patients"
exit 0
