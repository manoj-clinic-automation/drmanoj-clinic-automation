#!/bin/bash
# =============================================================================
#  install_m1a.sh · kit S187_M1a — B5, the pushed Marg export (D325).
#
#  WHAT THIS INSTALLS
#    /root/finance/finance_app.py                (81c26653...)  3 new routes
#    /root/finance/finance_ui/finance_workbench.html (420f82c2...)  the card
#    /root/deploy/live_pins.txt                  regenerated from Register v5.14
#  and, if not already configured, a FINANCE_MARG_TOKEN for the service.
#
#  THE GATE CHAIN (D317): SUMS -> KIT_ID -> currency gate on BOTH files ->
#  backup -> place -> LIVE SELFTEST (runs on a throwaway copy of the real
#  store; the store is never written) -> restart -> health check -> pin list.
#  A selftest failure RESTORES both files and does NOT restart: the running
#  service keeps executing the old, healthy code.
#
#  EXPECT: selftest ~375/375 on the live store (351 at S186 + 24 new), then
#  service active, then the pin check 42 match / 0 drift / 0 missing,
#  VERDICT AMBER (pending — Register v5.14's manifest row lands at the close).
#
#  Rehearsal: M1A_FIN=/tmp/t/finance M1A_DEPLOY=/tmp/t/deploy M1A_NOSVC=1 bash install_m1a.sh
# =============================================================================
set -u
KIT_NAME="S187_M1a"
FIN="${M1A_FIN:-/root/finance}"
DEP="${M1A_DEPLOY:-/root/deploy}"
NOSVC="${M1A_NOSVC:-0}"
PY=/usr/bin/python3
KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; cd "$KIT_DIR" || exit 1

OLD_APP="d04167a848e5d6f0baae19df014f70d4"; NEW_APP="81c26653cda7e4651fc737e4dea16599"
OLD_WB="18c71e63e5f1790c07d7fa3df53cd24e";  NEW_WB="420f82c2846bc49d0d12ab5040d8c542"

cur() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
gate_cur() {  # $1 path  $2 old  $3 new  $4 label
  C="$(cur "$1")"
  if [ "$C" = "$3" ]; then echo "-- $4: v-new already in place (idempotent re-run)";
  elif [ "$C" = "$2" ]; then echo "-- currency gate OK: $4 is the recorded live build";
  else echo "!! CURRENCY GATE RED: $4 is '$C' — neither the recorded live build nor this kit's."; \
       echo "   NOTHING was changed. Read the live file, fix the record first (D321(d))."; exit 1; fi
}

md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT_NAME" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum SUMS.md5 | awk '{print $1}')" ] \
&& echo "-- kit integrity OK" \
&& [ "$(cur finance_app_M1a.py)" = "$NEW_APP" ] \
&& [ "$(cur finance_workbench_M1a.html)" = "$NEW_WB" ] \
&& echo "-- payload hashes match the Register v5.14 pins" \
|| { echo "RED - kit integrity/payload gate failed. Nothing changed."; exit 1; }

gate_cur "$FIN/finance_app.py" "$OLD_APP" "$NEW_APP" "finance_app.py" || exit 1
gate_cur "$FIN/finance_ui/finance_workbench.html" "$OLD_WB" "$NEW_WB" "finance_workbench.html" || exit 1

cp -f "$FIN/finance_app.py" "$FIN/finance_app.py.bak_$KIT_NAME" \
&& cp -f "$FIN/finance_ui/finance_workbench.html" "$FIN/finance_ui/finance_workbench.html.bak_$KIT_NAME" \
&& echo "-- backups taken (*.bak_$KIT_NAME)" \
&& cp -f finance_app_M1a.py "$FIN/finance_app.py" \
&& cp -f finance_workbench_M1a.html "$FIN/finance_ui/finance_workbench.html" \
&& echo "-- files placed" \
|| { echo "RED - could not place files. Restore from *.bak_$KIT_NAME if partially copied."; exit 1; }

