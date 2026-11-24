#!/bin/bash
# install_S944_SHORT_CLIPS_SKIPPED.sh -- S944 (the parent, S511, 24-Nov-2026): the leftover loop stopped (roadmap S510 A2, F-1633).
# call_transcription.py (S942's bytes 6b72038d) gains two rules: a clip of 10 s or under is never sent (one 'skipped' row); a clip of
# 30 s or under that has failed three times gets one 'skipped' row and is never re-tried; a 'skipped' row settles the call. The verdict
# stage reads only 'done' rows, so a skipped call is never judged (no change there). The 14 clips the night sweep re-tried every
# night (1,530 failed rows) are settled by the next run itself -- no one-off. No service to restart (the worker and the 03:00 timer
# start the script afresh).
#   [1/5] SUMS gate   [2/5] the live file 6b72038d (S942's; or already this kit's); compiles under /root/wa/venv
#   [3/5] walk_s944 (kit vs live; control red)   [4/5] .bak_S944_6b72038d beside; placed; read back; a --dry-run under the venv
#         (reads the tabs only) must print its counts line   [5/5] said.   DRY=1: gates and walk.   --undo: the file back.
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s944kit && cp -rp /root/deploy/repo/deploy_kits/S944_SHORT_CLIPS_SKIPPED /tmp/s944kit && bash /tmp/s944kit/install_S944_SHORT_CLIPS_SKIPPED.sh
set -u
KIT="S944_SHORT_CLIPS_SKIPPED"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; RA="${RA:-$ROOT/wa/recordings-archive}"; APY="${APY:-$ROOT/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
F="call_transcription.py"; LIVE="$RA/$F"; FROM="6b72038d666b83a48e20e1d56bbe8584"
SCR="$(mktemp -d /tmp/s944_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
m8() { m5 "$1" | cut -c1-8; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { release_lock; rm -rf "${SCR:?}" "$RA/.$F.s944"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
pya() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 300 "$APY" -W ignore -B "$@" 2>&1); }
dry() { if [ -n "${DRYRUN_CMD:-}" ]; then $DRYRUN_CMD; else (cd "$RA" && pya "$LIVE" --dry-run); fi; }
TO="$(to_of "wa/recordings-archive/$F")"; BAK="$LIVE.bak_S944_${FROM:0:8}"
restore() { say "!! RED ($1) - putting back"; [ -f "$BAK" ] && \cp -p "$BAK" "$LIVE"; say "   $F $(m8 "$LIVE") (expected ${FROM:0:8}). Tell Claude."; release_lock; exit 1; }
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK" ] && [ "$(m5 "$BAK")" = "$FROM" ] || { say "!! --undo: no good backup $BAK - nothing undone"; exit 1; }
  [ "$(m5 "$LIVE")" = "$TO" ] || { say "!! --undo: $LIVE is $(m8 "$LIVE"), not this kit's ${TO:0:8} (a later kit?) - not undoing"; exit 1; }
  \cp -p "$BAK" "$LIVE" && [ "$(m5 "$LIVE")" = "$FROM" ] || { say "!! --undo: the copy back did not read ${FROM:0:8} - tell Claude"; exit 1; }
  say "$KIT: UNDONE ($F back at $(m8 "$LIVE") = S942's; the next run re-tries the short clips as before)"; exit 0
fi
cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "!! [1/5] KIT_ID.txt names another kit - nothing installed"
[ "$(m5 "$KDIR/$F")" = "$TO" ] || stop "!! [1/5] the kit's $F is not as built - nothing installed"
say "   [1/5] kit sums ok"
[ -x "$APY" ] || stop "!! [2/5] $APY is not there - STOP. Tell Claude."
[ -f "$LIVE" ] || stop "!! [2/5] $LIVE missing - STOP. Tell Claude."
l="$(m5 "$LIVE")"
[ "$l" = "$TO" ] && { say "-- $KIT is already installed ($F $(m8 "$LIVE")). Nothing done."; exit 0; }
[ "$l" = "$FROM" ] || stop "!! [2/5] $LIVE is ${l:0:8}, not ${FROM:0:8} (S942's) - S942 not installed, or the file changed after this kit was built: STOP, nothing installed. Tell Claude."
pya -m py_compile "$KDIR/$F" >/dev/null 2>&1 || stop "!! [2/5] the kit's $F does not compile under $APY - nothing installed"
if [ "${DRY:-0}" = 1 ]; then say "   [2/5] DRY RUN: live file ${l:0:8} as expected; compiles; no lock"
elif mkdir "$LOCK" 2>/dev/null; then echo "$KIT $$" > "$LOCK/owner"; TOOK_LOCK=1; say "   [2/5] live file ${l:0:8} as expected; compiles; the build lock taken"
else stop "!! [2/5] another build holds $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - try again in five minutes"; fi
W="$(pya "$KDIR/walk_s944.py" "$LIVE" "$KDIR/$F" | tail -1)"; [ "$W" = "WALK 17/17" ] || stop "!! [3/5] walk_s944: $W - nothing installed"
Wc="$(pya "$KDIR/walk_s944.py" "$LIVE" "$KDIR/$F" --control | tail -1)"; [ "$Wc" != "WALK 17/17" ] || stop "!! [3/5] walk_s944's control did not go red - nothing installed"
say "   [3/5] walk $W (control $Wc)"
[ "${DRY:-0}" = 1 ] && { say "-- DRY RUN: every gate, the walk green; nothing live changed"; exit 0; }
{ \cp -p "$LIVE" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop "!! [4/5] could not write the backup $BAK - nothing placed"
{ cat "$KDIR/$F" > "$RA/.$F.s944" && chmod --reference="$LIVE" "$RA/.$F.s944" && chown --reference="$LIVE" "$RA/.$F.s944" && [ "$(m5 "$RA/.$F.s944")" = "$TO" ]; } || stop "!! [4/5] could not stage $F - nothing placed"
mv -f "$RA/.$F.s944" "$LIVE" || restore "the rename"
[ "$(m5 "$LIVE")" = "$TO" ] || restore "read back $(m8 "$LIVE"), not the TO pin ${TO:0:8}"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
pya -m py_compile "$LIVE" >/dev/null 2>&1 || restore "the placed file does not compile"
D="$(dry | grep -m1 'Call_Recordings rows')"; case "$D" in *"to process this run"*) ;; *) restore "the placed script's --dry-run did not print its counts line";; esac
release_lock
say "   [4/5] $F ${FROM:0:8} -> $(m8 "$LIVE") (bak beside); no service to restart; dry-run: $D"
say "   [5/5] proof: the next run writes one 'skipped' row for each of the 14 short clips and never re-tries them -- the 03:00 log and the Call_Transcripts tab show it. Undo: bash $KDIR/install_$KIT.sh --undo"
say "$KIT: DONE."
exit 0
