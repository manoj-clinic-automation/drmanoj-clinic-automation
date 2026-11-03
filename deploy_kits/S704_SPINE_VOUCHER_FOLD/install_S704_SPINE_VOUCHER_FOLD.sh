#!/bin/bash
# =============================================================================
#  install_S704_SPINE_VOUCHER_FOLD.sh · kit S704 (03-Nov-2026, Sanjeevni session 383) · the buying model's step 3, display only:
#  F-1025 the spine's status line stops counting Amir's filed stock vouchers as open differences; F-1028 the owner's fold of the levels
#  model draws "The last list stood on", says the relist / stale lines in words, and a carried line carries the day's model word.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s704kit && cp -rp /root/deploy/repo/deploy_kits/S704_SPINE_VOUCHER_FOLD /tmp/s704kit && bash /tmp/s704kit/install_S704_SPINE_VOUCHER_FOLD.sh
#  (DRY=1 before bash: every gate, the walk, the control and the proof -- nothing written.)
#   /root/finance/spine/spine_build.py   1cd20ead -> TO   a difference equal to the filed vouchers is VOUCHER, not OPEN
#   /root/finance/order_rules.py         5e8330b3 -> TO   one S704 section appended (the fold; the carried line's word)
#  THE GATE THAT DECIDES: the walk on the rebuilt files (own rows), the control on the live files, and the proof -- the spine built TWICE
#  from the live readings (old file, new file; the build lock held; finance.db read-only) must agree on every table and gate row but the
#  findings' notes, and those only to VOUCHER; plan() and the fold old against new on a COPY of the database must agree on every line but
#  a carried line's model word.  No data step.  Restarts clinic-finance, then runs the spine build once (the cron's build line).
#  NEVER writes order.source; no order line's quantity, supplier or rail changes; the score's code (order_rehearsal.py) is not touched.
# =============================================================================
set -u
KIT="S704_SPINE_VOUCHER_FOLD"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SPLOCK="${SPLOCK:-/tmp/spine.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
FILES="finance/spine/spine_build.py finance/order_rules.py"
declare -A FROM=( [finance/spine/spine_build.py]=1cd20ead1c19ea0418c88bd728374e9c [finance/order_rules.py]=5e8330b33ba42ecd147f630bb25ea836 )
declare -A TO
for f in $FILES; do TO[$f]="$(awk -v f="$f" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s704_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
GREEN="40 of 40 green"
CONTROL="19 S704 check(s) red . 21 green"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S704_${FROM[$1]:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s704"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
fhealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { for f in $FILES; do rm -f "$(stg "$f")"; done; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -B "$KDIR/walk_s704.py" "$@" 2>&1); }
spine_now() {  # the build half of the cron's own line (crontab S331_SPINE), under the same lock; 0 = built and swapped. The evidence half
  # (Drive) stays the cron's: a Drive hiccup is not this kit's red.
  (cd "$ROOT/finance/spine" && flock -w 600 "$SPLOCK" "$VPY" -B spine_build.py --readings readings --out spine.db --finance-db "$DB" >> "$ROOT/finance/spine/spine.log" 2>&1)
}
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting both files back"
  PLACED=2
  for f in $FILES; do \cp -p "$(bak "$f")" "$ROOT/$f" || say "   !! could not put back $ROOT/$f"; rm -f "$(stg "$f")"; done
  find "$ROOT/finance" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  "$SYSTEMCTL" restart "$FSVC" || true
  for f in $FILES; do say "   $ROOT/$f $(m5 "$ROOT/$f" | cut -c1-8) (expected ${FROM[$f]:0:8})"; done
  say "   finance healthz $(wait200 fhz). The spine is rebuilt by its own cron within ten minutes. Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout flock; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/7] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $FILES; do [ -n "${TO[$f]}" ] || { say "!! [1/7] TO_PINS.md5 does not name $f - nothing installed"; exit 1; }; done
for f in $FILES; do [ -f "$ROOT/$f" ] || { say "!! [1/7] $ROOT/$f is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] && [ -d "$ROOT/finance/spine/readings" ] || { say "!! [1/7] $DB or the spine's readings are missing - nothing installed"; exit 1; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
ALL=1; for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- ALREADY INSTALLED: both files are the kit's. Nothing written. finance healthz $(fhz)"; exit 0; }
if [ "${DRY:-0}" = 1 ]; then
  say "[1/7] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/7] kit gates green; the build lock taken $(TZ=Asia/Kolkata date '+%d-%m %H:%M IST') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  TOOK_LOCK=1; say "[1/7] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."
  exit 3
fi
for f in $FILES; do C=$(m5 "$ROOT/$f"); [ "$C" = "${FROM[$f]}" ] || stop_unlocked "!! [2/7] $ROOT/$f is ${C:0:8}, expected ${FROM[$f]:0:8} - it changed after this kit was built: STOP, nothing installed"; done
say "[2/7] live pins exact: spine_build ${FROM[finance/spine/spine_build.py]:0:8}, order_rules ${FROM[finance/order_rules.py]:0:8}"

mkdir -p "$SCR/built" "$SCR/pyc" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s704.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/7] the builder refused a live file - nothing installed"; }
for f in $FILES; do
  [ "$(m5 "$SCR/built/$f")" = "${TO[$f]}" ] || stop_unlocked "!! [3/7] rebuilt, $f is $(m5 "$SCR/built/$f" | cut -c1-8), not ${TO[$f]:0:8} - nothing installed"
  for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$f" || stop_unlocked "!! [3/7] $f does not compile on $py - nothing installed"; done
