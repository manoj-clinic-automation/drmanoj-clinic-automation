#!/bin/bash
# =============================================================================
#  install_S909_PHONE_DAILY_CHECK.sh · kit S909 (20-Nov-2026, Sanjeevni session 494) · D1026, the owner's "GO" 19:37 and "OK" 20:43 IST:
#  a morning check message the reception phone sends to the clinic's own WhatsApp; not in the clinic inbox in 20 min -> the failed step
#  found and mended where the server can (once more / the clinic doctor), and the owner told on his phone and in Needs-you.
#   NEW /root/finance/phone_check.py                 : the check (its own two tables, four settings; reads the receiver's files and
#        the inbox store READ ONLY; runs /root/deploy/clinic_doctor.py as it is; tells the owner through owner_notice's table).
#   /root/finance/supplier_msg.py 407d2b1d -> TO     : a 'check' message never retried, never on the stuck list or the silent line;
#        the check's Needs-you line joins this file's lines.
#   /root/finance/porders_s454.py 06966a0f -> TO     : the owner's Reception phone card shows the check, the clinic number (masked),
#        Save, Check now; two owner-only doors /finance/porders/api/s909/*.
#   cron: */5 ... phone_check.py tick # S909_PHONE_CHECK
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s909kit && cp -rp /root/deploy/repo/deploy_kits/S909_PHONE_DAILY_CHECK /tmp/s909kit && bash /tmp/s909kit/install_S909_PHONE_DAILY_CHECK.sh
#  (DRY=1 before bash: every gate and the walk; NOTHING written.)
# =============================================================================
set -u
KIT="S909_PHONE_DAILY_CHECK"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; CRONTAB="${CRONTAB:-crontab}"
NAMES=("finance/supplier_msg.py" "finance/porders_s454.py" "finance/phone_check.py")
FROMS=("407d2b1d4cf7bda3bb28263bd55e0aa9" "06966a0f9262b1f87c1b608129d11848" "absent")
KF=("supplier_msg.py" "porders_s454.py" "phone_check.py")
TOS=(); for k in 0 1 2; do TOS[$k]="$(awk -v f="${NAMES[$k]}" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
TAG="# S909_PHONE_CHECK"
CRONLINE="*/5 * * * * cd $ROOT/finance && $VPY -B phone_check.py tick >> $ROOT/finance/phone_check.log 2>&1 $TAG"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s909_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cur() { [ -f "$ROOT/${NAMES[$1]}" ] && m5 "$ROOT/${NAMES[$1]}" || echo absent; }
say() { echo "$@"; }
bak() { echo "$ROOT/${NAMES[$1]}.bak_S909_${FROMS[$1]:0:8}"; }
stg() { local n="${NAMES[$1]}"; echo "$(dirname "$ROOT/$n")/.$(basename "$n").s909"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD; else curl -s -o /dev/null -m 8 -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{}' "http://127.0.0.1:$FIN_PORT/finance/porders/api/s909/check_now"; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
cron_has() { "$CRONTAB" -l 2>/dev/null | grep -qF "$TAG"; }
cron_add() { cron_has && return 0; { "$CRONTAB" -l 2>/dev/null; echo "$CRONLINE"; } | "$CRONTAB" - && cron_has; }
cron_del() { cron_has || return 0; "$CRONTAB" -l 2>/dev/null | grep -vF "$TAG" | "$CRONTAB" -; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for k in 0 1 2; do rm -f "$(stg $k)"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting everything back"
  cron_del
  for k in 0 1; do [ -f "$(bak $k)" ] && \cp -p "$(bak $k)" "$ROOT/${NAMES[$k]}"; done; rm -f "$ROOT/${NAMES[2]}"; "$SYSTEMCTL" restart "$FSVC" || true
  for k in 0 1 2; do say "   ${NAMES[$k]} $(cur $k | cut -c1-8) (expected ${FROMS[$k]:0:8})"; done
  say "   cron line: $(cron_has && echo STILL THERE || echo removed). $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
lay() { local d="$SCR/root_$1"; rm -rf "$d"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" \
  && find "$ROOT/finance" -maxdepth 1 -type f \( -name '*.py' -o -name '*.json' \) -exec cp -p {} "$d/finance/" \; \
  && \cp -p "$ROOT"/finance/spine/*.py "$d/finance/spine/" 2>/dev/null; [ -f "$d/finance/supplier_msg.py" ]; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPATH="$ROOT/shared${PYTHONPATH:+:$PYTHONPATH}" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -u -W ignore -B "$@" 2>&1); }
CPDB='import sqlite3,sys;s=sqlite3.connect("file:%s?mode=ro"%sys.argv[1],uri=True,timeout=60);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close();s.close();print("copied")'

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in 0 1 2; do [ -n "${TOS[$k]}" ] && [ "$(m5 "$KDIR/${KF[$k]}")" = "${TOS[$k]}" ] || { say "!! [1/5] the kit's ${KF[$k]} is not at its TO pin - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/5] $DB missing - nothing installed"; exit 1; }
ALL=1; for k in 0 1 2; do [ "$(cur $k)" = "${TOS[$k]}" ] || ALL=0; done; cron_has || ALL=0
[ "$ALL" = 1 ] && { say "$KIT: ALREADY INSTALLED - the three files are at the new version and the cron line is there; nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for k in 0 1 2; do [ "$(cur $k)" = "${FROMS[$k]}" ] || stop "!! [2/5] $ROOT/${NAMES[$k]} is $(cur $k | cut -c1-8), expected ${FROMS[$k]:0:8} - STOP, nothing installed. Tell Claude."; done
cron_has && stop "!! [2/5] a cron line tagged $TAG is already there without the files - STOP, nothing installed. Tell Claude."
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/supplier_msg.py" "$KDIR/porders_s454.py" "$KDIR/phone_check.py" || stop "!! [2/5] a file does not compile on $p - nothing installed"; done
say "[2/5] the two live files are at their FROM pins, phone_check.py is new; the three compile on both pythons"
RAWD="${RAWD:-$ROOT/wa/wa_logs}"; INBOXD="${INBOXD:-$ROOT/wa/wa_inbox/inbox.db}"
GATE='import os,re,sqlite3,sys,time
d,db=sys.argv[1],sys.argv[2]
try: fs=[f for f in os.listdir(d) if re.match(r"^\d{4}-\d{2}-\d{2}\.jsonl$",f) and time.time()-os.path.getmtime(os.path.join(d,f))<3*86400]
except OSError: fs=[]
if not fs: print("no receiver file of the last 3 days in "+d); sys.exit(1)
try:
  c=sqlite3.connect("file:%s?mode=ro"%db,uri=True,timeout=20); cols={r[1] for r in c.execute("PRAGMA table_info(msgs)")}; c.close()
except sqlite3.Error as e: print("the inbox store cannot be read: %s"%e.__class__.__name__); sys.exit(1)
if "body" not in cols: print("the inbox store has no msgs.body"); sys.exit(1)
print("ok")'
g=$("$VPY" -c "$GATE" "$RAWD" "$INBOXD" 2>&1 | tail -1); [ "$g" = ok ] || stop "!! [2/5] where the check looks (read only): $g - nothing installed. Tell Claude."
say "[2/5] the receiver's files and the inbox store are where the check looks (read only)"
"$VPY" -c "$CPDB" "$DB" "$SCR/f_new.db" >/dev/null && "$VPY" -c "$CPDB" "$DB" "$SCR/f_old.db" >/dev/null || stop "!! [3/5] could not copy the database for the walk - nothing installed"
lay new && \cp -p "$KDIR/supplier_msg.py" "$KDIR/porders_s454.py" "$KDIR/phone_check.py" "$SCR/root_new/finance/" \
  && lay old && \cp -p "$KDIR/phone_check.py" "$SCR/root_old/finance/" || stop "!! [3/5] could not lay out the walk - nothing installed"
R1F=$(py "$KDIR/synth_s909.py" --code "$SCR/root_new/finance" --finance "$SCR/f_new.db"); R1=$(echo "$R1F" | tail -1)
case "$R1" in "synth_s909: "*" ok, 0 red") ;; *) echo "$R1F" | grep "^RED" | cut -c1-160; stop "!! [3/5] synth_s909 on a copy of the live database: $R1 - nothing installed";; esac
R0F=$(py "$KDIR/synth_s909.py" --code "$SCR/root_old/finance" --finance "$SCR/f_old.db"); R0=$(echo "$R0F" | tail -1)
echo "$R0F" | grep -q "^RED  T11 never on the stuck list" || stop "!! [3/5] the control on the live files did not go red where it must ($R0) - nothing installed"
say "[3/5] $R1 (a copy of the live database); the control on the live files: red ($R0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for k in 0 1; do { \cp -p "$ROOT/${NAMES[$k]}" "$(bak $k)" && [ "$(m5 "$(bak $k)")" = "${FROMS[$k]}" ]; } || stop "!! [4/5] could not write the backup of ${NAMES[$k]} - nothing placed"; done
for k in 0 1 2; do s="$(stg $k)"; { cat "$KDIR/${KF[$k]}" > "$s" && chmod --reference="$ROOT/${NAMES[0]}" "$s" 2>/dev/null; chown --reference="$ROOT/${NAMES[0]}" "$s" 2>/dev/null; [ "$(m5 "$s")" = "${TOS[$k]}" ]; } || stop "!! [4/5] could not stage ${KF[$k]} - nothing placed"; done
PLACING=1
for k in 2 0 1; do mv -f "$(stg $k)" "$ROOT/${NAMES[$k]}" || restore "the rename of ${KF[$k]}"; [ "$(cur $k)" = "${TOS[$k]}" ] || restore "read back of ${KF[$k]}"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d1=$(door); case "$d1" in 404|000|5*) restore "the new door answers $d1 (not mounted)";; esac
cron_add || restore "the cron line could not be written"
t1=$(cd "$ROOT/finance" && PHONE_CHECK_DB="$DB" PHONE_CHECK_LOCK="$SCR/lk" timeout 120 "$VPY" -B phone_check.py status 2>&1 | tail -1)
case "$t1" in "S909 "*) ;; *) restore "phone_check.py status on the live database: $t1";; esac
PLACING=0
release_lock
say "[4/5] three files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the new door answers $d1 (mounted, login-gated); cron line added; $t1"
say "[5/5] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s909.sh  (the files back, phone_check.py and its cron line removed, $FSVC restarted)"
say ""
say "$KIT: DONE. On your Reception phone card: save the clinic's WhatsApp number once, then tap Check now."
exit 0
