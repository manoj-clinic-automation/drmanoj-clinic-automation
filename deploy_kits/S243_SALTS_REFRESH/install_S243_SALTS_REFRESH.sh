#!/bin/bash
# install_S243_SALTS_REFRESH.sh -- kit S243_SALTS_REFRESH
#
#  Installs /root/finance/salts_refresh.py (new file) and one cron line, so every SALT_WISE_ITEM_LIST that
#  reaches the server archive through the Marg door refreshes /finance/purchase/page/salts within 10 minutes.
#  NOTHING is restarted: the finance service, the door and the collector are untouched.
#
#  Run:       bash /root/deploy/repo/deploy_kits/S243_SALTS_REFRESH/install_S243_SALTS_REFRESH.sh
#  Rollback:  bash /root/deploy/repo/deploy_kits/S243_SALTS_REFRESH/install_S243_SALTS_REFRESH.sh --rollback
#  Mock:      ROOT=/tmp/mock bash install_S243_SALTS_REFRESH.sh      (everything lands under $ROOT; cron untouched)
#
#  Steps: copy .new -> md5 verify -> mv into place; py_compile (venv python, /usr/bin/python3 fallback);
#  smoke = --dry-run (prints counts only); crontab backed up to /root/crontab.bak_S243_salts, the line added
#  only if absent. A rerun with the same file already in place says ALREADY INSTALLED and changes nothing.
set -e
set -u

KIT="S243_SALTS_REFRESH"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${ROOT:-}"
FIN="$ROOT/root/finance"
DEST="$FIN/salts_refresh.py"
LOG="$FIN/salts_refresh.log"
CRON_BAK="$ROOT/root/crontab.bak_S243_salts"
TAG="# S243_SALTS_REFRESH"
CRON_LINE="*/10 8-22 * * * /root/wa/venv/bin/python3 -B /root/finance/salts_refresh.py --once >> /root/finance/salts_refresh.log 2>&1 $TAG"

PY="/root/wa/venv/bin/python3"
[ -x "$PY" ] || PY="/usr/bin/python3"
[ -x "$PY" ] || PY="$(command -v python3)"

red() { echo "!! $*" >&2; exit 1; }
say() { echo "-- $*"; }

md5_of() { md5sum "$1" | awk '{print $1}'; }

# ---------------------------------------------------------------- rollback
if [ "${1:-}" = "--rollback" ]; then
  say "$KIT rollback"
  if [ -f "$DEST" ]; then rm -f "$DEST" "$DEST"c; say "removed $DEST"; else say "$DEST not present"; fi
  if [ -z "$ROOT" ]; then
    if [ -f "$CRON_BAK" ]; then
      crontab "$CRON_BAK" && say "crontab restored from $CRON_BAK"
    else
      TMPC="$(mktemp)"; crontab -l 2>/dev/null | grep -v "$TAG" > "$TMPC" || true
      crontab "$TMPC"; rm -f "$TMPC"; say "no backup found; the $TAG line was removed from crontab"
    fi
    say "cron lines with $TAG now: $(crontab -l 2>/dev/null | grep -c "$TAG" || true)"
  else
    say "mock ROOT set: crontab untouched"
  fi
  say "state file $FIN/salts_refresh.state.json and log left in place (harmless; delete by hand if wanted)"
  say "ROLLED BACK. Nothing was restarted."
  exit 0
fi

# ---------------------------------------------------------------- preflight
say "$KIT install  (python: $PY)"
[ -f "$HERE/salts_refresh.py" ] || red "kit file salts_refresh.py missing beside this installer"
[ -f "$HERE/SUMS.md5" ] || red "kit SUMS.md5 missing"
( cd "$HERE" && md5sum -c SUMS.md5 --quiet ) || red "kit SUMS.md5 does not verify -- kit is damaged; do not install"
say "kit SUMS.md5 verified"
mkdir -p "$FIN"

if [ -f "$DEST" ] && [ "$(md5_of "$DEST")" = "$(md5_of "$HERE/salts_refresh.py")" ]; then
  if [ -n "$ROOT" ] || crontab -l 2>/dev/null | grep -qF "$TAG"; then
    say "ALREADY INSTALLED: $DEST matches the kit ($(md5_of "$DEST")) and the cron line is present"
    say "nothing changed. Immediate apply if wanted:  $PY -B $DEST --force"
    exit 0
  fi
  say "file already in place; only the cron line is missing -- adding it"
fi

# ---------------------------------------------------------------- copy .new -> verify -> mv
if [ ! -f "$DEST" ] || [ "$(md5_of "$DEST")" != "$(md5_of "$HERE/salts_refresh.py")" ]; then
  \cp -f "$HERE/salts_refresh.py" "$DEST.new"
  [ "$(md5_of "$DEST.new")" = "$(md5_of "$HERE/salts_refresh.py")" ] || { rm -f "$DEST.new"; red "copy did not verify by md5"; }
  "$PY" -m py_compile "$DEST.new" || { rm -f "$DEST.new"; red "py_compile failed on the new file"; }
  rm -rf "$FIN/__pycache__/salts_refresh.new"* 2>/dev/null || true
  mv -f "$DEST.new" "$DEST"
  chmod 700 "$DEST"
  say "installed $DEST  md5 $(md5_of "$DEST")"
fi
"$PY" -m py_compile "$DEST" || red "py_compile failed on $DEST"
say "py_compile ok"

# ---------------------------------------------------------------- smoke: dry run (counts only, nothing sent)
say "smoke: --dry-run"
if [ -n "$ROOT" ]; then
  SALTS_REFRESH_ROOT="$ROOT" "$PY" -B "$DEST" --dry-run || say "(mock: dry run exit $? -- no SALT_WISE file under $ROOT is fine)"
else
  "$PY" -B "$DEST" --dry-run || say "(dry run exit $? -- no SALT_WISE_ITEM_LIST in the archive yet, or too few rows; cron will pick up the next export)"
fi

# ---------------------------------------------------------------- cron (idempotent)
if [ -n "$ROOT" ]; then
  say "mock ROOT set: crontab untouched (would add: $CRON_LINE)"
else
  crontab -l 2>/dev/null > "$CRON_BAK" || : > "$CRON_BAK"
  say "crontab backed up to $CRON_BAK"
  if crontab -l 2>/dev/null | grep -qF "$TAG"; then
    say "cron line already present"
  else
    TMPC="$(mktemp)"
    { crontab -l 2>/dev/null || true; echo "$CRON_LINE"; } > "$TMPC"
    crontab "$TMPC"; rm -f "$TMPC"
    say "cron line added"
  fi
  say "cron lines with $TAG: $(crontab -l | grep -c "$TAG")"
  touch "$LOG"
fi

say "INSTALLED. Nothing was restarted."
say "Immediate apply (do not wait for cron):  $PY -B $DEST --force"
say "State:  $FIN/salts_refresh.state.json      Log:  $LOG"
