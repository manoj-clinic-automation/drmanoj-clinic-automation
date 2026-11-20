#!/bin/bash
# install_S911_CALL_CAP_LINE.sh -- S911 (the parent, S495, 20-Nov-2026): the 120-call cap's count on the owner's console (D1027).
# The engine (processor.py) gets ONE print line after the cap decides -- 'CALL CAP: kept 120 of 143 due for a call -- 23 wait for
# tomorrow' -- so the run's log says it; the owner's console (work section) reads the newest such line from the server runner's
# log. The cap itself stays. The clinic PC's engine gets the same line from the assistant (connected folder) -- both read 64824680.
#   [1/5] SUMS gate   [2/5] the ground: engine 6929fc15 (S910's) or already 64824680; owner_console.py 500534f7 (S897's) or already
#         the TO; the 3.11 venv; OFF present; finance healthz 200; the build lock
#   [3/5] the engine patched in place (.bak_S911_6929fc15 beside) and read back 64824680; compiles under the venv; Replay 2 --only 7
#         under the venv to a scratch report: run #7's content hash must EQUAL the live report's -- else the engine goes back, STOP
#   [4/5] owner_console.py placed (.bak_S911_500534f7 beside), read back at its TO pin; clinic-finance restarted; healthz 200;
#         /finance/console answers (200/302/303/401/403) -- else both files back, restarted, STOP
#   [5/5] said: whether the runner's log already carries a CALL CAP line (none before the switch -- the PC makes the list)
#   --undo : both files back from their .bak_S911_ files; clinic-finance restarted; healthz 200
set -u
KIT="S911_CALL_CAP_LINE"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FIN="${FIN:-$ROOT/finance}"; FUT="${FUT:-$ROOT/followup_tracker}"; WA="${WA:-$ROOT/wa}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
VPY="${VPY:-$FUT/venv/bin/python3}"; APY="${APY:-$WA/venv/bin/python3}"
ENG="$FUT/processor.py"; ENG_FROM="6929fc15"; ENG_TO="64824680"
OC="$FIN/owner_console.py"; OC_FROM="500534f7"
REPORT="$FUT/logs/REPLAY2_REPORT.txt"
SCR="$(mktemp -d /tmp/s911_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
m8() { m5 "$1" | cut -c1-8; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
fget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fget /finance/healthz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
pyv() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PYV_TIMEOUT:-3600}" "$VPY" -W ignore -B "$@" 2>&1); }
pya() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 300 "$APY" -W ignore -B "$@" 2>&1); }
hash7() { sed -nE 's/^#7 .*content ([0-9a-f]+).*/\1/p' "$1" | tail -1; }
ENG_BAK="$ENG.bak_S911_$ENG_FROM"; OC_BAK="$OC.bak_S911_$OC_FROM"
restore() {  # $1 = why; what this run changed goes back
  say "!! RED ($1) - putting back"
  [ "${ENG_CHANGED:-0}" = 1 ] && [ -f "$ENG_BAK" ] && mv -f "$ENG_BAK" "$ENG"
  if [ "${OC_CHANGED:-0}" = 1 ] && [ -f "$OC_BAK" ]; then mv -f "$OC_BAK" "$OC"; "$SYSTEMCTL" restart "$FSVC" >/dev/null 2>&1 || true; h="$(wait200)"; else h="(not restarted)"; fi
  say "   restored: engine $(m8 "$ENG"), owner_console.py $(m8 "$OC"); finance healthz $h. Tell Claude."; release_lock; exit 1
}
if [ "${1:-}" = "--undo" ]; then
  n=0; OC_TO="$(to_of finance/owner_console.py | cut -c1-8)"
  [ -f "$ENG_BAK" ] && { [ "$(m8 "$ENG")" = "$ENG_TO" ] || stop "!! --undo: the engine is $(m8 "$ENG"), not S911's $ENG_TO (a later kit?) - not undoing"; }
  [ -f "$OC_BAK" ] && { [ "$(m8 "$OC")" = "$OC_TO" ] || stop "!! --undo: owner_console.py is $(m8 "$OC"), not S911's $OC_TO (a later kit?) - not undoing"; }
  [ -f "$ENG_BAK" ] && { mv -f "$ENG_BAK" "$ENG"; n=$((n+1)); }
  if [ -f "$OC_BAK" ]; then mv -f "$OC_BAK" "$OC"; n=$((n+1)); "$SYSTEMCTL" restart "$FSVC"; h="$(wait200)"; [ "$h" = 200 ] || { say "!! UNDONE but finance healthz is $h - tell Claude"; exit 1; }; fi
  [ "$n" = 0 ] && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  say "$KIT: UNDONE ($n file(s) back: engine $(m8 "$ENG"), owner_console.py $(m8 "$OC"))"; exit 0
