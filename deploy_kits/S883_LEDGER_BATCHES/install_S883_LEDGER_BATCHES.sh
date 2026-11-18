#!/bin/bash
# =============================================================================
#  install_S883_LEDGER_BATCHES.sh · kit S883 (18-Nov-2026, Sanjeevni session 485) · the owner 19:22-19:45 IST, "ok" on mock-up v3
#  (https://claude.ai/artifact/37R4Qw5Bv2Y76emRyMTggz): the Item ledger shows each item's BATCHES with expiry (where each came in; whether
#  they add up to Marg), each sale and purchase line carries its batch and expiry, the ledger is folded by month with quiet days as one line,
#  and the period's totals are in words with its purchase bills opening from them. Read only, as S845/S847/S850.
#   /root/finance/expiry_watch.py 1ed95b6c -> TO  (each run also keeps every batch it worked out in a NEW table stock_batch_now, in its own
#                                                  transaction after the lists; the lists and Amir's fix cards are byte-for-byte as before)
#   /root/finance/item_ledger.py  b4040d8f -> TO  (the page; whole file, this project's own)
#  After the placing it runs the Expiry watch once (exactly what the 23:57 nightly runs) so the Batches box has its rows today.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s883kit && cp -rp /root/deploy/repo/deploy_kits/S883_LEDGER_BATCHES /tmp/s883kit && bash /tmp/s883kit/install_S883_LEDGER_BATCHES.sh
#  (DRY=1 before bash: every gate and walk; NOTHING written.)
# =============================================================================
set -u
KIT="S883_LEDGER_BATCHES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"; SPDB="${SPDB:-$ROOT/finance/spine/spine.db}"
ARCH="${ARCH:-$ROOT/marg_ingest/archive}"
KITS="${KITS:-/root/deploy/repo/deploy_kits}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
SAMPLE="${SAMPLE:-300}"
N1="finance/expiry_watch.py"; F1="1ed95b6cda37af1b1a279129119fae4a"
N2="finance/item_ledger.py";  F2="b4040d8fc2d09719b27747c9f6a51d26"
T1="$(awk -v f="$N1" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; T2="$(awk -v f="$N2" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s883_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
B1="$ROOT/$N1.bak_S883_${F1:0:8}"; B2="$ROOT/$N2.bak_S883_${F2:0:8}"
S1="$ROOT/finance/.expiry_watch.py.s883"; S2="$ROOT/finance/.item_ledger.py.s883"
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
flz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/sanjeevni/ledger/api/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/sanjeevni/ledger/api/healthz"; fi; }
jnl() { if [ -n "${JOURNAL_CMD:-}" ]; then $JOURNAL_CMD; elif command -v journalctl >/dev/null 2>&1; then journalctl -u "$FSVC" --since "@$1" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$S1" "$S2"; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting both files back"
  \cp -p "$B1" "$ROOT/$N1"; \cp -p "$B2" "$ROOT/$N2"; "$SYSTEMCTL" restart "$FSVC" || true
  say "   $N1 $(m5 "$ROOT/$N1" | cut -c1-8) (expected ${F1:0:8}); $N2 $(m5 "$ROOT/$N2" | cut -c1-8) (expected ${F2:0:8}); $FSVC restarted, finance healthz $(wait200)."
  say "   (the table stock_batch_now, if made, stays: nothing reads it without the new page.) Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
lay() { local d="$SCR/root_$1"; rm -rf "$d"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" \
  && find "$ROOT/finance" -maxdepth 1 -type f \( -name '*.py' -o -name '*.html' -o -name '*.sql' -o -name '*.json' \) -exec cp -p {} "$d/finance/" \; \
  && \cp -p "$ROOT"/finance/finance_ui/*.html "$d/finance/finance_ui/" 2>/dev/null; \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$d/finance/spine/" 2>/dev/null; \
  [ -f "$d/finance/item_ledger.py" ] && [ -f "$d/finance/expiry_watch.py" ] && [ -f "$d/finance/spine/spine_read.py" ]; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPATH="$ROOT/shared${PYTHONPATH:+:$PYTHONPATH}" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 1500 "$VPY" -u -W ignore -B "$@" 2>&1); }
fails() { echo "$1" | sed -n 's/.* \([0-9][0-9]*\) FAIL.*/\1/p; s/.*, \([0-9][0-9]*\) red.*/\1/p' | head -1; }
CPDB='import sqlite3,sys;s=sqlite3.connect("file:%s?mode=ro"%sys.argv[1],uri=True,timeout=60);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close();s.close();print("copied")'

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$T1" ] && [ "$(m5 "$KDIR/expiry_watch.py")" = "$T1" ] && [ -n "$T2" ] && [ "$(m5 "$KDIR/item_ledger.py")" = "$T2" ] || { say "!! [1/5] the kit's files are not at their TO pins - nothing installed"; exit 1; }
[ -f "$DB" ] && [ -f "$SPDB" ] && [ -d "$ARCH" ] || { say "!! [1/5] $DB, $SPDB or $ARCH missing - nothing installed"; exit 1; }
for k in S845_ITEM_LEDGER S847_LEDGER_ARRIVED S850_MARG_IS_RIGHT; do [ -d "$KITS/$k" ] || { say "!! [1/5] $KITS/$k is not there - publish first. Nothing installed."; exit 1; }; done
if [ "$(m5 "$ROOT/$N1")" = "$T1" ] && [ "$(m5 "$ROOT/$N2")" = "$T2" ]; then say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; fi
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$ROOT/$N1")" = "$F1" ] || stop "!! [2/5] $ROOT/$N1 is $(m5 "$ROOT/$N1" | cut -c1-8), expected ${F1:0:8} - STOP, nothing installed. Tell Claude."
[ "$(m5 "$ROOT/$N2")" = "$F2" ] || stop "!! [2/5] $ROOT/$N2 is $(m5 "$ROOT/$N2" | cut -c1-8), expected ${F2:0:8} - STOP, nothing installed. Tell Claude."
for p in "$APY" "$VPY"; do for f in expiry_watch.py item_ledger.py; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/$f" || stop "!! [2/5] $f does not compile on $p - nothing installed"; done; done
say "[2/5] the live files are at their FROM pins (${F1:0:8}, ${F2:0:8}); the new ones compile on both pythons"
"$VPY" -c "$CPDB" "$DB" "$SCR/finance.db" >/dev/null && "$VPY" -c "$CPDB" "$SPDB" "$SCR/spine.db" >/dev/null || stop "!! [3/5] could not copy the databases for the walk - nothing installed"
lay new && \cp -p "$KDIR/expiry_watch.py" "$SCR/root_new/$N1" && \cp -p "$KDIR/item_ledger.py" "$SCR/root_new/$N2" || stop "!! [3/5] could not lay out the walk - nothing installed"
lay old || stop "!! [3/5] could not lay out the control - nothing installed"
R1=$(SPINE_DB="$SCR/spine.db" py "$KDIR/synth_s883.py" --code "$SCR/root_new/finance" --old "$SCR/root_old/finance" --finance "$SCR/finance.db" --spine "$SCR/spine.db" --archive "$ARCH" --sample "$SAMPLE" | tail -1)
case "$R1" in "synth_s883: "*" ok, 0 red") ;; *) stop "!! [3/5] synth_s883 on copies of the live databases: $R1 - nothing installed";; esac
R0=$(SPINE_DB="$SCR/spine.db" py "$KDIR/synth_s883.py" --code "$SCR/root_old/finance" --finance "$SCR/finance.db" --spine "$SCR/spine.db" --archive "$ARCH" --sample 5 --control | tail -1)
case "$R0" in "synth_s883: "*" ok, 0 red") stop "!! [3/5] the control on the live files did not go red ($R0) - nothing installed";; esac
# the earlier proofs of the page: on the live files and on the new ones; the new must do no worse (the S837 rule -- frozen data outgrown by his taps is not a fault of this kit)
worse=""
for w in "S845_ITEM_LEDGER/walk_s845.py|%s|$SCR/finance.db|--box" "S845_ITEM_LEDGER/synth_s845.py|%s" "S847_LEDGER_ARRIVED/synth_s847.py|%s|$KITS/S845_ITEM_LEDGER" "S850_MARG_IS_RIGHT/synth_s850.py|%s|COPYDB"; do
  IFS='|' read -r f a1 a2 a3 <<< "$w"; res=""
  for side in old new; do
    a1v="$SCR/root_$side/finance"; a2v="$a2"; [ "$a2" = COPYDB ] && { cp "$SCR/finance.db" "$SCR/f850_$side.db"; a2v="$SCR/f850_$side.db"; }
    r=$(SPINE_DB="$SCR/spine.db" py "$KITS/$f" "$a1v" ${a2v:+"$a2v"} ${a3:+"$a3"} | tail -1); res="$res $side:[$r]"
    eval "x_$side=\$(fails \"\$r\")"
  done
  [ -n "$x_new" ] || x_new=999; [ -n "$x_old" ] || x_old=999
  [ "$x_new" -le "$x_old" ] || worse="$worse $f($res)"
  say "      $(basename "$f"):$res"
