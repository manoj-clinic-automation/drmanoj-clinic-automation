#!/bin/bash
# =============================================================================
#  install_S771_ORTHOTIC_BILLS.sh · kit S771 (10-Nov-2026, Sanjeevni session 423) · the owner's mock approved 11:27 IST ("go")
#  The Orthotic bills card on the Stock check hub: each orthotics dealer's bill, the scan's lines beside its Marg lines, a
#  differing line highlighted (and its bill kept on the card) until the next Marg export shows it fixed or the doctor clears it;
#  "Amir fixes Marg" puts one tap job on Amir's card; the scanned bill opens folded; an open difference stars its item at the
#  next count. Read-only on assets.db; it never writes to Marg or purchase_line.
#   /root/finance/section_count.py   d69e1681 -> TO   v1.2: GET /api/bills, POST /api/bills/mark, section_bill_mark, the star
#   /root/finance/stock_hub.html     90da7707 -> TO   the card under the counts
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s771kit && cp -rp /root/deploy/repo/deploy_kits/S771_ORTHOTIC_BILLS /tmp/s771kit && bash /tmp/s771kit/install_S771_ORTHOTIC_BILLS.sh
#  (DRY=1 before bash: every gate, the walk, its control and the proof on this box's data, printed; NOTHING written.)
# =============================================================================
set -u
KIT="S771_ORTHOTIC_BILLS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
FILES="finance/section_count.py finance/stock_hub.html"
declare -A FROM=( [finance/section_count.py]=d69e1681c42ba8a46a6034fed349e27c [finance/stock_hub.html]=90da7707a31b04812475346cc9fcec24 )
declare -A TO
for f in $FILES; do TO[$f]="$(awk -v f="$f" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s771_inst_$STAMP"
PLACED=0; TOOK_LOCK=0

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S771_${FROM[$1]:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s771"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
rcode() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/stockmatch/count/api/bills route; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/stockmatch/count/api/bills"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { for f in $FILES; do rm -f "$(stg "$f")"; done; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }
pids_of() { local m; m="$("$SYSTEMCTL" show -p MainPID --value "$1" 2>/dev/null)"; [ -n "$m" ] && [ "$m" != 0 ] && { echo "$m"; pgrep -P "$m" 2>/dev/null; }; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the files back"
  PLACED=2
  for f in $FILES; do \cp -p "$(bak "$f")" "$ROOT/$f" || say "   !! could not put back $ROOT/$f"; rm -f "$(stg "$f")"; done
  find "$ROOT/finance" "$ROOT/shared" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  "$SYSTEMCTL" restart "$FSVC" || true
  for f in $FILES; do say "   $ROOT/$f $(m5 "$ROOT/$f" | cut -c1-8) (expected ${FROM[$f]:0:8})"; done
  say "   finance healthz $(wait200 fhz). The table section_bill_mark, if made, is empty and harmless. Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s771.py" "$1" "$ROOT/shared" "$ROOT/finance" $2 2>&1); }
proof() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/proof_s771.py" "$1" "$ROOT/shared" "$ROOT/finance" "$SCR/proof.db" "$2" 2>&1); }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout pgrep; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
{ [ "$ROOT" != "/root" ] && [ "${SKIP_WINDOW:-0}" = 1 ]; } || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/6] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $FILES; do [ -n "${TO[$f]}" ] || { say "!! [1/6] TO_PINS.md5 does not name $f - nothing installed"; exit 1; }; done
for f in $FILES; do [ -f "$ROOT/$f" ] || { say "!! [1/6] $ROOT/$f is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/6] $DB is missing - nothing installed"; exit 1; }
mkdir -p "$SCR/built" "$SCR/pyc" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
ALL=1; for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the two files are the kit's. Nothing written. finance healthz $(fhz)"; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/6] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken $(TZ=Asia/Kolkata date '+%d-%m %H:%M IST') by $KIT"
else
  say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."
  exit 3
fi
for f in $FILES; do C=$(m5 "$ROOT/$f"); [ "$C" = "${FROM[$f]}" ] || stop_unlocked "!! [2/6] $ROOT/$f is ${C:0:8}, expected ${FROM[$f]:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
say "[2/6] live pins exact: section_count.py d69e1681 · stock_hub.html 90da7707"
"$APY" -B make_s771.py "$ROOT/finance" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/6] the builder refused a live file - nothing installed"; }
for f in $FILES; do
  b="$SCR/built/$(basename "$f")"
  [ "$(m5 "$b")" = "${TO[$f]}" ] || stop_unlocked "!! [3/6] rebuilt, $f is $(m5 "$b" | cut -c1-8), not ${TO[$f]:0:8} - nothing installed"
  case "$f" in *.py) for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$b" || stop_unlocked "!! [3/6] $f does not compile on $py - nothing installed"; done;; esac
