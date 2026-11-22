#!/bin/bash
# =============================================================================
#  install_S929_STAFF_DRESS_ASSETS.sh · kit S929 (the parent, S498, 22-Nov-2026) · staff dress, i-card 'paused', mobiles, cycle
#  1. CODE   /root/staff_register/staff_register.py 18973ca9 -> TO : approving a re-issue closes that item's open pause by itself;
#            an issue records SIZE and WHAT WAS GIVEN; the 2000-01-01 seed reads 'before the register'.
#  2. DATA   s929_load.py (one transaction, audited, database backed up first): the JAN 2027 tab = the current set of 10 staff;
#            the 2025 / 2026 tabs as earlier issues; Alisha / Shivani / Vikki's open pauses close to yesterday; 3 old pending
#            entries 'superseded'; mobiles Shavez / Darpan / Surendra / Ranjeet, cycle Sandip.
#  staff-register restarted.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s929kit && cp -rp /root/deploy/repo/deploy_kits/S929_STAFF_DRESS_ASSETS /tmp/s929kit && bash /tmp/s929kit/install_S929_STAFF_DRESS_ASSETS.sh
#  DRY=1 before bash: every gate and the walk, nothing changed. --undo: the file back (the data stays; it is the record).
# =============================================================================
set -u
KIT="S929_STAFF_DRESS_ASSETS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"; APY="${APY:-/usr/bin/python3}"
RDIR="${RDIR:-/root/staff_register}"; N="staff_register.py"; F="$RDIR/$N"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
RSVC="${RSVC:-staff-register}"; RPORT="${RPORT:-8044}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
FROM="18973ca92609519ed9aea819a66b9f68"
TO="$(awk '$2=="staff_register/staff_register.py"{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(TZ=Asia/Kolkata date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s929_inst_$STAMP"; TOOK_LOCK=0
BAK="$RDIR/$N.bak_S929_${FROM:0:8}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
rhealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$RPORT/register/health"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(rhealth); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$RDIR/.$N.s929"; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the file back"
  \cp -p "$BAK" "$F"; "$SYSTEMCTL" restart "$RSVC" || true
  say "   $N $(m5 "$F" | cut -c1-8) (expected ${FROM:0:8}); $RSVC restarted, health $(wait200). If the load had run, its records stay (the old file ignores the new columns). Send a photo of this screen to Claude."
  release_lock; exit 1; }
dbpath() { (cd "$RDIR" && PYTHONDONTWRITEBYTECODE=1 "$VPY" -B -c "import sys; sys.path.insert(0,'.'); import staff_register as s; print(s.DB_PATH)" 2>/dev/null | tail -1); }

if [ "${1:-}" = "--undo" ]; then
  [ "$(m5 "$F")" = "$FROM" ] && { say "-- $KIT is not installed (the file at its FROM pin) - nothing to undo."; exit 0; }
  [ -f "$BAK" ] && [ "$(m5 "$BAK")" = "$FROM" ] || { say "!! no good backup $BAK - nothing undone"; exit 1; }
  [ "$(m5 "$F")" = "$TO" ] || { say "!! $F is $(m5 "$F" | cut -c1-8), not this kit's - a later change is on it: nothing undone. Tell Claude."; exit 1; }
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
  \cp -p "$BAK" "$F"; "$SYSTEMCTL" restart "$RSVC"; h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but the register's health is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE (the file back, $RSVC restarted, health 200). The loaded records stay (they are the record; the old page shows them)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 "$KDIR/$N")" = "$TO" ] || { say "!! [1/6] the kit's $N is not as built - nothing installed"; exit 1; }
