#!/bin/bash
# =============================================================================
#  install_S931_PAUSE_ASK_APPROVE.sh · kit S931 (the parent, S498, 22-Nov-2026) · a dress / i-card pause needs approval
#  The owner 15:11: 'pause shd start only with Shavez or my approval, reception can only initiate it.'
#  /root/staff_register/staff_register.py 22a75b96 (S929) -> TO : reception's pause = an ASK (fine not paused) until Shavez
#  or a doctor taps Approve; Shavez's / a doctor's own pause starts at once; asks on the staff list (PAUSE ASKED), on
#  Pending review (a card) and in the portal tile's 'to approve'. staff-register restarted.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s931kit && cp -rp /root/deploy/repo/deploy_kits/S931_PAUSE_ASK_APPROVE /tmp/s931kit && bash /tmp/s931kit/install_S931_PAUSE_ASK_APPROVE.sh
#  DRY=1 before bash: every gate and walk, nothing changed. --undo: the file back.
# =============================================================================
set -u
KIT="S931_PAUSE_ASK_APPROVE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"; APY="${APY:-/usr/bin/python3}"
RDIR="${RDIR:-/root/staff_register}"; N="staff_register.py"; F="$RDIR/$N"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
RSVC="${RSVC:-staff-register}"; RPORT="${RPORT:-8044}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
FROM="22a75b9637050f9e57b99faf59fb98a9"
TO="$(awk '$2=="staff_register/staff_register.py"{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(TZ=Asia/Kolkata date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s931_inst_$STAMP"; TOOK_LOCK=0
BAK="$RDIR/$N.bak_S931_${FROM:0:8}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
rhealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$RPORT/register/health"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(rhealth); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$RDIR/.$N.s931"; release_lock; rm -rf "${SCR:?}"; rm -f "$KDIR/secret_key"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the file back"
  \cp -p "$BAK" "$F"; "$SYSTEMCTL" restart "$RSVC" || true
  say "   $N $(m5 "$F" | cut -c1-8) (expected ${FROM:0:8}); $RSVC restarted, health $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
pyrun() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$@" 2>&1 | grep -v '^att_correction'); }

if [ "${1:-}" = "--undo" ]; then
  [ "$(m5 "$F")" = "$FROM" ] && { say "-- $KIT is not installed (the file at its FROM pin) - nothing to undo."; exit 0; }
  [ -f "$BAK" ] && [ "$(m5 "$BAK")" = "$FROM" ] || { say "!! no good backup $BAK - nothing undone"; exit 1; }
  [ "$(m5 "$F")" = "$TO" ] || { say "!! $F is $(m5 "$F" | cut -c1-8), not this kit's - a later change is on it: nothing undone. Tell Claude."; exit 1; }
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
  \cp -p "$BAK" "$F"; "$SYSTEMCTL" restart "$RSVC"; h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but the register's health is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE (the file back, $RSVC restarted, health 200). An ask already made stays in the table (the old file counts it as a pause)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 "$KDIR/$N")" = "$TO" ] || { say "!! [1/5] the kit's $N is not as built - nothing installed"; exit 1; }
[ -f "$F" ] || { say "!! [1/5] $F missing - nothing installed"; exit 1; }
[ "$(m5 "$F")" = "$TO" ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$F")" = "$FROM" ] || stop "!! [2/5] $F is $(m5 "$F" | cut -c1-8), expected ${FROM:0:8} (S929) - STOP, nothing installed. Tell Claude."
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/$N" || stop "!! [2/5] $N does not compile on $p - nothing installed"; done
say "[2/5] the live pin exact (S929's); the file compiles on both pythons"
cp -p "$F" "$SCR/live_$N" || stop "!! [3/5] could not copy the live file - nothing installed"
W=$(pyrun "$KDIR/walk_s931.py" "$KDIR/$N"); R=$(echo "$W" | tail -1)
case "$R" in "WALK 17/17") ;; *) echo "$W" | grep '^FAIL' | cut -c1-160 | head -6 | sed 's/^/      /'; stop "!! [3/5] walk_s931 on the new file: $R - nothing installed";; esac
Rc=$(pyrun "$KDIR/walk_s931.py" "$SCR/live_$N" | tail -1)
case "$Rc" in "WALK 17/17") stop "!! [3/5] walk_s931's control (the live file) did not go red - nothing installed";; esac
R9=$(pyrun "$KDIR/walk_s929.py" "$KDIR/$N" | tail -1)
[ "$R9" = "WALK 23/23" ] || stop "!! [3/5] S929's walk on the new file: $R9 - nothing installed"
ST=$(cd "$SCR" && cp -p "$KDIR/$N" "$SCR/st_$N" && cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$SCR/st_$N" --selftest 2>&1 | grep -c '^SELFTEST OK')
[ "$ST" = 1 ] || stop "!! [3/5] the register's own --selftest on the new file is not OK - nothing installed"
say "[3/5] walk_s931 $R (control red: ${Rc:-crashed}); S929's walk $R9; the register's own selftest OK"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and walk green; nothing live changed"; exit 0; fi
h0=$(rhealth); [ "$h0" = 200 ] || stop "!! [4/5] the register's health $h0 before the install - nothing installed"
{ \cp -p "$F" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop "!! [4/5] could not write the backup of $N - nothing placed"
st="$RDIR/.$N.s931"; { cat "$KDIR/$N" > "$st" && chmod --reference="$F" "$st" 2>/dev/null; chown --reference="$F" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$TO" ]; } || stop "!! [4/5] could not stage $N - nothing placed"
mv -f "$st" "$F" || restore "the rename of $N"
[ "$(m5 "$F")" = "$TO" ] || restore "read back of $N"
"$SYSTEMCTL" restart "$RSVC" || restore "restart $RSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
h1=$(wait200); [ "$h1" = 200 ] || restore "the register's health $h1 after the restart"
release_lock
say "[4/5] placed and read back: $N at its TO pin; $RSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), health $h1"
say "[5/5] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""
say "$KIT: DONE."
exit 0
