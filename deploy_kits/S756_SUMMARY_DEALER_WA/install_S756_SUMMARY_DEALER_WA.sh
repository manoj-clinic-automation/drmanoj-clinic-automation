#!/bin/bash
# =============================================================================
#  install_S756_SUMMARY_DEALER_WA.sh · kit S756 (09-Nov-2026, Sanjeevni session 412) · D876 / F-1207 / F-1208 · the owner's go 06:31 IST 09-Nov
#  THE DEALER IS REMINDED, AND OCTOBER IS ON ONE SCREEN: from the 7th of the next month, at 11:30 IST, every day (Sundays too), one WhatsApp
#  from the reception phone to each dealer whose month summary is still awaited -- the owner's own Hindi words -- until it is recognised;
#  pause / resume per dealer; 'number missing' shown; the snapshot at the top of the purchase check; row 7's count line names every dealer and
#  the parked month's awaited line no longer claims reception's list (F-1208); owner_notice.py's command-line guard moved to the END so cron
#  reaches S755's morning line (F-1207). Three files of this project; one small table (s756_pause), made here.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s756kit && cp -rp /root/deploy/repo/deploy_kits/S756_SUMMARY_DEALER_WA /tmp/s756kit && bash /tmp/s756kit/install_S756_SUMMARY_DEALER_WA.sh
#  (DRY=1 before bash: every gate, the walk, its control, the earlier kits' walks, the cron-shape check and the proof on this box's databases
#   by the LIVE files and by the kit's -- printed whole; NOTHING written.)
#   /root/finance/scan_register.py 0822d308 -> TO   /root/finance/purchase_app.py e80f199c -> TO   /root/finance/owner_notice.py 9096af9a -> TO
#  Gates: SUMS, KIT_ID, the window, the build lock, the three live pins, the rebuild to the TO pins (both pythons compile), walk_s756 green on
#  the rebuilt files, its CONTROL on the live files, the earlier kits' walks (S755, S753, S750, S749, S740, S738, S736, S726, S711) on the
#  rebuilt files -- no red beyond the live files' own --, the cron shape by the rebuilt file, the proof by both.
#  After placing: the table, the service restarted, health, the pages refuse a stranger, the journal (new PIDs only), the walk again on the
#  placed files, the proof and the cron shape by the placed files. owner_notice.py needs no restart -- cron reads the new file at its next tick.
# =============================================================================
set -u
KIT="S756_SUMMARY_DEALER_WA"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
ADB="${ADB:-$ROOT/assetapp/assets.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
FILES="finance/scan_register.py finance/purchase_app.py finance/owner_notice.py"
declare -A FROM=( [finance/scan_register.py]=0822d3084c14fc479311d19c3847c57a [finance/purchase_app.py]=e80f199c2f29cde54baecd43000e659f
                  [finance/owner_notice.py]=9096af9a328627b923022029de8abc21 )
declare -A TO
for f in $FILES; do TO[$f]="$(awk -v f="$f" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s756_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
SCHEMA="$ROOT/finance/purchase_schema.sql"
GREEN="walk_s756: 0 check(s) failed (0 of them S756 checks)"
CONTROL="walk_s756: 31 check(s) failed (31 of them S756 checks)"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S756_${FROM[$1]:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s756"; }
fhealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { for f in $FILES; do rm -f "$(stg "$f")"; done; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s756.py" "$1" "$SCHEMA" "$2" 2>&1); }
walkk() { local w="$1" d="$2"; (cd /tmp && case "$w" in
  walk_s726) S726_SCHEMA_DIR="$ROOT/finance" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/$w.py" "$d" 2>&1;;
  walk_s711) PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/$w.py" "$d" "$SCHEMA" 2>&1;;
  walk_s749) PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/$w.py" "$d" "$SCHEMA" "$SCR/new/shared" "$ROOT/portal/portal.py" 2>&1;;
  *) PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/$w.py" "$d" "$SCHEMA" "$SCR/new/shared" 2>&1;; esac); }
