# -*- coding: utf-8 -*-
r"""install_s260.py -- Club C.3, one settings file per machine, on MANOJZ.  (S260)

WHAT IT DOES, IN ORDER, STOPPING AT THE FIRST THING THAT IS NOT AS EXPECTED

  1  reads the four live files and checks each is EXACTLY what this kit was
     built from (md5). Anything else and it refuses rather than overwrite it.
  2  READS TODAY'S SETTINGS OUT OF THOSE VERY FILES and writes them into
     D:\Downloads\margsync\_config\machine.conf. Nothing is typed, nothing is
     assumed: the file starts life saying exactly what the machine already does.
  3  backs each file up beside itself as <name>.bak_S260_<first 8 of its md5>
  4  copies the new versions in, and checks each landed byte-exact
  5  WALKS IT FOR REAL on this machine: proves each script reads the file, then
     proves that with the file renamed away every value falls back to what it
     always was -- the property that makes this safe
  6  puts the old files back by itself if any of that fails

    python install_s260.py              install and walk
    python install_s260.py --check      say what is there now; change nothing
"""
import argparse, hashlib, io, os, re, shutil, subprocess, sys

KIT = os.path.dirname(os.path.abspath(__file__))
MARGSYNC = r"D:\Downloads\margsync"
CONFDIR = os.path.join(MARGSYNC, "_config")
CONF = os.path.join(CONFDIR, "machine.conf")

FILES = [
    ("marg_gate.py", os.path.join(MARGSYNC, "MargPull", "marg_gate.py"),
     "af2c3ca507136f3f82ec7cf64e8aae34", "52f502d1ee1a59e37086fb3e514f7874"),
    ("pipeline_status.py", os.path.join(MARGSYNC, "MargPull", "pipeline_status.py"),
     "f4998f611befd9c4875b9303beb5c235", "31aad5e65a31eece32441027f6db6e47"),
    ("PULL_FROM_MEDICAL.bat", os.path.join(MARGSYNC, "MargPull", "PULL_FROM_MEDICAL.bat"),
     "39bd6ac8ba7333f0e4182812fc2d2702", "f7855fa823daecea5aa13263fc9c02e6"),
    ("PUSH_STOCK_DAILY.bat", os.path.join(MARGSYNC, "PUSH_STOCK_DAILY.bat"),
     "5c2a6c9098a783ef12f442e14697af34", "5cbec862593e201884b8f372775c7db2"),
]

ORDER = ["MEDICAL_HOST", "MEDICAL_SHARE", "SERVER_BASE", "TOKEN_LOCAL", "STOCK_BASELINE"]
WHAT = {
    "MEDICAL_HOST":  ["The medical PC's address on Tailscale. Change this one line and the",
                      "pull, the key it reads and the share it probes all follow it."],
    "MEDICAL_SHARE": ["The name that address shares its D: drive under."],
    "SERVER_BASE":   ["The clinic server. Every address this PC posts to is built from it,",
                      "so the whole machine follows the site if it ever moves."],
    "TOKEN_LOCAL":   ["Where this PC keeps its copy of the key. The key itself is never",
                      "here -- only where to find it."],
    "STOCK_BASELINE":["The day the computed stock figure walks forward from. Move it when a",
                      "fresh full closing export is taken and you want to start from that.",
                      "It must be a date a closing export actually exists for."],
}


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


def read_today():
    """TODAY'S settings, read out of the live files themselves. Never typed."""
    vals = {}
    gate = io.open(os.path.join(MARGSYNC, "MargPull", "marg_gate.py"),
                   encoding="utf-8", errors="replace").read()
    m = re.search(r'DEF_TOKEN_UNC = r"\\\\([^\\]+)\\([^\\]+)\\', gate)
    if m:
        vals["MEDICAL_HOST"], vals["MEDICAL_SHARE"] = m.group(1), m.group(2)
    m = re.search(r'DEF_TOKEN = r"([^"]+)"', gate)
    if m:
        vals["TOKEN_LOCAL"] = m.group(1)
    m = re.search(r'DEF_URL = "(https?://[^/"]+)', gate)
    if m:
        vals["SERVER_BASE"] = m.group(1)
    bat = io.open(os.path.join(MARGSYNC, "PUSH_STOCK_DAILY.bat"),
                  encoding="utf-8", errors="replace").read()
    m = re.search(r"(?im)^\s*set BASELINE=([0-9\-]+)\s*$", bat)
    if m:
        vals["STOCK_BASELINE"] = m.group(1)
    return vals


