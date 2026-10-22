#!/bin/bash
# install_s623.sh -- S623_STATIONERY_CHALLAN_HISTORY (D756; board _numbers v588 -> v589; built in the Scan App chat, session 337, 22-Oct-2026).
# The six Variety Stationers challans' lines written as the stationery RECEIVED history, each paper on its challan date (before the
# owner's 18-Oct opening counts, so the nine counted stocks stand); B-0013's token line corrected to 1 packet. A DATA-ONLY kit:
# NO file is changed or placed and NO service is restarted. stationery.py (18268ff0) and sorting_desk.py (110335ea) are read only, pinned.
# BUILD_NORM_v1 s3 order for a data kit: gates -> the build lock -> ALREADY INSTALLED (the key) -> pins -> the walk on made-up databases
# (with its negative control and mutants) -> on a scratch copy of the live database: the control (verify RED), the step, a second run
# (writes nothing), verify GREEN, the undo rehearsed (back exactly) -- DRY=1 stops here -> the database backup (backup API) -> the step
# live (one transaction, rolled back by itself if any stock moves other than its lines account for) -> verify live (red = undo at once)
# -> healthz -> what his pages now show -> the undo line.
# Run as root on the VPS: cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S623_STATIONERY_CHALLAN_HISTORY/install_s623.sh
set -u
KIT="S623_STATIONERY_CHALLAN_HISTORY"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S623_APP_DIR:-/root/assetapp}"
SERVICE="${S623_SERVICE:-assetapp}"
HEALTH="${S623_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S623_PYTHON:-python3}"
LOCK="${S623_LOCK:-/root/deploy/.claude_code_build.lock}"
HOSTPAT="${S623_HOST:-srv1746119}"
REH="${S623_REHEARSAL:-}"                       # set only by rehearse_s623.sh (a made-up root): skips the root check
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was written)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
if [ -z "${S623_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S623_DB:-${DB0:-$APP/assets.db}}"
STAMP="$(date +%Y%m%d_%H%M%S)"
HAVE_LOCK=0
WORK=""
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; [ "$HAVE_LOCK" = 1 ] && { rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null; }; }
trap cleanup EXIT
H="$PY -B $HERE/history_s623.py"

log "gates (the box, root, the kit, the files)"
case "$(hostname)" in *$HOSTPAT*) ;; *) die "this is not $HOSTPAT";; esac
[ -n "$REH" ] || [ "$(id -u)" = "0" ] || die "run as root"
for f in history_s623.py walk_s623.py PIN_READ_stationery.txt PIN_READ_sorting_desk.txt KIT_ID.txt; do [ -f "$HERE/$f" ] || die "kit file $f missing"; done
for k in PIN_READ_stationery.txt PIN_READ_sorting_desk.txt; do v="$(pin $k)"; [ ${#v} -eq 32 ] || die "$k is not a pin"; done
[ -f "$APP/stationery.py" ] && [ -f "$APP/sorting_desk.py" ] || die "$APP/stationery.py or sorting_desk.py missing"
[ -f "$DB" ] || die "no database at the service's path"
command -v "$PY" >/dev/null || die "no $PY"; "$PY" -c "import flask" 2>/dev/null || die "$PY has no flask"
echo "    the kit and $APP ok; the database read from the service (not shown)"

log "the server-wide build lock (one build at a time on the shared server)"
mkdir -p "$(dirname "$LOCK")"
if mkdir "$LOCK" 2>/dev/null; then HAVE_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; else
  die "another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) -- paste the line again when it is free"; fi
echo "    the build lock is ours"

log "pins -- the live bytes this kit reads (read only, never placed)"
for f in stationery sorting_desk; do L="$(md5 "$APP/$f.py")"; P="$(pin PIN_READ_$f.txt)"
  [ "$L" = "$P" ] || die "$f.py is ${L:0:8}, not the pinned ${P:0:8} -- another kit moved it; S623 is to be re-checked on the new bytes"
  echo "    $f.py ${L:0:8} = the pin"; done

log "already installed? (the done-key stationery.history_s623)"
HK="$("$PY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); r=c.execute(\"SELECT value FROM settings WHERE key='stationery.history_s623'\").fetchone(); print(r[0] if (r and not str(r[0]).startswith('undone')) else '')" "$DB" 2>/dev/null)" || die "the settings could not be read"
if [ -n "$HK" ]; then
  echo "$KIT: ALREADY INSTALLED (stationery.py and sorting_desk.py at the pins; the key stationery.history_s623 is set: $HK) -- nothing written"
  exit 0
fi
echo "    not yet (or undone)"

WORK="$(mktemp -d /tmp/s623work.XXXXXX)" || die "no scratch folder"
chmod 700 "$WORK"

log "the walk on made-up databases (no live row): the step, its gates, a second run, the undo, the negative control and two mutants"
"$PY" -B "$HERE/walk_s623.py" --app "$APP" --kit "$HERE" > "$WORK/walk.txt" 2>&1; WR=$?
grep -E '^(GREEN|RED)' "$WORK/walk.txt" | cut -c1-160
tail -1 "$WORK/walk.txt"
[ "$WR" = 0 ] || die "the walk is not all green"

log "a scratch copy of the live database (backup API, read only) -- the rehearsal of the step on it"
"$PY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$WORK/snap.db" || die "the scratch copy failed"
cp -p "$WORK/snap.db" "$WORK/undo.db"
$H --verify "$WORK/snap.db" --app "$APP" > "$WORK/ctl.txt" 2>&1
NCTL="$(tail -1 "$WORK/ctl.txt" | sed -n 's/^verify: \([0-9]*\) red$/\1/p')"
[ -n "$NCTL" ] && [ "$NCTL" -ge 20 ] || { cat "$WORK/ctl.txt"; die "the negative control is not red enough on the copy before the step (${NCTL:-?} red, want 20 or more) -- the checks cannot tell old from new"; }
echo "    control: verify on the copy BEFORE the step is red ($(tail -1 "$WORK/ctl.txt")) -- as it must be"
$H --apply "$WORK/snap.db" --app "$APP" > "$WORK/reh1.txt" 2>&1 || { cat "$WORK/reh1.txt"; die "the step REFUSED on the scratch copy of the live database"; }
sed 's/^/    /' "$WORK/reh1.txt"
$H --apply "$WORK/snap.db" --app "$APP" > "$WORK/reh2.txt" 2>&1 && grep -q "already done" "$WORK/reh2.txt" || { cat "$WORK/reh2.txt"; die "the second run on the copy did not say 'already done'"; }
echo "    second run on the copy: $(head -1 "$WORK/reh2.txt")"
$H --verify "$WORK/snap.db" --app "$APP" > "$WORK/ver.txt" 2>&1 || { cat "$WORK/ver.txt"; die "verify on the copy after the step is not all green"; }
echo "    verify on the copy after the step: $(tail -1 "$WORK/ver.txt")"
$H --apply "$WORK/undo.db" --app "$APP" > /dev/null 2>&1 || die "the step failed on the undo copy"
$H --undo "$WORK/undo.db" --app "$APP" > "$WORK/undo.txt" 2>&1 || { cat "$WORK/undo.txt"; die "the undo failed on the copy"; }
"$PY" -c "
import sqlite3,sys
q='SELECT bill_id,bill_created_at,line_no,name,qty,unit,rate,item_id,not_stock,day,ts FROM stationery_line WHERE voided_at=\'\' ORDER BY 1,2,3,4,5,8'
a=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True).execute(q).fetchall(); b=sqlite3.connect(sys.argv[2]).execute(q).fetchall()
sys.exit(0 if a==b else 1)" "$DB" "$WORK/undo.db" || die "after the undo on the copy the stationery lines are not exactly as before"
echo "    the undo on a copy: $(cat "$WORK/undo.txt") -- the lines exactly as before"
if [ -n "${DRY:-}" ]; then echo "$KIT: DRY RUN -- stopped before the backup; nothing live written"; exit 0; fi

