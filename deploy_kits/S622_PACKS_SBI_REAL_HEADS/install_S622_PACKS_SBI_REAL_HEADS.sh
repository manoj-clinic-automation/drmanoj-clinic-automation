#!/bin/bash
# =============================================================================
#  install_S622_PACKS_SBI_REAL_HEADS.sh · kit S622 (session S336, 22-Oct-2026, D755, F-975)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S622_PACKS_SBI_REAL_HEADS/install_S622_PACKS_SBI_REAL_HEADS.sh
#  DRY=1 before bash: pins, rebuild, walks and control only -- nothing changed.   --undo: the S621 files back.
#
#  FOUND ON THE LIVE SHELF at 09:18 IST: the owner's four 20-Oct SBI PDFs opened, but his savings and loan stayed unplaced and
#  Dr Bhawna's loan had no period. SBI prints the holder left of 'State Bank of India' (MANOJ KUMARAGARWAL, no space) and the
#  loan period after 'Statement :'. The reader now takes both; the SBI files are re-read once; a locked file added by hand gets a
#  jump to its password box. Two files: /root/finance/packs.py and packs.html; clinic-finance restarted.
# =============================================================================
set -u
KIT="S622_PACKS_SBI_REAL_HEADS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"                       # the finance app's own interpreter
VPY="${VPY:-/root/wa/venv/bin/python3}"              # pypdf lives here only (the shelf's unlock step)
FIN="${FIN:-/root/finance}"
PY="$FIN/packs.py"
HT="$FIN/packs.html"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-/root/s622_backup}"
FIN_PORT="${FIN_PORT:-8106}"
SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
FROM_PY="6ed8e18a9bad1676ca4156743182b6e5"
FROM_HT="da0cbb8c1a57af581e01d71fce56c98d"
W=/tmp/s622_walk
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
  b=$(ls -1t "$BK"/packs.py.bak_S622_* 2>/dev/null | head -1); [ -n "$b" ] && \cp -fp "$b" "$PY" && echo "    packs.py put back ($(m5 "$PY" | cut -c1-8))"
  b=$(ls -1t "$BK"/packs.html.bak_S622_* 2>/dev/null | head -1); [ -n "$b" ] && \cp -fp "$b" "$HT" && echo "    packs.html put back ($(m5 "$HT" | cut -c1-8))"
  "$SYSTEMCTL" restart "$SVC" || true
  echo "    finance health: $(up)"
  echo "UNDONE."; exit 0
fi

echo "[1] pins"
NOW_PY=$(m5 "$PY"); NOW_HT=$(m5 "$HT")
if [ "$NOW_PY" = "$NEW_PY" ] && [ "$NOW_HT" = "$NEW_HT" ]; then echo "    ALREADY INSTALLED (packs.py ${NEW_PY:0:8}, packs.html ${NEW_HT:0:8})"; exit 0; fi
[ "$NOW_PY" = "$FROM_PY" ] || stop "packs.py is ${NOW_PY:0:8}, not the S621 file ${FROM_PY:0:8} this kit was built on"
[ "$NOW_HT" = "$FROM_HT" ] || stop "packs.html is ${NOW_HT:0:8}, not the S621 file ${FROM_HT:0:8} this kit was built on"
echo "    packs.py ${FROM_PY:0:8} · packs.html ${FROM_HT:0:8}"
[ -x "$VPY" ] && "$VPY" -c "import pypdf" 2>/dev/null || stop "the venv python ($VPY) cannot import pypdf"

echo "[2] rebuild from the live bytes"
rm -rf "$W"; mkdir -p "$W"; chmod 700 "$W"
PYTHONPYCACHEPREFIX="$W/pyc" "$APY" -m py_compile edits_s622.py walk_s622.py walk_s621.py packs.py || stop "the kit's code does not compile on $APY"
"$APY" -B edits_s622.py py "$PY" "$W/rb.py" "$KDIR/packs.py" || stop "packs.py is not exactly the live file plus this kit's edits"
"$APY" -B edits_s622.py html "$HT" "$W/rb.html" "$KDIR/packs.html" || stop "packs.html is not exactly the live file plus this kit's edits"

