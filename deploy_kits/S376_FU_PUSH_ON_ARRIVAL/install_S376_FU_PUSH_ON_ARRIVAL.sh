#!/bin/bash
# install_S376_FU_PUSH_ON_ARRIVAL.sh -- the Callback Tracker's follow-up list refreshes minutes after the Docterz
# export, not at the next 22:00 / 07:00 / 11:00 timer. NEW /root/wa/fu_push_on_arrival.sh + ONE root cron line
# (every 5 minutes). No code file changes; clinic-followup-push and its timer are untouched. Pushes once now.
#
# One line on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S376_FU_PUSH_ON_ARRIVAL/install_S376_FU_PUSH_ON_ARRIVAL.sh
# Undo: crontab /root/wa/crontab.bak_S376
set -u
KIT="S376_FU_PUSH_ON_ARRIVAL"; KDIR="$(cd "$(dirname "$0")" && pwd)"
DST="/root/wa/fu_push_on_arrival.sh"; BAK="/root/wa/crontab.bak_S376"; UNIT="clinic-followup-push.service"
LINE="*/5 * * * * /bin/bash /root/wa/fu_push_on_arrival.sh >> /root/wa/fu_push_on_arrival.log 2>&1  # S376_FU_PUSH_ON_ARRIVAL"
CUR="/tmp/s376_cron_now_$$.txt"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/5] SUMS.md5 gate failed - nothing changed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { echo "!! [1/5] KIT_ID names another kit - nothing changed"; exit 1; }
bash -n fu_push_on_arrival.sh || { echo "!! [1/5] script does not parse - nothing changed"; exit 1; }
echo "[1/5] kit gates green"
systemctl cat "$UNIT" >/dev/null 2>&1 || { echo "!! [2/5] $UNIT not found on this machine - nothing changed"; exit 1; }
[ -d /root/wa/followup-inbox ] || { echo "!! [2/5] /root/wa/followup-inbox missing - nothing changed"; exit 1; }
crontab -l > "$CUR" 2>/dev/null || { echo "!! [2/5] cannot read root's crontab - nothing changed"; exit 1; }
if grep -q "S376_FU_PUSH_ON_ARRIVAL" "$CUR" && [ "$(m5 "$DST")" = "$(m5 fu_push_on_arrival.sh)" ]; then
  echo "-- ALREADY INSTALLED."; grep "S376_FU_PUSH_ON_ARRIVAL" "$CUR"; rm -f "$CUR"; exit 0
fi
if [ -e "$DST" ] && [ "$(m5 "$DST")" != "$(m5 fu_push_on_arrival.sh)" ]; then echo "!! [2/5] $DST exists and is not the kit's - nothing changed"; rm -f "$CUR"; exit 1; fi
echo "[2/5] $UNIT present · inbox present · crontab read"
\cp -p fu_push_on_arrival.sh "$DST" && chmod 700 "$DST" && [ "$(m5 "$DST")" = "$(m5 fu_push_on_arrival.sh)" ] || { echo "!! [3/5] placing the script failed"; rm -f "$CUR"; exit 1; }
echo "[3/5] placed $DST $(m5 "$DST")"
[ -e "$BAK" ] || \cp -p "$CUR" "$BAK" || { echo "!! [4/5] crontab backup failed - script placed, cron unchanged"; exit 1; }
grep -v "S376_FU_PUSH_ON_ARRIVAL" "$CUR" > "$CUR.new"; echo "$LINE" >> "$CUR.new"
before=$(grep -vc "S376_FU_PUSH_ON_ARRIVAL" "$CUR")
crontab "$CUR.new" || { echo "!! [4/5] crontab refused - restoring"; crontab "$BAK"; exit 1; }
crontab -l > "$CUR"
[ "$(grep -c "S376_FU_PUSH_ON_ARRIVAL" "$CUR")" = 1 ] && [ "$(grep -vc "S376_FU_PUSH_ON_ARRIVAL" "$CUR")" = "$before" ] || { echo "!! [4/5] read-back wrong - restoring"; crontab "$BAK"; exit 1; }
echo "[4/5] cron: 1 line added, the other $before lines unchanged · backup $BAK"
echo "[5/5] the first pass now (pushes the newest workbook to the Callback Tracker):"
/bin/bash "$DST" 2>&1 | tail -2 | tee -a /root/wa/fu_push_on_arrival.log
rm -f "$CUR" "$CUR.new"
echo "$KIT: DONE -- from now on a Docterz export reaches Followups_Today within about 10 minutes."
