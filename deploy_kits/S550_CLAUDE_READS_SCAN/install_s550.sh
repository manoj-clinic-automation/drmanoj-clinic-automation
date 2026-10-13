#!/bin/bash
# install_s550.sh -- S550_CLAUDE_READS_SCAN (D723): Claude reads every scan first (Sarvam when Claude answers nothing), and
# reads the older scans once in the background. The owner types the scanapp-reader key once, at a hidden prompt; it is kept
# root-only outside the app folder, never shown, never in the repository, a backup or a log.
# BUILD_NORM_v1 s3 order: gates -> pins -> the key -> rebuild -> walk + control -> backups -> place -> restart (assetapp only)
#                         -> health -> the live test (one made-up bill) -> the older scans started -> words -> undo.
# Run as root on the VPS: bash /root/deploy/repo/deploy_kits/S550_CLAUDE_READS_SCAN/install_s550.sh
#   --new-key   ask for the key again (replace a wrong or old key)
set -u
KIT="S550_CLAUDE_READS_SCAN"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S550_APP_DIR:-/root/assetapp}"
SERVICE="${S550_SERVICE:-assetapp}"
HEALTH="${S550_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S550_PYTHON:-python3}"
RESTART="${S550_RESTART_CMD:-systemctl restart $SERVICE}"
KEYDIR="${S550_KEY_DIR:-/root/.scanapp_secrets}"
KEYFILE="$KEYDIR/anthropic.key"
export SCANAPP_ANTHROPIC_KEY_FILE="$KEYFILE"
NEWKEY=0; [ "${1:-}" = "--new-key" ] && NEWKEY=1
FROM_AR=99652ff0ca4f8f52377b0c6f210eb4c9
FILES="asset_register.py claude_reader.py claude_reread.py"
declare -A TO
for f in $FILES; do TO[$f]="$(tr -d ' \n' < "$HERE/PIN_TO_${f%.*}.txt" 2>/dev/null)"; done
WORK="$(mktemp -d "${HOME:-/root}/s550_install_XXXX")" && [ -n "$WORK" ] && [ -d "$WORK" ] || { echo "REFUSED: no temporary folder"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
trap 'rm -rf "$WORK"; for f in $FILES; do rm -f "$APP/$f.tmp"; done' EXIT
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
# the database and the uploads folder the service itself uses (read quietly -- the service's settings are never printed)
SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
DB="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"; DB="${DB:-$APP/assets.db}"
UP="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_UPLOADS=//p' | head -1)"; UP="${UP:-$APP/uploads}"
unset SVC_ENV

ask_key(){
  echo "    Paste the scanapp-reader key, then press Enter. Nothing will show while you paste -- that is normal."
  K=""; IFS= read -r -s K; echo
  K="$(printf '%s' "$K" | tr -d '[:space:]')"
  case "$K" in sk-ant-?*) ;; *) K=""; echo "    That did not look like a Claude key (it starts sk-ant-)."; return 1;; esac
  ( umask 077; mkdir -p "$KEYDIR" && chmod 700 "$KEYDIR" && printf '%s\n' "$K" > "$KEYFILE.tmp" && chmod 600 "$KEYFILE.tmp" && mv -f "$KEYFILE.tmp" "$KEYFILE" )
  K=""; [ -s "$KEYFILE" ] || { echo "    the key could not be stored"; return 1; }
  echo "    key stored root-only (it is not shown)"
}
selftest(){
  "$PY" -B - "$APP" "$DB" "$WORK" <<'PYEOF'
import sys
sys.path.insert(0, sys.argv[1])
import claude_reader as c
ok, msg = c.selftest(sys.argv[2], sys.argv[3])
print("    " + msg)
sys.exit(0 if ok else 3)
PYEOF
}
start_reread(){
  if command -v systemd-run >/dev/null 2>&1 && [ -z "${S550_NO_SYSTEMD:-}" ]; then
    systemd-run --quiet --unit="scanapp-reread-$(date +%Y%m%d%H%M%S)" --collect --property=WorkingDirectory="$APP" \
      --setenv=SCANAPP_ANTHROPIC_KEY_FILE="$KEYFILE" "$PY" "$APP/claude_reread.py" --db "$DB" --uploads "$UP" >/dev/null 2>&1 && { echo "    started in the background (systemd)"; return 0; }
  fi
  ( cd "$APP" && nohup setsid "$PY" "$APP/claude_reread.py" --db "$DB" --uploads "$UP" >> "$APP/claude_reread.log" 2>&1 < /dev/null & )
  echo "    started in the background"
}
after_words(){
  echo "  The owner's card: https://followup.dr-manoj.in/scanapp/admin  (Reading the scans -- Claude: ON/OFF, today's count, the older scans' progress)"
}

