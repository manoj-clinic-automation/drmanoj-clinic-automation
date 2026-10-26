#!/bin/bash
# =============================================================================
#  install_S661_RESTORE_DRILLS.sh · kit S661 (26-Oct-2026, the parent, session 357) · the weekly audit's recovery-story asks, answered
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s661kit && cp -rp /root/deploy/repo/deploy_kits/S661_RESTORE_DRILLS /tmp/s661kit && bash /tmp/s661kit/install_S661_RESTORE_DRILLS.sh
#  (DRY=1 before bash: every gate, the offline tests, the two drills' preflight against the real Drive conf; nothing written.)
#
#   NEW  /root/state_backup/verify_restore_code.py    the code bundle pulled back from Drive, untarred, held to its MANIFEST and the live box
#   NEW  /root/state_backup/verify_restore_state.py   the encrypted bundle pulled back, decrypted with the box's key, untarred, databases checked
#   /root/state_backup/code_bundle.py          37a5a132 -> TO   v1.9: + clinic-doctor, static_inbox *.js, assetapp/static *.js; DEPLOY_ALLOW + clinic_doctor.py
#   /root/state_backup/clinic_state_backup.py  f315bf43 -> TO   SRC_FILES + .htaccess, the followup vhost.conf, the watchdog drop-in (each proven present here)
#   /root/finance/freshness_legs.json          9df66934 -> TO   + 4 legs; the finance drill 4400 h -> 200 h; the petty leg parked
#   crontab: THREE lines, tagged S661_RESTORE_DRILLS (Sunday 02:10 the finance drill · 02:20 the code drill · 02:35 the state drill)
#  No service restarted (the legs file is read on each collector run; the writers run at night). No data step.
#  ORDER: gates (window, SUMS, KIT_ID) -> ALREADY INSTALLED? -> lock -> the FROM pins + the three new sources present -> rebuilt here from the live
#  bytes = TO_PINS -> compile (both pythons) -> the offline tests (45) -> the two drills' --dry against the REAL conf (conf, key, openssl round trip,
#  the slots present; no download) -> DRY stops -> backups -> staged + renamed + read back -> crontab backup -> three lines appended -> read back
#  -> the state drill run ONCE for real (the first restore ever; FAIL puts everything back) -> the code drill run once -> DONE.
#  Under set -u, not set -e: every gate is a test.
# =============================================================================
set -u
KIT="S661_RESTORE_DRILLS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
TAG="# S661_RESTORE_DRILLS"
REL="root/state_backup/code_bundle.py root/state_backup/clinic_state_backup.py root/finance/freshness_legs.json"
NEW="root/state_backup/verify_restore_code.py root/state_backup/verify_restore_state.py"
MUST_EXIST="home/drmanojagarwal.com/public_html/.htaccess usr/local/lsws/conf/vhosts/followup.dr-manoj.in/vhost.conf etc/systemd/system/clinic-watchdog.service.d/s578-doctor-first.conf usr/local/bin/clinic-doctor root/deploy/clinic_doctor.py"
declare -A FROM TO
FROM[root/state_backup/code_bundle.py]=37a5a1326a8e90c364e3e50c6083f4f3
FROM[root/state_backup/clinic_state_backup.py]=f315bf43b619f97b2537930d245b98a6
FROM[root/finance/freshness_legs.json]=9df66934e0df2bf3771ffeb517312674
while read -r h f; do TO[$f]=$h; done < "$KDIR/TO_PINS.md5"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s661_inst_$STAMP"
CRONBAK="${CRONBAK:-/root/finance/crontab.bak_S661_$STAMP}"
PLACED=0; TOOK_LOCK=0; CRON_WRITTEN=0
L1="10 2 * * 0 $VPY /root/finance/verify_restore.py nightly >> /root/finance/verify_restore.log 2>&1 $TAG"
L2="20 2 * * 0 $VPY /root/state_backup/verify_restore_code.py >> /root/state_backup/verify_restore_code.log 2>&1 $TAG"
L3="35 2 * * 0 $VPY /root/state_backup/verify_restore_state.py >> /root/state_backup/verify_restore_state.log 2>&1 $TAG"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
rp() { echo "${ROOT%/}/$1"; }
bak() { echo "$(rp "$1").bak_S661_${FROM[$1]:0:8}"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
cronN() { crontab -l 2>/dev/null | wc -l | awk '{print $1}'; }
tagN() { local n; n="$(crontab -l 2>/dev/null | grep -cF -- "$TAG" || true)"; echo "${n:-0}"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the three files back, removing the two new ones, the crontab back"
  for r in $REL; do \cp -p "$(bak "$r")" "$(rp "$r")" || say "   !! could not put back $(rp "$r")"; done
  for n in $NEW; do rm -f "$(rp "$n")"; done
  rm -f "$(rp root/state_backup)"/.*.s661 "$(rp root/finance)"/.*.s661
  if [ "$CRON_WRITTEN" = 1 ]; then crontab "$CRONBAK" || say "!! crontab $CRONBAK failed - RUN BY HAND: crontab $CRONBAK"; fi
  for r in $REL; do say "   $(rp "$r") $(m5 "$(rp "$r")") (expected ${FROM[$r]})"; done
  say "   crontab tagged lines now $(tagN) (expected 0). Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date grep sleep find sed crontab wc tail od openssl timeout; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || [ "${REHEARSAL:-0}" = 1 ] || { { [ "$HH" -gt 8 ] || { [ "$HH" -eq 8 ] && [ "$MM" -ge 2 ]; }; } && { [ "$HH" -lt 23 ] || [ "$MM" -le 49 ]; }; } \
  || { say "!! [1/9] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 08:02-23:49 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/9] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/9] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for r in $REL; do [ -f "$(rp "$r")" ] || { say "!! [1/9] $(rp "$r") is not there - nothing installed"; exit 1; }; done
