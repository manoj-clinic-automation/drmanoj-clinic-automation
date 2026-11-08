#!/bin/bash
# =============================================================================
#  install_S754_SUMMARY_RECOGNISE.sh · kit S754 (08-Nov-2026, the Scan App chat's session 409) · the owner's word 17:27 IST 08-Nov:
#  staff scan a dealer's month summary on the pharmacy lane like any bill -- tick or no tick; the system recognises it.
#  Three live files remade from their pinned bytes (make_s754.py): /root/assetapp/asset_register.py, /root/assetapp/claude_reader.py,
#  /root/shared/scan_checks_s441.py. Then the data step (fix_s754.py): today's eight papers that are dealers' statements put right.
#    DRY=1 bash /tmp/s754kit/install_S754_SUMMARY_RECOGNISE.sh   # every gate, every walk and control, the data step's DRY read; NOTHING written
#    bash /tmp/s754kit/install_S754_SUMMARY_RECOGNISE.sh         # the same, then place, restart the scan app, walk the placed files, the data step
#  Order: gates -> pins -> rebuild -> walks + controls -> the data step's DRY -> backups -> place -> restart (assetapp only) -> health ->
#  the walk on the placed files -> the data step (backup of assets.db inside it) -> undo line. A red after placing puts the files back.
# =============================================================================
set -u
KIT="S754_SUMMARY_RECOGNISE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
FDB="${FDB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
AST_PORT="${AST_PORT:-8030}"; ASVC="${ASVC:-assetapp}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
FILES="assetapp/asset_register.py assetapp/claude_reader.py shared/scan_checks_s441.py"
declare -A FROM=( [assetapp/asset_register.py]=dfa0955ccae7d13aa32c069784f054ea [assetapp/claude_reader.py]=8e1ae6bf363f99719b6de5d2dbe01783
                  [shared/scan_checks_s441.py]=10787cbf67b0480950134047efa74372 )
