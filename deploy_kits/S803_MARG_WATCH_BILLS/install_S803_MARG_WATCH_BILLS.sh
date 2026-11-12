#!/bin/bash
# =============================================================================
#  install_S803_MARG_WATCH_BILLS.sh · kit S803 (12-Nov-2026, Sanjeevni session 438) · the owner's "Go" 17:49 IST
#  The Marg watch, Kit 1: bills changed after their day (removed, added late, altered in Marg after the day's report was taken).
#  READ ONLY on Marg and on every table that exists; its own page, its own two tables.
#   /root/finance/marg_billwatch.py       NEW              the compare, the owner's page /finance/sanjeevni/marg-watch, his closes
#   /root/finance/sanjeevni_approvals.py  569c5ee4 -> TO   init() also mounts marg_billwatch (these pages keep working if it cannot)
#   /root/finance/owner_notice.py         537b7c32 -> TO   one part added: a NEW changed bill is told once (history never) -- OFF until he turns it on, on the page
#   /root/finance/finance_ui/finance_approvals.html  6a4178ea -> TO   the Sanjeevni Hub's "Go to": one link added, to the Marg watch
#   finance.db: the history fill -- everything found so far is noted as 'Before this page' (tables billwatch_seen, billwatch_act;
#               settings billchange.since / .on / .sig). Nothing else is written.           clinic-finance is restarted.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s803kit && cp -rp /root/deploy/repo/deploy_kits/S803_MARG_WATCH_BILLS /tmp/s803kit && bash /tmp/s803kit/install_S803_MARG_WATCH_BILLS.sh
#  (DRY=1 before bash: every gate, the walk, its control and the proof on this box's data, printed; NOTHING written.)
# =============================================================================
set -u
KIT="S803_MARG_WATCH_BILLS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
OLDF="finance/sanjeevni_approvals.py finance/owner_notice.py finance/finance_ui/finance_approvals.html"
NEWF="finance/marg_billwatch.py"
FILES="$OLDF $NEWF"
declare -A FROM=( [finance/sanjeevni_approvals.py]=569c5ee4caa2692708be82c7967d2813 [finance/owner_notice.py]=537b7c321116304baff676cec8e98fb0 [finance/finance_ui/finance_approvals.html]=6a4178ea61d46c5df99a1af5d5d45e03 )
declare -A TO
for f in $FILES; do TO[$f]="$(awk -v f="$f" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s803_inst_$STAMP"
PLACED=0; TOOK_LOCK=0

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S803_${FROM[$1]:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s803"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { for f in $FILES; do rm -f "$(stg "$f")"; done; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }
pids_of() { local m; m="$("$SYSTEMCTL" show -p MainPID --value "$1" 2>/dev/null)"; [ -n "$m" ] && [ "$m" != 0 ] && { echo "$m"; pgrep -P "$m" 2>/dev/null; }; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the files back"
  PLACED=2
  for f in $OLDF; do \cp -p "$(bak "$f")" "$ROOT/$f" || say "   !! could not put back $ROOT/$f"; rm -f "$(stg "$f")"; done
  for f in $NEWF; do rm -f "$ROOT/$f" "$(stg "$f")"; done
  find "$ROOT/finance" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  "$SYSTEMCTL" restart "$FSVC" || true
  for f in $OLDF; do say "   $ROOT/$f $(m5 "$ROOT/$f" | cut -c1-8) (expected ${FROM[$f]:0:8})"; done
  for f in $NEWF; do [ -e "$ROOT/$f" ] && say "   !! $ROOT/$f is still there" || say "   $ROOT/$f removed"; done
  say "   finance healthz $(wait200). (If the fill ran, its rows stay in finance.db in the Marg watch's own two tables; nothing reads them.) Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s803.py" "$1" "$ROOT/shared" "$ROOT/finance" "$DB" $2 2>&1); }
