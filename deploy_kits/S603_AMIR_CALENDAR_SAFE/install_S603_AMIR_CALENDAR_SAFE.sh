#!/bin/bash
# =============================================================================
#  install_S603_AMIR_CALENDAR_SAFE.sh · kit S603 (20-Oct-2026) · brief claude_code_briefs/S603_AMIR_CALENDAR_SAFE.md (v2)
#  F-952 (the tap clears the band), F-953 (the judge reachable from /api/readiness), F-769 (the stock-ahead sentence), F-786 (the waiting
#  words), F-726 a (the answered salt on Amir's sheet). No D-number: every rule is the owner's existing one.
#
#  Run from a copy of the kit folder (or from /root/deploy/repo/deploy_kits/S603_AMIR_CALENDAR_SAFE), 08:00-23:49 IST only:
#    rm -rf /tmp/s603kit && cp -rp <kit> /tmp/s603kit && bash /tmp/s603kit/install_S603_AMIR_CALENDAR_SAFE.sh
#  (DRY=1 before bash: every gate, the scratch sides and the walks, nothing written, no lock.)
#
#   /root/finance/amir_day.py     3af992d9 -> TO   _export_fact (one fact), _reexport_due on it, _export_state covers-first + since, _s603_export_lines, absent ending, KIT
#   /root/finance/stock_app.py    4f73d0b0 -> TO   readiness by purchase_cover_how (read-only), _r_stock read-only, _s488_why absent, _s488_purchase_reach deleted
#   /root/finance/stock_watch.py  299c3ef7 -> TO   start_capture_lines: purchase_cover_how over the pending capture (end_day from the row), read-only
#   /root/finance/amir_salts.py   d8d9ba77 -> TO   the answered 'waiting' salt on tab 1 (exact text = the answer), ticked by id; tab 2 keeps the unanswered
#   the clone's claude_code_briefs/DUTY_MAP.json c2ef9c6c (v15) -> v16 (amir.salt_tasks) and one dated line in DUTY_MAP.md: placed by the PUBLISH
#   (git pull of /root/deploy/repo), never by this script; the kit ships the v16 copy its walk ran with.
#  No DDL, no new table, no new setting, no data step. Read only, must not move (this kit was built reading them): stock_figure 51e1fc63,
#  purchase_app 60f2d846, export_watch f6845ec5, shelf_figure 23b2394a, order_rules 8d078dbe, porders e5a5c4d4, darpan_kal b28d7342,
#  spine/spine_read 10697b38; proved unmoved: finance_app, portal.py, tile_grants.json, the crontab (84 lines, S577_WITNESS once), spine.db's schema.
#  ORDER: gates (window, lock, SUMS, KIT_ID, PINS, S602's and S598's kits present) -> pins (ALREADY first) + the read-only md5s + the clone's
#  DUTY_MAP.json + the crontab -> the spine green and fresh -> the live facts printed (F-510: the 18-Oct rows, the receipts after 09:35:24, the
#  18-10 09:37 capture row, the salt counts, amir.proof_wait_hours, the new duty's due_sql on the live database) -> build from the live bytes
#  (anchored edits, each anchor once; the built DUTY_MAP.json = the kit's copy) -> compile (both pythons) -> scratch: the finance folder twice,
#  a portal copy (never the live secret or user store), finance.db / assets.db / spine.db by the backup API; the walk on the OLD files (every
#  control red) then on the NEW files (green); S602's walk on the NEW files; S598's walk on both sides, its check lines equal -> DRY stops ->
#  the install-day state BEFORE (the OLD files on a copy) and as the NEW files read the same copy -> backups -> DOCTOR_AUTO_OFF -> the FOUR files
#  staged and renamed in ONE command -> ONE restart of clinic-finance -> healthz 200, the pages 302 -> journal clean -> the state AFTER (the live
#  files on a fresh copy) -> nothing else moved -> md5 read-back -> DOCTOR_AUTO_OFF removed. Red after placing: the four files put back in one
#  command, one restart, healthz. The build lock stays held until the report is written (released with rm -f .../owner; rmdir ...).
#  Under set -u, not set -e: every gate is a test.
# =============================================================================
set -u
KIT="S603_AMIR_CALENDAR_SAFE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
SPN="$FIN/spine"
POR="${POR:-/root/portal}"
MARG="${MARG:-/root/marg_ingest}"
ADB="${ADB:-/root/assetapp/assets.db}"
DB="${DB:-$FIN/finance.db}"
REPO="${REPO:-/root/deploy/repo}"
BRIEFS="$REPO/claude_code_briefs"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
S602KIT="${S602KIT:-$REPO/deploy_kits/S602_CUTOFF_LINE_AND_F943}"
S598KIT="${S598KIT:-$REPO/deploy_kits/S598_ARRIVALS_BY_LINE}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
EDITED="amir_day.py stock_app.py stock_watch.py amir_salts.py"
declare -A FROM TO READ
FROM[amir_day.py]=3af992d9e6b6c6050b1427e34757ca78
FROM[stock_app.py]=4f73d0b02a167289d9439af7a35b5fa0
FROM[stock_watch.py]=299c3ef76b73a10e4af1cd15974c7a3f
FROM[amir_salts.py]=d8d9ba772650a4d804add6953790d14d
DUTY_FROM=c2ef9c6c5adb8c930b21bff5441cc017
READ[stock_figure.py]=51e1fc63ab3fb1ac21170cb214f15b6b
READ[purchase_app.py]=60f2d846155659c4eddc33e4a0d42b39
READ[export_watch.py]=f6845ec5ae1dc8fe200ebf5f4c3ad173
READ[shelf_figure.py]=23b2394a7a10a99ff0c30121087813f1
READ[order_rules.py]=8d078dbe1b63a4706dc6f35e3c31ac9a
READ[porders.py]=e5a5c4d4dfa15c3ecd0b0cdf4786abcd
READ[darpan_kal.py]=b28d7342469814e85129602ea35a7423
READ[spine/spine_read.py]=10697b3869218151a75268e2259248d7
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s603_inst_$STAMP"
PLACED=0
DBBAK="$FIN/finance.db.bak_S603_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S603_${FROM[$1]:0:8}"; }
stg() { echo "$FIN/.$1.s603"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
on_exit() { rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
schema5() { "$APY" -c "import sqlite3,sys,hashlib; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); print(hashlib.md5('\n'.join(sorted(r[0] or '' for r in c.execute(\"SELECT sql FROM sqlite_master WHERE type IN ('table','index')\"))).encode()).hexdigest())" "$1" 2>/dev/null; }
jget() { "$APY" -c "import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], ''))" "$1" "$2" 2>/dev/null; }
sqlro() { "$APY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); [print('   ', *[str(x) for x in r]) for r in c.execute(sys.argv[2]).fetchall()]" "$1" "$2" 2>/dev/null | mask; }
caprows() { "$APY" -c "import sqlite3,sys,datetime as d; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); r=(d.date.today()-d.timedelta(days=21)).isoformat(); [print('   ', x[0][:8], 'printed', x[1], 'taken', x[2], '-> end', x[3], ':', x[4], ('/ '+x[5]) if x[5] else '', '(checked', str(x[6])+')') for x in c.execute('SELECT md5, as_on, stamp_iso, end_day, verdict, reason, checked_at FROM stock_start_capture WHERE as_on>=? ORDER BY stamp_iso', (r,))]" "$1" 2>/dev/null; }
caprows5() { "$APY" -c "import sqlite3,sys,datetime as d,hashlib; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); r=(d.date.today()-d.timedelta(days=21)).isoformat(); print(hashlib.md5(repr(c.execute('SELECT md5, as_on, stamp_iso, end_day, verdict FROM stock_start_capture WHERE as_on>=? ORDER BY stamp_iso', (r,)).fetchall()).encode()).hexdigest())" "$1" 2>/dev/null; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the four files back in one command"
  \cp -p "$(bak amir_day.py)" "$FIN/amir_day.py" && \cp -p "$(bak stock_app.py)" "$FIN/stock_app.py" && \cp -p "$(bak stock_watch.py)" "$FIN/stock_watch.py" && \cp -p "$(bak amir_salts.py)" "$FIN/amir_salts.py"
  rm -f "$FIN"/.*.s603
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  for n in $EDITED; do say "   $FIN/$n $(m5 "$FIN/$n") (expected ${FROM[$n]})"; done
  say "   after the restore: finance healthz $h"
  say "   the database backup stays: $DBBAK"
  rm -f "$OFFSW"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl timeout grep tail sleep find sed sort cmp crontab diff; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
command -v "$SYSTEMCTL" >/dev/null 2>&1 || { say "!! preflight: $SYSTEMCTL missing - nothing installed"; exit 1; }
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"
{ [ "$HH" -ge 8 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 49 ]; }; } || { say "!! [1/12] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 08:00-23:49 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/12] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/12] KIT_ID.txt names another kit - nothing installed"; exit 1; }
. "$KDIR/PINS.sh" || { say "!! [1/12] PINS.sh missing - nothing installed"; exit 1; }
for n in $EDITED; do [ -f "$FIN/$n" ] || { say "!! [1/12] $FIN/$n is not there - nothing installed"; exit 1; }; done
[ -f "$KDIR/DUTY_MAP.json" ] && [ -f "$BRIEFS/DUTY_MAP.json" ] && [ -f "$BRIEFS/DUTY_MAP.md" ] || { say "!! [1/12] DUTY_MAP.json (the kit's copy, or the clone's) or DUTY_MAP.md is missing - nothing installed"; exit 1; }
[ -f "$S602KIT/walk_s602.py" ] && ( cd "$S602KIT" && md5sum -c SUMS.md5 >/dev/null 2>&1 ) || { say "!! [1/12] S602's kit is not at $S602KIT or fails its SUMS (its walk is run on the NEW files) - nothing installed"; exit 1; }
[ -f "$S598KIT/walk_s598.py" ] && ( cd "$S598KIT" && md5sum -c SUMS.md5 >/dev/null 2>&1 ) || { say "!! [1/12] S598's kit is not at $S598KIT or fails its SUMS (its walk is run on both sides) - nothing installed"; exit 1; }
ALL_TO=1; for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then say "-- ALREADY INSTALLED: the four files are the kit's. Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null); healthz $(health /finance/healthz); the clone's DUTY_MAP.json $(m5 "$BRIEFS/DUTY_MAP.json" | cut -c1-8) (v16 = ${TO[DUTY_MAP.json]:0:8}, placed by the publish)"; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/12] DRY RUN: kit gates green (SUMS, KIT_ID, PINS, S602's and S598's kits, the window); no lock, no backup, nothing placed, nothing written"
elif mkdir "$LOCK" 2>/dev/null; then
  echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/12] kit gates green (SUMS, KIT_ID, PINS, S602's and S598's kits, the window); the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  say "[1/12] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/12] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again when it is free."
  exit 3
