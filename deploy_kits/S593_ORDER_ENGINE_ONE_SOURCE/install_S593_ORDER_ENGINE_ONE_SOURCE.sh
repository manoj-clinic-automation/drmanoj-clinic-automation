#!/bin/bash
# =============================================================================
#  install_S593_ORDER_ENGINE_ONE_SOURCE.sh · kit S593 (19-Oct-2026) · brief claude_code_briefs/S593_ORDER_ENGINE_ONE_SOURCE.md (v2) · D743;
#  F-916 F-717 F-738 F-739
#
#  Run from a copy of the kit folder (or from /root/deploy/repo/deploy_kits/S593_ORDER_ENGINE_ONE_SOURCE), 08:00-23:59 IST only:
#    rm -rf /tmp/s593kit && cp -rp <kit> /tmp/s593kit && bash /tmp/s593kit/install_S593_ORDER_ENGINE_ONE_SOURCE.sh
#  (DRY=1 before bash: every gate, the scratch sides and both walks, nothing written, no lock.)
#
#  THE ORDER ENGINE ON THE ONE STOCK FUNCTION AND THE ONE ARRIVALS RULE (step 4, Kit I of S327's plan; S308 i, ii, iii, viii, Part A).
#   /root/finance/order_rules.py        79f21c1e -> TO   _s470_snap on stock_figure.marg + taps + scan_arrivals (stock_watch.Spine + one Ctx); _s470_arrivals,
#                                                        ON_ORDER_DAYS and lead_learned's dead loop retired; rhythm() from the spine; days_left(); F-738; plan()['inputs']
#   /root/finance/porders.py            a5a823bf -> TO   detect_supplies asks stock_figure.carried (rules c / d; the packs of the bill's own line); send_med refuses on darpan
#   /root/finance/porders_s454.py       83079763 -> TO   F-916: a supplier with a card not repeated under 'Ho chuke'; an earlier day's line says its date; F-739 heading counts
#   /root/finance/order_sheet.py        f00f0163 -> TO   F-717: load_pending's fallback rolls back before it goes on
#   /root/finance/darpan_kal.py         8128598f -> TO   _s485_days_left retired; _s485_line serves named fields (no why / cover_days); the add door writes days_left
#   /root/finance/spine/spine_read.py   712a1e4e -> TO   one method: purchases_by_supplier
#   /root/deploy/repo/claude_code_briefs/DUTY_MAP.json  891defd8 -> DMAP_TO  by the PUBLISH (the clone's pull), never by this installer: it reads the md5 back and says
#                                                        whether it has landed (R1-B6).
#  Read only, must not move (this kit was built reading them): stock_figure, shelf_figure, stock_watch, purchase_app, order_sheet_pdf, darpan_kal.html,
#  finance_ui/finance_approvals.html, porders.html, aaj_kaam, amir_day, spine/spine_build, spine/selftest_spine, item_alias, qty_words; and proved
#  unmoved: finance_app, portal.py, tile_grants.json, the crontab, spine.db's schema (no table added to the spine). finance.db: no table, no setting, no data step.
#  ORDER: gates (window, lock, SUMS, KIT_ID, PINS) -> pins (ALREADY first) + the read-only md5s printed -> the spine green and fresh -> build from the live bytes
#  (anchored edits, each anchor once) -> compile (both pythons) -> scratch: the finance folder twice, finance.db / assets.db / spine.db by the backup API; the walk
#  on the OLD files (every control red) then on the NEW files (green) -> DRY stops -> the install-day state on the OLD and the NEW files -> backups -> DOCTOR_AUTO_OFF
#  -> the six files staged and renamed in ONE command -> ONE restart of clinic-finance -> healthz 200, the pages 302 -> journal clean -> porders.detect_supplies once
#  on the live database (its writes quoted, by rule letter, in packs) -> the state AFTER -> nothing else moved -> md5 read-back -> DUTY_MAP.json landed / not yet ->
#  DOCTOR_AUTO_OFF removed. Red after placing: the six files put back in one command, one restart, healthz. The build lock stays held until the report is written.
# =============================================================================
set -u
KIT="S593_ORDER_ENGINE_ONE_SOURCE"
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
EDITED="order_rules.py porders.py porders_s454.py order_sheet.py darpan_kal.py spine/spine_read.py"
declare -A FROM TO READ
FROM[order_rules.py]=79f21c1ee1f763b1ac06b370e3d77b79
FROM[porders.py]=a5a823bf30661a4bf65ced39b2355500
FROM[porders_s454.py]=8307976393e6ea161f8d3a94bcb0692c
FROM[order_sheet.py]=f00f0163bdd66a074c5af261c9b80a49
FROM[darpan_kal.py]=8128598f745fca48a08472905f47da97
FROM[spine/spine_read.py]=712a1e4ef827f6be4e8b23415c3ceb62
READ[stock_figure.py]=92367a196b360f0cded4cda6a5ded700
READ[shelf_figure.py]=23b2394a7a10a99ff0c30121087813f1
READ[stock_watch.py]=c5f3ce21a785c45df58f21932cf920e7
READ[purchase_app.py]=60f2d846155659c4eddc33e4a0d42b39
READ[order_sheet_pdf.py]=7fca11db1c016ec86a0c57c5020a7079
READ[darpan_kal.html]=75d5a5b51b017abd5ad3aa408609a1ff
READ[finance_ui/finance_approvals.html]=b32da7ffe605ce2440414febb8cf7bce
READ[porders.html]=7a6799ae3c8b41e783051cd1280a6964
READ[aaj_kaam.py]=cd232b1c987417aa07d341d498c5effc
READ[amir_day.py]=3af992d9e6b6c6050b1427e34757ca78
READ[spine/spine_build.py]=e3d3ed85973eab2df0326dc9621e230e
READ[spine/selftest_spine.py]=7d0edb4aafb17c83cf07be1052623f76
READ[item_alias.py]=111a8e4877035e5a02665dd586e01b06
READ[qty_words.py]=706db7ccfa7489fb8d296f663590f107
DMAP_FROM=891defd8431e291b1a152f9e3c85f8c6
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s593_inst_$STAMP"
PLACED=0
DBBAK="$FIN/finance.db.bak_S593_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S593_${FROM[$1]:0:8}"; }
stg() { echo "$FIN/$(dirname "$1")/.$(basename "$1").s593"; }
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
  \cp -p "$(bak order_rules.py)" "$FIN/order_rules.py" && \cp -p "$(bak porders.py)" "$FIN/porders.py" && \cp -p "$(bak porders_s454.py)" "$FIN/porders_s454.py" \
    && \cp -p "$(bak order_sheet.py)" "$FIN/order_sheet.py" && \cp -p "$(bak darpan_kal.py)" "$FIN/darpan_kal.py" && \cp -p "$(bak spine/spine_read.py)" "$FIN/spine/spine_read.py"
  rm -f "$FIN"/.*.s593 "$SPN"/.*.s593
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  for n in $EDITED; do say "   $FIN/$n $(m5 "$FIN/$n") (expected ${FROM[$n]})"; done
  say "   after the restore: finance healthz $h"
  say "   the database backup stays: $DBBAK (no table, no setting of this kit to reverse)"
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
if [ "$ALL_TO" = 1 ]; then say "-- ALREADY INSTALLED: the six files are the kit's. Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null); healthz $(health /finance/healthz); DUTY_MAP.json $(m5 "$DMAP") ($([ "$(m5 "$DMAP")" = "$DMAP_TO" ] && echo landed || echo 'not yet - arrives with the publish'))"; exit 0; fi
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
for n in stock_figure.py shelf_figure.py stock_watch.py purchase_app.py order_sheet_pdf.py darpan_kal.html finance_ui/finance_approvals.html porders.html aaj_kaam.py amir_day.py spine/spine_build.py spine/selftest_spine.py item_alias.py qty_words.py; do
  C="$(m5 "$FIN/$n")"; say "         $n $C"
  [ "$C" = "${READ[$n]}" ] || { say "!! [2/12] $FIN/$n is $C, not ${READ[$n]} - this kit was built reading it: STOP, nothing installed"; exit 1; }
