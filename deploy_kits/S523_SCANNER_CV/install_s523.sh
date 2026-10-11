#!/bin/bash
# install_s523.sh -- S523_SCANNER_CV: the smart outline (OpenCV.js) for the bill intake, installed SWITCHED OFF.
# BUILD_NORM_v1 s3 order: gates -> pins -> rebuild -> walk + control -> backups -> place -> restart (assetapp only)
#                         -> health -> data step (none) -> the owner's words -> the undo line.
# Run as root on the VPS: bash /root/deploy/repo/deploy_kits/S523_SCANNER_CV/install_s523.sh
# Rehearsal on a made-up root: S523_APP_DIR=... S523_RESTART_CMD=... S523_HEALTH_URL=... bash install_s523.sh
set -u
KIT="S523_SCANNER_CV"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S523_APP_DIR:-/root/assetapp}"
SERVICE="${S523_SERVICE:-assetapp}"
HEALTH="${S523_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
LIB_URL="${S523_LIB_URL:-https://registry.npmjs.org/@techstark/opencv-js/-/opencv-js-4.10.0-release.1.tgz}"
PY="${S523_PYTHON:-python3}"                       # the scan app's own service runs the system python3 (F-53)
RESTART="${S523_RESTART_CMD:-systemctl restart $SERVICE}"   # the rehearsal hands in its own
FROM_W="e2bca60222f043c225dfa57bce565522"; FROM_A="e774be89193472dfa4b142d85bdcc46c"
TO_W="$(cat "$HERE/PIN_TO_widget.txt" 2>/dev/null | tr -d ' \n')"; TO_A="$(cat "$HERE/PIN_TO_app.txt" 2>/dev/null | tr -d ' \n')"
LIB_MD5="ff1e10e731d08f505fc51eb0271c6c85"             # opencv.js 4.10.0 (dist/opencv.js of @techstark/opencv-js 4.10.0-release.1)
LIB_MD5_SHORT="ff1e10e7"
WORK="$(mktemp -d "${HOME:-/root}/s523_install_XXXX")"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; rm -rf "$WORK"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }

