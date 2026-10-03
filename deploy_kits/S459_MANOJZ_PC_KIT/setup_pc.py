#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
setup_pc.py -- kit S459_MANOJZ_PC_KIT. Puts the clinic's work back on DR MANOJ'S OWN PC after a
Windows reinstall. Run by the file the "Clinic PCs" page hands out; safe to run again.

Unlike the other PCs, almost nothing this PC needs is in a kit: it is this PC's own state -- the
follow-up tracker with its ledgers, the Marg pull and its settings, the nightly tools, the Docterz
archive, the scheduled tasks. Since S459 the 03:10 nightly zips all of that to the SSD
(F:\ClinicBackup\DrManojClinic_Automation\05_PC_STATE\manojz). THIS FILE RESTORES FROM THE NEWEST OF
THOSE ZIPS.

THE ONE RULE: IT ONLY PUTS BACK WHAT IS NOT THERE.
  * a folder is restored only if it does not exist (or is empty) -- a folder that is there is not
    opened, so on the working PC nothing is written;
  * a scheduled task is made again only if Task Scheduler has none of that name;
  * a Python package is installed only if Python does not have it.
So running it on the working PC is a read-only check, and that is how it is rehearsed.

In order:
  1  the kit is whole
  2  the SSD and the newest state zip (reopened, every CRC tested)
  3  the folders: tracker, Marg pull and settings, nightly tools, Docterz archive, Vitals
  4  the knowledge base (D:\Downloads\ClaudeCowork) from the newest nightly mirror, if absent
  5  Python's packages
  6  the scheduled tasks
  7  what only a person can do: said, with what this PC already has ticked

Standard library only. Prints counts and the names of folders, tasks and packages only.
"""
import argparse
import glob
import hashlib
import os
import re
import subprocess
import sys
import zipfile

VERSION = "S459.1"
IS_WIN = os.name == "nt"
STATE_DIR = os.environ.get("CLINIC_SETUP_STATE", r"F:\ClinicBackup\DrManojClinic_Automation\05_PC_STATE\manojz")
MIRROR_DIR = os.environ.get("CLINIC_SETUP_MIRRORS", r"F:\ClinicBackup\DrManojClinic_Automation\01_KB_MIRRORS")
ROOT_C = os.environ.get("CLINIC_SETUP_C", "C:\\")
ROOT_D = os.environ.get("CLINIC_SETUP_D", "D:\\")
SECTIONS = [  # (name in the zip, where it lives, loose files only?)
    ("tracker", (ROOT_C, "followup_tracker_local_test_kit", "local_test_kit", "followup_tracker"), False),
    ("margsync_config", (ROOT_D, "Downloads", "margsync", "_config"), False),
    ("margsync_MargPull", (ROOT_D, "Downloads", "margsync", "MargPull"), False),
    ("margsync_off", (ROOT_D, "Downloads", "margsync", "_off"), False),
    ("margsync_SendToClinic", (ROOT_D, "Downloads", "margsync", "SendToClinic"), False),
    ("margsync_analysis", (ROOT_D, "Downloads", "margsync", "_analysis"), False),
    ("margsync_top", (ROOT_D, "Downloads", "margsync"), True),
    ("DocterzArchive", (ROOT_D, "Downloads", "DocterzArchive"), False),
    ("kbtools", (ROOT_D, "Downloads", "_kbtools"), False),
    ("clinic_writer", (ROOT_D, "clinic_writer"), False),
]
KB_DIR = (ROOT_D, "Downloads", "ClaudeCowork")
CLONE = (ROOT_D, "dr-manoj-git", "drmanoj-clinic-automation")
CLONE_URL = "https://github.com/manoj-clinic-automation/drmanoj-clinic-automation.git"
# a task is one of the clinic's when the command it runs lives in one of these places
TASK_MARKS = ("\\downloads\\", "\\dr-manoj-git\\", "followup_tracker", "clinic_writer")
MEDICAL_HOST = "100.119.151.40"
_LOG = [None]
ATTENTION, PERSON = [], []
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def say(msg=""):
    print(msg)
    sys.stdout.flush()
    if _LOG[0]:
        try:
            with open(_LOG[0], "a", encoding="utf-8") as fh:
                fh.write(msg + "\n")
        except OSError:
            pass


def md5(path):
    try:
        h = hashlib.md5()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def run(cmd, timeout=120):
    """(rc, text); never raises. Replaced in the offline walk."""
    try:
        p = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=timeout, creationflags=NO_WINDOW)
        return p.returncode, p.stdout.decode("utf-8", "replace")
    except Exception as ex:                                    # noqa: BLE001
        return -1, "%s: %s" % (ex.__class__.__name__, ex)


def stop(why):
    say("")
    say("STOP: %s." % why)
    say("Nothing else was changed. Tell Claude what this window says.")
    return 1


def empty(folder, loose=False):
    """True when the folder is absent or holds nothing (for a loose-files section: holds no file)."""
    try:
        names = os.listdir(folder)
    except OSError:
        return True
    if loose:
        return not any(os.path.isfile(os.path.join(folder, n)) for n in names)
    return not names


def safe_members(z, prefix):
    out = []
    for n in z.namelist():
        if n.startswith(prefix) and not n.endswith("/"):
            rel = n[len(prefix):]
            if rel and ".." not in rel.split("/") and not rel.startswith("/") and ":" not in rel:
                out.append((n, rel))
    return out


def extract(z, members, dest):
    n = 0
    for name, rel in members:
        dst = os.path.join(dest, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with z.open(name) as src, open(dst, "wb") as out:
            for chunk in iter(lambda: src.read(1 << 20), b""):
                out.write(chunk)
        n += 1
    return n


def task_xml_for_this_user(raw, who):
    """A task definition as Windows exported it, with the old account's id replaced by this account."""
    for enc in ("utf-16", "utf-8-sig"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeError:
            continue
    else:
        return None, ""
    safe = who.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"<UserId>[^<]*</UserId>", lambda _m: "<UserId>%s</UserId>" % safe, text)
    return text.encode("utf-16"), text


