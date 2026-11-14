#!/bin/bash
# =============================================================================
#  install_S822_PC_KITS_CURRENT_NEW_FILES.sh · kit S822 (session S456, the parent, 14-Nov-2026) · D972, F-1385, F-1386
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S822_PC_KITS_CURRENT_NEW_FILES/install_S822_PC_KITS_CURRENT_NEW_FILES.sh
#  DRY=1 before bash: every gate, the rebuild, the proof -- NOTHING changed.
#  --undo after the file name: the cron line out, the pull script out, the old pc_kits.py back (only if the live file is this
#  kit's and this kit's backups are there).  DRY=1 with --undo: says what it would do, changes nothing.
#
#  WHAT THIS KIT DOES ON THE SERVER (the owner's word, D972: the Clinic PCs' set-ups stay current by themselves):
#   A. NEW /root/deploy/repo_pull_s822.sh + ONE cron line (7,37 * * * *  # S822_REPO_PULL): the repository clone the Clinic
#      PCs page serves its kits from is pulled fast-forward only every half hour, so a kit repacked on Dr Manoj's PC and
#      published by him reaches https://followup.dr-manoj.in/finance/pcs within half an hour -- no server line (F-1386).
#      It installs nothing: a pull only. It skips a round while a kit installer holds /root/deploy/.claude_code_build.lock.
#   B. /root/finance/pc_kits.py 4191e447 -> 45d6f15d: the Medical PC's kit sentence says so (display only); clinic-finance
#      is restarted.
#  THE OTHER HALF OF THE KIT runs on Dr Manoj's PC, not here: D:\Downloads\_kbtools\pc_kits_current.py (S723+S794 -> S822),
#  placed by Claude through the file tools -- a NEW program file on the medical PC joins the kit by itself (F-1385).
#
#  PROVED BEFORE ANYTHING IS PLACED: the clone is on main and tracks origin/main; git reaches the remote WITHOUT a terminal
#  (as cron will run it: GIT_TERMINAL_PROMPT=0, a bare environment); pc_kits.py rebuilt from the live bytes equals the kit's.
#  If the remote cannot be reached that way: NOT APPLIED, nothing changed. The crontab is edited only from a good read of it,
#  byte-wise; nothing that is not this kit's may be lost; read back. Any red after placing -> everything back.
# =============================================================================
set -u
KIT="S822_PC_KITS_CURRENT_NEW_FILES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/root/wa/venv/bin/python3}"
APY="${APY:-/usr/bin/python3}"
F="${F:-/root/finance/pc_kits.py}"
REPO="${REPO:-/root/deploy/repo}"
PULL="${PULL:-/root/deploy/repo_pull_s822.sh}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-/root/s822_backup}"
SVC="${SVC:-clinic-finance}"
BASE="${BASE:-http://127.0.0.1:8106}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
CRONTAB="${CRONTAB:-crontab}"
GIT="${GIT:-git}"
HEALTH="/finance/healthz"
FROM="4191e4471d2c51147b383347418f53ac"
TO="45d6f15dda69f1599d4fbfccd6c64a94"
PULL_MD5="$(md5sum "$KDIR/repo_pull_s822.sh" 2>/dev/null | cut -c1-32)"
CRON_LINE="7,37 * * * * /bin/bash $PULL # S822_REPO_PULL"
TAG="# S822_REPO_PULL"
BAK="$BK/pc_kits.py.bak_S822_${FROM:0:8}"
CBAK="$BK/crontab.before_S822"
STG="$(dirname "$F")/.pc_kits.py.s822"
W="${TMPW:-/tmp}/s822_inst_$$"
TOOK_LOCK=0; PLACED_F=0; PLACED_P=0; CRON_CHANGED=0; ORIG=""