declare -A TO
for f in $FILES; do TO[$f]="$(awk -v f="$f" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s754_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
GREEN="walk_s754: 0 check(s) failed (0 of them S754 checks)"
CONTROL="walk_s754: 21 check(s) failed (21 of them S754 checks)"
GREEN_FIX="walk_fix_s754: 0 check(s) failed"
GREEN_750="walk_s750_app: 0 check(s) failed (0 of them S750 checks)"
GREEN_651="WALK S651 APP: 15 green, 0 red"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S754_${FROM[$1]:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s754"; }
ahealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$AST_PORT$1"; fi; }
ahz() { ahealth /healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { for f in $FILES; do rm -f "$(stg "$f")"; done; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
# the service's own ASSETS_DB / ASSETS_UPLOADS, when its unit sets them; else the app's defaults
svc_env() { "$SYSTEMCTL" show -p Environment --value "$ASVC" 2>/dev/null | tr ' ' '\n' | awk -F= -v k="$1" '$1==k{print substr($0, length(k)+2)}' | tail -1; }
ADB="${ADB:-$(svc_env ASSETS_DB)}"; ADB="${ADB:-$ROOT/assetapp/assets.db}"
UPL="${UPL:-$(svc_env ASSETS_UPLOADS)}"; UPL="${UPL:-$ROOT/assetapp/uploads}"
py() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$APY" -W ignore -B "$@" 2>&1); }
walk() { py "$KDIR/walk_s754.py" --live "$ROOT/assetapp" --files "$1" --shared "$2"; }
fixpy() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" SHARED_LIB_DIR="$ROOT/shared" timeout 900 "$APY" -W ignore -B "$KDIR/fix_s754.py" --assets "$ADB" --uploads "$UPL" --finance "$FDB" "$@" 2>&1); }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the files back"
  PLACED=2
  for f in $FILES; do \cp -p "$(bak "$f")" "$ROOT/$f" || say "   !! could not put back $ROOT/$f"; rm -f "$(stg "$f")"; done
  find "$ROOT/assetapp" "$ROOT/shared" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  "$SYSTEMCTL" restart "$ASVC" || true
  for f in $FILES; do say "   $ROOT/$f $(m5 "$ROOT/$f" | cut -c1-8) (expected ${FROM[$f]:0:8})"; done
  say "   the scan app $(wait200 ahz). Nothing of the data step was run. Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }
pids_of() { local m; m="$("$SYSTEMCTL" show -p MainPID --value "$1" 2>/dev/null)"; [ -n "$m" ] && [ "$m" != 0 ] && { echo "$m"; pgrep -P "$m" 2>/dev/null; }; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
say "== $KIT · $(TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M IST')  ${DRY:+DRY RUN -- nothing is written}"
for c in md5sum awk cp mv date curl grep find sed timeout pgrep tr; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
{ [ "$ROOT" != "/root" ] && [ "${SKIP_WINDOW:-0}" = 1 ]; } || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/7] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $FILES; do [ -n "${TO[$f]}" ] || { say "!! [1/7] TO_PINS.md5 does not name $f - nothing installed"; exit 1; }; done
for f in $FILES; do [ -f "$ROOT/$f" ] || { say "!! [1/7] $ROOT/$f is missing - nothing installed"; exit 1; }; done
[ -f "$ADB" ] && [ -f "$FDB" ] && [ -d "$UPL" ] && [ -f "$ROOT/assetapp/sorting_desk.py" ] || { say "!! [1/7] $ADB, $FDB, $UPL or sorting_desk.py is missing - nothing installed"; exit 1; }
mkdir -p "$SCR/built" "$SCR/pyc" "$SCR/live" "$SCR/s651" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
ALL=1; for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then
  say "-- the three files are already the kit's (installed earlier): the code step is skipped. The scan app $(ahz)."
else
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
  for f in $FILES; do C=$(m5 "$ROOT/$f"); [ "$C" = "${FROM[$f]}" ] || stop_unlocked "!! [2/7] $ROOT/$f is ${C:0:8}, expected ${FROM[$f]:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
  say "[2/7] live pins exact: asset_register ${FROM[assetapp/asset_register.py]:0:8} · claude_reader ${FROM[assetapp/claude_reader.py]:0:8} · scan_checks_s441 ${FROM[shared/scan_checks_s441.py]:0:8}"
  "$APY" -B make_s754.py "$ROOT/assetapp" "$ROOT/shared" "$SCR/built" "$KDIR" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/7] the builder refused a live file - nothing installed"; }
  for f in $FILES; do
    [ "$(m5 "$SCR/built/$f")" = "${TO[$f]}" ] || stop_unlocked "!! [3/7] rebuilt, $f is $(m5 "$SCR/built/$f" | cut -c1-8), not ${TO[$f]:0:8} - nothing installed"
    for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$SCR/built/$f" || stop_unlocked "!! [3/7] $f does not compile on $p - nothing installed"; done
  done
  say "[3/7] rebuilt here from this box's live bytes: the three files at their TO pins; each compiles under both pythons"
  cp -p "$ROOT/assetapp/asset_register.py" "$ROOT/assetapp/claude_reader.py" "$ROOT/shared/scan_checks_s441.py" "$SCR/live/"
  cp -p "$SCR/built/assetapp/asset_register.py" "$SCR/built/assetapp/claude_reader.py" "$SCR/built/shared/scan_checks_s441.py" "$KDIR/fix_s754.py" "$SCR/s651/" 2>/dev/null
  cp -p "$ROOT/assetapp/sorting_desk.py" "$SCR/s651/"
  R=$(walk "$SCR/built/assetapp" "$SCR/built/shared" | tail -1)
  [ "$R" = "$GREEN" ] || { walk "$SCR/built/assetapp" "$SCR/built/shared" | grep -E 'FAIL|Error|raised' | head -12 | sed 's/^/         /'; PLACED=2; stop_unlocked "!! [4/7] the walk on the rebuilt files is not green ($R) - nothing installed (kept in $SCR)"; }
  R0=$(walk "$SCR/live" "$SCR/live" | tail -1)
  [ "$R0" = "$CONTROL" ] || { PLACED=2; stop_unlocked "!! [4/7] the control on the live files is not as expected ($R0; expected $CONTROL) - nothing installed (kept in $SCR)"; }
  RF=$(py "$KDIR/walk_fix_s754.py" --live "$ROOT/assetapp" --files "$SCR/s651" | tail -1)
  [ "$RF" = "$GREEN_FIX" ] || { py "$KDIR/walk_fix_s754.py" --live "$ROOT/assetapp" --files "$SCR/s651" | grep -E 'FAIL|raised' | head -12 | sed 's/^/         /'; PLACED=2; stop_unlocked "!! [4/7] the data step's walk is not green ($RF) - nothing installed (kept in $SCR)"; }
  R7=$(py "$KDIR/walk_s750_app.py" --live "$ROOT/assetapp" --files "$SCR/built/assetapp" | tail -1)
  [ "$R7" = "$GREEN_750" ] || { PLACED=2; stop_unlocked "!! [4/7] S750's own walk on the rebuilt files is not green ($R7) - nothing installed (kept in $SCR)"; }
  R6=$(py "$KDIR/walk_s651_app.py" --live "$ROOT/assetapp" --files "$SCR/s651" | tail -1)
  [ "$R6" = "$GREEN_651" ] || { PLACED=2; stop_unlocked "!! [4/7] S651's own walk (the S441 checks) on the rebuilt files is not green ($R6) - nothing installed (kept in $SCR)"; }
  a0=$(ahz); [ "$a0" = 200 ] || stop_unlocked "!! [4/7] the scan app answered $a0 before the install - nothing installed"
  say "[4/7] the walk: $R; the control on the live files: $R0; the data step's walk: $RF; S750's walk: $R7; S651's walk: $R6; the scan app healthy"
fi
say "---------------------------------------------------------------- the data step's DRY read on this box (writes nothing) -- paste all of it to Claude"
fixpy | sed 's/^/   /'
FXR=$(fixpy | tail -1)
say "----------------------------------------------------------------"
DATA=1
case "$FXR" in "DRY OK"*|"ALREADY DONE"*) ;; *) DATA=0; say "   !! the data step's DRY read REFUSED (above): the code still goes in on the real line; the data step is NOT run -- send this to Claude";; esac
if [ "${DRY:-0}" = 1 ]; then
  if [ "$DATA" = 1 ]; then say "-- DRY RUN: every gate, the walks, the control and the data step's DRY read green; NOTHING written. Paste this; the real line is the same without DRY=1."
  else say "-- DRY RUN: every gate, the walks and the control green; the data step's DRY read REFUSED; NOTHING written. Paste this to Claude before the real line."; fi
  exit 0
