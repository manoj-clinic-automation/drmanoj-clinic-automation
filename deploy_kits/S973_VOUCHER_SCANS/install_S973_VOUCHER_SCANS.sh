#!/bin/bash
# =============================================================================
#  install_S973_VOUCHER_SCANS.sh · kit S973 (27-Nov-2026, Sanjeevni session 540) · kit C of S534_FINAL_BUILD_PLAN (D1091 plan 2.4)
#  His "Proceed" 18:42 IST 27-Nov on S538_KIT_C_DESIGN. MARG STOCK VOUCHERS SCANNED ON THE PHARMACY LANE:
#   /root/finance/voucher_scan.py       NEW      : the print asks (a claim 'Pehle bana chuka hoon', a cut name), the scans read READ ONLY,
#                                                   a claim settled / back to Amir, a cut line named; reception's lines; the one push
#   /root/finance/voucher_inquiry.py    ac76b9d3 : 'already' -> the print card; the scan settles; his two settings
#   /root/finance/voucher_judge.py      6c725941 -> v1.4 : the register route only when no print ask is open; 'the voucher's scan'
#   /root/finance/amir_day.py           27a2a128 : the print card ('Print diya — reception ko' . 'Khud scan karein'); 'already' syncs at once
#   /root/finance/porders_s454.py       3f52d1f3 : reception's 'Stock voucher scan karna hai' on Aaj ka bill kaam
#   /root/assetapp/asset_register.py    a325d0f4 : (the Scan App's, PLANNED v2415) kind 'Stock voucher' -- the link, the reading, the heal
#   /root/assetapp/claude_reader.py     5b27b226 : (the Scan App's, PLANNED v2415) the pharmacy reader knows a stock voucher
#   /root/shared/scan_quality.py        505a114f : a stock voucher is never judged as a bill (never a 'rescan' ask)
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s973kit && cp -rp /root/deploy/repo/deploy_kits/S973_VOUCHER_SCANS /tmp/s973kit && bash /tmp/s973kit/install_S973_VOUCHER_SCANS.sh
#  (DRY=1 before bash: every gate and the walks; NOTHING written.)
# =============================================================================
set -u
KIT="S973_VOUCHER_SCANS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; REPO="${REPO:-/root/deploy/repo}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; ASVC="${ASVC:-assetapp}"; A_PORT="${A_PORT:-8030}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"; ADB="${ADB:-$ROOT/assetapp/assets.db}"
FILES=("finance/voucher_inquiry.py ac76b9d339de6b58b7835cab7e46e08d" "finance/voucher_judge.py 6c7259418481cd9f37099f93a9ca7b17"
       "finance/amir_day.py 27a2a128f8e6fbdbf0c015727db70538" "finance/porders_s454.py 3f52d1f390ff704d152fd3b96bba5afc" "finance/voucher_scan.py NEW"
       "assetapp/asset_register.py a325d0f400923e1989ff4cd2a4df408d" "assetapp/claude_reader.py 5b27b2269f4f358a36cd62aef6b0eb7a"
       "shared/scan_quality.py 505a114f34452b5be994b04eca36e4b7")
READS=("finance/stock_check.py 623c1052" "finance/stock_watch.py fe0a89cd" "finance/item_ledger.py 6735167f" "finance/order_rules.py 21e7cbee"
       "finance/marg_billwatch.py 9edda626" "finance/purchase_app.py c124adf3" "finance/scan_register.py 44d6e05e" "finance/order_track_page.py 37870161"
       "assetapp/sorting_desk.py 2eeb8b39" "assetapp/asset_machine.py 7dbd5e0c" "assetapp/stationery.py cfb3d8b5" "assetapp/batteries.py bb082b4c"
       "assetapp/procroom.py 3344e279" "assetapp/claude_reread.py ed7023d2" "assetapp/reader_watch.py 5ba95fce" "assetapp/clinic_papers.py 91305fe0"
       "assetapp/xray_costs.py 0a296116" "shared/scan_checks_s441.py 5c934bdb")
