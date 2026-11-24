#!/bin/bash
# rehearse_s946.sh -- S946's installer on a MADE-UP root (no live file, no systemctl, no crontab, no sheet: CSV stand-ins).
#   scenes: DRY (keep) . install (keep: runner + cron + legs A) . ALREADY . undo . install again . forced red at [4/6] restores .
#           forced red at [5/6] restores . the RETIRE branch (no web log carries the route: watchdog moved, legs B, no cron) .
#           its undo brings the watchdog back . a drifted worker stops . the pipeline lock busy for too long restores .
#   bash rehearse_s946.sh <kitdir> [workdir] [part 1-4 | all]   (parts in order; the roots persist in workdir between parts)
set -u
KDIR="$(cd "$1" && pwd)"; W="${2:-/tmp/s946_reh}"; PART="${3:-all}"; [ "$PART" = all ] || [ "$PART" = 1 ] && { rm -rf "$W"; mkdir -p "$W"; }; PASS=0; FAIL=0
in_part() { [ "$PART" = all ] || [ "$PART" = "$1" ]; }   # the whole thing takes ~8 min; run as parts 1..4 (in order) where a call may not run that long
ok() { PASS=$((PASS+1)); echo "  ok   $1"; }
bad() { FAIL=$((FAIL+1)); echo "  FAIL $1"; }
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
WK_FROM="$(m5 "$KDIR/from_worker.py")"; LG_FROM="$(m5 "$KDIR/from_legs.json")"
WK_TO="$(to_of call_pipeline_worker.py)"; LA_TO="$(to_of freshness_legs_a.json)"; LB_TO="$(to_of freshness_legs_b.json)"; RN_TO="$(to_of callhook_watch_run.py)"
mkroot() {   # $1 = root ; $2 = weblog carries the route (1) or not (0)
  local R="$1"; rm -rf "$R"; mkdir -p "$R/finance/_off" "$R/finance/logs" "$R/wa/recordings-archive/pipeline_queue" "$R/wa/call-hook" "$R/bin" "$R/weblogs" "$R/tabs" "$R/deploy"
  cp -p "$KDIR/from_worker.py" "$R/wa/recordings-archive/call_pipeline_worker.py"
  cp -p "$KDIR/from_legs.json" "$R/finance/freshness_legs.json"
  cp -p "$KDIR/from/callhook_watchdog.py" "$R/wa/call-hook/callhook_watchdog.py"
  mkdir -p "$R/wa/call-hook/call_hook_logs"; echo '{"x":1}' > "$R/wa/call-hook/call_hook_logs/$(date -d yesterday +%F).jsonl"
  if [ "$2" = 1 ]; then printf '1.2.3.4 - - [%s +0530] "POST /mo-callhook?key=madeup HTTP/1.1" 200 20 "-" "Go"\n' "$(date -d yesterday '+%d/%b/%Y:10:00:00')" > "$R/weblogs/site.access_log"
  else echo 'nothing of ours' > "$R/weblogs/site.access_log"; fi
  # a stub freshness.py: counts the legs beside it (the live one reads its conf)
  cat > "$R/finance/freshness.py" <<'PY'
import json, os, sys
d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "freshness_legs.json")))
print("[stub] %d leg(s) declared in freshness_legs.json" % len(d["legs"]))
PY
  # the tabs: the walk's own fixture shape, built by the walk's code path (made at run time, no literals here)
  python3 - "$R/tabs" <<'PY'
