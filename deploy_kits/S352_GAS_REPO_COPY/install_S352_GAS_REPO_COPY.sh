#!/bin/bash
# =============================================================================
#  install_S352_GAS_REPO_COPY.sh · kit S352_GAS_REPO_COPY (session 277, 20-Sep-2026) · F-591
#
#  gas_export.py's Sunday 02:20 run makes two comparisons; the second, "how stale is the copy people read",
#  reads the folder named by GAS_REPO_COPY= in /root/state_backup/clinic_state_backup.conf, falling back to
#  deploy_kits/S230_GAS_EXPORT -- the 07-Sep-2026 photograph, frozen (F-512) and now behind on two projects
#  (DailyClinicReports v6.1 at S348; UPIReconciliation gained VPS_Push_Lab.gs at S330 and VPS_Lab_Files.gs at
#  S333-S346). Its report goes only to gas_export.log.
#
#  THE CHANGE (data on the box; no code, no restart, no Google call):
#    ONE conf line  GAS_REPO_COPY=/root/deploy/repo/deploy_kits/GAS_CURRENT
#    GAS_CURRENT is the LIVING repository copy (READ_ME.md there), pulled by the same git pull as this kit.
#    Then `gas_export.py diff` -- READ-ONLY, no network -- prints what is STILL behind against the new folder.
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S352_GAS_REPO_COPY/install_S352_GAS_REPO_COPY.sh
#
#  The conf holds credentials: this script never prints it, only the one line it owns.
# =============================================================================
set -u
KIT="S352_GAS_REPO_COPY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
SB="$ROOT/state_backup"
CONF="${GAS_CONF:-$SB/clinic_state_backup.conf}"
REPO="${REPO_DIR:-$ROOT/deploy/repo}"
CUR="$REPO/deploy_kits/GAS_CURRENT"
GX="$SB/gas_export.py"
GX_PIN=072a941177fdf58f2c311aa164ea4e0d
LINE="GAS_REPO_COPY=$CUR"
STAMP="$(date +%Y%m%d_%H%M%S)"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - nothing changed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing changed"; exit 1; }
say "[1/6] kit gates green"
[ -f "$CONF" ] || { say "!! [2/6] no conf at $CONF - nothing changed"; exit 1; }
[ -f "$GX" ] || { say "!! [2/6] no gas_export.py at $GX - nothing changed"; exit 1; }
[ "$(m5 "$GX")" = "$GX_PIN" ] || { say "!! [2/6] gas_export.py is $(m5 "$GX"), not the S234 pin $GX_PIN - nothing changed"; exit 1; }
say "[2/6] conf present · gas_export.py at its pin"
[ -d "$CUR" ] || { say "!! [3/6] $CUR is not in the pulled repository - nothing changed"; exit 1; }
( cd "$CUR" && md5sum -c SUMS.md5 >/dev/null 2>&1 ) || { say "!! [3/6] GAS_CURRENT/SUMS.md5 does not verify - nothing changed"; exit 1; }
for p in ClinicAccountingReports DailyClinicReports UPIReconciliation; do
  [ -f "$CUR/$p/Code.gs" ] || { say "!! [3/6] $CUR/$p/Code.gs missing - nothing changed"; exit 1; }
done
say "[3/6] GAS_CURRENT present, sums green, three projects"
if grep -qx "$LINE" "$CONF"; then
  say "-- ALREADY INSTALLED (the conf already carries $LINE)."
else
  BAK="$CONF.bak_S352_$STAMP"
  \cp -p "$CONF" "$BAK" || { say "!! [4/6] backup failed - nothing changed"; exit 1; }
  chmod 600 "$BAK" 2>/dev/null
  if grep -q '^GAS_REPO_COPY=' "$CONF"; then
    OLD="$(grep '^GAS_REPO_COPY=' "$CONF" | head -1)"
    "$VPY" - "$CONF" "$LINE" <<'PY' || { say "!! [4/6] could not rewrite the line - restoring"; \cp -p "$BAK" "$CONF"; exit 1; }
import sys
p, line = sys.argv[1], sys.argv[2]
src = open(p, encoding="utf-8").read().split("\n")
out, done = [], False
for l in src:
    if l.startswith("GAS_REPO_COPY=") and not done:
        out.append(line); done = True
    elif l.startswith("GAS_REPO_COPY="):
        continue
    else:
        out.append(l)
open(p, "w", encoding="utf-8").write("\n".join(out))
PY
    say "[4/6] replaced: $OLD -> $LINE"
  else
    printf '\n# S352 (20-Sep-2026, F-591): the repository copy gas_export.py compares against -- the LIVING folder, not the frozen S230 photograph\n%s\n' "$LINE" >> "$CONF"
    say "[4/6] added: $LINE"
  fi
  N=$(grep -c '^GAS_REPO_COPY=' "$CONF")
  [ "$N" = "1" ] || { say "!! [4/6] expected exactly one GAS_REPO_COPY= line, found $N - restoring"; \cp -p "$BAK" "$CONF"; exit 1; }
  say "     backup $BAK (mode 600)"
fi
[ "$(grep '^GAS_REPO_COPY=' "$CONF")" = "$LINE" ] || { say "!! [5/6] the line did not read back"; exit 1; }
say "[5/6] the line reads back"
say "[6/6] gas_export.py diff -- READ-ONLY, no Google call: what is still behind against GAS_CURRENT"
GAS_CONF="$CONF" "$VPY" -B "$GX" diff 2>&1 | sed 's/^/     /' | grep -v 'no_copy' | head -40
say "$KIT: DONE -- next Sunday 02:20 the log compares against GAS_CURRENT"
