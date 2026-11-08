#!/bin/bash
# =============================================================================
#  install_S750_MONTH_END.sh · kit S750 (08-Nov-2026, Sanjeevni session 406) · D849 / F-1175 · the plan S406_KIT4_MONTH_END_PLAN.md, the mock
#  https://claude.ai/artifact/G7giUj7RrbiJAv2w8kHwvb approved 09:45 IST with the owner's words: 'summary', not 'statement'; the dealer ledger.
#  THE MONTH END: row 7 of the step view (each dealer's month summary against Marg, returns included; the owner's answers: ask / carry /
#  accept / gives no summary / ask reception), row 8 and the one lock gate waiting for the dealers too, the payment sheet's 'Dealer's summary'
#  column (Payable follows the dealer's figure when it agrees or is accepted), the dealer ledger (/finance/purchase/page/ledger), Amir's card
#  for an accepted bill, reception's 'hisaab scan karo' line; and the Scan App's two files (PLANNED, board/_numbers v1066): the intake's
#  'Dealer ka mahine ka hisaab (summary) hai' button (kind 'Summary', doc_kind 'summary') and the reader's summary prompt (read_summary).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s750kit && cp -rp /root/deploy/repo/deploy_kits/S750_MONTH_END /tmp/s750kit && bash /tmp/s750kit/install_S750_MONTH_END.sh
#  (DRY=1 before bash: every gate, both walks, both controls, the earlier kits' walks and the proof on this box's databases by the LIVE files
#   and by the kit's -- printed whole; NOTHING written. No live bill or record is re-paired or re-stated by this kit: new tables only.)
#   /root/finance/scan_register.py  5b066249 -> TO   /root/finance/purchase_app.py    0d49c249 -> TO   /root/finance/amir_day.py  98c40f51 -> TO
#   /root/finance/porders_s454.py   37c4f3bf -> TO   /root/assetapp/asset_register.py 16a2abea -> TO   /root/assetapp/claude_reader.py 1277e80d -> TO
#  Gates: SUMS, KIT_ID, the window, the build lock, the six live pins, the rebuild to the TO pins (both pythons compile), walk_s750 green on the
#  rebuilt finance files, its CONTROL on the live files (every S750 check red), walk_s750_app green on the rebuilt Scan App files and its
#  control, the earlier kits' walks (S749, S740, S738, S736, S726, S711) on the rebuilt files -- no red beyond the live files' own plus S749's
#  two counting lines (the dealers now count in the strip) --, the proof by both. After placing: both services restarted, health, the pages and
#  the new doors refuse a stranger, the journal (new PIDs only, F-1135), the walk again on the placed files, then [8/8] the two tables and the
#  proof by the placed files.
# =============================================================================
set -u
KIT="S750_MONTH_END"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
ADB="${ADB:-$ROOT/assetapp/assets.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
AST_PORT="${AST_PORT:-8030}"; ASVC="${ASVC:-assetapp}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
FILES="finance/scan_register.py finance/purchase_app.py finance/amir_day.py finance/porders_s454.py assetapp/asset_register.py assetapp/claude_reader.py"
declare -A FROM=( [finance/scan_register.py]=5b0662498992439075e6adfb2d834daa [finance/purchase_app.py]=0d49c2490d8ca05e6043192987f71c03
                  [finance/amir_day.py]=98c40f51d5b9ed1500baef26d2941d5c [finance/porders_s454.py]=37c4f3bf7589fde41617d4c103cd01ee
                  [assetapp/asset_register.py]=16a2abea4d716444bd3a9bd9540a1269 [assetapp/claude_reader.py]=1277e80de5c141cf3f5f7c97b9434cb9 )