[ -f "$F" ] || { say "!! [1/6] $F missing - nothing installed"; exit 1; }
DB="${DB:-$(dbpath)}"; [ -n "$DB" ] && [ -f "$DB" ] || { say "!! [1/6] the register's database not found ('$DB') - nothing installed"; exit 1; }
LOADNOW="$("$VPY" "$KDIR/s929_load.py" "$DB")"
if [ "$(m5 "$F")" = "$TO" ] && case "$LOADNOW" in "S929_LOAD: ALREADY DONE"*) true;; *) false;; esac; then say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; fi
case "$LOADNOW" in "S929_LOAD: WOULD"*|"S929_LOAD: ALREADY DONE"*) ;; *) say "!! [1/6] the data is not as expected: $LOADNOW - nothing installed. Tell Claude."; exit 1;; esac
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/6] DRY RUN: kit gates green ($LOADNOW); no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken by $KIT"
else say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
LIVE5="$(m5 "$F")"; [ "$LIVE5" = "$FROM" ] || [ "$LIVE5" = "$TO" ] || stop "!! [2/6] $F is ${LIVE5:0:8}, expected ${FROM:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/$N" "$KDIR/s929_load.py" || stop "!! [2/6] the kit's python does not compile on $p - nothing installed"; done
say "[2/6] the live pin exact; the file and the load compile on both pythons"
W=$(cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s929.py" "$KDIR/$N" 2>&1 | grep -v '^att_correction'); R=$(echo "$W" | tail -1)
case "$R" in "WALK 23/23") ;; *) echo "$W" | grep '^FAIL' | cut -c1-160 | head -6 | sed 's/^/      /'; stop "!! [3/6] walk_s929 (a made-up register) on the new file: $R - nothing installed";; esac
\cp -p "$F" "$SCR/live_$N" || stop "!! [3/6] could not copy the live file for the control - nothing installed"
[ "$LIVE5" = "$FROM" ] || \cp -p "$BAK" "$SCR/live_$N"
Rc=$(cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s929.py" "$SCR/live_$N" 2>&1 | tail -1)
case "$Rc" in "WALK 23/23") stop "!! [3/6] walk_s929's control (the live file) did not go red - nothing installed";; esac
ST=$(cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/$N" --selftest 2>&1 | grep -c '^SELFTEST OK')
[ "$ST" = 1 ] || stop "!! [3/6] the register's own --selftest on the new file is not OK - nothing installed"
"$VPY" -c "import sqlite3,sys;s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=30);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close()" "$DB" "$SCR/copy.db" || stop "!! [3/6] could not copy the database - nothing installed"
LC=$("$VPY" "$KDIR/s929_load.py" "$SCR/copy.db" --apply)
case "$LC" in "S929_LOAD: APPLIED"*|"S929_LOAD: ALREADY DONE"*) ;; *) stop "!! [3/6] the load on a COPY of the live register: $LC - nothing installed";; esac
say "[3/6] walk_s929 $R (made-up register; control red: ${Rc:-crashed}); the register's own selftest OK; on a copy of the live register: $LC"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk, the selftest and the load on a copy green; nothing live changed"; exit 0; fi
h0=$(rhealth); [ "$h0" = 200 ] || stop "!! [4/6] the register's health $h0 before the install - nothing installed"
if [ "$LIVE5" = "$FROM" ]; then
  { \cp -p "$F" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop "!! [4/6] could not write the backup of $N - nothing placed"
  st="$RDIR/.$N.s929"; { cat "$KDIR/$N" > "$st" && chmod --reference="$F" "$st" 2>/dev/null; chown --reference="$F" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$TO" ]; } || stop "!! [4/6] could not stage $N - nothing placed"
  mv -f "$st" "$F" || restore "the rename of $N"
  [ "$(m5 "$F")" = "$TO" ] || restore "read back of $N"
fi
DBB="$DB.bak_S929_$STAMP"
"$VPY" -c "import sqlite3,sys;s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=30);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close()" "$DB" "$DBB" || restore "the database backup before the load"
LD=$("$VPY" "$KDIR/s929_load.py" "$DB" --apply)
case "$LD" in "S929_LOAD: APPLIED"*|"S929_LOAD: ALREADY DONE"*) ;; *) restore "the load said: $LD (it changes nothing when it fails)";; esac
"$SYSTEMCTL" restart "$RSVC" || restore "restart $RSVC"
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/6]"
h1=$(wait200); [ "$h1" = 200 ] || restore "the register's health $h1 after the restart"
release_lock
say "[4/6] placed and read back: $N at its TO pin"
say "[5/6] $LD (database backed up first: $DBB); $RSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), health $h1"
say "[6/6] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""
say "$KIT: DONE."
exit 0
