#!/bin/bash
# oldwalks_s817.sh <page dir> <ring dir> <portal_console.py> -- the earlier walks on the S817 page. S748's walk (S745's and
# S747's whole, 103 checks): every red must be one NAMED in EXPECTED_REDS.txt -- the five S762 named, and the three checks of
# the follow-up sections' old line and colours that this kit changes on purpose (F14, F15, P4) -- and every named one must
# be red. S762's walk (36 checks) must be all green. Prints 'OLD WALKS OK: ...' or 'OLD WALKS RED: ...'.
K="$(cd "$(dirname "$0")" && pwd)"; VPY="${VPY:-python3}"; out=""; bad=0
got=$(timeout 300 "$VPY" -B "$K/walk_s748.py" "$1" "$2" "$3" 2>&1 | grep '^RED' | sed 's/^RED  //' | sed "s/^/walk_s748|/" | sort)
want=$(grep "^walk_s748|" "$K/EXPECTED_REDS.txt" | sort)
n=$(grep -c "^walk_s748|" "$K/EXPECTED_REDS.txt")
if [ "$got" = "$want" ]; then out="$out S748's walk: only the $n named reds;"; else bad=1; out="$out S748's walk: reds differ;"; fi
r=$(timeout 300 "$VPY" -B "$K/walk_s762.py" "$1" "$2" "$3" 2>&1 | tail -1)
case "$r" in "WALK OK"*) out="$out S762's walk: ${r#WALK OK: };";; *) bad=1; out="$out S762's walk: $r;";; esac
[ $bad = 0 ] && echo "OLD WALKS OK:$out" || echo "OLD WALKS RED:$out"
exit $bad
