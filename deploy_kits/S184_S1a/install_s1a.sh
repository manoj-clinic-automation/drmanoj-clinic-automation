#!/bin/bash
# =============================================================================
#  install_s1a.sh · kit S184_S1a
#
#  ############################################################
#  #  THIS KIT INSTALLS NOTHING.                              #
#  #  It runs one READ-ONLY survey and prints the result.     #
#  #  No file is swapped. No migration runs. No service is    #
#  #  restarted. finance.db is opened mode=ro and the script  #
#  #  proves that by attempting a write and being refused.    #
#  ############################################################
#
#  It is named install_*.sh only because vps_deploy.sh globs that name. The
#  honest description is above, printed again at run time, and the script exits
#  without touching a single live file.
#
#  WHY THIS EXISTS
#    S184's top task is booking the 16 Yes Bank cash deposits. The written
#    record says the medical drawer closes at -Rs 30,056 and that the deposits
#    are simply unrecorded. But if the deposits were merely missing, the drawer
#    would be roughly +Rs 17 lakh, not negative -- so something ELSE is already
#    pulling the balance down, and the documents do not say what. Building a
#    money migration on a guess about that is exactly the mistake this project
#    keeps writing findings about. The box gets asked first (D321(d)).
# =============================================================================
set -u

KIT_NAME="S184_S1a"
FIN=/root/finance
PY=/usr/bin/python3

echo ""
echo "============================================================"
echo " $KIT_NAME — READ-ONLY SURVEY. NOTHING WILL BE INSTALLED."
echo "============================================================"
echo ""

for c in md5sum awk; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — refusing"; exit 1; }
done
[ -x "$PY" ]             || { echo "!! preflight: $PY not executable — refusing"; exit 1; }
[ -f "$FIN/finance.db" ] || { echo "!! preflight: $FIN/finance.db not found — refusing"; exit 1; }

KIT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$KIT_DIR" || exit 1

BEFORE="$(md5sum "$FIN/finance.db" | awk '{print $1}')"

md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT_NAME" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum survey_medical_cash.py | awk '{print $1}')" ] \
&& echo "-- integrity + kit identity OK" \
&& "$PY" -m py_compile survey_medical_cash.py \
&& echo "-- compiles; running the survey now" \
&& "$PY" survey_medical_cash.py \
&& AFTER="$(md5sum "$FIN/finance.db" | awk '{print $1}')" \
&& { [ "$BEFORE" = "$AFTER" ] || {
       echo ""
       echo "!! ALARM — finance.db CHANGED during a read-only survey."
       echo "     before : $BEFORE"
       echo "     after  : $AFTER"
       echo "   Stop and report this. It should be impossible."
       exit 1; }; } \
&& echo "" \
&& echo "============================================================" \
&& echo " SURVEY COMPLETE — finance.db byte-identical before and after" \
&& echo "   md5 $BEFORE" \
&& echo " Nothing was installed, swapped, migrated or restarted." \
&& echo " Copy ALL of the output above back into the session." \
&& echo "============================================================" \
|| { echo ""; echo "RED — the survey did not complete."; \
     echo "   Nothing live was touched: this kit never writes."; exit 1; }
