#!/usr/bin/env python3
"""Offline walk of setup_pc.py (S458) on a scratch folder -- the fill-what-is-missing rule above all."""
import hashlib, importlib.util, io, os, shutil, sys, tempfile, time, zipfile, contextlib

KITZIP, PASS, FAIL = sys.argv[1], [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("%s  %s%s" % ("ok  " if cond else "FAIL", name, ("  -- " + str(detail)[:300]) if (detail and not cond) else ""))


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


tmp = tempfile.mkdtemp(prefix="s458_")
kit = os.path.join(tmp, "kit")
zipfile.ZipFile(KITZIP).extractall(kit)
pyzip = os.path.join(tmp, "pyportable.zip")
with zipfile.ZipFile(pyzip, "w") as z:
    for n in ("pyportable/python.exe", "pyportable/pythonw.exe", "pyportable/Lib/os.py"):
        z.writestr(n, "stand-in " + n)


def run(target, *args, allusers=None, mine=None):
    os.environ["CLINIC_SETUP_TARGET"] = target
    os.environ["CLINIC_SETUP_ALLUSERS"] = allusers or os.path.join(tmp, "allusers_" + os.path.basename(target))
    os.environ["CLINIC_SETUP_MINE"] = mine or os.path.join(tmp, "mine_" + os.path.basename(target))
    spec = importlib.util.spec_from_file_location("setup_pc_t%d" % len(PASS), os.path.join(kit, "setup_pc.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = m.main(["--kit", kit, "--pyzip", pyzip, "--no-start"] + list(args))
    return rc, buf.getvalue(), m


def tree(d):
    out = {}
    for r, _d, names in os.walk(d):
        for n in names:
            p = os.path.join(r, n)
            out[os.path.relpath(p, d)] = (md5(p), os.path.getmtime(p))
    return out


tools = sorted(n[8:] for n in zipfile.ZipFile(KITZIP).namelist() if n.startswith("payload/"))

# 1. a freshly reinstalled PC: nothing there
t1 = os.path.join(tmp, "fresh")
rc, out, m = run(t1, "--log", os.path.join(tmp, "log1.txt"))
check("a fresh PC: ends DONE, exit 0", rc == 0 and "DONE." in out, out[-400:])
check("...every tool is placed, byte for byte", all(md5(os.path.join(t1, n)) == md5(os.path.join(kit, "payload", n)) for n in tools)
      and "%d placed, 0 already here" % len(tools) in out, out)
check("...its Python is unpacked", os.path.isfile(os.path.join(t1, "pyportable", "python.exe")) and "unpacked" in out)
ent = os.path.join(tmp, "mine_fresh", "MargAgent.cmd")
check("...this account starts the agent at sign-in, with the kit's own starter", os.path.isfile(ent) and md5(ent) == md5(os.path.join(t1, "START_AGENT.cmd")))
check("...it says the token and the staff account are still owed", "token.txt is not in" in out and "ENABLE_AGENT_THIS_ACCOUNT.bat" in out)
check("...no token, no capture folder, no log was made by it", not any(os.path.exists(os.path.join(t1, n)) for n in ("token.txt", "_captured", "agent.log", "_off")))
check("...what it printed is also in its log", "DONE." in open(os.path.join(tmp, "log1.txt")).read())
check("...no half-written file left", not [n for n in tree(t1) if n.endswith(".part") or "_write_probe" in n], list(tree(t1))[:5])

# 2. run again: nothing changes
before = tree(t1)
time.sleep(1.1)
rc, out, m = run(t1)
check("run again: 0 placed, every tool 'already here and the same'", rc == 0 and "0 placed, %d already here and the same, 0 kept" % len(tools) in out, out)
check("...and not one file on the PC was rewritten", tree(t1) == before)
check("...Python left alone, start-up left alone", "already there, left alone" in out and "already set" in out, out)

# 3. THE WORKING PC: tools newer than the kit's, a token, captures, a running agent
t3 = os.path.join(tmp, "live")
shutil.copytree(t1, t3)
open(os.path.join(t3, "marg_txt.py"), "w").write("# the Sanjeevni side's newer reader\n")
open(os.path.join(t3, "marg_watch.py"), "w").write("# a newer watcher\n")
os.remove(os.path.join(t3, "medical_census.py"))
open(os.path.join(t3, "token.txt"), "w").write("stand-in")
os.makedirs(os.path.join(t3, "_captured")); open(os.path.join(t3, "_captured", "x.XLS"), "w").write("capture")
open(os.path.join(t3, "heartbeat.txt"), "w").write("WATCHER : ALIVE")
au = os.path.join(tmp, "allusers_live"); os.makedirs(au); shutil.copy(os.path.join(t3, "START_AGENT.cmd"), os.path.join(au, "MargAgent.cmd"))
before = tree(t3)
time.sleep(1.1)
rc, out, m = run(t3, allusers=au)
after = tree(t3)
check("the working PC: the two newer tools are KEPT, named, and not replaced", rc == 0 and "2 kept as this PC has them" in out
      and "NOT replaced" in out and open(os.path.join(t3, "marg_txt.py")).read().startswith("# the Sanjeevni") , out)
check("...only the one missing tool is placed", "1 placed" in out and "placed: medical_census.py" in out, out)
changed = sorted(k for k in after if before.get(k) != after[k])
check("...nothing else on the PC changed -- not the token, not a capture, not the heartbeat", changed == ["medical_census.py"], changed)
check("...an agent that is running is not started again", "already running" in out, out)
check("...the all-accounts start-up entry is recognised; this account gets no second one", "already set for every account" in out
      and not os.path.exists(os.path.join(tmp, "mine_live", "MargAgent.cmd")), out)
check("...with the token there, it is not asked for", "token.txt is not in" not in out, out)

# 4. a start-up entry that is not ours is left alone and said
t4 = os.path.join(tmp, "odd"); shutil.copytree(t1, t4)
mi = os.path.join(tmp, "mine_odd"); os.makedirs(mi); open(os.path.join(mi, "MargAgent.cmd"), "w").write("something else")
rc, out, m = run(t4, mine=mi)
check("a different start-up entry is left alone and said", rc == 0 and "left alone" in out and open(os.path.join(mi, "MargAgent.cmd")).read() == "something else", out)

# 5. a kit that is not whole is refused before anything is touched
bad = os.path.join(tmp, "badkit"); shutil.copytree(kit, bad)
open(os.path.join(bad, "payload", "marg_push.py"), "a").write("# tampered\n")
t5 = os.path.join(tmp, "t5")
os.environ["CLINIC_SETUP_TARGET"] = t5
spec = importlib.util.spec_from_file_location("setup_pc_bad", os.path.join(bad, "setup_pc.py")); mb = importlib.util.module_from_spec(spec); spec.loader.exec_module(mb)
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = mb.main(["--kit", bad, "--pyzip", pyzip, "--no-start"])
check("a tampered kit: STOP, exit 1, the folder is not even made", rc == 1 and "STOP: the kit is not whole" in buf.getvalue() and not os.path.exists(t5), buf.getvalue())

# 6. no Python part and none on the PC
t6 = os.path.join(tmp, "t6")
os.environ["CLINIC_SETUP_TARGET"] = t6
spec = importlib.util.spec_from_file_location("setup_pc_nopy", os.path.join(kit, "setup_pc.py")); mn = importlib.util.module_from_spec(spec); spec.loader.exec_module(mn)
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = mn.main(["--kit", kit, "--pyzip", os.path.join(tmp, "nope.zip"), "--no-start"])
check("no Python part: STOP with the reason, no tool placed", rc == 1 and "Python part did not come" in buf.getvalue() and not os.path.exists(os.path.join(t6, "medical_agent.py")), buf.getvalue())
check("the kit holds no token and no capture", not any("token" in n.lower() or "_captured" in n for n in zipfile.ZipFile(KITZIP).namelist()))

shutil.rmtree(tmp, ignore_errors=True)
print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
for f in FAIL:
    print("   FAILED: " + f)
sys.exit(1 if FAIL else 0)
