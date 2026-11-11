#!/bin/bash
# =============================================================================
#  run_S794_server.sh . kit S794_HOUSEKEEPING, the server part (11-Nov-2026, session S431, the parent; Runbook §2A item 7)
#    (1) READ-ONLY, for the S431 watch: the 3 pm / 6 pm X-ray photo notification runs (/root/finance/xray_photo_nudge.log) and
#        today's attendance-clock corrections (/root/attlistener.log CLOCK lines) -- counts, times and staff numbers only.
#    (2) REMOVES /root/s770_probe/ -- the S770 probe's own folder (its report and its RapidOCR venv), ~370 MB, used by nothing:
#        no cron line, no service, no code names it (read at S431 from the 10-Nov bundle; checked again here before removing).
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S794_HOUSEKEEPING/run_S794_server.sh
#  DRY=1 prints everything and removes nothing. No service is restarted; no live file changes.
# =============================================================================
set -u
KIT="S794_HOUSEKEEPING"
ROOT="${ROOT:-/root}"
P="$ROOT/s770_probe"
CRONTAB="${CRONTAB:-crontab}"
stop() { echo "!! STOPPED: $1"; echo "   Nothing was removed. Send a photo of this screen to Claude."; exit 1; }
echo "== $KIT (server part) == $(TZ=Asia/Kolkata date '+%d-%b %H:%M IST')"
KDIR="$(cd "$(dirname "$0")" && pwd)"
(cd "$KDIR" && md5sum -c SUMS.md5 --quiet >/dev/null 2>&1) || stop "the kit's files do not match SUMS.md5"
echo "[1/3] the 3 pm / 6 pm X-ray photo notifications -- the log's last lines:"
NL="$ROOT/finance/xray_photo_nudge.log"
if [ -f "$NL" ]; then tail -n 8 "$NL" | sed -E 's/[0-9]{10}/xxxxxxxxxx/g' | cut -c1-200 | sed 's/^/      /'; else echo "      (no log yet: $NL)"; fi
echo "[2/3] the attendance clock today -- CLOCK corrections and the last punches received:"
AL="$ROOT/attlistener.log"; TD=$(TZ=Asia/Kolkata date +%Y-%m-%d)
if [ -f "$AL" ]; then
  echo "      CLOCK lines today: $(grep "$TD" "$AL" | grep -c 'CLOCK')"
  grep "$TD" "$AL" | grep 'CLOCK' | tail -n 3 | cut -c1-200 | sed 's/^/      /'
  echo "      last 3 lines of the listener:"; tail -n 3 "$AL" | cut -c1-200 | sed 's/^/      /'
else echo "      (no log: $AL)"; fi
echo "[3/3] /root/s770_probe/"
if [ ! -e "$P" ]; then echo "      already gone -- nothing to do."; echo "$KIT: DONE."; exit 0; fi
[ -d "$P" ] && [ ! -L "$P" ] || stop "$P is not a plain folder"
SZ=$(du -sh "$P" 2>/dev/null | cut -f1); NF=$(find "$P" -type f 2>/dev/null | wc -l)
echo "      $SZ in $NF files"
C1=$("$CRONTAB" -l 2>/dev/null | grep -c 's770_probe'); [ "$C1" = 0 ] || stop "a cron line names s770_probe"
C2=$(grep -rIl 's770_probe' "$ROOT/finance" "$ROOT/portal" "$ROOT/wa" "$ROOT/labdata" "$ROOT/assetapp" "$ROOT/marg_ingest" /etc/systemd/system 2>/dev/null | grep -v -E '\.bak|\.log$' | head -3)
[ -z "$C2" ] || stop "a file names s770_probe: $C2"
C3=$(ps -eo args 2>/dev/null | grep 's770_probe' | grep -v grep | grep -v run_S794 | head -1)
[ -z "$C3" ] || stop "a running program uses it: $C3"
echo "      nothing uses it: no cron line, no file under /root's apps or systemd names it, no running program"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: would remove $P ($SZ). Nothing removed."; exit 0; }
rm -rf -- "$P"
[ -e "$P" ] && stop "it could not be removed completely"
echo "      removed. Disk free now: $(df -h "$ROOT" | awk 'NR==2{print $4}')"
echo "$KIT: DONE."
