#!/bin/bash
# S243_RETIRE dry run — READ ONLY. Prints what retire_move.sh WOULD move, by category,
# with a reference check. Writes nothing, restarts nothing.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; . "$HERE/retire_lib.sh"
echo "== S243 RETIRE DRY-RUN $(TZ=Asia/Kolkata date '+%d-%b-%Y %H:%M IST') root=$ROOT =="
enumerate > /tmp/s243_dryrun.tsv
total=0; held=0; kb=0
for c in A_bakcopy B_backupdir C_buildhelper D_installresidue E_oneoff F_legacydata G_salaryoutput; do
  n=$(awk -F'\t' -v c="$c" '$1==c' /tmp/s243_dryrun.tsv | wc -l); [ "$n" -eq 0 ] && continue
  k=$(awk -F'\t' -v c="$c" '$1==c{s+=$3}END{print s+0}' /tmp/s243_dryrun.tsv)
  echo "-- $c : $n items, ${k} KB"
  awk -F'\t' -v c="$c" '$1==c{ if($4!="") printf "  HELD  %s  <- referenced by: %s\n",$2,$4; else printf "  move  %s\n",$2 }' /tmp/s243_dryrun.tsv
  total=$((total+n)); kb=$((kb+k))
done
held=$(awk -F'\t' '$4!=""' /tmp/s243_dryrun.tsv | wc -l)
echo "-- TOTAL candidates $total, HELD (referenced, will NOT move) $held, size ~$((kb/1024)) MB"
echo "-- live check now: clinic-finance $(systemctl is-active clinic-finance 2>/dev/null || echo n/a) · clinic-portal $(systemctl is-active clinic-portal 2>/dev/null || echo n/a)"
md5sum /tmp/s243_dryrun.tsv | awk '{print "-- list fingerprint " substr($1,1,12)}'
echo "== END DRY-RUN =="
