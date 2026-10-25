#!/bin/bash
# =============================================================================
#  install_S646_PROCROOM_TILES.sh · kit S646 (25-Oct-2026, session S349, the parent) · the Scan App chat's ask, relayed by the owner
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s646kit && cp -rp /root/deploy/repo/deploy_kits/S646_PROCROOM_TILES /tmp/s646kit && bash /tmp/s646kit/install_S646_PROCROOM_TILES.sh
#  (DRY=1 before bash: every gate and the walk, nothing written.)
#
#  /root/portal/portal.py         6470f894 -> 844166b1  3 counted edits: 'Kal ke procedures' and 'Procedure room' tiles, their groups, the face
#  /root/portal/tile_grants.json  11385907 -> 025f8ab9  v38 -> v39: 'Kal ke procedures' to shavez by name; both masked for bhawna
#  No data step. Restarts clinic-portal. Red after placing: both files back byte-identically, restart.
#  Undo:  for f in portal.py tile_grants.json; do \cp -p /root/portal/$f.bak_S646 /root/portal/$f; done; systemctl restart clinic-portal
# =============================================================================
set -u
KIT="S646_PROCROOM_TILES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-}"
if [ -z "$PY" ]; then for c in /usr/bin/python3 /root/wa/venv/bin/python3; do "$c" -c "import flask" 2>/dev/null && { PY="$c"; break; }; done; fi
POR="${POR:-/root/portal}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
PSVC="${PSVC:-clinic-portal}"; PPORT="${PPORT:-8099}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="portal.py tile_grants.json"
declare -A FROM=( [portal.py]=6470f8944f8ad3a313816139b9bc263b [tile_grants.json]=1138590794786d4b24ad90055f82bc06 )
declare -A TO=( [portal.py]=844166b11f6d62ece43b42fde8e11094 [tile_grants.json]=025f8ab9a2691023148ccc6deeac4f50 )
HAVE_LOCK=0; SN=""; SO=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; [ -n "$SN" ] && rm -rf "$SN" "$SO"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
phealth() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PPORT/portal/health"; }
restore() { for n in $NAMES; do \cp -p "$POR/$n.bak_S646" "$POR/$n"; done; }

echo "== $KIT =="
[ -n "$PY" ] || stop "no python with flask found (the walk loads the portal code)"
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
echo "1. kit files: all match SUMS.md5"
all_to=1
for n in $NAMES; do [ "$(m5 "$KDIR/$n")" = "${TO[$n]}" ] || stop "the kit's $n is not the built file"; [ "$(m5 "$POR/$n")" = "${TO[$n]}" ] || all_to=0; done
[ "$all_to" = 1 ] && { echo "ALREADY INSTALLED."; exit 0; }
for n in $NAMES; do L=$(m5 "$POR/$n"); [ "$L" = "${FROM[$n]}" ] || stop "the live $POR/$n changed since this kit was built (live ${L:0:8}, kit expects ${FROM[$n]:0:8})"; done
echo "2. the two live files are the ones this kit was built from"
SN=$(mktemp -d /tmp/s646new.XXXX); SO=$(mktemp -d /tmp/s646old.XXXX)
for n in $NAMES; do \cp "$KDIR/$n" "$SN/$n"; \cp "$POR/$n" "$SO/$n"; done
"$PY" -W ignore::SyntaxWarning -B -m py_compile "$SN/portal.py" || stop "portal.py does not compile with $PY"
"$PY" -c "import json,sys; json.load(open(sys.argv[1]))" "$SN/tile_grants.json" || stop "tile_grants.json is not valid JSON"
R=$(cd /tmp && "$PY" -B "$KDIR/walk_s646.py" "$SN" "$POR" 2>&1 | tail -1); case "$R" in "10 of 10 green") echo "3. walk: $R";; *) (cd /tmp && "$PY" -B "$KDIR/walk_s646.py" "$SN" "$POR" 2>&1 | grep -E 'RED|Error'); stop "the walk is not green ($R)";; esac
R=$(cd /tmp && "$PY" -B "$KDIR/walk_s646.py" "$SO" "$POR" --old 2>&1 | tail -1); case "$R" in "6 S646 check(s) red · 0 older red · 4 green") echo "   control on the live files: $R";; *) echo "$R"; stop "the control on the live files is not as expected";; esac
[ "$(phealth)" = 200 ] || stop "the portal is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
for n in $NAMES; do \cp -p "$POR/$n" "$POR/$n.bak_S646" || stop "could not keep a backup of $n"; done
for n in $NAMES; do \cp "$KDIR/$n" "$POR/$n" && chmod --reference="$POR/$n.bak_S646" "$POR/$n" 2>/dev/null; done
for n in $NAMES; do [ "$(m5 "$POR/$n")" = "${TO[$n]}" ] || { restore; stop "read-back of $n did not match; the old files are back"; }; done
echo "4. placed the two files (backups *.bak_S646)"
"$SYSTEMCTL" restart "$PSVC"
p=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; p=$(phealth); [ "$p" = 200 ] && break; done
R=$(cd /tmp && "$PY" -B "$KDIR/walk_s646.py" "$POR" "$SO" 2>&1 | tail -1)
if [ "$p" != 200 ] || [ "$R" != "10 of 10 green" ]; then
  echo "!! RED after placing (portal $p; walk on the placed files: $R) - putting the old files back"
  restore; "$SYSTEMCTL" restart "$PSVC"
  ok=1; for n in $NAMES; do [ "$(m5 "$POR/$n")" = "${FROM[$n]}" ] || ok=0; done
  [ "$ok" = 1 ] && echo "   the old files are back" || echo "   !! a restored file does not match -- copy the .bak_S646 files back by hand"
  p2=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; p2=$(phealth); [ "$p2" = 200 ] && break; done
  echo "   after the restore: portal $p2. Send a photo of this screen to Claude."; exit 1
fi
echo "5. $PSVC restarted and healthy; the walk on the placed files: $R"
echo ""
echo "INSTALLED. Shavez: 'Kal ke procedures' under Patients. Yours: 'Procedure room' under Assets & papers."
