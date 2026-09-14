# -*- coding: utf-8 -*-
"""S259 live-shape walk -- proves each OFF switch on real copies, offline.

Run:  python walk_s259.py
It copies the kit's own files into a temporary tree, switches each job off and
on again, and asserts what actually happened to the files on disk -- not what
the code says it would do.
"""
import io, os, shutil, subprocess, sys, tempfile, threading, time

KIT = os.path.dirname(os.path.abspath(__file__))
OK = BAD = 0


def ck(name, cond, detail=""):
    global OK, BAD
    if cond:
        OK += 1
        print("  ok    %s" % name)
    else:
        BAD += 1
        print("  FAIL  %s %s" % (name, detail))


# ---------------------------------------------------------- 1 · pull_watchdog
root = tempfile.mkdtemp()
mp = os.path.join(root, "MargPull")
off = os.path.join(root, "_off")
os.makedirs(mp); os.makedirs(off)
shutil.copy(os.path.join(KIT, "manojz", "pull_watchdog.py"), mp)
pull = os.path.join(mp, "_last_pull.txt")
stamp = os.path.join(mp, "_watchdog_last.txt")
pic = os.path.join(root, "MARG_PICTURE.txt")
io.open(pull, "w").write("END 14-09-2026 6:00:00 -- ok\n")
io.open(pic, "w").write("picture body\n")

def run_wd(extra=()):
    cmd = [sys.executable, "-B", os.path.join(mp, "pull_watchdog.py"),
           "--pull-file", pull, "--picture", pic, "--stamp-file", stamp,
           "--alarm-file", os.path.join(mp, "_pull_alarm.txt"),
           "--logdir", os.path.join(mp, "_logs"), "--off-dir", off,
           "--no-feed", "--now", "2026-09-14T09:00:00+05:30"] + list(extra)
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, (r.stdout or "").strip()

rc, out = run_wd()
ck("watchdog ON: it runs and reports a state", rc == 0 and "state=" in out, out)
ck("watchdog ON: it wrote its own last-run stamp", os.path.isfile(stamp))
os.remove(stamp)

for marker in ("ALL_OFF.txt", "PULL_WATCHDOG_OFF.txt"):
    io.open(os.path.join(off, marker), "w").write("off")
    rc, out = run_wd()
    ck("watchdog OFF by %s: exit 0 and says OFF" % marker,
       rc == 0 and "OFF" in out and marker in out, out)
    ck("watchdog OFF by %s: nothing was written" % marker, not os.path.isfile(stamp))
    ck("watchdog OFF by %s: the picture is untouched" % marker,
       io.open(pic).read() == "picture body\n")
    os.remove(os.path.join(off, marker))

rc, out = run_wd()
ck("watchdog ON again after the marker is deleted -- no restart",
   rc == 0 and "state=" in out and os.path.isfile(stamp), out)

# ---------------------------------------------------------- 2 · marg_push
med = tempfile.mkdtemp()
shutil.copy(os.path.join(KIT, "medical", "marg_push.py"), med)
shutil.copy(os.path.join(KIT, "medical", "marg_watch.py"), med)
poff = os.path.join(med, "_off"); os.makedirs(poff)
spool = os.path.join(med, "_captured"); os.makedirs(spool)
io.open(os.path.join(spool, "20260914-090000__REPORT_1__aabbccdd.XLS"), "wb").write(
    b"\xd0\xcf\x11\xe0" + b"x" * 200)
io.open(os.path.join(med, "token.txt"), "w").write("not-a-real-key")
sys.path.insert(0, med)
import marg_push                                                   # noqa: E402

ck("pusher ON: it has work waiting", len(marg_push.pending(spool, {"sent": {}, "tries": {}})) == 1)
state = os.path.join(med, "push_state.json")
for marker in ("ALL_OFF.txt", "MARG_PUSH_OFF.txt"):
    io.open(os.path.join(poff, marker), "w").write("off")
    said = []
    got = marg_push.run_once(spool, said.append)
    ck("pusher OFF by %s: nothing sent, nothing tried" % marker, got == (0, 0, 0), str(got))
    ck("pusher OFF by %s: it says so in one line" % marker,
       any("OFF" in m and marker in m for m in said), str(said))
    ck("pusher OFF by %s: no state file was written" % marker, not os.path.isfile(state))
    os.remove(os.path.join(poff, marker))