reds() { grep -E '^  (FAIL|RED) ' | sort; }
proof() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -W ignore -B "$KDIR/proof_s756.py" "$1" "$SCR/new/shared" "$DB" "$ADB" "$SCR/proofcopy" 2>&1); }
cron_shape() { (cd "$1" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/check_s756_cron.py" "$DB" 2>&1); }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the files back"
  PLACED=2
  for f in $FILES; do \cp -p "$(bak "$f")" "$ROOT/$f" || say "   !! could not put back $ROOT/$f"; rm -f "$(stg "$f")"; done
  find "$ROOT/finance" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  "$SYSTEMCTL" restart "$FSVC" || true
  for f in $FILES; do say "   $ROOT/$f $(m5 "$ROOT/$f" | cut -c1-8) (expected ${FROM[$f]:0:8})"; done
  say "   finance healthz $(wait200 fhz). Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }
pids_of() { local m; m="$("$SYSTEMCTL" show -p MainPID --value "$1" 2>/dev/null)"; [ -n "$m" ] && [ "$m" != 0 ] && { echo "$m"; pgrep -P "$m" 2>/dev/null; }; }
earlier() {
  local w="$1" new old extra outn outo
  outn="$(walkk "$w" "$SCR/new/finance")"; outo="$(walkk "$w" "$SCR/old/finance")"
  printf '%s\n' "$outn" | tail -1 | grep -q -E '^(walk_s7[0-9]{2}: [0-9]+ check|WALK S711: [0-9]+ ok)' || { printf '%s\n' "$outn" | tail -4 | sed 's/^/         /'; echo "the walk did not reach its own last line on the rebuilt files"; return 1; }
  printf '%s\n' "$outo" | tail -1 | grep -q -E '^(walk_s7[0-9]{2}: [0-9]+ check|WALK S711: [0-9]+ ok)' || { printf '%s\n' "$outo" | tail -4 | sed 's/^/         /'; echo "the walk did not reach its own last line on the live files"; return 1; }
  new="$(printf '%s\n' "$outn" | reds)"; old="$(printf '%s\n' "$outo" | reds)"
  extra="$(comm -13 <(printf '%s\n' "$old" | sort) <(printf '%s\n' "$new" | sort) | sort)"
  if [ -n "$extra" ]; then printf '%s\n' "$extra" | head -8 | sed 's/^/         /'; return 1; fi
  echo "$(printf '%s\n' "$new" | grep -c . ) red(s), of which $(printf '%s\n' "$old" | grep -c .) the live files' own"
}

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout pgrep comm sort; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { [ "$ROOT" != "/root" ] && [ "${SKIP_WINDOW:-0}" = 1 ]; } || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/7] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $FILES; do [ -n "${TO[$f]}" ] || { say "!! [1/7] TO_PINS.md5 does not name $f - nothing installed"; exit 1; }; done
for f in $FILES finance/supplier_msg.py; do [ -f "$ROOT/$f" ] || { say "!! [1/7] $ROOT/$f is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$SCHEMA" ] && [ -f "$ROOT/shared/scan_quality.py" ] || { say "!! [1/7] $DB, $ADB, purchase_schema.sql or scan_quality.py is missing - nothing installed"; exit 1; }
mkdir -p "$SCR/built/finance" "$SCR/pyc" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
ALL=1; for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- ALREADY INSTALLED: the three files are the kit's. Nothing written. finance healthz $(fhz)"; exit 0; }
if [ "${DRY:-0}" = 1 ]; then
  say "[1/7] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/7] kit gates green; the build lock taken $(TZ=Asia/Kolkata date '+%d-%m %H:%M IST') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  TOOK_LOCK=1; say "[1/7] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."
  exit 3
fi
for f in $FILES; do C=$(m5 "$ROOT/$f"); [ "$C" = "${FROM[$f]}" ] || stop_unlocked "!! [2/7] $ROOT/$f is ${C:0:8}, expected ${FROM[$f]:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
say "[2/7] live pins exact: scan_register ${FROM[finance/scan_register.py]:0:8} · purchase_app ${FROM[finance/purchase_app.py]:0:8} · owner_notice ${FROM[finance/owner_notice.py]:0:8}"

"$APY" -B make_s756.py "$ROOT/finance" "$SCR/built" "$KDIR" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/7] the builder refused a live file - nothing installed"; }
for f in $FILES; do
  [ "$(m5 "$SCR/built/$f")" = "${TO[$f]}" ] || stop_unlocked "!! [3/7] rebuilt, $f is $(m5 "$SCR/built/$f" | cut -c1-8), not ${TO[$f]:0:8} - nothing installed"
  for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/$f" || stop_unlocked "!! [3/7] $f does not compile on $py - nothing installed"; done
