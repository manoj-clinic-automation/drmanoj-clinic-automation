# -*- coding: utf-8 -*-
r"""install_s499.py -- kit S499_MEDICAL_AGENT_BACKUP. Run ON THE MEDICAL PC by INSTALL_AGENT_S499.bat (a double-click).

It replaces ONE file, D:\SendToClinic\medical_agent.py, S205.1 (70d5c4e3) -> S499.1, and nothing else. The agent never
replaces itself (by design), so this is done by a person at that PC. Safe to run twice, and safe to run again after a run
that was interrupted.

HOW THIS PC RUNS THE AGENT, AND WHAT THIS DOES ABOUT IT
    Since S387/S388 (24-Sep-2026) the agent is the child of D:\SendToClinic\agent_guard.py, which every signed-in account
    starts from its start-up folder (MargAgent.cmd -> pythonw agent_guard.py). The guard has one switch:
    D:\SendToClinic\_off\AGENT_OFF.txt stops the agent (and the watcher under it) within 20 seconds; deleting the file brings
    the agent back within 30 seconds. It works from any Windows account, without administrator rights. This installer uses
    that switch and nothing else: no process is killed here, no start-up entry and no scheduled task is touched.

    The OLD installer on Drive (ToMedical\INSTALL_AGENT.bat, v3 of 25-Aug-2026) must NOT be used any more: it kills every
    python on the PC -- the guard included -- and writes a start-up entry that runs the agent without the guard.

THE ORDER, CHOSEN SO THAT THE AGENT IS OFF FOR AS SHORT A TIME AS THE GUARD ALLOWS
  1  gates -- nothing is changed if any fails: this is the only run; no switch a PERSON wrote is there (a switch an earlier,
     interrupted run of THIS installer wrote is recognised by its first line, taken away, and the agent waited for); the
     live file is the FROM pin (the TO pin = ALREADY INSTALLED, which is said only if the agent is really running it, with
     its watcher); the kit's file is the TO pin; a copy staged beside the live file is the TO pin and COMPILES with this PC's
     own python; no export was taken in the last five minutes; the guard's own records show its agent running
  2  a backup: medical_agent.py.before_70d5c4e3 (kept; the undo)
  3  the new file takes the live name while the OLD agent is still running from memory; its md5 is read back
  4  the switch is written, the guard's OWN "agent stopped" is waited for, and the switch is taken away again AT ONCE --
     in a `finally`, so that no error and no Ctrl-C can leave it behind. Nothing is printed while it is there (a click in a
     Windows console window freezes a program that prints). Not answered in 90 s: the old file goes back, nothing changed
  5  the new agent's own "starting" line, and a heartbeat that names S499.1 with WATCHER : ALIVE, are waited for (240 s)
  6  anything red after 3: the old file is put back byte-identically (md5 read back) and the old agent waited for
  7  D:\SendToClinic\S499_INSTALL_RESULT.txt and, when Drive is there, Clinic Data Archive\FromMedical\S499_INSTALL_RESULT.txt:
     every run's date and time, FROM, TO, the read-back, the verdict -- the newest last
"""
import datetime
import hashlib
import os
import re
import shutil
import stat
import sys
import tempfile
import time

KIT = os.path.dirname(os.path.abspath(__file__))
DEST = r"D:\SendToClinic"
AGENT = "medical_agent.py"
FROM_MD5 = "70d5c4e3c439eaa049acb27f9851688c"
FROM_VER = "S205.1"
TO_MD5 = "d91fa79ad972c39e531c70afb1a1c758"
TO_VER = "S499.1"
RESULT = "S499_INSTALL_RESULT.txt"
STOP_WAIT = 90          # the guard reads its switch every 20 s
START_WAIT = 240        # the guard waits up to 30 s; the agent beats in its first loop
POLL = 2.0
LOCK_STALE = 1200       # s: a lock older than this was left by a run that died
RECENT = 300            # s: an export this recent may still be being captured
FRESH_BEAT = 600        # s: ALREADY INSTALLED needs a heartbeat younger than this
SWITCH_MARK = "written by install_s499.py"
# where an export lands and where the watcher keeps what it took (marg_watch.py S488: .xls .xlsx .pdf, and Marg's text)
WATCHED = [r"D:\MARGERP\users", r"D:\MARG REPORTS", r"C:\Users\Public\MARG"]
STICK_TOP = "E:\\"
EXPORT_EXTS = (".xls", ".xlsx", ".pdf", ".txt")

