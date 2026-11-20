#!/bin/bash
# install_S908_STABLE_TIES.sh -- S908 (the parent, S493, 20-Nov-2026): the engine picks the same patients on every machine.
# Replay 2 (S897-S907) traced the Call Sheet's differences to ONE sort: over the 120-call cap, the room is filled with the most
# overdue dropouts, sorted on days overdue with a sort whose tie order the CPU settles -- the box and the PC choose different
# patients among those tied at the cut-off. `kind="stable"` on that sort (and the Probable Dropouts sheet's, the same column)
# keeps ties in the engine's own priority order: the same on every machine. The owner's OK of 20:1x IST; the PC's engine gets
# the same word from the assistant (connected folder). Then Replay 2 prints a content hash per run, compared with the VM's.
#   [1/5] SUMS gate  [2/5] processor.py bade3c1a (S900's) or f1c02736; the replay copy; S907's replay2 730b36cb; seeded; OFF
#   [3/5] processor.py and the replay copy patched in place (.bak_S908_<from> beside; --check 2 of 2); replay2 -> S897.8
#   [4/5] --import-check  [5/5] --run: RESULT (pass / order-only / fail) + the content hash of every compared run
#   --undo : the three files back from their .bak_S908_ files
set -u
KIT="S908_STABLE_TIES"; KDIR="$(cd "$(dirname "$0")" && pwd)"
FUT="${FUT:-/root/followup_tracker}"; WA="${WA:-/root/wa}"
VPY="${VPY:-}"; [ -n "$VPY" ] || { [ -x "$FUT/venv/bin/python3" ] && VPY="$FUT/venv/bin/python3" || VPY="/root/wa/venv/bin/python3"; }
ENG="$FUT/processor.py"; OLD="$FUT/replay/processor.py.bak_S777_0e7c129f"; R2="$FUT/replay2_s897.py"; R2_FROM="730b36cb"
SCR="$(mktemp -d /tmp/s908_inst.XXXXXX)"; trap 'rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null' EXIT
m8() { md5sum "$1" 2>/dev/null | cut -c1-8; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
stop() { say "$1"; exit 1; }
pyv() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PYV_TIMEOUT:-3600}" "$VPY" -W ignore -B "$@" 2>&1); }
restore() { say "!! RED ($1) - putting the files back"; for f in "$ENG" "$OLD" "$R2"; do b="$(ls "$f".bak_S908_* 2>/dev/null | head -1)"; [ -n "$b" ] && mv -f "$b" "$f"; done
  say "   restored: processor.py $(m8 "$ENG"), replay copy $(m8 "$OLD"), replay2 $(m8 "$R2"). Tell Claude."; exit 1; }
if [ "${1:-}" = "--undo" ]; then
  n=0; for f in "$ENG" "$OLD" "$R2"; do b="$(ls "$f".bak_S908_* 2>/dev/null | head -1)"; [ -n "$b" ] && { mv -f "$b" "$f"; n=$((n+1)); }; done
  [ "$n" = 0 ] && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  say "$KIT: UNDONE ($n file(s) back: processor.py $(m8 "$ENG"), replay copy $(m8 "$OLD"), replay2 $(m8 "$R2"))"; exit 0
fi
cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"
say "   [1/5] kit sums ok"
[ -x "$VPY" ] || stop "!! [2/5] $VPY is not there"
[ -f "$FUT/SEEDED_AT" ] || stop "!! [2/5] $FUT is not seeded - STOP. Tell Claude."
[ -e "$FUT/OFF" ] || stop "!! [2/5] $FUT/OFF is ABSENT - STOP. Tell Claude."
pyv "$KDIR/stable_sort_s908.py" "$ENG" --check >/dev/null && stop "-- $KIT is already on the engine ($(m8 "$ENG")); Replay 2 again: FUT_ROOT=$FUT $VPY -B $R2 --run"
case "$(m8 "$ENG")" in bade3c1a|f1c02736) ;; *) stop "!! [2/5] $ENG is $(m8 "$ENG"), neither S900's nor the PC's - STOP. Tell Claude.";; esac
[ -f "$OLD" ] || stop "!! [2/5] $OLD is not there - STOP. Tell Claude."
[ "$(m8 "$R2")" = "$R2_FROM" ] || stop "!! [2/5] $R2 is $(m8 "$R2"), not $R2_FROM (S907's) - STOP. Tell Claude."
say "   [2/5] engine $(m8 "$ENG"), replay copy $(m8 "$OLD"), replay2 $R2_FROM; seeded; OFF; python $VPY"
for f in "$ENG" "$OLD" "$R2"; do \cp -p "$f" "$f.bak_S908_$(m8 "$f")" || stop "!! [3/5] could not write the backup of $(basename "$f") - nothing placed"; done
pyv "$KDIR/stable_sort_s908.py" "$ENG" --apply | sed 's/^/         /' || restore "patching processor.py"
pyv "$KDIR/stable_sort_s908.py" "$OLD" --apply | sed 's/^/         /' || restore "patching the replay copy"
pyv "$KDIR/stable_sort_s908.py" "$ENG" --check >/dev/null || restore "processor.py --check"
pyv "$KDIR/stable_sort_s908.py" "$OLD" --check >/dev/null || restore "the replay copy --check"
pyv -m py_compile "$ENG" >/dev/null 2>&1 || restore "processor.py does not compile"
\cp -p "$KDIR/replay2_s897.py" "$R2.s908" && mv -f "$R2.s908" "$R2" && chmod 600 "$R2" || restore "placing replay2"
[ "$(md5sum "$R2" | cut -c1-32)" = "$(to_of followup_tracker/replay2_s897.py)" ] || restore "replay2 read back $(m8 "$R2")"
say "   [3/5] processor.py $(m8 "$ENG") (2 sorts stable; .bak_S908_ beside) . replay copy $(m8 "$OLD") . replay2 $(m8 "$R2")"
ic="$(FUT_ROOT="$FUT" pyv "$R2" --import-check | tail -1)"
echo "$ic" | grep -q '0 error' || restore "the engine does not import ($ic)"
say "   [4/5] $ic"
rp="$(FUT_ROOT="$FUT" FU_INBOX_DIR="$WA/followup-inbox" REPLAY2_SCRATCH="$SCR/replay" pyv "$R2" --run --report "$FUT/logs/REPLAY2_REPORT.txt")"
rs="$(echo "$rp" | grep '^RESULT:' | tail -1)"
say "   [5/5] REPLAY 2: ${rs:-did not finish -- $(echo "$rp" | tail -1 | cut -c1-200)}"
echo "$rp" | grep -E '^#[0-9]+ ' | grep -v SKIP | sed -E 's/ \(code [^)]*\)//; s/\[box [^ ]* inbox [^ ]* content ([0-9a-f]+)/content \1 [/; s/ -- by column.*//' | cut -c1-120 | sed 's/^/         /'
say "$KIT: DONE (the runner stays OFF). ${rs:-Replay 2 did not finish}."
exit 0
