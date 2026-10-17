#!/usr/bin/env python3
"""walk_s573.py -- the walk for clinic_doctor.py (kit S573). Runs the real script against a made-up server:
fake systemctl and fake curl that read one state file and record every call. No real service is touched.
    python3 walk_s573.py [path/to/clinic_doctor.py]
Prints one line per check and a count. Exit 0 only if every check is green."""
import json, os, subprocess, sys, tempfile, textwrap

DOC = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "clinic_doctor.py"))
PORTS = {"clinic-portal": 8099, "clinic-finance": 8106, "assetapp": 8030, "staff-register": 8044, "staff-ledger": 8043,
         "attendance-dashboard": 8042, "wa-receiver": 8095, "wa-send-api": 8096, "call-api": 8097, "call-hook": 8098,
         "clinic-followup-receiver": 8100, "wa-approve": 8101, "ring-hook": 8102}
OTHER = ["attlistener", "call-pipeline", "lshttpd", "mariadb", "pdns"]
HOSTS = ["followup.dr-manoj.in", "assets.dr-manoj.in", "drmanojagarwal.com"]

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
        print("active" if d and d["active"] else ("inactive" if d else "unknown")); sys.exit(0 if d and d["active"] else 3)
    if a[0] == "is-enabled":
        print("enabled" if d and d.get("enabled", True) else "disabled"); sys.exit(0)
    if a[0] == "restart":
        if d is None: sys.exit(5)
        d["restarts"] = d.get("restarts", 0) + 1
        if d.get("fix_on_restart", True):
            d["active"] = True; d["code"] = d.get("good", "200")
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
        host = url.split("/")[2]
        web = s["units"]["lshttpd"]["active"]
        ok = web and s.get("front_ok", True) and all(d["active"] and d["code"] not in ("000","502","503","504") for d in s["units"].values() if d.get("port"))
        sys.stdout.write("200" if ok and host not in s.get("front_bad_hosts", []) else ("503" if web else "000")); sys.exit(0)
    sys.stdout.write("000"); sys.exit(7)
    ''')


def base_state():
    u = {n: {"active": True, "code": "200", "port": p} for n, p in PORTS.items()}
    for n in OTHER:
        u[n] = {"active": True, "code": "200"}
    return {"units": u, "front_ok": True}


def run(state, args=(), env_extra=None):
    d = tempfile.mkdtemp(prefix="walk573_")
    stp, calls = os.path.join(d, "state.json"), os.path.join(d, "calls.log")
    json.dump(state, open(stp, "w")); open(calls, "w").close()
    for name, body in (("systemctl", FAKE_SYSTEMCTL), ("curl", FAKE_CURL)):
        p = os.path.join(d, name); open(p, "w").write(body); os.chmod(p, 0o755)
    ring = os.path.join(d, "ring_hook.env"); open(ring, "w").write("RING_HOOK_PORT=8102\n")
    env = dict(os.environ, WALK_STATE=stp, WALK_CALLS=calls, DOCTOR_SYSTEMCTL=os.path.join(d, "systemctl"),
               DOCTOR_CURL=os.path.join(d, "curl"), DOCTOR_LOG=os.path.join(d, "doctor.log"),
               DOCTOR_LOCK=os.path.join(d, "lock"), DOCTOR_RING_ENV=ring, DOCTOR_WAIT="0", DOCTOR_TRIES="2",
               DOCTOR_CLOCK="17-Oct-2026 16:00:00 IST", DOCTOR_DISK_USED="22")
    env.update(env_extra or {})
    p = subprocess.run([sys.executable, "-B", DOC] + list(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    out = p.stdout.decode()
    rest = [l.split()[-1] for l in open(calls) if l.startswith("restart")]
    logl = open(os.path.join(d, "doctor.log")).read() if os.path.exists(os.path.join(d, "doctor.log")) else ""
    return p.returncode, out, rest, logl, d


R = []
def check(name, cond):
    R.append((name, bool(cond))); print(("GREEN " if cond else "RED   ") + name)

# A all good
rc, out, rest, logl, _ = run(base_state())
check("A all good: verdict ALL GOOD, exit 0", rc == 0 and "ALL GOOD." in out)
check("A all good: nothing restarted", rest == [])
check("A all good: one log line with the verdict", logl.count("\n") == 1 and "ALL GOOD" in logl)
# B a stopped service
s = base_state(); s["units"]["clinic-finance"]["active"] = False
rc, out, rest, _, _ = run(s)
check("B finance stopped: restarted once, only it", rest == ["clinic-finance"])
check("B finance stopped: verdict FIXED, exit 0", rc == 0 and "FIXED." in out and "Finance app" in out)
# C running but hung (no reply) -- fixed by restart
s = base_state(); s["units"]["clinic-portal"]["code"] = "000"
rc, out, rest, _, _ = run(s)
check("C portal hung: restarted only the portal", rest == ["clinic-portal"])
check("C portal hung: says 'running but not answering' then FIXED", "running but not answering" in out and "FIXED." in out)
# D hung and the restart does not help
s = base_state(); s["units"]["clinic-portal"]["code"] = "000"; s["units"]["clinic-portal"]["fix_on_restart"] = False
rc, out, rest, logl, _ = run(s)
check("D not fixable: verdict NOT FIXED, exit 1, asks for a photo", rc == 1 and "NOT FIXED." in out and "photo" in out)
check("D not fixable: the portal restarted at most once", rest.count("clinic-portal") == 1)
check("D not fixable: logged NOT FIXED", "NOT FIXED" in logl)
# E backends fine, the web server stuck
s = base_state(); s["front_ok"] = False
rc, out, rest, _, _ = run(s)
check("E web server stuck: only lshttpd restarted", rest == ["lshttpd"])
check("E web server stuck: FIXED, names the web server", rc == 0 and "FIXED." in out and "LiteSpeed" in out)
# F disk full: no restarts, escalate
s = base_state(); s["units"]["clinic-finance"]["active"] = False
rc, out, rest, _, _ = run(s, env_extra={"DOCTOR_DISK_USED": "97"})
check("F disk full: nothing restarted", rest == [])
check("F disk full: NOT FIXED and says the disk is full", rc == 1 and "disk is full" in out and "NOT FIXED." in out)
# G --check: reports, never restarts
s = base_state(); s["units"]["clinic-finance"]["active"] = False; s["front_ok"] = False
rc, out, rest, logl, _ = run(s, ["--check"])
check("G --check: nothing restarted", rest == [])
check("G --check: reports the stopped service, NOT FIXED", "DOWN   Finance app" in out and rc == 1 and "| check |" in logl)
# H an app replying 500 is alive
s = base_state(); s["units"]["wa-approve"]["code"] = "500"; s["units"]["staff-ledger"]["code"] = "308"
rc, out, rest, _, _ = run(s)
check("H a 500 / 308 reply counts as answering: nothing restarted, ALL GOOD", rest == [] and "ALL GOOD." in out)
# I a unit not on the box is skipped; a stopped database is started
s = base_state(); del s["units"]["attendance-dashboard"]; s["units"]["mariadb"]["active"] = False
rc, out, rest, _, _ = run(s)
check("I missing unit skipped (not named)", "Attendance dashboard" not in out)
check("I stopped website database started, FIXED", rest == ["mariadb"] and "FIXED." in out)
# J a 502 from in front of an app means not answering
s = base_state(); s["units"]["call-api"]["code"] = "502"
rc, out, rest, _, _ = run(s)
check("J a 502 counts as not answering: call-api restarted, FIXED", rest == ["call-api"] and "FIXED." in out)
# K a second copy while one runs is refused
import fcntl
s = base_state(); d = tempfile.mkdtemp(prefix="walk573_lock_"); lk = open(os.path.join(d, "lock"), "w"); fcntl.flock(lk, fcntl.LOCK_EX)
rc, out, rest, _, _ = run(s, env_extra={"DOCTOR_LOCK": os.path.join(d, "lock")})
check("K second copy refused (exit 3), nothing restarted", rc == 3 and rest == [] and "already running" in out)
# L the output never prints a secret-shaped thing: no 'key', no token, no topic
rc, out, *_ = run(base_state())
check("L output holds no key/token/password word", not any(w in out.lower() for w in ("token", "password", "secret", "ntfy")))

g = sum(1 for _, ok in R if ok)
print("\nwalk_s573: %d of %d green" % (g, len(R)))
sys.exit(0 if g == len(R) else 1)
