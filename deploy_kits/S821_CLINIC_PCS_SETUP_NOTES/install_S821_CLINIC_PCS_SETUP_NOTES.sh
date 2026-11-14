#!/bin/bash
# =============================================================================
#  install_S821_CLINIC_PCS_SETUP_NOTES.sh · kit S821 (session S453, the parent, 14-Nov-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S821_CLINIC_PCS_SETUP_NOTES/install_S821_CLINIC_PCS_SETUP_NOTES.sh
#  DRY=1 before bash: every gate, the rebuild, the walk and its control -- NOTHING changed.
#  --undo after the file name: the file this kit replaced is put back (only if the live file is this kit's and this
#  kit's backup is the file it replaced).  DRY=1 with --undo: says what it would do, changes nothing.
#
#  THE OWNER'S WORD (14-Nov-2026 05:57 IST): the Medical PC's card must say how that PC is set up now, and that its kit
#  keeps itself current.  On https://followup.dr-manoj.in/finance/pcs the Medical PC's card gets a block 'How this PC is
#  set up now' (the cable and the Wi-Fi dongle, which USB port holds what), and the Medical and Reception cards say how
#  their kits are kept current.  One file: /root/finance/pc_kits.py 9c2b3615 -> 4191e447; clinic-finance is restarted.
#  No route, no door, no logic changed; no database change.
# =============================================================================
set -u
KIT="S821_CLINIC_PCS_SETUP_NOTES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/root/wa/venv/bin/python3}"                # runs the rebuild and the walk (it has Flask)
APY="${APY:-/usr/bin/python3}"                       # the interpreter clinic-finance itself runs on (its unit file)
F="${F:-/root/finance/pc_kits.py}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-/root/s821_backup}"
SVC="${SVC:-clinic-finance}"
BASE="${BASE:-http://127.0.0.1:8106}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
HEALTH="/finance/healthz"
FROM="9c2b3615bced5cd425b345d60f3daa15"
TO="4191e4471d2c51147b383347418f53ac"
BAK="$BK/pc_kits.py.bak_S821_${FROM:0:8}"
STG="$(dirname "$F")/.pc_kits.py.s821"
W="${TMPW:-/tmp}/s821_inst_$$"
TOOK_LOCK=0
PLACED=0

