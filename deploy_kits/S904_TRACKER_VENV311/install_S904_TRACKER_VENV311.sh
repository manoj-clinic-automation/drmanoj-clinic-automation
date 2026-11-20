#!/bin/bash
# install_S904_TRACKER_VENV311.sh -- S904 (the parent, S493, 20-Nov-2026): the tracker's own Python on the box.
#
# WHY. Replay 2 (S897-S903) found the engine on the box makes the same ledgers as the PC and the same workbook save the Call
# Sheet's LAST rows: a capped group of equal-priority rows whose members the box's numpy 2.0.2 picks differently from the PC's.
# The box's only Python is 3.9 (numpy stops at 2.0.2 there). The assistant's VM -- Python 3.10, pandas 2.3.3, numpy 2.2.6,
# openpyxl 3.1.5 -- reproduced the PC 30 of 30 (Replay 1). So the tracker gets its own venv on the box with those versions.
#
# WHAT ONE RUN DOES (nothing live changes until [6/6], and only on a green replay):
#   [1/6] the kit's SUMS.md5 gate
#   [2/6] S897 seeded; OFF present; S900 in place (processor.py bade3c1a, its .bak_S900_f1c02736 beside); the two S895 cron lines
#   [3/6] python3.11: already on the box, or installed by dnf (python3.11 + python3.11-pip)
#   [4/6] /root/followup_tracker/venv built from python3.11: numpy==2.2.6 pandas==2.3.3 openpyxl==3.1.5 gspread requests;
#         the versions read back; replay2 --import-check under it (0 errors or STOP)
#   [5/6] Replay 2 under the new venv (the engine still with S900's line -- harmless on 3.11)
#   [6/6] GREEN (0 fail) -> the engine back to the PC's bytes (S900's .bak files moved back: processor.py f1c02736, the replay
#         copy 0e7c129f), import-check again under the new venv, the two S895 cron lines re-pointed from /root/wa/venv to the
#         new venv (the runner stays OFF), one replay run (#7) to confirm. NOT GREEN -> nothing of [6/6]; the venv stays (harmless).
#   --undo : the cron lines back to /root/wa/venv; S900's line back onto the engine (py39_future.py from the S900 kit folder,
#            if present; else said); the venv folder left (say so).
set -u
KIT="S904_TRACKER_VENV311"; KDIR="$(cd "$(dirname "$0")" && pwd)"
FUT="${FUT:-/root/followup_tracker}"; WA="${WA:-/root/wa}"; OLDVENV="${OLDVENV:-/root/wa/venv}"; NEWVENV="${NEWVENV:-$FUT/venv}"
NPY="$NEWVENV/bin/python3"; CRONTAB="${CRONTAB:-crontab}"; DNF="${DNF:-dnf}"; PY311="${PY311:-}"
MARK="# S895_TRACKER"; MIN_CRON=20
ENG="$FUT/processor.py"; ENG_S900="bade3c1a"; ENG_PC="f1c02736"; OLD="$FUT/replay/processor.py.bak_S777_0e7c129f"; OLD_PC="0e7c129f"; OLD_S900="44adfff8"
WANT="numpy==2.2.6 pandas==2.3.3 openpyxl==3.1.5 gspread requests"
SCR="$(mktemp -d /tmp/s904_inst.XXXXXX)"; trap 'rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null' EXIT
m8() { md5sum "$1" 2>/dev/null | cut -c1-8; }
say() { echo "$@"; }
stop() { say "$1"; exit 1; }
cron_read() { "$CRONTAB" -l > "$SCR/cron.cur" 2>/dev/null && [ "$(grep -c . "$SCR/cron.cur")" -ge "$MIN_CRON" ]; }
pyn() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PYV_TIMEOUT:-3600}" "$NPY" -W ignore -B "$@" 2>&1); }
repoint() {  # $1 = from path, $2 = to path: the two S895 lines only
  cron_read || { say "!! the crontab could not be read whole - cron lines left as they are"; return 1; }
  awk -v from="$1" -v to="$2" -v mark="$MARK" 'index($0, mark) { n = index($0, from); if (n) $0 = substr($0, 1, n-1) to substr($0, n+length(from)) } { print }' "$SCR/cron.cur" > "$SCR/cron.new"
  [ "$(grep -c . "$SCR/cron.new")" = "$(grep -c . "$SCR/cron.cur")" ] || { say "!! the rewritten crontab is a different length - left as it is"; return 1; }
  "$CRONTAB" "$SCR/cron.new" && [ "$("$CRONTAB" -l | grep -F "$MARK" | grep -c "$2")" -ge 1 ]
}
if [ "${1:-}" = "--undo" ]; then
  if cron_read && grep -F "$MARK" "$SCR/cron.cur" | grep -q "$NEWVENV"; then repoint "$NEWVENV/bin/python3" "$OLDVENV/bin/python3" && say "   cron lines back to $OLDVENV"; else say "   cron lines already on $OLDVENV"; fi
  if [ "$(m8 "$ENG")" = "$ENG_PC" ]; then
    PF="$(ls /root/deploy/repo/deploy_kits/S900_ENGINE_PY39/py39_future.py 2>/dev/null | head -1)"
    if [ -n "$PF" ]; then "$OLDVENV/bin/python3" -B "$PF" "$ENG" --apply >/dev/null 2>&1 && "$OLDVENV/bin/python3" -B "$PF" "$OLD" --apply >/dev/null 2>&1 && say "   S900's line back on the engine ($(m8 "$ENG")) and the replay copy ($(m8 "$OLD"))"; else say "   !! S900's py39_future.py not found - the engine stays at the PC's bytes ($ENG_PC); on $OLDVENV it will not import. Tell Claude."; fi
  fi
  say "$KIT: UNDONE (the venv folder $NEWVENV is left in place; harmless)"; exit 0
