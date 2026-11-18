#!/bin/bash
# =============================================================================
#  install_S878_RECORDS_PAGE.sh · kit S878 (the parent, S484, 18-Nov-2026) · his word of today (F-1466, the mock-up v6):
#   1. /root/finance/records.py        FROM 29114ddd -> TO   his per-patient page /finance/records/p/<id> rebuilt on the one
#      reader (patient_events): banner with the full mobile and the diagnosis; the money a quiet "₹ ···" chip that opens on a
#      click (heads, months, free/concession counts, pharmacy net of returns, bill discounts); every day a folded card with
#      the Docterz line (analytical use on its face, the clinical lines inside), the pharmacy bill lines as in the Hub (item,
#      qty, pack, rate, line ₹, batch, exp), films and reports opening in place with a new-tab link; Expand all · Collapse
#      all · Top. The old page stays in the file as the fallback (_patient_html_s834). Other routes of records.py untouched.
#   2. /root/finance/patient_events.py FROM 4ad64172 -> TO   Sanjeevni's reader carries a 'dx' event per visit with a
#      diagnosis (dx_visit), sorted after the consultation line; nothing else changes (PLANNED line on the board, D646).
#   clinic-finance restarted.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s878kit && cp -rp /root/deploy/repo/deploy_kits/S878_RECORDS_PAGE /tmp/s878kit && bash /tmp/s878kit/install_S878_RECORDS_PAGE.sh
#  DRY=1 before bash: every gate, the walks, S876's and S834's proofs and the shape on a copy of the live database; nothing live changes.
#  --undo: the two files back.
# =============================================================================
set -u
KIT="S878_RECORDS_PAGE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
DMAP="${DMAP:-/root/deploy/repo/claude_code_briefs/DUTY_MAP.json}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="records.py patient_events.py"
from_of() { case "$1" in records.py) echo 29114ddd8e6d5d20e9daa4c2fef2e913;; patient_events.py) echo 4ad64172d39fbe6afd540a88e4c4656e;; esac; }
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s878_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
isfrom() { [ "$(m5 "$FIN/$1")" = "$(from_of "$1")" ]; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S878_$(from_of "$1" | cut -c1-8)"; }
fget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fget /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES; do rm -f "$FIN/.$n.s878"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the files back"
  for n in $NAMES; do [ -f "$(bak "$n")" ] && \cp -p "$(bak "$n")" "$FIN/$n"; done
  "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do say "   $n $(m5 "$FIN/$n" | cut -c1-8) (expected $(from_of "$n" | cut -c1-8))"; done
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."; release_lock; exit 1; }
pya() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 600 "$VPY" -W ignore -B "$@" 2>&1); }   # the app's python (F-1444: no -s)
CPDB='import sqlite3,sys;s=sqlite3.connect(sys.argv[1]);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close();s.close()'

if [ "${1:-}" = "--undo" ]; then
  U=1; for n in $NAMES; do isfrom "$n" || U=0; done
  [ "$U" = 1 ] && { say "-- $KIT is not installed - nothing to undo."; exit 0; }
  for n in $NAMES; do isfrom "$n" || [ "$(m5 "$FIN/$n")" = "$(to_of "$n")" ] || { say "!! $FIN/$n is $(m5 "$FIN/$n" | cut -c1-8), not this kit's - nothing undone. Tell Claude."; exit 1; }; done
  for n in $NAMES; do isfrom "$n" && continue; b=$(bak "$n"); [ -f "$b" ] && [ "$(m5 "$b")" = "$(from_of "$n")" ] || { say "!! no good backup $b - nothing undone"; exit 1; }; done
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo" > "$LOCK/owner"
  for n in $NAMES; do isfrom "$n" || \cp -p "$(bak "$n")" "$FIN/$n"; done; "$SYSTEMCTL" restart "$FSVC"
  h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but finance healthz is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE (records.py + patient_events.py back; $FSVC restarted, finance healthz 200)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES; do [ "$(m5 "$KDIR/$n")" = "$(to_of "$n")" ] || { say "!! [1/5] the kit's $n is not as built - nothing installed"; exit 1; }; done
