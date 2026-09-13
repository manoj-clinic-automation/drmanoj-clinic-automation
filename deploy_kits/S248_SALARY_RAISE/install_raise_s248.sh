#!/bin/bash
# =============================================================================
#  install_raise_s248.sh · kit S248_SALARY_RAISE
#
#  Run by:
#    bash /root/deploy/repo/deploy_kits/S248_SALARY_RAISE/install_raise_s248.sh
#
#  THE OWNER, 13-Sep-2026: "i need to increase sandeep salary , and awdhesh salary
#  ... i need to apply from august 2026 salary" — then: "awdhesh - increase by 500 /
#  sandeep - inrease by 600".
#
#      Awdhesh   Rs 10,000  ->  Rs 10,500
#      Sandip    Rs  7,400  ->  Rs  8,000
#
#  base_salary lives once per person in /root/staff_master.csv and carries no
#  effective-from date, so this is the whole change: two cells. August 2026 is NOT
#  locked, so the August pack recomputes with the new figures — which is exactly what
#  he asked for. July 2026 IS locked and its official total is stored, so nothing
#  already paid can move.
#
#  No code changes. No service file, no cron, no schema. One data file, two cells.
#  Gates: kit SUMS + KIT_ID -> the master exists and has the columns -> the kit's own
#  33-check walk ON THIS BOX -> a DRY RUN against the real master, printed -> backup
#  -> apply -> read back through the salary engine's own staff_bases() -> restart the
#  two services that read it. Any red: the master is restored from the backup.
# =============================================================================
set -u
KIT="S248_SALARY_RAISE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
MASTER="${STAFF_CSV:-/root/staff_master.csv}"
LEDGER_PY="${SL_LIVE:-/root/staff_ledger.py}"
PY="${PY:-/root/wa/venv/bin/python3}"
SVCS="${S248_SVCS:-staff-ledger.service staff-register.service}"

cd "$KDIR" || { echo "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp systemctl; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — nothing done"; exit 1; }
done
[ -x "$PY" ] || { echo "!! preflight: $PY not executable — nothing done"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/7] SUMS.md5 gate failed — kit corrupt, nothing done"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { echo "!! [1/7] KIT_ID names another kit — nothing done"; exit 1; }
echo "[1/7] kit gates green"

[ -f "$MASTER" ] || { echo "!! [2/7] $MASTER not found — nothing done"; exit 1; }
head -1 "$MASTER" | grep -q "base_salary" || { echo "!! [2/7] $MASTER has no base_salary column — nothing done"; exit 1; }
echo "[2/7] $MASTER present, md5 $(md5sum "$MASTER" | awk '{print $1}')"

OUT_W="$("$PY" -B walk_raise_s248.py raise_salary_s248.py "$LEDGER_PY" 2>&1)"
echo "$OUT_W" | grep -q "WALK GREEN" \
  || { echo "!! [3/7] the kit's own walk failed ON THIS BOX — nothing done"; echo "$OUT_W" | tail -12; exit 1; }
echo "[3/7] $(echo "$OUT_W" | grep -E '^== [0-9]+ checks' | tail -1)"

echo "[4/7] DRY RUN against the real staff master — nothing is written yet:"
"$PY" -B raise_salary_s248.py --dry "$MASTER" || { echo "!! [4/7] the dry run refused — nothing done"; exit 1; }

# read-only: who else on this box reads the staff master
echo "[5/7] files that read the staff master (read-only check):"
grep -rl "staff_master" /root --include="*.py" 2>/dev/null | grep -v "/deploy/repo/" | sed 's/^/        /' || true

BEFORE_MD5="$(md5sum "$MASTER" | awk '{print $1}')"
echo "[6/7] applying:"
"$PY" -B raise_salary_s248.py --apply "$MASTER" || { echo "!! [6/7] the raise refused — the master is untouched"; exit 1; }
AFTER_MD5="$(md5sum "$MASTER" | awk '{print $1}')"
[ "$BEFORE_MD5" != "$AFTER_MD5" ] || { echo "   (the master was already at these figures)"; }

BAK="$(ls -1t "${MASTER}".bak_S248_SALARY_RAISE_* 2>/dev/null | head -1)"
VERIFY="$("$PY" -B -c "
import sys, importlib.util
spec = importlib.util.spec_from_file_location('sl_v', '$LEDGER_PY')
sl = importlib.util.module_from_spec(spec); spec.loader.exec_module(sl)
sl.STAFF_CSV = '$MASTER'
b = sl.staff_bases()
bad = [n for n, v in (('Awdhesh', 10500.0), ('Sandip', 8000.0)) if b.get(n) != v]
print('BAD ' + ','.join(bad) if bad else 'OK %d staff, Awdhesh %g, Sandip %g' % (len(b), b['Awdhesh'], b['Sandip']))
" 2>&1)"
case "$VERIFY" in
  OK*) echo "[7/7] the salary engine now reads: $VERIFY" ;;
  *)   echo "!! [7/7] the salary engine does NOT read the new figures: $VERIFY"
       if [ -n "$BAK" ]; then cp -f "$BAK" "$MASTER"; echo "   the master has been put back from $BAK"; fi
       exit 1 ;;
esac

for s in $SVCS; do
  if systemctl list-unit-files 2>/dev/null | grep -q "^$s"; then
    systemctl restart "$s" && sleep 2
    if systemctl is-active --quiet "$s"; then echo "   restarted $s ✓"; else echo "   !! $s is NOT active after restart — check: systemctl status $s"; fi
  fi
done

echo
echo "=============================================================="
echo "  GREEN — the raise is in the staff master."
echo "    Awdhesh  Rs 10,000  ->  Rs 10,500"
echo "    Sandip   Rs  7,400  ->  Rs  8,000"
echo
echo "  SEE IT, then lock August:"
echo "    https://attendance.dr-manoj.in/register/salary?ym=2026-08"
echo
echo "  staff_master.csv: $BEFORE_MD5 -> $AFTER_MD5"
echo "  Reverse:  \\cp -f $BAK $MASTER"
echo "=============================================================="
