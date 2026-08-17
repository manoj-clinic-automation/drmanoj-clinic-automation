#!/bin/bash
# =============================================================================
#  install_v1c.sh · kit S186_V1c — the CORRECTED pin list (S186 post-close).
#
#  No code changes. It places one file: /root/deploy/live_pins.txt.
#
#  Why this kit exists. S186_V1b's list went RED on one file --
#  finance_workbench.html, record 45cb85b3..., box 18c71e63... The BOX WAS
#  RIGHT: the workbench shipped twice (S186_R2a, then a newer build inside
#  S186_I1a) and the close kept the superseded value (F-118). The Register is
#  corrected to v5.12 and this list is generated from it.
#
#  It also fixes what V1b's header claimed: V1b attested to manifest md5
#  04eff42c..., which exists nowhere -- the manifest was re-pinned after that
#  list was built (F-117). This list is generated with --manifest against the
#  rebuilt manifest 78881ddd..., so the attestation is true AND checkable.
#
#  Expect: GREEN -- 42 match, 0 drift, 0 missing.
#  NOTE: verify_live_pins.py still PRINTS the manifest md5 without comparing it
#  to a file. That gap is F-117 and the ~3-line fix is item 0 in Runbook v121.
# =============================================================================
set -u
KIT_NAME="S186_V1c"; DEST=/root/deploy; PY=/usr/bin/python3
KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; cd "$KIT_DIR" || exit 1
md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT_NAME" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum live_pins.txt | awk '{print $1}')" ] \
&& echo "-- kit integrity OK" \
&& grep -q '^# register_pin_verified: yes' live_pins.txt \
&& echo "-- the list is manifest-verified (register_pin_verified: yes)" \
&& grep -q '^# source_md5: 1da5b0c4783e50fc2cbebe4b9ac7c61a' live_pins.txt \
&& echo "-- built from KB Register v5.12 (1da5b0c4...)" \
&& grep -q '^VPS	18c71e63e5f1790c07d7fa3df53cd24e	/root/finance/finance_ui/finance_workbench.html' live_pins.txt \
&& echo "-- the F-118 correction is present (workbench pinned to the box build 18c71e63...)" \
&& { [ -f "$DEST/live_pins.txt" ] && cp -f "$DEST/live_pins.txt" "$DEST/live_pins.txt.bak_$KIT_NAME" \
     && echo "   previous list kept as live_pins.txt.bak_$KIT_NAME" || true; } \
&& cp -f live_pins.txt "$DEST/live_pins.txt" \
&& echo "" \
&& echo "-- running the check with the corrected list" \
&& { "$PY" "$DEST/verify_live_pins.py"; RC=$?; \
     echo ""; \
     if [ $RC -eq 0 ]; then echo ">> GREEN - the record and the box agree. F-118 closed."; \
     else echo ">> exit $RC - send this output back. Do NOT edit the box to match the record."; fi; \
     exit 0; } \
|| { echo ""; echo "RED - the list was not placed. Nothing changed. Check the message above."; exit 1; }
