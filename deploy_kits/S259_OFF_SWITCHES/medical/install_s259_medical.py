# -*- coding: utf-8 -*-
r"""install_s259_medical.py -- SUPERSEDED. Kept as a record.  (S259, 14-Sep-2026)

THE SHARE IS READ-ONLY. This was built to send the OFF switches to the medical
PC over \\100.119.151.40\DDrive, and that share turned out to be reachable but
not writable -- its own step 1 says so and stops. The files went instead into
the clinic Drive kit folder, which is synced on this PC at
    H:\My Drive\Clinic Data Archive\ToMedical\_kit\
and the shop's agent installs them from there under its own md5 gate. Running
this file changes nothing; it is here so the route that was ruled out is on the
record with the reason.

RUNS ON MANOJZ. It reaches the medical PC over the Tailscale share the pull
already uses -- \\100.119.151.40\DDrive\SendToClinic -- so nothing goes near
Google Drive and nothing has to be typed at the shop's machine.

WHAT IT DOES, IN ORDER, STOPPING AT THE FIRST THING THAT IS NOT AS EXPECTED

  1  checks the share is reachable and writable
  2  checks marg_push.py and marg_watch.py over there are EXACTLY the files
     this kit was built from (md5). Anything else and it refuses.
  3  backs each one up beside itself as <name>.bak_S259_<first 8 of its md5>
  4  copies the new versions across, and checks each landed byte-exact
  5  makes D:\SendToClinic\_off\ with its READ_ME, and puts TURN_OFF_ALL.bat
     and TURN_ON_ALL.bat in D:\SendToClinic\
  6  PROVES the delivered files: runs their own selftests, then switches the
     sending off for real and proves the pusher does nothing and says so
  7  puts everything back if any of that fails, and leaves it switched ON

THE ONE THING IT CANNOT DO is restart the watcher on the shop's machine. The
new files are in place; they start being used the next time that machine's
watcher restarts -- which happens on its own at the next reboot or logon.
Capture and sending carry on exactly as before until then.

    python install_s259_medical.py              install and prove
    python install_s259_medical.py --check      say what is there now; change nothing
"""
import argparse, hashlib, io, os, shutil, subprocess, sys

KIT = os.path.dirname(os.path.abspath(__file__))
MED = r"\\100.119.151.40\DDrive\SendToClinic"
OFFDIR = os.path.join(MED, "_off")

FILES = [
    ("marg_push.py",  "marg_push.py",  "630fc5efeac89513d5b0d057df9e0639",
                                       "566e189e986128fa2ebb341a78b9ab65"),
    ("marg_watch.py", "marg_watch.py", "581ff3a7bc9493602172ef9765af2f2f",
                                       "9f0bf9c4c5fc285d339541ef3c76179f"),
]
BESIDE = [("TURN_OFF_ALL.bat", "TURN_OFF_ALL.bat"), ("TURN_ON_ALL.bat", "TURN_ON_ALL.bat")]


def md5(path):
    try:
        return hashlib.md5(open(path, "rb").read()).hexdigest()
    except OSError:
        return ""


def say(m=""):
    print(m)
    sys.stdout.flush()


def run(cmd, cwd=None):
    """Never raises. A step that could not run says so and counts as a failure."""
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=300)
        return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()
    except Exception as e:                                     # noqa: BLE001
        return -1, "could not run (%s: %s)" % (e.__class__.__name__, str(e)[:160])


def check():
    say("  what is on the medical PC right now")
    if not os.path.isdir(MED):
        say("    the share is NOT reachable: %s" % MED)
        return
    for name, dest_name, before, after in FILES:
        h = md5(os.path.join(MED, dest_name))
        state = ("the S259 version" if h == after else
                 "the version this kit was built from" if h == before else
                 "MISSING" if not h else "SOMETHING ELSE")
        say("    %-20s %s  %s" % (dest_name, h[:8] or "--------", state))
    say("    _off folder          %s" % ("present" if os.path.isdir(OFFDIR) else "not there yet"))
    for src, dest_name in BESIDE:
        say("    %-20s %s" % (dest_name,
            "present" if os.path.isfile(os.path.join(MED, dest_name)) else "not there yet"))