fi

for n in $EDITED; do C="$(m5 "$FIN/$n")"; [ "$C" = "${FROM[$n]}" ] || { say "!! [2/12] $FIN/$n is $C, expected ${FROM[$n]} - it changed after the brief: STOP, nothing installed"; exit 1; }; done
say "[2/12] live pins exact: $(for n in $EDITED; do printf '%s %s . ' "$n" "${FROM[$n]:0:8}"; done)"
DM5="$(m5 "$BRIEFS/DUTY_MAP.json")"
if [ "$DM5" = "$DUTY_FROM" ]; then say "       the clone's DUTY_MAP.json $DM5 (v15, the brief's pin; v16 reaches it by the publish)";
elif [ "$DM5" = "${TO[DUTY_MAP.json]}" ]; then say "       the clone's DUTY_MAP.json is already v16 ($DM5) - the publish has landed; fine";
else say "!! [2/12] the clone's DUTY_MAP.json is $DM5, neither the FROM pin $DUTY_FROM (v15) nor the kit's v16 - STOP, nothing installed"; exit 1; fi
say "       the read-only files' live md5s (the brief, section 1):"
for n in stock_figure.py purchase_app.py export_watch.py shelf_figure.py order_rules.py porders.py darpan_kal.py spine/spine_read.py; do
  C="$(m5 "$FIN/$n")"; say "         $n $C"
  [ "$C" = "${READ[$n]}" ] || { say "!! [2/12] $FIN/$n is $C, not ${READ[$n]} - this kit was built reading it: STOP, nothing installed"; exit 1; }
