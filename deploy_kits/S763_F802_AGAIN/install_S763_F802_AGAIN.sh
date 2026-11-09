#!/bin/bash
# =============================================================================
#  install_S763_F802_AGAIN.sh · kit S763 (09-Nov-2026, Sanjeevni session 417) · F-802's permanent fix (D867 / D868 / D879)
#  THE SAME EXPORT, RECEIVED AGAIN -- the server half. Until now an export whose bytes the server already held was answered ALREADY and
#  written nowhere (and the medical PC did not even send it), so an unchanged salt list exported after a salt tick could never clear
#  Amir's "salt list due". Now:
#   /root/finance/marg_door.py   565ad9c8 -> TO   X-Marg-Note: again -> a record row in a NEW table mi_receipt (made by the door on its first
#                                                 re-receipt) and, for a VERIFIED report, the setting 'mi_again:<TYPE>' moved forward to the
#                                                 moment the PC says it was exported (never later than now); answer AGAIN "received again,
#                                                 same as <stamp>"; an md5 it does not hold is UNKNOWN, nothing written; mi_file is never touched
#   /root/finance/amir_day.py    c86bb8e5 -> TO   the salt duty reads the newest of: a verified salt list's first receipt, its export again
#   /root/finance/reports_tile.py f44fe768 -> TO  the salt row reads the same
#   claude_code_briefs/DUTY_MAP.json (the repository, arrives with the publish) v20 -> v21: amir.salt_list due_sql = amir_day's, byte for byte
#  The medical PC's half (marg_watch.py, which sends the re-receipt) is placed AFTER this, by the chat, through Drive ToMedical\_kit.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s763kit && cp -rp /root/deploy/repo/deploy_kits/S763_F802_AGAIN /tmp/s763kit && bash /tmp/s763kit/install_S763_F802_AGAIN.sh
#  (DRY=1 before bash: every gate, the walk, its control, the earlier walk and the proof on this box's data, printed; NOTHING written.)
#  The map v21 may reach this box with ANY pull, before this install: it reads only mi_file and the setting table, both always there,
#  and with no 'mi_again:' setting yet it reads exactly as v20 did.
#  Gates: the window, SUMS, KIT_ID, the build lock; the three live pins and the two it reads (marg_take, marg_ingest); the repository's map at its TO pin (real run);
#  the rebuild to the TO pins (both pythons compile); walk_s763 green on the rebuilt files and its CONTROL red on the live files; the
#  earlier walk S761 on a copy of finance.db -- no red beyond the live files' own; the proof by both on ONE copy of finance.db: the same
#  salt duty, the same salt row, every duty of the map the same (while no re-receipt has been written), and a made-up re-receipt in the
#  copy clears the salt duty by the kit's files only. After placing: finance restarted, health, the door refuses a stranger, the journal (new PIDs only), the walk again.
# =============================================================================
set -u
KIT="S763_F802_AGAIN"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
REPOMAP="${REPOMAP:-/root/deploy/repo/claude_code_briefs/DUTY_MAP.json}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
FILES="finance/marg_door.py finance/amir_day.py finance/reports_tile.py"
declare -A FROM=( [finance/marg_door.py]=565ad9c811ecb74a29340abd73c26f12 [finance/amir_day.py]=c86bb8e533a1084c62bd2a2dfc8f7aef
                  [finance/reports_tile.py]=f44fe768beed07069968113a3e55259d )