STAMP = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\s")


def P(name):
    return os.path.join(DEST, name)


def SWITCH():
    return os.path.join(DEST, "_off", "AGENT_OFF.txt")


def md5(p):
    try:
        h = hashlib.md5()
        with open(p, "rb") as fh:
            for c in iter(lambda: fh.read(1 << 20), b""):
                h.update(c)
        return h.hexdigest()
    except OSError:
        return None


def nowtxt():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Run(object):
    """What this run did, in order -- printed as it goes (except while the agent is switched off), and written to the
    result file at the end."""

    def __init__(self):
        self.lines = []
        self.verdict = ""
        self.live_before = None
        self.read_back = None
        self.started = nowtxt()
        self.quiet_from = None

    def _print(self, msg):
        try:
            print(msg)
            sys.stdout.flush()
        except Exception:                                       # noqa: BLE001 -- a closed console must not stop an install
            pass

    def say(self, msg=""):
        self.lines.append(msg)
        if self.quiet_from is None:
            self._print(msg)

    def hush(self):
        """Nothing reaches the console from here until speak(): while the agent is switched off, a click in the window
        (QuickEdit) would freeze this program at its next print -- with the agent off."""
        if self.quiet_from is None:
            self.quiet_from = len(self.lines)

    def speak(self):
        if self.quiet_from is not None:
            held, self.quiet_from = self.lines[self.quiet_from:], None
            for m in held:
                self._print(m)


def lines_since(path, t0, needle, tag=None):
    """The lines of a log written at or after t0 (this PC's clock) that contain needle -- and, when tag is given, that
    were written by the guard with that tag. Read whole each time: both logs are trimmed by their writers."""
    out = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if needle not in line or (tag and tag not in line):
                    continue
                m = STAMP.match(line)
                if not m:
                    continue
                try:
                    t = time.mktime(time.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"))
                except ValueError:
                    continue
                if t >= t0 - 1:
                    out.append(line.rstrip("\r\n"))
    except OSError:
        pass
    return out


def tail(path, n=4):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return [x.rstrip("\r\n") for x in fh.readlines()[-n:]]
    except OSError:
        return []


def wait_for(fn, secs):
    t0 = time.time()
    while True:
        v = fn()
        if v or time.time() - t0 >= secs:
            return v
        time.sleep(POLL)


def beat_info():
    """(version the heartbeat names, its mtime, does it say WATCHER : ALIVE) -- (None, None, False) without one."""
    try:
        with open(P("heartbeat.txt"), "r", encoding="utf-8", errors="replace") as fh:
            t = fh.read(8000)
        m = re.search(r"^agent\s+(\S+)\s+on\s", t, re.M)
        return ((m.group(1) if m else None), os.path.getmtime(P("heartbeat.txt")),
                re.search(r"^WATCHER\s*:\s*ALIVE", t, re.M) is not None)
    except OSError:
        return None, None, False


def guard_state():
    """(True, pid, tag) when the guard's own records say ITS agent is running now: the pid in _agent_guard.child is the
    pid of the guard's last 'agent started' line, and no later line of that guard says the agent stopped. tag is that
    guard's own mark in its log, '[<account> pid <n>]', so that only ITS answers are believed. Otherwise (False, why, None)."""
    try:
        with open(P("_agent_guard.child")) as fh:
            child = int(fh.read().strip() or 0)
    except (OSError, ValueError):
        child = 0
    last, tag, after = None, None, []
    try:
        with open(P("agent_guard.log"), "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                m = re.search(r"(\[[^\]]* pid \d+\]) agent started, pid (\d+)", line)
                if m:
                    tag, last, after = m.group(1), int(m.group(2)), []
                elif last is not None:
                    after.append(line)
    except OSError:
        return False, "agent_guard.log cannot be read", None
    if not child or last is None:
        return False, "the guard has no agent on record (no pid, or no 'agent started' line)", None
    if child != last:
        return False, "the guard's pid file says %d, its last 'agent started' line says %d" % (child, last), None
    for line in after:
        if tag in line and ("agent stopped" in line or "stepped back" in line):
            return False, "the guard's agent has stopped since: %s" % line.strip()[:120], None
    return True, child, tag


def switch_is_ours():
    try:
        with open(SWITCH(), "r", encoding="utf-8", errors="replace") as fh:
            return fh.readline().startswith(SWITCH_MARK)
    except OSError:
        return False


def write_switch():
    """The guard's switch, whole or not at all: written under a temp name the guard does not look at, then given the real
    name. An empty or half switch -- which a later run could not recognise as its own -- is never left."""
    tmp = SWITCH() + ".tmp"
    try:
        if not os.path.isdir(P("_off")):
            os.makedirs(P("_off"))
        with open(tmp, "w") as fh:
            fh.write("%s %s -- the installer removes it again\r\n" % (SWITCH_MARK, nowtxt()))
        os.replace(tmp, SWITCH())
        return ""
    except OSError as ex:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
        return str(ex)


def _close_cleanup(event=None):
    """What the console close / Ctrl handler does: take away a switch THIS installer wrote. Returns False, so that Windows
    goes on to close the window as asked."""
    try:
        if switch_is_ours():
            os.remove(SWITCH())
    except Exception:                                           # noqa: BLE001 -- a handler must never raise
        pass
    return False


_HANDLER = []                                                   # keeps the ctypes callback alive


def install_close_handler():
    """On Windows: closing the window, Ctrl-C, Ctrl-Break, log-off or shut-down first run _close_cleanup, so the agent is
    not left switched off. A failure to register is harmless -- the next run recognises its own switch anyway."""
    if not sys.platform.startswith("win"):
        return False
    try:
        import ctypes
        from ctypes import wintypes
        proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)
        cb = proto(lambda ev: bool(_close_cleanup(ev)))
        _HANDLER.append(cb)
        return bool(ctypes.windll.kernel32.SetConsoleCtrlHandler(cb, True))
    except Exception:                                           # noqa: BLE001
        return False