fi

if [ "$ALL" != 1 ]; then
  for f in $FILES; do { \cp -p "$ROOT/$f" "$(bak "$f")" && [ "$(m5 "$(bak "$f")")" = "${FROM[$f]}" ]; } || stop_unlocked "!! [5/7] could not write the backup $(bak "$f") - nothing placed"; done
  for f in $FILES; do { cat "$SCR/built/$f" > "$(stg "$f")" && [ "$(m5 "$(stg "$f")")" = "${TO[$f]}" ]; } || stop_unlocked "!! [5/7] could not stage $f - nothing placed"; done
  for f in $FILES; do chmod --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; chown --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; done
  OLDPIDS="$(pids_of "$ASVC" | tr '\n' ' ')"
  PLACED=1
  for f in $FILES; do mv -f "$(stg "$f")" "$ROOT/$f" || restore "the rename of $f"; done
  for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || restore "read back of $f"; done
  find "$ROOT/assetapp" "$ROOT/shared" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  say "[5/7] placed and read back: asset_register ${TO[assetapp/asset_register.py]:0:8} · claude_reader ${TO[assetapp/claude_reader.py]:0:8} · scan_checks_s441 ${TO[shared/scan_checks_s441.py]:0:8} (backups .bak_S754_<old md5> beside each)"
  T0="$(date '+%Y-%m-%d %H:%M:%S')"
  "$SYSTEMCTL" restart "$ASVC" || restore "restart $ASVC"
  c0=$(wait200 ahz); [ "$c0" = 200 ] || restore "the scan app's healthz answered $c0"
  c1=$(ahealth /intake); case "$c1" in 302|401|403) ;; *) restore "the intake answered $c1 without a login (expected 302, 401 or 403)";; esac
  c2=$(ahealth /bills); case "$c2" in 302|401|403) ;; *) restore "All papers answered $c2 without a login (expected 302, 401 or 403)";; esac
  if command -v "$JOURNALCTL" >/dev/null 2>&1; then
    JL="$("$JOURNALCTL" -u "$ASVC" --since "$T0" --no-pager -o short 2>/dev/null)"
    for p in $OLDPIDS; do JL="$(printf '%s\n' "$JL" | grep -v -E "\[$p\]:")"; done
    JR="$(printf '%s\n' "$JL" | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError|S754 .*NOT')"
    [ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'Traceback|Error|S754 .*NOT' | head -6 | sed 's/^/         /'; restore "journal: $JR error line(s) since the restart"; }
  fi
  say "[6/7] $ASVC restarted at $(TZ=Asia/Kolkata date '+%H:%M IST'): healthz $c0; without a login the intake $c1, All papers $c2; journal clean"
  mkdir -p "$SCR/placed"
  cp -p "$ROOT/assetapp/asset_register.py" "$ROOT/assetapp/claude_reader.py" "$ROOT/shared/scan_checks_s441.py" "$SCR/placed/"
  R=$(walk "$SCR/placed" "$SCR/placed" | tail -1)
  [ "${REHEARSE_RED_AT:-}" = 6 ] && R="rehearsal: a forced red at [6/7]"
  [ "$R" = "$GREEN" ] || restore "the walk on the placed files: $R"
  say "[6/7] the walk on the placed files: $R"
  release_lock
fi
if [ "$DATA" = 1 ]; then
  say "[7/7] the data step -- today's papers that are dealers' statements (backup of assets.db first, inside it)"
  fixpy --real | sed 's/^/   /'
  FX=$(fixpy | tail -1)
else
  FX="REFUSED at its DRY read (above) -- not run"
fi
say "   now: $FX"
say "undo of the code (one line): $(for f in $FILES; do printf '\\cp -p %s %s && ' "$(bak "$f")" "$ROOT/$f"; done)$SYSTEMCTL restart $ASVC"
say "      (the data step: every change is an audit row with its from / to; assets.db.bak_S754_<stamp> is for disaster recovery only -- copying it back loses every scan since. The recognition off without an undo: settings read.summary_recognise = off)"
say ""
case "$FX" in "ALREADY DONE"*) say "$KIT: DONE. All papers: https://followup.dr-manoj.in/scanapp/bills";;
  *) say "$KIT: the code is in; the data step says: $FX -- run the same line again later (it carries on); send this screen to Claude.";; esac
exit 0