done
[ -f "$DMAP" ] || { say "!! [2/12] $DMAP missing - nothing installed"; exit 1; }
C="$(m5 "$DMAP")"; say "         DUTY_MAP.json (the clone) $C"
case "$C" in
  "$DMAP_FROM") MAP_STATE="FROM (the publish has not landed yet; the kit builds the new map in scratch for the walk)";;
  "$DMAP_TO") MAP_STATE="TO (the publish has landed)";;
  *) say "!! [2/12] DUTY_MAP.json is $C, neither $DMAP_FROM (FROM) nor $DMAP_TO (the kit's) - STOP, nothing installed"; exit 1;;
esac
say "         DUTY_MAP.json is at $MAP_STATE"
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$SPN/spine.db" ] && [ -f "$SPN/spine_state.json" ] || { say "!! [2/12] a database or the spine is missing - nothing installed"; exit 1; }
SP_OK="$(jget "$SPN/spine_state.json" passed)"; SP_GATE="$(jget "$SPN/spine_state.json" gate)"; SP_AT="$(jget "$SPN/spine_state.json" last_success_iso)"
SP_AGE="$("$APY" -c "import sys,datetime as d; t=d.datetime.fromisoformat(sys.argv[1]); print(int((d.datetime.now(t.tzinfo)-t).total_seconds()//60))" "$SP_AT" 2>/dev/null || echo 9999)"
GATE_N="${SP_GATE%/*}"; GATE_D="${SP_GATE#*/}"
[ "$SP_OK" = True ] && [ -n "$GATE_N" ] && [ "$GATE_N" = "$GATE_D" ] && [ "$SP_AGE" -le 30 ] \
  || { say "!! [2/12] the spine is red or stale (passed $SP_OK, gate $SP_GATE, last success $SP_AT, $SP_AGE min ago) - the kit depends on it; nothing installed (charter 1b)"; exit 4; }
NOTT=("$FIN/stock_figure.py" "$FIN/shelf_figure.py" "$FIN/stock_watch.py" "$FIN/purchase_app.py" "$FIN/order_sheet_pdf.py" "$FIN/darpan_kal.html" "$FIN/finance_ui/finance_approvals.html" "$FIN/porders.html" "$FIN/aaj_kaam.py" "$FIN/amir_day.py" "$FIN/item_alias.py" "$FIN/qty_words.py" "$FIN/finance_app.py" "$SPN/spine_build.py" "$SPN/selftest_spine.py" "$SPN/order_rehearsal.py" "$POR/portal.py" "$POR/tile_grants.json")
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"; SCHEMA0="$(schema5 "$SPN/spine.db")"
[ -n "$SCHEMA0" ] || { say "!! [2/12] the spine's schema could not be read - nothing installed"; exit 1; }
say "       charter 1b: the spine passed $SP_GATE, last success $SP_AT ($SP_AGE min ago); spine.db schema $SCHEMA0; sp_meta.built $("$APY" -c "import sqlite3,sys; print(sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True).execute(\"SELECT value FROM sp_meta WHERE key='built'\").fetchone()[0])" "$SPN/spine.db" 2>/dev/null)"
say "       the settings (the brief, section 2):"
"$APY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); [print('         %s = %s' % r) for r in c.execute(\"SELECT key, value FROM setting WHERE key IN ('order.source','order.engine_source','order.stock_basis','order.in_transit_days','order.on_order_days','order.pace_days','order.lot_history_days','arrival.bill_grace_days','arrival.back_days','porders.ortho_vendor','order.model') ORDER BY key\")]; print('         order.model exists:', bool(c.execute(\"SELECT 1 FROM setting WHERE key='order.model'\").fetchone()))" "$DB"
say "       the DUTY_MAP darpan arm's SELECT on the live database (read only; CLAUDE.md 'every duty has a door' rule 1): n = $("$APY" -c "import sqlite3,sys; print(sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True).execute(\"SELECT COUNT(DISTINCT p.supplier_norm) AS n FROM order_proposal p WHERE p.day = date('now','localtime') AND p.status = 'darpan_ok'\").fetchone()[0])" "$DB")"

mkdir -p "$SCR/built/spine" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONDONTWRITEBYTECODE=1
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile make_s593.py walk_s593.py || { say "!! [3/12] compile failed on $py - nothing installed"; exit 1; }
done
"$APY" -B make_s593.py --finance "$FIN" --map "$DMAP" --map-to "$DMAP_TO" --out "$SCR/built" > "$SCR/make.txt" || { cat "$SCR/make.txt"; say "!! [4/12] the builder refused a live file - nothing installed"; exit 1; }
for n in $EDITED; do [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || { say "!! [4/12] rebuilt, $n is $(m5 "$SCR/built/$n"), not ${TO[$n]} - nothing installed"; exit 1; }; done
[ "$(m5 "$SCR/built/DUTY_MAP.json")" = "$DMAP_TO" ] || { say "!! [4/12] the built DUTY_MAP.json is $(m5 "$SCR/built/DUTY_MAP.json"), not $DMAP_TO - nothing installed"; exit 1; }
for py in "$APY" "$VPY"; do
  for n in $EDITED; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" || { say "!! [3/12] the built $n does not compile on $py - nothing installed"; exit 1; }; done
done
say "[3/12] the kit's python files and the six built files compile on $APY and $VPY"
say "[4/12] rebuilt here from this box's live bytes ($(grep -c 'anchored once, applied' "$SCR/make.txt") anchored edits): each of the six files at its TO pin; DUTY_MAP.json at $DMAP_TO"

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
for n in $EDITED; do cp -p "$SCR/built/$n" "$SCR/new/finance/$n"; done
say "[5/12] scratch: the finance folder twice (NEW with the six built files, OLD as it is), finance.db, assets.db and the spine by the backup API"
ROUT="$( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s593.py" --fin "$SCR/old/finance" --db "$SCR/old/f.db" --adb "$SCR/old/a.db" --marg "$SCR/old/marg_ingest" --map "$DMAP" --dump "$SCR/dump_old" --expect-red 2>&1 )"; RRC=$?
WOUT="$( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s593.py" --fin "$SCR/new/finance" --db "$SCR/new/f.db" --adb "$SCR/new/a.db" --marg "$SCR/new/marg_ingest" --map "$SCR/built/DUTY_MAP.json" --dump "$SCR/dump_new" --old-dump "$SCR/dump_old" 2>&1 )"; WRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | mask | sed 's/^/   /'
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK S593"; then say "!! [6/12] the walk is RED on this box (exit $WRC) - nothing installed"; exit 1; fi
echo "$ROUT" | mask | grep -E "^  RED on the old files:|^  FAIL C:|^WALK OK negative|^NEGATIVE CONTROL|^  NOT RED|^WALK RED" | sed 's/^/   /'
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK negative control"; then say "!! [6/12] the negative control did not go red on the old files - the walk proves nothing; nothing installed"; echo "$ROUT" | mask | tail -30; exit 1; fi
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${FROM[$n]}" ] || { say "!! [6/12] $FIN/$n changed during the walk - nothing installed"; exit 1; }; done
say "[6/12] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "       negative control, the old files: $(echo "$ROUT" | grep "^WALK OK negative control" | tail -1 | sed 's/^WALK OK negative control S593: //')"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the scratch sides and both walks green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

# ---- 7: the install-day state on the OLD and the NEW files (fresh copies of the live database) ----------------------------------------------
statelook() {   # $1 = a scratch finance folder, or LIVE (a fresh scratch copy of /root/finance as it stands, its spine.db beside it); $2 = label; $3 = the map
  local d="$SCR/st_$2" fin="$1"; mkdir -p "$d"
  if [ "$1" = LIVE ]; then
    mkside "st_$2" >/dev/null 2>&1 || return 1
    copydb "$SPN/spine.db" "$d/finance/spine/spine.db" || return 1
    fin="$d/finance"
  fi
  copydb "$DB" "$d/f.db" || return 1
  ( cd /tmp && timeout 900 "$APY" -B "$KDIR/walk_s593.py" --state --label "$2" --fin "$fin" --db "$d/f.db" --adb "$SCR/base_a.db" --marg "$SCR/new/marg_ingest" --map "$3" 2>&1 ) | mask
}
say "[7/12] the install-day state BEFORE (the live files on a copy) and as the NEW files read the same copy:"
SB="$(statelook "$SCR/old/finance" before "$DMAP")"; echo "$SB" | grep -E "^STATE|^   " | sed 's/^/ /'
SN="$(statelook "$SCR/new/finance" new "$SCR/built/DUTY_MAP.json")"; echo "$SN" | grep -E "^STATE|^   " | sed 's/^/ /'
echo "$SB" | grep -q "^STATE OK S593" && echo "$SN" | grep -q "^STATE OK S593" || { say "!! [7/12] the install-day state could not be read - nothing placed"; exit 1; }
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/12] the build lock is not held by $KIT - nothing placed"; exit 1; }

