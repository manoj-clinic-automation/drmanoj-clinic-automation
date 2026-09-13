#!/bin/bash
# =============================================================================
#  install_S243_CODE_BUNDLE.sh
#
#  KIT   S243_CODE_BUNDLE -- the live code gets a nightly off-box copy, the
#        way finance.db already has one (S213).
#  RUN   bash /root/deploy/repo/deploy_kits/S243_CODE_BUNDLE/install_S243_CODE_BUNDLE.sh
#
#  WHAT CHANGES
#    NEW      /root/state_backup/code_bundle.py     (nothing is replaced)
#    NEW      one root crontab line, tagged  # S243_CODE_BUNDLE  (idempotent)
#    NO service is restarted. NO database touched. NO other file.
#
#  HOW
#    gates from inside the kit folder -> copy as .new -> md5 verify -> mv into
#    place -> py_compile -> `build` as the smoke (no network) -> crontab backed
#    up to /root/crontab.bak_S243 -> the line added only if absent.
#    Any failure puts back what was there: the file is removed (or the previous
#    one restored) and the crontab is restored from the backup.
#
#  ROOT (tests only): when ROOT is set, every target path is under $ROOT and
#    the crontab is a plain file $ROOT/root/crontab.current instead of the
#    real crontab. On the box ROOT is unset.
#  PY  (tests only): python to use; default /root/wa/venv/bin/python3, then
#    /usr/bin/python3.
# =============================================================================
set -eu

KIT="S243_CODE_BUNDLE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-}"
DST_DIR="$ROOT/root/state_backup"
DST="$DST_DIR/code_bundle.py"
CRON_BAK="$ROOT/root/crontab.bak_S243"
CRON_FAKE="$ROOT/root/crontab.current"
CRON_LINE='35 1 * * * /root/wa/venv/bin/python3 /root/state_backup/code_bundle.py run >> /root/state_backup/code_bundle.log 2>&1 # S243_CODE_BUNDLE'
CRON_TAG='# S243_CODE_BUNDLE'

if [ -n "${PY:-}" ]; then
  APY="$PY"
elif [ -x /root/wa/venv/bin/python3 ]; then
  APY=/root/wa/venv/bin/python3
else
  APY=/usr/bin/python3
fi

PREV_BAK=""
FILE_PLACED=0
CRON_CHANGED=0
CRON_BACKED=0

cron_read() {
  if [ -n "$ROOT" ]; then
    if [ -f "$CRON_FAKE" ]; then cat "$CRON_FAKE"; fi
  else
    crontab -l 2>/dev/null || true
  fi
}

cron_write() {
  if [ -n "$ROOT" ]; then
    cat > "$CRON_FAKE"
  else
    crontab -
  fi
}

rollback() {
  set +e
  if [ "$FILE_PLACED" = "1" ]; then
    if [ -n "$PREV_BAK" ] && [ -f "$PREV_BAK" ]; then
      \cp -f "$PREV_BAK" "$DST"
      echo "   $DST put back from $PREV_BAK"
    else
      rm -f "$DST"
      echo "   $DST removed"
    fi
  fi
  rm -f "$DST.new"
  if [ "$CRON_CHANGED" = "1" ] && [ "$CRON_BACKED" = "1" ]; then
    cron_write < "$CRON_BAK"
    echo "   crontab restored from $CRON_BAK"
  fi
}

red() {
  rollback
  echo "!! RED -- $*"
  exit 1
}

trap 'red "unexpected failure at line $LINENO"' ERR

cd "$KDIR" || red "cannot enter the kit folder"

# -- gates, all from INSIDE this folder --------------------------------------
md5sum -c SUMS.md5 >/dev/null 2>&1 || red "SUMS.md5 gate failed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || red "KIT_ID names a different kit"
NEWSUM="$(md5sum code_bundle.py | awk '{print $1}')"
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$NEWSUM" ] || red "KIT_ID does not match code_bundle.py (F-88)"
[ -x "$APY" ] || red "$APY is not there"
echo "-- gates green; python $APY; payload $NEWSUM"

# -- lay the file down: .new -> verify -> mv ---------------------------------
mkdir -p "$DST_DIR"
if [ -f "$DST" ]; then
  CUR="$(md5sum "$DST" | awk '{print $1}')"
  if [ "$CUR" = "$NEWSUM" ]; then
    echo "-- $DST is already $NEWSUM (same bytes); file step skipped"
  else
    PREV_BAK="$DST.bak_${KIT}_$(date +%Y%m%d_%H%M%S)"
    \cp -f "$DST" "$PREV_BAK"
    echo "-- a different code_bundle.py was there ($CUR); kept at $PREV_BAK"
  fi
fi
if [ ! -f "$DST" ] || [ "$(md5sum "$DST" | awk '{print $1}')" != "$NEWSUM" ]; then
  \cp -f code_bundle.py "$DST.new"
  GOT="$(md5sum "$DST.new" | awk '{print $1}')"
  [ "$GOT" = "$NEWSUM" ] || red "copy did not verify ($GOT vs $NEWSUM)"
  mv -f "$DST.new" "$DST"
  FILE_PLACED=1
  chmod 700 "$DST"
  echo "-- placed $DST ($NEWSUM)"
fi

"$APY" -m py_compile "$DST" || red "py_compile code_bundle.py"
rm -f "$DST_DIR/__pycache__"/code_bundle.*.pyc 2>/dev/null || true
echo "-- py_compile green"

# -- the smoke: build, no network ---------------------------------------------
echo "-- smoke: build (no network)"
SMOKE="$(mktemp)"
if ROOT="$ROOT" "$APY" "$DST" build > "$SMOKE" 2>&1; then
  sed 's/^/   /' "$SMOKE"
else
  sed 's/^/   /' "$SMOKE"
  rm -f "$SMOKE"
  red "the build smoke failed on this box"
fi
grep -q "SUMMARY files=" "$SMOKE" || { rm -f "$SMOKE"; red "the smoke printed no summary"; }
rm -f "$SMOKE"

# -- the cron line, only if absent -------------------------------------------
cron_read > "$CRON_BAK"
CRON_BACKED=1
echo "-- crontab backed up to $CRON_BAK"
if grep -qF "$CRON_TAG" "$CRON_BAK"; then
  echo "-- cron line already present (tag $CRON_TAG); not added again"
else
  CRON_CHANGED=1
  { cat "$CRON_BAK"; echo "$CRON_LINE"; } | cron_write
  cron_read | grep -qF "$CRON_TAG" || red "the cron line did not land"
  echo "-- cron line added"
fi

trap - ERR
echo ""
echo "PINS  /root/state_backup/code_bundle.py $NEWSUM"
echo "$KIT GREEN -- local copy written; the nightly leg is cronned at 01:35."
echo "OWNER STEP (once, if not yet done): from the owner's Drive account upload any"
echo "file named exactly code_nightly.tar.gz into the folder that holds"
echo "finance_nightly.db.gz. Then verify with:"
echo "/root/wa/venv/bin/python3 /root/state_backup/code_bundle.py list"
