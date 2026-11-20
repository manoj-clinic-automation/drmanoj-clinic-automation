#!/bin/bash
# install_S897_TRACKER_SEED_REPLAY.sh -- S897 (the parent, S493, 20-Nov-2026): the tracker's move, session 2 -- the seed,
# Replay 2 on the box, the red line, the Docterz-reports door. NOTHING SWITCHES: the runner stays OFF (plan S492 FINAL s6.1).
#
# WHAT ONE RUN DOES (gates first; nothing live changes until [4/7]):
#   [1/7] the kit's own SUMS.md5 gate
#   [2/7] S895 is installed and OFF; the two live files are the bytes this kit was built on (owner_console.py c8a2263d,
#         freshness_legs.json 35595a1e); the finance app answers; no S897 cron line yet; the deploy lock is free
#   [3/7] every kit file compiles under the app's python and the venv's; pc_upload_watch --selftest 0; walk_s897 on a
#         made-up root against the LIVE reader (the controls red on the live files)
#   [4/7] placed: /root/finance/docterz_door.py (NEW) . owner_console.py (the door mounted + one console line; .bak_S897_)
#         . freshness_legs.json (+ one leg; .bak_S897_) . /root/followup_tracker/{seed_take,replay2_s897,pc_upload_watch}.py;
#         the finance app restarted; healthz 200; the door's page answers (200/302/303/401/403 = mounted; 404/000/5xx = not)
#   [5/7] cron: pc_upload_watch every 10 minutes (# S897_PC_UPLOAD_WATCH, NOT gated by OFF -- it watches before and after
#         the switch); one check run now ('not switched yet')
#   [6/7] THE SEED: seed_take.py takes the newest TRACKER_SEED_*.zip from the Drive folder (sha256 checked, paths translated,
#         placed, SEEDED_AT). No seed in Drive yet -> said, the rest stands; run `seed_take.py` later with one line.
#   [7/7] REPLAY 2 on the box (only when seeded): replay2_s897.py --run -> logs/REPLAY2_REPORT.txt; counts on the screen.
#         A FAIL there changes nothing live (the runner is OFF) -- it is read by Claude before the switch evening.
#   RED at [4/7]-[5/7]: the two files back from their .bak, the new files out, the app restarted. The seed is never undone by
#   a red (it is data, mode 600, the runner OFF); --undo keeps it too and says so.
#   --undo : the two files back, docterz_door.py set aside as .undone_S897, the cron line out, the watcher's state removed,
#            the app restarted. /root/followup_tracker/ and its seed stay (never deleted by an undo).
set -u
KIT="S897_TRACKER_SEED_REPLAY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="${FIN:-$ROOT/finance}"; FUT="${FUT:-$ROOT/followup_tracker}"; WA="${WA:-$ROOT/wa}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; CRONTAB="${CRONTAB:-crontab}"
MARK="# S897_PC_UPLOAD_WATCH"; MIN_CRON=20
OC_FROM="c8a2263d"; LEGS_FROM="35595a1e"
NEWFIN="docterz_door.py"; NEWFUT="seed_take.py replay2_s897.py pc_upload_watch.py"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s897_inst_$STAMP"; TOOK_LOCK=0; PLACED=0
mkdir -p "$SCR" && chmod 700 "$SCR"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
m8() { m5 "$1" | cut -c1-8; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
fget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fget /finance/healthz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
cron_has() { "$CRONTAB" -l 2>/dev/null | grep -qF "$MARK"; }
cron_read() { "$CRONTAB" -l > "$SCR/cron.cur" 2>/dev/null && [ "$(grep -c . "$SCR/cron.cur")" -ge "$MIN_CRON" ]; }
cron_drop() { cron_read || { say "!! the crontab could not be read whole - left as it is"; return 1; }
  grep -vF "$MARK" "$SCR/cron.cur" > "$SCR/cron.new"; "$CRONTAB" "$SCR/cron.new"; }
pya() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 300 "$APY" -W ignore -B "$@" 2>&1); }
pyv() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PYV_TIMEOUT:-3600}" "$VPY" -W ignore -B "$@" 2>&1); }
restore() {
  say "!! RED after placing ($1) - putting the files back"
  [ -f "$FIN/owner_console.py.bak_S897_$OC_FROM" ] && mv -f "$FIN/owner_console.py.bak_S897_$OC_FROM" "$FIN/owner_console.py"
  [ -f "$FIN/freshness_legs.json.bak_S897_$LEGS_FROM" ] && mv -f "$FIN/freshness_legs.json.bak_S897_$LEGS_FROM" "$FIN/freshness_legs.json"
  [ -f "$FIN/$NEWFIN" ] && mv -f "$FIN/$NEWFIN" "$FIN/$NEWFIN.undone_S897"
  for n in $NEWFUT; do rm -f "$FUT/$n"; done
  cron_has && { cron_drop >/dev/null 2>&1 || say "   !! the $MARK cron line is STILL in the crontab (it could not be read whole) - tell Claude"; }
  "$SYSTEMCTL" restart "$FSVC" >/dev/null 2>&1 || true
  if [ "$(m8 "$FIN/owner_console.py")" = "$OC_FROM" ] && [ "$(m8 "$FIN/freshness_legs.json")" = "$LEGS_FROM" ]; then
    say "   restored: owner_console.py $OC_FROM, freshness_legs.json $LEGS_FROM, the door set aside; finance healthz $(wait200)"
  else
    say "   !! restore incomplete (owner_console $(m8 "$FIN/owner_console.py"), legs $(m8 "$FIN/freshness_legs.json")) - send a photo of this screen to Claude"
  fi
  release_lock; exit 1
}
# ── undo ──────────────────────────────────────────────────────────────────────────────────────────
if [ "${1:-}" = "--undo" ]; then
  if [ "$(m8 "$FIN/owner_console.py")" = "$OC_FROM" ] && [ "$(m8 "$FIN/freshness_legs.json")" = "$LEGS_FROM" ] && [ ! -f "$FIN/$NEWFIN" ] && ! cron_has; then
    say "-- $KIT is not installed; nothing to undo"; exit 0; fi
  for spec in "$FIN/owner_console.py|finance/owner_console.py|$OC_FROM" "$FIN/freshness_legs.json|finance/freshness_legs.json|$LEGS_FROM"; do
    p="${spec%%|*}"; r="${spec#*|}"; rel="${r%%|*}"; from="${r#*|}"
    [ "$(m8 "$p")" = "$from" ] || [ "$(m5 "$p")" = "$(to_of "$rel")" ] || stop "!! $p is $(m8 "$p"), neither this kit's nor its FROM - a later kit owns it; nothing undone. Tell Claude."
    [ "$(m8 "$p")" = "$from" ] || { [ -f "$p.bak_S897_$from" ] && [ "$(m8 "$p.bak_S897_$from")" = "$from" ]; } || stop "!! no good backup for $p - nothing undone"
  done
  mkdir "$LOCK" 2>/dev/null || stop "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."
  TOOK_LOCK=1; echo "$KIT undo" > "$LOCK/owner"
  cron_has && { cron_drop || stop "!! the cron line could not be removed - nothing undone. Run it again in a minute."; }
  for spec in "$FIN/owner_console.py|$OC_FROM" "$FIN/freshness_legs.json|$LEGS_FROM"; do
    p="${spec%%|*}"; from="${spec#*|}"; [ "$(m8 "$p")" = "$from" ] || \cp -p "$p.bak_S897_$from" "$p"; done
  [ -f "$FIN/$NEWFIN" ] && mv -f "$FIN/$NEWFIN" "$FIN/$NEWFIN.undone_S897"
  for n in $NEWFUT; do rm -f "$FUT/$n"; done
  rm -f "$FUT/pc_upload_watch.state.json"
  "$SYSTEMCTL" restart "$FSVC"; h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but finance healthz is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE (two files back, the door set aside, the watcher's cron line out; $FSVC restarted, finance healthz 200)."
  [ -f "$FUT/SEEDED_AT" ] && say "   the seed in $FUT stays (an undo never deletes ledgers); the runner is $([ -e "$FUT/OFF" ] && echo OFF || echo 'NOT OFF - tell Claude')"
  exit 0
fi
# ── [1/7] the kit ─────────────────────────────────────────────────────────────────────────────────
cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/7] SUMS.md5 gate failed - kit corrupt, nothing installed"
for f in $NEWFIN $NEWFUT owner_console.py freshness_legs.json walk_s897.py seed_pack.py; do [ -f "$KDIR/$f" ] || stop "!! [1/7] $f missing from the kit"; done
say "   [1/7] kit sums ok"
# ── [2/7] the box ─────────────────────────────────────────────────────────────────────────────────
[ -f "$FIN/$NEWFIN" ] && [ "$(m5 "$FIN/$NEWFIN")" = "$(to_of "finance/$NEWFIN")" ] && stop "-- $KIT is already installed ($FIN/$NEWFIN at its TO pin); nothing done. The seed alone, one line: FUT_ROOT=$FUT $VPY -B $FUT/seed_take.py   (then Replay 2: FUT_ROOT=$FUT $VPY -B $FUT/replay2_s897.py --run)"
[ -x "$APY" ] && [ -x "$VPY" ] || stop "!! [2/7] python ($APY) or the venv ($VPY) is not there - nothing installed"
[ -f "$FUT/processor.py" ] && [ -f "$FUT/server_runner.py" ] || stop "!! [2/7] $FUT holds no engine - S895 is not installed. STOP. Tell Claude."
[ -e "$FUT/OFF" ] || stop "!! [2/7] $FUT/OFF is ABSENT - the runner is not off. STOP, nothing installed. Tell Claude."
[ -e "$FUT/SWITCHED_AT" ] && stop "!! [2/7] $FUT/SWITCHED_AT is present - this kit is for BEFORE the switch. STOP. Tell Claude."
[ "$(m8 "$FIN/owner_console.py")" = "$OC_FROM" ] || stop "!! [2/7] $FIN/owner_console.py is $(m8 "$FIN/owner_console.py"), not $OC_FROM (the 20-Nov bundle) - STOP, nothing installed. Tell Claude."
[ "$(m8 "$FIN/freshness_legs.json")" = "$LEGS_FROM" ] || stop "!! [2/7] $FIN/freshness_legs.json is $(m8 "$FIN/freshness_legs.json"), not $LEGS_FROM - STOP, nothing installed. Tell Claude."
[ -f "$FIN/docterz_pickup.py" ] && [ -f "$FIN/docterz_ingest.py" ] || stop "!! [2/7] $FIN lacks docterz_pickup.py or docterz_ingest.py - STOP. Tell Claude."
[ -f "$FIN/$NEWFIN" ] && stop "!! [2/7] $FIN/$NEWFIN already exists - STOP, nothing installed. Tell Claude."
cron_has && stop "!! [2/7] the crontab already holds a $MARK line - STOP, nothing installed. Tell Claude."
f0=$(fget /finance/healthz); [ "$f0" = 200 ] || stop "!! [2/7] finance healthz $f0 before the install - nothing installed"
mkdir "$LOCK" 2>/dev/null || stop "!! [2/7] another build holds the lock $LOCK - run it again in five minutes."
TOOK_LOCK=1; echo "$KIT install" > "$LOCK/owner"
say "   [2/7] S895 installed and OFF; owner_console.py $OC_FROM, freshness_legs.json $LEGS_FROM; finance healthz 200"
# ── [3/7] proofs ──────────────────────────────────────────────────────────────────────────────────
for f in "$KDIR"/*.py; do pya -m py_compile "$f" >/dev/null 2>&1 || stop "!! [3/7] $(basename "$f") does not compile under $APY - nothing installed"; done
for f in seed_take.py replay2_s897.py pc_upload_watch.py; do pyv -m py_compile "$KDIR/$f" >/dev/null 2>&1 || stop "!! [3/7] $f does not compile in the venv - nothing installed"; done
st="$(pyv "$KDIR/pc_upload_watch.py" --selftest | tail -1)"
[ "$st" = "selftest: 0 failure(s)" ] || stop "!! [3/7] pc_upload_watch selftest: '$st' - nothing installed"
mkdir -p "$SCR/live" && \cp -p "$FIN/docterz_pickup.py" "$FIN/owner_console.py" "$FIN/freshness_legs.json" "$FIN/freshness.py" "$SCR/live/" 2>/dev/null
W="$(pya "$KDIR/walk_s897.py" "$KDIR" "$SCR/live" | tail -1)"
case "$W" in "walk_s897: "*" 0 failure(s)") ;; *) stop "!! [3/7] $W - nothing installed";; esac
say "   [3/7] compiles (app python + venv); watcher selftest 0; $W (made-up root, the LIVE reader)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and proof green; nothing live changed"; exit 0; fi
# ── [4/7] place ───────────────────────────────────────────────────────────────────────────────────
\cp -p "$FIN/owner_console.py" "$FIN/owner_console.py.bak_S897_$OC_FROM" && [ "$(m8 "$FIN/owner_console.py.bak_S897_$OC_FROM")" = "$OC_FROM" ] || stop "!! [4/7] could not write the backup of owner_console.py - nothing placed"
\cp -p "$FIN/freshness_legs.json" "$FIN/freshness_legs.json.bak_S897_$LEGS_FROM" && [ "$(m8 "$FIN/freshness_legs.json.bak_S897_$LEGS_FROM")" = "$LEGS_FROM" ] || stop "!! [4/7] could not write the backup of freshness_legs.json - nothing placed"
PLACED=1
\cp -p "$KDIR/$NEWFIN" "$FIN/$NEWFIN" && chmod 600 "$FIN/$NEWFIN" || restore "placing $NEWFIN"
for n in $NEWFUT; do \cp -p "$KDIR/$n" "$FUT/$n" && chmod 600 "$FUT/$n" || restore "placing $n"; done
\cp -p "$KDIR/owner_console.py" "$FIN/.owner_console.py.s897" && mv -f "$FIN/.owner_console.py.s897" "$FIN/owner_console.py" || restore "placing owner_console.py"
\cp -p "$KDIR/freshness_legs.json" "$FIN/.freshness_legs.json.s897" && mv -f "$FIN/.freshness_legs.json.s897" "$FIN/freshness_legs.json" || restore "placing freshness_legs.json"
for spec in "$FIN/owner_console.py|finance/owner_console.py" "$FIN/freshness_legs.json|finance/freshness_legs.json" "$FIN/$NEWFIN|finance/$NEWFIN"; do
  p="${spec%%|*}"; rel="${spec#*|}"; [ "$(m5 "$p")" = "$(to_of "$rel")" ] || restore "$p read back $(m8 "$p"), not its TO pin"; done
for n in $NEWFUT; do [ "$(m5 "$FUT/$n")" = "$(to_of "followup_tracker/$n")" ] || restore "$FUT/$n read back $(m8 "$FUT/$n"), not its TO pin"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/7]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
for u in /finance/console /finance/console/docterz-reports /finance/console/docterz-reports/healthz /finance/console/off-days; do
  pg=$(fget "$u"); case "$pg" in 200|302|303|401|403) ;; *) restore "$u answered $pg (not mounted)";; esac; done
say "   [4/7] placed and read back at their TO pins: $NEWFIN (NEW) . owner_console.py $(m8 "$FIN/owner_console.py") . freshness_legs.json $(m8 "$FIN/freshness_legs.json") . $FUT/{$(echo $NEWFUT | tr ' ' ',')}"
say "         $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the door's page answers"
# ── [5/7] the watcher's cron ──────────────────────────────────────────────────────────────────────
cron_read || restore "the crontab could not be read whole (nothing written to it)"
{ cat "$SCR/cron.cur"
  echo "*/10 * * * * TZ=Asia/Kolkata $VPY -B $FUT/pc_upload_watch.py >> $FUT/logs/pc_upload_watch.log 2>&1 $MARK"
} > "$SCR/cron.new"
"$CRONTAB" "$SCR/cron.new" || restore "the crontab would not take the line"
[ "$("$CRONTAB" -l 2>/dev/null | grep -c .)" -ge "$(( $(grep -c . "$SCR/cron.cur") + 1 ))" ] || restore "the crontab read back shorter than before"
mkdir -p "$FUT/logs" && chmod 700 "$FUT/logs"
w1="$(FUT_ROOT="$FUT" pyv "$FUT/pc_upload_watch.py" | tail -1)"
case "$w1" in "ok  not switched"*) ;; *) restore "the watcher's first check said: $w1";; esac
say "   [5/7] cron line placed ($MARK, every 10 min, not gated by OFF); first check: $w1"
release_lock
say "         undo (one line): bash $KDIR/install_$KIT.sh --undo"
# ── [6/7] the seed ────────────────────────────────────────────────────────────────────────────────
if [ -f "$FUT/SEEDED_AT" ] && [ "${RESEED:-0}" != 1 ]; then
  say "   [6/7] already seeded: $(head -1 "$FUT/SEEDED_AT") -- kept (say RESEED=1 to take a newer seed from Drive)"
  SEEDED=1
