#!/bin/bash
# install_S947_FIXTURE_MASK.sh -- S947 (the parent, S513, 24-Nov-2026): F-1639 + F-1648.
#   The ten-digit fixtures in four live recordings-archive scripts become made-up 50000k+last-four numbers. Only digits
#   inside those runs move; every selftest stays green; NO_PHONE_NUMBERS reads 0 over the four. One of them (..8409,
#   daily_digest.py) was a real patient number (F-1648). Nothing is restarted: call-pipeline runs these as fresh
#   subprocesses, and each file is swapped atomically (mv), mode and owner kept.
#   [1/5] kit sums  [2/5] the ground (each file is the 24-Nov bundle's or already S947's)  [3/5] the walk here, the live
#   files as FROM, + its control red  [4/5] backups + the swap + read-back (build lock)  [5/5] live selftests + the gate.
#   Any red, or the run killed between [4/5] and its end: every swapped file put back (atomic, mode kept, read back).
#   DRY=1: [1]-[3] only.  --undo: the backups back, only where the file is still S947's and the backup reads as FROM.
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s947kit && cp -rp /root/deploy/repo/deploy_kits/S947_FIXTURE_MASK /tmp/s947kit && bash /tmp/s947kit/install_S947_FIXTURE_MASK.sh
set -u
KIT="S947_FIXTURE_MASK"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; RA="${RA:-$ROOT/wa/recordings-archive}"
APY="${APY:-$ROOT/wa/venv/bin/python3}"; GATE="${GATE:-$ROOT/deploy/repo/deploy_kits/NO_PHONE_NUMBERS.py}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
LIVE="call_verdict.py daily_digest.py flag_investigator.py verdict_review.py"
declare -A WANT=([call_verdict.py]="SELFTEST: 42/42 PASS" [daily_digest.py]="SELFTEST: 81/81 PASS" [flag_investigator.py]="SELFTEST: 51/51 PASS" [verdict_review.py]="SELFTEST: 144 passed, 0 failed")
SCR="$(mktemp -d /tmp/s947_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0; CHANGED=""; FINISHED=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
m8() { m5 "$1" | cut -c1-8; }
from_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/FROM_PINS.md5"; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
bak_of() { echo "$RA/$1.bak_S947_$(from_of "$1" | cut -c1-8)"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
swap_in() {   # $1 live path, $2 source: same mode and owner as the live file, atomic
  local t="$(dirname "$1")/.$(basename "$1").s947"
  \cp "$2" "$t" && chmod --reference="$1" "$t" && chown --reference="$1" "$t" && mv -f "$t" "$1"; }
put_back() {  # every swapped file back from its backup; says each with its md5
  local n b bad=0
  for n in $CHANGED; do b="$(bak_of $n)"
    if [ "$(m5 "$b")" = "$(from_of $n)" ] && swap_in "$RA/$n" "$b" && [ "$(m5 "$RA/$n")" = "$(from_of $n)" ]; then say "   $n back: $(m8 "$RA/$n")"
    else say "   !! $n NOT back: $(m8 "$RA/$n") (backup $(m8 "$b"), expected $(from_of $n | cut -c1-8))"; bad=1; fi; done
  CHANGED=""; return $bad; }
restore() { say "!! RED ($1) - putting back"; put_back; say "   Tell Claude."; release_lock; exit 1; }
on_exit() { trap '' INT TERM HUP; if [ "$FINISHED" = 0 ] && [ -n "$CHANGED" ]; then say "!! the run ended before its proof - putting back"; put_back; fi
  release_lock; rm -rf "${SCR:?}"; rm -f "$RA"/.*.s947 2>/dev/null; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
trap 'exit 130' INT TERM HUP
stop() { say "$1"; release_lock; exit 1; }
pya() { (cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PYA_TIMEOUT:-600}" "$APY" -B "$@" 2>&1); }
take_lock() { [ -d "$(dirname "$LOCK")" ] || stop "!! $1 $(dirname "$LOCK") does not exist - STOP. Tell Claude."
  mkdir "$LOCK" 2>/dev/null || stop "!! $1 another build holds $LOCK - try again in five minutes. Nothing changed."; TOOK_LOCK=1; echo "$KIT $2" > "$LOCK/owner"; }
if [ "${1:-}" = "--undo" ]; then
  todo=""
  for n in $LIVE; do b="$(bak_of $n)"; h="$(m5 "$RA/$n")"
    [ "$h" = "$(from_of $n)" ] && continue
    [ -f "$b" ] || { [ "$h" = "$(to_of $n)" ] && stop "!! --undo: $RA/$n is S947's but its backup $b is gone - not undoing. Tell Claude."; continue; }
    [ "$h" = "$(to_of $n)" ] || stop "!! --undo: $RA/$n is ${h:0:8}, not S947's (a later kit?) - not undoing"
    [ "$(m5 "$b")" = "$(from_of $n)" ] || stop "!! --undo: the backup $b is $(m8 "$b"), not the 24-Nov bytes - not undoing. Tell Claude."
    todo="$todo $n"; done
  [ -z "$todo" ] && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  take_lock "--undo:" undo; CHANGED="$todo"; put_back || { release_lock; say "!! --undo incomplete - tell Claude"; exit 1; }
  release_lock; say "$KIT: UNDONE ($(echo $todo | wc -w) file(s) back to the 24-Nov bundle's bytes)"; exit 0
fi
cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "!! [1/5] KIT_ID.txt names another kit - nothing installed"
for n in $LIVE; do [ "$(m5 "$KDIR/to/$n")" = "$(to_of $n)" ] || stop "!! [1/5] the kit's $n is not as built - nothing installed"; done
say "   [1/5] kit sums ok"
[ -x "$APY" ] || stop "!! [2/5] $APY is not there - STOP. Tell Claude."
[ -f "$GATE" ] || stop "!! [2/5] $GATE is not there (git pull first) - STOP. Tell Claude."
todo=""; already=0
for n in $LIVE; do p="$RA/$n"; [ -f "$p" ] || stop "!! [2/5] $p is missing - STOP. Tell Claude."; h="$(m5 "$p")"
  if [ "$h" = "$(to_of $n)" ]; then already=$((already+1))
  elif [ "$h" = "$(from_of $n)" ]; then todo="$todo $n"
  else stop "!! [2/5] $p is ${h:0:8}, not $(from_of $n | cut -c1-8) (the 24-Nov bundle's) - it changed after this kit was built: STOP. Tell Claude."; fi; done
say "   [2/5] the ground: $(echo $todo | wc -w) to mask, $already already S947's"
[ -z "$todo" ] && { say "$KIT: ALREADY in place ($already file(s) S947's) - nothing to do"; exit 0; }
# The kit carries no FROM bytes (they hold the numbers): the walk's FROM is the live files, md5-checked above.
mkdir -p "$SCR/from" "$SCR/to"
for n in $LIVE; do if [ "$(m5 "$RA/$n")" = "$(from_of $n)" ]; then \cp "$RA/$n" "$SCR/from/$n"; else \cp "$KDIR/to/$n" "$SCR/from/$n"; fi; \cp "$KDIR/to/$n" "$SCR/to/$n"; done
pya "$KDIR/walk_s947.py" "$SCR/from" "$SCR/to" "$GATE" "$APY" > "$SCR/walk.txt"; rc=$?
[ "$rc" = 0 ] && tail -1 "$SCR/walk.txt" | grep -q "^WALK: 27/27 PASS" || { grep -E "FAIL" "$SCR/walk.txt" | head -8; stop "!! [3/5] the walk is not 27/27 here - nothing installed"; }
pya "$KDIR/walk_s947.py" "$SCR/from" "$SCR/from" "$GATE" "$APY" > "$SCR/ctl.txt"; rc=$?
[ "$rc" != 0 ] && grep -q "FAIL NO_PHONE_NUMBERS" "$SCR/ctl.txt" || stop "!! [3/5] the control (the FROM files judged) did not go red - the walk proves nothing here; nothing installed"
rm -rf "$SCR/from"
say "   [3/5] walk 27/27; control red $(grep -c '^  FAIL' "$SCR/ctl.txt")"
[ "${DRY:-0}" = 1 ] && { say "$KIT: DRY ok - nothing changed ($(echo $todo | wc -w) file(s) would be masked)"; exit 0; }
take_lock "[4/5]" install
for n in $todo; do p="$RA/$n"; b="$(bak_of $n)"
  \cp -p "$p" "$b" && chmod 600 "$b" && [ "$(m5 "$b")" = "$(from_of $n)" ] || restore "[4/5] the backup of $n did not read back"
  CHANGED="$CHANGED $n"
  swap_in "$p" "$KDIR/to/$n" && [ "$(m5 "$p")" = "$(to_of $n)" ] || restore "[4/5] $n did not read back as S947's"
  [ "${FORCE_RED_AT:-}" = "4:$n" ] && restore "[4/5] forced red after $n (rehearsal)"
  [ "${FORCE_KILL_AT:-}" = "4:$n" ] && kill -TERM $$
done
say "   [4/5] masked:$(for n in $todo; do printf ' %s %s' $n "$(m8 "$RA/$n")"; done) (backups 0600 beside each, .bak_S947_<from8>)"
bad=""; : > "$SCR/gl.txt"
for n in $LIVE; do out="$(pya "$RA/$n" --selftest)"; rc=$?
  [ "$rc" = 0 ] && echo "$out" | tail -2 | grep -qF "${WANT[$n]}" || bad="$bad $n"; echo "$RA/$n" >> "$SCR/gl.txt"; done
[ "${FORCE_RED_AT:-}" = "5" ] && bad="$bad (forced)"
[ "$(wc -l < "$SCR/gl.txt")" = 4 ] || bad="$bad (gate list)"
g="$(cd "$(dirname "$GATE")" && "$APY" -B "$GATE" --files-from "$SCR/gl.txt" 2>&1)"; grc=$?
echo "$g" | grep -q "4 staged file" || grc="$grc (did not read 4 files)"
[ -z "$bad" ] && [ "$grc" = 0 ] || restore "[5/5] live selftest red:${bad:- none}; gate exit $grc"
FINISHED=1; release_lock
say "$KIT: INSTALLED - $(echo $todo | wc -w) file(s) masked, all four live selftests green, NO_PHONE_NUMBERS 0 over them. Undo: bash $KDIR/install_S947_FIXTURE_MASK.sh --undo"
