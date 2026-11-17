#!/bin/bash
# =============================================================================
#  install_S848_SUMMARY_PARTS.sh · kit S848 (17-Nov-2026, Sanjeevni session 473) · the owner's question 11:16 IST: L.K. Drug House sent October
#  in TWO summary papers (B-0296 Rs 3,656 + B-0332 Rs 9,178 = Marg Rs 12,834); only the newest spoke, so L.K. read 'Rs 3,656 short' and
#  October's lock held. Now a dealer's papers of one month that list DIFFERENT bills add up; any bill or credit on two papers (a revision or
#  a repeat) -- the newest speaks, as before.
#   /root/finance/scan_register.py f0bb05cd -> TO   (the whole file, made by make_s848.py from the FROM bytes on exact anchors)
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s848kit && cp -rp /root/deploy/repo/deploy_kits/S848_SUMMARY_PARTS /tmp/s848kit && bash /tmp/s848kit/install_S848_SUMMARY_PARTS.sh
#  (DRY=1 before bash: every gate and walk; NOTHING written.)
# =============================================================================
set -u
KIT="S848_SUMMARY_PARTS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"; ADB="${ADB:-$ROOT/assetapp/assets.db}"
KD="${KD:-/root/deploy/repo/deploy_kits}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
N="finance/scan_register.py"; FROM="f0bb05cd41a67769be3778545c1d2d5b"
TO="$(awk -v f="$N" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s848_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
BAK="$ROOT/$N.bak_S848_${FROM:0:8}"; STG="$ROOT/finance/.scan_register.py.s848"
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$STG"; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting the old file back"
  \cp -p "$BAK" "$ROOT/$N"; "$SYSTEMCTL" restart "$FSVC" || true
  say "   $N $(m5 "$ROOT/$N" | cut -c1-8) (expected ${FROM:0:8}); $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
lay() { local d="$SCR/root_$1"; rm -rf "$d"; mkdir -p "$d/finance" \
  && find "$ROOT/finance" -maxdepth 1 -type f \( -name '*.py' -o -name '*.html' -o -name '*.sql' -o -name '*.json' \) -exec cp -p {} "$d/finance/" \; \
  && [ -f "$d/finance/scan_register.py" ]; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPATH="$ROOT/shared${PYTHONPATH:+:$PYTHONPATH}" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
CPDB='import sqlite3,sys;s=sqlite3.connect("file:%s?mode=ro"%sys.argv[1],uri=True,timeout=60);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close();s.close();print("copied")'

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$TO" ] && [ "$(m5 "$KDIR/scan_register.py")" = "$TO" ] || { say "!! [1/5] the kit's file is not at its TO pin - nothing installed"; exit 1; }
[ -f "$DB" ] && [ -f "$ADB" ] || { say "!! [1/5] $DB or $ADB missing - nothing installed"; exit 1; }
for w in S750_MONTH_END/walk_s750.py S753_SUMMARY_SCANS_READ/walk_s753.py S755_SUMMARY_REMINDERS/walk_s755.py; do [ -f "$KD/$w" ] || { say "!! [1/5] $KD/$w missing - publish first. Nothing installed."; exit 1; }; done
[ "$(m5 "$ROOT/$N")" = "$TO" ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$ROOT/$N")" = "$FROM" ] || stop "!! [2/5] $ROOT/$N is $(m5 "$ROOT/$N" | cut -c1-8), expected ${FROM:0:8} - STOP, nothing installed. Tell Claude."
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/scan_register.py" || stop "!! [2/5] the file does not compile on $p - nothing installed"; done
say "[2/5] the live file is at FROM (${FROM:0:8}); the new one compiles on both pythons"
"$VPY" -c "$CPDB" "$DB" "$SCR/finance.db" >/dev/null && "$VPY" -c "$CPDB" "$ADB" "$SCR/assets.db" >/dev/null || stop "!! [3/5] could not copy the databases for the walk - nothing installed"
lay new && \cp -p "$KDIR/scan_register.py" "$SCR/root_new/$N" && lay old || stop "!! [3/5] could not lay out the walk - nothing installed"
R1=$(ASSETS_COPY="$SCR/assets.db" py "$KDIR/synth_s848.py" "$SCR/root_new/finance" "$SCR/finance.db" --real | tail -1)
case "$R1" in "SYNTH S848: "*" PASS, 0 FAIL") ;; *) stop "!! [3/5] synth_s848 on the new file (copies of the live databases): $R1 - nothing installed. Tell Claude.";; esac
R0=$(ASSETS_COPY="$SCR/assets.db" py "$KDIR/synth_s848.py" "$SCR/root_old/finance" "$SCR/finance.db" | tail -1)
case "$R0" in "SYNTH S848: "*" PASS, 0 FAIL") stop "!! [3/5] the control on the live file did not go red ($R0) - nothing installed";; esac
for w in S750_MONTH_END/walk_s750.py S753_SUMMARY_SCANS_READ/walk_s753.py S755_SUMMARY_REMINDERS/walk_s755.py; do
  a=$(py "$KD/$w" "$SCR/root_old/finance" "$ROOT/finance/purchase_schema.sql" "$ROOT/shared" | tail -1)
  b=$(py "$KD/$w" "$SCR/root_new/finance" "$ROOT/finance/purchase_schema.sql" "$ROOT/shared" | tail -1)
  [ "$a" = "$b" ] || stop "!! [3/5] $(basename "$w") differs on the new file: live '$a' / new '$b' - nothing installed"
done
say "[3/5] $R1 (copies of the live databases; L.K.'s live October agrees); the control on the live file: red; walks s750/s753/s755 the same on old and new"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and walk green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
{ \cp -p "$ROOT/$N" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop "!! [4/5] could not write the backup - nothing placed"
{ cat "$KDIR/scan_register.py" > "$STG" && chmod --reference="$ROOT/$N" "$STG" 2>/dev/null; chown --reference="$ROOT/$N" "$STG" 2>/dev/null; [ "$(m5 "$STG")" = "$TO" ]; } || stop "!! [4/5] could not stage the file - nothing placed"
PLACING=1
mv -f "$STG" "$ROOT/$N" || restore "the rename"
[ "$(m5 "$ROOT/$N")" = "$TO" ] || restore "read back"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
PLACING=0
release_lock
say "[4/5] placed and read back at ${TO:0:8}; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1"
say "[5/5] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s848.sh"
say ""
say "$KIT: DONE. A dealer's summary sent in parts now adds up; L.K.'s October agrees."
exit 0
