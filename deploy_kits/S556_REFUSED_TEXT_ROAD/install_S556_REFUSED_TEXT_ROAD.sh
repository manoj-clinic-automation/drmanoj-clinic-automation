#!/bin/bash
# =============================================================================
#  install_S556_REFUSED_TEXT_ROAD.sh · kit S556 (14-Oct-2026) · brief claude_code_briefs/S556_REFUSED_TEXT_ROAD.md (v3) · repairs F-893
#
#  THE SERVER PART. Run from a copy of the kit folder while the clone's DUTY_MAP is still v13:
#    rm -rf /tmp/s556kit && cp -rp <kit> /tmp/s556kit && bash /tmp/s556kit/install_S556_REFUSED_TEXT_ROAD.sh
#  (DRY=1 before bash: every gate, the state and the walks, nothing written.)
#  Then, AFTER the repository is published with DUTY_MAP v14:
#    PHASE=pull bash /tmp/s556kit/install_S556_REFUSED_TEXT_ROAD.sh      (git pull --ff-only, then the map gate v14)
#
#  A report the medical PC's reader stopped on ("the reader refused it (line N)") is HELD on Aaj ki reports -- "Report aa gayi ... Aapko ab
#  kuch nahi karna" -- not called wrong; the owner is told once by the morning message; Darpan's card does not ask him to save it again.
#   /root/finance/reports_tile.py   01f67f4d -> TO   reader_stop, the held state, its row, status, hindi_reason
#   /root/finance/reports_watch.py  a8bbd95e -> TO   decide's 'reader' item, _others
#   /root/finance/order_sheet.py    8c50d41e -> TO   refused_sheet(con, staff=False) in one time shape; darpan_card passes staff=True
#   /root/deploy/repo/claude_code_briefs/DUTY_MAP.json ead2be78 (v13) -> v14 and DUTY_MAP.md 96219048 -> TO, by the repository's pull (PHASE=pull)
#  No data step: finance.db is backed up and never written by this kit.
#  ORDER: gates -> pins (ALREADY first) + read-only pins + the clone at v13 -> the state before (a copy) -> compile (both pythons) -> rebuild
#  from the live bytes -> walk on scratch copies (new green; the old files and v13 red) + S543's walk on the new order_sheet -> DRY stops ->
#  backups -> place -> md5 read-back -> ONE restart of clinic-finance -> healthz 200, the pages 302 (login gate) -> the pages on a copy of the
#  placed files 200 -> the state after. Red after placing: the three files put back byte-identically, restart, healthz.
# =============================================================================
set -u
KIT="S556_REFUSED_TEXT_ROAD"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
POR="${POR:-/root/portal}"
MARG="${MARG:-/root/marg_ingest}"
ADB="${ADB:-/root/assetapp/assets.db}"
REPO="${REPO:-/root/deploy/repo}"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
GIT="${GIT:-git}"
BRF="$REPO/claude_code_briefs"; DMAP="$BRF/DUTY_MAP.json"; DMD="$BRF/DUTY_MAP.md"
MAPBAK="${MAPBAK:-/root/deploy/DUTY_MAP_v13.bak_S556}"
EDITED="reports_tile.py reports_watch.py order_sheet.py"
declare -A FROM TO READ
source "$KDIR/PINS.sh"
READ[marg_door.py]=dc5c1e36d2c8bee2cd556de5c5e4f018;     READ[reports_guide.py]=20a05704d8183af340cec4b138aa9fb1
READ[aaj_seed.py]=a97cd07bfc7270184c62c16dff4dff48;      READ[aaj_kaam.py]=cd232b1c987417aa07d341d498c5effc
READ[owner_console.py]=2b985708b1dc3239fafbb7f41e969e55; READ[porders_s454.py]=72e7fd563dadf2ae657fadef66e4e72e
READ[darpan_kal.html]=f5e279eb26e7f24827f29b79f95b2769;  READ[darpan_kal.py]=fd799a56cf212625cfaadce768d3431d
V12_PIN=f499dd1fb53cb9b23422154aac41596e
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s556_inst_$STAMP"
HAVE_LOCK=0; PLACED=0
DBBAK="$FIN/finance.db.bak_S556_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S556_${FROM[$1]:0:8}"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the three files back"
  for n in $EDITED; do [ -f "$(bak $n)" ] && \cp -p "$(bak $n)" "$FIN/$n"; done
  rm -f "$FIN"/.*.s556
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  for n in $EDITED; do say "   $FIN/$n $(m5 "$FIN/$n") (expected ${FROM[$n]})"; done
  say "   after the restore: finance healthz $h"
  say "   the clone's DUTY_MAP.json is $(m5 "$DMAP") (v13 ${MAP_FROM:0:8}; if it is v14, revert it by a new commit from $MAPBAK.json / .md, publish, pull --ff-only)"
  say "   the database backup stays: $DBBAK (this kit wrote nothing to the database)"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl timeout grep tail sleep find sed sort; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
