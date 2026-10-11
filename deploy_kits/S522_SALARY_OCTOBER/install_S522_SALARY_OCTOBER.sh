#!/bin/bash
# =============================================================================
#  install_S522_SALARY_OCTOBER.sh · kit S522_SALARY_OCTOBER (session 305, 11-Oct-2026) · D689 item 5
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S522_SALARY_OCTOBER/install_S522_SALARY_OCTOBER.sh
#
#  THE OWNER'S FOUR ITEMS BEFORE OCTOBER'S SALARY (07-Oct, D689 item 5; his word on a skipped month, 06-Oct:
#  "Should show in his related ledger everywhere"):
#   1  ONE BUTTON per person on the ledger's Advances page: skip a month on EVERY long-term loan of that person
#      at once, through the ledger's own DEFER (D332: DEFER replaces SKIP). Free twice a financial year, counted
#      in MONTHS -- one skipped month over two loans is one of the two; from the third month the loan with interest
#      carries the waivable Rs 1,000, as today. It reads "skipped" on Sheet 2's strip, his private loan page, his
#      slip and his ledger statement. The old per-loan "Skip (Rs 1000 capitalises)" button is no longer offered.
#   2  Sheet 4 prints a TOTAL row and its right border; Sheets 3 and 4 print rupees with thousands separators.
#   3  Sheet 3's dress / I-card footnote says what the settings charge.
#   4  The slip's line for a negative month says what is true: nothing carries it to next month (F-760).
#  FILES: /root/staff_ledger.py eacd7154 -> 32dfcfb9 · /root/staff_register/salary_policy.py ac603874 -> c3653896.
#  NOT TOUCHED: the ledger's data, any locked month, the settings, staff_register.py (its frozen-sheet reader
#  already strips separators -- the walk proves it), any cron line. Restarts staff-ledger and staff-register.
#
#  PROVEN BEFORE ANYTHING IS PLACED: kit SUMS + KIT_ID -> the build lock -> three live pins exact -> compile ->
#  THE WALK ON THIS BOX (walk_s522.py, on private copies of the ledger: every figure of every person the same in
#  both engines; Sheet 2 and the private page byte for byte; the lock's reader freezes the same Sheet 3; then a
#  skipped month and the close on a copy -- nothing collected on a skipped line, nobody else moved, the money the
#  same in both engines, the month shown as skipped everywhere). DRY=1 stops there and writes nothing.
#  Red after placing -> both old files back byte for byte, both services restarted. Pasted twice: says so.
#  No rupee figure is printed (F-31).
# =============================================================================
set -u
KIT="S522_SALARY_OCTOBER"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
SRD="$ROOT/staff_register"
POL="$SRD/salary_policy.py"
LEDM="$ROOT/staff_ledger.py"
SREG="$SRD/staff_register.py"
LEDD="${LEDGER_DIR:-$ROOT/staff_ledger}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
REG_PORT="${REG_PORT:-8044}"; LED_PORT="${LED_PORT:-8043}"
FROM_POL=ac603874431a43bed278f7db45d2c0f9; TO_POL=c36538963840a0258e0d25c6b950de4f
FROM_LED=eacd71544715ff597712aee5e6233135; TO_LED=32dfcfb9295c6ba9204a4d0d0c34daa9
PIN_SREG=0a098cfa315628e3db270602a831edd9
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="/tmp/s522_inst_$STAMP"
HAVE_LOCK=0; PLACED=0
BAK_POL="$POL.bak_S522_${FROM_POL:0:8}"; BAK_LED="$LEDM.bak_S522_${FROM_LED:0:8}"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; rm -rf "$SCR"; }
restore() {
  trap '' INT TERM HUP                                  # nothing interrupts the putting back
  say "!! RED after placing ($1) - putting both old files back byte for byte"
  [ -f "$BAK_POL" ] && \cp -p "$BAK_POL" "$POL"
  [ -f "$BAK_LED" ] && \cp -p "$BAK_LED" "$LEDM"
  systemctl restart staff-ledger || true; systemctl restart staff-register || true; sleep 3
  say "   $POL $(m5 "$POL")  (expected $FROM_POL)"
  say "   $LEDM $(m5 "$LEDM")  (expected $FROM_LED)"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date systemctl curl timeout grep tail sleep; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
[ -x "$VPY" ] || { say "!! preflight: $VPY not executable - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 salary_policy.py)" = "$TO_POL" ] && [ "$(m5 staff_ledger.py)" = "$TO_LED" ] \
  || { say "!! [1/8] the kit's two files are not their predicted md5 - nothing installed"; exit 1; }
mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
if [ "$HAVE_LOCK" != 1 ]; then
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Paste the line again when it is free."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
say "[1/8] kit gates green; the build lock is ours"

for f in "$POL" "$LEDM" "$SREG" "$LEDD/ledger.jsonl"; do
  [ -f "$f" ] || { say "!! [2/8] $f is not there - nothing installed"; exit 1; }
done
CP="$(m5 "$POL")"; CL="$(m5 "$LEDM")"
if [ "$CP" = "$TO_POL" ] && [ "$CL" = "$TO_LED" ]; then
  say "-- ALREADY INSTALLED: both files are the kit's. Nothing written."; md5sum "$POL" "$LEDM"; exit 0
fi
[ "$(m5 "$SREG")" = "$PIN_SREG" ] || { say "!! [2/8] $SREG is $(m5 "$SREG"), expected $PIN_SREG (the register whose frozen-sheet reader the walk proves) - nothing installed"; exit 1; }
[ "$CP" = "$FROM_POL" ] || { say "!! [2/8] $POL is $CP, expected $FROM_POL - nothing installed"; exit 1; }
[ "$CL" = "$FROM_LED" ] || { say "!! [2/8] $LEDM is $CL, expected $FROM_LED - nothing installed"; exit 1; }
say "[2/8] three live pins exact"

mkdir -p "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONPYCACHEPREFIX="$SCR/pyc"                 # compiled bytes go to /tmp, never into the deploy clone
export PYTHONDONTWRITEBYTECODE=1
"$VPY" -m py_compile salary_policy.py staff_ledger.py walk_s522.py || { say "!! [3/8] compile failed - nothing installed"; exit 1; }
say "[3/8] py_compile green (3 files)"

WOUT="$( cd /tmp && ROOT="$ROOT" LEDGER_DIR="$LEDD" S522_NEED_REGISTER=1 timeout 600 "$VPY" -B "$KDIR/walk_s522.py" "$KDIR" 2>&1 )"; WRC=$?
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK"; then
  say "!! [4/8] the walk is RED on this box (exit $WRC):"; echo "$WOUT" | tail -6; say "   nothing installed"; exit 1
fi
echo "$WOUT" | grep -E '^   20'
say "[4/8] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

\cp -p "$POL" "$BAK_POL" && \cp -p "$LEDM" "$BAK_LED" || { say "!! [5/8] backup failed - nothing placed"; exit 1; }
[ "$(m5 "$BAK_POL")" = "$FROM_POL" ] && [ "$(m5 "$BAK_LED")" = "$FROM_LED" ] || { say "!! [5/8] a backup is not the live file - nothing placed"; exit 1; }
say "[5/8] backups beside each file: $(basename "$BAK_POL") · $(basename "$BAK_LED")"

\cp -p salary_policy.py "$SRD/.salary_policy.py.s522" && \cp -p staff_ledger.py "$ROOT/.staff_ledger.py.s522" \
  || { rm -f "$SRD/.salary_policy.py.s522" "$ROOT/.staff_ledger.py.s522"; say "!! [6/8] could not stage the two files - nothing placed"; exit 1; }
PLACED=1
mv -f "$ROOT/.staff_ledger.py.s522" "$LEDM" || restore "placing staff_ledger.py"
mv -f "$SRD/.salary_policy.py.s522" "$POL" || restore "placing salary_policy.py"
[ "$(m5 "$LEDM")" = "$TO_LED" ] && [ "$(m5 "$POL")" = "$TO_POL" ] || restore "the files did not land at their pins"
say "[6/8] both files placed at their pins"

systemctl restart staff-ledger || restore "restart staff-ledger"
systemctl restart staff-register || restore "restart staff-register"
c1=000; c2=000; c3=000
for _try in 1 2 3 4 5 6 7 8 9 10; do                    # the apps need a few seconds; up to about 30
  sleep 3
  c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$REG_PORT/register/health")
  c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$LED_PORT/ledger/login")
  [ "$c1" = 200 ] && [ "$c2" = 200 ] && break
done
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$LED_PORT/ledger/advances")
systemctl is-active --quiet staff-ledger && systemctl is-active --quiet staff-register || restore "a service is not active"
say "[7/8] both services active · register health $c1 · ledger login $c2 · Advances without a login $c3 (302 expected)"
{ [ "$c1" = 200 ] && [ "$c2" = 200 ] && { [ "$c3" = 302 ] || [ "$c3" = 401 ]; }; } || restore "health $c1 / $c2 / $c3"

AOUT="$( cd /tmp && ROOT="$ROOT" timeout 120 "$VPY" -B -c "
import sys, importlib.util
def load(p, n):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m
L = load('$LEDM', 'sl_after'); P = load('$POL', 'sp_after')
assert hasattr(L, 'record_skip_month') and hasattr(L, 'skip_month_lines') and P.VERSION == '1.18-S522'
print('AFTER OK - the placed ledger has the one-button skip; the placed engine is', P.VERSION)
" 2>&1 )"; ARC=$?
if [ "$ARC" != 0 ] || ! echo "$AOUT" | grep -q "^AFTER OK"; then
  say "!! [8/8] the placed files do not read as they must (exit $ARC):"; echo "$AOUT" | tail -3; restore "after-check"
fi
PLACED=0
say "[8/8] $AOUT"
md5sum "$LEDM" "$POL"
say "$KIT: DONE"
say "read next: https://followup.dr-manoj.in/ledger/advances"
say "undo: \\cp -p $BAK_LED $LEDM && \\cp -p $BAK_POL $POL && systemctl restart staff-ledger staff-register"
