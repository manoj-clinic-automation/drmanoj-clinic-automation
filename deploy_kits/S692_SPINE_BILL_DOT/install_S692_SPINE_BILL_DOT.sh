#!/bin/bash
# =============================================================================
#  install_S692_SPINE_BILL_DOT.sh · kit S692 (01-Nov-2026, Sanjeevni session 375) · the spine's reader reads a BILL number typed in Marg
#  with a stray trailing dot ('3920.') as its digits. One Shivaaz bill of 26-Oct keyed that way made every purchase-line export of October
#  fail the spine gate from 29-Oct 09:40; the spine stayed at its last good build. Bill numbers only; batches untouched; no other reader changes.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s692kit && cp -rp /root/deploy/repo/deploy_kits/S692_SPINE_BILL_DOT /tmp/s692kit && bash /tmp/s692kit/install_S692_SPINE_BILL_DOT.sh
#  (DRY=1 before bash: every gate, the walk, the selftest and the spine proof on copies, nothing written.)
#   /root/finance/spine/marg_read.py   b47a1d62 -> TO   READER_VERSION S692.1; billno(); the dotted bill shape accepted in both purchase readers
#  THE GATE THAT DECIDES: on this box, the kit's reader re-reads the refused purchase exports from the archive and the spine is BUILT on a
#  copy of the database (the live reader fails this gate today). After placing, the live readings are re-read and the live spine rebuilt once
#  under the spine lock; it must pass. Red after placing: the file back, the stale readings back, finance restarted; the last good spine stays.
# =============================================================================
set -u
KIT="S692_SPINE_BILL_DOT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SPINE_LOCK="${SPINE_LOCK:-/tmp/spine.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
SRC="${SRC:-}"                       # the readings' source: empty = Drive (the box's way); a folder in a rehearsal
SPINE="$ROOT/finance/spine"
F="finance/spine/marg_read.py"
FROM="b47a1d626c36e2706879c41e2c316a69"
TO="$(awk -v f="$F" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s692_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
GREEN="22 of 22 green"
CONTROL="6 S692 check(s) red . 8 green"
BAK="$SPINE/marg_read.py.bak_S692_${FROM:0:8}"
STG="$SPINE/.marg_read.py.s692"
PURGE="import json,os,sys,shutil
d,keep=sys.argv[1],sys.argv[2]; os.makedirs(keep,exist_ok=True); n=0
for fn in sorted(os.listdir(d)):
    if not fn.endswith('.json'): continue
    p=os.path.join(d,fn)
    try: r=json.load(open(p))
    except Exception: continue
    if str(r.get('family') or '').startswith('PURCHASE_') and r.get('reader') != 'S692.1':
        shutil.copy2(p,os.path.join(keep,fn)); os.remove(p); n+=1
print('purchase readings of the older reader set aside for re-reading: %d' % n)"
COUNT="import json,os,sys
d=sys.argv[1]; n=0
for fn in os.listdir(d):
    if fn.endswith('.json'):
        try: n+= str(json.load(open(os.path.join(d,fn))).get('family') or '').startswith('PURCHASE_')
        except Exception: pass
print(n)"
PUTBACK="import os,sys,shutil
d,keep=sys.argv[1],sys.argv[2]; miss=[]
for fn in sorted(os.listdir(keep)) if os.path.isdir(keep) else []:
    if fn.endswith('.json') and not os.path.exists(os.path.join(d,fn)):
        shutil.copy2(os.path.join(keep,fn),os.path.join(d,fn)); miss.append(fn[:8])
print('readings not re-read (export no longer listed) -- the older reading kept: %d %s' % (len(miss), miss[:6]))"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
fhealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { rm -f "$STG"; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -B "$KDIR/walk_s692.py" "$@" 2>&1); }
src_args() { [ -n "$SRC" ] && echo "--source $SRC" || echo ""; }     # no spaces in these paths (the box, the rehearsal)
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting marg_read.py back"
  PLACED=2
  \cp -p "$BAK" "$SPINE/marg_read.py" || say "   !! could not put back $SPINE/marg_read.py"; rm -f "$STG"
  if [ -d "$SCR/stale" ]; then \cp -p "$SCR/stale"/*.json "$SPINE/readings/" 2>/dev/null && say "   the set-aside readings put back"; fi
  "$SYSTEMCTL" restart "$FSVC" || true
  say "   $SPINE/marg_read.py $(m5 "$SPINE/marg_read.py" | cut -c1-8) (expected ${FROM:0:8}); the spine stays as its last passed build left it"
  say "   finance healthz $(wait200 fhz). Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout flock; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/8] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$TO" ] || { say "!! [1/8] TO_PINS.md5 does not name $F - nothing installed"; exit 1; }
[ -f "$ROOT/$F" ] && [ -f "$DB" ] && [ -d "$SPINE/readings" ] && [ -f "$SPINE/spine_evidence.py" ] && [ -f "$SPINE/spine_build.py" ] \
  || { say "!! [1/8] $ROOT/$F, $DB, $SPINE/readings or the spine's programs are missing - nothing installed"; exit 1; }
[ "$(m5 "$ROOT/$F")" = "$TO" ] && { say "-- ALREADY INSTALLED: marg_read.py is the kit's. Nothing written. spine: $(grep -o '"status": "[^"]*' "$SPINE/spine_state.json" 2>/dev/null | cut -c12-90)"; exit 0; }
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
C=$(m5 "$ROOT/$F"); [ "$C" = "$FROM" ] || stop_unlocked "!! [2/8] $ROOT/$F is ${C:0:8}, expected ${FROM:0:8} - it changed after this kit was built: STOP, nothing installed"
say "[2/8] live pin exact: marg_read.py at its FROM ${FROM:0:8}; the spine today: $(grep -o '"gate": "[^"]*' "$SPINE/spine_state.json" 2>/dev/null | cut -c10-) $(grep -o '"passed": [a-z]*' "$SPINE/spine_state.json" 2>/dev/null)"

mkdir -p "$SCR/built" "$SCR/pyc" && chmod 700 "$SCR" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s692.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/8] the builder refused the live file - nothing installed"; }
[ "$(m5 "$SCR/built/$F")" = "$TO" ] || stop_unlocked "!! [3/8] rebuilt, marg_read.py is $(m5 "$SCR/built/$F" | cut -c1-8), not ${TO:0:8} - nothing installed"
for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$F" || stop_unlocked "!! [3/8] marg_read.py does not compile on $py - nothing installed"; done
say "[3/8] rebuilt here from this box's live bytes: at its TO pin ${TO:0:8}; compiles under both pythons"

# the walk, the control, the spine's own selftest on the kit's reader, then THE PROOF: the spine built on copies
R=$(walk --new "$SCR/built" | tail -1)
[ "$R" = "$GREEN" ] || { PLACED=2; stop_unlocked "!! [4/8] the walk on the rebuilt file is not green ($R) - nothing installed (kept in $SCR)"; }
R0=$(walk --old "$ROOT" | tail -1)
[ "$R0" = "$CONTROL" ] || { PLACED=2; stop_unlocked "!! [4/8] the control on the live file is not as expected ($R0) - nothing installed (kept in $SCR)"; }
mkdir -p "$SCR/sel/finance/spine" && cp -p "$ROOT"/finance/*.py "$SCR/sel/finance/" && cp -p "$SPINE"/*.py "$SPINE"/*.json "$SCR/sel/finance/spine/" \
  && cp -p "$SCR/built/$F" "$SCR/sel/finance/spine/marg_read.py" || stop_unlocked "!! [4/8] could not stage the spine's programs for the selftest - nothing installed"
ST=$(cd "$SCR/sel/finance/spine" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -B selftest_spine.py 2>&1 | tail -1)
case "$ST" in "SELFTEST OK"*) ;; *) PLACED=2; stop_unlocked "!! [4/8] the spine's selftest on the kit's reader: $ST - nothing installed (kept in $SCR)";; esac
copydb "$DB" "$SCR/walk.db" || stop_unlocked "!! [4/8] no copy of the database - nothing installed"
mkdir -p "$SCR/readings" && cp -p "$SPINE/readings"/*.json "$SCR/readings/" || stop_unlocked "!! [4/8] could not copy the readings - nothing installed"
N0=$("$APY" -c "$COUNT" "$SCR/readings"); [ "${N0:-0}" -gt 0 ] || stop_unlocked "!! [4/8] no purchase readings in the live store - nothing installed"
PG=$("$APY" -c "$PURGE" "$SCR/readings" "$SCR/stale_proof" 2>&1 | tail -1)
EV=$(cd "$SCR/sel/finance/spine" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -B spine_evidence.py $(src_args) --out "$SCR/readings" --limit 2000 2>&1 | tail -1)
case "$EV" in *"failed 0,"*) ;; *) PLACED=2; stop_unlocked "!! [4/8] the kit's reader could not re-read the archive ($EV) - nothing installed (kept in $SCR)";; esac
PB=$("$APY" -c "$PUTBACK" "$SCR/readings" "$SCR/stale_proof" 2>&1 | tail -1)
N1=$("$APY" -c "$COUNT" "$SCR/readings"); [ "$N1" -ge "$N0" ] || { PLACED=2; stop_unlocked "!! [4/8] purchase readings before $N0, after the re-read $N1 - nothing installed (kept in $SCR)"; }
case "$EV" in *" read 0 "*|*"listed 0,"*) PLACED=2; stop_unlocked "!! [4/8] the archive re-read read nothing ($EV) - nothing installed (kept in $SCR)";; esac
BL=$(cd "$SCR/sel/finance/spine" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -B spine_build.py --readings "$SCR/readings" --out "$SCR/spine_proof.db" --finance-db "$SCR/walk.db" > "$SCR/build_proof.txt" 2>&1; tail -1 "$SCR/build_proof.txt")
grep -E '^  (ok|FAIL) ' "$SCR/build_proof.txt" | grep -E 'purchase line export|FAIL' | cut -c1-150 | sed 's/^/         /'
case "$BL" in "SPINE BUILT AND SWAPPED"*) ;; *) PLACED=2; stop_unlocked "!! [4/8] THE PROOF: the spine does not build with the kit's reader ($BL) - nothing installed (kept in $SCR)";; esac
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/8] finance healthz $f0 before the install - nothing installed"
say "[4/8] the walk: $GREEN; the control on the live file: $R0; $ST; $PG; the archive re-read ($EV); $PB; purchase readings $N0 before, $N1 after; THE PROOF: the spine BUILT on copies with the kit's reader; finance healthy ($f0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk, the selftest and the spine proof green; NOTHING written"; exit 0; fi

{ \cp -p "$ROOT/$F" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop_unlocked "!! [5/8] could not write the backup $BAK - nothing placed"
{ cat "$SCR/built/$F" > "$STG" && [ "$(m5 "$STG")" = "$TO" ]; } || { rm -f "$STG"; stop_unlocked "!! [5/8] could not stage marg_read.py - nothing placed"; }
chmod --reference="$ROOT/$F" "$STG" 2>/dev/null; chown --reference="$ROOT/$F" "$STG" 2>/dev/null
PLACED=1
mv -f "$STG" "$ROOT/$F" || restore "the rename"
[ "$(m5 "$ROOT/$F")" = "$TO" ] || restore "read back"
find "$SPINE" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[5/8] placed and read back: marg_read.py at ${TO:0:8} (backup $BAK)"

# the live readings re-read and the live spine rebuilt ONCE, the way the cron does it, under the spine lock
T0I="$(date +%s)"
N0L=$("$APY" -c "$COUNT" "$SPINE/readings")
cat > "$SCR/live_cycle.sh" <<EOC
set -u
cd '$SPINE' || exit 9
'$APY' -c "\$PURGE_SRC" '$SPINE/readings' '$SCR/stale' > '$SCR/purge.txt' 2>&1 || exit 8
'$VPY' -B spine_evidence.py $(src_args) || exit 7
'$APY' -c "\$PUTBACK_SRC" '$SPINE/readings' '$SCR/stale' > '$SCR/putback.txt' 2>&1 || exit 6
[ "\$('$APY' -c "\$COUNT_SRC" '$SPINE/readings')" -ge "$N0L" ] || exit 5
'$VPY' -B spine_build.py --readings readings --out spine.db --finance-db '$DB'
EOC
export PURGE_SRC="$PURGE" PUTBACK_SRC="$PUTBACK" COUNT_SRC="$COUNT"
(flock -w 240 "$SPINE_LOCK" bash "$SCR/live_cycle.sh" >> "$SPINE/spine.log" 2>&1); RC=$?
PG2="$(tail -1 "$SCR/purge.txt" 2>/dev/null)"; PB2="$(tail -1 "$SCR/putback.txt" 2>/dev/null)"
[ "$RC" = 0 ] || restore "the live re-read and rebuild returned $RC (5 = a purchase reading did not come back; see $SPINE/spine.log; purge: $PG2)"
mkdir -p "$SPINE/readings_pre_S692" && cp -p "$SCR/stale"/*.json "$SPINE/readings_pre_S692/" 2>/dev/null
PASSED=$(grep -o '"passed": [a-z]*' "$SPINE/spine_state.json" 2>/dev/null | awk '{print $2}')
LS=$(grep -o '"last_success_iso": "[^"]*' "$SPINE/spine_state.json" 2>/dev/null | cut -c22-)
LSI=$("$APY" -c "import datetime as d,sys; print(int(d.datetime.fromisoformat(sys.argv[1]).timestamp()))" "$LS" 2>/dev/null || echo 0)
[ "$PASSED" = true ] && [ "${LSI:-0}" -ge $((T0I - 5)) ] || restore "the live spine gate after the rebuild: passed=$PASSED last_success=$LS"
say "[6/8] $PG2; $PB2; the older readings kept in $SPINE/readings_pre_S692/; the live readings re-read and the spine rebuilt under $SPINE_LOCK: GATE PASSED, last good $LS"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JR="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[7/8] $FSVC restarted (the reports tile reads with the kit's reader too): healthz $c1; journal clean; no data step"
R=$(walk --new "$ROOT" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 8 ] && R="rehearsal: a forced red at [8/8]"      # the rehearsal's hook only; unset on a real install
[ "$R" = "$GREEN" ] || restore "the walk on the placed file: $R"
release_lock
say "[8/8] the walk on the placed file: $R; the build lock released"
say "undo (one line): \\cp -p $BAK $SPINE/marg_read.py && $SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. The spine builds again; a bill number typed with a stray dot is read as its digits."
exit 0