log "the database backup (backup API), BEFORE the step"
"$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$DB.bak_S623_$STAMP" || die "the database backup failed"
chmod 600 "$DB.bak_S623_$STAMP" 2>/dev/null
echo "    $(basename "$DB").bak_S623_$STAMP"

log "the step on the live database (one transaction)"
$H --apply "$DB" --app "$APP" > "$WORK/live.txt" 2>&1; AR=$?
sed 's/^/    /' "$WORK/live.txt"
grep -qE "LEFT ALONE|skipped" "$WORK/live.txt" && echo "    NOTE: not every planned line was written -- the lines above marked LEFT ALONE / skipped are not in the stock (the rest is)"
[ "$AR" = 0 ] || { echo "$KIT: NOT INSTALLED (the step refused and rolled back by itself; nothing of it was written; the database backup stays)"; exit 1; }

log "verify on the live database"
$H --verify "$DB" --app "$APP" > "$WORK/vlive.txt" 2>&1; VR=$?
grep -E 'RED|verify:' "$WORK/vlive.txt" | sed 's/^/    /'
if [ "$VR" != 0 ]; then
  echo "    a check is red -- taking the step back now (undo: voids its lines, never deletes)"
  $H --undo "$DB" --app "$APP" > "$WORK/undolive.txt" 2>&1; UR=$?
  sed 's/^/    /' "$WORK/undolive.txt"
  [ "$UR" = 0 ] || { echo "$KIT: NOT INSTALLED -- AND THE UNDO FAILED: the database backup $(basename "$DB").bak_S623_$STAMP is the way back"; exit 1; }
  echo "$KIT: NOT INSTALLED (written, then undone at once; the key marked undone; the database backup stays)"; exit 1
fi

log "the scan app answers (no restart: no code changed)"
if [ "$HEALTH" = "skip" ]; then echo "    (rehearsal: not asked)"; else
  HC="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$HEALTH" 2>/dev/null || true)"; echo "    healthz $HC"; fi

echo
echo "WHAT THE OWNER'S PAGES NOW SHOW (https://followup.dr-manoj.in/scanapp/stationery):"
echo "  - the nine counted stocks exactly as before (the challans came before his 18-Oct count);"
echo "  - A4 paper 21 reams, File folder DC-217 3, X-ray envelope 500, Token 1 packet (each plus or minus any issue since);"
echo "  - October's 'Received this month': B-0109, B-0114, B-0133 and B-0163 -- a counted item can show 'received' without its stock rising;"
echo "  - on the sorting desk each of the six papers shows its lines matched, into the stock; the Estimate Book line stays unmatched."
echo "UNDO (voids S623's lines, brings back B-0013's ring file and token of 100; never deletes; a paper re-saved since is left as it is):"
echo "  $PY -B $HERE/history_s623.py --undo $DB"
echo "$KIT: DONE"
