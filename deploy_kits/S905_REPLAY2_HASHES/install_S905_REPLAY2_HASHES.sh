#!/bin/bash
# install_S905_REPLAY2_HASHES.sh -- S905 (the parent, S493, 20-Nov-2026): the same engine, the same libraries (S904), still 24 FAIL
# on the Call Sheet's last rows. Each compared run now prints the md5+size of the inbox workbook and of the box's own output, and
# keeps the box's outputs in logs/replay_out/ (the box only). One file: replay2_s897.py 3e786720 -> TO (S897.6); the venv the S904 one.
#   [1/4] SUMS gate  [2/4] the live file is 3e786720 (S903's)  [3/4] placed (.bak_S905_ beside), read back  [4/4] --run with hashes
#   --undo : the file back from its .bak
set -u
KIT="S905_REPLAY2_HASHES"; KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/followup_tracker/venv/bin/python3}"; FUT="${FUT:-/root/followup_tracker}"; WA="${WA:-/root/wa}"
FROM="3e786720"; F="$FUT/replay2_s897.py"
SCR="$(mktemp -d /tmp/s905_inst.XXXXXX)"; trap 'rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null' EXIT
m8() { md5sum "$1" 2>/dev/null | cut -c1-8; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
stop() { say "$1"; exit 1; }
pyv() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PYV_TIMEOUT:-3600}" "$VPY" -W ignore -B "$@" 2>&1); }
if [ "${1:-}" = "--undo" ]; then
  [ "$(m8 "$F")" = "$FROM" ] && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  [ "$(md5sum "$F" | cut -c1-32)" = "$(to_of followup_tracker/replay2_s897.py)" ] || stop "!! $F is $(m8 "$F"), not this kit's - nothing undone. Tell Claude."
  [ -f "$F.bak_S905_$FROM" ] && [ "$(m8 "$F.bak_S905_$FROM")" = "$FROM" ] || stop "!! no good backup - nothing undone"
  mv -f "$F.bak_S905_$FROM" "$F" && say "$KIT: UNDONE (replay2_s897.py back at $FROM)"; exit 0
fi
cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/4] SUMS.md5 gate failed - kit corrupt, nothing installed"
say "   [1/4] kit sums ok"
[ -x "$VPY" ] || stop "!! [2/4] $VPY is not there"
[ -f "$F" ] || stop "!! [2/4] $F is not there - S897 is not installed. Tell Claude."
[ "$(m8 "$F")" = "$FROM" ] || { [ "$(md5sum "$F" | cut -c1-32)" = "$(to_of followup_tracker/replay2_s897.py)" ] && stop "-- $KIT is already installed; to run Replay 2 again: FUT_ROOT=$FUT $VPY -B $F --run"; stop "!! [2/4] $F is $(m8 "$F"), not $FROM - STOP. Tell Claude."; }
[ -f "$FUT/SEEDED_AT" ] || stop "!! [2/4] $FUT is not seeded (no SEEDED_AT) - STOP. Tell Claude."
[ -e "$FUT/OFF" ] || stop "!! [2/4] $FUT/OFF is ABSENT - STOP. Tell Claude."
say "   [2/4] replay2_s897.py at $FROM; seeded; runner OFF"
pyv -m py_compile "$KDIR/replay2_s897.py" >/dev/null 2>&1 || stop "!! [3/4] replay2_s897.py does not compile in the venv - nothing installed"
\cp -p "$F" "$F.bak_S905_$FROM" && [ "$(m8 "$F.bak_S905_$FROM")" = "$FROM" ] || stop "!! [3/4] could not write the backup - nothing placed"
\cp -p "$KDIR/replay2_s897.py" "$F.s899" && mv -f "$F.s899" "$F" && chmod 600 "$F" || { mv -f "$F.bak_S905_$FROM" "$F"; stop "!! [3/4] could not place - put back"; }
[ "$(md5sum "$F" | cut -c1-32)" = "$(to_of followup_tracker/replay2_s897.py)" ] || { mv -f "$F.bak_S905_$FROM" "$F"; stop "!! [3/4] read back $(m8 "$F"), not the TO pin - put back"; }
say "   [3/4] placed: $F $(m8 "$F") (bak .bak_S905_$FROM)"
say "   [4/4] import-check under the venv:"
ic="$(FUT_ROOT="$FUT" pyv "$F" --import-check)"; echo "$ic" | sed 's/^/         /'
if echo "$ic" | grep -q 'import-check: 0 error'; then
  rp="$(FUT_ROOT="$FUT" FU_INBOX_DIR="$WA/followup-inbox" REPLAY2_SCRATCH="$SCR/replay" pyv "$F" --run --keep-out "$FUT/logs/replay_out" --report "$FUT/logs/REPLAY2_REPORT.txt")"
  rs="$(echo "$rp" | grep '^RESULT:' | tail -1)"
  say "         REPLAY 2: ${rs:-did not finish -- $(echo "$rp" | tail -1 | cut -c1-200)}"
  echo "$rp" | grep -E '^#[0-9]+ ' | grep -v SKIP | sed -E 's/\[xlsx.*//; s/ -- by column.*//' | cut -c1-150 | sed 's/^/         /'
  echo "$rp" | grep -q '^NOTHING COMPARED' && say "         !! NOTHING COMPARED. Tell Claude."
  say "$KIT: DONE. ${rs:-Replay 2 did not finish}. Report: $FUT/logs/REPLAY2_REPORT.txt"
else
  say "         the venv's: $(pyv -c "import sys; print(sys.version.split()[0])" | tail -1); $("$VPY" -m pip list 2>/dev/null | grep -iE '^(pandas|numpy|openpyxl) ' | tr '\n' ' ')"
  say "$KIT: DONE (file placed) -- THE ENGINE DOES NOT IMPORT UNDER THE VENV (the lines above say which module and why). Replay 2 not run. Send Claude the lines above."
fi
exit 0
