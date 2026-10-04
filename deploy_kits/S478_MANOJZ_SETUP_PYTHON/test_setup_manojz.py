#!/usr/bin/env python3
"""Offline walk of the manojz kit: pc_state_backup.py makes the state zip, setup_pc.py restores from it."""
import contextlib, hashlib, importlib.util, io, os, shutil, sys, tempfile, time, zipfile

KIT, PASS, FAIL = os.path.abspath(sys.argv[1]), [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("%s  %s%s" % ("ok  " if cond else "FAIL", name, ("  -- " + str(detail)[:400]) if (detail and not cond) else ""))


def load(path, tag):
    spec = importlib.util.spec_from_file_location(tag, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def put(path, text="x"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)


def tree(d):
    out = {}
    for r, _d, names in os.walk(d):
        for n in names:
            p = os.path.join(r, n)
            out[os.path.relpath(p, d)] = (hashlib.md5(open(p, "rb").read()).hexdigest(), os.path.getmtime(p))
    return out


tmp = tempfile.mkdtemp(prefix="s459_")
# ---- a stand-in for the working PC ----
live_c, live_d = os.path.join(tmp, "liveC"), os.path.join(tmp, "liveD")
trk = os.path.join(live_c, "followup_tracker_local_test_kit", "local_test_kit", "followup_tracker")
put(os.path.join(trk, "app.py"), "tracker"); put(os.path.join(trk, "data", "ledger.csv"), "ledger"); put(os.path.join(trk, "__pycache__", "a.pyc"))
put(os.path.join(trk, "fu_upload.env"), "SECRET=stand-in")
ms = os.path.join(live_d, "Downloads", "margsync")
put(os.path.join(ms, "_config", "machine.conf"), "conf"); put(os.path.join(ms, "MargPull", "pull.py"), "pull"); put(os.path.join(ms, "MargPull", "_logs", "big.log"), "log")
put(os.path.join(ms, "_off", "ALL_OFF.txt"), "off for a day"); put(os.path.join(ms, "_off", "READ_ME.txt"), "read me")
put(os.path.join(ms, "PUSH_STOCK_NIGHTLY.bat"), "bat"); put(os.path.join(ms, "MargArchive", "huge.xls"), "not taken")
put(os.path.join(live_d, "Downloads", "DocterzArchive", "_last_pass.txt"), "END ok")
put(os.path.join(live_d, "Downloads", "_kbtools", "NIGHTLY.bat"), "nightly"); put(os.path.join(live_d, "Downloads", "_kbtools", "vps_code", "x.tar.gz"), "not taken")
ssd = os.path.join(tmp, "ssd", "05_PC_STATE", "manojz")
B = load(os.path.join(KIT, "pc_state_backup.py"), "pcb")
src = ["tracker=" + trk, "margsync_config=" + os.path.join(ms, "_config"), "margsync_MargPull=" + os.path.join(ms, "MargPull"),
       "margsync_off=" + os.path.join(ms, "_off"), "margsync_top=" + ms, "DocterzArchive=" + os.path.join(live_d, "Downloads", "DocterzArchive"),
       "kbtools=" + os.path.join(live_d, "Downloads", "_kbtools"), "clinic_writer=" + os.path.join(live_d, "clinic_writer")]
args = ["--tools", os.path.join(live_d, "Downloads", "_kbtools"), "--dest", ssd, "--no-tasks"]
for s in src:
    args += ["--source", s]
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = B.main(args)
rep = buf.getvalue()
zs = [n for n in os.listdir(ssd) if n.endswith(".zip")]
names = zipfile.ZipFile(os.path.join(ssd, zs[0])).namelist() if zs else []
check("backup: one dated zip on the SSD, reopened and proven", len(zs) == 1 and "every CRC tested" in rep, rep)
check("backup: the tracker with its ledger and its settings file, the pull, the settings, the switches, the loose files", all(x in names for x in (
    "tracker/app.py", "tracker/data/ledger.csv", "tracker/fu_upload.env", "margsync_config/machine.conf", "margsync_MargPull/pull.py",
    "margsync_off/ALL_OFF.txt", "margsync_top/PUSH_STOCK_NIGHTLY.bat", "DocterzArchive/_last_pass.txt", "kbtools/NIGHTLY.bat")), names)
check("backup: not the pull's logs, not the server bundles, not the Marg archive, no compiled files", not any(
    ("_logs/" in n or "vps_code" in n or "MargArchive" in n or n.endswith(".pyc") or "/" in n[len("margsync_top/"):] and n.startswith("margsync_top/")) for n in names), names)
check("backup: a folder that is not there is SAID and the verdict is WARN, not OK", "clinic_writer" in rep and "NOT THERE" in rep and rc == 2, rep)
check("backup: the report holds counts and sizes -- no file name of the tracker's", "ledger.csv" not in rep and "fu_upload" not in rep, rep)
check("backup: its report is written beside the tools", os.path.isfile(os.path.join(live_d, "Downloads", "_kbtools", "PC_STATE_BACKUP_LATEST.txt")))
for i in range(1, 10):
    shutil.copy(os.path.join(ssd, zs[0]), os.path.join(ssd, "manojz_state_2026-09-%02d.zip" % i))
with contextlib.redirect_stdout(io.StringIO()):
    B.main(args)
left = sorted(n for n in os.listdir(ssd) if n.endswith(".zip"))
check("backup: the newest 7 stay, older ones are MOVED aside, none deleted", len(left) == 7 and len(os.listdir(os.path.join(ssd, "99_SUPERSEDED"))) == 3, (left, os.listdir(ssd)))
with contextlib.redirect_stdout(io.StringIO()):
    rc = B.main(["--tools", os.path.join(tmp, "t2"), "--dest", os.path.join(live_d, "Downloads", "_kbtools", "NIGHTLY.bat", "sub"), "--no-tasks", "--source", "tracker=" + trk])
check("backup: an SSD that is not reachable is FAIL (exit 3), not a quiet pass", rc == 3, rc)

# ---- add what only Windows can give: the task definitions and the machine facts ----
state = os.path.join(ssd, sorted(n for n in os.listdir(ssd) if n.endswith(".zip"))[-1])
def task(cmd, uid="S-1-5-21-111-222-333-1001"):
    return ('<?xml version="1.0" encoding="UTF-16"?><Task><Principals><Principal id="Author"><UserId>%s</UserId></Principal></Principals>'
            '<Actions><Exec><Command>%s</Command></Exec></Actions></Task>' % (uid, cmd)).encode("utf-16")
with zipfile.ZipFile(state, "a") as z:
    z.writestr("tasks/KB Manifest Rebuild.xml", task(r"D:\Downloads\_kbtools\NIGHTLY.bat"))
    z.writestr("tasks/DocterzPickup.xml", task(r'wscript.exe "C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\RUN_HIDDEN.vbs"'))
    z.writestr("tasks/MargPushEvery30.xml", task(r"D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S240_SANJEEVNI_PC\PUSH_MARG_EVERY_30.bat"))
    z.writestr("tasks/GoogleUpdaterTask.xml", task(r"C:\Program Files\Google\updater.exe"))
    z.writestr("tasks/../evil.xml", task(r"D:\Downloads\x.bat"))
    z.writestr("tracker/../../escape.txt", "must never be written")
    z.writestr("MACHINE_FACTS.txt", "MACHINE FACTS\n== PYTHON PACKAGES (python -m pip freeze) ==\n   flask==3.1.3\n   pandas==2.3.0\n   requests==2.32.0\n\n== GIT ==\n   git version 2.50\n")
mir = os.path.join(tmp, "ssd", "01_KB_MIRRORS"); os.makedirs(mir)
with zipfile.ZipFile(os.path.join(mir, "KB_mirror_ClaudeCowork_nightly_2026-10-03.zip"), "w") as z:
    z.writestr("00_INDEX.md", "index"); z.writestr("03_WORKING_PAPERS/S292/x.md", "paper")
kit = os.path.join(tmp, "kit"); os.makedirs(kit)
for n in ("setup_pc.py", "README_REINSTALL_MANOJZ.txt"):
    shutil.copy(os.path.join(KIT, n), kit)
with open(os.path.join(kit, "MD5SUMS.txt"), "w") as fh:
    for n in ("README_REINSTALL_MANOJZ.txt", "setup_pc.py"):
        fh.write("%s  %s\n" % (hashlib.md5(open(os.path.join(kit, n), "rb").read()).hexdigest(), n))


def setup(c, d, state_dir=ssd, have_tasks=(), pip_have="", python=True, create_rc=0, kitdir=kit):
    os.environ.update({"CLINIC_SETUP_C": c, "CLINIC_SETUP_D": d, "CLINIC_SETUP_STATE": state_dir, "CLINIC_SETUP_MIRRORS": mir,
                       "USERDOMAIN": "MANOJZ", "USERNAME": "Dr Manoj Agarwal"})
    S = load(os.path.join(kitdir, "setup_pc.py"), "s%d" % len(PASS))
    calls = []

    def fake(cmd, timeout=120):
        calls.append(list(cmd))
        if cmd[:2] == ["schtasks", "/Query"]:
            return (0 if cmd[3] in have_tasks else 1), ""
        if cmd[:2] == ["schtasks", "/Create"]:
            calls[-1].append(open(cmd[5], "rb").read().decode("utf-16"))
            return create_rc, ""
        if cmd[1:4] == ["-m", "pip", "freeze"]:
            return (0, pip_have) if python else (9009, "not recognized")
        if cmd[1:4] == ["-m", "pip", "install"]:
            return 0, "ok"
        if cmd[0] == "cmdkey":
            return 0, "Target: Domain:target=100.119.151.40" if have_tasks else "none"
        return (0, "ok") if have_tasks else (1, "")
    S.run = fake
    S.system_python = (lambda: "X:\\Python\\python.exe") if python else (lambda: "")     # S459.2: the PC's own Python, by full path
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = S.main(["--kit", kitdir])
    return rc, buf.getvalue(), calls


# 1. A FRESH PC
fc, fd = os.path.join(tmp, "freshC"), os.path.join(tmp, "freshD"); os.makedirs(fc); os.makedirs(fd)
rc, out, calls = setup(fc, fd)
ftrk = os.path.join(fc, "followup_tracker_local_test_kit", "local_test_kit", "followup_tracker")
check("fresh PC: ends DONE", rc == 0 and "DONE." in out, out[-600:])
check("...the tracker is back with its ledger and its settings file", open(os.path.join(ftrk, "data", "ledger.csv")).read() == "ledger" and os.path.isfile(os.path.join(ftrk, "fu_upload.env")), out)
check("...the Marg pull, its settings, its switches as they stood, its loose files, the nightly tools, the Docterz archive", all(os.path.isfile(os.path.join(fd, "Downloads", *p)) for p in (
    ("margsync", "_config", "machine.conf"), ("margsync", "MargPull", "pull.py"), ("margsync", "_off", "ALL_OFF.txt"), ("margsync", "PUSH_STOCK_NIGHTLY.bat"),
    ("_kbtools", "NIGHTLY.bat"), ("DocterzArchive", "_last_pass.txt"))), out)
check("...the knowledge base comes back from the newest nightly mirror", os.path.isfile(os.path.join(fd, "Downloads", "ClaudeCowork", "03_WORKING_PAPERS", "S292", "x.md")) and "RESTORED, 2 file(s)" in out, out)
made = [c for c in calls if c[:2] == ["schtasks", "/Create"]]
check("...the clinic's three tasks are made again; Windows' own task is not touched", sorted(c[3] for c in made) == ["DocterzPickup", "KB Manifest Rebuild", "MargPushEvery30"]
      and "1 of Windows' own not touched" in out, [c[:4] for c in made])
check("...each task is made for THIS account, not the old account's id", all("<UserId>MANOJZ\\Dr Manoj Agarwal</UserId>" in c[-1] and "S-1-5-21" not in c[-1] for c in made))
inst = [c for c in calls if c[1:4] == ["-m", "pip", "install"]]
check("...the missing Python packages are installed, by name and version", len(inst) == 1 and inst[0][-3:] == ["flask==3.1.3", "pandas==2.3.0", "requests==2.32.0"], inst)
check("...and pip is asked through the PC's own Python by its full path, never the bare name (S459.2)",
      inst[0][0] == "X:\\Python\\python.exe" and not [c for c in calls if c and c[0] == "python"], [c[:4] for c in calls if "pip" in c])
check("...a file that tries to leave its folder is never written", not os.path.exists(os.path.join(tmp, "escape.txt")) and not os.path.exists(os.path.join(fc, "escape.txt"))
      and not any("evil" in c[3] for c in made))
check("...what only a person can do is listed unticked", "[ ] Git for Windows" in out and "[ ] Tailscale" in out, out)
check("...nothing is left in the kit folder", sorted(os.listdir(kit)) == ["MD5SUMS.txt", "README_REINSTALL_MANOJZ.txt", "setup_pc.py"], os.listdir(kit))

# 2. THE WORKING PC -- a read-only check
os.remove(os.path.join(ms, "_off", "ALL_OFF.txt"))            # the switch was put back ON since the backup
put(os.path.join(live_d, "Downloads", "ClaudeCowork", "00_INDEX.md"), "today's index")
before_c, before_d = tree(live_c), tree(live_d)
time.sleep(1.1)
rc, out, calls = setup(live_c, live_d, have_tasks=("DocterzPickup", "KB Manifest Rebuild", "MargPushEvery30"), pip_have="Flask==3.1.3\npandas==2.3.0\nrequests==2.32.0\nnumpy==2.0\n")
check("working PC: DONE, and NOT ONE FILE on it was written", rc == 0 and tree(live_c) == before_c and tree(live_d) == before_d, out)
check("...the switch that was turned back on since the backup is NOT put back off", not os.path.exists(os.path.join(ms, "_off", "ALL_OFF.txt")))
check("...every folder 'already here', the knowledge base left alone", out.count("already here, left alone") >= 7 and "RESTORED" not in out, out)
check("...no task is made, no package installed", not [c for c in calls if c[:2] == ["schtasks", "/Create"] or c[1:4] == ["-m", "pip", "install"]]
      and "3 already there, 0 made again" in out and "all 3 already here" in out, out)
check("...and what this PC has is ticked", "[x] Git for Windows" in out and "[x] Tailscale signed in" in out and "[x] the Medical PC's share login" in out, out)
check("...clinic_writer, in neither the PC nor the zip, is said", "clinic_writer" in out and "not in the state zip" in out, out)

# 3. the edges
c3, d3 = os.path.join(tmp, "c3"), os.path.join(tmp, "d3"); os.makedirs(c3); os.makedirs(d3)
rc, out, calls = setup(c3, d3, state_dir=os.path.join(tmp, "no_ssd"))
check("no SSD: STOP, and nothing is restored", rc == 1 and "plug in the ClinicBackup SSD" in out and os.listdir(c3) == [] and os.listdir(d3) == [], out)
badssd = os.path.join(tmp, "badssd"); os.makedirs(badssd); open(os.path.join(badssd, "manojz_state_2026-10-03.zip"), "wb").write(b"not a zip")
rc, out, calls = setup(c3, d3, state_dir=badssd)
check("a state zip that does not read back: STOP, nothing restored", rc == 1 and "does not read back whole" in out and os.listdir(c3) == [], out)
rc, out, calls = setup(c3, d3, create_rc=1)
check("tasks Windows refuses: said, with what to do (run once as administrator)", rc == 0 and "3 could not be made" in out and "Run as administrator" in out, out)
c4, d4 = os.path.join(tmp, "c4"), os.path.join(tmp, "d4"); os.makedirs(c4); os.makedirs(d4)
rc, out, calls = setup(c4, d4, python=False)
check("no Python on the PC: the folders still come back; Python is named as the person's step", rc == 0 and "no Python on its PATH" in out and os.path.isdir(os.path.join(d4, "Downloads", "_kbtools")), out)
badkit = os.path.join(tmp, "badkit"); shutil.copytree(kit, badkit); open(os.path.join(badkit, "setup_pc.py"), "a").write("\n# x\n")
c5, d5 = os.path.join(tmp, "c5"), os.path.join(tmp, "d5"); os.makedirs(c5); os.makedirs(d5)
rc, out, calls = setup(c5, d5, kitdir=badkit)
check("a tampered kit: STOP before anything", rc == 1 and "kit is not whole" in out and os.listdir(d5) == [], out)

shutil.rmtree(tmp, ignore_errors=True)
# 5. S459.2 -- the PC's own Python is found on the PATH, this program's own folder left out
S = load(os.path.join(KIT, "setup_pc.py"), "sp_unit")
exe = "python.exe" if S.IS_WIN else "python3"
tmp2 = tempfile.mkdtemp(prefix="s478_")
own, other, store = os.path.join(tmp2, "p_own"), os.path.join(tmp2, "p_other"), os.path.join(tmp2, "p_store", "Microsoft", "WindowsApps")
for d in (own, other, store):
    put(os.path.join(d, exe), "stand-in")
_exe0, _path0 = sys.executable, os.environ.get("PATH", "")
try:
    sys.executable = os.path.join(own, exe)
    os.environ["PATH"] = os.pathsep.join([own, other])
    check("S459.2: with its own folder first on the PATH, the OTHER Python is the one found", S.system_python() == os.path.join(other, exe), S.system_python())
    os.environ["PATH"] = own
    check("S459.2: with only its own folder on the PATH, none is found (the kit's Python is never taken for the PC's)", S.system_python() == "", S.system_python())
    os.environ["PATH"] = os.pathsep.join([store, own])
    check("S459.2: the Store's stand-in is taken when nothing else is there", S.system_python() == os.path.join(store, exe), S.system_python())
    os.environ["PATH"] = os.pathsep.join([store, '"%s"' % other, "", own])
    check("S459.2: a real Python wins over the Store's stand-in, quotes and empty PATH entries tolerated", S.system_python() == os.path.join(other, exe), S.system_python())
    os.environ["PATH"] = ""
    check("S459.2: an empty PATH is answered, not raised", S.system_python() == "")
finally:
    sys.executable, os.environ["PATH"] = _exe0, _path0
    shutil.rmtree(tmp2, ignore_errors=True)

print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
for f in FAIL:
    print("   FAILED: " + f)
sys.exit(1 if FAIL else 0)
