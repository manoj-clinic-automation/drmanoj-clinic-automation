#!/bin/bash
# =============================================================================
#  install_S729_UNION_PASSBOOK.sh . kit S729_UNION_PASSBOOK (06-Nov-2026, session S390, the parent)
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s729kit && cp -rp /root/deploy/repo/deploy_kits/S729_UNION_PASSBOOK /tmp/s729kit && bash /tmp/s729kit/install_S729_UNION_PASSBOOK.sh
#  (DRY=1 before bash: every gate; nothing written.)   Undo: bash /tmp/s729kit/install_S729_UNION_PASSBOOK.sh --undo
#
#  The owner, 16:37-16:38 IST 06-Nov: Union Bank of India savings, his and Dr Bhawna's -- "they fill the passbook, it is printed
#  by the printer, and then we can scan and upload it whenever required".
#  /root/finance/packs.py  7507d991 (S728) -> fb987b27   (make_s729.py: 9 counted edits on the live bytes)
#      two half-yearly cells in the accountants' pack (April - September, October - March), Union Bank a hand-added bank like SBI:
#      the empty cell says to scan the printed passbook pages and use the Add statements box; a scanned passbook is filed by the
#      owner's one tap and dated the day it was added (printed July - December: April - September's). No account number anywhere.
#      Every other cell unchanged (the live database copy: all 228 cells of 2026 the same). Restarts clinic-finance; red after
#      placing: the old file back.
# =============================================================================
set -u
KIT="S729_UNION_PASSBOOK"
KDIR="$(cd "$(dirname "$0")" && pwd)"
FIN="${FIN:-/root/finance}"
DB="${DB:-/root/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SVC="${SVC:-clinic-finance}"; PORT="${PORT:-8106}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
MOD="packs"
LF="$FIN/$MOD.py"; FROM=7507d9916083e156b822d1516a64d00e; TO=fb987b271f9b99dec2c696590501b19d
WALK_OK="WALK OK 18/18"
HAVE_LOCK=0; PLACED=0; W=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; [ -n "$W" ] && rm -rf "$W"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/healthz"; }
restart_ok() {
  local since; since=$(date '+%Y-%m-%d %H:%M:%S')
  "$SYSTEMCTL" restart "$SVC"; h=000
  for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health); [ "$h" = 200 ] && break; done
  [ "$h" = 200 ] || return 1
  "$JOURNALCTL" -u "$SVC" --since "$since" --no-pager 2>/dev/null | grep -q "$MOD NOT mounted" && return 2
  return 0
}

restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting $MOD.py back"
  :
  \cp -p "$LF.bak_S729" "$LF"; restart_ok; r=$?
  [ "$(m5 "$LF")" = "$FROM" ] && echo "   $MOD.py is back byte-identically" || echo "   !! copy $LF.bak_S729 back by hand"
  echo "   after the restore: finance $(health). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 "$KDIR/$MOD.py")" = "$TO" ] || stop "the kit's $MOD.py is not the built one"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$LF.bak_S729" ] || stop "no backup $LF.bak_S729 -- nothing to undo"
  [ "$(m5 "$LF")" = "$TO" ] || stop "the live $MOD.py is not this kit's (${TO:0:8}) -- a later change would be undone; nothing done"
  mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK)"; HAVE_LOCK=1
  :
  \cp -p "$LF.bak_S729" "$LF"; restart_ok; echo "UNDONE: $MOD.py $(m5 "$LF" | cut -c1-8), finance $(health)."; exit 0
