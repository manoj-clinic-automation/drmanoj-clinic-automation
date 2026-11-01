#!/bin/bash
# =============================================================================
#  install_S693_STOCK_ON_BATCH.sh · kit S693 (01-Nov-2026, Sanjeevni session 375) · new stock placed on its batch from the purchase item
#  report, so a counter sale into a minus batch is caught the next morning for every medicine, re-bought ones included (plan section 9, step 0).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s693kit && cp -rp /root/deploy/repo/deploy_kits/S693_STOCK_ON_BATCH /tmp/s693kit && bash /tmp/s693kit/install_S693_STOCK_ON_BATCH.sh
#  (DRY=1 before bash: every gate, the walk, the control and both proofs on copies -- nothing written.)
#   /root/finance/expiry_watch.py   b68cda86 -> TO   _s693_place / _s693_tie / _s693_sale_tie; the wrong-batch rule for a placed re-supply
#  THE GATE THAT DECIDES: on this box, on COPIES of the database and the spine and the live archive (read only), the OLD and the NEW watch
#  run once each -- every difference explained (a bought medicine's minus named against its sales or Marg's printed minus; stock up by a
#  purchase; a new batch) -- twice: on the live archive and on the archive without its newest report (so purchases since a report exist).
#  Data step: the watch run once after placing. Restarts clinic-finance (Amir's card imports the watch). Red after placing: the file back.
# =============================================================================
set -u
KIT="S693_STOCK_ON_BATCH"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
SPINE="${SPINE:-$ROOT/finance/spine/spine.db}"
ARCHIVE="${ARCHIVE:-$ROOT/marg_ingest/archive}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F="finance/expiry_watch.py"
FROM="b68cda86162768661226065192286336"
TO="$(awk -v f="$F" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s693_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
GREEN="22 of 22 green"
CONTROL="13 S693 check(s) red . 7 green"
BAK="$ROOT/$F.bak_S693_${FROM:0:8}"
STG="$ROOT/finance/.expiry_watch.py.s693"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
fhealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { rm -f "$STG"; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -B "$KDIR/walk_s693.py" "$@" 2>&1); }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting expiry_watch.py back"
  PLACED=2
  \cp -p "$BAK" "$ROOT/$F" || say "   !! could not put back $ROOT/$F"; rm -f "$STG"
  "$SYSTEMCTL" restart "$FSVC" || true
  say "   $ROOT/$F $(m5 "$ROOT/$F" | cut -c1-8) (expected ${FROM:0:8})"
  say "   finance healthz $(wait200 fhz). Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/8] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$TO" ] || { say "!! [1/8] TO_PINS.md5 does not name $F - nothing installed"; exit 1; }
[ -f "$ROOT/$F" ] && [ -f "$DB" ] && [ -f "$SPINE" ] && [ -d "$ARCHIVE/BATCH_STOCK" ] || { say "!! [1/8] $ROOT/$F, $DB, $SPINE or $ARCHIVE/BATCH_STOCK is missing - nothing installed"; exit 1; }
[ "$(m5 "$ROOT/$F")" = "$TO" ] && { say "-- ALREADY INSTALLED: expiry_watch.py is the kit's. Nothing written. finance healthz $(fhz)"; exit 0; }
for off in "$ROOT/finance/spine/OFF" "$ROOT/finance/_off/ALL_OFF"; do [ -e "$off" ] && { say "!! [1/8] the switch $off is set: the watch would not run after placing - nothing installed"; exit 1; }; done
if [ "${DRY:-0}" = 1 ]; then
  say "[1/8] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/8] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  TOOK_LOCK=1; say "[1/8] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."
  exit 3
fi
C=$(m5 "$ROOT/$F"); [ "$C" = "$FROM" ] || stop_unlocked "!! [2/8] $ROOT/$F is ${C:0:8}, expected ${FROM:0:8} - it changed after this kit was built: STOP, nothing installed"
say "[2/8] live pin exact: expiry_watch.py at its FROM ${FROM:0:8}"

