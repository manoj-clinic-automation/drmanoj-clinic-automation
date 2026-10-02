#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
agent_guard.py  --  S448.  Runs ON THE RECEPTION PC, started at logon.

It has one job: keep reception_agent.py running, and undo a bad update.

  * It starts the agent and waits. Exit code 42 means "start me again" (a
    restart was asked for, or a new version was just installed).
  * Any other ending is a death. If an update is still unconfirmed
    (update_pending.json is there -- the new version never wrote a heartbeat)
    the previous file is put back before the agent is started again.
  * An agent that is alive but has written no heartbeat for 15 minutes is
    stopped and treated the same way.

THIS FILE IS NEVER REPLACED WHILE IT RUNS, and the agent has no way to
replace it: a process that rewrites its own supervisor is how an unattended
machine bricks itself (the reason medical_agent.py never updates itself).
A new guard takes effect at the next logon.

Stdlib only. Writes guard.log, _guard.lock, _agent.pid in its own folder.
"""

import datetime as dt
import os
import shutil
import subprocess
import sys
import time

GUARD_VERSION = "S448.1"

ROOT = os.path.dirname(os.path.abspath(__file__))
AGENT = os.path.join(ROOT, "reception_agent.py")
PREV = AGENT + ".prev"
FAILED = AGENT + ".failed"
MARKER = os.path.join(ROOT, "update_pending.json")
BEAT = os.path.join(ROOT, "heartbeat.json")
LOG = os.path.join(ROOT, "guard.log")
LOCK = os.path.join(ROOT, "_guard.lock")
GUARD_PID = os.path.join(ROOT, "_guard.pid")
AGENT_PID = os.path.join(ROOT, "_agent.pid")

EXIT_RESTART = 42
POLL = 15                 # seconds between looks at the agent
STALE_BEAT = 900          # an agent silent this long is stopped
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def log(msg):
    line = "%s  %s\n" % (dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    try:
        if os.path.exists(LOG) and os.path.getsize(LOG) > 256 * 1024:
            with open(LOG, "r", encoding="utf-8", errors="replace") as fh:
                tail = fh.readlines()[-1000:]
            with open(LOG, "w", encoding="utf-8") as fh:
                fh.writelines(tail)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        pass
    try:
        if sys.stdout is not None:
            sys.stdout.write(line)
            sys.stdout.flush()
    except Exception:                                          # noqa: BLE001
        pass


def take_lock():
    """One guard per PC. The lock dies with the process, so a crash or a
    power cut never leaves a stale one behind."""
    try:
        fh = open(LOCK, "a+")
        if os.name == "nt":
            import msvcrt
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fh
    except OSError:
        return None


def write_pid(path, pid):
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(str(pid))
    except OSError:
        pass


def start_agent():
    p = subprocess.Popen([sys.executable, AGENT], cwd=ROOT,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, creationflags=NO_WINDOW)
    write_pid(AGENT_PID, p.pid)
    return p


def stop(p):
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"],
                           stdin=subprocess.DEVNULL, capture_output=True,
                           timeout=20, creationflags=NO_WINDOW)
        else:
            p.kill()
        p.wait(timeout=20)
    except Exception:                                          # noqa: BLE001
        try:
            p.kill()
        except Exception:                                      # noqa: BLE001
            pass


def roll_back():
    """Put the previous agent back if an update is still unconfirmed."""
    if not (os.path.exists(MARKER) and os.path.exists(PREV)):
        return False
    try:
        shutil.copyfile(AGENT, FAILED)
        shutil.copyfile(PREV, AGENT)
        os.remove(MARKER)
    except OSError as ex:
        log("ROLL BACK FAILED: %s" % ex)
        return False
    log("ROLLED BACK: the new agent died before its first heartbeat; the "
        "previous file is running again and the new one is kept as "
        "reception_agent.py.failed")
    return True


def beat_age():
    try:
        return time.time() - os.path.getmtime(BEAT)
    except OSError:
        return None


def main(max_starts=None):
    lock = take_lock()
    if lock is None:
        return 0                     # another guard already has this PC
    write_pid(GUARD_PID, os.getpid())
    log("=" * 60)
    log("agent_guard %s starting (python %s, pid %d)"
        % (GUARD_VERSION, sys.version.split()[0], os.getpid()))
    quick_deaths = 0
    starts = 0
    while max_starts is None or starts < max_starts:
        if not os.path.exists(AGENT):
            log("reception_agent.py is missing -- waiting for it")
            time.sleep(60)
            starts += 1
            continue
        started = time.time()
        try:
            p = start_agent()
        except OSError as ex:
            log("could not start the agent: %s" % ex)
            time.sleep(60)
            starts += 1
            continue
        starts += 1
        log("agent started, pid %d" % p.pid)
        rc = None
        last_look = started
        while True:
            rc = p.poll()
            if rc is not None:
                break
            # The PC slept (or its clock moved): the time that passed while
            # nothing ran is not silence. Give the agent a fresh 15 minutes.
            t = time.time()
            if t - last_look > 4 * POLL or t < last_look:
                started = t
            last_look = t
            ran = t - started
            age = beat_age()
            if ran > STALE_BEAT and (age is None or age > STALE_BEAT):
                log("the agent is alive but silent for %ds -- stopping it"
                    % int(age if age is not None else ran))
                stop(p)
                rc = p.poll()
                if rc is None or rc == EXIT_RESTART:
                    rc = -9
                break
            time.sleep(POLL if max_starts is None else 0.2)
        ran = time.time() - started
        if rc == EXIT_RESTART:
            log("the agent asked to be started again")
            quick_deaths = 0
            time.sleep(1)
            continue
        log("THE AGENT ENDED (exit %s) after %ds" % (rc, int(ran)))
        rolled = roll_back()
        quick_deaths = quick_deaths + 1 if ran < 120 else 0
        wait = 5 if rolled else min(300, 15 * max(1, quick_deaths))
        time.sleep(wait if max_starts is None else 0.2)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException:                                      # noqa: BLE001
        import traceback
        try:
            with open(os.path.join(ROOT, "guard_crash.txt"), "a",
                      encoding="utf-8") as fh:
                fh.write("agent_guard %s CRASHED at %s\n\n%s\n"
                         % (GUARD_VERSION, dt.datetime.now().isoformat(
                             timespec="seconds"), traceback.format_exc()))
        except OSError:
            pass
        raise
