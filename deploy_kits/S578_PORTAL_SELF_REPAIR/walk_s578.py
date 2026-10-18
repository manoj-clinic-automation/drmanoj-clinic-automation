#!/usr/bin/env python3
"""walk_s578.py -- the walk for clinic_doctor.py 2.0 (kit S578). Runs the real script against a made-up server:
a fake systemctl and a fake curl that read one state file and record every call. No real service is touched,
and every file the script writes (log, lock, state, status, phone lines) goes to a temporary folder.
    python3 walk_s578.py [path/to/clinic_doctor.py]
Part 1 is S573's 22 checks (the manual run is unchanged); part 2 is the automatic run (--auto).
Prints one line per check and a count. Exit 0 only if every check is green."""
import fcntl, json, os, subprocess, sys, tempfile, textwrap, time

DOC = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "clinic_doctor.py"))
PORTS = {"clinic-portal": 8099, "clinic-finance": 8106, "assetapp": 8030, "staff-register": 8044, "staff-ledger": 8043,
         "attendance-dashboard": 8042, "wa-receiver": 8095, "wa-send-api": 8096, "call-api": 8097, "call-hook": 8098,
         "clinic-followup-receiver": 8100, "wa-approve": 8101, "ring-hook": 8102}
OTHER = ["attlistener", "call-pipeline", "lshttpd", "mariadb", "pdns"]
T0 = 1792300000            # a fixed clock for the hour rules (18-Oct-2026, made up)
SECRET = "walkTopicXq7"    # stands in for the phone address; must never be printed or logged

FAKE_SYSTEMCTL = textwrap.dedent('''\
    #!/usr/bin/env python3
    import json, os, sys
    st = os.environ["WALK_STATE"]; s = json.load(open(st))
    open(os.environ["WALK_CALLS"], "a").write(" ".join(sys.argv[1:]) + "\\n")
    a = sys.argv[1:]
    if a[0] == "show":
        u = a[-1]; print("loaded" if u in s["units"] else "not-found"); sys.exit(0)
    u = a[-1]; d = s["units"].get(u)
    if a[0] == "is-active":
        if d and d.get("state"): print(d["state"]); sys.exit(3)
        print("active" if d and d["active"] else ("inactive" if d else "unknown")); sys.exit(0 if d and d["active"] else 3)
    if a[0] == "is-enabled":
        print("enabled" if d and d.get("enabled", True) else "disabled"); sys.exit(0)
    if a[0] == "restart":
        if d is None: sys.exit(5)
        d["restarts"] = d.get("restarts", 0) + 1
        if d.get("fix_on_restart", True):
            d["active"] = True; d["code"] = d.get("good", "200"); d.pop("state", None)
            if u == "lshttpd": s["front_ok"] = True
        json.dump(s, open(st, "w")); sys.exit(0)
    sys.exit(0)
    ''')
FAKE_CURL = textwrap.dedent('''\
    #!/usr/bin/env python3
    import json, os, sys
    s = json.load(open(os.environ["WALK_STATE"])); a = sys.argv[1:]
    open(os.environ["WALK_CALLS"], "a").write("curl " + a[-1] + "\\n")
    url = a[-1]
    if url.startswith("http://127.0.0.1:"):
        port = int(url.split(":")[2].split("/")[0])
        for u, d in s["units"].items():
            if d.get("port") == port:
                sys.stdout.write(d["code"] if d["active"] else "000"); sys.exit(0)
        sys.stdout.write("000"); sys.exit(7)
    if "--resolve" in a:
        host = url.split("/")[2]; path = "/" + "/".join(url.split("/")[3:])
        web = s["units"]["lshttpd"]["active"]
        behind = {"/finance/healthz": "clinic-finance", "/portal/login": "clinic-portal", "/register/login": "staff-register"}.get(path)
        if host == "assets.dr-manoj.in": behind = "assetapp"
        b = s["units"].get(behind) if behind else None
        app_ok = b is None or (b["active"] and b["code"] not in ("000", "502", "503", "504"))
        ok = web and s.get("front_ok", True) and app_ok
        sys.stdout.write("200" if ok and host not in s.get("front_bad_hosts", []) else ("503" if web else "000")); sys.exit(0)
    sys.stdout.write("000"); sys.exit(7)
    ''')


