#!/bin/bash
# =============================================================================
#  install_S524_AMIR_ONE_JUDGMENT.sh · kit S524_AMIR_ONE_JUDGMENT (Sanjeevni, session 307, 11-Oct-2026; D706)
#  ONE proof of Amir's vouchers, read from the spine (F-843 F-844 F-845 F-846 F-847 F-848 F-840) -- after Part 0, the spine gate of 08-Oct:
#  the purchase item-wise reader and the tie step repaired so the spine builds again (13/13).
#
#  Run by (on the VPS):   bash <kit>/install_S524_AMIR_ONE_JUDGMENT.sh        DRY=1 : gates, build, compile, Part 0 in scratch, walk on scratch copies only.
#  ORDER: gate 0 (SUMS, KIT_ID, PINS; ALREADY INSTALLED) · the lock · gates (flask, the SEVEN FROM pins, DUTY_MAP.json v10 at its pin, the
#  must-not-move md5s recorded) · build (make_s524.py) · compile both pythons · PART 0 IN SCRATCH (the two refused readings re-read with the new
#  reader; the OLD builder on the OLD readings -> 11/13 (control); the NEW builder on the re-read readings -> 13/13; the two cross builds) ·
#  scratch copies · the walk (DRY stops) · re-check · backups (.bak_S524_<from8> beside every file, finance.db.bak_S524, the two readings) ·
#  PART 0 ON THE BOX (OFF touched; the two spine files placed; the two readings placed; the live build under the cron's own lock -> swapped,
#  13/13; spine_compare; OFF removed) · the five finance-side files placed by rename · md5 read-back · ONE restart · healthz · the gated curl ·
#  the journal · the live board read once as the owner and as amir · nothing else moved.
#  Red after placing the finance side -> the five files restored byte-identically, restart, healthz, report; the spine STAYS the new build
#  (the installer restores files, not the spine; the old builder would then fail its gate every ten minutes and keep it -- harmless).
#  No database write by the kit itself (the read-back may write the once-only (A, recheck, 'pending:1') stage event, as the brief says).
# =============================================================================
set -u
KIT="S524_AMIR_ONE_JUDGMENT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; SPN=$FIN/spine; ING=/root/marg_ingest; POR=/root/portal; AST=/root/assetapp
DBF="$FIN/finance.db"; ADB="$AST/assets.db"; SPD="$SPN/spine.db"
DMAP="${DUTY_MAP_PATH:-/root/deploy/repo/claude_code_briefs/DUTY_MAP.json}"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s524_walk_$STAMP"
SVC=clinic-finance
READ1=5cdf845ef938746761e3abaf77dfa49c; READ2=009cb60e8d0087dd736bc8e9e9db8efa
declare -A FROM=( [stock_app.py]=c0f0623f7d540bbdedb4369aa459405a [stockmatch.py]=fc1caf4496c4fd072e909b4d3e6784aa [shelf_figure.py]=a1e87d1ff758e8f9a8206205a457b875
                  [amir_day.py]=f1ce78e8bd788fbbb8c9774c04119af9 [marg_take.py]=a86a0f26d4fc86a51e963b6a1b561323 [spine_build.py]=11f8acb05c46aeaa72e1771d5c89922c
                  [marg_read.py]=96f565a8d138d9ce75c0ed228b471495 )
declare -A DIR=( [stock_app.py]=$FIN [stockmatch.py]=$FIN [shelf_figure.py]=$FIN [amir_day.py]=$FIN [marg_take.py]=$ING [spine_build.py]=$SPN [marg_read.py]=$SPN )
FINSIDE=(stock_app.py stockmatch.py shelf_figure.py amir_day.py marg_take.py)
SPSIDE=(spine_build.py marg_read.py)
ALL=("${SPSIDE[@]}" "${FINSIDE[@]}")
declare -A TO
NOTT=("$SPN/spine_read.py" "$SPN/spine_evidence.py" "$SPN/spine_rules.json" "$FIN/stock_amir.html" "$FIN/stock_hub.html" "$FIN/reports_watch.py" "$FIN/item_alias.py"
      "$FIN/qty_words.py" "$FIN/loss_piles.py" "$FIN/stock_watch.py" "$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json")
