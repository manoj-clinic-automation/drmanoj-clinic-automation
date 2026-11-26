#!/bin/bash
# =============================================================================
#  install_S964_VOUCHER_NAME_SHAPE.sh · kit S964 (26-Nov-2026, Sanjeevni session 530)
#  The S963 reader refused the real Stock Receive report of 26-Nov: four item names carry an inch mark (PRIME PAD 4"), which its
#  item-name shape did not allow, and the door then kept no file of it. This kit:
#   1. /root/marg_ingest/marg_vouchers.py 7bc3df84 -> TO (the item-name shape: any printed mark, single spaces, at most 24 letters)
#   2. clears the server's record of every voucher sheet refused for that shape (mi_voucher_file + mi_file rows, nothing else), so the
#      five-minute collection takes it again from Drive MargArchive (the medical PC's copy is there) -- no step for anyone.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s964kit && cp -rp /root/deploy/repo/deploy_kits/S964_VOUCHER_NAME_SHAPE /tmp/s964kit && bash /tmp/s964kit/install_S964_VOUCHER_NAME_SHAPE.sh
#  (DRY=1 before bash: every gate, the walk and the control; NOTHING written.)
# =============================================================================
set -u
KIT="S964_VOUCHER_NAME_SHAPE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
S963K="${S963K:-/root/deploy/repo/deploy_kits/S963_STOCK_VOUCHERS}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; MLOCK="${MLOCK:-/tmp/marg_ingest.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
N="marg_ingest/marg_vouchers.py"; FROM="7bc3df848ff4a8fdb5ba6d978d4496c0"; TO="$(awk -v f="$N" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s964_inst_$STAMP"; TOOK_LOCK=0; HELD_M=0
BAK="$ROOT/$N.bak_S964_${FROM:0:8}"; STG="$ROOT/marg_ingest/.marg_vouchers.py.s964"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
take_m() { exec 9>>"$MLOCK" && flock -w "${MWAIT:-120}" 9 && HELD_M=1; }
free_m() { [ "$HELD_M" = 1 ] || return 0; flock -u 9; exec 9>&-; HELD_M=0; }
release_lock() { free_m; [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$STG"; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the S963 reader back"
  [ "$HELD_M" = 1 ] || take_m || true
  { cat "$BAK" > "$STG" && mv -f "$STG" "$ROOT/$N"; } || \cp -p "$BAK" "$ROOT/$N"
  "$SYSTEMCTL" restart "$FSVC" || true; free_m
  say "   $N $(m5 "$ROOT/$N" | cut -c1-8) (expected ${FROM:0:8}); finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
full() { case "$1" in "WALK "*) local a=${1#WALK }; [ "${a%/*}" = "${a#*/}" ];; *) return 1;; esac; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] && [ -n "$TO" ] || { say "!! [1/5] KIT_ID / TO pin wrong - nothing installed"; exit 1; }
[ "$(m5 "$ROOT/$N")" = "$TO" ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
[ -f "$DB" ] && [ -f "$S963K/walk_s963.py" ] && [ -f "$S963K/medical/marg_txt.py" ] || { say "!! [1/5] $DB or the S963 kit's walk is missing - nothing installed"; exit 1; }
(cd /tmp && "$VPY" -B -c "import sys; sys.path.insert(0, sys.argv[1]); import xlrd" "$ROOT/marg_ingest") >/dev/null 2>&1 || { say "!! [1/5] $VPY cannot import xlrd beside $ROOT/marg_ingest - nothing installed. Tell Claude."; exit 1; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK - nothing installed. Run it again in five minutes."; exit 3; fi

[ "$(m5 "$ROOT/$N")" = "$FROM" ] || stop "!! [2/5] $ROOT/$N is $(m5 "$ROOT/$N" | cut -c1-8), expected ${FROM:0:8} - it changed after this kit was built: nothing installed. Tell Claude."
[ "$(m5 "$KDIR/marg_vouchers.py")" = "$TO" ] || stop "!! [2/5] the kit's reader is not at its TO pin - nothing installed"
for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$KDIR/marg_vouchers.py" || stop "!! [2/5] does not compile on $py - nothing installed"; done
ST=$(cd "$KDIR" && PYTHONPYCACHEPREFIX="$SCR/pyc" "$VPY" -B marg_vouchers.py --selftest 2>&1 | tail -1); [ "$ST" = "SELFTEST OK" ] || stop "!! [2/5] the new reader's selftest: $ST - nothing installed"
CTL=$(cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" "$VPY" -B -c "
import importlib.util,sys
s=importlib.util.spec_from_file_location('old',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
r=[x if x[3]!='MEG QCS' else x[:3]+['PRIME PAD 4\"']+x[4:] for x in m._rows()]
try:
    m.read(m._Sheet(r)); print('read')
except m.NotRead: print('refused')" "$ROOT/$N" 2>&1 | tail -1)
[ "$CTL" = "refused" ] || stop "!! [2/5] the control: the live reader did not refuse an inch mark ($CTL) - nothing installed"
say "[2/5] the live reader exact (${FROM:0:8}); the new one at its TO pin, compiles on both pythons, selftest OK; the control: the live one refuses PRIME PAD 4\""

d="$SCR/root_new"; mkdir -p "$d/marg_ingest/lib" && find "$ROOT/marg_ingest" -maxdepth 1 -type f \( -name '*.py' -o -name '*.json' \) -exec cp -p {} "$d/marg_ingest/" \; \
  && { \cp -p "$ROOT"/marg_ingest/lib/*.py "$d/marg_ingest/lib/" 2>/dev/null; true; } && { [ ! -d "$ROOT/marg_ingest/xlrd" ] || \cp -rp "$ROOT/marg_ingest/xlrd" "$d/marg_ingest/xlrd"; } \
  && \cp -p "$KDIR/marg_vouchers.py" "$d/$N" || stop "!! [3/5] could not lay out the walk - nothing installed"
R=$(cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$S963K/walk_s963.py" "$d" "$S963K" 2>&1 | tail -1)
full "$R" || stop "!! [3/5] the S963 walk on the new reader: $R - nothing installed"
say "[3/5] the S963 walk on the new reader (made-up reports, a scratch database): $R"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the control green; NOTHING written"; exit 0; fi

f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
{ \cp -p "$ROOT/$N" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop "!! [4/5] could not write the backup - nothing placed"
{ cat "$KDIR/marg_vouchers.py" > "$STG" && chmod --reference="$ROOT/$N" "$STG" 2>/dev/null; chown --reference="$ROOT/$N" "$STG" 2>/dev/null; [ "$(m5 "$STG")" = "$TO" ]; } || stop "!! [4/5] could not stage - nothing placed"
take_m || stop "!! [4/5] the collector's lock was not free - nothing placed. Run it again."
mv -f "$STG" "$ROOT/$N" || restore "the rename"
[ "$(m5 "$ROOT/$N")" = "$TO" ] || restore "read back"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
say "[4/5] placed under the collector's lock and read back (${TO:0:8}); $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1"
CL=$(cd /tmp && "$VPY" -B -c "
import sqlite3,sys
c=sqlite3.connect(sys.argv[1],timeout=60)
m=[r[0] for r in c.execute(\"SELECT v.md5 FROM mi_voucher_file v JOIN mi_file f ON f.md5=v.md5 WHERE v.ok=0 AND f.type='STOCK_VOUCHERS' AND f.kept=0 AND v.note LIKE 'not read: row % a cell not of its column%'\")]
for x in m:
    c.execute('DELETE FROM mi_voucher_file WHERE md5=?',(x,)); c.execute('DELETE FROM mi_file WHERE md5=?',(x,))
c.commit(); print('cleared %d' % len(m))" "$DB" 2>&1 | tail -1)
free_m
case "$CL" in "cleared "*) ;; *) restore "clearing the refused record: $CL";; esac
release_lock
say "[5/5] $CL refused voucher sheet(s) from the server's record; the five-minute collection takes it again from Drive MargArchive"
say "      undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s964.sh"
say ""
say "$KIT: DONE. Item names with an inch mark are read; the Stock Receive report of 26-Nov is taken again within five minutes."
exit 0
