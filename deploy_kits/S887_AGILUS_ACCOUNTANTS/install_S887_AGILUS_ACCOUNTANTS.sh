#!/bin/bash
# =============================================================================
#  install_S887_AGILUS_ACCOUNTANTS.sh · kit S887 (the parent, S486, 18-Nov-2026) · his word 20:25-20:29: the Agilus figures
#  are the NET amount; the accountants get a running ledger of net amounts against the invoices only -- the ledger alone.
#   /root/finance/agilus_ledger.py    FROM 41412d2d -> TO   the accountants' rows; the paper's net from its TOTAL line when
#                                                           its header is not read; why a paper differs, in figures only
#   /root/finance/payment_ledgers.py  FROM d227bd74 -> TO   "For the accountants" on the Agilus page: an xlsx by month --
#                                                           date, Bill of Supply No., net amount, deposit (blank), running total
#   Then every paper is read again (counts only on screen).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s887kit && cp -rp /root/deploy/repo/deploy_kits/S887_AGILUS_ACCOUNTANTS /tmp/s887kit && bash /tmp/s887kit/install_S887_AGILUS_ACCOUNTANTS.sh
#  DRY=1 before bash: every gate and the walks; nothing live changes.   --undo: both files back.
# =============================================================================
set -u
KIT="S887_AGILUS_ACCOUNTANTS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="agilus_ledger.py payment_ledgers.py"
from_of() { case "$1" in agilus_ledger.py) echo 41412d2dafae130f211b1bee4209c689;; payment_ledgers.py) echo d227bd74bcd795f78b783c0465ae0d72;; esac; }
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s887_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S887_$(from_of "$1" | cut -c1-8)"; }
fget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fget /finance/healthz; }
jrn() { if [ -n "${JOURNAL_CMD:-}" ]; then $JOURNAL_CMD; elif command -v journalctl >/dev/null 2>&1; then journalctl -u "$FSVC" --since "@$1" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES; do rm -f "$FIN/.$n.s887"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
pya() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 300 "$APY" -W ignore -B "$@" 2>&1); }   # F-1444: no -s
restore() { say "!! RED after placing ($1) - putting both files back"
  for n in $NAMES; do [ -f "$(bak "$n")" ] && \cp -p "$(bak "$n")" "$FIN/$n"; done; "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do say "   $n $(m5 "$FIN/$n" | cut -c1-8) (expected $(from_of "$n" | cut -c1-8))"; done
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."; release_lock; exit 1; }

if [ "${1:-}" = "--undo" ]; then
  U=1; for n in $NAMES; do [ "$(m5 "$FIN/$n")" = "$(from_of "$n")" ] || U=0; done
  [ "$U" = 1 ] && { say "-- $KIT is not installed - nothing to undo."; exit 0; }
  for n in $NAMES; do [ "$(m5 "$FIN/$n")" = "$(from_of "$n")" ] || [ "$(m5 "$FIN/$n")" = "$(to_of "$n")" ] || { say "!! $FIN/$n is $(m5 "$FIN/$n" | cut -c1-8), not this kit's - nothing undone. Tell Claude."; exit 1; }; done
  for n in $NAMES; do [ "$(m5 "$FIN/$n")" = "$(from_of "$n")" ] && continue; b=$(bak "$n"); [ -f "$b" ] && [ "$(m5 "$b")" = "$(from_of "$n")" ] || { say "!! no good backup $b - nothing undone"; exit 1; }; done
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo" > "$LOCK/owner"
  for n in $NAMES; do [ "$(m5 "$FIN/$n")" = "$(from_of "$n")" ] || \cp -p "$(bak "$n")" "$FIN/$n"; done
  "$SYSTEMCTL" restart "$FSVC"; h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but finance healthz is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE (both files back; $FSVC restarted, finance healthz 200)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES; do [ "$(m5 "$KDIR/$n")" = "$(to_of "$n")" ] || { say "!! [1/5] the kit's $n is not as built - nothing installed"; exit 1; }; done
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
A=1; for n in $NAMES; do [ "$(m5 "$FIN/$n")" = "$(to_of "$n")" ] || A=0; done
[ "$A" = 1 ] && { say "-- $KIT is ALREADY INSTALLED."; "$VPY" -B "$FIN/agilus_ledger.py" status; exit 0; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do [ "$(m5 "$FIN/$n")" = "$(from_of "$n")" ] || stop "!! [2/5] $FIN/$n is $(m5 "$FIN/$n" | cut -c1-8), expected $(from_of "$n" | cut -c1-8) - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do for n in $NAMES; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/$n" || stop "!! [2/5] $n does not compile on $p - nothing installed"; done; done
(cd /tmp && "$APY" -c "import openpyxl") >/dev/null 2>&1 || stop "!! [2/5] the app's python has no openpyxl - nothing installed. Tell Claude."
say "[2/5] both files at their FROM pins; both compile on both pythons; openpyxl there"
mkdir -p "$SCR/new" "$SCR/live" "$SCR/reg"
\cp -p "$KDIR/agilus_ledger.py" "$KDIR/payment_ledgers.py" "$SCR/new/"; \cp -p "$FIN/agilus_ledger.py" "$FIN/payment_ledgers.py" "$SCR/live/"
R1=$(pya "$KDIR/walk_s887.py" "$SCR/new" "$SCR/w887" "$FIN" | tail -1)
case "$R1" in "WALK 44/44") ;; *) stop "!! [3/5] walk_s887 (made-up papers, the accountants' file) on the new files: $R1 - nothing installed";; esac
R1c=$(pya "$KDIR/walk_s887.py" "$SCR/live" "$SCR/w887c" "$FIN" | tail -1)
case "$R1c" in "WALK 44/44"|"") stop "!! [3/5] walk_s887's control (the live files) did not go red - nothing installed";; WALK\ *) ;; *) stop "!! [3/5] walk_s887's control ended oddly (${R1c:0:40}) - nothing installed";; esac
R2=$(pya "$KDIR/walk_s884.py" "$SCR/new" "$SCR/w884" "$FIN" | tail -1); R3=$(pya "$KDIR/walk_s885.py" "$SCR/new" "$SCR/w885" "$FIN" | tail -1); R4=$(pya "$KDIR/walk_s886.py" "$SCR/new" "$SCR/w886" "$FIN" | tail -1)
[ "$R2" = "WALK 28/28" ] && [ "$R3" = "WALK 31/31" ] && [ "$R4" = "WALK 34/34" ] || stop "!! [3/5] the earlier walks on the new files: S884 $R2, S885 $R3, S886 $R4 - nothing installed"
\cp -p "$FIN/payment_records.py" "$FIN/owner_console.py" "$KDIR/walk_s882.py" "$KDIR/payment_ledgers.py" "$KDIR/agilus_ledger.py" "$SCR/reg/"
R5=$(pya "$SCR/reg/walk_s882.py" "$SCR/reg" "$SCR/w882" | tail -1)
[ "$R5" = "WALK 54/54" ] || stop "!! [3/5] S882's walk on the new page: $R5 - nothing installed"
say "[3/5] walk_s887 $R1 (every role; the accountants' file carries no patient, no test); control (live files) red (${R1c:0:14}); S884 $R2, S885 $R3, S886 $R4, S882 $R5"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walks green; nothing live changed"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$FIN/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
for n in $NAMES; do st="$FIN/.$n.s887"; { cat "$KDIR/$n" > "$st" && chmod --reference="$FIN/$n" "$st" 2>/dev/null; chown --reference="$FIN/$n" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
for n in $NAMES; do mv -f "$FIN/.$n.s887" "$FIN/$n" || restore "the rename of $n"; done
for n in $NAMES; do [ "$(m5 "$FIN/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
for u in /finance/ledgers/healthz /finance/ledgers/agilus /finance/ledgers/agilus/accountants.xlsx; do pg=$(fget "$u"); case "$pg" in 200|302|401|403) ;; *) restore "$u answered $pg";; esac; done
jrn "$T0" | grep -q "payment_ledgers NOT mounted\|owner_console NOT mounted" && restore "the service log says: not mounted"
release_lock
say "[4/5] placed and read back: both files at their TO pins; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1"
say "      undo (one line): bash $KDIR/install_$KIT.sh --undo"
say "[5/5] every Agilus paper read again (counts only) ..."
BO=$(cd /tmp && TZ=Asia/Kolkata timeout 900 "$VPY" -W ignore -B "$FIN/agilus_ledger.py" build 2>&1 | tail -1); say "      $BO"; say ""
case "$BO" in "agilus_ledger S887"*) ;; *) say "$KIT: INSTALLED, but the reading did NOT finish (the line above). Tell Claude."; exit 0;; esac
say "$KIT: DONE. Your Agilus ledger (the accountants' file is at the top): https://followup.dr-manoj.in/finance/ledgers/agilus"; exit 0
