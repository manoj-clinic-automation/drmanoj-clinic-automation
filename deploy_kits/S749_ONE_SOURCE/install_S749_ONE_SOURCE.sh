#!/bin/bash
# =============================================================================
#  install_S749_ONE_SOURCE.sh · kit S749 (08-Nov-2026, Sanjeevni session 405) · D865 / D866 (the owner 05:13 - 06:04 IST 8-Nov), the plan
#  S403_KIT5_ONE_SOURCE_PLAN.md, the mock https://claude.ai/artifact/BpPSuh8Cm2gPVmkzLDwmXi approved 06:04 with one addition (everything inline).
#  ONE SOURCE, ONE LANGUAGE across the purchase pages: the step view (eight rows, every action inline), the register, the audit page, the hub,
#  the payment sheet (Step 2 by the server; the one lock gate reads the register), Amir's card (round-offs), the console month line and the
#  Marg Purchases tile (the parent's two files, PLANNED on the board). Every difference, Rs 1 included, is Amir's; the "You" state is gone;
#  Ravi Medical Agency is an owner-confirmed supplier (the seed: one setting).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s749kit && cp -rp /root/deploy/repo/deploy_kits/S749_ONE_SOURCE /tmp/s749kit && bash /tmp/s749kit/install_S749_ONE_SOURCE.sh
#  (DRY=1 before bash: every gate, the walks, the control, the proof on this box's databases by the LIVE files and by the kit's, and their
#   difference -- printed whole; NOTHING written. F-1153: that difference is read before the real line.)
#   /root/finance/scan_register.py  12e3c7cb -> TO     /root/finance/purchase_app.py  600c96d7 -> TO     /root/finance/amir_day.py  42a8430b -> TO
#   /root/finance/porders.py        eda0a4c6 -> TO     /root/finance/month_read.py    d5d6f676 -> TO     /root/portal/portal.py     d52261a2 -> TO
#  Gates: SUMS, KIT_ID, the window, the build lock, the six live pins, the rebuild to the TO pins (both pythons compile), the walk on the
#  rebuilt files green, the CONTROL on the live files (every S749 check red), the earlier kits' walks (S740, S738, S736, S726, S711) on the
#  rebuilt files -- each red named, and none beyond the live files' own reds plus the kit's wording changes --, the proof by both. After
#  placing: both services restarted, health, the pages and the new doors refuse a stranger, the journal (new PIDs only, F-1135), the walk
#  again on the placed files, then [8/8] the seed (the setting, only if absent) and the proof by the placed files.
# =============================================================================
set -u
KIT="S749_ONE_SOURCE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
ADB="${ADB:-$ROOT/assetapp/assets.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
POR_PORT="${POR_PORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
FILES="finance/scan_register.py finance/purchase_app.py finance/amir_day.py finance/porders.py finance/month_read.py portal/portal.py"
declare -A FROM=( [finance/scan_register.py]=12e3c7cb057b678084de7c82e414e1bf [finance/purchase_app.py]=600c96d733da7885f98ab6272ac6e8ad
                  [finance/amir_day.py]=42a8430be4a9df19701326d8efb6159a [finance/porders.py]=eda0a4c6d31a011611b6c786f6d49512
                  [finance/month_read.py]=d5d6f676e15f15583229243093a4b2f4 [portal/portal.py]=d52261a25791fb00bfdc6cbfcb44a124 )