command -v "$SYSTEMCTL" >/dev/null 2>&1 || { say "!! preflight: $SYSTEMCTL missing - nothing installed"; exit 1; }
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/11] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/11] KIT_ID.txt names another kit - nothing installed"; exit 1; }
if [ "${LOCK_HELD:-0}" = 1 ]; then
  grep -q "$KIT" "$LOCK/owner" 2>/dev/null || { say "!! [1/11] LOCK_HELD=1 but $LOCK/owner does not name $KIT - nothing installed"; exit 3; }
else
  mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
  if [ "$HAVE_LOCK" != 1 ]; then
    say "!! [1/11] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again when it is free."
    exit 3
  fi
  echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
fi
say "[1/11] kit gates green (SUMS, KIT_ID); the build lock is ours"

# ------------------------------------------------------------------------------------------------ PHASE=pull (after the publish)
if [ "${PHASE:-place}" = pull ]; then
  for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || { say "!! [pull] $FIN/$n is $(m5 "$FIN/$n"), not the kit's ${TO[$n]} - place first; nothing pulled"; exit 1; }; done
  if [ "$(m5 "$DMAP")" = "$MAP_TO" ] && [ "$(m5 "$DMD")" = "$MD_TO" ]; then
    say "-- ALREADY PULLED: the clone's DUTY_MAP.json is v14 ${MAP_TO:0:8}, DUTY_MAP.md ${MD_TO:0:8}"
  else
    [ -z "$("$GIT" -C "$REPO" status --porcelain 2>/dev/null)" ] || { say "!! [pull] the clone $REPO is not clean - nothing pulled"; exit 1; }
    PLACED=1
    PULL="$("$GIT" -C "$REPO" pull --ff-only 2>&1)"; PRC=$?
    [ "$PRC" = 0 ] && [ "$(m5 "$DMAP")" = "$MAP_TO" ] && [ "$(m5 "$DMD")" = "$MD_TO" ] || { echo "$PULL" | tail -3; restore "the pull did not bring DUTY_MAP v14 (exit $PRC; DUTY_MAP.json $(m5 "$DMAP"), .md $(m5 "$DMD"))"; }
    PLACED=0
  fi
  ( cd "$REPO/deploy_kits/$KIT" 2>/dev/null && md5sum -c SUMS.md5 >/dev/null 2>&1 ) && KITREPO="byte-identical to this run" || KITREPO="NOT found byte-identical in the clone"
  [ -z "$("$GIT" -C "$REPO" status --porcelain 2>/dev/null)" ] && CLEAN=clean || CLEAN="NOT clean"
  say "[pull] $REPO pulled: DUTY_MAP.json v14 $(m5 "$DMAP" | cut -c1-8) (= the kit's ${MAP_TO:0:8}); DUTY_MAP.md $(m5 "$DMD" | cut -c1-8); the kit in the clone: $KITREPO; the clone $CLEAN"
  say "$KIT: the map gate is v14 - aaj_kaam reads it on its next read; finance healthz $(health /finance/healthz)"
  exit 0
fi