log "gates"
[ -n "$TO_W" ] && [ -n "$TO_A" ] || die "the kit's PIN_TO files are missing"
[ -d "$APP" ] || die "$APP is not a folder"
[ -f "$APP/asset_register.py" ] && [ -f "$APP/scanner_widget.js" ] || die "the two live files are not in $APP"
command -v "$PY" >/dev/null || die "no $PY"
"$PY" -c "import flask" 2>/dev/null || die "$PY has no flask (the scan app runs on the system python3, F-53)"
for f in make_s523.py s523_block.js walk_box_s523.py; do [ -f "$HERE/$f" ] || die "kit file $f missing"; done
ls "$APP"/*.lock 2>/dev/null | grep -q . && die "a lock file sits in $APP"

log "pins -- the live bytes must be the ones this kit was built on"
LW="$(md5 "$APP/scanner_widget.js")"; LA="$(md5 "$APP/asset_register.py")"
if [ "$LW" = "$TO_W" ] && [ "$LA" = "$TO_A" ] && [ -f "$APP/static/opencv.js" ]; then
  echo "$KIT: ALREADY INSTALLED (scanner_widget.js ${TO_W:0:8}, asset_register.py ${TO_A:0:8}, static/opencv.js present)"; rm -rf "$WORK"; exit 0
fi
[ "$LW" = "$FROM_W" ] || die "scanner_widget.js is ${LW:0:8}, not the pinned ${FROM_W:0:8} -- another kit moved it; rebuild S523 on the new bytes"
[ "$LA" = "$FROM_A" ] || die "asset_register.py is ${LA:0:8}, not the pinned ${FROM_A:0:8} -- another kit moved it; rebuild S523 on the new bytes"
echo "    scanner_widget.js ${LW:0:8} ok . asset_register.py ${LA:0:8} ok"

log "the library -- the kit's own copy if present, else the pinned package from the npm registry"
mkdir -p "$WORK/lib"
if [ -f "$HERE/opencv.js" ]; then cp "$HERE/opencv.js" "$WORK/lib/opencv.js"; echo "    from the kit folder"
else
  curl -fsSL --max-time 300 -o "$WORK/lib/pkg.tgz" "$LIB_URL" || die "the library could not be downloaded (no network from the box?)"
  tar xzf "$WORK/lib/pkg.tgz" -C "$WORK/lib" || die "the package did not unpack"
  cp "$WORK/lib/package/dist/opencv.js" "$WORK/lib/opencv.js" || die "dist/opencv.js not in the package"
  echo "    downloaded $(stat -c %s "$WORK/lib/pkg.tgz") bytes"
fi
LM="$(md5 "$WORK/lib/opencv.js")"
[ "$LM" = "$LIB_MD5" ] || die "opencv.js is ${LM:0:8}, not the pinned ${LIB_MD5:0:8}"
gzip -9 -k -f "$WORK/lib/opencv.js" || die "gzip failed"
echo "    opencv.js ${LM:0:8} ok . $(stat -c %s "$WORK/lib/opencv.js") B, gzip $(stat -c %s "$WORK/lib/opencv.js.gz") B"

log "rebuild on the box, from the live bytes"
mkdir -p "$WORK/built" "$WORK/live_in"; cp "$APP/scanner_widget.js" "$APP/asset_register.py" "$WORK/live_in/"
cp "$HERE/make_s523.py" "$HERE/s523_block.js" "$WORK/"
"$PY" "$WORK/make_s523.py" "$WORK/live_in" "$WORK/built" || die "the builder refused"
BW="$(md5 "$WORK/built/scanner_widget.js")"; BA="$(md5 "$WORK/built/asset_register.py")"
[ "$BW" = "$TO_W" ] || die "the rebuilt scanner_widget.js is ${BW:0:8}, the kit says ${TO_W:0:8}"
[ "$BA" = "$TO_A" ] || die "the rebuilt asset_register.py is ${BA:0:8}, the kit says ${TO_A:0:8}"
"$PY" -m py_compile "$WORK/built/asset_register.py" || die "the built app does not compile"
echo "    rebuilt: scanner_widget.js ${BW:0:8} . asset_register.py ${BA:0:8} -- equal to the kit's pins"

log "walk on a copy of the live database (made under the session's home, removed after) -- and the control on the live files"
[ -f "$APP/assets.db" ] || die "no $APP/assets.db"
cp "$APP/clinic_papers.py" "$WORK/built/" 2>/dev/null || true
cp "$APP/clinic_papers.py" "$WORK/live_in/" 2>/dev/null || true
cd "$WORK" && HOME="$WORK" "$PY" "$HERE/walk_box_s523.py" "$WORK/built" "$WORK/lib/opencv.js" "$APP/assets.db" > "$WORK/walk.txt" 2>&1 || { cat "$WORK/walk.txt"; die "the walk is RED on the built files"; }
tail -1 "$WORK/walk.txt" | sed 's/^/    walk: /'
HOME="$WORK" "$PY" "$HERE/walk_box_s523.py" "$WORK/live_in" "$WORK/lib/opencv.js" "$APP/assets.db" --expect-red > "$WORK/control.txt" 2>&1 || { cat "$WORK/control.txt"; die "the NEGATIVE CONTROL did not go red on the live files -- the walk cannot tell old from new"; }
tail -1 "$WORK/control.txt" | sed 's/^/    control (live files, must be red): /'
cd "$HERE"

log "backups beside the live files"
cp -p "$APP/scanner_widget.js" "$APP/scanner_widget.js.bak_S523_${FROM_W:0:8}" || die "backup failed"
cp -p "$APP/asset_register.py" "$APP/asset_register.py.bak_S523_${FROM_A:0:8}" || die "backup failed"
echo "    scanner_widget.js.bak_S523_${FROM_W:0:8} . asset_register.py.bak_S523_${FROM_A:0:8}"

log "place"
mkdir -p "$APP/static" || die "cannot make $APP/static"
cp "$WORK/lib/opencv.js" "$APP/static/opencv.js.tmp" && mv -f "$APP/static/opencv.js.tmp" "$APP/static/opencv.js" || die "could not place opencv.js"
cp "$WORK/lib/opencv.js.gz" "$APP/static/opencv.js.gz.tmp" && mv -f "$APP/static/opencv.js.gz.tmp" "$APP/static/opencv.js.gz" || die "could not place opencv.js.gz"
cp "$WORK/built/scanner_widget.js" "$APP/scanner_widget.js.tmp" && mv -f "$APP/scanner_widget.js.tmp" "$APP/scanner_widget.js" || die "could not place the widget"
cp "$WORK/built/asset_register.py" "$APP/asset_register.py.tmp" && mv -f "$APP/asset_register.py.tmp" "$APP/asset_register.py" || die "could not place the app"
PW="$(md5 "$APP/scanner_widget.js")"; PA="$(md5 "$APP/asset_register.py")"; PL="$(md5 "$APP/static/opencv.js")"
[ "$PW" = "$TO_W" ] && [ "$PA" = "$TO_A" ] && [ "${PL:0:8}" = "$LIB_MD5_SHORT" ] || die "read-back after placing differs"
echo "    placed: scanner_widget.js ${PW:0:8} . asset_register.py ${PA:0:8} . static/opencv.js ${PL:0:8} (+ .gz)"

restore(){
  echo "RESTORING the two files from their backups"
  cp -p "$APP/scanner_widget.js.bak_S523_${FROM_W:0:8}" "$APP/scanner_widget.js"; cp -p "$APP/asset_register.py.bak_S523_${FROM_A:0:8}" "$APP/asset_register.py"
  rm -f "$APP/static/opencv.js" "$APP/static/opencv.js.gz"
  eval "$RESTART" || true
  echo "$KIT: NOT INSTALLED (restored: scanner_widget.js $(md5 "$APP/scanner_widget.js" | cut -c1-8), asset_register.py $(md5 "$APP/asset_register.py" | cut -c1-8))"
  rm -rf "$WORK"; exit 1
}

log "restart $SERVICE only, then health"
eval "$RESTART" || restore; sleep 3
HC="$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$HEALTH" || echo 000)"
[ "$HC" = "200" ] || { echo "    healthz answered $HC"; restore; }
LIBC="$(curl -s -o /dev/null -w '%{http_code} %{size_download}' -H 'Accept-Encoding: gzip' --max-time 60 "${HEALTH%/healthz}/scan/opencv.js" || echo "000 0")"
case "$LIBC" in 200\ *) ;; *) echo "    /scan/opencv.js answered $LIBC"; restore ;; esac
echo "    healthz 200 . /scan/opencv.js $LIBC (gzip bytes)"

log "data step: none -- the switch scan.cv is not written; the intake is as today until the owner's tap"
SW="$("$PY" - "$APP/assets.db" <<'EOF'
import sqlite3, sys
db = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
r = db.execute("SELECT value FROM settings WHERE key='scan.cv'").fetchone(); print((r[0] if r else "absent"))
EOF
)"
echo "    scan.cv on the live database: $SW (absent = OFF)"

rm -rf "$WORK"
echo
echo "$KIT: DONE."
echo "  PINS (read back): scanner_widget.js $PW . asset_register.py $PA . static/opencv.js $PL"
echo "  WHAT THE OWNER SEES: nothing changes for anyone yet. On https://followup.dr-manoj.in/scanapp/admin a new card"
echo "  'Scanner - smart outline (OpenCV)' reads OFF with one button, Switch ON. After his tap, the bill intake on a phone"
echo "  that can carry it downloads the library once (3.4 MB), draws the paper's outline live on the camera, keeps the"
echo "  full camera resolution, and shows Adjust beside Retake on every page. The other six scan screens are untouched."
echo "  UNDO (one line): cp -p $APP/scanner_widget.js.bak_S523_${FROM_W:0:8} $APP/scanner_widget.js && cp -p $APP/asset_register.py.bak_S523_${FROM_A:0:8} $APP/asset_register.py && systemctl restart $SERVICE"
exit 0