declare -A READS=( [marg_ingest/marg_take.py]=5cad2d24d63344146f562fd5d441dbdf [marg_ingest/marg_ingest.py]=828c4dad6b159207b034d8129aed3ab7 )
declare -A TO
for f in $FILES; do TO[$f]="$(awk -v f="$f" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
MAP_FROM=78b5f07ef7cdd48b1a76d78db52107fc
MAP_TO="$(awk '$2=="claude_code_briefs/DUTY_MAP.json"{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s763_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
GREEN="WALK GREEN"
CONTROL="CONTROL RED as it must be (every S763 check red on the live files, every old check green)"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S763_${FROM[$1]:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s763"; }
fhealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fhealth /finance/healthz; }
fdoor() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/api/marg-file; else curl -s -o /dev/null -m 8 -w '%{http_code}' -X POST -H 'X-Marg-Note: again' -H 'Content-Type: application/json' -d '{}' "http://127.0.0.1:$FIN_PORT/finance/api/marg-file"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { for f in $FILES; do rm -f "$(stg "$f")"; done; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
dbcopy() { "$VPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True, timeout=30); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$1"; }
mkroot() {   # $1 = a root to make: finance/, finance/spine/, finance/finance_ui/, marg_ingest/ -- code, pages, rules, as the nightly bundle holds them
  local d e f
  for d in finance finance/spine finance/finance_ui marg_ingest marg_ingest/lib; do
    [ -d "$ROOT/$d" ] || continue
    mkdir -p "$1/$d" || return 1
    for e in py html json sql txt sh; do for f in "$ROOT/$d"/*."$e"; do if [ -f "$f" ]; then cp -p "$f" "$1/$d/" || return 1; fi; done; done
  done
  return 0; }
codedir() {  # $1 = the dir to make, $2 = the root whose three files it takes, $3 = from|to (the medical file and the map)
  mkdir -p "$1" || return 1
  for f in $FILES; do cp -p "$2/$f" "$1/" || return 1; done
  if [ "$3" = to ]; then cp -p "$KDIR/medical/marg_watch.py" "$KDIR/to/DUTY_MAP.json" "$1/"; else cp -p "$KDIR/from/marg_watch.py" "$KDIR/from/DUTY_MAP.json" "$1/"; fi; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s763.py" "$1" "$2" $3 2>&1); }
proof() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -W ignore -B "$KDIR/proof_s763.py" "$1" "$2" "$SCR/walk.db" "$3" "$4" "$5" 2>&1); }   # ONE copy for both (review 6)
reds() { grep -E '^ *(FAIL|RED) ' | sed -E 's/ +\| .*$//; s/ +\[\[.*$//' | sort; }
earlier761() {   # walk_s761 (the hub's needs-you and the console's count read the duties) on the rebuilt root and on the live root
  local outn outo extra
  outn="$(cd /tmp && PYTHONPATH="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s761.py" --root "$SCR/new" --db "$SCR/walk.db" --scratch "$SCR/e761n" --page "$SCR/new/finance/finance_ui/finance_approvals.html" 2>&1)"
  outo="$(cd /tmp && PYTHONPATH="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s761.py" --root "$SCR/old" --db "$SCR/walk.db" --scratch "$SCR/e761o" --page "$SCR/old/finance/finance_ui/finance_approvals.html" 2>&1)"
  printf '%s\n' "$outn" | grep -q -E '^walk_s761: [0-9]+ check' || { printf '%s\n' "$outn" | tail -4 | sed 's/^/         /'; echo "walk_s761 did not run on the rebuilt files"; return 1; }
  extra="$(comm -13 <(printf '%s\n' "$outo" | reds) <(printf '%s\n' "$outn" | reds))"
  if [ -n "$extra" ]; then
    echo "      walk_s761 -- red on the rebuilt files, NOT on the live files:" >&2; printf '%s\n' "$extra" | head -12 | sed 's/^/         /' >&2
    return 1
  fi
  if printf '%s\n' "$outn" | reds | grep -q .; then
    echo "      walk_s761 -- its red lines (the live files show the same):" >&2; printf '%s\n' "$outn" | grep -E '^ *(FAIL|RED) ' | head -12 | cut -c1-200 | sed 's/^/         /' >&2
  fi
  echo "$(printf '%s\n' "$outn" | tail -1)"
}
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the three files back"
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

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout pgrep comm sort; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { [ "$ROOT" != "/root" ] && [ "${SKIP_WINDOW:-0}" = 1 ]; } || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/7] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $FILES; do [ -n "${TO[$f]}" ] || { say "!! [1/7] TO_PINS.md5 does not name $f - nothing installed"; exit 1; }; done
[ -n "$MAP_TO" ] && [ "$(m5 "$KDIR/to/DUTY_MAP.json")" = "$MAP_TO" ] || { say "!! [1/7] the kit's map is not its TO pin - nothing installed"; exit 1; }
for f in $FILES "${!READS[@]}"; do [ -f "$ROOT/$f" ] || { say "!! [1/7] $ROOT/$f is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/7] $DB is missing - nothing installed"; exit 1; }
mkdir -p "$SCR/built/finance" "$SCR/pyc" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
ALL=1; for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the three files are the kit's. Nothing written. finance healthz $(fhz)"; exit 0; fi
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
for f in "${!READS[@]}"; do C=$(m5 "$ROOT/$f"); [ "$C" = "${READS[$f]}" ] || stop_unlocked "!! [2/7] $ROOT/$f is ${C:0:8}, expected ${READS[$f]:0:8} (read by the door) - STOP, nothing installed. Tell Claude."; done
RM=$(m5 "$REPOMAP")
if [ "${DRY:-0}" = 1 ]; then
  case "$RM" in "$MAP_FROM") MSAY="the repository's map is still v20 (78b5f07e)";; "$MAP_TO") MSAY="the repository's map is already v21 (${MAP_TO:0:8})";; *) stop_unlocked "!! [2/7] the repository's map is ${RM:0:8}, neither v20 nor the kit's v21 - STOP. Tell Claude.";; esac
else
  [ "$RM" = "$MAP_TO" ] || stop_unlocked "!! [2/7] the repository's map is ${RM:0:8}, not the kit's v21 ${MAP_TO:0:8} - the publish has not reached this box: STOP, nothing installed. Tell Claude."
  MSAY="the repository's map v21 ${MAP_TO:0:8}"
fi
say "[2/7] live pins exact: marg_door ${FROM[finance/marg_door.py]:0:8} · amir_day ${FROM[finance/amir_day.py]:0:8} · reports_tile ${FROM[finance/reports_tile.py]:0:8}; read: marg_take 5cad2d24 · marg_ingest 828c4dad; $MSAY"

"$APY" -B make_s763.py "$ROOT/finance" "$SCR/built/finance" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/7] the builder refused a live file - nothing installed"; }
for f in $FILES; do
  [ "$(m5 "$SCR/built/$f")" = "${TO[$f]}" ] || stop_unlocked "!! [3/7] rebuilt, $f is $(m5 "$SCR/built/$f" | cut -c1-8), not ${TO[$f]:0:8} - nothing installed"
  for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/$f" || stop_unlocked "!! [3/7] $f does not compile on $py - nothing installed"; done
done
mkroot "$SCR/new" && mkroot "$SCR/old" || stop_unlocked "!! [3/7] could not copy $ROOT for the walks - nothing installed"
for f in $FILES; do cp -p "$SCR/built/$f" "$SCR/new/$f"; done
codedir "$SCR/cnew" "$SCR/new" to && codedir "$SCR/cold" "$SCR/old" from || stop_unlocked "!! [3/7] could not make the walk's code folders - nothing installed"
dbcopy "$SCR/walk.db" || stop_unlocked "!! [3/7] could not copy $DB for the earlier walk - nothing installed"
say "[3/7] rebuilt here from this box's live bytes: the three files at their TO pins; they compile under both pythons"

R=$(walk "$SCR/cnew" "$SCR/new" "" | tail -1)
[ "$R" = "$GREEN" ] || { walk "$SCR/cnew" "$SCR/new" "" | grep -E 'RED|Error|raised' | head -12 | sed 's/^/         /'; PLACED=2; stop_unlocked "!! [4/7] the walk on the rebuilt files is not green ($R) - nothing installed (kept in $SCR)"; }
R0=$(walk "$SCR/cold" "$SCR/old" "--control" | tail -1)
[ "$R0" = "$CONTROL" ] || { PLACED=2; stop_unlocked "!! [4/7] the control on the live files is not as expected ($R0) - nothing installed (kept in $SCR)"; }
if [ "${REHEARSE_EARLIER:-}" = none ] && [ "$ROOT" != "/root" ]; then E761="walk_s761 not run (a rehearsal on a made-up root)"; else
E761="$(earlier761)" || { PLACED=2; stop_unlocked "!! [4/7] walk_s761 on the rebuilt files shows a red the live files do not (above) - nothing installed (kept in $SCR)"; }; fi
NW=$(walk "$SCR/cnew" "$SCR/new" "" | grep -c -E '^  OK ')
say "[4/7] walk_s763: $R ($NW checks); its control: red as it must be; earlier: $E761"
proof "$SCR/old/finance" "$SCR/old" "$SCR/pold" "$KDIR/from/DUTY_MAP.json" "(the live files)" > "$SCR/proof_live.txt"
proof "$SCR/new/finance" "$SCR/new" "$SCR/pnew" "$KDIR/to/DUTY_MAP.json" "(the kit)" > "$SCR/proof_kit.txt"
PL=$(tail -1 "$SCR/proof_live.txt"); PK=$(tail -1 "$SCR/proof_kit.txt")
say "---------------------------------------------------------------- the proof by the KIT's files (read only, a copy of finance.db) -- paste all of it to Claude"
sed -E 's/^/   /' "$SCR/proof_kit.txt"
say "---------------------------------------------------------------- the live files said"
sed 's/^/   /' "$SCR/proof_live.txt"
say "----------------------------------------------------------------"
echo "$PK" | grep -q -E '^PROOF S763 \(the kit\): salt duty n=' || { PLACED=2; stop_unlocked "!! [4/7] the proof by the kit's files: $PK - nothing installed (kept in $SCR)"; }
echo "$PL" | grep -q -E '^PROOF S763 \(the live files\): salt duty n=' || { PLACED=2; stop_unlocked "!! [4/7] the proof by the live files: $PL - nothing installed (kept in $SCR)"; }
BK="$(echo "$PK" | sed -E 's/^PROOF S763 \(the kit\): //; s/ · after a re-receipt now: .*$//')"; BL="$(echo "$PL" | sed -E 's/^PROOF S763 \(the live files\): //; s/ · after a re-receipt now: .*$//')"
AGK="$(grep -E '^AGAIN-KEY ' "$SCR/proof_kit.txt" | head -1)"
if [ "$AGK" = "AGAIN-KEY absent" ]; then
  [ "$BK" = "$BL" ] || { PLACED=2; stop_unlocked "!! [4/7] the kit's files read today differently from the live files (above) - with no re-receipt yet they must agree; nothing installed (kept in $SCR)"; }
else
  say "      (a salt re-receipt is already recorded -- ${AGK#AGAIN-KEY } -- so the kit's files may read the salt duty differently from the live ones: shown, not compared)"
fi
AK="$(echo "$PK" | sed -E 's/^.* · after a re-receipt now: //')"
case "$AK" in "n=0"|"no verified salt list on this box") ;; *) PLACED=2; stop_unlocked "!! [4/7] a made-up re-receipt in the copy did not clear the salt duty by the kit's files ($AK) - nothing installed (kept in $SCR)";; esac
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/7] finance healthz $f0 before the install - nothing installed"
say "[4/7] the proof: the kit's files and the live files read today the same ($BL); a made-up re-receipt in the copy -> the kit: $AK; finance healthy"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk, the control, the earlier walk and the proof green; NOTHING written"; exit 0; fi

for f in $FILES; do { \cp -p "$ROOT/$f" "$(bak "$f")" && [ "$(m5 "$(bak "$f")")" = "${FROM[$f]}" ]; } || stop_unlocked "!! [5/7] could not write the backup $(bak "$f") - nothing placed"; done
for f in $FILES; do { cat "$SCR/built/$f" > "$(stg "$f")" && [ "$(m5 "$(stg "$f")")" = "${TO[$f]}" ]; } || stop_unlocked "!! [5/7] could not stage $f - nothing placed"; done
for f in $FILES; do chmod --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; chown --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; done
OLDPIDS="$(pids_of "$FSVC" | tr '\n' ' ')"
PLACED=1
for f in $FILES; do mv -f "$(stg "$f")" "$ROOT/$f" || restore "the rename of $f"; done
for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || restore "read back of $f"; done
find "$ROOT/finance" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[5/7] placed and read back: marg_door ${TO[finance/marg_door.py]:0:8} · amir_day ${TO[finance/amir_day.py]:0:8} · reports_tile ${TO[finance/reports_tile.py]:0:8}"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(fdoor); case "$c2" in 401|403) ;; *) restore "the Marg door answered a re-receipt without the key with $c2 (expected 401)";; esac
NEWPIDS="$(pids_of "$FSVC" | tr '\n' ' ')"
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager -o short 2>/dev/null)"
  for p in $OLDPIDS; do JL="$(printf '%s\n' "$JL" | grep -v -E "\[$p\]:")"; done
  JR="$(printf '%s\n' "$JL" | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError|NOT mounted')"
  [ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'Traceback|Error|NOT mounted' | head -6 | sed 's/^/         /'; restore "journal: $JR error line(s) from the new master ($NEWPIDS) since the restart"; }
fi
say "[6/7] $FSVC restarted at $(TZ=Asia/Kolkata date '+%H:%M IST'): healthz $c1; a re-receipt without the key -> $c2; journal clean (new PIDs: $NEWPIDS)"
rm -rf "$SCR/placed" "$SCR/cplaced"; mkroot "$SCR/placed" && codedir "$SCR/cplaced" "$SCR/placed" to || restore "could not copy the placed files for the walk"
R=$(walk "$SCR/cplaced" "$SCR/placed" "" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 7 ] && R="rehearsal: a forced red at [7/7]"
[ "$R" = "$GREEN" ] || restore "the walk on the placed files: $R"
say "[7/7] the walk on the placed files: $R"
release_lock
say "undo (one line): $(for f in $FILES; do printf '\\cp -p %s %s && ' "$(bak "$f")" "$ROOT/$f"; done)$SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE (the server half). Next: the chat places the medical PC's marg_watch.py through Drive ToMedical\\_kit."
exit 0
