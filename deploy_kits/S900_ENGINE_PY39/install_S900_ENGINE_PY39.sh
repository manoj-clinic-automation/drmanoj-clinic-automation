#!/bin/bash
# install_S900_ENGINE_PY39.sh -- S900 (the parent, S493, 20-Nov-2026): the tracker's engine stands on the box's Python 3.9.
# S899's import-check: /root/wa/venv is Python 3.9.25; processor.py's 3.10-style type hints (`str | None`) refuse to import
# there. ONE LINE -- `from __future__ import annotations` -- as the engine's first statement after its docstring cures it;
# nothing else changes (revenue.py / revenue_ingest.py already carry the line). The replay's seeded copy of the pre-10-Nov
# engine (replay/processor.py.bak_S777_0e7c129f) gets the same line in place. The runner stays OFF.
#   [1/5] the kit's SUMS.md5 gate   [2/5] /root/followup_tracker/processor.py is f1c02736 (S895's, = the PC's bytes); the replay
#         copy is 0e7c129f; S897 seeded; OFF present; the venv   [3/5] placed: processor.py -> bade3c1a (.bak_S900_f1c02736);
#         the replay copy patched in place by py39_future.py (.bak_S900_0e7c129f); both read back
#   [4/5] --import-check under the venv must say 0 errors, else both files go back   [5/5] Replay 2 --run; counts
#   --undo : both files back from their .bak
set -u
KIT="S900_ENGINE_PY39"; KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"; FUT="${FUT:-/root/followup_tracker}"; WA="${WA:-/root/wa}"
ENG="$FUT/processor.py"; ENG_FROM="f1c02736"; OLD="$FUT/replay/processor.py.bak_S777_0e7c129f"; OLD_FROM="0e7c129f"; OLD_TO="44adfff8"
SCR="$(mktemp -d /tmp/s900_inst.XXXXXX)"; trap 'rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null' EXIT
m8() { md5sum "$1" 2>/dev/null | cut -c1-8; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
stop() { say "$1"; exit 1; }
pyv() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PYV_TIMEOUT:-3600}" "$VPY" -W ignore -B "$@" 2>&1); }
restore() { say "!! RED ($1) - putting the engine back"
  [ -f "$ENG.bak_S900_$ENG_FROM" ] && mv -f "$ENG.bak_S900_$ENG_FROM" "$ENG"
  [ -f "$OLD.bak_S900_$OLD_FROM" ] && mv -f "$OLD.bak_S900_$OLD_FROM" "$OLD"
  say "   restored: processor.py $(m8 "$ENG") (expected $ENG_FROM); the replay copy $(m8 "$OLD") (expected $OLD_FROM). Send a photo of this screen to Claude."; exit 1; }
if [ "${1:-}" = "--undo" ]; then
  [ "$(m8 "$ENG")" = "$ENG_FROM" ] && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  [ "$(md5sum "$ENG" | cut -c1-32)" = "$(to_of followup_tracker/processor.py)" ] || stop "!! $ENG is $(m8 "$ENG"), not this kit's - nothing undone. Tell Claude."
  [ -f "$ENG.bak_S900_$ENG_FROM" ] && [ "$(m8 "$ENG.bak_S900_$ENG_FROM")" = "$ENG_FROM" ] || stop "!! no good backup of processor.py - nothing undone"
  mv -f "$ENG.bak_S900_$ENG_FROM" "$ENG"
  [ -f "$OLD.bak_S900_$OLD_FROM" ] && mv -f "$OLD.bak_S900_$OLD_FROM" "$OLD"
  say "$KIT: UNDONE (processor.py back at $(m8 "$ENG"); the replay copy at $(m8 "$OLD"))"; exit 0
