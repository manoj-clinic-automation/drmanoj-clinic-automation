#!/bin/bash
# =============================================================================
#  install_S825_ARRIVALS_BY_THE_BILL.sh · kit S825 (built 14-Nov-2026 at Sanjeevni session 455, REBUILT at session 457 after its review)
#  F-1220 (D883): a bill scan tied to an order made the stock figure presume that EVERY open line of that order had arrived. Now a scan-tied
#  line counts as arrived only when the bill tied to its order CARRIES it (the tracker's own matcher; a sibling size never answers); a line
#  the bill does not carry has not arrived and stays ON ORDER (the engine does not propose it again); an unread scan or an unreachable scan
#  store keeps the old reading. Three files, REBUILT HERE from the live bytes by make_s825.py:
#    /root/finance/order_track.py (size words) · /root/finance/stock_figure.py (the judgement) · /root/finance/order_rules.py (on order)
#  The proof lists every scan-tied open line, before and after, on this box's own databases (read-only).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s825kit && cp -rp /root/deploy/repo/deploy_kits/S825_ARRIVALS_BY_THE_BILL /tmp/s825kit && bash /tmp/s825kit/install_S825_ARRIVALS_BY_THE_BILL.sh
#  (DRY=1 before bash: every gate, the walk and the proof; NOTHING written.)
# =============================================================================
set -u
KIT="S825_ARRIVALS_BY_THE_BILL"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"; ADB="${ADB:-$ROOT/assetapp/assets.db}"
export SPINE_DB="${SPINE_DB:-$ROOT/finance/spine/spine.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
FILES="order_track.py stock_figure.py order_rules.py"
declare -A FROM=( [order_track.py]=3f20faca36a159bc23dd45fc4bfce332 [stock_figure.py]=a0008c14353d5a7bda260854ff73b0e2 [order_rules.py]=bdefd058490dedb8b301a9f81ef3c5e1 )
declare -A TO
for f in $FILES; do TO[$f]="$(awk -v f="finance/$f" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s825_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
GREEN="walk_s825: 0 check(s) failed"
CONTROL="walk_s825: 15 check(s) failed"
bak() { echo "$ROOT/finance/$1.bak_S825_${FROM[$1]:0:8}"; }
stg() { echo "$ROOT/finance/.$1.s825"; }

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
fhealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { for f in $FILES; do rm -f "$(stg $f)"; done; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -W ignore -B "$KDIR/walk_s825.py" "$1" "$SCR/new/shared" "$DB" 2>&1); }
pread() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -W ignore -B "$KDIR/proof_s825.py" read "$1" "$SCR/new/shared" "$DB" "$ADB" "$2" 2>&1); }
pcomp() { "$APY" -B "$KDIR/proof_s825.py" compare "$1" "$2" 2>&1; }
copyfin() { mkdir -p "$1/finance/spine"; for f in "$ROOT"/finance/*.py "$ROOT"/finance/*.json "$ROOT"/finance/*.sql; do [ -f "$f" ] && cp -p "$f" "$1/finance/"; done
            for f in "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json; do [ -f "$f" ] && cp -p "$f" "$1/finance/spine/"; done; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the files back"
  PLACED=2
  for f in $FILES; do [ -f "$(bak $f)" ] && { \cp -p "$(bak $f)" "$ROOT/finance/$f" || say "   !! could not put back $ROOT/finance/$f -- the old file is $(bak $f)"; }; rm -f "$(stg $f)"; done
  find "$ROOT/finance" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  "$SYSTEMCTL" restart "$FSVC" || true
  for f in $FILES; do say "   $ROOT/finance/$f $(m5 "$ROOT/finance/$f" | cut -c1-8) (expected ${FROM[$f]:0:8})"; done
  say "   finance healthz $(wait200 fhz). Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop() { say "$1"; release_lock; exit "${2:-1}"; }
pids_of() { local m; m="$("$SYSTEMCTL" show -p MainPID --value "$FSVC" 2>/dev/null)"; [ -n "$m" ] && [ "$m" != 0 ] && { echo "$m"; pgrep -P "$m" 2>/dev/null; }; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout pgrep; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || [ "${SKIP_WINDOW:-0}" = 1 ] || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/7] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $FILES; do [ -n "${TO[$f]}" ] && [ -f "$ROOT/finance/$f" ] || { say "!! [1/7] the TO pin or $ROOT/finance/$f is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$SPINE_DB" ] || { say "!! [1/7] $DB, $ADB or $SPINE_DB is missing - nothing installed"; exit 1; }
AT=0; for f in $FILES; do [ "$(m5 "$ROOT/finance/$f")" = "${TO[$f]}" ] && AT=$((AT+1)); done
if [ "$AT" = 3 ]; then say "-- $KIT is ALREADY INSTALLED (all three files at their TO pins); nothing to do. finance healthz $(fhz)"; exit 0; fi
mkdir -p "$SCR/built" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/7] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/7] kit gates green; the build lock taken $(TZ=Asia/Kolkata date '+%d-%m %H:%M IST') by $KIT"
else say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for f in $FILES; do C=$(m5 "$ROOT/finance/$f"); [ "$C" = "${FROM[$f]}" ] || stop "!! [2/7] $ROOT/finance/$f is ${C:0:8}, expected ${FROM[$f]:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
"$APY" -B make_s825.py "$ROOT/finance" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/7] the builder refused - nothing installed"; }
for f in $FILES; do
  [ "$(m5 "$SCR/built/$f")" = "${TO[$f]}" ] || stop "!! [2/7] rebuilt, $f is not at its TO pin - nothing installed"
  for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/$f" || stop "!! [2/7] $f does not compile on $py - nothing installed"; done
done
copyfin "$SCR/new"; copyfin "$SCR/old"; mkdir -p "$SCR/new/shared"
for f in "$ROOT"/shared/*.py; do [ -f "$f" ] && cp -p "$f" "$SCR/new/shared/"; done
for f in $FILES; do cp -p "$SCR/built/$f" "$SCR/new/finance/$f"; done
say "[2/7] live pins exact (order_track ${FROM[order_track.py]:0:8}, stock_figure ${FROM[stock_figure.py]:0:8}, order_rules ${FROM[order_rules.py]:0:8}); rebuilt here from the live bytes at their TO pins; they compile on both pythons"

R=$(walk "$SCR/new/finance" | tail -1)
[ "$R" = "$GREEN" ] || { walk "$SCR/new/finance" | grep -E 'FAIL|raised' | head -10 | sed 's/^/         /'; PLACED=2; stop "!! [3/7] the walk on the rebuilt files: $R - nothing installed (kept in $SCR)"; }
R0=$(walk "$SCR/old/finance" | tail -1)
[ "$R0" = "$CONTROL" ] || { PLACED=2; stop "!! [3/7] the control on the live files: $R0 (expected $CONTROL) - nothing installed (kept in $SCR)"; }
say "[3/7] walk_s825: $R; its control on the live files: $R0"

pread "$SCR/old/finance" "$SCR/old.json" > "$SCR/p_old.txt"; pread "$SCR/new/finance" "$SCR/new.json" > "$SCR/p_new.txt"
pcomp "$SCR/old.json" "$SCR/new.json" > "$SCR/proof.txt"
P=$(tail -1 "$SCR/proof.txt")
say "---------------------------------------------------------------- the proof (read only)"
sed 's/^/   /' "$SCR/p_old.txt" "$SCR/p_new.txt" "$SCR/proof.txt"
say "----------------------------------------------------------------"
[ "${P:0:18}" = "PROOF S825: PROVEN" ] || { PLACED=2; stop "!! [4/7] $P - nothing installed (kept in $SCR). Send a photo of this screen to Claude."; }
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/7] finance healthz $f0 before the install - nothing installed"
say "[4/7] $P on this box's own databases (opened read-only); finance healthy"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks and the proof green; NOTHING written"; exit 0; fi

for f in $FILES; do
  { \cp -p "$ROOT/finance/$f" "$(bak $f)" && [ "$(m5 "$(bak $f)")" = "${FROM[$f]}" ]; } || stop "!! [5/7] could not write the backup of $f - nothing placed"
  { cat "$SCR/built/$f" > "$(stg $f)" && [ "$(m5 "$(stg $f)")" = "${TO[$f]}" ]; } || stop "!! [5/7] could not stage $f - nothing placed"
  chmod --reference="$ROOT/finance/$f" "$(stg $f)" 2>/dev/null; chown --reference="$ROOT/finance/$f" "$(stg $f)" 2>/dev/null
done
OLDPIDS="$(pids_of | tr '\n' ' ')"
PLACED=1
for f in $FILES; do mv -f "$(stg $f)" "$ROOT/finance/$f" || restore "the rename of $f"; done
for f in $FILES; do [ "$(m5 "$ROOT/finance/$f")" = "${TO[$f]}" ] || restore "read back $f"; done
find "$ROOT/finance" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[5/7] placed and read back: order_track ${TO[order_track.py]:0:8}, stock_figure ${TO[stock_figure.py]:0:8}, order_rules ${TO[order_rules.py]:0:8} (backups *.bak_S825_*)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(fhealth /finance/amir/step/1); case "$c2" in 302|401|403) ;; *) restore "Amir's page answered $c2 without a login (expected 302, 401 or 403)";; esac
c3=$(fhealth /finance/porders); case "$c3" in 302|401|403) ;; *) restore "the orders page answered $c3 without a login (expected 302, 401 or 403)";; esac
c4=$(fhealth /finance/purchase/page/check); case "$c4" in 302|401|403) ;; *) restore "the step view answered $c4 without a login (expected 302, 401 or 403)";; esac
NEWPIDS="$(pids_of | tr '\n' ' ')"
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager -o short 2>/dev/null)"
  for p in $OLDPIDS; do JL="$(printf '%s\n' "$JL" | grep -v -E "\[$p\]:")"; done
  JR="$(printf '%s\n' "$JL" | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError|Logging error')"
  [ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'Traceback|Error' | head -6 | sed 's/^/         /'; restore "journal: $JR error line(s) from the new master ($NEWPIDS) since the restart"; }
fi
say "[6/7] $FSVC restarted at $(TZ=Asia/Kolkata date '+%H:%M IST'): healthz $c1; without a login Amir's page $c2, the orders page $c3, the step view $c4; journal clean"
mkdir -p "$SCR/placed"; copyfin "$SCR/placed"
R=$(walk "$SCR/placed/finance" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 7 ] && R="rehearsal: a forced red at [7/7]"
[ "$R" = "$GREEN" ] || restore "the walk on the placed files: $R"
pread "$SCR/old/finance" "$SCR/old7.json" > /dev/null; pread "$SCR/placed/finance" "$SCR/placed.json" > /dev/null   # both read now (the live data moves)
P7=$(pcomp "$SCR/old7.json" "$SCR/placed.json" | tail -1)
[ "${P7:0:18}" = "PROOF S825: PROVEN" ] || restore "the proof by the placed files: $P7"
say "[7/7] by the placed files: the walk $R; $P7"
release_lock
U=""; for f in $FILES; do U="$U\\cp -p $(bak $f) $ROOT/finance/$f && "; done
say "undo (one line): ${U}$SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. A scanned bill now counts as arrived only what it actually carries; a medicine missing from the bill stays on order and is not ordered again."
exit 0