declare -A TO
for f in $FILES; do TO[$f]="$(awk -v f="$f" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s750_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
SCHEMA="$ROOT/finance/purchase_schema.sql"
GREEN="walk_s750: 0 check(s) failed (0 of them S750 checks)"
CONTROL="walk_s750: 82 check(s) failed (82 of them S750 checks)"
GREEN_APP="walk_s750_app: 0 check(s) failed (0 of them S750 checks)"
CONTROL_APP="walk_s750_app: 15 check(s) failed (15 of them S750 checks)"
# the earlier kits' walks: a red on the rebuilt files is allowed only when the LIVE files show it too, or it is one of these (the dealers now count in the strip)
ALLOW749="$(printf '%s\n' "  FAIL [S749] 3 the strip: 'NEFT on hold · 13 open'" "  FAIL [S749] 4 ... the step view: row 3 empty, row 1 carries Ravi 'confirmed by you' with Undo, the strip 7 open")"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S750_${FROM[$1]:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s750"; }
fhealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
ahealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$AST_PORT$1"; fi; }
fhz() { fhealth /finance/healthz; }
ahz() { ahealth /healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { for f in $FILES; do rm -f "$(stg "$f")"; done; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s750.py" "$1" "$SCHEMA" "$2" 2>&1); }
walkapp() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$APY" -W ignore -B "$KDIR/walk_s750_app.py" --live "$ROOT/assetapp" --files "$1" 2>&1); }
walkk() { local w="$1" d="$2"; (cd /tmp && case "$w" in
  walk_s726) S726_SCHEMA_DIR="$ROOT/finance" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/$w.py" "$d" 2>&1;;
  walk_s711) PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/$w.py" "$d" "$SCHEMA" 2>&1;;
  walk_s749) PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/$w.py" "$d" "$SCHEMA" "$SCR/new/shared" "$ROOT/portal/portal.py" 2>&1;;
  *) PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/$w.py" "$d" "$SCHEMA" "$SCR/new/shared" 2>&1;; esac); }
reds() { grep -E '^  (FAIL|RED) ' | sort; }
proof() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -W ignore -B "$KDIR/proof_s750.py" "$1" "$SCR/new/shared" "$DB" "$ADB" --brief 2>&1); }
seed() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/seed_s750.py" "$1" "$SCR/new/shared" "$DB" $2 2>&1); }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the files back"
  PLACED=2
  for f in $FILES; do \cp -p "$(bak "$f")" "$ROOT/$f" || say "   !! could not put back $ROOT/$f"; rm -f "$(stg "$f")"; done
  find "$ROOT/finance" "$ROOT/assetapp" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  "$SYSTEMCTL" restart "$FSVC" || true; "$SYSTEMCTL" restart "$ASVC" || true
  for f in $FILES; do say "   $ROOT/$f $(m5 "$ROOT/$f" | cut -c1-8) (expected ${FROM[$f]:0:8})"; done
  say "   finance healthz $(wait200 fhz) · the scan app $(wait200 ahz). Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }
pids_of() { local m; m="$("$SYSTEMCTL" show -p MainPID --value "$1" 2>/dev/null)"; [ -n "$m" ] && [ "$m" != 0 ] && { echo "$m"; pgrep -P "$m" 2>/dev/null; }; }
# an earlier kit's walk on the rebuilt files: its reds must be the live files' own reds plus the allowed counting changes, nothing else
earlier() {
  local w="$1" allow="$2" new old extra outn outo
  outn="$(walkk "$w" "$SCR/new/finance")"; outo="$(walkk "$w" "$SCR/old/finance")"
  printf '%s\n' "$outn" | tail -1 | grep -q -E '^(walk_s7[0-9]{2}: [0-9]+ check|WALK S711: [0-9]+ ok)' || { printf '%s\n' "$outn" | tail -4 | sed 's/^/         /'; echo "the walk did not reach its own last line on the rebuilt files"; return 1; }
  printf '%s\n' "$outo" | tail -1 | grep -q -E '^(walk_s7[0-9]{2}: [0-9]+ check|WALK S711: [0-9]+ ok)' || { printf '%s\n' "$outo" | tail -4 | sed 's/^/         /'; echo "the walk did not reach its own last line on the live files"; return 1; }
  new="$(printf '%s\n' "$outn" | reds)"; old="$(printf '%s\n' "$outo" | reds)"
  extra="$(comm -13 <(printf '%s\n' "$old" | sort) <(printf '%s\n' "$new" | sort) | sort)"
  extra="$(comm -23 <(printf '%s\n' "$extra") <(printf '%s\n' "$allow" | sort))"
  if [ -n "$extra" ]; then printf '%s\n' "$extra" | head -8 | sed 's/^/         /'; return 1; fi
  echo "$(printf '%s\n' "$new" | grep -c . ) red(s), of which $(printf '%s\n' "$old" | grep -c .) the live files' own"
}

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout pgrep comm sort; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { [ "$ROOT" != "/root" ] && [ "${SKIP_WINDOW:-0}" = 1 ]; } || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/8] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $FILES; do [ -n "${TO[$f]}" ] || { say "!! [1/8] TO_PINS.md5 does not name $f - nothing installed"; exit 1; }; done
for f in $FILES; do [ -f "$ROOT/$f" ] || { say "!! [1/8] $ROOT/$f is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$SCHEMA" ] && [ -f "$ROOT/shared/scan_quality.py" ] && [ -f "$ROOT/finance/item_check.py" ] || { say "!! [1/8] $DB, $ADB, purchase_schema.sql, scan_quality.py or item_check.py is missing - nothing installed"; exit 1; }
mkdir -p "$SCR/built/finance" "$SCR/built/assetapp" "$SCR/pyc" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
ALL=1; for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- ALREADY INSTALLED: the six files are the kit's. Nothing written. finance healthz $(fhz) · the scan app $(ahz)"; exit 0; }
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
for f in $FILES; do C=$(m5 "$ROOT/$f"); [ "$C" = "${FROM[$f]}" ] || stop_unlocked "!! [2/8] $ROOT/$f is ${C:0:8}, expected ${FROM[$f]:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
say "[2/8] live pins exact: scan_register ${FROM[finance/scan_register.py]:0:8} · purchase_app ${FROM[finance/purchase_app.py]:0:8} · amir_day ${FROM[finance/amir_day.py]:0:8} · porders_s454 ${FROM[finance/porders_s454.py]:0:8} · asset_register ${FROM[assetapp/asset_register.py]:0:8} · claude_reader ${FROM[assetapp/claude_reader.py]:0:8}"

