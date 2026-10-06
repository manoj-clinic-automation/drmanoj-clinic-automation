#!/bin/bash
# =============================================================================
#  install_S489_SALARY_LAYOUT.sh · kit S489_SALARY_LAYOUT (session 297, 06-Oct-2026) · D681, D682
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S489_SALARY_LAYOUT/install_S489_SALARY_LAYOUT.sh
#
#  THE OWNER'S RULINGS OF 06-OCT-2026, on three mock-ups ("All are good", "Plan looks good", "Come off", "go"):
#   D681  Sheet 2 shows advances in two tables that never mix -- this month's advances (cut in full from this
#         salary) and instalment loans, ONE LINE PER PERSON PER LOAN however many parts it was handed over in --
#         with one closing line per person. A salary slip is printed only for a person with a running loan.
#   D682  Darpan is back on the common salary sheet at his salary LESS the long-term loan's standing instalment;
#         late, absence, overtime and incentive are still worked on the full salary. The long-term loan lives
#         only on his private page -- one loan-ledger table from April 2026. A month the instalment is skipped
#         shows only there. And April 2026's flat Rs 1,000 comes off the loan.
#
#  WHAT IT DOES, in this order:
#   1  ONE ROW in the staff ledger, by restate_s489.py through staff_ledger.py's own append (dry run first; a dated
#      backup and a correction note beside the ledger; the tool proves on the rows themselves that the loan moved by
#      exactly Rs 1,000 and nothing else moved, and never writes its backup over the ledger).
#      Outside salary money: no salary, instalment, interest charge or locked month changes.
#   2  /root/staff_register/loan_pages.json  NEW  the two owner-ruled records the pages need (data_s489.py):
#      Surendra's three-part advance is one loan; which of Darpan's loan months before the ledger began
#      (Apr-Jun 2026) were skipped and which paid. It holds no balance and no salary.
#   3  /root/staff_register/salary_policy.py  92aecbe3 -> the kit's v1.17 (full file). DISPLAY ONLY: every rupee
#      is still the staff ledger's own.   full net == common-sheet net + what the private page pays him.
#   NOT TOUCHED: staff_register.py, staff_ledger.py, the settings, the hold ledger, any locked month, any cron
#   line, anything on manojz or the medical PC. Restarts staff-register once (a few seconds).
#
#  HOW IT IS PROVEN BEFORE ANYTHING IS WRITTEN: kit SUMS + KIT_ID -> the build lock -> three live pins exact ->
#  compile -> THE WALK ON THIS BOX (walk_s489.py: the LIVE engine and the kit's engine compute the same months
#  from this box's own data side by side, read-only; every figure of every person identical except Darpan's
#  shown figures, which must be what the ledger's own lines give when worked out in the walk; table 1 + table 2
#  = the Advance figure; the figures printed on the pages are those figures; the common pages never show the
#  private loan; the frozen Sheet 3 reads back through the register's own reader; then the restatement on a
#  SCRATCH COPY of the ledger: exactly Rs 1,000, nothing else moves, and the private loan page row by row is
#  what the ledger's raw rows give) -> the restatement's dry run on the real ledger.
#  Then the three writes above, the restart, health, and after_s489.py on the engine AS PLACED.
#  Red after the engine is placed -> the old engine is put back byte for byte, loan_pages.json set aside, the
#  service restarted. The ledger row then STAYS: it is the owner's ruling, has its own backup and note, and the
#  old engine reads it correctly too.
#  DRY=1 writes nothing (every gate, the walk and the dry run only). Pasted twice: the second run says so.
#  No rupee figure is printed (F-31).
# =============================================================================
set -u
KIT="S489_SALARY_LAYOUT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
SRD="$ROOT/staff_register"
DEST="$SRD/salary_policy.py"
LPJ="$SRD/loan_pages.json"
SREG="$SRD/staff_register.py"
LEDM="$ROOT/staff_ledger.py"
LEDD="${LEDGER_DIR:-$ROOT/staff_ledger}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FROM=92aecbe37d4272523c1cf6a4d8c8aced
TO=ac603874431a43bed278f7db45d2c0f9
PIN_LEDM=eacd71544715ff597712aee5e6233135
PIN_SREG=0a098cfa315628e3db270602a831edd9
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="/tmp/s489_inst_$STAMP"
HAVE_LOCK=0; PLACED=0; HAD_LPJ=0; BAK=""

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
clean() { rm -rf "$SCR"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; clean; }
restore() {
  trap '' INT TERM HUP                                  # nothing interrupts the putting back
  say "!! RED after placing ($1) - putting the old engine back byte for byte"
  \cp -p "$BAK" "$DEST"
  if [ "$HAD_LPJ" = 0 ] && [ -f "$LPJ" ]; then mv -f "$LPJ" "$LPJ.set_aside_S489_$STAMP"; fi
  systemctl restart staff-register || true; sleep 3
  say "   $DEST $(m5 "$DEST")  (expected $FROM)"
  say "   the staff ledger's restatement row STAYS - the owner's ruling, with its own backup and note; the old engine reads it too"
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
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/9] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/9] KIT_ID.txt names another kit - nothing installed"; exit 1; }
mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
if [ "$HAVE_LOCK" != 1 ]; then
  say "!! [1/9] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Paste the line again when it is free."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
