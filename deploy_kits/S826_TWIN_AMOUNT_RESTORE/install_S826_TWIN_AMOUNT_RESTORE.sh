#!/bin/bash
# =============================================================================
#  install_S826_TWIN_AMOUNT_RESTORE.sh · kit S826 (14-Nov-2026, the Scan App chat's session 410) · F-1378, the scan side
#  The owner's word (via the Sanjeevni chat's S455): two different amounts are two papers, never a double.
#  1. /root/shared/scan_checks_s441.py 59d5cb1c -> TO : no twin question when both amounts are read and differ by more than 2%; an
#     open one on such a pair is settled 'different' by the next pass; a 'same' answer on such a pair keeps both.
#  2. /root/assetapp/asset_register.py 74043cdb -> TO : the owner's "Restore — not a duplicate" on a pharmacy scan set aside as a duplicate.
#  Both files are REBUILT HERE from the live bytes by make_s826.py and checked against the TO pins. The scan app (assetapp) is restarted;
#  the finance app only READS the questions and is not restarted. No database change except what the next pass settles (recorded).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s826kit && cp -rp /root/deploy/repo/deploy_kits/S826_TWIN_AMOUNT_RESTORE /tmp/s826kit && bash /tmp/s826kit/install_S826_TWIN_AMOUNT_RESTORE.sh
#  (DRY=1 before bash: every gate, the walk and its control; NOTHING written.)
# =============================================================================
set -u
KIT="S826_TWIN_AMOUNT_RESTORE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
AST_PORT="${AST_PORT:-8030}"; ASVC="${ASVC:-assetapp}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
FILES="shared/scan_checks_s441.py assetapp/asset_register.py"
declare -A FROM=( [shared/scan_checks_s441.py]=59d5cb1cb7b2caf1355726cdce6fe3bb [assetapp/asset_register.py]=74043cdbe6a7d1c0a5ba0b61470eea5d )
declare -A TO
for f in $FILES; do TO[$f]="$(awk -v f="$f" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s826_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S826_${FROM[$1]:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s826"; }
ahealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$AST_PORT$1"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(ahealth /healthz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for f in $FILES; do rm -f "$(stg "$f")"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
pins() { local s=""; for f in $FILES; do s="$s $(basename "$f") $(m5 "$ROOT/$f" | cut -c1-8)"; done; echo "$s"; }
restore() { trap '' INT TERM HUP; say "!! RED after placing ($1) - putting the two files back"
  for f in $FILES; do \cp -p "$(bak "$f")" "$ROOT/$f" || say "   !! could not put back $ROOT/$f"; done
  find "$ROOT/assetapp" "$ROOT/shared" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  "$SYSTEMCTL" restart "$ASVC" || true
  say "   now:$(pins) (expected ${FROM[shared/scan_checks_s441.py]:0:8} ${FROM[assetapp/asset_register.py]:0:8}); the scan app $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$APY" -W ignore -B "$KDIR/walk_s826.py" --live "$ROOT/assetapp" --files "$1" $2 2>&1); }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $FILES; do [ -n "${TO[$f]}" ] && [ -f "$ROOT/$f" ] || { say "!! [1/6] a TO pin or $ROOT/$f missing - nothing installed"; exit 1; }; done
ALL=1; for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED (both files at their TO pins); nothing to do."; exit 0; }
mkdir -p "$SCR/built" "$SCR/live" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/6] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken by $KIT"
else say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${FROM[$f]}" ] || stop "!! [2/6] $ROOT/$f is $(m5 "$ROOT/$f" | cut -c1-8), expected ${FROM[$f]:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
"$APY" -B make_s826.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/6] the builder refused - nothing installed"; }
for f in $FILES; do [ "$(m5 "$SCR/built/$(basename "$f")")" = "${TO[$f]}" ] || stop "!! [2/6] rebuilt, $f is not at its TO pin - nothing installed"; done
for f in $FILES; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$APY" -W ignore -m py_compile "$SCR/built/$(basename "$f")" || stop "!! [2/6] $f does not compile - nothing installed"; done
say "[2/6] live pins exact; both files rebuilt here at their TO pins; both compile"
for f in $FILES; do cp -p "$ROOT/$f" "$SCR/live/"; done
O=$(walk "$SCR/built" ""); R=$(printf '%s\n' "$O" | tail -1)
[ "$R" = "WALK S826 GREEN" ] || { printf '%s\n' "$O" | grep -E "RED|STOP|Error" | head -8 | sed 's/^/      /'; stop "!! [3/6] walk_s826: $R - nothing installed"; }
O0=$(walk "$SCR/live" "--control"); R0=$(printf '%s\n' "$O0" | tail -1)
[ "$R0" = "CONTROL S826 RED as it must be" ] || { printf '%s\n' "$O0" | tail -6 | sed 's/^/      /'; stop "!! [3/6] the control on the live files: $R0 - nothing installed"; }
say "[3/6] walk_s826 on the rebuilt files (the real app, a made-up database): $R; its control on the live files red as it must be"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and its control green; NOTHING written"; exit 0; fi
h0=$(ahealth /healthz); [ "$h0" = 200 ] || stop "!! [4/6] the scan app's healthz $h0 before the install - nothing installed"
for f in $FILES; do { \cp -p "$ROOT/$f" "$(bak "$f")" && [ "$(m5 "$(bak "$f")")" = "${FROM[$f]}" ]; } || stop "!! [4/6] could not write the backup of $f - nothing placed"; done
for f in $FILES; do S="$(stg "$f")"; { cat "$SCR/built/$(basename "$f")" > "$S" && chmod --reference="$ROOT/$f" "$S" 2>/dev/null; chown --reference="$ROOT/$f" "$S" 2>/dev/null; [ "$(m5 "$S")" = "${TO[$f]}" ]; } || stop "!! [4/6] could not stage $f - nothing placed"; done
for f in $FILES; do mv -f "$(stg "$f")" "$ROOT/$f" || restore "the rename of $f"; done
for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || restore "read back of $f"; done
find "$ROOT/assetapp" "$ROOT/shared" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$ASVC" || restore "restart $ASVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
c0=$(wait200); [ "$c0" = 200 ] || restore "the scan app's healthz answered $c0"
c1=$(ahealth /bills); case "$c1" in 302|401|403) ;; *) restore "All papers answered $c1 without a login (expected 302, 401 or 403)";; esac
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JR="$("$JOURNALCTL" -u "$ASVC" --since "$T0" --no-pager -o cat 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[4/6] placed and read back:$(pins); $ASVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'): healthz $c0, All papers without a login $c1, journal clean"
mkdir -p "$SCR/placed"; for f in $FILES; do cp -p "$ROOT/$f" "$SCR/placed/"; done
O4=$(walk "$SCR/placed" ""); R4=$(printf '%s\n' "$O4" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 5 ] && R4="rehearsal: a forced red at [5/6]"
[ "$R4" = "WALK S826 GREEN" ] || restore "walk_s826 on the placed files: $R4"
release_lock
say "[5/6] walk_s826 on the placed files: $R4"
U=""; for f in $FILES; do U="$U\\cp -p $(bak "$f") $ROOT/$f && "; done
say "[6/6] undo (one line): ${U}$SYSTEMCTL restart $ASVC"
say ""
say "$KIT: DONE. Two scans with different amounts are no longer asked about as the same paper, and a pharmacy scan set aside as a duplicate now has your Restore button on its own page."
exit 0
