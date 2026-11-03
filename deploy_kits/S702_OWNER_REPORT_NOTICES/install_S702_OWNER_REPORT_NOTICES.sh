#!/bin/bash
# =============================================================================
#  install_S702_OWNER_REPORT_NOTICES.sh · kit S702 (03-Nov-2026, Sanjeevni session 380) · the owner is told when the Marg work is DONE --
#  Shavez's morning pair, the Stock Valuation, Amir's three exports, Darpan's order sheet, his own three lists, the reception phone silent --
#  every day, Sundays too; a Monday asks for Sunday's pair; Stock Expiry off Shavez's month rows (F-1090); the WhatsApp button says why (F-1089).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s702kit && cp -rp /root/deploy/repo/deploy_kits/S702_OWNER_REPORT_NOTICES /tmp/s702kit && bash /tmp/s702kit/install_S702_OWNER_REPORT_NOTICES.sh
#  (DRY=1 before bash: every gate, the walk, the control and the proof on copies -- nothing written, nothing sent.)
#   /root/finance/reports_tile.py    03902a5d -> TO   _due_day yesterday every day; Stock Expiry out of the month rows
#   /root/finance/reports_watch.py   428c389c -> TO   the morning alarms no longer silent on Sundays
#   /root/finance/porders_s454.py    438714b8 -> TO   the disabled WhatsApp button says why (F-1089)
#   /root/finance/owner_notice.py    NEW              the messages (clinic app; ntfy when no device)
#   the crontab: ONE line added (every 5 minutes, owner_notice.py tick); removed again on undo
#  THE GATE THAT DECIDES: the walk on the rebuilt files (own rows, 2099), the control on the live files, and the proof -- the OLD and NEW
#  page judgement and alarms on a COPY of the database for the last 36 days: only Mondays (due day Sunday), Stock Expiry rows and the
#  Sunday alarms may differ.  Data step: the settings, owner_notice.since = the install's minute.  Restarts clinic-finance.
#  After placing: ONE test message to the owner (the road's proof; a message that cannot go is said, never a restore).
# =============================================================================
set -u
KIT="S702_OWNER_REPORT_NOTICES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"; CRONTAB="${CRONTAB:-crontab}"
FILES="finance/reports_tile.py finance/reports_watch.py finance/porders_s454.py"
NEWF="finance/owner_notice.py"
declare -A FROM=( [finance/reports_tile.py]=03902a5d1e2be049d51bcfe38306b431 [finance/reports_watch.py]=428c389c0cbac3eab881fa99d4659b06
                  [finance/porders_s454.py]=438714b8d5c094a9ee7cdc71731b44e0 )
