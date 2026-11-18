#!/bin/bash
# =============================================================================
#  install_S876_HUB_RECORD_INLINE.sh · kit S876 (18-Nov-2026, Sanjeevni session 483) · D1007 · his OK 15:25 on the mock-up
#  On his Hub, a clinic ID on a bill or a sale return (and on the Returns card) opens the patient's record right under the
#  row: events newest first, in words, the paper one tap under each, "Open the full record" for the rest.
#   1. NEW /root/finance/patient_events.py (the one reader; read-only)
#   2. /root/finance/sanjeevni_day.py db30da9f -> TO (init mounts patient_events, as hub_cash)
#   3. /root/finance/finance_ui/finance_approvals.html 254c0bbf -> TO (4 anchors)
#  Rebuilt HERE from the live bytes (make_s876.py), checked against the TO pins; clinic-finance restarted.
#  Nothing is written to any table.  records.py (the parent's) is not touched.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s876kit && cp -rp /root/deploy/repo/deploy_kits/S876_HUB_RECORD_INLINE /tmp/s876kit && bash /tmp/s876kit/install_S876_HUB_RECORD_INLINE.sh
#  (DRY=1 before bash: every gate and the proofs; NOTHING written.)
# =============================================================================
set -u
KIT="S876_HUB_RECORD_INLINE"; KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
OLDK="${OLDK:-/root/deploy/repo/deploy_kits}"; LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
OLDN="finance/sanjeevni_day.py finance/finance_ui/finance_approvals.html"; NEWN="finance/patient_events.py"; NAMES="$OLDN $NEWN"
from_of() { case "$1" in finance/sanjeevni_day.py) echo db30da9f33ee8319b3c8c15f1d39fb12;; finance/finance_ui/finance_approvals.html) echo 254c0bbf47b18a539437a11dec831b0a;; finance/patient_events.py) echo NEW;; esac; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s876_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { local f; f=$(from_of "$1"); echo "$ROOT/$1.bak_S876_${f:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s876"; }
hz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { hz /finance/healthz; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES; do rm -f "$(stg "$n")"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
PLACING=0; PLACED=0; trap on_exit EXIT
on_sig() { if [ "$PLACING" = 1 ]; then restore "interrupted while placing"; fi; [ "$PLACED" = 1 ] && { say "!! interrupted after the install finished - the files ARE placed; undo: undo_s876.sh"; release_lock; exit 1; }
  say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
stop() { say "$1"; release_lock; exit 1; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting the files back"
  for n in $OLDN; do \cp -p "$(bak "$n")" "$ROOT/$n"; done; rm -f "$ROOT/$NEWN"; "$SYSTEMCTL" restart "$FSVC" || true
  for n in $OLDN; do f=$(from_of "$n"); say "   $n $(m5 "$ROOT/$n" | cut -c1-8) (expected ${f:0:8})"; done
  [ -e "$ROOT/$NEWN" ] && say "   $NEWN STILL PRESENT" || say "   $NEWN removed (it was new)"
  say "   $FSVC restarted, finance healthz $(wait200). Nothing was written to any table. Send a photo of this screen to Claude."; release_lock; exit 1; }
lay() { local d="$SCR/root_$1"; rm -rf "$d"; mkdir -p "$d/finance/finance_ui" \
  && find "$ROOT/finance" -maxdepth 1 -type f \( -name '*.py' -o -name '*.html' -o -name '*.sql' -o -name '*.json' \) -exec cp -p {} "$d/finance/" \; \
  && \cp -p "$ROOT"/finance/finance_ui/*.html "$d/finance/finance_ui/" 2>/dev/null; [ -f "$d/finance/sanjeevni_day.py" ]; }
synth() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -u -W ignore -B "$KDIR/synth_s876.py" "$@" 2>&1); }
s874() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -u -W ignore -B "$OLDK/S874_HUB_SHORT_MOBILE_CALL/synth_s874.py" "$1" "$2" 2>&1); }
jrn() { if [ -n "${JOURNAL_CMD:-}" ]; then $JOURNAL_CMD; else journalctl -u "$FSVC" --since "@$1" --no-pager 2>/dev/null; fi; }
CPDB='import sqlite3,sys;s=sqlite3.connect("file:%s?mode=ro"%sys.argv[1],uri=True,timeout=60);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close();s.close();print("copied")'
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES; do [ -n "$(to_of "$n")" ] || { say "!! [1/5] no TO pin for $n - nothing installed"; exit 1; }; done
for n in $OLDN; do [ -f "$ROOT/$n" ] || { say "!! [1/5] the live file $n is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/5] $DB missing - nothing installed"; exit 1; }
[ -f "$OLDK/S874_HUB_SHORT_MOBILE_CALL/synth_s874.py" ] || { say "!! [1/5] S874's proof is not in $OLDK - publish first. Nothing installed."; exit 1; }
ALL=1; for n in $NAMES; do [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR/built/finance/finance_ui" && chmod 700 "$SCR" || { say "!! cannot make $SCR"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $OLDN; do fr=$(from_of "$n"); [ "$(m5 "$ROOT/$n")" = "$fr" ] || stop "!! [2/5] $ROOT/$n is $(m5 "$ROOT/$n" | cut -c1-8), expected ${fr:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
[ -e "$ROOT/$NEWN" ] && stop "!! [2/5] $ROOT/$NEWN already exists and is not this kit's - STOP, nothing installed. Tell Claude."
"$APY" -B make_s876.py "$ROOT/finance" "$SCR/built/finance" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/5] the builder refused - nothing installed"; }
for n in $NAMES; do [ "$(m5 "$SCR/built/$n")" = "$(to_of "$n")" ] || stop "!! [2/5] rebuilt, $n is not at its TO pin - nothing installed"; done
for py in "$APY" "$VPY"; do for f in sanjeevni_day.py patient_events.py; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/finance/$f" || stop "!! [2/5] $f does not compile on $py - nothing installed"; done; done
say "[2/5] two live pins exact, the new file absent; rebuilt here at the TO pins; both .py compile on both pythons"
"$VPY" -c "$CPDB" "$DB" "$SCR/finance.db" >/dev/null && \cp -p "$SCR/finance.db" "$SCR/f2.db" && \cp -p "$SCR/finance.db" "$SCR/f3.db" \
  && \cp -p "$SCR/finance.db" "$SCR/f4.db" || stop "!! [3/5] could not copy the database for the proof - nothing installed"
lay new && for n in $NAMES; do \cp -p "$SCR/built/$n" "$SCR/root_new/$n"; done || stop "!! [3/5] could not lay out the proof - nothing installed"
O=$(synth "$SCR/root_new/finance" --real "$SCR/finance.db"); R=$(printf '%s\n' "$O" | tail -1); printf '%s\n' "$O" | grep -E "FAIL|Traceback" | head -6 | sed 's/^/      /'
case "$R" in "S876 synth: "*" ok, 0 failed") ;; *) stop "!! [3/5] synth_s876 (made-up + every ID on a copy of the live database): $R - nothing installed";; esac
lay old || stop "!! [3/5] could not lay out the control - nothing installed"
R0=$(synth "$SCR/root_old/finance" | tail -1); case "$R0" in *" ok, 0 failed") stop "!! [3/5] the control on the live files did not go red ($R0) - nothing installed";; esac
# S874's proof on both: a check may fail on the rebuilt files only if it already fails on the live ones -- save its T9, a frozen
# count of s874Mob( calls on the page that this kit's record header raises by one (the same renderer reused; S876's T25-T32 prove the page).
O4=$(s874 "$SCR/root_new/finance" "$SCR/f3.db"); O4o=$(s874 "$SCR/root_old/finance" "$SCR/f4.db")
R4=$(printf '%s\n' "$O4" | tail -1); R4o=$(printf '%s\n' "$O4o" | tail -1)
case "$R4" in "SYNTH S874: "*) ;; *) stop "!! [3/5] S874's proof did not finish on the rebuilt files ($R4) - nothing installed";; esac
case "$R4o" in "SYNTH S874: "*) ;; *) stop "!! [3/5] S874's proof did not finish on the live files ($R4o) - nothing installed";; esac
WORSE=$(comm -23 <(printf '%s\n' "$O4" | grep '^FAIL ' | sort -u) <(printf '%s\n' "$O4o" | grep '^FAIL ' | sort -u) | grep -v '^FAIL T9 the page: the mobile renderer')
[ -z "$WORSE" ] || stop "!! [3/5] S874's own proof is WORSE on the rebuilt files: $WORSE - nothing installed"
say "[3/5] proof: $R; control on the live files: red ($R0); S874's proof: rebuilt $R4 / live $R4o (not worse)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the proofs green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for n in $OLDN; do b=$(bak "$n"); { \cp -p "$ROOT/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
REF="$ROOT/finance/sanjeevni_day.py"
for n in $NAMES; do st=$(stg "$n"); { cat "$SCR/built/$n" > "$st" && chmod --reference="$REF" "$st" 2>/dev/null; chown --reference="$REF" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
PLACING=1
for n in $NAMES; do mv -f "$(stg "$n")" "$ROOT/$n" || restore "the rename of $n"; done
for n in $NAMES; do [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
c2=$(hz /finance/sanjeevni/api/patient-events/healthz)
case "$c2" in 200|302|401|403) ;; *) restore "the record door is not mounted (healthz $c2; 200 or a login answer means mounted, F-1439)";; esac
jrn "$T0" | grep -q "patient_events not mounted" && restore "the service log says: patient_events not mounted"
PLACING=0; PLACED=1; release_lock
say "[4/5] placed and read back at the TO pins; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the record door $c2 (mounted)"
say "[5/5] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s876.sh  (the two backups back, the new file out, $FSVC restarted). Nothing was written to any table."
say ""; say "$KIT: DONE. Reload the Hub (Ctrl+F5): https://followup.dr-manoj.in/finance/approvals -- tap a clinic ID on a bill or a return in a day."
exit 0
