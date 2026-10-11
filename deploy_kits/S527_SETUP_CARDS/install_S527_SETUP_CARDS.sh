#!/bin/bash
# =============================================================================
#  install_S527_SETUP_CARDS.sh · kit S527_SETUP_CARDS (session 305, 11-Oct-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S527_SETUP_CARDS/install_S527_SETUP_CARDS.sh
#
#  THE OWNER, 06-Oct ("all hostinger, cyberpanel, ssh login etc, websites setup and logins, links to open these from
#  here, bitwarden setup for storing logins in a phased easy and comprehensive way") and 11-Oct 08:10 IST ("DO NOW"):
#  the five set-up cards on /finance/pcs that were "to be built" -- Hostinger, CyberPanel, the SSH login, the websites,
#  Bitwarden -- written from the server's own files and the records. Never a password, a key, or where one lies.
#  FILE: /root/finance/setup_notes.py 61348f42 -> 63477bc0. Restarts clinic-finance (the page's app).
#  ORDER: kit SUMS + KIT_ID -> the build lock -> the pin (ALREADY INSTALLED first) -> compile -> THE WALK ON THIS BOX
#  (both versions render the section with this box's punch file and staff list; the biometric card byte for byte the
#  same; five well-formed cards after it) -> DRY=1 stops -> backup -> place -> restart -> health -> after-check -> undo.
#  Red after placing -> the old file back byte for byte and the app restarted.
# =============================================================================
set -u
KIT="S527_SETUP_CARDS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"                       # the finance app's own interpreter
FIN="${FIN:-/root/finance}"
SN="$FIN/setup_notes.py"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"
SVC="${SVC:-clinic-finance}"
FROM_SN=61348f425820d28f3e2a53435ca64acd; TO_SN=63477bc0781f6554b57a7868ea6161dc
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="/tmp/s527_inst_$STAMP"
HAVE_LOCK=0; PLACED=0
BAK="$SN.bak_S527_${FROM_SN:0:8}"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; rm -rf "$SCR"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the old file back byte for byte"
  [ -f "$BAK" ] && \cp -p "$BAK" "$SN"
  systemctl restart "$SVC" || true; sleep 3
  say "   $SN $(m5 "$SN")  (expected $FROM_SN)"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date systemctl curl timeout grep tail sleep; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
[ -x "$APY" ] || { say "!! preflight: $APY not executable - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 setup_notes.py)" = "$TO_SN" ] || { say "!! [1/8] the kit's file is not its predicted md5 - nothing installed"; exit 1; }
mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
if [ "$HAVE_LOCK" != 1 ]; then
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Paste the line again when it is free."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
say "[1/8] kit gates green; the build lock is ours"

[ -f "$SN" ] || { say "!! [2/8] $SN is not there - nothing installed"; exit 1; }
CUR="$(m5 "$SN")"
if [ "$CUR" = "$TO_SN" ]; then say "-- ALREADY INSTALLED: $SN is the kit's. Nothing written."; md5sum "$SN"; exit 0; fi
[ "$CUR" = "$FROM_SN" ] || { say "!! [2/8] $SN is $CUR, expected $FROM_SN - nothing installed"; exit 1; }
say "[2/8] the live pin exact"

mkdir -p "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONPYCACHEPREFIX="$SCR/pyc"
export PYTHONDONTWRITEBYTECODE=1
"$APY" -m py_compile setup_notes.py walk_s527.py make_s527.py || { say "!! [3/8] compile failed - nothing installed"; exit 1; }
say "[3/8] py_compile green (3 files)"

WOUT="$( cd /tmp && timeout 120 "$APY" -B "$KDIR/walk_s527.py" "$KDIR" --live "$SN" 2>&1 )"; WRC=$?
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK"; then
  say "!! [4/8] the walk is RED on this box (exit $WRC):"; echo "$WOUT" | tail -6; say "   nothing installed"; exit 1
fi
echo "$WOUT" | grep -E '^   '
say "[4/8] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

\cp -p "$SN" "$BAK" || { say "!! [5/8] backup failed - nothing placed"; exit 1; }
[ "$(m5 "$BAK")" = "$FROM_SN" ] || { say "!! [5/8] the backup is not the live file - nothing placed"; exit 1; }
say "[5/8] backup beside the file: $(basename "$BAK")"

\cp -p setup_notes.py "$FIN/.setup_notes.py.s527" || { rm -f "$FIN/.setup_notes.py.s527"; say "!! [6/8] could not stage the file - nothing placed"; exit 1; }
PLACED=1
mv -f "$FIN/.setup_notes.py.s527" "$SN" || restore "placing setup_notes.py"
[ "$(m5 "$SN")" = "$TO_SN" ] || restore "the file did not land at its pin"
say "[6/8] the file placed at its pin"

systemctl restart "$SVC" || restore "restart $SVC"
c1=000; c2=000
for _try in 1 2 3 4 5 6 7 8 9 10; do
  sleep 3
  c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz")
  [ "$c1" = 200 ] && break
done
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/pcs")
systemctl is-active --quiet "$SVC" || restore "$SVC is not active"
say "[7/8] $SVC active - health $c1 - the PCs page without a login $c2 (302 expected)"
{ [ "$c1" = 200 ] && { [ "$c2" = 302 ] || [ "$c2" = 401 ] || [ "$c2" = 303 ]; }; } || restore "health $c1 / $c2"

AOUT="$( cd /tmp && timeout 60 "$APY" -B -c "
import importlib.util
s = importlib.util.spec_from_file_location('sn_after', '$SN'); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
h = m.section()
assert len(m.CARDS) == 5 and not m.TO_BUILD and 'To be built' not in h and h.count('<div class=pc>') == 6
print('AFTER OK - the placed notes render the biometric card and the five set-up cards, %d characters' % len(h))
" 2>&1 )"; ARC=$?
if [ "$ARC" != 0 ] || ! echo "$AOUT" | grep -q "^AFTER OK"; then
  say "!! [8/8] the placed file does not read as it must (exit $ARC):"; echo "$AOUT" | tail -3; restore "after-check"
fi
PLACED=0
say "[8/8] $AOUT"
md5sum "$SN"
say "$KIT: DONE"
say "read next: https://followup.dr-manoj.in/finance/pcs"
say "undo: \\cp -p $BAK $SN && systemctl restart $SVC"
