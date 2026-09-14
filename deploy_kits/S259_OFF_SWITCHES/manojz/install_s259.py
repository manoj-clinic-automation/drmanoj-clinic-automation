# -*- coding: utf-8 -*-
r"""install_s259.py -- Club C.2, the OFF switches, on MANOJZ.  (S259, 14-Sep-2026)

WHAT IT DOES, IN ORDER, AND IT STOPS AT THE FIRST THING THAT IS NOT AS EXPECTED

  1  reads the three live files and checks each one is EXACTLY the file this
     kit was built from (md5). A different file means someone changed it since,
     and this installer refuses rather than overwrite it.
  2  backs each one up beside itself as  <name>.bak_S259_<first 8 of its md5>
  3  copies the new versions in, and checks each landed byte-exact
  4  makes D:\Downloads\margsync\_off\ with its READ_ME, and puts
     TURN_OFF_ALL.bat / TURN_ON_ALL.bat in D:\Downloads\margsync\
  5  WALKS IT FOR REAL on this machine: switches everything off, runs both
     stock bats and the watchdog and proves each one did nothing and said so,
     switches back on, and proves the watchdog works again.
  6  if any part of the walk fails, it puts the backups back and says so.

It leaves the system SWITCHED ON. Run it as many times as you like.

    python install_s259.py              install and walk
    python install_s259.py --check      say what is there now; change nothing
"""
import argparse, hashlib, io, os, shutil, subprocess, sys

KIT = os.path.dirname(os.path.abspath(__file__))
MARGSYNC = r"D:\Downloads\margsync"
OFFDIR = os.path.join(MARGSYNC, "_off")

# kit file, live path, md5 BEFORE (what this kit was built from), md5 AFTER
FILES = [
    ("pull_watchdog.py", os.path.join(MARGSYNC, "MargPull", "pull_watchdog.py"),
     "f0eb9f40a0cd06875aba107b12151a73", "8d7fc79d12e3f8bbbdeaeb04289e0787"),
    ("PUSH_STOCK_DAILY.bat", os.path.join(MARGSYNC, "PUSH_STOCK_DAILY.bat"),
     "73a0635ba6164ec8da8c8f61de9d3210", "5c2a6c9098a783ef12f442e14697af34"),
    ("PUSH_STOCK_NIGHTLY.bat", os.path.join(MARGSYNC, "PUSH_STOCK_NIGHTLY.bat"),
     "99d05e3f7f05d472413c864d1665ccea", "c2492438c9f77169c418ac133513ad75"),
]
BESIDE = [("TURN_OFF_ALL.bat", MARGSYNC), ("TURN_ON_ALL.bat", MARGSYNC)]


def md5(path):
    try:
        return hashlib.md5(open(path, "rb").read()).hexdigest()
    except OSError:
        return ""


def say(m=""):
    print(m)
    sys.stdout.flush()


def check():
    say("  what is on this PC right now")
    for name, live, before, after in FILES:
        h = md5(live)
        state = ("the S259 version" if h == after else
                 "the version this kit was built from" if h == before else
                 "MISSING" if not h else "SOMETHING ELSE")
        say("    %-24s %s  %s" % (name, h[:8] or "--------", state))
    say("    _off folder              %s" % ("present" if os.path.isdir(OFFDIR) else "not there yet"))
    for name, dest in BESIDE:
        say("    %-24s %s" % (name, "present" if os.path.isfile(os.path.join(dest, name)) else "not there yet"))


def run(cmd, cwd=None):
    """Never raises. A step that could not run says so and counts as a failure."""
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=300)
        return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()
    except Exception as e:                                     # noqa: BLE001
        return -1, "could not run (%s: %s)" % (e.__class__.__name__, str(e)[:160])


def walk():
    """The live-shape walk, on this machine, with the switch really thrown."""
    ok = True
    def ck(n, c, d=""):
        nonlocal ok
        say(("    ok    " if c else "    FAIL  ") + n + (("   " + d[:160]) if not c and d else ""))
        ok = ok and c

    marker = os.path.join(OFFDIR, "ALL_OFF.txt")
    lastrun = os.path.join(MARGSYNC, "_analysis", "push_stock_lastrun.txt")
    before_lastrun = md5(lastrun)
    io.open(marker, "w").write("walk\n")
    try:
        return _walk_body(ck, marker, lastrun, before_lastrun) and ok
    finally:
        if os.path.isfile(marker):        # the walk NEVER leaves the switch off
            os.remove(marker)