def switch_on():
    """Take away the switch -- only ever one THIS installer wrote. True when none of ours is left."""
    if not os.path.isfile(SWITCH()):
        return True
    if not switch_is_ours():
        return False
    try:
        os.remove(SWITCH())
    except OSError:
        pass
    return not os.path.isfile(SWITCH())


def switch_off_and_on(R, tag, strict, on_no_answer=None):
    """Write the guard's switch, wait for THAT guard's answer, and take the switch away again at once, whatever happens.

    strict: only "agent stopped" counts -- the guard had its agent and stopped it. Not strict (putting the old file back,
    when the new agent may already have died by itself and the guard is waiting to restart it): the same guard's
    "not starting the agent" counts too. A line from another account's guard, standing by, never counts.

    on_no_answer: run INSIDE the finally, BEFORE the switch goes, when the guard did not answer -- so that a guard that
    stops the agent late can only ever restart the file put back, never the new one."""
    needle = "AGENT_OFF.txt is present -- agent stopped" if strict else "AGENT_OFF.txt is present"
    t0 = time.time()
    got = []
    R.hush()
    try:
        err = write_switch()
        if err:
            R.say("     could not write AGENT_OFF.txt: %s" % err)
            return False
        got = wait_for(lambda: lines_since(P("agent_guard.log"), t0, needle, tag), STOP_WAIT)
        return bool(got)
    finally:
        if not got and on_no_answer:
            try:
                on_no_answer()
            except Exception as ex:                             # noqa: BLE001
                R.say("     putting the old file back failed: %s" % ex)
        gone = switch_on()
        if got:
            R.say("     the guard says: %s" % got[-1][-90:])
        if not gone:
            R.say("     COULD NOT delete %s -- delete it by hand" % SWITCH())
        R.speak()