import csv, sys, os
d = sys.argv[1]
VH = ["Date","Time","Direction","Patient Number","Agent","Patient Name","Clinic ID","Duration","Claimed Outcome","AI Outcome","Verdict","Match Confidence","Outcome TRUE/FALSE","AI Reason","Evidence","Spoke With","Confidence","Flag PostOp","Flag Complaint","Flag Urgent","Flag Surgery","Flag Clinical","Flag Conduct","Conduct Note","Recording Link","Transcript Link","Join Key","Status","Error","Judged At","Prompt Ver","Model","Doctor Flag","Doctor Note","Final Outcome"]
TH = ["Date","Time","Direction","Duration","Join Key","Status","Transcript Drive Link","Transcript Drive File ID"]
def jk(i, ts): return "".join(["9","0","0","0","0","0","0"]) + "%03d" % i + "_" + str(ts)
def vrow(date, key, status):
    r = [""] * len(VH); r[0] = date; r[VH.index("Join Key")] = key; r[VH.index("Status")] = status; r[VH.index("Verdict")] = "Match" if status == "done" else ""; return r
def trow(date, key): return [date, "10:00", "in", "61", key, "done", "https://drive.example/t", "id"]
V, T = [VH], [TH]
for i in range(2):
    k = jk(i, 1754000000 + i); V += [vrow("2026-08-0%d" % (i+1), k, "FAILED"), vrow("2026-08-0%d" % (i+1), k, "done")]; T.append(trow("2026-08-0%d" % (i+1), k))
k = jk(5, 1752000000); T.append(trow("2026-07-05", k))
csv.writer(open(os.path.join(d, "Call_Verdicts.csv"), "w", newline="")).writerows(V)
csv.writer(open(os.path.join(d, "Call_Transcripts.csv"), "w", newline="")).writerows(T)
PY
  # stubs: systemctl (active unless the flag says down; restart re-raises it), crontab (a file)
  cat > "$R/bin/systemctl" <<'SH'
#!/bin/bash
F="$STUB_ROOT/svc_down"
case "$1" in is-active) [ ! -e "$F" ];; restart) echo "restart $2" >> "$STUB_ROOT/svc.log"; rm -f "$F"; exit "${RESTART_RC:-0}";; *) exit 0;; esac
SH
  cat > "$R/bin/crontab" <<'SH'
#!/bin/bash
F="$STUB_ROOT/crontab.txt"; [ -f "$F" ] || echo "0 3 * * * /bin/true # an older line" > "$F"
case "${1:-}" in -l) cat "$F";; -) cat > "$F.new" && mv -f "$F.new" "$F";; esac    # read whole before the write, as the real crontab does
SH
  chmod +x "$R/bin/"*
}
ENVS() { local R="$1"; echo "ROOT=$R FIN=$R/finance WA=$R/wa RA=$R/wa/recordings-archive CH=$R/wa/call-hook APY=$(command -v python3) RET=$R/_retired/S510 LOCK=$R/deploy/.lock PSVC=call-pipeline SYSTEMCTL=$R/bin/systemctl CRONTAB=$R/bin/crontab STUB_ROOT=$R CAND_GLOBS=$R/weblogs/*access* S946_FAKE_DIR=$R/tabs NAP=0 LOCK_TRIES=2 FRESH=$R/finance/freshness.py"; }
run_inst() { local R="$1"; shift; env $(ENVS "$R") "$@" bash "$KDIR/install_S946_A2_REST.sh" "${EXTRA:-}" 2>&1; }

