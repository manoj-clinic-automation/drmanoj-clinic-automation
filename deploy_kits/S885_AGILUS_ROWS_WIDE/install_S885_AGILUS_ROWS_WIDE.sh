#!/bin/bash
# =============================================================================
#  install_S885_AGILUS_ROWS_WIDE.sh · kit S885 (the parent, S486, 18-Nov-2026) · S884 read 83 Agilus papers but 0 lines:
#  the real rows run past the rate (more columns after it). One file:
#   /root/finance/agilus_ledger.py  FROM 5395d324 -> TO   rows read by their columns whatever follows the test; the amount
#   is the column that adds up to the paper (the rate, or the line's last figure); the check carries row shapes (classes only).
#   Then every paper is read again (counts only on screen). S884's cron line (02:35) stays as it is.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s885kit && cp -rp /root/deploy/repo/deploy_kits/S885_AGILUS_ROWS_WIDE /tmp/s885kit && bash /tmp/s885kit/install_S885_AGILUS_ROWS_WIDE.sh
#  DRY=1 before bash: every gate and the walks; nothing live changes.   --undo: S884's reader back.
# =============================================================================
set -u
KIT="S885_AGILUS_ROWS_WIDE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
F="$FIN/agilus_ledger.py"; FROM=5395d324bf9142382924c292e5d19935
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
TO="$(to_of agilus_ledger.py)"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s885_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
BAK="$F.bak_S885_${FROM:0:8}"
fget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fget /finance/healthz; }
jrn() { if [ -n "${JOURNAL_CMD:-}" ]; then $JOURNAL_CMD; elif command -v journalctl >/dev/null 2>&1; then journalctl -u "$FSVC" --since "@$1" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$FIN/.agilus_ledger.py.s885"; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
pya() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 300 "$APY" -W ignore -B "$@" 2>&1); }   # F-1444: no -s
reread() { (cd /tmp && TZ=Asia/Kolkata timeout 900 "$VPY" -W ignore -B "$F" build 2>&1 | tail -1); }
restore() { say "!! RED after placing ($1) - putting S884's reader back"
  [ -f "$BAK" ] && \cp -p "$BAK" "$F"; "$SYSTEMCTL" restart "$FSVC" || true
  say "   agilus_ledger.py $(m5 "$F" | cut -c1-8) (expected ${FROM:0:8}); $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }

if [ "${1:-}" = "--undo" ]; then
  [ "$(m5 "$F")" = "$FROM" ] && { say "-- $KIT is not installed - nothing to undo."; exit 0; }
  [ "$(m5 "$F")" = "$TO" ] || { say "!! $F is $(m5 "$F" | cut -c1-8), not this kit's - nothing undone. Tell Claude."; exit 1; }
  [ -f "$BAK" ] && [ "$(m5 "$BAK")" = "$FROM" ] || { say "!! no good backup $BAK - nothing undone"; exit 1; }
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo" > "$LOCK/owner"
  \cp -p "$BAK" "$F"; "$SYSTEMCTL" restart "$FSVC"; h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but finance healthz is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE (S884's reader back; $FSVC restarted, finance healthz 200; the tables are re-read by it tonight at 02:35)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 "$KDIR/agilus_ledger.py")" = "$TO" ] || { say "!! [1/5] the kit's agilus_ledger.py is not as built - nothing installed"; exit 1; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "$(m5 "$F")" = "$TO" ]; then say "-- $KIT is ALREADY INSTALLED."; "$VPY" -B "$F" status; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$F")" = "$FROM" ] || stop "!! [2/5] $F is $(m5 "$F" | cut -c1-8), expected ${FROM:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/agilus_ledger.py" || stop "!! [2/5] agilus_ledger.py does not compile on $p - nothing installed"; done
say "[2/5] agilus_ledger.py at its FROM pin (S884); the new one compiles on both pythons"
mkdir -p "$SCR/new" "$SCR/live"
\cp -p "$KDIR/agilus_ledger.py" "$FIN/payment_ledgers.py" "$SCR/new/"; \cp -p "$F" "$FIN/payment_ledgers.py" "$SCR/live/"
R1=$(pya "$KDIR/walk_s885.py" "$SCR/new" "$SCR/w885" "$FIN" | tail -1)
case "$R1" in "WALK 31/31") ;; *) stop "!! [3/5] walk_s885 (made-up papers, rows wider than the rate) on the new reader: $R1 - nothing installed";; esac
R1c=$(pya "$KDIR/walk_s885.py" "$SCR/live" "$SCR/w885c" "$FIN" | tail -1)
case "$R1c" in "WALK 31/31"|"") stop "!! [3/5] walk_s885's control (S884's reader) did not go red - nothing installed";; WALK\ [0-9]*/31) ;; *) stop "!! [3/5] walk_s885's control ended oddly (${R1c:0:40}) - nothing installed";; esac
R2=$(pya "$KDIR/walk_s884.py" "$SCR/new" "$SCR/w884" "$FIN" | tail -1)
case "$R2" in "WALK 28/28") ;; *) stop "!! [3/5] S884's walk on the new reader: $R2 - nothing installed";; esac
say "[3/5] walk_s885 $R1 (made-up papers, rows wider than the rate, every role); control (S884's reader) red (${R1c:0:14}); S884's walk on the new reader $R2"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walks green; nothing live changed"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
{ \cp -p "$F" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop "!! [4/5] could not write the backup - nothing placed"
st="$FIN/.agilus_ledger.py.s885"
{ cat "$KDIR/agilus_ledger.py" > "$st" && chmod --reference="$F" "$st" 2>/dev/null; chown --reference="$F" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$TO" ]; } || stop "!! [4/5] could not stage agilus_ledger.py - nothing placed"
mv -f "$st" "$F" || restore "the rename"
[ "$(m5 "$F")" = "$TO" ] || restore "read back"
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
lz=$(fget /finance/ledgers/agilus/check); case "$lz" in 200|302|401|403) ;; *) restore "the Agilus check answered $lz";; esac
jrn "$T0" | grep -q "payment_ledgers NOT mounted\|owner_console NOT mounted" && restore "the service log says: not mounted"
release_lock
say "[4/5] placed and read back: agilus_ledger.py at its TO pin; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1"
say "      undo (one line): bash $KDIR/install_$KIT.sh --undo"
say "[5/5] every Agilus paper read again (counts only) ..."
BO=$(reread); say "      $BO"; say ""
case "$BO" in "agilus_ledger S885"*) ;; *) say "$KIT: INSTALLED, but the reading did NOT finish (the line above). Tell Claude."; exit 0;; esac
say "$KIT: DONE. Your Agilus ledger: https://followup.dr-manoj.in/finance/ledgers/agilus"; exit 0
