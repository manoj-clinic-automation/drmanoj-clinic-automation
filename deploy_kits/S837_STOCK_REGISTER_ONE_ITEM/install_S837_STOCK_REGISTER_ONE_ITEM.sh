#!/bin/bash
# =============================================================================
#  install_S837_STOCK_REGISTER_ONE_ITEM.sh · kit S837 (14-Nov-2026, Sanjeevni session 463) · the owner's "Mockup is good" of 20:28 IST
#  Marg's Stock Register for ONE item: asked by him from a Marg watch row or from his own list (/finance/sanjeevni/marg-watch/take); kept
#  with HIM (the Hub's Needs-you line, the Hub's Go to with a count, the Marg watch strip); a switch for Shavez, OFF to start; the register
#  read name-free at the door (new /root/marg_ingest/marg_register.py; the file is deleted as every sale-family file is), shown in the row,
#  and a voucher-type entry only Marg holds that equals the move takes the row out of the count.
#   1. /root/finance/marg_billwatch.py 960b5309 -> TO    2. /root/finance/reports_tile.py 163a869a -> TO
#   3. /root/finance/sanjeevni_approvals.py ae29e2bc -> TO   4. /root/finance/finance_ui/finance_approvals.html 82f459ef -> TO
#   5. /root/marg_ingest/marg_take.py 5cad2d24 -> TO     6. /root/marg_ingest/marg_ingest.py 828c4dad -> TO    7. NEW /root/marg_ingest/marg_register.py
#  All rebuilt HERE from the live bytes (make_s837.py), checked against the TO pins. clinic-finance is restarted.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s837kit && cp -rp /root/deploy/repo/deploy_kits/S837_STOCK_REGISTER_ONE_ITEM /tmp/s837kit && bash /tmp/s837kit/install_S837_STOCK_REGISTER_ONE_ITEM.sh
#  (DRY=1 before bash: every gate, the walks and the control; NOTHING written.)
# =============================================================================
set -u
KIT="S837_STOCK_REGISTER_ONE_ITEM"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"; SPDB="${SPDB:-$ROOT/finance/spine/spine.db}"
DMAP="${DMAP:-/root/deploy/repo/claude_code_briefs/DUTY_MAP.json}"
OLDK="${OLDK:-/root/deploy/repo/deploy_kits/S815_MARG_WATCH_DARPAN_REPORTS}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="finance/marg_billwatch.py finance/reports_tile.py finance/sanjeevni_approvals.py finance/finance_ui/finance_approvals.html marg_ingest/marg_take.py marg_ingest/marg_ingest.py"
NEW="marg_ingest/marg_register.py"
from_of() { case "$1" in finance/marg_billwatch.py) echo 960b5309e78570ef6fac605e34594f1f;; finance/reports_tile.py) echo 163a869aee0547f891d47023a45873c4;;
  finance/sanjeevni_approvals.py) echo ae29e2bc5bf2da9819e1f095e8aee7a5;; finance/finance_ui/finance_approvals.html) echo 82f459efc902085a6b4f9285efe9c1ef;;
  marg_ingest/marg_take.py) echo 5cad2d24d63344146f562fd5d441dbdf;; marg_ingest/marg_ingest.py) echo 828c4dad6b159207b034d8129aed3ab7;; esac; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s837_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { local f; f=$(from_of "$1"); echo "$ROOT/$1.bak_S837_${f:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s837"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
ftk() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/sanjeevni/marg-watch/take; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/sanjeevni/marg-watch/take"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES $NEW; do rm -f "$(stg "$n")"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the six files back and taking the new reader away (the added tables and column stay; the old files never read them)"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/$n"; done
  rm -f "$ROOT/$NEW"; "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do f=$(from_of "$n"); say "   $n $(m5 "$ROOT/$n" | cut -c1-8) (expected ${f:0:8})"; done
  say "   $NEW present: $([ -e "$ROOT/$NEW" ] && echo yes || echo no) (expected no)"
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
lay() { local d="$SCR/root_$1"; rm -rf "$d"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" "$d/marg_ingest/lib" \
  && find "$ROOT/finance" -maxdepth 1 -type f \( -name '*.py' -o -name '*.html' -o -name '*.sql' -o -name '*.json' \) -exec cp -p {} "$d/finance/" \; \
  && \cp -p "$ROOT"/finance/finance_ui/*.html "$d/finance/finance_ui/" 2>/dev/null; \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$d/finance/spine/" 2>/dev/null; \
  find "$ROOT/marg_ingest" -maxdepth 1 -type f \( -name '*.py' -o -name '*.json' \) -exec cp -p {} "$d/marg_ingest/" \; ; \cp -p "$ROOT"/marg_ingest/lib/*.py "$d/marg_ingest/lib/" 2>/dev/null; \
  [ -f "$d/finance/marg_billwatch.py" ] && [ -f "$d/marg_ingest/marg_take.py" ]; }
w837() { (cd /tmp && TMPDIR="$SCR" PYTHONPATH="$ROOT/shared${PYTHONPATH:+:$PYTHONPATH}" PYTHONPYCACHEPREFIX="$SCR/pyc" SPINE_DB="$SCR/spine.db" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s837.py" "$1" "$SCR/finance.db" SYNTH 2>&1); }
wold() { (cd /tmp && TMPDIR="$SCR" PYTHONPATH="$ROOT/shared${PYTHONPATH:+:$PYTHONPATH}" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$OLDK/$1" "$2" "$SCR/spine.db" "$SCR/finance.db" ${3:+"$3"} 2>&1); }
w803() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$OLDK/walk_s803.py" "$1" "$ROOT/shared" "$2" "$DB" 2>&1); }
full() { case "$1" in "WALK "*) local a=${1#WALK }; [ "${a%/*}" = "${a#*/}" ];; *) return 1;; esac; }
CPDB='import sqlite3,sys;s=sqlite3.connect("file:%s?mode=ro"%sys.argv[1],uri=True,timeout=60);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close();s.close();print("copied")'

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES $NEW; do [ -n "$(to_of "$n")" ] || { say "!! [1/7] no TO pin for $n - nothing installed"; exit 1; }; done
for n in $NAMES; do [ -f "$ROOT/$n" ] || { say "!! [1/7] the live file $ROOT/$n is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] && [ -f "$SPDB" ] || { say "!! [1/7] $DB or $SPDB missing - nothing installed"; exit 1; }
[ -f "$OLDK/walk_s815.py" ] && [ -f "$OLDK/walk_s814.py" ] && [ -f "$OLDK/walk_s812.py" ] && [ -f "$OLDK/walk_s803.py" ] || { say "!! [1/7] the earlier walks are not in $OLDK - publish first. Nothing installed."; exit 1; }
ALL=1; for n in $NAMES $NEW; do [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
[ -e "$ROOT/$NEW" ] && stop "!! [1/7] $ROOT/$NEW already exists and is not this kit's - nothing installed. Tell Claude."
mkdir -p "$SCR/built" "$SCR/w803" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/7] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/7] kit gates green; the build lock taken by $KIT"
else say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do fr=$(from_of "$n"); [ "$(m5 "$ROOT/$n")" = "$fr" ] || stop "!! [2/7] $ROOT/$n is $(m5 "$ROOT/$n" | cut -c1-8), expected ${fr:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
"$APY" -B make_s837.py "$ROOT" "$SCR/built" "$KDIR" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/7] the builder refused - nothing installed"; }
for n in $NAMES $NEW; do [ "$(m5 "$SCR/built/$n")" = "$(to_of "$n")" ] || stop "!! [2/7] rebuilt, $n is not at its TO pin - nothing installed"; done
for py in "$APY" "$VPY"; do for n in $NAMES $NEW; do case "$n" in *.py) PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/$n" || stop "!! [2/7] $n does not compile on $py - nothing installed";; esac; done; done
say "[2/7] six live pins exact; rebuilt here at their TO pins with the new reader; every .py compiles on both pythons"
"$VPY" -c "$CPDB" "$DB" "$SCR/finance.db" >/dev/null && "$VPY" -c "$CPDB" "$SPDB" "$SCR/spine.db" >/dev/null || stop "!! [3/7] could not copy the databases for the walk - nothing installed"
lay new && for n in $NAMES $NEW; do \cp -p "$SCR/built/$n" "$SCR/root_new/$n" || stop "!! [3/7] could not copy $n into the walk's layout - nothing installed"; done || stop "!! [3/7] could not lay out the walk - nothing installed"
O=$(w837 "$SCR/root_new"); R=$(printf '%s\n' "$O" | tail -1)
printf '%s\n' "$O" | grep -E "^FAIL|Error" | head -8 | sed 's/^/      /'
full "$R" || stop "!! [3/7] walk_s837: $R - nothing installed"
O1=$(wold walk_s815.py "$SCR/root_new/finance" "$DMAP"); R1=$(printf '%s\n' "$O1" | tail -1); full "$R1" || stop "!! [3/7] the reports-on-need walk (S815) on the rebuilt files: $R1 - nothing installed"
O2=$(wold walk_s814.py "$SCR/root_new/finance"); R2=$(printf '%s\n' "$O2" | tail -1); full "$R2" || stop "!! [3/7] the Ask walk (S814) on the rebuilt files: $R2 - nothing installed"
if [ "${REHEARSE_NO_S812:-0}" = 1 ]; then R3="(the section A walk: not on a rehearsal stand -- it needs the box's own spine)"
else O3=$(wold walk_s812.py "$SCR/root_new/finance"); R3=$(printf '%s\n' "$O3" | tail -1); full "$R3" || stop "!! [3/7] the section A walk (S812) on the rebuilt files: $R3 - nothing installed"; fi
lay old || stop "!! [3/7] could not lay out the control - nothing installed"
R0=$(w837 "$SCR/root_old" | tail -1); full "$R0" && stop "!! [3/7] the control on the live files did not go red ($R0) - nothing installed"
\cp -p "$SCR/built/finance/marg_billwatch.py" "$SCR/built/finance/sanjeevni_approvals.py" "$SCR/built/finance/finance_ui/finance_approvals.html" "$ROOT/finance/owner_notice.py" "$SCR/w803/"
O4=$(w803 "$SCR/w803" "$SCR/root_new/finance"); R4=$(printf '%s\n' "$O4" | tail -1); [ "$R4" = "WALK S803 GREEN" ] || { printf '%s\n' "$O4" | grep -E "RED|Error" | head -6 | sed 's/^/      /'; stop "!! [3/7] the Marg watch's own walk (S803) on the rebuilt page: $R4 - nothing installed"; }
RT=$(cd "$SCR/root_new/finance" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 120 "$VPY" -W ignore -B reports_tile.py --selftest 2>&1 | tail -1)
case "$RT" in *", 0 failures"*) ;; *) stop "!! [3/7] Shavez's page selftest on the rebuilt file: $RT - nothing installed";; esac
say "[3/7] walk_s837 on copies of the live databases: $R; reports on need: $R1; Ask: $R2; section A: $R3; the Marg watch's own: $R4; $RT; the control on the live files: red"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks and the control green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/7] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$ROOT/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/7] could not write the backup of $n - nothing placed"; done
for n in $NAMES $NEW; do st=$(stg "$n"); ref="$ROOT/$n"; [ -e "$ref" ] || ref="$ROOT/marg_ingest/marg_take.py"
  { cat "$SCR/built/$n" > "$st" && chmod --reference="$ref" "$st" 2>/dev/null; chown --reference="$ref" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(m5 "$SCR/built/$n")" ]; } || stop "!! [4/7] could not stage $n - nothing placed"; done
for n in $NEW marg_ingest/marg_ingest.py marg_ingest/marg_take.py finance/reports_tile.py finance/sanjeevni_approvals.py finance/finance_ui/finance_approvals.html finance/marg_billwatch.py; do
  mv -f "$(stg "$n")" "$ROOT/$n" || restore "the rename of $n"; done
for n in $NAMES $NEW; do [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/7]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
t1=$(ftk); case "$t1" in 404|000|5*) restore "his list page answered $t1 after the restart (the Marg watch not mounted)";; esac
say "[4/7] placed and read back: the six files and the new reader at their TO pins; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1"
TB=$(cd "$ROOT/finance" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 120 "$VPY" -W ignore -B -c "import sqlite3,sys;sys.path.insert(0,'.');sys.path.insert(0,'$ROOT/marg_ingest');import marg_billwatch as BW,marg_register as MR;c=sqlite3.connect('$DB',timeout=30);BW.ensure(c);MR.ensure(c);c.commit();print('item', 'item' in {r[1] for r in c.execute('PRAGMA table_info(marg_watch_report)')}, 'shavez', BW.setting(c,'mwr.reg_shavez',''), 'register', BW._table(c,'mi_register'))" 2>&1 | tail -1)
say "      $TB"
case "$TB" in "item True shavez off register True"|"item True shavez on register True") ;; *) restore "the tables and the switch: $TB";; esac
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/7]"
release_lock
say "[5/7] the register tables made; the item column added; Shavez's switch $(echo "$TB" | awk '{print toupper($4)}')"
say "[6/7] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s837.sh  (the six backups back, the new reader gone, the open Stock Register asks closed, $FSVC restarted)"
say "[7/7] nothing goes to Shavez until you turn him on, on your list page; nothing is asked until you ask."
say ""
say "$KIT: DONE. Marg's Stock Register for one item can now be asked from a Marg watch row or your list; it waits on your Hub until it comes."
exit 0
