# -*- coding: utf-8 -*-
r"""agent_guard.py -- ONE medical agent for the whole machine, whichever Windows account signs in.  (S386)

WHY THIS EXISTS (F-618, 24-Sep-2026)
    The agent -- capture, sending, the offsite backup -- was started by ONE file,
    C:\Users\SET\...\Startup\MargAgent.cmd, the start-up folder of the Windows account SET.
    On 24-Sep the PC came up in SET at 07:31, SET was signed out about 08:14, and the staff
    account "user" -- where Shavez works and exports from Marg -- has no start-up entry. From
    08:14 nothing was captured and nothing was sent; the 23-Sep bill-wise sale never arrived.

WHAT IT DOES
    It is started at EVERY sign-in, in every account (the all-users start-up folder). It then:
      * takes a lock on D:\SendToClinic\_agent_guard.lock. Only one guard on the machine can
        hold it, so only one agent ever runs, however many accounts are signed in at once;
      * a guard that cannot take the lock STANDS BY and tries again every half minute -- so when
        the account running the agent signs out (its guard dies, the lock is released) another
        signed-in account takes over within a minute;
      * before starting the agent it checks the heartbeat: a heartbeat under 7 minutes old that
        did not come from a guarded agent means the OLD launcher is running one -- it stands aside
        until that one stops, and it steps back if one starts later. Two agents never fight;
      * it starts D:\SendToClinic\medical_agent.py exactly as MargAgent.cmd did, and starts it
        again (after a pause that grows) if it ever stops;
      * D:\SendToClinic\_off\AGENT_OFF.txt stops the agent and keeps it stopped; delete it and the
        agent comes back. Read every half minute, no restart needed.
    medical_agent.py and marg_watch.py are not changed. Every line it writes goes to
    D:\SendToClinic\agent_guard.log.

    pythonw agent_guard.py            run (what START_AGENT.cmd does)
    python  agent_guard.py --selftest prove it, in a scratch folder, with a stand-in agent
"""
import os, sys, time, subprocess, re, getpass, tempfile, shutil

VERSION = "S386.1"
WIN = sys.platform.startswith("win")
HERE = os.path.dirname(os.path.abspath(__file__))
STARTING = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\s+medical_agent \S+ starting")


def cfg():
    d = os.environ.get("AG_DIR") or HERE
    return dict(
        dir=d,
        py=os.environ.get("AG_PY") or os.path.join(d, "pyportable", "pythonw.exe"),
        agent=os.environ.get("AG_AGENT") or os.path.join(d, "medical_agent.py"),
        agent_log=os.path.join(d, "agent.log"),
        heartbeat=os.path.join(d, "heartbeat.txt"),
        lockfile=os.path.join(d, "_agent_guard.lock"),
        childfile=os.path.join(d, "_agent_guard.child"),
        offfile=os.path.join(d, "_off", "AGENT_OFF.txt"),
        glog=os.path.join(d, "agent_guard.log"),
        fresh=float(os.environ.get("AG_FRESH") or 420),
        poll=float(os.environ.get("AG_POLL") or 20),
        standby=float(os.environ.get("AG_STANDBY") or 30),
    )


C = cfg()


def who():
    try:
        return getpass.getuser()
    except Exception:                                           # noqa: BLE001
        return "?"


def glog(msg):
    try:
        p = C["glog"]
        if os.path.exists(p) and os.path.getsize(p) > 256 * 1024:
            with open(p, "rb") as fh:
                fh.seek(-64 * 1024, 2)
                tail = fh.read()
            with open(p, "wb") as fh:
                fh.write(tail)
        with open(p, "a", encoding="utf-8") as fh:
            fh.write("%s  [%s pid %d] %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), who(), os.getpid(), msg))
    except Exception:                                           # noqa: BLE001
        pass


# ------------------------------------------------------------------ the lock
def try_lock():
    """An open file holding an exclusive lock, or None if another guard holds it. The OS drops
    the lock when the process ends -- a sign-out releases it without anyone having to."""
    try:
        fh = open(C["lockfile"], "a+b")
    except OSError as ex:
        glog("cannot open the lock file (%s) -- carrying on without it" % ex.__class__.__name__)
        return "nolock"
    try:
        if WIN:
            import msvcrt
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fh
    except OSError:
        fh.close()
        return None


# ------------------------------------------------------------- processes
def pid_alive(pid):
    if not pid:
        return False
    if WIN:
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.OpenProcess.restype = wintypes.HANDLE
        k32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        k32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        k32.CloseHandle.argtypes = (wintypes.HANDLE,)
        h = k32.OpenProcess(0x1000, False, int(pid))            # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return ctypes.get_last_error() == 5                 # access denied = it exists, in another account
        try:
            code = wintypes.DWORD()
            k32.GetExitCodeProcess(h, ctypes.byref(code))
            return code.value == 259                            # STILL_ACTIVE
        finally:
            k32.CloseHandle(h)
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False


def kill_tree(pid):
    try:
        if WIN:
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, timeout=20)
        else:
            import signal
            try:
                os.killpg(int(pid), signal.SIGKILL)
            except OSError:
                os.kill(int(pid), signal.SIGKILL)
    except Exception:                                           # noqa: BLE001
        pass


