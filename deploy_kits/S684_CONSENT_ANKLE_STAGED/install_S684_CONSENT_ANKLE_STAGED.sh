#!/bin/bash
# =============================================================================
#  install_S684_CONSENT_ANKLE_STAGED.sh · kit S684 (the parent, session S371, 31-Oct-2026)
#  The Case Pack consent: the ankle's own selector, and the staged plan on a closed fracture.
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s684kit && cp -rp /root/deploy/repo/deploy_kits/S684_CONSENT_ANKLE_STAGED /tmp/s684kit && bash /tmp/s684kit/install_S684_CONSENT_ANKLE_STAGED.sh
#  (DRY=1 before bash: every gate, nothing written.)
#
#  ONE file, pinned:
#   /root/wa/casepack/casepack_page.html  26cba6b1 -> TO   (S680's TO; confirmed by the 31-Oct bundle)
#     * Ankle fracture: tick the bones (medial / lateral / posterior malleolus), the joint (in place / subluxation /
#       dislocation) and fixed-with (plate-screws / screws / wires; none = "screws, wires or plate, as suitable");
#       the opening is built from the ticks and no longer promises plate-screws.
#     * Plan now on any CLOSED fracture: fix now / external fixator now, fix later -- the two-stage paragraph, its risks
#       and "this consent is for the first stage" print from it. An open fracture keeps its own pathway (unchanged);
#       planned operations (replacements, ACL, implant removal...) show no plan-now.
#     * An additional fracture can be marked "plan later" (with or without an operation, decided later).
#     * The ankle's bone list gains the posterior malleolus; an already-plural opening is no longer doubled ("हैंं").
#  The page is read by the portal on every request: NO restart. Saved cases are untouched; an old case reloads as before.
#  The walk runs in a real browser where the kit was built (45 of 45; control on 26cba6b1: 30 S684 red, 0 older red).
#  Here the gate is that make_s684.py, run on THIS box's live file, rebuilds the kit's page byte for byte.
#  Red after placing: the old page back from its backup.
# =============================================================================
set -u
KIT="S684_CONSENT_ANKLE_STAGED"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
REL="wa/casepack/casepack_page.html"
LIVE="$ROOT/$REL"
FROM_MD5=26cba6b11a21f1bf6a5062f6084314a6
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
PPORT="${PPORT:-8099}"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s684_inst_$STAMP"
BAK="$LIVE.bak_S684_${FROM_MD5:0:8}"
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
  rm -f "$(dirname "$LIVE")/.casepack_page.html.s684"
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
PYTHONPYCACHEPREFIX="$SCR/pyc" "$APY" -m py_compile make_s684.py || stop "make_s684.py does not compile"
R="$("$APY" -I -B make_s684.py "$LIVE" "$SCR/rebuilt.html" 2>&1 | tail -1)"
[ "$(m5 "$SCR/rebuilt.html")" = "$TO_MD5" ] || stop "rebuilding from this box's live page did not give the kit's page ($R)"
say "[3/6] rebuilt from this box's live page by its nine anchored edits: byte for byte the kit's ($R)"
n1=$(grep -c "S684 end" "$KDIR/casepack_page.html"); n2=$(grep -c "</html>" "$KDIR/casepack_page.html")
{ [ "$n1" = 1 ] && [ "$n2" = 1 ]; } || stop "the new page is not whole (S684 end $n1, </html> $n2)"
p0=$(code "http://127.0.0.1:$PPORT/portal/health"); [ "$p0" = 200 ] || stop "the portal is not healthy before the install ($p0)"
c0=$(code "http://127.0.0.1:$PPORT/portal/casepack"); case "$c0" in 000|5*) stop "the Case Pack page does not answer before the install ($c0)";; esac
say "[4/6] the new page is whole; portal healthy ($p0); the Case Pack page answers $c0 without a login (its gate)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate green; NOTHING written, nothing placed"; exit 0; fi

\cp -p "$LIVE" "$BAK" && [ "$(m5 "$BAK")" = "$FROM_MD5" ] || stop "the backup of the live page failed"
STG="$(dirname "$LIVE")/.casepack_page.html.s684"
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
say "INSTALLED. In the Case Pack consent: the ankle has its own ticks (which bones, the joint, fixed with), any closed fracture"
say "can be planned 'external fixator now, fix later', and an extra fracture can be 'plan later'."
say "Reload the Case Pack page once (pull down / F5)."
say "undo (one line): \\cp -p $BAK $LIVE"
exit 0
