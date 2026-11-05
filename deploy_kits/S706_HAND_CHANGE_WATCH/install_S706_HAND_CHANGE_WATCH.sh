#!/bin/bash
# =============================================================================
#  install_S706_HAND_CHANGE_WATCH.sh · kit S706 (05-Nov-2026, Sanjeevni session 386; D828) · Marg's stock changed with no bill, sale or
#  voucher: found from the spine, told to the owner the next morning (the item, the days, the quantities shifted), and kept as a collapsed
#  section on top of his Expiry watch page with a red count of what is new.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s706kit && cp -rp /root/deploy/repo/deploy_kits/S706_HAND_CHANGE_WATCH /tmp/s706kit && bash /tmp/s706kit/install_S706_HAND_CHANGE_WATCH.sh
#  (DRY=1 before bash: every gate, the walk, the control and the real-data read -- nothing written.)
#   /root/finance/owner_notice.py      2bc96912 -> TO   the 'hand' message (08:00-21:00), its link to the Expiry watch; the phone line's Wi-Fi
#   /root/finance/expiry_watch.py      15417df5 -> TO   the top section, collapsed, with the red count
#   /root/finance/marg_hand_change.py  NEW             the finder (spine.db and the filed vouchers READ-ONLY; its own table)
#  THE GATE THAT DECIDES, before anything is placed: the walk on the rebuilt files (made-up root), the control on the live files, and the
#  finder READ-ONLY on the live spine -- it must find CARTILOX SACHET's 3 -> 0 of 24-25 Oct (S705's read) and no more than 40 rows.
#  After placing: clinic-finance restarted, the first fill (the history: on the page, never announced), the walk on the placed files.
# =============================================================================
set -u
KIT="S706_HAND_CHANGE_WATCH"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
SPINE="${SPINE:-$ROOT/finance/spine/spine.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
ONLOCK="${ONLOCK:-/tmp/owner_notice.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
EDIT="finance/owner_notice.py finance/expiry_watch.py"
NEWF="finance/marg_hand_change.py"
FILES="$EDIT $NEWF"
declare -A FROM=( [finance/owner_notice.py]=2bc969126990a723ef9d29e041fb83f8 [finance/expiry_watch.py]=15417df553986694db5d8739f04bf0aa )
declare -A TO
for f in $FILES; do TO[$f]="$(awk -v f="$f" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s706_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
GREEN="WALK S706: 34 ok, 0 red"
CONTROL="WALK S706: 13 ok, 21 red"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S706_${FROM[$1]:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s706"; }
fhealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { for f in $FILES; do rm -f "$(stg "$f")"; done; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -B "$KDIR/walk_s706.py" "$1" "$ROOT/finance/spine/spine_build.py" 2>&1); }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the files back"
  PLACED=2
  for f in $EDIT; do \cp -p "$(bak "$f")" "$ROOT/$f" || say "   !! could not put back $ROOT/$f"; rm -f "$(stg "$f")"; done
  mv -f "$ROOT/$NEWF" "$SCR/marg_hand_change.py.removed" 2>/dev/null
  "$APY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1],timeout=60); c.execute('DROP TABLE IF EXISTS marg_hand_change'); c.execute(\"DELETE FROM setting WHERE key LIKE 'hand.%'\"); c.commit()" "$DB" 2>/dev/null || say "   !! the table marg_hand_change could not be dropped (harmless; unread)"
  find "$ROOT/finance" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  "$SYSTEMCTL" restart "$FSVC" || true
  for f in $EDIT; do say "   $ROOT/$f $(m5 "$ROOT/$f" | cut -c1-8) (expected ${FROM[$f]:0:8})"; done
  say "   $ROOT/$NEWF removed; its table dropped. finance healthz $(wait200 fhz). Send a photo of this screen to Claude."
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
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $FILES; do [ -n "${TO[$f]}" ] || { say "!! [1/7] TO_PINS.md5 does not name $f - nothing installed"; exit 1; }; done
for f in $EDIT; do [ -f "$ROOT/$f" ] || { say "!! [1/7] $ROOT/$f is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] && [ -f "$SPINE" ] || { say "!! [1/7] $DB or $SPINE is missing - nothing installed"; exit 1; }
mkdir -p "$SCR/built/finance" "$SCR/pyc" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
ALL=1; for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- ALREADY INSTALLED: the three files are the kit's. Nothing written. finance healthz $(fhz)"; exit 0; }
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
for f in $EDIT; do C=$(m5 "$ROOT/$f"); [ "$C" = "${FROM[$f]}" ] || stop_unlocked "!! [2/7] $ROOT/$f is ${C:0:8}, expected ${FROM[$f]:0:8} - it changed after this kit was built: STOP, nothing installed"; done
[ -e "$ROOT/$NEWF" ] && stop_unlocked "!! [2/7] $ROOT/$NEWF already exists and is not the kit's - STOP, nothing installed"
say "[2/7] live pins exact: owner_notice ${FROM[finance/owner_notice.py]:0:8}, expiry_watch ${FROM[finance/expiry_watch.py]:0:8}; $NEWF not there yet"

"$APY" -B make_s706.py "$ROOT/finance" "$SCR/built/finance" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/7] the builder refused a live file - nothing installed"; }
cp -p "$KDIR/marg_hand_change.py" "$SCR/built/$NEWF"
for f in $FILES; do
  [ "$(m5 "$SCR/built/$f")" = "${TO[$f]}" ] || stop_unlocked "!! [3/7] rebuilt, $f is $(m5 "$SCR/built/$f" | cut -c1-8), not ${TO[$f]:0:8} - nothing installed"
  for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$f" || stop_unlocked "!! [3/7] $f does not compile on $py - nothing installed"; done
