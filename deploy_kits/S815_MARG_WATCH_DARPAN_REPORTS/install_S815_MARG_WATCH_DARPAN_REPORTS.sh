#!/bin/bash
# =============================================================================
#  install_S815_MARG_WATCH_DARPAN_REPORTS.sh · kit S815 (13-Nov-2026, Sanjeevni sessions 446-448) · the owner's "looks right" of 11:33 IST (D960)
#  (a) Darpan's own Ask line: a Marg watch question to Darpan lands FIRST on his own page, Kal ka hisaab -- one tap, an optional line, no take-back.
#  (b) Reports on need: a sale report (Detail) asked again -- by him from a row, or by the Marg watch itself when 3 or more items rise on one
#      closing with no record (his figure on the page; only moves found after this install) -- shows on Shavez's Aaj ki reports, closes itself.
#  1. /root/finance/marg_billwatch.py a36d8265 -> TO   2. /root/finance/darpan_kal.py a64353c0 -> TO   3. /root/finance/darpan_kal.html b89ca3ad -> TO
#  4. /root/finance/reports_tile.py   a96bcad5 -> TO   5. /root/finance/owner_notice.py 8bbfb9ef -> TO (the tick closes an ask whose files came; sends nothing)
#  All five REBUILT HERE from the live bytes (make_s815a/b/c/d.py), checked against the TO pins. The duty map (DUTY_MAP.json v24: darpan.mw_ask,
#  shavez.mw_report) rides the publish -- this installer stops unless the repository's copy carries both. clinic-finance is restarted.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s815kit && cp -rp /root/deploy/repo/deploy_kits/S815_MARG_WATCH_DARPAN_REPORTS /tmp/s815kit && bash /tmp/s815kit/install_S815_MARG_WATCH_DARPAN_REPORTS.sh
#  (DRY=1 before bash: every gate, the walks and the control; NOTHING written.)
# =============================================================================
set -u
KIT="S815_MARG_WATCH_DARPAN_REPORTS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"; SPDB="${SPDB:-$ROOT/finance/spine/spine.db}"
DMAP="${DMAP:-/root/deploy/repo/claude_code_briefs/DUTY_MAP.json}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="marg_billwatch.py darpan_kal.py darpan_kal.html reports_tile.py owner_notice.py"
from_of() { case "$1" in marg_billwatch.py) echo a36d82651b09996c4bc85139af2690e3;; darpan_kal.py) echo a64353c066bfbaa5b226415786486850;;
  darpan_kal.html) echo b89ca3ad270af00eb174973d8975ad3d;; reports_tile.py) echo a96bcad5acb429699465557b66b40665;; owner_notice.py) echo 8bbfb9ef8a59e0715eb209da0d155357;; esac; }
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s815_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { local f; f=$(from_of "$1"); echo "$ROOT/finance/$1.bak_S815_${f:0:8}"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES; do rm -f "$ROOT/finance/.$n.s815"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
# on any way back: the old page knows no question on Darpan's page and no asked report -- an open one is closed as withdrawn (the row keeps it)
WD_PY="import sqlite3,sys,datetime;c=sqlite3.connect(sys.argv[1],timeout=30);t={r[0] for r in c.execute('SELECT name FROM sqlite_master WHERE type=\'table\'')};n=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S');c.execute('UPDATE marg_watch_ask SET staff_ref=\'darpan:withdrawn\' WHERE staff_ref=\'darpan:card\' AND answered_at IS NULL') if 'marg_watch_ask' in t else None;c.execute('UPDATE marg_watch_report SET closed_at=?, closed_how=\'withdrawn_S815\' WHERE closed_at IS NULL',(n,)) if 'marg_watch_report' in t else None;c.commit()"
restore() { say "!! RED after placing ($1) - putting the five files back (the report table stays; the old files never read it)"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/finance/$n"; done
  "$VPY" -c "$WD_PY" "$DB" 2>/dev/null || true; "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do f=$(from_of "$n"); say "   $n $(m5 "$ROOT/finance/$n" | cut -c1-8) (expected ${f:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
mkfin() { rm -rf "$SCR/fin_$1"; mkdir -p "$SCR/fin_$1/spine" "$SCR/fin_$1/finance_ui" && find "$ROOT/finance" -maxdepth 1 -type f \( -name '*.py' -o -name '*.html' -o -name '*.sql' -o -name '*.json' \) -exec cp -p {} "$SCR/fin_$1/" \; && \cp -p "$ROOT"/finance/finance_ui/*.html "$SCR/fin_$1/finance_ui/" 2>/dev/null; \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/fin_$1/spine/" 2>/dev/null; [ -f "$SCR/fin_$1/marg_billwatch.py" ]; }
walk() { (cd /tmp && TMPDIR="$SCR" PYTHONPATH="$ROOT/shared${PYTHONPATH:+:$PYTHONPATH}" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/$1" "$2" "$SCR/spine.db" "$SCR/finance.db" ${3:+"$3"} 2>&1); }
w803() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s803.py" "$1" "$ROOT/shared" "$ROOT/finance" "$DB" 2>&1); }
full() { case "$1" in "WALK "*) local a=${1#WALK }; [ "${a%/*}" = "${a#*/}" ];; *) return 1;; esac; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES; do [ -n "$(to_of "$n")" ] && [ -f "$ROOT/finance/$n" ] || { say "!! [1/7] the TO pin or the live file of $n missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] && [ -f "$SPDB" ] || { say "!! [1/7] $DB or $SPDB missing - nothing installed"; exit 1; }
ALL=1; for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
"$APY" -c "import json,sys;m=json.load(open(sys.argv[1]));ids={d.get('id') for d in m.get('duties',[])};sys.exit(0 if int(m.get('version',0))>=24 and {'darpan.mw_ask','shavez.mw_report'}<=ids else 1)" "$DMAP" 2>/dev/null \
  || { say "!! [1/7] the duty map $DMAP does not carry darpan.mw_ask and shavez.mw_report (v24) - publish first, then run this line again. Nothing installed."; exit 1; }
mkdir -p "$SCR/built" "$SCR/w803" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/7] DRY RUN: kit gates green; the duty map v24 carries both duties; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/7] kit gates green; the duty map v24 carries both duties; the build lock taken by $KIT"
else say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do fr=$(from_of "$n"); [ "$(m5 "$ROOT/finance/$n")" = "$fr" ] || stop "!! [2/7] $ROOT/finance/$n is $(m5 "$ROOT/finance/$n" | cut -c1-8), expected ${fr:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
{ "$APY" -B make_s815a.py "$ROOT/finance/darpan_kal.py" "$ROOT/finance/darpan_kal.html" "$SCR/built/darpan_kal.py" "$SCR/built/darpan_kal.html" \
  && "$APY" -B make_s815b.py "$ROOT/finance/marg_billwatch.py" "$KDIR/seg_bw_s815.py" "$SCR/built/marg_billwatch.py" \
  && "$APY" -B make_s815c.py "$ROOT/finance/reports_tile.py" "$SCR/built/reports_tile.py" \
  && "$APY" -B make_s815d.py "$ROOT/finance/owner_notice.py" "$SCR/built/owner_notice.py"; } > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/7] the builder refused - nothing installed"; }