def wait_started(ver, t0, secs):
    """The agent of version `ver` has started since t0 AND has written a heartbeat that names it and says
    WATCHER : ALIVE. (ok, why)"""
    def look():
        for line in tail(P("agent.log"), 300):
            m = re.match(r"medical_agent (\S+) CRASHED at (\S+)", line)
            if m and m.group(1) == ver:
                try:
                    if time.mktime(time.strptime(m.group(2)[:19], "%Y-%m-%dT%H:%M:%S")) >= t0 - 1:
                        return "crashed"
                except ValueError:
                    pass
        if lines_since(P("agent.log"), t0, "FATAL:"):
            return "fatal"
        if not lines_since(P("agent.log"), t0, "medical_agent %s starting" % ver):
            return None
        v, mt, alive = beat_info()
        if v == ver and mt is not None and mt >= t0 - 1 and alive:
            return "ok"
        return None
    got = wait_for(look, secs)
    if got == "ok":
        return True, ""
    if got == "crashed":
        return False, "the agent %s crashed at its start (D:\\SendToClinic\\agent_crash.txt has why)" % ver
    if got == "fatal":
        return False, "the agent %s stopped at its start with FATAL (D:\\SendToClinic\\agent.log has why)" % ver
    if lines_since(P("agent.log"), t0, "medical_agent %s starting" % ver):
        v, mt, alive = beat_info()
        if v == ver and mt is not None and mt >= t0 - 1:
            return False, "the agent %s runs but its heartbeat does not say WATCHER : ALIVE" % ver
        return False, "the agent %s started but wrote no heartbeat in %d s" % (ver, secs)
    return False, "no start of the agent %s was seen in %d s" % (ver, secs)


