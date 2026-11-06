#!/bin/bash
# =============================================================================
#  install_S738_AMIR_CORRECTIONS.sh · kit S738 (06-Nov-2026, Sanjeevni session 396) · D839 D840: Amir's correction list on his Marg sudhar
#  card (the paper reads less / more -- with the lines Marg lacks when they add up -- / entered twice; the bill date; Kaagaz dekhiye),
#  proved only by his own export; the owner's step view: the bill date, the scan and a folded in-page scan viewer on every scanned line,
#  row 3 since when / proved, a back-to-top button, PC first. The owner's OK 21:28 IST on the mock.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s738kit && cp -rp /root/deploy/repo/deploy_kits/S738_AMIR_CORRECTIONS /tmp/s738kit && bash /tmp/s738kit/install_S738_AMIR_CORRECTIONS.sh
#  (DRY=1 before bash: every gate, the walks, the control and the proof -- printed whole; nothing written.)
#   /root/finance/scan_register.py  4d8432ea -> TO
#   /root/finance/amir_day.py       10a5f9c4 -> TO
#   /root/finance/purchase_app.py   5fde52aa -> TO
#  Gates: SUMS, KIT_ID, the window, the build lock, the live pins, the rebuild to the TO pins (both pythons compile), the walk on the
#  rebuilt files, the control on the live files, S736's / S711's / S726's walks on the rebuilt files (each changed check named), the proof
#  on this box's own databases (read only). After placing: restart, health, Amir's page, the step view and the scan door refuse a stranger,
#  the journal (new PIDs only, F-1135), the walk again, then [8/8] the proof again on the placed files.
# =============================================================================
set -u
KIT="S738_AMIR_CORRECTIONS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
ADB="${ADB:-$ROOT/assetapp/assets.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
EDIT="finance/scan_register.py finance/amir_day.py finance/purchase_app.py"
FILES="$EDIT"
declare -A FROM=( [finance/scan_register.py]=4d8432ea94822692c15e5e840c8d08d7 [finance/amir_day.py]=10a5f9c4793f170c040e5e71b516503c [finance/purchase_app.py]=5fde52aafbb5367f329fb3696082f784 )
declare -A TO
for f in $FILES; do TO[$f]="$(awk -v f="$f" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s738_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
SCHEMA="$ROOT/finance/purchase_schema.sql"
GREEN="walk_s738: 0 check(s) failed (0 of them S738 checks)"
CONTROL="walk_s738: 40 check(s) failed (40 of them S738 checks)"
G736="walk_s736: 1 check(s) failed (1 of them S736 checks)"
F736="  FAIL [S736] 6 ... the step view's Differences row carries Deepam 641 with Amir's name"
G711="WALK S711: 38 ok, 0 red"
G726="walk_s726: 5 check(s) failed (5 of them S726 checks)"
F726="$(printf '%s\n' "  FAIL [S726] 6 seven rows, in order, each a <details>" "  FAIL [S726] 6 row 3 Differences → Amir: 'NANDI DRUG HOUSE 555 ₹10'" "  FAIL [S726] 6 row 4 Rounding: Shivaaz and Gunina" "  FAIL [S726] 6 row 5 You & Shavez: Deepam's second look" "  FAIL [S726] 6 phone-first: no fixed width wider than 390 px")"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S738_${FROM[$1]:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s738"; }
fhealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { for f in $FILES; do rm -f "$(stg "$f")"; done; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s738.py" "$1" "$SCHEMA" "$2" 2>&1); }
walk736() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s736.py" "$1" "$SCHEMA" "$2" 2>&1); }
walk711() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s711.py" "$1" "$SCHEMA" 2>&1); }
walk726() { (cd /tmp && S726_SCHEMA_DIR="$ROOT/finance" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s726.py" "$1" 2>&1); }
proof() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -W ignore -B "$KDIR/proof_s738.py" "$1" "$SCR/new/shared" "$DB" "$ADB" 2>&1); }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the files back"
  PLACED=2
  for f in $EDIT; do \cp -p "$(bak "$f")" "$ROOT/$f" || say "   !! could not put back $ROOT/$f"; rm -f "$(stg "$f")"; done
  find "$ROOT/finance" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  "$SYSTEMCTL" restart "$FSVC" || true
  for f in $EDIT; do say "   $ROOT/$f $(m5 "$ROOT/$f" | cut -c1-8) (expected ${FROM[$f]:0:8})"; done
  say "   finance healthz $(wait200 fhz). Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }
pids_of() { local m; m="$("$SYSTEMCTL" show -p MainPID --value "$FSVC" 2>/dev/null)"; [ -n "$m" ] && [ "$m" != 0 ] && { echo "$m"; pgrep -P "$m" 2>/dev/null; }; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout pgrep; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/8] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $FILES; do [ -n "${TO[$f]}" ] || { say "!! [1/8] TO_PINS.md5 does not name $f - nothing installed"; exit 1; }; done
for f in $EDIT; do [ -f "$ROOT/$f" ] || { say "!! [1/8] $ROOT/$f is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$SCHEMA" ] && [ -f "$ROOT/shared/scan_quality.py" ] && [ -f "$ROOT/finance/item_check.py" ] || { say "!! [1/8] $DB, $ADB, purchase_schema.sql or scan_quality.py is missing - nothing installed"; exit 1; }
mkdir -p "$SCR/built/finance" "$SCR/pyc" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
ALL=1; for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- ALREADY INSTALLED: the three files are the kit's. Nothing written. finance healthz $(fhz)"; exit 0; }
if [ "${DRY:-0}" = 1 ]; then
  say "[1/8] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/8] kit gates green; the build lock taken $(TZ=Asia/Kolkata date '+%d-%m %H:%M IST') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  TOOK_LOCK=1; say "[1/8] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."
  exit 3
fi
for f in $EDIT; do C=$(m5 "$ROOT/$f"); [ "$C" = "${FROM[$f]}" ] || stop_unlocked "!! [2/8] $ROOT/$f is ${C:0:8}, expected ${FROM[$f]:0:8} - it changed after this kit was built: STOP, nothing installed"; done
say "[2/8] live pins exact: scan_register ${FROM[finance/scan_register.py]:0:8} · amir_day ${FROM[finance/amir_day.py]:0:8} · purchase_app ${FROM[finance/purchase_app.py]:0:8}"

"$APY" -B make_s738.py "$ROOT/finance" "$SCR/built/finance" "$KDIR" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/8] the builder refused a live file - nothing installed"; }
for f in $FILES; do
  [ "$(m5 "$SCR/built/$f")" = "${TO[$f]}" ] || stop_unlocked "!! [3/8] rebuilt, $f is $(m5 "$SCR/built/$f" | cut -c1-8), not ${TO[$f]:0:8} - nothing installed"
  for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/$f" || stop_unlocked "!! [3/8] $f does not compile on $py - nothing installed"; done
