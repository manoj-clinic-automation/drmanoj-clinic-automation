#!/bin/bash
# rehearse_s942.sh -- kit S942 on a MADE-UP root: the VM's python3 as the venv, a stub probe (PROBE_CMD). No live file, no network.
# Scenes: A dry . B install . C again . D undo . E forced red at [4/5] . F dry-run red after placing -> restored . G tampered kit . H wrong
#         live pin -> nothing . I lock held -> nothing
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; R="$(mktemp -d /tmp/s944_reh.XXXXXX)"; trap 'rm -rf "$R"' EXIT
FROMF="${FROMF:?call_transcription.py FROM 6b72038d (S942 TO)}"
n=0; f=0; ok() { n=$((n+1)); if eval "$2"; then echo "  ok   $1"; else echo "  FAIL $1"; f=$((f+1)); fi; }
m8() { md5sum "$1" | cut -c1-8; }
TO8="$(awk '/call_transcription/{print substr($1,1,8)}' "$KDIR/TO_PINS.md5")"
mk() { rm -rf "$R/root"; mkdir -p "$R/root/wa/recordings-archive" "$R/root/deploy"; cp "$FROMF" "$R/root/wa/recordings-archive/call_transcription.py"
  printf '#!/bin/bash\necho "Call_Recordings rows: 9 eligible, 7 already done, 2 to process this run."\n' > "$R/dok"; printf '#!/bin/bash\necho "ERROR: could not open sheet"\n' > "$R/dbad"; chmod +x "$R/dok" "$R/dbad"; }
run() { ROOT="$R/root" LOCK="$R/root/deploy/.lock" APY="$(command -v python3)" DRYRUN_CMD="${DRYC:-$R/dok}" bash "$KDIR/install_S944_SHORT_CLIPS_SKIPPED.sh" "$@" 2>&1; }
LIVE="$R/root/wa/recordings-archive/call_transcription.py"
echo "A  dry"; mk; out="$(DRY=1 run)"; echo "$out" | tail -2 | sed 's/^/     /'
ok "A dry says nothing changed" 'echo "$out" | grep -q "nothing live changed"'; ok "A live untouched" '[ "$(m8 "$LIVE")" = 6b72038d ]'
echo "B  install"; out="$(run)"; echo "$out" | tail -3 | sed 's/^/     /'
ok "B DONE" 'echo "$out" | grep -q "S944_SHORT_CLIPS_SKIPPED: DONE"'; ok "B live at TO, bak beside" '[ "$(m8 "$LIVE")" = "$TO8" ] && [ "$(m8 "$LIVE.bak_S944_6b72038d")" = 6b72038d ]'
ok "B lock released" '[ ! -d "$R/root/deploy/.lock" ]'
echo "C  again"; out="$(run)"; ok "C already installed" 'echo "$out" | grep -q "already installed"'
echo "D  undo"; out="$(run --undo)"; ok "D UNDONE, live back" 'echo "$out" | grep -q "UNDONE" && [ "$(m8 "$LIVE")" = 6b72038d ]'
echo "E  forced red at 4"; mk; out="$(REHEARSE_RED_AT=4 run)"; ok "E restored, exit 1" 'echo "$out" | grep -q "RED" && [ "$(m8 "$LIVE")" = 6b72038d ]'
ok "E lock released" '[ ! -d "$R/root/deploy/.lock" ]'
echo "F  dry-run red after placing"; mk; out="$(DRYC="$R/dbad" run)"; ok "F restored: the file back" 'echo "$out" | grep -q "did not print its counts line" && [ "$(m8 "$LIVE")" = 6b72038d ]'
echo "G  tampered kit"; mk; cp -rp "$KDIR" "$R/kitT"; echo "# x" >> "$R/kitT/call_transcription.py"
out="$(ROOT="$R/root" LOCK="$R/root/deploy/.lock" APY="$(command -v python3)" DRYRUN_CMD="$R/dok" bash "$R/kitT/install_S944_SHORT_CLIPS_SKIPPED.sh" 2>&1)"; ok "G SUMS gate" 'echo "$out" | grep -q "SUMS.md5 gate failed"'
echo "H  wrong live pin"; mk; echo "# drift" >> "$LIVE"; out="$(run)"; ok "H stop, nothing installed" 'echo "$out" | grep -q "changed after this kit was built" && [ ! -f "$LIVE.bak_S944_6b72038d" ]'
echo "I  lock held"; mk; mkdir -p "$R/root/deploy/.lock"; out="$(run)"; ok "I refused, live untouched" 'echo "$out" | grep -q "another build holds" && [ "$(m8 "$LIVE")" = 6b72038d ]'
echo "REHEARSAL $((n-f))/$n"; [ "$f" = 0 ]
