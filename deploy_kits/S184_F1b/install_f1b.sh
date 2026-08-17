#!/bin/bash
# =============================================================================
#  install_f1a.sh · kit S184_F1b — D322 missing-day classifier in finance_app.py
#
#  Sundays + attendance-sourced clinic holidays become OPTIONAL (kind
#  'clinic_holiday', low, not owed); genuine weekday gaps stay owed missing_day.
#  Cross-reads the attendance DB read-only, FAIL-SOFT to Sunday-only.
#
#  Proven S182 pattern + an F-97 CURRENCY GATE:
#   preflight -> SUMS -> KIT_ID -> currency gate (live == 86382f62) -> stage ->
#   stop -> backup -> swap -> py_compile -> --selftest on a copy of the REAL
#   store -> restart on green -> healthz -> HONEST red that restores + restarts.
#  No DB migration: recon_exception.kind is free text; the reclassification
#  happens self-healing on the next dashboard load.
# =============================================================================
set -u
for c in python3 systemctl curl md5sum awk cp mv; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — refusing"; exit 1; }
done
KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; LIVE=/root/finance
EXPECT_LIVE="86382f62907b65cf17fded2ee914328e"   # finance_app.py this kit was built against (F-97)
cd "$KIT_DIR" \
&& md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "S184_F1b" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum finance_app.py.new | awk '{print $1}')" ] \
&& echo "-- integrity + kit identity OK" \
&& LIVE_NOW="$(md5sum "$LIVE/finance_app.py" | awk '{print $1}')" \
&& { [ "$LIVE_NOW" = "$EXPECT_LIVE" ] || {
       echo "!! REFUSING — live finance_app.py is not the build this kit was made against (F-97)."
       echo "     live now : $LIVE_NOW"; echo "     expected : $EXPECT_LIVE"
       echo "   Send the current $LIVE/finance_app.py back and the kit is rebuilt on it."
       exit 1; }; } \
&& echo "-- currency gate OK (live finance_app.py = $LIVE_NOW)" \
&& cp finance_app.py.new "$LIVE/finance_app.py.new" \
&& cd "$LIVE" \
&& systemctl stop clinic-finance \
&& cp finance_app.py finance_app.py.bak_S184F1b \
&& cp finance.db finance.db.bak_S184F1b \
&& touch .S184F1b_touched \
&& mv finance_app.py.new finance_app.py \
&& python3 -m py_compile finance_app.py \
&& echo "-- swapped + compiles; running --selftest on a copy of the real store" \
&& python3 finance_app.py --selftest \
&& systemctl start clinic-finance \
&& sleep 2 && curl -sf http://127.0.0.1:8106/finance/healthz >/dev/null \
&& rm -f .S184F1b_touched \
&& echo "" \
&& echo "=============================================================" \
&& echo " S184_F1b INSTALLED — D322 missing-day classifier live" \
&& echo "   Sundays + clinic holidays -> optional (clinic_holiday, not owed)" \
&& echo "   weekday gaps -> still owed (missing_day)" \
&& echo "   attendance cross-read: fail-soft to Sunday-only" \
&& echo "   selftest green, service restarted, healthz OK" \
&& echo "   backups: finance_app.py.bak_S184F1b · finance.db.bak_S184F1b" \
&& echo "   The dashboard reclassifies the Sunday/holiday shouts on next load." \
&& echo "=============================================================" \
|| { echo ""; echo "RED — install did not complete."; \
     if [ -f "$LIVE/.S184F1b_touched" ]; then \
        echo "   live files WERE touched — restoring:"; \
        cp -f "$LIVE/finance_app.py.bak_S184F1b" "$LIVE/finance_app.py" && echo "   finance_app.py restored"; \
        cp -f "$LIVE/finance.db.bak_S184F1b" "$LIVE/finance.db" && echo "   finance.db restored"; \
        rm -f "$LIVE/.S184F1b_touched"; \
     else echo "   gate fired BEFORE anything live was touched — nothing to restore."; fi; \
     systemctl start clinic-finance; \
     echo "   the classifier is NOT installed"; exit 1; }
