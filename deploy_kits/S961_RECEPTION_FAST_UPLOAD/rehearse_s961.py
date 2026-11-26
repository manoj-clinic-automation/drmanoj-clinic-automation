#!/usr/bin/env python3
"""S961 rehearsal: the guard runs S456.1 (the live bytes); job j48 (its real text, ROOT pointed at a scratch folder) is
dropped into jobs/in and run BY THE RUNNING AGENT; the agent must take its own update and come back as S961.1, .prev =
S456.1. Then a broken .new is refused and S961.1 keeps beating."""
import hashlib, json, os, shutil, subprocess, sys, tempfile, time
FROM, JOB, GUARD = [os.path.abspath(a) for a in sys.argv[1:4]]
R = tempfile.mkdtemp(prefix="r961_"); ok = []
def say(n, c): ok.append(c); print(("ok  " if c else "FAIL"), "", n)
shutil.copy(FROM, os.path.join(R, "reception_agent.py")); shutil.copy(GUARD, os.path.join(R, "agent_guard.py"))
json.dump({"tick_seconds": 1, "beat_seconds": 2, "server_url": "http://127.0.0.1:9"}, open(os.path.join(R, "config.json"), "w"))
env = dict(os.environ, USERPROFILE=R, LOCALAPPDATA=R)
g = subprocess.Popen([sys.executable, "-c", "import sys; sys.path.insert(0, %r); import agent_guard as g; g.POLL=1; sys.exit(g.main())" % R],
                     cwd=R, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
def ver():
    try: return json.load(open(os.path.join(R, "heartbeat.json")))["agent_version"]
    except Exception: return None
def wait(fn, s=60):
    t = time.time()
    while time.time() - t < s:
        if fn(): return True
        time.sleep(0.3)
    return False
md5 = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest() if os.path.exists(p) else "-"
try:
    say("the guard runs S456.1", wait(lambda: ver() == "S456.1"))
    job = open(JOB, encoding="utf-8").read().replace('"C:" + chr(92) + "ClinicAgent"', repr(R))
    open(os.path.join(R, "jobs", "in", "j48_rehearse.py"), "w", encoding="utf-8").write(job)
    say("the running agent runs j48 and comes back as S961.1", wait(lambda: ver() == "S961.1", 90))
    say("reception_agent.py is the kit's bytes; .prev is S456.1; no .new left",
        md5(os.path.join(R, "reception_agent.py")) == "5896d665e6ed7a9fc4bcb343ab8301e0"
        and md5(os.path.join(R, "reception_agent.py.prev")) == "d3d4b67bdb1c3a356037b9cce9a30a0d"
        and not os.path.exists(os.path.join(R, "reception_agent.py.new")))
    say("the update is confirmed (marker gone)", wait(lambda: not os.path.exists(os.path.join(R, "update_pending.json")), 20))
    outs = os.listdir(os.path.join(R, "jobs", "out"))
    txt = "".join(open(os.path.join(R, "jobs", "out", n), encoding="utf-8", errors="replace").read() for n in outs)
    say("the job's result says it wrote the new file", "reception_agent.py.new written" in txt)
    open(os.path.join(R, "reception_agent.py.new"), "w").write("this is not python (\n")
    time.sleep(6)
    say("a broken update is refused and S961.1 keeps beating",
        os.path.exists(os.path.join(R, "reception_agent.py.rejected")) and wait(lambda: ver() == "S961.1")
        and md5(os.path.join(R, "reception_agent.py")) == "5896d665e6ed7a9fc4bcb343ab8301e0")
    log = open(os.path.join(R, "agent.log"), encoding="utf-8").read()
    say("agent.log: no crash, no FAILED from the fast lane", "CRASHED" not in log and "fast upload FAILED" not in log)
finally:
    g.kill()
print("\n%d passed, %d failed" % (sum(ok), len(ok) - sum(ok))); sys.exit(0 if all(ok) else 1)
