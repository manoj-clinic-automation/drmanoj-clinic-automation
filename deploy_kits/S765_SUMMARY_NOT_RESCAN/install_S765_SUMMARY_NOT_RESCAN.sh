#!/bin/bash
# =============================================================================
#  install_S765_SUMMARY_NOT_RESCAN.sh · kit S765 (09-Nov-2026, Sanjeevni session 417) · the owner, 17:34 IST
#  Alisha's list showed the dealers' month summaries she scanned on 08-Nov as "Yeh bill nahi hai -- asli bill dhoondh kar scan kijiye", and
#  Aaj ka bill kaam said "Dobara scan karo 22": a summary paper (bills.kind 'Summary') was judged as a bill. Two files:
#   /root/shared/scan_quality.py   16fb2402 -> TO   a summary paper is never judged (no 'bill nahi hai' on any screen)
#   /root/finance/porders_s454.py  c463b87c -> TO   the server never asks for a summary paper; its own open ask on one is withdrawn the next
#                                                   time reception's home opens (an ask a PERSON sent stays)
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s765kit && cp -rp /root/deploy/repo/deploy_kits/S765_SUMMARY_NOT_RESCAN /tmp/s765kit && bash /tmp/s765kit/install_S765_SUMMARY_NOT_RESCAN.sh
#  (DRY=1 before bash: every gate, the walk, its control and the proof on this box's data, printed; NOTHING written.)
# =============================================================================
set -u
KIT="S765_SUMMARY_NOT_RESCAN"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
FILES="shared/scan_quality.py finance/porders_s454.py"
declare -A FROM=( [shared/scan_quality.py]=16fb24029610ce7c0c0ecd502f529f7b [finance/porders_s454.py]=c463b87cf70212c8c20fcbb23beb6c38 )
declare -A TO
for f in $FILES; do TO[$f]="$(awk -v f="$f" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s765_inst_$STAMP"
PLACED=0; TOOK_LOCK=0

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S765_${FROM[$1]:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s765"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { for f in $FILES; do rm -f "$(stg "$f")"; done; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }
pids_of() { local m; m="$("$SYSTEMCTL" show -p MainPID --value "$1" 2>/dev/null)"; [ -n "$m" ] && [ "$m" != 0 ] && { echo "$m"; pgrep -P "$m" 2>/dev/null; }; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the two files back"
  PLACED=2
  for f in $FILES; do \cp -p "$(bak "$f")" "$ROOT/$f" || say "   !! could not put back $ROOT/$f"; rm -f "$(stg "$f")"; done
  find "$ROOT/finance" "$ROOT/shared" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  "$SYSTEMCTL" restart "$FSVC" || true
  for f in $FILES; do say "   $ROOT/$f $(m5 "$ROOT/$f" | cut -c1-8) (expected ${FROM[$f]:0:8})"; done
  say "   finance healthz $(wait200 fhz). Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s765.py" "$1" "$2" "$ROOT/finance" $3 2>&1); }
proof() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/proof_s765.py" "$1" "$2" "$ROOT/finance" "$SCR/proof.db" "$3" 2>&1); }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout pgrep; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
{ [ "$ROOT" != "/root" ] && [ "${SKIP_WINDOW:-0}" = 1 ]; } || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/6] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $FILES; do [ -n "${TO[$f]}" ] || { say "!! [1/6] TO_PINS.md5 does not name $f - nothing installed"; exit 1; }; [ -f "$ROOT/$f" ] || { say "!! [1/6] $ROOT/$f is missing - nothing installed"; exit 1; }; done
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
say "[2/6] live pins exact: scan_quality ${FROM[shared/scan_quality.py]:0:8} · porders_s454 ${FROM[finance/porders_s454.py]:0:8}"
"$APY" -B make_s765.py "$ROOT/shared" "$ROOT/finance" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/6] the builder refused a live file - nothing installed"; }
for f in $FILES; do
  b="$SCR/built/$(basename "$f")"
  [ "$(m5 "$b")" = "${TO[$f]}" ] || stop_unlocked "!! [3/6] rebuilt, $f is $(m5 "$b" | cut -c1-8), not ${TO[$f]:0:8} - nothing installed"
  for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$b" || stop_unlocked "!! [3/6] $f does not compile on $py - nothing installed"; done