fi
echo "1. kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
NOW=$(m5 "$LF")
if [ "$NOW" = "$TO" ]; then echo "-- ALREADY INSTALLED ($MOD.py ${TO:0:8})"; :; exit 0; fi
[ "$NOW" = "$FROM" ] || stop "the live $MOD.py changed since this kit was built (live ${NOW:0:8}, kit expects ${FROM:0:8})"
echo "2. the live $MOD.py is the one this kit was built from (${FROM:0:8})"
PYF=""; for c in /root/wa/venv/bin/python3 /usr/bin/python3 /root/finance/venv/bin/python3 "$(command -v python3)"; do [ -x "$c" ] && "$c" -c "import flask, pypdf" 2>/dev/null && PYF="$c" && break; done
[ -n "$PYF" ] || stop "no python on this box can import flask and pypdf for the walk (the locked paper is opened in it)"
command -v pdftotext >/dev/null || stop "pdftotext is not on this box"
[ -f "$FIN/stmt_shelf.py" ] || stop "$FIN/stmt_shelf.py not found"
W=$(mktemp -d /tmp/s729w.XXXX); \cp "$LF" "$W/live.py"; \cp "$KDIR/$MOD.py" "$W/kit.py"
"$PYF" -B "$KDIR/make_s729.py" "$LF" "$W/rebuilt.py" --expect "$TO" >/dev/null || stop "the kit's packs.py is not exactly the live file plus this kit's edits"
echo "   rebuilt from the live bytes on this box: the same file as the kit's (${TO:0:8})"
"$PYF" -B -m py_compile "$W/kit.py" || stop "$MOD.py does not compile with $PYF"
R=$(cd "$W" && "$PYF" -B "$KDIR/walk_s729.py" "$W/kit.py" "$FIN/stmt_shelf.py" 2>&1 | tail -1)
[ "$R" = "$WALK_OK" ] || { (cd "$W" && "$PYF" -B "$KDIR/walk_s729.py" "$W/kit.py" "$FIN/stmt_shelf.py" 2>&1 | grep -E 'FAIL|Error' | head); stop "the walk is not green ($R)"; }
echo "3. the walk on a made-up database, against the live file: $R"
R=$(cd "$W" && "$PYF" -B "$KDIR/walk_s729.py" "$W/live.py" "$FIN/stmt_shelf.py" 2>&1 | tail -1)
case "$R" in "WALK RED"*) echo "   control (the live file in the kit's place): $R -- red, as it must be";; *) stop "the control did not go red ($R)";; esac
:
[ "$(health)" = 200 ] || stop "the finance app is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
[ "$(m5 "$LF")" = "$FROM" ] || stop "the live $MOD.py changed while this kit was checking -- run the line again"
\cp -p "$LF" "$LF.bak_S729" || stop "could not keep a backup of $MOD.py"
echo "4. backup: $MOD.py.bak_S729"
PLACED=1
\cp "$KDIR/$MOD.py" "$LF.s729new" && chmod --reference="$LF.bak_S729" "$LF.s729new" && chown --reference="$LF.bak_S729" "$LF.s729new" && mv -f "$LF.s729new" "$LF" || restore "$MOD.py could not be placed"
[ "$(m5 "$LF")" = "$TO" ] || restore "read-back did not match"
echo "5. placed $MOD.py (${TO:0:8}), read back by md5"
restart_ok; RR=$?
[ "$RR" = 0 ] || restore "finance $(health); the journal says $MOD NOT mounted: $([ "$RR" = 2 ] && echo yes || echo no)"
echo "6. $SVC restarted and healthy; $MOD mounted (no 'NOT mounted' line since the restart)"
(cd "$FIN" && FINANCE_DB="$DB" "$PYF" -B -c "
import sqlite3, sys, packs
c = sqlite3.connect(sys.argv[1])
packs.ensure(c)
for l, n in c.execute(\"SELECT s.holder_label, COUNT(f.id) FROM stmt_slot s LEFT JOIN stmt_file f ON f.slot_id=s.id WHERE s.bank='UNION' GROUP BY s.id ORDER BY s.sort\"):
    print('7. %-50s %d paper(s) so far' % (l, n))" "$DB" 2>&1 | head -4)
PLACED=0
echo ""
echo "$KIT: DONE. Two Union Bank passbook cells are in the accountants' pack, every half-year. Scan the printed passbook to a PDF, add it on the packs page, and tap whose it is."
