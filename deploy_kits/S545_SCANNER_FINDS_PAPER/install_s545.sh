#!/bin/bash
# install_s545.sh -- S545_SCANNER_FINDS_PAPER (F-890): the smart scanner finds the bill when a hand holds it or it touches
# the photo's edge, and a sideways bill is saved upright. One file: /root/assetapp/scanner_widget.js (shared by seven
# surfaces; every change sits inside the S523 smart-path block that only the scan app's intake switches on).
# BUILD_NORM_v1 s3 order: gates -> pin -> rebuild -> walk + control -> backup -> place -> health (the app serves the file
#                         from disk with an mtime version, so no restart) -> words -> undo. No database change.
# Run as root on the VPS: bash /root/deploy/repo/deploy_kits/S545_SCANNER_FINDS_PAPER/install_s545.sh
set -u
KIT="S545_SCANNER_FINDS_PAPER"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S545_APP_DIR:-/root/assetapp}"
BASEURL="${S545_BASE_URL:-http://127.0.0.1:8030}"
PY="${S545_PYTHON:-python3}"
F="scanner_widget.js"
FROM="65127fcb7c9c00ded03190c5156c7f6e"
TO="$(tr -d ' \n' < "$HERE/PIN_TO_scanner_widget.txt" 2>/dev/null)"
WORK="$(mktemp -d "${HOME:-/root}/s545_install_XXXX")" && [ -n "$WORK" ] && [ -d "$WORK" ] || { echo "REFUSED: no temporary folder"; echo "S545_SCANNER_FINDS_PAPER: NOT INSTALLED (nothing was placed)"; exit 1; }
trap 'rm -rf "$WORK"; rm -f "$APP/$F.tmp"' EXIT
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; rm -rf "$WORK"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }

log "gates"
[ -n "$TO" ] || die "PIN_TO_scanner_widget.txt missing"
[ -f "$APP/$F" ] || die "$APP/$F missing"
command -v "$PY" >/dev/null || die "no $PY"
for k in make_s545.py s545_block.js walk_box_s545.py; do [ -f "$HERE/$k" ] || die "kit file $k missing"; done

log "pin -- the live bytes must be the ones this kit was built on"
L="$(md5 "$APP/$F")"
if [ "$L" = "$TO" ]; then echo "$KIT: ALREADY INSTALLED ($F at the kit's pin ${TO:0:8})"; rm -rf "$WORK"; exit 0; fi
[ "$L" = "$FROM" ] || die "$F is ${L:0:8}, not the pinned ${FROM:0:8} -- another kit moved it; rebuild S545 on the new bytes"
echo "    $F ${L:0:8} ok"

log "rebuild on the box, from the live bytes"
cp "$APP/$F" "$WORK/live.js"
"$PY" "$HERE/make_s545.py" "$WORK/live.js" "$HERE/s545_block.js" "$WORK/built.js" >/dev/null || die "the builder refused"
B="$(md5 "$WORK/built.js")"; [ "$B" = "$TO" ] || die "the rebuilt file is ${B:0:8}, the kit says ${TO:0:8}"
echo "    rebuilt ${B:0:8} = the kit's pin"
if command -v node >/dev/null; then node --check "$WORK/built.js" || die "the built file is not valid JavaScript"; echo "    node --check: valid"; fi

log "walk on the built file -- and the control on the live file (must go red)"
"$PY" "$HERE/walk_box_s545.py" "$WORK/built.js" > "$WORK/walk.txt" 2>&1 || { cat "$WORK/walk.txt"; die "the walk is RED on the built file"; }
tail -1 "$WORK/walk.txt" | sed 's/^/    walk: /'
"$PY" "$HERE/walk_box_s545.py" "$WORK/live.js" --expect-red > "$WORK/control.txt" 2>&1 || { cat "$WORK/control.txt"; die "the NEGATIVE CONTROL did not go red on the live file"; }
tail -1 "$WORK/control.txt" | sed 's/^/    control (live file, must be red): /'
echo "    the browser walk (made-up photos, the seven surfaces, OpenCV 4.10.0): walk/walk_results.txt in this kit"

log "backup beside the live file"
cp -p "$APP/$F" "$APP/$F.bak_S545_${FROM:0:8}" || die "backup failed"
echo "    $F.bak_S545_${FROM:0:8}"

restore(){
  echo "RESTORING $F from its backup"
  cp -p "$APP/$F.bak_S545_${FROM:0:8}" "$APP/$F.tmp" && mv -f "$APP/$F.tmp" "$APP/$F"
  if [ "$(md5 "$APP/$F")" != "$FROM" ]; then echo "RESTORE FAILED -- run the UNDO line in the README"; exit 2; fi
  echo "$KIT: NOT INSTALLED (restored; $F is back at ${FROM:0:8})"; rm -rf "$WORK"; exit 1
}

log "place"
if ! { cp "$WORK/built.js" "$APP/$F.tmp" && mv -f "$APP/$F.tmp" "$APP/$F"; }; then rm -f "$APP/$F.tmp"; [ "$(md5 "$APP/$F")" = "$FROM" ] || restore; die "could not place $F"; fi
[ "$(md5 "$APP/$F")" = "$TO" ] || restore
echo "    placed at the kit's pin"

log "health -- the app and the file it serves"
sleep 2
HC="$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$BASEURL/healthz" || echo 000)"
[ "$HC" = "200" ] || { echo "    healthz answered $HC"; restore; }
WC="$(curl -s --max-time 20 "$BASEURL/scan/widget.js" | grep -c 'S545.1' || true)"
[ "${WC:-0}" != "0" ] || { echo "    the served widget does not carry S545.1"; restore; }
echo "    healthz 200 . the served widget carries S545.1"
rm -rf "$WORK"
echo
echo "$KIT: DONE."
echo "  PIN (read back): $F $(md5 "$APP/$F")"
echo "  WHAT STAFF SEE: nothing new to tap. When a bill is held in the hand, touches the photo's edge or lies on a light table,"
echo "  the green outline now finds the paper and the page is cut to it; a wide bill photographed with the phone upright is"
echo "  saved the right way up. Each phone picks it up the next time it opens the intake page."
echo "  The finance app's five scan screens and the asset page: unchanged (the smart path is the intake's alone)."
echo "  UNDO (one line): cp -p $APP/$F.bak_S545_${FROM:0:8} $APP/$F"
exit 0