done
mkdir -p "$SCR/live" && \cp -p "$ROOT/shared/scan_quality.py" "$ROOT/finance/porders_s454.py" "$SCR/live/" || stop_unlocked "!! [3/6] could not copy the live files - nothing installed"
say "[3/6] rebuilt here from this box's live bytes: both files at their TO pins; they compile under both pythons"
R=$(walk "$SCR/built" "$SCR/built" "" | tail -1)
[ "$R" = "WALK S765 GREEN" ] || { walk "$SCR/built" "$SCR/built" "" | grep -E 'RED|Error' | head -8; PLACED=2; stop_unlocked "!! [4/6] the walk on the rebuilt files: $R - nothing installed (kept in $SCR)"; }
R0=$(walk "$SCR/live" "$SCR/live" "--control" | tail -1)
[ "$R0" = "CONTROL S765 RED as it must be" ] || { PLACED=2; stop_unlocked "!! [4/6] the control on the live files: $R0 - nothing installed (kept in $SCR)"; }
"$VPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True, timeout=30); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$SCR/proof.db" \
  || stop_unlocked "!! [4/6] could not copy $DB for the proof - nothing installed"
if [ "${REHEARSE_PROOF:-}" = skip ] && [ "$ROOT" != "/root" ]; then PL="PROOF S765 (the live files): open server asks 0 · on summary papers 0 · would withdraw 0 (on summaries 0) · would ask 0 (on summaries 0)"; PK="PROOF S765 (the kit): open server asks 0 · on summary papers 0 · would withdraw 0 (on summaries 0) · would ask 0 (on summaries 0)"; else
PL=$(proof "$SCR/live" "$SCR/live" "(the live files)" | tail -1); PK=$(proof "$SCR/built" "$SCR/built" "(the kit)" | tail -1); fi
say "   $PL"; say "   $PK"
echo "$PK" | grep -q -E '^PROOF S765 \(the kit\): open server asks' || { PLACED=2; stop_unlocked "!! [4/6] the proof by the kit's files did not run - nothing installed (kept in $SCR)"; }
S=$(echo "$PK" | sed -E 's/.*on summary papers ([0-9]+).*/\1/'); WS=$(echo "$PK" | sed -E 's/.*would withdraw [0-9]+ \(on summaries ([0-9]+)\).*/\1/'); AS=$(echo "$PK" | sed -E 's/.*would ask [0-9]+ \(on summaries ([0-9]+)\).*/\1/')
[ "$AS" = 0 ] && [ "$WS" = "$S" ] || { PLACED=2; stop_unlocked "!! [4/6] by the kit's files the server would still ask for $AS summary paper(s), or would withdraw $WS of its $S open asks on summaries - nothing installed (kept in $SCR)"; }
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/6] finance healthz $f0 before the install - nothing installed"
say "[4/6] walk_s765: $R; its control: red as it must be; the proof: every open server ask on a summary paper ($S) would be withdrawn, none asked again; finance healthy"
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
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager -o short 2>/dev/null)"
  for p in $OLDPIDS; do JL="$(printf '%s\n' "$JL" | grep -v -E "\[$p\]:")"; done
  JR="$(printf '%s\n' "$JL" | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'Traceback|Error' | head -6 | sed 's/^/         /'; restore "journal: $JR error line(s) since the restart"; }
fi
say "[5/6] placed and read back: scan_quality ${TO[shared/scan_quality.py]:0:8} · porders_s454 ${TO[finance/porders_s454.py]:0:8}; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), healthz $c1, journal clean"
mkdir -p "$SCR/placed" && \cp -p "$ROOT/shared/scan_quality.py" "$ROOT/finance/porders_s454.py" "$SCR/placed/" || restore "could not copy the placed files"
R=$(walk "$SCR/placed" "$SCR/placed" "" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 6 ] && R="rehearsal: a forced red at [6/6]"
[ "$R" = "WALK S765 GREEN" ] || restore "the walk on the placed files: $R"
say "[6/6] the walk on the placed files: $R"
release_lock
say "undo (one line): $(for f in $FILES; do printf '\\cp -p %s %s && ' "$(bak "$f")" "$ROOT/$f"; done)$SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. The server's $S asks on summary papers are withdrawn the next time reception's home opens."
exit 0