# ------------------------------------------------------------------------------------------------ PHASE=place
for n in $EDITED; do [ -f "$FIN/$n" ] || { say "!! [2/11] $FIN/$n is not there - nothing installed"; exit 1; }; done
ALL_TO=1; for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then say "-- ALREADY INSTALLED: the three files are the kit's. Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null); the clone's DUTY_MAP.json $(m5 "$DMAP") (v14 is ${MAP_TO:0:8}: PHASE=pull after the publish)"; exit 0; fi
for n in $EDITED; do C="$(m5 "$FIN/$n")"; [ "$C" = "${FROM[$n]}" ] || { say "!! [2/11] $FIN/$n is $C, expected ${FROM[$n]} - it changed after this kit was built: STOP, nothing installed"; exit 1; }; done
for n in "${!READ[@]}"; do C="$(m5 "$FIN/$n")"; [ "$C" = "${READ[$n]}" ] || { say "!! [2/11] $FIN/$n is $C, not ${READ[$n]} - this kit was built reading that file: STOP, nothing installed"; exit 1; }; done
[ "$(m5 "$DMAP")" = "$MAP_FROM" ] || { say "!! [2/11] the clone's DUTY_MAP.json is $(m5 "$DMAP"), not v13's $MAP_FROM (run this BEFORE pulling the repository) - nothing installed"; exit 1; }
[ "$(m5 "$DMD")" = "$MD_FROM" ] || { say "!! [2/11] the clone's DUTY_MAP.md is $(m5 "$DMD"), not $MD_FROM - nothing installed"; exit 1; }
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$POR/portal.py" ] && [ -f "$POR/tile_grants.json" ] || { say "!! [2/11] the database, the assets database or the portal is missing - nothing installed"; exit 1; }
say "[2/11] live pins exact (reports_tile 01f67f4d, reports_watch a8bbd95e, order_sheet 8c50d41e); 8 read-only files at their pins; the clone's DUTY_MAP.json v13 ${MAP_FROM:0:8}, DUTY_MAP.md ${MD_FROM:0:8}"

mkdir -p "$SCR/built" "$SCR/state" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONDONTWRITEBYTECODE=1
copydb "$DB" "$SCR/state/f.db" || { say "!! [3/11] no copy of the database for the state - nothing installed"; exit 1; }
say "[3/11] the install-day state, before (the live files, map v13, on a copy of the database):"
( cd /tmp && "$APY" -B "$KDIR/state_s556.py" --fin "$FIN" --db "$SCR/state/f.db" --map "$DMAP" ) || { say "!! [3/11] the state could not be read - nothing installed"; exit 1; }