m5() { md5sum "$1" 2>/dev/null | cut -c1-32; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$STG"; rm -rf "${W:?}"; release_lock; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
hz() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$BASE$HEALTH"; }
wait200() { local c=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c=$(hz); [ "$c" = 200 ] && break; done; echo "$c"; }
compiles() {      # $1 = a python file; on the walk's python and, when it is there, on the service's own
  PYTHONPYCACHEPREFIX="$W/pyc" "$PY" -W ignore -m py_compile "$1" || return 1
  if [ -x "$APY" ]; then PYTHONPYCACHEPREFIX="$W/pyc" "$APY" -W ignore -m py_compile "$1" || return 1; fi
  return 0
}
# After the new file is in place, ANY failure comes here: the old file back, the service restarted, and what is
# actually in place said as it is.
put_back() {
  PLACED=0
  echo "!! RED after the new file was placed ($1) -- putting the old file back"
  \cp -fp "$BAK" "$F"
  "$SYSTEMCTL" restart "$SVC" || echo "   !! the restart command itself failed"
  local c n; c=$(wait200); n=$(m5 "$F")
  if [ "$n" = "$FROM" ]; then echo "   The old file is back: pc_kits.py is ${n:0:8}, as it was before this kit."
  else echo "   !! THE OLD FILE IS NOT BACK: pc_kits.py is now ${n:-missing}, expected $FROM. Its backup is $BAK"; fi
  if [ "$c" = 200 ]; then echo "   $SVC was restarted and answers (health 200)."
  else echo "   !! $SVC was restarted but does NOT answer (health $c)."; fi
  echo "   Send a photo of this screen to Claude."
  exit 1
}
on_signal() { [ "$PLACED" = 1 ] && put_back "the install was interrupted"; echo "!! interrupted. Nothing was changed."; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || { echo "!! STOPPED: the kit folder was not found. Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
{ [ "$(grep -c . SUMS.md5 2>/dev/null)" = 6 ] && md5sum -c SUMS.md5 >/dev/null 2>&1; } || stop "the kit's files do not match SUMS.md5 -- the kit did not arrive whole"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 pc_kits.py)" = "$TO" ] || stop "the kit's pc_kits.py is not the file this installer was written for"
command -v "$PY" >/dev/null 2>&1 || stop "the python $PY is not there"
if mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
elif [ -d "$LOCK" ]; then
  echo "!! STOPPED: another install is running (lock $LOCK, held by: $(cat "$LOCK/owner" 2>/dev/null || echo unknown))."
  echo "   Nothing was changed. Wait five minutes and run the line again; if it says this again, send a photo of this screen to Claude."
  exit 3
else stop "the lock $LOCK could not be made"; fi
mkdir -p "$W" && chmod 700 "$W" || stop "the working folder $W could not be made"

# ----------------------------------------------------------------------------------------------------------- undo
if [ "${1:-}" = "--undo" ]; then
  echo "[undo]"
  NOW=$(m5 "$F")
  [ "$NOW" = "$TO" ] || stop "pc_kits.py is ${NOW:-missing}, not this kit's file ${TO:0:8} -- there is nothing of this kit to undo, or a later kit has changed the file since"
  [ -f "$BAK" ] || stop "this kit's backup is not there ($BAK)"
  [ "$(m5 "$BAK")" = "$FROM" ] || stop "the backup $BAK is $(m5 "$BAK" | cut -c1-8), not the file this kit replaced (${FROM:0:8})"
  if [ "${DRY:-0}" = 1 ]; then echo "-- DRY RUN: --undo would put $BAK back as $F (${TO:0:8} -> ${FROM:0:8}) and restart $SVC. NOTHING was changed."; exit 0; fi
  { \cp -fp "$BAK" "$STG" && [ "$(m5 "$STG")" = "$FROM" ]; } || stop "the backup could not be copied beside the live file"
  mv -f "$STG" "$F" || echo "   !! the old file could not be moved into place"
  NOW=$(m5 "$F")
  [ "$NOW" = "$FROM" ] || stop "after the undo pc_kits.py is ${NOW:-missing}, NOT the old file $FROM" "The undo did NOT complete and $SVC was NOT restarted; the backup is still $BAK."
  echo "    pc_kits.py put back: ${TO:0:8} -> ${NOW:0:8} (checked)"
  "$SYSTEMCTL" restart "$SVC" || echo "   !! the restart command itself failed"
  c=$(wait200)
  [ "$c" = 200 ] || stop "the old file is back (checked), but $SVC does not answer after its restart (health $c)" "The file is the old one; the service needs a look."
  echo "    $SVC restarted, health $c"
  echo "UNDONE. The Clinic PCs page is as it was before this kit."
  exit 0
fi

# -------------------------------------------------------------------------------------------------------- install
compiles edits_s821.py && compiles walk_s821.py && compiles pc_kits.py || stop "the kit's code does not compile on this server's python"
echo "[1] pins"
NOW=$(m5 "$F")
[ -n "$NOW" ] || stop "$F is not there"
if [ "$NOW" = "$TO" ]; then echo "    ALREADY INSTALLED (pc_kits.py ${TO:0:8}); nothing to do."; exit 0; fi
[ "$NOW" = "$FROM" ] || stop "pc_kits.py is ${NOW:0:8}, not ${FROM:0:8} this kit was built on -- the file changed after the kit was made"
echo "    pc_kits.py ${FROM:0:8}, the file this kit was built on"

echo "[2] rebuild from the live bytes"
"$PY" -W ignore -B edits_s821.py "$F" "$W/rebuilt.py" "$KDIR/pc_kits.py" > "$W/edits.txt" 2>&1 || { sed 's/^/    /' "$W/edits.txt"; stop "the kit's file is not exactly the live file plus this kit's edits"; }
[ "$(m5 "$W/rebuilt.py")" = "$TO" ] || stop "rebuilt from the live file, pc_kits.py is not ${TO:0:8}"
sed 's/^/  /' "$W/edits.txt"

echo "[3] the walk (made-up kits and health rows; nothing of the live system is touched) and its control"
mkdir -p "$W/old" "$W/new" && \cp -p "$F" "$W/old/pc_kits.py" && \cp "$W/rebuilt.py" "$W/new/pc_kits.py" || stop "the walk's folders could not be made"
[ -f "$(dirname "$F")/setup_notes.py" ] && \cp -p "$(dirname "$F")/setup_notes.py" "$W/old/setup_notes.py"
walk() { ( cd "$W" && PYTHONPYCACHEPREFIX="$W/pyc" timeout 300 "$PY" -W ignore -B "$KDIR/walk_s821.py" --code "$1" --old "$W/old" --scratch "$W/walk" $2 2>&1 ); }
O=$(walk "$W/new" ""); WK=$?; R=$(printf '%s\n' "$O" | tail -1)
{ [ "$WK" = 0 ] && [ "${R#WALK S821 GREEN: }" != "$R" ]; } || { printf '%s\n' "$O" | grep -E "FAIL|Error|COULD NOT" | head -8 | sed 's/^/    /'; stop "the walk is not green: $R"; }
echo "    $R"
O0=$(walk "$W/old" "--control"); WC=$?; R0=$(printf '%s\n' "$O0" | tail -1)
{ [ "$WC" = 0 ] && [ "${R0#CONTROL S821 RED as it must be}" != "$R0" ]; } || stop "the control did not go red on the live file -- the walk cannot tell old from new: $R0"
echo "    $R0"
if [ "${DRY:-0}" = 1 ]; then echo "-- DRY RUN: every gate, the rebuild, the walk and its control are green. NOTHING was changed."; exit 0; fi

echo "[4] backup -> $BK"
c0=$(hz); [ "$c0" = 200 ] || stop "$SVC does not answer BEFORE the install (health $c0) -- this kit will not install over a service that is already down"
mkdir -p "$BK" && chmod 700 "$BK" || stop "the backup folder $BK could not be made"
{ \cp -fp "$F" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop "the backup could not be written byte-exact"
echo "    $BAK (${FROM:0:8}, checked)"

echo "[5] placed"
{ \cp -f "$KDIR/pc_kits.py" "$STG" && chmod --reference="$F" "$STG" && [ "$(m5 "$STG")" = "$TO" ]; } || stop "the new file could not be copied beside the live one"
chown --reference="$F" "$STG" 2>/dev/null
PLACED=1
mv -f "$STG" "$F" || put_back "the new file could not be moved into place"
[ "$(m5 "$F")" = "$TO" ] || put_back "the file did not land byte-exact"
compiles "$F" || put_back "the placed file does not compile"
echo "    pc_kits.py ${FROM:0:8} -> ${TO:0:8} (checked; it compiles)"

echo "[6] $SVC restarted and checked"
"$SYSTEMCTL" restart "$SVC" || put_back "the restart of $SVC failed"
c1=$(wait200); [ "$c1" = 200 ] || put_back "health $c1 after the restart"
"$SYSTEMCTL" is-active --quiet "$SVC" || put_back "$SVC is not active"
[ "$(m5 "$F")" = "$TO" ] || put_back "the file changed during the restart"
PLACED=0
release_lock
echo "    active · health $c1 · restarted $(TZ=Asia/Kolkata date '+%d-%b-%Y %H:%M IST')"

echo "[7] what you will see"
echo "    https://followup.dr-manoj.in/finance/pcs"
echo "    The Medical PC's card has a new box, 'How this PC is set up now': the cable and the Wi-Fi dongle, which USB port"
echo "    holds the dongle and which the pen drive, and to put them back the same way. Under it, the kit line says the kit"
echo "    is checked every night and repacks itself. The Reception PC's kit line says its kit is checked every night too."
echo "[8] pins and undo"
echo "    $(md5sum "$F")"
echo "    undo: bash $KDIR/install_${KIT}.sh --undo"
echo "DONE."
exit 0
