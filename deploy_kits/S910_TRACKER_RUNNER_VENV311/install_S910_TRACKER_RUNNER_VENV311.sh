#!/bin/bash
# install_S910_TRACKER_RUNNER_VENV311.sh -- S910 (the parent, S495, 20-Nov-2026): the runner to its own Python 3.11; the engine
# back to the clinic PC's exact bytes. Session 3 of the Follow-up Tracker's move (plan S492_TRACKER_TO_SERVER_PLAN_FINAL).
# NOTHING SWITCHES: /root/followup_tracker/OFF stays present; the clinic PC still makes and sends the list.
#
# WHAT ONE RUN DOES
#   [1/6] the kit's SUMS.md5 gate
#   [2/6] the ground: seeded; OFF present; /root/followup_tracker/venv (S904) answers with numpy 2.2.6 / pandas 2.3.3 / openpyxl 3.1.5;
#         the engine reads b5b01d87 (S900's line + S908) or 6929fc15 (the PC's); the replay copy 8d56e084 or c1f7b50f;
#         the two '# S895_TRACKER' cron lines are there; the last Replay 2 report (S908's content hashes) is there
#   [3/6] S900's one line taken out of the engine and the replay copy (future_out_s910.py; .bak_S910_<from> beside each);
#         the engine must then read 6929fc15 = the PC's processor.py byte for byte, the replay copy c1f7b50f -- else put back, STOP
#   [4/6] under the 3.11 venv: replay2 --import-check (0 errors) and server_runner.py --selftest (0 fails) -- else put back, STOP
#   [5/6] Replay 2 under the 3.11 venv on the PC's bytes: every compared run's content hash must EQUAL S908's (24 of 24) -- else put back, STOP
#   [6/6] the two cron lines re-pointed /root/wa/venv/bin/python3 -> /root/followup_tracker/venv/bin/python3 (runner still OFF);
#         then a DRY pass on a COPY of the tracker folder with OFF lifted there only (nothing written on the live side)
#   then the watch, read only: the receiver's upload log (today, by origin), the push unit's Do_Not_Call lines, the logs folder
#   --undo : the cron lines back to /root/wa/venv; the engine and the replay copy back from their .bak_S910_ files
set -u
KIT="S910_TRACKER_RUNNER_VENV311"; KDIR="$(cd "$(dirname "$0")" && pwd)"
FUT="${FUT:-/root/followup_tracker}"; WA="${WA:-/root/wa}"; OLDVENV="${OLDVENV:-/root/wa/venv}"; NEWVENV="${NEWVENV:-$FUT/venv}"
NPY="${NPY:-$NEWVENV/bin/python3}"; CRONTAB="${CRONTAB:-crontab}"; MARK="# S895_TRACKER"; MIN_CRON=20
ENG="$FUT/processor.py"; OLD="$FUT/replay/processor.py.bak_S777_0e7c129f"
ENG_BOX="b5b01d87"; ENG_PC="6929fc15"; OLD_BOX="8d56e084"; OLD_PC="c1f7b50f"
REPORT="$FUT/logs/REPLAY2_REPORT.txt"; BEFORE="$FUT/logs/REPLAY2_REPORT_before_S910.txt"; MIN_RUNS=24
UPLOG="${UPLOG:-$WA/followup-inbox/.uploads.log}"; PUSH_UNIT="${PUSH_UNIT:-clinic-followup-push.service}"
SCR="$(mktemp -d /tmp/s910_inst.XXXXXX)"; trap 'rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null' EXIT
m8() { md5sum "$1" 2>/dev/null | cut -c1-8; }
say() { echo "$@"; }
stop() { say "$1"; exit 1; }
cron_read() { "$CRONTAB" -l > "$SCR/cron.cur" 2>/dev/null && [ "$(grep -c . "$SCR/cron.cur")" -ge "$MIN_CRON" ]; }
pyn() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PYV_TIMEOUT:-3600}" "$NPY" -W ignore -B "$@" 2>&1); }
repoint() {  # $1 = from path, $2 = to path: the two S895 lines only, the crontab's length unchanged
  cron_read || { say "!! the crontab could not be read whole - cron lines left as they are"; return 1; }
  awk -v from="$1" -v to="$2" -v mark="$MARK" 'index($0, mark) { n = index($0, from); if (n) $0 = substr($0, 1, n-1) to substr($0, n+length(from)) } { print }' "$SCR/cron.cur" > "$SCR/cron.new"
  [ "$(grep -c . "$SCR/cron.new")" = "$(grep -c . "$SCR/cron.cur")" ] || { say "!! the rewritten crontab is a different length - left as it is"; return 1; }
  "$CRONTAB" "$SCR/cron.new" || return 1
  [ "$("$CRONTAB" -l | grep -F "$MARK" | grep -c "$2")" = 2 ] || { if "$CRONTAB" "$SCR/cron.cur"; then say "!! the rewritten crontab did not read back - the old one put back"; else say "!! the rewritten crontab did not read back AND the old one could not be restored - run crontab -l now and tell Claude"; fi; return 1; }
}
MADE=""   # the backups THIS run made: "<backup>:<file>" pairs
putback() {  # only what this run made goes back
  [ -n "$MADE" ] || { say "   nothing to put back (this run changed no file): engine $(m8 "$ENG"), replay copy $(m8 "$OLD")"; return; }
  for pair in $MADE; do mv -f "${pair%%:*}" "${pair#*:}"; done; MADE=""
  say "   put back: engine $(m8 "$ENG"), replay copy $(m8 "$OLD")"
}
hashes() { sed -nE 's/^(#[0-9]+) .*content ([0-9a-f]+).*/\1 \2/p' "$1" | sort -V; }

