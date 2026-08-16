#!/bin/bash
# =============================================================================
#  install_m1a.sh · kit S182_M1a — the Marg fortnight backfill DRIVER.
#
#  This kit installs NO service and replaces NO live file. It places one
#  read-first script at /root/finance/ and stops. Nothing touches the database
#  until YOU run it, and even then not until you add --apply.
#
#  Shape: preflight -> SUMS -> KIT_ID -> place script -> print the two commands.
#  There is deliberately no restart and no gate-then-swap here, because nothing
#  live is being swapped. An installer should do what it says and no more.
# =============================================================================
set -u

KIT_NAME="S182_M1a"
LIVE=/root/finance
PY=/usr/bin/python3          # the finance app runs on system python3 (F-53)

for c in md5sum awk cp; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — refusing"; exit 1; }
done
[ -x "$PY" ] || { echo "!! preflight: $PY not executable — refusing"; exit 1; }
[ -d "$LIVE" ] || { echo "!! preflight: $LIVE not found — is this the VPS?"; exit 1; }
[ -f "$LIVE/marg_report.py" ] || { echo "!! preflight: $LIVE/marg_report.py missing — refusing"; exit 1; }
[ -f "$LIVE/finance_ingest.py" ] || { echo "!! preflight: $LIVE/finance_ingest.py missing — refusing"; exit 1; }
"$PY" -c "import xlrd" 2>/dev/null || { echo "!! preflight: xlrd not installed for $PY — refusing"; exit 1; }

KIT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$KIT_DIR" || exit 1

md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT_NAME" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum marg_backfill.py | awk '{print $1}')" ] \
&& "$PY" -m py_compile marg_backfill.py \
&& cp marg_backfill.py "$LIVE/marg_backfill.py" \
&& echo "" \
&& echo "$KIT_NAME PLACED — no service touched, no database touched." \
&& echo "" \
&& echo "  Put the Marg .xls on the box (WinSCP), then:" \
&& echo "" \
&& echo "  1) DRY RUN — writes nothing, tells you what it would do:" \
&& echo "       $PY $LIVE/marg_backfill.py /root/finance/incoming/MARG_1_15_AUG.XLS" \
&& echo "" \
&& echo "  2) Only if the dry run looks right:" \
&& echo "       $PY $LIVE/marg_backfill.py /root/finance/incoming/MARG_1_15_AUG.XLS --apply" \
&& echo "" \
&& echo "  It backs up finance.db before the first write, refuses any day you" \
&& echo "  have not filed, and aborts the whole run if the adapter reads fewer" \
&& echo "  rows than the export contains." \
|| { echo ""; echo "RED — kit did not install. Nothing was placed."; exit 1; }
