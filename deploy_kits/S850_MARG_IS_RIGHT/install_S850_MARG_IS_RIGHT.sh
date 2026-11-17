#!/bin/bash
# =============================================================================
#  install_S850_MARG_IS_RIGHT.sh · kit S850 (17-Nov-2026, Sanjeevni session 476; D993 b-d, D995; F-1440) · the owner's "ok" 11:38 IST on
#  mock-up v2 (tabs 3 and 4): on "Scan reading against Marg" a scan line differing from Marg's is Marg-accepted by itself when the bill's
#  totals agree, else one tap "Marg is right"; every accepted line kept as a correction (a monthly table by kind, for the Scan App's reader);
#  the Item ledger's purchase rows carry the verdict; a scan whose read number and total match a Marg bill names it (F-1440).
#   NEW /root/finance/marg_right.py · whole files (make_s850.py on exact anchors from the FROM bytes): scan_ask.py · purchase_app.py · item_ledger.py
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s850kit && cp -rp /root/deploy/repo/deploy_kits/S850_MARG_IS_RIGHT /tmp/s850kit && bash /tmp/s850kit/install_S850_MARG_IS_RIGHT.sh
#  (DRY=1 before bash: every gate and walk; NOTHING written.)
# =============================================================================
set -u
KIT="S850_MARG_IS_RIGHT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"; ADB="${ADB:-$ROOT/assetapp/assets.db}"; SPDB="${SPDB:-$ROOT/finance/spine/spine.db}"
KD="${KD:-/root/deploy/repo/deploy_kits}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
FILES="scan_ask.py purchase_app.py item_ledger.py"
NEWF="marg_right.py"
declare -A FROM=([scan_ask.py]=41adf66bceb6e7ef31f25181c8a2da71 [purchase_app.py]=b789e3791684743969bbf1d25e1b3f92 [item_ledger.py]=49768145965c2bbd81bdf56ab5ca9f74)
to() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s850_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
phz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/purchase/page/sarvam; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/purchase/page/sarvam"; fi; }
jnl() { if [ -n "${JOURNAL_CMD:-}" ]; then $JOURNAL_CMD; elif command -v journalctl >/dev/null 2>&1; then journalctl -u "$FSVC" --since "@$1" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for f in $FILES $NEWF; do rm -f "$ROOT/finance/.$f.s850"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting every file back"
  for f in $FILES; do \cp -p "$ROOT/finance/$f.bak_S850_${FROM[$f]:0:8}" "$ROOT/finance/$f"; done
  [ -f "$ROOT/finance/$NEWF" ] && mv -f "$ROOT/finance/$NEWF" "$ROOT/finance/$NEWF.withdrawn_S850_$STAMP"
  "$SYSTEMCTL" restart "$FSVC" || true
  for f in $FILES; do say "   $f $(m5 "$ROOT/finance/$f" | cut -c1-8) (expected ${FROM[$f]:0:8})"; done
  say "   $NEWF withdrawn; $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
lay() { local d="$SCR/root_$1"; rm -rf "$d"; mkdir -p "$d/finance/finance_ui" "$d/finance/spine" \
  && find "$ROOT/finance" -maxdepth 1 -type f \( -name '*.py' -o -name '*.html' -o -name '*.sql' -o -name '*.json' \) -exec cp -p {} "$d/finance/" \; \
  && \cp -p "$ROOT"/finance/finance_ui/*.html "$d/finance/finance_ui/" 2>/dev/null; \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$d/finance/spine/" 2>/dev/null; \
  [ -f "$d/finance/purchase_app.py" ]; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPATH="$ROOT/shared${PYTHONPATH:+:$PYTHONPATH}" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
CPDB='import sqlite3,sys;s=sqlite3.connect("file:%s?mode=ro"%sys.argv[1],uri=True,timeout=60);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close();s.close();print("copied")'

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $FILES $NEWF; do t=$(to "$f"); [ -n "$t" ] && [ "$(m5 "$KDIR/$f")" = "$t" ] || { say "!! [1/5] the kit's $f is not at its TO pin - nothing installed"; exit 1; }; done
[ -f "$DB" ] && [ -f "$ADB" ] || { say "!! [1/5] $DB or $ADB missing - nothing installed"; exit 1; }
WALKS="S781_PROVISIONAL_BILLS/walk_s781.py S761_HUB_NEEDS_GOTO/walk_s761.py S750_MONTH_END/walk_s750.py S753_SUMMARY_SCANS_READ/walk_s753.py S755_SUMMARY_REMINDERS/walk_s755.py S814_MARG_WATCH_ASK/walk_s814.py S845_ITEM_LEDGER/walk_s845.py S849_SCAN_NOT_IN_MARG/synth_s849.py"
for w in $WALKS; do [ -f "$KD/$w" ] || { say "!! [1/5] $KD/$w missing - publish first. Nothing installed."; exit 1; }; done
all_to=1; for f in $FILES $NEWF; do [ "$(m5 "$ROOT/finance/$f")" = "$(to "$f")" ] || all_to=0; done
[ "$all_to" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for f in $FILES; do [ "$(m5 "$ROOT/finance/$f")" = "${FROM[$f]}" ] || stop "!! [2/5] $ROOT/finance/$f is $(m5 "$ROOT/finance/$f" | cut -c1-8), expected ${FROM[$f]:0:8} - STOP, nothing installed. Tell Claude."; done
[ -e "$ROOT/finance/$NEWF" ] && stop "!! [2/5] $ROOT/finance/$NEWF already exists (not this kit's) - STOP, nothing installed. Tell Claude."
for f in $FILES $NEWF; do for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/$f" || stop "!! [2/5] $f does not compile on $p - nothing installed"; done; done
say "[2/5] the three live files are at their FROM pins; the four new ones compile on both pythons"
"$VPY" -c "$CPDB" "$DB" "$SCR/finance.db" >/dev/null && "$VPY" -c "$CPDB" "$ADB" "$SCR/assets.db" >/dev/null || stop "!! [3/5] could not copy the databases for the walk - nothing installed"
HAVE_SPINE=0; [ -f "$SPDB" ] && "$VPY" -c "$CPDB" "$SPDB" "$SCR/spine.db" >/dev/null && HAVE_SPINE=1
{ lay old && lay new; } || stop "!! [3/5] could not lay out the walk - nothing installed"
for f in $FILES $NEWF; do \cp -p "$KDIR/$f" "$SCR/root_new/finance/$f" || stop "!! [3/5] could not lay out the walk ($f) - nothing installed"; done
R1=$(py "$KDIR/synth_s850.py" "$SCR/root_new/finance" "$SCR/finance.db" --real "$SCR/assets.db" | tail -1)
case "$R1" in "SYNTH S850: "*" PASS, 0 FAIL") ;; *) stop "!! [3/5] synth_s850 on the new files (copies of the live databases): $R1 - nothing installed. Tell Claude.";; esac
\cp -p "$KDIR/$NEWF" "$SCR/root_old/finance/$NEWF"                      # the control: the live files + the new module -> the seams and F-1440 red
R0=$(py "$KDIR/synth_s850.py" "$SCR/root_old/finance" "$SCR/finance.db" | tail -1)
rm -f "$SCR/root_old/finance/$NEWF"
case "$R0" in "SYNTH S850: "*" PASS, 0 FAIL") stop "!! [3/5] the control on the live files did not go red ($R0) - nothing installed";; esac
same() { [ "$2" = "$3" ] || stop "!! [3/5] $1 differs on the new files: live '$2' / new '$3' - nothing installed. Tell Claude."; }
a=$(py "$KD/S781_PROVISIONAL_BILLS/walk_s781.py" "$SCR/root_old/finance" "$ROOT/shared" "$SCR/root_old/finance" "$SCR/finance.db" | tail -1)
b=$(py "$KD/S781_PROVISIONAL_BILLS/walk_s781.py" "$SCR/root_new/finance" "$ROOT/shared" "$SCR/root_new/finance" "$SCR/finance.db" | tail -1); same walk_s781 "$a" "$b"
for side in old new; do cp "$SCR/finance.db" "$SCR/w761_$side.db"; mkdir -p "$SCR/scr761_$side"; done
a=$(py "$KD/S761_HUB_NEEDS_GOTO/walk_s761.py" --root "$SCR/root_old" --db "$SCR/w761_old.db" --scratch "$SCR/scr761_old" --page "$SCR/root_old/finance/finance_ui/finance_approvals.html" | tail -1)
b=$(py "$KD/S761_HUB_NEEDS_GOTO/walk_s761.py" --root "$SCR/root_new" --db "$SCR/w761_new.db" --scratch "$SCR/scr761_new" --page "$SCR/root_new/finance/finance_ui/finance_approvals.html" | tail -1); same walk_s761 "$a" "$b"
for w in S750_MONTH_END/walk_s750.py S753_SUMMARY_SCANS_READ/walk_s753.py S755_SUMMARY_REMINDERS/walk_s755.py; do
  a=$(py "$KD/$w" "$SCR/root_old/finance" "$ROOT/finance/purchase_schema.sql" "$ROOT/shared" | tail -1)
  b=$(py "$KD/$w" "$SCR/root_new/finance" "$ROOT/finance/purchase_schema.sql" "$ROOT/shared" | tail -1); same "$(basename "$w")" "$a" "$b"; done
a=$(py "$KD/S849_SCAN_NOT_IN_MARG/synth_s849.py" "$SCR/root_old/finance" "$SCR/finance.db" | tail -1)
b=$(py "$KD/S849_SCAN_NOT_IN_MARG/synth_s849.py" "$SCR/root_new/finance" "$SCR/finance.db" | tail -1); same synth_s849 "$a" "$b"
if [ "$HAVE_SPINE" = 1 ]; then
  a=$(SPINE_DB="$SCR/spine.db" py "$KD/S814_MARG_WATCH_ASK/walk_s814.py" "$SCR/root_old/finance" "$SCR/spine.db" "$SCR/finance.db" | tail -1)
  b=$(SPINE_DB="$SCR/spine.db" py "$KD/S814_MARG_WATCH_ASK/walk_s814.py" "$SCR/root_new/finance" "$SCR/spine.db" "$SCR/finance.db" | tail -1); same walk_s814 "$a" "$b"
  a=$(SPINE_DB="$SCR/spine.db" py "$KD/S845_ITEM_LEDGER/walk_s845.py" "$SCR/root_old/finance" "$SCR/finance.db" --box | tail -1)
  b=$(SPINE_DB="$SCR/spine.db" py "$KD/S845_ITEM_LEDGER/walk_s845.py" "$SCR/root_new/finance" "$SCR/finance.db" --box | tail -1); same walk_s845 "$a" "$b"
  W2="walks s781/s761/s750/s753/s755, synth_s849, s814/s845 the same on old and new"
else W2="walks s781/s761/s750/s753/s755, synth_s849 the same on old and new (no spine copy: s814/s845 not run)"; fi
say "[3/5] $R1 (copies of the live databases: October's lines judged, its corrections kept); the control on the live files: red; $W2"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and walk green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for f in $FILES; do B="$ROOT/finance/$f.bak_S850_${FROM[$f]:0:8}"; { \cp -p "$ROOT/finance/$f" "$B" && [ "$(m5 "$B")" = "${FROM[$f]}" ]; } || stop "!! [4/5] could not write the backup of $f - nothing placed"; done
for f in $FILES $NEWF; do STG="$ROOT/finance/.$f.s850"; { cat "$KDIR/$f" > "$STG" && chmod --reference="$ROOT/finance/purchase_app.py" "$STG" 2>/dev/null; chown --reference="$ROOT/finance/purchase_app.py" "$STG" 2>/dev/null; [ "$(m5 "$STG")" = "$(to "$f")" ]; } || stop "!! [4/5] could not stage $f - nothing placed"; done
PLACING=1; T0=$(date +%s)
for f in $NEWF $FILES; do mv -f "$ROOT/finance/.$f.s850" "$ROOT/finance/$f" || restore "the rename of $f"; [ "$(m5 "$ROOT/finance/$f")" = "$(to "$f")" ] || restore "read back $f"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
s1=$(phz); case "$s1" in 404|000|5*) restore "the Scan reading page answered $s1 after the restart";; esac   # 302/401 = behind the login gate (as S849)
jnl "$T0" | grep -q "S850 cards failed\|S850 ledger verdicts failed\|marg_right sync failed\|marg_right ledger verdict failed" && restore "the service log says an S850 part failed"
PLACING=0
release_lock
say "[4/5] four files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the Scan reading page answers ($s1)"
say "[5/5] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s850.sh"
say ""
say "$KIT: DONE. Marg is now taken over a misread scan line when the totals agree; one tap 'Marg is right' otherwise."
exit 0