# ---- 8: backups ---------------------------------------------------------------------------------------------------------------------------
copydb "$DB" "$DBBAK" && chmod 600 "$DBBAK" || { rm -f "$DBBAK"; say "!! [8/12] database backup failed - nothing placed"; exit 1; }
for n in $EDITED; do
  \cp -p "$FIN/$n" "$(bak $n)" || { say "!! [8/12] backup of $n failed - nothing placed"; exit 1; }
  [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ] || { say "!! [8/12] the backup of $n is not the live file - nothing placed"; exit 1; }
done
say "[8/12] backups: $(basename "$DBBAK") (sqlite backup API, $(stat -c %s "$DBBAK") bytes); $(for n in $EDITED; do printf '%s ' "$(bak $n | sed "s#$FIN/##")"; done)"

# ---- 9-10: the six files in ONE move, one restart -----------------------------------------------------------------------------------------
mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's; S578 must not restart a part it finds down" > "$OFFSW" || { say "!! [9/12] could not write $OFFSW - nothing placed"; exit 1; }
for n in $EDITED; do
  { \cp -p "$FIN/$n" "$(stg $n)" && cat "$SCR/built/$n" > "$(stg $n)" && [ "$(m5 "$(stg $n)")" = "${TO[$n]}" ]; } || { rm -f "$FIN"/.*.s593 "$SPN"/.*.s593 "$OFFSW"; say "!! [9/12] could not stage $n - nothing placed"; exit 1; }