say "[1/9] kit gates green; the build lock is ours"

for f in "$DEST" "$SREG" "$LEDM" "$LEDD/ledger.jsonl"; do
  [ -f "$f" ] || { say "!! [2/9] $f is not there - nothing installed"; exit 1; }
done
[ "$(m5 salary_policy.py)" = "$TO" ] || { say "!! [2/9] the kit's salary_policy.py is not its predicted md5 - nothing installed"; exit 1; }
[ "$(m5 "$LEDM")" = "$PIN_LEDM" ] || { say "!! [2/9] $LEDM is $(m5 "$LEDM"), expected $PIN_LEDM (the ledger module the restatement was proven on) - nothing installed"; exit 1; }
[ "$(m5 "$SREG")" = "$PIN_SREG" ] || { say "!! [2/9] $SREG is $(m5 "$SREG"), expected $PIN_SREG (the register whose frozen-sheet reader this kit was proven against) - nothing installed"; exit 1; }
CUR="$(m5 "$DEST")"
ENGINE_IN=0
if [ "$CUR" = "$TO" ]; then ENGINE_IN=1
elif [ "$CUR" != "$FROM" ]; then say "!! [2/9] $DEST is $CUR, expected $FROM (v1.16, S240) - nothing installed"; exit 1; fi
if [ "$ENGINE_IN" = 1 ]; then say "[2/9] the engine is ALREADY the kit's (v1.17); the ledger module and the register are at their pins"
else say "[2/9] three live pins exact; the kit engine at its predicted md5"; fi

mkdir -p "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONPYCACHEPREFIX="$SCR/pyc"                 # compiled bytes go to /tmp, never into the deploy clone
export PYTHONDONTWRITEBYTECODE=1
"$VPY" -m py_compile salary_policy.py walk_s489.py after_s489.py restate_s489.py data_s489.py \
  || { say "!! [3/9] compile failed - nothing installed"; exit 1; }
say "[3/9] py_compile green (5 files)"

if [ "$ENGINE_IN" = 0 ]; then
  WOUT="$( cd /tmp && ROOT="$ROOT" LEDGER_DIR="$LEDD" S489_NEED_REGISTER=1 timeout 280 "$VPY" -B "$KDIR/walk_s489.py" "$KDIR" 2>&1 )"; WRC=$?
  if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK"; then
    say "!! [4/9] the walk is RED on this box (exit $WRC):"; echo "$WOUT" | tail -6; say "   nothing installed"; exit 1
  fi
  echo "$WOUT" | grep -E '^   (20|[0-9]+ forward plan)'
  say "[4/9] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
else
  say "[4/9] the walk compares the old engine with the kit's; the kit's is already live - skipped"
fi

ROUT="$( cd /tmp && timeout 60 "$VPY" -B "$KDIR/restate_s489.py" --ledger "$LEDD" --module "$LEDM" --by manoj 2>&1 )"; RRC=$?
RSTATE=""
if [ "$RRC" = 0 ]; then
  echo "$ROUT" | grep -q "^-- ALREADY APPLIED" && RSTATE="done"
  echo "$ROUT" | grep -q "^RESTATE PLAN OK" && RSTATE="plan"
fi
[ -n "$RSTATE" ] || { say "!! [5/9] the restatement's dry run is RED on the real ledger:"; echo "$ROUT" | tail -4; say "   nothing installed"; exit 1; }
if [ "$RSTATE" = plan ]; then say "[5/9] the restatement's dry run on the real ledger: every precondition holds, one row to write"
else say "[5/9] the restatement row is already in the ledger - nothing to write there"; fi

if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the dry run green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi
if [ "$ENGINE_IN" = 1 ] && [ "$RSTATE" = done ] && "$VPY" -B "$KDIR/data_s489.py" --check "$LPJ" >/dev/null 2>&1; then
  say "-- ALREADY INSTALLED: the engine, the loan record and the ledger row are all in. Nothing written."
  md5sum "$DEST"; exit 0