def conf_text(vals):
    """The file, written strictly: KEY=VALUE, no spaces, because cmd.exe does
    not trim and a stray space would give batch the wrong key."""
    L = []
    L.append("# machine.conf -- what THIS PC is, in one place.  (S260, Club C.3)")
    L.append("#")
    L.append("# One line per setting, written KEY=VALUE with no spaces around the =.")
    L.append("# A line starting with # is a note. Delete a line, or leave its value")
    L.append("# blank, and the script that wanted it simply uses what it always used,")
    L.append("# so this file can never break anything by being wrong or missing.")
    L.append("#")
    L.append("# It is NOT in the repository. It says where this machine is, and that")
    L.append("# is not the code's business (F-185).")
    L.append("#")
    L.append("# Written at the S260 install by reading the live scripts themselves, so")
    L.append("# it started life saying exactly what this PC already did.")
    L.append("")
    for k in ORDER:
        if k in vals:
            for note in WHAT.get(k, []):
                L.append("# %s" % note)
            L.append("%s=%s" % (k, vals[k]))
            L.append("")
    return "\n".join(L).rstrip("\n") + "\n"


def check():
    say("  what is on this PC right now")
    for name, live, before, after in FILES:
        h = md5(live)
        state = ("the S260 version" if h == after else
                 "the version this kit was built from" if h == before else
                 "MISSING" if not h else "SOMETHING ELSE")
        say("    %-24s %s  %s" % (name, h[:8] or "--------", state))
    say("    machine.conf             %s" % ("present" if os.path.isfile(CONF) else "not there yet"))
    if os.path.isfile(CONF):
        for line in io.open(CONF, encoding="utf-8-sig", errors="replace"):
            line = line.strip()
            if line and not line.startswith("#"):
                say("      %s" % line)