proof() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/proof_s803.py" "$1" "$ROOT/shared" "$ROOT/finance" "$SCR/proof.db" ${PROOF_ASSETS:-} 2>&1); }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout pgrep; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
{ [ "$ROOT" != "/root" ] && [ "${SKIP_WINDOW:-0}" = 1 ]; } || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/6] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $FILES; do [ -n "${TO[$f]}" ] || { say "!! [1/6] TO_PINS.md5 does not name $f - nothing installed"; exit 1; }; done
for f in $OLDF; do [ -f "$ROOT/$f" ] || { say "!! [1/6] $ROOT/$f is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/6] $DB is missing - nothing installed"; exit 1; }
mkdir -p "$SCR/built" "$SCR/pyc" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
ALL=1; for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the four files are the kit's. Nothing written. finance healthz $(fhz)"; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/6] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken $(TZ=Asia/Kolkata date '+%d-%m %H:%M IST') by $KIT"
else
  say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."
  exit 3
fi
for f in $OLDF; do C=$(m5 "$ROOT/$f"); [ "$C" = "${FROM[$f]}" ] || stop_unlocked "!! [2/6] $ROOT/$f is ${C:0:8}, expected ${FROM[$f]:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
for f in $NEWF; do [ -e "$ROOT/$f" ] && stop_unlocked "!! [2/6] $ROOT/$f already exists ($(m5 "$ROOT/$f" | cut -c1-8)) - STOP, nothing installed. Tell Claude."; done
say "[2/6] live pins exact: sanjeevni_approvals.py ${FROM[finance/sanjeevni_approvals.py]:0:8} · owner_notice.py ${FROM[finance/owner_notice.py]:0:8} · finance_approvals.html ${FROM[finance/finance_ui/finance_approvals.html]:0:8}; marg_billwatch.py not there yet"
"$APY" -B make_s803.py "$ROOT/finance" "$KDIR" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/6] the builder refused a live file - nothing installed"; }
for f in $FILES; do
  b="$SCR/built/$(basename "$f")"
  [ "$(m5 "$b")" = "${TO[$f]}" ] || stop_unlocked "!! [3/6] rebuilt, $f is $(m5 "$b" | cut -c1-8), not ${TO[$f]:0:8} - nothing installed"
  case "$f" in *.py) for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$b" || stop_unlocked "!! [3/6] $f does not compile on $py - nothing installed"; done;; esac
done
mkdir -p "$SCR/live" && \cp -p "$ROOT/finance/sanjeevni_approvals.py" "$ROOT/finance/owner_notice.py" "$ROOT/finance/finance_ui/finance_approvals.html" "$SCR/live/" || stop_unlocked "!! [3/6] could not copy the live files - nothing installed"
say "[3/6] rebuilt here from this box's live bytes: the four files at their TO pins; the three .py compile under both pythons"
R=$(walk "$SCR/built" "" | tail -1)
[ "$R" = "WALK S803 GREEN" ] || { walk "$SCR/built" "" | grep -E '^RED|Error' | head -8; PLACED=2; stop_unlocked "!! [4/6] the walk on the rebuilt files: $R - nothing installed (kept in $SCR)"; }
R0=$(walk "$SCR/live" "--control" | tail -1)
[ "$R0" = "CONTROL S803 RED as it must be" ] || { PLACED=2; stop_unlocked "!! [4/6] the control on the live files: $R0 - nothing installed (kept in $SCR)"; }
"$VPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True, timeout=30); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$SCR/proof.db" \
  || stop_unlocked "!! [4/6] could not copy $DB for the proof - nothing installed"
proof "$SCR/built" > "$SCR/proof.txt"; PK=$(tail -1 "$SCR/proof.txt"); sed '$d' "$SCR/proof.txt" | sed 's/^/   /'
rm -f "$SCR/proof.db"
say "   $PK"
echo "$PK" | grep -q -E '^PROOF S803: counted [0-9]+ ' || { PLACED=2; stop_unlocked "!! [4/6] the proof on a copy of this box's data did not run - nothing installed (kept in $SCR)"; }
echo "$PK" | grep -q -E 'paper side read' || { PLACED=2; stop_unlocked "!! [4/6] the proof could not read the scanned bills (assets.db) - nothing installed (kept in $SCR)"; }
echo "$PK" | grep -q -E 'page [0-9]+ bytes$' || { PLACED=2; stop_unlocked "!! [4/6] the proof could not make the page - nothing installed (kept in $SCR)"; }
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/6] finance healthz $f0 before the install - nothing installed"
say "[4/6] walk_s803: $R; its control: red as it must be; the proof on a copy of finance.db made the page; finance healthy"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk, the control and the proof green; NOTHING written"; exit 0; fi

