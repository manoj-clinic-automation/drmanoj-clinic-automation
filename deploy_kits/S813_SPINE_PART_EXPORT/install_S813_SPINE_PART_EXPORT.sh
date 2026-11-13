#!/bin/bash
# =============================================================================
#  install_S813_SPINE_PART_EXPORT.sh · kit S813 (13-Nov-2026, Sanjeevni session 444)
#  The pharmacy's stock record (the spine) has not been rebuilt since 11-Nov 11:10 IST: its gate fails because a 4-bill PART
#  list of November's purchases (11-Nov 11:04:15) was taken as the authority over the 29-bill list taken 15 s earlier.
#  /root/finance/spine/spine_build.py 67d5693f -> TO : S795's rule in the spine's own reader -- a later purchase report with
#  under half the rows of the older report it would retire, and more than two short, is a part list: set aside (sp_export
#  role PART_LIST, ok 0), the fuller report stays the authority.  REBUILT HERE from the live bytes by make_s813.py.
#  Then the spine is built once, now, by the same command as its cron line, and must come out BUILT AND SWAPPED.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s813kit && cp -rp /root/deploy/repo/deploy_kits/S813_SPINE_PART_EXPORT /tmp/s813kit && bash /tmp/s813kit/install_S813_SPINE_PART_EXPORT.sh
#  (DRY=1 before bash: every gate, the walk and its control; NOTHING written.)
# =============================================================================
set -u
KIT="S813_SPINE_PART_EXPORT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SPLOCK="${SPLOCK:-/tmp/spine.lock}"
FS="finance/spine/spine_build.py"; SDIR="$ROOT/finance/spine"
FROM_S="67d5693fbd853fca7979fa4763f9f825"
TO_S="$(awk -v f="$FS" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s813_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
BAK_S="$ROOT/$FS.bak_S813_${FROM_S:0:8}"; STG_S="$SDIR/.spine_build.py.s813"
SPINE_CMD="${SPINE_CMD:-cd $SDIR && $VPY -B spine_evidence.py && $VPY -B spine_build.py --readings readings --out spine.db --finance-db $ROOT/finance/finance.db}"
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$STG_S"; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the old file back"
  flock -w 600 "$SPLOCK" \cp -p "$BAK_S" "$ROOT/$FS" || say "!! the copy back did not run -- the old file is $BAK_S"
  say "   spine_build.py $(m5 "$ROOT/$FS" | cut -c1-8) (expected ${FROM_S:0:8}). ${2:-The spine itself was not changed (a failed build swaps nothing).} Send a photo of this screen to Claude."
  release_lock; exit 1; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 120 "$VPY" -W ignore -B "$KDIR/walk_s813.py" "$1" 2>&1 | tail -1); }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$TO_S" ] && [ -f "$ROOT/$FS" ] || { say "!! [1/6] the TO pin or $ROOT/$FS missing - nothing installed"; exit 1; }
if [ "$(m5 "$ROOT/$FS")" = "$TO_S" ]; then say "-- $KIT is ALREADY INSTALLED (spine_build.py ${TO_S:0:8}); nothing to do."; exit 0; fi
mkdir -p "$SCR/built" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/6] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken by $KIT"
else say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$ROOT/$FS")" = "$FROM_S" ] || stop "!! [2/6] $ROOT/$FS is $(m5 "$ROOT/$FS" | cut -c1-8), expected ${FROM_S:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
"$APY" -B make_s813.py "$ROOT/$FS" "$SCR/built/spine_build.py" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/6] the builder refused - nothing installed"; }
[ "$(m5 "$SCR/built/spine_build.py")" = "$TO_S" ] || stop "!! [2/6] rebuilt, the file is not at its TO pin - nothing installed"
for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/spine_build.py" || stop "!! [2/6] spine_build.py does not compile on $py - nothing installed"; done
say "[2/6] live pin exact (${FROM_S:0:8}); rebuilt here at its TO pin (${TO_S:0:8}); it compiles on both pythons"
R=$(walk "$SCR/built/spine_build.py")
[ "${R:0:10}" = "WALK GREEN" ] || stop "!! [3/6] the walk: $R - nothing installed"
R0=$(walk "$ROOT/$FS")
[ "${R0:0:8}" = "WALK RED" ] || stop "!! [3/6] the control on the live file: $R0 (must be RED) - nothing installed"
say "[3/6] walk_s813: $R; its control on the live file red as it must be"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the control green; NOTHING written"; exit 0; fi
{ \cp -p "$ROOT/$FS" "$BAK_S" && [ "$(m5 "$BAK_S")" = "$FROM_S" ]; } || stop "!! [4/6] could not write the backup - nothing placed"
{ cat "$SCR/built/spine_build.py" > "$STG_S" && chmod --reference="$ROOT/$FS" "$STG_S" 2>/dev/null; chown --reference="$ROOT/$FS" "$STG_S" 2>/dev/null; [ "$(m5 "$STG_S")" = "$TO_S" ]; } || stop "!! [4/6] could not stage the file - nothing placed"
flock -w 600 "$SPLOCK" mv -f "$STG_S" "$ROOT/$FS" || restore "the rename (the spine's own lock was not free within 10 minutes)"
[ "$(m5 "$ROOT/$FS")" = "$TO_S" ] || restore "read back"
say "[4/6] placed and read back: spine_build.py ${TO_S:0:8} (backup ${BAK_S##*/})"
ST=$(cd "$SDIR" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B selftest_spine.py 2>&1 | tail -1)
[ "${ST:0:11}" = "SELFTEST OK" ] || restore "the spine's own selftest in place: $ST"
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/6]"
BO=$(flock -w 600 "$SPLOCK" sh -c "$SPINE_CMD" 2>&1); BL=$(printf '%s\n' "$BO" | grep -E "SPINE BUILT AND SWAPPED|GATE FAILED" | tail -1)
case "$BL" in
  "SPINE BUILT AND SWAPPED"*) : ;;
  *) printf '%s\n' "$BO" | grep -E "FAIL|Error|Traceback" | head -6 | sed 's/^/      /'; restore "the spine build now: ${BL:-no result line}" ;;
esac
SQ() { "$VPY" -B -c "import sqlite3,sys; c=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro', uri=True); print(c.execute(sys.argv[2]).fetchone()[0])" "$SDIR/spine.db" "$1" 2>/dev/null || echo "?"; }
PARTS=$(SQ "SELECT COUNT(*) FROM sp_export WHERE role='PART_LIST'"); BUILT=$(SQ "SELECT value FROM sp_meta WHERE key='built'")
VER=$(SQ "SELECT value FROM sp_meta WHERE key='build_version'")
[ "$VER" = "S813.1" ] || restore "the new spine says build_version $VER, not S813.1" "A spine was built; the next run of its cron line rebuilds it with the old file."
say "[5/6] the spine's own selftest OK in place; the spine built now: $BUILT -- gate green; part lists set aside: $PARTS"
release_lock
say "[6/6] undo (one line): flock -w 600 $SPLOCK \\cp -p $BAK_S $ROOT/$FS"
say ""
say "$KIT: DONE. The stock record is up to date again (built $BUILT); a part copy of a purchase report can no longer replace the full one."
exit 0