ALL=1; for r in $REL; do [ "$(m5 "$(rp "$r")")" = "${TO[$r]}" ] || ALL=0; done; for n in $NEW; do [ -f "$(rp "$n")" ] || ALL=0; done
if [ "$ALL" = 1 ] && [ "$(tagN)" = 3 ]; then say "-- ALREADY INSTALLED: the three files at their TO, the two drills in place, three tagged crontab lines. Nothing written."; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/9] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/9] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  TOOK_LOCK=1; say "[1/9] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/9] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."
  exit 3
fi

for r in $REL; do C="$(m5 "$(rp "$r")")"; [ "$C" = "${FROM[$r]}" ] || stop_unlocked "!! [2/9] $(rp "$r") is ${C:0:8}, expected ${FROM[$r]:0:8} - it changed after this kit was built: STOP, nothing installed"; done
for n in $NEW; do [ -e "$(rp "$n")" ] && stop_unlocked "!! [2/9] $(rp "$n") already exists and is not this kit's - STOP, nothing installed"; done
for m in $MUST_EXIST; do [ -f "$(rp "$m")" ] || stop_unlocked "!! [2/9] $(rp "$m") is not on this box - the state bundle would refuse the night (FATAL 41) if it were named: STOP, nothing installed"; done
[ "$(tagN)" = 0 ] || stop_unlocked "!! [2/9] the crontab already holds $(tagN) '$TAG' line(s) - not this kit's state: STOP, nothing installed"
say "[2/9] live pins exact (the three FROM); the two drills absent; the five files the bundles gain are all on the box; no tagged crontab line"