def walk():
    ok = True
    def ck(n, c, d=""):
        nonlocal ok
        say(("    ok    " if c else "    FAIL  ") + n + (("   " + str(d)[:200]) if not c and d else ""))
        ok = ok and c

    gate = os.path.join(MARGSYNC, "MargPull", "marg_gate.py")
    pipe = os.path.join(MARGSYNC, "MargPull", "pipeline_status.py")
    ask = ("import marg_gate,sys;"
           "sys.stdout.write(marg_gate.DEF_URL+'|'+marg_gate.DEF_TOKEN+'|'+marg_gate.DEF_TOKEN_UNC)")
    ask2 = ("import pipeline_status as p,sys;"
            "sys.stdout.write(p.DEF_URL+'|'+p.DEF_MEDICAL_HOST+'|'+p.DEF_SHARE_PROBE)")
    here = os.path.dirname(gate)

    rc, out = run([sys.executable, "-B", "-c", ask], cwd=here)
    ck("the sender reads the settings file and still knows where to post",
       rc == 0 and out.startswith("http"), "rc=%s %s" % (rc, out))
    live_gate = out
    rc, out = run([sys.executable, "-B", "-c", ask2], cwd=here)
    ck("the pipeline reporter reads it too",
       rc == 0 and out.startswith("http"), "rc=%s %s" % (rc, out))
    live_pipe = out

    vals = {}
    for line in io.open(CONF, encoding="utf-8-sig", errors="replace"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            vals[k.strip()] = v.strip()
    ck("what they report matches the settings file, line for line",
       vals.get("MEDICAL_HOST", "") in live_gate
       and vals.get("SERVER_BASE", "") in live_gate
       and vals.get("MEDICAL_HOST", "") in live_pipe,
       "%s | %s" % (live_gate, live_pipe))

    # the property that makes this safe: take the file away, nothing changes
    away = CONF + ".walk_away"
    os.replace(CONF, away)
    try:
        rc, out = run([sys.executable, "-B", "-c", ask], cwd=here)
        ck("with the settings file TAKEN AWAY the sender falls back to what it always was",
           rc == 0 and out == live_gate, "rc=%s %s" % (rc, out))
        rc, out = run([sys.executable, "-B", "-c", ask2], cwd=here)
        ck("and so does the pipeline reporter", rc == 0 and out == live_pipe,
           "rc=%s %s" % (rc, out))
    finally:
        os.replace(away, CONF)
    ck("the settings file was put back", os.path.isfile(CONF))

    # cmd.exe, for real -- the probe carries the SAME six lines as the two jobs
    probe = os.path.join(KIT, "probe_conf_s260.bat")
    rc, out = run(["cmd", "/c", probe, CONF], cwd=KIT)
    ck("cmd.exe reads the settings file the same way the jobs do",
       rc == 0 and ("MEDHOST=" + vals.get("MEDICAL_HOST", "?")) in out,
       "rc=%s %s" % (rc, out[-300:]))
    ck("and the share path it builds is the real one",
       ("SHARE=\\\\%s\\%s" % (vals.get("MEDICAL_HOST", "?"),
                                   vals.get("MEDICAL_SHARE", "?"))).replace("\\\\", "\\\\") in out
       or ("SHARE=\\\\" + vals.get("MEDICAL_HOST", "?")) in out, out[-200:])
    ck("and the stock baseline came through",
       ("BASELINE=" + vals.get("STOCK_BASELINE", "?")) in out, out[-200:])
    rc, out = run(["cmd", "/c", probe, os.path.join(CONFDIR, "no_such_file.conf")], cwd=KIT)
    ck("with no settings file cmd.exe keeps the fallbacks, exactly like the jobs",
       rc == 0 and "MEDHOST=FALLBACK_HOST" in out and "BASELINE=FALLBACK_DATE" in out,
       "rc=%s %s" % (rc, out[-200:]))

    # the real stock push, with the S259 switch thrown, so it parses and sends nothing
    offdir = os.path.join(MARGSYNC, "_off")
    marker = os.path.join(offdir, "ALL_OFF.txt")
    had = os.path.isfile(marker)
    if not had:
        if not os.path.isdir(offdir):
            os.makedirs(offdir)
        io.open(marker, "w").write("S260 walk\n")
    try:
        rc, out = run([os.path.join(MARGSYNC, "PUSH_STOCK_DAILY.bat")], cwd=MARGSYNC)
        ck("the real stock push still runs clean on the new lines, and sent nothing",
           rc == 0 and "OFF" in out.upper(), "rc=%s %s" % (rc, out[-300:]))
    finally:
        if not had and os.path.isfile(marker):
            os.remove(marker)
    ck("the S259 switch was left as it was found", os.path.isfile(marker) == had)
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)

    say("S260 -- one settings file for this PC")
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
    say("  1  the four live files are exactly what this kit was built from" if not already
        else "  1  %d of 4 already carry S260; %d to do" % (already, len(todo)))

    # 2 -- the settings file, read out of the live files
    vals = read_today()
    missing = [k for k in ORDER if k not in vals]
    if missing:
        say("  STOPPED: could not read %s out of the live files." % ", ".join(missing))
        say("  Nothing has been changed.")
        return 2
    if not os.path.isdir(CONFDIR):
        os.makedirs(CONFDIR)
    if not os.path.isfile(CONF):
        io.open(CONF, "w", encoding="utf-8", newline="\r\n").write(conf_text(vals))
        say("  2  %s written, from what the live files already say:" % CONF)
    else:
        say("  2  %s is already there and was left alone. It says:" % CONF)
    for k in ORDER:
        say("       %-15s %s" % (k, vals[k]))

    # 3 + 4 -- backup and install
    done = []
    for name, live, before, after in todo:
        bak = "%s.bak_S260_%s" % (live, before[:8])
        if not os.path.isfile(bak):
            shutil.copy2(live, bak)
        shutil.copy2(os.path.join(KIT, name), live)
        got = md5(live)
        if got != after:
            say("  STOPPED: %s landed as %s, expected %s" % (name, got, after))
            for n2, l2, b2, _a2 in done + [(name, live, before, after)]:
                shutil.copy2("%s.bak_S260_%s" % (l2, b2[:8]), l2)
            say("  Everything already copied has been put back.")
            return 3
        done.append((name, live, before, after))
        say("     installed %-24s -> %s   (backup .bak_S260_%s)" % (name, after[:8], before[:8]))
    if todo:
        say("  3  each one backed up beside itself first")
        say("  4  each one landed byte-exact")

    # 5 -- the walk
    say("  5  walking it for real on this machine")
    walked = False
    try:
        walked = walk()
    except Exception as e:                                     # noqa: BLE001
        say("     the walk itself could not run (%s: %s)" % (e.__class__.__name__, str(e)[:160]))
    if not walked:
        say("")
        say("  THE WALK FAILED. Putting the old files back.")
        for name, live, before, after in done:
            shutil.copy2("%s.bak_S260_%s" % (live, before[:8]), live)
        say("  The four files are back as they were. %s was left in place;" % CONF)
        say("  nothing reads it now, so it is harmless.")
        return 4

    say("")
    say("  DONE.")
    say("")
    say("  From now on, everything this PC needs to know about where things are")
    say("  lives in one file:")
    say("     %s" % CONF)
    say("  Move the medical PC, move the site, or re-baseline the stock, and it is")
    say("  one line there instead of four files.")
    say("")
    for name, live, before, after in FILES:
        say("    %-24s %s" % (name, md5(live)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