declare -A TO
for f in $FILES; do TO[$f]="$(awk -v f="$f" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s749_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
SCHEMA="$ROOT/finance/purchase_schema.sql"
GREEN="walk_s749: 0 check(s) failed (0 of them S749 checks)"
CONTROL="walk_s749: 67 check(s) failed (67 of them S749 checks)"
# the earlier kits' walks: a red on the rebuilt files is allowed only when the LIVE files show it too, or it is one of these (the kit's wording)
ALLOW740="$(printf '%s\n' "  FAIL [S740] 6 November: the NEFT strip holds on its pending return and October's still pending (Nu, R-6800): '3 pending returns'" "  FAIL [S740] 6 row 8 'Returns (pending until the dealer's credit note or revised bill)'")"
ALLOW738="$(printf '%s\n' "  FAIL [S738] 4 row 3 'Differences' says since when it is on Amir's list")"
ALLOW736="$(printf '%s\n' "  FAIL [S736] 6 row 3 is 'Differences' (F-1154)" "  FAIL [S736] 6 row 2 lists the server's asks with the try")"
ALLOW726="$(printf '%s\n' "  FAIL [S726] ... and names the new states" "  FAIL [S726] 3 Gunina 81974 (12,972 / 12,973) verifies and shows the rupee" "  FAIL [S726] 3 Shivaaz 3688 (paper 7,979 / Marg 7,978) verifies and SHOWS the rupee" "  FAIL [S726] 3 a 50-paise difference is shown with its paise" "  FAIL [S726] 6 a month select" "  FAIL [S726] 6 row 1 'Scans paired' n / total" "  FAIL [S726] 6 rows 6 and 7 greyed: 'later' and 'after 1–6'" "  FAIL [S726] the new states have English labels")"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S749_${FROM[$1]:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s749"; }
fhealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
phealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$POR_PORT$1"; fi; }
fhz() { fhealth /finance/healthz; }
phz() { phealth /portal/login; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { for f in $FILES; do rm -f "$(stg "$f")"; done; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s749.py" "$1" "$SCHEMA" "$2" "$3" 2>&1); }
walkk() { local w="$1" d="$2"; (cd /tmp && case "$w" in
  walk_s726) S726_SCHEMA_DIR="$ROOT/finance" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/$w.py" "$d" 2>&1;;
  walk_s711) PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/$w.py" "$d" "$SCHEMA" 2>&1;;
  *) PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/$w.py" "$d" "$SCHEMA" "$SCR/new/shared" 2>&1;; esac); }
reds() { grep -E '^  (FAIL|RED) ' | sort; }
proof() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -W ignore -B "$KDIR/proof_s749.py" "$1" "$SCR/new/shared" "$DB" "$ADB" --brief 2>&1); }
seed() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/seed_s749.py" "$1" "$SCR/new/shared" "$DB" $2 2>&1); }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the files back"
  PLACED=2
  for f in $FILES; do \cp -p "$(bak "$f")" "$ROOT/$f" || say "   !! could not put back $ROOT/$f"; rm -f "$(stg "$f")"; done
  find "$ROOT/finance" "$ROOT/portal" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  "$SYSTEMCTL" restart "$FSVC" || true; "$SYSTEMCTL" restart "$PSVC" || true
  for f in $FILES; do say "   $ROOT/$f $(m5 "$ROOT/$f" | cut -c1-8) (expected ${FROM[$f]:0:8})"; done
  say "   finance healthz $(wait200 fhz) · portal $(wait200 phz). Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }
pids_of() { local m; m="$("$SYSTEMCTL" show -p MainPID --value "$1" 2>/dev/null)"; [ -n "$m" ] && [ "$m" != 0 ] && { echo "$m"; pgrep -P "$m" 2>/dev/null; }; }
# an earlier kit's walk on the rebuilt files: its reds must be the live files' own reds plus the allowed wording changes, nothing else
earlier() {
  local w="$1" allow="$2" new old extra outn outo
  outn="$(walkk "$w" "$SCR/new/finance")"; outo="$(walkk "$w" "$SCR/old/finance")"
  printf '%s\n' "$outn" | tail -1 | grep -q -E '^(walk_s7[0-9]{2}: [0-9]+ check|WALK S711: [0-9]+ ok)' || { printf '%s\n' "$outn" | tail -4 | sed 's/^/         /'; echo "the walk did not reach its own last line on the rebuilt files" >&2; return 1; }
  printf '%s\n' "$outo" | tail -1 | grep -q -E '^(walk_s7[0-9]{2}: [0-9]+ check|WALK S711: [0-9]+ ok)' || { printf '%s\n' "$outo" | tail -4 | sed 's/^/         /'; echo "the walk did not reach its own last line on the live files" >&2; return 1; }
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
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/8] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $FILES; do [ -n "${TO[$f]}" ] || { say "!! [1/8] TO_PINS.md5 does not name $f - nothing installed"; exit 1; }; done
for f in $FILES; do [ -f "$ROOT/$f" ] || { say "!! [1/8] $ROOT/$f is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$SCHEMA" ] && [ -f "$ROOT/shared/scan_quality.py" ] && [ -f "$ROOT/finance/item_check.py" ] || { say "!! [1/8] $DB, $ADB, purchase_schema.sql, scan_quality.py or item_check.py is missing - nothing installed"; exit 1; }
mkdir -p "$SCR/built/finance" "$SCR/built/portal" "$SCR/pyc" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
ALL=1; for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- ALREADY INSTALLED: the six files are the kit's. Nothing written. finance healthz $(fhz) · portal $(phz)"; exit 0; }
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
for f in $FILES; do C=$(m5 "$ROOT/$f"); [ "$C" = "${FROM[$f]}" ] || stop_unlocked "!! [2/8] $ROOT/$f is ${C:0:8}, expected ${FROM[$f]:0:8} - it changed after this kit was built: STOP, nothing installed"; done
say "[2/8] live pins exact: scan_register ${FROM[finance/scan_register.py]:0:8} · purchase_app ${FROM[finance/purchase_app.py]:0:8} · amir_day ${FROM[finance/amir_day.py]:0:8} · porders ${FROM[finance/porders.py]:0:8} · month_read ${FROM[finance/month_read.py]:0:8} · portal ${FROM[portal/portal.py]:0:8}"

"$APY" -B make_s749.py "$ROOT/finance" "$ROOT/portal" "$SCR/built" "$KDIR" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/8] the builder refused a live file - nothing installed"; }
for f in $FILES; do
  [ "$(m5 "$SCR/built/$f")" = "${TO[$f]}" ] || stop_unlocked "!! [3/8] rebuilt, $f is $(m5 "$SCR/built/$f" | cut -c1-8), not ${TO[$f]:0:8} - nothing installed"
  for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/$f" || stop_unlocked "!! [3/8] $f does not compile on $py - nothing installed"; done