done
mkdir -p "$SCR/new/finance" "$SCR/new/shared" "$SCR/old/finance"
for f in "$ROOT"/finance/*.py "$ROOT"/finance/*.json "$ROOT"/finance/*.sql "$ROOT"/finance/*.html; do [ -f "$f" ] && cp -p "$f" "$SCR/new/finance/" && cp -p "$f" "$SCR/old/finance/"; done
for f in "$ROOT"/shared/*.py; do [ -f "$f" ] && cp -p "$f" "$SCR/new/shared/"; done
for f in $FILES; do cp -p "$SCR/built/$f" "$SCR/new/finance/$(basename "$f")"; done
say "[3/7] rebuilt here from this box's live bytes: the three files at their TO pins; each compiles under both pythons"

R=$(walk "$SCR/new/finance" "$SCR/new/shared" | tail -1)
[ "$R" = "$GREEN" ] || { walk "$SCR/new/finance" "$SCR/new/shared" | grep -E 'FAIL|Error|raised' | head -12 | sed 's/^/         /'; PLACED=2; stop_unlocked "!! [4/7] the walk on the rebuilt files is not green ($R) - nothing installed (kept in $SCR)"; }
R0=$(walk "$SCR/old/finance" "$SCR/new/shared" | tail -1)
[ "$R0" = "$CONTROL" ] || { PLACED=2; stop_unlocked "!! [4/7] the control on the live files is not as expected ($R0; expected $CONTROL) - nothing installed (kept in $SCR)"; }
EARLIER_ALL="walk_s755 walk_s753 walk_s750 walk_s749 walk_s740 walk_s738 walk_s736 walk_s726 walk_s711"
if [ "$ROOT" != "/root" ]; then EARLIER="${REHEARSE_EARLIER:-$EARLIER_ALL}"; else EARLIER="$EARLIER_ALL"; fi
ESAY=""
for w in $EARLIER; do
  E="$(earlier "$w")" || { PLACED=2; stop_unlocked "!! [4/7] $w on the rebuilt files shows a red the live files do not (above) - nothing installed (kept in $SCR)"; }
  ESAY="$ESAY; $w: $E"
done
say "[4/7] the walk: $R; the control: $R0$ESAY"
proof "$SCR/old/finance" > "$SCR/proof_live.txt"; proof "$SCR/new/finance" > "$SCR/proof_kit.txt"
PL=$(tail -1 "$SCR/proof_live.txt"); PK=$(tail -1 "$SCR/proof_kit.txt")
say "---------------------------------------------------------------- the proof by the KIT's files (read only; the queue tried on a copy) -- paste all of it to Claude"
sed 's/^/   /' "$SCR/proof_kit.txt"
say "---------------------------------------------------------------- the live files said"
sed 's/^/   /' "$SCR/proof_live.txt"
say "----------------------------------------------------------------"
echo "$PK" | grep -q -E '^PROOF S756: ended months [0-9]+ .* would queue [0-9]+ today' || { PLACED=2; stop_unlocked "!! [4/7] the proof on this box's databases: $PK - nothing installed (kept in $SCR)"; }
echo "$PL" | grep -q -E '^PROOF S756: ended months [0-9]+ ' || { PLACED=2; stop_unlocked "!! [4/7] the proof by the live files: $PL - nothing installed (kept in $SCR)"; }
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/7] finance healthz $f0 before the install - nothing installed"
say "[4/7] live: $PL"
say "      kit:  $PK; finance healthy"
C4="$(cron_shape "$SCR/new/finance")"
{ [ "$ROOT" != "/root" ] || ! echo "$C4" | tail -1 | grep -q "ASSETS UNREAD"; } && echo "$C4" | tail -1 | grep -q -E '^S756 CRON-SHAPE: ok ' || { echo "$C4" | tail -6 | sed 's/^/         /'; PLACED=2; stop_unlocked "!! [4/7] owner_notice.py, run as cron runs it (the rebuilt file), does not reach the morning line - nothing installed (kept in $SCR)"; }
say "      cron-shape, by the rebuilt file: $(echo "$C4" | tail -1)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk, the control, the earlier kits' walks, the cron-shape check and the proof green; NOTHING written"; exit 0; fi

for f in $FILES; do { \cp -p "$ROOT/$f" "$(bak "$f")" && [ "$(m5 "$(bak "$f")")" = "${FROM[$f]}" ]; } || stop_unlocked "!! [5/7] could not write the backup $(bak "$f") - nothing placed"; done
for f in $FILES; do { cat "$SCR/built/$f" > "$(stg "$f")" && [ "$(m5 "$(stg "$f")")" = "${TO[$f]}" ]; } || stop_unlocked "!! [5/7] could not stage $f - nothing placed"; done
for f in $FILES; do chmod --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; chown --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; done
"$VPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1], timeout=30); c.execute(\"CREATE TABLE IF NOT EXISTS s756_pause (id INTEGER PRIMARY KEY AUTOINCREMENT, dealer TEXT NOT NULL, paused_at TEXT NOT NULL, paused_by TEXT, resumed_at TEXT, resumed_by TEXT)\"); c.commit()" "$DB" \
  || stop_unlocked "!! [5/7] could not make the table s756_pause - nothing placed"
OLDPIDS="$(pids_of "$FSVC" | tr '\n' ' ')"
PLACED=1
for f in $FILES; do mv -f "$(stg "$f")" "$ROOT/$f" || restore "the rename of $f"; done
for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || restore "read back of $f"; done
find "$ROOT/finance" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[5/7] the table s756_pause made; placed and read back: scan_register ${TO[finance/scan_register.py]:0:8} · purchase_app ${TO[finance/purchase_app.py]:0:8} · owner_notice ${TO[finance/owner_notice.py]:0:8}"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(fhealth /finance/amir/step/1); case "$c2" in 302|401|403) ;; *) restore "Amir's page answered $c2 without a login (expected 302, 401 or 403)";; esac
c3=$(fhealth /finance/purchase/page/check); case "$c3" in 302|401|403) ;; *) restore "the step view answered $c3 without a login (expected 302, 401 or 403)";; esac
c4=$(fhealth /finance/porders/s454/billkaam); case "$c4" in 302|401|403) ;; *) restore "Aaj ka bill kaam answered $c4 without a login (expected 302, 401 or 403)";; esac
c5=$(fhealth /finance/purchase/page/pay); case "$c5" in 302|401|403) ;; *) restore "the payment sheet answered $c5 without a login (expected 302, 401 or 403)";; esac
NEWPIDS="$(pids_of "$FSVC" | tr '\n' ' ')"
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager -o short 2>/dev/null)"
  for p in $OLDPIDS; do JL="$(printf '%s\n' "$JL" | grep -v -E "\[$p\]:")"; done
  JR="$(printf '%s\n' "$JL" | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError|Logging error')"
  [ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'Traceback|Error' | head -6 | sed 's/^/         /'; restore "journal: $JR error line(s) from the new master ($NEWPIDS) since the restart"; }
fi
say "[6/7] $FSVC restarted at $(TZ=Asia/Kolkata date '+%H:%M IST'): healthz $c1; without a login Amir's page $c2, the step view $c3, Aaj ka bill kaam $c4, the payment sheet $c5; journal clean (new PIDs: $NEWPIDS)"
mkdir -p "$SCR/placed/finance"
for f in "$ROOT"/finance/*.py "$ROOT"/finance/*.json "$ROOT"/finance/*.sql "$ROOT"/finance/*.html; do [ -f "$f" ] && cp -p "$f" "$SCR/placed/finance/"; done
R=$(walk "$SCR/placed/finance" "$SCR/new/shared" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 7 ] && R="rehearsal: a forced red at [7/7]"
[ "$R" = "$GREEN" ] || restore "the walk on the placed files: $R"
P7=$(proof "$SCR/placed/finance" | tail -1)
echo "$P7" | grep -q -E '^PROOF S756: ended months [0-9]+ .* would queue [0-9]+ today' || restore "the proof by the placed files: $P7"
C7="$(cron_shape "$ROOT/finance")"
{ [ "$ROOT" != "/root" ] || ! echo "$C7" | tail -1 | grep -q "ASSETS UNREAD"; } && echo "$C7" | tail -1 | grep -q -E '^S756 CRON-SHAPE: ok ' || { echo "$C7" | tail -6 | sed 's/^/         /'; restore "owner_notice.py, run as cron runs it, does not reach the morning line"; }
say "      $(echo "$C7" | tail -1)"
NOWM=$((10#$(TZ=Asia/Kolkata date +%H) * 60 + 10#$(TZ=Asia/Kolkata date +%M)))
if [ "$NOWM" -ge 690 ]; then WHEN="at owner_notice's next five-minute tick (it is past 11:30 IST)"; else WHEN="at 11:30 IST today"; fi
say "[7/7] the walk on the placed files: $R; by the placed files: $P7 -- the first reminders are queued $WHEN; the purchase check shows the snapshot at its next load"
release_lock
say "undo (one line): $(for f in $FILES; do printf '\\cp -p %s %s && ' "$(bak "$f")" "$ROOT/$f"; done)$SYSTEMCTL restart $FSVC && $VPY -c \"import sqlite3; c=sqlite3.connect('$DB'); c.execute(\\\"UPDATE supplier_msg SET status='skipped', last_error='undo S756' WHERE kind='summary' AND (status='failed' OR (status='queued' AND handed_at IS NULL))\\\"); c.commit()\""
say ""
say "$KIT: DONE. Your purchase check: https://followup.dr-manoj.in/finance/purchase/page/check?month=2026-10"
exit 0
