#!/bin/bash
# =============================================================================
#  install_S695_COUNT_ON_SPINE.sh · kit S695 (01-Nov-2026, Sanjeevni session 375) · the stock count's sheet, Amir's voucher proof and the
#  owner's Loss desk read every SALE line from the spine (the old store's shape, the count's own unit rule), so count #1's every figure stays
#  what it was and only the source moves; the old store answers only when the spine cannot be opened (plan section 9, step 2).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s695kit && cp -rp /root/deploy/repo/deploy_kits/S695_COUNT_ON_SPINE /tmp/s695kit && bash /tmp/s695kit/install_S695_COUNT_ON_SPINE.sh
#  (DRY=1 before bash: every gate, the walk, the control and the proof on copies -- nothing written.)
#   /root/finance/stock_app.py    5433d7b7 -> TO   _s695_spine / _s695_sale_rows; _mrp_p, _r_sale, _r_returns, _item_life, _sales_since, _pursue_sales read through them
#   /root/finance/loss_piles.py   2b9023fd -> TO   whole_unit_candidates reads through stock_app's
#  THE GATE THAT DECIDES: on this box, on COPIES of the database and the spine (read only), the OLD and the NEW modules compute every count
#  item's sale figures from the count's day, the horizon, the whole-unit list -- identical, or a difference the kit explains (a day or a line
#  the spine holds and the old store never had; the median rate over them) -- else nothing is placed. No data step. Restarts clinic-finance.
# =============================================================================
set -u
KIT="S695_COUNT_ON_SPINE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
SPINE="${SPINE:-$ROOT/finance/spine/spine.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F="finance/stock_app.py"; F2="finance/loss_piles.py"
FROM="5433d7b734126c9a5c518e4d797f1ff3"; FROM2="2b9023fd06aadc0ddaef30e2f26eccb3"
TO2="$(awk -v f="$F2" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
TO="$(awk -v f="$F" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s695_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
GREEN="17 of 17 green"
CONTROL="9 S695 check(s) red . 3 green"
BAK="$ROOT/$F.bak_S695_${FROM:0:8}"; BAK2="$ROOT/$F2.bak_S695_${FROM2:0:8}"
STG="$ROOT/finance/.stock_app.py.s695"; STG2="$ROOT/finance/.loss_piles.py.s695"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
fhealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { rm -f "$STG" "$STG2"; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 1800 "$VPY" -B "$KDIR/walk_s695.py" "$@" 2>&1); }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting stock_app.py and loss_piles.py back"
  PLACED=2
  \cp -p "$BAK" "$ROOT/$F" || say "   !! could not put back $ROOT/$F"; rm -f "$STG"
  [ -f "$BAK2" ] && { \cp -p "$BAK2" "$ROOT/$F2" || say "   !! could not put back $ROOT/$F2"; }; rm -f "$STG2"
  "$SYSTEMCTL" restart "$FSVC" || true
  say "   $ROOT/$F $(m5 "$ROOT/$F" | cut -c1-8) (expected ${FROM:0:8}); $ROOT/$F2 $(m5 "$ROOT/$F2" | cut -c1-8) (expected ${FROM2:0:8})"
  say "   finance healthz $(wait200 fhz). Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/8] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$TO" ] && [ -n "$TO2" ] || { say "!! [1/8] TO_PINS.md5 does not name both files - nothing installed"; exit 1; }
[ -f "$ROOT/$F" ] && [ -f "$ROOT/$F2" ] && [ -f "$ROOT/finance/stock_schema.sql" ] && [ -f "$DB" ] && [ -f "$SPINE" ] || { say "!! [1/8] $ROOT/$F, $ROOT/$F2, stock_schema.sql, $DB or $SPINE is missing - nothing installed"; exit 1; }
[ "$(m5 "$ROOT/$F")" = "$TO" ] && [ "$(m5 "$ROOT/$F2")" = "$TO2" ] && { say "-- ALREADY INSTALLED: both files are the kit's. Nothing written. finance healthz $(fhz)"; exit 0; }
if [ "${DRY:-0}" = 1 ]; then
  say "[1/8] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/8] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  TOOK_LOCK=1; say "[1/8] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."
  exit 3
