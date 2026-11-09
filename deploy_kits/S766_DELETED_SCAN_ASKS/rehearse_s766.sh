#!/bin/bash
# rehearse_s765.sh -- kit S765's installer on a MADE-UP root (never /root): bash rehearse_s765.sh <a root holding finance/ and shared/ code>
# DRY · a changed live file (STOP at [2/6]) · INSTALL · ALREADY INSTALLED · a forced red at [6/6] (both files back). Last line: 'REHEARSAL S766: 5 of 5 as expected'.
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; SRC="$1"; S765OUT="$2"; PY="${PY:-python3}"; W="$(mktemp -d /tmp/s766reh_XXXX)"; OKN=0
mk() { rm -rf "$W/root"; mkdir -p "$W/root/finance" "$W/root/shared" "$W/bin"; cp -p "$SRC/finance/"*.py "$SRC/finance/"*.json "$W/root/finance/" 2>/dev/null; cp -p "$SRC/shared/"*.py "$W/root/shared/"; cp -p "$S765OUT/porders_s454.py" "$W/root/finance/"; cp -p "$S765OUT/scan_quality.py" "$W/root/shared/"; : > "$W/root/finance/finance.db"
  printf '#!/bin/bash\ncase "$1" in show) echo 0;; *) exit 0;; esac\n' > "$W/bin/systemctl"; printf '#!/bin/bash\necho 200\n' > "$W/bin/health"; chmod +x "$W/bin/"*; }
run() { local want="$1"; shift; local out; out="$(env ROOT="$W/root" LOCK="$W/lock" APY="$(command -v "$PY")" VPY="$(command -v "$PY")" SYSTEMCTL="$W/bin/systemctl" JOURNALCTL=none-here HEALTH_CMD="$W/bin/health" SKIP_WINDOW=1 REHEARSE_PROOF=skip TMPW="$W" "$@" bash "$KDIR/install_S766_DELETED_SCAN_ASKS.sh" 2>&1)"
  if printf '%s\n' "$out" | grep -q -E "$want"; then OKN=$((OKN+1)); echo "  as expected: $want"; else echo "  NOT as expected ($want):"; printf '%s\n' "$out" | tail -6 | sed 's/^/      /'; fi; }
mk; run '^-- DRY RUN: every gate' DRY=1
[ ! -e "$W/root/finance/porders_s454.py.bak_S766_903df714" ] || { echo "  !! the DRY wrote a backup"; OKN=$((OKN-1)); }
echo "# changed" >> "$W/root/finance/porders_s454.py"; run 'porders_s454.py is .*expected 903df714.* STOP' DRY=1
mk; run 'S766_DELETED_SCAN_ASKS: DONE'
run '^-- ALREADY INSTALLED'
mk; run 'RED after placing \(the walk on the placed files: rehearsal: a forced red at \[6/6\]\)' REHEARSE_RED_AT=6
[ "$(md5sum "$W/root/finance/porders_s454.py" | cut -c1-32)" = 903df7148662a18fa9825cc629322f74 ] || { echo "  !! porders_s454 not put back"; OKN=$((OKN-1)); }
[ -d "$W/lock" ] && { echo "  !! the lock was left behind"; OKN=$((OKN-1)); }
rm -rf "$W"; echo "REHEARSAL S766: $OKN of 5 as expected"; [ "$OKN" = 5 ]