R="$W/keep"
if in_part 1; then mkroot "$R" 1
out="$(run_inst "$R" DRY=1)"; echo "$out" | grep -q "DRY RUN: every gate" && echo "$out" | grep -q "watchdog: KEEP" && [ "$(m5 "$R/wa/recordings-archive/call_pipeline_worker.py")" = "$WK_FROM" ] && [ ! -f "$R/wa/call-hook/callhook_watch_run.py" ] && ls "$R/wa/recordings-archive/backup_S946/" | grep -q Call_Verdicts && ok "DRY (keep): gates, probe KEEP, nothing placed, the backup CSV written" || { bad "DRY keep"; echo "$out" | tail -8; }
out="$(run_inst "$R")"; echo "$out" | grep -q "S946_A2_REST: DONE" && [ "$(m5 "$R/wa/recordings-archive/call_pipeline_worker.py")" = "$WK_TO" ] && [ "$(m5 "$R/finance/freshness_legs.json")" = "$LA_TO" ] && [ "$(m5 "$R/wa/call-hook/callhook_watch_run.py")" = "$RN_TO" ] && grep -q "S946_CALLHOOK_WATCH" "$R/crontab.txt" && grep -q "an older line" "$R/crontab.txt" && grep -q "restart call-pipeline" "$R/svc.log" && [ -f "$R/wa/call-hook/callhook_watchdog.state.json" ] && echo "$out" | grep -q "CLEANUP OK: removed 2, marked 1" && [ -f "$R/wa/recordings-archive/call_pipeline_worker.py.bak_S946_${WK_FROM:0:8}" ] && ok "install (keep): worker TO, legs A, runner + cron, service restarted, first watch, one-off removed 2 marked 1" || { bad "install keep"; echo "$out" | tail -12; }
out="$(run_inst "$R")"; echo "$out" | grep -q "already installed" && [ "$(wc -l < "$R/svc.log")" = 1 ] && ok "ALREADY: nothing done, no second restart" || { bad "ALREADY"; echo "$out" | tail -4; }
out="$(EXTRA=--undo run_inst "$R")"; echo "$out" | grep -q "UNDONE" && [ "$(m5 "$R/wa/recordings-archive/call_pipeline_worker.py")" = "$WK_FROM" ] && [ "$(m5 "$R/finance/freshness_legs.json")" = "$LG_FROM" ] && [ ! -f "$R/wa/call-hook/callhook_watch_run.py" ] && ! grep -q "S946_CALLHOOK_WATCH" "$R/crontab.txt" && grep -q "an older line" "$R/crontab.txt" && [ "$(wc -l < "$R/svc.log")" = 2 ] && ok "undo: files back, runner aside, cron out, the older cron line kept, service restarted" || { bad "undo"; echo "$out" | tail -6; }
fi
if in_part 2; then
out="$(run_inst "$R")"; echo "$out" | grep -q "S946_A2_REST: DONE" && echo "$out" | grep -q "CLEANUP OK: removed 0, marked 0" && ok "install again after undo: DONE, the one-off finds nothing more" || { bad "install again"; echo "$out" | tail -6; }
out="$(EXTRA=--undo run_inst "$R")"; echo "$out" | grep -q "UNDONE" && ok "undo again" || bad "undo again"
out="$(run_inst "$R" REHEARSE_RED_AT=4)"; echo "$out" | grep -q "RED (rehearsal: a forced red at \[4/6\])" && [ "$(m5 "$R/wa/recordings-archive/call_pipeline_worker.py")" = "$WK_FROM" ] && [ "$(m5 "$R/finance/freshness_legs.json")" = "$LG_FROM" ] && [ ! -f "$R/wa/call-hook/callhook_watch_run.py" ] && ! grep -q "S946_CALLHOOK_WATCH" "$R/crontab.txt" && [ ! -d "$R/deploy/.lock" ] && ok "forced red at [4/6]: everything back, lock released" || { bad "red at 4"; echo "$out" | tail -6; }
fi
if in_part 3; then
out="$(run_inst "$R" REHEARSE_RED_AT=5)"; echo "$out" | grep -q "RED (rehearsal: a forced red at \[5/6\])" && [ "$(m5 "$R/wa/recordings-archive/call_pipeline_worker.py")" = "$WK_FROM" ] && ! grep -q "S946_CALLHOOK_WATCH" "$R/crontab.txt" && ok "forced red at [5/6] (after the one-off): files and cron back" || { bad "red at 5"; echo "$out" | tail -6; }

