#!/bin/bash
# =============================================================================
#  install_i1a.sh · kit S186_I1a — the F-114 fix + Marg upload through the portal
#
#  REPLACES TWO LIVE MODULES. Gated on BOTH of their current md5s, backed up,
#  selftested before the service returns, self-restoring on any red.
#
#  1. finance_ingest.py — F-114. A line read cleanly but carrying neither a
#     clinic ID nor a name now attributes to WALK-IN instead of being parked in
#     a review queue with nothing in it a human could resolve. Low-confidence
#     lines still go to review; OCR is never treated as "cleanly anonymous".
#     Reversible without code: setting ingest.anonymous_to_walkin = 0.
#     Diff: ONE line replaced, 17 added.
#
#  2. finance_app.py + the workbench — upload a Marg export through the portal.
#     Parsed, surveyed, ingested and DELETED in one request; the file never
#     persists on this box. Keeps every guard the command-line driver has, and
#     adds the one it lacks: a day skipped as NOT FILED writes a data_flag
#     (F-113), because a console line does not survive the run.
#
#  PROVEN BEFORE SHIPPING (F-87 differential, seeded store)
#     unmodified live bytes : SMOKE 303/314
#     this build            : SMOKE 340/351   -> 37 added, ZERO failures added
# =============================================================================
set -u
for c in python3 systemctl curl md5sum awk cp mv; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — refusing"; exit 1; }
done
KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; LIVE=/root/finance
EXPECT_APP="31642789bc2863150e976b6acf9344bd"
EXPECT_ING="2cd0f264fb1a091f3e3ec7c3f4a17438"
cd "$KIT_DIR" \
&& md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "S186_I1a" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum finance_app.py.new | awk '{print $1}')" ] \
&& echo "-- integrity + kit identity OK" \
&& APP_NOW="$(md5sum "$LIVE/finance_app.py" | awk '{print $1}')" \
&& ING_NOW="$(md5sum "$LIVE/finance_ingest.py" | awk '{print $1}')" \
&& { [ "$APP_NOW" = "$EXPECT_APP" ] || { echo "!! live finance_app.py is $APP_NOW, expected $EXPECT_APP"; exit 1; }; } \
&& { [ "$ING_NOW" = "$EXPECT_ING" ] || { echo "!! live finance_ingest.py is $ING_NOW, expected $EXPECT_ING"; \
       echo "   Refusing — this kit was built on the other bytes (F-97)."; exit 1; }; } \
&& echo "-- currency gate OK (both modules are the builds this kit was made against)" \
&& cp finance_app.py.new     "$LIVE/finance_app.py.new" \
&& cp finance_ingest.py.new  "$LIVE/finance_ingest.py.new" \
&& cp finance_ui/finance_workbench.html "$LIVE/finance_ui/finance_workbench.html.new" \
&& cd "$LIVE" \
&& systemctl stop clinic-finance \
&& cp finance_app.py    finance_app.py.bak_S186I1a \
&& cp finance_ingest.py finance_ingest.py.bak_S186I1a \
&& cp finance.db        finance.db.bak_S186I1a \
&& touch .S186I1a_touched \
&& mv finance_app.py.new    finance_app.py \
&& mv finance_ingest.py.new finance_ingest.py \
&& mv finance_ui/finance_workbench.html.new finance_ui/finance_workbench.html \
&& python3 -m py_compile finance_app.py finance_ingest.py \
&& echo "-- swapped + compiles; running --selftest on a copy of the real store" \
&& python3 finance_app.py --selftest \
&& systemctl start clinic-finance \
&& sleep 2 && curl -sf http://127.0.0.1:8106/finance/healthz >/dev/null \
&& rm -f .S186I1a_touched \
&& echo "" \
&& echo "=============================================================" \
&& echo " S186_I1a INSTALLED — selftest green, service up, healthz OK" \
&& echo "" \
&& echo " Upload Marg exports here from now on — no scp, no file left" \
&& echo " on the server:" \
&& echo "   https://followup.dr-manoj.in/finance/workbench" \
&& echo "" \
&& echo " From this point a no-ID bill goes straight to WALK-IN, so the" \
&& echo " review queue stops refilling. Run S186_W1a next to clear the" \
&& echo " 2,072 legacy rows once and for all." \
&& echo "=============================================================" \
|| { echo ""; echo "RED — install did not complete."; \
     if [ -f "$LIVE/.S186I1a_touched" ]; then \
        echo "   live files WERE touched — restoring:"; \
        cp -f "$LIVE/finance_app.py.bak_S186I1a"    "$LIVE/finance_app.py"    && echo "   finance_app.py restored"; \
        cp -f "$LIVE/finance_ingest.py.bak_S186I1a" "$LIVE/finance_ingest.py" && echo "   finance_ingest.py restored"; \
        cp -f "$LIVE/finance.db.bak_S186I1a"        "$LIVE/finance.db"        && echo "   finance.db restored"; \
        rm -f "$LIVE/.S186I1a_touched"; \
     else echo "   gate fired BEFORE anything live was touched."; fi; \
     systemctl start clinic-finance; exit 1; }
