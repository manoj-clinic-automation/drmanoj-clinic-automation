#!/bin/bash
# oldwalks_s818.sh <page dir> <portal dir> <portal_console.py> <finance dir> -- the earlier walks on the S818 page. S748's walk
# (S745's and S747's whole, 103 checks): every red must be one NAMED in EXPECTED_REDS.txt -- the same eight S817 named, none
# added by this kit -- and every named one must be red. S762's walk (36 checks) must be all green. S817's own walk (48 checks
# and its ten mutations) must be all green on this page (run without a page to compare with: its comparisons were with
# S762's page). The marks store is pointed at a file that is not there, so no earlier walk reads the live one.
# Prints 'OLD WALKS OK: ...' or 'OLD WALKS RED: ...'.
K="$(cd "$(dirname "$0")" && pwd)"; VPY="${VPY:-python3}"; out=""; bad=0
export PORTAL_WA_AWAITING_DB="${TMPDIR:-/tmp}/s818_oldwalks_no_store_$$/wa_awaiting.db"
got=$(timeout 300 "$VPY" -B "$K/walk_s748.py" "$1" "$2" "$3" 2>&1 | grep '^RED' | sed 's/^RED  //' | sed "s/^/walk_s748|/" | sort)
want=$(grep "^walk_s748|" "$K/EXPECTED_REDS.txt" | sort)
n=$(grep -c "^walk_s748|" "$K/EXPECTED_REDS.txt")
if [ "$got" = "$want" ]; then out="$out S748's walk: only the $n named reds;"; else bad=1; out="$out S748's walk: reds differ;"; fi
r=$(timeout 300 "$VPY" -B "$K/walk_s762.py" "$1" "$2" "$3" 2>&1 | tail -1)
case "$r" in "WALK OK"*) out="$out S762's walk: ${r#WALK OK: };";; *) bad=1; out="$out S762's walk: $r;";; esac
r=$(timeout 300 "$VPY" -B "$K/walk_s817.py" "$1" "$2" "$3" "$4" 2>&1 | tail -1)
case "$r" in "WALK OK: 48 of 48; 10 of 10 mutations red"*) out="$out S817's walk: 48 of 48, 10 of 10 mutations red;";; *) bad=1; out="$out S817's walk: $r;";; esac
[ $bad = 0 ] && echo "OLD WALKS OK:$out" || echo "OLD WALKS RED:$out"
exit $bad