R2="$W/retire"; mkroot "$R2" 0
out="$(run_inst "$R2" DRY=1)"; echo "$out" | grep -q "watchdog: RETIRE" && [ -f "$R2/wa/call-hook/callhook_watchdog.py" ] && ok "DRY (retire): the probe says RETIRE, nothing moved" || { bad "DRY retire"; echo "$out" | tail -6; }
out="$(run_inst "$R2")"; echo "$out" | grep -q "S946_A2_REST: DONE" && [ ! -f "$R2/wa/call-hook/callhook_watchdog.py" ] && [ -f "$R2/_retired/S510/callhook_watchdog.py" ] && [ "$(m5 "$R2/finance/freshness_legs.json")" = "$LB_TO" ] && [ ! -f "$R2/wa/call-hook/callhook_watch_run.py" ] && ! grep -q "S946_CALLHOOK_WATCH" "$R2/crontab.txt" && [ "$(m5 "$R2/wa/recordings-archive/call_pipeline_worker.py")" = "$WK_TO" ] && ok "install (retire): watchdog moved to _retired, legs B, no runner, no cron, worker TO" || { bad "install retire"; echo "$out" | tail -8; }
fi
if in_part 4; then R2="$W/retire"
out="$(run_inst "$R2")"; echo "$out" | grep -q "already installed (RETIRED already" && ok "ALREADY (retire branch)" || { bad "ALREADY retire"; echo "$out" | tail -4; }
out="$(EXTRA=--undo run_inst "$R2")"; echo "$out" | grep -q "UNDONE" && [ -f "$R2/wa/call-hook/callhook_watchdog.py" ] && [ ! -f "$R2/_retired/S510/callhook_watchdog.py" ] && [ "$(m5 "$R2/finance/freshness_legs.json")" = "$LG_FROM" ] && ok "undo (retire): the watchdog back in place, legs back" || { bad "undo retire"; echo "$out" | tail -6; }

R3="$W/drift"; mkroot "$R3" 1; echo "# drift" >> "$R3/wa/recordings-archive/call_pipeline_worker.py"
out="$(run_inst "$R3")"; echo "$out" | grep -q "\[2/6\].*call_pipeline_worker.py is" && [ ! -f "$R3/wa/call-hook/callhook_watch_run.py" ] && ok "a drifted worker stops at [2/6], nothing placed" || { bad "drift"; echo "$out" | tail -4; }
R4="$W/busy"; mkroot "$R4" 1
out="$( (exec 9>"$R4/wa/recordings-archive/pipeline.lock"; flock 9; run_inst "$R4") )"; echo "$out" | grep -q "RED (restart call-pipeline" && [ "$(m5 "$R4/wa/recordings-archive/call_pipeline_worker.py")" = "$WK_FROM" ] && ! grep -q "S946_CALLHOOK_WATCH" "$R4/crontab.txt" && ok "the pipeline lock held too long: restore, nothing live" || { bad "busy"; echo "$out" | tail -6; }
R6="$W/quiet"; mkroot "$R6" 1
out="$(run_inst "$R6" REHEARSE_CLOCK=0300)"; echo "$out" | grep -q "inside the night sweeps' window" && [ "$(m5 "$R6/wa/recordings-archive/call_pipeline_worker.py")" = "$WK_FROM" ] && ok "inside the night sweeps' window: stop at [2/6]" || { bad "quiet"; echo "$out" | tail -4; }
out="$(run_inst "$R6" REHEARSE_CLOCK=0405 DRY=1)"; echo "$out" | grep -q "DRY RUN: every gate" && ok "04:05 is outside the window" || { bad "0405"; echo "$out" | tail -4; }
R5="$W/down"; mkroot "$R5" 1; touch "$R5/svc_down"
out="$(run_inst "$R5")"; echo "$out" | grep -q "call-pipeline is not active before" && ok "the service down before: stop at [2/6]" || { bad "down"; echo "$out" | tail -4; }
fi
echo "REHEARSAL part $PART: $PASS/$((PASS+FAIL))"; [ "$FAIL" = 0 ]
