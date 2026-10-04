#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
rehearse_pc_kits.py -- kit S477_PC_KITS_REHEARSAL (session 294, 04-Oct-2026). The scratch-folder rehearsal, on a real
Windows, of the two setup kits the "Clinic PCs & phones" page hands out but nobody has yet run on Windows:
   S458  the Medical PC's kit   (deploy_kits/PC_KITS/medical/kit.zip)
   S459  Dr Manoj's PC's kit    (deploy_kits/PC_KITS/manojz/kit.zip)
It is run ONCE by NIGHTLY.bat on Dr Manoj's PC (its last step), because that is the Windows the assistant can run a
program on without handing the owner a step. It does what ClinicSetup_<PC>.cmd does after its download, with the same
Windows tools (certutil for the md5, tar.exe to unpack, the kit's own Python 3.11.9 to run setup_pc.py) -- but every
place the installers write is pointed at a scratch folder through the knobs the installers already have:

   the Medical kit   CLINIC_SETUP_TARGET / _ALLUSERS / _MINE -> scratch;  --no-start (no agent is started here)
   Dr Manoj's kit    CLINIC_SETUP_C / CLINIC_SETUP_D -> scratch; the state zip and the knowledge-base mirror are READ
                     from the SSD where they are; and the installer's run() is wrapped so that a 'pip install' or a
                     'schtasks /Create' is NOT run and is written down instead (on this PC neither is expected:
                     every package and every task is already here).

WHAT IT CHANGES ON THIS PC: nothing outside its scratch folder (default D:\Downloads\_r477), which it removes at the
end, and its report beside this file, PC_KITS_REHEARSAL_LATEST.txt (counts and the names of tools, folders and tasks'
counts only -- no patient, no number, no secret). The restored copy of this PC's state (which holds patient data and
keys) exists only inside the scratch folder, on this same disk, for the minutes the rehearsal runs.
It never fails the nightly: any error ends in the report as RED and exit code 0. NIGHTLY.bat calls it every night; once
its report exists it only sweeps a scratch folder a cut run may have left, and returns. To run the rehearsal again,
move the report aside.

    python rehearse_pc_kits.py --tools D:\Downloads\_kbtools
        [--repo D:\dr-manoj-git\drmanoj-clinic-automation] [--scratch D:\Downloads\_r477] [--force]
Standard library only.
"""
import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import time
import zipfile

VERSION = "S477.1"
IS_WIN = os.name == "nt"
REPORT = "PC_KITS_REHEARSAL_LATEST.txt"
SCRATCH_MARK = "_r477"
CHILD_TIMEOUT = 4200                    # more than the sum of the inner limits below; a hang is cut, never waited out
LOCK = "PC_KITS_REHEARSAL.lock"
NOWIN = 0x08000000 if IS_WIN else 0
LINES, REDS, CHECKS = [], [], [0]

WRAP = r'''# -*- coding: utf-8 -*-
# written by rehearse_pc_kits.py: runs the kit's own setup_pc.main() with its run() wrapped, so that a command that
# would change this PC (pip install, schtasks /Create) is not run and is written down instead.
import json, os, sys
kit, log, blocked_path = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, kit)
import setup_pc
_real = setup_pc.run
blocked = []
def guarded(cmd, timeout=120):
    low = [str(c).lower() for c in cmd]
    if ("pip" in low and "install" in low) or "/create" in low or "/delete" in low or "/change" in low:
        blocked.append(low[:6])
        with open(blocked_path, "w", encoding="utf-8") as fh:
            json.dump(blocked, fh)
        return 0, "REHEARSAL: not run"
    return _real(cmd, timeout)
setup_pc.run = guarded
with open(blocked_path, "w", encoding="utf-8") as fh:
    json.dump(blocked, fh)
sys.exit(setup_pc.main(["--kit", kit, "--log", log]))
'''


def say(msg=""):
    LINES.append(msg)


def check(name, ok, detail=""):
    CHECKS[0] += 1
    say("  %s  %s%s" % ("ok " if ok else "RED", name, ("  -- " + str(detail)[:300]) if (detail and not ok) else ""))
    if not ok:
        REDS.append(name)
    return ok


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def run(cmd, timeout=600, env=None, cwd=None, quiet=False):
    """(rc, output). Never raises. quiet=True sends the output to NUL (F-698: a rehearsal reads the installer's log file)."""
    try:
        p = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=(subprocess.DEVNULL if quiet else subprocess.PIPE),
                           stderr=(subprocess.DEVNULL if quiet else subprocess.STDOUT), timeout=timeout, env=env, cwd=cwd,
                           creationflags=NOWIN)
        return p.returncode, ("" if quiet else p.stdout.decode("utf-8", "replace"))
    except Exception as ex:                                  # noqa: BLE001
        return 999, "%s: %s" % (ex.__class__.__name__, ex)


