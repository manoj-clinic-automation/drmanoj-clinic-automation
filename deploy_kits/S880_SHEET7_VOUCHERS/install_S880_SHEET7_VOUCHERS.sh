#!/bin/bash
# =============================================================================
#  install_S880_SHEET7_VOUCHERS.sh · kit S880 (the parent, S484, 18-Nov-2026) · his word of 17:23: sheet 7 must not repeat the card spends
#   /root/finance/packs.py FROM 68c7c79d -> TO
#     7 · a payment paper whose charge is a line of a card statement already read leaves sheet 7 for the workbook's own 'Paid by card'
#         sheet (the trace: the card, the line's date, the card sheet's month) and becomes the 'Receipt' column of that line in the
#         card sheet (4.4, 'Every line' + 2 columns; every paper of a charge, within Rs 1 as the split);
#         sheet 7 keeps only the payments on no card, each with 'Where the debit is' -- the bank statement line it matches (amount
#         within Rs 1, 7 days; withdrawals only), or 'card statements of this date not yet read', or 'receipt only'.
#     No figure of any other sheet changes; the page's row-7 label says it.
#   clinic-finance restarted.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s880kit && cp -rp /root/deploy/repo/deploy_kits/S880_SHEET7_VOUCHERS /tmp/s880kit && bash /tmp/s880kit/install_S880_SHEET7_VOUCHERS.sh
#  DRY=1 before bash: every gate, the walks and the shape on a copy of the live database; nothing live changes.
#  --undo: the file back.
# =============================================================================
set -u
KIT="S880_SHEET7_VOUCHERS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="packs.py"
from_of() { case "$1" in packs.py) echo 68c7c79d39ed3f123953e055abecf05c;; esac; }
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s880_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
isfrom() { [ "$(m5 "$FIN/$1")" = "$(from_of "$1")" ]; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S880_$(from_of "$1" | cut -c1-8)"; }
fget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fget /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES; do rm -f "$FIN/.$n.s880"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the files back"
  for n in $NAMES; do [ -f "$(bak "$n")" ] && \cp -p "$(bak "$n")" "$FIN/$n"; done
  "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do say "   $n $(m5 "$FIN/$n" | cut -c1-8) (expected $(from_of "$n" | cut -c1-8))"; done
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."; release_lock; exit 1; }
pya() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 300 "$APY" -W ignore -B "$@" 2>&1); }   # as the app runs (F-1444: no -s)

