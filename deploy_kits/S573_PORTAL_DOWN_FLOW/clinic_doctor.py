#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""clinic-doctor -- kit S573_PORTAL_DOWN_FLOW (S319, 17-Oct-2026).

The owner types ONE word on the server:   clinic-doctor
It checks the machine, every web service of the clinic portal and the web server (LiteSpeed) end to end,
restarts ONLY what is down or not answering (each at most once per run), checks again, and ends with one
plain verdict:  ALL GOOD  /  FIXED  /  NOT FIXED -- send a photo of this screen to Claude.

    clinic-doctor            check, repair what is down, verdict
    clinic-doctor --check    check only: restarts nothing, writes nothing but its log line

What it never does: delete, edit a file, touch a database, change a setting, restart anything that is answering.
The fix it applies is the one every service already documents: `systemctl restart <service>`.
Every run appends to /root/deploy/clinic_doctor.log (IST).  Stdlib only; Python 3.6+.
"""
import fcntl
import os
import shutil
import subprocess
import sys
import time

VERSION = "S573 1.0"
SYSTEMCTL = os.environ.get("DOCTOR_SYSTEMCTL", "systemctl")
CURL = os.environ.get("DOCTOR_CURL", "curl")
LOG = os.environ.get("DOCTOR_LOG", "/root/deploy/clinic_doctor.log")
LOCK = os.environ.get("DOCTOR_LOCK", "/run/clinic-doctor.lock")
ROOTFS = os.environ.get("DOCTOR_ROOTFS", "/")
RING_ENV = os.environ.get("DOCTOR_RING_ENV", "/root/portal/ring_hook.env")
WAIT = float(os.environ.get("DOCTOR_WAIT", "4"))          # seconds between re-probes after a restart
TRIES = int(os.environ.get("DOCTOR_TRIES", "6"))          # re-probes after a restart
TIMEOUT = os.environ.get("DOCTOR_TIMEOUT", "10")          # seconds one probe may take
CLOCK = os.environ.get("DOCTOR_CLOCK")                    # walk only: a fixed clock

# (unit, what the owner calls it, local port or None, path probed on that port)
# A service answers when its port gives any HTTP reply within TIMEOUT seconds (502/503/504 count as no reply).
SERVICES = [
    ("clinic-portal",            "Clinic portal (home, tiles, call list)", 8099, "/portal/login"),
    ("clinic-finance",           "Finance app (money, health, packs)",     8106, "/finance/healthz"),
    ("assetapp",                 "Scan app and asset register",            8030, "/"),
    ("staff-register",           "Staff register and salary",              8044, "/register/login"),
    ("staff-ledger",             "Staff ledger (advances)",                8043, "/ledger"),
    ("attendance-dashboard",     "Attendance dashboard",                   8042, "/"),
    ("wa-receiver",              "WhatsApp messages coming in",            8095, "/"),
    ("wa-send-api",              "WhatsApp reply box",                     8096, "/"),
    ("call-api",                 "Click-to-call (IVR button)",             8097, "/"),
    ("call-hook",                "Call records coming in",                 8098, "/"),
    ("clinic-followup-receiver", "Follow-up list receiver",                8100, "/"),
    ("wa-approve",               "WhatsApp approvals",                     8101, "/"),
    ("ring-hook",                "Phone ring / after-call card",           "RING", "/"),
    ("attlistener",              "Biometric punches coming in",            None, None),
    ("call-pipeline",            "Call recordings worker",                 None, None),
]
WEB = "lshttpd"                                    # the web server in front of everything
# Checked THROUGH the web server, the way a phone reaches them (resolved to this machine, so the internet is not in the test).
FRONT = [
    ("followup.dr-manoj.in", "/finance/healthz", "Portal address -- finance"),
    ("followup.dr-manoj.in", "/portal/login",    "Portal address -- home page"),
    ("followup.dr-manoj.in", "/register/login",  "Portal address -- staff register"),
    ("assets.dr-manoj.in",   "/",                "Scan app address"),
    ("drmanojagarwal.com",   "/",                "Your website"),
]
ONLY_IF_STOPPED = [("mariadb", "Website database"), ("mysqld", "Website database"), ("pdns", "Domain name service")]


def now():
    if CLOCK:
        return CLOCK
    os.environ.setdefault("TZ", "Asia/Kolkata")
    try:
        time.tzset()
    except AttributeError:
        pass
    return time.strftime("%d-%b-%Y %H:%M:%S IST")


def run(cmd, timeout=60):
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        return p.returncode, p.stdout.decode("utf-8", "replace").strip()
    except Exception as exc:                                  # noqa: BLE001
        return 99, str(exc)


def unit_exists(unit):
    rc, out = run([SYSTEMCTL, "show", "-p", "LoadState", "--value", unit])
    return rc == 0 and out.strip() not in ("", "not-found")


def unit_active(unit):
    rc, out = run([SYSTEMCTL, "is-active", unit])
    return out.strip() == "active"


def unit_enabled(unit):
    rc, out = run([SYSTEMCTL, "is-enabled", unit])
    return out.strip() in ("enabled", "static", "alias", "indirect")


def ring_port():
    try:
        with open(RING_ENV) as fh:
            for line in fh:
                k, _, v = line.strip().partition("=")
                if k.strip() == "RING_HOOK_PORT" and v.strip().strip('"').isdigit():
                    return int(v.strip().strip('"'))
    except OSError:
        pass
    return None


def http_code(url, resolve=None):
    cmd = [CURL, "-s", "-k", "-o", "/dev/null", "-m", TIMEOUT, "-w", "%{http_code}"]
    if resolve:
        cmd += ["--resolve", resolve]
    rc, out = run(cmd + [url], timeout=int(TIMEOUT) + 5)
    code = out.strip()[-3:] if out else "000"
    return code if code.isdigit() else "000"


def answers(code):
    """Any reply counts as alive -- an error page is the app speaking. Only no reply (000) or a gateway error
    from in front of the app (502, 503, 504) means not answering."""
    return code != "000" and code not in ("502", "503", "504")


def probe_service(port, path):
    if port is None:
        return None
    return http_code("http://127.0.0.1:%d%s" % (port, path))


def probe_front(host, path):
    return http_code("https://%s%s" % (host, path), resolve="%s:443:127.0.0.1" % host)


def restart(unit):
    rc, out = run([SYSTEMCTL, "restart", unit], timeout=120)
    return rc == 0


def log(line):
    try:
        with open(LOG, "a") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


def main(argv):
    check_only = "--check" in argv
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0
    try:
        lk = open(LOCK, "w")
        fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("clinic-doctor is already running in another window. Wait one minute and run it again.")
        return 3
    say = print
    say("")
    say("clinic-doctor %s  --  %s%s" % (VERSION, now(), "  (check only: nothing will be restarted)" if check_only else ""))
    say("=" * 72)
    restarted, still_bad, notes = [], [], []

    # 1 . the machine
    try:
        du = shutil.disk_usage(ROOTFS)
        used = 100.0 * du.used / du.total
    except OSError:
        used = -1
    if os.environ.get("DOCTOR_DISK_USED"):                    # walk only
        used = float(os.environ["DOCTOR_DISK_USED"])
    mem = None
    try:
        with open(os.environ.get("DOCTOR_MEMINFO", "/proc/meminfo")) as fh:
            for line in fh:
                if line.startswith("MemAvailable:"):
                    mem = int(line.split()[1]) // 1024
    except OSError:
        pass
    say("1. The machine")
    say("   disk used %s   memory free %s" % ("%d%%" % used if used >= 0 else "?", "%d MB" % mem if mem is not None else "?"))
    disk_full = used >= 95
    if disk_full:
        say("   !! The disk is full. A full disk stops everything, and freeing it needs a careful hand.")
        still_bad.append("disk full")
    if mem is not None and mem < 200:
        notes.append("memory was very low (%d MB free)" % mem)

    # 2 . each service: running, and answering
    say("")
    say("2. The portal's services")
    rp = ring_port()
    for unit, label, port, path in SERVICES:
        if port == "RING":
            port = rp
        if not unit_exists(unit):
            continue
        act = unit_active(unit)
        code = probe_service(port, path) if act else None
        ok = act and (code is None or answers(code))
        why = "" if ok else ("stopped" if not act else "running but not answering")
        if ok:
            say("   OK     %s" % label)
            continue
        if check_only or disk_full:
            say("   DOWN   %s -- %s" % (label, why))
            still_bad.append(label)
            continue
        say("   DOWN   %s -- %s. Restarting it ..." % (label, why))
        restart(unit)
        restarted.append(label)
        good = False
        for _ in range(TRIES):
            time.sleep(WAIT)
            if unit_active(unit):
                c2 = probe_service(port, path)
                if c2 is None or answers(c2):
                    good = True
                    break
        say("          %s" % ("back and answering" if good else "STILL NOT ANSWERING"))
        if not good:
            still_bad.append(label)

    # 3 . the web server, end to end
    say("")
    say("3. The web server (how your phone reaches the portal)")
    for unit, label in ONLY_IF_STOPPED:
        if unit_exists(unit) and unit_enabled(unit) and not unit_active(unit):
            if check_only or disk_full:
                say("   DOWN   %s -- stopped" % label)
                still_bad.append(label)
            else:
                say("   DOWN   %s -- stopped. Starting it ..." % label)
                restart(unit)
                restarted.append(label)
                time.sleep(WAIT)
                if not unit_active(unit):
                    still_bad.append(label)

    def front_round():
        bad = []
        for host, path, label in FRONT:
            c = probe_front(host, path)
            if not answers(c):
                bad.append(label)
        return bad

    web_ok = unit_active(WEB)
    bad = front_round() if web_ok else [l for _h, _p, l in FRONT]
    if not bad:
        say("   OK     all %d addresses answer" % len(FRONT))
    elif check_only or disk_full:
        for l in bad:
            say("   DOWN   %s" % l)
        still_bad.extend(bad)
    else:
        for l in bad:
            say("   DOWN   %s" % l)
        say("   Restarting the web server ...")
        restart(WEB)
        restarted.append("Web server (LiteSpeed)")
        bad2 = bad
        for _ in range(TRIES):
            time.sleep(WAIT)
            bad2 = front_round()
            if not bad2:
                break
        if bad2:
            for l in bad2:
                say("          STILL NOT ANSWERING: %s" % l)
            still_bad.extend(bad2)
        else:
            say("          all %d addresses answer now" % len(FRONT))

    # 4 . the verdict
    say("")
    say("=" * 72)
    if still_bad:
        verdict = "NOT FIXED"
        say("NOT FIXED.  Still not working: %s." % ", ".join(dict.fromkeys(still_bad)))
        if restarted:
            say("            (restarted: %s)" % ", ".join(restarted))
        say("            Send a photo of this screen to Claude.")
    elif restarted:
        verdict = "FIXED"
        say("FIXED.  Restarted: %s.  Everything answers now." % ", ".join(restarted))
        say("        Open the portal on your phone to confirm.")
    else:
        verdict = "ALL GOOD"
        say("ALL GOOD.  Every part of the portal answers on this server.")
        say("           If your phone still cannot open the portal, the problem is outside this server:")
        say("           follow step 4 of the guide (restart from the Hostinger panel).")
    if notes:
        say("Note: " + "; ".join(notes) + ".")
    say("=" * 72)
    log("%s | %s | %s | restarted: %s | still bad: %s" % (now(), "check" if check_only else "repair", verdict,
                                                         ", ".join(restarted) or "-", ", ".join(dict.fromkeys(still_bad)) or "-"))
    return 0 if verdict != "NOT FIXED" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
