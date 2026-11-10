#!/bin/bash
# =============================================================================
#  install_S773_UNSPILL_BILLS.sh · kit S773 (10-Nov-2026, Sanjeevni session 423) · F-1233 · the owner's "GO" 12:43 IST
#  The item-wise purchase reader: a bill number Marg fused onto the item name ('06202627CAST SHOE M TYNOR', 'A000207_TYRO BR')
#  is split off ONLY when it matches a real, live bill of the same supplier (not in a FINAL month) -- on every purchase push, and
#  once here over the stored lines. Every change logged (purchase_unspill_log), so the undo puts each line back.
#   /root/finance/purchase_app.py       8424e05b -> TO   one guarded call in api_push, before the lines are re-dated
#   /root/finance/purchase_unspill.py   NEW             the evidence split, its log, its undo
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s773kit && cp -rp /root/deploy/repo/deploy_kits/S773_UNSPILL_BILLS /tmp/s773kit && bash /tmp/s773kit/install_S773_UNSPILL_BILLS.sh
#  (DRY=1 before bash: every gate, the walk, its control and the proof on a copy of this box's data, printed; NOTHING written.)
# =============================================================================
set -u
KIT="S773_UNSPILL_BILLS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
OLDF="finance/purchase_app.py"
NEWF="finance/purchase_unspill.py"
FILES="$OLDF $NEWF"
declare -A FROM=( [finance/purchase_app.py]=8424e05b780db4624b23b16189ead545 )
declare -A TO
for f in $FILES; do TO[$f]="$(awk -v f="$f" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s773_inst_$STAMP"
PLACED=0; TOOK_LOCK=0; APPLIED=0

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S773_${FROM[$1]:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s773"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
rcode() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/purchase/api/push route; else curl -s -o /dev/null -m 8 -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{}' "http://127.0.0.1:$FIN_PORT/finance/purchase/api/push"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { for f in $FILES; do rm -f "$(stg "$f")"; done; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }
pids_of() { local m; m="$("$SYSTEMCTL" show -p MainPID --value "$1" 2>/dev/null)"; [ -n "$m" ] && [ "$m" != 0 ] && { echo "$m"; pgrep -P "$m" 2>/dev/null; }; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the files back"
  PLACED=2
  for f in $OLDF; do \cp -p "$(bak "$f")" "$ROOT/$f" || say "   !! could not put back $ROOT/$f"; rm -f "$(stg "$f")"; done
  find "$ROOT/finance" "$ROOT/shared" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  "$SYSTEMCTL" restart "$FSVC" || true
  wait200 fhz >/dev/null                                     # the old code serves again: no push can join a line from here on
  if [ "$APPLIED" = 1 ]; then (cd /tmp && "$VPY" -B "$KDIR/purchase_unspill.py" "$DB" --undo) || say "   !! the joined lines could not be put back -- tell Claude"; fi
  for f in $NEWF; do rm -f "$ROOT/$f" "$(stg "$f")"; done
  for f in $OLDF; do say "   $ROOT/$f $(m5 "$ROOT/$f" | cut -c1-8) (expected ${FROM[$f]:0:8})"; done
  for f in $NEWF; do [ -e "$ROOT/$f" ] && say "   !! $ROOT/$f is still there" || say "   $ROOT/$f removed"; done
  say "   finance healthz $(wait200 fhz). Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s773.py" "$1" "$ROOT/shared" "$ROOT/finance" $2 2>&1); }
proof() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/proof_s773.py" "$1" "$SCR/proof.db" "$2" 2>&1); }

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
[ -f "$ROOT/finance/purchase_schema.sql" ] || { say "!! [1/6] $ROOT/finance/purchase_schema.sql is missing - nothing installed"; exit 1; }
[ -f "$DB" ] || { say "!! [1/6] $DB is missing - nothing installed"; exit 1; }
mkdir -p "$SCR/built" "$SCR/pyc" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
ALL=1; for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the two files are the kit's. Nothing written. finance healthz $(fhz)"; exit 0; fi
for f in $NEWF; do [ -e "$ROOT/$f" ] && { say "!! [1/6] $ROOT/$f already exists and is not the kit's - nothing installed. Tell Claude."; exit 1; }; done
if [ "${DRY:-0}" = 1 ]; then
  say "[1/6] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken $(TZ=Asia/Kolkata date '+%d-%m %H:%M IST') by $KIT"
else
  say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."
  exit 3
fi
for f in $OLDF; do C=$(m5 "$ROOT/$f"); [ "$C" = "${FROM[$f]}" ] || stop_unlocked "!! [2/6] $ROOT/$f is ${C:0:8}, expected ${FROM[$f]:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
say "[2/6] live pin exact: purchase_app.py 8424e05b; purchase_unspill.py not yet there"
"$APY" -B make_s773.py "$ROOT/finance" "$KDIR" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/6] the builder refused a live file - nothing installed"; }
for f in $FILES; do
  b="$SCR/built/$(basename "$f")"
  [ "$(m5 "$b")" = "${TO[$f]}" ] || stop_unlocked "!! [3/6] rebuilt, $f is $(m5 "$b" | cut -c1-8), not ${TO[$f]:0:8} - nothing installed"
  case "$f" in *.py) for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$b" || stop_unlocked "!! [3/6] $f does not compile on $py - nothing installed"; done;; esac