def running_right(ver):
    """[] when the agent `ver` is really running: no switch, a fresh heartbeat naming it, its watcher alive."""
    bad = []
    if os.path.isfile(SWITCH()):
        bad.append("%s is there: the agent is switched off" % SWITCH())
    v, mt, alive = beat_info()
    if mt is None:
        bad.append("there is no heartbeat.txt")
    else:
        age = time.time() - mt
        if age > FRESH_BEAT:
            bad.append("the heartbeat is %d minute(s) old" % (age // 60))
        if v != ver:
            bad.append("the heartbeat names agent %s, not %s" % (v, ver))
        if not alive:
            bad.append("the heartbeat does not say WATCHER : ALIVE")
    return bad


def recent_exports():
    """Report files written in the last five minutes where Marg exports and where the watcher keeps what it took.
    The agent is stopped for about half a minute during the swap, and with it the watcher; an export being taken now
    could be missed -- Marg re-uses its file names."""
    now = time.time()
    found = []

    def look(top, deep, exts):
        try:
            if deep:
                walker = os.walk(top)
            else:
                walker = [(top, [], [f for f in os.listdir(top) if os.path.isfile(os.path.join(top, f))])]
            for base, _dirs, files in walker:
                for f in files:
                    if exts and not f.lower().endswith(exts):
                        continue
                    p = os.path.join(base, f)
                    try:
                        m = os.path.getmtime(p)
                    except OSError:
                        continue
                    if now - RECENT <= m <= now + 60:
                        found.append((p, int(now - m)))
        except OSError:
            pass
    look(P("_captured"), True, None)
    look(P("_captured_txt"), True, None)
    for d in WATCHED:
        look(d, True, EXPORT_EXTS)
    look(STICK_TOP, False, EXPORT_EXTS)
    return found


def put_back(R, why, tag):
    """Red after the new file was placed: the old file back byte-identically, the old agent started again."""
    live, bak = P(AGENT), P(AGENT + ".before_" + FROM_MD5[:8])
    R.say("  RED: %s" % why)
    R.say("  6  putting the old file back")
    t0 = time.time()                        # the old agent can only start after this: the switch comes first
    if not switch_off_and_on_restore(R, tag, live, bak):
        return
    ok, _w = wait_started(FROM_VER, t0, START_WAIT // 2)
    if ok and R.read_back == FROM_MD5:
        R.verdict = "ROLLED BACK - %s. The old file is back (md5 %s) and the old agent is running again." % (why, R.read_back)
    else:
        R.verdict = ("ROLLED BACK - %s. The old file is back (md5 %s) but the old agent's start was not seen: restart this PC."
                     % (why, R.read_back))


def switch_off_and_on_restore(R, tag, live, bak):
    """The switch, then the old file back WHILE the guard keeps the agent stopped, then the switch away -- in one finally."""
    needle = "AGENT_OFF.txt is present"
    t0 = time.time()
    R.hush()
    restored = False
    try:
        err = write_switch()
        if err:
            R.say("     could not write AGENT_OFF.txt (%s) -- putting the file back all the same" % err)
        got = wait_for(lambda: lines_since(P("agent_guard.log"), t0, needle, tag), STOP_WAIT)
        if got:
            R.say("     the guard says: %s" % got[-1][-90:])
        else:
            R.say("     the guard did not answer the switch in %d s -- putting the file back all the same" % STOP_WAIT)
        try:
            shutil.copyfile(bak, live + ".restore_S499")
            if md5(live + ".restore_S499") != FROM_MD5:
                raise OSError("the backup does not read back as %s" % FROM_MD5[:8])
            os.replace(live + ".restore_S499", live)
            restored = True
        except OSError as ex:
            R.read_back = md5(live)
            R.verdict = ("FAILED TO RESTORE - %s. %s is now %s; the old file is %s. Tell Claude NOW."
                         % (ex, live, R.read_back, bak))
            return False
        R.read_back = md5(live)
        R.say("     %s reads back %s (the old file)" % (live, R.read_back))
        return True
    finally:
        switch_on()
        try:
            if os.path.exists(live + ".restore_S499"):
                os.remove(live + ".restore_S499")
        except OSError:
            pass
        R.speak()
        if not restored and not R.verdict:
            R.verdict = "FAILED TO RESTORE - interrupted. %s reads %s now. Tell Claude NOW." % (live, md5(live))


def pid_alive(pid):
    """Is process `pid` running? agent_guard.py's own test (S387): on Windows OpenProcess + GetExitCodeProcess (access
    denied = it exists, in another account); elsewhere signal 0."""
    if not pid:
        return False
    if sys.platform.startswith("win"):
        try:
            import ctypes
            from ctypes import wintypes
            k32 = ctypes.WinDLL("kernel32", use_last_error=True)
            k32.OpenProcess.restype = wintypes.HANDLE
            k32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
            k32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
            k32.CloseHandle.argtypes = (wintypes.HANDLE,)
            h = k32.OpenProcess(0x1000, False, int(pid))        # PROCESS_QUERY_LIMITED_INFORMATION
            if not h:
                return ctypes.get_last_error() == 5
            try:
                code = wintypes.DWORD()
                k32.GetExitCodeProcess(h, ctypes.byref(code))
                return code.value == 259                        # STILL_ACTIVE
            finally:
                k32.CloseHandle(h)
        except Exception:                                       # noqa: BLE001 -- cannot tell: treat as alive, the age rule still applies
            return True
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False


def take_lock():
    """(lock path, '') -- or (None, why). The lock holds the pid of the run that took it: a lock whose run is gone (the
    window was closed) is stale AT ONCE, and the leftover-switch recovery then runs. Only a live run's lock means
    'another run'; anything else is said as itself."""
    lock = P("S499_INSTALL.lock")
    for _ in (1, 2):
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, ("%d %s\r\n" % (os.getpid(), nowtxt())).encode("ascii"))
            os.close(fd)
            return lock, ""
        except FileExistsError:
            try:
                try:
                    with open(lock, "r") as fh:
                        holder = int((fh.read().split() or ["0"])[0])
                except (OSError, ValueError):
                    holder = 0
                if (holder and not pid_alive(holder)) or time.time() - os.path.getmtime(lock) > LOCK_STALE:
                    os.remove(lock)
                    continue
            except OSError:
                pass
            return None, "another run of this installer is going on (%s). Wait for it." % lock
        except OSError as ex:
            return None, "this account cannot write in %s (%s: %s)" % (DEST, ex.__class__.__name__, ex)
    return None, "the lock %s could not be taken" % lock


def from_medical():
    """The FromMedical folder of the clinic Drive -- where this PC's heartbeat goes -- found the way the agent finds it,
    or None."""
    cands = []
    d = KIT
    for _ in range(6):
        if os.path.basename(d).lower() == "clinic data archive":
            cands.append(os.path.join(d, "FromMedical"))
            break
        nd = os.path.dirname(d)
        if nd == d:
            break
        d = nd
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        cands.append("%s:\\My Drive\\Clinic Data Archive\\FromMedical" % letter)
    cands.append(os.path.join(os.environ.get("USERPROFILE", ""), "My Drive", "Clinic Data Archive", "FromMedical"))
    for c in cands:
        if os.path.isdir(c):
            return c
    return None


def write_result(R):
    live = P(AGENT)
    out = ["S499_MEDICAL_AGENT_BACKUP -- install result",
           "written   : %s  (this PC's own clock)" % nowtxt(),
           "started   : %s" % R.started,
           "computer  : %s   account: %s   python: %s" % (os.environ.get("COMPUTERNAME", "?"), os.environ.get("USERNAME", "?"),
                                                      sys.version.split()[0]),
           "file      : %s" % live,
           "FROM      : %s  (%s)" % (FROM_MD5, FROM_VER),
           "TO        : %s  (%s)" % (TO_MD5, TO_VER),
           "before    : %s" % R.live_before,
           "read back : %s" % (R.read_back if R.read_back is not None else md5(live)),
           "VERDICT   : %s" % R.verdict,
           "", "what this run printed:"] + ["    " + x for x in R.lines]
    text = "\r\n".join(x.encode("ascii", "replace").decode("ascii") for x in out) + "\r\n" + "=" * 100 + "\r\n"
    wrote = []
    fm = from_medical()
    for d in (DEST, fm):
        if not d:
            continue
        try:
            with open(os.path.join(d, RESULT), "a", newline="") as fh:     # every run is kept, the newest last
                fh.write(text)
            wrote.append(os.path.join(d, RESULT))
        except OSError:
            pass
    return wrote, fm


def recover_leftover(R):
    """A switch at the start. Ours (an earlier run was interrupted): take it away and wait for the agent. A person's:
    leave it. Returns '' to go on, or the verdict to stop with."""
    if not os.path.isfile(SWITCH()):
        return ""
    if not switch_is_ours():
        return ("NOT INSTALLED - nothing changed: %s is there and was NOT written by this installer -- someone switched "
                "the agent off on purpose. Ask why before deleting it; then run this again." % SWITCH())
    R.say("  0  an earlier run of this installer was interrupted and left its switch: taking it away")
    t0 = time.time()
    if not switch_on():
        return "NOT INSTALLED - the switch an earlier run left could not be deleted: delete %s by hand" % SWITCH()

    def back():
        if guard_state()[0] and not lines_since(P("agent_guard.log"), t0, "AGENT_OFF.txt is present"):
            return True                         # the guard never acted on that switch: its agent ran on throughout
        if not lines_since(P("agent_guard.log"), t0, "agent started, pid"):
            return False
        v, mt, alive = beat_info()
        return v is not None and mt is not None and mt >= t0 - 1 and alive
    if not wait_for(back, START_WAIT):
        return ("NOT DONE - the switch an earlier run left is gone, but no agent came back within %d s. Restart this PC, "
                "wait two minutes, and run this again." % START_WAIT)
    R.say("     the agent is running again (%s)" % (beat_info()[0] or "?"))
    return ""


def install(R):
    """Returns the process's exit code; R.verdict says what happened."""
    live, staged, bak = P(AGENT), P(AGENT + ".new_S499"), P(AGENT + ".before_" + FROM_MD5[:8])
    R.say("S499 -- the Marg medical agent, %s -> %s" % (FROM_VER, TO_VER))
    R.say("  %s   account: %s   python %s" % (nowtxt(), os.environ.get("USERNAME", "?"), sys.version.split()[0]))
    R.say("  Do this when nobody is exporting from Marg.")
    R.say("  Do NOT click inside this window and do NOT close it until it says DONE or NOT DONE.")
    R.say("")

    # ---- 1. gates: nothing is changed by any of them
    stop = recover_leftover(R)
    if stop:
        R.verdict = stop
        return 1
    R.live_before = md5(live)
    if R.live_before == TO_MD5:
        R.read_back = R.live_before
        v_now = beat_info()[0]
        g_ok, g_what, g_tag = guard_state()
        if (v_now == FROM_VER and g_ok and md5(bak) == FROM_MD5 and not os.path.isfile(SWITCH())
                and not lines_since(P("agent.log"), time.time() - 30, "medical_agent %s starting" % TO_VER)):
            # an earlier run was cut short after placing the file and before the guard saw its switch: the new file is in
            # place, the old agent still runs it from memory. Finish the job through the guard.
            R.say("  the new file is in place but the old agent still runs from memory (an earlier run was cut short):")
            R.say("  restarting it through the guard %s" % g_tag)
            return restart_into_new(R, g_tag, live, bak)
        if running_right(TO_VER):               # it may be starting this minute (after an interrupted run): wait for it
            wait_for(lambda: not running_right(TO_VER), START_WAIT)
        bad = running_right(TO_VER)
        if bad:
            R.verdict = ("INSTALLED BUT NOT RUNNING RIGHT - %s is %s (%s), but %s. Restart this PC; if it still says so, "
                         "tell Claude." % (live, TO_MD5, TO_VER, "; ".join(bad)))
            return 1
        R.verdict = ("ALREADY INSTALLED - %s is %s (%s); the agent runs it, its heartbeat is fresh and says WATCHER : ALIVE. "
                     "Nothing was changed." % (live, TO_MD5, TO_VER))
        return 0
    if R.live_before != FROM_MD5:
        R.verdict = ("NOT INSTALLED - nothing changed: %s is %s, neither the FROM pin %s nor the TO pin. Someone has changed it "
                     "since this kit was made." % (live, R.live_before, FROM_MD5[:8]))
        return 1
    if md5(os.path.join(KIT, AGENT)) != TO_MD5:
        R.verdict = ("NOT INSTALLED - nothing changed: the kit's %s is %s, not the TO pin %s (is Drive still downloading it?)"
                     % (AGENT, md5(os.path.join(KIT, AGENT)), TO_MD5[:8]))
        return 1
    if not os.path.isfile(P("agent_guard.py")):
        R.verdict = ("NOT INSTALLED - nothing changed: %s is not there, so this PC does not start the agent the way this "
                     "installer knows (S387)." % P("agent_guard.py"))
        return 1
    fresh = recent_exports()
    if fresh:
        R.verdict = ("NOT INSTALLED - nothing changed: an export was just taken (%s, %d s ago) -- wait five minutes and "
                     "double-click again." % (fresh[0][0], fresh[0][1]))
        return 1
    try:
        shutil.copyfile(os.path.join(KIT, AGENT), staged)
        if md5(staged) != TO_MD5:
            raise OSError("the staged copy reads back %s" % md5(staged))
        import py_compile
        cfile = os.path.join(tempfile.gettempdir(), "_s499_check_%d.pyc" % os.getpid())
        try:
            py_compile.compile(staged, cfile=cfile, doraise=True)
        finally:
            try:
                os.remove(cfile)
            except OSError:
                pass
    except Exception as ex:                                     # noqa: BLE001 -- py_compile raises its own class
        R.verdict = "NOT INSTALLED - nothing changed: the new file could not be staged or does not compile here (%s)" % str(ex)[:160]
        return 1
    R.say("  1  the live file is the FROM pin %s; the kit's file is the TO pin %s; it compiles with this python"
          % (FROM_MD5[:8], TO_MD5[:8]))
    ok, what, tag = guard_state()
    if not ok:
        R.verdict = ("NOT INSTALLED - nothing changed: the guard is not running its agent now (%s). Restart this PC, wait "
                     "two minutes, and run this again." % what)
        return 1
    R.say("     the guard %s is running the agent (pid %s)" % (tag, what))

    # ---- 2. the backup
    try:
        if not os.path.exists(bak):
            shutil.copyfile(live, bak)
        if md5(bak) != FROM_MD5:
            raise OSError("%s reads back %s, not %s" % (bak, md5(bak), FROM_MD5[:8]))
    except OSError as ex:
        R.verdict = "NOT INSTALLED - nothing changed: the backup could not be made (%s)" % ex
        return 1
    R.say("  2  backup: %s (%s)" % (bak, FROM_MD5[:8]))

    # ---- 3. place, while the old agent still runs from memory
    try:
        try:
            os.chmod(live, stat.S_IWRITE | stat.S_IREAD)
        except OSError:
            pass
        os.replace(staged, live)
    except OSError as ex:
        R.read_back = md5(live)
        if R.read_back == FROM_MD5:
            R.verdict = "NOT INSTALLED - nothing changed: the file could not be replaced (%s)" % ex
            return 1
        put_back(R, "the file could not be replaced cleanly (%s)" % ex, tag)
        return 1
    R.read_back = md5(live)
    if R.read_back != TO_MD5:
        put_back(R, "the placed file reads back %s, not %s" % (R.read_back, TO_MD5[:8]), tag)
        return 1
    R.say("  3  placed; %s reads back %s (the old agent still runs from memory)" % (live, R.read_back))

    return restart_into_new(R, tag, live, bak)


def restart_into_new(R, tag, live, bak):
    """Steps 4 and 5: the guard stops the agent running from memory and, the switch gone at once, starts the new file."""
    # ---- 4. the guard stops the old agent and, the switch gone at once, starts the new one
    R.say("  4  the guard's switch -- on, its answer, off again (up to %d s)" % STOP_WAIT)
    t0 = time.time()

    def _restore():
        shutil.copyfile(bak, live + ".restore_S499")
        os.replace(live + ".restore_S499", live)
    if not switch_off_and_on(R, tag, strict=True, on_no_answer=_restore):
        R.read_back = md5(live)
        if R.read_back == FROM_MD5:
            R.verdict = ("NOT INSTALLED - nothing changed: the guard did not say 'agent stopped' within %d s of its switch; "
                         "the switch is gone and the old file is back (%s)." % (STOP_WAIT, R.read_back))
        else:
            R.verdict = "FAILED TO RESTORE - the guard did not answer and %s reads %s. Tell Claude NOW." % (live, R.read_back)
        return 1

    # ---- 5. the new agent's own word
    R.say("  5  waiting for the new agent's own word (up to %d s)..." % START_WAIT)
    ok, why = wait_started(TO_VER, t0, START_WAIT)
    if not ok:
        put_back(R, why, tag)
        return 1
    R.say("     agent.log: %s" % (lines_since(P("agent.log"), t0, "medical_agent %s starting" % TO_VER) or ["?"])[-1])
    R.say("     the heartbeat names agent %s and says WATCHER : ALIVE" % TO_VER)
    R.verdict = "INSTALLED - %s is %s (%s) and the new agent is running; the old file is kept as %s" % (live, R.read_back, TO_VER, bak)
    return 0


def main():
    R = Run()
    rc = 1
    install_close_handler()
    lock, why = take_lock() if os.path.isdir(DEST) else ("nolock", "")
    if lock is None:
        R.verdict = "NOT INSTALLED - nothing changed: %s" % why
    else:
        try:
            rc = install(R)
        except BaseException as ex:                             # noqa: BLE001 -- Ctrl-C too: say it, and leave nothing switched off
            R.verdict = (R.verdict + " | " if R.verdict else "") + (
                "INTERRUPTED (%s: %s). %s reads %s now; the switch of this installer is taken away, so the guard runs "
                "whichever file is in place. Run this again." % (ex.__class__.__name__, str(ex)[:120], P(AGENT), md5(P(AGENT))))
            rc = 1
        finally:
            if switch_is_ours():                                # never leave the agent switched off -- whatever happened
                switch_on()
            try:
                if os.path.exists(P(AGENT + ".new_S499")):
                    os.remove(P(AGENT + ".new_S499"))
            except OSError:
                pass
            R.speak()
            if lock != "nolock":
                try:
                    os.remove(lock)
                except OSError:
                    pass
    R.say("")
    R.say("  " + R.verdict)
    # the agent compares itself with Drive's ToMedical\medical_agent.py and says OUT OF DATE when they differ
    fm = from_medical()
    if fm and rc == 0:
        there = md5(os.path.join(os.path.dirname(fm), "ToMedical", AGENT))
        if there != TO_MD5:
            R.say("  NOTE: Drive's ToMedical\\%s is %s, not %s -- until it is replaced with this kit's file the heartbeat"
                  % (AGENT, (there or "missing")[:8], TO_MD5[:8]))
            R.say("        says THIS AGENT IS OUT OF DATE. Do NOT run the old ToMedical\\INSTALL_AGENT.bat. Tell Claude.")
    wrote, _fm = write_result(R)
    try:
        for w in wrote:
            print("  result written: %s" % w)
        if not _fm:
            print("  (Drive's FromMedical folder is not visible from this account -- the result is on this PC only)")
        print("")
        print("  DONE." if rc == 0 else "  NOT DONE -- read the line above.")
    except Exception:                                           # noqa: BLE001
        pass
    return rc


if __name__ == "__main__":
    sys.exit(main())
