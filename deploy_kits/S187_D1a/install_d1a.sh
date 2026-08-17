#!/bin/bash
# =============================================================================
#  install_d1a.sh · kit S187_D1a — Daily Flow v2, stage D1 (D326).
#
#  Places: /root/finance/finance_app.py            (cd3faaa4...)
#          /root/finance/finance_ui/finance_approvals.html  (3798f9f7..., NEW)
#          /root/deploy/live_pins.txt              (Register v5.15, PENDING)
#
#  READ-ONLY STAGE: no schema change, no migration, no token, no data write.
#  The only writing route it touches is the EXISTING approve, reused as-is.
#
#  EXPECT: selftest ~387/387 live (375 at M1a + 12 new) -> service answering ->
#  pins 43 match / 0 drift / 0 missing, AMBER (pending until the close).
#  A selftest failure restores and does NOT restart (old code keeps running).
#
#  Rehearsal: D1A_FIN=/tmp/t/finance D1A_DEPLOY=/tmp/t/deploy D1A_NOSVC=1 bash install_d1a.sh
# =============================================================================
set -u
KIT_NAME="S187_D1a"
FIN="${D1A_FIN:-/root/finance}"
DEP="${D1A_DEPLOY:-/root/deploy}"
NOSVC="${D1A_NOSVC:-0}"
PY=/usr/bin/python3
KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; cd "$KIT_DIR" || exit 1

OLD_APP="81c26653cda7e4651fc737e4dea16599"; NEW_APP="cd3faaa4b30397f573d48bacf659bcf7"
NEW_PAGE="3798f9f7765b6c541582d61ff0731793"

cur() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }

md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT_NAME" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum SUMS.md5 | awk '{print $1}')" ] \
&& echo "-- kit integrity OK" \
&& [ "$(cur finance_app_D1a.py)" = "$NEW_APP" ] \
&& [ "$(cur finance_approvals.html)" = "$NEW_PAGE" ] \
&& echo "-- payload hashes match the Register v5.15 pins" \
|| { echo "RED - kit gate failed. Nothing changed."; exit 1; }

C="$(cur "$FIN/finance_app.py")"
if [ "$C" = "$NEW_APP" ]; then echo "-- app already at D1a (idempotent re-run)";
elif [ "$C" = "$OLD_APP" ]; then echo "-- currency gate OK: the box runs the M1a build ($OLD_APP)";
else echo "!! CURRENCY GATE RED: finance_app.py is '$C' — neither M1a nor D1a."; \
     echo "   NOTHING was changed. Read the live file, fix the record first (D321(d))."; exit 1; fi

P="$(cur "$FIN/finance_ui/finance_approvals.html")"
if [ -n "$P" ] && [ "$P" != "$NEW_PAGE" ]; then
  echo "!! CURRENCY GATE RED: an approvals page already exists with unexpected bytes ($P)."; exit 1; fi

cp -f "$FIN/finance_app.py" "$FIN/finance_app.py.bak_$KIT_NAME" \
&& echo "-- backup taken (finance_app.py.bak_$KIT_NAME)" \
&& cp -f finance_app_D1a.py "$FIN/finance_app.py" \
&& cp -f finance_approvals.html "$FIN/finance_ui/finance_approvals.html" \
&& echo "-- files placed" \
|| { echo "RED - could not place files."; exit 1; }

echo "-- live selftest (throwaway copy; the store is never written)"
( cd "$FIN" && FINANCE_DB="$FIN/finance.db" "$PY" finance_app.py --selftest )
if [ $? -ne 0 ]; then
  echo "!! SELFTEST RED — restoring. The service was NOT restarted."
  cp -f "$FIN/finance_app.py.bak_$KIT_NAME" "$FIN/finance_app.py"
  rm -f "$FIN/finance_ui/finance_approvals.html"
  exit 1
fi
echo "-- selftest GREEN"

if [ "$NOSVC" != "1" ]; then
  systemctl restart clinic-finance \
    && sleep 2 \
    && HC="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8106/finance/api/whoami)" \
    && { [ "$HC" = "200" ] || [ "$HC" = "401" ]; } \
    && echo "-- service restarted and answering (HTTP $HC)" \
    || { echo "!! SERVICE HEALTH RED — restoring and restarting the old build."; \
         cp -f "$FIN/finance_app.py.bak_$KIT_NAME" "$FIN/finance_app.py"; \
         rm -f "$FIN/finance_ui/finance_approvals.html"; \
         systemctl restart clinic-finance; exit 1; }
else
  echo "-- rehearsal mode: service step skipped"
fi

[ -f "$DEP/live_pins.txt" ] && cp -f "$DEP/live_pins.txt" "$DEP/live_pins.txt.bak_$KIT_NAME"
cp -f live_pins_D1a.txt "$DEP/live_pins.txt" \
&& echo "-- pin list updated (previous kept as live_pins.txt.bak_$KIT_NAME)"
if [ "$NOSVC" != "1" ]; then
  echo ""
  "$PY" "$DEP/verify_live_pins.py" --pins "$DEP/live_pins.txt"
  echo ""
  echo ">> EXPECTED: 43 match / 0 drift / 0 missing, VERDICT AMBER (pending)."
  echo ">> Your new page: https://followup.dr-manoj.in/finance/approvals"
fi
exit 0
