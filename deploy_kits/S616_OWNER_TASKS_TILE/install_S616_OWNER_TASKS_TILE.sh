#!/bin/bash
# =============================================================================
#  install_S616_OWNER_TASKS_TILE.sh · kit S616 (session S336, 22-Oct-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S616_OWNER_TASKS_TILE/install_S616_OWNER_TASKS_TILE.sh
#  DRY=1 before bash: pins, rebuild, walk and control only -- nothing changed.   --undo: both old files back.
#
#  THE OWNER, his board note of 06:21 IST: "we developed a messaging and tasks app and connected with voiceapp, cant see
#  it in my portal".  It is live -- his panel's Tasks and the Voicenotes lines at /finance/aaj -- but his home had no door.
#  Now a 'Tasks & messages' tile on his home (shown only to the panel's owner) with the waiting count, opening on Tasks.
#  Files: /root/portal/portal.py (clinic-portal restarted) and /root/finance/aaj_panel.html (read per request).
# =============================================================================
set -u
KIT="S616_OWNER_TASKS_TILE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
POR="${POR:-/root/portal}"
PAN="${PAN:-/root/finance/aaj_panel.html}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-/root/s616_backup}"
POR_PORT="${POR_PORT:-8099}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
PO_FROM="3be15f45c7a4a8d4121b744e0bdd022a"
PA_FROM="36bd57bcda586f18183aec54c537e2e6"
W=/tmp/s616_walk
HAVE_LOCK=0
on_exit() { rm -rf "$W"; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
m5() { md5sum "$1" 2>/dev/null | cut -c1-32; }
health() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"); [ "$h" = "$2" ] && break; done; echo "$h"; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
PO_TO=$(m5 portal.py); PA_TO=$(m5 aaj_panel.html)

if [ "${1:-}" = "--undo" ]; then
  echo "[undo]"
  b=$(ls -1t "$BK"/portal.py.bak_S616_* 2>/dev/null | head -1); [ -n "$b" ] && \cp -fp "$b" "$POR/portal.py" && echo "    portal.py put back ($(m5 "$POR/portal.py" | cut -c1-8))"
  b=$(ls -1t "$BK"/aaj_panel.html.bak_S616_* 2>/dev/null | head -1); [ -n "$b" ] && \cp -fp "$b" "$PAN" && echo "    aaj_panel.html put back ($(m5 "$PAN" | cut -c1-8))"
  "$SYSTEMCTL" restart clinic-portal || true
  echo "    portal login: $(health "http://127.0.0.1:$POR_PORT/portal/login" 200)"
  echo "UNDONE."; exit 0
fi

echo "[1] pins"
if [ "$(m5 "$POR/portal.py")" = "$PO_TO" ] && [ "$(m5 "$PAN")" = "$PA_TO" ]; then echo "    ALREADY INSTALLED (portal ${PO_TO:0:8} · panel ${PA_TO:0:8})"; exit 0; fi
[ "$(m5 "$POR/portal.py")" = "$PO_FROM" ] || stop "$POR/portal.py is $(m5 "$POR/portal.py" | cut -c1-8), not the pinned ${PO_FROM:0:8}"
[ "$(m5 "$PAN")" = "$PA_FROM" ] || stop "$PAN is $(m5 "$PAN" | cut -c1-8), not the pinned ${PA_FROM:0:8}"
echo "    portal.py ${PO_FROM:0:8} · aaj_panel.html ${PA_FROM:0:8}"

echo "[2] rebuild from the live bytes"
rm -rf "$W"; mkdir -p "$W"; chmod 700 "$W"
PYTHONPYCACHEPREFIX="$W/pyc" "$VPY" -m py_compile edits_s616.py walk_s616.py || stop "the kit's code does not compile"
"$VPY" -B edits_s616.py portal "$POR/portal.py" "$W/portal.py" "$KDIR/portal.py" || stop "portal.py is not exactly the live file plus this kit's edits"
"$VPY" -B edits_s616.py panel "$PAN" "$W/aaj_panel.html" "$KDIR/aaj_panel.html" || stop "aaj_panel.html is not exactly the live file plus this kit's edits"
PYTHONPYCACHEPREFIX="$W/pyc" "$VPY" -W ignore -m py_compile "$KDIR/portal.py" || stop "the new portal.py does not compile on $VPY"

echo "[3] the walk (every login's home rendered from both files, against the live tile grants) and the control"
\cp -p "$POR/tile_grants.json" "$W/grants.json"
( cd "$W" && PYTHONPATH="$POR" timeout 600 "$VPY" -B "$KDIR/walk_s616.py" "$POR/portal.py" "$KDIR/portal.py" "$W/grants.json" "$PAN" "$KDIR/aaj_panel.html" > "$W/walk.txt" 2>&1 )
WK=$?; tail -1 "$W/walk.txt" | sed 's/^/    walk: /'
[ "$WK" = 0 ] || { grep "FAIL\|RED\|Error" "$W/walk.txt" | head -8; stop "the walk is not green"; }
( cd "$W" && PYTHONPATH="$POR" timeout 600 "$VPY" -B "$KDIR/walk_s616.py" "$POR/portal.py" "$POR/portal.py" "$W/grants.json" "$PAN" "$PAN" > "$W/ctl.txt" 2>&1 )
[ $? != 0 ] && echo "    control on the live files: RED, as it must be" || stop "the control did not go red -- the walk cannot tell old from new"
if [ "${DRY:-0}" = "1" ]; then echo "-- DRY RUN: nothing changed"; exit 0; fi

echo "[4] backups -> $BK"
mkdir -p "$BK"; chmod 700 "$BK"
\cp -fp "$POR/portal.py" "$BK/portal.py.bak_S616_${PO_FROM:0:8}" && \cp -fp "$PAN" "$BK/aaj_panel.html.bak_S616_${PA_FROM:0:8}" || stop "a backup failed"
put_back() {
  \cp -fp "$BK/portal.py.bak_S616_${PO_FROM:0:8}" "$POR/portal.py"; \cp -fp "$BK/aaj_panel.html.bak_S616_${PA_FROM:0:8}" "$PAN"
  "$SYSTEMCTL" restart clinic-portal || true
  stop "$1" "Both old files were put back and the portal restarted (login $(health "http://127.0.0.1:$POR_PORT/portal/login" 200))."
}

echo "[5] placed"
\cp -p "$KDIR/aaj_panel.html" "$PAN.s616" && chmod --reference="$BK/aaj_panel.html.bak_S616_${PA_FROM:0:8}" "$PAN.s616" && mv -f "$PAN.s616" "$PAN" || put_back "placing aaj_panel.html"
\cp -p "$KDIR/portal.py" "$POR/.portal.py.s616" && mv -f "$POR/.portal.py.s616" "$POR/portal.py" || put_back "placing portal.py"
[ "$(m5 "$POR/portal.py")" = "$PO_TO" ] && [ "$(m5 "$PAN")" = "$PA_TO" ] || put_back "a file did not land byte-exact"
echo "    portal.py ${PO_FROM:0:8} -> ${PO_TO:0:8} · aaj_panel.html ${PA_FROM:0:8} -> ${PA_TO:0:8}"

echo "[6] clinic-portal restarted and checked"
"$SYSTEMCTL" restart clinic-portal || put_back "restart clinic-portal"
c2=$(health "http://127.0.0.1:$POR_PORT/portal/login" 200)
"$SYSTEMCTL" is-active --quiet clinic-portal || put_back "clinic-portal is not active"
[ "$c2" = 200 ] || put_back "the portal login answers $c2"
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$POR_PORT/portal/")
case "$c3" in 200|302) ;; *) put_back "the home page answers $c3";; esac
echo "    active · login $c2 · home $c3"

echo "[7] what you will see"
echo "    Your portal home: a blue 'Tasks & messages' tile under Today -- how many Voicenotes lines wait, tasks open and"
echo "    answered. It opens your panel on Tasks. Dr Bhawna's and the staff's screens are unchanged."
echo "[8] pins"
echo "    $(md5sum "$POR/portal.py")"
echo "    $(md5sum "$PAN")"
echo "DONE."
