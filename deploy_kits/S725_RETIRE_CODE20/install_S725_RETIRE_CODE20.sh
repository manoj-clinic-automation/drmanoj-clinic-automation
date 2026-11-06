#!/bin/bash
# =============================================================================
#  install_S725_RETIRE_CODE20.sh . kit S725 (06-Nov-2026, session S390, the parent)
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s725kit && cp -rp /root/deploy/repo/deploy_kits/S725_RETIRE_CODE20 /tmp/s725kit && bash /tmp/s725kit/install_S725_RETIRE_CODE20.sh
#  (DRY=1 before bash: the checks and what would change; nothing written.)
#  finance.db (data only): EXIT-2026-0002 (Arjun) carries Emp Code 20, and code 20 is retired 2026-09-30 -- never given
#  to anyone again. Backup first (sqlite's backup API, finance.db.bak_S725_<time>). No code, no restart.
# =============================================================================
set -u
KIT="S725_RETIRE_CODE20"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"; [ -x "$PY" ] || PY=/root/wa/venv/bin/python3
FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
HAVE_LOCK=0
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
DB="${DB:-}"
if [ -z "$DB" ]; then DB=$("$SYSTEMCTL" show -p Environment "$FSVC" 2>/dev/null | sed 's/^Environment=//' | tr ' ' '\n' | sed -n 's/^FINANCE_DB=//p' | head -1); fi
[ -n "$DB" ] || DB=/root/finance/finance.db
[ -f "$DB" ] || stop "no finance database at $DB"
echo "1. kit files match SUMS.md5; the finance database: $DB"
R=$(cd /tmp && "$PY" -B "$KDIR/walk_s725.py" "$KDIR/retire20_s725.py" 2>&1 | tail -1)
[ "$R" = "WALK OK 13/13" ] || stop "the walk is not green ($R)"
echo "2. the walk on made-up databases: $R"
R=$(cd /tmp && "$PY" -B "$KDIR/walk_s725.py" "$KDIR/retire20_s725.py" --control 2>&1 | tail -1)
case "$R" in "WALK RED"*) echo "   control: $R -- red, as it must be";; *) stop "the control did not go red ($R)";; esac
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
A=""; [ "${DRY:-0}" = 1 ] && A="--dry"
R=$("$PY" -B "$KDIR/retire20_s725.py" "$DB" $A 2>&1); RC=$?
echo "$R" | sed 's/^/3. /'
[ "$RC" = 0 ] || { echo "!! the step stopped (rc $RC). Send a photo of this screen to Claude."; exit 1; }
echo ""
echo "$KIT: DONE. Arjun's exit record carries code 20 and the code is retired for good."
