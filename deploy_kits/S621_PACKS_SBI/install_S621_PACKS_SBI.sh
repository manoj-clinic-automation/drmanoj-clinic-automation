#!/bin/bash
# =============================================================================
#  install_S621_PACKS_SBI.sh · kit S621 (session S336, 22-Oct-2026, D754)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S621_PACKS_SBI/install_S621_PACKS_SBI.sh
#  DRY=1 before bash: pins, rebuild, walk and control only -- nothing changed.   --undo: the S568 files back.
#
#  THE OWNER, 22-Oct-2026 08:09 IST: the SBI papers -- three savings (his, Dr Bhawna's, the HUF), two loans, two PPF -- are
#  downloaded by hand, password-locked, badly named; "I need the system to check these, incorporate these, and make a
#  provision for these in future packs." Two files: /root/finance/packs.py and packs.html; clinic-finance restarted.
#  The seven SBI cells appear on the shelf at the first page load (the table is created by the page, as for every account).
# =============================================================================
set -u
KIT="S621_PACKS_SBI"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"                       # the finance app's own interpreter
VPY="${VPY:-/root/wa/venv/bin/python3}"              # pypdf lives here only (the shelf's unlock step)
FIN="${FIN:-/root/finance}"
PY="$FIN/packs.py"
HT="$FIN/packs.html"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-/root/s621_backup}"
FIN_PORT="${FIN_PORT:-8106}"
SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
FROM_PY="e46264b85f22563f3e0d8643597e1d58"
FROM_HT="499069693a21de84fbad09d427a5fb0c"
W=/tmp/s621_walk
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
NEW_PY=$(m5 packs.py); NEW_HT=$(m5 packs.html)

if [ "${1:-}" = "--undo" ]; then
  echo "[undo]"
  b=$(ls -1t "$BK"/packs.py.bak_S621_* 2>/dev/null | head -1); [ -n "$b" ] && \cp -fp "$b" "$PY" && echo "    packs.py put back ($(m5 "$PY" | cut -c1-8))"
  b=$(ls -1t "$BK"/packs.html.bak_S621_* 2>/dev/null | head -1); [ -n "$b" ] && \cp -fp "$b" "$HT" && echo "    packs.html put back ($(m5 "$HT" | cut -c1-8))"
  # the old file reads every row of the slot table: the seven SBI cells go too, their files back to 'not placed' (kept)
  "$APY" -B -c "