m5() { md5sum "$1" 2>/dev/null | cut -c1-32; }
G() { LC_ALL=C grep -a "$@"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$STG"; rm -rf "${W:?}"; release_lock; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
hz() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$BASE$HEALTH"; }
wait200() { local c=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c=$(hz); [ "$c" = 200 ] && break; done; echo "$c"; }
compiles() { PYTHONPYCACHEPREFIX="$W/pyc" "$PY" -W ignore -m py_compile "$1" || return 1
  if [ -x "$APY" ]; then PYTHONPYCACHEPREFIX="$W/pyc" "$APY" -W ignore -m py_compile "$1" || return 1; fi; return 0; }
# a GOOD read of root's crontab: the command answered 0, the file is not empty and ends with a newline
read_cron() { "$CRONTAB" -l > "$1" 2>/dev/null || return 1; [ -s "$1" ] || return 1; [ -z "$(tail -c1 "$1")" ] || return 1; return 0; }
n_tag() { G -c -F -- "$TAG" "$1"; }
# $1 = as read, $2 = to write: every line of $1 that is not this kit's must be in $2 (byte-wise)
keeps_all() { local ln; while IFS= read -r ln || [ -n "$ln" ]; do case "$ln" in *"$TAG"*) continue;; esac
  G -q -x -F -- "$ln" "$2" || { echo "   !! a line of the crontab would be lost: $(printf '%s' "$ln" | cut -c1-80)"; return 1; }; done < "$1"; return 0; }