else
  if [ -n "${SEED_CMD:-}" ]; then sd="$($SEED_CMD 2>&1)"; else sd="$(FUT_ROOT="$FUT" pyv "$FUT/seed_take.py" --root "$FUT" $([ "${RESEED:-0}" = 1 ] && echo --again) 2>&1)"; fi
  if echo "$sd" | grep -q '^PLACED'; then
    say "   [6/7] THE SEED: $(echo "$sd" | grep '^seed:' | head -1 | cut -c1-80)"
    say "         $(echo "$sd" | grep '^PLACED' | head -1)"
    SEEDED=1
  else
    say "   [6/7] THE SEED: not taken -- $(echo "$sd" | tail -1 | cut -c1-200)"
    say "         (the rest of this kit stands; when the seed is in Drive, one line: FUT_ROOT=$FUT $VPY -B $FUT/seed_take.py)"
    SEEDED=0
  fi
fi
# ── [7/7] replay 2 ────────────────────────────────────────────────────────────────────────────────
if [ "$SEEDED" = 1 ]; then
  if [ -n "${REPLAY_CMD:-}" ]; then rp="$($REPLAY_CMD 2>&1)"; else
    rp="$(FUT_ROOT="$FUT" FU_INBOX_DIR="$WA/followup-inbox" REPLAY2_SCRATCH="$SCR/replay" pyv "$FUT/replay2_s897.py" --run --report "$FUT/logs/REPLAY2_REPORT.txt" 2>&1)"; fi
  rs="$(echo "$rp" | grep '^RESULT:' | tail -1)"
  say "   [7/7] REPLAY 2 on the box: ${rs:-did not finish -- $(echo "$rp" | tail -1 | cut -c1-160)}"
  echo "$rp" | grep -q '^NOTHING COMPARED' && say "         !! NOTHING COMPARED -- every run skipped: not a proof. Tell Claude."
  echo "$rp" | grep -E '^#[0-9]+ .* (FAIL|SKIP)' | head -12 | sed 's/^/         /'
  say "         the report: $FUT/logs/REPLAY2_REPORT.txt"
else
  say "   [7/7] REPLAY 2: waits for the seed"
fi
say ""
say "$KIT: DONE (the runner stays OFF; nothing switched). Seed: $([ "$SEEDED" = 1 ] && echo 'PLACED' || echo 'NOT YET'). Replay 2: ${rs:-not run}."
say "      the door: https://followup.dr-manoj.in/finance/console/docterz-reports . the red line: the health page's 'clinic PC still sending after the switch'"
exit 0
