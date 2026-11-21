#!/bin/bash
# =============================================================================
#  install_S914_PHONE_SETUP_PAGE.sh · kit S914 (21-Nov-2026, Sanjeevni session 497) · D1029 (the owner's own phone steps,
#  19:58-20:43 IST 20-Nov): the reception phone's set-up written as the phone now stands.
#   /root/finance/supplier_msg.py 77656157 -> TO  : the set-up page /finance/purchase/page/phone-setup (Hindi, staff) -- screen
#        lock None; the macro with NO constraints; Screen On + Wait 2 s after JSON Parse; the 'sent' POST with no constraint;
#        a card saying the 10:00 daily check proves it; the Clinic PCs page named for the whole macro file. Nothing else changes.
#   /root/finance/porders_s454.py 0053ae60 -> TO  : three wordings that said "keep the phone unlocked" / "a dark phone does not
#        ask" (reception's WhatsApp line, the silent-phone line, the owner's Reception phone card). No flow changes.
#   The repository's reference macro deploy_kits/PC_KITS/macrodroid/receptionmobile/ is brought to the same in the publish
#   itself (the server reads it from its own pull) -- nothing for this script.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s914kit && cp -rp /root/deploy/repo/deploy_kits/S914_PHONE_SETUP_PAGE /tmp/s914kit && bash /tmp/s914kit/install_S914_PHONE_SETUP_PAGE.sh
#  (DRY=1 before bash: every gate and the walk; NOTHING written.)
# =============================================================================
set -u
KIT="S914_PHONE_SETUP_PAGE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES=("finance/supplier_msg.py" "finance/porders_s454.py")
FROMS=("77656157b038765d2b88f8ec28069b81" "0053ae60f8dc93d9301463ba69671aed")
KF=("supplier_msg.py" "porders_s454.py")
TOS=(); for k in 0 1; do TOS[$k]="$(awk -v f="${NAMES[$k]}" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s914_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cur() { [ -f "$ROOT/${NAMES[$1]}" ] && m5 "$ROOT/${NAMES[$1]}" || echo absent; }
say() { echo "$@"; }
bak() { echo "$ROOT/${NAMES[$1]}.bak_S914_${FROMS[$1]:0:8}"; }
stg() { local n="${NAMES[$1]}"; echo "$(dirname "$ROOT/$n")/.$(basename "$n").s914"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for k in 0 1; do rm -f "$(stg $k)"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting everything back"
  for k in 0 1; do [ -f "$(bak $k)" ] && \cp -p "$(bak $k)" "$ROOT/${NAMES[$k]}"; done; "$SYSTEMCTL" restart "$FSVC" || true
  for k in 0 1; do say "   ${NAMES[$k]} $(cur $k | cut -c1-8) (expected ${FROMS[$k]:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -u -W ignore -B "$@" 2>&1); }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in 0 1; do [ -n "${TOS[$k]}" ] && [ "$(m5 "$KDIR/${KF[$k]}")" = "${TOS[$k]}" ] || { say "!! [1/5] the kit's ${KF[$k]} is not at its TO pin - nothing installed"; exit 1; }; done
ALL=1; for k in 0 1; do [ "$(cur $k)" = "${TOS[$k]}" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "$KIT: ALREADY INSTALLED - both files are at the new version; nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for k in 0 1; do [ "$(cur $k)" = "${FROMS[$k]}" ] || stop "!! [2/5] $ROOT/${NAMES[$k]} is $(cur $k | cut -c1-8), expected ${FROMS[$k]:0:8} - STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/supplier_msg.py" "$KDIR/porders_s454.py" || stop "!! [2/5] a file does not compile on $p - nothing installed"; done
say "[2/5] both live files are at their FROM pins; the two new ones compile on both pythons"
mkdir -p "$SCR/new" "$SCR/old" && \cp -p "$KDIR/supplier_msg.py" "$KDIR/porders_s454.py" "$SCR/new/" \
  && \cp -p "$ROOT/${NAMES[0]}" "$ROOT/${NAMES[1]}" "$SCR/old/" || stop "!! [3/5] could not lay out the walk - nothing installed"
R1F=$(py "$KDIR/synth_s914.py" --code "$SCR/new"); R1=$(echo "$R1F" | tail -1)
case "$R1" in "synth_s914: "*" ok, 0 red") ;; *) echo "$R1F" | grep "^RED" | cut -c1-160; stop "!! [3/5] synth_s914 on the new files: $R1 - nothing installed";; esac
R0F=$(py "$KDIR/synth_s914.py" --code "$SCR/old"); R0=$(echo "$R0F" | tail -1)
echo "$R0F" | grep -q "^RED  T2 screen lock None" && echo "$R0F" | grep -q "^RED  T11 " || stop "!! [3/5] the control on the live files did not go red where it must ($R0) - nothing installed"
say "[3/5] $R1 (the page rendered on a made-up database); the control on the live files: red ($R0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for k in 0 1; do { \cp -p "$ROOT/${NAMES[$k]}" "$(bak $k)" && [ "$(m5 "$(bak $k)")" = "${FROMS[$k]}" ]; } || stop "!! [4/5] could not write the backup of ${NAMES[$k]} - nothing placed"; done
for k in 0 1; do s="$(stg $k)"; { cat "$KDIR/${KF[$k]}" > "$s" && chmod --reference="$ROOT/${NAMES[$k]}" "$s" 2>/dev/null; chown --reference="$ROOT/${NAMES[$k]}" "$s" 2>/dev/null; [ "$(m5 "$s")" = "${TOS[$k]}" ]; } || stop "!! [4/5] could not stage ${KF[$k]} - nothing placed"; done
PLACING=1
for k in 0 1; do mv -f "$(stg $k)" "$ROOT/${NAMES[$k]}" || restore "the rename of ${KF[$k]}"; [ "$(cur $k)" = "${TOS[$k]}" ] || restore "read back of ${KF[$k]}"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d1=$(door /finance/purchase/page/phone-setup); case "$d1" in 404|000|5*) restore "the set-up page answers $d1 (not mounted)";; esac
d2=$(door /finance/porders/s454/old); case "$d2" in 404|000|5*) restore "the orders page answers $d2";; esac
PLACING=0
release_lock
say "[4/5] two files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the set-up page answers $d1 and the orders page $d2 (mounted, login-gated)"
say "[5/5] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s914.sh  (both files back, $FSVC restarted)"
say ""
say "$KIT: DONE."
exit 0