# the remote reached WITHOUT a terminal, in a bare environment, as cron will have it
git_bare() { env -i HOME=/root PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin GIT_TERMINAL_PROMPT=0 LC_ALL=C timeout 60 "$GIT" -C "$REPO" "$@"; }
# after anything was placed, ANY failure comes here: everything back, said as it is
put_back() {
  echo "!! RED after placing ($1) -- putting everything back"
  local ok=1 c n
  if [ "$CRON_CHANGED" = 1 ]; then
    "$CRONTAB" - < "$CBAK" 2>/dev/null
    if read_cron "$W/ct.back" && [ "$(m5 "$W/ct.back")" = "$ORIG" ]; then echo "   the crontab is back as it was, byte for byte (md5 ${ORIG:0:8})"
    else ok=0; echo "   !! THE CRONTAB DID NOT GO BACK -- its copy from before is kept at $CBAK"; fi
    CRON_CHANGED=0
  fi
  if [ "$PLACED_P" = 1 ]; then rm -f "$PULL"; [ -f "$PULL" ] && { ok=0; echo "   !! $PULL could not be removed"; } || echo "   $PULL taken out again"; PLACED_P=0; fi
  if [ "$PLACED_F" = 1 ]; then
    \cp -fp "$BAK" "$F"; "$SYSTEMCTL" restart "$SVC" || echo "   !! the restart command itself failed"
    c=$(wait200); n=$(m5 "$F")
    if [ "$n" = "$FROM" ]; then echo "   The old pc_kits.py is back (${n:0:8})."; else ok=0; echo "   !! THE OLD FILE IS NOT BACK: pc_kits.py is ${n:-missing}; its backup is $BAK"; fi
    if [ "$c" = 200 ]; then echo "   $SVC answers (health 200)."; else ok=0; echo "   !! $SVC does NOT answer (health $c)."; fi
    PLACED_F=0
  fi
  [ "$ok" = 1 ] && echo "   Everything is as it was before this kit." || echo "   NOT everything went back -- see the lines above."
  echo "   Send a photo of this screen to Claude."
  exit 1
}
on_signal() { { [ "$PLACED_F" = 1 ] || [ "$PLACED_P" = 1 ] || [ "$CRON_CHANGED" = 1 ]; } && put_back "the install was interrupted"; echo "!! interrupted. Nothing was changed."; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || { echo "!! STOPPED: the kit folder was not found. Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
{ [ "$(grep -c . SUMS.md5 2>/dev/null)" = 8 ] && md5sum -c SUMS.md5 >/dev/null 2>&1; } || stop "the kit's files do not match SUMS.md5 -- the kit did not arrive whole"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 pc_kits.py)" = "$TO" ] || stop "the kit's pc_kits.py is not the file this installer was written for"
[ -n "$PULL_MD5" ] || stop "the kit's repo_pull_s822.sh is missing"
command -v "$PY" >/dev/null 2>&1 || stop "the python $PY is not there"
command -v "$GIT" >/dev/null 2>&1 || stop "git is not there"
command -v flock >/dev/null 2>&1 || stop "flock is not there (the pull script needs it)"
if mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
elif [ -d "$LOCK" ]; then
  echo "!! STOPPED: another install is running (lock $LOCK, held by: $(cat "$LOCK/owner" 2>/dev/null || echo unknown))."
  echo "   Nothing was changed. Wait five minutes and run the line again; if it says this again, send a photo of this screen to Claude."; exit 3
else stop "the lock $LOCK could not be made"; fi
mkdir -p "$W" && chmod 700 "$W" || stop "the working folder $W could not be made"

# ----------------------------------------------------------------------------------------------------------- undo
if [ "${1:-}" = "--undo" ]; then
  echo "[undo]"
  NOW=$(m5 "$F")
  [ "$NOW" = "$TO" ] || stop "pc_kits.py is ${NOW:-missing}, not this kit's file ${TO:0:8} -- nothing of this kit to undo, or a later kit changed the file since"
  [ -f "$BAK" ] && [ "$(m5 "$BAK")" = "$FROM" ] || stop "this kit's backup of pc_kits.py is not there or not the file it replaced ($BAK)"
  read_cron "$W/ct" || stop "root's crontab could not be read -- nothing undone"
  if [ "${DRY:-0}" = 1 ]; then echo "-- DRY RUN: --undo would take the $TAG line out of the crontab, remove $PULL, put $BAK back as $F and restart $SVC. NOTHING was changed."; exit 0; fi
  G -v -F -- "$TAG" "$W/ct" > "$W/ct.want"; [ -s "$W/ct.want" ] || stop "taking the line out would leave an empty crontab -- not undone"
  keeps_all "$W/ct" "$W/ct.want" || stop "the new crontab would lose a line that is not this kit's -- not written, not undone"
  "$CRONTAB" - < "$W/ct.want" || stop "the crontab could not be written -- not undone" "The crontab is as it was."
  read_cron "$W/ct.now" && [ "$(m5 "$W/ct.now")" = "$(m5 "$W/ct.want")" ] || stop "the crontab did not read back as written -- send a photo" "Look at the crontab before anything else."
  echo "    the $TAG line is out of the crontab"
  rm -f "$PULL" "$(dirname "$PULL")/.repo_pull_s822.lock"; echo "    $PULL removed"
  { \cp -fp "$BAK" "$STG" && [ "$(m5 "$STG")" = "$FROM" ]; } || stop "the backup could not be copied beside the live file" "The cron line and the pull script are out; pc_kits.py is still this kit's."
  mv -f "$STG" "$F"; [ "$(m5 "$F")" = "$FROM" ] || stop "after the undo pc_kits.py is $(m5 "$F"), NOT the old file" "The service was NOT restarted; the backup is still $BAK."
  "$SYSTEMCTL" restart "$SVC" || echo "   !! the restart command itself failed"
  c=$(wait200); [ "$c" = 200 ] || stop "the old file is back, but $SVC does not answer after its restart (health $c)" "The file is the old one; the service needs a look."
  echo "    pc_kits.py put back ${TO:0:8} -> ${FROM:0:8}; $SVC restarted, health $c"
  echo "UNDONE. The clone is pulled by server lines only again, as before this kit."
  exit 0
fi

# -------------------------------------------------------------------------------------------------------- install
compiles edits_s822.py && compiles pc_kits.py || stop "the kit's code does not compile on this server's python"
bash -n repo_pull_s822.sh || stop "the kit's pull script does not parse"
echo "[1/7] pins"
NOW=$(m5 "$F"); [ -n "$NOW" ] || stop "$F is not there"
read_cron "$W/ct" || stop "root's crontab could not be read (crontab -l gave nothing usable) -- it is never edited from a bad read"
ORIG=$(m5 "$W/ct")
if [ "$NOW" = "$TO" ] && [ "$(m5 "$PULL")" = "$PULL_MD5" ] && [ "$(n_tag "$W/ct")" = 1 ]; then echo "    ALREADY INSTALLED (pc_kits.py ${TO:0:8}, the pull script, the cron line); nothing to do."; exit 0; fi
[ "$NOW" = "$FROM" ] || stop "pc_kits.py is ${NOW:0:8}, not ${FROM:0:8} this kit was built on -- the file changed after the kit was made"
[ "$(n_tag "$W/ct")" = 0 ] || stop "a $TAG line is already in the crontab while pc_kits.py is the old file -- a half install; send a photo"
[ ! -e "$PULL" ] || stop "$PULL already exists ($(m5 "$PULL" | cut -c1-8)) while the cron line is not there -- a half install; send a photo"
echo "    pc_kits.py ${FROM:0:8}; crontab read ($(wc -l < "$W/ct") lines, md5 ${ORIG:0:8}); no S822 line yet"

echo "[2/7] rebuild pc_kits.py from the live bytes"
"$PY" -W ignore -B edits_s822.py "$F" "$W/rebuilt.py" "$KDIR/pc_kits.py" > "$W/edits.txt" 2>&1 || { sed 's/^/    /' "$W/edits.txt"; stop "the kit's file is not exactly the live file plus this kit's edits"; }
[ "$(m5 "$W/rebuilt.py")" = "$TO" ] || stop "rebuilt from the live file, pc_kits.py is not ${TO:0:8}"
sed 's/^/    /' "$W/edits.txt"
"$PY" -W ignore -B - "$W/rebuilt.py" <<'EOF' > "$W/sentence.txt" 2>&1 || { sed 's/^/    /' "$W/sentence.txt"; stop "the rebuilt page module does not say the new sentence for the Medical PC"; }
import importlib.util, sys
spec = importlib.util.spec_from_file_location("pck", sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
med = [p for p in m.PCS if p.get("id") == "medical"]
assert len(med) == 1, "no single Medical PC entry"
kk = med[0].get("kit_keeps", "")
rec = [p for p in m.PCS if p.get("id") == "reception"]
assert rec and "not repacked by itself" in rec[0].get("kit_keeps", ""), "the Reception PC's sentence changed -- it must not"
assert "within half an hour of your publish" in kk, kk
assert "next server line" not in kk, kk
print("the Medical PC's kit sentence:", kk)
EOF
sed 's/^/    /' "$W/sentence.txt"

echo "[3/7] the clone and the remote, as cron will see them (nothing pulled)"
[ -d "$REPO/.git" ] || stop "$REPO is not a git clone"
BR=$(git_bare symbolic-ref --short HEAD 2>/dev/null); [ "$BR" = main ] || stop "the clone is on '${BR:-?}', not main -- a timed pull is built for main only"
UP=$(git_bare rev-parse --abbrev-ref '@{u}' 2>/dev/null); [ "$UP" = origin/main ] || stop "the clone tracks '${UP:-nothing}', not origin/main"
if ! git_bare ls-remote --exit-code -q origin refs/heads/main > "$W/lsr.txt" 2> "$W/lsr.err"; then
  sed 's/^/    /' "$W/lsr.err" | head -3
  echo "    NOT APPLIED: git cannot reach the remote without a terminal (as cron would run it) -- a timed pull would fail every half hour."
  echo "    Nothing was changed. The owner's server line stays the way a publish reaches this page."
  exit 0
fi
DIRTY=$(git_bare status --porcelain --untracked-files=no 2>/dev/null | wc -l)
[ "$DIRTY" = 0 ] || stop "the clone has $DIRTY changed tracked file(s) -- a fast-forward pull would refuse; the clone needs a look first"
"$SYSTEMCTL" is-active --quiet cron 2>/dev/null || "$SYSTEMCTL" is-active --quiet crond 2>/dev/null || stop "the cron service is not active on this server -- a timed pull would never run"
echo "    main, tracks origin/main, remote reached without a terminal; no changed tracked file; cron active"
if [ "${DRY:-0}" = 1 ]; then echo "-- DRY RUN: every gate, the rebuild and the proof are green. NOTHING was changed."; exit 0; fi

echo "[4/7] backups -> $BK"
c0=$(hz); [ "$c0" = 200 ] || stop "$SVC does not answer BEFORE the install (health $c0) -- this kit will not install over a service that is already down"
mkdir -p "$BK" && chmod 700 "$BK" || stop "the backup folder $BK could not be made"
{ \cp -fp "$F" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop "the backup of pc_kits.py could not be written byte-exact"
{ \cp -f "$W/ct" "$CBAK" && chmod 600 "$CBAK" && [ "$(m5 "$CBAK")" = "$ORIG" ]; } || stop "the copy of the crontab could not be kept"
read_cron "$W/ct2" && [ "$(m5 "$W/ct2")" = "$ORIG" ] || stop "the crontab changed while this kit was checking -- run the line again"
echo "    $BAK (${FROM:0:8}); $CBAK (${ORIG:0:8})"

echo "[5/7] the pull script placed and run once"
{ \cp -f "$KDIR/repo_pull_s822.sh" "$PULL.s822new" && chmod 700 "$PULL.s822new" && [ "$(m5 "$PULL.s822new")" = "$PULL_MD5" ]; } || stop "the pull script could not be written"
mv -f "$PULL.s822new" "$PULL" || stop "the pull script could not be moved into place"
PLACED_P=1
[ "$(m5 "$PULL")" = "$PULL_MD5" ] || put_back "the pull script did not land byte-exact"
H0=$(git_bare rev-parse --short=8 HEAD)
# the first run pulls for real: this installer holds the install lock, which the script would otherwise respect and skip
S822_REPO="$REPO" S822_INSTALL_LOCK="$W/no_such_lock" S822_LOCK="$(dirname "$PULL")/.repo_pull_s822.lock" S822_LOG="$(dirname "$PULL")/repo_pull_s822.log" /bin/bash "$PULL" || put_back "the pull script's first run did not exit 0"
H1=$(git_bare rev-parse --short=8 HEAD)
[ -n "$H1" ] || put_back "the clone cannot be read after the first pull"
echo "    $PULL (${PULL_MD5:0:8}); first run ok (a real pull); the clone $H0 -> $H1$( [ "$H0" = "$H1" ] && echo ' (already current, as expected after your own pull)')"

echo "[6/7] pc_kits.py placed, $SVC restarted"
{ \cp -f "$KDIR/pc_kits.py" "$STG" && chmod --reference="$F" "$STG" && [ "$(m5 "$STG")" = "$TO" ]; } || put_back "the new file could not be copied beside the live one"
chown --reference="$F" "$STG" 2>/dev/null
PLACED_F=1
mv -f "$STG" "$F" || put_back "the new file could not be moved into place"
[ "$(m5 "$F")" = "$TO" ] || put_back "the file did not land byte-exact"
compiles "$F" || put_back "the placed file does not compile"
"$SYSTEMCTL" restart "$SVC" || put_back "the restart of $SVC failed"
c1=$(wait200); [ "$c1" = 200 ] || put_back "health $c1 after the restart"
"$SYSTEMCTL" is-active --quiet "$SVC" || put_back "$SVC is not active"
echo "    pc_kits.py ${FROM:0:8} -> ${TO:0:8}; $SVC active, health $c1"

echo "[7/7] the cron line"
read_cron "$W/ct3" && [ "$(m5 "$W/ct3")" = "$ORIG" ] || put_back "the crontab changed during the install"
{ cat "$W/ct"; printf '%s\n' "$CRON_LINE"; } > "$W/ct.want"
keeps_all "$W/ct" "$W/ct.want" || put_back "the new crontab would lose a line that is not this kit's -- not written"
CRON_CHANGED=1
"$CRONTAB" - < "$W/ct.want" || put_back "the crontab could not be written"
read_cron "$W/ct.now" && [ "$(m5 "$W/ct.now")" = "$(m5 "$W/ct.want")" ] || put_back "the crontab did not read back as written"
[ "$(n_tag "$W/ct.now")" = 1 ] || put_back "the cron line is not there exactly once"
echo "    one line added, read back; every other line kept ($(wc -l < "$W/ct") lines before, $(wc -l < "$W/ct.now") now)"
PLACED_F=0; PLACED_P=0; CRON_CHANGED=0
release_lock

echo "[what you will see]"
echo "    https://followup.dr-manoj.in/finance/pcs -- the Medical PC's kit line now says a new program joins the kit the same way and"
echo "    the new kit shows there within half an hour of your publish. From now on the server pulls the repository at 7 and 37 past"
echo "    every hour by itself; your server lines keep working as before. Log: $(dirname "$PULL")/repo_pull_s822.log (events only)."
echo "    pins: $(md5sum "$F") · $(md5sum "$PULL")"
echo "    undo: bash $KDIR/install_${KIT}.sh --undo"
echo "S822_PC_KITS_CURRENT_NEW_FILES: DONE. The Clinic PC kits now keep themselves current: a new program on the medical PC joins its kit by itself (checked each night on your PC), and a repacked kit reaches the page within half an hour of your publish, with no server line."
exit 0
