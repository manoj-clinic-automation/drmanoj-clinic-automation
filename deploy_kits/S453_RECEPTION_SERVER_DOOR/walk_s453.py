#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s453.py -- kit S453_RECEPTION_SERVER_DOOR. THE REAL finance_app.py (a copy of /root/finance) over a SCRATCH COPY
of finance.db, and THE KIT'S OWN AGENT -- unpacked from deploy_kits/PC_KITS/reception/kit.zip exactly as a PC would get
it -- talking to it over real HTTP. Keys, queue, heartbeat and log all in the scratch folder; the two keys are made here.

  * the relay's five doors by test client: who may put a job in, what is refused and how, that no login is needed and
    none helps, the queue's files and their modes;
  * THE CHAIN: a job is signed with the kit's own signing tool, submitted as the assistant's browser submits it, fetched
    by the kit's agent, verified by it, RUN, its output posted back and read with a signed read -- byte for byte;
  * THE POINT OF THE DESIGN: a job the server accepts but the PC's own key list does not know is REFUSED BY THE PC;
  * the two older doors (heartbeat, Clinic PCs) still answer; the Clinic PCs page serves the new kit.
  The box as it is (S451) must have none of the five doors.

  --new NEW --old OLD   copies of /root/finance: with the kit's files / the box as it is
  --sso PATH            a copy of /root/portal's *.py WITHOUT portal_config.py
  --db PATH             the scratch finance.db; PATH.old is made for the old app
  --kits PATH           deploy_kits/PC_KITS
