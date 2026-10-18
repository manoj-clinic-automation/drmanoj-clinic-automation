#!/bin/bash
# =============================================================================
#  install_S587_MORNING_FLOW.sh · kit S587 (18-Oct-2026) · brief claude_code_briefs/S587_MORNING_FLOW.md (v2) · D740, D737; F-926 F-927 F-933 F-936
#
#  Run from a copy of the kit folder (or from /root/deploy/repo/deploy_kits/S587_MORNING_FLOW), 08:00-23:59 IST only:
#    rm -rf /tmp/s587kit && cp -rp <kit> /tmp/s587kit && bash /tmp/s587kit/install_S587_MORNING_FLOW.sh
#  (DRY=1 before bash: every gate, the scratch sides and both walks, nothing written, no lock.)
#
#  THE MORNING FLOW. (1) D740: a closing printed as on today and taken before the day's first sale is the START of that day (the end of
#  yesterday plus the morning's Marg work) once verified item by item against the day's sale report and Amir's purchase export
#  (stock_figure: captures / start_ready / verify_start; the record finance.db.stock_start_capture, one new table, created on first use).
#  (2) R2-B3: a start / early-morning capture never counts the printed day's purchases twice (marg(); approx purchase_on_start).
#  (3) R2-B4: purchase_cover -- the reach, the newest exports, or Amir's VISIT COVER (the last export after his last bill-entry tap covers
#  every closing until his next visit); tryable's purchase half, read by the proof and by shelf_figure.record_gaps alike. (4) R2-B5: a voucher
#  that agrees on any usable, sale-covered closing is proven at once; 'wrong' only from the newest closing inside both reaches. (5) F-933:
#  a key Amir marked done after the judged closing is pending_fix, the owner's line "ITEM: Amir marked it done dd-mm hh:mm -- judged on the
#  next closing taken after it". (6) Amir's page: Marg sudhar is position 3, the Export position 4 (ids unchanged); the re-export line when a
#  bill is entered after the export. (7) Two settings on 'Counts & watch'. (8) F-936: the stock-now fifth heading on the items table.
#   /root/finance/stock_figure.py   72b9135a -> TO   captures (start captures), purchase_cover / visit_cover, tryable(con, ctx), marg (R2-B3), verify-start CLI
#   /root/finance/shelf_figure.py   14ef2c24 -> TO   ONE edit: record_gaps passes con / ctx to tryable
#   /root/finance/stock_app.py      1883807d -> TO   _s524_table on captures(); every usable try; N inside both reaches; pending_fix; the owner's line; _s524_closings / early_bill retired
#   /root/finance/amir_day.py       3deca3b9 -> TO   ORDER / pos / id_at; the banner, 'Step N of 7', the redirects and the visit summary by position; the re-export line; KIT
#   /root/finance/stock_watch.py    555202ce -> TO   count.start_capture, count.start_unexplained_max; settings(); start_capture_lines on Needs-you
#   /root/finance/stock_now.html    ff415eb2 -> TO   the items table by id (#itemtbl); the fifth heading appended there
#  Read only, must not move (this kit was built reading them): loss_piles, stockmatch, spine_build, selftest_spine, spine_read, item_alias,
#  reports_tile, qty_words, DUTY_MAP.json; and proved unmoved: finance_app, portal.py, tile_grants.json, the crontab, spine.db's schema.
#  ORDER: gates (window, lock, SUMS, KIT_ID, PINS) -> pins (ALREADY first) + the read-only md5s printed -> the spine green and fresh -> build from
#  the live bytes -> compile (both pythons) -> scratch: the finance folder twice, the databases and the spine by the backup API; the walk on the
#  OLD files (every control red) then on the NEW files (green) -> DRY stops -> the install-day state on the OLD and the NEW files -> backups ->
#  DOCTOR_AUTO_OFF -> the six files staged and renamed in ONE command -> ONE restart of clinic-finance -> healthz 200, the pages 302 -> journal
#  clean -> stock_figure.py verify-start once on the live database (the first verdicts, quoted) -> the state AFTER -> nothing else moved ->
#  md5 read-back -> DOCTOR_AUTO_OFF removed. Red after placing: the six files put back in one command, one restart, healthz; the new table
#  stays (additive; its reverse is one DROP in the README, never run here). The build lock stays held by S587 until the report is written.
# =============================================================================
set -u
KIT="S587_MORNING_FLOW"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
SPN="$FIN/spine"
POR="${POR:-/root/portal}"
MARG="${MARG:-/root/marg_ingest}"
ADB="${ADB:-/root/assetapp/assets.db}"
REPO="${REPO:-/root/deploy/repo}"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
DMAP="$REPO/claude_code_briefs/DUTY_MAP.json"
EDITED="stock_figure.py shelf_figure.py stock_app.py amir_day.py stock_watch.py stock_now.html"
declare -A FROM TO READ
FROM[stock_figure.py]=72b9135ab00db0af2fe8e54091147bb5
FROM[shelf_figure.py]=14ef2c24e272ae8ea684615ae82b6cb5
FROM[stock_app.py]=1883807d7c0872b805f6101e92206878
FROM[amir_day.py]=3deca3b95380165d81ae4a8406a53d75
FROM[stock_watch.py]=555202ce50b8df0b5111b5c56952efda
FROM[stock_now.html]=ff415eb22ee1ad94a95f2c87365341a3
READ[loss_piles.py]=2b9023fd06aadc0ddaef30e2f26eccb3
READ[stockmatch.py]=623cb6f1db2640edd6fe2b8ef7f98837
READ[spine/spine_build.py]=e3d3ed85973eab2df0326dc9621e230e
READ[spine/selftest_spine.py]=7d0edb4aafb17c83cf07be1052623f76
READ[spine/spine_read.py]=712a1e4ef827f6be4e8b23415c3ceb62
READ[item_alias.py]=111a8e4877035e5a02665dd586e01b06
READ[reports_tile.py]=535b579011004ba2e8d8c41070067b2c
READ[qty_words.py]=706db7ccfa7489fb8d296f663590f107
DMAP_MD5=891defd8431e291b1a152f9e3c85f8c6
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s587_inst_$STAMP"
PLACED=0
DBBAK="$FIN/finance.db.bak_S587_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S587_${FROM[$1]:0:8}"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
on_exit() { rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
schema5() { "$APY" -c "import sqlite3,sys,hashlib; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); print(hashlib.md5('\n'.join(sorted(r[0] or '' for r in c.execute(\"SELECT sql FROM sqlite_master WHERE type IN ('table','index')\"))).encode()).hexdigest())" "$1" 2>/dev/null; }
jget() { "$APY" -c "import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], ''))" "$1" "$2" 2>/dev/null; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the six files back in one command"
  \cp -p "$(bak stock_figure.py)" "$FIN/stock_figure.py" && \cp -p "$(bak shelf_figure.py)" "$FIN/shelf_figure.py" && \cp -p "$(bak stock_app.py)" "$FIN/stock_app.py" \
    && \cp -p "$(bak amir_day.py)" "$FIN/amir_day.py" && \cp -p "$(bak stock_watch.py)" "$FIN/stock_watch.py" && \cp -p "$(bak stock_now.html)" "$FIN/stock_now.html"
  rm -f "$FIN"/.*.s587
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  for n in $EDITED; do say "   $FIN/$n $(m5 "$FIN/$n") (expected ${FROM[$n]})"; done
  say "   after the restore: finance healthz $h"
  say "   the database backup stays: $DBBAK; the table stock_start_capture (additive) stays -- its reverse is in the README, never run here"
  rm -f "$OFFSW"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl timeout grep tail sleep find sed sort cmp crontab; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
command -v "$SYSTEMCTL" >/dev/null 2>&1 || { say "!! preflight: $SYSTEMCTL missing - nothing installed"; exit 1; }
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"
[ "$HH" -ge 8 ] || { say "!! [1/12] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 08:00-23:59 IST (the spine builds */10 8-23) - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/12] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/12] KIT_ID.txt names another kit - nothing installed"; exit 1; }
. "$KDIR/PINS.sh" || { say "!! [1/12] PINS.sh missing - nothing installed"; exit 1; }
for n in $EDITED; do [ -f "$FIN/$n" ] || { say "!! [1/12] $FIN/$n is not there - nothing installed"; exit 1; }; done
ALL_TO=1; for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then say "-- ALREADY INSTALLED: the six files are the kit's. Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null); healthz $(health /finance/healthz)"; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/12] DRY RUN: kit gates green (SUMS, KIT_ID, PINS, the window); no lock, no backup, nothing placed, nothing written"
elif mkdir "$LOCK" 2>/dev/null; then
  echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/12] kit gates green (SUMS, KIT_ID, PINS, the window); the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  say "[1/12] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/12] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again when it is free."
  exit 3