done
PLACED=1
mv -f "$(stg order_rules.py)" "$FIN/order_rules.py" && mv -f "$(stg porders.py)" "$FIN/porders.py" && mv -f "$(stg porders_s454.py)" "$FIN/porders_s454.py" \
  && mv -f "$(stg order_sheet.py)" "$FIN/order_sheet.py" && mv -f "$(stg darpan_kal.py)" "$FIN/darpan_kal.py" && mv -f "$(stg spine/spine_read.py)" "$FIN/spine/spine_read.py" || restore "placing the six files"
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] && cmp -s "$FIN/$n" "$SCR/built/$n" || restore "$n did not land at its pin"; done
say "[9/12] placed by rename in ONE command; md5 read back: $(for n in $EDITED; do printf '%s %s . ' "$n" "$(m5 "$FIN/$n" | cut -c1-8)"; done)(= the kit's TO pins, byte-identical to the walked files)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
"$SYSTEMCTL" is-active --quiet "$SVC" || restore "$SVC is not active"
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/porders); c3=$(health /finance/porders/s454/order); c4=$(health /finance/darpan/kal); c5=$(health /finance/amir); c6=$(health /finance/reports/aaj); c7=$(health /finance/porders/api/day)
for c in "$c2" "$c3" "$c4" "$c5" "$c6" "$c7"; do case "$c" in 302|401|303) ;; *) restore "a page answered $c without a login (302 = the login gate, expected): porders $c2 / s454-order $c3 / darpan-kal $c4 / amir $c5 / reports-aaj $c6 / api-day $c7";; esac; done
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  "$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[10/12] $SVC restarted at $T0 (nothing else) and active - healthz $c1 - /finance/porders $c2, /s454/order $c3, /darpan/kal $c4, /amir $c5, /reports/aaj $c6, /porders/api/day $c7 without a login (302 = the login gate, expected) - journal clean"