fi
cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"
for f in call_cap_s911.py owner_console.py walk_s911.py make_s911.py; do [ -f "$KDIR/$f" ] || stop "!! [1/5] $f missing from the kit"; done
say "   [1/5] kit sums ok"
[ -x "$VPY" ] || stop "!! [2/5] $VPY is not there (S904/S910) - STOP. Tell Claude."
[ -e "$FUT/OFF" ] || stop "!! [2/5] $FUT/OFF is ABSENT - STOP. Tell Claude."
e="$(m8 "$ENG")"; o="$(m8 "$OC")"; OC_TO="$(to_of finance/owner_console.py | cut -c1-8)"
if [ "$e" = "$ENG_TO" ] && [ "$o" = "$OC_TO" ]; then say "-- $KIT is already installed (engine $e, owner_console.py $o). Nothing done."; exit 0; fi
[ "$e" = "$ENG_FROM" ] || [ "$e" = "$ENG_TO" ] || stop "!! [2/5] $ENG is $e, not $ENG_FROM (S910's = the PC's bytes) - STOP. Tell Claude."
[ "$o" = "$OC_FROM" ] || [ "$o" = "$OC_TO" ] || stop "!! [2/5] $OC is $o, not $OC_FROM (S897's) - STOP. Tell Claude."
H_LIVE="$(hash7 "$REPORT" 2>/dev/null)"; [ -n "$H_LIVE" ] || stop "!! [2/5] $REPORT holds no content hash for run #7 - STOP. Tell Claude."
f0=$(fget /finance/healthz); [ "$f0" = 200 ] || stop "!! [2/5] finance healthz $f0 before the install - nothing installed"
if mkdir "$LOCK" 2>/dev/null; then echo "$KIT $$" > "$LOCK/owner"; TOOK_LOCK=1; else stop "!! [2/5] another build holds $LOCK - try again in a minute"; fi
say "   [2/5] engine $e, owner_console.py $o, venv ok, OFF present, finance healthz 200, lock taken"
# [3/5] the engine
if [ "$e" = "$ENG_TO" ]; then say "   [3/5] engine already $ENG_TO"; else
  \cp -p "$ENG" "$ENG_BAK" && [ "$(m8 "$ENG_BAK")" = "$ENG_FROM" ] || stop "!! [3/5] could not write the engine's backup - nothing changed"
  ENG_CHANGED=1
  out="$(pyv "$KDIR/call_cap_s911.py" "$ENG" --apply)"; [ $? = 0 ] || restore "call_cap_s911.py: $out"
  [ "$(m5 "$ENG")" = "$(to_of followup_tracker/processor.py)" ] || restore "the engine read back $(m8 "$ENG"), not its TO pin $ENG_TO"
  pyv -m py_compile "$ENG" >/dev/null 2>&1 || restore "the engine does not compile under the venv"
  ic="$(FUT_ROOT="$FUT" pyv "$FUT/replay2_s897.py" --import-check | tail -1)"; [ "$ic" = "import-check: 0 error(s) under $VPY" ] || restore "$ic"
  FUT_ROOT="$FUT" FU_INBOX_DIR="$WA/followup-inbox" REPLAY2_SCRATCH="$SCR/replay" pyv "$FUT/replay2_s897.py" --run --only 7 --report "$SCR/r7.txt" > "$SCR/r7.out" 2>&1
  grep -q "CALL CAP: kept" "$SCR/r7.out" || restore "run #7 never reached the CALL CAP line (its output not captured?)"
  h_new="$(hash7 "$SCR/r7.txt")"
  [ -n "$h_new" ] && [ "$h_new" = "$H_LIVE" ] || restore "Replay 2 run #7 content hash $h_new vs the live report's $H_LIVE - the engine's output changed"
  say "   [3/5] engine $ENG_FROM -> $ENG_TO (bak beside); compiles; imports; Replay 2 run #7 content hash $h_new = the live report's"
fi
# [4/5] the console
if [ "$o" = "$OC_TO" ]; then say "   [4/5] owner_console.py already $OC_TO"; else
  pya -m py_compile "$KDIR/owner_console.py" >/dev/null 2>&1 || restore "the kit's owner_console.py does not compile under $APY"
  \cp -p "$OC" "$OC_BAK" && [ "$(m8 "$OC_BAK")" = "$OC_FROM" ] || restore "could not write the backup of owner_console.py"
  OC_CHANGED=1
  \cp -p "$KDIR/owner_console.py" "$FIN/.owner_console.py.s911" && mv -f "$FIN/.owner_console.py.s911" "$OC" || restore "placing owner_console.py"
  [ "$(m5 "$OC")" = "$(to_of finance/owner_console.py)" ] || restore "owner_console.py read back $(m8 "$OC"), not its TO pin"
  "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
  [ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
  c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
  pg=$(fget /finance/console); case "$pg" in 200|302|303|401|403) ;; *) restore "/finance/console answered $pg";; esac
  say "   [4/5] owner_console.py $OC_FROM -> $(m8 "$OC") (bak beside); $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), healthz $c1, the console answers $pg"
fi
release_lock
cc="$(grep -c 'CALL CAP: kept' "$FUT/logs/runner.log" 2>/dev/null)"
say "   [5/5] the runner's log holds ${cc:-0} CALL CAP line(s) (none until the switch: the PC makes the list; the console says so)"
say "$KIT: DONE. Engine $(m8 "$ENG") (the PC's gets the same line from Claude), owner_console.py $(m8 "$OC"). Undo: bash $KDIR/install_$KIT.sh --undo"
exit 0
