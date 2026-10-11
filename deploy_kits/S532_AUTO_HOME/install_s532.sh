#!/bin/bash
# install_s532.sh -- S532_AUTO_HOME: the system sends a scan home from the scan app's own history (the flow proposal's K3).
# BUILD_NORM_v1 s3 order: gates -> pins -> rebuild -> walk + control -> backups -> place -> restart (assetapp only) -> health
#                         -> data step (the heal at start places the waiting papers the history allows; read back) -> words -> undo.
# Run as root on the VPS: bash /root/deploy/repo/deploy_kits/S532_AUTO_HOME/install_s532.sh
set -u
KIT="S532_AUTO_HOME"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S532_APP_DIR:-/root/assetapp}"
SERVICE="${S532_SERVICE:-assetapp}"
HEALTH="${S532_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S532_PYTHON:-python3}"
RESTART="${S532_RESTART_CMD:-systemctl restart $SERVICE}"
declare -A FROM=([asset_register.py]=4e924b80e8b8a8615f3bdd54726fd305 [clinic_papers.py]=93d23481faacc1417a484fda529eef04)
WIDGET_PIN="65127fcb7c9c00ded03190c5156c7f6e"     # scanner_widget.js after S531 -- read, not edited
declare -A TO
for f in asset_register.py clinic_papers.py; do TO[$f]="$(cat "$HERE/PIN_TO_${f%.*}.txt" 2>/dev/null | tr -d ' \n')"; done
WORK="$(mktemp -d "${HOME:-/root}/s532_install_XXXX")"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; rm -rf "$WORK"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
placed(){ "$PY" - "$APP/assets.db" <<'EOF'
import sqlite3, sys
db = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
rows = db.execute("SELECT b.stamp_no, a.action, a.detail FROM bill_audit a JOIN bills b ON b.id=a.bill_id WHERE a.action IN ('auto_lane','auto_group') ORDER BY a.id").fetchall()
print(len(rows))
for r in rows: print("      %s %s %s" % r)
EOF
}

log "gates"
for f in asset_register.py clinic_papers.py; do [ -n "${TO[$f]}" ] || die "PIN_TO_${f%.*}.txt missing"; [ -f "$APP/$f" ] || die "$APP/$f missing"; done
[ -f "$APP/assets.db" ] && [ -f "$APP/scanner_widget.js" ] || die "the live database or the widget is missing"
command -v "$PY" >/dev/null || die "no $PY"; "$PY" -c "import flask" 2>/dev/null || die "$PY has no flask"
for f in make_s532.py walk_s532.py; do [ -f "$HERE/$f" ] || die "kit file $f missing"; done