mkdir -p "$SCR/built" "$SCR/old" "$SCR/pyc" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s661.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/9] the builder refused a live file - nothing installed"; }
for r in $REL; do [ "$(m5 "$SCR/built/$r")" = "${TO[$r]}" ] || stop_unlocked "!! [3/9] rebuilt, $r is $(m5 "$SCR/built/$r" | cut -c1-8), not ${TO[$r]:0:8} - nothing installed"; done
for n in $NEW; do mkdir -p "$(dirname "$SCR/built/$n")"; \cp -p "$KDIR/$(basename "$n")" "$SCR/built/$n"; [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || stop_unlocked "!! [3/9] $n is not at its TO pin - nothing installed"; done
for py in "$APY" "$VPY"; do for f in root/state_backup/code_bundle.py root/state_backup/clinic_state_backup.py $NEW; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore::SyntaxWarning -m py_compile "$SCR/built/$f" || stop_unlocked "!! [3/9] $f does not compile on $py - nothing installed"; done; done
"$APY" -c "import json,sys; d=json.load(open(sys.argv[1])); assert len(d['legs'])==len({l['name'] for l in d['legs']})" "$SCR/built/root/finance/freshness_legs.json" || stop_unlocked "!! [3/9] the built legs file is not valid or has a duplicate name - nothing installed"
for r in $REL; do mkdir -p "$(dirname "$SCR/old/$r")"; \cp -p "$(rp "$r")" "$SCR/old/$r"; done
say "[3/9] rebuilt here from this box's live bytes: each at its TO pin; the two drills at theirs; everything compiles under both pythons; the legs read"

T=$(cd "$SCR" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -B "$KDIR/test_s661.py" --writers "$SCR/built/root/state_backup" 2>&1); TL="$(echo "$T" | tail -1)"
[ "$TL" = "45 of 45 green" ] || { echo "$T" | grep -E 'FAIL|RED|Error|Traceback' | head -20; stop_unlocked "!! [4/9] the offline tests are not green ($TL) - nothing installed"; }
say "[4/9] the offline tests on the venv python: $TL"
if [ "${REHEARSAL:-0}" = 1 ]; then
  say "[5/9] REHEARSAL on a made-up root: the two preflights against the real conf are SKIPPED (no Drive here) -- the offline tests above stand for them"
else
  D1=$(cd "$SCR" && timeout 300 "$VPY" -B "$SCR/built/root/state_backup/verify_restore_code.py" --dry --root "$ROOT" 2>&1); R1=$?
  D2=$(cd "$SCR" && timeout 300 "$VPY" -B "$SCR/built/root/state_backup/verify_restore_state.py" --dry --root "$ROOT" 2>&1); R2=$?
  [ "$R1" = 0 ] || { echo "$D1" | tail -6; stop_unlocked "!! [5/9] the code drill's preflight is red (exit $R1) - nothing installed"; }
  [ "$R2" = 0 ] || { echo "$D2" | tail -6; stop_unlocked "!! [5/9] the state drill's preflight is red (exit $R2) - nothing installed"; }
  say "[5/9] both drills' preflight green against the REAL conf (the folder, the slots, the key file, openssl's round trip); nothing downloaded"
fi
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the tests and both preflights green; NOTHING written, nothing placed, the crontab untouched"; exit 0; fi

for r in $REL; do \cp -p "$(rp "$r")" "$(bak "$r")" && [ "$(m5 "$(bak "$r")")" = "${FROM[$r]}" ] || stop_unlocked "!! [6/9] could not write the backup of $(rp "$r") - nothing placed"; done
for f in $REL $NEW; do
  Lf="$(rp "$f")"; STG="$(dirname "$Lf")/.$(basename "$Lf").s661"
  { cat "$SCR/built/$f" > "$STG" && [ "$(m5 "$STG")" = "${TO[$f]}" ]; } || { rm -f "$(rp root/state_backup)"/.*.s661 "$(rp root/finance)"/.*.s661; stop_unlocked "!! [6/9] could not stage $Lf - nothing placed"; }
  if [ -f "$Lf" ]; then chmod --reference="$Lf" "$STG" 2>/dev/null; chown --reference="$Lf" "$STG" 2>/dev/null; else chmod 700 "$STG"; fi
done
PLACED=1
for f in $REL $NEW; do Lf="$(rp "$f")"; mv -f "$(dirname "$Lf")/.$(basename "$Lf").s661" "$Lf" || restore "the rename of $Lf"; [ "$(m5 "$Lf")" = "${TO[$f]}" ] || restore "the md5 read back of $Lf"; done
say "[6/9] placed and read back: three files at their TO pins (backups *.bak_S661_<from8>), the two drills in /root/state_backup (mode 700)"

crontab -l > "$CRONBAK" 2>/dev/null || restore "crontab -l > $CRONBAK failed"
L0="$(cronN)"; M0="$(cron5)"
[ -s "$CRONBAK" ] && [ "$(m5 "$CRONBAK")" = "$M0" ] && [ "$(tail -c1 "$CRONBAK" | od -An -c | tr -d ' ')" = '\n' ] || restore "the crontab backup is empty, differs from crontab -l, or does not end in a newline"
chmod 600 "$CRONBAK"
( crontab -l; echo "$L1"; echo "$L2"; echo "$L3" ) | crontab - || restore "crontab - failed"
CRON_WRITTEN=1
[ "$(cronN)" = $((L0 + 3)) ] && [ "$(tagN)" = 3 ] || restore "the crontab read back: $(cronN) lines (expected $((L0 + 3))), tagged $(tagN) (expected 3)"
[ "$(crontab -l | grep -vF -- "$TAG" | md5sum | awk '{print $1}')" = "$M0" ] || restore "the crontab without the three new lines is not the backup"
say "[7/9] crontab: backup $CRONBAK ($L0 lines, $M0); three tagged lines appended and read back ($(cronN) lines)"

if [ "${REHEARSAL:-0}" = 1 ]; then
  say "[8/9] REHEARSAL: the first real drills are SKIPPED (no Drive here)"
else
  say "[8/9] the first restore drills ever, now (read-only on Drive; the plaintext deleted after):"
  S=$(cd "$SCR" && timeout 1500 "$VPY" -B "$(rp root/state_backup/verify_restore_state.py)" 2>&1); RS=$?
  echo "$S" | tail -4 | sed 's/^/      /'
  [ "$RS" = 0 ] || restore "the state bundle's restore drill is RED (exit $RS) - the backup is not provably recoverable; everything is put back and this is the week's finding"
  C=$(cd "$SCR" && timeout 1500 "$VPY" -B "$(rp root/state_backup/verify_restore_code.py)" 2>&1); RC=$?
  echo "$C" | tail -4 | sed 's/^/      /'
  [ "$RC" = 0 ] || restore "the code bundle's restore drill is RED (exit $RC)"
fi
release_lock
UNDO=""; for r in $REL; do UNDO="$UNDO\\cp -p $(bak "$r") $(rp "$r") && "; done
say "[9/9] the build lock released"
say "undo (one line): ${UNDO}rm -f $(rp root/state_backup/verify_restore_code.py) $(rp root/state_backup/verify_restore_state.py) && crontab $CRONBAK"
say ""
say "$KIT: DONE. Both backups pulled back and opened for the first time; the drills repeat every Sunday; four new rows on the health page."
exit 0