echo "[3] the walks (made-up statements; then a scratch copy of the live database) and the control"
mkdir -p "$W/old" "$W/new"
find "$FIN" -maxdepth 1 -type f \( -name '*.py' -o -name '*.html' -o -name '*.json' -o -name '*.sql' \) -exec \cp -p {} "$W/old/" \;
\cp -p "$W/old/"* "$W/new/" && \cp -p "$KDIR/packs.py" "$KDIR/packs.html" "$W/new/" || stop "could not lay out the walk's folders"
( cd "$W" && WALK_VPY="$VPY" timeout 300 "$APY" -B "$KDIR/walk_s622.py" "$W/old" "$W/new" --live-db "$DB" > "$W/walk.txt" 2>&1 )
WK=$?; sed -n '/^\[B\]/,$p' "$W/walk.txt" | grep "^  ok\|^    SBI" | sed 's/^ *ok */    /;s/^    SBI/    SBI/'; tail -1 "$W/walk.txt" | sed 's/^/    walk: /'
[ "$WK" = 0 ] || { grep "FAIL\|RED\|Error" "$W/walk.txt" | head -8; stop "the walk is not green"; }
( cd "$W" && WALK_VPY="$VPY" timeout 300 "$APY" -B "$KDIR/walk_s621.py" "$W/new" "$W/new" > "$W/w621.txt" 2>&1 )
[ $? = 0 ] && echo "    S621's own walk on the new files: $(tail -1 "$W/w621.txt")" || { grep FAIL "$W/w621.txt" | head -5; stop "S621's walk is not green on the new files"; }
( cd "$W" && WALK_VPY="$VPY" timeout 300 "$APY" -B "$KDIR/walk_s622.py" "$W/old" "$W/old" > "$W/ctl.txt" 2>&1 )
[ $? != 0 ] && echo "    control on the live files: RED, as it must be" || stop "the control did not go red -- the walk cannot tell old from new"
if [ "${DRY:-0}" = "1" ]; then echo "-- DRY RUN: nothing changed"; exit 0; fi

echo "[4] backup -> $BK"
mkdir -p "$BK"; chmod 700 "$BK"
\cp -fp "$PY" "$BK/packs.py.bak_S622_${FROM_PY:0:8}" && \cp -fp "$HT" "$BK/packs.html.bak_S622_${FROM_HT:0:8}" || stop "the backup failed"
put_back() {
  \cp -fp "$BK/packs.py.bak_S622_${FROM_PY:0:8}" "$PY"; \cp -fp "$BK/packs.html.bak_S622_${FROM_HT:0:8}" "$HT"
  "$SYSTEMCTL" restart "$SVC" || true
  stop "$1" "The old files were put back and $SVC restarted (health $(up))."
}

echo "[5] placed"
\cp -p "$KDIR/packs.html" "$HT.s622" && chmod --reference="$BK/packs.html.bak_S622_${FROM_HT:0:8}" "$HT.s622" && mv -f "$HT.s622" "$HT" || put_back "placing packs.html"
\cp -p "$KDIR/packs.py" "$PY.s622" && chmod --reference="$BK/packs.py.bak_S622_${FROM_PY:0:8}" "$PY.s622" && mv -f "$PY.s622" "$PY" || put_back "placing packs.py"
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
h = m.sbi_ident('  MANOJ KUMARAGARWAL      State Bank of India\n  Statement  : 01-04-2026 to 20-10-2026', 'MANOJ KUMARAGARWAL      State Bank of India  Auto Loan')
assert h['holder'] == 'MANOJ KUMAR AGARWAL' and h['kind'] == 'loan' and h['period_to'] == '2026-10-20', h
print('AFTER OK -- the placed packs read the real SBI head')
" 2>&1 )"
echo "$A" | grep -q "^AFTER OK" || { echo "$A" | tail -3; put_back "the placed packs do not load as they must"; }
echo "    active · health $c1 · without a login: the packs page $c2, the upload door $c3 · $A"

echo "[6b] the SBI files on the shelf read once more, as the 're-read the shelf' button does"
R="$( cd "$FIN" && STMT_VENV_PYTHON="$VPY" timeout 240 "$APY" -B -c "
import sqlite3, packs
c = sqlite3.connect('$DB', timeout=60)
n = c.execute(\"UPDATE stmt_file SET read_status=NULL WHERE folder='bank' AND bank='SBI' AND (slot_id IS NULL OR period_to IS NULL)\").rowcount
c.commit(); c.close()
r = packs.process_inbox()
c = sqlite3.connect('file:$DB?mode=ro', uri=True)
rows = c.execute(\"SELECT f.name, COALESCE(s.holder_label,''), COALESCE(f.period_from,''), COALESCE(f.period_to,'') FROM stmt_file f LEFT JOIN stmt_slot s ON s.id=f.slot_id WHERE f.folder='bank' AND f.bank='SBI' ORDER BY f.id\").fetchall()
print('    %d SBI file(s) sent back to the reader; the shelf pass: placed %s, unplaced %s' % (n, r.get('placed'), r.get('unplaced')))
for nm, acc, a, b in rows:
    print('    %s -> %s %s' % (nm, acc or 'NOT PLACED', ('%s to %s' % (a, b)) if b else '(no period)'))
" 2>&1 )"
echo "$R" | tail -12

echo "[7] what you will see"
echo "    The packs page: your SBI statements on their own accounts with their periods. A locked file you add has a"
echo "    'Go to its password box' button beside it."
echo "[8] pins"
echo "    $(md5sum "$PY")"
echo "    $(md5sum "$HT")"
echo "DONE."