mkdir -p "$SCR/built/finance" "$SCR/pyc" && chmod 700 "$SCR" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s693.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/8] the builder refused the live file - nothing installed"; }
[ "$(m5 "$SCR/built/$F")" = "$TO" ] || stop_unlocked "!! [3/8] rebuilt, expiry_watch.py is $(m5 "$SCR/built/$F" | cut -c1-8), not ${TO:0:8} - nothing installed"
for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$F" || stop_unlocked "!! [3/8] expiry_watch.py does not compile on $py - nothing installed"; done
# the rebuilt file's root: the live neighbours (read only) beside the kit's file
mkdir -p "$SCR/newroot/finance/spine" && for f in "$ROOT"/finance/*.py; do ln -s "$f" "$SCR/newroot/finance/$(basename "$f")"; done
for f in "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json; do ln -s "$f" "$SCR/newroot/finance/spine/$(basename "$f")"; done
rm -f "$SCR/newroot/$F" && cp -p "$SCR/built/$F" "$SCR/newroot/$F"
say "[3/8] rebuilt here from this box's live bytes: at its TO pin ${TO:0:8}; compiles under both pythons"

R=$(walk --new "$SCR/newroot" --scratch "$SCR/w1" | tail -1)
[ "$R" = "$GREEN" ] || { walk --new "$SCR/newroot" --scratch "$SCR/w1b" | grep -E 'RED' | head -12 | sed 's/^/         /'; PLACED=2; stop_unlocked "!! [4/8] the walk on the rebuilt file is not green ($R) - nothing installed (kept in $SCR)"; }
R0=$(walk --old "$ROOT" --scratch "$SCR/w0" | tail -1)
[ "$R0" = "$CONTROL" ] || { PLACED=2; stop_unlocked "!! [4/8] the control on the live file is not as expected ($R0) - nothing installed (kept in $SCR)"; }
copydb "$DB" "$SCR/walk.db" || stop_unlocked "!! [4/8] no copy of the database - nothing installed"
copydb "$SPINE" "$SCR/spine.db" || stop_unlocked "!! [4/8] no copy of the spine - nothing installed"
P1=$(walk --proof --old-root "$ROOT" --new "$SCR/newroot" --db "$SCR/walk.db" --spine "$SCR/spine.db" --archive "$ARCHIVE" --scratch "$SCR/wp1")
echo "$P1" | grep -E '^  --  |RED' | head -30 | sed 's/^/         /'
PL1="$(echo "$P1" | tail -1)"
case "$PL1" in "proof: old "*" . CLEAN . "*) ;; *) PLACED=2; stop_unlocked "!! [4/8] the proof on the live archive is not clean ($PL1) - nothing installed (kept in $SCR)";; esac
# the second proof: the archive WITHOUT the report the first proof read (not merely the newest capture), so purchases since a report exist
MD8="$(echo "$PL1" | sed -n 's/.* \. report \([0-9a-f]\{8\}\) \. .*/\1/p')"
[ -n "$MD8" ] && [ "$MD8" != "none" ] || { PLACED=2; stop_unlocked "!! [4/8] the first proof read no whole-shop report ($PL1) - nothing installed (kept in $SCR)"; }
mkdir -p "$SCR/arch2/BATCH_STOCK"; DROPPED=0
for d in "$ARCHIVE"/BATCH_STOCK/*/; do [ -d "$d" ] || continue; mkdir -p "$SCR/arch2/BATCH_STOCK/$(basename "$d")"; for f in "$d"*; do [ -f "$f" ] || continue; case "$(basename "$f")" in *"__${MD8}"*) DROPPED=$((DROPPED+1)); continue;; esac; ln -s "$f" "$SCR/arch2/BATCH_STOCK/$(basename "$d")/$(basename "$f")"; done; done
[ "$DROPPED" = 1 ] || { PLACED=2; stop_unlocked "!! [4/8] the report $MD8 the first proof read is not one file in the archive ($DROPPED) - nothing installed (kept in $SCR)"; }
P2=$(walk --proof --old-root "$ROOT" --new "$SCR/newroot" --db "$SCR/walk.db" --spine "$SCR/spine.db" --archive "$SCR/arch2" --scratch "$SCR/wp2")
echo "$P2" | grep -E '^  --  |RED' | head -40 | sed 's/^/         /'
PL2="$(echo "$P2" | tail -1)"
case "$PL2" in "proof: old "*" . CLEAN . "*) ;; *) PLACED=2; stop_unlocked "!! [4/8] the proof on the archive without the report is not clean ($PL2) - nothing installed (kept in $SCR)";; esac
NPL="$(echo "$PL2" | sed -n 's/.* \. \([0-9]\+\) purchase line(s) since .*/\1/p')"
[ "${NPL:-0}" -ge 1 ] || { PLACED=2; stop_unlocked "!! [4/8] the second proof placed no purchase line (${NPL:-?}) - it proved nothing; nothing installed (kept in $SCR)"; }
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/8] finance healthz $f0 before the install - nothing installed"
say "[4/8] the walk: $GREEN; the control on the live file: $R0; proof on the live archive: $PL1; proof without the report $MD8: $PL2; finance healthy ($f0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk, the control and both proofs green; NOTHING written"; exit 0; fi

{ \cp -p "$ROOT/$F" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop_unlocked "!! [5/8] could not write the backup $BAK - nothing placed"
{ cat "$SCR/built/$F" > "$STG" && [ "$(m5 "$STG")" = "$TO" ]; } || { rm -f "$STG"; stop_unlocked "!! [5/8] could not stage expiry_watch.py - nothing placed"; }
chmod --reference="$ROOT/$F" "$STG" 2>/dev/null; chown --reference="$ROOT/$F" "$STG" 2>/dev/null
PLACED=1
mv -f "$STG" "$ROOT/$F" || restore "the rename"
[ "$(m5 "$ROOT/$F")" = "$TO" ] || restore "read back"
find "$ROOT/finance" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[5/8] placed and read back: expiry_watch.py at ${TO:0:8} (backup $BAK)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(fhealth /finance/amir/step/3); case "$c2" in 302|401|303|403) ;; *) restore "Amir's step 3 answered $c2 without a login";; esac
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JR="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[6/8] $FSVC restarted at $T0: healthz $c1; Amir's step 3 $c2 without a login (the login gate, expected); journal clean"
R=$(walk --new "$ROOT" --scratch "$SCR/w2" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 8 ] && R="rehearsal: a forced red at [8/8]"      # the rehearsal's hook only; unset on a real install
[ "$R" = "$GREEN" ] || restore "the walk on the placed file: $R"
say "[7/8] the walk on the placed file: $R"
(cd "$ROOT/finance" && timeout 600 "$VPY" -B expiry_watch.py run --db "$DB" --spine "$SPINE" --archive "$ARCHIVE" > "$SCR/run.txt" 2>&1); RC=$?
[ "$RC" = 0 ] && grep -q "expiry_watch .* run " "$SCR/run.txt" || { cat "$SCR/run.txt" | tail -3; restore "the watch's run after placing returned $RC (its rows, if any, stay; the next run rewrites them)"; }
say "[8/8] the watch run once on the placed file: $(tail -1 "$SCR/run.txt" | cut -c1-200)"
release_lock
say "      the build lock released"
say "undo (one line): \\cp -p $BAK $ROOT/$F && $SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. New stock is placed on its batch from the purchase report; a minus batch is caught for every medicine."
exit 0