if [ "${1:-}" = "--undo" ]; then
  cron_read || stop "!! --undo: the crontab could not be read whole - nothing touched. Tell Claude."
  if grep -F "$MARK" "$SCR/cron.cur" | grep -q "$NEWVENV"; then repoint "$NEWVENV/bin/python3" "$OLDVENV/bin/python3" && say "   cron lines back to $OLDVENV" || stop "!! --undo: the cron lines could not be put back - nothing else touched. Tell Claude."; else say "   cron lines already on $OLDVENV"; fi
  n=0; for f in "$ENG" "$OLD"; do b="$(ls "$f".bak_S910_* 2>/dev/null | head -1)"; [ -n "$b" ] && { mv -f "$b" "$f"; n=$((n+1)); }; done
  say "$KIT: UNDONE ($n file(s) back: engine $(m8 "$ENG"), replay copy $(m8 "$OLD"); runner on $OLDVENV, still OFF). $([ "$(m8 "$ENG")" = "$ENG_PC" ] && echo 'NOTE: the engine is the PC'"'"'s bytes - on /root/wa/venv (3.9) it will not import; run S900'"'"'s py39_future.py --apply on it, or install this kit again.')"
  exit 0
fi

cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"
say "   [1/6] kit sums ok"
[ -f "$FUT/SEEDED_AT" ] || stop "!! [2/6] $FUT is not seeded - STOP. Tell Claude."
[ -e "$FUT/OFF" ] || stop "!! [2/6] $FUT/OFF is ABSENT - STOP. Tell Claude."
[ -x "$NPY" ] || stop "!! [2/6] $NPY is not there (S904's venv) - STOP. Tell Claude."
VERS="$("$NPY" -c 'import importlib.metadata as m, sys; print(sys.version.split()[0]+": "+", ".join(p+" "+m.version(p) for p in ("numpy","pandas","openpyxl")))' 2>&1)"
echo "$VERS" | grep -q "numpy 2.2.6, pandas 2.3.3, openpyxl 3.1.5" || stop "!! [2/6] the venv reads $VERS - not the PC's versions - STOP. Tell Claude."
case "$(m8 "$ENG")" in "$ENG_BOX"|"$ENG_PC") ;; *) stop "!! [2/6] $ENG is $(m8 "$ENG"), neither S908's $ENG_BOX nor the PC's $ENG_PC - STOP. Tell Claude.";; esac
[ -f "$OLD" ] || stop "!! [2/6] $OLD is not there - STOP. Tell Claude."
case "$(m8 "$OLD")" in "$OLD_BOX"|"$OLD_PC") ;; *) stop "!! [2/6] the replay copy is $(m8 "$OLD"), neither $OLD_BOX nor $OLD_PC - STOP. Tell Claude.";; esac
[ -f "$FUT/replay2_s897.py" ] && grep -q 'content_hash' "$FUT/replay2_s897.py" || stop "!! [2/6] replay2_s897.py (S905+) is not there - STOP. Tell Claude."
[ -f "$FUT/server_runner.py" ] || stop "!! [2/6] $FUT/server_runner.py is not there - STOP. Tell Claude."
cron_read || stop "!! [2/6] the crontab could not be read whole - STOP"
[ "$(grep -cF "$MARK" "$SCR/cron.cur")" = 2 ] || stop "!! [2/6] expected 2 '$MARK' cron lines, found $(grep -cF "$MARK" "$SCR/cron.cur") - STOP. Tell Claude."
ON_OLD="$(grep -F "$MARK" "$SCR/cron.cur" | grep -c "$OLDVENV/bin/python3")"; ON_NEW="$(grep -F "$MARK" "$SCR/cron.cur" | grep -c "$NEWVENV/bin/python3")"
if [ "$(m8 "$ENG")" = "$ENG_PC" ] && [ "$(m8 "$OLD")" = "$OLD_PC" ] && [ "$ON_NEW" = 2 ]; then say "-- $KIT is already installed (engine $ENG_PC, replay copy $OLD_PC, runner on $NEWVENV, OFF $([ -e "$FUT/OFF" ] && echo present || echo ABSENT)). Nothing done."; exit 0; fi
[ "$ON_OLD" = 2 ] || [ "$ON_NEW" = 2 ] || stop "!! [2/6] the two cron lines name neither venv twice ($ON_OLD on $OLDVENV, $ON_NEW on $NEWVENV) - STOP. Tell Claude."
[ -f "$REPORT" ] || stop "!! [2/6] $REPORT (S908's Replay 2) is not there - STOP. Tell Claude."
BASE="$REPORT"; [ -f "$BEFORE" ] && BASE="$BEFORE"   # S908's hashes: the kept copy once one exists
hashes "$BASE" > "$SCR/h_before.txt"; NB="$(grep -c . "$SCR/h_before.txt")"
[ "$NB" -ge "$MIN_RUNS" ] || stop "!! [2/6] $BASE carries $NB content hash(es), fewer than $MIN_RUNS - STOP. Tell Claude."
say "   [2/6] seeded; OFF present; venv $VERS; engine $(m8 "$ENG"), replay copy $(m8 "$OLD"); cron lines: $ON_OLD on the old venv, $ON_NEW on the new; last Replay 2: $NB content hashes"