done
mkdir -p "$SCR/new/finance" "$SCR/new/shared" "$SCR/old/finance"
for f in "$ROOT"/finance/*.py "$ROOT"/finance/*.json "$ROOT"/finance/*.sql; do [ -f "$f" ] && cp -p "$f" "$SCR/new/finance/" && cp -p "$f" "$SCR/old/finance/"; done
for f in "$ROOT"/shared/*.py; do [ -f "$f" ] && cp -p "$f" "$SCR/new/shared/"; done
for f in $FILES; do cp -p "$SCR/built/$f" "$SCR/new/finance/$(basename "$f")"; done
say "[3/8] rebuilt here from this box's live bytes: the three files at their TO pins; each compiles under both pythons"

R=$(walk "$SCR/new/finance" "$SCR/new/shared" | tail -1)
[ "$R" = "$GREEN" ] || { walk "$SCR/new/finance" "$SCR/new/shared" | grep -E 'FAIL|Error|raised' | head -12 | sed 's/^/         /'; PLACED=2; stop_unlocked "!! [4/8] the walk on the rebuilt files is not green ($R) - nothing installed (kept in $SCR)"; }
R0=$(walk "$SCR/old/finance" "$SCR/new/shared" | tail -1)
[ "$R0" = "$CONTROL" ] || { PLACED=2; stop_unlocked "!! [4/8] the control on the live files is not as expected ($R0) - nothing installed (kept in $SCR)"; }
W736="$(walk736 "$SCR/new/finance" "$SCR/new/shared")"
R3=$(printf '%s\n' "$W736" | tail -1); F3=$(printf '%s\n' "$W736" | grep -E '^  FAIL ')
[ "$R3" = "$G736" ] && [ "$F3" = "$F736" ] || { printf '%s\n' "$F3" | head -6 | sed 's/^/         /'; PLACED=2; stop_unlocked "!! [4/8] S736's walk on the rebuilt files: $R3 (expected $G736, its one red the Deepam line drawn in columns) - nothing installed (kept in $SCR)"; }
R1=$(walk711 "$SCR/new/finance" | tail -1)
[ "$R1" = "$G711" ] || { PLACED=2; stop_unlocked "!! [4/8] S711's walk on the rebuilt files: $R1 (expected $G711) - nothing installed (kept in $SCR)"; }
W726="$(walk726 "$SCR/new/finance")"
R2=$(printf '%s\n' "$W726" | tail -1); F2=$(printf '%s\n' "$W726" | grep -E '^  FAIL ')
[ "$R2" = "$G726" ] && [ "$F2" = "$F726" ] || { printf '%s\n' "$F2" | head -6 | sed 's/^/         /'; PLACED=2; stop_unlocked "!! [4/8] S726's walk on the rebuilt files: $R2 (expected $G726: its five line-format checks, the lines now drawn in columns) - nothing installed (kept in $SCR)"; }
say "[4/8] the walk: $R; the control on the live files: $R0; S736's walk: $R3; S711's walk: $R1; S726's walk: $R2 (the reds named: the step view's lines now in columns, the owner's ask)"
proof "$SCR/new/finance" > "$SCR/proof.txt"
P=$(tail -1 "$SCR/proof.txt")
say "---------------------------------------------------------------- the proof (read only) -- paste all of it to Claude"
sed 's/^/   /' "$SCR/proof.txt"
say "----------------------------------------------------------------"
echo "$P" | grep -q -E '^PROOF S738: [0-9]+ correction\(s\) for Amir ' || { PLACED=2; stop_unlocked "!! [4/8] the proof on this box's databases: $P - nothing installed (kept in $SCR)"; }
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/8] finance healthz $f0 before the install - nothing installed"
say "[4/8] $P (both databases opened read-only); finance healthy"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks, the control and the proof green; NOTHING written"; exit 0; fi

for f in $EDIT; do { \cp -p "$ROOT/$f" "$(bak "$f")" && [ "$(m5 "$(bak "$f")")" = "${FROM[$f]}" ]; } || stop_unlocked "!! [5/8] could not write the backup $(bak "$f") - nothing placed"; done
for f in $FILES; do { cat "$SCR/built/$f" > "$(stg "$f")" && [ "$(m5 "$(stg "$f")")" = "${TO[$f]}" ]; } || stop_unlocked "!! [5/8] could not stage $f - nothing placed"; done
for f in $EDIT; do chmod --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; chown --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; done
OLDPIDS="$(pids_of | tr '\n' ' ')"
PLACED=1
for f in $FILES; do mv -f "$(stg "$f")" "$ROOT/$f" || restore "the rename of $f"; done
for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || restore "read back of $f"; done
find "$ROOT/finance" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[5/8] placed and read back: scan_register ${TO[finance/scan_register.py]:0:8} · amir_day ${TO[finance/amir_day.py]:0:8} · purchase_app ${TO[finance/purchase_app.py]:0:8} (backups *.bak_S738_*)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(fhealth /finance/amir/step/1); case "$c2" in 302|401|403) ;; *) restore "Amir's page answered $c2 without a login (expected 302, 401 or 403)";; esac
c4=$(fhealth /finance/purchase/api/s738/scan/1); case "$c4" in 302|401|403) ;; *) restore "the scan door answered $c4 without a login (expected 302, 401 or 403)";; esac
c3=$(fhealth /finance/purchase/page/check); case "$c3" in 302|401|403) ;; *) restore "the step view answered $c3 without a login (expected 302, 401 or 403)";; esac
NEWPIDS="$(pids_of | tr '\n' ' ')"
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  # F-1135: the stopping master's shutdown noise is not this install's fault -- count only lines of PIDs that are not the old ones
  JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager -o short 2>/dev/null)"
  for p in $OLDPIDS; do JL="$(printf '%s\n' "$JL" | grep -v -E "\[$p\]:")"; done
  JR="$(printf '%s\n' "$JL" | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError|Logging error')"
  [ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'Traceback|Error' | head -6 | sed 's/^/         /'; restore "journal: $JR error line(s) from the new master ($NEWPIDS) since the restart"; }
fi
say "[6/8] $FSVC restarted at $(TZ=Asia/Kolkata date '+%H:%M IST'): healthz $c1; without a login Amir's page $c2, the step view $c3, the scan door $c4; journal clean (old PIDs $OLDPIDS left out, F-1135)"
mkdir -p "$SCR/placed/finance"
for f in "$ROOT"/finance/*.py "$ROOT"/finance/*.json "$ROOT"/finance/*.sql; do [ -f "$f" ] && cp -p "$f" "$SCR/placed/finance/"; done
R=$(walk "$SCR/placed/finance" "$SCR/new/shared" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 7 ] && R="rehearsal: a forced red at [7/8]"
[ "$R" = "$GREEN" ] || restore "the walk on the placed files: $R"
say "[7/8] the walk on the placed files: $R"
# [8/8] the list as Amir will see it, by the placed files (read only)
P8=$(proof "$SCR/placed/finance" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 8 ] && P8="rehearsal: a forced red at [8/8]"
echo "$P8" | grep -q -E '^PROOF S738: [0-9]+ correction\(s\) for Amir ' || restore "the list by the placed files: $P8"
say "[8/8] by the placed files: $P8 -- his card shows it at his next page read"
release_lock
say "undo (one line): $(for f in $EDIT; do printf '\\cp -p %s %s && ' "$(bak "$f")" "$ROOT/$f"; done)$SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. Your step view: https://followup.dr-manoj.in/finance/purchase/page/check"
exit 0