fi
cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"
say "   [1/6] kit sums ok"
[ -f "$FUT/SEEDED_AT" ] || stop "!! [2/6] $FUT is not seeded - STOP. Tell Claude."
[ -e "$FUT/OFF" ] || stop "!! [2/6] $FUT/OFF is ABSENT - STOP. Tell Claude."
[ "$(m8 "$ENG")" = "$ENG_S900" ] || [ "$(m8 "$ENG")" = "$ENG_PC" ] || stop "!! [2/6] $ENG is $(m8 "$ENG"), neither S900's nor the PC's - STOP. Tell Claude."
[ -f "$FUT/replay2_s897.py" ] && grep -q 'import-check' "$FUT/replay2_s897.py" || stop "!! [2/6] replay2_s897.py (S899+) is not there - STOP. Tell Claude."
cron_read || stop "!! [2/6] the crontab could not be read whole - STOP"
[ "$(grep -cF "$MARK" "$SCR/cron.cur")" = 2 ] || stop "!! [2/6] expected 2 '$MARK' cron lines, found $(grep -cF "$MARK" "$SCR/cron.cur") - STOP. Tell Claude."
say "   [2/6] seeded, OFF, engine $(m8 "$ENG"), two S895 cron lines on $(grep -F "$MARK" "$SCR/cron.cur" | grep -c "$OLDVENV")x $OLDVENV"
if [ -z "$PY311" ]; then PY311="$(command -v python3.11 || true)"; fi
if [ -z "$PY311" ]; then
  say "   [3/6] python3.11 not on the box - installing (dnf) ..."
  "$DNF" install -y -q python3.11 python3.11-pip >"$SCR/dnf.log" 2>&1 || stop "!! [3/6] dnf could not install python3.11: $(tail -2 "$SCR/dnf.log" | tr '\n' ' ') - nothing changed"
  PY311="$(command -v python3.11 || true)"; [ -n "$PY311" ] || stop "!! [3/6] python3.11 still not found after dnf - nothing changed"
