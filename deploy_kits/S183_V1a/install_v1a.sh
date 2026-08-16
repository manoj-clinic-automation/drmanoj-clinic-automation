#!/bin/bash
# =============================================================================
#  install_v1a.sh · kit S183_V1a — the F-97 structural fix.
#
#  WHAT THIS INSTALLS
#     /root/deploy/verify_live_pins.py   the live-code pin checker (read-only)
#     /root/deploy/live_pins.tsv         the pins, generated from KB Register v5.4
#
#  WHAT IT DOES NOT TOUCH
#     Nothing live. Not one file under /root/portal, /root/wa, /root/finance,
#     /root/staff_register, /root/assetapp or /root/shared is read for anything
#     other than its md5, and none is written to. No service is restarted.
#     There is nothing here to roll back.
#
#  Shape per D317: preflight -> SUMS -> KIT_ID -> selftest gate BEFORE placing
#  anything -> place -> run the real check -> honest report.
#
#  ONE THING TO UNDERSTAND BEFORE YOU RUN IT
#  -----------------------------------------
#  The first real check may well come back RED. That is the tool working, not
#  the install failing. A RED verification is INFORMATION — it means the record
#  and the box disagree, which is the entire reason this exists. So the install
#  succeeds or fails on whether the TOOL is sound (its selftest) and got placed.
#  The verification result is printed afterwards and never rolls anything back.
#  If a genuine drift made the install look broken, the install would get
#  retried and the drift waved through — which is the failure mode this project
#  has already written down twice.
# =============================================================================
set -u

KIT_NAME="S183_V1a"
DEST=/root/deploy
PY=/usr/bin/python3

for c in md5sum awk cp mkdir; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — refusing before touching anything"; exit 1; }
done
[ -x "$PY" ] || { echo "!! preflight: $PY not executable — refusing before touching anything"; exit 1; }

KIT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$KIT_DIR" || exit 1

md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT_NAME" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum verify_live_pins.py | awk '{print $1}')" ] \
&& echo "-- kit integrity + currency OK" \
&& echo "" \
&& echo "-- GATE: proving the checker can actually fail, before it is trusted..." \
&& "$PY" verify_live_pins.py --selftest \
&& "$PY" -m py_compile verify_live_pins.py \
&& echo "" \
&& echo "-- gate green; placing the tool (nothing live is touched)" \
&& mkdir -p "$DEST" \
&& { [ -f "$DEST/verify_live_pins.py" ] && cp -f "$DEST/verify_live_pins.py" "$DEST/verify_live_pins.py.bak_$KIT_NAME" && echo "   (previous copy kept as verify_live_pins.py.bak_$KIT_NAME)" || true; } \
&& { [ -f "$DEST/live_pins.tsv" ] && cp -f "$DEST/live_pins.tsv" "$DEST/live_pins.tsv.bak_$KIT_NAME" || true; } \
&& cp -f verify_live_pins.py "$DEST/verify_live_pins.py" \
&& cp -f live_pins.tsv "$DEST/live_pins.tsv" \
&& chmod 0755 "$DEST/verify_live_pins.py" \
&& echo "" \
&& echo "=============================================================" \
&& echo " $KIT_NAME INSTALLED — tool placed, selftest green." \
&& echo " Nothing live was touched and no service was restarted." \
&& echo "=============================================================" \
&& echo "" \
&& echo "-- now running the FIRST REAL CHECK of this box against the record." \
&& echo "   Whatever it says below, the install above already succeeded." \
&& echo "" \
&& { "$PY" "$DEST/verify_live_pins.py" --pins "$DEST/live_pins.tsv"; RC=$?; \
     echo ""; \
     if [ $RC -eq 0 ]; then \
       echo ">> GREEN: the Register's live-code pins are TRUE of this box."; \
     elif [ $RC -eq 1 ]; then \
       echo ">> RED: the record and the box disagree — this is F-97, found."; \
       echo "   Send this output back. The Register gets corrected from the BOX,"; \
       echo "   never the other way round, and no kit is built on a drifted pin."; \
     else \
       echo ">> The checker could not run (setup problem, exit $RC)."; \
       echo "   The tool is placed; nothing was verified. Send this output back."; \
     fi; \
     echo ""; \
     echo "   From now on, run this at the start of every session:"; \
     echo ""; \
     echo "     python3 /root/deploy/verify_live_pins.py"; \
     echo ""; \
     exit 0; } \
|| { echo ""; \
     echo "RED — install did not complete."; \
     echo "   The gate fired before anything was placed, OR a copy failed."; \
     echo "   Nothing live was touched by this kit at any point — it does not"; \
     echo "   write to live files. Check the message above."; \
     exit 1; }