# [3/6] S900's line out
for f in "$ENG" "$OLD"; do
  if pyn "$KDIR/future_out_s910.py" "$f" >/dev/null; then say "   [3/6] $(basename "$f") already the PC's shape"; continue; fi
  b="$f.bak_S910_$(m8 "$f")"; cp -p "$f" "$b" || { say "!! [3/6] could not back up $f - STOP"; putback; exit 1; }; MADE="$MADE $b:$f"
  out="$(pyn "$KDIR/future_out_s910.py" "$f" --apply)"; [ $? = 0 ] || { say "!! [3/6] $out"; putback; exit 1; }
  say "   [3/6] $out"
done
[ "$(m8 "$ENG")" = "$ENG_PC" ] || { say "!! [3/6] the engine reads $(m8 "$ENG"), not the PC's $ENG_PC - STOP"; putback; exit 1; }
[ "$(m8 "$OLD")" = "$OLD_PC" ] || { say "!! [3/6] the replay copy reads $(m8 "$OLD"), not $OLD_PC - STOP"; putback; exit 1; }
say "   [3/6] engine $ENG_PC = the PC's processor.py byte for byte; replay copy $OLD_PC"

# [4/6] imports and the self-test under 3.11
ic="$(FUT_ROOT="$FUT" pyn "$FUT/replay2_s897.py" --import-check | tail -1)"
[ "$ic" = "import-check: 0 error(s) under $NPY" ] || { say "!! [4/6] $ic - STOP"; putback; exit 1; }
st="$(FUT_ROOT="$FUT" pyn "$FUT/server_runner.py" --selftest 2>&1 | tail -1)"
[ "$st" = "selftest: 0 failure(s)" ] || { say "!! [4/6] server_runner --selftest: $st - STOP"; putback; exit 1; }
say "   [4/6] $ic; selftest: $st"

# [5/6] Replay 2 on the PC's bytes under 3.11 -- the content hashes must equal S908's
NEWREP="$SCR/REPLAY2_REPORT_s910.txt"
rp="$(FUT_ROOT="$FUT" FU_INBOX_DIR="$WA/followup-inbox" REPLAY2_SCRATCH="$SCR/replay" pyn "$FUT/replay2_s897.py" --run --report "$NEWREP")"
rs="$(echo "$rp" | grep '^RESULT:' | tail -1)"
[ -n "$rs" ] && [ -s "$NEWREP" ] || { say "!! [5/6] Replay 2 did not finish or wrote no report: $(echo "$rp" | tail -1 | cut -c1-200) - STOP"; putback; exit 1; }
hashes "$NEWREP" > "$SCR/h_after.txt"; NA="$(grep -c . "$SCR/h_after.txt")"
if ! cmp -s "$SCR/h_before.txt" "$SCR/h_after.txt"; then
  say "!! [5/6] the content hashes differ from S908's ($NB before, $NA now) - the live report untouched:"; diff "$SCR/h_before.txt" "$SCR/h_after.txt" | head -6 | sed 's/^/         /'
  say "         $rs"; putback; exit 1
