#!/bin/bash
# install_s531.sh -- S531_CHALLAN_FLOW (D689 item 2): the CHALLAN tap at intake, Bills awaited, the join, the delete.
# BUILD_NORM_v1 s3 order: gates -> pins -> rebuild -> walk + control -> backups -> place -> restart (assetapp only) -> health
#                         -> data step (three additive columns, added by the app's own migration at start; read back) -> words -> undo.
# Run as root on the VPS: bash /root/deploy/repo/deploy_kits/S531_CHALLAN_FLOW/install_s531.sh
set -u
KIT="S531_CHALLAN_FLOW"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S531_APP_DIR:-/root/assetapp}"
SERVICE="${S531_SERVICE:-assetapp}"
HEALTH="${S531_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S531_PYTHON:-python3}"
RESTART="${S531_RESTART_CMD:-systemctl restart $SERVICE}"
declare -A FROM=([asset_register.py]=d3f1b64ee103efe22266426af9280fbe [clinic_papers.py]=c60e043ce62cb2e8843d5963e9db0256 [scanner_widget.js]=cd9c6e6053d85895e8132eb021b63b6b)
declare -A TO
for f in asset_register.py clinic_papers.py scanner_widget.js; do TO[$f]="$(cat "$HERE/PIN_TO_${f%.*}.txt" 2>/dev/null | tr -d ' \n')"; done
WORK="$(mktemp -d "${HOME:-/root}/s531_install_XXXX")"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; rm -rf "$WORK"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
cols(){ "$PY" - "$APP/assets.db" <<'EOF'
import sqlite3, sys
db = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
c = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
print(" ".join(sorted(x for x in ("doc_kind", "challan_state", "challan_of") if x in c)) or "none")
EOF
}

log "gates"
for f in asset_register.py clinic_papers.py scanner_widget.js; do [ -n "${TO[$f]}" ] || die "PIN_TO_${f%.*}.txt missing"; [ -f "$APP/$f" ] || die "$APP/$f missing"; done
[ -f "$APP/assets.db" ] || die "no $APP/assets.db"
command -v "$PY" >/dev/null || die "no $PY"; "$PY" -c "import flask" 2>/dev/null || die "$PY has no flask"
for f in make_s531.py walk_s531.py; do [ -f "$HERE/$f" ] || die "kit file $f missing"; done

