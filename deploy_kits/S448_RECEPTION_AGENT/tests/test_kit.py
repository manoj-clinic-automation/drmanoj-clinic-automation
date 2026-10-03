#!/usr/bin/env python3
"""Offline walk of S448_RECEPTION_AGENT. Run with the SAME Python version the
PC will run (3.11.9). Every check prints one line; the last line is the count.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

KIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kit")
if not os.path.isdir(KIT):                 # in the repository the tests sit inside the kit folder
    KIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("%s  %s%s" % ("ok  " if cond else "FAIL", name,
                        ("  -- " + str(detail)) if (detail and not cond) else ""))


def fresh_root():
    d = tempfile.mkdtemp(prefix="recagent_")
    for f in ("reception_agent.py", "agent_guard.py"):
        shutil.copy(os.path.join(KIT, f), d)
    return d


def load(root, modname="reception_agent"):
    spec = importlib.util.spec_from_file_location(
        modname + "_" + os.path.basename(root), os.path.join(root, modname + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def tick(m, st, cfg, n=1, pause=0.0):
    for _ in range(n):
        m.poll_running_job(st, cfg)
        m.poll_local_jobs(st, cfg)
        if pause:
            time.sleep(pause)


def wait_job(m, st, cfg, secs=30):
    t = time.time()
    while time.time() - t < secs:
        tick(m, st, cfg)
        if not st.get("job") and not os.listdir(m.JOBS_IN):
            return True
        time.sleep(0.2)
    return False


def put(path, text, age=10):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    t = time.time() - age
    os.utime(path, (t, t))


# ---------------------------------------------------------------- 1. Ed25519
root = fresh_root()
m = load(root)
VEC = [  # RFC 8032 section 7.1: secret, public, message, signature
    ("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
     "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a", "",
     "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
     "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"),
    ("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
     "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c", "72",
     "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da"
     "085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"),
    ("c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7",
     "fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025", "af82",
     "6291d657deec24024827e69c3abe01a30ce548a284743a445e3680d7db5ac3ac"
     "18ff9b538d16f290ae67f760984dc6594a7c15e9716ed28dc027beceea1ec40a"),
]
for i, (sk, pk, msg, sig) in enumerate(VEC, 1):
    sk, pk, msg, sig = (bytes.fromhex(x) for x in (sk, pk, msg, sig))
    check("ed25519 RFC vector %d: public key" % i, m.ed_public(sk) == pk)
    check("ed25519 RFC vector %d: signature" % i, m.ed_sign(sk, msg) == sig)
    check("ed25519 RFC vector %d: verifies" % i, m.ed_verify(pk, msg, sig))
    check("ed25519 RFC vector %d: a changed message is refused" % i,
          not m.ed_verify(pk, msg + b"x", sig))
    bad = bytearray(sig); bad[5] ^= 1
    check("ed25519 RFC vector %d: a changed signature is refused" % i,
          not m.ed_verify(pk, msg, bytes(bad)))
check("ed25519: junk inputs are refused, not raised",
      not m.ed_verify(b"", b"", b"") and not m.ed_verify(b"\xff" * 32, b"m", b"\xff" * 64))
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization as ser
    agree = True
    for i in range(40):
        sk = os.urandom(32)
        msg = os.urandom(i * 7)
        k = Ed25519PrivateKey.from_private_bytes(sk)
        pk = k.public_key().public_bytes(ser.Encoding.Raw, ser.PublicFormat.Raw)
        agree &= (m.ed_public(sk) == pk and m.ed_sign(sk, msg) == k.sign(msg)
                  and m.ed_verify(pk, msg, k.sign(msg)))
    check("ed25519: 40 random keys agree with the `cryptography` library", agree)
except ImportError:
    print("note  `cryptography` not installed here -- cross-check skipped")

# ------------------------------------------------------------- 2. local jobs
m.ensure_dirs()
st, cfg = m.new_state(), m.load_config()
put(os.path.join(m.JOBS_IN, "a1.py"), "print('hello from job'); import sys; sys.exit(3)\n")
tick(m, st, cfg)
check("a job is not started on first sight (may still be arriving)", st["job"] is None
      and os.path.exists(os.path.join(m.JOBS_IN, "a1.py")))
check("job runs to its end", wait_job(m, st, cfg))
out = open(os.path.join(m.JOBS_OUT, "a1.py.out.txt"), encoding="utf-8").read()
check("job output captured", "hello from job" in out, out)
check("job exit code recorded", "EXIT: 3" in out, out)
check("job script moved to done", any(n.endswith("__a1.py") for n in os.listdir(m.JOBS_DONE)))
check("nothing left in running", os.listdir(m.JOBS_RUNNING) == [])

put(os.path.join(m.JOBS_IN, "slow.py"), "# timeout=5\nimport time\nprint('start', flush=True)\ntime.sleep(60)\n")
t0 = time.time()
check("timed-out job ends", wait_job(m, st, cfg, 40))
out = open(os.path.join(m.JOBS_OUT, "slow.py.out.txt"), encoding="utf-8").read()
check("timeout recorded and partial output kept", "TIMED_OUT: yes" in out and "start" in out, out)
check("timeout honoured (5s directive, not 60s)", time.time() - t0 < 30, time.time() - t0)

put(os.path.join(m.JOBS_IN, "bad name.py"), "print(1)\n")
put(os.path.join(m.JOBS_IN, "notes.txt"), "x\n")
tick(m, st, cfg, 3)
check("a file with a space in its name is refused, not run",
      not os.path.exists(os.path.join(m.JOBS_IN, "bad name.py"))
      and os.path.exists(os.path.join(m.JOBS_OUT, "bad_name.py.out.txt")))
check("a .txt is refused, not run", os.path.exists(os.path.join(m.JOBS_OUT, "notes.txt.out.txt")))

# a file that keeps growing is never started
p = os.path.join(m.JOBS_IN, "grow.py")
for i in range(4):
    with open(p, "a") as fh:
        fh.write("print(%d)\n" % i)
    tick(m, st, cfg)
check("a file still being written is left alone", st["job"] is None and os.path.exists(p))
t = time.time() - 10; os.utime(p, (t, t))
tick(m, st, cfg); check("...and runs once it is still", wait_job(m, st, cfg))

# off switches
os.makedirs(m.P("_off"), exist_ok=True)
put(m.OFF_JOBS, "off until further notice\n")
check("JOBS_OFF.txt switches jobs off", m.is_off(m.OFF_JOBS))
put(m.OFF_JOBS, "ON\n")
check("a switch file that says ON counts as absent", not m.is_off(m.OFF_JOBS))
check("no switch file means on", not m.is_off(m.OFF_ALL))

# orphan
put(os.path.join(m.JOBS_RUNNING, "orph.py"), "print('never again')\n")
m.recover_orphans(st, cfg)
out = open(os.path.join(m.JOBS_OUT, "orph.py.out.txt"), encoding="utf-8").read()
check("a job cut short by a restart is reported and NOT re-run",
      "NOT run again" in out and "never again" not in out, out)

# job commands, Windows shape
os.environ["SystemRoot"] = r"C:\Windows"
c = m.job_command(r"C:\ClinicAgent\jobs\running\x.ps1")
check("ps1 -> powershell, bypass, -File", c[0].replace("/", "\\").endswith(
    "WindowsPowerShell\\v1.0\\powershell.exe") and c[-2:] == ["-File", r"C:\ClinicAgent\jobs\running\x.ps1"]
    and "Bypass" in c, c)
c = m.job_command(r"C:\ClinicAgent\jobs\running\x.cmd")
check("cmd -> cmd.exe /d /c", c[0].replace("/", "\\").endswith("System32\\cmd.exe") and c[1:3] == ["/d", "/c"], c)
check("unknown type -> no command", m.job_command("x.exe") is None)
check("timeout directive is capped", m.job_timeout(os.path.join(m.JOBS_DONE, "nope"), cfg) == cfg["job_timeout_default"])
for nm, txt, want in (("t1.py", "import subprocess\np.wait(timeout=30)\n", 600), ("t2.cmd", "@echo off\r\nREM timeout=900\r\n", 900),
                      ("t3.ps1", "# timeout: 45\n", 45), ("t4.cmd", ":: timeout=99999999\n", 600), ("t5.py", "#timeout=1\n", 5)):
    put(os.path.join(root, nm), txt)
    got = m.job_timeout(os.path.join(root, nm), cfg)
    check("timeout directive: %s -> %ds" % (nm, want), got == want, got)

# ------------------------------------------- 3. heartbeat: counts, never names
drive = os.path.join(root, "G", "My Drive")
ex = os.path.join(drive, "Clinic Records", "Docterz exports")
inbox = os.path.join(drive, "Clinic Records", "X-ray inbox")
chk = os.path.join(drive, "Clinic Records", "X-ray check")
arch = os.path.join(drive, "Clinic Data Archive")
for d in (ex, os.path.join(inbox, "_filed", "30-Sep"), chk, arch):
    os.makedirs(d)
SECRET_NAMES = ["RAMKALI DEVI 9911.jpg", "SOHANLAL 9912.jpg", "MUNNI BEGUM.jpg"]
put(os.path.join(inbox, SECRET_NAMES[0]), "x", age=30 * 3600)
put(os.path.join(inbox, "_filed", "30-Sep", SECRET_NAMES[1]), "x")
put(os.path.join(chk, SECRET_NAMES[2]), "x")
put(os.path.join(ex, "consultation_report_2026-10-02.csv"), "x", age=5)
put(os.path.join(ex, "followup_logs (63).csv"), "x", age=3 * 86400)
put(os.path.join(ex, "ChromeSetup.exe"), "x")
m.find_my_drive = lambda: drive
home = os.path.join(root, "home"); os.makedirs(os.path.join(home, "Downloads"))
os.environ["USERPROFILE"] = home
la = os.path.join(root, "local"); os.environ["LOCALAPPDATA"] = la
for prof, dl in (("Default", ex), ("Profile 2", None)):
    os.makedirs(os.path.join(la, "Google", "Chrome", "User Data", prof))
    json.dump({"download": ({"default_directory": dl} if dl else {})},
              open(os.path.join(la, "Google", "Chrome", "User Data", prof, "Preferences"), "w"))
m.process_names = lambda: {"googledrivefs.exe": [1], "chrome.exe": [2]}
beat, procs = m.build_beat(st, cfg)
blob = json.dumps(beat) + m.human(beat)
check("heartbeat carries NO file name from the X-ray folders",
      not any(n.split(".")[0] in blob or n.split()[0] in blob for n in SECRET_NAMES), blob)
check("reports counted: consultation today 1, follow-up 0 today and 3 days old",
      beat["docterz_exports"]["consultation_today"] == 1 and beat["docterz_exports"]["followup_today"] == 0
      and beat["docterz_exports"]["followup_days_old"] == 3, beat["docterz_exports"])
check("stray downloads counted, not named", beat["docterz_exports"]["other_files"] == 1 and "ChromeSetup" not in blob)
check("x-ray inbox: 1 waiting, ~30 h old, check 1",
      beat["xray"]["inbox_waiting"] == 1 and 29 < beat["xray"]["inbox_oldest_hours"] < 31
      and beat["xray"]["check_waiting"] == 1, beat["xray"])
check("chrome folder read from Preferences and matched", beat["chrome_saves_to_exports"] is True, beat["chrome_download_dirs"])
check("attention names the stuck X-ray and the missing Claude app",
      any("X-ray" in a for a in beat["attention"]) and any("Claude" in a for a in beat["attention"]), beat["attention"])
check("drive running is read from the process list", beat["google_drive_running"] is True)
ok = m.write_beat(beat, cfg)
check("heartbeat written locally and to Drive FromReception",
      ok and os.path.exists(m.LOCAL_BEAT_JSON) and os.path.exists(os.path.join(arch, "FromReception", "heartbeat.txt")))
# Chrome's download folder: changed only while Chrome is closed, and faithfully
pp = os.path.join(la, "Google", "Chrome", "User Data", "Profile 2", "Preferences")
orig = {"download": {"default_directory": "C:\\Users\\dell\\Downloads", "prompt_for_download": True},
        "profile": {"name": "\u0930\u093f\u0938\u0947\u092a\u094d\u0936\u0928", "n": 12345678901234567890, "f": 1.5}, "z": [1, {"a": None}]}
open(pp, "w", encoding="utf-8").write(json.dumps(orig, ensure_ascii=False))
r = m.chrome_set_download_dir(ex, {"chrome.exe": [2]})
check("Chrome running -> its settings are not touched", r == [("*", "Chrome is running -- nothing changed")]
      and json.load(open(pp, encoding="utf-8")) == orig, r)
m.process_names = lambda: {"googledrivefs.exe": [1]}
r = dict(m.chrome_set_download_dir(ex, {"googledrivefs.exe": [1]}))
now_ = json.load(open(pp, encoding="utf-8"))
want = json.loads(json.dumps(orig)); want["download"] = {"default_directory": ex, "prompt_for_download": False}
check("Chrome closed -> the wrong profile is set, the right one left alone",
      r.get("Profile 2", "").startswith("SET to") and r.get("Default") == "already set", r)
check("...and nothing else in the settings file changed (Hindi text, big numbers, order)",
      now_ == want and list(now_) == list(orig), now_)
check("...and the original is kept beside it", json.load(open(pp + ".before_clinicagent", encoding="utf-8")) == orig)
open(pp, "wb").write(b"\xff\xfe not json")
r = dict(m.chrome_set_download_dir(ex, {"x.exe": [1]}))
check("an unreadable settings file is left alone, not guessed at", r["Profile 2"].startswith("left alone")
      and open(pp, "rb").read() == b"\xff\xfe not json", r)
json.dump({"download": {}}, open(pp, "w"))
kf2 = os.path.join(root, "kit_keys.txt"); open(kf2, "w").write("# kit\n" + "ab" * 32 + "  parent-manojz\n" + "zz\n")
check("keys from the kit are added once", m.install_keys(kf2) == (1, 1) and m.install_keys(kf2) == (0, 1)
      and [lab for _, lab in m.authorized_keys()] == ["parent-manojz"])
check("a missing kit key file adds nothing", m.install_keys(os.path.join(root, "nope.txt")) == (0, 1))
os.remove(m.KEYS_FILE); m.ensure_dirs()
m.process_names = lambda: {"chrome.exe": [2]}
beat, procs = m.build_beat(st, cfg)
check("Drive not running -> attention", any("Google Drive is NOT running" in a for a in beat["attention"]))
calls = []
m.start_google_drive = lambda: calls.append("drive") or "launch.bat"
m.start_claude = lambda c: calls.append("claude") or None
st["started_ts"] = time.time() - 10
m.repairs(st, cfg, beat, procs)
check("no repair in the first minutes after logon", calls == [])
st["started_ts"] = time.time() - 1000
m.repairs(st, cfg, beat, procs); m.repairs(st, cfg, beat, procs)
check("repairs tried once, not on every beat", calls == ["drive", "claude"], calls)
check("a repair that found no way is said so", any("no way to start" in r for r in st["repairs"]), st["repairs"])
json.dump({"download": {"default_directory": "C:\\elsewhere"}}, open(os.path.join(la, "Google", "Chrome", "User Data", "Default", "Preferences"), "w"))
beat3, procs3 = m.build_beat(st, cfg)
m.repairs(st, cfg, beat3, procs3)
check("Chrome saving elsewhere while Chrome is OPEN: reported, not touched",
      beat3["chrome_saves_to_exports"] is False and any("Chrome is NOT saving" in a for a in beat3["attention"])
      and not any("Chrome was not saving" in r for r in st["repairs"]))
m.process_names = lambda: {"explorer.exe": [5]}
beat3, procs3 = m.build_beat(st, cfg); st["repair_at"]["drive"] = st["repair_at"]["claude"] = time.time()
m.repairs(st, cfg, beat3, procs3)
beat4, _ = m.build_beat(st, cfg)
check("...and put right by itself once Chrome is closed", beat4["chrome_saves_to_exports"] is True
      and any("Chrome was not saving" in r and "SET to" in r for r in st["repairs"]), st["repairs"])
m.process_names = lambda: {"chrome.exe": [2]}
put(m.OFF_ALL, "off\n")
beat2, _ = m.build_beat(st, cfg); calls.clear(); st["repair_at"] = {}
m.repairs(st, cfg, beat2, procs)
check("ALL_OFF stops repairs and says so", calls == [] and beat2["switched_off"] and beat2["attention"][0].startswith("the agent is SWITCHED OFF"))
put(m.OFF_ALL, "ON\n")
sample = '"System Idle Process","0","Services","0","8 K"\r\n"GoogleDriveFS.exe","1234","Console","1","120,000 K"\r\n"Claude.exe","88","Console","1","9 K"\r\n"Claude.exe","89","Console","1","9 K"\r\n'
m.run_quiet = lambda cmd, timeout=30: (0, sample)
del m.process_names
m2 = load(root); m2.run_quiet = lambda cmd, timeout=30: (0, sample)
pn = m2.process_names()
check("tasklist CSV parsed", pn.get("googledrivefs.exe") == [1234] and pn.get("claude.exe") == [88, 89], pn)
check("path compare ignores case and trailing slash", m2._same_path("g:\\my drive\\X\\", "G:/My Drive/x"))

# -------------------------------------------------------------- 4. Drive jobs
import datetime as _dt
m = load(root); m.find_my_drive = lambda: drive
st, cfg = m.new_state(), m.load_config()
jobs_dir = os.path.join(arch, "ToReception", "jobs"); os.makedirs(jobs_dir)
res_dir = os.path.join(arch, "FromReception", "results")
sk = os.urandom(32); pk = m.ed_public(sk)


def stamp(hours_ago=0.0):
    return (_dt.datetime.now() - _dt.timedelta(hours=hours_ago)).strftime("%Y%m%dT%H%M%S_")


def drive_job(name, text, key=sk, sign_name=None):
    put(os.path.join(jobs_dir, name), text)
    sig = m.ed_sign(key, m.job_message(sign_name or name, text.encode()))
    put(os.path.join(jobs_dir, name + ".sig"), sig.hex())
    return name


d1 = drive_job(stamp() + "d1.py", "print('ran from drive')\n")
m.poll_drive_jobs(st, cfg)
check("no key enrolled -> the Drive job is not even read", os.listdir(m.JOBS_IN) == [] and not os.path.exists(m.SEEN_FILE))
with open(m.KEYS_FILE, "w", encoding="utf-16") as fh:      # as Notepad / PowerShell would save it
    fh.write("# keys\r\n%s  test key\r\n" % pk.hex())
check("a key file saved as UTF-16 is still read", [k for k, _ in m.authorized_keys()] == [pk])
with open(m.KEYS_FILE, "w", encoding="utf-8-sig") as fh:
    fh.write("%s  test key\n" % pk.hex())
check("a key file with a byte-order mark is still read", [k for k, _ in m.authorized_keys()] == [pk])
with open(m.OFF_JOBS, "w", encoding="utf-16") as fh:
    fh.write("ON\r\n")
check("a UTF-16 switch file that says ON counts as absent", not m.is_off(m.OFF_JOBS))
m.poll_drive_jobs(st, cfg)
check("signed Drive job is queued", os.path.exists(os.path.join(m.JOBS_IN, "drive__" + d1)))
check("...and moved aside on Drive", os.path.exists(os.path.join(jobs_dir, "_taken", d1)) and not os.path.exists(os.path.join(jobs_dir, d1)))
os.utime(os.path.join(m.JOBS_IN, "drive__" + d1), (time.time() - 10,) * 2)
wait_job(m, st, cfg); m.poll_drive_jobs(st, cfg)
r = os.path.join(res_dir, d1 + ".out.txt")
check("its result goes back to Drive", os.path.exists(r) and "ran from drive" in open(r).read())
drive_job(d1, "print('ran from drive')\n")
m.poll_drive_jobs(st, cfg)
check("the same signed job put back is NOT run again (no replay)", os.listdir(m.JOBS_IN) == [])
d2 = drive_job(stamp() + "d2.py", "print('evil')\n", key=os.urandom(32))
d3 = drive_job(stamp() + "d3.py", "print('renamed')\n", sign_name=stamp() + "other.py")
d4 = stamp() + "d4.py"; put(os.path.join(jobs_dir, d4), "print('unsigned')\n")
d5 = stamp() + "d5.py"; put(os.path.join(jobs_dir, d5), "print('tampered')\n")
put(os.path.join(jobs_dir, d5 + ".sig"), m.ed_sign(sk, m.job_message(d5, b"print('original')\n")).hex())
d6 = drive_job(stamp(50) + "d6.py", "print('old but genuine')\n")
d7 = drive_job(stamp(-5) + "d7.py", "print('from the future')\n")
d8 = drive_job("d8.py", "print('no stamp')\n")
m.poll_drive_jobs(st, cfg)
check("wrong key, renamed, tampered, 50 h old, future-dated and unstamped jobs are all refused",
      os.listdir(m.JOBS_IN) == [] and st["drive_refused"] == 6
      and all(os.path.exists(os.path.join(res_dir, n + ".REFUSED.txt")) for n in (d2, d3, d5, d6, d7, d8)),
      (os.listdir(m.JOBS_IN), st["drive_refused"]))
check("the old genuine job is refused for its AGE, not its signature",
      "48 hours" in open(os.path.join(res_dir, d6 + ".REFUSED.txt")).read())
check("an unsigned job is left untouched, never run", d4 not in m._seen_read())
seen = m._seen_read()
for i in range(2100):
    seen["junk%04d.cmd" % i] = {"at": m.iso(), "sha256": "", "refused": "x"}
m._seen_write(seen)
check("a flood of 2,100 refused names does not push out the used one", d1 in m._seen_read() and len(m._seen_read()) <= 2100)
d9 = drive_job(stamp() + "d9.py", "print('must not run')\n")
real_write = m._seen_write; m._seen_write = lambda s: False
m.poll_drive_jobs(st, cfg)
check("if the used-names list cannot be written the job is NOT taken", os.listdir(m.JOBS_IN) == [])
m._seen_write = real_write
jc = dict(cfg); bad = os.path.join(root, "config.json")
json.dump({"beat_seconds": 5000, "disk_warn_gb": "lots", "docterz_rel": "x"}, open(bad, "w"))
c2 = m.load_config(); os.remove(bad)
check("config values that would hurt are clamped or dropped",
      c2["beat_seconds"] == 600 and c2["disk_warn_gb"] == 10 and c2["docterz_rel"] == m.DEFAULTS["docterz_rel"], c2)
put(os.path.join(ex, "consultation_report_bad.csv"), "x"); os.utime(os.path.join(ex, "consultation_report_bad.csv"), (-1e12, -1e12))
try:
    rr = m.scan_reports(ex); okr = rr["present"]
except Exception as exn:
    okr = False
check("a report file with an impossible date does not break the heartbeat", okr)
os.remove(os.path.join(ex, "consultation_report_bad.csv"))

# ------------------------------------------------- 5. update and roll-back
root2 = fresh_root()
py = sys.executable
# the live agent talks to a server that is not there (a closed local port): its life must not depend on it
json.dump({"tick_seconds": 1, "beat_seconds": 2, "server_url": "http://127.0.0.1:9"}, open(os.path.join(root2, "config.json"), "w"))
env = dict(os.environ, USERPROFILE=root2, LOCALAPPDATA=root2)
agent_src = open(os.path.join(root2, "reception_agent.py"), encoding="utf-8").read()
g = subprocess.Popen([py, "-c",
                      "import sys; sys.path.insert(0, %r); import agent_guard as g; g.POLL=1; sys.exit(g.main())" % root2],
                     cwd=root2, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wait_for(fn, secs=40):
    t = time.time()
    while time.time() - t < secs:
        try:
            if fn():
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def beat_version():
    return json.load(open(os.path.join(root2, "heartbeat.json")))["agent_version"]


check("guard starts the agent and a heartbeat appears", wait_for(lambda: beat_version() == "S456.1"))
g2 = subprocess.run([py, os.path.join(root2, "agent_guard.py")], cwd=root2, env=env, timeout=30)
check("a second guard steps aside (one per PC)", g2.returncode == 0 and g.poll() is None)
put(os.path.join(root2, "jobs", "in", "live.py"), "print('through the running agent')\n")
check("a job dropped in runs through the live agent",
      wait_for(lambda: "through the running agent" in open(os.path.join(root2, "jobs", "out", "live.py.out.txt")).read()))
put(os.path.join(root2, "reception_agent.py.new"), agent_src.replace('AGENT_VERSION = "S456.1"', 'AGENT_VERSION = "S449.4-test"'))
check("a good update is installed and the new version reports in",
      wait_for(lambda: beat_version() == "S449.4-test"))
check("...and is confirmed (marker gone, .prev kept)",
      wait_for(lambda: not os.path.exists(os.path.join(root2, "update_pending.json")))
      and os.path.exists(os.path.join(root2, "reception_agent.py.prev")))
put(os.path.join(root2, "reception_agent.py.new"), "def broken(:\n")
check("an update that does not compile is refused and set aside",
      wait_for(lambda: os.path.exists(os.path.join(root2, "reception_agent.py.rejected")))
      and beat_version() == "S449.4-test")
put(os.path.join(root2, "reception_agent.py.new"),
    agent_src.replace('AGENT_VERSION = "S456.1"', 'AGENT_VERSION = "S449.5-bad"').replace(
        "def main():\n    quiet_errors()", "def main():\n    raise RuntimeError('dies at start')\n    quiet_errors()"))
check("an update that compiles but dies is ROLLED BACK by the guard",
      wait_for(lambda: os.path.exists(os.path.join(root2, "reception_agent.py.failed"))
               and "ROLLED BACK" in open(os.path.join(root2, "guard.log")).read(), 60))
old = os.path.getmtime(os.path.join(root2, "heartbeat.json"))
check("...and the previous version is heartbeating again",
      wait_for(lambda: os.path.getmtime(os.path.join(root2, "heartbeat.json")) > old + 1
               and beat_version() == "S449.4-test", 60))
put(os.path.join(root2, "RESTART.flag"), "x")
check("RESTART.flag restarts the agent under the guard",
      wait_for(lambda: open(os.path.join(root2, "guard.log")).read().count("asked to be started again") >= 2))
apid = int(open(os.path.join(root2, "_agent.pid")).read())
g.kill()
try:
    os.kill(apid, 9)
except OSError:
    pass
blob = open(os.path.join(root2, "heartbeat.json")).read()
check("local heartbeat is valid JSON with the attention list", "attention" in json.loads(blob))
check("the live agent kept running with the server unreachable, and said so in its heartbeat",
      json.loads(blob)["direct_upload"]["enabled"] is True and json.loads(blob)["direct_upload"]["last_accepted"] is None
      and "direct upload: heartbeat not accepted" in open(os.path.join(root2, "agent.log")).read())

tool = fresh_root(); shutil.copy(os.path.join(KIT, "reception_sign.py"), tool)
kf = os.path.join(tool, "k.txt"); jf = os.path.join(tool, "fix.ps1"); put(jf, "Write-Output 1\n")
pub = subprocess.run([py, os.path.join(tool, "reception_sign.py"), "keygen", kf], capture_output=True, text=True).stdout.strip()
sg = subprocess.run([py, os.path.join(tool, "reception_sign.py"), "sign", kf, jf], capture_output=True, text=True)
made = [n for n in os.listdir(tool) if n.endswith("_fix.ps1")]
mm = load(tool)
# judge the stamp as the reception PC will: on a clock that reads IST
mm.now = lambda: (_dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(hours=5, minutes=30)).replace(tzinfo=None)
check("the signing tool makes a stamped job the agent accepts",
      sg.returncode == 0 and len(made) == 1 and mm.drive_job_stamp_verdict(made[0]) is None
      and mm.ed_verify(bytes.fromhex(pub), mm.job_message(made[0], open(os.path.join(tool, made[0]), "rb").read()),
                       bytes.fromhex(open(os.path.join(tool, made[0] + ".sig")).read().strip())), sg.stdout + sg.stderr)

# ------------------------------------------- 6. S449: straight to the server
import hashlib as _hl
import http.server as _hs
import threading as _th

root6 = fresh_root()
m6 = load(root6)
home6 = os.path.join(root6, "home"); dl6 = os.path.join(home6, "Downloads"); os.makedirs(dl6)
os.environ["USERPROFILE"] = home6
drive6 = os.path.join(root6, "G", "My Drive"); ex6 = os.path.join(drive6, "Clinic Records", "Docterz exports")
os.makedirs(ex6); os.makedirs(os.path.join(drive6, "Clinic Data Archive"))
m6.find_my_drive = lambda: drive6
m6.ensure_dirs()
CONS = "Patient Name,Consultation Date,Mode Of Payment,Amount\nW449 TEST A,07-01-2031,Cash,100\n"
FOLL = "Appointment ID,Patient Name,Mobile No,Due Date\nW1,W449 TEST B,x,09-01-2031\n"
put(os.path.join(ex6, "consultation_report_2031-01-07.csv"), CONS, age=60)
put(os.path.join(dl6, "followup_logs (3).csv"), FOLL, age=3600)
put(os.path.join(dl6, "consultation_report_not_really.csv"), "name,phone\nSOMEONE,private\n", age=60)   # right name, wrong first line
put(os.path.join(dl6, "RAMKALI DEVI report.csv"), CONS, age=60)                                         # right first line, wrong name
put(os.path.join(dl6, "consultation_report_old.csv"), CONS + "W449 OLD,01-01-2031,Cash,1\n", age=9 * 86400)
put(os.path.join(dl6, "consultation_report_fresh.csv"), CONS + "W449 FRESH,07-01-2031,UPI,5\n", age=2)  # still being written

p1 = m6.upload_public()
key_text = open(m6.UPLOAD_KEY_FILE).read()
check("the PC makes its own signing key once", p1 and len(p1) == 64 and m6.upload_public() == p1
      and open(m6.UPLOAD_KEY_FILE).read() == key_text)
open(m6.UPLOAD_KEY_FILE, "w").write("damaged\n")
check("a damaged key file is never silently replaced", m6.upload_public() is None
      and open(m6.UPLOAD_KEY_FILE).read() == "damaged\n")
open(m6.UPLOAD_KEY_FILE, "w").write(key_text)
check("what is signed changes with every part of the request", len({m6.upload_message(*a) for a in (
    ("report", 1, "a.csv", 5, b"x"), ("heartbeat", 1, "a.csv", 5, b"x"), ("report", 2, "a.csv", 5, b"x"),
    ("report", 1, "b.csv", 5, b"x"), ("report", 1, "a.csv", 6, b"x"), ("report", 1, "a.csv", 5, b"y"))}) == 6)

cache6 = {}
cands = m6.report_candidates([ex6, dl6], 4, cache6)
check("only the two reports are candidates -- by name AND first line, recent, and no longer being written",
      sorted(os.path.basename(c[0]) for c in cands) == ["consultation_report_2031-01-07.csv", "followup_logs (3).csv"],
      [os.path.basename(c[0]) for c in cands])
check("a file with the wrong name is never opened (it is not in the cache at all)",
      not any("RAMKALI" in k[0] for k in cache6))

GOT = {"beats": [], "reports": [], "mode": "ok"}


class H(_hs.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        if self.path.endswith("/pc-kit/enroll"):
            j = json.loads(body)
            good_code = self.headers.get("X-Kit-Code") == "GOODCODE"
            if good_code:
                GOT["enrolled"] = j
            raw = json.dumps({"ok": good_code, "message": "" if good_code else "this code is not known"}).encode()
            self.send_response(200 if good_code else 401); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw); return
        kind = "heartbeat" if self.path.endswith("/heartbeat") else "report"
        msg = m6.upload_message(kind, self.headers.get("X-Rx-Time"), self.headers.get("X-Rx-Name") or "",
                                self.headers.get("X-Rx-Mtime") or "", body)
        good = m6.ed_verify(bytes.fromhex(p1), msg, bytes.fromhex(self.headers.get("X-Rx-Sig") or ""))
        if GOT["mode"] == "login":
            self.send_response(302); self.send_header("Location", "/portal"); self.end_headers(); return
        if GOT["mode"] == "401" or not good:
            out, code = {"ok": False, "status": "NOT_YOU", "message": "bad signature"}, 401
        elif kind == "heartbeat":
            GOT["beats"].append(json.loads(body)); out, code = {"ok": True, "status": "KEPT"}, 200
        elif b"Consultation Date" in body or b"Appointment ID" in body:
            GOT["reports"].append((self.headers.get("X-Rx-Name"), _hl.md5(body).hexdigest()))
            out, code = {"ok": True, "status": "TAKEN", "day": "2031-01-07"}, 200
        else:
            out, code = {"ok": False, "status": "REFUSED", "message": "not a report"}, 400
        raw = json.dumps(out).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)


srv = _hs.HTTPServer(("127.0.0.1", 0), H)
_th.Thread(target=srv.serve_forever, daemon=True).start()
json.dump({"server_url": "http://elsewhere.example"}, open(os.path.join(root6, "config.json"), "w"))
check("a server address that is neither https nor this machine is not used",
      m6.load_config()["server_url"] == "https://followup.dr-manoj.in")
json.dump({"server_url": "http://127.0.0.1:%d" % srv.server_address[1]}, open(os.path.join(root6, "config.json"), "w"))
cfg6 = m6.load_config()
st6 = m6.new_state()
beat6, _ = m6.build_beat(st6, cfg6)
m6.direct_pass(st6, cfg6, beat6)
check("the heartbeat reaches the server, signed, and is the same heartbeat",
      len(GOT["beats"]) == 1 and GOT["beats"][0]["agent_version"] == "S456.1" and st6["upload"]["ok_at"])
check("both reports are sent, each once, under a clean name",
      sorted(n for n, _ in GOT["reports"]) == ["consultation_report_2031-01-07.csv", "followup_logs (3).csv"]
      and st6["upload"]["reports_sent"] == 2, GOT["reports"])
sent6 = json.load(open(m6.UPLOAD_SENT_FILE))
check("what was sent is remembered by md5, with the server's verdict",
      len(sent6) == 2 and all(v["status"] == "TAKEN" for v in sent6.values()))
m6.direct_pass(st6, cfg6, m6.build_beat(st6, cfg6)[0])
check("the next pass sends the heartbeat again and no report twice",
      len(GOT["beats"]) == 2 and len(GOT["reports"]) == 2)
st6b = m6.new_state()                                           # a restart: the ledger is on disk, not in memory
m6.direct_pass(st6b, cfg6, m6.build_beat(st6b, cfg6)[0])
check("after a restart nothing already sent is sent again", len(GOT["reports"]) == 2)
put(os.path.join(ex6, "consultation_report_2031-01-07 (1).csv"), CONS + "W449 TEST C,07-01-2031,UPI,200\n", age=60)
m6.direct_pass(st6b, cfg6, m6.build_beat(st6b, cfg6)[0])
check("a new export of the same day IS sent", len(GOT["reports"]) == 3)
hb = json.dumps(GOT["beats"][-1])
check("the heartbeat sent to the server carries no file name and no patient text",
      "W449" not in hb and "consultation_report" not in hb and "RAMKALI" not in hb and ".csv" not in hb)
check("the heartbeat shows the public key and never the secret",
      GOT["beats"][-1]["direct_upload"]["public_key"] == p1 and key_text.strip() not in hb)

GOT["mode"] = "401"
put(os.path.join(ex6, "consultation_report_2031-01-08.csv"), CONS.replace("07-01", "08-01"), age=60)
st6c = m6.new_state()
for _ in range(3):
    m6.direct_pass(st6c, cfg6, m6.build_beat(st6c, cfg6)[0])
b401, _ = m6.build_beat(st6c, cfg6)
check("a server that refuses: no report is tried, and after three times the heartbeat asks for attention",
      len(GOT["reports"]) == 3 and st6c["upload"]["fail_streak"] == 3
      and any("direct upload" in a for a in b401["attention"]), b401["attention"])
GOT["mode"] = "login"
st6d = m6.new_state(); m6.direct_pass(st6d, cfg6, m6.build_beat(st6d, cfg6)[0])
check("a login page is not taken for an answer (redirect not followed)",
      st6d["upload"]["ok_at"] is None and "302" in (st6d["upload"]["last_error"] or ""), st6d["upload"])
GOT["mode"] = "ok"
m6.direct_pass(st6c, cfg6, m6.build_beat(st6c, cfg6)[0])
b_ok, _ = m6.build_beat(st6c, cfg6)
check("when the server answers again the count clears, the waiting report goes, the attention line leaves",
      st6c["upload"]["fail_streak"] == 0 and len(GOT["reports"]) == 4
      and not any("direct upload" in a for a in b_ok["attention"]))
import contextlib as _cl
import io as _io
buf = _io.StringIO()
with _cl.redirect_stdout(buf):
    rc_bad = m6.enroll("WRONG")
check("--enroll with a code the server does not know: says so, exit 1, nothing enrolled",
      rc_bad == 1 and "did not take" in buf.getvalue() and "enrolled" not in GOT, buf.getvalue())
buf = _io.StringIO(); nb = len(GOT["beats"])
with _cl.redirect_stdout(buf):
    rc_ok = m6.enroll("GOODCODE")
check("--enroll with the page's code: the PUBLIC key goes up, then one signed heartbeat is accepted",
      rc_ok == 0 and GOT.get("enrolled", {}).get("pc_key") == p1 and len(GOT["beats"]) == nb + 1
      and key_text.strip() not in json.dumps(GOT["enrolled"]), (rc_ok, buf.getvalue()))
check("the heartbeat carries the two facts the Clinic PCs page ticks (None off Windows, never a guess)",
      set(GOT["beats"][-1]["owner_view"]) == {"tailscale_running", "share_ready"}
      and GOT["beats"][-1]["owner_view"]["share_ready"] is None)
import types as _ty


class _FakeKey:
    def __init__(self, names): self.names = names
    def __enter__(self): return self
    def __exit__(self, *a): return False


def _fake_winreg(names, broken=False):
    w = _ty.ModuleType("winreg"); w.HKEY_LOCAL_MACHINE = object(); asked = []
    def OpenKey(root, path):
        if broken:
            raise PermissionError("no")
        asked.append(path); return _FakeKey(names)
    def QueryValueEx(k, name):
        if name not in k.names:
            raise FileNotFoundError(name)
        return (["Path=C:\\"], 7)
    w.OpenKey, w.QueryValueEx, w.asked = OpenKey, QueryValueEx, asked
    return w


m6.IS_WIN = True
sys.modules["winreg"] = _fake_winreg(["print$", "ReceptionC"])
check("on Windows the share is read from the registry's own list of shares (no command, no administrator rights)",
      m6.share_ready("ReceptionC") is True and "LanmanServer" in sys.modules["winreg"].asked[-1])
sys.modules["winreg"] = _fake_winreg(["print$"])
check("...a missing share reads False, and a name that is not a share name is never looked up",
      m6.share_ready("ReceptionC") is False and m6.share_ready("x & del") is None)
sys.modules["winreg"] = _fake_winreg([], broken=True)
check("...and when the registry cannot be read the answer is None, never a guess", m6.share_ready("ReceptionC") is None)
del sys.modules["winreg"]
m6.IS_WIN = False
srv.shutdown()
cfg_off = dict(cfg6, direct_upload=False)
n_before = len(GOT["beats"])
m6.direct_pass(m6.new_state(), cfg_off, beat6)
check("direct_upload false in config.json: nothing is sent", len(GOT["beats"]) == n_before)
m6.process_names = lambda: {"chrome.exe": [1]}
bq3, _ = m6.build_beat(m6.new_state(), dict(cfg6, keep_claude_running=False))
check("with keep_claude_running false a missing Claude app is not an attention line",
      bq3["claude_app_running"] is False and not any("Claude" in a for a in bq3["attention"]), bq3["attention"])
bq4, _ = m6.build_beat(m6.new_state(), cfg6)
check("...and with it true (the default) it still is",
      any("Claude" in a for a in bq4["attention"]), bq4["attention"])
check("the text heartbeat has the SERVER and VIEW lines", "SERVER  : direct upload on" in m6.human(b_ok) and "VIEW    : Tailscale running" in m6.human(b_ok))


# ---------------------------------------------------------------------------
# 7. S453 -- the second job door: the server relays, this PC decides
# ---------------------------------------------------------------------------
import base64 as _b64
import datetime as _dt
root7 = fresh_root()
m7 = load(root7)
os.environ["USERPROFILE"] = os.path.join(root7, "home"); os.makedirs(os.path.join(root7, "home", "Downloads"))
m7.find_my_drive = lambda: None
m7.ensure_dirs()
sk7 = bytes(range(7, 39)); pk7 = m7.ed_public(sk7).hex()
p7 = m7.upload_public()
Q = {"offer": None, "acks": [], "results": [], "asked": 0, "mode": "ok"}


class H7(_hs.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        kind = {"next": "jobs-next", "ack": "jobs-ack", "result": "job-result", "heartbeat": "heartbeat"}[self.path.rsplit("/", 1)[1]]
        name = self.headers.get("X-Rx-Name") or ""
        good = m7.ed_verify(bytes.fromhex(p7), m7.upload_message(kind, self.headers.get("X-Rx-Time"), name,
                            self.headers.get("X-Rx-Mtime") or "", body), bytes.fromhex(self.headers.get("X-Rx-Sig") or ""))
        if Q["mode"] == "401" or not good:
            out, code = {"ok": False, "status": "NOT_YOU", "message": "bad signature"}, 401
        elif kind == "jobs-next":
            Q["asked"] += 1
            out, code = (dict(Q["offer"], ok=True, status="JOB") if Q["offer"] else {"ok": True, "status": "NONE"}), 200
        elif kind == "jobs-ack":
            Q["acks"].append((name, body.decode()))
            if Q["offer"] and Q["offer"]["name"] == name and not Q.get("deaf"):
                Q["offer"] = None
            out, code = {"ok": True, "status": "NOTED"}, 200
        elif kind == "job-result":
            Q["results"].append((name, body.decode("utf-8", "replace"))); out, code = {"ok": True, "status": "KEPT"}, 200
        else:
            out, code = {"ok": True, "status": "KEPT"}, 200
        raw = json.dumps(out).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)


srv7 = _hs.HTTPServer(("127.0.0.1", 0), H7)
_th.Thread(target=srv7.serve_forever, daemon=True).start()
json.dump({"server_url": "http://127.0.0.1:%d" % srv7.server_address[1], "job_timeout_default": 30}, open(os.path.join(root7, "config.json"), "w"))
cfg7 = m7.load_config()
st7 = m7.new_state()


def offer(tail, text, key=sk7, hours_ago=0.0, sign_text=None, b64=None):
    name = (m7.now() - _dt.timedelta(hours=hours_ago)).strftime("%Y%m%dT%H%M%S_") + tail
    content = text.encode()
    sig = m7.ed_sign(key, m7.job_message(name, (sign_text if sign_text is not None else text).encode()))
    Q["offer"] = {"name": name, "job": b64 if b64 is not None else _b64.b64encode(content).decode(), "sig": sig.hex()}
    return name


def queued():
    return sorted(n for n in os.listdir(m7.JOBS_IN) if not n.endswith(".tmp"))


check("S453: the defaults switch the server door on, once a minute", cfg7["server_jobs"] is True and cfg7["server_jobs_seconds"] == 60)
n1 = offer("a1.py", "print('never run')\n")
m7.poll_server_jobs(st7, cfg7)
check("S453: with no key enrolled the server is not even asked, whatever it offers", Q["asked"] == 0 and queued() == [])
put(m7.KEYS_FILE, "# test\n%s  parent-test\n" % pk7)
Q["offer"] = None
m7.poll_server_jobs(st7, cfg7)
check("S453: the server is asked, signed with this PC's own key; nothing waiting, nothing queued",
      Q["asked"] == 1 and queued() == [] and st7["server_jobs"]["ok_at"] and st7["server_jobs"]["last_error"] is None)
n2 = offer("hello.py", "print('hello from the server door')\n")
m7.poll_server_jobs(st7, cfg7)
check("S453: a job signed with an enrolled key is queued byte for byte, acknowledged 'taken', and its name recorded as used",
      queued() == ["server__" + n2] and open(os.path.join(m7.JOBS_IN, "server__" + n2)).read() == "print('hello from the server door')\n"
      and Q["acks"][-1] == (n2, "taken") and Q["offer"] is None and m7._seen_read()[n2].get("road") == "server", (queued(), Q["acks"]))
check("S453: it runs like any other job", wait_job(m7, st7, cfg7) and st7["last_job"]["name"] == "server__" + n2 and st7["last_job"]["exit"] == 0, st7.get("last_job"))
check("S453: its result is remembered ON DISK until the server has it", st7["server_results"] == ["server__" + n2]
      and json.load(open(m7.SERVER_RESULTS_FILE)) == ["server__" + n2] and m7.new_state()["server_results"] == ["server__" + n2])
Q["mode"] = "401"
m7.poll_server_jobs(st7, cfg7)
check("S453: a server that does not answer: the result stays waiting, nothing raises, the heartbeat says so",
      st7["server_results"] == ["server__" + n2] and Q["results"] == [] and st7["server_jobs"]["last_error"]
      and m7.build_beat(st7, cfg7)[0]["server_jobs"]["results_waiting"] == 1)
Q["mode"] = "ok"
m7.poll_server_jobs(st7, cfg7)
check("S453: when it answers again the result goes back under the job's own name, once",
      len(Q["results"]) == 1 and Q["results"][0][0] == n2 and "hello from the server door" in Q["results"][0][1] and "EXIT: 0" in Q["results"][0][1]
      and st7["server_results"] == [] and json.load(open(m7.SERVER_RESULTS_FILE)) == [], Q["results"])
m7.poll_server_jobs(st7, cfg7)
check("...and is not sent twice", len(Q["results"]) == 1)
Q["offer"] = {"name": n2, "job": _b64.b64encode(b"print('hello from the server door')\n").decode(), "sig": "00" * 64}
a_before = len(Q["acks"])
m7.poll_server_jobs(st7, cfg7)
check("S453: the same job offered again (the server lost the acknowledgement): NOT run again, acknowledged again",
      queued() == [] and len(Q["acks"]) == a_before + 1 and Q["acks"][-1] == (n2, "taken"))
for label, kw, want in (
        ("a key that is not enrolled", dict(key=bytes(range(9, 41))), "does not match an enrolled key"),
        ("a job changed after it was signed", dict(sign_text="print('something else')\n"), "does not match an enrolled key"),
        ("a job signed 50 hours ago", dict(hours_ago=50), "more than 48 hours ago"),
        ("a job that did not arrive whole", dict(b64="not base64 !!"), "did not arrive whole")):
    r_before = st7["drive_refused"]
    nx = offer("bad%d.py" % r_before, "print('must never run')\n", **kw)
    m7.poll_server_jobs(st7, cfg7)
    check("S453: %s is REFUSED -- never queued, the server told why, the name never read again" % label,
          queued() == [] and Q["acks"][-1][0] == nx and want in Q["acks"][-1][1] and st7["drive_refused"] == r_before + 1
          and m7._seen_read()[nx]["refused"], Q["acks"][-1])
big = "x = 1\n" * 180000
nb = offer("big.py", big)
m7.poll_server_jobs(st7, cfg7)
check("S453: a job over 1 MB is refused", queued() == [] and "larger than 1 MB" in Q["acks"][-1][1])
seen7 = m7._seen_read(); nd = (m7.now()).strftime("%Y%m%dT%H%M%S_") + "twice.py"
seen7[nd] = {"at": m7.iso(), "sha256": "x", "refused": None}; m7._seen_write(seen7)
Q["offer"] = {"name": nd, "job": _b64.b64encode(b"print(1)\n").decode(), "sig": m7.ed_sign(sk7, m7.job_message(nd, b"print(1)\n")).hex()}
m7.poll_server_jobs(st7, cfg7)
check("S453: a job the Drive door already took is not run a second time through the server", queued() == [] and Q["acks"][-1] == (nd, "taken"))
Q["offer"] = {"name": "../../evil.py", "job": "", "sig": ""}
a_before = len(Q["acks"])
m7.poll_server_jobs(st7, cfg7); m7.poll_server_jobs(st7, cfg7)
check("S453: a name that is not a job name is ignored outright (no file, no acknowledgement, said once in the log)",
      queued() == [] and len(Q["acks"]) == a_before and open(m7.AGENT_LOG).read().count("SERVER JOB IGNORED") == 1)
Q["offer"] = None
asked = Q["asked"]
m7.poll_server_jobs(st7, dict(cfg7, server_jobs=False)); m7.poll_server_jobs(st7, dict(cfg7, direct_upload=False))
check("S453: server_jobs false, or direct_upload false, in config.json: the server is not asked", Q["asked"] == asked)
n3 = offer("deaf.cmd" if os.name == "nt" else "deaf.py", "print('once')\n")
Q["deaf"] = True
m7.poll_server_jobs(st7, cfg7); wait_job(m7, st7, cfg7); m7.poll_server_jobs(st7, cfg7); m7.poll_server_jobs(st7, cfg7)
check("S453: a server that keeps offering a job it was told is taken: the job still runs exactly once",
      st7["jobs_done"] == 2 and [r[0] for r in Q["results"]].count(n3) == 1, (st7["jobs_done"], [r[0] for r in Q["results"]]))
Q["deaf"] = False; Q["offer"] = None
srv7.shutdown(); srv7.server_close()
m7.poll_server_jobs(st7, cfg7)
check("S453: the server gone altogether: no error raised, the heartbeat carries the reason",
      st7["server_jobs"]["last_error"] and "server_jobs" in m7.build_beat(st7, cfg7)[0])
b7, _ = m7.build_beat(st7, cfg7)
check("S453: the heartbeat's server_jobs block holds counts and times only", set(b7["server_jobs"]) == {"enabled", "last_answer", "taken_since_start", "results_waiting", "last_error"}
      and b7["server_jobs"]["taken_since_start"] == 2 and "SERVER JOBS: on" in m7.human(b7))
tool7 = fresh_root(); shutil.copy(os.path.join(KIT, "reception_sign.py"), tool7)
kf7 = os.path.join(tool7, "k.txt"); open(kf7, "w").write(sk7.hex() + "\n")
tk = subprocess.run([sys.executable, os.path.join(tool7, "reception_sign.py"), "read-token", kf7, n2], capture_output=True, text=True)
try:
    tj = json.loads(tk.stdout)
except ValueError:
    tj = {}
check("S453: the signing tool's read-token is the job's name, the time and a signature over exactly those",
      tk.returncode == 0 and tj.get("name") == n2 and abs(int(tj.get("ts", 0)) - time.time()) < 30
      and m7.ed_verify(bytes.fromhex(pk7), b"clinic-reception-job-read-v1\n" + n2.encode() + b"\n" + tj["ts"].encode(), bytes.fromhex(tj["sig"])), tk.stdout + tk.stderr)
check("...and it refuses a name that is not a stamped job name", subprocess.run([sys.executable, os.path.join(tool7, "reception_sign.py"), "read-token", kf7, "x.py"], capture_output=True).returncode == 2)

# ---- S456 (F-700): how current Windows is ------------------------------------------------------------------------------
root8 = fresh_root()
m8 = load(root8)


def _ft(y, mo, d):
    n = int((m8.dt.datetime(y, mo, d, 6, 30) - m8.dt.datetime(1601, 1, 1)).total_seconds() * 10 ** 7)
    return n >> 32, n & 0xFFFFFFFF


_cv10 = {"ProductName": "Windows 10 Home", "DisplayVersion": "22H2", "CurrentBuild": "19045", "UBR": 6466}
_rf = "Package_for_RollupFix~31bf3856ad364e35~amd64~~19041.%s.1.9"
w8 = m8.windows_facts(_cv10, [(_rf % "6466", 112) + _ft(2025, 11, 12), (_rf % "6332", 80) + _ft(2025, 10, 15),
                              (_rf % "7000", 112) + _ft(2026, 9, 16)], 1761000000)
check("S456: build, release and product are read as Windows states them",
      w8["product"] == "Windows 10 Home" and w8["release"] == "22H2" and w8["build"] == "19045.6466", w8)
check("S456: the update that counts is the one whose number IS this build, not a later-dated package",
      w8["update_installed"] == "2025-11-12" and w8["update_is_this_build"] is True, w8)
check("S456: the system files' date is a date", w8["system_files_dated"] == "2025-10-20", w8)
w8b = m8.windows_facts(_cv10, [(_rf % "6332", 112) + _ft(2025, 10, 15), (_rf % "6466", 80) + _ft(2025, 11, 12)], None)
check("S456: no installed package for this build -> the newest installed one, and it says it is not this build",
      w8b["update_installed"] == "2025-10-15" and w8b["update_is_this_build"] is False and w8b["system_files_dated"] is None, w8b)
w8c = m8.windows_facts({"ProductName": "Windows 10 Pro", "DisplayVersion": "24H2", "CurrentBuild": "26100", "UBR": 4061}, [], None)
check("S456: Windows 11 is called 11 (its registry still says 10)", w8c["product"] == "Windows 11 Pro" and w8c["update_installed"] is None
      and w8c["update_is_this_build"] is None, w8c)
w8d = m8.windows_facts(None, [("x", 112, None, None), 7, ("a~b", 112, "z", 1), (_rf % "1", 112, -5, 0)], "junk")
check("S456: junk in, nothing raised, every value None", all(v is None for v in w8d.values()), w8d)
check("S456: a nonsense date is refused, not printed", m8._filetime_date(0, 0) is None and m8._filetime_date(2 ** 40, 0) is None)
m8.IS_WIN = False
check("S456: off Windows the reading is None and nothing is called", m8.windows_state(force=True) is None)
calls8 = []
m8.IS_WIN = True
m8._read_windows_raw = lambda: (calls8.append(1), (_cv10, [(_rf % "6466", 112) + _ft(2025, 11, 12)], 1761000000))[1]
a8 = m8.windows_state(force=True)
b8 = m8.windows_state()
check("S456: read once and kept -- the second heartbeat does not read the registry again", a8 is b8 and calls8 == [1] and a8["build"] == "19045.6466", calls8)
m8._WIN_CACHE["at"] = time.time() - m8.WIN_EVERY - 5
m8.windows_state()
check("S456: ...and read again after six hours", calls8 == [1, 1], calls8)


def _boom():
    raise OSError("registry closed")


m8._read_windows_raw = _boom
check("S456: a read that raises is None, not a crash", m8.windows_state(force=True) is None)
m8._read_windows_raw = lambda: (_cv10, [(_rf % "6466", 112) + _ft(2025, 11, 12)], 1761000000)
m8.IS_WIN = False                      # the rest of build_beat must run as on this machine
m8._WIN_CACHE["value"], m8._WIN_CACHE["at"] = m8.windows_facts(*m8._read_windows_raw()), time.time()
m8.ensure_dirs()
beat8, _ = m8.build_beat(m8.new_state(), m8.load_config())
txt8 = m8.human(beat8)
check("S456: the heartbeat carries the reading and the text file says it in one line",
      beat8["windows"]["build"] == "19045.6466"
      and "WINDOWS : Windows 10 Home 22H2 build 19045.6466 | system files dated 2025-10-20 | last cumulative update installed 2025-11-12" in txt8, txt8)
check("S456: the reading holds six plain values and no path, user or file name",
      sorted(beat8["windows"]) == ["build", "product", "release", "system_files_dated", "update_installed", "update_is_this_build"])
m8._WIN_CACHE["value"] = None
check("S456: a PC whose Windows could not be read says 'not read'", "WINDOWS : not read" in m8.human(m8.build_beat(m8.new_state(), m8.load_config())[0]))


print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
for f in FAIL:
    print("   FAILED: " + f)
sys.exit(1 if FAIL else 0)