done
mkdir -p "$SCR/live" && \cp -p "$ROOT/finance/section_count.py" "$ROOT/finance/stock_hub.html" "$SCR/live/" || stop_unlocked "!! [3/6] could not copy the live files - nothing installed"
say "[3/6] rebuilt here from this box's live bytes: the two files at their TO pins; section_count.py compiles under both pythons"
R=$(walk "$SCR/built" "" | tail -1)
[ "$R" = "WALK S771 GREEN" ] || { walk "$SCR/built" "" | grep -E 'RED|Error' | head -8; PLACED=2; stop_unlocked "!! [4/6] the walk on the rebuilt files: $R - nothing installed (kept in $SCR)"; }
R0=$(walk "$SCR/live" "--control" | tail -1)
[ "$R0" = "CONTROL S771 RED as it must be" ] || { PLACED=2; stop_unlocked "!! [4/6] the control on the live files: $R0 - nothing installed (kept in $SCR)"; }
"$VPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True, timeout=30); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$SCR/proof.db" \
  || stop_unlocked "!! [4/6] could not copy $DB for the proof - nothing installed"
if [ "${REHEARSE_PROOF:-}" = skip ] && [ "$ROOT" != "/root" ]; then PK="PROOF S771 (the kit): dealers YUVIKA SURGICALS · this month 2 · earlier still open 5 · settled 2 · differing bills 6 · scans read"; else
proof "$SCR/built" "(the kit)" > "$SCR/proof.txt"; PK=$(tail -1 "$SCR/proof.txt"); sed '$d' "$SCR/proof.txt" | sed 's/^/   /'; fi
rm -f "$SCR/proof.db"
say "   $PK"
echo "$PK" | grep -q -E '^PROOF S771 \(the kit\): dealers YUVIKA SURGICALS .* scans read$' || { PLACED=2; stop_unlocked "!! [4/6] the proof by the kit's files: $PK - nothing installed (kept in $SCR)"; }
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/6] finance healthz $f0 before the install - nothing installed"
say "[4/6] walk_s771: $R; its control: red as it must be; the proof on a copy of finance.db (and assets.db read only) read the card; finance healthy"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk, the control and the proof green; NOTHING written"; exit 0; fi

for f in $FILES; do { \cp -p "$ROOT/$f" "$(bak "$f")" && [ "$(m5 "$(bak "$f")")" = "${FROM[$f]}" ]; } || stop_unlocked "!! [5/6] could not write the backup $(bak "$f") - nothing placed"; done
for f in $FILES; do { cat "$SCR/built/$(basename "$f")" > "$(stg "$f")" && [ "$(m5 "$(stg "$f")")" = "${TO[$f]}" ]; } || stop_unlocked "!! [5/6] could not stage $f - nothing placed"; done
for f in $FILES; do chmod --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; chown --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; done
OLDPIDS="$(pids_of "$FSVC" | tr '\n' ' ')"
PLACED=1
for f in $FILES; do mv -f "$(stg "$f")" "$ROOT/$f" || restore "the rename of $f"; done
for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || restore "read back of $f"; done
find "$ROOT/finance" "$ROOT/shared" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
rc=$(rcode); [ "$rc" != 404 ] && [ "$rc" != 000 ] && [ "$rc" != 500 ] || restore "the card's address answers $rc"
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager -o short 2>/dev/null)"
  for p in $OLDPIDS; do JL="$(printf '%s\n' "$JL" | grep -v -E "\[$p\]:")"; done
  JR="$(printf '%s\n' "$JL" | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError|section_count NOT mounted')"
  [ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'Traceback|Error|NOT mounted' | head -6 | sed 's/^/         /'; restore "journal: $JR error line(s) since the restart"; }
fi
say "[5/6] placed and read back: section_count.py ${TO[finance/section_count.py]:0:8} · stock_hub.html ${TO[finance/stock_hub.html]:0:8}; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), healthz $c1, the card's address $rc (not 404), journal clean"
mkdir -p "$SCR/placed" && for f in $FILES; do \cp -p "$ROOT/$f" "$SCR/placed/"; done || restore "could not copy the placed files"
R=$(walk "$SCR/placed" "" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 6 ] && R="rehearsal: a forced red at [6/6]"
[ "$R" = "WALK S771 GREEN" ] || restore "the walk on the placed files: $R"
say "[6/6] the walk on the placed files: $R"
release_lock
say "undo (one line): $(for f in $FILES; do printf '\\cp -p %s %s && ' "$(bak "$f")" "$ROOT/$f"; done)$SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. The Orthotic bills card is on the Stock check page: https://followup.dr-manoj.in/finance/stock/page/hub"
exit 0
