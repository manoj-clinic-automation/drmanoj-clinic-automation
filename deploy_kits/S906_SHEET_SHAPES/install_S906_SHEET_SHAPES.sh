#!/bin/bash
# install_S906_SHEET_SHAPES.sh -- S906 (the parent, S493, 20-Nov-2026): READ ONLY. For runs #7 and #25 of Replay 2, print the
# Call Sheet's header row and the differing rows' non-identity values (box vs inbox). Nothing placed, nothing changed.
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; FUT="${FUT:-/root/followup_tracker}"; WA="${WA:-/root/wa}"; VPY="${VPY:-/root/followup_tracker/venv/bin/python3}"
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! SUMS.md5 gate failed"; exit 1; }
for pair in "07:Staff_Action_Today_2026-10-23.xlsx" "25:Staff_Action_Today_2026-11-11.xlsx"; do
  n="${pair%%:*}"; name="${pair#*:}"
  box="$(ls "$FUT"/logs/replay_out/run${n}_*.xlsx 2>/dev/null | head -1)"
  echo "== run #$n: box $(basename "${box:-none}") vs inbox $name"
  [ -n "$box" ] && [ -f "$WA/followup-inbox/$name" ] || { echo "   one of the two files is not there"; continue; }
  TZ=Asia/Kolkata "$VPY" -B "$KDIR/sheet_shapes_s906.py" "$box" "$WA/followup-inbox/$name" 2>&1 | cut -c1-400
done
echo "S906_SHEET_SHAPES: DONE (read only)"
