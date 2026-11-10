#!/bin/bash
# =============================================================================
#  install_S778_ORDER_SCREEN.sh · kit S778 (10-Nov-2026, Sanjeevni session 425) · D890 · the owner's mock approved 15:08 IST, "Go" 18:27 IST
#  The order screen: (a) the old orders at the top of 'Order karna hai' in a red box with their age, Dobara order karo / Ab nahi milta;
#  (b) 'Ab nahi milta' -> off today's list at once -> the doctor's Needs-you line -> Stop it everywhere / Keep ordering / Undo;
#  (c) the wrong-dealer check on the cards and in the box. Four new tables of its own; never Marg, purchase_line or the rules' lists.
#   /root/finance/porders_s454.py   cd2feeb3 -> TO   the S778 block appended; api_qty takes an S778 line
#   /root/finance/order_s778.py     NEW              the logic
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s778kit && cp -rp /root/deploy/repo/deploy_kits/S778_ORDER_SCREEN /tmp/s778kit && bash /tmp/s778kit/install_S778_ORDER_SCREEN.sh
#  (DRY=1 before bash: every gate, the walk, its control and the proof on a copy of this box's data, printed; NOTHING written.)
# =============================================================================
set -u
KIT="S778_ORDER_SCREEN"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
OLDF="finance/porders_s454.py"
NEWF="finance/order_s778.py"
FILES="$OLDF $NEWF"
declare -A FROM=( [finance/porders_s454.py]=cd2feeb3ad0ef6f34cb2515d56838770 )
declare -A NEEDS=( [finance/order_sheet.py]=53abf46175d3f22eb834be246e2233f6 [finance/order_track.py]=6f4746c570323942bffb0d5eea4b3cba [finance/order_rules.py]=bdefd058490dedb8b301a9f81ef3c5e1 )
declare -A TO
for f in $FILES; do TO[$f]="$(awk -v f="$f" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s778_inst_$STAMP"
PLACED=0; TOOK_LOCK=0

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S778_${FROM[$1]:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s778"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
rcode() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/porders/api/s778/na route; else curl -s -o /dev/null -m 8 -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{}' "http://127.0.0.1:$FIN_PORT/finance/porders/api/s778/na"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { for f in $FILES; do rm -f "$(stg "$f")"; done; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }
pids_of() { local m; m="$("$SYSTEMCTL" show -p MainPID --value "$1" 2>/dev/null)"; [ -n "$m" ] && [ "$m" != 0 ] && { echo "$m"; pgrep -P "$m" 2>/dev/null; }; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the files back"
  PLACED=2
  for f in $OLDF; do \cp -p "$(bak "$f")" "$ROOT/$f" || say "   !! could not put back $ROOT/$f"; rm -f "$(stg "$f")"; done
  for f in $NEWF; do rm -f "${ROOT:?}/${f:?}" "$(stg "$f")"; done
  find "$ROOT/finance" "$ROOT/shared" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  "$SYSTEMCTL" restart "$FSVC" || true
  for f in $OLDF; do say "   $ROOT/$f $(m5 "$ROOT/$f" | cut -c1-8) (expected ${FROM[$f]:0:8})"; done
  for f in $NEWF; do [ -e "$ROOT/$f" ] && say "   !! $ROOT/$f is still there" || say "   $ROOT/$f removed"; done
  say "   finance healthz $(wait200 fhz). The tables order_s778_*, if made, are harmless: nothing reads them without the kit. Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
walk() { (cd /tmp && TMPDIR="$SCR/tmp" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s778.py" "$1" "$ROOT/shared" "$ROOT/finance" "$DB" $2 2>&1); }
proof() { (cd /tmp && TMPDIR="$SCR/tmp" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/proof_s778.py" "$1" "$ROOT/shared" "$ROOT/finance" "$SCR/proof.db" "$2" 2>&1); }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout pgrep; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
{ [ "$ROOT" != "/root" ] && [ "${SKIP_WINDOW:-0}" = 1 ]; } || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/6] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $FILES; do [ -n "${TO[$f]}" ] || { say "!! [1/6] TO_PINS.md5 does not name $f - nothing installed"; exit 1; }; done
for f in $OLDF; do [ -f "$ROOT/$f" ] || { say "!! [1/6] $ROOT/$f is missing - nothing installed"; exit 1; }; done
for f in "${!NEEDS[@]}"; do [ "$(m5 "$ROOT/$f")" = "${NEEDS[$f]}" ] || { say "!! [1/6] $ROOT/$f is $(m5 "$ROOT/$f" | cut -c1-8), not ${NEEDS[$f]:0:8} (the kit reads it) - nothing installed. Tell Claude."; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/6] $DB is missing - nothing installed"; exit 1; }
mkdir -p "$SCR/built" "$SCR/pyc" "$SCR/tmp" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
ALL=1; for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the two files are the kit's. Nothing written. finance healthz $(fhz)"; exit 0; fi
for f in $NEWF; do [ -e "$ROOT/$f" ] && { say "!! [1/6] $ROOT/$f already exists and is not the kit's - nothing installed. Tell Claude."; exit 1; }; done
if [ "${DRY:-0}" = 1 ]; then
  say "[1/6] DRY RUN: kit gates green (SUMS, KIT_ID, the window, the three files it reads at their pins); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken $(TZ=Asia/Kolkata date '+%d-%m %H:%M IST') by $KIT"
else
  say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."
  exit 3
fi
for f in $OLDF; do C=$(m5 "$ROOT/$f"); [ "$C" = "${FROM[$f]}" ] || stop_unlocked "!! [2/6] $ROOT/$f is ${C:0:8}, expected ${FROM[$f]:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
say "[2/6] live pins exact: porders_s454.py cd2feeb3; order_sheet.py 53abf461 · order_track.py 6f4746c5 · order_rules.py bdefd058 (read, unchanged)"
"$APY" -B make_s778.py "$ROOT/finance" "$KDIR" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/6] the builder refused a live file - nothing installed"; }
for f in $FILES; do
  b="$SCR/built/$(basename "$f")"
  [ "$(m5 "$b")" = "${TO[$f]}" ] || stop_unlocked "!! [3/6] rebuilt, $f is $(m5 "$b" | cut -c1-8), not ${TO[$f]:0:8} - nothing installed"
  for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$b" || stop_unlocked "!! [3/6] $f does not compile on $py - nothing installed"; done
done
mkdir -p "$SCR/live" && \cp -p "$ROOT/finance/porders_s454.py" "$SCR/live/" || stop_unlocked "!! [3/6] could not copy the live file - nothing installed"
say "[3/6] rebuilt here from this box's live bytes: both files at their TO pins; both compile under both pythons"
R=$(walk "$SCR/built" "" | tail -1)
[ "$R" = "WALK S778 GREEN" ] || { walk "$SCR/built" "" | grep -E 'RED|Error' | head -8; PLACED=2; stop_unlocked "!! [4/6] the walk on the rebuilt files: $R - nothing installed (kept in $SCR)"; }
R0=$(walk "$SCR/live" "--control" | tail -1)
[ "$R0" = "CONTROL S778 RED as it must be" ] || { PLACED=2; stop_unlocked "!! [4/6] the control on the live file: $R0 - nothing installed (kept in $SCR)"; }
"$VPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True, timeout=30); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$SCR/proof.db" \
  || stop_unlocked "!! [4/6] could not copy $DB for the proof - nothing installed"
if [ "${REHEARSE_PROOF:-}" = skip ] && [ "$ROOT" != "/root" ]; then PK="PROOF S778 (the kit): red box 0 (+0 on cards) · rehearsal · GREEN"; else
proof "$SCR/built" "(the kit)" > "$SCR/proof.txt"; PK=$(tail -1 "$SCR/proof.txt"); sed '$d' "$SCR/proof.txt" | grep -v '^S740' | sed 's/^/   /'; fi
rm -f "$SCR/proof.db"
say "   $PK"
echo "$PK" | grep -q -E '^PROOF S778 \(the kit\): red box [0-9]+ .* GREEN$' || { PLACED=2; stop_unlocked "!! [4/6] the proof by the kit's files: $PK - nothing installed (kept in $SCR)"; }
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/6] finance healthz $f0 before the install - nothing installed"
say "[4/6] walk_s778: $R; its control: red as it must be; the proof on a copy of finance.db pressed every door on today's lines; finance healthy"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk, the control and the proof green; NOTHING written"; exit 0; fi

for f in $OLDF; do { \cp -p "$ROOT/$f" "$(bak "$f")" && [ "$(m5 "$(bak "$f")")" = "${FROM[$f]}" ]; } || stop_unlocked "!! [5/6] could not write the backup $(bak "$f") - nothing placed"; done
for f in $FILES; do { cat "$SCR/built/$(basename "$f")" > "$(stg "$f")" && [ "$(m5 "$(stg "$f")")" = "${TO[$f]}" ]; } || stop_unlocked "!! [5/6] could not stage $f - nothing placed"; done
for f in $FILES; do chmod --reference="$ROOT/$OLDF" "$(stg "$f")" 2>/dev/null; chown --reference="$ROOT/$OLDF" "$(stg "$f")" 2>/dev/null; done
OLDPIDS="$(pids_of "$FSVC" | tr '\n' ' ')"
PLACED=1
for f in $NEWF $OLDF; do mv -f "$(stg "$f")" "$ROOT/$f" || restore "the rename of $f"; done
for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || restore "read back of $f"; done
find "$ROOT/finance" "$ROOT/shared" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
rc=$(rcode); [ "$rc" != 404 ] && [ "$rc" != 000 ] && [ "$rc" != 500 ] || restore "the new door answers $rc"
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager -o short 2>/dev/null)"
  for p in $OLDPIDS; do JL="$(printf '%s\n' "$JL" | grep -v -E "\[$p\]:")"; done
  JR="$(printf '%s\n' "$JL" | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError|porders_s454 NOT mounted|S778 .* failed')"
  [ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'Traceback|Error|NOT mounted|S778' | head -6 | sed 's/^/         /'; restore "journal: $JR error line(s) since the restart"; }
fi
say "[5/6] placed and read back: porders_s454.py ${TO[finance/porders_s454.py]:0:8} · order_s778.py ${TO[finance/order_s778.py]:0:8} (new); $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), healthz $c1, the new door $rc (not 404), journal clean"
mkdir -p "$SCR/placed" && \cp -p "$ROOT/finance/porders_s454.py" "$ROOT/finance/order_s778.py" "$SCR/placed/" || restore "could not copy the placed files"
R=$(walk "$SCR/placed" "" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 6 ] && R="rehearsal: a forced red at [6/6]"
[ "$R" = "WALK S778 GREEN" ] || restore "the walk on the placed files: $R"
say "[6/6] the walk on the placed files: $R"
release_lock
say "undo (one line): cd /tmp && $VPY -B $ROOT/finance/order_s778.py $DB --lift-all && \\cp -p $(bak finance/porders_s454.py) $ROOT/finance/porders_s454.py && rm -f $ROOT/finance/order_s778.py && $SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. The order screen with the old orders at the top: https://followup.dr-manoj.in/finance/porders/s454/order"
exit 0