done
mkdir -p "$SCR/new/finance" "$SCR/new/shared" "$SCR/old/finance" "$SCR/new/portal"
for f in "$ROOT"/finance/*.py "$ROOT"/finance/*.json "$ROOT"/finance/*.sql "$ROOT"/finance/*.html; do [ -f "$f" ] && cp -p "$f" "$SCR/new/finance/" && cp -p "$f" "$SCR/old/finance/"; done
for f in "$ROOT"/shared/*.py; do [ -f "$f" ] && cp -p "$f" "$SCR/new/shared/"; done
for f in $FILES; do case "$f" in finance/*) cp -p "$SCR/built/$f" "$SCR/new/finance/$(basename "$f")";; portal/*) cp -p "$SCR/built/$f" "$SCR/new/portal/$(basename "$f")";; esac; done
say "[3/8] rebuilt here from this box's live bytes: the six files at their TO pins; each compiles under both pythons"

R=$(walk "$SCR/new/finance" "$SCR/new/shared" "$SCR/new/portal/portal.py" | tail -1)
[ "$R" = "$GREEN" ] || { walk "$SCR/new/finance" "$SCR/new/shared" "$SCR/new/portal/portal.py" | grep -E 'FAIL|Error|raised' | head -12 | sed 's/^/         /'; PLACED=2; stop_unlocked "!! [4/8] the walk on the rebuilt files is not green ($R) - nothing installed (kept in $SCR)"; }
R0=$(walk "$SCR/old/finance" "$SCR/new/shared" "$ROOT/portal/portal.py" | tail -1)
[ "$R0" = "$CONTROL" ] || { PLACED=2; stop_unlocked "!! [4/8] the control on the live files is not as expected ($R0; expected $CONTROL) - nothing installed (kept in $SCR)"; }
E740="$(earlier walk_s740 "$ALLOW740")" || { PLACED=2; stop_unlocked "!! [4/8] S740's walk on the rebuilt files shows a red the live files do not (above) - nothing installed (kept in $SCR)"; }
E738="$(earlier walk_s738 "$ALLOW738")" || { PLACED=2; stop_unlocked "!! [4/8] S738's walk on the rebuilt files shows a red the live files do not (above) - nothing installed (kept in $SCR)"; }
E736="$(earlier walk_s736 "$ALLOW736")" || { PLACED=2; stop_unlocked "!! [4/8] S736's walk on the rebuilt files shows a red the live files do not (above) - nothing installed (kept in $SCR)"; }
E726="$(earlier walk_s726 "$ALLOW726")" || { PLACED=2; stop_unlocked "!! [4/8] S726's walk on the rebuilt files shows a red the live files do not (above) - nothing installed (kept in $SCR)"; }
E711="$(earlier walk_s711 "")" || { PLACED=2; stop_unlocked "!! [4/8] S711's walk on the rebuilt files shows a red the live files do not (above) - nothing installed (kept in $SCR)"; }
say "[4/8] the walk: $R; the control on the live files: $R0; S740's walk: $E740; S738's: $E738; S736's: $E736; S726's: $E726; S711's: $E711"
proof "$SCR/old/finance" > "$SCR/proof_live.txt"; proof "$SCR/new/finance" > "$SCR/proof_kit.txt"
PL=$(tail -1 "$SCR/proof_live.txt"); PK=$(tail -1 "$SCR/proof_kit.txt")
say "---------------------------------------------------------------- the proof by the KIT's files (read only) -- paste all of it to Claude"
sed 's/^/   /' "$SCR/proof_kit.txt"
say "---------------------------------------------------------------- what the kit RE-STATES against the live files (F-1153: read this before the real line)"
diff <(grep -v -E '^(S749 proof|PROOF S749)|read in [0-9]' "$SCR/proof_live.txt") <(grep -v -E '^(S749 proof|PROOF S749)|read in [0-9]' "$SCR/proof_kit.txt") | grep -E '^[<>]' | sed 's/^</   LIVE /; s/^>/   KIT  /' | head -80
say "----------------------------------------------------------------"
echo "$PK" | grep -q -E '^PROOF S749: [0-9]+ counted month' || { PLACED=2; stop_unlocked "!! [4/8] the proof on this box's databases: $PK - nothing installed (kept in $SCR)"; }
echo "$PL" | grep -q -E '^PROOF S749: [0-9]+ counted month' || { PLACED=2; stop_unlocked "!! [4/8] the proof by the live files: $PL - nothing installed (kept in $SCR)"; }
SD="$(seed "$SCR/new/finance" --dry | tail -1)"
echo "$SD" | grep -q -E '^SEED S749: (dry|already|written)' || { PLACED=2; stop_unlocked "!! [4/8] the seed: $SD - nothing installed (kept in $SCR)"; }
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/8] finance healthz $f0 before the install - nothing installed"
p0=$(phz); [ "$p0" = 200 ] || stop_unlocked "!! [4/8] the portal answered $p0 before the install - nothing installed"
say "[4/8] live: $PL"
say "      kit:  $PK (both databases opened read-only); the seed: $SD; finance and the portal healthy"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks, the control and the proof green; NOTHING written"; exit 0; fi

for f in $FILES; do { \cp -p "$ROOT/$f" "$(bak "$f")" && [ "$(m5 "$(bak "$f")")" = "${FROM[$f]}" ]; } || stop_unlocked "!! [5/8] could not write the backup $(bak "$f") - nothing placed"; done
for f in $FILES; do { cat "$SCR/built/$f" > "$(stg "$f")" && [ "$(m5 "$(stg "$f")")" = "${TO[$f]}" ]; } || stop_unlocked "!! [5/8] could not stage $f - nothing placed"; done
for f in $FILES; do chmod --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; chown --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; done
OLDPIDS="$(pids_of "$FSVC" | tr '\n' ' ') $(pids_of "$PSVC" | tr '\n' ' ')"
PLACED=1
for f in $FILES; do mv -f "$(stg "$f")" "$ROOT/$f" || restore "the rename of $f"; done
for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || restore "read back of $f"; done
find "$ROOT/finance" "$ROOT/portal" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[5/8] placed and read back: scan_register ${TO[finance/scan_register.py]:0:8} · purchase_app ${TO[finance/purchase_app.py]:0:8} · amir_day ${TO[finance/amir_day.py]:0:8} · porders ${TO[finance/porders.py]:0:8} · month_read ${TO[finance/month_read.py]:0:8} · portal ${TO[portal/portal.py]:0:8} (backups *.bak_S749_*)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c0=$(wait200 phz); [ "$c0" = 200 ] || restore "the portal's login page answered $c0"
c2=$(fhealth /finance/amir/step/1); case "$c2" in 302|401|403) ;; *) restore "Amir's page answered $c2 without a login (expected 302, 401 or 403)";; esac
c3=$(fhealth /finance/purchase/page/check); case "$c3" in 302|401|403) ;; *) restore "the step view answered $c3 without a login (expected 302, 401 or 403)";; esac
c4=$(fhealth /finance/purchase/api/s749/pick?scan=1); case "$c4" in 302|401|403) ;; *) restore "the pick door answered $c4 without a login (expected 302, 401 or 403)";; esac
c5=$(fhealth /finance/purchase/page/pay); case "$c5" in 302|401|403) ;; *) restore "the payment sheet answered $c5 without a login (expected 302, 401 or 403)";; esac
c6=$(fhealth /finance/purchase/page/hub); case "$c6" in 302|401|403) ;; *) restore "the hub answered $c6 without a login (expected 302, 401 or 403)";; esac
c7=$(phealth /portal); case "$c7" in 200|302) ;; *) restore "the portal's home answered $c7 (expected 200 or 302)";; esac
NEWPIDS="$(pids_of "$FSVC" | tr '\n' ' ') $(pids_of "$PSVC" | tr '\n' ' ')"
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JL="$("$JOURNALCTL" -u "$FSVC" -u "$PSVC" --since "$T0" --no-pager -o short 2>/dev/null)"
  for p in $OLDPIDS; do JL="$(printf '%s\n' "$JL" | grep -v -E "\[$p\]:")"; done
  JR="$(printf '%s\n' "$JL" | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError|Logging error')"
  [ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'Traceback|Error' | head -6 | sed 's/^/         /'; restore "journal: $JR error line(s) from the new masters ($NEWPIDS) since the restart"; }
fi
say "[6/8] $FSVC and $PSVC restarted at $(TZ=Asia/Kolkata date '+%H:%M IST'): finance healthz $c1, portal login $c0; without a login Amir's page $c2, the step view $c3, the pick door $c4, the payment sheet $c5, the hub $c6; portal home $c7; journal clean (old PIDs left out, F-1135)"
mkdir -p "$SCR/placed/finance" "$SCR/placed/portal"
for f in "$ROOT"/finance/*.py "$ROOT"/finance/*.json "$ROOT"/finance/*.sql "$ROOT"/finance/*.html; do [ -f "$f" ] && cp -p "$f" "$SCR/placed/finance/"; done
cp -p "$ROOT/portal/portal.py" "$SCR/placed/portal/"
R=$(walk "$SCR/placed/finance" "$SCR/new/shared" "$SCR/placed/portal/portal.py" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 7 ] && R="rehearsal: a forced red at [7/8]"
[ "$R" = "$GREEN" ] || restore "the walk on the placed files: $R"
say "[7/8] the walk on the placed files: $R"
# [8/8] the seed (the one setting, only if absent; the kit's two tables), then the proof by the placed files
S8="$(seed "$SCR/placed/finance" "" | tail -1)"
case "$S8" in "SEED S749: written"|"SEED S749: already") ;; *) restore "the seed: $S8";; esac
P8=$(proof "$SCR/placed/finance" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 8 ] && P8="rehearsal: a forced red at [8/8]"
echo "$P8" | grep -q -E '^PROOF S749: [0-9]+ counted month' || restore "the proof by the placed files: $P8"
say "[8/8] $S8; by the placed files: $P8 -- your step view, the register, the audit page, the hub, the payment sheet, Amir's card and the console read it at their next load"
release_lock
say "undo (one line): $(for f in $FILES; do printf '\\cp -p %s %s && ' "$(bak "$f")" "$ROOT/$f"; done)$SYSTEMCTL restart $FSVC && $SYSTEMCTL restart $PSVC"
say ""
say "$KIT: DONE. Your purchase check: https://followup.dr-manoj.in/finance/purchase/page/check"
exit 0
