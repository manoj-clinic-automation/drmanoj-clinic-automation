#!/bin/bash
# =============================================================================
#  install_S874_HUB_SHORT_MOBILE_CALL.sh · kit S874 (18-Nov-2026, Sanjeevni session 482) · his words 13:41
#  The day panel names its OWN short with Accept (write off) / Add an entry; every bill and return on his Hub carries the patient's FULL
#  mobile (the Call Console's patient mirror by clinic ID, read-only) with a Call button through the portal's own click-to-call door.
#   1. /root/finance/sanjeevni_day.py 4359d048 -> TO (v1.4, whole)      2. /root/finance/finance_ui/finance_approvals.html 1f594b5f -> TO (4 anchors)
#  Rebuilt HERE from the live bytes (make_s874.py), checked against the TO pins; clinic-finance restarted. Nothing written to any table.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s874kit && cp -rp /root/deploy/repo/deploy_kits/S874_HUB_SHORT_MOBILE_CALL /tmp/s874kit && bash /tmp/s874kit/install_S874_HUB_SHORT_MOBILE_CALL.sh
#  (DRY=1 before bash: every gate and the proofs; NOTHING written.)
# =============================================================================
set -u
KIT="S874_HUB_SHORT_MOBILE_CALL"; KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
OLDK="${OLDK:-/root/deploy/repo/deploy_kits}"; LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="finance/sanjeevni_day.py finance/finance_ui/finance_approvals.html"
from_of() { case "$1" in finance/sanjeevni_day.py) echo 4359d04826ad508867be3e9e880d9168;; finance/finance_ui/finance_approvals.html) echo 1f594b5f8a750b90f16c590abada0bdc;; esac; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s874_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { local f; f=$(from_of "$1"); echo "$ROOT/$1.bak_S874_${f:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s874"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES; do rm -f "$(stg "$n")"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
PLACING=0; trap on_exit EXIT
on_sig() { if [ "$PLACING" = 1 ]; then restore "interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
stop() { say "$1"; release_lock; exit 1; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting the two files back"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/$n"; done; "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do f=$(from_of "$n"); say "   $n $(m5 "$ROOT/$n" | cut -c1-8) (expected ${f:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Nothing was written to any table. Send a photo of this screen to Claude."; release_lock; exit 1; }
lay() { local d="$SCR/root_$1"; rm -rf "$d"; mkdir -p "$d/finance/finance_ui" \
  && find "$ROOT/finance" -maxdepth 1 -type f \( -name '*.py' -o -name '*.html' -o -name '*.sql' -o -name '*.json' \) -exec cp -p {} "$d/finance/" \; \
  && \cp -p "$ROOT"/finance/finance_ui/*.html "$d/finance/finance_ui/" 2>/dev/null; [ -f "$d/finance/sanjeevni_day.py" ]; }
synth() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -u -W ignore -B "$KDIR/synth_s874.py" "$1" "$2" 2>&1); }
s869() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -u -W ignore -B "$OLDK/S869_HUB_DAYS_CASH/synth_s869.py" "$1" "$2" --box 2>&1 | tail -1); }
CPDB='import sqlite3,sys;s=sqlite3.connect("file:%s?mode=ro"%sys.argv[1],uri=True,timeout=60);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close();s.close();print("copied")'
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES; do [ -n "$(to_of "$n")" ] && [ -f "$ROOT/$n" ] || { say "!! [1/5] no TO pin or the live file $n is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/5] $DB missing - nothing installed"; exit 1; }
[ -f "$OLDK/S869_HUB_DAYS_CASH/synth_s869.py" ] || { say "!! [1/5] S869's proof is not in $OLDK - publish first. Nothing installed."; exit 1; }
ALL=1; for n in $NAMES; do [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR/built/finance/finance_ui" && chmod 700 "$SCR" || { say "!! cannot make $SCR"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do fr=$(from_of "$n"); [ "$(m5 "$ROOT/$n")" = "$fr" ] || stop "!! [2/5] $ROOT/$n is $(m5 "$ROOT/$n" | cut -c1-8), expected ${fr:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
"$APY" -B make_s874.py "$ROOT/finance" "$SCR/built/finance" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/5] the builder refused - nothing installed"; }
for n in $NAMES; do [ "$(m5 "$SCR/built/$n")" = "$(to_of "$n")" ] || stop "!! [2/5] rebuilt, $n is not at its TO pin - nothing installed"; done
for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/finance/sanjeevni_day.py" || stop "!! [2/5] sanjeevni_day.py does not compile on $py - nothing installed"; done
say "[2/5] two live pins exact; rebuilt here at their TO pins; compiles on both pythons"
"$VPY" -c "$CPDB" "$DB" "$SCR/finance.db" >/dev/null && \cp -p "$SCR/finance.db" "$SCR/f2.db" && \cp -p "$SCR/finance.db" "$SCR/f3.db" || stop "!! [3/5] could not copy the database for the proof - nothing installed"
lay new && for n in $NAMES; do \cp -p "$SCR/built/$n" "$SCR/root_new/$n"; done || stop "!! [3/5] could not lay out the proof - nothing installed"
O=$(synth "$SCR/root_new/finance" "$SCR/finance.db"); R=$(printf '%s\n' "$O" | tail -1); printf '%s\n' "$O" | grep -E "^FAIL|Traceback" | head -6 | sed 's/^/      /'
case "$R" in "SYNTH S874: "*" PASS, 0 FAIL") ;; *) stop "!! [3/5] synth_s874 on a copy of the live database: $R - nothing installed";; esac
lay old || stop "!! [3/5] could not lay out the control - nothing installed"
R0=$(synth "$SCR/root_old/finance" "$SCR/f2.db" | tail -1); case "$R0" in "SYNTH S874: "*" PASS, 0 FAIL") stop "!! [3/5] the control on the live files did not go red ($R0) - nothing installed";; esac
R9=$(s869 "$SCR/root_new/finance" "$SCR/f3.db"); case "$R9" in "SYNTH S869: "*" PASS, 0 FAIL") ;; *) stop "!! [3/5] S869's own proof on the rebuilt files: $R9 - nothing installed";; esac
say "[3/5] proof on a copy of the live database: $R; control on the live files: red; S869's proof on the rebuilt files: $R9"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the proofs green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$ROOT/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
for n in $NAMES; do st=$(stg "$n"); { cat "$SCR/built/$n" > "$st" && chmod --reference="$ROOT/$n" "$st" 2>/dev/null; chown --reference="$ROOT/$n" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
PLACING=1
for n in $NAMES; do mv -f "$(stg "$n")" "$ROOT/$n" || restore "the rename of $n"; done
for n in $NAMES; do [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
PLACING=0; release_lock
say "[4/5] placed and read back at their TO pins; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1"
say "[5/5] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s874.sh  (the two backups back, $FSVC restarted). Nothing was written to any table."
say ""; say "$KIT: DONE. Reload the Hub (Ctrl+F5): https://followup.dr-manoj.in/finance/approvals -- a day's short on its own panel; the full mobile + Call on bills and returns."
exit 0