done
mkdir -p "$SCR/live" && \cp -p "$ROOT/finance/purchase_app.py" "$SCR/live/" || stop_unlocked "!! [3/6] could not copy the live files - nothing installed"
say "[3/6] rebuilt here from this box's live bytes: the two files at their TO pins; both compile under both pythons"
R=$(walk "$SCR/built" "" | tail -1)
[ "$R" = "WALK S773 GREEN" ] || { walk "$SCR/built" "" | grep -E 'RED|Error' | head -8; PLACED=2; stop_unlocked "!! [4/6] the walk on the rebuilt files: $R - nothing installed (kept in $SCR)"; }
R0=$(walk "$SCR/live" "--control" | tail -1)
[ "$R0" = "CONTROL S773 RED as it must be" ] || { PLACED=2; stop_unlocked "!! [4/6] the control on the live files: $R0 - nothing installed (kept in $SCR)"; }
"$VPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True, timeout=30); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$SCR/proof.db" \
  || stop_unlocked "!! [4/6] could not copy $DB for the proof - nothing installed"
if [ "${REHEARSE_PROOF:-}" = skip ] && [ "$ROOT" != "/root" ]; then PK="PROOF S773 (the kit): 70 line(s) would join 2 bill(s); applied on the copy 70, left 0, undone 70 -- ok"; else
proof "$SCR/built" "(the kit)" > "$SCR/proof.txt"; PK=$(tail -1 "$SCR/proof.txt"); sed '$d' "$SCR/proof.txt" | sed 's/^/   /'; fi
rm -f "$SCR/proof.db"
say "   $PK"
echo "$PK" | grep -q -E '^PROOF S773 \(the kit\): [0-9]+ line\(s\) would join .* -- ok$' || { PLACED=2; stop_unlocked "!! [4/6] the proof by the kit's files: $PK - nothing installed (kept in $SCR)"; }
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/6] finance healthz $f0 before the install - nothing installed"
say "[4/6] walk_s773: $R; its control: red as it must be; the proof on a copy of finance.db joined, read back and undid every line; finance healthy"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk, the control and the proof green; NOTHING written"; exit 0; fi

for f in $OLDF; do { \cp -p "$ROOT/$f" "$(bak "$f")" && [ "$(m5 "$(bak "$f")")" = "${FROM[$f]}" ]; } || stop_unlocked "!! [5/6] could not write the backup $(bak "$f") - nothing placed"; done
for f in $FILES; do { cat "$SCR/built/$(basename "$f")" > "$(stg "$f")" && [ "$(m5 "$(stg "$f")")" = "${TO[$f]}" ]; } || stop_unlocked "!! [5/6] could not stage $f - nothing placed"; done
for f in $FILES; do chmod --reference="$ROOT/finance/purchase_app.py" "$(stg "$f")" 2>/dev/null; chown --reference="$ROOT/finance/purchase_app.py" "$(stg "$f")" 2>/dev/null; done
OLDPIDS="$(pids_of "$FSVC" | tr '\n' ' ')"
PLACED=1; APPLIED=1                                          # from here a push may join lines: a red undoes them too
for f in $FILES; do mv -f "$(stg "$f")" "$ROOT/$f" || restore "the rename of $f"; done
for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || restore "read back of $f"; done
find "$ROOT/finance" "$ROOT/shared" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
rc=$(rcode); [ "$rc" != 404 ] && [ "$rc" != 000 ] && [ "$rc" != 500 ] || restore "the push door answers $rc"
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager -o short 2>/dev/null)"
  for p in $OLDPIDS; do JL="$(printf '%s\n' "$JL" | grep -v -E "\[$p\]:")"; done
  JR="$(printf '%s\n' "$JL" | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError|section_count NOT mounted')"
  [ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'Traceback|Error|NOT mounted' | head -6 | sed 's/^/         /'; restore "journal: $JR error line(s) since the restart"; }
fi
say "[5/6] placed and read back: purchase_app.py ${TO[finance/purchase_app.py]:0:8} · purchase_unspill.py ${TO[finance/purchase_unspill.py]:0:8}; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), healthz $c1, the push door $rc (not 404), journal clean"
mkdir -p "$SCR/placed" && for f in $FILES; do \cp -p "$ROOT/$f" "$SCR/placed/"; done || restore "could not copy the placed files"
R=$(walk "$SCR/placed" "" | tail -1)
[ "$R" = "WALK S773 GREEN" ] || restore "the walk on the placed files: $R"
AP=$(cd /tmp && "$VPY" -B "$ROOT/finance/purchase_unspill.py" "$DB" --apply 2>&1 | tail -1)
[ "${REHEARSE_RED_AT:-}" = 6 ] && AP="rehearsal: a forced red at [6/6]"
echo "$AP" | grep -q -E '^UNSPILL APPLIED: [0-9]+ line' || restore "the repair of the stored lines: $AP"
LEFT=$(cd /tmp && "$VPY" -B "$ROOT/finance/purchase_unspill.py" "$DB" 2>&1 | tail -1)
[ "$LEFT" = "UNSPILL PLAN: 0 line(s)" ] || restore "after the repair the plan still reads: $LEFT"
say "[6/6] the walk on the placed files: $R; the stored lines: $AP (nothing left to join)"
release_lock
say "undo (one line): \\cp -p $(bak finance/purchase_app.py) $ROOT/finance/purchase_app.py && $SYSTEMCTL restart $FSVC && sleep 8 && $VPY -B $ROOT/finance/purchase_unspill.py $DB --undo && rm -f $ROOT/finance/purchase_unspill.py"
say ""
say "$KIT: DONE. Bills whose number Marg fused onto the item name now carry their lines: https://followup.dr-manoj.in/finance/purchase/page/items?month=2026-10"
exit 0