declare -A NOTT_PIN=( ["$SPN/spine_read.py"]=712a1e4e ["$SPN/spine_evidence.py"]=0fcf6c64 ["$SPN/spine_rules.json"]=dd6c7616 ["$FIN/stock_amir.html"]=2e41e406 )
mkdir -p "$WALK/noring" || exit 1
export ORDER_PUSH_STUB="$WALK/installer_pushes.jsonl" RING_PORTAL_DIR="$WALK/noring" REPORTS_NTFY_STUB="$WALK/installer_ntfy_stub.jsonl"
unset ORDER_PUSH_NONE ORDER_TODAY ORDER_TICK ORDER_CLOCK
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
jget() { "$SPY" -c "import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])" "$1" "$2" 2>/dev/null; }
state_now() { "$SPY" -c "
import sqlite3,sys
c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True)
r=c.execute('SELECT MAX(count_id) FROM stock_voucher_line').fetchone()
root=int(r[0]) if r and r[0] else 0
print('stage events of count %d: %s' % (root, c.execute('SELECT stage, event, ref, at, detail FROM stock_stage_event WHERE count_id=? ORDER BY id', (root,)).fetchall()))
" "$DBF"; }
spine_meta() { "$SPY" -c "
import sqlite3,sys
c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True)
m=dict(c.execute('SELECT key,value FROM sp_meta').fetchall())
g=c.execute('SELECT COUNT(*), SUM(ok) FROM sp_gate WHERE blocking=1').fetchone()
print('built %s · build_version %s · blocking gate %s/%s · checkable to %s · pending %s' % (m.get('built'), m.get('build_version'), g[1], g[0], (m.get('checkable') or '').split(',')[-1], m.get('pending') or 'none'))
" "$1"; }
OFF_TOUCHED=0
off_clear() { [ "$OFF_TOUCHED" = 1 ] && rm -f "$SPN/OFF" && OFF_TOUCHED=0 && say "   /root/finance/spine/OFF removed"; }
bail() { say "$1"; off_clear; rm -rf "$WALK"; exit "${2:-1}"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [0/14] SUMS.md5 gate failed - nothing done"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [0/14] KIT_ID.txt names another kit - nothing done"; exit 1; }
. "$KDIR/PINS.sh" || { say "!! [0/14] PINS.sh missing - nothing done"; exit 1; }
AT=1; for f in "${ALL[@]}"; do [ "$(m5 "${DIR[$f]}/$f")" = "${TO[$f]}" ] || AT=0; done
if [ "$AT" = 1 ]; then
  say "-- ALREADY INSTALLED: the seven files are at the kit's pins; $SVC $(systemctl is-active "$SVC"); healthz $(health http://127.0.0.1:8106/finance/healthz)"
  say "   spine: $(spine_meta "$SPD")"; say "   $(state_now)"; rm -rf "$WALK"; exit 0
fi
# ---- 1: the lock -----------------------------------------------------------------------------------------------------------------------
if [ "${DRY:-0}" = 1 ]; then say "[1/14] DRY RUN: no lock, no backup, nothing placed, nothing written (Part 0 runs in scratch only)"
elif mkdir "$LOCK" 2>/dev/null; then echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/14] build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then say "[1/14] the build lock is already held by $KIT"
else say "!! [1/14] the build lock is held by '$(cat "$LOCK/owner" 2>/dev/null)' (made $(stat -c %y "$LOCK" 2>/dev/null)) - another build is installing; nothing done"; rm -rf "$WALK"; exit 3; fi
# ---- 2: gates --------------------------------------------------------------------------------------------------------------------------
"$VPY" -c "import flask, openpyxl" 2>/dev/null || bail "!! [2/14] the venv python lacks flask or openpyxl; nothing placed"
for k in "$DBF" "$ADB" "$SPD" "$POR/portal.py" "$POR/tile_grants.json" "$DMAP" "$SPN/readings/$READ1.json" "$SPN/readings/$READ2.json" "$ING/archive"; do
  [ -e "$k" ] || bail "!! [2/14] $k must be reachable - nothing placed"; done
