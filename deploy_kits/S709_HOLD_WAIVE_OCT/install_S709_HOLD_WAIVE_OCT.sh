#!/bin/bash
# =============================================================================
#  install_S709_HOLD_WAIVE_OCT.sh . kit S709 (05-Nov-2026, session S385, the parent) . September's holds waived
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s709kit && cp -rp /root/deploy/repo/deploy_kits/S709_HOLD_WAIVE_OCT /tmp/s709kit && bash /tmp/s709kit/install_S709_HOLD_WAIVE_OCT.sh
#  (DRY=1 before bash: the checks and the list of holds; nothing written.)
#
#  The owner, 20:15 IST 05-Nov: "REMOVE PREVIOUS HOLD DEDUCTION FRM OCTOBER SALARY SHEET".
#  /root/staff_register/hold_ledger.jsonl   append only: one WAIVE line per September hold still HELD
#      (the ledger's own closing action, through salary_policy.append_hold). October then collects
#      nothing from September. No code, no setting, no other month; no restart (read on every compute).
#  Red at any check after writing: the ledger put back byte-identically.
#  Undo:  the tool prints the exact line (the backup it took).
# =============================================================================
set -u
KIT="S709_HOLD_WAIVE_OCT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SRD="${SRD:-/root/staff_register}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SPOL_PIN=c36538963840a0258e0d25c6b950de4f
HAVE_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
release() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 "$SRD/salary_policy.py")" = "$SPOL_PIN" ] || stop "the live salary_policy.py is not the one this kit was built on (${SPOL_PIN:0:8})"
[ -f "$SRD/hold_ledger.jsonl" ] || stop "no hold ledger at $SRD/hold_ledger.jsonl"
echo "[kit] files match SUMS.md5; the live salary_policy.py is ${SPOL_PIN:0:8}"
W=$(VPY="$VPY" bash "$KDIR/walk_s709.sh" "$SRD/salary_policy.py" 2>&1 | tail -1)
case "$W" in "WALK OK"*) ;; *) stop "the walk on the live salary code is not green ($W)";; esac
echo "[walk] the tool on made-up ledgers with the LIVE salary code: $W"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ "${DRY:-0}" = 1 ]; then
  (cd "$SRD" && "$VPY" -B "$KDIR/hold_waive_s709.py" --dir "$SRD") ; echo "DRY=1: nothing written."; exit 0
fi
cd "$SRD" && "$VPY" -B "$KDIR/hold_waive_s709.py" --dir "$SRD" --apply
