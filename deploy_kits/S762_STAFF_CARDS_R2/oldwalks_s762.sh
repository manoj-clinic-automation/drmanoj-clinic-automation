#!/bin/bash
# oldwalks_s762.sh <page dir> <ring dir> <portal_console.py> -- S745's, S747's and S748's walks on the S762 page: every red
# must be one NAMED in EXPECTED_REDS.txt (the owner's rulings of 09-Nov change those counts on purpose), and every named
# one must be red. Prints 'OLD WALKS OK: ...' or 'OLD WALKS RED: ...'.
K="$(cd "$(dirname "$0")" && pwd)"; VPY="${VPY:-python3}"; out=""; bad=0
for w in walk_s745 walk_s747 walk_s748; do
  got=$(timeout 300 "$VPY" -B "$K/$w.py" "$1" "$2" "$3" 2>&1 | grep '^RED' | sed 's/^RED  //' | sed "s/^/$w|/" | sort)
  want=$(grep "^$w|" "$K/EXPECTED_REDS.txt" | sort)
  n=$(grep -c "^$w|" "$K/EXPECTED_REDS.txt")
  if [ "$got" = "$want" ]; then out="$out $w: $n named reds;"; else bad=1; out="$out $w: reds differ;"; fi
done
[ $bad = 0 ] && echo "OLD WALKS OK:$out" || echo "OLD WALKS RED:$out"
exit $bad
