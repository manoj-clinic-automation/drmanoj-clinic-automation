#!/bin/bash
# =============================================================================
#  install_S884_AGILUS_LINES.sh · kit S884 (the parent, S486, 18-Nov-2026) · his word 18:48: the Agilus ledger with every
#  patient line -- name, date, test, amount
#   1. NEW /root/finance/agilus_ledger.py      reads every Agilus Bill of Supply on the server into agilus_invoice + agilus_line
#   2. /root/finance/payment_ledgers.py  FROM 5832bdad -> TO   the Agilus page shows every line, a search box, the check
#   3. cron: 35 2 * * * ... agilus_ledger.py build   # S884_AGILUS_LEDGER     then the first reading runs now (counts only).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s884kit && cp -rp /root/deploy/repo/deploy_kits/S884_AGILUS_LINES /tmp/s884kit && bash /tmp/s884kit/install_S884_AGILUS_LINES.sh
#  DRY=1 before bash: every gate and the walks; nothing live changes.   --undo: payment_ledgers.py back, the reader set aside,
#  the cron line out; the two tables are kept (nothing reads them then).
# =============================================================================
set -u
KIT="S884_AGILUS_LINES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
CRONTAB="${CRONTAB:-crontab}"; MARK="# S884_AGILUS_LEDGER"
OC="$FIN/payment_ledgers.py"; OC_FROM=5832bdad198e5f58cccb70f4c3621ce7
NEWF="agilus_ledger.py"
CRONLINE="35 2 * * * $VPY -B $FIN/agilus_ledger.py build >> $FIN/agilus_ledger.log 2>&1 $MARK"
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s884_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
OBAK="$OC.bak_S884_${OC_FROM:0:8}"
fget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fget /finance/healthz; }
jrn() { if [ -n "${JOURNAL_CMD:-}" ]; then $JOURNAL_CMD; elif command -v journalctl >/dev/null 2>&1; then journalctl -u "$FSVC" --since "@$1" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NEWF payment_ledgers.py; do rm -f "$FIN/.$n.s884"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
MIN_CRON="${MIN_CRON:-20}"
cron_has() { "$CRONTAB" -l 2>/dev/null | grep -qF "$MARK"; }
cron_read() { "$CRONTAB" -l > "$SCR/cron.cur" 2>/dev/null && [ "$(grep -c . "$SCR/cron.cur")" -ge "$MIN_CRON" ]; }
cron_drop() { cron_read || { say "!! the crontab could not be read whole - left as it is"; return 1; }
  grep -vF "$MARK" "$SCR/cron.cur" > "$SCR/cron.new"; [ "$(grep -c . "$SCR/cron.new")" -ge "$MIN_CRON" ] && "$CRONTAB" "$SCR/cron.new"; }
pya() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 300 "$APY" -W ignore -B "$@" 2>&1); }   # as the app runs (F-1444: no -s)
setaside() { for n in $NEWF; do [ -f "$FIN/$n" ] && mv -f "$FIN/$n" "$FIN/$n.undone_S884"; done; }
restore() { say "!! RED after placing ($1) - putting everything back"
  mkdir -p "$SCR"
  for _t in 1 2 3; do if cron_read; then grep -qF "$MARK" "$SCR/cron.cur" && cron_drop; break; fi; sleep "${NAP:-2}"; done
  [ -f "$OBAK" ] && \cp -p "$OBAK" "$OC"; setaside
  "$SYSTEMCTL" restart "$FSVC" || true
  say "   payment_ledgers.py $(m5 "$OC" | cut -c1-8) (expected ${OC_FROM:0:8}); agilus_ledger.py set aside; $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }

if [ "${1:-}" = "--undo" ]; then
  mkdir -p "$SCR"
  [ "$(m5 "$OC")" = "$OC_FROM" ] && ! cron_has && [ ! -f "$FIN/agilus_ledger.py" ] && { say "-- $KIT is not installed - nothing to undo."; exit 0; }
  [ "$(m5 "$OC")" = "$OC_FROM" ] || [ "$(m5 "$OC")" = "$(to_of payment_ledgers.py)" ] || { say "!! $OC is $(m5 "$OC" | cut -c1-8), not this kit's - a later change is on it: nothing undone. Tell Claude."; exit 1; }
  [ "$(m5 "$OC")" = "$OC_FROM" ] || { [ -f "$OBAK" ] && [ "$(m5 "$OBAK")" = "$OC_FROM" ]; } || { say "!! no good backup $OBAK - nothing undone"; exit 1; }
  for n in $NEWF; do [ ! -f "$FIN/$n" ] || [ "$(m5 "$FIN/$n")" = "$(to_of "$n")" ] || { say "!! $FIN/$n is $(m5 "$FIN/$n" | cut -c1-8), not this kit's - a later change is on it: nothing undone. Tell Claude."; exit 1; }; done
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
  cron_has && { cron_drop || { say "!! the cron line could not be removed - nothing undone. Run it again in a minute."; release_lock; exit 1; }; }
  [ "$(m5 "$OC")" = "$OC_FROM" ] || \cp -p "$OBAK" "$OC"
  setaside
  "$SYSTEMCTL" restart "$FSVC"; h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but finance healthz is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE (payment_ledgers.py back to S882's page, agilus_ledger.py set aside, no cron line; $FSVC restarted, finance healthz 200; the two tables kept)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $NEWF payment_ledgers.py; do [ "$(m5 "$KDIR/$f")" = "$(to_of "$f")" ] || { say "!! [1/5] the kit's $f is not as built - nothing installed"; exit 1; }; done
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "$(m5 "$OC")" = "$(to_of payment_ledgers.py)" ] && [ "$(m5 "$FIN/agilus_ledger.py")" = "$(to_of agilus_ledger.py)" ] && cron_has; then
  say "-- $KIT is ALREADY INSTALLED."; "$VPY" -B "$FIN/agilus_ledger.py" status; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$OC")" = "$OC_FROM" ] || stop "!! [2/5] $OC is $(m5 "$OC" | cut -c1-8), expected ${OC_FROM:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