log "gates"
for f in $FILES; do [ -n "${TO[$f]}" ] || die "PIN_TO_${f%.*}.txt missing"; done
for f in asset_register.py clinic_papers.py; do [ -f "$APP/$f" ] || die "$APP/$f missing"; done
[ -f "$DB" ] || die "no database at the service's path"
command -v "$PY" >/dev/null || die "no $PY"; "$PY" -c "import flask" 2>/dev/null || die "$PY has no flask"
for k in make_s550.py walk_s550.py claude_reader.py claude_reread.py; do [ -f "$HERE/$k" ] || die "kit file $k missing"; done
for f in claude_reader.py claude_reread.py; do [ "$(md5 "$HERE/$f")" = "${TO[$f]}" ] || die "the kit's $f is not at its pin"; done

log "pins -- the live bytes must be the ones this kit was built on"
ALL_TO=1; for f in $FILES; do { [ -f "$APP/$f" ] && [ "$(md5 "$APP/$f")" = "${TO[$f]}" ]; } || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then
  echo "$KIT: ALREADY INSTALLED (the three files at the kit's pins)"
  if [ "$NEWKEY" = 1 ] || [ ! -s "$KEYFILE" ]; then ask_key || { echo "    the key was not changed -- run this line again"; exit 1; }; fi
  log "the live test"
  if selftest; then log "the older scans"; start_reread; else echo "    Sarvam carries on reading. If the key was wrong, run this line again with --new-key at its end."; fi
  after_words; exit 0
fi
L="$(md5 "$APP/asset_register.py")"; [ "$L" = "$FROM_AR" ] || die "asset_register.py is ${L:0:8}, not the pinned ${FROM_AR:0:8} -- another kit moved it; rebuild S550 on the new bytes"
echo "    asset_register.py ${L:0:8} ok"
for f in claude_reader.py claude_reread.py; do [ -e "$APP/$f" ] && die "$APP/$f already exists and is not this kit's -- look before placing"; done

log "the key"
if [ "$NEWKEY" = 1 ] || [ ! -s "$KEYFILE" ]; then ask_key || die "no key stored"; else echo "    a key is already stored (not shown)"; fi

log "rebuild on the box, from the live bytes"
mkdir -p "$WORK/live_in" "$WORK/built"
cp "$APP/asset_register.py" "$APP/clinic_papers.py" "$WORK/live_in/"
"$PY" "$HERE/make_s550.py" "$WORK/live_in" "$WORK/built" >/dev/null || die "the builder refused"
cp "$APP/clinic_papers.py" "$WORK/built/"
for f in $FILES; do B="$(md5 "$WORK/built/$f")"; [ "$B" = "${TO[$f]}" ] || die "the rebuilt $f is ${B:0:8}, the kit says ${TO[$f]:0:8}"; echo "    rebuilt $f ${B:0:8} = the kit's pin"; done
"$PY" -m py_compile "$WORK/built/asset_register.py" "$WORK/built/claude_reader.py" "$WORK/built/claude_reread.py" || die "a built file does not compile"

