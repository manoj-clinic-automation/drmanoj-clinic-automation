#!/bin/bash
# =============================================================================
#  install_S898_PHONE_STUCK_AND_SILENT.sh · kit S898 (20-Nov-2026, Sanjeevni session 490) · the owner 17:49 IST: "old 2 messages not sent
#  need to be removed from reminder or sent again, but thru a built in functionality in the reception phone page as well"
#   /root/finance/supplier_msg.py bdfe4ce7 -> TO : the phone's last 'sent' report kept; ONE Needs-you line when the phone takes
#        messages but its 'sent' report stops (the 12-Nov..20-Nov MacroDroid constraint); the stuck list, Send again, Remove.
#   /root/finance/porders_s454.py c992ba91 -> TO : the owner's Reception phone card shows the last report and the messages the phone
#        took and never reported, each with Send again / Remove (two-tap, no dialog); two owner-only doors /finance/porders/api/s898/*.
#   /root/finance/finance_ui/finance_approvals.html f045686d -> TO : the Hub's Go to links to that card.
#   All three built by make_s898.py from the live bytes (anchors). No table added; one setting written by the server itself.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s898kit && cp -rp /root/deploy/repo/deploy_kits/S898_PHONE_STUCK_AND_SILENT /tmp/s898kit && bash /tmp/s898kit/install_S898_PHONE_STUCK_AND_SILENT.sh
#  (DRY=1 before bash: every gate and the walk; NOTHING written.)
# =============================================================================
set -u
KIT="S898_PHONE_STUCK_AND_SILENT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES=("finance/supplier_msg.py" "finance/porders_s454.py" "finance/finance_ui/finance_approvals.html")
FROMS=("bdfe4ce75ca0930b92ecd4fd960723cd" "c992ba910315200293fdd7273ebbfacb" "f045686d8f53535184bbb64758165118")
KF=("supplier_msg.py" "porders_s454.py" "finance_approvals.html")
TOS=(); for k in 0 1 2; do TOS[$k]="$(awk -v f="${NAMES[$k]}" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s898_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/${NAMES[$1]}.bak_S898_${FROMS[$1]:0:8}"; }
stg() { local n="${NAMES[$1]}"; echo "$(dirname "$ROOT/$n")/.$(basename "$n").s898"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD; else curl -s -o /dev/null -m 8 -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{}' "http://127.0.0.1:$FIN_PORT/finance/porders/api/s898/remove"; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for k in 0 1 2; do rm -f "$(stg $k)"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting the three files back"
  for k in 0 1 2; do [ -f "$(bak $k)" ] && \cp -p "$(bak $k)" "$ROOT/${NAMES[$k]}"; done; "$SYSTEMCTL" restart "$FSVC" || true
  for k in 0 1 2; do say "   ${NAMES[$k]} $(m5 "$ROOT/${NAMES[$k]}" | cut -c1-8) (expected ${FROMS[$k]:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Nothing else was changed. Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
lay() { local d="$SCR/root_$1"; rm -rf "$d"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" \
  && find "$ROOT/finance" -maxdepth 1 -type f \( -name '*.py' -o -name '*.json' \) -exec cp -p {} "$d/finance/" \; \
  && \cp -p "$ROOT"/finance/spine/*.py "$d/finance/spine/" 2>/dev/null; \cp -p "$ROOT/finance/finance_ui/finance_approvals.html" "$d/finance/finance_ui/"; \
  [ -f "$d/finance/supplier_msg.py" ]; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPATH="$ROOT/shared${PYTHONPATH:+:$PYTHONPATH}" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -u -W ignore -B "$@" 2>&1); }
CPDB='import sqlite3,sys;s=sqlite3.connect("file:%s?mode=ro"%sys.argv[1],uri=True,timeout=60);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close();s.close();print("copied")'

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in 0 1 2; do [ -n "${TOS[$k]}" ] && [ "$(m5 "$KDIR/${KF[$k]}")" = "${TOS[$k]}" ] || { say "!! [1/5] the kit's ${KF[$k]} is not at its TO pin - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/5] $DB missing - nothing installed"; exit 1; }
ALL=1; for k in 0 1 2; do [ "$(m5 "$ROOT/${NAMES[$k]}")" = "${TOS[$k]}" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "$KIT: ALREADY INSTALLED - the three files are at the new version; nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for k in 0 1 2; do [ "$(m5 "$ROOT/${NAMES[$k]}")" = "${FROMS[$k]}" ] || stop "!! [2/5] $ROOT/${NAMES[$k]} is $(m5 "$ROOT/${NAMES[$k]}" | cut -c1-8), expected ${FROMS[$k]:0:8} - STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/supplier_msg.py" "$KDIR/porders_s454.py" || stop "!! [2/5] a file does not compile on $p - nothing installed"; done
say "[2/5] the three live files are at their FROM pins; the new ones compile on both pythons"
"$VPY" -c "$CPDB" "$DB" "$SCR/f_new.db" >/dev/null && "$VPY" -c "$CPDB" "$DB" "$SCR/f_old.db" >/dev/null || stop "!! [3/5] could not copy the database for the walk - nothing installed"
lay new && \cp -p "$KDIR/supplier_msg.py" "$KDIR/porders_s454.py" "$SCR/root_new/finance/" && \cp -p "$KDIR/finance_approvals.html" "$SCR/root_new/finance/finance_ui/" && lay old || stop "!! [3/5] could not lay out the walk - nothing installed"
R1=$(py "$KDIR/synth_s898.py" --code "$SCR/root_new/finance" --finance "$SCR/f_new.db" | tail -1)
case "$R1" in "synth_s898: "*" ok, 0 red") ;; *) stop "!! [3/5] synth_s898 on a copy of the live database: $R1 - nothing installed";; esac
R0=$(py "$KDIR/synth_s898.py" --code "$SCR/root_old/finance" --finance "$SCR/f_old.db" | tail -1)
case "$R0" in "synth_s898: "*" ok, 0 red") stop "!! [3/5] the control on the live files did not go red ($R0) - nothing installed";; esac
say "[3/5] $R1 (a copy of the live database); the control on the live files: red ($R0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for k in 0 1 2; do { \cp -p "$ROOT/${NAMES[$k]}" "$(bak $k)" && [ "$(m5 "$(bak $k)")" = "${FROMS[$k]}" ]; } || stop "!! [4/5] could not write the backup of ${NAMES[$k]} - nothing placed"; done
for k in 0 1 2; do s="$(stg $k)"; { cat "$KDIR/${KF[$k]}" > "$s" && chmod --reference="$ROOT/${NAMES[$k]}" "$s" 2>/dev/null; chown --reference="$ROOT/${NAMES[$k]}" "$s" 2>/dev/null; [ "$(m5 "$s")" = "${TOS[$k]}" ]; } || stop "!! [4/5] could not stage ${KF[$k]} - nothing placed"; done
PLACING=1
for k in 0 1 2; do mv -f "$(stg $k)" "$ROOT/${NAMES[$k]}" || restore "the rename of ${KF[$k]}"; [ "$(m5 "$ROOT/${NAMES[$k]}")" = "${TOS[$k]}" ] || restore "read back of ${KF[$k]}"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d1=$(door); case "$d1" in 404|000|5*) restore "the new door answers $d1 (not mounted)";; esac
PLACING=0
release_lock
say "[4/5] three files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the new door answers $d1 (mounted, login-gated)"
say "[5/5] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s898.sh  (the three files back, $FSVC restarted)"
say ""
say "$KIT: DONE. Your Reception phone card lists the messages the phone took and never reported, with Send again / Remove."
exit 0
