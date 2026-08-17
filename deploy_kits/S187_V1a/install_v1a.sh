#!/bin/bash
# =============================================================================
#  install_v1a.sh · kit S187_V1a — verify_live_pins v1.2 + gen_live_pins v1.2
#                   + the regenerated pin list (Register v5.13, PENDING).
#
#  THE FAULT THIS FIXES (F-117, proved live at the S187 open as F-122).
#  The v1.1 checker printed `source : VERIFIED against the manifest (md5 ...)`
#  on the strength of the word `yes` in the pin list header — hashing nothing.
#  The md5 it displayed, `78881ddd...`, matches NO file in any of the repo's
#  157 commits: the generator hashed the manifest mid-EOS, and the manifest's
#  own rule ("self-row recomputed last") guarantees that state is edited again
#  before the push. Every generation minted a phantom (V1b: `04eff42c...`).
#
#  FROM v1.2 THE CLAIM IS PROVED ON THIS BOX, from /root/deploy/repo (the D317
#  chain's clone, pulled by vps_deploy.sh before this script ran): find the
#  file in repo canon that HASHES to the pin list's source_md5 (D188), parse
#  the manifest beside it, confirm its CURRENT KB_Register row pins that hash.
#  VERIFIED is printed only after both comparisons pass. Anything else: AMBER.
#
#  EXPECT AFTER THIS INSTALL:  match 42 · drift 0 · missing 0 ·
#  VERDICT: AMBER (pending) — the pin list is generated from Register v5.13,
#  whose manifest row lands at the S187 close. AMBER-by-design, the S186_V1a
#  precedent. It goes GREEN when the close regenerates the list with
#  --manifest against the rebuilt manifest — and that GREEN will be PROVED.
#
#  Rehearsal: VLP_DEST=/tmp/throwaway/deploy bash install_v1a.sh
# =============================================================================
set -u
KIT_NAME="S187_V1a"
DEST="${VLP_DEST:-/root/deploy}"
PY=/usr/bin/python3
KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; cd "$KIT_DIR" || exit 1

# expected CURRENT state of the box (the D317 currency gate):
OLD_CHECKER="ea3677b9fc6456b514a1ef623a9ced15"   # verify_live_pins.py v1.1
NEW_CHECKER="b4da75ec19f8c7fa613fb9962a272a1a"   # verify_live_pins.py v1.2
NEW_GEN="9c402c366e7c902f27047a2014062107"       # gen_live_pins.py    v1.2

md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT_NAME" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum SUMS.md5 | awk '{print $1}')" ] \
&& echo "-- kit integrity OK" \
&& [ "$(md5sum verify_live_pins.py | awk '{print $1}')" = "$NEW_CHECKER" ] \
&& [ "$(md5sum gen_live_pins.py    | awk '{print $1}')" = "$NEW_GEN" ] \
&& echo "-- payload hashes match the Register v5.13 pins" \
&& { CUR="$(md5sum "$DEST/verify_live_pins.py" 2>/dev/null | awk '{print $1}')"; \
     if [ "$CUR" = "$NEW_CHECKER" ]; then echo "-- v1.2 already installed; will re-place idempotently"; \
     elif [ "$CUR" = "$OLD_CHECKER" ]; then echo "-- currency gate OK: the box runs v1.1 ($OLD_CHECKER)"; \
     else echo "!! CURRENCY GATE RED: $DEST/verify_live_pins.py is '$CUR'"; \
          echo "   -- neither v1.1 nor v1.2. The box is not in the recorded state."; \
          echo "   -- NOTHING was changed. Read the live file, fix the record first (D321(d))."; \
          exit 1; fi; } \
&& grep -q '^# register_pin_verified: pending' live_pins.txt \
&& grep -q '^# source_md5: 3f1c46d8148586decccd77816df7e3de' live_pins.txt \
&& echo "-- pin list is the v5.13 PENDING list (source_md5 3f1c46d8...)" \
&& grep -q "^VPS	$NEW_CHECKER	/root/deploy/verify_live_pins.py" live_pins.txt \
&& echo "-- the list pins the checker at its OWN new hash (no expected drift)" \
&& "$PY" verify_live_pins.py --selftest >/dev/null 2>&1 \
&& echo "-- NEW checker selftest GREEN on this machine (43/43), from the kit dir, before any swap" \
&& "$PY" gen_live_pins.py --selftest >/dev/null 2>&1 \
&& echo "-- NEW generator selftest GREEN on this machine (22/22)" \
&& mkdir -p "$DEST" \
&& { for f in verify_live_pins.py gen_live_pins.py live_pins.txt; do \
       [ -f "$DEST/$f" ] && cp -f "$DEST/$f" "$DEST/$f.bak_$KIT_NAME"; done; \
     echo "   previous files kept as *.bak_$KIT_NAME"; } \
&& cp -f verify_live_pins.py gen_live_pins.py live_pins.txt "$DEST/" \
&& chmod +x "$DEST/verify_live_pins.py" \
&& echo "" \
&& echo "-- running the NEW checker against the NEW list" \
&& { "$PY" "$DEST/verify_live_pins.py" --pins "$DEST/live_pins.txt"; RC=$?; \
     echo ""; \
     if [ $RC -eq 0 ]; then \
       echo ">> EXPECTED RESULT: 42 match / 0 drift / 0 missing, VERDICT AMBER (pending)."; \
       echo ">> AMBER is BY DESIGN until the S187 close pins Register v5.13 in the manifest."; \
       echo ">> If it printed VERIFIED ON THIS MACHINE it proved it. It cannot lie by design."; \
     else \
       echo ">> exit $RC - send this output back. Do NOT edit the box to match the record."; \
     fi; exit 0; } \
|| { echo ""; echo "RED - nothing was installed (or the failing gate above stopped the run)."; \
     echo "      Any files already backed up as *.bak_$KIT_NAME are untouched originals."; exit 1; }