def freeze_names(text):
    """{'flask': 'flask==3.1.3', ...} from pip-freeze lines (plain name==version rows only)."""
    out = {}
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"^([A-Za-z0-9_.\-]+)==([A-Za-z0-9_.\-+!]+)$", line)
        if m:
            out[m.group(1).lower().replace("_", "-")] = line
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--pyzip", default="")                     # not used on this PC; accepted so one setup file serves all
    ap.add_argument("--log", default="")
    a = ap.parse_args(argv)
    _LOG[0] = a.log or None
    kit = os.path.abspath(a.kit)
    who = "%s\\%s" % (os.environ.get("USERDOMAIN") or os.environ.get("COMPUTERNAME", ""), os.environ.get("USERNAME", ""))
    say("Setting up Dr Manoj's PC -- kit %s -- %s on %s" % (VERSION, os.environ.get("USERNAME", "?"), os.environ.get("COMPUTERNAME", "?")))
    say("")

    # 1 -- the kit
    try:
        rows = [l.rstrip("\r\n").split("  ", 1) for l in open(os.path.join(kit, "MD5SUMS.txt"), encoding="ascii") if l.strip()]
    except (OSError, ValueError):
        return stop("the kit has no readable MD5SUMS.txt")
    bad = [n for m, n in rows if md5(os.path.join(kit, n.replace("/", os.sep))) != m.strip().lower()]
    if bad or not rows:
        return stop("the kit is not whole -- not as listed: %s" % ", ".join(bad[:5]))
    say("  1 of 7  the kit is whole                      ok")

    # 2 -- the SSD and the newest state zip
    if IS_WIN and not os.path.isdir(ROOT_D):
        return stop("this PC has no D: drive -- the clinic's folders live on D:")
    zips = sorted(glob.glob(os.path.join(STATE_DIR, "manojz_state_*.zip")))
    if not zips:
        return stop("no state zip was found in %s -- plug in the ClinicBackup SSD (it must be F:) and press the button again" % STATE_DIR)
    state = zips[-1]
    try:
        z = zipfile.ZipFile(state)
        if z.testzip() is not None:
            raise zipfile.BadZipFile("a member failed its CRC")
    except (OSError, zipfile.BadZipFile) as ex:
        return stop("the newest state zip %s does not read back whole (%s)" % (os.path.basename(state), ex.__class__.__name__))
    say("  2 of 7  the newest state on the SSD           ok  (%s, %d files, every CRC tested)" % (os.path.basename(state), len(z.namelist())))

    # 3 -- the folders: only one that is not there
    say("  3 of 7  the folders")
    # decided for every folder BEFORE anything is written: restoring one must not make another look "already here"
    absent = {name: (empty(os.path.join(*where)) if not loose else (empty(os.path.join(*where)) and empty(os.path.join(*where), True)))
              for name, where, loose in SECTIONS}
    for name, where, loose in SECTIONS:
        dest = os.path.join(*where)
        members = safe_members(z, name + "/")
        if loose:
            members = [(n, rel) for n, rel in members if "/" not in rel]
        if not members:
            say("            %-22s not in the state zip -- nothing to restore" % name)
            if not os.path.isdir(dest):
                ATTENTION.append("%s is not on this PC and was not in the state zip" % dest)
            continue
        if not absent[name]:
            say("            %-22s already here, left alone" % name)
            continue
        try:
            n = extract(z, members, dest)
        except OSError as ex:
            return stop("could not restore %s into %s (%s)" % (name, dest, ex.__class__.__name__))
        say("            %-22s RESTORED, %d file(s) -> %s" % (name, n, dest))

    # 4 -- the knowledge base
    kb = os.path.join(*KB_DIR)
    if not empty(kb):
        say("  4 of 7  the knowledge base                    ok  (already here, left alone)")
    else:
        mirrors = sorted(glob.glob(os.path.join(MIRROR_DIR, "KB_mirror_ClaudeCowork_nightly_*.zip")))
        if not mirrors:
            say("  4 of 7  the knowledge base                    NOT RESTORED -- no nightly mirror in %s" % MIRROR_DIR)
            ATTENTION.append("D:\\Downloads\\ClaudeCowork is not here and no nightly mirror was found on the SSD")
        else:
            try:
                with zipfile.ZipFile(mirrors[-1]) as kz:
                    names = [n for n in kz.namelist() if not n.endswith("/")]
                    strip = "ClaudeCowork/" if names and all(n.startswith("ClaudeCowork/") for n in names) else ""
                    n = extract(kz, [(x, r) for x, r in safe_members(kz, strip)], kb)
                say("  4 of 7  the knowledge base                    RESTORED, %d file(s) from %s" % (n, os.path.basename(mirrors[-1])))
            except (OSError, zipfile.BadZipFile) as ex:
                say("  4 of 7  the knowledge base                    NOT RESTORED (%s)" % ex.__class__.__name__)
                ATTENTION.append("the knowledge base could not be restored from %s" % os.path.basename(mirrors[-1]))

    # 5 -- Python and its packages (the tracker and the Vitals tool need them; the nightly does not)
    want = {}
    try:
        facts = z.read("MACHINE_FACTS.txt").decode("utf-8", "replace")
        block = facts.split("== PYTHON PACKAGES", 1)[1].split("\n== ", 1)[0] if "== PYTHON PACKAGES" in facts else ""
        want = freeze_names("\n".join(l.strip() for l in block.splitlines()))
    except KeyError:
        pass
    rc, have_txt = run(["python", "-m", "pip", "freeze"], 120)
    if rc != 0:
        say("  5 of 7  Python's packages                     NOT DONE -- this PC has no Python on its PATH")
        PERSON.append("Python: install it from python.org with \"Add python.exe to PATH\" ticked, then press the button again")
    else:
        have = freeze_names(have_txt)
        missing = [want[k] for k in sorted(want) if k not in have]
        if not want:
            say("  5 of 7  Python's packages                     the state zip carries no list -- nothing to compare")
        elif not missing:
            say("  5 of 7  Python's packages                     ok  (all %d already here)" % len(want))
        else:
            rc, out = run(["python", "-m", "pip", "install", "--disable-pip-version-check"] + missing, 1500)
            if rc == 0:
                say("  5 of 7  Python's packages                     ok  (%d installed: %s)" % (len(missing), ", ".join(m.split("==")[0] for m in missing[:12])))
            else:
                say("  5 of 7  Python's packages                     %d could NOT be installed" % len(missing))
                ATTENTION.append("pip could not install: %s" % ", ".join(m.split("==")[0] for m in missing[:12]))

    # 6 -- the scheduled tasks: only one that Task Scheduler does not have
    made, there, failed, skipped = [], [], [], 0
    for name, rel in safe_members(z, "tasks/"):
        if not rel.lower().endswith(".xml"):
            continue
        xml, text = task_xml_for_this_user(z.read(name), who)
        if xml is None or not any(mark in text.lower() for mark in TASK_MARKS):
            skipped += 1
            continue
        task = rel[:-4]
        rc, _o = run(["schtasks", "/Query", "/TN", task], 30)
        if rc == 0:
            there.append(task)
            continue
        tmp = os.path.join(kit, "_task.xml")
        with open(tmp, "wb") as fh:
            fh.write(xml)
        rc, out = run(["schtasks", "/Create", "/TN", task, "/XML", tmp], 60)
        try:
            os.remove(tmp)
        except OSError:
            pass
        (made if rc == 0 else failed).append(task)
    say("  6 of 7  the scheduled tasks                   %s  (%d already there, %d made again, %d could not be made; %d of Windows' own not touched)"
        % ("ok" if not failed else "LOOK", len(there), len(made), len(failed), skipped))
    for t in made:
        say("            made again: %s" % t)
    for t in failed:
        say("            NOT made: %s" % t)
    if failed:
        ATTENTION.append("%d task(s) need an administrator: right-click the downloaded setup file, Run as administrator, once more "
                         "(%s)" % (len(failed), ", ".join(failed[:6])))

    # 7 -- what only a person can do
    say("  7 of 7  what only a person can do")
    def tick(ok, words):
        say("            [%s] %s" % ("x" if ok else " ", words))
        if not ok:
            PERSON.append(words)
    rc_git, _o = run(["git", "--version"], 30)
    tick(rc_git == 0, "Git for Windows installed")
    tick(os.path.isdir(os.path.join(*CLONE, ".git")), "the repository at %s  (git clone %s , after signing in to GitHub)" % (os.path.join(*CLONE), CLONE_URL))
    tick(os.path.isdir("H:\\My Drive") if IS_WIN else False, "Google Drive for desktop, the clinic account, as drive H:")
    rc_ts, _o = run(["tailscale", "status"], 30)
    tick(rc_ts == 0, "Tailscale signed in")
    rc_ck, out_ck = run(["cmdkey", "/list"], 30)
    tick(rc_ck == 0 and MEDICAL_HOST in out_ck, "the Medical PC's share login stored on this PC (Claude gives the one line; the password is yours)")
    tick(False, "the Claude desktop app, with the folders connected again  (not something this file can see)")

    say("")
    say("DONE. Everything this file can put back is back.")
    if ATTENTION:
        say("")
        say("LOOK AT THESE:")
        for line in ATTENTION:
            say("  * " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