done
mkdir -p "$SCR/newcode/spine"
for f in "$ROOT"/finance/*.py "$ROOT"/finance/*.json; do [ -f "$f" ] && cp -p "$f" "$SCR/newcode/"; done
for f in "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json; do [ -f "$f" ] && cp -p "$f" "$SCR/newcode/spine/"; done
for f in $FILES; do cp -p "$SCR/built/$f" "$SCR/newcode/$(basename "$f")"; done
say "[3/7] rebuilt here from this box's live bytes: the three files at their TO pins; each compiles under both pythons"

R=$(walk "$SCR/newcode" | tail -1)
[ "$R" = "$GREEN" ] || { walk "$SCR/newcode" | grep -E 'RED' | head -12 | sed 's/^/         /'; PLACED=2; stop_unlocked "!! [4/7] the walk on the rebuilt files is not green ($R) - nothing installed (kept in $SCR)"; }
R0=$(walk "$ROOT/finance" | tail -1)
[ "$R0" = "$CONTROL" ] || { PLACED=2; stop_unlocked "!! [4/7] the control on the live files is not as expected ($R0) - nothing installed (kept in $SCR)"; }
DRYOUT="$(cd "$SCR/newcode" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -B marg_hand_change.py dry --db "$DB" --spine "$SPINE" 2>&1)"
echo "$DRYOUT" | sed 's/^/         /' | head -60
NROWS=$(echo "$DRYOUT" | grep -c -E '^  (hand|rename) ')
echo "$DRYOUT" | grep -q -E '^S706 dry END' || stop_unlocked "!! [4/7] the finder did not finish on the live spine - nothing installed"
echo "$DRYOUT" | grep -q -E '^  hand +CARTILOX SACHET .*Marg 3 -> 0' || stop_unlocked "!! [4/7] the finder did not find CARTILOX SACHET 3 -> 0 (S705's read) - nothing installed"
JT="$(echo "$DRYOUT" | sed -n 's/.*judged to \([0-9-]*\);.*/\1/p' | head -1)"
[ -n "$JT" ] && [ "$JT" \> "$(TZ=Asia/Kolkata date -d '4 days ago' +%Y-%m-%d)" ] || stop_unlocked "!! [4/7] the finder judges only to '$JT' (more than 3 days ago: a sale export is missing) - nothing installed"
[ "$NROWS" -le 40 ] || stop_unlocked "!! [4/7] the finder found $NROWS rows on the live spine (more than 40: too noisy to show) - nothing installed"
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/7] finance healthz $f0 before the install - nothing installed"
say "[4/7] the walk: $R; the control on the live files: $R0; the finder READ-ONLY on the live spine: $NROWS row(s), CARTILOX found, judged to $JT; finance healthy"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk, the control and the real-data read green; NOTHING written"; exit 0; fi