for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile make_s556.py walk_s556.py state_s556.py marg_watch.py || { say "!! [4/11] compile failed on $py - nothing installed"; exit 1; }
done
"$APY" -B make_s556.py --only server --fin "$FIN" --briefs "$BRF" --out "$SCR/built" >/dev/null || { say "!! [5/11] the builder refused a live file - nothing installed"; exit 1; }
for n in $EDITED; do [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || { say "!! [5/11] rebuilt, $n is $(m5 "$SCR/built/$n"), not ${TO[$n]} - nothing installed"; exit 1; }; done
[ "$(m5 "$SCR/built/DUTY_MAP.json")" = "$MAP_TO" ] && [ "$(m5 "$SCR/built/DUTY_MAP.md")" = "$MD_TO" ] || { say "!! [5/11] the map did not rebuild to v14's pins - nothing installed"; exit 1; }
for py in "$APY" "$VPY"; do
  for n in $EDITED; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" || { say "!! [4/11] the built $n does not compile on $py - nothing installed"; exit 1; }; done
done
say "[4/11] the kit's python files and the three built files compile on $APY and $VPY"
say "[5/11] rebuilt here from this box's live bytes (16 + 3 + 2 counted edits) and DUTY_MAP v14 (5) / .md (4) from the clone's v13: each at its TO pin"

mkside() {   # $1 = side: a copy of the live finance code, the door's reader and its ORDER_PENDING archive, the two databases (backup API)
  local d="$SCR/$1"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" "$d/marg_ingest/archive"
  cp -p "$FIN"/*.py "$d/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$d/finance/finance_ui/" 2>/dev/null; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$d/finance/spine/" 2>/dev/null
  for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do cp -p "$MARG/$f" "$d/marg_ingest/" || return 1; done
  cp -rp "$MARG/archive/ORDER_PENDING" "$d/marg_ingest/archive/" || return 1
  copydb "$DB" "$d/f.db" && copydb "$ADB" "$d/a.db"
}
for side in new old s543new s543old; do mkside "$side" || { say "!! [6/11] no scratch side '$side' - nothing installed"; exit 1; }; done
for n in $EDITED; do cp -p "$SCR/built/$n" "$SCR/new/finance/" && cp -p "$SCR/built/$n" "$SCR/s543new/finance/"; done
mkdir -p "$SCR/oldpy"; for n in $EDITED; do cp -p "$FIN/$n" "$SCR/oldpy/"; done
mkdir -p "$SCR/por"; for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$SCR/por/"; done; cp -p "$POR/tile_grants.json" "$SCR/por/"
WOUT="$( cd /tmp && timeout 1800 "$APY" -B "$KDIR/walk_s556.py" --fin "$SCR/new/finance" --old "$SCR/oldpy" --db "$SCR/new/f.db" --adb "$SCR/new/a.db" --marg "$SCR/new/marg_ingest" --portal "$SCR/por" --map13 "$DMAP" --map14 "$SCR/built/DUTY_MAP.json" 2>&1 )"; WRC=$?
ROUT="$( cd /tmp && timeout 1800 "$APY" -B "$KDIR/walk_s556.py" --fin "$SCR/old/finance" --old "$SCR/oldpy" --db "$SCR/old/f.db" --adb "$SCR/old/a.db" --marg "$SCR/old/marg_ingest" --portal "$SCR/por" --map13 "$DMAP" --map14 "$DMAP" --expect-red 2>&1 )"; RRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | sed 's/^/   /'
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK S556"; then say "!! [6/11] the walk is RED on this box (exit $WRC) - nothing installed"; exit 1; fi
echo "$ROUT" | grep -E "^  RED on the old files:|^WALK OK negative|^NEGATIVE CONTROL" | sed 's/^/   /'
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK negative control"; then say "!! [6/11] the negative control did not go red on the old files - the walk proves nothing; nothing installed"; echo "$ROUT" | tail -12; exit 1; fi
# S543's walk, read-only, on the new order_sheet (and on the live one beside it): its markers must stay as they are
V12=""
for h in $("$GIT" -C "$REPO" log --format=%H -n 60 -- claude_code_briefs/DUTY_MAP.json); do
  [ "$("$GIT" -C "$REPO" show "$h:claude_code_briefs/DUTY_MAP.json" 2>/dev/null | md5sum | awk '{print $1}')" = "$V12_PIN" ] && { V12=$h; break; }
done
[ -n "$V12" ] || { say "!! [6/11] DUTY_MAP v12 (S543's walk reads it) not found in the clone's history - nothing installed"; exit 1; }
"$GIT" -C "$REPO" show "$V12:claude_code_briefs/DUTY_MAP.json" > "$SCR/map12.json"
S543K="$REPO/deploy_kits/S543_ORDER_SHEET_MARG"
for side in s543new s543old; do
  ( cd /tmp && timeout 1800 "$APY" -B "$S543K/walk_s543.py" --fin "$SCR/$side/finance" --db "$SCR/$side/f.db" --adb "$SCR/$side/a.db" --marg "$SCR/$side/marg_ingest" \
      --portal "$SCR/por" --map12 "$SCR/map12.json" --map13 "$DMAP" --kit "$S543K" > "$SCR/$side.txt" 2>&1 )
done
find "$S543K" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
FN="$(grep -E '^  FAIL ' "$SCR/s543new.txt" | sed 's/   \[.*$//' | sort)"; FO="$(grep -E '^  FAIL ' "$SCR/s543old.txt" | sed 's/   \[.*$//' | sort)"
GN="$(grep -c -E '^  ok ' "$SCR/s543new.txt")"; GO="$(grep -c -E '^  ok ' "$SCR/s543old.txt")"
if grep -q "^WALK OK S543" "$SCR/s543new.txt"; then
  S543SAY="S543's walk on the new order_sheet: WALK OK ($GN checks green)"
elif [ -n "$FN" ] && [ "$FN" = "$FO" ] && [ "$GN" = "$GO" ]; then
  S543SAY="S543's walk on the new order_sheet: $GN green, the same $(echo "$FN" | wc -l) red as on the live files beside it (the install-day state, not this kit): $(echo "$FN" | cut -c8-90 | tr '\n' '|')"
else
  say "!! [6/11] S543's walk moved on the new order_sheet (new: $GN green, old: $GO green):"; diff <(echo "$FO") <(echo "$FN") | head -8; exit 1
fi
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${FROM[$n]}" ] || { say "!! [6/11] $FIN/$n changed during the walk - nothing installed"; exit 1; }; done
[ "$(m5 "$DMAP")" = "$MAP_FROM" ] || { say "!! [6/11] the clone's DUTY_MAP.json moved during the walk - nothing installed"; exit 1; }
say "[6/11] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "       negative control, the old files and map v13: $(echo "$ROUT" | grep "^WALK OK" | tail -1 | cut -c27-)"
say "       $S543SAY"
rm -rf "$SCR/new" "$SCR/old" "$SCR/s543new" "$SCR/s543old"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the state and the walks green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

copydb "$DB" "$DBBAK" && chmod 600 "$DBBAK" || { rm -f "$DBBAK"; say "!! [7/11] database backup failed - nothing placed"; exit 1; }
for n in $EDITED; do
  \cp -p "$FIN/$n" "$(bak $n)" || { say "!! [7/11] backup of $n failed - nothing placed"; exit 1; }
  [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ] || { say "!! [7/11] the backup of $n is not the live file - nothing placed"; exit 1; }
done
\cp -p "$DMAP" "$MAPBAK.json" && \cp -p "$DMD" "$MAPBAK.md" && [ "$(m5 "$MAPBAK.json")" = "$MAP_FROM" ] && [ "$(m5 "$MAPBAK.md")" = "$MD_FROM" ] \
  || { say "!! [7/11] the clone's v13 map could not be copied aside - nothing placed"; exit 1; }
say "[7/11] backups: $(basename "$DBBAK") (sqlite backup API); $(for n in $EDITED; do printf '%s ' "$(basename "$(bak $n)")"; done); $(basename "$MAPBAK").json / .md"

for n in $EDITED; do
  { \cp -p "$FIN/$n" "$FIN/.$n.s556" && cat "$SCR/built/$n" > "$FIN/.$n.s556" && [ "$(m5 "$FIN/.$n.s556")" = "${TO[$n]}" ]; } || { rm -f "$FIN"/.*.s556; say "!! [8/11] could not stage $n - nothing placed"; exit 1; }
done
PLACED=1
for n in $EDITED; do mv -f "$FIN/.$n.s556" "$FIN/$n" || restore "placing $n"; done
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || restore "$n did not land at its pin"; done
say "[8/11] placed; md5 read back: $(for n in $EDITED; do printf '%s %s . ' "$n" "$(m5 "$FIN/$n" | cut -c1-8)"; done)(= the kit's)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
"$SYSTEMCTL" is-active --quiet "$SVC" || restore "$SVC is not active"
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/reports/aaj); c3=$(health /finance/darpan/kal)
for c in "$c2" "$c3"; do case "$c" in 302|401) ;; *) restore "a page answered $c without a login (302 = the login gate, expected): reports/aaj $c2 / darpan/kal $c3";; esac; done
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[9/11] $SVC restarted at $T0 (nothing else) and active - healthz $c1 - /finance/reports/aaj $c2, /finance/darpan/kal $c3 without a login (302 = the login gate, expected) - journal clean"

mkdir -p "$SCR/placed/finance/spine" "$SCR/placed/marg_ingest/archive"; cp -p "$FIN"/*.py "$SCR/placed/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$SCR/placed/finance/" 2>/dev/null
cp -rp "$FIN/finance_ui" "$SCR/placed/finance/" 2>/dev/null; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$SCR/placed/finance/spine/" 2>/dev/null
for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do cp -p "$MARG/$f" "$SCR/placed/marg_ingest/"; done; cp -rp "$MARG/archive/ORDER_PENDING" "$SCR/placed/marg_ingest/archive/"
copydb "$DB" "$SCR/placed/f.db" && copydb "$ADB" "$SCR/placed/a.db" || restore "no copy of the database for the page look"
POUT="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/walk_s556.py" --page --fin "$SCR/placed/finance" --db "$SCR/placed/f.db" --adb "$SCR/placed/a.db" --marg "$SCR/placed/marg_ingest" --map14 "$SCR/built/DUTY_MAP.json" 2>&1 )"; PRC=$?
echo "$POUT" | grep -E "^   /finance|^PAGE" | sed 's/^/ /'
[ "$PRC" = 0 ] && echo "$POUT" | grep -q "^PAGE OK" || restore "the two pages on a copy of the placed files are red"
say "[10/11] /finance/reports/aaj (shavez) and /finance/darpan/kal (darpan) answer 200 on a copy of the placed files"

say "[11/11] the state after (the placed files, map v14 as built, on a copy of the database):"
copydb "$DB" "$SCR/state/f2.db" && ( cd /tmp && "$APY" -B "$KDIR/state_s556.py" --fin "$FIN" --db "$SCR/state/f2.db" --map "$SCR/built/DUTY_MAP.json" ) || say "   (the state could not be read -- the files are placed and green; said for the report)"
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0
for n in $EDITED; do md5sum "$FIN/$n"; done
say "$KIT: the server part is PLACED - a report the medical PC's reader stopped on is held on Aaj ki reports, the owner is told once, Darpan's card does not ask him again"
say "next: publish the repository (DUTY_MAP v14), then: LOCK_HELD=1 PHASE=pull bash $KDIR/$(basename "$0")"
say "undo: $(for n in $EDITED; do printf '\\cp -p %s %s && ' "$(bak $n)" "$FIN/$n"; done)$SYSTEMCTL restart $SVC"
exit 0
