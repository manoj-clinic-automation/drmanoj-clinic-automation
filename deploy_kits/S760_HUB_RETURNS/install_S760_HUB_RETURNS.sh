#!/bin/bash
# =============================================================================
#  install_S760_HUB_RETURNS.sh · kit S760 (09-Nov-2026, Sanjeevni session 414) · D873 / F-1200
#  THE HUB'S RETURNS CARD AS APPROVED: every month on one card (the month picker goes); the returns waiting for the owner's OK from
#  every month together at the top, newest first, each naming only the medicine in question, Approve / Reject on the line (Reject
#  recovers the money in question, never more than was refunded); a batch repeated across them named once; the batch check a COUNT
#  only ("sold by us N times, not under this patient's ID" / "we never sold this batch"); can't-be-checked beneath; the months
#  folded, June - August as history; petty refund differences never shown (F-1200). One new READ door: /finance/darpan/api/cn-hub.
#  The owner's decisions still go through cn-approve (untouched). The Needs-you returns line reads the card's own count (returns_kinds.hub,
#  light) -- "Returns waiting for your OK -- N · ₹X · oldest DD-Mon" -- the S446 line its fail-soft: one number on the page.
#  Four files of this project; no table, no setting, no money figure.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s760kit && cp -rp /root/deploy/repo/deploy_kits/S760_HUB_RETURNS /tmp/s760kit && bash /tmp/s760kit/install_S760_HUB_RETURNS.sh
#  (DRY=1 before bash: every gate, the walk, its control, the earlier walks and the proof on this box's data, printed; NOTHING written.)
#   /root/finance/returns_kinds.py 9dd7175d -> TO   /root/finance/darpan_app.py a55ecbed -> TO   /root/finance/finance_ui/finance_approvals.html 037af626 -> TO
#   /root/finance/sanjeevni_approvals.py d063e939 -> TO
#  Gates: SUMS, KIT_ID, the window, the build lock, the four live pins, the rebuild to the TO pins (both pythons compile), walk_s760
#  green on the rebuilt files, its CONTROL on the live files, the earlier walks (S677, S406, S368) -- no red beyond the live files'
#  own --, the proof by both on a COPY of finance.db and the LIVE spine (SPINE_DB = /root/finance/spine/spine.db, opened read only):
#  counts only, the Needs-you line equal to the card, no cn_kind row saved, the hub read under 3 s. cn-approve can now decide a return
#  only the spine holds (its date read from the spine, read only). After placing: the service restarted, health,
#  the hub and the new door refuse a stranger, the journal (new PIDs only), the walk and the proof again on the placed files.
# =============================================================================
set -u
KIT="S760_HUB_RETURNS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
FILES="finance/returns_kinds.py finance/darpan_app.py finance/finance_ui/finance_approvals.html finance/sanjeevni_approvals.py"
declare -A FROM=( [finance/returns_kinds.py]=9dd7175de142cbf3c8f6e6b415580822 [finance/darpan_app.py]=a55ecbed4bbe1230b24565b4185b8755
                  [finance/finance_ui/finance_approvals.html]=037af6261a636273a71db99625da4abf [finance/sanjeevni_approvals.py]=d063e939bbe14d21a3741b8629fceef7 )