fi

if [ "$RSTATE" = plan ]; then
  AOUT="$( cd /tmp && timeout 60 "$VPY" -B "$KDIR/restate_s489.py" --ledger "$LEDD" --module "$LEDM" --by manoj --apply 2>&1 )"; ARC=$?
  if [ "$ARC" != 0 ] || ! echo "$AOUT" | grep -q "^RESTATE APPLIED"; then
    say "!! [6/9] the restatement did not finish green (exit $ARC):"; echo "$AOUT" | tail -4
    say "   the engine is NOT placed. Read the lines above: they say whether the row is in the ledger. Paste the line again - it picks up from where the ledger stands."; exit 1
  fi
  echo "$AOUT" | grep -E '^   (written|backup|note)'
  say "[6/9] the staff ledger: one row written - April's Rs 1,000 is off the loan"
else
  say "[6/9] the staff ledger: nothing to write"
fi

[ -f "$LPJ" ] && HAD_LPJ=1
"$VPY" -B "$KDIR/data_s489.py" --write "$LPJ" || { say "!! [7/9] loan_pages.json could not be written - the engine is NOT placed"; exit 1; }
if [ "$ENGINE_IN" = 0 ]; then
  BAK="$DEST.bak_S489_${FROM:0:8}"
  \cp -p "$DEST" "$BAK" || { say "!! [7/9] backup failed - the engine is NOT placed"; exit 1; }
  [ "$(m5 "$BAK")" = "$FROM" ] || { say "!! [7/9] the backup is not the live file - the engine is NOT placed"; exit 1; }
  \cp -p salary_policy.py "$SRD/.salary_policy.py.s489" || { say "!! [7/9] could not stage the engine - NOT placed"; exit 1; }
  PLACED=1
  mv -f "$SRD/.salary_policy.py.s489" "$DEST" || restore "placing salary_policy.py"
  [ "$(m5 "$DEST")" = "$TO" ] || restore "the engine did not land at its pin"
  say "[7/9] loan_pages.json in place; the engine placed, backup $BAK"
else
  BAK="$DEST.bak_S489_${FROM:0:8}"
  # the kit's engine is already live: if the old engine's backup is still beside it, a red below puts that back
  if [ -f "$BAK" ] && [ "$(m5 "$BAK")" = "$FROM" ]; then PLACED=1; fi
  say "[7/9] loan_pages.json in place; the engine was already the kit's"
fi

systemctl restart staff-register || { [ "$PLACED" = 1 ] && restore "restart staff-register"; say "!! staff-register did not restart"; exit 1; }
c1=000; c2=000
for _try in 1 2 3 4 5 6 7 8 9 10; do                    # the app needs a few seconds; give it up to about 30
  sleep 3
  c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8044/register/health)
  [ "$c1" = 200 ] && break
done
systemctl is-active --quiet staff-register || { [ "$PLACED" = 1 ] && restore "staff-register not active"; say "!! staff-register is not active"; exit 1; }
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:8044/register/salary/flow/sheet2?ym=2026-09")
say "[8/9] staff-register active · health $c1 · Sheet 2 without a login $c2 (302 expected)"
if ! { [ "$c1" = 200 ] && { [ "$c2" = 302 ] || [ "$c2" = 401 ]; }; }; then
  [ "$PLACED" = 1 ] && restore "health $c1 / sheet2 $c2"; say "!! health is not green"; exit 1
fi

FOUT="$( cd /tmp && ROOT="$ROOT" LEDGER_DIR="$LEDD" timeout 200 "$VPY" -B "$KDIR/after_s489.py" 2>&1 )"; FRC=$?
if [ "$FRC" != 0 ] || ! echo "$FOUT" | grep -q "^AFTER OK"; then
  say "!! [9/9] the engine as placed does not read as it must (exit $FRC):"; echo "$FOUT" | tail -4
  [ "$PLACED" = 1 ] && restore "after_s489"
  say "!! the kit's engine is still live and the old engine's backup is not beside it - tell the assistant"; exit 1
fi
PLACED=0
say "[9/9] $(echo "$FOUT" | grep "^AFTER OK" | tail -1)"
md5sum "$DEST"
say "$KIT: DONE"
say "read next: https://followup.dr-manoj.in/register/salary/flow/sheet2?ym=2026-09"
say "then, to put September on the new sheets: unlock September on the lock desk and lock it again:"
say "           https://followup.dr-manoj.in/register/salary?ym=2026-09"
