#!/bin/bash
# =============================================================================
#  install_S685_CONSENT_SPELLING_FIX.sh · kit S685 (the parent, session S371, 31-Oct-2026)
#  The consent's Hindi-spelling box: a corrected address (or name) now reaches the consent.
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s685kit && cp -rp /root/deploy/repo/deploy_kits/S685_CONSENT_SPELLING_FIX /tmp/s685kit && bash /tmp/s685kit/install_S685_CONSENT_SPELLING_FIX.sh
#  (DRY=1 before bash: every gate, nothing written.)
#
#  ONE file, pinned:  /root/wa/casepack/casepack_page.html  ff713e36 (S684's TO, installed 09:12 IST) -> TO
#   The box looked for the spelling as typed; the consent prints it tidied (no space before a comma, no double space), so
#   a correction found 0 places, still showed a tick, and changed only the header. Now it looks for the printed form, and a
#   correction that finds nothing changes nothing and says so. The page is read per request: NO restart.
#  The walk runs in a real browser where the kit was built (walk_s685 10 of 10; control on ff713e36 7 red, 0 older red;
#  walk_s684 still 45 of 45 on the new page). Here the gate is that make_s685.py rebuilds the kit's page byte for byte
#  from THIS box's live file. Red after placing: the old page back from its backup.
# =============================================================================
set -u
KIT="S685_CONSENT_SPELLING_FIX"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
REL="wa/casepack/casepack_page.html"
LIVE="$ROOT/$REL"
FROM_MD5=ff713e36a1ecd082a43ee1824b654df1
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
PPORT="${PPORT:-8099}"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s685_inst_$STAMP"
BAK="$LIVE.bak_S685_${FROM_MD5:0:8}"
TOOK_LOCK=0; PLACED=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
code() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; release_lock; }
trap on_exit EXIT
stop() { say "!! STOPPED: $1"; say "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the old page back"
  [ -f "$BAK" ] && \cp -p "$BAK" "$LIVE"
  rm -f "$(dirname "$LIVE")/.casepack_page.html.s685"
  say "   $LIVE $(m5 "$LIVE") (expected $FROM_MD5) · portal health $(code "http://127.0.0.1:$PPORT/portal/health")"
  say "   Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_signal INT TERM HUP

say "== $KIT =="
cd "$KDIR" || { say "!! the kit folder is not there"; exit 1; }
for c in md5sum awk cp mv date curl grep find; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || { say "!! the kit's files do not match SUMS.md5 - nothing installed"; exit 1; }
TO_MD5=$(m5 "$KDIR/casepack_page.html")
say "[1/6] kit files: all match SUMS.md5 (the new page $TO_MD5)"
mkdir -p "$(dirname "$LOCK")" && mkdir "$LOCK" 2>/dev/null || { say "!! another install is running (lock $LOCK). Wait 5 minutes and run the line again"; exit 1; }
TOOK_LOCK=1; echo "$KIT $STAMP" > "$LOCK/owner"
mkdir -p "$SCR" || stop "no scratch folder"
h=$(m5 "$LIVE")
if [ "$h" = "$TO_MD5" ]; then say "ALREADY INSTALLED (the live page is the kit's). Nothing written."; exit 0; fi
[ "$h" = "$FROM_MD5" ] || stop "the live page is $h -- neither its pinned version ${FROM_MD5:0:8} nor the kit's"
say "[2/6] pin: $LIVE ${FROM_MD5:0:8}"
PYTHONPYCACHEPREFIX="$SCR/pyc" "$APY" -m py_compile make_s685.py || stop "make_s685.py does not compile"
R="$("$APY" -I -B make_s685.py "$LIVE" "$SCR/rebuilt.html" 2>&1 | tail -1)"
[ "$(m5 "$SCR/rebuilt.html")" = "$TO_MD5" ] || stop "rebuilding from this box's live page did not give the kit's page ($R)"
say "[3/6] rebuilt from this box's live page by its four anchored edits: byte for byte the kit's ($R)"
n1=$(grep -c "S685 (31-Oct-2026)" "$KDIR/casepack_page.html"); n2=$(grep -c "</html>" "$KDIR/casepack_page.html")
{ [ "$n1" = 1 ] && [ "$n2" = 1 ]; } || stop "the new page is not whole (S685 marker $n1, </html> $n2)"
p0=$(code "http://127.0.0.1:$PPORT/portal/health"); [ "$p0" = 200 ] || stop "the portal is not healthy before the install ($p0)"
c0=$(code "http://127.0.0.1:$PPORT/portal/casepack"); case "$c0" in 000|5*) stop "the Case Pack page does not answer before the install ($c0)";; esac
say "[4/6] the new page is whole; portal healthy ($p0); the Case Pack page answers $c0 without a login (its gate)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate green; NOTHING written, nothing placed"; exit 0; fi

\cp -p "$LIVE" "$BAK" && [ "$(m5 "$BAK")" = "$FROM_MD5" ] || stop "the backup of the live page failed"
STG="$(dirname "$LIVE")/.casepack_page.html.s685"
{ cat "$KDIR/casepack_page.html" > "$STG" && [ "$(m5 "$STG")" = "$TO_MD5" ]; } || { rm -f "$STG"; stop "could not stage the new page"; }
chmod --reference="$LIVE" "$STG" 2>/dev/null; chown --reference="$LIVE" "$STG" 2>/dev/null
PLACED=1
mv -f "$STG" "$LIVE" || restore "the rename"
[ "$(m5 "$LIVE")" = "$TO_MD5" ] || restore "the md5 read back"
say "[5/6] placed and read back: $LIVE $TO_MD5 (backup $(basename "$BAK"))"
p1=$(code "http://127.0.0.1:$PPORT/portal/health"); [ "$p1" = 200 ] || restore "portal health $p1 after placing"
c1=$(code "http://127.0.0.1:$PPORT/portal/casepack"); [ "$c1" = "$c0" ] || restore "the Case Pack page answers $c1 after placing ($c0 before)"
say "[6/6] portal healthy after placing ($p1); the Case Pack page answers $c1 as before; no restart needed (read on every request)"
release_lock
say ""
say "INSTALLED. In the consent's Hindi-spelling box, a corrected name or address now changes in the consent too;"
say "if a correction cannot be found in the text, the box now says so instead of showing a tick."
say "Reload the Case Pack page once (pull down / F5)."
say "undo (one line): \\cp -p $BAK $LIVE"
exit 0