fi

for n in $EDITED; do C="$(m5 "$FIN/$n")"; [ "$C" = "${FROM[$n]}" ] || { say "!! [2/12] $FIN/$n is $C, expected ${FROM[$n]} - it changed after the brief: STOP, nothing installed"; exit 1; }; done
say "[2/12] live pins exact: $(for n in $EDITED; do printf '%s %s . ' "$n" "${FROM[$n]:0:8}"; done)"
say "       the read-only files' live md5s (the brief, section 1):"
for n in loss_piles.py stockmatch.py spine/spine_build.py spine/selftest_spine.py spine/spine_read.py item_alias.py reports_tile.py qty_words.py; do
  C="$(m5 "$FIN/$n")"; say "         $n $C"
  [ "$C" = "${READ[$n]}" ] || { say "!! [2/12] $FIN/$n is $C, not ${READ[$n]} - this kit was built reading it: STOP, nothing installed"; exit 1; }
done
[ -f "$DMAP" ] || { say "!! [2/12] $DMAP missing - nothing installed"; exit 1; }
C="$(m5 "$DMAP")"; say "         DUTY_MAP.json $C"
[ "$C" = "$DMAP_MD5" ] || { say "!! [2/12] DUTY_MAP.json is $C, not $DMAP_MD5 - STOP, nothing installed"; exit 1; }
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$SPN/spine.db" ] && [ -f "$SPN/spine_state.json" ] || { say "!! [2/12] a database or the spine is missing - nothing installed"; exit 1; }
SP_OK="$(jget "$SPN/spine_state.json" passed)"; SP_GATE="$(jget "$SPN/spine_state.json" gate)"; SP_AT="$(jget "$SPN/spine_state.json" last_success_iso)"
SP_AGE="$("$APY" -c "import sys,datetime as d; t=d.datetime.fromisoformat(sys.argv[1]); print(int((d.datetime.now(t.tzinfo)-t).total_seconds()//60))" "$SP_AT" 2>/dev/null || echo 9999)"
GATE_N="${SP_GATE%/*}"; GATE_D="${SP_GATE#*/}"
[ "$SP_OK" = True ] && [ -n "$GATE_N" ] && [ "$GATE_N" = "$GATE_D" ] && [ "$SP_AGE" -le 30 ] \
  || { say "!! [2/12] the spine is red or stale (passed $SP_OK, gate $SP_GATE, last success $SP_AT, $SP_AGE min ago) - the kit depends on it; nothing installed (charter 1b)"; exit 4; }
NOTT=("$FIN/loss_piles.py" "$FIN/stockmatch.py" "$FIN/item_alias.py" "$FIN/reports_tile.py" "$FIN/qty_words.py" "$FIN/finance_app.py" "$FIN/purchase_app.py" "$FIN/order_rules.py" "$FIN/porders_s454.py" "$SPN/spine_build.py" "$SPN/spine_read.py" "$SPN/selftest_spine.py" "$POR/portal.py" "$POR/tile_grants.json" "$DMAP")
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"; SCHEMA0="$(schema5 "$SPN/spine.db")"
[ -n "$SCHEMA0" ] || { say "!! [2/12] the spine's schema could not be read - nothing installed"; exit 1; }
say "       charter 1b: the spine passed $SP_GATE, last success $SP_AT ($SP_AGE min ago); spine.db schema $SCHEMA0"
say "       the live start-capture record: $(if "$APY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); sys.exit(0 if c.execute(\"SELECT 1 FROM sqlite_master WHERE name='stock_start_capture'\").fetchone() else 1)" "$DB"; then echo "table present (rows: $("$APY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); print(c.execute('SELECT COUNT(*) FROM stock_start_capture').fetchone()[0])" "$DB"))"; else echo "no table yet (created by stock_figure on first use)"; fi)"

mkdir -p "$SCR/built" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONDONTWRITEBYTECODE=1
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile make_s587.py walk_s587.py || { say "!! [3/12] compile failed on $py - nothing installed"; exit 1; }
done
"$APY" -B make_s587.py --finance "$FIN" --out "$SCR/built" > "$SCR/make.txt" || { cat "$SCR/make.txt"; say "!! [4/12] the builder refused a live file - nothing installed"; exit 1; }
for n in $EDITED; do [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || { say "!! [4/12] rebuilt, $n is $(m5 "$SCR/built/$n"), not ${TO[$n]} - nothing installed"; exit 1; }; done
for py in "$APY" "$VPY"; do
  for n in $EDITED; do case "$n" in *.py) PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" || { say "!! [3/12] the built $n does not compile on $py - nothing installed"; exit 1; };; esac; done
done
say "[3/12] the kit's python files and the five built .py files compile on $APY and $VPY"
say "[4/12] rebuilt here from this box's live bytes ($(grep -c 'anchored once, applied' "$SCR/make.txt") anchored edits): each of the six files at its TO pin"

copydb "$DB" "$SCR/base.db" && copydb "$ADB" "$SCR/base_a.db" && copydb "$SPN/spine.db" "$SCR/spine.db" || { say "!! [5/12] no copy of the databases - nothing installed"; exit 1; }
mkside() {   # $1 = side: a copy of the live finance code (spine folder included), the ingest reader, the databases (backup API), the spine copy
  local d="$SCR/$1"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" "$d/marg_ingest/archive"
  cp -p "$FIN"/*.py "$d/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$d/finance/finance_ui/" 2>/dev/null; cp -p "$SPN"/*.py "$SPN"/*.json "$d/finance/spine/" 2>/dev/null
  for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do cp -p "$MARG/$f" "$d/marg_ingest/" || return 1; done
  cp -rp "$MARG/archive/ORDER_PENDING" "$d/marg_ingest/archive/" || return 1
  cp -p "$SCR/base.db" "$d/f.db" && cp -p "$SCR/base_a.db" "$d/a.db" && cp -p "$SCR/spine.db" "$d/finance/spine/spine.db"
}
for side in new old; do mkside "$side" || { say "!! [5/12] no scratch side '$side' - nothing installed"; exit 1; }; done
for n in $EDITED; do cp -p "$SCR/built/$n" "$SCR/new/finance/"; done
say "[5/12] scratch: the finance folder twice (NEW with the six built files, OLD as it is), finance.db, assets.db and the spine by the backup API"
ROUT="$( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s587.py" --fin "$SCR/old/finance" --db "$SCR/old/f.db" --adb "$SCR/old/a.db" --marg "$SCR/old/marg_ingest" --map "$DMAP" --dump "$SCR/dump_old" --expect-red 2>&1 )"; RRC=$?
WOUT="$( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s587.py" --fin "$SCR/new/finance" --db "$SCR/new/f.db" --adb "$SCR/new/a.db" --marg "$SCR/new/marg_ingest" --map "$DMAP" --dump "$SCR/dump_new" --old-dump "$SCR/dump_old" 2>&1 )"; WRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | mask | sed 's/^/   /'
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK S587"; then say "!! [6/12] the walk is RED on this box (exit $WRC) - nothing installed"; exit 1; fi
echo "$ROUT" | mask | grep -E "^  RED on the old files:|^  FAIL C:|^WALK OK negative|^NEGATIVE CONTROL|^  NOT RED|^WALK RED" | sed 's/^/   /'
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK negative control"; then say "!! [6/12] the negative control did not go red on the old files - the walk proves nothing; nothing installed"; echo "$ROUT" | mask | tail -30; exit 1; fi
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${FROM[$n]}" ] || { say "!! [6/12] $FIN/$n changed during the walk - nothing installed"; exit 1; }; done
say "[6/12] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "       negative control, the old files: $(echo "$ROUT" | grep "^WALK OK negative control" | tail -1 | sed 's/^WALK OK negative control S587: //')"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the scratch sides and both walks green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

# ---- 7: the install-day state on the OLD and the NEW files (fresh copies of the live database) ----------------------------------------------
statelook() {   # $1 = a scratch finance folder, or LIVE (a fresh scratch copy of /root/finance as it stands, its spine.db beside it); $2 = label
  local d="$SCR/st_$2" fin="$1"; mkdir -p "$d"
  if [ "$1" = LIVE ]; then
    mkside "st_$2" >/dev/null 2>&1 || return 1
    copydb "$SPN/spine.db" "$d/finance/spine/spine.db" || return 1
    fin="$d/finance"
  fi
  copydb "$DB" "$d/f.db" || return 1
  ( cd /tmp && timeout 900 "$APY" -B "$KDIR/walk_s587.py" --state --label "$2" --fin "$fin" --db "$d/f.db" --adb "$SCR/base_a.db" --marg "$SCR/new/marg_ingest" --map "$DMAP" 2>&1 ) | mask
}
say "[7/12] the install-day state BEFORE (the live files on a copy) and as the NEW files read the same copy:"
SB="$(statelook "$SCR/old/finance" before)"; echo "$SB" | grep -E "^STATE|^   " | sed 's/^/ /'
SN="$(statelook "$SCR/new/finance" new)"; echo "$SN" | grep -E "^STATE|^   " | sed 's/^/ /'
echo "$SB" | grep -q "^STATE OK S587" && echo "$SN" | grep -q "^STATE OK S587" || { say "!! [7/12] the install-day state could not be read - nothing placed"; exit 1; }
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/12] the build lock is not held by $KIT - nothing placed"; exit 1; }

# ---- 8: backups ---------------------------------------------------------------------------------------------------------------------------
copydb "$DB" "$DBBAK" && chmod 600 "$DBBAK" || { rm -f "$DBBAK"; say "!! [8/12] database backup failed - nothing placed"; exit 1; }
for n in $EDITED; do
  \cp -p "$FIN/$n" "$(bak $n)" || { say "!! [8/12] backup of $n failed - nothing placed"; exit 1; }
  [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ] || { say "!! [8/12] the backup of $n is not the live file - nothing placed"; exit 1; }
done
say "[8/12] backups: $(basename "$DBBAK") (sqlite backup API, $(stat -c %s "$DBBAK") bytes); $(for n in $EDITED; do printf '%s ' "$(basename "$(bak $n)")"; done)"

# ---- 9-10: the six files in ONE move, one restart -----------------------------------------------------------------------------------------
mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's; S578 must not restart a part it finds down" > "$OFFSW" || { say "!! [9/12] could not write $OFFSW - nothing placed"; exit 1; }
for n in $EDITED; do
  { \cp -p "$FIN/$n" "$FIN/.$n.s587" && cat "$SCR/built/$n" > "$FIN/.$n.s587" && [ "$(m5 "$FIN/.$n.s587")" = "${TO[$n]}" ]; } || { rm -f "$FIN"/.*.s587 "$OFFSW"; say "!! [9/12] could not stage $n - nothing placed"; exit 1; }
done
PLACED=1
mv -f "$FIN/.stock_figure.py.s587" "$FIN/stock_figure.py" && mv -f "$FIN/.shelf_figure.py.s587" "$FIN/shelf_figure.py" && mv -f "$FIN/.stock_app.py.s587" "$FIN/stock_app.py" \
  && mv -f "$FIN/.amir_day.py.s587" "$FIN/amir_day.py" && mv -f "$FIN/.stock_watch.py.s587" "$FIN/stock_watch.py" && mv -f "$FIN/.stock_now.html.s587" "$FIN/stock_now.html" || restore "placing the six files"
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] && cmp -s "$FIN/$n" "$SCR/built/$n" || restore "$n did not land at its pin"; done
say "[9/12] placed by rename in ONE command; md5 read back: $(for n in $EDITED; do printf '%s %s . ' "$n" "$(m5 "$FIN/$n" | cut -c1-8)"; done)(= the kit's TO pins, byte-identical to the walked files)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
"$SYSTEMCTL" is-active --quiet "$SVC" || restore "$SVC is not active"
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/amir); c3=$(health /finance/stock/page/now); c4=$(health /finance/stockmatch); c5=$(health /finance/porders); c6=$(health /finance/stock/page/loss); c7=$(health /finance/amir/day)
for c in "$c2" "$c3" "$c4" "$c5" "$c6" "$c7"; do case "$c" in 302|401|303) ;; *) restore "a page answered $c without a login (302 = the login gate, expected): amir $c2 / now $c3 / stockmatch $c4 / porders $c5 / loss $c6 / amir-day $c7";; esac; done
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  "$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[10/12] $SVC restarted at $T0 (nothing else) and active - healthz $c1 - /finance/amir $c2, /stock/page/now $c3, /stockmatch $c4, /porders $c5, /stock/page/loss $c6, /amir/day $c7 without a login (302 = the login gate, expected) - journal clean"

# ---- 11: the first verdicts (stock_figure verify-start on the LIVE database, once); the state AFTER; nothing else moved -------------------------
VOUT="$( cd "$FIN" && FINANCE_DB="$DB" timeout 600 "$APY" -B stock_figure.py verify-start 2>&1 )" || true
say "[11/12] stock_figure.py verify-start on the live database (the first verdicts, a record):"
echo "$VOUT" | mask | sed 's/^/        /'
echo "$VOUT" | grep -q "^start capture " || restore "verify-start printed no start capture (the record could not be written)"
say "        the install-day state AFTER placing (the live files, a fresh copy of the live database):"
SA_="$(statelook LIVE after)"; echo "$SA_" | grep -E "^STATE|^   " | sed 's/^/ /'
echo "$SA_" | grep -q "^STATE OK S587" || restore "the state after placing could not be read"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(schema5 "$SPN/spine.db")" = "$SCHEMA0" ] || restore "spine.db's schema moved -- no table may be added to the spine"
[ "$(health /finance/healthz)" = 200 ] || restore "healthz at the end"
rm -f "$OFFSW"
say "        nothing else moved (the read-only files, finance_app, the spine's files and schema, portal.py, tile_grants.json, DUTY_MAP, the crontab); healthz 200; $OFFSW removed"
say "        the order_rules tick (record_gaps) and the 06:30 stock_watch job pick the new files up on their next run"

find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0
say "[12/12] md5 read back:"
for n in $EDITED; do md5sum "$FIN/$n"; done
say "$KIT: DONE. The build lock stays held by $KIT until the report is written."
say "undo: $(for n in $EDITED; do printf '\\cp -p %s %s && ' "$(bak $n)" "$FIN/$n"; done)$SYSTEMCTL restart $SVC"
exit 0
