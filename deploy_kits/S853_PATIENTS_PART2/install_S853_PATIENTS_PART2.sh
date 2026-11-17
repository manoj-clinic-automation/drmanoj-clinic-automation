#!/bin/bash
# =============================================================================
#  install_S853_PATIENTS_PART2.sh · kit S853 (the parent, S477, 17-Nov-2026) · D939 Part 2 (mock-up v16)
#  His Patients page, Part 2: the same months a year before (from his two Docterz exports, counts only) · Before they reach
#  you — Google · At the front desk — calls and WhatsApp, each caller once a day · Google reviews · the "Called" columns.
#   1. /root/finance/patients_page.py   FROM 595ce680 -> TO   (calls Part 2 at the end of each reading, inside a try)
#   2. /root/finance/patients_page.html FROM a2a8a17c -> TO   (the four new blocks, the Called columns)
#   3. NEW /root/finance/patients_part2.py, patients_history.json, patients_google.json
#   The old reading (patients_reading.dat) is set aside so the first open builds the new one. clinic-finance restarted.
#   It READS /root/wa/console.db, /root/wa/wa_inbox/inbox.db, /root/portal/wa_awaiting.db, /root/portal/gmb_store.db and
#   /root/portal/calls_console.py; it writes none of them.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s853kit && cp -rp /root/deploy/repo/deploy_kits/S853_PATIENTS_PART2 /tmp/s853kit && bash /tmp/s853kit/install_S853_PATIENTS_PART2.sh
#  DRY=1 before bash: every gate, both walks, their controls and the live shape; nothing live changes.
#  --undo: the two files back, the three new files set aside.
# =============================================================================
set -u
KIT="S853_PATIENTS_PART2"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
CONDB="${CONDB:-$ROOT/wa/console.db}"; INBDB="${INBDB:-$ROOT/wa/wa_inbox/inbox.db}"; MARKDB="${MARKDB:-$ROOT/portal/wa_awaiting.db}"
GMBDB="${GMBDB:-$ROOT/portal/gmb_store.db}"; CCPY="${CCPY:-$ROOT/portal/calls_console.py}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="patients_page.py patients_page.html"
NEW="patients_part2.py patients_history.json patients_google.json"
READING="$ROOT/finance/patients_reading.dat"
from_of() { case "$1" in patients_page.py) echo 595ce680946c9222995888945f2feb6a;; patients_page.html) echo a2a8a17cafde7a80bfa3c2403d4958f9;; esac; }
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s853_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { local f; f=$(from_of "$1"); echo "$ROOT/finance/$1.bak_S853_${f:0:8}"; }
aside() { echo "$ROOT/finance/$1.undone_S853"; }
fget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fget /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES $NEW; do rm -f "$ROOT/finance/.$n.s853"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the files back"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/finance/$n"; done
  for n in $NEW; do [ -f "$ROOT/finance/$n" ] && mv -f "$ROOT/finance/$n" "$(aside "$n")"; done
  rm -f "$READING"; [ -f "$READING.pre_S853" ] && mv -f "$READING.pre_S853" "$READING"
  "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do f=$(from_of "$n"); say "   $n $(m5 "$ROOT/finance/$n" | cut -c1-8) (expected ${f:0:8})"; done
  say "   the three new files set aside; $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
mkfin() { rm -rf "$SCR/fin_$1"; mkdir -p "$SCR/fin_$1" && find "$ROOT/finance" -maxdepth 1 -type f \( -name '*.py' -o -name '*.html' \) -exec cp -p {} "$SCR/fin_$1/" \; && [ -f "$SCR/fin_$1/records.py" ]; }
pya() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 600 "$APY" -W ignore -B "$@" 2>&1); }   # as the app runs: its user site included (flask)
pyv() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -s -B "$@" 2>&1); }
cpdb() { [ -f "$1" ] || return 1; "$APY" -c "import sqlite3,sys;s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=30);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close()" "$1" "$2"; }

if [ "${1:-}" = "--undo" ]; then
  U=1; for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(from_of "$n")" ] || U=0; done; for n in $NEW; do [ -e "$ROOT/finance/$n" ] && U=0; done
  [ "$U" = 1 ] && { say "-- $KIT is not installed (the page at its FROM pins, the new files absent) - nothing to undo."; exit 0; }
  for n in $NAMES; do b=$(bak "$n"); [ -f "$b" ] && [ "$(m5 "$b")" = "$(from_of "$n")" ] || { say "!! no good backup $b - nothing undone"; exit 1; }; done
  for n in $NAMES $NEW; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || { say "!! $ROOT/finance/$n is $(m5 "$ROOT/finance/$n" | cut -c1-8), not this kit's - a later change is on it: nothing undone. Tell Claude."; exit 1; }; done
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/finance/$n"; done; for n in $NEW; do mv -f "$ROOT/finance/$n" "$(aside "$n")"; done
  rm -f "$READING" "$READING.pre_S853"; "$SYSTEMCTL" restart "$FSVC"
  for n in $NAMES; do say "   $n $(m5 "$ROOT/finance/$n" | cut -c1-8) (expected $(from_of "$n" | cut -c1-8))"; done
  say "   patients_part2.py and the two .json files set aside as *.undone_S853"
  h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but finance healthz is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE ($FSVC restarted, finance healthz 200)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES $NEW; do [ "$(m5 "$KDIR/$n")" = "$(to_of "$n")" ] || { say "!! [1/5] the kit's $n is not as built - nothing installed"; exit 1; }; done
