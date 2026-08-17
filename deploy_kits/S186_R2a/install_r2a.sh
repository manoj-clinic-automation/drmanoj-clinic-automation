#!/bin/bash
# =============================================================================
#  install_r2a.sh · kit S186_R2a — the three surfaces.
#
#  REPLACES THE LIVE APP. Gated, backed up, selftested before the service comes
#  back, and it restores itself on any red.
#
#  WHAT ARRIVES
#    /finance/api/yesbank-statement   load a Yes Bank CSV; it reconciles at once
#    /finance/api/yesbank/reconcile   re-check any window without loading
#    /finance/workbench               Entered · Marg · Bank on one screen
#    /finance/api/workbench/<ym>      that month's data (checker only)
#    /finance/api/custody             who handed what to whom + month-end marker
#    /finance/api/cash-count          the drawer count; blank = UNKNOWN, flagged
#
#  WHAT DOES NOT CHANGE
#    Darpan's daily entry screen is NOT touched by this kit. Its Hindi labels
#    are not approved yet and the maker screen is the highest-traffic surface in
#    the system, so custody capture lives on the doctor's workbench for now.
#    The app diff is PURELY ADDITIVE: 0 lines removed, 239 added.
#
#  PROVEN BEFORE SHIPPING (the F-87 differential, on a seeded store)
#    unmodified live bytes : SMOKE 303/314
#    this build            : SMOKE 330/341   -> 27 checks added, ZERO failures added
# =============================================================================
set -u
for c in python3 systemctl curl md5sum awk cp mv; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — refusing"; exit 1; }
done
KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; LIVE=/root/finance
EXPECT_LIVE="c66bec2b9ea8c11af9c4a4244541e96f"   # verified FROM THE BOX at S186
cd "$KIT_DIR" \
&& md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "S186_R2a" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum finance_app.py.new | awk '{print $1}')" ] \
&& echo "-- integrity + kit identity OK" \
&& { [ -f "$LIVE/finance_yesbank.py" ] || {
       echo "!! REFUSING — finance_yesbank.py is not on the box. Install S186_R1a first."; exit 1; }; } \
&& echo "-- prerequisite OK (S186_R1a is installed)" \
&& LIVE_NOW="$(md5sum "$LIVE/finance_app.py" | awk '{print $1}')" \
&& { [ "$LIVE_NOW" = "$EXPECT_LIVE" ] || {
       echo "!! REFUSING — live finance_app.py is not the build this kit was made against (F-97)."
       echo "     live now : $LIVE_NOW"; echo "     expected : $EXPECT_LIVE"
       echo "   Send the current $LIVE/finance_app.py back and the kit is rebuilt on it."
       exit 1; }; } \
&& echo "-- currency gate OK (live finance_app.py = $LIVE_NOW)" \
&& cp finance_app.py.new "$LIVE/finance_app.py.new" \
&& cp finance_ui/finance_workbench.html "$LIVE/finance_ui/finance_workbench.html.new" \
&& cd "$LIVE" \
&& systemctl stop clinic-finance \
&& cp finance_app.py finance_app.py.bak_S186R2a \
&& cp finance.db finance.db.bak_S186R2a \
&& touch .S186R2a_touched \
&& mv finance_app.py.new finance_app.py \
&& mv finance_ui/finance_workbench.html.new finance_ui/finance_workbench.html \
&& python3 -m py_compile finance_app.py \
&& echo "-- swapped + compiles; running --selftest on a copy of the real store" \
&& python3 finance_app.py --selftest \
&& systemctl start clinic-finance \
&& sleep 2 && curl -sf http://127.0.0.1:8106/finance/healthz >/dev/null \
&& rm -f .S186R2a_touched \
&& echo "" \
&& echo "=============================================================" \
&& echo " S186_R2a INSTALLED — selftest green, service up, healthz OK" \
&& echo "" \
&& echo " Open:  https://followup.dr-manoj.in/finance/workbench" \
&& echo "" \
&& echo " First thing to do there: load today's Yes Bank CSV. It will" \
&& echo " reconcile every booked deposit against the statement and tell" \
&& echo " you, in one line, what the books claim that the bank did not." \
&& echo "" \
&& echo " backups: finance_app.py.bak_S186R2a · finance.db.bak_S186R2a" \
&& echo "=============================================================" \
|| { echo ""; echo "RED — install did not complete."; \
     if [ -f "$LIVE/.S186R2a_touched" ]; then \
        echo "   live files WERE touched — restoring:"; \
        cp -f "$LIVE/finance_app.py.bak_S186R2a" "$LIVE/finance_app.py" && echo "   finance_app.py restored"; \
        cp -f "$LIVE/finance.db.bak_S186R2a" "$LIVE/finance.db" && echo "   finance.db restored"; \
        rm -f "$LIVE/.S186R2a_touched"; \
     else echo "   gate fired BEFORE anything live was touched — nothing to restore."; fi; \
     systemctl start clinic-finance; \
     echo "   the three surfaces are NOT installed"; exit 1; }