def heartbeat_age():
    try:
        return time.time() - os.path.getmtime(C["heartbeat"])
    except OSError:
        return None


def read_child():
    try:
        return int(open(C["childfile"]).read().strip() or 0)
    except (OSError, ValueError):
        return 0


def write_child(pid):
    try:
        with open(C["childfile"], "w") as fh:
            fh.write(str(pid))
    except OSError:
        pass


def other_agent_alive():
    """True while an agent this guard did not start is running: a heartbeat under the fresh limit
    that is NOT explained by a guarded agent which has since stopped."""
    age = heartbeat_age()
    if age is None or age > C["fresh"]:
        return False
    prev = read_child()
    if prev and not pid_alive(prev):
        return False                        # the beat was our own previous agent's, and it is gone
    return True


def starts_since(t0):
    """How many agents have written their 'starting' line since t0 (a timestamp)."""
    n = 0
    try:
        with open(C["agent_log"], "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                m = STARTING.match(line)
                if m:
                    try:
                        t = time.mktime(time.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"))
                    except ValueError:
                        continue
                    if t >= t0 - 2:
                        n += 1
    except OSError:
        pass
    return n


def off():
    return os.path.isfile(C["offfile"])


def start_child():
    flags = 0
    kw = {}
    if WIN:
        flags = 0x08000000 | 0x00000200                        # CREATE_NO_WINDOW | NEW_PROCESS_GROUP
    else:
        kw["start_new_session"] = True
    p = subprocess.Popen([C["py"], C["agent"]], cwd=C["dir"], creationflags=flags,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kw)
    write_child(p.pid)
    return p


def run_once():
    """Start the agent and watch it. Returns 'exited', 'yielded' or 'off'."""
    t0 = time.time()
    p = start_child()
    glog("agent started, pid %d" % p.pid)
    while True:
        time.sleep(C["poll"])
        if off():
            kill_tree(p.pid)
            glog("AGENT_OFF.txt is present -- agent stopped")
            return "off"
        if p.poll() is not None:
            glog("agent stopped by itself (exit %s)" % p.returncode)
            return "exited"
        if starts_since(t0) >= 2:
            kill_tree(p.pid)
            glog("another agent started (the old launcher) -- this one stepped back, pid %d stopped" % p.pid)
            return "yielded"


def main():
    glog("guard %s starting" % VERSION)
    lock = None
    said = None
    backoff = C["standby"]
    while True:
        try:
            if off():
                if said != "off":
                    glog("AGENT_OFF.txt is present -- not starting the agent"); said = "off"
                time.sleep(C["standby"]); continue
            if lock is None:
                lock = try_lock()
                if lock is None:
                    if said != "standby":
                        glog("another account's guard runs the agent -- standing by"); said = "standby"
                    time.sleep(C["standby"]); continue
                glog("lock taken -- this account runs the agent" if lock != "nolock" else "running without the lock")
            if other_agent_alive():
                if said != "legacy":
                    glog("an agent from the old launcher is running (heartbeat %ds old) -- standing aside"
                         % int(heartbeat_age() or 0)); said = "legacy"
                time.sleep(C["standby"]); continue
            said = None
            why = run_once()
            if why == "exited":
                time.sleep(backoff)
                backoff = min(backoff * 2, 300)
            else:
                backoff = C["standby"]
        except Exception as ex:                                 # noqa: BLE001 -- the guard never dies of its own fault
            glog("guard error %s: %s" % (ex.__class__.__name__, str(ex)[:200]))
            time.sleep(C["standby"])


# ================================================================= selftest
FAKE_AGENT = r'''
import os, sys, time
d = os.environ["AG_DIR"]
with open(os.path.join(d, "agent.log"), "a") as fh:
    fh.write("%s  medical_agent FAKE starting (python x)\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
while True:
    with open(os.path.join(d, "heartbeat.txt"), "w") as fh:
        fh.write("beat %s %d\n" % (os.environ.get("AG_TAG", "?"), os.getpid()))
    time.sleep(0.3)
'''


def selftest():
    ok = True
    def ck(name, cond, got=None):
        nonlocal ok
        print(("  OK   " if cond else "  FAIL ") + name + ("" if got is None else "   [%s]" % got))
        ok = ok and bool(cond)
    d = tempfile.mkdtemp(prefix="ag_selftest_")
    os.makedirs(os.path.join(d, "_off"))
    fake = os.path.join(d, "fake_agent.py")
    open(fake, "w").write(FAKE_AGENT)
    env = dict(os.environ, AG_DIR=d, AG_PY=sys.executable, AG_AGENT=fake,
               AG_FRESH="3", AG_POLL="0.4", AG_STANDBY="0.5")
    flags = 0x08000000 if WIN else 0
    procs = []

    def guard(tag):
        e = dict(env, AG_TAG=tag)
        kw = {} if WIN else {"start_new_session": True}
        p = subprocess.Popen([sys.executable, os.path.abspath(__file__)], env=e, cwd=d, creationflags=flags,
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kw)
        procs.append(p)
        return p

    def beats_from(tag, wait=4.0):
        end = time.time() + wait
        while time.time() < end:
            try:
                if open(os.path.join(d, "heartbeat.txt")).read().split()[1] == tag:
                    return True
            except (OSError, IndexError):
                pass
            time.sleep(0.2)
        return False

    def agents_running():
        """stand-in agents alive right now = distinct pids beating in the last second"""
        seen = set()
        end = time.time() + 1.5
        while time.time() < end:
            try:
                seen.add(open(os.path.join(d, "heartbeat.txt")).read().split()[2])
            except (OSError, IndexError):
                pass
            time.sleep(0.1)
        return len(seen)

    try:
        a = guard("A")
        ck("the first account's guard starts the agent", beats_from("A"))
        b = guard("B")
        time.sleep(2.5)
        ck("a second account signed in at the same time does NOT start a second agent",
           agents_running() == 1 and not beats_from("B", 1.0))
        c = read_child_in(d)
        kill_tree(a.pid)                                          # the first account signs out:
        if c:                                                     # its guard AND its agent end with it
            kill_tree(c)
        ck("when that account signs out, the other takes over within seconds", beats_from("B", 6.0))
        # the old launcher starts an agent that knows nothing of the guard
        leg_env = dict(env, AG_TAG="LEGACY")
        kw = {} if WIN else {"start_new_session": True}
        leg = subprocess.Popen([sys.executable, fake], env=leg_env, cwd=d, creationflags=flags,
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kw)
        procs.append(leg)
        time.sleep(2.5)
        ck("an agent from the old launcher appears -> the guarded one steps back (one agent, not two)",
           agents_running() == 1 and beats_from("LEGACY", 1.0))
        kill_tree(leg.pid)
        ck("the old one stops -> the guard brings its own back once the heartbeat goes stale",
           beats_from("B", 9.0))
        open(os.path.join(d, "_off", "AGENT_OFF.txt"), "w").write("off")
        time.sleep(2.0)
        ck("AGENT_OFF.txt stops the agent", heartbeat_age_in(d) > 1.2)
        os.remove(os.path.join(d, "_off", "AGENT_OFF.txt"))
        ck("deleting AGENT_OFF.txt brings it back", beats_from("B", 4.0))
        log = open(os.path.join(d, "agent_guard.log"), encoding="utf-8").read()
        ck("every step is written in agent_guard.log", all(s in log for s in (
            "lock taken", "standing by", "stepped back", "AGENT_OFF.txt is present")))
    finally:
        for p in procs:
            kill_tree(p.pid)
        c = read_child_in(d)
        if c:
            kill_tree(c)
        time.sleep(0.5)
        shutil.rmtree(d, ignore_errors=True)
    print("SELFTEST " + ("OK" if ok else "FAILED"))
    return 0 if ok else 1


def heartbeat_age_in(d):
    try:
        return time.time() - os.path.getmtime(os.path.join(d, "heartbeat.txt"))
    except OSError:
        return 999


def read_child_in(d):
    try:
        return int(open(os.path.join(d, "_agent_guard.child")).read().strip() or 0)
    except (OSError, ValueError):
        return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    main()