KEEP="shared/scan_quality.py"   # second look M2: never put back -- papers already filed 'Stock voucher' must never be judged as bills again
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s973_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
ahz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$A_PORT/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$2$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD "$1"; else journalctl -u "$1" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for e in "${FILES[@]}"; do n="${e%% *}"; rm -f "$ROOT/$(dirname "$n")/.$(basename "$n").s973"; done; release_lock; rm -rf "${SCR:?}"
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
apy() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$APY" -u -W ignore -B "$@" 2>&1); }
fin() { (cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" ASSETS_DB="$ADB" SHARED_LIB_DIR="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
dbback() { "$VPY" -c "
import sqlite3,sys,datetime as dt
c=sqlite3.connect(sys.argv[1], timeout=30); ts=dt.datetime.now(dt.timezone(dt.timedelta(hours=5,minutes=30))).strftime('%Y-%m-%d %H:%M:%S')
n=c.execute(\"UPDATE amir_job SET said_at=?, said_by='S973 put back', said_what='withdrawn', done_at=?, done_how='withdrawn' WHERE key LIKE 'S973:%' AND done_at IS NULL\", (ts, ts)).rowcount
has=lambda t: c.execute('SELECT 1 FROM sqlite_master WHERE name=?', (t,)).fetchone()
m=c.execute(\"UPDATE stock_voucher_claim SET state='yours' WHERE state='print'\").rowcount if has('stock_voucher_claim') else 0
k=c.execute(\"UPDATE stock_voucher_scanask SET state='closed', closed_at=?, closed_how='put back' WHERE state IN ('card','printed')\", (ts,)).rowcount if has('stock_voucher_scanask') else 0
c.commit(); print('S973 cards withdrawn:', n, '- claims back to his call:', m, '- print asks closed:', k)" "$LIVE_DB" 2>&1 | tail -1; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting it back"
  say "   $(dbback)"                                          # review M4: what the new code wrote in the meantime goes back to kit B's road
  for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; f="$ROOT/$n"; [ "$n" = "$KEEP" ] && continue
    if [ "$fr" = NEW ]; then [ -f "$f" ] && mv -f "$f" "$f.bak_S973_removed_$STAMP"; else b="$f.bak_S973_${fr:0:8}"; [ -f "$b" ] && \cp -p "$b" "$f"; fi; done
  "$SYSTEMCTL" restart "$FSVC" || true; "$SYSTEMCTL" restart "$ASVC" || true
  for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; say "   $n $( [ -f "$ROOT/$n" ] && m5 "$ROOT/$n" | cut -c1-8 || echo absent) (expected ${fr:0:8})"; done
  say "   $FSVC + $ASVC restarted, finance healthz $(wait200 fhz), scan app healthz $(wait200 ahz). Nothing else was changed (the empty table may stay; nothing reads it then). Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
ALL=1
for e in "${FILES[@]}"; do n="${e%% *}"; to="$(to_of "$n")"
  [ -n "$to" ] && [ "$(m5 "$KDIR/$(basename "$n")")" = "$to" ] || { say "!! [1/7] the kit's $(basename "$n") is not at its TO pin - nothing installed"; exit 1; }
  [ "$(m5 "$ROOT/$n")" = "$to" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "$KIT: ALREADY INSTALLED - the eight files are at the new version."; exit 0; fi
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/7] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/7] kit gates green; the build lock taken by $KIT"
else say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"
  if [ "$fr" = NEW ]; then [ ! -e "$ROOT/$n" ] || stop "!! [2/7] $ROOT/$n already exists ($(m5 "$ROOT/$n" | cut -c1-8)) - not this kit's; STOP, nothing installed. Tell Claude."
  elif [ "$n" = "$KEEP" ] && [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ]; then :          # kept at its new version by an earlier undo
  else [ "$(m5 "$ROOT/$n")" = "$fr" ] || stop "!! [2/7] $ROOT/$n is $(m5 "$ROOT/$n" | cut -c1-8), expected ${fr:0:8} - changed after this kit was built. STOP, nothing installed. Tell Claude."; fi; done
for r in "${READS[@]}"; do n="${r% *}"; p="${r#* }"; [ "$(m5 "$ROOT/$n" | cut -c1-8)" = "$p" ] || stop "!! [2/7] $ROOT/$n is not at $p - STOP, nothing installed. Tell Claude."; done
for w in S841_PHARMACY_CREDIT_NOTE/walk_s841_app.py S754_SUMMARY_RECOGNISE/walk_s754.py; do [ -f "$REPO/deploy_kits/$w" ] || stop "!! [2/7] $REPO/deploy_kits/$w is missing - nothing installed"; done
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/voucher_scan.py" "$KDIR/voucher_inquiry.py" "$KDIR/voucher_judge.py" "$KDIR/amir_day.py" \
  "$KDIR/porders_s454.py" "$KDIR/asset_register.py" "$KDIR/claude_reader.py" "$KDIR/scan_quality.py" "$KDIR/walk_s973.py" "$KDIR/walk_s973_app.py" "$KDIR/walk_s971.py" \
  || stop "!! [2/7] a file does not compile on $p - nothing installed"; done
say "[2/7] the seven files at their FROM pins, voucher_scan.py absent; the eighteen files the kit reads at their pins; the kit compiles on both pythons"
# [3/7] the Sanjeevni side: the walk on made-up data (twice on one layout), the control red, kit B/A2/A1/S965's walks on the new files
for side in new old; do mkdir -p "$SCR/$side/finance/spine" "$SCR/$side/marg_ingest"
  \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.json "$SCR/$side/finance/" 2>/dev/null; \cp -p "$ROOT"/shared/*.py "$SCR/$side/finance/" 2>/dev/null
  \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/$side/finance/spine/" 2>/dev/null; \cp -rp "$ROOT"/marg_ingest/*.py "$SCR/$side/marg_ingest/" 2>/dev/null
  [ -d "$ROOT/marg_ingest/xlrd" ] && \cp -rp "$ROOT/marg_ingest/xlrd" "$SCR/$side/marg_ingest/"; done
\cp -p "$KDIR/voucher_scan.py" "$KDIR/voucher_inquiry.py" "$KDIR/voucher_judge.py" "$KDIR/amir_day.py" "$KDIR/porders_s454.py" "$KDIR/scan_quality.py" "$SCR/new/finance/" \
  && \cp -p "$KDIR/voucher_scan.py" "$SCR/old/finance/" || stop "!! [3/7] could not lay out the walk - nothing installed"
W1=$(py "$KDIR/walk_s973.py" "$SCR/new/finance" "$SCR/new/marg_ingest" "$KDIR/walk_s971.py"); R1=$(echo "$W1" | tail -1)
case "$R1" in "WALK "*) a=${R1#WALK }; [ "${a%/*}" = "${a#*/}" ] && [ "${a%/*}" -ge 36 ] || { echo "$W1" | grep "^FAIL" | cut -c1-200; stop "!! [3/7] the walk: $R1 - nothing installed"; };;
  *) echo "$W1" | tail -5 | cut -c1-200; stop "!! [3/7] the walk did not finish - nothing installed";; esac
W2=$(py "$KDIR/walk_s973.py" "$SCR/new/finance" "$SCR/new/marg_ingest" "$KDIR/walk_s971.py"); [ "$(echo "$W2" | tail -1)" = "$R1" ] || stop "!! [3/7] the walk a second time: $(echo "$W2" | tail -1) - nothing installed"
W0=$(py "$KDIR/walk_s973.py" "$SCR/old/finance" "$SCR/old/marg_ingest" "$KDIR/walk_s971.py")
echo "$W0" | grep -q "^FAIL  P1 'Pehle bana chuka hoon'" || stop "!! [3/7] the control on the live files did not go red ($(echo "$W0" | tail -1)) - nothing installed"
rm -f "$SCR/new/finance/voucher_scan.py.x"
chk() { local nm="$1" want="$2" allow="$3"; local out; out=$(py "$KDIR/$nm" "$SCR/new/finance" "$SCR/new/marg_ingest"); local fl; fl=$(echo "$out" | grep "^FAIL" | grep -vE "$allow")
  [ -z "$fl" ] && echo "$out" | tail -1 | grep -q "^WALK $want" || { echo "$fl" | head -3 | cut -c1-200; stop "!! [3/7] $nm on the new files: $(echo "$out" | tail -1) - nothing installed"; }; }
chk walk_s971.py 84/85 "^FAIL  J4 the judge v1.3"
chk walk_s969.py 48/49 "^FAIL  R3 healthz v1.7 with writes"
chk walk_s967.py 39/41 "^FAIL  (W4 the healthz says v1.6|D13 the rules panel)"
chk walk_s965_regress.py 31/32 "^FAIL  C14c the healthz says v1.5"
say "[3/7] Sanjeevni: the walk $R1, twice on one layout; the control red on the live files; kit B's 84/85 (its version line), A2's 48/49, A1's 39/41, S965's 31/32 (version lines)"
# [4/7] the Scan App side: the walk on the REAL app (made-up rows), the control red, S841's and S754's walks on the new files
mkdir -p "$SCR/ato" "$SCR/afrom" "$SCR/a754" && \cp -p "$KDIR/asset_register.py" "$KDIR/claude_reader.py" "$SCR/ato/" && \cp -p "$ROOT/assetapp/asset_register.py" "$ROOT/assetapp/claude_reader.py" "$SCR/afrom/" \
  && \cp -p "$KDIR/asset_register.py" "$KDIR/claude_reader.py" "$ROOT/shared/scan_checks_s441.py" "$SCR/a754/" || stop "!! [4/7] could not lay out the app walk - nothing installed"
A1=$(apy "$KDIR/walk_s973_app.py" --live "$ROOT/assetapp" --shared "$ROOT/shared" --files "$SCR/ato" | tail -1)
[ "$A1" = "WALK: 26 green, 0 red" ] || stop "!! [4/7] the walk on the real app: $A1 - nothing installed"
A0=$(apy "$KDIR/walk_s973_app.py" --live "$ROOT/assetapp" --shared "$ROOT/shared" --files "$SCR/afrom" --expect-red | tail -1)
[ "$A0" = "CONTROL: 16 of 16 went red as they must" ] || stop "!! [4/7] the app control on the live files: $A0 - nothing installed"
A8=$(apy "$REPO/deploy_kits/S841_PHARMACY_CREDIT_NOTE/walk_s841_app.py" --live "$ROOT/assetapp" --shared "$ROOT/shared" --files "$SCR/ato" | tail -1)
[ "$A8" = "WALK: 20 green, 0 red" ] || stop "!! [4/7] S841's walk on the new files: $A8 - nothing installed"
A7=$(apy "$REPO/deploy_kits/S754_SUMMARY_RECOGNISE/walk_s754.py" --live "$ROOT/assetapp" --files "$SCR/a754" --shared "$ROOT/shared" | tail -1)
[ "$A7" = "walk_s754: 0 check(s) failed (0 of them S754 checks)" ] || stop "!! [4/7] S754's walk on the new files: $A7 - nothing installed"
py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LIVE_DB" "$SCR/copy.db" >/dev/null \
  && [ -s "$SCR/copy.db" ] || stop "!! [4/7] could not take a copy of the database - nothing installed"
LS=$(cd "$SCR/new/finance" && FINANCE_DB="$SCR/copy.db" ASSETS_DB="$ADB" SHARED_LIB_DIR="$ROOT/shared" ORDER_PUSH_STUB="$SCR/push.jsonl" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B -c "
import sqlite3,sys,datetime as dt; sys.path.insert(0,'.'); import voucher_inquiry as VI, voucher_scan as VS, voucher_judge as VJ
c=sqlite3.connect(sys.argv[1]); VI.ensure(c); VS.ensure(c); c.commit(); today=dt.datetime.now(dt.timezone(dt.timedelta(hours=5,minutes=30))).date().isoformat()
c.execute(\"INSERT INTO setting (key,value) VALUES ('stock.scan_ask_from',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value\", (today,)); c.commit()
o=VI.sync(c); n=VJ.ask_registers(c); S=VS.scans()
print('LIVE-SHAPE ok=%s print_asks=%s claims_waiting=%s cut=%s scans=%s' % (o.get('ok'), c.execute('SELECT COUNT(*) FROM stock_voucher_scanask').fetchone()[0],
      c.execute(\"SELECT COUNT(*) FROM stock_voucher_claim WHERE state='print'\").fetchone()[0], (o.get('s973') or {}).get('asked'), None if S is None else len(S)))" "$SCR/copy.db" 2>&1 | grep "^LIVE-SHAPE" | tail -1)
rm -f "$SCR/copy.db"; echo "    $LS" | cut -c1-240
case "$LS" in "LIVE-SHAPE ok="*" scans="[0-9]*) ;; *) stop "!! [4/7] kit C on a copy of the live database: ${LS:-no answer} - nothing installed";; esac
say "[4/7] the Scan App: the walk on the real app 26/26, the control 16/16 red, S841's 20/20, S754's 0 failed; kit C on a COPY of the live database (above): nothing old reaches Amir"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walks green; NOTHING written"; exit 0; fi
f0=$(fhz); a0=$(ahz); [ "$f0" = 200 ] && [ "$a0" = 200 ] || stop "!! [5/7] finance healthz $f0 / scan app healthz $a0 before the install - nothing installed"
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; [ "$fr" = NEW ] && continue; [ "$(m5 "$ROOT/$n")" = "$fr" ] || continue; b="$ROOT/$n.bak_S973_${fr:0:8}"
  { \cp -p "$ROOT/$n" "$b" && [ "$(m5 "$b")" = "$fr" ]; } || stop "!! [5/7] could not write the backup of $n - nothing placed"; done
REF="$ROOT/finance/voucher_inquiry.py"
for e in "${FILES[@]}"; do n="${e%% *}"; S="$ROOT/$(dirname "$n")/.$(basename "$n").s973"; f="$ROOT/$n"; [ -f "$f" ] || f="$REF"
  { cat "$KDIR/$(basename "$n")" > "$S" && chmod --reference="$f" "$S" 2>/dev/null; chown --reference="$f" "$S" 2>/dev/null; [ "$(m5 "$S")" = "$(to_of "$n")" ]; } || stop "!! [5/7] could not stage $n - nothing placed"; done
PLACING=1
for e in "${FILES[@]}"; do n="${e%% *}"; mv -f "$ROOT/$(dirname "$n")/.$(basename "$n").s973" "$ROOT/$n" || restore "the rename of $n"
  [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || restore "the read back of $n"; done
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"; "$SYSTEMCTL" restart "$ASVC" || restore "restart $ASVC"
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/7]"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
c2=$(wait200 ahz); [ "$c2" = 200 ] || restore "scan app healthz $c2 after the restart"
for u in /finance/amir /finance/stockcheck/ /finance/porders/s454/billkaam /finance/approvals; do d=$(door "$u" "$FIN_PORT"); case "$d" in 404|000|5*) restore "$u answers $d";; esac; done
d=$(door /desk "$A_PORT"); case "$d" in 404|000|5*) restore "the scan app's /desk answers $d";; esac
TK=$(cd "$ROOT/finance" && FINANCE_DB="$SCR/none.db" timeout 60 "$VPY" -W ignore -B -c "
import voucher_scan, voucher_judge, voucher_inquiry, amir_day
print('S973 modules ok', voucher_scan.VERSION, voucher_judge.VERSION, hasattr(voucher_inquiry,'KIT_S973'), hasattr(amir_day,'KIT_S973'))" 2>&1 | tail -1)
case "$TK" in "S973 modules ok 1.0 1.4 True True") ;; *) restore "the modules do not load ($TK)";; esac
TR=$(cd "$ROOT/assetapp" && timeout 60 "$APY" -W ignore -B -c "import claude_reader as C; print('S973 reader', C.S973_READY, C.S841_READY)" 2>&1 | tail -1)
[ "$TR" = "S973 reader True True" ] || restore "the reader does not know the stock voucher ($TR)"
sleep "${NAP:-3}"; LG=$(flog "$FSVC"); bad=$(echo "$LG" | grep -E "File \".*/(voucher_scan|voucher_inquiry|voucher_judge|amir_day|porders_s454|scan_quality)\.py\"|NOT mounted|not mounted|S973 .* failed" | head -3)
[ -z "$bad" ] || restore "the finance log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
AL=$(flog "$ASVC"); abad=$(echo "$AL" | grep -E "NOT mounted|NOT installed|S973:|File \".*/(asset_register|claude_reader)\.py\"" | head -3)
[ -z "$abad" ] || restore "the scan app's log after the restart: $(echo "$abad" | head -1 | cut -c1-120)"
say "[5/7] eight files placed and read back; $FSVC + $ASVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), healthz $c1 / $c2, the doors answer, the modules load, the reader knows the kind, both logs clean"
MK=$(fin -c "
import sqlite3,sys,datetime as dt; sys.path.insert(0,'.'); import voucher_scan as VS
c=sqlite3.connect('$LIVE_DB', timeout=30); VS.ensure(c)
d=dt.datetime.now(dt.timezone(dt.timedelta(hours=5,minutes=30))).date()
c.execute(\"INSERT OR IGNORE INTO setting (key,value,note) VALUES ('stock.scan_ask_from',?,'S973: the install day -- no older voucher reaches Amir')\", (d.isoformat(),)); c.commit()
print('S973 table ok, cut-name date', VS.setting(c,'stock.scan_ask_from'), 'switch', 'on' if VS.on(c) else 'off')" | tail -1)
case "$MK" in "S973 table ok"*) ;; *) restore "the table could not be made ($(echo "$MK" | cut -c1-120))";; esac
RD=$(fin -c "
import sqlite3,sys; sys.path.insert(0,'.'); import voucher_scan as VS, voucher_inquiry as VI
c=sqlite3.connect('file:$LIVE_DB?mode=ro', uri=True); S=VS.scans(); cv=VI.claims_view(c)
print('S973 on the live database: stock voucher scans', None if S is None else len(S), '| print asks', len(VS.view(c)), '| claims shown', len(cv), '| reception lines', len(VS.reception_lines(c)))" | tail -1)
case "$RD" in "S973 on the live database: stock voucher scans "[0-9]*) ;; *) restore "the live read ($(echo "$RD" | cut -c1-140))";; esac
[ "${REHEARSE_RED_AT:-}" = 6 ] && restore "rehearsal: a forced red at [6/7]"
PLACING=0
say "[6/7] $MK"
say "[7/7] $RD"
say "    Backups: $ROOT/finance/*.bak_S973_* . $ROOT/assetapp/*.bak_S973_*  ·  The switches: stock.voucher_scan (the Stock check page) . read.stock_voucher (the scan app's settings)"
release_lock
say "    undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s973.sh"
say ""
say "$KIT: DONE."
exit 0