# ---- 11: detect_supplies once on the LIVE database (the writes quoted); the state AFTER; nothing else moved --------------------------------
say "[11/12] porders.detect_supplies once on the live database (what the page's every read and the ten-minute tick do; its writes quoted, by rule letter, in packs):"
DOUT="$( cd "$FIN" && FINANCE_DB="$DB" timeout 600 "$APY" -B -c '
import os, sqlite3, sys, json
sys.path.insert(0, os.getcwd())
import porders, stock_figure as SF, stock_watch as SW
db = os.environ["FINANCE_DB"]
con = sqlite3.connect(db, timeout=60); con.row_factory = sqlite3.Row
def rows():
    return {int(r[0]): dict(r) for r in con.execute("SELECT l.id, l.item, l.packs, l.billed_qty, l.billed_bill_no, l.billed_date, l.supplied, l.short, o.vendor, o.created_at, o.id AS oid FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id WHERE o.status IN (\"sent\",\"received\")")}
b = rows()
sw = SW.Spine()
rule = {}
for i, r in b.items():
    if r["billed_qty"] is None:
        h = SF.carried(con, sw, dict(line_id=i, item=r["item"], vendor=r["vendor"], order_at=r["created_at"], billed_bill_no=None), SF.Ctx(con, sw))
        rule[i] = (h or {}).get("how")
