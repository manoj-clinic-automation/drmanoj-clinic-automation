#!/bin/bash
# =============================================================================
#  install_S751_SUMMARY_SCANS_CLEANUP.sh · kit S751 (08-Nov-2026, Sanjeevni session 407) · the owner's word 13:25 / 13:42 IST.
#  Removes the sixteen papers B-0274 .. B-0289 (Shivani's 11:54-12:04 scans of fourteen dealers' October summaries, scanned without the
#  SUMMARY tick and read as ordinary bills) the way the app's own Delete does -- audited, after a backup of both databases -- so staff can
#  rescan them properly. No code file changes; no service restarts. All or nothing; refuses if any paper is not the one read on the screen.
#    DRY=1 bash /tmp/s751kit/install_S751_SUMMARY_SCANS_CLEANUP.sh      # reads and prints everything, writes nothing (F-1153: read first)
#    bash /tmp/s751kit/install_S751_SUMMARY_SCANS_CLEANUP.sh            # the DRY again, then the removal, then the read-back
# =============================================================================
set -u
KIT="S751_SUMMARY_SCANS_CLEANUP"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
ADB="${ADB:-$ROOT/assetapp/assets.db}"
FDB="${FDB:-$ROOT/finance/finance.db}"
say() { echo "$@"; }
say "== $KIT · $(date '+%Y-%m-%d %H:%M:%S %Z')  ${DRY:+DRY RUN -- nothing is written}"
say "[1/4] the kit's own sums"
( cd "$KDIR" && md5sum -c SUMS.md5 --quiet ) || { say "   !! SUMS.md5 does not match the kit's files -- STOP, nothing done"; exit 1; }
[ "$(cat "$KDIR/KIT_ID.txt" 2>/dev/null)" = "$KIT" ] || { say "   !! KIT_ID.txt is not $KIT -- STOP"; exit 1; }
say "   ok"
say "[2/4] the two databases"
for p in "$ADB" "$FDB"; do [ -f "$p" ] || { say "   !! missing: $p -- STOP"; exit 1; }; done
say "   $ADB  $(stat -c %s "$ADB") B"
say "   $FDB  $(stat -c %s "$FDB") B"
say "[3/4] the DRY read -- every guard, every count"
"$APY" -B "$KDIR/cleanup_s751.py" --assets "$ADB" --finance "$FDB" || { say "   !! the DRY read refused -- STOP, nothing changed"; exit 1; }
if [ -n "${DRY:-}" ]; then say "DRY RUN complete -- nothing written. Paste this output; the real line is the same without DRY=1."; exit 0; fi
say "[4/4] the removal (backups first, inside the script)"
"$APY" -B "$KDIR/cleanup_s751.py" --assets "$ADB" --finance "$FDB" --real || { say "   !! the removal did not finish clean -- read the lines above; the backups are beside the databases"; exit 1; }
say "$KIT: DONE."
