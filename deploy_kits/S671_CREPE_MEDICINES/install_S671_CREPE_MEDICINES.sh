#!/bin/bash
# =============================================================================
#  install_S671_CREPE_MEDICINES.sh · kit S671 (28-Oct-2026, Sanjeevni session 359) · the owner 05:31 IST: crepe bandages (all sizes) and
#  Leukoband are pharmacy stock sold to patients, not consumables. DATA ONLY: nine rows of finance.db stock_item_section.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s671kit && cp -rp /root/deploy/repo/deploy_kits/S671_CREPE_MEDICINES /tmp/s671kit && bash /tmp/s671kit/install_S671_CREPE_MEDICINES.sh
#  No code, no restart, no crontab: every reader of the table follows at its next read.
# =============================================================================
set -u
KIT="S671_CREPE_MEDICINES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
STAMP="$(date +%Y%m%d_%H%M%S)"
BAK="$ROOT/deploy/s671_rows_before_$STAMP.json"
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
[ -x "$APY" ] || { say "!! preflight: $APY not executable - nothing changed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! SUMS.md5 gate failed - kit corrupt, nothing changed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! KIT_ID.txt names another kit - nothing changed"; exit 1; }
[ -f "$DB" ] || { say "!! $DB is missing - nothing changed"; exit 1; }
C="$("$APY" -B s671_rows.py check "$DB")"
case "$C" in
  "ROWS 9 BEFORE 0 AFTER 9") say "-- ALREADY DONE: the nine crepe rows are Medicines by your word. Nothing changed."; exit 0;;
  "ROWS 9 BEFORE 9 AFTER 0") say "[1/3] the nine crepe rows read as this kit read them: Consumables (the September seed)";;
  *) say "!! [1/3] the nine crepe rows are not as this kit read them ($C) - nothing changed"; exit 1;;
esac
mkdir -p "$ROOT/deploy"
R="$("$APY" -B s671_rows.py apply "$DB" "$BAK")"; RC=$?
say "[2/3] $R (backup of the nine rows: $BAK)"
if [ "$RC" != 0 ]; then
  [ -f "$BAK" ] && "$APY" -B s671_rows.py undo "$DB" "$BAK"
  say "!! RED - put back from $BAK. Send a photo of this screen to Claude."; exit 1
fi
C2="$("$APY" -B s671_rows.py check "$DB")"
[ "$C2" = "ROWS 9 BEFORE 0 AFTER 9" ] || { "$APY" -B s671_rows.py undo "$DB" "$BAK"; say "!! [3/3] read back $C2 - put back. Send a photo to Claude."; exit 1; }
say "[3/3] read back: $C2"
say "undo (one line): cd /tmp/s671kit && $APY -B s671_rows.py undo $DB $BAK"
say ""
say "$KIT: DONE. Crepe bandages, every size, are Medicines; Leukoband already was."
exit 0