fi
say "   [3/6] $PY311: $("$PY311" -c 'import sys; print(sys.version.split()[0])')"
if [ -x "$NPY" ]; then say "   [4/6] $NEWVENV exists - its packages brought to the wanted versions"; else "$PY311" -m venv "$NEWVENV" || stop "!! [4/6] venv could not be made at $NEWVENV"; fi
"$NPY" -m pip install -q --upgrade pip >"$SCR/pip.log" 2>&1 || say "   (pip itself not upgraded: $(tail -1 "$SCR/pip.log" | cut -c1-120))"
"$NPY" -m pip install -q $WANT >"$SCR/pip2.log" 2>&1 || stop "!! [4/6] pip could not install the packages: $(tail -2 "$SCR/pip2.log" | tr '\n' ' ')"
VERS="$("$NPY" -c 'import importlib.metadata as m; print(", ".join(p+" "+m.version(p) for p in ("numpy","pandas","openpyxl","gspread","requests")))' 2>&1)"
echo "$VERS" | grep -q "numpy 2.2.6, pandas 2.3.3, openpyxl 3.1.5" || stop "!! [4/6] the venv reads $VERS - not the wanted versions"
ic="$(FUT_ROOT="$FUT" pyn "$FUT/replay2_s897.py" --import-check)"; echo "$ic" | grep -v '^ok' | sed 's/^/         /'
echo "$ic" | grep -q 'import-check: 0 error' || stop "!! [4/6] the engine does not import under the new venv - nothing changed on the live side"
say "   [4/6] $NEWVENV: $VERS; the engine imports"
if [ -n "${REPLAY_CMD:-}" ]; then rp="$($REPLAY_CMD 2>&1)"; else rp="$(FUT_ROOT="$FUT" FU_INBOX_DIR="$WA/followup-inbox" REPLAY2_SCRATCH="$SCR/replay" pyn "$FUT/replay2_s897.py" --run --report "$FUT/logs/REPLAY2_REPORT.txt")"; fi
rs="$(echo "$rp" | grep '^RESULT:' | tail -1)"
say "   [5/6] REPLAY 2 under the new venv: ${rs:-did not finish -- $(echo "$rp" | tail -1 | cut -c1-200)}"
echo "$rp" | grep -E '^#[0-9]+ .* (FAIL|ORDER)' | head -8 | cut -c1-230 | sed 's/^/         /'
fails="$(echo "$rs" | sed -n 's/.*, \([0-9]*\) fail,.*/\1/p')"; passes="$(echo "$rs" | sed -n 's/^RESULT: \([0-9]*\) pass.*/\1/p')"
if [ -z "$rs" ] || [ "${fails:-1}" != 0 ] || [ "${passes:-0}" = 0 ]; then
  say "$KIT: DONE WITHOUT THE SWITCH -- the venv stands at $NEWVENV, the runner still on $OLDVENV, the engine as before; nothing live changed. Report: $FUT/logs/REPLAY2_REPORT.txt. Send Claude the lines above."; exit 0
fi
if [ "$(m8 "$ENG")" = "$ENG_S900" ]; then
  [ -f "$ENG.bak_S900_$ENG_PC" ] && [ "$(m8 "$ENG.bak_S900_$ENG_PC")" = "$ENG_PC" ] || stop "!! [6/6] S900's backup of the engine is not there - the venv stands; the engine not reverted. Tell Claude."
  mv -f "$ENG.bak_S900_$ENG_PC" "$ENG"; [ -f "$OLD.bak_S900_$OLD_PC" ] && mv -f "$OLD.bak_S900_$OLD_PC" "$OLD"
fi
[ "$(m8 "$ENG")" = "$ENG_PC" ] || stop "!! [6/6] the engine reads $(m8 "$ENG"), not the PC's $ENG_PC - STOP. Tell Claude."
ic2="$(FUT_ROOT="$FUT" pyn "$FUT/replay2_s897.py" --import-check | tail -1)"
[ "$ic2" = "import-check: 0 error(s) under $NPY" ] || stop "!! [6/6] the PC's engine does not import under the new venv ($ic2) - the cron lines NOT re-pointed. Tell Claude."
repoint "$OLDVENV/bin/python3" "$NPY" || stop "!! [6/6] the cron lines could not be re-pointed - the engine is the PC's bytes, the venv stands; the runner (OFF) still names $OLDVENV. Tell Claude."
if [ -n "${REPLAY_CMD:-}" ]; then one="(rehearsal)"; else one="$(FUT_ROOT="$FUT" FU_INBOX_DIR="$WA/followup-inbox" REPLAY2_SCRATCH="$SCR/one" pyn "$FUT/replay2_s897.py" --run --only 7 --report "$SCR/one.txt" | grep -E '^#7 ' | cut -c1-120)"; fi
say "   [6/6] engine back to the PC's bytes ($(m8 "$ENG"); replay copy $(m8 "$OLD")); S895's two cron lines now on $NPY (runner still OFF); $one"
say "$KIT: DONE. ${rs}. The tracker runs on $NEWVENV ($VERS). Report: $FUT/logs/REPLAY2_REPORT.txt"
exit 0