log "walk on a copy of the live database (under the session's home, removed after; made-up rows; nothing sent to Claude) -- and the control"
( cd "$WORK" && HOME="$WORK" "$PY" -B "$HERE/walk_s550.py" "$WORK/built" "$DB" > "$WORK/walk.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/walk.txt"; die "the walk is RED on the built files"; }
grep -E 'checks' "$WORK/walk.txt" | tail -1 | sed 's/^/    walk: /'
cp "$HERE/claude_reader.py" "$HERE/claude_reread.py" "$WORK/live_in/"
( cd "$WORK" && HOME="$WORK" "$PY" -B "$HERE/walk_s550.py" "$WORK/live_in" "$DB" --expect-red > "$WORK/control.txt" 2>&1 ) || { grep -E 'checks' "$WORK/control.txt"; die "the NEGATIVE CONTROL did not go red on the live file"; }
grep -E 'checks' "$WORK/control.txt" | tail -1 | sed 's/^/    control (live file, must be red): /'

log "backups beside the live file"
cp -p "$APP/asset_register.py" "$APP/asset_register.py.bak_S550_${FROM_AR:0:8}" || die "backup failed"
"$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$DB.bak_S550_$(date +%Y%m%d_%H%M%S)" || die "database backup failed"
echo "    asset_register.py.bak_S550_${FROM_AR:0:8}; assets.db.bak_S550_<stamp>"

restore(){
  echo "RESTORING asset_register.py from its backup; the two new files taken out"
  cp -p "$APP/asset_register.py.bak_S550_${FROM_AR:0:8}" "$APP/asset_register.py.tmp" && mv -f "$APP/asset_register.py.tmp" "$APP/asset_register.py"
  rm -f "$APP/claude_reader.py" "$APP/claude_reread.py"
  eval "$RESTART" || true
  [ "$(md5 "$APP/asset_register.py")" = "$FROM_AR" ] || { echo "RESTORE FAILED -- run the UNDO line in the README"; exit 2; }
  RH=""; for i in $(seq 1 20); do sleep 2; RH="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$HEALTH" || true)"; [ "$RH" = "200" ] && break; done
  [ "$RH" = "200" ] || { echo "RESTORED THE FILES, BUT THE APP DOES NOT ANSWER (healthz ${RH:-nothing}) -- the scan app is DOWN: tell Claude now"; exit 2; }
  echo "    healthz 200 after the restore"
  echo "$KIT: NOT INSTALLED (restored; the key stays stored, unused; the reading table, if made, is read by nothing)"
  exit 1
}

log "place (the two new files first, then the app)"
for f in claude_reader.py claude_reread.py asset_register.py; do
  if ! { cp "$WORK/built/$f" "$APP/$f.tmp" && mv -f "$APP/$f.tmp" "$APP/$f"; }; then restore; fi
done
for f in $FILES; do [ "$(md5 "$APP/$f")" = "${TO[$f]}" ] || restore; done
echo "    placed: the three files at the kit's pins"

log "restart $SERVICE only, then health"
eval "$RESTART" || restore
HC=""; for i in $(seq 1 20); do sleep 2; HC="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$HEALTH" || true)"; [ "$HC" = "200" ] && break; done
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing} for 40 s"; restore; }
echo "    healthz 200"

log "the live test -- Claude reads one made-up bill (no person, no real supplier)"
LIVE=0; if selftest; then LIVE=1; fi

log "the older scans"
if [ "$LIVE" = 1 ]; then start_reread; else echo "    not started -- Claude did not read the test bill. The app reads with Sarvam as before."; fi
echo
echo "$KIT: DONE."
echo "  PINS (read back): asset_register.py $(md5 "$APP/asset_register.py") . claude_reader.py $(md5 "$APP/claude_reader.py") . claude_reread.py $(md5 "$APP/claude_reread.py")"
if [ "$LIVE" = 1 ]; then
  echo "  CLAUDE READS: ON. Every new scan is read by Claude first (Sarvam when it cannot); the older scans are being read now,"
  echo "  one by one, filling only what is empty."
else
  echo "  CLAUDE READS: NOT YET -- the key did not work or the server could not reach Claude. Sarvam reads as before."
  echo "  To try another key: bash $HERE/install_s550.sh --new-key"
fi
after_words
echo "  UNDO (one line): cp -p $APP/asset_register.py.bak_S550_${FROM_AR:0:8} $APP/asset_register.py && rm -f $APP/claude_reader.py $APP/claude_reread.py && systemctl restart $SERVICE"
exit 0
