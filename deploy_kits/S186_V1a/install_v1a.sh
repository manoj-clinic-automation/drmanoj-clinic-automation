#!/bin/bash
# =============================================================================
#  install_v1a.sh · kit S186_V1a — the F-110 + F-111 fixes.
#
#  WHAT THIS INSTALLS
#     /root/deploy/verify_live_pins.py   checker v1.0 -> v1.1
#     /root/deploy/gen_live_pins.py      generator v1.0 -> v1.1 (reference copy)
#     /root/deploy/live_pins.txt         regenerated from KB Register v5.7
#
#  WHAT IT DOES NOT TOUCH
#     Nothing live. Not one file under /root/portal, /root/wa, /root/finance,
#     /root/staff_register, /root/assetapp or /root/shared is read for anything
#     other than its md5, and none is written to. No service is restarted.
#
#  WHY THIS KIT EXISTS
#     The pin list on this box was generated at S183 from an intermediate DRAFT
#     of Register v5.5 (`ff509b01...`) that never became canonical. It carried
#     pre-S183 values for two Marg files, so the S186 opening check reported
#     three DRIFT reds of which TWO WERE FALSE — the canonical Register already
#     agreed with the box. The list declared its own source md5 in its header
#     every single run for three sessions, and nothing ever compared it to the
#     manifest (F-110). Reporting is not enforcing.
#
#  EXPECT AMBER, NOT GREEN, ON THE FIRST RUN
#     The new list is built from Register v5.7, which is authored THIS session
#     and whose manifest row does not exist until the S186 close. So the list is
#     honestly stamped `register_pin_verified: pending`, and v1.1 will print a
#     loud banner and refuse to say GREEN. That is the tool being correct about
#     what it does and does not know. It flips to GREEN when the list is
#     regenerated against the rebuilt manifest at the close.
#
#  Shape per D317: preflight -> SUMS -> KIT_ID -> selftest gate BEFORE placing
#  anything -> backup -> place -> run the real check -> honest report.
# =============================================================================
set -u

KIT_NAME="S186_V1a"
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
&& echo "-- CURRENCY GATE (F-97): the box must be running the checker we think it is." \
&& { if [ -f "$DEST/verify_live_pins.py" ]; then \
       LIVE_NOW="$(md5sum "$DEST/verify_live_pins.py" | awk '{print $1}')"; \
       if [ "$LIVE_NOW" != "ce36dbf10e7d5bbd5310507add41f3cb" ]; then \
         echo "!! live verify_live_pins.py is $LIVE_NOW, expected ce36dbf10e... (v1.0)"; \
         echo "   Refusing. Read the live file and rebuild on THAT — this is F-97."; \
         exit 1; \
       fi; \
       echo "   live checker = ce36dbf10e... (v1.0) as expected"; \
     else \
       echo "   no checker installed yet — first install, nothing to be stale"; \
     fi; } \
&& echo "" \
&& echo "-- GATE: proving BOTH tools can actually fail, before either is trusted..." \
&& "$PY" verify_live_pins.py --selftest \
&& "$PY" gen_live_pins.py --selftest \
&& "$PY" -m py_compile verify_live_pins.py \
&& "$PY" -m py_compile gen_live_pins.py \
&& echo "" \
&& echo "-- gate green; placing the tools (nothing live is touched)" \
&& mkdir -p "$DEST" \
&& { [ -f "$DEST/verify_live_pins.py" ] && cp -f "$DEST/verify_live_pins.py" "$DEST/verify_live_pins.py.bak_$KIT_NAME" && echo "   (previous checker kept as verify_live_pins.py.bak_$KIT_NAME)" || true; } \
&& { [ -f "$DEST/gen_live_pins.py" ]    && cp -f "$DEST/gen_live_pins.py"    "$DEST/gen_live_pins.py.bak_$KIT_NAME" || true; } \
&& { [ -f "$DEST/live_pins.txt" ]       && cp -f "$DEST/live_pins.txt"       "$DEST/live_pins.txt.bak_$KIT_NAME" && echo "   (previous pin list kept as live_pins.txt.bak_$KIT_NAME — the ff509b01 one)" || true; } \
&& cp -f verify_live_pins.py "$DEST/verify_live_pins.py" \
&& cp -f gen_live_pins.py    "$DEST/gen_live_pins.py" \
&& cp -f live_pins.txt       "$DEST/live_pins.txt" \
&& chmod 0755 "$DEST/verify_live_pins.py" \
&& echo "" \
&& echo "=============================================================" \
&& echo " $KIT_NAME INSTALLED — tools placed, both selftests green." \
&& echo " Nothing live was touched and no service was restarted." \
&& echo "=============================================================" \
&& echo "" \
&& echo "-- now running the FIRST REAL CHECK against the corrected record." \
&& echo "   Whatever it says below, the install above already succeeded." \
&& echo "" \
&& { "$PY" "$DEST/verify_live_pins.py" --pins "$DEST/live_pins.txt"; RC=$?; \
     echo ""; \
     if [ $RC -eq 0 ]; then \
       echo ">> No drift. Expect the verdict line to read AMBER, not GREEN:"; \
       echo "   the pin list is honestly stamped 'pending' because Register v5.7"; \
       echo "   is not in the manifest until the S186 close. Regenerate then."; \
     elif [ $RC -eq 1 ]; then \
       echo ">> RED: the record and the box still disagree somewhere."; \
       echo "   Send this output back. The Register gets corrected from the BOX,"; \
       echo "   never the other way round (D321(d))."; \
     else \
       echo ">> The checker refused to run (exit $RC). Tools are placed;"; \
       echo "   nothing was verified. Send this output back."; \
     fi; \
     echo ""; \
     exit 0; } \
|| { echo ""; \
     echo "RED — install did not complete."; \
     echo "   A gate fired before anything was placed, OR a copy failed."; \
     echo "   Nothing live was touched by this kit at any point."; \
     exit 1; }