for f in $EDIT; do { \cp -p "$ROOT/$f" "$(bak "$f")" && [ "$(m5 "$(bak "$f")")" = "${FROM[$f]}" ]; } || stop_unlocked "!! [5/7] could not write the backup $(bak "$f") - nothing placed"; done
for f in $FILES; do { cat "$SCR/built/$f" > "$(stg "$f")" && [ "$(m5 "$(stg "$f")")" = "${TO[$f]}" ]; } || stop_unlocked "!! [5/7] could not stage $f - nothing placed"; done
for f in $FILES; do chmod --reference="$ROOT/finance/owner_notice.py" "$(stg "$f")" 2>/dev/null; chown --reference="$ROOT/finance/owner_notice.py" "$(stg "$f")" 2>/dev/null; done
PLACED=1
exec 9>"$ONLOCK"; flock -w 120 9 || restore "the owner_notice tick lock was not free in two minutes"
for f in $FILES; do mv -f "$(stg "$f")" "$ROOT/$f" || restore "the rename of $f"; done
for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || restore "read back of $f"; done
find "$ROOT/finance" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
FILL="$(cd "$ROOT/finance" && timeout 300 "$VPY" -B marg_hand_change.py refresh --db "$DB" --spine "$SPINE" 2>&1 | tail -1)"
flock -u 9; exec 9>&-
case "$FILL" in *'"ok": true'*) ;; *) restore "the first fill: $FILL";; esac
say "[5/7] placed and read back: owner_notice ${TO[finance/owner_notice.py]:0:8}, expiry_watch ${TO[finance/expiry_watch.py]:0:8}, marg_hand_change ${TO[$NEWF]:0:8} (backups *.bak_S706_*); the first fill (the history, never announced): $FILL"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(fhealth /finance/sanjeevni/expiry); case "$c2" in 302|401|303|403) ;; *) restore "the Expiry watch answered $c2 without a login";; esac
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JR="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
PAGE="$(cd "$ROOT/finance" && timeout 120 "$VPY" -B -c "import sqlite3,expiry_watch as X; c=sqlite3.connect('file:$DB?mode=ro',uri=True); c.row_factory=sqlite3.Row; h=X.owner_page(c); print('SECTION' if 'id=\"hand\"' in h else 'NO SECTION')" 2>&1 | tail -1)"
[ "$PAGE" = "SECTION" ] || restore "the Expiry watch drawn on the live data: $PAGE"
say "[6/7] $FSVC restarted at $(TZ=Asia/Kolkata date '+%H:%M IST'): healthz $c1; the Expiry watch $c2 without a login (the login gate); journal clean; the page drawn on the live data shows the section"
R=$(walk "$ROOT/finance" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 7 ] && R="rehearsal: a forced red at [7/7]"
[ "$R" = "$GREEN" ] || restore "the walk on the placed files: $R"
say "[7/7] the walk on the placed files: $R"
release_lock
say "undo (one line): $(for f in $EDIT; do printf '\\cp -p %s %s && ' "$(bak "$f")" "$ROOT/$f"; done)rm -f $ROOT/$NEWF && $SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. A Marg stock change with no bill, sale or voucher is told the next morning; the list is on top of the Expiry watch."
exit 0
