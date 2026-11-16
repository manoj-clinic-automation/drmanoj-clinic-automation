#!/bin/bash
# =============================================================================
#  install_S847_LEDGER_ARRIVED.sh · kit S847 (16-Nov-2026, Sanjeevni session 470) · after reading the live Item ledger (S845) at 11:3x IST:
#  ROSIKA FORTE's expected stock read 5071:0 from a 12-Oct scan whose quantity was read as 5010. On the Item ledger's "Arrived -- not yet in
#  Marg", a scan more than the arrivals' grace older than Marg's newest purchase bill, or a line far beyond the item's own purchases and
#  closings, is SHOWN with its reason and NEVER added to the expected stock. Read only, as S845.
#   /root/finance/item_ledger.py 22c24bd9 (S845) -> TO   (the whole file: it is this project's own, read back against its FROM pin first)
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s847kit && cp -rp /root/deploy/repo/deploy_kits/S847_LEDGER_ARRIVED /tmp/s847kit && bash /tmp/s847kit/install_S847_LEDGER_ARRIVED.sh
#  (DRY=1 before bash: every gate and walk; NOTHING written.)
# =============================================================================
set -u
KIT="S847_LEDGER_ARRIVED"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"; SPDB="${SPDB:-$ROOT/finance/spine/spine.db}"
K845="${K845:-/root/deploy/repo/deploy_kits/S845_ITEM_LEDGER}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
N="finance/item_ledger.py"; FROM="22c24bd91e82f77cc34c5f4d27d8dc51"
TO="$(awk -v f="$N" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s847_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
BAK="$ROOT/$N.bak_S847_${FROM:0:8}"; STG="$ROOT/finance/.item_ledger.py.s847"
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
flz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/sanjeevni/ledger/api/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/sanjeevni/ledger/api/healthz"; fi; }
jnl() { if [ -n "${JOURNAL_CMD:-}" ]; then $JOURNAL_CMD; elif command -v journalctl >/dev/null 2>&1; then journalctl -u "$FSVC" --since "@$1" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$STG"; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting S845's page back"
  \cp -p "$BAK" "$ROOT/$N"; "$SYSTEMCTL" restart "$FSVC" || true
  say "   $N $(m5 "$ROOT/$N" | cut -c1-8) (expected ${FROM:0:8}); $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
lay() { local d="$SCR/root_$1"; rm -rf "$d"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" \
  && find "$ROOT/finance" -maxdepth 1 -type f \( -name '*.py' -o -name '*.html' -o -name '*.sql' -o -name '*.json' \) -exec cp -p {} "$d/finance/" \; \
  && \cp -p "$ROOT"/finance/finance_ui/*.html "$d/finance/finance_ui/" 2>/dev/null; \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$d/finance/spine/" 2>/dev/null; \
  [ -f "$d/finance/item_ledger.py" ] && [ -f "$d/finance/spine/spine_read.py" ]; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPATH="$ROOT/shared${PYTHONPATH:+:$PYTHONPATH}" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
full() { case "$1" in "WALK S845: "*" PASS, 0 FAIL"|"SYNTH S84"[57]": "*" PASS, 0 FAIL") return 0;; *) return 1;; esac; }
CPDB='import sqlite3,sys;s=sqlite3.connect("file:%s?mode=ro"%sys.argv[1],uri=True,timeout=60);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close();s.close();print("copied")'

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$TO" ] && [ "$(m5 "$KDIR/item_ledger.py")" = "$TO" ] || { say "!! [1/5] the kit's page is not at its TO pin - nothing installed"; exit 1; }
[ -f "$DB" ] && [ -f "$SPDB" ] || { say "!! [1/5] $DB or $SPDB missing - nothing installed"; exit 1; }
[ -f "$K845/walk_s845.py" ] && [ -f "$K845/synth_s845.py" ] || { say "!! [1/5] S845's kit is not in $K845 - publish first. Nothing installed."; exit 1; }
[ "$(m5 "$ROOT/$N")" = "$TO" ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$ROOT/$N")" = "$FROM" ] || stop "!! [2/5] $ROOT/$N is $(m5 "$ROOT/$N" | cut -c1-8), expected S845's ${FROM:0:8} - STOP, nothing installed. Tell Claude."
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/item_ledger.py" || stop "!! [2/5] the page does not compile on $p - nothing installed"; done
say "[2/5] the live page is S845's (${FROM:0:8}); the new one compiles on both pythons"
"$VPY" -c "$CPDB" "$DB" "$SCR/finance.db" >/dev/null && "$VPY" -c "$CPDB" "$SPDB" "$SCR/spine.db" >/dev/null || stop "!! [3/5] could not copy the databases for the walk - nothing installed"
lay new && \cp -p "$KDIR/item_ledger.py" "$SCR/root_new/$N" || stop "!! [3/5] could not lay out the walk - nothing installed"
R1=$(SPINE_DB="$SCR/spine.db" py "$K845/walk_s845.py" "$SCR/root_new/finance" "$SCR/finance.db" --box | tail -1); full "$R1" || stop "!! [3/5] S845's walk on the new page (copies of the live databases): $R1 - nothing installed"
R2=$(py "$KDIR/synth_s847.py" "$SCR/root_new/finance" "$K845" | tail -1); full "$R2" || stop "!! [3/5] synth_s847 on the new page: $R2 - nothing installed"
R3=$(py "$K845/synth_s845.py" "$SCR/root_new/finance" | tail -1); full "$R3" || stop "!! [3/5] synth_s845 on the new page: $R3 - nothing installed"
lay old || stop "!! [3/5] could not lay out the control - nothing installed"
R0=$(py "$KDIR/synth_s847.py" "$SCR/root_old/finance" "$K845" | tail -1); full "$R0" && stop "!! [3/5] the control on the live page did not go red ($R0) - nothing installed"
say "[3/5] $R1 (copies of the live databases); $R2; $R3; the control on the live page: red"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and walk green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
{ \cp -p "$ROOT/$N" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop "!! [4/5] could not write the backup - nothing placed"
{ cat "$KDIR/item_ledger.py" > "$STG" && chmod --reference="$ROOT/$N" "$STG" 2>/dev/null; chown --reference="$ROOT/$N" "$STG" 2>/dev/null; [ "$(m5 "$STG")" = "$TO" ]; } || stop "!! [4/5] could not stage the page - nothing placed"
PLACING=1; T0=$(date +%s)
mv -f "$STG" "$ROOT/$N" || restore "the rename"
[ "$(m5 "$ROOT/$N")" = "$TO" ] || restore "read back"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
l1=$(flz); case "$l1" in 404|000|5*) restore "the ledger answered $l1 after the restart (not mounted)";; esac
jnl "$T0" | grep -q "item_ledger NOT mounted" && restore "the Hub's log says the ledger was NOT mounted"
PLACING=0
release_lock
say "[4/5] placed and read back at ${TO:0:8}; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the ledger answers ($l1)"
say "[5/5] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s847.sh  (S845's page back, $FSVC restarted)"
say ""
say "$KIT: DONE. A stale scan or a misread quantity is now shown on the Item ledger, never added to the expected stock."
exit 0
