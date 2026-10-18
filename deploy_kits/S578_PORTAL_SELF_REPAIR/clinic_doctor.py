#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""clinic-doctor -- kit S573_PORTAL_DOWN_FLOW (S319, 17-Oct-2026); --auto added by kit S578_PORTAL_SELF_REPAIR (S325, 18-Oct-2026).

The owner types ONE word on the server:   clinic-doctor
It checks the machine, every web service of the clinic portal and the web server (LiteSpeed) end to end,
restarts ONLY what is down or not answering (each at most once per run), checks again, and ends with one
plain verdict:  ALL GOOD  /  FIXED  /  NOT FIXED -- send a photo of this screen to Claude.

    clinic-doctor            check, repair what is down, verdict
    clinic-doctor --check    check only: restarts nothing, writes nothing but its log line and its status file
    clinic-doctor --auto     the server's own run, every 5 minutes, just before the watchman (S578, D734):
                             the same repair, but at most ONE restart per part per hour; a part someone switched
                             off on purpose (stopped and disabled) is left alone; nothing while an install runs,
                             in the first 5 minutes after boot, or while /root/deploy/_off/DOCTOR_AUTO_OFF exists;
                             the restart of the web server only when a CLINIC address fails (never for the
                             website alone); a line to the owner's phone only when it fixed something, could not
                             fix something, or things came back; its log line only when something was not right.