[ -f "$DMAP" ] || { say "!! [1/5] $DMAP not found (S834's proof needs it) - nothing installed"; exit 1; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
ALL=1; for n in $NAMES; do [ "$(m5 "$FIN/$n")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do isfrom "$n" || stop "!! [2/5] $FIN/$n is $(m5 "$FIN/$n" | cut -c1-8), expected $(from_of "$n" | cut -c1-8) - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
# rebuilt here from the live bytes must give the very same TO bytes (F-472)
mkdir -p "$SCR/built" && "$APY" -B "$KDIR/make_s878.py" "$FIN" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/5] the builder refused on the live files - nothing installed"; }
for n in $NAMES; do [ "$(m5 "$SCR/built/$n")" = "$(to_of "$n")" ] || stop "!! [2/5] rebuilt from the live $n, not at the TO pin - nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do for n in $NAMES; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/$n" || stop "!! [2/5] $n does not compile on $p - nothing installed"; done; done
say "[2/5] the live pins exact; rebuilt from the live bytes at the TO pins; both files compile on both pythons"
lay() { local d="$SCR/$1"; rm -rf "$d"; mkdir -p "$d/finance_ui" && \cp -p "$FIN"/*.py "$d/" && \cp -p "$FIN"/finance_ui/*.html "$d/finance_ui/" 2>/dev/null; [ -f "$d/records.py" ]; }
lay fin_new && for n in $NAMES; do \cp -p "$KDIR/$n" "$SCR/fin_new/$n"; done && lay fin_old || stop "!! [3/5] could not lay out the walks - nothing installed"
R1=$(pya "$KDIR/walk_s878.py" "$SCR/fin_new" "$SCR/w_new" | tail -1)
case "$R1" in "WALK 28/28") ;; *) pya "$KDIR/walk_s878.py" "$SCR/fin_new" "$SCR/w_new2" | grep -E "FAIL|Error" | head -6; stop "!! [3/5] walk_s878 (made-up) on the new files: $R1 - nothing installed";; esac
R1c=$(pya "$KDIR/walk_s878.py" "$SCR/fin_old" "$SCR/w_old" | tail -1)
case "$R1c" in "WALK 28/28") stop "!! [3/5] walk_s878's control (the live files) did not go red - nothing installed";; esac
"$VPY" -c "$CPDB" "$FIN/finance.db" "$SCR/finance.db" >/dev/null && \cp -p "$SCR/finance.db" "$SCR/f2.db" && \cp -p "$SCR/finance.db" "$SCR/f3.db" || stop "!! [3/5] could not copy the database for the proofs - nothing installed"
O2=$(pya -u "$KDIR/synth_s876.py" "$SCR/fin_new" --real "$SCR/finance.db"); R2=$(printf '%s\n' "$O2" | tail -1); printf '%s\n' "$O2" | grep -E "FAIL|Traceback" | head -6 | sed 's/^/      /'
case "$R2" in "S876 synth: "*" ok, 0 failed") ;; *) stop "!! [3/5] S876's proof (the Hub's record panel) on the new files: $R2 - nothing installed. Tell Claude.";; esac
R3=$(S834_PYLIB=/nonexistent pya "$KDIR/walk_s834.py" "$SCR/fin_new" "$DMAP" "$SCR/f2.db" | tail -1)
case "$R3" in "S834 walk: "*" green, 0 red") ;; *) stop "!! [3/5] S834's walk (Check karein's due rule, in records.py) on the new files: $R3 - nothing installed. Tell Claude.";; esac
# the shape: his page for real IDs on a copy of the live database -- every one answers, carries the chip, no dialog
R4=$(pya "$KDIR/shape_s878.py" "$SCR/fin_new" "$SCR/f3.db" 60 | tail -1)
case "$R4" in "SHAPE OK ok="*" fail=0 "*) ;; *) stop "!! [3/5] the shape (real IDs on a copy of the live database): $R4 - nothing installed. Tell Claude.";; esac
say "[3/5] walk_s878 $R1 (made-up; control red: $R1c); S876's proof $R2; S834's walk $R3; the shape: $R4"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks, the proofs and the shape green; nothing live changed"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$FIN/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
for n in $NAMES; do st="$FIN/.$n.s878"; { cat "$KDIR/$n" > "$st" && chmod --reference="$FIN/$n" "$st" 2>/dev/null; chown --reference="$FIN/$n" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
for n in patient_events.py records.py; do mv -f "$FIN/.$n.s878" "$FIN/$n" || restore "the rename of $n"; done
for n in $NAMES; do [ "$(m5 "$FIN/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
# the page for every role (F-1445): signed out it must answer with the door (302/401/403), never a crash
PG=""; for u in /finance/records/p/ZZ9000 /finance/records /finance/records/xray-check /finance/sanjeevni/api/patient-events/healthz; do c=$(fget "$u"); case "$c" in 200|302|303|401|403|404) PG="$PG $c";; *) restore "the page $u answered $c";; esac; done
release_lock
say "[4/5] placed and read back: records.py + patient_events.py at their TO pins; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the pages answer$PG"
say "[5/5] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""; say "$KIT: DONE. Open any patient from https://followup.dr-manoj.in/finance/records"; exit 0