fi
C=$(m5 "$ROOT/$F"); [ "$C" = "$FROM" ] || stop_unlocked "!! [2/8] $ROOT/$F is ${C:0:8}, expected ${FROM:0:8} - it changed after this kit was built: STOP, nothing installed"
C2=$(m5 "$ROOT/$F2"); [ "$C2" = "$FROM2" ] || stop_unlocked "!! [2/8] $ROOT/$F2 is ${C2:0:8}, expected ${FROM2:0:8} - it changed after this kit was built: STOP, nothing installed"
say "[2/8] live pins exact: stock_app.py ${FROM:0:8}, loss_piles.py ${FROM2:0:8}"

mkdir -p "$SCR/built/finance" "$SCR/pyc" && chmod 700 "$SCR" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s695.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/8] the builder refused the live file - nothing installed"; }
[ "$(m5 "$SCR/built/$F")" = "$TO" ] || stop_unlocked "!! [3/8] rebuilt, stock_app.py is $(m5 "$SCR/built/$F" | cut -c1-8), not ${TO:0:8} - nothing installed"
[ "$(m5 "$SCR/built/$F2")" = "$TO2" ] || stop_unlocked "!! [3/8] rebuilt, loss_piles.py is $(m5 "$SCR/built/$F2" | cut -c1-8), not ${TO2:0:8} - nothing installed"
for py in "$APY" "$VPY"; do for f in "$F" "$F2"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$f" || stop_unlocked "!! [3/8] $f does not compile on $py - nothing installed"; done; done
# the rebuilt file's root: the live neighbours (read only) beside the kit's file
mkdir -p "$SCR/newroot/finance/spine" && for f in "$ROOT"/finance/*; do [ -f "$f" ] && ln -s "$f" "$SCR/newroot/finance/$(basename "$f")"; done
for f in "$ROOT"/finance/spine/*; do [ -f "$f" ] && ln -s "$f" "$SCR/newroot/finance/spine/$(basename "$f")"; done
rm -f "$SCR/newroot/$F" "$SCR/newroot/$F2" && cp -p "$SCR/built/$F" "$SCR/newroot/$F" && cp -p "$SCR/built/$F2" "$SCR/newroot/$F2"
say "[3/8] rebuilt here from this box's live bytes: at their TO pins ${TO:0:8} / ${TO2:0:8}; both compile under both pythons"

R=$(walk --new "$SCR/newroot" --scratch "$SCR/w1" | tail -1)
[ "$R" = "$GREEN" ] || { walk --new "$SCR/newroot" --scratch "$SCR/w1b" | grep -E 'RED' | head -12 | sed 's/^/         /'; PLACED=2; stop_unlocked "!! [4/8] the walk on the rebuilt file is not green ($R) - nothing installed (kept in $SCR)"; }
R0=$(walk --old "$ROOT" --scratch "$SCR/w0" | tail -1)
[ "$R0" = "$CONTROL" ] || { PLACED=2; stop_unlocked "!! [4/8] the control on the live file is not as expected ($R0) - nothing installed (kept in $SCR)"; }
copydb "$DB" "$SCR/walk.db" || stop_unlocked "!! [4/8] no copy of the database - nothing installed"
copydb "$SPINE" "$SCR/spine.db" || stop_unlocked "!! [4/8] no copy of the spine - nothing installed"
P1=$(walk --proof --old-root "$ROOT" --new "$SCR/newroot" --db "$SCR/walk.db" --spine "$SCR/spine.db" --scratch "$SCR/wp1")
echo "$P1" | grep -E '^  days|^  --  ' | grep -v -E "median rate|whole-unit list|read whole" | head -20 | sed 's/^/         /'
PL1="$(echo "$P1" | tail -1)"
case "$PL1" in "proof: items "*" . unexplained 0 . CLEAN") ;; *) PLACED=2; stop_unlocked "!! [4/8] the proof is not clean ($PL1) - nothing installed (kept in $SCR)";; esac
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/8] finance healthz $f0 before the install - nothing installed"
say "[4/8] the walk: $GREEN; the control on the live file: $R0; $PL1; finance healthy ($f0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk, the control and the proof green; NOTHING written"; exit 0; fi

{ \cp -p "$ROOT/$F" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop_unlocked "!! [5/8] could not write the backup $BAK - nothing placed"
{ \cp -p "$ROOT/$F2" "$BAK2" && [ "$(m5 "$BAK2")" = "$FROM2" ]; } || stop_unlocked "!! [5/8] could not write the backup $BAK2 - nothing placed"
{ cat "$SCR/built/$F" > "$STG" && [ "$(m5 "$STG")" = "$TO" ]; } || { rm -f "$STG"; stop_unlocked "!! [5/8] could not stage stock_app.py - nothing placed"; }
{ cat "$SCR/built/$F2" > "$STG2" && [ "$(m5 "$STG2")" = "$TO2" ]; } || { rm -f "$STG" "$STG2"; stop_unlocked "!! [5/8] could not stage loss_piles.py - nothing placed"; }
chmod --reference="$ROOT/$F" "$STG" 2>/dev/null; chown --reference="$ROOT/$F" "$STG" 2>/dev/null
chmod --reference="$ROOT/$F2" "$STG2" 2>/dev/null; chown --reference="$ROOT/$F2" "$STG2" 2>/dev/null
PLACED=1
mv -f "$STG" "$ROOT/$F" || restore "the rename"
mv -f "$STG2" "$ROOT/$F2" || restore "the rename of loss_piles.py"
[ "$(m5 "$ROOT/$F")" = "$TO" ] && [ "$(m5 "$ROOT/$F2")" = "$TO2" ] || restore "read back"
find "$ROOT/finance" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[5/8] placed and read back: stock_app.py ${TO:0:8}, loss_piles.py ${TO2:0:8} (backups $BAK, $BAK2)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(fhealth /finance/stock/); case "$c2" in 302|401|303|403|200) ;; *) restore "the stock pages answered $c2";; esac
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  # the NEW master's lines only: the old master's shutdown can print Python's own '--- Logging error ---' traceback while it is being
  # stopped (gunicorn reaping a worker inside a signal handler) -- that is not the kit's; the 1-Nov install of this kit was refused by it
  "$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null | awk '/Starting gunicorn/{buf=""} {buf=buf $0 "\n"} END{printf "%s", buf}' > "$SCR/journal_new.txt"
  JR="$(grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError' "$SCR/journal_new.txt")"
  [ "${JR:-0}" = 0 ] || { grep -i -E -B3 -A12 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError' "$SCR/journal_new.txt" | head -40 | sed 's/^/   /'; restore "journal: $JR error line(s) in the new process since the restart (kept in $SCR/journal_new.txt)"; }
fi
say "[6/8] $FSVC restarted at $T0: healthz $c1; the stock pages $c2; journal clean"
say "[7/8] no data step"
R=$(walk --new "$ROOT" --scratch "$SCR/w2" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 8 ] && R="rehearsal: a forced red at [8/8]"      # the rehearsal's hook only; unset on a real install
[ "$R" = "$GREEN" ] || restore "the walk on the placed file: $R"
release_lock
say "[8/8] the walk on the placed file: $R; the build lock released"
say "undo (one line): \\cp -p $BAK $ROOT/$F && \\cp -p $BAK2 $ROOT/$F2 && $SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. The count sheet, the voucher proof and the Loss desk read every sale line from the spine; the figures are what they were."
exit 0