for n in $NAMES; do [ "$(m5 "$SCR/built/$n")" = "$(to_of "$n")" ] || stop "!! [2/7] rebuilt, $n is not at its TO pin - nothing installed"; done
for py in "$APY" "$VPY"; do for f in marg_billwatch.py darpan_kal.py reports_tile.py owner_notice.py; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/$f" || stop "!! [2/7] $f does not compile on $py - nothing installed"; done; done
say "[2/7] five live pins exact; rebuilt here at their TO pins; the four .py compile on both pythons"
"$VPY" -B copy_dbs.py "$DB" "$SCR/finance.db" >/dev/null && "$VPY" -B copy_dbs.py "$SPDB" "$SCR/spine.db" >/dev/null || stop "!! [3/7] could not copy the databases for the walk - nothing installed"
mkfin new && for n in $NAMES; do \cp -p "$SCR/built/$n" "$SCR/fin_new/$n" || exit 9; done || stop "!! [3/7] could not lay out the walk - nothing installed"
O=$(walk walk_s815.py "$SCR/fin_new" "$DMAP"); R=$(printf '%s\n' "$O" | tail -1)
printf '%s\n' "$O" | grep -E "^FAIL|Error" | head -8 | sed 's/^/      /'
full "$R" || stop "!! [3/7] walk_s815: $R - nothing installed"
O1=$(walk walk_s814.py "$SCR/fin_new"); R1=$(printf '%s\n' "$O1" | tail -1); full "$R1" || stop "!! [3/7] the Ask walk (S814) on the rebuilt files: $R1 - nothing installed"
O2=$(walk walk_s812.py "$SCR/fin_new"); R2=$(printf '%s\n' "$O2" | tail -1); full "$R2" || stop "!! [3/7] the section A walk (S812) on the rebuilt files: $R2 - nothing installed"
mkfin old || stop "!! [3/7] could not lay out the control - nothing installed"
R0=$(walk walk_s815.py "$SCR/fin_old" "$DMAP" | tail -1); full "$R0" && stop "!! [3/7] the control on the live files did not go red ($R0) - nothing installed"
\cp -p "$SCR/built/marg_billwatch.py" "$SCR/built/owner_notice.py" "$SCR/w803/"; \cp -p "$ROOT/finance/sanjeevni_approvals.py" "$ROOT/finance/finance_ui/finance_approvals.html" "$SCR/w803/"
O3=$(w803 "$SCR/w803"); R3=$(printf '%s\n' "$O3" | tail -1); [ "$R3" = "WALK S803 GREEN" ] || { printf '%s\n' "$O3" | grep -E "RED|Error" | head -6 | sed 's/^/      /'; stop "!! [3/7] the Marg watch's own walk (S803) on the rebuilt page: $R3 - nothing installed"; }
RT=$(cd "$SCR/fin_new" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 120 "$VPY" -W ignore -B reports_tile.py --selftest 2>&1 | tail -1)
case "$RT" in *", 0 failures"*) ;; *) stop "!! [3/7] Shavez's page selftest on the rebuilt file: $RT - nothing installed";; esac
say "[3/7] walk_s815 on copies of the live databases: $R; the Ask walk: $R1; section A: $R2; the Marg watch's own: $R3; $RT; the control on the live files: red"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks and the control green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/7] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$ROOT/finance/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/7] could not write the backup of $n - nothing placed"; done
for n in $NAMES; do st="$ROOT/finance/.$n.s815"
  { cat "$SCR/built/$n" > "$st" && chmod --reference="$ROOT/finance/$n" "$st" 2>/dev/null; chown --reference="$ROOT/finance/$n" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(m5 "$SCR/built/$n")" ]; } || stop "!! [4/7] could not stage $n - nothing placed"; done
for n in owner_notice.py reports_tile.py darpan_kal.html darpan_kal.py marg_billwatch.py; do mv -f "$ROOT/finance/.$n.s815" "$ROOT/finance/$n" || restore "the rename of $n"; done
for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/7]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
say "[4/7] placed and read back: the five files at their TO pins; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1"
TB=$(cd "$ROOT/finance" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 120 "$VPY" -W ignore -B -c "import sqlite3,sys;sys.path.insert(0,'.');import marg_billwatch as BW;c=sqlite3.connect('$DB',timeout=30);BW.ensure(c);c.commit();print('report', BW._rpt_table(c), 'cluster', BW.rpt_cluster(c), 'since', BW.setting(c,'mwr.since','')[:16])" 2>&1 | tail -1)
say "      $TB"
printf '%s\n' "$TB" | grep -q "^report True cluster 3 since 20" || restore "the report table: $TB"
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/7]"
release_lock
say "[5/7] the report table made; the figure 3; history never asks by itself (from $(printf '%s' "$TB" | awk '{print $NF}'))"
say "[6/7] undo (one line): for n in $NAMES; do \\cp -p $ROOT/finance/\$n.bak_S815_* $ROOT/finance/\$n; done && $VPY -c \"$WD_PY\" $DB && $SYSTEMCTL restart $FSVC"
say "[7/7] nothing goes to Darpan until you put a question on his page; Shavez's page shows a card only when a report is asked for."
say ""
say "$KIT: DONE. A question can now go to Darpan's own page; a sale report asked again shows on Shavez's Aaj ki reports and closes itself when the files come."
exit 0