import sqlite3
c = sqlite3.connect('$DB', timeout=60)
ids = [r[0] for r in c.execute(\"SELECT id FROM stmt_slot WHERE bank='SBI' AND key LIKE 'sbi_%'\")]
for i in ids:
    c.execute('UPDATE stmt_file SET slot_id=NULL WHERE slot_id=?', (i,))
    c.execute('DELETE FROM stmt_slot WHERE id=?', (i,))
c.commit()
print('    the %d SBI cells taken off the shelf (their files kept, not placed)' % len(ids))
" || echo "    !! the SBI cells could not be taken off -- send a photo of this screen to Claude"
  "$SYSTEMCTL" restart "$SVC" || true
  echo "    finance health: $(up)"
  echo "UNDONE."; exit 0
fi

echo "[1] pins"
NOW_PY=$(m5 "$PY"); NOW_HT=$(m5 "$HT")
if [ "$NOW_PY" = "$NEW_PY" ] && [ "$NOW_HT" = "$NEW_HT" ]; then echo "    ALREADY INSTALLED (packs.py ${NEW_PY:0:8}, packs.html ${NEW_HT:0:8})"; exit 0; fi
[ "$NOW_PY" = "$FROM_PY" ] || stop "packs.py is ${NOW_PY:0:8}, not the file ${FROM_PY:0:8} this kit was built on"
[ "$NOW_HT" = "$FROM_HT" ] || stop "packs.html is ${NOW_HT:0:8}, not the file ${FROM_HT:0:8} this kit was built on"
echo "    packs.py ${FROM_PY:0:8} · packs.html ${FROM_HT:0:8}"
[ -x "$VPY" ] && "$VPY" -c "import pypdf" 2>/dev/null || stop "the venv python ($VPY) cannot import pypdf"

echo "[2] rebuild from the live bytes"
rm -rf "$W"; mkdir -p "$W"; chmod 700 "$W"
PYTHONPYCACHEPREFIX="$W/pyc" "$APY" -m py_compile edits_s621.py walk_s621.py packs.py || stop "the kit's code does not compile on $APY"
"$APY" -B edits_s621.py py "$PY" "$W/rb.py" "$KDIR/packs.py" || stop "packs.py is not exactly the live file plus this kit's edits"
"$APY" -B edits_s621.py html "$HT" "$W/rb.html" "$KDIR/packs.html" || stop "packs.html is not exactly the live file plus this kit's edits"

echo "[3] the walk (made-up statements; then a scratch copy of the live database) and the control"
mkdir -p "$W/old" "$W/new"
find "$FIN" -maxdepth 1 -type f \( -name '*.py' -o -name '*.html' -o -name '*.json' -o -name '*.sql' \) -exec \cp -p {} "$W/old/" \;
\cp -p "$W/old/"* "$W/new/" && \cp -p "$KDIR/packs.py" "$KDIR/packs.html" "$W/new/" || stop "could not lay out the walk's folders"
( cd "$W" && WALK_VPY="$VPY" timeout 300 "$APY" -B "$KDIR/walk_s621.py" "$W/old" "$W/new" --live-db "$DB" > "$W/walk.txt" 2>&1 )
WK=$?; sed -n '/^\[B\]/,$p' "$W/walk.txt" | grep "^  ok" | sed 's/^ *ok */    /'; tail -1 "$W/walk.txt" | sed 's/^/    walk: /'
[ "$WK" = 0 ] || { grep "FAIL\|RED\|Error" "$W/walk.txt" | head -8; stop "the walk is not green"; }
( cd "$W" && WALK_VPY="$VPY" timeout 300 "$APY" -B "$KDIR/walk_s621.py" "$W/old" "$W/old" > "$W/ctl.txt" 2>&1 )
[ $? != 0 ] && echo "    control on the live files: RED, as it must be" || stop "the control did not go red -- the walk cannot tell old from new"
if [ "${DRY:-0}" = "1" ]; then echo "-- DRY RUN: nothing changed"; exit 0; fi

echo "[4] backup -> $BK"
mkdir -p "$BK"; chmod 700 "$BK"
\cp -fp "$PY" "$BK/packs.py.bak_S621_${FROM_PY:0:8}" && \cp -fp "$HT" "$BK/packs.html.bak_S621_${FROM_HT:0:8}" || stop "the backup failed"
put_back() {
  \cp -fp "$BK/packs.py.bak_S621_${FROM_PY:0:8}" "$PY"; \cp -fp "$BK/packs.html.bak_S621_${FROM_HT:0:8}" "$HT"
  "$SYSTEMCTL" restart "$SVC" || true
  stop "$1" "The old files were put back and $SVC restarted (health $(up))."
}

echo "[5] placed"
\cp -p "$KDIR/packs.html" "$HT.s621" && chmod --reference="$BK/packs.html.bak_S621_${FROM_HT:0:8}" "$HT.s621" && mv -f "$HT.s621" "$HT" || put_back "placing packs.html"
\cp -p "$KDIR/packs.py" "$PY.s621" && chmod --reference="$BK/packs.py.bak_S621_${FROM_PY:0:8}" "$PY.s621" && mv -f "$PY.s621" "$PY" || put_back "placing packs.py"
[ "$(m5 "$PY")" = "$NEW_PY" ] && [ "$(m5 "$HT")" = "$NEW_HT" ] || put_back "the files did not land byte-exact"
echo "    packs.py ${FROM_PY:0:8} -> ${NEW_PY:0:8} · packs.html ${FROM_HT:0:8} -> ${NEW_HT:0:8}"

echo "[6] $SVC restarted and checked"
"$SYSTEMCTL" restart "$SVC" || put_back "restart $SVC"
c1=$(up)
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/packs")
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' -X POST "http://127.0.0.1:$FIN_PORT/finance/packs/api/upload")
"$SYSTEMCTL" is-active --quiet "$SVC" || put_back "$SVC is not active"
ok_gate() { case "$1" in 302|303|401|403) return 0;; *) return 1;; esac; }
{ [ "$c1" = 200 ] && ok_gate "$c2" && ok_gate "$c3"; } || put_back "health $c1 / the packs page $c2 / the upload door $c3 without a login"
A="$( cd /tmp && timeout 60 "$APY" -B -c "
import importlib.util
s = importlib.util.spec_from_file_location('pk_after', '$PY'); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
n = sum(1 for x in m.SLOTS if x[1] == 'SBI')
assert n == 7 and len(m.SLOT_EVERY) == 7 and m.MANUAL_BANKS == ('SBI',)
print('AFTER OK -- the placed packs carry %d SBI accounts' % n)
" 2>&1 )"
echo "$A" | grep -q "^AFTER OK" || { echo "$A" | tail -3; put_back "the placed packs do not load as they must"; }
echo "    active · health $c1 · without a login: the packs page $c2, the upload door $c3 · $A"

echo "[7] what you will see"
echo "    The packs page has 'Add statements' near the top: pick the SBI PDFs you downloaded, any name. The Statement"
echo "    passwords card has a box for each SBI account. The September pack asks for the seven SBI statements"
echo "    (savings and loans July-September; PPF April-September); October's pack asks for none."
echo "[8] pins"
echo "    $(md5sum "$PY")"
echo "    $(md5sum "$HT")"
echo "DONE."