done
mkdir -p "$SCR/newroot/finance/spine"
for f in "$ROOT"/finance/*.py "$ROOT"/finance/*.json; do [ -e "$f" ] && ln -s "$f" "$SCR/newroot/finance/$(basename "$f")"; done
[ -d "$ROOT/finance/finance_ui" ] && ln -s "$ROOT/finance/finance_ui" "$SCR/newroot/finance/finance_ui"
for f in "$ROOT"/finance/spine/*; do [ -e "$f" ] && ln -s "$f" "$SCR/newroot/finance/spine/$(basename "$f")"; done
for f in $FILES; do rm -f "$SCR/newroot/$f" && cp -p "$SCR/built/$f" "$SCR/newroot/$f"; done
say "[3/7] rebuilt here from this box's live bytes: both files at their TO pins; each compiles under both pythons"

R=$(walk --new "$SCR/newroot" --scratch "$SCR/w1" | tail -1)
[ "$R" = "$GREEN" ] || { walk --new "$SCR/newroot" --scratch "$SCR/w1b" | grep -E 'RED' | head -12 | sed 's/^/         /'; PLACED=2; stop_unlocked "!! [4/7] the walk on the rebuilt files is not green ($R) - nothing installed (kept in $SCR)"; }
R0=$(walk --old "$ROOT" --scratch "$SCR/w0" | tail -1)
[ "$R0" = "$CONTROL" ] || { PLACED=2; stop_unlocked "!! [4/7] the control on the live files is not as expected ($R0) - nothing installed (kept in $SCR)"; }
copydb "$DB" "$SCR/walk.db" || stop_unlocked "!! [4/7] no copy of the database - nothing installed"
P=$(flock -w 600 "$SPLOCK" bash -c "cd /tmp && PYTHONPYCACHEPREFIX='$SCR/pyc' timeout 1500 '$VPY' -B '$KDIR/walk_s704.py' --proof --old-root '$ROOT' --new '$SCR/newroot' --readings '$ROOT/finance/spine/readings' --findb '$DB' --db '$SCR/walk.db' --scratch '$SCR/wp' 2>&1")
PL="$(echo "$P" | tail -1)"
echo "$P" | grep -E '^  --  |RED|Error' | head -24 | sed 's/^/         /'
case "$PL" in "proof: old vs new on the live readings and a copy of the database . CLEAN . "*) ;; *) PLACED=2; stop_unlocked "!! [4/7] the proof is not clean ($PL) - nothing installed (kept in $SCR)";; esac
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/7] finance healthz $f0 before the install - nothing installed"
say "[4/7] the walk: $R; the control on the live files: $R0; $PL; finance healthy ($f0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk, the control and the proof green; NOTHING written"; exit 0; fi

for f in $FILES; do { \cp -p "$ROOT/$f" "$(bak "$f")" && [ "$(m5 "$(bak "$f")")" = "${FROM[$f]}" ]; } || stop_unlocked "!! [5/7] could not write the backup $(bak "$f") - nothing placed"; done
for f in $FILES; do { cat "$SCR/built/$f" > "$(stg "$f")" && [ "$(m5 "$(stg "$f")")" = "${TO[$f]}" ]; } || stop_unlocked "!! [5/7] could not stage $f - nothing placed"; done
for f in $FILES; do chmod --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; chown --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; done
PLACED=1
for f in $FILES; do mv -f "$(stg "$f")" "$ROOT/$f" || restore "the rename of $f"; done
for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || restore "read back of $f"; done
find "$ROOT/finance" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[5/7] placed and read back: spine_build ${TO[finance/spine/spine_build.py]:0:8}, order_rules ${TO[finance/order_rules.py]:0:8} (backups *.bak_S704_*)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(fhealth /finance/porders); case "$c2" in 302|401|303|403) ;; *) restore "the order page answered $c2 without a login";; esac
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JR="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[6/7] $FSVC restarted at $(TZ=Asia/Kolkata date '+%H:%M IST'): healthz $c1; the order page $c2 without a login (the login gate, expected); journal clean"
R=$(walk --new "$ROOT" --scratch "$SCR/w2" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 7 ] && R="rehearsal: a forced red at [7/7]"      # the rehearsal's hook only; unset on a real install
[ "$R" = "$GREEN" ] || restore "the walk on the placed files: $R"
[ "${SKIP_SPINE_NOW:-0}" = 1 ] || { spine_now || restore "the spine build with the new file did not swap (see $ROOT/finance/spine/spine.log)"; }
ST="$("$APY" -c "import json,sys; print(json.load(open(sys.argv[1])).get('status',''))" "$ROOT/finance/spine/spine_state.json" 2>/dev/null | cut -c1-260)"
say "[7/7] the walk on the placed files: $R; the spine built now with the new file: $ST"
release_lock
say "undo (one line): $(for f in $FILES; do printf '\\cp -p %s %s && ' "$(bak "$f")" "$ROOT/$f"; done)$SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. The spine's line no longer counts Amir's filed vouchers as differences; the order fold says what the list stood on, in words."
exit 0