What it never does: delete, edit a file, touch a database, change a setting, restart anything that is answering.
The fix it applies is the one every service already documents: `systemctl restart <service>`.
Every manual run appends to /root/deploy/clinic_doctor.log (IST); every run writes /root/deploy/clinic_doctor_status.json.
Stdlib only; Python 3.6+.
"""
import fcntl
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

VERSION = "S578 2.0"
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
# S578 -- the automatic run
STATE = os.environ.get("DOCTOR_STATE", "/root/deploy/clinic_doctor_state.json")     # when each part was last restarted
STATUS = os.environ.get("DOCTOR_STATUS", "/root/deploy/clinic_doctor_status.json")  # the last run's verdict
AUTO_OFF = os.environ.get("DOCTOR_AUTO_OFF", "/root/deploy/_off/DOCTOR_AUTO_OFF")   # the switch: this file stops --auto
BUILD_LOCK = os.environ.get("DOCTOR_BUILD_LOCK", "/root/deploy/.claude_code_build.lock")  # an install is running
ALERT_ENV = os.environ.get("DOCTOR_ALERT_ENV", "/root/wa/.env")   # the watchman's phone address (never printed)
PUSH_LOG = os.environ.get("DOCTOR_PUSH_LOG")              # walk only: record the phone line instead of sending it
CAP = int(os.environ.get("DOCTOR_CAP", "3600"))           # --auto: one restart per part per this many seconds
BOOT_GRACE = 300                                          # --auto: seconds after boot when nothing is touched
GUIDE = "https://claude.ai/artifact/H5W1T3WPNm85t2peTnNnfP"

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
WEB_LABEL = "Web server (LiteSpeed)"
# Checked THROUGH the web server, the way a phone reaches them (resolved to this machine, so the internet is not in the test).
FRONT = [
    ("followup.dr-manoj.in", "/finance/healthz", "Portal address -- finance"),
    ("followup.dr-manoj.in", "/portal/login",    "Portal address -- home page"),
    ("followup.dr-manoj.in", "/register/login",  "Portal address -- staff register"),
    ("assets.dr-manoj.in",   "/",                "Scan app address"),
    ("drmanojagarwal.com",   "/",                "Your website"),
]
WEBSITE = "Your website"                           # --auto never restarts the web server for this one alone
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


def epoch():
    e = os.environ.get("DOCTOR_EPOCH")                    # walk only
    return float(e) if e else time.time()


def hhmm(ts):
    os.environ.setdefault("TZ", "Asia/Kolkata")
    try:
        time.tzset()
    except AttributeError:
        pass
    return time.strftime("%H:%M", time.localtime(ts))


def run(cmd, timeout=60):
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        return p.returncode, p.stdout.decode("utf-8", "replace").strip()
    except Exception as exc:                                  # noqa: BLE001
        return 99, str(exc)


def unit_exists(unit):
    rc, out = run([SYSTEMCTL, "show", "-p", "LoadState", "--value", unit])
    return rc == 0 and out.strip() not in ("", "not-found")


def unit_state(unit):
    rc, out = run([SYSTEMCTL, "is-active", unit])
    return out.strip()


def unit_active(unit):
    return unit_state(unit) == "active"


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


def load_json(path, default):
    try:
        with open(path) as fh:
            v = json.load(fh)
            return v if isinstance(v, dict) else default
    except (OSError, ValueError):
        return default


def save_json(path, obj):
    try:
        tmp = path + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(obj, fh, indent=1, sort_keys=True)
        os.replace(tmp, path)
    except OSError:
        pass


def uptime():
    u = os.environ.get("DOCTOR_UPTIME")                   # walk only
    if u:
        return float(u)
    try:
        with open("/proc/uptime") as fh:
            return float(fh.read().split()[0])
    except (OSError, ValueError, IndexError):
        return 10 ** 9


def alert_url():
    """The watchman's own phone address, read from its settings file. Never printed, never logged."""
    try:
        with open(ALERT_ENV) as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("WATCHDOG_NTFY_URL="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def phone(title, body, priority, anchor):
    """One line to the owner's phone. Returns True when it was accepted."""
    if PUSH_LOG:
        with open(PUSH_LOG, "a") as fh:
            fh.write(json.dumps({"title": title, "body": body, "priority": priority, "click": GUIDE + anchor}) + "\n")
        return True
    url = alert_url()
    if not url:
        log("%s | auto | phone line NOT SENT: no alert address in the watchman's settings | %s" % (now(), title))
        return False
    try:
        req = urllib.request.Request(url, data=body.encode("utf-8"), method="POST", headers={
            "Title": title.encode("ascii", "ignore").decode("ascii"), "Priority": priority,
            "Tags": "wrench" if priority != "high" else "rotating_light", "Click": GUIDE + anchor})
        urllib.request.urlopen(req, timeout=15)
        return True
    except Exception as exc:                                  # noqa: BLE001
        log("%s | auto | phone line NOT SENT (%s) | %s" % (now(), type(exc).__name__, title))
        return False


def main(argv):
    check_only = "--check" in argv
    auto = "--auto" in argv and not check_only
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0
    if auto:
        # The automatic run stays out of the way: switched off, an install running, or the machine just booted.
        if os.path.exists(AUTO_OFF):
            return 0
        if os.path.exists(BUILD_LOCK):
            try:
                if epoch() - os.path.getmtime(BUILD_LOCK) < 3600:
                    return 0
            except OSError:
                return 0
        if uptime() < BOOT_GRACE:
            return 0
    try:
        lk = open(LOCK, "w")
        fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        if auto:
            return 3                                           # the owner is running it by hand; stay quiet
        print("clinic-doctor is already running in another window. Wait one minute and run it again.")
        return 3
    lines = []

    def say(s):
        lines.append(s)
        if not auto:
            print(s)
    state = load_json(STATE, {})
    last = state.setdefault("restarted", {})
    t0 = epoch()

    def held(unit):
        """--auto only: was this part restarted (by anyone's run) within the last hour?"""
        return auto and (t0 - float(last.get(unit, 0))) < CAP

    def do_restart(unit):
        restart(unit)
        last[unit] = epoch()

    say("")
    say("clinic-doctor %s  --  %s%s" % (VERSION, now(), "  (check only: nothing will be restarted)" if check_only
                                         else ("  (automatic run)" if auto else "")))
    say("=" * 72)
    restarted, still_bad, notes, waits = [], [], [], []

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
        st = unit_state(unit)
        if auto and st in ("activating", "reloading", "deactivating"):
            say("   WAIT   %s -- starting up; looked at again in 5 minutes" % label)
            continue
        act = st == "active"
        code = probe_service(port, path) if act else None
        ok = act and (code is None or answers(code))
        why = "" if ok else ("stopped" if not act else "running but not answering")
        if ok:
            say("   OK     %s" % label)
            continue
        if auto and not act and not unit_enabled(unit):
            say("   OFF    %s -- switched off on purpose (disabled); left alone" % label)
            continue
        if check_only or disk_full:
            say("   DOWN   %s -- %s" % (label, why))
            still_bad.append(label)
            continue
        if held(unit):
            say("   DOWN   %s -- %s. Restarted at %s; tried again after an hour at most." % (label, why, hhmm(last[unit])))
            still_bad.append(label)
            waits.append(label)
            continue
        say("   DOWN   %s -- %s. Restarting it ..." % (label, why))
        do_restart(unit)
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
            elif held(unit):
                say("   DOWN   %s -- stopped. Started at %s; tried again after an hour at most." % (label, hhmm(last[unit])))
                still_bad.append(label)
                waits.append(label)
            else:
                say("   DOWN   %s -- stopped. Starting it ..." % label)
                do_restart(unit)
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
    behind_bad = bool(still_bad)                       # S578: a part behind the web server is still down
    bad = front_round() if web_ok else [l for _h, _p, l in FRONT]
    if not bad:
        say("   OK     all %d addresses answer" % len(FRONT))
    elif check_only or disk_full:
        for l in bad:
            say("   DOWN   %s" % l)
        still_bad.extend(bad)
    elif web_ok and behind_bad:
        for l in bad:
            say("   DOWN   %s" % l)
        say("   The web server is not restarted: a part behind it is still down, and that is what these addresses wait for.")
        still_bad.extend(bad)
    elif auto and web_ok and bad == [WEBSITE]:
        say("   DOWN   %s -- the clinic addresses answer, so the web server is not restarted for it" % WEBSITE)
        notes.append("your website did not answer (the clinic portal did)")
    elif held(WEB):
        for l in bad:
            say("   DOWN   %s" % l)
        say("   The web server was restarted at %s; tried again after an hour at most." % hhmm(last[WEB]))
        still_bad.extend(bad)
        waits.append(WEB_LABEL)
    else:
        for l in bad:
            say("   DOWN   %s" % l)
        say("   Restarting the web server ...")
        do_restart(WEB)
        restarted.append(WEB_LABEL)
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
    bad_names = list(dict.fromkeys(still_bad))
    if still_bad:
        verdict = "NOT FIXED"
        say("NOT FIXED.  Still not working: %s." % ", ".join(bad_names))
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
    mode = "check" if check_only else ("auto" if auto else "repair")
    line = "%s | %s | %s | restarted: %s | still bad: %s" % (now(), mode, verdict, ", ".join(restarted) or "-",
                                                             ", ".join(bad_names) or "-")
    if notes:
        line += " | note: " + "; ".join(notes)
    if not auto or verdict != "ALL GOOD" or notes:             # the automatic run logs only when something was not right
        log(line)
    save_json(STATUS, {"at": now(), "epoch": int(epoch()), "mode": mode, "verdict": verdict, "version": VERSION,
                       "restarted": restarted, "still_bad": bad_names, "waiting_for_the_hour": waits, "notes": notes})

    # 5 . the phone (automatic run only): fixed, could not fix, or back again -- never every 5 minutes
    if auto:
        told = state.get("told", {})
        if verdict == "FIXED":
            phone("Clinic server repaired itself",
                  "The server found %s not working and restarted %s by itself at %s. Everything answers now. "
                  "Nothing for you to do." % (", ".join(restarted), "it" if len(restarted) == 1 else "them", hhmm(t0)),
                  "default", "#s3")
            told = {"verdict": "FIXED", "at": t0}
        elif verdict == "NOT FIXED":
            same = told.get("verdict") == "NOT FIXED" and told.get("bad") == bad_names
            if not same or t0 - float(told.get("at", 0)) >= CAP:
                extra = (" It restarted %s, which did not help." % ", ".join(restarted)) if restarted else ""
                if waits:
                    extra += " It already restarted %s within the hour, so it waits before trying again." % ", ".join(waits)
                phone("Clinic server could NOT repair itself",
                      "Still not working: %s.%s\nNext: open Termius, type clinic-doctor, and send a photo of the "
                      "screen to Claude (guide steps 3 and 5)." % (", ".join(bad_names), extra), "high", "#s3")
                told = {"verdict": "NOT FIXED", "bad": bad_names, "at": t0}
        elif told.get("verdict") == "NOT FIXED":
            phone("Clinic server is fine again", "Every part of the portal answers again (%s). Nothing for you to do."
                  % hhmm(t0), "default", "#s3")
            told = {"verdict": "ALL GOOD", "at": t0}
        state["told"] = told
    save_json(STATE, state)
    return 0 if verdict != "NOT FIXED" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