if [ "${1:-}" = "--undo" ]; then
  U=1; for n in $NAMES; do isfrom "$n" || U=0; done
  [ "$U" = 1 ] && { say "-- $KIT is not installed - nothing to undo."; exit 0; }
  for n in $NAMES; do isfrom "$n" || [ "$(m5 "$FIN/$n")" = "$(to_of "$n")" ] || { say "!! $FIN/$n is $(m5 "$FIN/$n" | cut -c1-8), not this kit's - nothing undone. Tell Claude."; exit 1; }; done
  for n in $NAMES; do isfrom "$n" && continue; b=$(bak "$n"); [ -f "$b" ] && [ "$(m5 "$b")" = "$(from_of "$n")" ] || { say "!! no good backup $b - nothing undone"; exit 1; }; done
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo" > "$LOCK/owner"
  for n in $NAMES; do isfrom "$n" || \cp -p "$(bak "$n")" "$FIN/$n"; done; "$SYSTEMCTL" restart "$FSVC"
  h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but finance healthz is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE (packs.py back; $FSVC restarted, finance healthz 200)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES; do [ "$(m5 "$KDIR/$n")" = "$(to_of "$n")" ] || { say "!! [1/5] the kit's $n is not as built - nothing installed"; exit 1; }; done
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
ALL=1; for n in $NAMES; do [ "$(m5 "$FIN/$n")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do isfrom "$n" || stop "!! [2/5] $FIN/$n is $(m5 "$FIN/$n" | cut -c1-8), expected $(from_of "$n" | cut -c1-8) - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/packs.py" || stop "!! [2/5] packs.py does not compile on $p - nothing installed"; done
mkdir -p "$SCR/built" && "$APY" -B "$KDIR/make_s880.py" "$FIN" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/5] the builder refused on the live file - nothing installed"; }
[ "$(m5 "$SCR/built/packs.py")" = "$(to_of packs.py)" ] || stop "!! [2/5] rebuilt from the live packs.py, not at the TO pin - nothing installed. Tell Claude."
say "[2/5] the live pin exact; rebuilt from the live bytes at the TO pin; packs.py compiles on both pythons"
{ mkdir -p "$SCR/fin_new" "$SCR/fin_old" && cp -p "$FIN"/*.py "$FIN"/*.html "$SCR/fin_new/" && cp -p "$FIN"/*.py "$FIN"/*.html "$SCR/fin_old/" && for n in $NAMES; do \cp -p "$KDIR/$n" "$SCR/fin_new/$n"; done; } || stop "!! [3/5] could not lay out the walks - nothing installed"
R1=$(pya "$KDIR/walk_s880.py" "$SCR/fin_new" "$SCR/w_new" | tail -1)
case "$R1" in "WALK 28/28") ;; *) pya "$KDIR/walk_s880.py" "$SCR/fin_new" "$SCR/w_new2" | grep -E "FAIL|Error" | head -6; stop "!! [3/5] walk_s880 (made-up) on the new file: $R1 - nothing installed";; esac
R1c=$(pya "$KDIR/walk_s880.py" "$SCR/fin_old" "$SCR/w_old" | tail -1)
case "$R1c" in "WALK 28/28") stop "!! [3/5] walk_s880's control (the live file) did not go red - nothing installed";; esac
R2=$(pya "$KDIR/walk_s877.py" "$SCR/fin_new" "$SCR/w877" | tail -1)
case "$R2" in "WALK 25/25") ;; *) stop "!! [3/5] S877's walk on the new file: $R2 - nothing installed";; esac
# S875's walk: its D5 (exactly two sheets) and D6 (the old column wording) assert what this kit changes on purpose -- those two alone may be red
O3=$(pya "$KDIR/walk_s875.py" "$SCR/fin_new" "$SCR/w875"); R3=$(printf '%s\n' "$O3" | tail -1); F3=$(printf '%s\n' "$O3" | grep '^FAIL' | grep -v '^FAIL D6 ' | grep -v '^FAIL D5 ' | head -3)
case "$R3" in "WALK 34/34"|"WALK 33/34"|"WALK 32/34") [ -z "$F3" ] || { printf '%s\n' "$F3"; stop "!! [3/5] S875's walk on the new file: $R3 with a red beyond D5/D6 - nothing installed"; };; *) stop "!! [3/5] S875's walk on the new file: $R3 - nothing installed";; esac
R4=$(pya "$KDIR/walk_s866.py" "$SCR/fin_new" "$SCR/w866" | tail -1)
case "$R4" in "WALK 18/18") ;; *) stop "!! [3/5] S866's walk on the new file: $R4 - nothing installed";; esac
R5=$(pya "$KDIR/walk_s873.py" "$SCR/fin_new" "$SCR/w873" | tail -1)
case "$R5" in "WALK 11/11") ;; *) stop "!! [3/5] S873's walk on the new file: $R5 - nothing installed";; esac
# the shape: last month's papers on a COPY of the live database -- every paper accounted for, the digest built (or every paper on a card)
pya -c "import sqlite3,sys;s=sqlite3.connect(sys.argv[1]);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close();s.close()" "$FIN/finance.db" "$SCR/shape.db" >/dev/null || stop "!! [3/5] could not copy the database for the shape check - nothing installed"
SH=$(pya "$KDIR/shape_s880.py" "$SCR/fin_new" "$SCR/shape.db" | tail -1)
case "$SH" in "SHAPE OK "*) ;; *) stop "!! [3/5] the shape check (last month): $SH - nothing installed. Tell Claude.";; esac
M2=$("$APY" -c "import datetime as d;t=d.date.today().replace(day=1)-d.timedelta(days=1);t=t.replace(day=1)-d.timedelta(days=1);print(t.strftime('%Y-%m'))")
SH2=$(pya "$KDIR/shape_s880.py" "$SCR/fin_new" "$SCR/shape.db" "$M2" | tail -1)
case "$SH2" in "SHAPE OK "*) ;; *) stop "!! [3/5] the shape check (the month before, whose card sheet builds): $SH2 - nothing installed. Tell Claude.";; esac
say "[3/5] walk_s880 $R1 (made-up; control red: $R1c); S877's walk $R2; S875's $R3 (D5/D6 are the old shape); S866's $R4; S873's $R5; last month on a copy of the live database: $SH; the month before: $SH2"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks and the shape green; nothing live changed"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$FIN/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
for n in $NAMES; do st="$FIN/.$n.s880"; { cat "$KDIR/$n" > "$st" && chmod --reference="$FIN/$n" "$st" 2>/dev/null; chown --reference="$FIN/$n" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
for n in packs.py; do mv -f "$FIN/.$n.s880" "$FIN/$n" || restore "the rename of $n"; done
for n in $NAMES; do [ "$(m5 "$FIN/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
pg=$(fget /finance/packs); case "$pg" in 200|302|303|401|403) ;; *) restore "the packs page answered $pg";; esac
release_lock
say "[4/5] placed and read back: packs.py at its TO pin; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the page answers $pg"
say "[5/5] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""; say "$KIT: DONE. Your page: https://followup.dr-manoj.in/finance/packs"; exit 0