"""
import argparse
import os
import sqlite3
import subprocess
import sys

ap = argparse.ArgumentParser()
for k in ("--new", "--old", "--sso", "--db", "--kits"):
    ap.add_argument(k, required=True)
a = ap.parse_args()
assert "walk" in a.db or "scratch" in a.db or a.db.startswith("/tmp"), "refusing a non-scratch database"


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


copydb(a.db, a.db + ".old")

FIN = r'''
import base64, datetime, hashlib, importlib.util, io, json, os, re, stat, subprocess, sys, threading, time, zipfile
APP = os.environ["APPDIR"]; SCR = os.environ["SCRATCH"]; NEW = os.environ["MODE"] == "new"; KITS = os.environ["KITS"]
sys.path.insert(0, APP); os.chdir(APP)
KEYS = os.path.join(SCR, "keys.txt"); BEAT = os.path.join(SCR, "beat.json"); JKEYS = os.path.join(SCR, "job_keys.txt"); JDIR = os.path.join(SCR, "jobs")
os.environ.update(RECEPTION_KEYS=KEYS, RECEPTION_BEAT=BEAT, RECEPTION_JOB_KEYS=JKEYS, RECEPTION_JOB_DIR=JDIR,
                  DOCTERZ_EXPORT_STORE=os.path.join(SCR, "store"), PC_KITS_ROOT=KITS, PC_KIT_CODES=os.path.join(SCR, "codes.json"),
                  PC_KIT_LOG=os.path.join(SCR, "log.txt"), FINANCE_ALLOW_HEADER_AUTH="1")
n, fails = 0, []
def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:300] + "]") if (got is not None and not cond) else ""))
    if not cond:
        fails.append(label)
# ---- the kit's own agent and signing tool, unpacked from the zip the Clinic PCs page serves
PC = os.path.join(SCR, "pc"); AG = os.path.join(PC, "ClinicAgent"); os.makedirs(AG)
zf = zipfile.ZipFile(os.path.join(KITS, "reception", "kit.zip")); zf.extractall(os.path.join(PC, "kit"))
for f in ("reception_agent.py", "reception_sign.py"):
    open(os.path.join(AG, f), "wb").write(open(os.path.join(PC, "kit", f), "rb").read())
os.environ["USERPROFILE"] = os.path.join(PC, "home"); os.makedirs(os.path.join(PC, "home", "Downloads"))
spec = importlib.util.spec_from_file_location("ra_w453", os.path.join(AG, "reception_agent.py")); ra = importlib.util.module_from_spec(spec); spec.loader.exec_module(ra)
ra.find_my_drive = lambda: None
ra.now = lambda: datetime.datetime.utcnow() + datetime.timedelta(hours=5.5)      # the reception PC's clock is IST; this box's may not be
ra.ensure_dirs()
PARENT = os.path.join(SCR, "parent_key.txt"); open(PARENT, "w").write(bytes(range(11, 43)).hex() + "\n")     # the walk's stand-in for the owner's key
STRANGER = bytes(range(60, 92))                                                                               # a key nobody enrolled
SECOND = bytes(range(100, 132))                                                                               # on the server's list, NOT on the PC's
ppub = ra.ed_public(bytes(range(11, 43))).hex()
open(ra.KEYS_FILE, "w").write("# walk\n%s  parent-walk\n" % ppub)
open(JKEYS, "w").write("# walk\n%s  parent-walk\n%s  second-walk (not on the PC)\n" % (ppub, ra.ed_public(SECOND).hex()))
open(KEYS, "w").write("# walk\n%s  receptionpc (walk)\n" % ra.upload_public())

import finance_app as fa
c = fa.app.test_client()
check("the finance app loads with every part mounted", not fa._MOUNT_FAILED, fa._MOUNT_FAILED)
RD = sys.modules.get("reception_door")
P5 = ["/finance/api/reception/jobs/" + x for x in ("submit", "next", "ack", "result", "read")]
def stamp(hours_ago=0.0):
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=5.5 - hours_ago)).strftime("%Y%m%dT%H%M%S_")
def signed_job(tail, text, key=None, hours_ago=0.0, sign_text=None):
    name = stamp(hours_ago) + tail; key = key or bytes(range(11, 43))
    sig = ra.ed_sign(key, ra.job_message(name, (sign_text if sign_text is not None else text).encode()))
    return {"name": name, "job": base64.b64encode(text.encode()).decode(), "sig": sig.hex()}
BROWSER = {"Origin": "https://followup.dr-manoj.in", "Sec-Fetch-Site": "same-origin", "Content-Type": "application/json"}
def submit(j, **h):
    return c.post(P5[0], data=json.dumps(j), headers=dict(BROWSER, **h))
def pc_post(path, kind, body=b"", name="", key=None):
    ts = int(time.time()); key = key or ra.upload_secret()
    return c.post(path, data=body, headers={"X-Rx-Time": str(ts), "X-Rx-Name": name, "X-Rx-Mtime": "", "X-Rx-Sig": ra.ed_sign(key, ra.upload_message(kind, ts, name, "", body)).hex()})
def read(name, key=None, ts=None, sig=None):
    ts = str(ts or int(time.time())); key = key or bytes(range(11, 43))
    sig = sig or ra.ed_sign(key, b"clinic-reception-job-read-v1\n" + name.encode() + b"\n" + ts.encode()).hex()
    return c.post(P5[4], data=json.dumps({"name": name, "ts": ts, "sig": sig}), headers=BROWSER)
J = lambda r: r.get_json(silent=True) or {}

if not NEW:
    for p in P5:
        r = c.post(p, data=json.dumps(signed_job("old.py", "print(1)\n")), headers=BROWSER)
        check("OLD APP (S451, the box as it is): %s is shut by the gate (401 not_signed_in)" % p.rsplit("/", 1)[1], r.status_code == 401 and J(r).get("error") == "not_signed_in", r.status_code)
    check("OLD APP: its reception door has no job relay", RD is not None and not hasattr(RD, "job_keys"))
    print("WALK_S453 FIN OLD %s (%d checks, %d failed)" % ("AS EXPECTED" if not fails else "UNEXPECTED", n, len(fails)))
    sys.exit(0 if not fails else 1)

# ---- 1. what was already there still stands
with fa.app.app_context():
    h = fa._health_state(fa.db())
mr = [x for x in h["checks"] if x["key"] == "mounts"]
check("the mounts row still counts 27 parts, all loaded (no new part: the relay lives in reception_door.py)", mr and mr[0]["state"] == "ok" and "all 27 parts" in mr[0]["detail"], mr)
check("the five relay paths are public by exact path, and nothing near them is", all(p in fa.PUBLIC_PATHS for p in P5)
      and c.post("/finance/api/reception/jobs").status_code in (401, 404, 405) and c.post("/finance/api/reception/jobs/submit/x").status_code in (401, 404)
      and c.get("/finance/api/reception/jobs/list").status_code in (401, 404))
r = pc_post("/finance/api/reception/heartbeat", "heartbeat", json.dumps({"agent_version": "walk", "attention": []}).encode())
check("the S449 heartbeat door still takes this PC's signed heartbeat", r.status_code == 200 and J(r).get("status") == "KEPT", r.status_code)

# ---- 2. the submit door
import sqlite3
con = sqlite3.connect(os.environ["FINANCE_DB"]); ME = con.execute("SELECT username FROM unit_role WHERE unit='medical' AND role='checker' AND active=1").fetchone()[0]; con.close()
good = signed_job("hello.py", "import os\nprint('hello from', os.path.basename(__file__))\nprint('ran in', os.path.basename(os.getcwd()))\n")
r = submit(good)
check("a job signed with the owner's key is QUEUED -- with no login at all", r.status_code == 200 and J(r).get("status") == "QUEUED", (r.status_code, J(r)))
inn = os.path.join(JDIR, "in")
check("the queue keeps the job byte for byte and its signature, in files only root can read, in folders only root can enter",
      open(os.path.join(inn, good["name"]), "rb").read() == base64.b64decode(good["job"]) and open(os.path.join(inn, good["name"] + ".sig")).read().strip() == good["sig"]
      and all(stat.S_IMODE(os.stat(os.path.join(inn, f)).st_mode) == 0o600 for f in os.listdir(inn)) and stat.S_IMODE(os.stat(inn).st_mode) == 0o700 and stat.S_IMODE(os.stat(JDIR).st_mode) == 0o700)
r = submit(good)
check("the same job again: ALREADY -- a name is used once, nothing is queued twice", r.status_code == 200 and J(r).get("status") == "ALREADY" and len(os.listdir(inn)) == 2, J(r))
before = sorted(os.listdir(inn))
r = submit(signed_job("s1.py", "print(1)\n", key=STRANGER))
check("a job signed with a key that is not on the server's list: 401, nothing queued", r.status_code == 401 and J(r).get("status") == "NOT_YOU" and sorted(os.listdir(inn)) == before, r.status_code)
r = submit(signed_job("s2.py", "print(1)\n", sign_text="print(2)\n"))
check("a job changed after it was signed: 401, nothing queued", r.status_code == 401 and sorted(os.listdir(inn)) == before)
j3 = signed_job("s3.py", "print(1)\n"); j3["name"] = j3["name"].replace("s3.py", "s4.py")
check("a job renamed after it was signed: 401", submit(j3).status_code == 401)
check("a login does not stand in for the signature: the owner, signed in, with an unsigned job -> 401",
      c.post(P5[0], data=json.dumps(dict(signed_job("s5.py", "print(1)\n"), sig="00" * 64)), headers=dict(BROWSER, **{"X-Clinic-User": ME, "X-Clinic-Role": ""})).status_code == 401)
for label, j, code in (("a name with no signing time", dict(good, name="hello.py"), 400), ("a name that climbs out of the folder", dict(good, name=stamp() + "../x.py"), 400),
                       ("a file type the PC does not run", dict(signed_job("x.exe", "MZ")), 400), ("no signature at all", dict(good, name=stamp() + "n.py", sig=""), 401),
                       ("a body that is not base64", dict(signed_job("b.py", "x"), job="***"), 400), ("an empty job", signed_job("e.py", ""), 400),
                       ("a job signed 50 hours ago", signed_job("old.py", "print(1)\n", hours_ago=50), 400), ("a job dated 3 hours ahead", signed_job("fut.py", "print(1)\n", hours_ago=-3), 400),
                       ("a job over 256 KB", signed_job("big.py", "x = 1\n" * 50000), 400)):
    r = submit(j)
    check("refused at the door: %s (%d)" % (label, code), r.status_code == code and J(r).get("ok") is False and sorted(os.listdir(inn)) == before, (r.status_code, J(r)))
check("refused at the door: not JSON, and a JSON list", c.post(P5[0], data=b"hello", headers=BROWSER).status_code == 400 and c.post(P5[0], data=b"[1]", headers=BROWSER).status_code == 400)
check("GET opens none of the five", all(c.get(p).status_code == 405 for p in P5))
RD._hits.clear()
keep = RD.JOB_WAITING_MAX; RD.JOB_WAITING_MAX = 1
r = submit(signed_job("full.py", "print(1)\n"))
check("a full queue says so (429 FULL) and takes nothing", r.status_code == 429 and J(r).get("status") == "FULL" and sorted(os.listdir(inn)) == before, J(r))
RD.JOB_WAITING_MAX = keep
os.rename(JKEYS, JKEYS + ".away")
check("with no job-key file the relay is shut: submit and read both 503", submit(signed_job("nk.py", "print(1)\n")).status_code == 503 and read(good["name"]).status_code == 503)
os.rename(JKEYS + ".away", JKEYS)

# ---- 3. the read door
r = read(good["name"])
check("a signed read of a waiting job: QUEUED, no result yet", r.status_code == 200 and J(r).get("state") == "QUEUED" and J(r).get("result") is None, J(r))
check("a read with no signature, a stranger's signature, or a signature for another job: 401",
      c.post(P5[4], data=json.dumps({"name": good["name"]}), headers=BROWSER).status_code == 401 and read(good["name"], key=STRANGER).status_code == 401
      and read(good["name"], sig=ra.ed_sign(bytes(range(11, 43)), b"clinic-reception-job-read-v1\n" + b"20260101T000000_other.py" + b"\n" + str(int(time.time())).encode()).hex()).status_code == 401)
r = read(good["name"], ts=int(time.time()) - 1200)
check("a read signed 20 minutes ago: 401 CLOCK (a copied read does not keep working)", r.status_code == 401 and J(r).get("status") == "CLOCK", J(r))
check("a signed read of a name nobody sent: UNKNOWN", J(read(stamp() + "nobody.py")).get("state") == "UNKNOWN")
check("a job's signature does not open the read door (the two are signed differently)", read(good["name"], sig=good["sig"]).status_code == 401)

# ---- 4. the PC's three doors, by hand
check("next / ack / result with no signature: the door's own 401", all(c.post(p, data=b"").status_code == 401 for p in P5[1:4]))
check("next signed with a key that is not this PC's: 401", pc_post(P5[1], "jobs-next", key=STRANGER).status_code == 401)
check("a heartbeat's signature does not open 'next' (each kind is signed as itself)", pc_post(P5[1], "heartbeat").status_code == 401)
r = pc_post(P5[1], "jobs-next")
check("next signed by the PC: the waiting job, byte for byte, with its signature", r.status_code == 200 and J(r).get("status") == "JOB" and J(r).get("name") == good["name"]
      and J(r).get("job") == good["job"] and J(r).get("sig") == good["sig"], J(r).get("status"))
check("asking again before acknowledging hands over the same job (nothing is lost if the answer never arrived)", J(pc_post(P5[1], "jobs-next")).get("name") == good["name"])
check("a result for a job this server never handed out is refused (400)", pc_post(P5[3], "job-result", b"x", stamp() + "never.py").status_code == 400)
check("ack / result with a name that is not a job name: 400", pc_post(P5[2], "jobs-ack", b"taken", "hello.py").status_code == 400 and pc_post(P5[3], "job-result", b"x", "hello.py").status_code == 400)

# ---- 5. THE CHAIN, over real HTTP: the kit's own agent fetches, verifies, RUNS, answers
from werkzeug.serving import make_server
srv = make_server("127.0.0.1", 0, fa.app, threaded=True)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = "http://127.0.0.1:%d" % srv.server_port
json.dump({"server_url": BASE, "job_timeout_default": 60}, open(os.path.join(AG, "config.json"), "w"))
cfg = ra.load_config(); st = ra.new_state()
def run_jobs(secs=40):
    t = time.time()
    while time.time() - t < secs:
        ra.poll_running_job(st, cfg); ra.poll_local_jobs(st, cfg)
        if not st.get("job") and not [x for x in os.listdir(ra.JOBS_IN) if not x.endswith(".tmp")]:
            return True
        time.sleep(0.2)
    return False
ra.poll_server_jobs(st, cfg)
check("CHAIN: the kit's agent asks the server, verifies the job with ITS OWN key list, and queues it", os.listdir(ra.JOBS_IN) == ["server__" + good["name"]]
      and open(os.path.join(ra.JOBS_IN, "server__" + good["name"]), "rb").read() == base64.b64decode(good["job"]), os.listdir(ra.JOBS_IN))
check("CHAIN: the server knows the PC took it -- out of the waiting folder, state TAKEN", J(read(good["name"])).get("state") == "TAKEN" and os.listdir(inn) == []
      and os.path.isfile(os.path.join(JDIR, "taken", good["name"])))
check("CHAIN: the job RUNS on the PC", run_jobs() and (st.get("last_job") or {}).get("name") == "server__" + good["name"] and st["last_job"]["exit"] == 0, st.get("last_job"))
ra.poll_server_jobs(st, cfg)
r = read(good["name"]); res = J(r).get("result") or ""
check("CHAIN: its output comes back and is read with a signed read -- the job's own words, its exit code, the agent's version",
      J(r).get("state") == "RESULT" and "hello from server__" + good["name"] in res and "ran in work" in res and "EXIT: 0" in res and "AGENT: S453.1" in res and st["server_results"] == [], res[:300])
tok = subprocess.run([sys.executable, "-B", os.path.join(AG, "reception_sign.py"), "read-token", PARENT, good["name"]], capture_output=True, text=True)
r = c.post(P5[4], data=tok.stdout.strip(), headers=BROWSER)
check("CHAIN: the kit's signing tool makes a read-token this server takes", tok.returncode == 0 and r.status_code == 200 and J(r).get("state") == "RESULT", (tok.stdout[:120], r.status_code))
jf = os.path.join(SCR, "tooljob.py"); open(jf, "w").write("print('signed by the tool')\n")
sg = subprocess.run([sys.executable, "-B", os.path.join(AG, "reception_sign.py"), "sign", PARENT, jf], capture_output=True, text=True)
tn = re.search(r"signed: (\S+)", sg.stdout).group(1)
r = submit({"name": tn, "job": base64.b64encode(open(os.path.join(SCR, tn), "rb").read()).decode(), "sig": open(os.path.join(SCR, tn + ".sig")).read().strip()})
ra.poll_server_jobs(st, cfg); ok_run = run_jobs(); ra.poll_server_jobs(st, cfg)
check("CHAIN: a job stamped and signed by the kit's own signing tool goes the whole road", J(r).get("status") == "QUEUED" and ok_run and "signed by the tool" in (J(read(tn)).get("result") or ""), J(read(tn)))
check("CHAIN: the same job cannot be put in again once it has run", J(submit(good)).get("status") == "ALREADY" and J(submit(good)).get("state") == "RESULT")

# ---- 6. THE POINT OF THE DESIGN: the server cannot make the PC run a job
sj = signed_job("server_says_run.py", "open('PWNED.txt','w').write('x')\n", key=SECOND)
r = submit(sj)
done_before = st["jobs_done"]
ra.poll_server_jobs(st, cfg); run_jobs(5); ra.poll_server_jobs(st, cfg)
r2 = J(read(sj["name"], key=SECOND))
check("a job the SERVER accepts (its list knows the key) but the PC's own list does not know: the PC REFUSES it, runs nothing, and says why",
      J(r).get("status") == "QUEUED" and st["jobs_done"] == done_before and os.listdir(ra.JOBS_IN) == [] and not os.path.exists(os.path.join(ra.JOBS_WORK, "PWNED.txt"))
      and r2.get("state") == "REFUSED" and "does not match an enrolled key" in (r2.get("refused") or ""), r2)
tj = signed_job("tampered.py", "print('as signed')\n")
submit(tj); open(os.path.join(inn, tj["name"]), "wb").write(b"open('PWNED2.txt','w').write('x')\n")     # the server's own disk is changed under it
ra.poll_server_jobs(st, cfg); run_jobs(5)
r3 = J(read(tj["name"]))
check("a job changed ON THE SERVER after it was queued: the PC refuses it", st["jobs_done"] == done_before and not os.path.exists(os.path.join(ra.JOBS_WORK, "PWNED2.txt")) and r3.get("state") == "REFUSED", r3)
check("the queue is empty again and the trail has every step, with no job text in it", os.listdir(inn) == []
      and all(w in open(os.path.join(JDIR, "log.txt")).read() for w in ("QUEUED (signed by parent-walk", "took it", "REFUSED it", "sent the result", "REFUSED at the door"))
      and "PWNED" not in open(os.path.join(JDIR, "log.txt")).read())
old = os.path.join(JDIR, "results", "20200101T000000_ancient.py.out.txt"); open(old, "w").write("x"); os.utime(old, (time.time() - 20 * 86400,) * 2)
submit(signed_job("prune.py", "print(1)\n"))
check("results older than 14 days are cleared when a new job arrives", not os.path.exists(old))
b, _ = ra.build_beat(st, cfg)
check("the agent's heartbeat says the server door is on, when the server last answered and how many jobs it took (2)",
      b["server_jobs"]["enabled"] is True and b["server_jobs"]["last_answer"] and b["server_jobs"]["taken_since_start"] == 2 and b["server_jobs"]["results_waiting"] == 0, b["server_jobs"])
srv.shutdown()

# ---- 7. the Clinic PCs page serves the kit this agent came from
PK = sys.modules.get("pc_kits"); info = PK.kit_info("reception")
pg = c.get("/finance/pcs", headers={"X-Clinic-User": ME, "X-Clinic-Role": ""}).get_data(as_text=True)
check("the Clinic PCs page offers the new kit (agent S453.1), whole and matching its KIT_INFO", info and "agent S453.1" in info["version"] and "agent S453.1" in pg and "<form method=post" in pg
      and hashlib.md5(open(os.path.join(KITS, "reception", "kit.zip"), "rb").read()).hexdigest() == info["kit_md5"], info)
sums = [l.split(None, 1) for l in open(os.path.join(PC, "kit", "MD5SUMS.txt")).read().splitlines() if l.strip()]
okf = [(f.strip(), hashlib.md5(open(os.path.join(PC, "kit", f.strip()), "rb").read()).hexdigest() == h_) for h_, f in sums if f.strip() != "pyportable.zip"]
check("every file in the kit is what the kit's own MD5SUMS.txt says (%d files)" % len(okf), len(okf) == 9 and all(v for _f, v in okf), okf)
bat = open(os.path.join(PC, "kit", "INSTALL_RECEPTION_AGENT.bat"), "rb").read()
check("the installer in the kit still has its Windows line endings", bat.count(b"\r\n") > 100 and bat.count(b"\n") == bat.count(b"\r\n"))
print("WALK_S453 FIN NEW %s (%d checks, %d failed)" % ("GREEN" if not fails else "RED", n, len(fails)))
for f in fails:
    print("   FAILED: " + f)
sys.exit(0 if not fails else 1)
'''

res = {}
base = os.path.dirname(os.path.abspath(a.db))
runs = [("fin", "new", FIN, sys.executable, a.new, a.db), ("fin", "old", FIN, sys.executable, a.old, a.db + ".old")]
for part, mode, probe, exe, app, db in runs:
    scr = os.path.join(base, "scr_%s_%s" % (part, mode))
    os.makedirs(scr, exist_ok=True)
    env = dict(os.environ, APPDIR=os.path.abspath(app), SCRATCH=scr, MODE=mode, KITS=os.path.abspath(a.kits), PYTHONDONTWRITEBYTECODE="1",
               FINANCE_SSO_DIR=os.path.abspath(a.sso), FINANCE_DB=os.path.abspath(db))
    env.pop("FINANCE_MARG_TOKEN", None)
    p = subprocess.run([exe, "-B", "-c", probe], env=env, capture_output=True, text=True, timeout=900)
    out = [l for l in p.stdout.splitlines() if l.strip()]
    for l in out:
        if l.startswith(("  ok", "  FAIL", "   FAILED", "WALK_S453", "--")):
            print(("" if mode == "new" else "-- old: ") + l)
    if p.returncode != 0:
        print("-- %s %s probe exit %d: %s" % (part, mode, p.returncode, p.stderr.strip()[-1500:]))
    res[(part, mode)] = (p.returncode, " ".join(o for o in out if o.startswith("WALK_S453")))
good = (res[("fin", "new")][0] == 0 and "FIN NEW GREEN" in res[("fin", "new")][1] and res[("fin", "old")][0] == 0 and "FIN OLD AS EXPECTED" in res[("fin", "old")][1])
print("WALK_S453 GREEN" if good else "WALK_S453 RED: %s" % {"%s %s" % k: v[1] or ("exit %d" % v[0]) for k, v in res.items()})
sys.exit(0 if good else 1)
