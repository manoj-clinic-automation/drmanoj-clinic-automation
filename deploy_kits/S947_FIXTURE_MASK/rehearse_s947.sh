#!/bin/bash
# rehearse_s947.sh <kit> <work> <NO_PHONE_NUMBERS.py> <FROM dir> [1|2] -- S947 on a made-up root: every branch of the
# installer, read back by md5 and mode. The FROM dir is outside the kit (the kit carries no FROM bytes).
set -u; K="$1"; W="$2"; G="$3"; F="$4"; pass=0; fail=0; RAW="$W/root/wa/recordings-archive"
ok() { if eval "$2"; then pass=$((pass+1)); echo "  PASS $1"; else fail=$((fail+1)); echo "  FAIL $1"; fi; }
fresh() { rm -rf "$W"; mkdir -p "$RAW" "$W/root/wa/venv/bin" "$W/root/deploy/repo/deploy_kits"
  for n in call_verdict daily_digest flag_investigator verdict_review; do cp "$F/$n.py" "$RAW/"; chmod 755 "$RAW/$n.py"; done
  ln -s "$(command -v python3)" "$W/root/wa/venv/bin/python3"; cp "$G" "$W/root/deploy/repo/deploy_kits/NO_PHONE_NUMBERS.py"; }
run() { ROOT="$W/root" LOCK="$W/root/deploy/build.lock" bash "${KK:-$K}/install_S947_FIXTURE_MASK.sh" "$@" > "$W.out" 2>&1; echo $? > "$W.rc"; }
rc() { cat "$W.rc"; }
allis() { for n in call_verdict daily_digest flag_investigator verdict_review; do [ "$(md5sum < "$RAW/$n.py" | cut -c1-32)" = "$(awk -v f=$n.py '$2==f{print $1}' "$K/$1")" ] || return 1; done; }
modes() { for n in call_verdict daily_digest flag_investigator verdict_review; do [ "$(stat -c %a "$RAW/$n.py")" = 755 ] || return 1; done; }
noleft() { [ -z "$(ls -A "$RAW" | grep -E '^\.')" ] && [ ! -d "$W/root/deploy/build.lock" ] && [ -z "$(find "$K" -name __pycache__)" ]; }
case "${5:-all}" in 1|all)
fresh; DRY=1 run; ok "DRY exit 0, walk 27/27, control red, nothing changed" '[ $(rc) = 0 ] && grep -q "DRY ok" $W.out && grep -q "walk 27/27; control red" $W.out && allis FROM_PINS.md5'
run; ok "install: INSTALLED 4, all TO, modes kept, nothing left behind" '[ $(rc) = 0 ] && grep -q "INSTALLED - 4 file" $W.out && allis TO_PINS.md5 && modes && noleft'
ok "install: 4 backups 0600 with FROM bytes" '[ $(ls $RAW/*.bak_S947_* | wc -l) = 4 ] && [ "$(stat -c %a $RAW/daily_digest.py.bak_S947_8140f543)" = 600 ] && [ "$(md5sum < $RAW/daily_digest.py.bak_S947_8140f543 | cut -c1-8)" = 8140f543 ]'
run; ok "again: ALREADY" '[ $(rc) = 0 ] && grep -q "ALREADY" $W.out'
run --undo; ok "undo: 4 back, FROM bytes, modes kept" '[ $(rc) = 0 ] && grep -q "UNDONE (4" $W.out && allis FROM_PINS.md5 && modes && noleft'
run --undo; ok "undo twice: nothing to undo" '[ $(rc) = 0 ] && grep -q "nothing to undo" $W.out'
run; ok "install after an undo: INSTALLED again" '[ $(rc) = 0 ] && allis TO_PINS.md5'
: > "$RAW/verdict_review.py.bak_S947_280eb2ce"; run --undo; ok "undo with an emptied backup: refuses, nothing changed" '[ $(rc) = 1 ] && grep -q "not the 24-Nov bytes" $W.out && allis TO_PINS.md5'
fresh; run; mv "$RAW/verdict_review.py.bak_S947_280eb2ce" "$W.bak"; run --undo; ok "undo with a backup gone: refuses, nothing changed" '[ $(rc) = 1 ] && grep -q "backup .* is gone" $W.out && allis TO_PINS.md5'; rm -f "$W.bak"
;; esac
case "${5:-all}" in 2|all)
fresh; echo "# drift" >> "$RAW/verdict_review.py"; run; ok "drifted live file stops at [2/5], nothing changed" '[ $(rc) = 1 ] && grep -q "\[2/5\].*changed after" $W.out && [ -z "$(ls $RAW | grep bak_)" ]'
fresh; FORCE_RED_AT=4:flag_investigator.py run; ok "forced red at [4/5]: all FROM, modes 755, lock freed" '[ $(rc) = 1 ] && grep -q "putting back" $W.out && allis FROM_PINS.md5 && modes && noleft'
fresh; FORCE_RED_AT=5 run; ok "forced red at [5/5]: all four FROM, modes 755" '[ $(rc) = 1 ] && allis FROM_PINS.md5 && modes && noleft'
fresh; FORCE_KILL_AT=4:daily_digest.py run; ok "killed mid-[4/5]: put back, exit not 0, modes 755" '[ $(rc) != 0 ] && grep -q "ended before its proof" $W.out && allis FROM_PINS.md5 && modes && noleft'
fresh; mkdir "$W/root/deploy/build.lock"; run; ok "lock held: stops at [4/5], nothing changed" '[ $(rc) = 1 ] && grep -q "another build" $W.out && allis FROM_PINS.md5'
fresh; run; echo "# later kit" >> "$RAW/daily_digest.py"; run --undo; ok "undo refuses a file a later kit changed" '[ $(rc) = 1 ] && grep -q "not S947" $W.out'
fresh; rm -rf "$W.kit"; cp -rp "$K" "$W.kit"; echo x >> "$W.kit/to/daily_digest.py"; KK="$W.kit" run; ok "a corrupt kit stops at [1/5], nothing changed" '[ $(rc) = 1 ] && grep -q "\[1/5\]" $W.out && allis FROM_PINS.md5'; rm -rf "$W.kit"
fresh; rm "$W/root/deploy/repo/deploy_kits/NO_PHONE_NUMBERS.py"; run; ok "no gate on the box: stops at [2/5]" '[ $(rc) = 1 ] && grep -q "\[2/5\].*git pull first" $W.out && allis FROM_PINS.md5'
;; esac
rm -rf "$W" "$W.out" "$W.rc"; echo "REHEARSAL: $pass passed, $fail failed"; [ $fail = 0 ]
