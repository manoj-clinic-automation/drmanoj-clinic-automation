#!/bin/bash
# rehearse_s942.sh -- kit S942 on a MADE-UP root: the VM's python3 as the venv, a stub probe (PROBE_CMD). No live file, no network.
# Scenes: A dry . B install . C again . D undo . E forced red at [4/5] . F probe red -> nothing changed . G tampered kit . H wrong
#         live pin -> nothing . I lock held -> nothing
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; R="$(mktemp -d /tmp/s942_reh.XXXXXX)"; trap 'rm -rf "$R"' EXIT
FROMF="${FROMF:?call_transcription.py FROM ee8d3e41}"
n=0; f=0; ok() { n=$((n+1)); if eval "$2"; then echo "  ok   $1"; else echo "  FAIL $1"; f=$((f+1)); fi; }
m8() { md5sum "$1" | cut -c1-8; }
TO8="$(awk '/call_transcription/{print substr($1,1,8)}' "$KDIR/TO_PINS.md5")"
mk() { rm -rf "$R/root"; mkdir -p "$R/root/wa/recordings-archive" "$R/root/deploy"; cp "$FROMF" "$R/root/wa/recordings-archive/call_transcription.py"
  printf '#!/bin/bash\necho "PROBE OK stub"\n' > "$R/pok"; printf '#!/bin/bash\necho "PROBE FAIL stub 400"\n' > "$R/pbad"; chmod +x "$R/pok" "$R/pbad"; }
run() { ROOT="$R/root" LOCK="$R/root/deploy/.lock" APY="$(command -v python3)" PROBE_CMD="${PROBE:-$R/pok}" bash "$KDIR/install_S942_SAARAS_V4.sh" "$@" 2>&1; }
LIVE="$R/root/wa/recordings-archive/call_transcription.py"
echo "A  dry"; mk; out="$(DRY=1 run)"; echo "$out" | tail -2 | sed 's/^/     /'
ok "A dry says nothing changed" 'echo "$out" | grep -q "nothing live changed"'; ok "A live untouched" '[ "$(m8 "$LIVE")" = ee8d3e41 ]'
echo "B  install"; out="$(run)"; echo "$out" | tail -3 | sed 's/^/     /'
ok "B DONE" 'echo "$out" | grep -q "S942_SAARAS_V4: DONE"'; ok "B live at TO, bak beside" '[ "$(m8 "$LIVE")" = "$TO8" ] && [ "$(m8 "$LIVE.bak_S942_ee8d3e41")" = ee8d3e41 ]'
ok "B lock released" '[ ! -d "$R/root/deploy/.lock" ]'
echo "C  again"; out="$(run)"; ok "C already installed" 'echo "$out" | grep -q "already installed"'
echo "D  undo"; out="$(run --undo)"; ok "D UNDONE, live back" 'echo "$out" | grep -q "UNDONE" && [ "$(m8 "$LIVE")" = ee8d3e41 ]'
echo "E  forced red at 4"; mk; out="$(REHEARSE_RED_AT=4 run)"; ok "E restored, exit 1" 'echo "$out" | grep -q "RED" && [ "$(m8 "$LIVE")" = ee8d3e41 ]'
ok "E lock released" '[ ! -d "$R/root/deploy/.lock" ]'
echo "F  probe red"; mk; out="$(PROBE="$R/pbad" run)"; ok "F stopped at the probe, nothing changed" 'echo "$out" | grep -q "did not take saaras:v4" && [ "$(m8 "$LIVE")" = ee8d3e41 ] && [ ! -f "$LIVE.bak_S942_ee8d3e41" ]'
echo "G  tampered kit"; mk; cp -rp "$KDIR" "$R/kitT"; echo "# x" >> "$R/kitT/call_transcription.py"
out="$(ROOT="$R/root" LOCK="$R/root/deploy/.lock" APY="$(command -v python3)" PROBE_CMD="$R/pok" bash "$R/kitT/install_S942_SAARAS_V4.sh" 2>&1)"; ok "G SUMS gate" 'echo "$out" | grep -q "SUMS.md5 gate failed"'
echo "H  wrong live pin"; mk; echo "# drift" >> "$LIVE"; out="$(run)"; ok "H stop, nothing installed" 'echo "$out" | grep -q "it changed after this kit was built"'
echo "I  lock held"; mk; mkdir -p "$R/root/deploy/.lock"; out="$(run)"; ok "I refused, live untouched" 'echo "$out" | grep -q "another build holds" && [ "$(m8 "$LIVE")" = ee8d3e41 ]'
echo "REHEARSAL $((n-f))/$n"; [ "$f" = 0 ]