n = porders.detect_supplies(con)
a = rows()
print("detect_supplies wrote %d line(s)" % n)
for i in sorted(a):
    if a[i]["billed_qty"] is not None and (b.get(i) or {}).get("billed_qty") is None:
        r = a[i]
        print("   line %-4s order %-3s %-30s %-26s ordered %3s packs -> billed %3s by bill %-14s of %s (rule %s) supplied %s short %s" % (i, r["oid"], r["item"][:30], r["vendor"][:26], r["packs"], r["billed_qty"], r["billed_bill_no"], r["billed_date"], rule.get(i), r["supplied"], r["short"]))
con.close()
' 2>&1 )" || true
echo "$DOUT" | mask | sed 's/^/        /'
echo "$DOUT" | grep -q "^detect_supplies wrote" || restore "detect_supplies on the live database did not run"
say "        the install-day state AFTER placing (the live files, a fresh copy of the live database):"
SA_="$(statelook LIVE after "$SCR/built/DUTY_MAP.json")"; echo "$SA_" | grep -E "^STATE|^   " | sed 's/^/ /'
echo "$SA_" | grep -q "^STATE OK S593" || restore "the state after placing could not be read"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(schema5 "$SPN/spine.db")" = "$SCHEMA0" ] || restore "spine.db's schema moved -- no table may be added to the spine"
[ "$(health /finance/healthz)" = 200 ] || restore "healthz at the end"
rm -f "$OFFSW"
say "        nothing else moved (the read-only files, finance_app, the spine's files and schema, portal.py, tile_grants.json, the crontab); healthz 200; $OFFSW removed"
say "        the 09:00 prepare_day, the ten-minute tick and Darpan's tab pick the new files up on their next run"

find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0
say "[12/12] md5 read back:"
for n in $EDITED; do md5sum "$FIN/$n"; done
C="$(m5 "$DMAP")"
if [ "$C" = "$DMAP_TO" ]; then say "        DUTY_MAP.json (the clone) $C -- the kit's: landed"; else say "        DUTY_MAP.json (the clone) $C -- not yet: it arrives with the publish (the owner's double-click and the clone's pull); the kit's is $DMAP_TO"; fi
say "$KIT: DONE. The build lock stays held by $KIT until the report is written."
say "undo: $(for n in $EDITED; do printf '\\cp -p %s %s && ' "$(bak $n)" "$FIN/$n"; done)$SYSTEMCTL restart $SVC"
exit 0