"$APY" -B make_s750.py "$ROOT/finance" "$ROOT/assetapp" "$SCR/built" "$KDIR" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/8] the builder refused a live file - nothing installed"; }
for f in $FILES; do
  [ "$(m5 "$SCR/built/$f")" = "${TO[$f]}" ] || stop_unlocked "!! [3/8] rebuilt, $f is $(m5 "$SCR/built/$f" | cut -c1-8), not ${TO[$f]:0:8} - nothing installed"
  for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/$f" || stop_unlocked "!! [3/8] $f does not compile on $py - nothing installed"; done
done
mkdir -p "$SCR/new/finance" "$SCR/new/shared" "$SCR/old/finance"
for f in "$ROOT"/finance/*.py "$ROOT"/finance/*.json "$ROOT"/finance/*.sql "$ROOT"/finance/*.html; do [ -f "$f" ] && cp -p "$f" "$SCR/new/finance/" && cp -p "$f" "$SCR/old/finance/"; done
for f in "$ROOT"/shared/*.py; do [ -f "$f" ] && cp -p "$f" "$SCR/new/shared/"; done
for f in $FILES; do case "$f" in finance/*) cp -p "$SCR/built/$f" "$SCR/new/finance/$(basename "$f")";; esac; done
say "[3/8] rebuilt here from this box's live bytes: the six files at their TO pins; each compiles under both pythons"

R=$(walk "$SCR/new/finance" "$SCR/new/shared" | tail -1)
[ "$R" = "$GREEN" ] || { walk "$SCR/new/finance" "$SCR/new/shared" | grep -E 'FAIL|Error|raised' | head -12 | sed 's/^/         /'; PLACED=2; stop_unlocked "!! [4/8] the walk on the rebuilt files is not green ($R) - nothing installed (kept in $SCR)"; }
R0=$(walk "$SCR/old/finance" "$SCR/new/shared" | tail -1)
[ "$R0" = "$CONTROL" ] || { PLACED=2; stop_unlocked "!! [4/8] the control on the live files is not as expected ($R0; expected $CONTROL) - nothing installed (kept in $SCR)"; }
RA=$(walkapp "$SCR/built/assetapp" | tail -1)
[ "$RA" = "$GREEN_APP" ] || { walkapp "$SCR/built/assetapp" | grep -E 'FAIL|Error|raised' | head -12 | sed 's/^/         /'; PLACED=2; stop_unlocked "!! [4/8] the Scan App walk on the rebuilt files is not green ($RA) - nothing installed (kept in $SCR)"; }
RA0=$(walkapp "$ROOT/assetapp" | tail -1)
[ "$RA0" = "$CONTROL_APP" ] || { PLACED=2; stop_unlocked "!! [4/8] the Scan App control on the live files is not as expected ($RA0; expected $CONTROL_APP) - nothing installed (kept in $SCR)"; }
# the earlier kits' walks (REHEARSE_EARLIER names a subset for the rehearsal on a made-up root only; on the box every one runs)
EARLIER_ALL="walk_s749 walk_s740 walk_s738 walk_s736 walk_s726 walk_s711"
if [ "$ROOT" != "/root" ]; then EARLIER="${REHEARSE_EARLIER:-$EARLIER_ALL}"; else EARLIER="$EARLIER_ALL"; fi
ESAY=""
for w in $EARLIER; do
  case "$w" in walk_s749) allow="$ALLOW749";; *) allow="";; esac
  E="$(earlier "$w" "$allow")" || { PLACED=2; stop_unlocked "!! [4/8] $w on the rebuilt files shows a red the live files do not (above) - nothing installed (kept in $SCR)"; }
  ESAY="$ESAY; $w: $E"
done
say "[4/8] the walk: $R; the control: $R0; the Scan App walk: $RA; its control: $RA0$ESAY"
proof "$SCR/old/finance" > "$SCR/proof_live.txt"; proof "$SCR/new/finance" > "$SCR/proof_kit.txt"
PL=$(tail -1 "$SCR/proof_live.txt"); PK=$(tail -1 "$SCR/proof_kit.txt")
say "---------------------------------------------------------------- the proof by the KIT's files (read only) -- paste all of it to Claude"
sed 's/^/   /' "$SCR/proof_kit.txt"
say "---------------------------------------------------------------- the live files said"
sed 's/^/   /' "$SCR/proof_live.txt"
say "----------------------------------------------------------------"
echo "$PK" | grep -q -E '^PROOF S750: [0-9]+ counted month' || { PLACED=2; stop_unlocked "!! [4/8] the proof on this box's databases: $PK - nothing installed (kept in $SCR)"; }
echo "$PK" | grep -q -E 'payable changed 0 ' || { PLACED=2; stop_unlocked "!! [4/8] the proof says the kit would change a payable before any answer of yours: $PK - nothing installed (kept in $SCR)"; }
echo "$PL" | grep -q -E '^PROOF S750: [0-9]+ counted month' || { PLACED=2; stop_unlocked "!! [4/8] the proof by the live files: $PL - nothing installed (kept in $SCR)"; }
SD="$(seed "$SCR/new/finance" --dry | tail -1)"
echo "$SD" | grep -q -E '^SEED S750: DRY' || { PLACED=2; stop_unlocked "!! [4/8] the seed: $SD - nothing installed (kept in $SCR)"; }
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/8] finance healthz $f0 before the install - nothing installed"
a0=$(ahz); [ "$a0" = 200 ] || stop_unlocked "!! [4/8] the scan app answered $a0 before the install - nothing installed"
say "[4/8] live: $PL"
say "      kit:  $PK (both databases opened read-only); $SD; finance and the scan app healthy"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, both walks, both controls, the earlier kits' walks and the proof green; NOTHING written"; exit 0; fi

for f in $FILES; do { \cp -p "$ROOT/$f" "$(bak "$f")" && [ "$(m5 "$(bak "$f")")" = "${FROM[$f]}" ]; } || stop_unlocked "!! [5/8] could not write the backup $(bak "$f") - nothing placed"; done
for f in $FILES; do { cat "$SCR/built/$f" > "$(stg "$f")" && [ "$(m5 "$(stg "$f")")" = "${TO[$f]}" ]; } || stop_unlocked "!! [5/8] could not stage $f - nothing placed"; done
for f in $FILES; do chmod --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; chown --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; done
OLDPIDS="$(pids_of "$FSVC" | tr '\n' ' ') $(pids_of "$ASVC" | tr '\n' ' ')"
PLACED=1
for f in $FILES; do mv -f "$(stg "$f")" "$ROOT/$f" || restore "the rename of $f"; done
for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || restore "read back of $f"; done
find "$ROOT/finance" "$ROOT/assetapp" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[5/8] placed and read back: scan_register ${TO[finance/scan_register.py]:0:8} · purchase_app ${TO[finance/purchase_app.py]:0:8} · amir_day ${TO[finance/amir_day.py]:0:8} · porders_s454 ${TO[finance/porders_s454.py]:0:8} · asset_register ${TO[assetapp/asset_register.py]:0:8} · claude_reader ${TO[assetapp/claude_reader.py]:0:8}"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
"$SYSTEMCTL" restart "$ASVC" || restore "restart $ASVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c0=$(wait200 ahz); [ "$c0" = 200 ] || restore "the scan app's healthz answered $c0"
c2=$(fhealth /finance/amir/step/1); case "$c2" in 302|401|403) ;; *) restore "Amir's page answered $c2 without a login (expected 302, 401 or 403)";; esac
c3=$(fhealth /finance/purchase/page/check); case "$c3" in 302|401|403) ;; *) restore "the step view answered $c3 without a login (expected 302, 401 or 403)";; esac
c4=$(fhealth /finance/purchase/page/ledger); case "$c4" in 302|401|403) ;; *) restore "the ledger answered $c4 without a login (expected 302, 401 or 403)";; esac
c5=$(fhealth /finance/purchase/page/pay); case "$c5" in 302|401|403) ;; *) restore "the payment sheet answered $c5 without a login (expected 302, 401 or 403)";; esac
c6=$(fhealth /finance/porders/s454/billkaam); case "$c6" in 302|401|403) ;; *) restore "Aaj ka bill kaam answered $c6 without a login (expected 302, 401 or 403)";; esac
c7=$(ahealth /intake); case "$c7" in 302|401|403) ;; *) restore "the scan app's intake answered $c7 without a login (expected 302, 401 or 403)";; esac
c8=$(curl -s -o /dev/null -m 8 -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{}' "http://127.0.0.1:$FIN_PORT/finance/purchase/api/s750/answer" 2>/dev/null || echo 000); [ -n "${HEALTH_CMD:-}" ] && c8=403
case "$c8" in 302|401|403|405) ;; *) restore "the answer door answered $c8 without a login (expected 302, 401 or 403)";; esac
NEWPIDS="$(pids_of "$FSVC" | tr '\n' ' ') $(pids_of "$ASVC" | tr '\n' ' ')"
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JL="$("$JOURNALCTL" -u "$FSVC" -u "$ASVC" --since "$T0" --no-pager -o short 2>/dev/null)"
  for p in $OLDPIDS; do JL="$(printf '%s\n' "$JL" | grep -v -E "\[$p\]:")"; done
  JR="$(printf '%s\n' "$JL" | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError|Logging error')"
  [ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'Traceback|Error' | head -6 | sed 's/^/         /'; restore "journal: $JR error line(s) from the new masters ($NEWPIDS) since the restart"; }
fi
say "[6/8] $FSVC and $ASVC restarted at $(TZ=Asia/Kolkata date '+%H:%M IST'): finance healthz $c1, the scan app $c0; without a login Amir's page $c2, the step view $c3, the ledger $c4, the payment sheet $c5, Aaj ka bill kaam $c6, the intake $c7, the answer door $c8; journal clean"
mkdir -p "$SCR/placed/finance"
for f in "$ROOT"/finance/*.py "$ROOT"/finance/*.json "$ROOT"/finance/*.sql "$ROOT"/finance/*.html; do [ -f "$f" ] && cp -p "$f" "$SCR/placed/finance/"; done
R=$(walk "$SCR/placed/finance" "$SCR/new/shared" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 7 ] && R="rehearsal: a forced red at [7/8]"
[ "$R" = "$GREEN" ] || restore "the walk on the placed files: $R"
say "[7/8] the walk on the placed files: $R"
# [8/8] the two tables (the owner's answers), then the proof by the placed files
S8="$(seed "$SCR/placed/finance" "" | tail -1)"
case "$S8" in "SEED S750: tables present: s750_answer, s750_dealer_of") ;; *) restore "the seed: $S8";; esac
P8=$(proof "$SCR/placed/finance" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 8 ] && P8="rehearsal: a forced red at [8/8]"
echo "$P8" | grep -q -E '^PROOF S750: [0-9]+ counted month' || restore "the proof by the placed files: $P8"
say "[8/8] $S8; by the placed files: $P8 -- row 7, the lock, the sheet's column, the ledgers, Amir's card, reception's line and the intake's button read it at their next load"
release_lock
say "undo (one line): $(for f in $FILES; do printf '\\cp -p %s %s && ' "$(bak "$f")" "$ROOT/$f"; done)$SYSTEMCTL restart $FSVC && $SYSTEMCTL restart $ASVC"
say ""
say "$KIT: DONE. Your purchase check: https://followup.dr-manoj.in/finance/purchase/page/check · the dealer ledgers: https://followup.dr-manoj.in/finance/purchase/page/ledger"
exit 0