log "pins -- the live bytes must be the ones this kit was built on"
ALL=1; for f in asset_register.py clinic_papers.py; do [ "$(md5 "$APP/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then echo "$KIT: ALREADY INSTALLED (both files at the kit's pins)"; rm -rf "$WORK"; exit 0; fi
for f in asset_register.py clinic_papers.py; do L="$(md5 "$APP/$f")"; [ "$L" = "${FROM[$f]}" ] || die "$f is ${L:0:8}, not the pinned ${FROM[$f]:0:8} -- another kit moved it (S531 installed?); rebuild S532 on the new bytes"; echo "    $f ${L:0:8} ok"; done
W="$(md5 "$APP/scanner_widget.js")"; [ "$W" = "$WIDGET_PIN" ] || die "scanner_widget.js is ${W:0:8}, not ${WIDGET_PIN:0:8} (S531's) -- the walk ran against that widget"
echo "    scanner_widget.js ${W:0:8} ok (read only)"

log "rebuild on the box, from the live bytes"
mkdir -p "$WORK/live_in" "$WORK/built"; for f in asset_register.py clinic_papers.py; do cp "$APP/$f" "$WORK/live_in/"; done; cp "$HERE/make_s532.py" "$WORK/"
"$PY" "$WORK/make_s532.py" "$WORK/live_in" "$WORK/built" || die "the builder refused"
for f in asset_register.py clinic_papers.py; do B="$(md5 "$WORK/built/$f")"; [ "$B" = "${TO[$f]}" ] || die "the rebuilt $f is ${B:0:8}, the kit says ${TO[$f]:0:8}"; echo "    rebuilt $f ${B:0:8} = the kit's pin"; done
"$PY" -m py_compile "$WORK/built/asset_register.py" "$WORK/built/clinic_papers.py" || die "a built file does not compile"
cp "$APP/scanner_widget.js" "$WORK/built/"; cp "$APP/scanner_widget.js" "$WORK/live_in/"

log "walk on a copy of the live database (under the session's home, removed after) -- and the control on the live files"
cd "$WORK" && HOME="$WORK" "$PY" "$HERE/walk_s532.py" "$WORK/built" "$APP/assets.db" > "$WORK/walk.txt" 2>&1 || { grep -E '^(GREEN|RED)|checks' "$WORK/walk.txt"; die "the walk is RED on the built files"; }
grep -E 'checks' "$WORK/walk.txt" | tail -1 | sed 's/^/    walk: /'
HOME="$WORK" "$PY" "$HERE/walk_s532.py" "$WORK/live_in" "$APP/assets.db" --expect-red > "$WORK/control.txt" 2>&1 || { grep -E 'checks' "$WORK/control.txt"; die "the NEGATIVE CONTROL did not go red on the live files"; }
grep -E 'checks' "$WORK/control.txt" | tail -1 | sed 's/^/    control (live files, must be red): /'
cd "$HERE"
echo "    papers the system has placed so far (live database): $(placed | head -1)"

log "backups beside the live files"
for f in asset_register.py clinic_papers.py; do cp -p "$APP/$f" "$APP/$f.bak_S532_${FROM[$f]:0:8}" || die "backup of $f failed"; done
cp -p "$APP/assets.db" "$APP/assets.db.bak_S532_$(date +%Y%m%d_%H%M%S)" || die "database backup failed (the heal writes rows)"
echo "    .bak_S532_<from8> beside each file; assets.db.bak_S532_<stamp>"

log "place"
for f in asset_register.py clinic_papers.py; do cp "$WORK/built/$f" "$APP/$f.tmp" && mv -f "$APP/$f.tmp" "$APP/$f" || die "could not place $f"; done
for f in asset_register.py clinic_papers.py; do P="$(md5 "$APP/$f")"; [ "$P" = "${TO[$f]}" ] || die "read-back of $f differs"; done
echo "    placed: both files at the kit's pins"

restore(){
  echo "RESTORING the two files from their backups"
  for f in asset_register.py clinic_papers.py; do cp -p "$APP/$f.bak_S532_${FROM[$f]:0:8}" "$APP/$f"; done
  eval "$RESTART" || true
  echo "$KIT: NOT INSTALLED (restored; a paper the heal placed stays placed -- as a tap would have; the database backup stands beside the live one)"
  rm -rf "$WORK"; exit 1
}

log "restart $SERVICE only, then health"
eval "$RESTART" || restore; sleep 4
HC="$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$HEALTH" || echo 000)"
[ "$HC" = "200" ] || { echo "    healthz answered $HC"; restore; }
echo "    healthz 200"

log "data step -- the heal at start placed the waiting papers the history allows; read back"
placed | sed '1s/^/    papers placed by the system (all time): /'
rm -rf "$WORK"
echo
echo "$KIT: DONE."
echo "  PINS (read back): asset_register.py $(md5 "$APP/asset_register.py") . clinic_papers.py $(md5 "$APP/clinic_papers.py") . scanner_widget.js $(md5 "$APP/scanner_widget.js") (unchanged)"
echo "  WHAT CHANGES: within a minute of a scan being read, a supplier whose earlier papers all went to the pharmacy lane (three or more)"
echo "  sends the new one there by itself; a clinic supplier whose papers you or Shavez always sorted into one group gets that group and is"
echo "  accepted; a supplier seen on two lanes (Yuvika) is never decided; sections are never guessed; a challan is never moved; the lab and"
echo "  Dr MK expense lanes are never touched. A placed paper's page says so and can be changed there. Staff screens: unchanged."
echo "  UNDO (one line): cp -p $APP/asset_register.py.bak_S532_4e924b80 $APP/asset_register.py && cp -p $APP/clinic_papers.py.bak_S532_93d23481 $APP/clinic_papers.py && systemctl restart $SERVICE"
exit 0