fi
cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"
say "   [1/5] kit sums ok"
[ -x "$VPY" ] || stop "!! [2/5] $VPY is not there"
[ -f "$ENG" ] || stop "!! [2/5] $ENG is not there - S895 is not installed. Tell Claude."
[ "$(m8 "$ENG")" = "$ENG_FROM" ] || { [ "$(md5sum "$ENG" | cut -c1-32)" = "$(to_of followup_tracker/processor.py)" ] && stop "-- $KIT is already installed; Replay 2 again: FUT_ROOT=$FUT $VPY -B $FUT/replay2_s897.py --run"; stop "!! [2/5] $ENG is $(m8 "$ENG"), not $ENG_FROM - STOP. Tell Claude."; }
[ -f "$OLD" ] || stop "!! [2/5] $OLD is not there - the seed did not carry the replay engine. Tell Claude."
[ "$(m8 "$OLD")" = "$OLD_FROM" ] || stop "!! [2/5] $OLD is $(m8 "$OLD"), not $OLD_FROM - STOP. Tell Claude."
[ -f "$FUT/SEEDED_AT" ] || stop "!! [2/5] $FUT is not seeded - STOP. Tell Claude."
[ -e "$FUT/OFF" ] || stop "!! [2/5] $FUT/OFF is ABSENT - STOP. Tell Claude."
[ -f "$FUT/replay2_s897.py" ] && grep -q 'import-check' "$FUT/replay2_s897.py" || stop "!! [2/5] S899's replay2_s897.py is not there - STOP. Tell Claude."
say "   [2/5] engine $ENG_FROM (the PC's bytes), replay copy $OLD_FROM, seeded, OFF; venv $(pyv -c 'import sys; print(sys.version.split()[0])' | tail -1)"
pyv -m py_compile "$KDIR/processor.py" >/dev/null 2>&1 || stop "!! [3/5] the kit's processor.py does not compile in the venv - nothing installed"
\cp -p "$ENG" "$ENG.bak_S900_$ENG_FROM" && [ "$(m8 "$ENG.bak_S900_$ENG_FROM")" = "$ENG_FROM" ] || stop "!! [3/5] could not write the engine's backup - nothing placed"
\cp -p "$OLD" "$OLD.bak_S900_$OLD_FROM" && [ "$(m8 "$OLD.bak_S900_$OLD_FROM")" = "$OLD_FROM" ] || stop "!! [3/5] could not write the replay copy's backup - nothing placed"
\cp -p "$KDIR/processor.py" "$ENG.s900" && mv -f "$ENG.s900" "$ENG" && chmod 600 "$ENG" || restore "placing processor.py"
[ "$(md5sum "$ENG" | cut -c1-32)" = "$(to_of followup_tracker/processor.py)" ] || restore "processor.py read back $(m8 "$ENG"), not its TO pin"
pyv "$KDIR/py39_future.py" "$OLD" --apply >/dev/null 2>&1 || restore "the replay copy could not take the line"
[ "$(m8 "$OLD")" = "$OLD_TO" ] || restore "the replay copy read back $(m8 "$OLD"), not $OLD_TO"
say "   [3/5] placed: processor.py $(m8 "$ENG") (one line more than $ENG_FROM; .bak beside) . replay copy $(m8 "$OLD") (.bak beside)"
ic="$(FUT_ROOT="$FUT" pyv "$FUT/replay2_s897.py" --import-check)"; echo "$ic" | sed 's/^/         /'
echo "$ic" | grep -q 'import-check: 0 error' || restore "the engine still does not import"
say "   [4/5] the engine imports under the venv"
rp="$(FUT_ROOT="$FUT" FU_INBOX_DIR="$WA/followup-inbox" REPLAY2_SCRATCH="$SCR/replay" pyv "$FUT/replay2_s897.py" --run --report "$FUT/logs/REPLAY2_REPORT.txt")"
rs="$(echo "$rp" | grep '^RESULT:' | tail -1)"
say "   [5/5] REPLAY 2 on the box: ${rs:-did not finish -- $(echo "$rp" | tail -1 | cut -c1-200)}"
echo "$rp" | grep -E '^#[0-9]+ .* FAIL' | head -10 | sed 's/^/         /'
echo "$rp" | grep -q '^NOTHING COMPARED' && say "         !! NOTHING COMPARED. Tell Claude."
say "$KIT: DONE (the runner stays OFF). ${rs:-Replay 2 did not finish}. Report: $FUT/logs/REPLAY2_REPORT.txt"
exit 0