def walk():
    """Prove the files that were just delivered, from here, over the share."""
    ok = True
    def ck(n, c, d=""):
        nonlocal ok
        say(("    ok    " if c else "    FAIL  ") + n + (("   " + str(d)[:200]) if not c and d else ""))
        ok = ok and c

    push = os.path.join(MED, "marg_push.py")
    watch = os.path.join(MED, "marg_watch.py")

    rc, out = run([sys.executable, "-B", push, "--selftest"])
    ck("the delivered pusher proves itself (11 checks)",
       rc == 0 and "0 failed" in out, "rc=%s %s" % (rc, out[-300:]))
    rc, out = run([sys.executable, "-B", watch, "--selftest"])
    ck("the delivered watcher proves itself (6 checks)",
       rc == 0 and "FAIL" not in out.upper(), "rc=%s %s" % (rc, out[-300:]))

    marker = os.path.join(OFFDIR, "ALL_OFF.txt")
    io.open(marker, "w").write("walk\n")
    try:
        rc, out = run([sys.executable, "-B", push, "--once"])
        ck("switched off, the pusher sends nothing and says so",
           rc == 0 and "OFF" in out.upper(), "rc=%s %s" % (rc, out[-300:]))
        ck("switched off, it named the marker that did it",
           "ALL_OFF.txt" in out, out[-200:])
    finally:
        if os.path.isfile(marker):          # the walk NEVER leaves it switched off
            os.remove(marker)
    ck("the switch was put back on", not os.path.isfile(marker))
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)

    say("S259 -- the OFF switches on the MEDICAL PC, sent from this one")
    say("")
    if a.check:
        check()
        return 0

    # 1 -- the share
    if not os.path.isdir(MED):
        say("  STOPPED: cannot reach %s" % MED)
        say("  The medical PC is off, asleep, or Tailscale is down. Nothing was changed.")
        return 1
    probe = os.path.join(MED, "_s259_write_probe.tmp")
    try:
        io.open(probe, "w").write("x")
        os.remove(probe)
    except OSError as e:
        say("  STOPPED: the share is reachable but not writable (%s)" % e.__class__.__name__)
        say("  Nothing was changed.")
        return 1
    say("  1  the medical PC is reachable and writable over the share")

    # 2 -- the gate
    todo, already = [], 0
    for name, dest_name, before, after in FILES:
        dest = os.path.join(MED, dest_name)
        h = md5(dest)
        if h == after:
            already += 1
        elif h == before:
            todo.append((name, dest_name, before, after))
        else:
            say("  STOPPED: %s is not the file this kit was built from." % dest)
            say("           it reads   %s" % (h or "(missing)"))
            say("           expected   %s" % before)
            say("  Nothing has been changed. Tell Claude what it reads.")
            return 2
    say("  2  both files over there are exactly what this kit was built from" if not already
        else "  2  %d of 2 already carry S259; %d to do" % (already, len(todo)))

    # 3 + 4 -- backup and copy
    done = []
    for name, dest_name, before, after in todo:
        dest = os.path.join(MED, dest_name)
        bak = "%s.bak_S259_%s" % (dest, before[:8])
        try:
            if not os.path.isfile(bak):
                shutil.copy2(dest, bak)
            shutil.copy2(os.path.join(KIT, name), dest)
        except OSError as e:
            say("  STOPPED: could not write %s (%s)" % (dest, e.__class__.__name__))
            for n2, d2, b2, _a2 in done:
                shutil.copy2("%s.bak_S259_%s" % (os.path.join(MED, d2), b2[:8]),
                             os.path.join(MED, d2))
            say("  Everything already copied has been put back.")
            return 3
        got = md5(dest)
        if got != after:
            say("  STOPPED: %s landed as %s, expected %s" % (dest_name, got, after))
            for n2, d2, b2, _a2 in done:
                shutil.copy2("%s.bak_S259_%s" % (os.path.join(MED, d2), b2[:8]),
                             os.path.join(MED, d2))
            shutil.copy2(bak, dest)
            say("  Everything copied has been put back.")
            return 3
        done.append((name, dest_name, before, after))
        say("     sent %-16s -> %s   (backup .bak_S259_%s)" % (dest_name, after[:8], before[:8]))
    if todo:
        say("  3  each one backed up over there first")
        say("  4  each one landed byte-exact")

    # 5 -- the folder, the README and the two double-clicks
    try:
        if not os.path.isdir(OFFDIR):
            os.makedirs(OFFDIR)
        shutil.copy2(os.path.join(KIT, "_off_READ_ME.txt"), os.path.join(OFFDIR, "READ_ME.txt"))
        for src, dest_name in BESIDE:
            shutil.copy2(os.path.join(KIT, src), os.path.join(MED, dest_name))
    except OSError as e:
        say("  STOPPED at step 5: %s" % e)
        return 3
    say("  5  %s is there, with its READ_ME, and both double-clicks are beside it" % OFFDIR)

    # 6 -- the proof
    say("  6  proving the delivered files, from here, over the share")
    proved = False
    try:
        proved = walk()
    except Exception as e:                                     # noqa: BLE001
        say("     the proof itself could not run (%s: %s)" % (e.__class__.__name__, str(e)[:160]))
    if not proved:
        say("")
        say("  THE PROOF FAILED. Putting the old files back.")
        for name, dest_name, before, after in done:
            try:
                shutil.copy2("%s.bak_S259_%s" % (os.path.join(MED, dest_name), before[:8]),
                             os.path.join(MED, dest_name))
            except OSError:
                say("     COULD NOT RESTORE %s -- tell Claude" % dest_name)
        try:
            m = os.path.join(OFFDIR, "ALL_OFF.txt")
            if os.path.isfile(m):
                os.remove(m)
        except OSError:
            pass
        say("  Nothing is switched off.")
        return 4

    say("")
    say("  DONE, and everything is switched ON.")
    say("")
    say("  The new files are in place on the medical PC. They start being used")
    say("  the next time that machine's watcher restarts -- at its next reboot")
    say("  or logon. Until then capture and sending carry on exactly as before.")
    say("")
    say("  On the medical PC, to switch the SENDING off:  D:\\SendToClinic\\TURN_OFF_ALL.bat")
    say("  and to switch it back on:                      D:\\SendToClinic\\TURN_ON_ALL.bat")
    say("  Capture is never stopped by those -- see D:\\SendToClinic\\_off\\READ_ME.txt")
    say("")
    for name, dest_name, before, after in FILES:
        say("    %-20s %s" % (dest_name, md5(os.path.join(MED, dest_name))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
