#!/bin/bash
# =============================================================================
#  install_S310_FRESHNESS_LEGS_2.sh · kit S310_FRESHNESS_LEGS_2 (session 267, 17-Sep-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S310_FRESHNESS_LEGS_2/install_S310_FRESHNESS_LEGS_2.sh
#
#  After S309, the rest of what the live crontab (read on the box at 22:46 IST) says about watched jobs:
#    CHANGE  "asset app archive"          200 h "weekly"  ->  26 h, nightly at 02:30 since S286 (verified, 14 days)
#    ADD     "petty bill photos off-box"  NEW 26 h log_mtime /root/backups/petty_backup.log (S295, 02:40)
#  The petty leg is added only once that log exists -- its first run is 02:40 the morning after S295 went
#  live. Until then the kit says SKIPPED and changes nothing else; RE-RUN THIS SAME LINE after 02:40 and it
#  adds the leg. Re-running when there is nothing to do says ALREADY and writes nothing.
#
#  DATA ONLY: the legs file the live collector reads (freshness.conf LEGS_FILE). Backup beside it, parsed
#  leg-by-leg compare, read-back. No code, no service, no cron line, no restart.
#
#  Gates: kit SUMS + KIT_ID -> the selftest on a COPY of the live file with the watched things faked in /tmp
#  (25 checks) -> a read-only --check (each leg, and how old the thing it watches actually is) -> --apply,
#  which refuses a window whose watched thing is ALREADY older than it, and skips a new leg that would go
#  red at once -> read-back.
# =============================================================================
set -u
KIT="S310_FRESHNESS_LEGS_2"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
STAMP="$(date +%Y%m%d_%H%M%S)"
T="/tmp/s310_$STAMP"
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
[ -x "$VPY" ] || { say "!! preflight: $VPY not executable - nothing changed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing changed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing changed"; exit 1; }
say "[1/5] kit gates green"

export PYTHONPYCACHEPREFIX="$T/pyc"
mkdir -p "$T" || exit 1
LIVE="$("$VPY" -B -c "import sys; sys.path.insert(0,'$KDIR'); import update_legs_s310 as u; print(u.resolve_file(None))")"
[ -f "$LIVE" ] || { say "!! [2/5] no legs file at ${LIVE:-<unresolved>} - nothing changed"; rm -rf "$T"; exit 1; }
cp -p "$LIVE" "$T/legs_copy.json"
SOUT="$( cd /tmp && timeout 120 "$VPY" -B "$KDIR/selftest_s310.py" "$KDIR" "$T/legs_copy.json" 2>&1 | tail -1 )"
echo "$SOUT" | grep -q "^SELFTEST OK" || { say "!! [2/5] selftest red on a copy of the live file: $SOUT - nothing changed"; rm -rf "$T"; exit 1; }
say "[2/5] $SOUT"
say "    live legs file: $LIVE"

say "[3/5] the legs as they stand now (read-only):"
"$VPY" -B update_legs_s310.py --check | sed 's/^/    /'

say "[4/5] applying:"
AOUT="$("$VPY" -B update_legs_s310.py --apply 2>&1)"
echo "$AOUT" | sed 's/^/    /'
if echo "$AOUT" | grep -q "^FAIL:"; then
  say "!! [4/5] refused for the reason above - nothing changed"; rm -rf "$T"; exit 1
fi
"$VPY" -B update_legs_s310.py --check | grep -q "RESULT ALREADY" \
  || { say "!! [4/5] the read-back does not carry the changes -- the backup beside the file holds the original"; rm -rf "$T"; exit 1; }
rm -rf "$T"
say "[4/5] done -- the collector picks it up on its next run; nothing was restarted"

if echo "$AOUT" | grep -q "^   SKIPPED"; then
  say "[5/5] one leg was skipped (see above). RE-RUN THIS SAME LINE after the job's first run and it will be added."
else
  say "[5/5] every leg in this kit is on the page."
fi
say "$KIT: DONE"
say "read next: https://followup.dr-manoj.in/finance/freshness"
