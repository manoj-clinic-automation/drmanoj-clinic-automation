#!/bin/bash
# =============================================================================
#  install_v1b.sh · kit S186_V1b — the regenerated pin list.
#
#  No code changes. It places one file: /root/deploy/live_pins.txt, regenerated
#  from KB Register v5.11 with FULL manifest verification, so the header now
#  reads `register_pin_verified: yes` instead of `pending`.
#
#  After this, verify_live_pins.py should read GREEN rather than AMBER, and the
#  four pins that moved during S186 (finance_app, finance_ingest, the new
#  finance_yesbank module and the workbench page) are the ones it holds the box
#  to. This is the step that closes F-110 in practice.
# =============================================================================
set -u
KIT_NAME="S186_V1b"; DEST=/root/deploy; PY=/usr/bin/python3
KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; cd "$KIT_DIR" || exit 1
md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT_NAME" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum live_pins.txt | awk '{print $1}')" ] \
&& echo "-- kit integrity OK" \
&& grep -q '^# register_pin_verified: yes' live_pins.txt \
&& echo "-- the list is manifest-verified (register_pin_verified: yes)" \
&& { [ -f "$DEST/live_pins.txt" ] && cp -f "$DEST/live_pins.txt" "$DEST/live_pins.txt.bak_$KIT_NAME" \
     && echo "   previous list kept as live_pins.txt.bak_$KIT_NAME" || true; } \
&& cp -f live_pins.txt "$DEST/live_pins.txt" \
&& echo "" \
&& echo "-- running the check with the new list" \
&& { "$PY" "$DEST/verify_live_pins.py"; RC=$?; \
     echo ""; \
     if [ $RC -eq 0 ]; then echo ">> GREEN — the record and the box agree, and the list is manifest-verified."; \
     else echo ">> exit $RC — send this output back."; fi; \
     exit 0; } \
|| { echo ""; echo "RED — the list was not placed. Check the message above."; exit 1; }