def base_state():
    u = {n: {"active": True, "code": "200", "port": p} for n, p in PORTS.items()}
    for n in OTHER:
        u[n] = {"active": True, "code": "200"}
    return {"units": u, "front_ok": True}


def make_dir():
    d = tempfile.mkdtemp(prefix="walk578_")
    for name, body in (("systemctl", FAKE_SYSTEMCTL), ("curl", FAKE_CURL)):
        p = os.path.join(d, name); open(p, "w").write(body); os.chmod(p, 0o755)
    open(os.path.join(d, "ring_hook.env"), "w").write("RING_HOOK_PORT=8102\n")
    open(os.path.join(d, "alert.env"), "w").write("WATCHDOG_NTFY_URL=https://push.invalid/%s\n" % SECRET)
    return d


def run(state, args=(), env_extra=None, d=None, doctor_state=None):
    d = d or make_dir()
    stp, calls = os.path.join(d, "state.json"), os.path.join(d, "calls.log")
    json.dump(state, open(stp, "w")); open(calls, "w").close()
    pushes = os.path.join(d, "pushes.log")
    if os.path.exists(pushes):
        os.remove(pushes)
    if doctor_state is not None:
        json.dump(doctor_state, open(os.path.join(d, "doctor_state.json"), "w"))
    env = dict(os.environ, WALK_STATE=stp, WALK_CALLS=calls, DOCTOR_SYSTEMCTL=os.path.join(d, "systemctl"),
               DOCTOR_CURL=os.path.join(d, "curl"), DOCTOR_LOG=os.path.join(d, "doctor.log"),
               DOCTOR_LOCK=os.path.join(d, "lock"), DOCTOR_RING_ENV=os.path.join(d, "ring_hook.env"),
               DOCTOR_WAIT="0", DOCTOR_TRIES="2", DOCTOR_CLOCK="18-Oct-2026 16:00:00 IST", DOCTOR_DISK_USED="22",
               DOCTOR_STATE=os.path.join(d, "doctor_state.json"), DOCTOR_STATUS=os.path.join(d, "status.json"),
               DOCTOR_AUTO_OFF=os.path.join(d, "_off", "DOCTOR_AUTO_OFF"),
               DOCTOR_BUILD_LOCK=os.path.join(d, "build.lock"), DOCTOR_ALERT_ENV=os.path.join(d, "alert.env"),
               DOCTOR_PUSH_LOG=pushes, DOCTOR_EPOCH=str(T0), DOCTOR_UPTIME="86400", TZ="Asia/Kolkata")
    env.update(env_extra or {})
    env = {k: v for k, v in env.items() if v is not None}
    p = subprocess.run([sys.executable, "-B", DOC] + list(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    out = p.stdout.decode()
    allcalls = open(calls).read().splitlines()
    rest = [l.split()[-1] for l in allcalls if l.startswith("restart")]
    lp = os.path.join(d, "doctor.log")
    logl = open(lp).read() if os.path.exists(lp) else ""
    ph = [json.loads(l) for l in open(pushes)] if os.path.exists(pushes) else []
    sp = os.path.join(d, "status.json")
    status = json.load(open(sp)) if os.path.exists(sp) else {}
    return {"rc": p.returncode, "out": out, "rest": rest, "log": logl, "d": d, "push": ph, "status": status,
            "calls": allcalls}


def load_state(r):
    try:
        return json.load(open(os.path.join(r["d"], "doctor_state.json")))
    except (OSError, ValueError):
        return {}


R = []
def check(name, cond):
    R.append((name, bool(cond))); print(("GREEN " if cond else "RED   ") + name)


# ---------------------------------------------------------------- part 1: S573's 22 checks, the manual run unchanged
r = run(base_state())
check("A all good: verdict ALL GOOD, exit 0", r["rc"] == 0 and "ALL GOOD." in r["out"])
check("A all good: nothing restarted", r["rest"] == [])
check("A all good: one log line with the verdict", r["log"].count("\n") == 1 and "ALL GOOD" in r["log"])
s = base_state(); s["units"]["clinic-finance"]["active"] = False
r = run(s)
check("B finance stopped: restarted once, only it", r["rest"] == ["clinic-finance"])
check("B finance stopped: verdict FIXED, exit 0", r["rc"] == 0 and "FIXED." in r["out"] and "Finance app" in r["out"])
s = base_state(); s["units"]["clinic-portal"]["code"] = "000"
r = run(s)
check("C portal hung: restarted only the portal", r["rest"] == ["clinic-portal"])
check("C portal hung: says 'running but not answering' then FIXED", "running but not answering" in r["out"] and "FIXED." in r["out"])
s = base_state(); s["units"]["clinic-portal"]["code"] = "000"; s["units"]["clinic-portal"]["fix_on_restart"] = False
r = run(s)
check("D not fixable: verdict NOT FIXED, exit 1, asks for a photo", r["rc"] == 1 and "NOT FIXED." in r["out"] and "photo" in r["out"])
check("D not fixable: the portal restarted at most once", r["rest"].count("clinic-portal") == 1)
check("D not fixable: logged NOT FIXED", "NOT FIXED" in r["log"])
check("D2 (S578) the web server is NOT restarted when the fault is a part behind it", "lshttpd" not in r["rest"]
      and "not restarted: a part behind it" in r["out"])
s = base_state(); s["front_ok"] = False
r = run(s)
check("E web server stuck: only lshttpd restarted", r["rest"] == ["lshttpd"])
check("E web server stuck: FIXED, names the web server", r["rc"] == 0 and "FIXED." in r["out"] and "LiteSpeed" in r["out"])
s = base_state(); s["units"]["clinic-finance"]["active"] = False
r = run(s, env_extra={"DOCTOR_DISK_USED": "97"})
check("F disk full: nothing restarted", r["rest"] == [])
check("F disk full: NOT FIXED and says the disk is full", r["rc"] == 1 and "disk is full" in r["out"] and "NOT FIXED." in r["out"])
s = base_state(); s["units"]["clinic-finance"]["active"] = False; s["front_ok"] = False
r = run(s, ["--check"])
check("G --check: nothing restarted", r["rest"] == [])
check("G --check: reports the stopped service, NOT FIXED", "DOWN   Finance app" in r["out"] and r["rc"] == 1 and "| check |" in r["log"])
s = base_state(); s["units"]["wa-approve"]["code"] = "500"; s["units"]["staff-ledger"]["code"] = "308"
r = run(s)
check("H a 500 / 308 reply counts as answering: nothing restarted, ALL GOOD", r["rest"] == [] and "ALL GOOD." in r["out"])
s = base_state(); del s["units"]["attendance-dashboard"]; s["units"]["mariadb"]["active"] = False
r = run(s)
check("I missing unit skipped (not named)", "Attendance dashboard" not in r["out"])
check("I stopped website database started, FIXED", r["rest"] == ["mariadb"] and "FIXED." in r["out"])
s = base_state(); s["units"]["call-api"]["code"] = "502"
r = run(s)
check("J a 502 counts as not answering: call-api restarted, FIXED", r["rest"] == ["call-api"] and "FIXED." in r["out"])
d = make_dir(); lk = open(os.path.join(d, "lock"), "w"); fcntl.flock(lk, fcntl.LOCK_EX)
r = run(base_state(), d=d)
check("K second copy refused (exit 3), nothing restarted", r["rc"] == 3 and r["rest"] == [] and "already running" in r["out"])
lk.close()
r = run(base_state())
check("L output holds no key/token/password word", not any(w in r["out"].lower() for w in ("token", "password", "secret", "ntfy")))

# ---------------------------------------------------------------- part 2: the automatic run (S578, D734)
A = ["--auto"]
r = run(base_state(), A)
check("M auto all good: exit 0, nothing restarted, nothing printed, no log line, no phone line",
      r["rc"] == 0 and r["rest"] == [] and r["out"].strip() == "" and r["log"] == "" and r["push"] == [])
check("M auto all good: the status file says ALL GOOD (mode auto)", r["status"].get("verdict") == "ALL GOOD" and r["status"].get("mode") == "auto")

s = base_state(); s["units"]["clinic-finance"]["active"] = False
r = run(s, A)
check("N auto stopped part: restarted once, only it, FIXED", r["rest"] == ["clinic-finance"] and r["rc"] == 0)
check("N auto stopped part: ONE phone line 'repaired itself', ordinary priority, names it",
      len(r["push"]) == 1 and "repaired itself" in r["push"][0]["title"] and r["push"][0]["priority"] == "default"
      and "Finance app" in r["push"][0]["body"])
check("N auto stopped part: one log line '| auto | FIXED'", "| auto | FIXED" in r["log"] and r["log"].count("\n") == 1)
st = load_state(r)
check("N auto: the restart time is remembered", int(st.get("restarted", {}).get("clinic-finance", 0)) == T0)

s = base_state(); s["units"]["clinic-finance"]["active"] = False
r = run(s, A, doctor_state={"restarted": {"clinic-finance": T0 - 600}})
check("O auto, restarted 10 min ago and down again: NOT restarted (once an hour)", r["rest"] == [] and r["rc"] == 1)
check("O auto: phone line 'could NOT repair itself', high, says it waits, points to step 3",
      len(r["push"]) == 1 and "could NOT" in r["push"][0]["title"] and r["push"][0]["priority"] == "high"
      and "within the hour" in r["push"][0]["body"] and r["push"][0]["click"].endswith("#s3"))

s = base_state(); s["units"]["clinic-finance"]["active"] = False
r = run(s, A, doctor_state={"restarted": {"clinic-finance": T0 - 7200}})
check("P auto, last restart 2 hours ago: restarted again", r["rest"] == ["clinic-finance"])

s = base_state(); s["units"]["clinic-portal"]["code"] = "000"; s["units"]["clinic-portal"]["fix_on_restart"] = False
r1 = run(s, A)
check("Q auto not fixable: one restart, one high phone line", r1["rest"] == ["clinic-portal"] and len(r1["push"]) == 1
      and r1["push"][0]["priority"] == "high")
r2 = run(s, A, d=r1["d"], env_extra={"DOCTOR_EPOCH": str(T0 + 300)})
check("Q next run 5 min later, same fault: no restart, NO second phone line", r2["rest"] == [] and r2["push"] == [])
r3 = run(s, A, d=r1["d"], env_extra={"DOCTOR_EPOCH": str(T0 + 3700)})
check("Q an hour later, still the same: one more restart and one reminder", r3["rest"] == ["clinic-portal"] and len(r3["push"]) == 1)
r4 = run(base_state(), A, d=r1["d"], env_extra={"DOCTOR_EPOCH": str(T0 + 4000)})
check("R it comes back: one 'fine again' line", len(r4["push"]) == 1 and "fine again" in r4["push"][0]["title"])
r5 = run(base_state(), A, d=r1["d"], env_extra={"DOCTOR_EPOCH": str(T0 + 4300)})
check("R the next good run: no line", r5["push"] == [] and r5["log"].count("\n") == r4["log"].count("\n"))

s = base_state(); s["units"]["call-api"]["active"] = False; s["units"]["call-api"]["enabled"] = False
r = run(s, A)
check("S auto: a part stopped AND disabled on purpose is left alone, ALL GOOD, no line",
      r["rest"] == [] and r["status"].get("verdict") == "ALL GOOD" and r["push"] == [])
r = run(s)
check("S the manual run still restarts it (the owner asked)", r["rest"] == ["call-api"])

s = base_state(); s["units"]["staff-ledger"]["active"] = False; s["units"]["staff-ledger"]["state"] = "activating"
r = run(s, A)
check("T auto: a part still starting up is not restarted", r["rest"] == [])

s = base_state(); s["front_bad_hosts"] = ["drmanojagarwal.com"]
r = run(s, A)
check("U auto: only the website fails -> the web server is NOT restarted, no phone line",
      r["rest"] == [] and r["push"] == [] and r["status"].get("verdict") == "ALL GOOD")
check("U auto: the website note is logged", "website did not answer" in r["log"])
s = base_state(); s["front_bad_hosts"] = ["followup.dr-manoj.in", "drmanojagarwal.com"]
r = run(s, A)
check("U2 auto: a clinic address fails -> the web server IS restarted", r["rest"] == ["lshttpd"])
s = base_state(); s["front_ok"] = False
r = run(s, A, doctor_state={"restarted": {"lshttpd": T0 - 900}})
check("U3 auto: web server restarted 15 min ago -> not again, NOT FIXED line", r["rest"] == [] and r["rc"] == 1 and len(r["push"]) == 1)

d = make_dir(); os.makedirs(os.path.join(d, "_off")); open(os.path.join(d, "_off", "DOCTOR_AUTO_OFF"), "w").close()
s = base_state(); s["units"]["clinic-finance"]["active"] = False
r = run(s, A, d=d)
check("V auto switched off by the file: exit 0, not one systemctl call, no line", r["rc"] == 0 and r["calls"] == [] and r["push"] == [])
r = run(s, d=d)
check("V the switch does not stop the owner's manual run", r["rest"] == ["clinic-finance"])

d = make_dir(); os.makedirs(os.path.join(d, "build.lock"))
r = run(s, A, d=d, env_extra={"DOCTOR_EPOCH": str(time.time())})
check("W auto while an install holds the build lock: nothing touched", r["calls"] == [] and r["rc"] == 0)
os.utime(os.path.join(d, "build.lock"), (time.time() - 7200, time.time() - 7200))
r = run(s, A, d=d, env_extra={"DOCTOR_EPOCH": str(time.time())})
check("W a build lock 2 hours old is stale: the repair runs", r["rest"] == ["clinic-finance"])

r = run(s, A, env_extra={"DOCTOR_UPTIME": "100"})
check("X auto in the first 5 minutes after boot: nothing touched", r["calls"] == [] and r["rc"] == 0)

d = make_dir(); lk = open(os.path.join(d, "lock"), "w"); fcntl.flock(lk, fcntl.LOCK_EX)
r = run(s, A, d=d)
check("Y auto while the owner runs it by hand: exit 3, silent, nothing restarted", r["rc"] == 3 and r["out"] == "" and r["rest"] == [])
lk.close()

s = base_state(); s["units"]["clinic-portal"]["active"] = False
r = run(s, A, doctor_state={"restarted": {}})
check("Z auto output is silent even when it repairs", r["out"].strip() == "")
r = run(s, A, env_extra={"DOCTOR_PUSH_LOG": None})
check("Z a phone line that cannot be sent is logged as NOT SENT, and the address is never printed or logged",
      "NOT SENT" in r["log"] and SECRET not in r["log"] and SECRET not in r["out"])

s = base_state(); s["units"]["clinic-finance"]["active"] = False
r = run(s, doctor_state={"restarted": {"clinic-finance": T0 - 60}})
check("AA the manual run is never held by the hour rule", r["rest"] == ["clinic-finance"])
st = load_state(r)
check("AB the manual run's restart is remembered, so the automatic run respects it",
      int(st.get("restarted", {}).get("clinic-finance", 0)) == T0)
check("AC no phone line from a manual run", r["push"] == [])

g = sum(1 for _, ok in R if ok)
print("\nwalk_s578: %d of %d green" % (g, len(R)))
sys.exit(0 if g == len(R) else 1)