ck("pusher ON again: the marker is gone and it is on", marg_push.off_marker(poff) is None)

# ---------------------------------------------------------- 3 · marg_watch
import marg_watch                                                  # noqa: E402
wroot = tempfile.mkdtemp()
src = os.path.join(wroot, "users"); os.makedirs(src)
wspool = os.path.join(wroot, "spool")
marg_watch.OFFDIR = poff                       # the walk's own _off folder
io.open(os.path.join(poff, "MARG_WATCH_OFF.txt"), "w").write("off")

lines = []
stop_after = [False]
th = threading.Thread(target=marg_watch.watch,
                      args=([src], wspool, False, False, lines.append, None, 0.2),
                      daemon=True)
th.start()
time.sleep(1.0)
io.open(os.path.join(src, "REPORT_1.XLS"), "wb").write(b"\xd0\xcf\x11\xe0" + b"A" * 300)
time.sleep(2.5)
captured_while_off = len(os.listdir(wspool)) if os.path.isdir(wspool) else 0
ck("capture OFF: the export was NOT copied while the marker was there",
   captured_while_off == 0, "found %d" % captured_while_off)
ck("capture OFF: it says so", any("capture: OFF" in m for m in lines), str(lines[-3:]))

os.remove(os.path.join(poff, "MARG_WATCH_OFF.txt"))
time.sleep(3.0)
captured_after = len(os.listdir(wspool)) if os.path.isdir(wspool) else 0
ck("capture ON again without a restart: the export was copied",
   captured_after == 1, "found %d" % captured_after)
ck("capture ON again: it says so", any(m.strip() == "capture: on" for m in lines), str(lines[-3:]))

# ALL_OFF must NOT stop capture -- the whole point of the separate marker
io.open(os.path.join(poff, "ALL_OFF.txt"), "w").write("off")
time.sleep(0.8)
io.open(os.path.join(src, "REPORT_2.XLS"), "wb").write(b"\xd0\xcf\x11\xe0" + b"B" * 300)
time.sleep(3.0)
ck("ALL_OFF does NOT stop capture -- capture keeps its own marker",
   (len(os.listdir(wspool)) if os.path.isdir(wspool) else 0) == 2,
   "found %d" % (len(os.listdir(wspool)) if os.path.isdir(wspool) else 0))

# ---------------------------------------------------------- 4 · the two .bat files
# cmd.exe does not exist off Windows, so the OFF branch of the two stock bats is
# proved here by reading them, and proved by RUNNING inside install_s259.py on
# manojz itself (F-443: a step that could not run here says so).
import re
for f, own in (("manojz/PUSH_STOCK_DAILY.bat", "PUSH_STOCK_OFF.txt"),
               ("manojz/PUSH_STOCK_NIGHTLY.bat", "PUSH_STOCK_OFF.txt")):
    t = io.open(os.path.join(KIT, f), encoding="utf-8").read().replace("\r\n", "\n")
    lines = t.split("\n")
    def first(pred):
        for i, l in enumerate(lines):
            if pred(l):
                return i
        return 10 ** 6
    i_all = first(lambda l: 'ALL_OFF.txt" goto :off' in l)
    i_own = first(lambda l: own + '" goto :off' in l)
    i_py = first(lambda l: l.strip().startswith("python "))
    i_call = first(lambda l: l.strip().lower().startswith("call "))
    i_lab = first(lambda l: l.strip() == ":off")
    name = os.path.basename(f)
    ck("%s: both markers are tested before anything is run" % name,
       i_all < 10 ** 6 and i_own < 10 ** 6 and max(i_all, i_own) < min(i_py, i_call))
    ck("%s: the :off branch exists and ends at exit /b 0" % name,
       i_lab < 10 ** 6 and bool(re.search(r"\nexit /b 0", "\n".join(lines[i_lab:]))))
    seg = "\n".join(lines[i_lab:])
    m = re.search(r"\nexit /b 0", seg)
    body = seg[:m.start()] if m else seg
    ck("%s: the :off branch runs no python and calls no other bat" % name,
       "python " not in body and not re.search(r"(?im)^\s*call ", body))
    ck("%s: the :off branch names the folder and the way back on" % name,
       "%OFFDIR%" in body and "TURN_ON_ALL.bat" in body)

print("\n%d ok, %d failed" % (OK, BAD))
sys.exit(1 if BAD else 0)