declare -A TO
for f in $FILES; do TO[$f]="$(awk -v f="$f" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s760_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
GREEN="walk_s760: 0 check(s) failed (0 of them S760 checks)"
CONTROL="walk_s760: 19 check(s) failed (19 of them S760 checks)"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S760_${FROM[$1]:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s760"; }
fhealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { for f in $FILES; do rm -f "$(stg "$f")"; done; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
dbcopy() { "$VPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True, timeout=30); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$1"; }
mkroot() {   # $1 = a root to make: finance/, finance/spine/, finance/finance_ui/ -- code, pages, rules, as the nightly bundle holds them
  local d e f
  for d in finance finance/spine finance/finance_ui; do
    mkdir -p "$1/$d" || return 1
    for e in py html json sql txt sh; do for f in "$ROOT/$d"/*."$e"; do if [ -f "$f" ]; then cp -p "$f" "$1/$d/" || return 1; fi; done; done
  done
  return 0; }
walk() { (cd /tmp && PYTHONPATH="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s760.py" --root "$1" --db "$SCR/walk.db" --scratch "$2" --page "$1/finance/finance_ui/finance_approvals.html" 2>&1); }
SPINE="${SPINE:-$ROOT/finance/spine/spine.db}"
proof() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -W ignore -B "$KDIR/proof_s760.py" "$1" "$ROOT/shared" "$DB" "$2" "$SPINE" 2>&1); }
spine_ok() { [ "$ROOT" != "/root" ] || echo "$1" | grep -q " · spine yes · "; }
reds() { grep -E '^ *(FAIL|RED) ' | sed -E 's/ +\| .*$//; s/ +\[\[.*$//' | sort; }
earlier() {   # $1 = walk name; runs it on the rebuilt root and on the live-files root; a red the live files do not show STOPS
  local w="$1" outn outo extra
  case "$w" in
    walk_s677) outn="$(cd /tmp && PYTHONPATH="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s677.py" --new "$SCR/new" --db "$SCR/walk.db" --scratch "$SCR/e677n" 2>&1)"
               outo="$(cd /tmp && PYTHONPATH="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s677.py" --new "$SCR/old" --db "$SCR/walk.db" --scratch "$SCR/e677o" 2>&1)";;
    walk_s406) cp "$SCR/walk.db" "$SCR/e406n.db"; cp "$SCR/walk.db" "$SCR/e406o.db"
               outn="$(cd /tmp && PYTHONPATH="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s406.py" --app "$SCR/new/finance" --old "$SCR/old/finance" --db "$SCR/e406n.db" 2>&1)"
               outo="$(cd /tmp && PYTHONPATH="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s406.py" --app "$SCR/old/finance" --old "$SCR/old/finance" --db "$SCR/e406o.db" 2>&1)";;
    walk_s368) cp "$SCR/walk.db" "$SCR/e368n.db"; cp "$SCR/walk.db" "$SCR/e368o.db"
               outn="$(cd /tmp && PYTHONPATH="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s368.py" --app "$SCR/new/finance" --db "$SCR/e368n.db" 2>&1)"
               outo="$(cd /tmp && PYTHONPATH="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s368.py" --app "$SCR/old/finance" --db "$SCR/e368o.db" 2>&1)";;
  esac
  printf '%s\n' "$outn" | grep -q -E '(of [0-9]+ green|WALK_S368|^  (ok|FAIL) )' || { printf '%s\n' "$outn" | tail -4 | sed 's/^/         /'; echo "the walk did not run on the rebuilt files"; return 1; }
  extra="$(comm -13 <(printf '%s\n' "$outo" | reds) <(printf '%s\n' "$outn" | reds))"
  if [ -n "$extra" ]; then printf '%s\n' "$extra" | head -8 | sed 's/^/         /'; return 1; fi
  echo "$(printf '%s\n' "$outn" | reds | grep -c .) red(s), all the live files' own"
}
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

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout pgrep comm sort tar; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { [ "$ROOT" != "/root" ] && [ "${SKIP_WINDOW:-0}" = 1 ]; } || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/7] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $FILES; do [ -n "${TO[$f]}" ] || { say "!! [1/7] TO_PINS.md5 does not name $f - nothing installed"; exit 1; }; done
for f in $FILES finance/finance_returns_audit.py finance/spine/spine_read.py finance/spine/spine_build.py; do [ -f "$ROOT/$f" ] || { say "!! [1/7] $ROOT/$f is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/7] $DB is missing - nothing installed"; exit 1; }
[ "$ROOT" != "/root" ] || [ -f "$SPINE" ] || { say "!! [1/7] $SPINE is missing - the proof could not read the real returns; nothing installed"; exit 1; }
mkdir -p "$SCR/built/finance" "$SCR/pyc" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
ALL=1; for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the four files are the kit's. Nothing written. finance healthz $(fhz)"; exit 0; fi
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
say "[2/7] live pins exact: returns_kinds ${FROM[finance/returns_kinds.py]:0:8} · darpan_app ${FROM[finance/darpan_app.py]:0:8} · finance_approvals.html ${FROM[finance/finance_ui/finance_approvals.html]:0:8} · sanjeevni_approvals ${FROM[finance/sanjeevni_approvals.py]:0:8}"

"$APY" -B make_s760.py "$ROOT/finance" "$SCR/built" "$KDIR" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/7] the builder refused a live file - nothing installed"; }
for f in $FILES; do
  [ "$(m5 "$SCR/built/$f")" = "${TO[$f]}" ] || stop_unlocked "!! [3/7] rebuilt, $f is $(m5 "$SCR/built/$f" | cut -c1-8), not ${TO[$f]:0:8} - nothing installed"
  case "$f" in *.py) for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/$f" || stop_unlocked "!! [3/7] $f does not compile on $py - nothing installed"; done;; esac
done
mkroot "$SCR/new" && mkroot "$SCR/old" || stop_unlocked "!! [3/7] could not copy $ROOT/finance for the walks - nothing installed"
for f in $FILES; do cp -p "$SCR/built/$f" "$SCR/new/$f"; done
dbcopy "$SCR/walk.db" || stop_unlocked "!! [3/7] could not copy $DB for the walks - nothing installed"
say "[3/7] rebuilt here from this box's live bytes: the four files at their TO pins; the three .py compile under both pythons"

R=$(walk "$SCR/new" "$SCR/wn" | tail -1)
[ "$R" = "$GREEN" ] || { walk "$SCR/new" "$SCR/wn2" | grep -E 'RED|Error|raised' | head -12 | sed 's/^/         /'; PLACED=2; stop_unlocked "!! [4/7] the walk on the rebuilt files is not green ($R) - nothing installed (kept in $SCR)"; }
R0=$(walk "$SCR/old" "$SCR/wo" | tail -1)
[ "$R0" = "$CONTROL" ] || { PLACED=2; stop_unlocked "!! [4/7] the control on the live files is not as expected ($R0; expected $CONTROL) - nothing installed (kept in $SCR)"; }
EARLIER="${REHEARSE_EARLIER:-walk_s677 walk_s406 walk_s368}"
ESAY=""
for w in $EARLIER; do
  E="$(earlier "$w")" || { PLACED=2; stop_unlocked "!! [4/7] $w on the rebuilt files shows a red the live files do not (above) - nothing installed (kept in $SCR)"; }
  ESAY="$ESAY; $w: $E"
done
say "[4/7] the walk: $R; the control: $R0$ESAY"
proof "$SCR/old/finance" "$SCR/pold" > "$SCR/proof_live.txt"; proof "$SCR/new/finance" "$SCR/pnew" > "$SCR/proof_kit.txt"
PL=$(tail -1 "$SCR/proof_live.txt"); PK=$(tail -1 "$SCR/proof_kit.txt")
say "---------------------------------------------------------------- the proof by the KIT's files (read only, a copy of finance.db) -- paste all of it to Claude"
sed -E 's/^/   /' "$SCR/proof_kit.txt"
say "---------------------------------------------------------------- the live files said"
sed 's/^/   /' "$SCR/proof_live.txt"
say "----------------------------------------------------------------"
{ echo "$PK" | grep -q -E '^PROOF S760: months [0-9]+ · needs [0-9]+ ' && spine_ok "$PK"; } || { PLACED=2; stop_unlocked "!! [4/7] the proof on this box's data: $PK - nothing installed (kept in $SCR)"; }
echo "$PL" | grep -q -E '^PROOF S760 \(the live files\): no hub' || { PLACED=2; stop_unlocked "!! [4/7] the proof by the live files: $PL - nothing installed (kept in $SCR)"; }
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/7] finance healthz $f0 before the install - nothing installed"
say "[4/7] live: $PL"
say "      kit:  $PK; finance healthy"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk, the control, the earlier walks and the proof green; NOTHING written"; exit 0; fi

for f in $FILES; do { \cp -p "$ROOT/$f" "$(bak "$f")" && [ "$(m5 "$(bak "$f")")" = "${FROM[$f]}" ]; } || stop_unlocked "!! [5/7] could not write the backup $(bak "$f") - nothing placed"; done
for f in $FILES; do { cat "$SCR/built/$f" > "$(stg "$f")" && [ "$(m5 "$(stg "$f")")" = "${TO[$f]}" ]; } || stop_unlocked "!! [5/7] could not stage $f - nothing placed"; done
for f in $FILES; do chmod --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; chown --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; done
OLDPIDS="$(pids_of "$FSVC" | tr '\n' ' ')"
PLACED=1
for f in $FILES; do mv -f "$(stg "$f")" "$ROOT/$f" || restore "the rename of $f"; done
for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || restore "read back of $f"; done
find "$ROOT/finance" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[5/7] placed and read back: returns_kinds ${TO[finance/returns_kinds.py]:0:8} · darpan_app ${TO[finance/darpan_app.py]:0:8} · finance_approvals.html ${TO[finance/finance_ui/finance_approvals.html]:0:8} · sanjeevni_approvals ${TO[finance/sanjeevni_approvals.py]:0:8}"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(fhealth /finance/approvals); case "$c2" in 302|401|403) ;; *) restore "the hub answered $c2 without a login (expected 302, 401 or 403)";; esac
c3=$(fhealth /finance/darpan/api/cn-hub); case "$c3" in 302|401|403) ;; *) restore "the new door answered $c3 without a login (expected 302, 401 or 403)";; esac
c4=$(fhealth /finance/darpan/api/cn-detail); case "$c4" in 302|401|403) ;; *) restore "cn-detail answered $c4 without a login (expected 302, 401 or 403)";; esac
c5=$(fhealth /finance/sanjeevni/api/needs-you); case "$c5" in 302|401|403) ;; *) restore "needs-you answered $c5 without a login (expected 302, 401 or 403)";; esac
NEWPIDS="$(pids_of "$FSVC" | tr '\n' ' ')"
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager -o short 2>/dev/null)"
  for p in $OLDPIDS; do JL="$(printf '%s\n' "$JL" | grep -v -E "\[$p\]:")"; done
  JR="$(printf '%s\n' "$JL" | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError|Logging error|darpan_app NOT mounted')"
  [ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'Traceback|Error|NOT mounted' | head -6 | sed 's/^/         /'; restore "journal: $JR error line(s) from the new master ($NEWPIDS) since the restart"; }
fi
say "[6/7] $FSVC restarted at $(TZ=Asia/Kolkata date '+%H:%M IST'): healthz $c1; without a login the hub $c2, cn-hub $c3, cn-detail $c4, needs-you $c5; journal clean (new PIDs: $NEWPIDS)"
mkroot "$SCR/placed" || restore "could not copy the placed files for the walk"
R=$(walk "$SCR/placed" "$SCR/wp" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 7 ] && R="rehearsal: a forced red at [7/7]"
[ "$R" = "$GREEN" ] || restore "the walk on the placed files: $R"
P7=$(proof "$SCR/placed/finance" "$SCR/pplaced" | tail -1)
{ echo "$P7" | grep -q -E '^PROOF S760: months [0-9]+ · needs [0-9]+ ' && spine_ok "$P7"; } || restore "the proof by the placed files: $P7"
say "[7/7] the walk on the placed files: $R; by the placed files: $P7"
release_lock
say "undo (one line): $(for f in $FILES; do printf '\\cp -p %s %s && ' "$(bak "$f")" "$ROOT/$f"; done)$SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. Your hub: https://followup.dr-manoj.in/finance/approvals#returnsCard"
exit 0
