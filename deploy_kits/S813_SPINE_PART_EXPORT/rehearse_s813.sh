#!/bin/bash
# rehearse_s813.sh -- the installer on a made-up root (device VM only). usage: bash rehearse_s813.sh <bundle root> <readings dir> <pylib>
set -u
K="$(cd "$(dirname "$0")" && pwd)"; B="$1"; RD="$2"; PL="$3"; W=/tmp/s813_reh; P=0; N=0
fresh() { rm -rf "$W"; mkdir -p "$W/root" "$W/lock"; cp -r "$B/root/finance" "$W/root/finance"; cp "$B/finance.db" "$W/root/finance/finance.db"; rm -rf "$W/lockdir"; }
run() { (cd "$K" && env ROOT="$W/root" LOCK="$W/lockdir" SPLOCK="$W/spine.lock" APY=python3 VPY=python3 PYTHONPATH="$PL" TMPW="$W" \
  SPINE_CMD="cd $W/root/finance/spine && python3 -B spine_build.py --readings $RD --rules spine_rules.json --out spine.db --finance-db $W/root/finance/finance.db" "$@" bash install_S813_SPINE_PART_EXPORT.sh 2>&1); }
ok() { N=$((N+1)); if [ "$1" = 1 ]; then P=$((P+1)); echo "  ok   $2"; else echo "  FAIL $2"; fi; }
SB=finance/spine/spine_build.py; FROM=67d5693fbd853fca7979fa4763f9f825; TO=$(awk '{print $1}' "$K/TO_PINS.md5")
m5() { md5sum "$1" | awk '{print $1}'; }
fresh; O=$(run DRY=1); [[ "$O" == *"DRY RUN: every gate"* && "$(m5 $W/root/$SB)" = "$FROM" ]] && ok 1 "DRY: green, nothing written" || { ok 0 "DRY"; echo "$O" | tail -5; }
fresh; echo "# x" >> "$W/root/$SB"; O=$(run); [[ "$O" == *"changed after this kit was built"* ]] && ok 1 "a live file not the pinned one: stop" || { ok 0 "pin stop"; echo "$O" | tail -3; }
fresh; mkdir "$W/lockdir"; O=$(run); [[ "$O" == *"another build holds the lock"* && "$(m5 $W/root/$SB)" = "$FROM" ]] && ok 1 "the build lock held: nothing done" || ok 0 "lock"
fresh; O=$(run SPINE_CMD=false); [[ "$O" == *"RED after placing"* && "$(m5 $W/root/$SB)" = "$FROM" ]] && ok 1 "the spine build failing after placing: the old file back" || { ok 0 "build red"; echo "$O" | tail -4; }
fresh; O=$(run REHEARSE_RED_AT=5); [[ "$O" == *"forced red"* && "$(m5 $W/root/$SB)" = "$FROM" ]] && ok 1 "a red at [5/6]: the old file back" || ok 0 "red at 5"
fresh; O=$(run); [[ "$O" == *"S813_SPINE_PART_EXPORT: DONE"* && "$(m5 $W/root/$SB)" = "$TO" && "$O" == *"part lists set aside: 3"* ]] && ok 1 "install: DONE, the spine built, 3 part lists set aside" || { ok 0 "install"; echo "$O" | tail -8; }
echo "$O" | sed -n '/\[1\/6\]/,$p' | sed 's/^/      /'
O2=$(run); [[ "$O2" == *"ALREADY INSTALLED"* ]] && ok 1 "again: ALREADY" || ok 0 "already"
U=$(echo "$O" | grep "undo (one line)" | sed 's/.*undo (one line): //'); eval "$U"; [ "$(m5 $W/root/$SB)" = "$FROM" ] && ok 1 "the undo line puts the old file back byte-identical" || ok 0 "undo"
cp -r "$K" "$W/kitcopy"; echo x >> "$W/kitcopy/walk_s813.py"; O=$(cd "$W/kitcopy" && ROOT="$W/root" bash install_S813_SPINE_PART_EXPORT.sh 2>&1); [[ "$O" == *"SUMS.md5 gate failed"* ]] && ok 1 "a kit file altered: stop" || ok 0 "sums"
rm -rf "$W"; find "$K" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "REHEARSAL $P/$N"
