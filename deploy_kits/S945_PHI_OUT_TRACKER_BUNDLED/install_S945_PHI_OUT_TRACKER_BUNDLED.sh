#!/bin/bash
# install_S945_PHI_OUT_TRACKER_BUNDLED.sh -- S945 (the parent, S511, 24-Nov-2026): roadmap S510 phase 0, A3 + A4.
#   A3 (F-1631): make_force_keys.py (41 patient numbers in its TRIPLES list), force_keys.txt and call_verdict_BACKUP_S123_* leave
#       /root/wa/recordings-archive/ for /root/_retired/S510/ (0700; the bundle never enters _retired); the retired script's list
#       is emptied -- the numbers are gone from the box's code. Nothing imports them.
#   A4 (F-1613): /root/state_backup/code_bundle.py aa8f985f -> TO: the server tracker's top-level *.py / *.sh join the nightly bundle.
#   [1/5] SUMS   [2/5] code_bundle.py aa8f985f (or already TO); the venv; the lock   [3/5] walk_s945 + retire --selftest + --check
#   [4/5] retire --apply; code_bundle.py placed (.bak_S945_aa8f985f), read back; `code_bundle.py build` (local tar only, no Drive)
#         must list the tracker's server_runner.py and no make_force_keys.py -- else everything back   [5/5] the counts said
#   DRY=1: gates, walk, selftest, --check.   --undo: code_bundle.py back; the three files back (the numbers do not come back).
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s945kit && cp -rp /root/deploy/repo/deploy_kits/S945_PHI_OUT_TRACKER_BUNDLED /tmp/s945kit && bash /tmp/s945kit/install_S945_PHI_OUT_TRACKER_BUNDLED.sh
set -u
KIT="S945_PHI_OUT_TRACKER_BUNDLED"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/}"; SB="${SB:-${ROOT%/}/root/state_backup}"; RA="${RA:-${ROOT%/}/root/wa/recordings-archive}"; RET="${RET:-${ROOT%/}/root/_retired/S510}"
APY="${APY:-/root/wa/venv/bin/python3}"; LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
CB="code_bundle.py"; LIVE="$SB/$CB"; FROM="aa8f985f197289992e502b0cf997a25d"
SCR="$(mktemp -d /tmp/s945_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0; RETIRED=0; CB_CHANGED=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
m8() { m5 "$1" | cut -c1-8; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { release_lock; rm -rf "${SCR:?}" "$SB/.$CB.s945"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
pya() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 900 "$APY" -W ignore -B "$@" 2>&1); }
ret() { (cd /tmp && RA="$RA" RET="$RET" TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" "$APY" -W ignore -B "$KDIR/retire_s945.py" "$@" 2>&1); }
TO="$(to_of "state_backup/$CB")"; BAK="$LIVE.bak_S945_${FROM:0:8}"
restore() { say "!! RED ($1) - putting back"
  [ "$CB_CHANGED" = 1 ] && [ -f "$BAK" ] && \cp -p "$BAK" "$LIVE"
  [ "$RETIRED" = 1 ] && ret --undo
  say "   restored: $CB $(m8 "$LIVE") (expected ${FROM:0:8}); $(ret --check). Tell Claude."; release_lock; exit 1; }
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK" ] && { [ "$(m5 "$LIVE")" = "$TO" ] || stop "!! --undo: $LIVE is $(m8 "$LIVE"), not this kit's (a later kit?) - not undoing"; }
  mkdir "$LOCK" 2>/dev/null || stop "!! --undo: another build holds $LOCK - try again in five minutes"; TOOK_LOCK=1; echo "$KIT undo" > "$LOCK/owner"
  [ -f "$BAK" ] && { \cp -p "$BAK" "$LIVE"; [ "$(m5 "$LIVE")" = "$FROM" ] || say "!! --undo: $CB read back $(m8 "$LIVE"), not ${FROM:0:8} - tell Claude"; }
  ret --undo; release_lock; say "$KIT: UNDONE ($CB $(m8 "$LIVE"); $(ret --check))"; exit 0
fi
cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "!! [1/5] KIT_ID.txt names another kit - nothing installed"
[ "$(m5 "$KDIR/$CB")" = "$TO" ] || stop "!! [1/5] the kit's $CB is not as built - nothing installed"
say "   [1/5] kit sums ok"
[ -x "$APY" ] || stop "!! [2/5] $APY is not there - STOP. Tell Claude."
[ -f "$LIVE" ] && [ -d "$RA" ] || stop "!! [2/5] $LIVE or $RA missing - STOP. Tell Claude."
l="$(m5 "$LIVE")"; C0="$(ret --check)"
if [ "$l" = "$TO" ] && [ "${C0#*leftovers in the live folder 0 of 3}" != "$C0" ]; then say "-- $KIT is already installed ($C0). Nothing done."; exit 0; fi
[ "$l" = "$FROM" ] || [ "$l" = "$TO" ] || stop "!! [2/5] $LIVE is ${l:0:8}, not ${FROM:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
pya -m py_compile "$KDIR/$CB" >/dev/null 2>&1 || stop "!! [2/5] the kit's $CB does not compile under $APY - nothing installed"
if [ "${DRY:-0}" = 1 ]; then say "   [2/5] DRY RUN: $CB ${l:0:8}; compiles; $C0; no lock"
elif mkdir "$LOCK" 2>/dev/null; then echo "$KIT $$" > "$LOCK/owner"; TOOK_LOCK=1; say "   [2/5] $CB ${l:0:8}; compiles; $C0; the build lock taken"
else stop "!! [2/5] another build holds $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - try again in five minutes"; fi
W="$(pya "$KDIR/walk_s945.py" "$KDIR/$CB" "$SCR/w945" | tail -1)"; [ "$W" = "WALK 8/8" ] || stop "!! [3/5] walk_s945: $W - nothing installed"
Wc="$(CB_FROM="$LIVE" pya "$KDIR/walk_s945.py" "$KDIR/$CB" "$SCR/w945c" --control | tail -1)"; [ "$Wc" != "WALK 8/8" ] || { [ "$l" = "$TO" ] || stop "!! [3/5] walk_s945's control did not go red - nothing installed"; }
say "   [3/5] walk $W (control $Wc); before: $C0"
[ "${DRY:-0}" = 1 ] && { say "-- DRY RUN: every gate and the walk green; nothing live changed"; exit 0; }
A="$(ret --apply)"; case "$A" in "APPLY moved"*) RETIRED=1 ;; *) RETIRED=1; restore "[4/5] $A";; esac
if [ "$l" != "$TO" ]; then
  { \cp -p "$LIVE" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || restore "could not write the backup $BAK"
  { cat "$KDIR/$CB" > "$SB/.$CB.s945" && chmod --reference="$LIVE" "$SB/.$CB.s945" && chown --reference="$LIVE" "$SB/.$CB.s945" && [ "$(m5 "$SB/.$CB.s945")" = "$TO" ]; } || restore "could not stage $CB"
  CB_CHANGED=1; mv -f "$SB/.$CB.s945" "$LIVE" || restore "the rename"
  [ "$(m5 "$LIVE")" = "$TO" ] || restore "read back $(m8 "$LIVE"), not the TO pin ${TO:0:8}"
fi
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
(cd "$SB" && ROOT="$ROOT" pya "$LIVE" build) > "$SCR/build.txt" 2>&1; B="$(tail -3 "$SCR/build.txt")"; echo "$B" | grep -q 'SUMMARY files=' || restore "code_bundle.py build did not finish: $B"
TAR="$SB/code_nightly.tar.gz"; [ -f "$TAR" ] || restore "no local bundle at $TAR after the build"
MAN="$(tar -xzOf "$TAR" MANIFEST.md5 2>/dev/null)"
echo "$MAN" | grep -q 'root/followup_tracker/server_runner.py' || { grep -E 'EXCLUDED|source directory absent' "$SCR/build.txt" | sed 's/^/        build said: /'; restore "the built bundle's MANIFEST does not list root/followup_tracker/server_runner.py"; }
echo "$MAN" | grep -q 'make_force_keys' && restore "the built bundle still carries make_force_keys.py"
echo "$MAN" | grep -q 'followup_tracker/data/\|followup_tracker/uploads/\|followup_tracker/venv/' && restore "the built bundle entered a tracker data folder"
release_lock
say "   [4/5] $(echo "$A" | head -1); $CB ${FROM:0:8} -> $(m8 "$LIVE") (bak beside); the local bundle rebuilt: $(echo "$MAN" | grep -c 'root/followup_tracker/') tracker file(s) in, make_force_keys out"
say "   [5/5] after: $(ret --check). The 25-Nov bundle (01:35) is the proof the nightly carries it. Undo: bash $KDIR/install_$KIT.sh --undo"
say "$KIT: DONE."
exit 0
