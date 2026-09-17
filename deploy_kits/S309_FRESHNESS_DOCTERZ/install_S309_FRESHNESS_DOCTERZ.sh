#!/bin/bash
# =============================================================================
#  install_S309_FRESHNESS_DOCTERZ.sh · kit S309_FRESHNESS_DOCTERZ (session 267, 17-Sep-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S309_FRESHNESS_DOCTERZ/install_S309_FRESHNESS_DOCTERZ.sh
#
#  F-517: the health page's leg "clinic day revenue ingest" still carries the 200-hour window and the note
#  "docterz_ingest.py is run by hand today ... Tighten to 26 h the day it gets a timer". It has had a timer
#  since S238 and runs every ten minutes all day since S291, so the leg would stay silent through eight days
#  of no data. This sets the window to 50 h and rewrites the note (50, not 26: the leg watches the DATA, and
#  the database shows real 24.0 h and 28.7 h quiet spells -- a closed Sunday, a PC that was off).
#
#  DATA ONLY: two strings inside one leg of the legs file the live collector reads (freshness.conf LEGS_FILE,
#  normally /root/finance/freshness_legs.json). A backup is written beside it. No code file, no service, no
#  cron line, no restart -- the collector reads the file on each run.
#
#  Gates: kit SUMS + KIT_ID -> the selftest on a COPY of the live file (21 checks, refusals, backup, only
#  this leg) -> a read-only --check of the live file (window, note, and how old the data actually is) ->
#  --apply (which refuses by itself if the data is already older than the new window) -> read-back.
#  Then it prints the live cron lines for docterz / assetapp / petty_backup, with any long value masked.
# =============================================================================
set -u
KIT="S309_FRESHNESS_DOCTERZ"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
STAMP="$(date +%Y%m%d_%H%M%S)"
T="/tmp/s309_$STAMP"
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
[ -x "$VPY" ] || { say "!! preflight: $VPY not executable - nothing changed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing changed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing changed"; exit 1; }
say "[1/5] kit gates green"

export PYTHONPYCACHEPREFIX="$T/pyc"
mkdir -p "$T" || exit 1
LIVE="$("$VPY" -B -c "import sys; sys.path.insert(0,'$KDIR'); import update_legs_s309 as u; print(u.resolve_file(None))")"
[ -f "$LIVE" ] || { say "!! [2/5] no legs file at ${LIVE:-<unresolved>} - nothing changed"; rm -rf "$T"; exit 1; }
if "$VPY" -B update_legs_s309.py --check | grep -q "RESULT ALREADY"; then
  say "-- ALREADY INSTALLED: the leg already carries the S309 window and note."; rm -rf "$T"; exit 0
fi
cp -p "$LIVE" "$T/legs_copy.json"
SOUT="$( cd /tmp && timeout 120 "$VPY" -B "$KDIR/selftest_s309.py" "$KDIR" "$T/legs_copy.json" 2>&1 | tail -1 )"
echo "$SOUT" | grep -q "^SELFTEST OK" || { say "!! [2/5] selftest red on a copy of the live file: $SOUT - nothing changed"; rm -rf "$T"; exit 1; }
say "[2/5] $SOUT"
say "    live legs file: $LIVE"

say "[3/5] the leg as it stands now (read-only):"
"$VPY" -B update_legs_s309.py --check | sed 's/^/    /'

say "[4/5] applying:"
AOUT="$("$VPY" -B update_legs_s309.py --apply 2>&1)"
echo "$AOUT" | sed 's/^/    /'
if echo "$AOUT" | grep -q "^FAIL:"; then
  say "!! [4/5] the change was refused for the reason above - nothing changed"; rm -rf "$T"; exit 1
fi
"$VPY" -B update_legs_s309.py --check | grep -q "RESULT ALREADY" \
  || { say "!! [4/5] the read-back does not carry the change -- the backup beside the file holds the original"; rm -rf "$T"; exit 1; }
rm -rf "$T"
say "[4/5] done -- the collector picks it up on its next run; nothing was restarted"

say "[5/5] the live cron lines that matter here (long values masked):"
crontab -l 2>/dev/null | grep -E 'docterz|assetapp|petty_backup' | sed -E 's/[A-Za-z0-9_-]{24,}/<masked>/g' | sed 's/^/    /'
say "$KIT: DONE"
say "read next: https://followup.dr-manoj.in/finance/freshness"