def _walk_body(ck, marker, lastrun, before_lastrun):
    ok = True
    _ck = ck
    def ck(n, c, d=""):
        nonlocal ok
        _ck(n, c, d)
        ok = ok and c

    rc, out = run([os.path.join(MARGSYNC, "PUSH_STOCK_DAILY.bat")], cwd=MARGSYNC)
    ck("the daily stock push is off and says so", rc == 0 and "OFF" in out.upper(), "rc=%s %s" % (rc, out))
    ck("the daily stock push sent nothing", md5(lastrun) == before_lastrun)

    rc, out = run([os.path.join(MARGSYNC, "PUSH_STOCK_NIGHTLY.bat")], cwd=MARGSYNC)
    ck("the nightly stock push is off and says so", rc == 0 and "OFF" in out.upper(), "rc=%s %s" % (rc, out))
    ck("the nightly stock push sent nothing", md5(lastrun) == before_lastrun)

    wd = os.path.join(MARGSYNC, "MargPull", "pull_watchdog.py")
    rc, out = run([sys.executable, "-B", wd, "--dry-run", "--no-feed"])
    ck("the pull watchdog is off and says so", rc == 0 and "OFF" in out.upper(), "rc=%s %s" % (rc, out))

    os.remove(marker)
    rc, out = run([sys.executable, "-B", wd, "--dry-run", "--no-feed"])
    ck("switched back on, the watchdog works again -- nothing restarted",
       rc == 0 and "state=" in out, "rc=%s %s" % (rc, out))
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)

    say("S259 -- the OFF switches, on this PC")
    say("")
    if a.check:
        check()
        return 0

    if not os.path.isdir(MARGSYNC):
        say("  STOPPED: %s is not there. This runs on MANOJZ." % MARGSYNC)
        return 1

    # 1 -- the gate
    todo, already = [], 0
    for name, live, before, after in FILES:
        h = md5(live)
        if h == after:
            already += 1
        elif h == before:
            todo.append((name, live, before, after))
        else:
            say("  STOPPED: %s is not the file this kit was built from." % live)
            say("           it reads   %s" % (h or "(missing)"))
            say("           expected   %s" % before)
            say("  Nothing has been changed. Tell Claude what it reads.")
            return 2
    say("  1  the three live files are exactly what this kit was built from" if not already
        else "  1  %d of 3 already carry S259; %d to do" % (already, len(todo)))

    # 2 + 3 -- backup and install
    done = []
    for name, live, before, after in todo:
        bak = "%s.bak_S259_%s" % (live, before[:8])
        if not os.path.isfile(bak):
            shutil.copy2(live, bak)
        shutil.copy2(os.path.join(KIT, name), live)
        got = md5(live)
        if got != after:
            say("  STOPPED: %s landed as %s, expected %s" % (name, got, after))
            for n2, l2, b2, _a2 in done:
                shutil.copy2("%s.bak_S259_%s" % (l2, b2[:8]), l2)
            say("  Everything already copied has been put back.")
            return 3
        done.append((name, live, before, after))
        say("     installed %-24s -> %s   (backup .bak_S259_%s)" % (name, after[:8], before[:8]))
    if todo:
        say("  2  each one backed up beside itself first")
        say("  3  each one landed byte-exact")

    # 4 -- the folder, the README and the two double-clicks
    if not os.path.isdir(OFFDIR):
        os.makedirs(OFFDIR)
    shutil.copy2(os.path.join(KIT, "_off_READ_ME.txt"), os.path.join(OFFDIR, "READ_ME.txt"))
    for name, dest in BESIDE:
        shutil.copy2(os.path.join(KIT, name), os.path.join(dest, name))
    say("  4  %s is there, with its READ_ME, and both double-clicks are beside it" % OFFDIR)

    # 5 -- the walk
    say("  5  walking it for real -- the switch is actually thrown")
    walked = False
    try:
        walked = walk()
    except Exception as e:                                     # noqa: BLE001
        say("     the walk itself could not run (%s: %s)" % (e.__class__.__name__, str(e)[:160]))
    if not walked:
        say("")
        say("  THE WALK FAILED. Putting the old files back.")
        for name, live, before, after in done:
            shutil.copy2("%s.bak_S259_%s" % (live, before[:8]), live)
        try:
            os.remove(os.path.join(OFFDIR, "ALL_OFF.txt"))
        except OSError:
            pass
        say("  The three files are back as they were. Nothing is switched off.")
        return 4

    say("")
    say("  DONE, and everything is switched ON.")
    say("")
    say("  To switch it all off:   %s\\TURN_OFF_ALL.bat" % MARGSYNC)
    say("  To switch it back on:   %s\\TURN_ON_ALL.bat" % MARGSYNC)
    say("")
    for name, live, before, after in FILES:
        say("    %-24s %s" % (name, md5(live)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