declare -A TO
for f in $FILES $NEWF; do TO[$f]="$(awk -v f="$f" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s702_inst_$STAMP"
PLACED=0; TOOK_LOCK=0; CRON_ADDED=0; NEW_PLACED=0; SELF=""
GREEN="46 of 46 green"
CONTROL="32 S702 check(s) red . 14 green"
CRONLINE="*/5 * * * * cd $ROOT/finance && $VPY -B owner_notice.py tick >> $ROOT/finance/owner_notice.log 2>&1 # S702"
CRONKEY="owner_notice.py tick"
CRONBAK="$ROOT/finance/crontab.bak_S702_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S702_${FROM[$1]:0:8}"; }
stg() { echo "$ROOT/finance/.$(basename "$1").s702"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
fhealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { for f in $FILES $NEWF; do rm -f "$(stg "$f")"; done; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -B "$KDIR/walk_s702.py" "$@" 2>&1); }
cron_read() {   # the crontab to a file; 0 = read (maybe empty: 'no crontab' is not a fault), 1 = could not read -- a failed read is never piped back
  local out; out="$("$CRONTAB" -l 2>"$SCR/cron.err")"; local rc=$?
  if [ $rc -ne 0 ] && ! grep -q -i "no crontab" "$SCR/cron.err"; then return 1; fi
  printf '%s\n' "$out" | sed '/^$/d' > "$SCR/cron.now"; return 0
}
cron_has() { cron_read && grep -F -q -- "$CRONKEY" "$SCR/cron.now"; }
cron_add() { cron_read || return 1; \cp -p "$SCR/cron.now" "$CRONBAK" 2>/dev/null; { cat "$SCR/cron.now"; echo "$CRONLINE"; } | "$CRONTAB" - && CRON_ADDED=1; }
cron_del() { cron_read || return 1; grep -F -v -- "$CRONKEY" "$SCR/cron.now" | "$CRONTAB" - ; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the three files back and taking the new one away"
  PLACED=2
  for f in $FILES; do \cp -p "$(bak "$f")" "$ROOT/$f" || say "   !! could not put back $ROOT/$f"; rm -f "$(stg "$f")"; done
  [ "$NEW_PLACED" = 1 ] && { mv -f "$ROOT/$NEWF" "$ROOT/$NEWF.removed_S702_$STAMP" && say "   $ROOT/$NEWF moved aside"; }
  [ "$CRON_ADDED" = 1 ] && { cron_del && say "   the cron line removed again"; }
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

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/8] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $FILES $NEWF; do [ -n "${TO[$f]}" ] || { say "!! [1/8] TO_PINS.md5 does not name $f - nothing installed"; exit 1; }; done
for f in $FILES; do [ -f "$ROOT/$f" ] || { say "!! [1/8] $ROOT/$f is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/8] $DB is missing - nothing installed"; exit 1; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
ALL=1; for f in $FILES $NEWF; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then
  cron_has || { [ "${DRY:-0}" = 1 ] || { cron_add && say "-- the files were already the kit's; the cron line was missing and is added now"; }; }
  say "-- ALREADY INSTALLED: the four files are the kit's. Nothing else written. finance healthz $(fhz)"; exit 0
fi
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
for f in $FILES; do C=$(m5 "$ROOT/$f"); [ "$C" = "${FROM[$f]}" ] || stop_unlocked "!! [2/8] $ROOT/$f is ${C:0:8}, expected ${FROM[$f]:0:8} - it changed after this kit was built: STOP, nothing installed"; done
[ -e "$ROOT/$NEWF" ] && stop_unlocked "!! [2/8] $ROOT/$NEWF already exists and is not the kit's - STOP, nothing installed"
say "[2/8] live pins exact: reports_tile ${FROM[finance/reports_tile.py]:0:8}, reports_watch ${FROM[finance/reports_watch.py]:0:8}, porders_s454 ${FROM[finance/porders_s454.py]:0:8}; owner_notice.py not there yet"

mkdir -p "$SCR/built/finance" "$SCR/pyc" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s702.py "$ROOT" "$KDIR" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/8] the builder refused a live file - nothing installed"; }
for f in $FILES $NEWF; do
  [ "$(m5 "$SCR/built/$f")" = "${TO[$f]}" ] || stop_unlocked "!! [3/8] rebuilt, $f is $(m5 "$SCR/built/$f" | cut -c1-8), not ${TO[$f]:0:8} - nothing installed"
  for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$f" || stop_unlocked "!! [3/8] $f does not compile on $py - nothing installed"; done
