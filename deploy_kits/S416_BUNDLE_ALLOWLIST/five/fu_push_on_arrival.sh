#!/bin/bash
# fu_push_on_arrival.sh -- kit S376_FU_PUSH_ON_ARRIVAL (session 279, 23-Sep-2026)
# THE OWNER, 23-Sep-2026: "I exported yesterday's report this morning ... the callback tracker is not updated."
# The PC's Docterz pickup (S239) sends Staff_Action_Today_<day>.xlsx to /root/wa/followup-inbox within ~5 minutes
# of the export, but clinic-followup-push (which writes Followups_Today into the Callback Tracker) ran only at
# 22:00 / 07:00 / 11:00 -- an export at 07:40 waited until 11:00. Run by root's cron every 5 minutes: when a
# workbook NEWER than the last one seen is in the inbox, start the same push service at once. The timer stays.
# Off switch: /root/finance/_off/ALL_OFF or /root/finance/_off/FU_PUSH_ON_ARRIVAL.
INBOX="${FU_INBOX_DIR:-/root/wa/followup-inbox}"
SEEN="${FU_SEEN:-/root/wa/.fu_push_seen}"
UNIT="${FU_UNIT:-clinic-followup-push.service}"
{ [ -e /root/finance/_off/ALL_OFF ] || [ -e /root/finance/_off/FU_PUSH_ON_ARRIVAL ]; } && exit 0
new="$(ls -t "$INBOX"/Staff_Action_Today_*.xlsx 2>/dev/null | head -1)"
[ -n "$new" ] || exit 0
if [ -e "$SEEN" ] && ! [ "$new" -nt "$SEEN" ]; then exit 0; fi
touch -r "$new" "$SEEN"
echo "$(date '+%F %T') new workbook $(basename "$new") -> start $UNIT"
systemctl start "$UNIT"
echo "   exit $? · $(systemctl show -p Result --value "$UNIT" 2>/dev/null)"
