#!/bin/bash
# =============================================================================
#  install_S879_DARPAN_ENTRIES_TRANSIT.sh · kit S879 (18-Nov-2026, Sanjeevni session 483) · his "do 1 to 4 now" 16:57
#   1. /root/finance/darpan_kal.py   d27ed062 -> TO   Darpan's expected cash reads the owner's day entries (F-1468)
#   2. /root/finance/darpan_kal.html b7d2d61e -> TO   one row on his card (Hindi, amount only) + the doctor's own view
#   3. /root/finance/purchase_app.py c15bc1c5 -> TO   the tables fallback never counts a line its bill does not carry twice
#  Rebuilt HERE from the live bytes (make_s879.py), checked against the TO pins; clinic-finance restarted.
#  Nothing is written to any table by the install (a day is re-decided only when Darpan's page is next opened on it).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s879kit && cp -rp /root/deploy/repo/deploy_kits/S879_DARPAN_ENTRIES_TRANSIT /tmp/s879kit && bash /tmp/s879kit/install_S879_DARPAN_ENTRIES_TRANSIT.sh
#  (DRY=1 before bash: every gate and the proofs; NOTHING written.)
# =============================================================================
set -u
KIT="S879_DARPAN_ENTRIES_TRANSIT"; KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
OLDK="${OLDK:-/root/deploy/repo/deploy_kits}"; LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="finance/darpan_kal.py finance/darpan_kal.html finance/purchase_app.py"
from_of() { case "$1" in finance/darpan_kal.py) echo d27ed062f73e3becbd23b5a9136f7ba0;; finance/darpan_kal.html) echo b7d2d61e946454d940f6836e5677f294;; finance/purchase_app.py) echo c15bc1c5806bb4a7aabd261b6cd580f9;; esac; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s879_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { local f; f=$(from_of "$1"); echo "$ROOT/$1.bak_S879_${f:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s879"; }
hz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { hz /finance/healthz; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES; do rm -f "$(stg "$n")"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
PLACING=0; PLACED=0; trap on_exit EXIT
on_sig() { if [ "$PLACING" = 1 ]; then restore "interrupted while placing"; fi; [ "$PLACED" = 1 ] && { say "!! interrupted after the install finished - the files ARE placed; undo: undo_s879.sh"; release_lock; exit 1; }
  say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
stop() { say "$1"; release_lock; exit 1; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting the files back"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/$n"; done; "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do f=$(from_of "$n"); say "   $n $(m5 "$ROOT/$n" | cut -c1-8) (expected ${f:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Nothing was written to any table. Send a photo of this screen to Claude."; release_lock; exit 1; }
lay() { local d="$SCR/root_$1"; rm -rf "$d"; mkdir -p "$d/finance/finance_ui" \
  && find "$ROOT/finance" -maxdepth 1 -type f \( -name '*.py' -o -name '*.html' -o -name '*.sql' -o -name '*.json' \) -exec cp -p {} "$d/finance/" \; \
  && \cp -p "$ROOT"/finance/finance_ui/*.html "$d/finance/finance_ui/" 2>/dev/null; [ -f "$d/finance/darpan_kal.py" ]; }
synth() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -u -W ignore -B "$KDIR/synth_s879.py" "$@" 2>&1); }
s867() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -u -W ignore -B "$OLDK/S867_CONFIRM_WORDS/synth_s867.py" "$1" "$2" --real 2>&1); }
CPDB='import sqlite3,sys;s=sqlite3.connect("file:%s?mode=ro"%sys.argv[1],uri=True,timeout=60);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close();s.close();print("copied")'
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES; do [ -n "$(to_of "$n")" ] && [ -f "$ROOT/$n" ] || { say "!! [1/5] no TO pin or the live file $n is missing - nothing installed"; exit 1; }; done
[ -f "$ROOT/finance/hub_cash.py" ] || { say "!! [1/5] /root/finance/hub_cash.py (S869) is missing - nothing installed"; exit 1; }
[ -f "$DB" ] || { say "!! [1/5] $DB missing - nothing installed"; exit 1; }
[ -f "$OLDK/S867_CONFIRM_WORDS/synth_s867.py" ] || { say "!! [1/5] S867's proof is not in $OLDK - publish first. Nothing installed."; exit 1; }
ALL=1; for n in $NAMES; do [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR/built/finance" && chmod 700 "$SCR" || { say "!! cannot make $SCR"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do fr=$(from_of "$n"); [ "$(m5 "$ROOT/$n")" = "$fr" ] || stop "!! [2/5] $ROOT/$n is $(m5 "$ROOT/$n" | cut -c1-8), expected ${fr:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
"$APY" -B make_s879.py "$ROOT/finance" "$SCR/built/finance" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/5] the builder refused - nothing installed"; }
for n in $NAMES; do [ "$(m5 "$SCR/built/$n")" = "$(to_of "$n")" ] || stop "!! [2/5] rebuilt, $n is not at its TO pin - nothing installed"; done
for py in "$APY" "$VPY"; do for f in darpan_kal.py purchase_app.py; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/finance/$f" || stop "!! [2/5] $f does not compile on $py - nothing installed"; done; done
say "[2/5] three live pins exact; rebuilt here at the TO pins; both .py compile on both pythons"
"$VPY" -c "$CPDB" "$DB" "$SCR/finance.db" >/dev/null && \cp -p "$SCR/finance.db" "$SCR/f2.db" && \cp -p "$SCR/finance.db" "$SCR/f3.db" \
  && \cp -p "$SCR/finance.db" "$SCR/f4.db" || stop "!! [3/5] could not copy the database for the proof - nothing installed"
lay new && for n in $NAMES; do \cp -p "$SCR/built/$n" "$SCR/root_new/$n"; done || stop "!! [3/5] could not lay out the proof - nothing installed"
lay old || stop "!! [3/5] could not lay out the control - nothing installed"
O=$(synth "$SCR/root_new/finance" "$SCR/root_old/finance" "$SCR/finance.db"); R=$(printf '%s\n' "$O" | tail -1); printf '%s\n' "$O" | grep -E "FAIL|Traceback" | head -6 | sed 's/^/      /'
case "$R" in "S879 synth: "*" ok, 0 failed") ;; *) stop "!! [3/5] synth_s879 on a copy of the live database: $R - nothing installed";; esac
R0=$(synth "$SCR/root_old/finance" "$SCR/root_old/finance" "$SCR/f2.db" | tail -1); case "$R0" in *" ok, 0 failed") stop "!! [3/5] the control on the live files did not go red ($R0) - nothing installed";; esac
O7=$(s867 "$SCR/root_new/finance" "$SCR/f3.db"); O7o=$(s867 "$SCR/root_old/finance" "$SCR/f4.db")
R7=$(printf '%s\n' "$O7" | tail -1); R7o=$(printf '%s\n' "$O7o" | tail -1)
case "$R7" in "SYNTH S867: "*) ;; *) stop "!! [3/5] S867's proof did not finish on the rebuilt files ($R7) - nothing installed";; esac
case "$R7o" in "SYNTH S867: "*) ;; *) stop "!! [3/5] S867's proof did not finish on the live files ($R7o) - nothing installed";; esac
WORSE=$(comm -23 <(printf '%s\n' "$O7" | grep '^FAIL ' | sort -u) <(printf '%s\n' "$O7o" | grep '^FAIL ' | sort -u))
[ -z "$WORSE" ] || stop "!! [3/5] S867's own proof is WORSE on the rebuilt files: $WORSE - nothing installed"
say "[3/5] proof: $R; control on the live files: red; S867's proof (purchase_app): rebuilt $R7 / live $R7o (not worse)"
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
c2=$(hz /finance/darpan/kal/api/healthz); case "$c2" in 200|302|401|403) ;; *) restore "Darpan's page door answers $c2";; esac
PLACING=0; PLACED=1; release_lock
say "[4/5] placed and read back at the TO pins; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, Darpan's door $c2"
say "[5/5] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s879.sh  (the three backups back, $FSVC restarted)."
say ""; say "$KIT: DONE."
exit 0