done
mkdir -p "$SCR/newroot/finance" && for f in "$ROOT"/finance/*.py "$ROOT"/finance/*.json; do [ -e "$f" ] && ln -s "$f" "$SCR/newroot/finance/$(basename "$f")"; done
[ -d "$ROOT/finance/spine" ] && ln -s "$ROOT/finance/spine" "$SCR/newroot/finance/spine"
for f in $FILES $NEWF; do rm -f "$SCR/newroot/$f" && cp -p "$SCR/built/$f" "$SCR/newroot/$f"; done
say "[3/8] rebuilt here from this box's live bytes: the four files at their TO pins; each compiles under both pythons"

R=$(walk --new "$SCR/newroot" --scratch "$SCR/w1" | tail -1)
[ "$R" = "$GREEN" ] || { walk --new "$SCR/newroot" --scratch "$SCR/w1b" | grep -E 'RED' | head -12 | sed 's/^/         /'; PLACED=2; stop_unlocked "!! [4/8] the walk on the rebuilt files is not green ($R) - nothing installed (kept in $SCR)"; }
R0=$(walk --old "$ROOT" --scratch "$SCR/w0" | tail -1)
[ "$R0" = "$CONTROL" ] || { PLACED=2; stop_unlocked "!! [4/8] the control on the live files is not as expected ($R0) - nothing installed (kept in $SCR)"; }
for t in reports_tile reports_watch; do
  case "$t" in reports_tile) a="selftest";; *) a="--selftest";; esac
  ST=$(cd "$SCR/newroot/finance" && FINANCE_DB="$SCR/st_$t.db" SPINE_READINGS="$SCR/st_rd_$t" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -B "$t.py" $a 2>&1 | tail -1)
  case "$ST" in *" 0 failure"*|*"0 failures"*) ;; *) PLACED=2; stop_unlocked "!! [4/8] $t's own selftest on the rebuilt file: $ST - nothing installed (kept in $SCR)";; esac
  SELF="$SELF $t: $ST;"
done
copydb "$DB" "$SCR/walk.db" || stop_unlocked "!! [4/8] no copy of the database - nothing installed"
P=$(walk --proof --old-root "$ROOT" --new "$SCR/newroot" --db "$SCR/walk.db" --scratch "$SCR/wp")
PL="$(echo "$P" | tail -1)"
echo "$P" | grep -E '^  --  |RED' | head -24 | sed 's/^/         /'
case "$PL" in "proof: old vs new over "*" . CLEAN . "*) ;; *) PLACED=2; stop_unlocked "!! [4/8] the proof is not clean ($PL) - nothing installed (kept in $SCR)";; esac
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/8] finance healthz $f0 before the install - nothing installed"
say "[4/8] the walk: $R; the control on the live files: $R0;$SELF $PL; finance healthy ($f0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk, the control, the selftests and the proof green; NOTHING written, nothing sent"; exit 0; fi

for f in $FILES; do { \cp -p "$ROOT/$f" "$(bak "$f")" && [ "$(m5 "$(bak "$f")")" = "${FROM[$f]}" ]; } || stop_unlocked "!! [5/8] could not write the backup $(bak "$f") - nothing placed"; done
for f in $FILES $NEWF; do { cat "$SCR/built/$f" > "$(stg "$f")" && [ "$(m5 "$(stg "$f")")" = "${TO[$f]}" ]; } || stop_unlocked "!! [5/8] could not stage $f - nothing placed"; done
for f in $FILES; do chmod --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; chown --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; done
chmod --reference="$ROOT/finance/reports_watch.py" "$(stg "$NEWF")" 2>/dev/null; chown --reference="$ROOT/finance/reports_watch.py" "$(stg "$NEWF")" 2>/dev/null
PLACED=1
for f in $FILES; do mv -f "$(stg "$f")" "$ROOT/$f" || restore "the rename of $f"; done
mv -f "$(stg "$NEWF")" "$ROOT/$NEWF" && NEW_PLACED=1 || restore "the rename of $NEWF"
for f in $FILES $NEWF; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || restore "read back of $f"; done
find "$ROOT/finance" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[5/8] placed and read back: reports_tile ${TO[finance/reports_tile.py]:0:8}, reports_watch ${TO[finance/reports_watch.py]:0:8}, porders_s454 ${TO[finance/porders_s454.py]:0:8}, owner_notice ${TO[$NEWF]:0:8} (backups *.bak_S702_*)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(fhealth /finance/porders); case "$c2" in 302|401|303|403) ;; *) restore "the order page answered $c2 without a login";; esac
c3=$(fhealth /finance/reports/aaj); case "$c3" in 302|401|303|403) ;; *) restore "Shavez's page answered $c3 without a login";; esac
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JR="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[6/8] $FSVC restarted at $T0: healthz $c1; the order page $c2 and Shavez's page $c3 without a login (the login gate, expected); journal clean"
R=$(walk --new "$ROOT" --scratch "$SCR/w2" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 7 ] && R="rehearsal: a forced red at [7/8]"      # the rehearsal's hook only; unset on a real install
[ "$R" = "$GREEN" ] || restore "the walk on the placed files: $R"
SINCE="$(TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M:%S')"
( cd "$ROOT/finance" && "$VPY" -B -c "
import sqlite3, sys
import owner_notice as o
con = sqlite3.connect(sys.argv[1], timeout=30); o.ensure(con)
con.execute(\"UPDATE setting SET value=? WHERE key='owner_notice.since'\", (sys.argv[2],)); con.commit()
print(con.execute(\"SELECT value FROM setting WHERE key='owner_notice.since'\").fetchone()[0])" "$DB" "$SINCE" > "$SCR/since.txt" 2>&1 ) || { cat "$SCR/since.txt"; restore "the settings step"; }
cron_has || cron_add || restore "the cron line could not be added"
say "[7/8] the walk on the placed files: $R; the settings seeded, owner_notice.since $(tail -1 "$SCR/since.txt"); the cron line $( [ "$CRON_ADDED" = 1 ] && echo "added (the crontab as it was: $CRONBAK)" || echo 'was already there' )"
release_lock
TM=$(cd "$ROOT/finance" && timeout 60 "$VPY" -B owner_notice.py test --db "$DB" 2>&1 | tail -1)
TK=$(cd "$ROOT/finance" && timeout 120 "$VPY" -B owner_notice.py tick --db "$DB" 2>&1 | tail -1 | cut -c1-220)
say "[8/8] the test message: $TM"
say "      the first tick: $TK"
case "$TM" in *"test: SENT -- clinic app"*) ;; *"test: SENT -- ntfy"*) say "      -- it went by ntfy: no device of the owner's login has allowed the clinic app yet";; *) say "      !! the test message did not go -- the kit stays installed (the messages wait and are tried again); send a photo of this screen to Claude";; esac
say "undo (one line): $(for f in $FILES; do printf '\\cp -p %s %s && ' "$(bak "$f")" "$ROOT/$f"; done)mv -f $ROOT/$NEWF $ROOT/$NEWF.undone && (crontab -l | grep -F -v -- '$CRONKEY' | crontab -) && $SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. The owner is told when the morning reports, Amir's exports, Darpan's order sheet and his own lists are in -- Sundays too."
exit 0
