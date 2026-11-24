#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
walk_s946.py <kitdir> <workdir> [--control]  -- S946's walk on a MADE-UP root. No live file, no network, no patient data
(every join key is assembled at run time). --control runs it against the FROM files (WORKER_FROM / LEGS_FROM env) -- must go red.
  A  the runner: its selftest; then against the REAL watchdog (the kit's from/ copy) with a made-up web log:
     a Sunday of accepted deliveries -> OK; a Monday with no raw log -> CRITICAL; a glob that matches nothing -> ERROR.
  B  the patched worker: --selftest; --once on a made-up recordings folder with three stand-in stages -> the state file says
     complete; a failing stage -> INCOMPLETE with last_success kept; runs_today counts; the lock busy -> no state written.
  C  the clean-up on CSV stand-ins of the two tabs: backup 0600; debris found by the rule (a FAILED row with no done row stays;
     a done row never moves); --dry writes nothing; live removes exactly the debris, marks the July calls once, re-reads green;
     a second run finds nothing; a tab with no Join Key column stops.
  D  the two legs files: parse, the counts, kinds known, names unique, the new legs' fields.
"""
import csv
import json
import os
import shutil
import subprocess
import sys
import time

KIT = os.path.abspath(sys.argv[1])
WORK = os.path.abspath(sys.argv[2])
CONTROL = "--control" in sys.argv
PY = sys.executable
passed = failed = 0


def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print("  FAIL:", name)


def run(cmd, env=None, cwd=None, inp=None):
    e = dict(os.environ)
    e.update(env or {})
    e["TZ"] = "Asia/Kolkata"
    r = subprocess.run(cmd, capture_output=True, text=True, env=e, cwd=cwd or WORK, input=inp, timeout=300)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


shutil.rmtree(WORK, ignore_errors=True)
os.makedirs(WORK)

WORKER = os.environ.get("WORKER_FROM") if CONTROL and os.environ.get("WORKER_FROM") else os.path.join(KIT, "call_pipeline_worker.py")
LEGS_A = os.environ.get("LEGS_FROM") if CONTROL and os.environ.get("LEGS_FROM") else os.path.join(KIT, "freshness_legs_a.json")
LEGS_B = os.environ.get("LEGS_FROM") if CONTROL and os.environ.get("LEGS_FROM") else os.path.join(KIT, "freshness_legs_b.json")
RUNNER = os.path.join(KIT, "callhook_watch_run.py")
CLEAN = os.path.join(KIT, "s946_verdict_cleanup.py")
WATCHDOG = os.path.join(KIT, "from", "callhook_watchdog.py")

# ---------------------------------------------------------------- A  the runner
rc, out = run([PY, "-B", RUNNER, "--selftest"])
check("A1 runner selftest 15/15", rc == 0 and "SELFTEST 15/15" in out)
hook = os.path.join(WORK, "hook")
os.makedirs(os.path.join(hook, "logs"))
os.makedirs(os.path.join(hook, "raw"))
logp = os.path.join(hook, "logs", "site.access_log")
with open(logp, "w") as f:
    for i in range(5):
        f.write('1.2.3.4 - - [22/Nov/2026:10:%02d:00 +0530] "POST /mo-callhook?key=madeupkey HTTP/1.1" 200 20 "-" "Go"\n' % (10 + i))
    f.write('1.2.3.4 - - [23/Nov/2026:09:05:00 +0530] "POST /mo-callhook?key=madeupkey HTTP/1.1" 200 20 "-" "Go"\n')
env = {"WATCH_RUN_WATCHDOG": WATCHDOG, "WATCH_RUN_PYTHON": PY,
       "WATCH_RUN_STATE": os.path.join(hook, "state.json"), "WATCH_RUN_WD_STATE": os.path.join(hook, "wd.json")}
rawd = os.path.join(hook, "raw")                    # the walk's own raw-log folder, never the box's
rc, out = run([PY, "-B", RUNNER, "--access-glob", os.path.join(hook, "logs", "*access*"), "--date", "2026-11-22", "--raw-log-dir", rawd], env)
st = json.load(open(env["WATCH_RUN_STATE"]))
check("A2 a Sunday of accepted deliveries -> OK (real watchdog)", rc == 0 and st["severity"] == "OK" and st["accepted_200"] == 5)
check("A3 no key in the state", "madeupkey" not in json.dumps(st) and "madeupkey" not in out)
good = st["last_success_iso"]
time.sleep(1.1)                             # a later second, as a later day would be
rc, out = run([PY, "-B", RUNNER, "--access-glob", os.path.join(hook, "logs", "*access*"), "--date", "2026-11-23", "--raw-log-dir", rawd], env)
st = json.load(open(env["WATCH_RUN_STATE"]))
check("A4 a clinic day with no raw log -> CRITICAL, exit 2", rc == 2 and st["severity"] == "CRITICAL" and "CALLHOOK_RAWLOG_MISSING" in st["findings"])
check("A5 last_success kept, last_fail set", st["last_success_iso"] == good and st["last_fail_iso"] == st["last_run_iso"])
rc, out = run([PY, "-B", RUNNER, "--access-glob", os.path.join(hook, "nowhere", "*"), "--raw-log-dir", rawd], env)
st = json.load(open(env["WATCH_RUN_STATE"]))
check("A6 a glob matching nothing -> ERROR, exit 3", rc == 3 and st["severity"] == "ERROR" and "no access log" in st["error"])
rc, out = run([PY, "-B", RUNNER, "--check"], env)
check("A7 --check says the state in one line", rc == 1 and out.startswith("WATCH STATE ERROR"))

# ---------------------------------------------------------------- B  the worker
rc, out = run([PY, "-B", WORKER, "--selftest"])
check("B1 worker selftest passes", rc == 0 and "SELFTEST: 14/14 PASS" in out)
ra = os.path.join(WORK, "ra")
q = os.path.join(ra, "pipeline_queue")
os.makedirs(q)
for name in ("call_recording_archive.py", "call_transcription.py", "call_verdict.py"):
    with open(os.path.join(ra, name), "w") as f:
        f.write("import os, sys, time\nprint('stand-in', sys.argv[-1])\ntime.sleep(0.2)\n"
                "sys.exit(1 if os.environ.get('FAIL_STAGE') == %r else 0)\n" % name)
wenv = {"PIPELINE_RA_DIR": ra, "PIPELINE_PYTHON": PY, "CALLHOOK_QUEUE_DIR": q}
statep = os.path.join(ra, "pipeline_state.json")


def kick():
    with open(os.path.join(q, "k%d.kick" % int(time.time() * 1000)), "w") as f:
        json.dump({"due": 0}, f)


kick()
rc, out = run([PY, "-B", WORKER, "--once"], wenv)
check("B2 --once ran the three stand-ins", rc == 0 and "run complete" in out and "--once: ran" in out)
ok_state = os.path.exists(statep)
check("B3 the state file written after a complete run", ok_state)
st = json.load(open(statep)) if ok_state else {}
check("B4 complete: last_success = last_run, no fail, kicks 1, seconds > 0",
      st.get("last_result") == "complete" and st.get("last_success_iso") == st.get("last_run_iso") and st.get("last_fail_iso") == ""
      and st.get("kicks") == 1 and st.get("fresh") == 1 and st.get("seconds", 0) > 0 and st.get("runs_today") == 1)
check("B5 the state file is owner-only", ok_state and (os.stat(statep).st_mode & 0o777) == 0o600)
good = st.get("last_success_iso")
for p in os.listdir(q):            # drop the retry kick the run scheduled, keep the test deterministic
    os.remove(os.path.join(q, p))
kick()
wenv2 = dict(wenv, FAIL_STAGE="call_transcription.py")
rc, out = run([PY, "-B", WORKER, "--once"], wenv2)
st = json.load(open(statep)) if os.path.exists(statep) else {}
check("B6 a failing stage -> run INCOMPLETE, chain stopped at transcribe", "INCOMPLETE" in out and "chain stopped at transcribe" in out)
check("B7 INCOMPLETE: last_fail = last_run, last_success kept, runs_today 2",
      st.get("last_result") == "INCOMPLETE" and st.get("last_fail_iso") == st.get("last_run_iso") and st.get("last_success_iso") == good
      and st.get("runs_today") == 2)
# the lock busy: the state must not move
for p in os.listdir(q):
    os.remove(os.path.join(q, p))
kick()
before = open(statep).read() if os.path.exists(statep) else ""
rc, out = run(["bash", "-c", "exec 9>'%s'; flock -n 9; '%s' -B '%s' --once" % (os.path.join(ra, "pipeline.lock"), PY, WORKER)], wenv)
after = open(statep).read() if os.path.exists(statep) else ""
check("B8 lock busy -> kicks wait, state untouched", "pipeline busy" in out and before == after)
# a broken state file never stops a run
with open(statep, "w") as f:
    f.write("not json")
for p in os.listdir(q):
    os.remove(os.path.join(q, p))
kick()
rc, out = run([PY, "-B", WORKER, "--once"], wenv)
try:
    st = json.load(open(statep))
except Exception:
    st = {}
check("B9 a corrupt state file is rewritten by the next run", "run complete" in out and st.get("last_result") == "complete" and st.get("runs_today") == 1)
check("B10 nothing else of the worker changed: the quiet window, the retry, the stages untouched",
      all(s in open(WORKER).read() for s in ('QUIET_START = (1, 55)', 'RETRY_DELAY_SECONDS = 600', '("verdict", "call_verdict.py")')))

# ---------------------------------------------------------------- C  the clean-up
VH = ["Date", "Time", "Direction", "Patient Number", "Agent", "Patient Name", "Clinic ID", "Duration",
      "Claimed Outcome", "AI Outcome", "Verdict", "Match Confidence", "Outcome TRUE/FALSE", "AI Reason", "Evidence",
      "Spoke With", "Confidence", "Flag PostOp", "Flag Complaint", "Flag Urgent", "Flag Surgery", "Flag Clinical",
      "Flag Conduct", "Conduct Note", "Recording Link", "Transcript Link", "Join Key", "Status", "Error", "Judged At",
      "Prompt Ver", "Model", "Doctor Flag", "Doctor Note", "Final Outcome"]
TH = ["Date", "Time", "Direction", "Duration", "Join Key", "Status", "Transcript Drive Link", "Transcript Drive File ID"]


def jk(i, ts):
    return "".join(["9", "0", "0", "0", "0", "0", "0"]) + "%03d" % i + "_" + str(ts)     # assembled, never a literal


def vrow(date, key, status, verdict="Match"):
    r = [""] * len(VH)
    r[VH.index("Date")] = date
    r[VH.index("Join Key")] = key
    r[VH.index("Status")] = status
    r[VH.index("Verdict")] = verdict if status == "done" else ""
    r[VH.index("Error")] = "" if status == "done" else "API 400: bad request"
    return r


def trow(date, key, status="done", link="https://drive.example/t"):
    r = [""] * len(TH)
    r[0], r[1], r[2], r[3], r[4], r[5], r[6] = date, "10:00", "incoming", "61", key, status, link
    return r


fake = os.path.join(WORK, "tabs")
os.makedirs(fake)
V = [VH]
T = [TH]
# 3 August calls, each with 2 FAILED rows then a done row (debris 6)
for i in range(3):
    k = jk(i, 1754000000 + i)
    V += [vrow("2026-08-1%d" % i, k, "FAILED"), vrow("2026-08-1%d" % i, k, "FAILED"), vrow("2026-08-1%d" % i, k, "done")]
    T.append(trow("2026-08-1%d" % i, k))
# 1 September call: FAILED only (no done row) -> kept
k_keep = jk(9, 1756000000)
V.append(vrow("2026-09-02", k_keep, "FAILED"))
T.append(trow("2026-09-02", k_keep))
# 1 October done row with a FAILED row AFTER it (debris 1 -- order must not matter)
k_oct = jk(10, 1759000000)
V += [vrow("2026-10-05", k_oct, "done"), vrow("2026-10-05", k_oct, "FAILED")]
T.append(trow("2026-10-05", k_oct))
# July: 4 transcribed calls with no verdict row (one listed twice in the transcripts), 1 July call already judged, 1 July not done
july_keys = [jk(20 + i, 1752000000 + i) for i in range(4)]
for i, k in enumerate(july_keys):
    T.append(trow("2026-07-1%d" % i, k))
T.append(trow("2026-07-10", july_keys[0]))                       # a duplicate transcript line
k_jdone = jk(30, 1752500000)
V.append(vrow("2026-07-20", k_jdone, "done"))
T.append(trow("2026-07-20", k_jdone))
T.append(trow("2026-07-21", jk(31, 1752600000), status="FAILED"))
# a row with an empty join key and no status (a stray line) -> neither debris nor done; stays
V.append(vrow("2026-08-30", "", ""))
with open(os.path.join(fake, "Call_Verdicts.csv"), "w", newline="") as f:
    csv.writer(f).writerows(V)
with open(os.path.join(fake, "Call_Transcripts.csv"), "w", newline="") as f:
    csv.writer(f).writerows(T)
n_before = len(V) - 1                       # 15 rows
bdir = os.path.join(WORK, "backup")
rc, out = run([PY, "-B", CLEAN, "--dry", "--fake", fake, "--backup-dir", bdir])
check("C1 --dry: counts right (debris 7 = Aug 6 + Oct 1, kept 2 = the Sept FAILED + the stray, July 4)",
      rc == 0 and "debris 7 [2026-08 6, 2026-10 1]" in out and "failed kept (no done row) 2" in out and "July calls to mark 4" in out)
check("C2 --dry wrote nothing", len(list(csv.reader(open(os.path.join(fake, "Call_Verdicts.csv"))))) - 1 == n_before and "DRY: nothing written" in out)
baks = os.listdir(bdir) if os.path.isdir(bdir) else []
check("C3 backup written, dir 0700, file 0600, rows = the tab's",
      len(baks) == 1 and (os.stat(bdir).st_mode & 0o777) == 0o700 and (os.stat(os.path.join(bdir, baks[0])).st_mode & 0o777) == 0o600
      and len(list(csv.reader(open(os.path.join(bdir, baks[0]))))) == n_before + 1)
time.sleep(1.1)                             # a second backup needs a new stamp
rc, out = run([PY, "-B", CLEAN, "--fake", fake, "--backup-dir", bdir])
V2 = list(csv.reader(open(os.path.join(fake, "Call_Verdicts.csv"))))
check("C4 live: CLEANUP OK removed 7, marked 4; rows = before - 7 + 4", rc == 0 and "CLEANUP OK: removed 7, marked 4" in out and len(V2) - 1 == n_before - 7 + 4)
sti, jki, vi, ei, di = VH.index("Status"), VH.index("Join Key"), VH.index("Verdict"), VH.index("Error"), VH.index("Date")
rows2 = V2[1:]
check("C5 every done row still there (5 originals), the kept FAILED row there, the stray row there",
      sum(1 for r in rows2 if r[sti] == "done" and r[vi] == "Match") == 5 and any(r[jki] == k_keep and r[sti] == "FAILED" for r in rows2)
      and any(r[jki] == "" and r[sti] == "" for r in rows2))
marks = [r for r in rows2 if r[vi] == "Not judgeable"]
check("C6 the 4 July calls marked once each: done, 'before the stage (S946)', the date and key carried, nothing else",
      len(marks) == 4 and set(r[jki] for r in marks) == set(july_keys) and all(r[sti] == "done" and r[ei] == "before the stage (S946)"
      and r[di].startswith("2026-07") and r[VH.index("Judged At")] and len(r) == len(VH) for r in marks))
check("C7 no debris left: no FAILED row whose key has a done row", not any(r[sti] != "done" and r[jki] and any(d[jki] == r[jki] and d[sti] == "done" for d in rows2) for r in rows2))
time.sleep(1.1)
rc, out = run([PY, "-B", CLEAN, "--fake", fake, "--backup-dir", bdir])
check("C8 a second run finds nothing and changes nothing, and says no July call is left", rc == 0 and "removed 0, marked 0" in out and "WARN: no July call" in out and len(list(csv.reader(open(os.path.join(fake, "Call_Verdicts.csv"))))) == len(V2))
check("C9 no 10-digit run printed by the clean-up", not any(c.isdigit() and len(c) >= 10 for c in out.replace("_", " ").split()))
bad = os.path.join(WORK, "bad")
os.makedirs(bad)
with open(os.path.join(bad, "Call_Verdicts.csv"), "w", newline="") as f:
    csv.writer(f).writerows([["Date", "Status"], ["2026-08-01", "FAILED"]])
shutil.copy(os.path.join(fake, "Call_Transcripts.csv"), bad)
rc, out = run([PY, "-B", CLEAN, "--dry", "--fake", bad, "--backup-dir", os.path.join(WORK, "backup2")])
check("C10 a tab without the Join Key column stops before any backup", rc != 0 and "lacks 'Join Key'" in out and not os.path.isdir(os.path.join(WORK, "backup2")))

# C11/C12  the one-off under the pipeline lock (fake tabs, the lock made real by S946_LOCK_IN_FAKE)
lockdir = os.path.join(WORK, "ra2")
os.makedirs(lockdir, exist_ok=True)
lockp = os.path.join(lockdir, "pipeline.lock")
fake2 = os.path.join(WORK, "tabs2")
shutil.copytree(fake, fake2)
lenv = {"S946_LOCK_IN_FAKE": "1", "S946_RA_DIR": lockdir, "S946_LOCK_WAIT_S": "6"}
rc, out = run(["bash", "-c", "exec 9>'%s'; flock 9; '%s' -B '%s' --dry --fake '%s' --backup-dir '%s'" % (lockp, PY, CLEAN, fake2, os.path.join(WORK, "backup3"))], lenv)
check("C11 the lock held by another process: the one-off waits, then stops before any read or backup",
      rc != 0 and "held its lock for" in out and "waiting for its lock" in out and not os.path.isdir(os.path.join(WORK, "backup3")))
rc, out = run(["bash", "-c", "( exec 9>'%s'; flock 9; sleep 2 ) & sleep 0.3; '%s' -B '%s' --dry --fake '%s' --backup-dir '%s'; wait" % (lockp, PY, CLEAN, fake2, os.path.join(WORK, "backup3"))], lenv)
check("C12 the lock freed after 2 s: the one-off waited and went on", rc == 0 and "waiting for its lock" in out and "DRY: nothing written" in out)

# ---------------------------------------------------------------- D  the legs
KINDS = ("state_json", "file_mtime", "glob_newest", "log_mtime", "sqlite_max")
for tag, path, n_want, names_want in (("a", LEGS_A, 44, ("AI judged within 15 min", "call webhook watchdog")),
                                      ("b", LEGS_B, 43, ("AI judged within 15 min",))):
    try:
        d = json.loads(open(path, encoding="utf-8").read())
        legs = d["legs"]
    except Exception:
        d, legs = {}, []
    names = [l.get("name") for l in legs]
    check("D1%s legs file parses with %d legs, names unique, every kind known" % (tag, n_want),
          len(legs) == n_want and len(set(names)) == len(names) and all(l.get("kind") in KINDS for l in legs))
    check("D2%s the new leg(s) there with field, fail_field, target, group" % tag,
          all(any(l.get("name") == w and l.get("field") == "last_success_iso" and l.get("fail_field") == "last_fail_iso"
                  and l.get("target", "").endswith(".json") and l.get("group") == "Console and calls" for l in legs) for w in names_want))
    check("D3%s the earlier 42 legs byte-equal to S943's (only appended)" % tag,
          legs[:42] == json.loads(open(os.path.join(KIT, "from_legs.json"), encoding="utf-8").read())["legs"][:42] and "server record" in names)
    check("D4%s no number, id or key path in the new notes (F-185)" % tag,
          not any(c.isdigit() and len(c) >= 6 for l in legs[42:] for c in (l.get("note", "") + l.get("target", "")).replace("/", " ").split()))

# D5  the real freshness collector (the kit's from/ copy) judges the two state files the walk produced
sys.path.insert(0, os.path.join(KIT, "from"))
try:
    import freshness as fr
    legs = fr.load_legs(LEGS_A, {"STATE_FILE": os.path.join(WORK, "fs.json")})
    byname = {l["name"]: l for l in legs}
    lw = dict(byname["call webhook watchdog"], target=env["WATCH_RUN_STATE"])      # ended on an ERROR run
    lp = dict(byname["AI judged within 15 min"], target=statep)                    # ended on a complete run
    now = time.time()
    rw, rp = fr.check_leg(lw, now), fr.check_leg(lp, now)
    check("D5 freshness judges the watchdog leg STALE (newest run FAILED) and the pipeline leg OK",
          rw["verdict"] == fr.STALE and "newest build FAILED" in rw["age_words"] and rp["verdict"] == fr.OK and rp["age_h"] < 1)
    lq = dict(lp, target=os.path.join(WORK, "absent.json"))
    check("D6 a state file not yet written -> NEVER, not an ERROR", fr.check_leg(lq, now)["verdict"] == fr.NEVER)
except Exception as ex:
    check("D5 freshness import/judge (%s)" % ex, False)

print("WALK %d/%d" % (passed, passed + failed))
sys.exit(0 if failed == 0 else 1)