for f in "${ALL[@]}"; do
  [ "$(m5 "${DIR[$f]}/$f")" = "${FROM[$f]}" ] || bail "!! [2/14] ${DIR[$f]}/$f is $(m5 "${DIR[$f]}/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing placed"
done
[ "$(jget "$DMAP" version)" = 10 ] || bail "!! [2/14] $DMAP is not version 10 (it reads $(jget "$DMAP" version)) - pull the repository first; nothing placed"
[ "$(m5 "$DMAP")" = "${TO[DUTY_MAP.json]}" ] || bail "!! [2/14] $DMAP is $(m5 "$DMAP"), not the kit's pin ${TO[DUTY_MAP.json]} - nothing placed"
declare -A NT0
for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"
say "[2/14] gates green (SUMS, KIT_ID, PINS, flask+openpyxl, the databases, the portal, the two readings, the archive); the seven files at their FROM pins; DUTY_MAP.json v10 at its pin"
for f in "${NOTT[@]}"; do p="${NOTT_PIN[$f]:-}"; [ -n "$p" ] && [ "${NT0[$f]:0:8}" != "$p" ] && say "   must not move: $f is ${NT0[$f]} (the brief read $p…: moved before this run -- recorded; only a change DURING this install is a fault)"; done
# ---- 3-4: build, compile ---------------------------------------------------------------------------------------------------------------
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s524.py --finance "$FIN" --spine "$SPN" --ingest "$ING" --only "$(IFS=,; echo "${ALL[*]}")" --out "$WALK/built" | sed 's/^/   /'
for f in "${ALL[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || bail "!! [3/14] the built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing placed"; done
say "[3/14] live bytes + the anchored edits give the seven pinned files (DUTY_MAP.json and .md were built from v9 when the kit was packed; the clone's copy is at its pin, gate 2)"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && for f in "${ALL[@]}"; do cp -p "$WALK/built/$f" "$WALK/cc/built_$f"; done
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || bail "!! [4/14] compile on both pythons failed - nothing placed"
rm -rf "$WALK/cc/__pycache__"
say "[4/14] the seven built files and the kit's scripts compile on /usr/bin/python3 and the venv python (a scratch copy)"
# ---- 5: Part 0 in scratch --------------------------------------------------------------------------------------------------------------
P0="$WALK/p0"
mkdir -p "$P0/old_old" "$P0/new_new" "$P0/old_new" "$P0/new_old" "$P0/spine_old" "$P0/spine_new" || exit 1
cp -rp "$SPN/readings" "$P0/readings_old" && cp -rp "$P0/readings_old" "$P0/readings_new" || bail "!! [5/14] no scratch copy of the readings"
cp -p "$SPN"/*.py "$SPN"/*.json "$P0/spine_old/" && cp -p "$SPN"/*.py "$SPN"/*.json "$P0/spine_new/" && cp -p "$WALK/built/spine_build.py" "$WALK/built/marg_read.py" "$P0/spine_new/" || bail "!! [5/14] no scratch spine folders"
copydb "$SPD" "$P0/live_spine.db" || bail "!! [5/14] no copy of the live spine"
say "   re-reading the two refused exports of 08-Oct with the new reader (scratch readings only):"
"$VPY" -B "$KDIR/reread_s524.py" --spine-dir "$P0/spine_new" --archive "$ING/archive" --readings "$P0/readings_new" --md5 "$READ1" --md5 "$READ2" | mask | sed 's/^/   /'
[ -s "$P0/readings_new/$READ1.json" ] && [ -s "$P0/readings_new/$READ2.json" ] || bail "!! [5/14] the re-read did not write both readings - nothing placed"
p0build() { ( cd "$2" && "$VPY" -B spine_build.py --readings "$3" --out "$4/spine.db" --finance-db "$DBF" > "$4/build.log" 2>&1 ); echo $?; }
RC_OO=$(p0build oo "$P0/spine_old" "$P0/readings_old" "$P0/old_old")
RC_NN=$(p0build nn "$P0/spine_new" "$P0/readings_new" "$P0/new_new")
RC_ON=$(p0build on "$P0/spine_old" "$P0/readings_new" "$P0/old_new")
RC_NO=$(p0build no "$P0/spine_new" "$P0/readings_old" "$P0/new_old")
say "   gate lines BEFORE (the old builder on the old readings, exit $RC_OO):"; grep -E '^  (FAIL|ok  )' "$P0/old_old/build.log" | cut -c1-200 | mask | sed 's/^/      /'
say "   gate lines AFTER (the new builder on the re-read readings, exit $RC_NN):"; grep -E '^  (FAIL|ok  )' "$P0/new_new/build.log" | cut -c1-200 | mask | sed 's/^/      /'
say "   cross: old builder / new readings exit $RC_ON gate $(jget "$P0/old_new/spine_state.json" gate); new builder / old readings exit $RC_NO gate $(jget "$P0/new_old/spine_state.json" gate)"
[ "$RC_OO" = 3 ] && [ "$(jget "$P0/old_old/spine_state.json" gate)" = "11/13" ] || bail "!! [5/14] the control (the OLD builder on the OLD readings) did not fail 11/13 as the box does -- the evidence moved; nothing placed" 4
if [ "$RC_NN" != 0 ] || [ "$(jget "$P0/new_new/spine_state.json" passed)" != True ]; then
  say "!! [5/14] PART 0 DOES NOT PASS: the new builder on the re-read readings gives $(jget "$P0/new_new/spine_state.json" gate) -- a THIRD cause; the whole kit stops here (nothing placed):"
  grep -E '^  FAIL' "$P0/new_new/build.log" | cut -c1-600 | mask | sed 's/^/      /'
  bail "   see the brief, Part 0 step 3" 4
fi
say "[5/14] Part 0 in scratch: the old builder fails 11/13 on the old readings (control); the new builder passes 13/13 on the re-read readings: $(spine_meta "$P0/new_new/spine.db")"
# ---- 6-7: scratch copies, the walk ------------------------------------------------------------------------------------------------------
R="$WALK/run"
for side in new old; do
  mkdir -p "$R/$side/finance/finance_ui" "$R/$side/finance/spine" "$R/$side/marg_ingest" || exit 1
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/$side/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$R/$side/finance/finance_ui/"; cp -p "$SPN"/*.py "$SPN"/*.json "$R/$side/finance/spine/" 2>/dev/null
  cp -p "$ING"/*.py "$ING"/*.json "$R/$side/marg_ingest/" 2>/dev/null
  [ -f "$R/$side/finance/finance_app.py" ] && [ -f "$R/$side/marg_ingest/marg_take.py" ] || bail "!! [6/14] no scratch copy of the finance / ingest folders - nothing placed"
done
for f in stock_app.py stockmatch.py shelf_figure.py amir_day.py; do cp -p "$WALK/built/$f" "$R/new/finance/$f"; done
cp -p "$WALK/built/marg_take.py" "$R/new/marg_ingest/marg_take.py"
cp -p "$WALK/built/spine_build.py" "$WALK/built/marg_read.py" "$R/new/finance/spine/"
mkdir -p "$R/por" || exit 1
for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$R/por/"; done   # never the live secret, never the user store
cp -p "$POR/tile_grants.json" "$R/por/"
copydb "$DBF" "$R/scratch.db" && copydb "$ADB" "$R/scratch_assets.db" || bail "!! [6/14] no scratch copies - nothing placed"
say "[6/14] scratch copies: the finance and ingest folders twice (NEW with the built files, OLD as it is), the portal's code; finance.db and assets.db by the backup API; the spine = Part 0's new build"
WOUT="$( cd "$R" && timeout 3000 "$VPY" -B "$KDIR/walk_s524.py" --kit "$KDIR" --work "$R/w" --run "$R" --por "$R/por" --db "$R/scratch.db" --adb "$R/scratch_assets.db" \
         --spine "$P0/new_new/spine.db" --p0 "$P0" --duty-map "$DMAP" 2>&1 )"
echo "$WOUT" | mask | cut -c1-1800 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S524 GREEN" || bail "!! [7/14] walk_s524 red - nothing placed"
say "[7/14] walk_s524 green on scratch copies; every named control red on the old files (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed, nothing written"; rm -rf "$WALK"; exit 0; fi
# ---- 8-9: re-check, backups ---------------------------------------------------------------------------------------------------------------
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || bail "!! [8/14] the build lock is not held by $KIT - nothing placed"
for f in "${ALL[@]}"; do [ "$(m5 "${DIR[$f]}/$f")" = "${FROM[$f]}" ] || bail "!! [8/14] ${DIR[$f]}/$f moved during the walk - nothing placed"; done
say "[8/14] the lock is held by $KIT; the seven FROM pins still stand after the walk"
say "   before: $(state_now)"
declare -A BAK
for f in "${ALL[@]}"; do
  BAK[$f]="${DIR[$f]}/$f.bak_S524_${FROM[$f]:0:8}"
  \cp -p "${DIR[$f]}/$f" "${BAK[$f]}" && [ "$(m5 "${BAK[$f]}")" = "${FROM[$f]}" ] || bail "!! [9/14] the backup of $f does not read back - nothing placed"
done
copydb "$DBF" "$FIN/finance.db.bak_S524_$STAMP" && [ -s "$FIN/finance.db.bak_S524_$STAMP" ] || bail "!! [9/14] database backup failed - nothing placed"
for m in $READ1 $READ2; do
  \cp -p "$SPN/readings/$m.json" "$SPN/readings/$m.json.bak_S524_$(m5 "$SPN/readings/$m.json" | cut -c1-8)" || bail "!! [9/14] the backup of reading $m does not read back - nothing placed"
done
say "[9/14] seven .bak_S524_<from8> beside the files; $FIN/finance.db.bak_S524_$STAMP by the backup API ($(stat -c %s "$FIN/finance.db.bak_S524_$STAMP") bytes); the two readings backed up beside themselves"
putfile() { \cp -p "$1" "$2.s524_new" && mv -f "$2.s524_new" "$2"; }
restore_spine() {
  say "!! RED in Part 0 on the box ($1) - restoring the two spine files and the two readings byte-identically; the spine.db was not swapped"
  for f in "${SPSIDE[@]}"; do putfile "${BAK[$f]}" "${DIR[$f]}/$f"; done
  for m in $READ1 $READ2; do b="$(ls "$SPN/readings/$m.json.bak_S524_"* 2>/dev/null | head -1)"; [ -n "$b" ] && putfile "$b" "$SPN/readings/$m.json"; done
  for f in "${SPSIDE[@]}"; do say "   ${DIR[$f]}/$f $(m5 "${DIR[$f]}/$f") (FROM ${FROM[$f]})"; done
  bail "   nothing of the finance side placed; the lock stays held until the report" 1
}
# ---- 10: Part 0 on the box ---------------------------------------------------------------------------------------------------------------
touch "$SPN/OFF" && OFF_TOUCHED=1 && say "   /root/finance/spine/OFF touched (the ten-minute evidence+build skips itself while Part 0 places)"
for f in "${SPSIDE[@]}"; do putfile "$WALK/built/$f" "${DIR[$f]}/$f" || restore_spine "copy $f"; [ "$(m5 "${DIR[$f]}/$f")" = "${TO[$f]}" ] || restore_spine "md5 read-back $f"; done
for m in $READ1 $READ2; do putfile "$P0/readings_new/$m.json" "$SPN/readings/$m.json" || restore_spine "reading $m"; [ "$(m5 "$SPN/readings/$m.json")" = "$(m5 "$P0/readings_new/$m.json")" ] || restore_spine "reading $m read-back"; done
BUILT0="$("$SPY" -c "import sqlite3,sys; print(sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True).execute(\"SELECT value FROM sp_meta WHERE key='built'\").fetchone()[0])" "$SPD")"
# the live build, exactly the cron's line, under the cron's own lock (its flock -n then skips); OFF is removed inside, just before the build
( cd "$SPN" && flock -w 600 /tmp/spine.lock sh -c "rm -f OFF; $VPY -B spine_build.py --readings readings --out spine.db --finance-db $DBF" > "$WALK/live_build.log" 2>&1 ); RC_LIVE=$?
OFF_TOUCHED=0
grep -E '^  (FAIL|ok  )|SPINE BUILT|GATE FAILED' "$WALK/live_build.log" | cut -c1-200 | mask | sed 's/^/   /'
[ "$RC_LIVE" = 0 ] && [ "$(jget "$SPN/spine_state.json" passed)" = True ] && [ "$(jget "$SPN/spine_state.json" gate)" = "13/13" ] || { touch "$SPN/OFF"; OFF_TOUCHED=1; restore_spine "the live build did not swap (exit $RC_LIVE, $(jget "$SPN/spine_state.json" gate))"; }
BUILT1="$("$SPY" -c "import sqlite3,sys; print(sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True).execute(\"SELECT value FROM sp_meta WHERE key='built'\").fetchone()[0])" "$SPD")"
[ "$BUILT1" \> "$BUILT0" ] || restore_spine "sp_meta.built did not move ($BUILT0 -> $BUILT1)"
( cd "$SPN" && "$VPY" -B spine_compare.py > "$WALK/compare.log" 2>&1 ) || say "   (spine_compare.py exited non-zero; its witness file is read below as it is)"
say "[10/14] Part 0 on the box: spine_build.py $(m5 "$SPN/spine_build.py" | cut -c1-8), marg_read.py $(m5 "$SPN/marg_read.py" | cut -c1-8) placed; the two readings placed; the live build SWAPPED: $(spine_meta "$SPD")"
say "   spine_state.json: passed $(jget "$SPN/spine_state.json" passed), gate $(jget "$SPN/spine_state.json" gate), last_success $(jget "$SPN/spine_state.json" last_success_iso); sp_meta.built $BUILT0 -> $BUILT1; OFF removed"
say "   spine_compare_latest.txt, first eight lines:"; head -8 "$SPN/spine_compare_latest.txt" | mask | sed 's/^/      /'
# ---- 11: the finance side placed ----------------------------------------------------------------------------------------------------------
restore() {
  say "!! RED after placing ($1) - restoring the five finance-side files byte-identically (the spine stays the new build)"
  for f in "${FINSIDE[@]}"; do putfile "${BAK[$f]}" "${DIR[$f]}/$f"; done
  systemctl restart "$SVC" || true; sleep 8
  for f in "${FINSIDE[@]}"; do say "   ${DIR[$f]}/$f $(m5 "${DIR[$f]}/$f") (FROM ${FROM[$f]})"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC") · $(state_now)"
  rm -rf "$WALK"; exit 1
}
for f in "${FINSIDE[@]}"; do
  putfile "$WALK/built/$f" "${DIR[$f]}/$f" || restore "copy $f"
  [ "$(m5 "${DIR[$f]}/$f")" = "${TO[$f]}" ] || restore "md5 read-back $f"
done
cmp -s "$FIN/stock_app.py" "$R/new/finance/stock_app.py" && cmp -s "$ING/marg_take.py" "$R/new/marg_ingest/marg_take.py" || restore "a placed file is not the walk's file"
say "[11/14] the five finance-side files placed by rename; every md5 read back = its TO pin; byte-identical to the walk's NEW copies"
# ---- 12: restart, health ------------------------------------------------------------------------------------------------------------------
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz); say "health : finance healthz $c1"
[ "$c1" = 200 ] || restore "finance healthz"
c=$(health "http://127.0.0.1:8106/finance/stock/page/amir?count=1"); say "         /finance/stock/page/amir $c (302/401 = the login gate, expected)"
[ "$c" = 302 ] || [ "$c" = 401 ] || restore "the gated page answered $c"
c=$(health "http://127.0.0.1:8106/finance/stock/page/hub"); say "         /finance/stock/page/hub $c (302/401 = the login gate, expected)"
[ "$c" = 302 ] || [ "$c" = 401 ] || restore "the gated hub answered $c"
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
[ "$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')" = 0 ] || restore "$SVC journal errors"
say "[12/14] $SVC active (restarted once, $T0); healthz 200; the gated pages answer the gate; no error in its journal"
# ---- 13: the live board, read once as the owner and as amir --------------------------------------------------------------------------------
mkdir -p "$R/rb/nosso"
RB="$( cd "$FIN" && FINANCE_DB="$DBF" FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR="$R/rb/nosso" timeout 600 "$VPY" -B - <<'PYEOF' 2>&1
import sqlite3, sys, time
sys.path.insert(0, ".")
import finance_app as fa
import stock_app as SA
con = sqlite3.connect("file:/root/finance/finance.db?mode=ro", uri=True)
root = SA._s446_root(con)
ev0 = con.execute("SELECT stage, event, ref, at, detail FROM stock_stage_event WHERE count_id=? ORDER BY id", (root,)).fetchall()
c = fa.app.test_client()
for who, role in (("manoj", "doctor"), ("amir", "staff")):
    t0 = time.perf_counter()
    r = c.get("/finance/stock/api/pad/amir/%d" % root, headers={"X-Clinic-User": who, "X-Clinic-Role": role})
    ms = int((time.perf_counter() - t0) * 1000)
    j = r.get_json(silent=True) or {}
    rn = (j.get("renames") or {}).get("rows") or []
    st = j.get("stage") if isinstance(j.get("stage"), dict) else {}
    print("as %s: board %s in %d ms; stage %s; proof_state %r; proof_hi %r; renames_ready %r (%d rows, %d still to do); vouchers listed %d"
          % (who, r.status_code, ms, st.get("stage"), j.get("proof_state"), j.get("proof_hi"), j.get("renames_ready"), len(rn), sum(1 for x in rn if x.get("state") == "planned"),
             len(((j.get("made") or {}).get("vouchers_flat") or []))))
r = c.get("/finance/stock/api/pad/hub/%d" % root, headers={"X-Clinic-User": "manoj", "X-Clinic-Role": "doctor"})
j = r.get_json(silent=True) or {}
P = j.get("proof") or {}
print("hub step 7 as the owner: %s; state %r; text %r; rows %s" % (r.status_code, P.get("state"), P.get("text"), [(x.get("item"), x.get("why")) for x in (P.get("rows") or [])][:6]))
O = j.get("ortho") or {}
print("orthotic section: ok %r; proof condition %r" % (O.get("ok"), [(x.get("ok"), x.get("en")) for x in (O.get("conds") or []) if x.get("key") == "proof"]))
r = c.get("/finance/amir/step/6", headers={"X-Clinic-User": "amir", "X-Clinic-Role": "staff"})
h = r.get_data(as_text=True)
import re
tx = [re.sub(r"\s+", " ", x).strip() for x in re.findall(r">([^<]{3,300})<", h)]
print("amir's step 6: %s; %s" % (r.status_code, [x for x in tx if x.startswith(("Orthotic", "Naam badlo", "Ek orthotic", "Marg sudhar"))][:5]))
print("'hona chahiye' on step 6: %s" % ("hona chahiye" in h))
ev1 = con.execute("SELECT stage, event, ref, at, detail FROM stock_stage_event WHERE count_id=? ORDER BY id", (root,)).fetchall()
print("stage events of count %d: %d before the read, %d after%s" % (root, len(ev0), len(ev1), (" -- NEW: %s" % ev1[len(ev0):]) if len(ev1) > len(ev0) else " (none written)"))
print("READ_BACK OK")
PYEOF
)"
echo "$RB" | mask | cut -c1-1200 | sed 's/^/   /'
echo "$RB" | grep -q "^READ_BACK OK" || restore "the read of the live board"
say "[13/14] the live board, hub step 7, the orthotic section and Amir's step 6 read once (above: what they say, and whether the read wrote a stage event)"
# ---- 14: nothing else moved -------------------------------------------------------------------------------------------------------------
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ -e "$SPN/OFF" ] && restore "/root/finance/spine/OFF is still there"
[ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz at the end"
say "[14/14] nothing else moved (the thirteen must-not-move files, the crontab); OFF gone; healthz 200"
say "   after : $(state_now)"
for f in "${ALL[@]}"; do md5sum "${DIR[$f]}/$f"; done
rm -rf "$WALK"
say "   done · healthz 200 · backups: seven .bak_S524_<from8>, $FIN/finance.db.bak_S524_$STAMP, the two readings · the lock stays held by $KIT until the report is written"
say "$KIT: DONE"
