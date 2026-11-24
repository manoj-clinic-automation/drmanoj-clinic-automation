#!/bin/bash
# install_S942_SAARAS_V4.sh -- S942 (the parent, S511, 24-Nov-2026): the call transcriber moves to Sarvam's Saaras v4.
# Sarvam's mail of 16-Oct-2026 ("Action needed: move fully to Saaras v4"): v3 is legacy; one change -- the model name; same
# request, same price. The ONE place the estate sends speech to Sarvam is /root/wa/recordings-archive/call_transcription.py
# (the at-hangup worker and the 03:00 timer both run it afresh each time -- no service to restart). The call hook never talks to
# Sarvam: no webhook change.
#   [1/5] SUMS gate   [2/5] the live file ee8d3e41 (or already this kit's); compiles under /root/wa/venv
#   [3/5] walk_s942 (kit vs live; control red) ; the PROBE: saaras:v4 answers through BOTH doors with the live key (a 1.2-s
#         made-up tone; one batch job initiated, never started) -- red = STOP, nothing changed
#   [4/5] .bak_S942_ee8d3e41 beside; the file placed and read back at its TO pin   [5/5] said: how the first real run proves it
#   DRY=1 bash ... : gates, walk and probe only.   --undo : the file back from its .bak_S942_ file.
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s942kit && cp -rp /root/deploy/repo/deploy_kits/S942_SAARAS_V4 /tmp/s942kit && bash /tmp/s942kit/install_S942_SAARAS_V4.sh
set -u
KIT="S942_SAARAS_V4"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; RA="${RA:-$ROOT/wa/recordings-archive}"; APY="${APY:-$ROOT/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
F="call_transcription.py"; LIVE="$RA/$F"; FROM="ee8d3e4134ff78d0c01f4e2ecd34a215"
SCR="$(mktemp -d /tmp/s942_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
m8() { m5 "$1" | cut -c1-8; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { release_lock; rm -rf "${SCR:?}" "$RA/.$F.s942"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
pya() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 300 "$APY" -W ignore -B "$@" 2>&1); }
probe() { if [ -n "${PROBE_CMD:-}" ]; then $PROBE_CMD; else pya "$KDIR/probe_s942.py"; fi; }
TO="$(to_of "wa/recordings-archive/$F")"; BAK="$LIVE.bak_S942_${FROM:0:8}"
restore() { say "!! RED ($1) - putting back"; [ -f "$BAK" ] && \cp -p "$BAK" "$LIVE"; say "   $F $(m8 "$LIVE") (expected ${FROM:0:8}). Tell Claude."; release_lock; exit 1; }
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK" ] && [ "$(m5 "$BAK")" = "$FROM" ] || { say "!! --undo: no good backup $BAK - nothing undone"; exit 1; }
  [ "$(m5 "$LIVE")" = "$TO" ] || { say "!! --undo: $LIVE is $(m8 "$LIVE"), not this kit's ${TO:0:8} (a later kit?) - not undoing"; exit 1; }
  \cp -p "$BAK" "$LIVE" && [ "$(m5 "$LIVE")" = "$FROM" ] || { say "!! --undo: the copy back did not read ${FROM:0:8} - tell Claude"; exit 1; }
  say "$KIT: UNDONE ($F back at $(m8 "$LIVE") = saaras:v3; the next run uses v3)"; exit 0
fi
cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "!! [1/5] KIT_ID.txt names another kit - nothing installed"
[ "$(m5 "$KDIR/$F")" = "$TO" ] || stop "!! [1/5] the kit's $F is not as built - nothing installed"
say "   [1/5] kit sums ok"
[ -x "$APY" ] || stop "!! [2/5] $APY is not there - STOP. Tell Claude."
[ -f "$LIVE" ] || stop "!! [2/5] $LIVE missing - STOP. Tell Claude."
l="$(m5 "$LIVE")"
[ "$l" = "$TO" ] && { say "-- $KIT is already installed ($F $(m8 "$LIVE") = saaras:v4). Nothing done."; exit 0; }
[ "$l" = "$FROM" ] || stop "!! [2/5] $LIVE is ${l:0:8}, not ${FROM:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
pya -m py_compile "$KDIR/$F" >/dev/null 2>&1 || stop "!! [2/5] the kit's $F does not compile under $APY - nothing installed"
if [ "${DRY:-0}" = 1 ]; then say "   [2/5] DRY RUN: live file ${l:0:8} as expected; compiles; no lock"
elif mkdir "$LOCK" 2>/dev/null; then echo "$KIT $$" > "$LOCK/owner"; TOOK_LOCK=1; say "   [2/5] live file ${l:0:8} as expected; compiles; the build lock taken"
else stop "!! [2/5] another build holds $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - try again in five minutes"; fi
W="$(pya "$KDIR/walk_s942.py" "$LIVE" "$KDIR/$F" | tail -1)"; [ "$W" = "WALK 9/9" ] || stop "!! [3/5] walk_s942: $W - nothing installed"
Wc="$(pya "$KDIR/walk_s942.py" "$LIVE" "$KDIR/$F" --control | tail -1)"; [ "$Wc" != "WALK 9/9" ] || stop "!! [3/5] walk_s942's control did not go red - nothing installed"
P="$(probe | tail -1)"; case "$P" in "PROBE OK"*) ;; *) stop "!! [3/5] $P - Sarvam did not take saaras:v4 with the live key: nothing changed (v3 stays). Tell Claude.";; esac
say "   [3/5] walk $W (control $Wc); $P"
[ "${DRY:-0}" = 1 ] && { say "-- DRY RUN: every gate, the walk and the probe green; nothing live changed"; exit 0; }
{ \cp -p "$LIVE" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop "!! [4/5] could not write the backup $BAK - nothing placed"
{ cat "$KDIR/$F" > "$RA/.$F.s942" && chmod --reference="$LIVE" "$RA/.$F.s942" && chown --reference="$LIVE" "$RA/.$F.s942" && [ "$(m5 "$RA/.$F.s942")" = "$TO" ]; } || stop "!! [4/5] could not stage $F - nothing placed"
mv -f "$RA/.$F.s942" "$LIVE" || restore "the rename"
[ "$(m5 "$LIVE")" = "$TO" ] || restore "read back $(m8 "$LIVE"), not the TO pin ${TO:0:8}"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
pya -m py_compile "$LIVE" >/dev/null 2>&1 || restore "the placed file does not compile"
release_lock
say "   [4/5] $F ${FROM:0:8} -> $(m8 "$LIVE") (bak beside); no service to restart -- the at-hangup worker and the 03:00 timer start it afresh"
say "   [5/5] proof: the next call's transcript row (Call_Transcripts, Status done) is v4's; the 11:00 pulse mail counts them as before. Undo: bash $KDIR/install_$KIT.sh --undo"
say "$KIT: DONE."
exit 0