done
[ -z "$worse" ] || stop "!! [3/5] the new files do worse than the live ones on:$worse - nothing installed"
say "[3/5] $R1 (copies of the live databases); the earlier proofs no worse; the control on the live files: red"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and walk green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
{ \cp -p "$ROOT/$N1" "$B1" && [ "$(m5 "$B1")" = "$F1" ] && \cp -p "$ROOT/$N2" "$B2" && [ "$(m5 "$B2")" = "$F2" ]; } || stop "!! [4/5] could not write the backups - nothing placed"
{ cat "$KDIR/expiry_watch.py" > "$S1" && chmod --reference="$ROOT/$N1" "$S1" 2>/dev/null; chown --reference="$ROOT/$N1" "$S1" 2>/dev/null; [ "$(m5 "$S1")" = "$T1" ]; } || stop "!! [4/5] could not stage expiry_watch.py - nothing placed"
{ cat "$KDIR/item_ledger.py" > "$S2" && chmod --reference="$ROOT/$N2" "$S2" 2>/dev/null; chown --reference="$ROOT/$N2" "$S2" 2>/dev/null; [ "$(m5 "$S2")" = "$T2" ]; } || stop "!! [4/5] could not stage item_ledger.py - nothing placed"
PLACING=1; T0=$(date +%s)
mv -f "$S1" "$ROOT/$N1" || restore "the rename of expiry_watch.py"
mv -f "$S2" "$ROOT/$N2" || restore "the rename of item_ledger.py"
[ "$(m5 "$ROOT/$N1")" = "$T1" ] && [ "$(m5 "$ROOT/$N2")" = "$T2" ] || restore "read back"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
l1=$(flz); case "$l1" in 404|000|5*) restore "the ledger answered $l1 after the restart (not mounted)";; esac
jnl "$T0" | grep -q "item_ledger NOT mounted" && restore "the Hub's log says the ledger was NOT mounted"
# the Expiry watch once, exactly as the nightly runs it -- the run must finish as it always does; the batch rows are its new part
ER=$(cd "$ROOT/finance/spine" && timeout 600 "$VPY" -B near_expiry.py 2>&1 | tail -3)
if echo "$ER" | grep -q "expiry_watch: switched off"; then say "      the Expiry watch is switched off ($(echo "$ER" | tail -1)) - the Batches box fills at its next run"
else echo "$ER" | grep -q "expiry_watch S693_STOCK_ON_BATCH: run " || restore "the Expiry watch run did not finish as it does every night: $(echo "$ER" | tail -1)"; fi
NB=$("$VPY" -c 'import sqlite3,sys;c=sqlite3.connect("file:%s?mode=ro"%sys.argv[1],uri=True);print(c.execute("SELECT COUNT(*) FROM stock_batch_now").fetchone()[0])' "$DB" 2>/dev/null)
PLACING=0
release_lock
say "[4/5] placed and read back (${T1:0:8}, ${T2:0:8}); $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the ledger answers ($l1)"
say "      the Expiry watch ran once: $(echo "$ER" | grep -o 'S883_LEDGER_BATCHES: [0-9]* batch row(s) kept' | head -1 || true) -- stock_batch_now holds ${NB:-?} rows"
say "[5/5] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s883.sh  (both files back, $FSVC restarted)"
say ""
say "$KIT: DONE. The Item ledger now shows each item's batches with expiry, the batch on every line, folded by month."
exit 0