done
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$SPN/spine.db" ] && [ -f "$SPN/spine_state.json" ] && [ -f "$POR/tile_grants.json" ] && [ -f "$POR/clinic_users.py" ] || { say "!! [2/12] a database, the spine or the portal is missing - nothing installed"; exit 1; }
CRONN="$(crontab -l 2>/dev/null | wc -l | awk '{print $1}')"; CRONW="$(crontab -l 2>/dev/null | grep -c S577_WITNESS || true)"
say "       the crontab: $CRONN lines, S577_WITNESS lines ${CRONW:-0}"
[ "$CRONN" = 84 ] && [ "${CRONW:-0}" = 1 ] || { say "!! [2/12] the crontab is not as the brief read it (84 lines, S577_WITNESS once) - STOP, nothing installed"; exit 1; }
SP_OK="$(jget "$SPN/spine_state.json" passed)"; SP_GATE="$(jget "$SPN/spine_state.json" gate)"; SP_AT="$(jget "$SPN/spine_state.json" last_success_iso)"
SP_AGE="$("$APY" -c "import sys,datetime as d; t=d.datetime.fromisoformat(sys.argv[1]); print(int((d.datetime.now(t.tzinfo)-t).total_seconds()//60))" "$SP_AT" 2>/dev/null || echo 9999)"
GATE_N="${SP_GATE%/*}"; GATE_D="${SP_GATE#*/}"
[ "$SP_OK" = True ] && [ -n "$GATE_N" ] && [ "$GATE_N" = "$GATE_D" ] && [ "$SP_AGE" -le 30 ] \
  || { say "!! [2/12] the spine is red or stale (passed $SP_OK, gate $SP_GATE, last success $SP_AT, $SP_AGE min ago) - the kit depends on it; nothing installed (charter 1b)"; exit 4; }
NOTT=("$FIN/stock_figure.py" "$FIN/purchase_app.py" "$FIN/export_watch.py" "$FIN/shelf_figure.py" "$FIN/order_rules.py" "$FIN/porders.py" "$FIN/darpan_kal.py" "$SPN/spine_read.py" "$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json")
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"; SCHEMA0="$(schema5 "$SPN/spine.db")"
[ -n "$SCHEMA0" ] || { say "!! [2/12] the spine's schema could not be read - nothing installed"; exit 1; }
say "       charter 1b: the spine passed $SP_GATE, last success $SP_AT ($SP_AGE min ago); spine.db schema $SCHEMA0"
say "       F-510, the live facts read from the live database (read only) at $(TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M:%S IST'):"
say "         the 18-Oct amir_step_log rows (id, step, done_at, note):"
sqlro "$DB" "SELECT id, step, done_at, COALESCE(note,'') FROM amir_step_log WHERE day='2026-10-18' ORDER BY id"
say "         purchase receipts after 2026-10-18 09:35:24 -- mi_file VERIFIED purchase rows, purchase_export pair rows (expected 0 0 until his next export):"
sqlro "$DB" "SELECT (SELECT COUNT(*) FROM mi_file WHERE verdict='VERIFIED' AND type IN ('PURCHASE_BILLWISE','PURCHASE_ITEMWISE','PURCHASE_BILLITEMWISE') AND substr(replace(received_at,'T',' '),1,19) > '2026-10-18 09:35:24'), (SELECT COUNT(*) FROM purchase_export WHERE type IN ('BILLWISE','ITEMWISE','BILLITEMWISE') AND substr(replace(received_at,'T',' '),1,19) > '2026-10-18 09:35:24')"
say "         the newest purchase receipt on the server (mi_file / purchase_export):"
sqlro "$DB" "SELECT (SELECT MAX(substr(replace(received_at,'T',' '),1,19)) FROM mi_file WHERE verdict='VERIFIED' AND type LIKE 'PURCHASE_%'), (SELECT MAX(substr(replace(received_at,'T',' '),1,19)) FROM purchase_export WHERE type IN ('BILLWISE','ITEMWISE','BILLITEMWISE'))"
say "         stock_start_capture rows within LATE_DAYS (21):"
caprows "$DB"
CAP0="$(caprows5 "$DB")"
say "         purchase_salt_task by section and done:"
sqlro "$DB" "SELECT section, COALESCE(done,0), COUNT(*) FROM purchase_salt_task GROUP BY section, COALESCE(done,0)"
say "         settings: $("$APY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); print(dict(c.execute(\"SELECT key, value FROM setting WHERE key IN ('amir.proof_wait_hours','amir.job_wait_days','count.start_capture') ORDER BY key\").fetchall()))" "$DB")"
say "         the new duty amir.salt_tasks: its due_sql run on the live database (CLAUDE.md 'Every duty has a door' 1):"
sqlro "$DB" "$("$APY" -c "import json,sys; print([d for d in json.load(open(sys.argv[1]))['duties'] if d['id']=='amir.salt_tasks'][0]['due_sql'])" "$KDIR/DUTY_MAP.json")"

mkdir -p "$SCR/built" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONDONTWRITEBYTECODE=1
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile make_s603.py walk_s603.py || { say "!! [3/12] compile failed on $py - nothing installed"; exit 1; }
done
"$APY" -B make_s603.py --finance "$FIN" --briefs "$BRIEFS" --out "$SCR/built" > "$SCR/make.txt" || { cat "$SCR/make.txt"; say "!! [4/12] the builder refused a live file - nothing installed"; exit 1; }
for n in $EDITED DUTY_MAP.json DUTY_MAP.md; do [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || { say "!! [4/12] rebuilt, $n is $(m5 "$SCR/built/$n"), not ${TO[$n]} - nothing installed"; exit 1; }; done
cmp -s "$SCR/built/DUTY_MAP.json" "$KDIR/DUTY_MAP.json" || { say "!! [4/12] the built DUTY_MAP.json is not the kit's shipped copy - nothing installed"; exit 1; }
for py in "$APY" "$VPY"; do
  for n in $EDITED; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" || { say "!! [3/12] the built $n does not compile on $py - nothing installed"; exit 1; }; done
done
say "[3/12] the kit's python files and the four built python files compile on $APY and $VPY"
say "[4/12] rebuilt here from this box's live bytes ($(grep -c 'anchored once, applied' "$SCR/make.txt") anchored edits + DUTY_MAP v16 + the dated line): each at its TO pin; the built DUTY_MAP.json = the kit's copy"

copydb "$DB" "$SCR/base.db" && copydb "$ADB" "$SCR/base_a.db" && copydb "$SPN/spine.db" "$SCR/spine.db" || { say "!! [5/12] no copy of the databases - nothing installed"; exit 1; }
mkside() {   # $1 = side: a copy of the live finance code (spine folder included), a portal copy (never the live secret or user store), the ingest reader, the databases
  local d="$SCR/$1"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" "$d/marg_ingest/archive" "$d/portal"
  cp -p "$FIN"/*.py "$d/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$d/finance/finance_ui/" 2>/dev/null; cp -p "$SPN"/*.py "$SPN"/*.json "$d/finance/spine/" 2>/dev/null
  for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do cp -p "$MARG/$f" "$d/marg_ingest/" || return 1; done
  cp -rp "$MARG/archive/ORDER_PENDING" "$d/marg_ingest/archive/" || return 1
  for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$d/portal/"; done
  cp -p "$POR/tile_grants.json" "$d/portal/" || return 1; cp -rp "$POR/forms" "$d/portal/" 2>/dev/null
  cp -p "$SCR/base.db" "$d/f.db" && cp -p "$SCR/base.db" "$d/f602.db" && cp -p "$SCR/base.db" "$d/f598.db" && cp -p "$SCR/base_a.db" "$d/a.db" && cp -p "$SCR/spine.db" "$d/finance/spine/spine.db"
}
for side in new old; do mkside "$side" || { say "!! [5/12] no scratch side '$side' - nothing installed"; exit 1; }; done
for n in $EDITED; do cp -p "$SCR/built/$n" "$SCR/new/finance/$n"; done
say "[5/12] scratch: the finance folder twice (NEW with the four built files, OLD as it is), a portal copy per side, finance.db (three copies a side: this walk's, S602's, S598's), assets.db and the spine by the backup API"
ROUT="$( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s603.py" --fin "$SCR/old/finance" --db "$SCR/old/f.db" --adb "$SCR/old/a.db" --marg "$SCR/old/marg_ingest" --por "$SCR/old/portal" --duty-map "$KDIR/DUTY_MAP.json" --dump "$SCR/dump_old" --expect-red 2>&1 )"; RRC=$?
WOUT="$( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s603.py" --fin "$SCR/new/finance" --db "$SCR/new/f.db" --adb "$SCR/new/a.db" --marg "$SCR/new/marg_ingest" --por "$SCR/new/portal" --duty-map "$KDIR/DUTY_MAP.json" --dump "$SCR/dump_new" --old-dump "$SCR/dump_old" 2>&1 )"; WRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | mask | sed 's/^/   /'
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK S603"; then say "!! [6/12] the walk is RED on this box (exit $WRC) - nothing installed"; exit 1; fi
echo "$ROUT" | mask | grep -E "^  RED on the old files:|^  FAIL C:|^WALK OK negative|^NEGATIVE CONTROL|^  NOT RED|^WALK RED" | sed 's/^/   /'
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK negative control"; then say "!! [6/12] the negative control did not go red on the old files - the walk proves nothing; nothing installed"; echo "$ROUT" | mask | tail -30; exit 1; fi
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${FROM[$n]}" ] || { say "!! [6/12] $FIN/$n changed during the walk - nothing installed"; exit 1; }; done
say "[6/12] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "       negative control, the old files: $(echo "$ROUT" | grep "^WALK OK negative control" | tail -1 | sed 's/^WALK OK negative control S603: //')"
say "       S602's walk (walk_s602.py, whole) on the NEW files (its four files are untouched by this kit; stock_figure's kit line stays S602's):"
W602="$( cd /tmp && timeout 2400 "$APY" -B "$S602KIT/walk_s602.py" --fin "$SCR/new/finance" --db "$SCR/new/f602.db" --adb "$SCR/new/a.db" --marg "$SCR/new/marg_ingest" --dump "$SCR/dump602_new" 2>&1 )"; W602RC=$?
find "$S602KIT" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "         $(echo "$W602" | grep -E '^WALK (OK|RED)' | tail -1 | mask | cut -c1-100) (exit $W602RC; $(echo "$W602" | grep -c '^  FAIL ') FAIL line(s))"
echo "$W602" | grep '^  FAIL ' | mask | cut -c1-160 | sed 's/^/         /'
[ "$W602RC" = 0 ] && echo "$W602" | grep -q "^WALK OK S602" || { say "!! [6/12] S602's walk is not green on the NEW files - nothing installed"; exit 1; }
say "       S598's walk (walk_s598.py, whole) on the NEW files and on the OLD files -- its check lines must be the same on both (the kit changes nothing it sees):"
w598() { ( cd /tmp && timeout 2400 "$APY" -B "$S598KIT/walk_s598.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f598.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --kit "$S598KIT" --dump "$SCR/dump598_$1" 2>&1 ); }
W598N="$(w598 new)"; W598O="$(w598 old)"
find "$S598KIT" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
w598lines() { grep -E '^  (ok|FAIL) ' | sed -E 's/[0-9]+\.[0-9]s/N.Ns/g; s/\(200, [0-9]+ bytes\)/(200, N bytes)/'; }
echo "$W598N" | w598lines > "$SCR/w598_new.txt"
echo "$W598O" | w598lines > "$SCR/w598_old.txt"
say "         NEW: $(echo "$W598N" | grep -E '^WALK (OK|RED)' | tail -1 | mask | cut -c1-60)... ($(grep -c '^  FAIL ' "$SCR/w598_new.txt") FAIL line(s))"
say "         OLD: $(echo "$W598O" | grep -E '^WALK (OK|RED)' | tail -1 | mask | cut -c1-60)... ($(grep -c '^  FAIL ' "$SCR/w598_old.txt") FAIL line(s))"
if ! cmp -s "$SCR/w598_new.txt" "$SCR/w598_old.txt"; then say "!! [6/12] S598's walk reads differently on the NEW files than on the OLD files - nothing installed"; diff "$SCR/w598_old.txt" "$SCR/w598_new.txt" | mask | head -20; exit 1; fi
[ -s "$SCR/w598_new.txt" ] || { say "!! [6/12] S598's walk printed no check line - nothing installed"; exit 1; }
grep '^  FAIL ' "$SCR/w598_new.txt" | mask | cut -c1-150 | sed 's/^/         (both sides, today'"'"'s data) /'
say "         S598's walk: $(wc -l < "$SCR/w598_new.txt") check lines identical on both sides"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the scratch sides and the walks green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

# ---- 7: the install-day state on the OLD and the NEW files (fresh copies of the live database) ----------------------------------------------
statelook() {   # $1 = a scratch finance folder, or LIVE (a fresh scratch copy of /root/finance as it stands); $2 = label
  local d="$SCR/st_$2" fin="$1"; mkdir -p "$d"
  if [ "$1" = LIVE ]; then
    mkside "st_$2" >/dev/null 2>&1 || return 1
    copydb "$SPN/spine.db" "$d/finance/spine/spine.db" || return 1
    fin="$d/finance"
  fi
  copydb "$DB" "$d/f.db" || return 1
  ( cd /tmp && timeout 900 "$APY" -B "$KDIR/walk_s603.py" --state --label "$2" --fin "$fin" --db "$d/f.db" --adb "$SCR/base_a.db" --marg "$SCR/new/marg_ingest" --por "$SCR/new/portal" --duty-map "$KDIR/DUTY_MAP.json" 2>&1 ) | mask
}
say "[7/12] the install-day state BEFORE (the live files on a copy) and as the NEW files read the same copy (charter 7):"
SB="$(statelook "$SCR/old/finance" before)"; echo "$SB" | grep -E "^STATE|^   " | sed 's/^/ /'
SN="$(statelook "$SCR/new/finance" new)"; echo "$SN" | grep -E "^STATE|^   " | sed 's/^/ /'
echo "$SB" | grep -q "^STATE OK S603" && echo "$SN" | grep -q "^STATE OK S603" || { say "!! [7/12] the install-day state could not be read - nothing placed"; exit 1; }
echo "$SN" | grep -q "^STATE new: _reexport_due(2026-10-18) = (True, '2026-10-18 09:35:24')" || say "        note: the NEW files no longer read 18-Oct as re-export due (his next export must have landed): $(echo "$SN" | grep '^STATE new: _reexport_due')"
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/12] the build lock is not held by $KIT - nothing placed"; exit 1; }

# ---- 8: backups ---------------------------------------------------------------------------------------------------------------------------
copydb "$DB" "$DBBAK" && chmod 600 "$DBBAK" || { rm -f "$DBBAK"; say "!! [8/12] database backup failed - nothing placed"; exit 1; }
for n in $EDITED; do
  \cp -p "$FIN/$n" "$(bak $n)" || { say "!! [8/12] backup of $n failed - nothing placed"; exit 1; }
  [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ] || { say "!! [8/12] the backup of $n is not the live file - nothing placed"; exit 1; }
done
say "[8/12] backups: $(basename "$DBBAK") (sqlite backup API, $(stat -c %s "$DBBAK") bytes); $(for n in $EDITED; do printf '%s ' "$(bak $n | sed "s#$FIN/##")"; done)"

# ---- 9-10: the four files in ONE move, one restart ------------------------------------------------------------------------------------------
mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's; S578 must not restart a part it finds down" > "$OFFSW" || { say "!! [9/12] could not write $OFFSW - nothing placed"; exit 1; }
for n in $EDITED; do
  { \cp -p "$FIN/$n" "$(stg $n)" && cat "$SCR/built/$n" > "$(stg $n)" && [ "$(m5 "$(stg $n)")" = "${TO[$n]}" ]; } || { rm -f "$FIN"/.*.s603 "$OFFSW"; say "!! [9/12] could not stage $n - nothing placed"; exit 1; }
done
PLACED=1
mv -f "$(stg amir_day.py)" "$FIN/amir_day.py" && mv -f "$(stg stock_app.py)" "$FIN/stock_app.py" && mv -f "$(stg stock_watch.py)" "$FIN/stock_watch.py" && mv -f "$(stg amir_salts.py)" "$FIN/amir_salts.py" || restore "placing the four files"
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] && cmp -s "$FIN/$n" "$SCR/built/$n" || restore "$n did not land at its pin"; done
say "[9/12] placed by rename in ONE command; md5 read back: $(for n in $EDITED; do printf '%s %s . ' "$n" "$(m5 "$FIN/$n" | cut -c1-8)"; done)(= the kit's TO pins, byte-identical to the walked files)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
"$SYSTEMCTL" is-active --quiet "$SVC" || restore "$SVC is not active"
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/amir); c3=$(health /finance/amir/day); c4=$(health /finance/amir/salts); c5=$(health /finance/stock/api/readiness); c6=$(health /finance/reports/aaj); c7=$(health /finance/porders); c8=$(health /finance/darpan/kal)
for c in "$c2" "$c3" "$c4" "$c5" "$c6" "$c7" "$c8"; do case "$c" in 302|401|303) ;; *) restore "a page answered $c without a login (302 = the login gate, expected): amir $c2 / amir/day $c3 / amir/salts $c4 / stock api/readiness $c5 / reports-aaj $c6 / porders $c7 / darpan/kal $c8";; esac; done
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  "$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[10/12] $SVC restarted at $T0 (nothing else) and active - healthz $c1 - /finance/amir $c2, /amir/day $c3, /amir/salts $c4, /stock/api/readiness $c5, /reports/aaj $c6, /porders $c7, /darpan/kal $c8 without a login (302 = the login gate, expected) - journal clean"

# ---- 11: the state AFTER; nothing else moved --------------------------------------------------------------------------------------------------
say "[11/12] the install-day state AFTER placing (the live files, a fresh copy of the live database; the box's clock in the first STATE line):"
SA_="$(statelook LIVE after)"; echo "$SA_" | grep -E "^STATE|^   " | sed 's/^/ /'
echo "$SA_" | grep -q "^STATE OK S603" || restore "the state after placing could not be read"
echo "$SA_" | grep -q "^STATE after: files NEW (S603)" || restore "the state after placing does not read the NEW files"
echo "$SA_" | grep -q "readiness()\['warnings'\]" && ! echo "$SA_" | grep "readiness()\['warnings'\]" | grep -q "Purchases are" || restore "readiness after placing still carries the purchase 'days behind' sentence"
CAP1="$(caprows5 "$DB")"
[ "$CAP1" = "$CAP0" ] || say "        note: a stock_start_capture row's verdict moved between the open and now (the day's own pages judge as before; this kit's reads never do):"
caprows "$DB"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(schema5 "$SPN/spine.db")" = "$SCHEMA0" ] || restore "spine.db's schema moved -- no table may be added to the spine"
[ "$(health /finance/healthz)" = 200 ] || restore "healthz at the end"
rm -f "$OFFSW"
say "        nothing else moved (the read-only files, finance_app, portal.py, tile_grants.json, the crontab, the spine's schema); healthz 200; $OFFSW removed"
say "        the clone's DUTY_MAP.json is $(m5 "$BRIEFS/DUTY_MAP.json" | cut -c1-8) now; v16 (${TO[DUTY_MAP.json]:0:8}) reaches it by the publish and the clone's pull -- the Needs-you duty check reads it there"

find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0
say "[12/12] md5 read back:"
for n in $EDITED; do md5sum "$FIN/$n"; done
say "$KIT: DONE. The build lock stays held by $KIT until the report is written (release: rm -f $LOCK/owner; rmdir $LOCK)."
say "undo (the files): \\cp -p $(bak amir_day.py) $FIN/amir_day.py && \\cp -p $(bak stock_app.py) $FIN/stock_app.py && \\cp -p $(bak stock_watch.py) $FIN/stock_watch.py && \\cp -p $(bak amir_salts.py) $FIN/amir_salts.py && $SYSTEMCTL restart $SVC"
exit 0