for n in $NEWF; do [ -e "$FIN/$n" ] && stop "!! [2/5] $FIN/$n already exists and is not this kit's - STOP, nothing installed. Tell Claude."; done
cron_has && stop "!! [2/5] the crontab already holds a $MARK line - STOP, nothing installed. Tell Claude."
[ -f "$FIN/payment_records.py" ] || stop "!! [2/5] $FIN/payment_records.py (S882) is missing - nothing installed. Tell Claude."
command -v pdftotext >/dev/null || stop "!! [2/5] pdftotext is not on the server - nothing installed. Tell Claude."
for p in "$APY" "$VPY"; do for n in $NEWF payment_ledgers.py; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/$n" || stop "!! [2/5] $n does not compile on $p - nothing installed"; done; done
say "[2/5] payment_ledgers.py at its FROM pin (S882); no reader and no cron line yet; payment_records.py and pdftotext there; both compile on both pythons"
R1=$(pya "$KDIR/walk_s884.py" "$KDIR" "$SCR/w884" "$FIN" | tail -1)
case "$R1" in "WALK 28/28") ;; *) stop "!! [3/5] walk_s884 (made-up Agilus papers) on the new files: $R1 - nothing installed";; esac
mkdir -p "$SCR/live"; \cp -p "$OC" "$SCR/live/payment_ledgers.py"; \cp -p "$KDIR/agilus_ledger.py" "$SCR/live/"   # the new reader beside the live page: the page must go red
R1c=$(pya "$KDIR/walk_s884.py" "$SCR/live" "$SCR/w884c" "$FIN" | tail -1)
case "$R1c" in "WALK 28/28") stop "!! [3/5] walk_s884's control (the live files) did not go red - nothing installed";; esac
mkdir -p "$SCR/reg"; \cp -p "$FIN/payment_records.py" "$FIN/owner_console.py" "$KDIR/walk_s882.py" "$SCR/reg/"; \cp -p "$KDIR/payment_ledgers.py" "$KDIR/agilus_ledger.py" "$SCR/reg/"
R2=$(pya "$SCR/reg/walk_s882.py" "$SCR/reg" "$SCR/w882" | tail -1)
case "$R2" in "WALK 54/54") ;; *) stop "!! [3/5] S882's own walk on the new page: $R2 - nothing installed";; esac
say "[3/5] walk_s884 $R1 (made-up Agilus papers laid out as the real one; every role); control (the new reader + the live page) red (${R1c:0:14}); S882's walk on the new page, the reader present with no tables yet, $R2"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; nothing live changed"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
{ \cp -p "$OC" "$OBAK" && [ "$(m5 "$OBAK")" = "$OC_FROM" ]; } || stop "!! [4/5] could not write the backup of payment_ledgers.py - nothing placed"
for n in $NEWF payment_ledgers.py; do st="$FIN/.$n.s884"
  { cat "$KDIR/$n" > "$st" && chmod --reference="$OC" "$st" 2>/dev/null; chown --reference="$OC" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
for n in $NEWF payment_ledgers.py; do mv -f "$FIN/.$n.s884" "$FIN/$n" || restore "the rename of $n"; done
for n in $NEWF payment_ledgers.py; do [ "$(m5 "$FIN/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
cron_read || restore "the crontab could not be read whole (nothing written to it)"
{ cat "$SCR/cron.cur"; echo "$CRONLINE"; } > "$SCR/cron.new" && "$CRONTAB" "$SCR/cron.new" || restore "the cron line"
[ "$("$CRONTAB" -l 2>/dev/null | grep -c .)" -ge "$(( $(grep -c . "$SCR/cron.cur") + 1 ))" ] || restore "the crontab read back shorter than before"
[ "$("$CRONTAB" -l 2>/dev/null | grep -cF "$MARK")" = 1 ] || restore "the cron line read back"
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
lz=$(fget /finance/ledgers/healthz); case "$lz" in 200|302|401|403) ;; *) restore "the ledgers are not mounted (healthz $lz; 200 or a login answer means mounted, F-1439)";; esac
jrn "$T0" | grep -q "payment_ledgers NOT mounted\|owner_console NOT mounted" && restore "the service log says: not mounted"
for u in /finance/console /finance/ledgers /finance/ledgers/agilus /finance/ledgers/agilus/check /finance/ledgers/myoperator; do pg=$(fget "$u"); case "$pg" in 200|302|303|401|403) ;; *) restore "$u answered $pg";; esac; done
release_lock
say "[4/5] placed and read back: agilus_ledger.py + payment_ledgers.py at their TO pins; one cron line (02:35 nightly); $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the ledgers mounted"
say "      undo (one line): bash $KDIR/install_$KIT.sh --undo"
say "[5/5] the first reading of the Agilus papers on the server (counts only) ..."
BO=$(cd /tmp && TZ=Asia/Kolkata timeout 900 "$VPY" -W ignore -B "$FIN/agilus_ledger.py" build 2>&1 | tail -1)
say "      $BO"; say ""
case "$BO" in *"NOT OK"*|"") say "$KIT: INSTALLED, but the first reading did NOT finish (the line above). The page shows S882's list until tonight's 02:35 reading. Tell Claude."; exit 0;; esac
say "$KIT: DONE. Your Agilus ledger: https://followup.dr-manoj.in/finance/ledgers/agilus"; exit 0