for n in $NAMES; do [ -f "$ROOT/finance/$n" ] || { say "!! [1/5] $ROOT/finance/$n missing - nothing installed"; exit 1; }; done
for f in "$DB" "$CONDB" "$INBDB" "$GMBDB" "$CCPY"; do [ -f "$f" ] || { say "!! [1/5] $f missing - nothing installed"; exit 1; }; done
ALL=1; for n in $NAMES $NEW; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do fr=$(from_of "$n"); [ "$(m5 "$ROOT/finance/$n")" = "$fr" ] || stop "!! [2/5] $ROOT/finance/$n is $(m5 "$ROOT/finance/$n" | cut -c1-8), expected ${fr:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
for n in $NEW; do [ -e "$ROOT/finance/$n" ] && stop "!! [2/5] $ROOT/finance/$n already exists and is not this kit's - STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do for n in patients_page.py patients_part2.py; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/$n" || stop "!! [2/5] $n does not compile on $p - nothing installed"; done; done
for n in patients_history.json patients_google.json; do "$APY" -c "import json,sys;json.load(open(sys.argv[1]))" "$KDIR/$n" || stop "!! [2/5] $n does not read - nothing installed"; done
say "[2/5] the live pins exact; the new files absent; both .py files compile on both pythons; both .json files read"
cpdb "$DB" "$SCR/finance.db" || stop "!! [3/5] could not copy the database for the walks - nothing installed"
"$VPY" -c "import sqlite3,sys;s=sqlite3.connect(sys.argv[1]);d=sqlite3.connect(sys.argv[2])
for (q,) in s.execute(\"select sql from sqlite_master where sql is not null and name not like 'sqlite_%'\"): d.execute(q)
d.commit()" "$SCR/finance.db" "$SCR/schema.db" || stop "!! [3/5] could not make the empty schema copy - nothing installed"
{ cpdb "$CONDB" "$SCR/console.db" && cpdb "$INBDB" "$SCR/inbox.db" && cpdb "$GMBDB" "$SCR/gmb.db"; } || stop "!! [3/5] could not copy the call record, the inbox or Review Assist's store - nothing installed"
MK="-"; [ -f "$MARKDB" ] && { cpdb "$MARKDB" "$SCR/marks.db" && MK="$SCR/marks.db" || stop "!! [3/5] could not copy the WhatsApp marks - nothing installed"; }
{ mkfin old && mkfin new && for n in $NAMES $NEW; do \cp -p "$KDIR/$n" "$SCR/fin_new/$n" || exit 9; done; } || stop "!! [3/5] could not lay out the walks - nothing installed"
R1A=$(pya "$KDIR/walk_s853.py" "$SCR/fin_new" "$CCPY" "$SCR/w853_new"); R1=$(echo "$R1A" | tail -1)
case "$R1" in "WALK 39/39") ;; *) echo "$R1A" | grep -E '^FAIL|Error|error' | cut -c1-160 | head -8 | sed 's/^/      /'; stop "!! [3/5] walk_s853 (made-up root) on the new files: $R1 - nothing installed";; esac
R1c=$(pya "$KDIR/walk_s853.py" "$SCR/fin_old" "$CCPY" "$SCR/w853_old" | tail -1)
case "$R1c" in "WALK 39/39") stop "!! [3/5] walk_s853's control (the live files) did not go red - nothing installed";; esac
R2=$(PATIENTS_CONSOLE_DB=/nonexistent/c.db PATIENTS_GMB_DB=/nonexistent/g.db pyv "$KDIR/walk_s851.py" "$SCR/fin_new" "$SCR/fin_new" "$SCR/schema.db" "$SCR/w851_new" | tail -1)
case "$R2" in "WALK 34/34") ;; *) stop "!! [3/5] S851's walk on the new files: $R2 - nothing installed";; esac
RS=$(pya "$KDIR/shape_s853.py" "$SCR/fin_new" "$SCR/fin_old" "$SCR/finance.db" "$SCR/console.db" "$SCR/inbox.db" "$SCR/gmb.db" "$MK" "$CCPY")
echo "$RS" | grep -E '^  ' | sed 's/^/      /'
RSL=$(echo "$RS" | tail -1)
case "$RSL" in "SHAPE OK "*) ;; *) echo "$RS" | grep -E '^FAIL' | sed 's/^/      /'; stop "!! [3/5] the live shape on copies of the stores: $RSL - nothing installed";; esac
say "[3/5] walk_s853 $R1 (made-up root; control red: ${R1c:-crashed}); S851's walk $R2 on the new files; live shape $RSL"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, both walks, the control and the live shape green; nothing live changed"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$ROOT/finance/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
REF="$ROOT/finance/patients_page.py"
for n in $NAMES $NEW; do st="$ROOT/finance/.$n.s853"
  { cat "$KDIR/$n" > "$st" && chmod --reference="$REF" "$st" 2>/dev/null; chown --reference="$REF" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
for n in $NEW; do mv -f "$ROOT/finance/.$n.s853" "$ROOT/finance/$n" || restore "the rename of $n"; done
for n in $NAMES; do mv -f "$ROOT/finance/.$n.s853" "$ROOT/finance/$n" || restore "the rename of $n"; done
for n in $NAMES $NEW; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
[ -f "$READING" ] && mv -f "$READING" "$READING.pre_S853"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
pg=$(fget /finance/console/patients); case "$pg" in 200|302|303|401|403) ;; *) restore "his page answered $pg";; esac
ap=$(fget /finance/console/api/patients); case "$ap" in 200|302|303|401|403) ;; *) restore "the page's reading answered $ap";; esac
rm -f "$READING.pre_S853"
release_lock
say "[4/5] placed and read back: five files at their TO pins; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the page answers $pg, its reading $ap (behind your login: the new reading is built on your first open; Part 2 on the live stores was proven by the shape at [3/5])"
say "[5/5] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""
say "$KIT: DONE. Your page: https://followup.dr-manoj.in/finance/console/patients"
exit 0