def _rw(func, path, _exc):
    try:
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
        func(path)
    except OSError:
        pass


def safe_scratch(path):
    """The only folder this file ever deletes: its own, by name, two levels or more below a drive root."""
    p = os.path.abspath(path)
    parts = [x for x in p.replace("\\", "/").split("/") if x]
    return os.path.basename(p) == SCRATCH_MARK and len(parts) >= 3


def wipe(scratch):
    if not safe_scratch(scratch):
        return False
    for _ in range(10):                                      # an antivirus handle or a process still ending: wait and try again
        if not os.path.exists(scratch):
            return True
        shutil.rmtree(scratch, onerror=_rw)
        if not os.path.exists(scratch):
            return True
        time.sleep(3)
    return not os.path.exists(scratch)


def read(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def kit_info(folder):
    out = {}
    for line in read(os.path.join(folder, "KIT_INFO.txt")).splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def unpack(zip_path, dest, tar):
    """As the .cmd does it: tar.exe -xf <zip> -C <dest>. Off Windows (the offline test) Python's zipfile stands in."""
    os.makedirs(dest, exist_ok=True)
    if tar:
        rc, out = run([tar, "-xf", zip_path, "-C", dest], 900)
        return rc == 0, out[-200:]
    try:
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(dest)
        return True, ""
    except Exception as ex:                                  # noqa: BLE001
        return False, str(ex)


def certutil_md5(path):
    """The .cmd's own :md5of -- the second line of certutil's answer, spaces removed."""
    rc, out = run(["certutil", "-hashfile", path, "MD5"], 300)
    lines = [l.strip() for l in out.splitlines() if l.strip()]
    return (lines[1].replace(" ", "").lower() if rc == 0 and len(lines) > 1 else "")


def startup_names():
    dirs = [os.path.join(os.environ.get("ProgramData", r"C:\ProgramData"), "Microsoft", "Windows", "Start Menu", "Programs", "StartUp"),
            os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")]
    out = []
    for d in dirs:
        try:
            out.append(sorted((n, os.path.getsize(os.path.join(d, n))) for n in os.listdir(d)))
        except OSError:
            out.append(None)
    return out


def medical(a, W, S, py, tar):
    say("")
    say("== THE MEDICAL PC'S KIT (S458) -- into a scratch folder, no agent started")
    info = kit_info(os.path.join(a.repo, "deploy_kits", "PC_KITS", "medical"))
    kz = os.path.join(a.repo, "deploy_kits", "PC_KITS", "medical", "kit.zip")
    if not check("the kit the page serves is the one its KIT_INFO names (%s)" % info.get("version", "?"), os.path.isfile(kz) and md5(kz) == info.get("kit_md5")):
        return
    kit = os.path.join(W, "med", "kit")
    ok, why = unpack(kz, kit, tar)
    if not check("unpacked as the setup file unpacks it (%s)" % ("tar.exe" if tar else "zipfile, off Windows"), ok and os.path.isfile(os.path.join(kit, "setup_pc.py")), why):
        return
    payload = []
    for base, _d, files in os.walk(os.path.join(kit, "payload")):
        payload += [os.path.join(base, f) for f in files]
    target = os.path.join(S, "med", "SendToClinic")
    env = dict(os.environ, CLINIC_SETUP_TARGET=target, CLINIC_SETUP_ALLUSERS=os.path.join(S, "med", "startup_all"), CLINIC_SETUP_MINE=os.path.join(S, "med", "startup_mine"))
    before = startup_names()
    log1 = os.path.join(S, "med", "install_log_1.txt")
    os.makedirs(os.path.dirname(log1), exist_ok=True)
    rc, _o = run([py, "-B", os.path.join(kit, "setup_pc.py"), "--kit", kit, "--pyzip", a.pyzip, "--log", log1, "--no-start"], 600, env=env, quiet=True)
    t = read(log1)
    check("first run ends 0 and says DONE", rc == 0 and "DONE. The clinic's tools are in place" in t, "rc %s · %s" % (rc, t[-300:]))
    for want in ("1 of 6  the kit is whole", "2 of 6", "3 of 6  its own Python", "4 of 6  the tools", "5 of 6  start at every sign-in", "6 of 6  the agent"):
        check("the log carries step '%s'" % want, want in t)
    check("its own Python was unpacked into the scratch target", "(unpacked," in t and os.path.isfile(os.path.join(target, "pyportable", "python.exe")), t[:400])
    check("every tool of the kit was placed (%d) and none 'kept'" % len(payload), "(%d placed, 0 already here and the same, 0 kept" % len(payload) in t, [l for l in t.splitlines() if "4 of 6" in l])
    check("the start-up entry went to the SCRATCH start-up folder, as the kit's starter", os.path.isfile(os.path.join(S, "med", "startup_mine", "MargAgent.cmd"))
          and md5(os.path.join(S, "med", "startup_mine", "MargAgent.cmd")) == md5(os.path.join(target, "START_AGENT.cmd")))
    check("the agent was not started (asked not to)", "not started (asked not to)" in t and not os.path.exists(os.path.join(target, "heartbeat.txt")))
    check("this PC's real start-up folders are exactly as before", startup_names() == before)
    check("no token, no capture, no log was made in the target", not any(os.path.exists(os.path.join(target, n)) for n in ("token.txt", "_captured", "agent_guard.log")))
    if IS_WIN:
        tpy = os.path.join(target, "pyportable", "python.exe")
        rc, out = run([tpy, "-c", "import sys; print(sys.version.split()[0])"], 120)
        check("the unpacked Python runs on this Windows and is 3.11.9", rc == 0 and out.strip() == "3.11.9", out[:200])
        pys = [p for p in payload if p.lower().endswith(".py")]
        bad = []
        for p in pys:
            dst = os.path.join(target, os.path.relpath(p, os.path.join(kit, "payload")))
            rc, out = run([tpy, "-B", "-c", "import sys; compile(open(sys.argv[1], 'rb').read(), sys.argv[1], 'exec')", dst], 120)
            if rc != 0:
                bad.append(os.path.basename(p))
        check("every Python tool placed (%d) compiles under that Python" % len(pys), not bad, bad)
    log2 = os.path.join(S, "med", "install_log_2.txt")
    rc, _o = run([py, "-B", os.path.join(kit, "setup_pc.py"), "--kit", kit, "--pyzip", a.pyzip, "--log", log2, "--no-start"], 600, env=env, quiet=True)
    t2 = read(log2)
    check("second run places nothing: every tool 'already here and the same'", rc == 0 and "(0 placed, %d already here and the same, 0 kept" % len(payload) in t2,
          [l for l in t2.splitlines() if "4 of 6" in l])
    check("second run leaves the Python and the start-up entry alone", "(already there, left alone)" in t2 and "(already set" in t2)
    say("     (%d tools; the first log %d lines, the second %d)" % (len(payload), len(t.splitlines()), len(t2.splitlines())))


def manojz(a, W, S, py, tar):
    say("")
    say("== DR MANOJ'S PC'S KIT (S459) -- restored into a scratch C: and D:, nothing installed, no task made")
    info = kit_info(os.path.join(a.repo, "deploy_kits", "PC_KITS", "manojz"))
    kz = os.path.join(a.repo, "deploy_kits", "PC_KITS", "manojz", "kit.zip")
    if not check("the kit the page serves is the one its KIT_INFO names (%s)" % info.get("version", "?"), os.path.isfile(kz) and md5(kz) == info.get("kit_md5")):
        return
    kit = os.path.join(W, "mz", "kit")
    ok, why = unpack(kz, kit, tar)
    if not check("unpacked as the setup file unpacks it", ok and os.path.isfile(os.path.join(kit, "setup_pc.py")), why):
        return
    C, D = os.path.join(S, "mz", "C") + os.sep, os.path.join(S, "mz", "D") + os.sep
    os.makedirs(C); os.makedirs(D)
    env = dict(os.environ, CLINIC_SETUP_C=C, CLINIC_SETUP_D=D)
    if a.state:
        env["CLINIC_SETUP_STATE"] = a.state
    if a.mirrors:
        env["CLINIC_SETUP_MIRRORS"] = a.mirrors
    state_dir = a.state or r"F:\ClinicBackup\DrManojClinic_Automation\05_PC_STATE\manojz"
    zips = sorted(n for n in (os.listdir(state_dir) if os.path.isdir(state_dir) else []) if n.startswith("manojz_state_") and n.endswith(".zip"))
    if not check("the SSD's state folder is in reach and holds a state zip", bool(zips), state_dir):
        return
    z = zipfile.ZipFile(os.path.join(state_dir, zips[-1]))
    names = [i for i in z.infolist() if not i.filename.endswith("/")]
    tasks = [i for i in names if i.filename.startswith("tasks/") and i.filename.lower().endswith(".xml")]
    say("     the newest state zip: %s · %d files · %d task definitions" % (zips[-1], len(names), len(tasks)))
    wrap = os.path.join(W, "mz", "run_guarded.py")
    with open(wrap, "w", encoding="utf-8") as fh:
        fh.write(WRAP)
    blocked_path = os.path.join(S, "mz", "blocked.json")
    log1 = os.path.join(S, "mz", "install_log_1.txt")
    t0 = time.time()
    rc, _o = run([py, "-B", wrap, kit, log1, blocked_path], 1500, env=env, quiet=True)
    t = read(log1)
    check("first run ends 0 and says DONE (%.0f s)" % (time.time() - t0), rc == 0 and "DONE. Everything this file can put back is back." in t, "rc %s · %s" % (rc, t[-400:]))
    for want in ("1 of 7  the kit is whole", "2 of 7  the newest state on the SSD", "3 of 7  the folders", "4 of 7  the knowledge base", "5 of 7  Python's packages", "6 of 7  the scheduled tasks", "7 of 7"):
        check("the log carries step '%s'" % want, want in t)
    check("the state zip it chose is the newest, every CRC tested", zips[-1] in t and "every CRC tested" in t)
    restored = [l.split()[0] for l in t.splitlines() if " RESTORED, " in l and "knowledge base" not in l]
    notin = [l.split()[0] for l in t.splitlines() if "not in the state zip" in l and not l.strip().startswith("*")]
    left = [l.split()[0] for l in t.splitlines() if "already here, left alone" in l and "of 7" not in l]
    say("     folders: %d restored (%s) · %d not in the zip (%s) · %d 'already here'" % (len(restored), ", ".join(restored), len(notin), ", ".join(notin) or "-", len(left)))
    check("no folder was 'already here' in an empty scratch, and none failed", not left and "could not restore" not in t, left)
    # every restored file against the zip: there, and the zip's own size and CRC
    import zlib
    sections = {"tracker": (C, "followup_tracker_local_test_kit", "local_test_kit", "followup_tracker"), "margsync_config": (D, "Downloads", "margsync", "_config"),
                "margsync_MargPull": (D, "Downloads", "margsync", "MargPull"), "margsync_off": (D, "Downloads", "margsync", "_off"),
                "margsync_SendToClinic": (D, "Downloads", "margsync", "SendToClinic"), "margsync_analysis": (D, "Downloads", "margsync", "_analysis"),
                "margsync_top": (D, "Downloads", "margsync"), "DocterzArchive": (D, "Downloads", "DocterzArchive"), "kbtools": (D, "Downloads", "_kbtools"),
                "clinic_writer": (D, "clinic_writer")}
    n_ok = n_bad = 0
    longest = 0
    per = {}
    for i in names:
        sec = i.filename.split("/", 1)[0]
        if sec not in sections or "/" not in i.filename:
            continue
        rel = i.filename.split("/", 1)[1]
        if sec == "margsync_top" and "/" in rel:
            continue
        dst = os.path.join(*sections[sec], *rel.split("/"))
        longest = max(longest, len(dst))
        try:
            crc = 0
            with open(dst, "rb") as fh:
                for b in iter(lambda: fh.read(1 << 20), b""):
                    crc = zlib.crc32(b, crc)
            good = (crc & 0xFFFFFFFF) == i.CRC and os.path.getsize(dst) == i.file_size
        except OSError:
            good = False
        n_ok += good; n_bad += (not good)
        per[sec] = per.get(sec, 0) + 1
    check("every file of the ten folders came back byte for byte (the zip's own CRC and size): %d files" % n_ok, n_bad == 0 and n_ok > 0, "%d not as the zip" % n_bad)
    say("     per folder: %s · the longest restored path %d characters" % (", ".join("%s %d" % kv for kv in sorted(per.items())), longest))
    kb_line = [l for l in t.splitlines() if "4 of 7" in l]
    check("the knowledge base was restored from the newest nightly mirror", bool(kb_line) and "RESTORED," in kb_line[0], kb_line)
    pk = [l for l in t.splitlines() if "5 of 7" in l]
    check("Python's packages: all already here (nothing to install)", bool(pk) and ("already here)" in pk[0] or "nothing to compare" in pk[0]), pk)
    tk = [l for l in t.splitlines() if "6 of 7" in l]
    check("the scheduled tasks: every one already there, none made, none failed", bool(tk) and "0 made again, 0 could not be made" in tk[0], tk)
    say("     %s" % (tk[0].strip() if tk else "(no task line)"))
    try:
        blocked = json.load(open(blocked_path, encoding="utf-8"))
    except (OSError, ValueError):
        blocked = None
    check("no command that would change this PC was even attempted (pip install, schtasks /Create)", blocked == [], blocked)
    say("     what only a person can do, as the installer ticked it:")
    for l in t.splitlines():
        if l.strip().startswith("[x]") or l.strip().startswith("[ ]"):
            say("       " + l.strip()[:110])
    att = [l.strip() for l in (t.split("LOOK AT THESE:", 1)[1].strip().splitlines() if "LOOK AT THESE:" in t else []) if l.strip()]
    real = [l for l in att if "was not in the state zip" not in l]     # an empty folder on this PC is not a restore fault
    check("the installer raised nothing under 'LOOK AT THESE' (%d note(s) of a folder not in the zip)" % (len(att) - len(real)), not real, real[:4])
    log2 = os.path.join(S, "mz", "install_log_2.txt")
    rc, _o = run([py, "-B", wrap, kit, log2, blocked_path], 900, env=env, quiet=True)
    t2 = read(log2)
    again = [l for l in t2.splitlines() if "already here, left alone" in l]
    check("second run restores nothing: every folder and the knowledge base 'already here'", rc == 0 and " RESTORED, " not in t2 and len(again) >= len(restored) + 1, t2[-300:])


def child(a):
    S = os.path.abspath(a.scratch)
    W = os.path.join(S, "w")
    say("PC KITS REHEARSAL -- %s" % VERSION)
    say("when       : %s (local clock on this PC)" % time.strftime("%Y-%m-%d %H:%M:%S"))
    import platform
    say("this PC    : %s · %s · Python %s" % (os.environ.get("COMPUTERNAME", platform.node()), platform.platform(), platform.python_version()))
    say("scratch    : %s (removed when this ends)" % S)
    if not safe_scratch(S):
        check("the scratch folder is this file's own (%s)" % SCRATCH_MARK, False, S)
        return
    if os.path.exists(S) and not wipe(S):
        check("an older scratch folder could be removed first", False, S)
        return
    os.makedirs(W)
    free = shutil.disk_usage(S).free
    if not check("at least 3 GB free where the scratch folder is (%.1f GB)" % (free / 2 ** 30), free > 3 * 2 ** 30):
        return
    say("")
    say("== THE WINDOWS TOOLS THE SETUP FILE USES")
    tar = cert = None
    if IS_WIN:
        tar = shutil.which("tar.exe"); cert = shutil.which("certutil.exe"); curl = shutil.which("curl.exe")
        check("tar.exe, curl.exe and certutil are on this Windows", bool(tar and cert and curl), (tar, curl, cert))
    else:
        say("  (not Windows: tar.exe / certutil / the kit's python.exe are not exercised; Python stands in)")
    shared = os.path.join(a.repo, "deploy_kits", "PC_KITS", "_shared")
    info = kit_info(os.path.join(a.repo, "deploy_kits", "PC_KITS", "medical"))
    a.pyzip = os.path.join(shared, info.get("python_file", "pyportable_3.11.9.zip"))
    if not check("the Python part is in the repository copy and is the one KIT_INFO names", os.path.isfile(a.pyzip) and md5(a.pyzip) == info.get("python_md5")):
        return
    py = sys.executable
    if IS_WIN:
        check("certutil's md5, read as the setup file reads it, equals the real md5", certutil_md5(a.pyzip) == md5(a.pyzip))
        ok, why = unpack(a.pyzip, W, tar)
        py = os.path.join(W, "pyportable", "python.exe")
        if not check("tar.exe unpacks the Python part and python.exe is there", ok and os.path.isfile(py), why):
            return
        rc, out = run([py, "-c", "import sys; print(sys.version.split()[0])"], 120)
        if not check("the kit's own Python starts on this Windows (3.11.9)", rc == 0 and out.strip() == "3.11.9", out[:200]):
            return
    for part in (medical, manojz):
        try:
            part(a, W, S, py, tar)
        except Exception as ex:                              # noqa: BLE001
            import traceback
            check("%s: the rehearsal itself did not break" % part.__name__, False, "%s: %s | %s" % (ex.__class__.__name__, ex, traceback.format_exc()[-400:].replace("\n", " / ")))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tools", required=True)
    ap.add_argument("--repo", default=r"D:\dr-manoj-git\drmanoj-clinic-automation")
    ap.add_argument("--scratch", default=r"D:\Downloads\_r477")
    ap.add_argument("--state", default="")
    ap.add_argument("--mirrors", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--child", action="store_true")
    a = ap.parse_args(argv)
    report = os.path.join(a.tools, REPORT)
    if a.child:
        try:
            child(a)
        except Exception as ex:                              # noqa: BLE001
            check("the rehearsal ran to its end", False, "%s: %s" % (ex.__class__.__name__, ex))
        finally:
            wipe(a.scratch)                                  # the restored copy never outlives the run, whoever ends it
        print(json.dumps({"lines": LINES, "reds": REDS, "checks": CHECKS[0]}))
        return 0
    lock = os.path.join(a.tools, LOCK)
    try:
        if os.path.exists(lock) and time.time() - os.path.getmtime(lock) > 3 * 3600:
            os.remove(lock)                                  # a lock older than three hours is a run that died
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, time.strftime("%Y-%m-%d %H:%M:%S").encode("ascii"))
        os.close(fd)
    except OSError:
        print("another rehearsal is running (%s) -- nothing done" % lock)
        return 0
    try:
        return parent(a, report)
    finally:
        try:
            os.remove(lock)
        except OSError:
            pass


def parent(a, report):
    # a scratch folder left by a run that was cut (a shutdown, a kill) is removed FIRST, on every night, report or no report
    swept = ""
    if os.path.exists(a.scratch):
        swept = "a scratch folder left by an earlier run was %s" % ("removed" if wipe(a.scratch) else "FOUND AND COULD NOT BE REMOVED: %s" % a.scratch)
        print(swept)
    if os.path.exists(report) and not a.force:
        print("the rehearsal has already run: %s" % report)
        if swept:
            try:
                with open(report, "a", encoding="utf-8", newline="\r\n" if IS_WIN else "\n") as fh:
                    fh.write("\n%s  %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), swept))
            except OSError:
                pass
        return 0
    t0 = time.time()
    out = {"lines": [], "reds": ["the rehearsal did not finish"], "checks": 0}
    note = ""
    try:
        cmd = [sys.executable, "-B", os.path.abspath(__file__), "--child", "--tools", a.tools, "--repo", a.repo, "--scratch", a.scratch]
        if a.state:
            cmd += ["--state", a.state]
        if a.mirrors:
            cmd += ["--mirrors", a.mirrors]
        p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=NOWIN)
        try:
            so, se = p.communicate(timeout=CHILD_TIMEOUT)
            try:
                out = json.loads(so.decode("utf-8", "replace").strip().splitlines()[-1])
            except Exception:                                # noqa: BLE001
                note = "the rehearsal's answer could not be read (rc %s): %s" % (p.returncode, se.decode("utf-8", "replace")[-400:])
        except subprocess.TimeoutExpired:
            note = "the rehearsal was stopped after %d minutes" % (CHILD_TIMEOUT // 60)
            if IS_WIN:                                       # the whole tree: the installer it started must not keep restoring
                run(["taskkill", "/F", "/T", "/PID", str(p.pid)], 60)
            p.kill()
            try:
                p.communicate(timeout=30)
            except Exception:                                # noqa: BLE001
                pass
    except Exception as ex:                                  # noqa: BLE001
        note = "the rehearsal could not be started: %s: %s" % (ex.__class__.__name__, ex)
    gone = wipe(a.scratch) if os.path.exists(a.scratch) else True
    lines = list(out.get("lines") or [])
    lines += ["", "== AFTER"]
    lines.append("  %s  the scratch folder is removed (%s)" % ("ok " if gone else "RED", a.scratch))
    reds = list(out.get("reds") or []) + ([] if gone else ["the scratch folder is still there: %s" % a.scratch])
    if note:
        lines.append("  RED  " + note)
        reds.append(note)
    lines += ["", "took       : %.0f s" % (time.time() - t0),
              "VERDICT    : %s  (%d checks, %d red)" % ("GREEN" if not reds else "RED", int(out.get("checks") or 0) + 1, len(reds))]
    for r in reds:
        lines.append("   red: %s" % r[:200])
    try:
        with open(report + ".part", "w", encoding="utf-8", newline="\r\n" if IS_WIN else "\n") as fh:
            fh.write("\n".join(lines) + "\n")
        os.replace(report + ".part", report)
    except OSError as ex:
        print("the report could not be written: %s" % ex)
    print("\n".join(lines[-6:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
