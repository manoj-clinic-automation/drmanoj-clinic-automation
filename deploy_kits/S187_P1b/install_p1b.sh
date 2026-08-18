#!/bin/bash
# =============================================================================
#  install_p1b.sh · kit S187_P1b — the Sanjeevni tile lands on the hub and
#  carries live pending counts. Touches TWO services, each with its own gate:
#
#    /root/portal/portal.py                     (34dbeef7...)  clinic-portal
#    /root/finance/finance_app.py               (65f19424...)  clinic-finance
#    /root/finance/finance_ui/finance_approvals.html (e37cb13b...)
#    /root/deploy/live_pins.txt                 (Register v5.16, PENDING)
#
#  ORDER: all gates first (kit SUMS, payload hashes, THREE currency gates,
#  the finance selftest AND the portal served-HTML gate against the LIVE
#  baseline) -> only then any swap. A red during finance restores finance and
#  stops BEFORE the portal is touched; a red during portal restores portal
#  (finance stays at P1a — additive-only, the old tile URL /finance/review
#  still works, so a half-window is safe by construction).
#
#  EXPECT: finance selftest ~389/389 · portal gate 18/18 · both services
#  answering · pins 43 / 0 / 0 AMBER (pending until the close).
#
#  Rehearsal: P1A_FIN=... P1A_PORTAL=... P1A_DEPLOY=... P1A_NOSVC=1 bash install_p1b.sh
# =============================================================================
set -u
KIT_NAME="S187_P1b"
FIN="${P1A_FIN:-/root/finance}"
POR="${P1A_PORTAL:-/root/portal}"
DEP="${P1A_DEPLOY:-/root/deploy}"
NOSVC="${P1A_NOSVC:-0}"
PY=/usr/bin/python3
KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; cd "$KIT_DIR" || exit 1

OLD_APP="cd3faaa4b30397f573d48bacf659bcf7"; NEW_APP="fe92a74dda3b374c813cab3c98ad2897"
OLD_PG="3798f9f7765b6c541582d61ff0731793";  NEW_PG="e37cb13b225316980b3566e8f6321120"
OLD_POR="2784b1cb76abfb9dbe2407c38da5bd83"; NEW_POR="34dbeef7292bc98752398a26c021a224"

cur() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
gate() { C="$(cur "$1")"; if [ "$C" = "$3" ]; then echo "-- $4 already at P1a (idempotent)";
  elif [ "$C" = "$2" ]; then echo "-- currency gate OK: $4 is the recorded live build";
  else echo "!! CURRENCY GATE RED: $4 is '$C'. NOTHING changed (D321(d))."; exit 1; fi; }

md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT_NAME" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum SUMS.md5 | awk '{print $1}')" ] \
&& echo "-- kit integrity OK" \
&& [ "$(cur finance_app_P1b.py)" = "$NEW_APP" ] \
&& [ "$(cur finance_approvals.html)" = "$NEW_PG" ] \
&& [ "$(cur portal_P1a.py)" = "$NEW_POR" ] \
&& echo "-- payload hashes match the Register v5.16 pins" \
|| { echo "RED - kit gate failed. Nothing changed."; exit 1; }

gate "$FIN/finance_app.py" "$OLD_APP" "$NEW_APP" "finance_app.py" || exit 1
gate "$FIN/finance_ui/finance_approvals.html" "$OLD_PG" "$NEW_PG" "finance_approvals.html" || exit 1
gate "$POR/portal.py" "$OLD_POR" "$NEW_POR" "portal.py" || exit 1

echo "-- portal served-HTML gate (candidate vs the LIVE portal, BEFORE any swap)"
"$PY" smoke_portal_P1a.py portal_P1a.py "$POR/portal.py" || { echo "RED - portal gate. Nothing changed."; exit 1; }

cp -f "$FIN/finance_app.py" "$FIN/finance_app.py.bak_$KIT_NAME"
cp -f "$FIN/finance_ui/finance_approvals.html" "$FIN/finance_ui/finance_approvals.html.bak_$KIT_NAME"
cp -f "$POR/portal.py" "$POR/portal.py.bak_$KIT_NAME"
echo "-- backups taken (*.bak_$KIT_NAME)"

# ---- finance first ----------------------------------------------------------
cp -f finance_app_P1b.py "$FIN/finance_app.py"
cp -f finance_approvals.html "$FIN/finance_ui/finance_approvals.html"
echo "-- finance files placed; live selftest (throwaway copy)"
( cd "$FIN" && FINANCE_DB="$FIN/finance.db" "$PY" finance_app.py --selftest )
if [ $? -ne 0 ]; then
  echo "!! FINANCE SELFTEST RED — restoring finance; PORTAL NOT TOUCHED."
  cp -f "$FIN/finance_app.py.bak_$KIT_NAME" "$FIN/finance_app.py"
  cp -f "$FIN/finance_ui/finance_approvals.html.bak_$KIT_NAME" "$FIN/finance_ui/finance_approvals.html"
  exit 1
fi
if [ "$NOSVC" != "1" ]; then
  systemctl restart clinic-finance && sleep 2 \
    && HC="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8106/finance/api/whoami)" \
    && { [ "$HC" = "200" ] || [ "$HC" = "401" ]; } \
    && echo "-- clinic-finance restarted and answering (HTTP $HC)" \
    || { echo "!! FINANCE HEALTH RED — restoring finance; PORTAL NOT TOUCHED."; \
         cp -f "$FIN/finance_app.py.bak_$KIT_NAME" "$FIN/finance_app.py"; \
         cp -f "$FIN/finance_ui/finance_approvals.html.bak_$KIT_NAME" "$FIN/finance_ui/finance_approvals.html"; \
         systemctl restart clinic-finance; exit 1; }
fi

# ---- portal second ----------------------------------------------------------
cp -f portal_P1a.py "$POR/portal.py"
echo "-- portal placed"
if [ "$NOSVC" != "1" ]; then
  systemctl restart clinic-portal && sleep 2 \
    && PC="$(curl -s -o /dev/null -w '%{http_code}' https://followup.dr-manoj.in/portal)" \
    && { [ "$PC" = "200" ] || [ "$PC" = "302" ]; } \
    && echo "-- clinic-portal restarted and answering (HTTP $PC)" \
    || { echo "!! PORTAL HEALTH RED — restoring portal (finance stays at P1a, safe: additive)."; \
         cp -f "$POR/portal.py.bak_$KIT_NAME" "$POR/portal.py"; \
         systemctl restart clinic-portal; exit 1; }
fi

[ -f "$DEP/live_pins.txt" ] && cp -f "$DEP/live_pins.txt" "$DEP/live_pins.txt.bak_$KIT_NAME"
cp -f live_pins_P1b.txt "$DEP/live_pins.txt" && echo "-- pin list updated"
if [ "$NOSVC" != "1" ]; then
  echo ""; "$PY" "$DEP/verify_live_pins.py" --pins "$DEP/live_pins.txt"; echo ""
  echo ">> EXPECTED: 43 match / 0 drift / 0 missing, AMBER (pending)."
  echo ">> Open the portal: the Sanjeevni tile now shows live counts and lands"
  echo ">> on /finance/approvals — the Marg reports are one visible click away."
fi
exit 0