fi
[ -f "$BEFORE" ] || cp -p "$REPORT" "$BEFORE" || { say "!! [5/6] could not keep S908's report as $BEFORE - STOP"; putback; exit 1; }
cp "$NEWREP" "$REPORT" || { say "!! [5/6] could not write $REPORT - STOP"; putback; exit 1; }
say "   [5/6] REPLAY 2 under $NEWVENV on the PC's bytes: $NA of $NB content hashes EQUAL S908's; $rs"

# [6/6] the runner's python; a dry pass on a copy with OFF lifted there
if [ "$ON_NEW" = 2 ]; then say "   [6/6] cron lines already on $NEWVENV"; else
  repoint "$OLDVENV/bin/python3" "$NPY" || { say "!! [6/6] the cron lines could not be re-pointed - the engine is the PC's bytes and the runner (OFF) still names $OLDVENV, where it will not import - putting the engine back"; putback; exit 1; }
  say "   [6/6] S895's two cron lines now on $NPY (runner still OFF: $([ -e "$FUT/OFF" ] && echo present || echo ABSENT))"
fi
COPY="$SCR/fut_copy"; mkdir -p "$COPY"
SZ="$(cd "$FUT" && du -sm --exclude=venv --exclude=logs . 2>/dev/null | cut -f1)"
if [ "${SZ:-0}" -gt 2048 ]; then say "   [6/6] the tracker folder is ${SZ} MB - too big to copy for a dry pass; skipped (the install stands)"; else
  ( cd "$FUT" && tar --exclude=./venv --exclude=./logs --exclude='./*.bak_*' --exclude='./*.s910' --exclude=./OFF -cf - . ) | ( cd "$COPY" && tar -xf - ) 2>/dev/null
  mkdir -p "$COPY/logs"; LDB="${FINANCE_DB:-/root/finance/finance.db}"; LST="${DOCTERZ_EXPORT_STORE:-/root/finance/docterz_exports}"
  DBH="$(m8 "$LDB")"; STL="$(ls -la --full-time "$LST" 2>/dev/null | md5sum | cut -c1-8)"
  dry="$(FUT_ROOT="$COPY" FUT_OFF="$COPY/OFF" FUT_ALL_OFF="$COPY/ALL_OFF" pyn "$COPY/server_runner.py" --dry-run 2>&1 | tail -6)"
  say "   [6/6] DRY pass on a copy (${SZ} MB) with OFF lifted there - the live folder untouched:"; echo "$dry" | cut -c1-160 | sed 's/^/         /'
  if [ ! -f "$LDB" ] || [ ! -d "$LST" ]; then say "         (finance.db / the export store not at their usual paths - not checked)"; elif [ "$DBH" = "$(m8 "$LDB")" ] && [ "$STL" = "$(ls -la --full-time "$LST" 2>/dev/null | md5sum | cut -c1-8)" ]; then say "         finance.db and the export store: unchanged by the dry pass"; else say "   !! finance.db or the export store CHANGED during the dry pass - tell Claude (the install itself stands)"; fi
fi
say "$KIT: DONE. Engine $ENG_PC (= the PC's), runner on $NEWVENV ($VERS), OFF $([ -e "$FUT/OFF" ] && echo present || echo ABSENT) - nothing switched. Report: $REPORT (S908's kept as $BEFORE)."

# the watch (read only)
TODAY="$(date +%Y-%m-%d)"; npc="$(grep -c "^$TODAY.* pc " "$UPLOG" 2>/dev/null)"; nsv="$(grep -c "^$TODAY.* server " "$UPLOG" 2>/dev/null)"
say "   -- watch: uploads today by origin: ${npc:-0} pc, ${nsv:-0} server; last: $(tail -1 "$UPLOG" 2>/dev/null | cut -c1-80)"
say "   -- watch: push unit today: $(journalctl -u "$PUSH_UNIT" --since today --no-pager 2>/dev/null | grep -iE 'Do-not-call|Do_Not_Call' | tail -2 | cut -c1-100 | tr '\n' ' ' || echo 'no journal line')"
say "   -- watch: $FUT/logs holds: $(ls "$FUT/logs" 2>/dev/null | tr '\n' ' ')"
exit 0
