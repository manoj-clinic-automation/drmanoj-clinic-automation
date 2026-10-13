#!/bin/bash
# =============================================================================
#  install_S541_NO_SPLIT_WORD.sh · kit S541 (session 313, 13-Oct-2026) · D718 · F-869
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S541_NO_SPLIT_WORD/install_S541_NO_SPLIT_WORD.sh
#
#  THE OWNER, 05:28-05:34 IST 13-Oct: "in the main place those payments were recorded as they were and the split payment
#  should totally disappear from any description" · "required mostly from October and if possible from September" ·
#  "clearly 600 is the consultation and the other is whatever entered in the patient bill whether it is x-ray or a procedure".
#   /root/finance/finance_clinic_day.py f6729d83 -> FCD_TO, clinic_day_pdf.py 150192e2 -> PDF_TO, packs.py 382081fa -> PK_TO,
#   and clinic_money.py b3ddc8d2 -> its new pin (widened at the owner's word 07:26 IST: "everywhere this part of split bill does
#   not come"), all four built HERE from the live bytes by make_s541.py (20 + 11 + 2 + 5 counted edits):
#   1  the day page, its month table and its PDF show every line as it was actually paid: the bill's parts matched to its
#      items (one to one; a group of items to one part; else one item in two parts, "Cash 400 + Online 400"); no parts ->
#      "mode not known", never guessed. The SPLIT PAYMENTS card, the Split column, the Split tender line are gone.
#      The day's total never moves; cash / online / card now include each bill's parts.
#   2  F-869: only a CONSULTATION line with a Razorpay number is portal money on the day page's bank card and MPR page.
#   3  the accountants' income sheet: the word 'split' out of its two lines (wording only).
#   4  the morning match (clinic_money.py): 'part of split bill' -> 'part of bill'; its two other 'split' sentences reworded;
#      F-869 in its own channel rule too. Nothing else in it changes.
#  Restarts clinic-finance. clinic_register.py is NOT touched. Read-only pages: no data step.
#  ORDER: gates -> pins (ALREADY first) -> compile -> rebuild from the live bytes -> walk (made-up + the old files red +
#  September/October on a copy of the database) -> DRY stops -> backups -> place -> restart -> health -> undo line.
# =============================================================================
set -u
KIT="S541_NO_SPLIT_WORD"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
NAMES="finance_clinic_day.py clinic_day_pdf.py packs.py clinic_money.py"
declare -A FROM TO
FROM[finance_clinic_day.py]=f6729d8345a3d77adacfecd4e33475b4; TO[finance_clinic_day.py]=2c539bad7878b81fd414f7595ad0efb7
FROM[clinic_day_pdf.py]=150192e227bbeb539e6df686e25ae2b2;     TO[clinic_day_pdf.py]=1534818bf2200594f3b3f11076ca4c18
FROM[packs.py]=382081fa886000065e648d63dc793ece;              TO[packs.py]=ada0860ad0b64e95836b24880927071f
FROM[clinic_money.py]=b3ddc8d2ac884b4d92058c588c3378b3;        TO[clinic_money.py]=b0408f82ec104e2170ccc069d0ec6450
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="/tmp/s541_inst_$STAMP"
HAVE_LOCK=0; PLACED=0

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S541_${FROM[$1]:0:8}"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; rm -rf "$SCR"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the four files back"
  for n in $NAMES; do [ -f "$(bak $n)" ] && \cp -p "$(bak $n)" "$FIN/$n"; done
  systemctl restart "$SVC" || true; sleep 3
  for n in $NAMES; do say "   $FIN/$n $(m5 "$FIN/$n") (expected ${FROM[$n]})"; done
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date systemctl curl timeout grep tail sleep; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
[ -x "$APY" ] || { say "!! preflight: $APY not executable - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES; do [ "$(m5 "$n")" = "${TO[$n]}" ] || { say "!! [1/8] the kit's $n is not its predicted md5 - nothing installed"; exit 1; }; done
mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
if [ "$HAVE_LOCK" != 1 ]; then
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Paste the line again when it is free."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
say "[1/8] kit gates green; the build lock is ours"

ALL_TO=1
for n in $NAMES; do [ -f "$FIN/$n" ] || { say "!! [2/8] $FIN/$n is not there - nothing installed"; exit 1; }; [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then say "-- ALREADY INSTALLED: all four files are the kit's. Nothing written."; exit 0; fi
for n in $NAMES; do C="$(m5 "$FIN/$n")"; [ "$C" = "${FROM[$n]}" ] || { say "!! [2/8] $FIN/$n is $C, expected ${FROM[$n]} - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [2/8] $DB is not there - nothing installed"; exit 1; }
say "[2/8] four live pins exact (finance_clinic_day f6729d83, clinic_day_pdf 150192e2, packs 382081fa, clinic_money b3ddc8d2)"

mkdir -p "$SCR/old" "$SCR/new" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONPYCACHEPREFIX="$SCR/pyc"; export PYTHONDONTWRITEBYTECODE=1
"$APY" -m py_compile finance_clinic_day.py clinic_day_pdf.py packs.py clinic_money.py walk_s541.py make_s541.py || { say "!! [3/8] compile failed - nothing installed"; exit 1; }
say "[3/8] py_compile green (6 files)"

"$APY" -B make_s541.py "$FIN/finance_clinic_day.py" "$SCR/new/finance_clinic_day.py" "$FIN/clinic_day_pdf.py" "$SCR/new/clinic_day_pdf.py" \
  "$FIN/packs.py" "$SCR/new/packs.py" "$FIN/clinic_money.py" "$SCR/new/clinic_money.py" >/dev/null || { say "!! [4/8] the builder refused a live file - nothing installed"; exit 1; }
for n in $NAMES; do
  [ "$(m5 "$SCR/new/$n")" = "${TO[$n]}" ] || { say "!! [4/8] rebuilt from the live bytes, $n is not the kit's - nothing installed"; exit 1; }
  \cp -p "$FIN/$n" "$SCR/old/$n"
done
say "[4/8] rebuilt from the live bytes: byte for byte the kit's four files"

"$APY" - "$DB" "$SCR/copy.db" <<'PYEOF' || { say "!! [5/8] could not take a copy of the database - nothing installed"; exit 1; }
import sqlite3, sys
src = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
dst = sqlite3.connect(sys.argv[2])
src.backup(dst)
dst.close(); src.close()
PYEOF
WOUT="$( cd /tmp && timeout 600 "$APY" -B "$KDIR/walk_s541.py" "$SCR/new" --db "$SCR/copy.db" --from 2026-09-01 2>&1 )"; WRC=$?
ROUT="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/walk_s541.py" "$SCR/old" --expect-red 2>&1 )"; RRC=$?
rm -f "$SCR/copy.db"
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK"; then
  say "!! [5/8] the walk is RED on this box (exit $WRC):"; echo "$WOUT" | tail -8; say "   nothing installed"; exit 1
fi
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK"; then
  say "!! [5/8] the negative control did not go red on the old files - the walk proves nothing; nothing installed"; exit 1
fi
say "[5/8] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "      negative control: $(echo "$ROUT" | grep "^WALK OK" | tail -1 | cut -c1-110)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

for n in $NAMES; do
  \cp -p "$FIN/$n" "$(bak $n)" || { say "!! [6/8] backup of $n failed - nothing placed"; exit 1; }
  [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ] || { say "!! [6/8] the backup of $n is not the live file - nothing placed"; exit 1; }
done
for n in $NAMES; do
  \cp -p "$SCR/new/$n" "$FIN/.$n.s541" || { rm -f "$FIN"/.*.s541; say "!! [6/8] could not stage $n - nothing placed"; exit 1; }
done
PLACED=1
for n in $NAMES; do mv -f "$FIN/.$n.s541" "$FIN/$n" || restore "placing $n"; done
for n in $NAMES; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || restore "$n did not land at its pin"; done
say "[6/8] backups beside all four files; the four files placed"

systemctl restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"); [ "$c1" = 200 ] && break; done
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/clinic/day")
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/clinic/day/2026-10-12/pdf")
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/clinic/match/2026-10-12")
systemctl is-active --quiet "$SVC" || restore "$SVC is not active"
ok2() { [ "$1" = 302 ] || [ "$1" = 401 ] || [ "$1" = 303 ] || [ "$1" = 403 ]; }
{ [ "$c1" = 200 ] && ok2 "$c2" && ok2 "$c3" && ok2 "$c4"; } || restore "finance health $c1 / day page $c2 / day PDF $c3 / morning match $c4"
MF="$(journalctl -u "$SVC" --since "-2 min" --no-pager 2>/dev/null | grep -E "(finance_clinic_day|clinic_day_pdf|packs|clinic_money) NOT mounted" | head -1)"
[ -z "$MF" ] || restore "a module did not mount: $MF"
say "[7/8] $SVC active - health $c1 - the day page $c2, its PDF $c3 and the morning match $c4 without a login (302 expected) - all four modules mounted"
PLACED=0
for n in $NAMES; do md5sum "$FIN/$n"; done
say "[8/8] $KIT: DONE"
say "read next: https://followup.dr-manoj.in/finance/clinic/day/2026-10-12"
say "undo: \\cp -p $(bak finance_clinic_day.py) $FIN/finance_clinic_day.py && \\cp -p $(bak clinic_day_pdf.py) $FIN/clinic_day_pdf.py && \\cp -p $(bak packs.py) $FIN/packs.py && \\cp -p $(bak clinic_money.py) $FIN/clinic_money.py && systemctl restart $SVC"
