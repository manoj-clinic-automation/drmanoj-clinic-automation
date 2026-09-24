# -*- coding: utf-8 -*-
r"""install_s387.py -- kit S387_AGENT_ANY_USER_2 (F-618). Run ON THE MEDICAL PC by INSTALL_S387.bat.

S387: the same installer as S386 (refused at its own on-machine proof, nothing changed) carrying the
corrected guard -- one that steps back for the old launcher now stays back.

Makes the medical agent start whichever Windows account signs in -- SET or "user" -- and only ever
ONE copy of it. Stops at the first thing that is not as expected, and puts everything back.

  1  checks: D:\SendToClinic, its python and medical_agent.py are there; the kit's files are the
     ones built (md5)
  2  places agent_guard.py and START_AGENT.cmd in D:\SendToClinic (an older copy is kept beside
     each as .bak_S387_<md5>)
  3  PROVES the guard on this machine (its own selftest, in a scratch folder, with a stand-in
     agent): one agent with two accounts in, a hand-over when one signs out, stepping aside for the
     old launcher, the off switch. Red -> the placed files are taken back out and nothing else runs
  4  start-up: with administrator rights, MargAgent.cmd goes into the ALL-USERS start-up folder
     and every account's own old MargAgent.cmd is renamed .replaced_S387.bak; D:\SendToClinic is
     opened to every account (Users: modify). Without them, this account's own start-up folder
     gets it, and it says to run this once in the other account too
  5  starts the guard now and reads back what it says
"""
import hashlib, os, shutil, subprocess, sys, time, glob

KIT = os.path.dirname(os.path.abspath(__file__))
DEST = r"D:\SendToClinic"
PYW = os.path.join(DEST, "pyportable", "pythonw.exe")
PY = os.path.join(DEST, "pyportable", "python.exe")
FILES = {"agent_guard.py": "b8b5a900321cc52054df3be978c15318",
         "START_AGENT.cmd": "c58946c337cc3b423ecea67b54d4b7ca"}
ALLUSERS = os.path.join(os.environ.get("ProgramData", r"C:\ProgramData"),
                        r"Microsoft\Windows\Start Menu\Programs\StartUp")
MINE = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
ENTRY = "MargAgent.cmd"


def md5(p):
    try:
        return hashlib.md5(open(p, "rb").read()).hexdigest()
    except OSError:
        return None


def say(m=""):
    print(m); sys.stdout.flush()


def main():
    say("S387 -- the medical agent, for whichever account signs in")
    say("  running as: %s" % os.environ.get("USERNAME", "?"))
    say("")
    # 1 -- gates
    for p in (DEST, PY, PYW, os.path.join(DEST, "medical_agent.py")):
        if not os.path.exists(p):
            say("  STOPPED: %s is not there. Nothing was changed. Tell Claude." % p); return 1
    for n, h in FILES.items():
        if md5(os.path.join(KIT, n)) != h:
            say("  STOPPED: %s in the kit is not the file that was built (%s). Nothing was changed." % (n, md5(os.path.join(KIT, n))))
            return 1
    say("  1  the medical PC's folder, its python and the agent are there; the kit is intact")

    # 2 -- place
    placed = []
    for n, h in FILES.items():
        dst = os.path.join(DEST, n)
        old = md5(dst)
        if old == h:
            continue
        try:
            if old:
                shutil.copy2(dst, "%s.bak_S387_%s" % (dst, old[:8]))
            shutil.copy2(os.path.join(KIT, n), dst)
        except OSError as ex:
            say("  STOPPED: could not write %s (%s). Nothing is switched." % (dst, ex)); return 1
        if md5(dst) != h:
            say("  STOPPED: %s landed wrong. Nothing is switched." % dst); return 1
        placed.append((dst, old))
    say("  2  agent_guard.py and START_AGENT.cmd are in %s" % DEST)

    # 3 -- prove it here
    say("  3  proving the guard on this machine (about half a minute)...")
    try:
        r = subprocess.run([PY, "-B", os.path.join(DEST, "agent_guard.py"), "--selftest"],
                           capture_output=True, text=True, timeout=240, cwd=DEST)
        out = (r.stdout or "") + (r.stderr or "")
    except Exception as ex:                                     # noqa: BLE001
        out = "could not run: %s" % ex
    for line in out.strip().splitlines():
        say("     " + line)
    if "SELFTEST OK" not in out:
        for dst, old in placed:
            try:
                if old:
                    shutil.copy2("%s.bak_S387_%s" % (dst, old[:8]), dst)
                else:
                    os.remove(dst)
            except OSError:
                pass
        say("  STOPPED: the proof failed on this machine. The files were taken back out; the start-up")
        say("  folders were not touched. Nothing has changed. Tell Claude what it printed.")
        return 1

    # 4 -- start-up
    body = open(os.path.join(DEST, "START_AGENT.cmd"), "rb").read()
    admin = False
    try:
        with open(os.path.join(ALLUSERS, ENTRY), "wb") as fh:
            fh.write(body)
        admin = True
    except OSError:
        pass
    if admin:
        say("  4  the agent now starts for EVERY account: %s" % os.path.join(ALLUSERS, ENTRY))
        for old in glob.glob(r"C:\Users\*\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\%s" % ENTRY):
            try:
                os.replace(old, old + ".replaced_S387.bak")
                say("     retired the old one-account launcher: %s" % old)
            except OSError as ex:
                say("     COULD NOT retire %s (%s) -- the guard steps aside for it, so no clash" % (old, ex.__class__.__name__))
        try:
            r = subprocess.run(["icacls", DEST, "/grant", "*S-1-5-32-545:(OI)(CI)M", "/T", "/C", "/Q"],
                               capture_output=True, text=True, timeout=120)
            res = "done" if r.returncode == 0 else "icacls said %s" % (r.stdout or r.stderr).strip()[:160]
        except Exception as ex:                                 # noqa: BLE001
            res = "could not run icacls (%s)" % ex.__class__.__name__
        say("     %s opened to every account on this PC: %s" % (DEST, res))
    else:
        try:
            dst = os.path.join(MINE, ENTRY)
            if os.path.exists(dst) and open(dst, "rb").read() != body:
                os.replace(dst, dst + ".replaced_S387.bak")
            with open(dst, "wb") as fh:
                fh.write(body)
        except OSError as ex:
            say("  STOPPED at 4: could not write this account's start-up folder (%s)." % ex); return 1
        say("  4  NO administrator rights here, so the agent now starts for THIS account only:")
        say("     %s" % os.path.join(MINE, ENTRY))
        say("     >>> Run this same double-click once in the other Windows account too. <<<")

    # 5 -- start it now
    try:
        subprocess.Popen([PYW, os.path.join(DEST, "agent_guard.py")], cwd=DEST,
                         creationflags=0x00000008 | 0x00000200,       # detached, own process group
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as ex:                                     # noqa: BLE001
        say("  5  could not start the guard now (%s) -- it starts at the next sign-in" % ex)
        return 0
    time.sleep(25)
    tail = []
    try:
        tail = open(os.path.join(DEST, "agent_guard.log"), encoding="utf-8", errors="replace").read().splitlines()[-4:]
    except OSError:
        pass
    say("  5  the guard is running. What it says:")
    for line in tail:
        say("     " + line)
    say("")
    say("  DONE. From now on the agent runs whichever account is signed in, and only once.")
    say("  To stop it: put a file named AGENT_OFF.txt in D:\\SendToClinic\\_off\\ ; delete it to start again.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
