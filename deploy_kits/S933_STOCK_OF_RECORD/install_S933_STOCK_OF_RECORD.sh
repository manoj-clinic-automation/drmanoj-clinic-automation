#!/bin/bash
# =============================================================================
#  install_S933_STOCK_OF_RECORD.sh · kit S933 v1.2 (22-Nov-2026, Sanjeevni session 504) · the owner's "go" 19:33 IST -- AFTER S928 / S930; v1.2 over the live v1.1 (21:29 IST)
#   v1.2 (21:32 IST, the owner's challenge on TYRO BR / TRAMATEE): a bill with no first-seen day is placed by the residual, never assumed inside; a pre-window bill
#        first seen on the print day is placed by the surplus; a fresh count below Marg names the bill of the day before ("was that delivery on the shelf?");
#        a count older than 21 days is called an estimate ("count again"); the below-zero note once.
#   v1.1 (the cold review's should-fixes + the first live read, 21:12 IST): the residual against the PREVIOUS print carried through the window (the
#        ledger's reading) + Amir's filed vouchers -- v1.0 measured it from the opening and flagged 30+ rows as "moved with no record"; a RETURN keyed
#        late subtracted; the surplus test (a bill the print held after all); a count carried below zero judged at 0; an item at zero in Marg with a
#        count judged against zero; approx = a family figure only.
#   NEW /root/finance/stock_record.py : THE STOCK OF RECORD -- one table (stock_of_record) every page reads: Marg's newest closing report (a morning
#        print = the end of the day before, no hold), the bills Amir keyed after the print (his export's first-seen day; the shortfall decides a
#        same-day one), the sales since, the last count carried forward, the deliveries waiting in one of three states, consumables, Marg behind a bill.
#   /root/finance/stock_figure.py   8130315e -> TO : S928's bill_units speaks on every scan tie (arrived=0 when the tap came before the scan).
#   /root/finance/stock_check.py    42118289 -> TO : record() reads the stock of record; the page computes no stock figure itself.
#   /root/finance/stock_check.html  ae61a18c -> TO : the words (a bill keyed after the print), Marg behind a bill, clinic consumables, the closing's day.
#   /root/finance/item_ledger.py    5fbb6020 -> TO : the head figures (Marg stock / Expected) from the record.
#   crontab: `*/10 5-23 * * * ... stock_record.py --build` (# S933_STOCK_OF_RECORD) -- the record kept fresh between page reads.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s933kit && cp -rp /root/deploy/repo/deploy_kits/S933_STOCK_OF_RECORD /tmp/s933kit && bash /tmp/s933kit/install_S933_STOCK_OF_RECORD.sh
#  (DRY=1 before bash: every gate and the walk; NOTHING written.)
# =============================================================================
set -u
KIT="S933_STOCK_OF_RECORD"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
REPO_KITS="${REPO_KITS:-/root/deploy/repo/deploy_kits}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"; SPINE_DB_LIVE="${SPINE_DB_LIVE:-$ROOT/finance/spine/spine.db}"
CRON_LINE='*/10 * * * * cd /root/finance && FINANCE_DB=/root/finance/finance.db SHARED_LIB_DIR=/root/shared flock -n /tmp/stock_record.lock /root/wa/venv/bin/python3 -B /root/finance/stock_record.py --build >> /root/finance/stock_record.log 2>&1 # S933_STOCK_OF_RECORD'   # every ten minutes round the clock (the box clock is not IST); --build does nothing when the record is fresh
NAMES=("finance/stock_record.py" "finance/stock_figure.py" "finance/stock_check.py" "finance/stock_check.html" "finance/item_ledger.py")
FROMS=("ed3223bf806366b1b15bbbe7832d0d43" "5d15e77dae11c7ee0799290e1a442760" "bf68c55b20f90673b134e8d25c23aaa5" "4d6cbc6f8733226663688371473c0ff0" "d2f68ee900dfbcb40a25f570f6782c58")   # v1.2 over v1.1 (live 21:29 IST 22-Nov): stock_record.py v1.1 -> v1.2; the four others unchanged (FROM = TO). The v1.0 kit's FROMS were 8130315e / 42118289 / ae61a18c / 5fbb6020 (+ stock_record absent) -- undo_s933.sh still returns to THOSE (the pre-S933 files) from the first install's backups.
KF=("stock_record.py" "stock_figure.py" "stock_check.py" "stock_check.html" "item_ledger.py")
N=5; IDX="0 1 2 3 4"
TOS=(); for k in $IDX; do TOS[$k]="$(awk -v f="${NAMES[$k]}" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s933_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cur() { [ -f "$ROOT/${NAMES[$1]}" ] && m5 "$ROOT/${NAMES[$1]}" || echo absent; }
say() { echo "$@"; }
bak() { echo "$ROOT/${NAMES[$1]}.bak_S933_${FROMS[$1]:0:8}"; }
stg() { local n="${NAMES[$1]}"; echo "$(dirname "$ROOT/$n")/.$(basename "$n").s933"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for k in $IDX; do rm -f "$(stg $k)"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
CT() { if [ -n "${CRONTAB_CMD:-}" ]; then $CRONTAB_CMD "$@"; else crontab "$@"; fi; }
CRON_BAK="$ROOT/finance/crontab.bak_S933_$(date +%Y%m%d_%H%M%S)"
cron_save() { CT -l > "$CRON_BAK" 2>/dev/null; [ -s "$CRON_BAK" ] && [ "$(grep -c '' "$CRON_BAK")" -ge 10 ]; }   # the whole crontab must read back (the estate has ~110 lines) before any rewrite -- never a crontab holding this line alone
cron_off() { cron_save || { say "!! the crontab could not be read back ($CRON_BAK) - NOT rewriting it"; return 1; }; grep -v '# S933_STOCK_OF_RECORD' "$CRON_BAK" | CT - ; }
cron_on() { cron_save || { say "!! the crontab could not be read back ($CRON_BAK) - NOT rewriting it"; return 1; }; { grep -v '# S933_STOCK_OF_RECORD' "$CRON_BAK"; echo "$CRON_LINE"; } | CT - && [ "$(CT -l | grep -c '')" -ge "$(grep -c '' "$CRON_BAK")" ]; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting everything back"
  for k in $IDX; do if [ "${FROMS[$k]}" = absent ]; then rm -f "$ROOT/${NAMES[$k]}"; else [ -f "$(bak $k)" ] && \cp -p "$(bak $k)" "$ROOT/${NAMES[$k]}"; fi; done
  if CT -l 2>/dev/null | grep -q '# S933_STOCK_OF_RECORD'; then cron_off; fi
  "$SYSTEMCTL" restart "$FSVC" || true
  for k in $IDX; do say "   ${NAMES[$k]} $(cur $k | cut -c1-8) (expected ${FROMS[$k]:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 1500 "$VPY" -u -W ignore -B "$@" 2>&1); }
reds() { { echo "$1" | grep -E '^(FAIL|RED)' | sed -E 's/^(FAIL|RED) +//' | cut -d'[' -f1 | sed 's/ *$//'; echo "$1" | grep -q '^RESULT:' || echo "the walk did not finish"; } | sort -u; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in $IDX; do [ -n "${TOS[$k]}" ] && [ "$(m5 "$KDIR/${KF[$k]}")" = "${TOS[$k]}" ] || { say "!! [1/6] the kit's ${KF[$k]} is not at its TO pin - nothing installed"; exit 1; }; done
ALL=1; for k in $IDX; do [ "$(cur $k)" = "${TOS[$k]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "$KIT: ALREADY INSTALLED - the files are at the new version."; exit 0; fi
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/6] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken by $KIT"
else say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for k in $IDX; do [ "$(cur $k)" = "${FROMS[$k]}" ] || { [ "${FROMS[$k]}" = absent ] && [ "$(cur $k)" = "${TOS[$k]}" ]; } || stop "!! [2/6] $ROOT/${NAMES[$k]} is $(cur $k | cut -c1-8), expected ${FROMS[$k]:0:8} - STOP, nothing installed. (S928 and S930 must be live.) Tell Claude."; done
[ -f "$REPO_KITS/S928_STOCK_ONE_RULE/synth_s928.py" ] || stop "!! [2/6] the repo has no S928_STOCK_ONE_RULE/synth_s928.py (an earlier proof) - nothing installed"
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/stock_record.py" "$KDIR/stock_figure.py" "$KDIR/stock_check.py" "$KDIR/item_ledger.py" "$KDIR/synth_s933.py" "$KDIR/liveshape_s933.py" || stop "!! [2/6] a file does not compile on $p - nothing installed"; done
say "[2/6] the live files at their FROM pins; the kit's python compiles on both pythons"
mkdir -p "$SCR/new" "$SCR/old" "$SCR/new/spine" "$SCR/old/spine" && \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.sql "$ROOT"/finance/*.json "$SCR/new/" 2>/dev/null; \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/new/spine/" 2>/dev/null
\cp -rp "$SCR/new/." "$SCR/old/"
mkdir -p "$SCR/new/finance_ui" "$SCR/old/finance_ui" && \cp -p "$ROOT"/finance/finance_ui/* "$SCR/new/finance_ui/" 2>/dev/null; \cp -p "$ROOT"/finance/finance_ui/* "$SCR/old/finance_ui/" 2>/dev/null
\cp -p "$ROOT"/finance/finance_ui/finance_approvals.html "$SCR/new/" 2>/dev/null; \cp -p "$ROOT"/finance/finance_ui/finance_approvals.html "$SCR/old/" 2>/dev/null   # S927's walk reads it beside the code
for k in $IDX; do \cp -p "$KDIR/${KF[$k]}" "$SCR/new/" || stop "!! [3/6] could not lay out the walk - nothing installed"; done
copydb() { py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2" >/dev/null && [ -s "$2" ]; }
copydb "$LIVE_DB" "$SCR/copy.db" || stop "!! [3/6] could not take a copy of the database - nothing installed"
# (a) the synth: made-up spine, scans, orders, bills, counts on a scratch database with the copy's schema; the control (the live files) must go red
W1=$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$KDIR/synth_s933.py" "$SCR/new" "$SCR/copy.db"); R1=$(echo "$W1" | tail -1)
echo "$W1" | grep "^INFO" | cut -c1-220
[ "$R1" = "RESULT: ALL PASS" ] || { echo "$W1" | grep -E "^FAIL|Traceback|Error" | cut -c1-220; stop "!! [3/6] the walk on the new files: $R1 - nothing installed"; }
W0=$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$KDIR/synth_s933.py" "$SCR/old" "$SCR/copy.db" --control); R0=$(echo "$W0" | tail -1)
case "$R0" in "RESULT: "*FAIL) ;; *) stop "!! [3/6] the control did not go red ($R0) - nothing installed";; esac
say "[3/6] S933's walk: $(echo "$W1" | grep -c '^ok') checks pass on the new files; the control goes red as it must ($(echo "$W0" | grep -c '^FAIL') red)"
# (b) the live shape: the record built on copies of the live databases; the page on it, beside the old page's figures
if [ -f "$SPINE_DB_LIVE" ]; then
  copydb "$SPINE_DB_LIVE" "$SCR/spine.db" || stop "!! [3/6] could not copy the spine - nothing installed"; copydb "$LIVE_DB" "$SCR/c_ls.db" || stop "!! [3/6] could not copy the database - nothing installed"
  LS=$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$KDIR/liveshape_s933.py" "$SCR/new" "$SCR/old" "$SCR/c_ls.db" "$SCR/spine.db"); RL=$(echo "$LS" | tail -1)
  echo "$LS" | grep -E "^INFO|^   " | head -24 | cut -c1-220
  [ "$RL" = "RESULT: ALL PASS" ] || { echo "$LS" | grep -E "Traceback|Error" | head -5 | cut -c1-200; stop "!! [3/6] the record on copies of the live databases: $RL - nothing installed"; }
  say "   the record builds on copies of the live databases and the page reads it"
  rm -f "$SCR/c_ls.db" "$SCR/spine.db"
else stop "!! [3/6] no spine at $SPINE_DB_LIVE - the live-shape build cannot run; nothing installed"; fi
# (c) the earlier kits' proofs are not worse on the new files (S837 rule)
WORSE=""
for kk in S927_HUB_NEEDS_YOU_INLINE/walk_s927.py; do
  w="$REPO_KITS/$kk"; [ -f "$w" ] || { say "   (no $kk in the repo - skipped)"; continue; }
  copydb "$LIVE_DB" "$SCR/c_old.db"; copydb "$LIVE_DB" "$SCR/c_new.db"
  O=$(py "$w" "$SCR/old" "$SCR/c_old.db"); Nn=$(py "$w" "$SCR/new" "$SCR/c_new.db")
  extra=$(comm -13 <(reds "$O") <(reds "$Nn") | grep -v '^$')
  say "   $(basename "$w"): old $(echo "$O" | grep -c '^ok') ok / new $(echo "$Nn" | grep -c '^ok') ok"
  [ -z "$extra" ] || WORSE="$WORSE
$(basename "$w"): $extra"
  rm -f "$SCR/c_old.db" "$SCR/c_new.db"
done
S8=$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$REPO_KITS/S928_STOCK_ONE_RULE/synth_s928.py" "$SCR/new" "$SCR/copy.db"); R8=$(echo "$S8" | tail -1)
say "   synth_s928 on the new files: $R8"
[ "$R8" = "RESULT: ALL PASS" ] || WORSE="$WORSE
synth_s928: $R8"
if [ -f "$REPO_KITS/S930_STOCK_CHECK_PAGE/walk_s930.py" ]; then
  copydb "$LIVE_DB" "$SCR/c_w930.db"
  S9=$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$REPO_KITS/S930_STOCK_CHECK_PAGE/walk_s930.py" "$SCR/new" "$SCR/c_w930.db" "$REPO_KITS/S928_STOCK_ONE_RULE"); R9=$(echo "$S9" | tail -1)
  S9o=$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$REPO_KITS/S930_STOCK_CHECK_PAGE/walk_s930.py" "$SCR/old" "$SCR/c_w930.db" "$REPO_KITS/S928_STOCK_ONE_RULE")
  # two of walk_s930's lines are SUPERSEDED by S933 and are not a worsening: a delivery waiting for an UNCOUNTED item is now shown (the old
  # page listed waiting lines for counted items only), so its fixture's BETA (never counted, a tap the matcher pairs with the scan's ZETA line
  # -- the S619 letters-alike rule, two letters apart) now carries a waiting line and the totals' 'arrived' count moves 1 -> 2.
  extra=$(comm -13 <(reds "$S9o") <(reds "$S9") | grep -v '^$' | grep -v -e '^C: BETA (tapped, not on the bill)' -e '^C: the totals -- 10 items')
  say "   walk_s930 on the new files: $R9 (old: $(echo "$S9o" | tail -1)); its two superseded lines (an uncounted item's waiting delivery) are not counted as worse"
  [ -z "$extra" ] || WORSE="$WORSE
walk_s930: $extra"
  rm -f "$SCR/c_w930.db"
fi
[ -z "$WORSE" ] || stop "!! [3/6] an earlier kit's proof is WORSE on the new files than on the live ones - nothing installed:$WORSE"
rm -f "$SCR/copy.db"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walks green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
for k in $IDX; do if [ "${FROMS[$k]}" = absent ]; then [ ! -e "$ROOT/${NAMES[$k]}" ] || [ "$(cur $k)" = "${TOS[$k]}" ] || stop "!! [4/6] $ROOT/${NAMES[$k]} already exists with other bytes - nothing placed"; continue; fi
  { \cp -p "$ROOT/${NAMES[$k]}" "$(bak $k)" && [ "$(m5 "$(bak $k)")" = "${FROMS[$k]}" ]; } || stop "!! [4/6] could not write the backup of ${NAMES[$k]} - nothing placed"; done
for k in $IDX; do s="$(stg $k)"; ref="$ROOT/${NAMES[$k]}"; [ -e "$ref" ] || ref="$ROOT/finance/stock_figure.py"
  { cat "$KDIR/${KF[$k]}" > "$s" && chmod --reference="$ref" "$s" 2>/dev/null; chown --reference="$ref" "$s" 2>/dev/null; [ "$(m5 "$s")" = "${TOS[$k]}" ]; } || stop "!! [4/6] could not stage ${KF[$k]} - nothing placed"; done
PLACING=1
for k in $IDX; do mv -f "$(stg $k)" "$ROOT/${NAMES[$k]}" || restore "the rename of ${KF[$k]}"; [ "$(cur $k)" = "${TOS[$k]}" ] || restore "read back of ${KF[$k]}"; done
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d1=$(door /finance/stockcheck/api/healthz); case "$d1" in 404|000|5*) restore "the Stock check healthz answers $d1";; esac   # login-gated: 302 says nothing (F-1439); the log proves the mount
d2=$(door /finance/stockcheck/); case "$d2" in 404|000|5*) restore "the Stock check page answers $d2";; esac
d3=$(door /finance/sanjeevni/ledger); case "$d3" in 404|000|5*) restore "the item ledger answers $d3";; esac
d4=$(door /finance/sanjeevni/approvals); case "$d4" in 404|000|5*) restore "his Hub page answers $d4";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "stock_check not mounted|hub_panels not mounted|hub_cash not mounted|Traceback" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
flog | grep -q "S930 stock_check mounted v1.2" || restore "the service log since the restart does not say stock_check mounted v1.2 (F-1554)"
# the first build of the record on the LIVE database (the page never computes stock itself now); then the cron line, with the crontab read back whole first
B1=$(cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" timeout 600 "$VPY" -B "$ROOT/finance/stock_record.py" --build --force 2>&1 | tail -3)
echo "$B1" | grep -q '"ok": true' || restore "the first build of the stock of record did not say ok: $(echo "$B1" | tail -1 | cut -c1-160)"
say "   $(echo "$B1" | tail -1 | cut -c1-200)"
cron_on || restore "the crontab line could not be written (the crontab is untouched; its read-back copy: $CRON_BAK)"
CT -l 2>/dev/null | grep -q '# S933_STOCK_OF_RECORD' || restore "the crontab line is not there after writing"
PLACING=0
say "[4/6] the five files placed and read back; $FSVC restarted; the stock of record built on the live database; the cron line in (the crontab's read-back copy kept at $CRON_BAK); $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the doors $d1 / $d2 / $d3 / $d4 (login-gated), the service log says stock_check mounted v1.2 and is clean since the restart"
release_lock
say "[5/6] what changes now: your Stock check page and the item ledger read ONE stock record (Marg's newest report, the bills Amir keyed after it, the sales since, the last count carried, the deliveries waiting); the record is rebuilt every ten minutes and whenever a report, tap, scan or count moves it."
say "[6/6] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s933.sh  (the four patched files back, stock_record.py removed, the cron line out, $FSVC restarted; the table stock_of_record stays, harmless)"
say ""
say "$KIT: DONE."
exit 0
