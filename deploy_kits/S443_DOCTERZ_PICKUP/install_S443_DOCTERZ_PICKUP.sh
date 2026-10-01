#!/bin/bash
# =============================================================================
#  install_S443_DOCTERZ_PICKUP.sh · kit S443_DOCTERZ_PICKUP (session 287, 01-Oct-2026, D645) · PARENT
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S443_DOCTERZ_PICKUP/install_S443_DOCTERZ_PICKUP.sh
#  (DRY=1 runs the gates and the walk on a scratch copy and places nothing.)
#
#  The Docterz export from the reception PC: Chrome there saves into the clinic Drive folder "Docterz exports"
#  (Clinic Records / Docterz exports -- made 01-Oct and shared read-only with the box's service account). Every 15 minutes
#  the box lists it, knows each file by its CONTENT, keeps one current export per kind and day (newest wins; fewer rows =
#  quarantined and shouted), stores the bytes on the box only, and the owner's money page shows a red line when the last
#  working day's export has not arrived by 10:00 (S442's clinic_money asks for it; it heals by itself).
#  NOT IN THIS KIT: moving the follow-up tracker -- it carries live ledgers on the PC; a decision for the owner first.
#  FILES:  /root/finance/docterz_pickup.py   NEW -> see SUMS
#  CRON:   */15 * * * *  (root) the pickup, behind flock and the finance ALL_OFF switch
#  DATA:   finance.db: the table docterz_export (made by the first run). /root/finance/docterz_exports/ (mode 700).
#  No restart: nothing running imports it until S442's page asks (fail-soft).
# =============================================================================
set -u
KIT="S443_DOCTERZ_PICKUP"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"
DBF="${FINANCE_DB:-$FIN/finance.db}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s443_walk_$STAMP"
F=docterz_pickup.py
CRON="*/15 * * * * [ -e $FIN/_off/ALL_OFF ] || flock -n /tmp/docterz_pickup.lock $VPY -B $FIN/$F >> $FIN/logs/docterz_pickup.log 2>&1 # S443_DOCTERZ_PICKUP the reception PC's Docterz exports from Drive, every 15 min"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$VPY" -c "import google.oauth2, requests" 2>/dev/null || { say "!! [1/6] the venv python lacks google-auth / requests; nothing installed"; exit 1; }
[ -f "$DBF" ] && [ -f "$FIN/docterz_ingest.py" ] || { say "!! [1/6] finance.db or docterz_ingest.py (its credential) is not there; nothing installed"; exit 1; }
say "[1/6] kit gates green (SUMS, KIT_ID, the venv's google-auth + requests, finance.db, docterz_ingest.py)"
TO="$(grep " built/$F" SUMS.md5 | awk '{print $1}')"
if [ "$(m5 "$FIN/$F")" = "$TO" ] && crontab -l 2>/dev/null | grep -q "S443_DOCTERZ_PICKUP"; then say "-- ALREADY INSTALLED"; exit 0; fi
[ ! -e "$FIN/$F" ] || [ "$(m5 "$FIN/$F")" = "$TO" ] || { say "!! [2/6] $FIN/$F exists and is not this kit's - nothing installed"; exit 1; }
( "$SPY" -m py_compile "built/$F" walk_s443.py && "$VPY" -m py_compile "built/$F" walk_s443.py ) 2>/dev/null || { say "!! [2/6] compile failed - nothing installed"; clean; exit 1; }
clean
say "[2/6] the file is new; compiles on both pythons"
mkdir -p "$WALK/app" && cp -p "built/$F" "$FIN/docterz_ingest.py" "$WALK/app/" && copydb "$DBF" "$WALK/scratch_fin.db" || { say "!! [3/6] no scratch copy - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd "$WALK" && timeout 600 "$VPY" -B "$KDIR/walk_s443.py" --app "$WALK/app" --db "$WALK/scratch_fin.db" 2>&1 )"
echo "$WOUT" | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S443 GREEN" || { say "!! [3/6] walk red - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[3/6] walk_s443 green on a scratch copy (above)"
LOUT="$( cd "$WALK/app" && FINANCE_DB="$WALK/scratch_fin.db" DOCTERZ_EXPORT_STORE="$WALK/store" timeout 300 "$VPY" -B "$WALK/app/$F" --db "$WALK/scratch_fin.db" 2>&1 )"
echo "$LOUT" | sed 's/^/   /'
echo "$LOUT" | grep -q "^docterz_pickup: " || { say "!! [4/6] the service account could not read the Drive folder (above) - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/6] the service account reads the 'Docterz exports' folder (a real pass, on the scratch copy)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: gates, walk and the Drive read green; NOTHING placed"; clean; rm -rf "$WALK"; exit 0; fi
\cp "built/$F" "$FIN/$F" && [ "$(m5 "$FIN/$F")" = "$TO" ] || { rm -f "$FIN/$F"; say "!! [5/6] placing failed - nothing installed"; rm -rf "$WALK"; exit 1; }
mkdir -p "$FIN/docterz_exports" "$FIN/logs" && chmod 700 "$FIN/docterz_exports"
crontab -l 2>/dev/null > "$WALK/cron.before"
if ! grep -q "S443_DOCTERZ_PICKUP" "$WALK/cron.before"; then
  { cat "$WALK/cron.before"; echo "$CRON"; } | crontab - || { rm -f "$FIN/$F"; say "!! [5/6] crontab refused - file removed, nothing installed"; rm -rf "$WALK"; exit 1; }
  \cp "$WALK/cron.before" "$FIN/crontab.bak_S443_$STAMP"
fi
crontab -l | grep -q "S443_DOCTERZ_PICKUP" || { say "!! [5/6] the cron line is not there"; exit 1; }
say "[5/6] placed (md5 = the kit's pin); cron line added (the old crontab kept as $FIN/crontab.bak_S443_$STAMP)"
( cd "$FIN" && "$VPY" -B "$FIN/$F" && "$VPY" -B "$FIN/$F" --status ) 2>&1 | sed 's/^/   /'
say "[6/6] the first live pass ran (above)"
clean; rm -rf "$WALK"
md5sum "$FIN/$F"
say "$KIT: DONE -- the folder: https://drive.google.com/drive/folders/1JjWcfk_7IzSBQUbLlbNWPvf96LGcjjDt · the red line shows on https://followup.dr-manoj.in/finance/clinic/money"
