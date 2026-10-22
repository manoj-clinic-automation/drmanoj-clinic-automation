#!/bin/bash
# =============================================================================
#  install_S617_PCS_PAGE_LIVE.sh · kit S617 (session S336, 22-Oct-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S617_PCS_PAGE_LIVE/install_S617_PCS_PAGE_LIVE.sh
#  DRY=1 before bash: pins, rebuild, walk and control only -- nothing changed.   --undo: the S527 file back.
#
#  THE OWNER (his board note, his pick 07:12 IST): "clinic pc tile - keep the content and data updated there, so that it
#  stays current always".  The set-up cards on /finance/pcs read 'Now' lines from the server each time the page opens
#  (the disk, running since, the nightly jobs, this morning's certificate check); each card says when its notes were
#  checked; the Websites card is brought up to date.  One file: /root/finance/setup_notes.py; clinic-finance restarted.
# =============================================================================
set -u
KIT="S617_PCS_PAGE_LIVE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"                       # the finance app's own interpreter
SN="${SN:-/root/finance/setup_notes.py}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-/root/s617_backup}"
FIN_PORT="${FIN_PORT:-8106}"
SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
BOXFLAG="${BOXFLAG---box}"
FROM="d32423d1472081416b140fc5437523ab"
W=/tmp/s617_walk
HAVE_LOCK=0
on_exit() { rm -rf "$W"; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
m5() { md5sum "$1" 2>/dev/null | cut -c1-32; }
up() { local c=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"); [ "$c" = 200 ] && break; done; echo "$c"; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
NEW=$(m5 setup_notes.py)

if [ "${1:-}" = "--undo" ]; then
  echo "[undo]"
  b=$(ls -1t "$BK"/setup_notes.py.bak_S617_* 2>/dev/null | head -1)
  [ -n "$b" ] && \cp -fp "$b" "$SN" && echo "    setup_notes.py put back ($(m5 "$SN" | cut -c1-8))"
  "$SYSTEMCTL" restart "$SVC" || true
  echo "    finance health: $(up)"
  echo "UNDONE."; exit 0
fi

echo "[1] pins"
NOW=$(m5 "$SN")
if [ "$NOW" = "$NEW" ]; then echo "    ALREADY INSTALLED (setup_notes.py ${NEW:0:8})"; exit 0; fi
[ "$NOW" = "$FROM" ] || stop "setup_notes.py is ${NOW:0:8}, not the S527 file ${FROM:0:8} this kit was built on"
echo "    setup_notes.py ${FROM:0:8} (S527)"

echo "[2] rebuild from the live bytes"
rm -rf "$W"; mkdir -p "$W"; chmod 700 "$W"
PYTHONPYCACHEPREFIX="$W/pyc" "$APY" -m py_compile edits_s617.py walk_s617.py setup_notes.py || stop "the kit's code does not compile on $APY"
"$APY" -B edits_s617.py "$SN" "$W/rb.py" "$KDIR/setup_notes.py" || stop "the kit's file is not exactly the live file plus this kit's edits"

echo "[3] the walk (made-up files; then this machine's real ones, read only) and the control"
\cp -p "$SN" "$W/old.py"
( cd "$W" && timeout 120 "$APY" -B "$KDIR/walk_s617.py" "$W/old.py" "$KDIR/setup_notes.py" $BOXFLAG > "$W/walk.txt" 2>&1 )
WK=$?; grep "on this machine" "$W/walk.txt" | sed 's/^ *ok */    /'; tail -1 "$W/walk.txt" | sed 's/^/    walk: /'
[ "$WK" = 0 ] || { grep "FAIL\|RED\|Error" "$W/walk.txt" | head -8; stop "the walk is not green"; }
( cd "$W" && timeout 120 "$APY" -B "$KDIR/walk_s617.py" "$W/old.py" "$W/old.py" > "$W/ctl.txt" 2>&1 )
[ $? != 0 ] && echo "    control on the live file: RED, as it must be" || stop "the control did not go red -- the walk cannot tell old from new"
if [ "${DRY:-0}" = "1" ]; then echo "-- DRY RUN: nothing changed"; exit 0; fi

echo "[4] backup -> $BK"
mkdir -p "$BK"; chmod 700 "$BK"
\cp -fp "$SN" "$BK/setup_notes.py.bak_S617_${FROM:0:8}" || stop "the backup failed"
put_back() {
  \cp -fp "$BK/setup_notes.py.bak_S617_${FROM:0:8}" "$SN"; "$SYSTEMCTL" restart "$SVC" || true
  stop "$1" "The old file was put back and $SVC restarted (health $(up))."
}

echo "[5] placed"
\cp -p "$KDIR/setup_notes.py" "$SN.s617" && chmod --reference="$BK/setup_notes.py.bak_S617_${FROM:0:8}" "$SN.s617" && mv -f "$SN.s617" "$SN" || put_back "placing setup_notes.py"
[ "$(m5 "$SN")" = "$NEW" ] || put_back "the file did not land byte-exact"
echo "    setup_notes.py ${FROM:0:8} -> ${NEW:0:8}"

echo "[6] $SVC restarted and checked"
"$SYSTEMCTL" restart "$SVC" || put_back "restart $SVC"
c1=$(up)
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/pcs")
"$SYSTEMCTL" is-active --quiet "$SVC" || put_back "$SVC is not active"
{ [ "$c1" = 200 ] && { [ "$c2" = 302 ] || [ "$c2" = 401 ] || [ "$c2" = 303 ] || [ "$c2" = 403 ]; }; } || put_back "health $c1 / the PCs page $c2"
A="$( cd /tmp && timeout 60 "$APY" -B -c "
import importlib.util, sys
s = importlib.util.spec_from_file_location('sn_after', '$SN'); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
h = m.section()
assert h.count('<div class=now>') == 3 and h.count('Notes checked') == len(m.CARDS) == 5
print('AFTER OK -- the placed notes render, %d characters' % len(h))
" 2>&1 )"
echo "$A" | grep -q "^AFTER OK" || { echo "$A" | tail -3; put_back "the placed notes do not render as they must"; }
echo "    active · health $c1 · the PCs page without a login $c2 · $A"

echo "[7] what you will see"
echo "    Your Clinic PCs page: the server, CyberPanel and website cards show a 'Now' box read from the server every"
echo "    time you open it -- the disk, how long it has run, last night's jobs, this morning's certificate check."
echo "[8] pins"
echo "    $(md5sum "$SN")"
echo "DONE."