echo "-- live selftest (runs on a throwaway COPY; the store is never written)"
( cd "$FIN" && FINANCE_DB="$FIN/finance.db" "$PY" finance_app.py --selftest )
if [ $? -ne 0 ]; then
  echo "!! SELFTEST RED — restoring both files. The service was NOT restarted"
  echo "   and keeps running the old, healthy code. Send the output back."
  cp -f "$FIN/finance_app.py.bak_$KIT_NAME" "$FIN/finance_app.py"
  cp -f "$FIN/finance_ui/finance_workbench.html.bak_$KIT_NAME" "$FIN/finance_ui/finance_workbench.html"
  exit 1
fi
echo "-- selftest GREEN"

# ---- the sender token: created only if absent; never printed in full --------
if [ "$NOSVC" != "1" ]; then
  if ! systemctl cat clinic-finance 2>/dev/null | grep -q "FINANCE_MARG_TOKEN"; then
    TOK="$(openssl rand -hex 16)"
    mkdir -p /etc/systemd/system/clinic-finance.service.d
    printf '[Service]\nEnvironment=FINANCE_MARG_TOKEN=%s\n' "$TOK" \
      > /etc/systemd/system/clinic-finance.service.d/marg_token.conf
    chmod 600 /etc/systemd/system/clinic-finance.service.d/marg_token.conf
    { echo "FINANCE_MARG_TOKEN for the medical PC sender (kit $KIT_NAME)."
      echo "Token: $TOK"
      echo ""
      echo "Put this token into SEND_TO_CLINIC.bat on the MEDICAL PC"
      echo "(the TOKEN= line), then DELETE THIS FILE."
    } > "$DEP/MARG_TOKEN_S187.txt"
    chmod 600 "$DEP/MARG_TOKEN_S187.txt"
    systemctl daemon-reload
    echo "-- FINANCE_MARG_TOKEN created (ends ...${TOK: -4})."
    echo "   Full token written to $DEP/MARG_TOKEN_S187.txt — copy it into the"
    echo "   sender on the medical PC, then delete that file."
  else
    echo "-- FINANCE_MARG_TOKEN already configured; left untouched"
  fi
  systemctl restart clinic-finance \
    && sleep 2 \
    && HC="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8106/finance/api/whoami)" \
    && { [ "$HC" = "200" ] || [ "$HC" = "401" ]; } \
    && echo "-- service restarted and answering (HTTP $HC on whoami)" \
    || { echo "!! SERVICE HEALTH RED after restart — restoring and restarting the old build."; \
         cp -f "$FIN/finance_app.py.bak_$KIT_NAME" "$FIN/finance_app.py"; \
         cp -f "$FIN/finance_ui/finance_workbench.html.bak_$KIT_NAME" "$FIN/finance_ui/finance_workbench.html"; \
         systemctl restart clinic-finance; exit 1; }
else
  echo "-- rehearsal mode: service/token steps skipped"
fi

# ---- the pin list moves WITH the pins (record pins as they move) ------------
[ -f "$DEP/live_pins.txt" ] && cp -f "$DEP/live_pins.txt" "$DEP/live_pins.txt.bak_$KIT_NAME"
cp -f live_pins_M1a.txt "$DEP/live_pins.txt" \
&& echo "-- pin list updated (previous kept as live_pins.txt.bak_$KIT_NAME)"
if [ "$NOSVC" != "1" ]; then
  echo ""
  "$PY" "$DEP/verify_live_pins.py" --pins "$DEP/live_pins.txt"
  echo ""
  echo ">> EXPECTED: 42 match / 0 drift / 0 missing, VERDICT AMBER (pending)."
  echo ">> Then on the MEDICAL PC: copy SEND_TO_CLINIC.bat from this kit into a"
  echo ">> folder (e.g. Desktop\\SendToClinic\\), paste the token into its"
  echo ">> TOKEN= line, and reception double-clicks it after the morning report."
fi
exit 0