log "pins -- the live bytes must be the ones this kit was built on"
ALL_TO=1; for f in asset_register.py clinic_papers.py scanner_widget.js; do L="$(md5 "$APP/$f")"; [ "$L" = "${TO[$f]}" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then echo "$KIT: ALREADY INSTALLED (the three files at the kit's pins)"; rm -rf "$WORK"; exit 0; fi
for f in asset_register.py clinic_papers.py scanner_widget.js; do L="$(md5 "$APP/$f")"; [ "$L" = "${FROM[$f]}" ] || die "$f is ${L:0:8}, not the pinned ${FROM[$f]:0:8} -- another kit moved it (S530 installed? S523?); rebuild S531 on the new bytes"; echo "    $f ${L:0:8} ok"; done

log "rebuild on the box, from the live bytes"
mkdir -p "$WORK/live_in" "$WORK/built"; for f in asset_register.py clinic_papers.py scanner_widget.js; do cp "$APP/$f" "$WORK/live_in/"; done; cp "$HERE/make_s531.py" "$WORK/"
"$PY" "$WORK/make_s531.py" "$WORK/live_in" "$WORK/built" || die "the builder refused"
for f in asset_register.py clinic_papers.py scanner_widget.js; do B="$(md5 "$WORK/built/$f")"; [ "$B" = "${TO[$f]}" ] || die "the rebuilt $f is ${B:0:8}, the kit says ${TO[$f]:0:8}"; echo "    rebuilt $f ${B:0:8} = the kit's pin"; done
"$PY" -m py_compile "$WORK/built/asset_register.py" "$WORK/built/clinic_papers.py" || die "a built file does not compile"

log "walk on a copy of the live database (under the session's home, removed after) -- and the control on the live files"
cd "$WORK" && HOME="$WORK" "$PY" "$HERE/walk_s531.py" "$WORK/built" "$APP/assets.db" > "$WORK/walk.txt" 2>&1 || { grep -E '^(GREEN|RED)|checks' "$WORK/walk.txt"; die "the walk is RED on the built files"; }
grep -E 'checks' "$WORK/walk.txt" | tail -1 | sed 's/^/    walk: /'
HOME="$WORK" "$PY" "$HERE/walk_s531.py" "$WORK/live_in" "$APP/assets.db" --expect-red > "$WORK/control.txt" 2>&1 || { grep -E 'checks' "$WORK/control.txt"; die "the NEGATIVE CONTROL did not go red on the live files"; }
grep -E 'checks' "$WORK/control.txt" | tail -1 | sed 's/^/    control (live files, must be red): /'
cd "$HERE"
echo "    columns on the live database before: $(cols)"

log "backups beside the live files"
for f in asset_register.py clinic_papers.py scanner_widget.js; do cp -p "$APP/$f" "$APP/$f.bak_S531_${FROM[$f]:0:8}" || die "backup of $f failed"; done
cp -p "$APP/assets.db" "$APP/assets.db.bak_S531_$(date +%Y%m%d_%H%M%S)" || die "database backup failed"
echo "    .bak_S531_<from8> beside each file; assets.db.bak_S531_<stamp>"

log "place"
for f in asset_register.py clinic_papers.py scanner_widget.js; do cp "$WORK/built/$f" "$APP/$f.tmp" && mv -f "$APP/$f.tmp" "$APP/$f" || die "could not place $f"; done
for f in asset_register.py clinic_papers.py scanner_widget.js; do P="$(md5 "$APP/$f")"; [ "$P" = "${TO[$f]}" ] || die "read-back of $f differs"; done
echo "    placed: the three files at the kit's pins"

restore(){
  echo "RESTORING the three files from their backups"
  for f in asset_register.py clinic_papers.py scanner_widget.js; do cp -p "$APP/$f.bak_S531_${FROM[$f]:0:8}" "$APP/$f"; done
  eval "$RESTART" || true
  echo "$KIT: NOT INSTALLED (restored; the three added columns, if any, stay -- they are additive and read by nothing in the old files)"
  rm -rf "$WORK"; exit 1
}

log "restart $SERVICE only, then health"
eval "$RESTART" || restore; sleep 4
HC="$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$HEALTH" || echo 000)"
[ "$HC" = "200" ] || { echo "    healthz answered $HC"; restore; }
WC="$(curl -s --max-time 20 "${HEALTH%/healthz}/scan/widget.js" | grep -c 'S531' || echo 0)"
[ "$WC" != "0" ] || { echo "    the served widget does not carry S531"; restore; }
echo "    healthz 200 . the served widget carries S531"

log "data step -- the three additive columns (the app's own migration at start); read back"
echo "    columns on the live database after: $(cols)"
rm -rf "$WORK"
echo
echo "$KIT: DONE."
echo "  PINS (read back): asset_register.py $(md5 "$APP/asset_register.py") . clinic_papers.py $(md5 "$APP/clinic_papers.py") . scanner_widget.js $(md5 "$APP/scanner_widget.js")"
echo "  WHAT STAFF SEE on the bill intake: one big button under the lane line, CHALLAN HAI? -- one tap before Save when the paper is a"
echo "  challan; it turns amber, the line says CHALLAN, the slip says CHALLAN, and it goes back to normal after every Save. A plain bill: nothing to touch."
echo "  WHAT THE OWNER SEES: https://followup.dr-manoj.in/scanapp/papers/challans -- Bills awaited (amber after 15 days; 'Bill nahi aayega' closes"
echo "  one); a new bill from the same supplier offers the join on its own page and on the to-sort card; after the join the challan can be deleted"
echo "  (its number stays, its file is moved to uploads/_deleted_challans, its picture is inside the bill's PDF). The finance app's five scan screens: unchanged."
echo "  UNDO (one line): cp -p $APP/asset_register.py.bak_S531_d3f1b64e $APP/asset_register.py && cp -p $APP/clinic_papers.py.bak_S531_c60e043c $APP/clinic_papers.py && cp -p $APP/scanner_widget.js.bak_S531_cd9c6e60 $APP/scanner_widget.js && systemctl restart $SERVICE"
exit 0
