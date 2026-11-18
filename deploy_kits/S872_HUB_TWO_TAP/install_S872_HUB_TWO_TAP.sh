#!/bin/bash
# =============================================================================
#  install_S872_HUB_TWO_TAP.sh · kit S872 (18-Nov-2026, Sanjeevni session 482) · the owner's word 13:26: 'Mark all received is not working in your browser'
#  The Claude app's built-in browser answers every confirm() dialog with No by itself, so three S869 buttons never fired there: Mark all N
#  received, Accept (write off), remove an entry. They now use the Hub's own two-tap (first tap arms the words, second sends). One file:
#   1. /root/finance/finance_ui/finance_approvals.html 7253dc9f -> TO   (five anchors, make_s872.py; S869's page)
#  The live file is rebuilt HERE from its live bytes, checked against the TO pin; clinic-finance restarted (the page is static, the restart is the habit).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s872kit && cp -rp /root/deploy/repo/deploy_kits/S872_HUB_TWO_TAP /tmp/s872kit && bash /tmp/s872kit/install_S872_HUB_TWO_TAP.sh
#  (DRY=1 before bash: every gate and the proof; NOTHING written.)
# =============================================================================
set -u
KIT="S872_HUB_TWO_TAP"; KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; ROOT="${ROOT:-/root}"; LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
N="finance/finance_ui/finance_approvals.html"; FR="7253dc9f9a8ec0cfd576808af4c9b6a7"
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s872_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
BAK="$ROOT/$N.bak_S872_${FR:0:8}"; STG="$(dirname "$ROOT/$N")/.$(basename "$N").s872"
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$STG"; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
PLACING=0; trap on_exit EXIT
on_sig() { if [ "$PLACING" = 1 ]; then restore "interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
stop() { say "$1"; release_lock; exit 1; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting the page back"; \cp -p "$BAK" "$ROOT/$N"; "$SYSTEMCTL" restart "$FSVC" || true
  say "   $N $(m5 "$ROOT/$N" | cut -c1-8) (expected ${FR:0:8}); $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."; release_lock; exit 1; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$(to_of "$N")" ] && [ -f "$ROOT/$N" ] || { say "!! [1/5] no TO pin or the live page is missing - nothing installed"; exit 1; }
[ "$(m5 "$ROOT/$N")" = "$(to_of "$N")" ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR/built" && chmod 700 "$SCR" || { say "!! cannot make $SCR"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$ROOT/$N")" = "$FR" ] || stop "!! [2/5] $ROOT/$N is $(m5 "$ROOT/$N" | cut -c1-8), expected ${FR:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
"$APY" -B make_s872.py "$ROOT/finance" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/5] the builder refused - nothing installed"; }
[ "$(m5 "$SCR/built/finance_ui/finance_approvals.html")" = "$(to_of "$N")" ] || stop "!! [2/5] rebuilt, the page is not at its TO pin - nothing installed"
say "[2/5] live pin exact; rebuilt here at its TO pin"
R=$("$APY" -B synth_s872.py "$SCR/built/finance_ui/finance_approvals.html" 2>&1 | tail -1); [ "$R" = "SYNTH S872: 6 PASS, 0 FAIL" ] || stop "!! [3/5] the proof on the rebuilt page: $R - nothing installed"
R0=$("$APY" -B synth_s872.py "$ROOT/$N" 2>&1 | tail -1); [ "$R0" != "SYNTH S872: 6 PASS, 0 FAIL" ] || stop "!! [3/5] the control on the live page did not go red - nothing installed"
say "[3/5] proof on the rebuilt page: $R; control on the live page: red"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the proof green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
{ \cp -p "$ROOT/$N" "$BAK" && [ "$(m5 "$BAK")" = "$FR" ]; } || stop "!! [4/5] could not write the backup - nothing placed"
{ cat "$SCR/built/finance_ui/finance_approvals.html" > "$STG" && chmod --reference="$ROOT/$N" "$STG" 2>/dev/null; chown --reference="$ROOT/$N" "$STG" 2>/dev/null; [ "$(m5 "$STG")" = "$(to_of "$N")" ]; } || stop "!! [4/5] could not stage the page - nothing placed"
PLACING=1
mv -f "$STG" "$ROOT/$N" || restore "the rename"
[ "$(m5 "$ROOT/$N")" = "$(to_of "$N")" ] || restore "read back"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
PLACING=0; release_lock
say "[4/5] placed and read back at its TO pin; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1"
say "[5/5] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s872.sh  (the backup back, $FSVC restarted). Nothing was written to any table."
say ""; say "$KIT: DONE. Reload the Hub (Ctrl+F5): https://followup.dr-manoj.in/finance/approvals -- Mark all / Accept / remove now take TWO taps."
exit 0