for f in $OLDF; do { \cp -p "$ROOT/$f" "$(bak "$f")" && [ "$(m5 "$(bak "$f")")" = "${FROM[$f]}" ]; } || stop_unlocked "!! [5/6] could not write the backup $(bak "$f") - nothing placed"; done
for f in $FILES; do { cat "$SCR/built/$(basename "$f")" > "$(stg "$f")" && [ "$(m5 "$(stg "$f")")" = "${TO[$f]}" ]; } || stop_unlocked "!! [5/6] could not stage $f - nothing placed"; done
for f in $FILES; do chmod --reference="$ROOT/finance/sanjeevni_approvals.py" "$(stg "$f")" 2>/dev/null; chown --reference="$ROOT/finance/sanjeevni_approvals.py" "$(stg "$f")" 2>/dev/null; done
OLDPIDS="$(pids_of "$FSVC" | tr '\n' ' ')"
PLACED=1
for f in $NEWF $OLDF; do mv -f "$(stg "$f")" "$ROOT/$f" || restore "the rename of $f"; done
for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || restore "read back of $f"; done
FILL=$(cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" "$VPY" -W ignore -B "$ROOT/finance/marg_billwatch.py" "$DB" --fill 2>&1 | grep -E '^FILL S803: ' | tail -1)
echo "$FILL" | grep -q -E "^FILL S803: [0-9]+ finding" || restore "the history fill: ${FILL:-no answer}"
ONC=$(cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 120 "$VPY" -W ignore -B "$ROOT/finance/owner_notice.py" collect --db "$DB" 2>&1); ONRC=$?
{ [ "$ONRC" = 0 ] && ! echo "$ONC" | grep -q -E 'Traceback|SyntaxError|NameError|bills: '; } || { echo "$ONC" | tail -4 | sed 's/^/         /'; restore "owner_notice.py collect (it writes nothing) did not run clean"; }
find "$ROOT/finance" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1"
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  sleep "${NAP:-3}"
  JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager -o short 2>/dev/null)"
  for p in $OLDPIDS; do JL="$(printf '%s\n' "$JL" | grep -v -E "\[$p\]:")"; done
  JR="$(printf '%s\n' "$JL" | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError|marg_billwatch NOT mounted|sanjeevni_approvals not mounted')"
  [ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'Traceback|Error|not mounted' | head -6 | sed 's/^/         /'; restore "journal: $JR error line(s) since the restart"; }
fi
say "[5/6] placed and read back: marg_billwatch.py ${TO[finance/marg_billwatch.py]:0:8} · sanjeevni_approvals.py ${TO[finance/sanjeevni_approvals.py]:0:8} · owner_notice.py ${TO[finance/owner_notice.py]:0:8} · finance_approvals.html ${TO[finance/finance_ui/finance_approvals.html]:0:8}"
say "      $FILL"
say "      owner_notice collect ran clean (wrote nothing); $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), healthz $c1; the journal is clean"
mkdir -p "$SCR/placed" && for f in $FILES; do \cp -p "$ROOT/$f" "$SCR/placed/"; done || restore "could not copy the placed files"
R=$(walk "$SCR/placed" "" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 6 ] && R="rehearsal: a forced red at [6/6]"
[ "$R" = "WALK S803 GREEN" ] || restore "the walk on the placed files: $R"
say "[6/6] the walk on the placed files: $R"
release_lock
say "undo (one line): $(for f in $OLDF; do printf '\\cp -p %s %s && ' "$(bak "$f")" "$ROOT/$f"; done)rm -f $(for f in $NEWF; do printf '%s ' "$ROOT/$f"; done)&& $SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. The Marg watch is at https://followup.dr-manoj.in/finance/sanjeevni/marg-watch (also in the Sanjeevni Hub: Go to > Purchases & dealers) -- everything found so far sits under 'Before this page'. The phone notice is OFF until you turn it on, on the page."
exit 0
