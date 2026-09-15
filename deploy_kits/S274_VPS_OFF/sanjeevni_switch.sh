#!/bin/bash
# sanjeevni_switch.sh -- turn a Sanjeevni server job off or on, and say which
# are which. Creates and removes marker files under /root/finance/_off and does
# nothing else: no service, no cron line, no database.
#
#   bash /root/finance/sanjeevni_switch.sh status
#   bash /root/finance/sanjeevni_switch.sh off all
#   bash /root/finance/sanjeevni_switch.sh on  spine
set -u
OFF=/root/finance/_off
declare -A M=( [all]=ALL_OFF [spine]=SPINE_OFF [attribution]=ATTRIBUTION_OFF \
               [export]=EXPORT_WATCH_OFF [salts]=SALTS_REFRESH_OFF )

usage() {
  echo "usage: sanjeevni_switch.sh status"
  echo "       sanjeevni_switch.sh off|on  all|spine|attribution|export|salts"
  exit 1
}

status() {
  echo "Sanjeevni server jobs -- $OFF"
  for k in all spine attribution export salts; do
    n=${M[$k]}
    if [ -e "$OFF/$n" ] || [ -e "$OFF/$n.txt" ]; then s="OFF"; else s="running"; fi
    printf "  %-12s %-20s %s\n" "$k" "$n" "$s"
  done
  if [ -e /root/marg_ingest/OFF ]; then s="OFF"; else s="running"; fi
  printf "  %-12s %-20s %s\n" "marg" "marg_ingest/OFF" "$s"
}

[ $# -ge 1 ] || usage
case "$1" in
  status) status; exit 0 ;;
  off|on) [ $# -eq 2 ] || usage ;;
  *) usage ;;
esac
key="$2"
[ -n "${M[$key]+x}" ] || usage
mkdir -p "$OFF"
n=${M[$key]}
if [ "$1" = "off" ]; then
  date -u +"switched off %Y-%m-%dT%H:%M:%SZ" > "$OFF/$n"
  echo "$key is now OFF ($OFF/$n)"
else
  rm -f "$OFF/$n" "$OFF/$n.txt"
  echo "$key is now running (marker removed)"
fi
echo
status
