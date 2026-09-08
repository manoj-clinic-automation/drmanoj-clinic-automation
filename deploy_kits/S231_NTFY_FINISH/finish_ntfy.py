#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
finish_ntfy.py  --  S231 / F-358 part 2 : the topic lives in ONE file, and the
notifier unit stops carrying one at all.

WHY
---
After the rotation the live unit /etc/systemd/system/wa-notifier.service still
holds the topic inline as Environment=NTFY_TOPIC=...  That is the LAST copy
outside /root/wa/.env, and it is the copy the repository also has.  While it
exists, a deploy of the repo's version of that unit would silently point the
notifier at the dead topic -- WhatsApp alerts would stop, with no error and no
sign, which is this project's oldest failure shape.

So: put NTFY_TOPIC in /root/wa/.env beside the URL the rotation already wrote,
point the unit at that file, and prove the RUNNING PROCESS actually has it.

The proof is the point.  "systemctl is-active" only says the process started.
This reads /proc/<pid>/environ and checks the variable is really there, because
a unit that starts fine with no topic is exactly the silent failure we are
trying to make impossible.

RUN (VPS, root):
    /root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S231_NTFY_FINISH/finish_ntfy.py --check
    /root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S231_NTFY_FINISH/finish_ntfy.py --install
"""

import os
import re
import sys
import time
import shutil
import datetime
import subprocess

ENV_PATH  = "/root/wa/.env"
UNIT      = "/etc/systemd/system/wa-notifier.service"
SERVICE   = "wa-notifier.service"
STAMP     = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP    = "/root/_backup_S231_finish_%s" % STAMP

KEY_RE  = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*=')
URL_RE  = re.compile(r'^https://ntfy\.sh/([A-Za-z0-9_\-]+)$')


def say(m=""):
    print(m, flush=True)


def mask(t):
    return t[:2] + "*" * (len(t) - 4) + t[-2:] if len(t) > 5 else "*" * len(t)


def read_env():
    out = {}
    if not os.path.exists(ENV_PATH):
        return out
    for line in open(ENV_PATH, "r", errors="ignore"):
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def env_file_is_systemd_safe():
    """systemd refuses a malformed EnvironmentFile and the unit then starts with
    NOTHING from it. Check before we depend on it."""
    bad = []
    for n, line in enumerate(open(ENV_PATH, "r", errors="ignore"), 1):
        s = line.rstrip("\n")
        if not s.strip() or s.lstrip().startswith("#"):
            continue
        if s.lstrip().startswith("export "):
            bad.append((n, "starts with 'export ' -- systemd does not accept it"))
            continue
        if not KEY_RE.match(s.lstrip()):
            bad.append((n, "not a bare KEY=VALUE line"))
            continue
        key = s.lstrip().split("=", 1)[0]
        if s.lstrip()[len(key):len(key) + 2] == " =" or " = " in s.split("=", 1)[0] + "=":
            bad.append((n, "spaces around '='"))
    return bad


def proc_env_has(service, key):
    """Read the RUNNING process's environment. The only honest proof."""
    r = subprocess.run(["systemctl", "show", service, "-p", "MainPID", "--value"],
                       capture_output=True, text=True, timeout=30)
    pid = r.stdout.strip()
    if not pid or pid == "0":
        return None, "no MainPID"
    path = "/proc/%s/environ" % pid
    try:
        raw = open(path, "rb").read().decode("utf-8", "ignore")
    except Exception as e:
        return None, "cannot read %s: %s" % (path, e)
    for item in raw.split("\0"):
        if item.startswith(key + "="):
            return item.split("=", 1)[1], "pid %s" % pid
    return None, "pid %s has no %s" % (pid, key)


def main():
    mode = "--check"
    for a in sys.argv[1:]:
        if a in ("--check", "--install"):
            mode = a

    say("=" * 72)
    say("S231 ntfy finish  --  mode %s  --  %s" % (mode, STAMP))
    say("=" * 72)

    say("\n[1] the topic, from the file the rotation wrote")
    env = read_env()
    url = env.get("WATCHDOG_NTFY_URL", "")
    m = URL_RE.match(url)
    if not m:
        say("    REFUSING -- WATCHDOG_NTFY_URL missing or not a plain ntfy.sh URL.")
        say("    Run the rotation first.")
        return 2
    topic = m.group(1)
    say("    found (%s), %d chars" % (mask(topic), len(topic)))
    if env.get("NTFY_TOPIC") == topic:
        say("    NTFY_TOPIC already present and matching")
    else:
        say("    NTFY_TOPIC absent or different -- will be set")

    say("\n[2] is %s safe to hand systemd as an EnvironmentFile?" % ENV_PATH)
    bad = env_file_is_systemd_safe()
    if bad:
        say("    REFUSING -- %d unusable line(s):" % len(bad))
        for n, why in bad:
            say("      line %d: %s" % (n, why))
        say("    Nothing changed. A malformed file would start the unit with")
        say("    NO variables at all, which is the silent failure we are avoiding.")
        return 2
    say("    yes -- every line is a bare KEY=VALUE")

    say("\n[3] the unit today")
    if not os.path.exists(UNIT):
        say("    REFUSING -- %s not found" % UNIT)
        return 2
    unit_txt = open(UNIT, "r", errors="ignore").read()
    inline = [l.strip() for l in unit_txt.splitlines()
              if l.strip().startswith("Environment=NTFY_")]
    has_envfile = ("EnvironmentFile=" + ENV_PATH) in unit_txt
    for l in inline:
        say("    inline: %s" % re.sub(r'=([A-Za-z0-9_\-]{6,})$',
                                      lambda mm: "=" + mask(mm.group(1)), l))
    say("    EnvironmentFile already present: %s" % has_envfile)
    if not inline and has_envfile:
        say("    nothing to do -- the unit is already clean")
        return 0

    if mode == "--check":
        say("\n[4] --check only. NOTHING WAS CHANGED.")
        return 0

    say("\n[4] backing up")
    os.makedirs(BACKUP, exist_ok=True)
    shutil.copy2(ENV_PATH, os.path.join(BACKUP, "env.bak"))
    shutil.copy2(UNIT, os.path.join(BACKUP, "wa-notifier.service.bak"))
    say("    %s" % BACKUP)

    say("\n[5] writing NTFY_TOPIC into %s  (config BEFORE the unit changes)" % ENV_PATH)
    lines = open(ENV_PATH, "r", errors="ignore").read().splitlines()
    want = {"NTFY_TOPIC": topic, "NTFY_SERVER": "https://ntfy.sh"}
    seen = set()
    out = []
    for line in lines:
        k = line.split("=", 1)[0].strip() if "=" in line else None
        if k in want:
            out.append("%s=%s" % (k, want[k]))
            seen.add(k)
        else:
            out.append(line)
    for k, v in want.items():
        if k not in seen:
            out.append("%s=%s" % (k, v))
    open(ENV_PATH, "w").write("\n".join(out).rstrip("\n") + "\n")
    os.chmod(ENV_PATH, 0o600)
    if read_env().get("NTFY_TOPIC") != topic:
        say("    REFUSING -- did not read back. Restore:")
        say("      \\cp %s/env.bak %s" % (BACKUP, ENV_PATH))
        return 2
    say("    written and read back (mode 600)")

    say("\n[6] rewriting the unit -- no topic in it at all")
    new_lines, inserted = [], False
    for line in unit_txt.splitlines():
        s = line.strip()
        if s.startswith("Environment=NTFY_"):
            if not inserted:
                new_lines.append("# S231/F-358: the topic is a SECRET and lives only in %s."
                                 % ENV_PATH)
                new_lines.append("# Never put it back in this file -- this file is public.")
                new_lines.append("EnvironmentFile=" + ENV_PATH)
                inserted = True
            continue
        new_lines.append(line)
    if not inserted and not has_envfile:
        say("    REFUSING -- could not find where to put EnvironmentFile")
        return 2
    new_unit = "\n".join(new_lines).rstrip("\n") + "\n"
    if re.search(r'Environment=NTFY_', new_unit):
        say("    REFUSING -- an inline topic survived")
        return 2
    open(UNIT, "w").write(new_unit)
    say("    unit rewritten; no Environment=NTFY_ line remains")

    say("\n[7] reload, restart, and PROVE the running process has the topic")
    def restore(why):
        say("    REFUSING -- %s" % why)
        say("    rolling back automatically...")
        shutil.copy2(os.path.join(BACKUP, "wa-notifier.service.bak"), UNIT)
        subprocess.run(["systemctl", "daemon-reload"], capture_output=True, timeout=60)
        subprocess.run(["systemctl", "restart", SERVICE], capture_output=True, timeout=90)
        r = subprocess.run(["systemctl", "is-active", SERVICE],
                           capture_output=True, text=True, timeout=30)
        say("    rolled back; %s is now %s" % (SERVICE, r.stdout.strip()))
        say("    (.env keeps NTFY_TOPIC -- harmless, and correct for next time)")

    subprocess.run(["systemctl", "daemon-reload"], capture_output=True, timeout=60)
    subprocess.run(["systemctl", "restart", SERVICE], capture_output=True, timeout=90)
    time.sleep(3)
    r = subprocess.run(["systemctl", "is-active", SERVICE],
                       capture_output=True, text=True, timeout=30)
    state = r.stdout.strip()
    say("    is-active: %s" % state)
    if state != "active":
        restore("%s did not come back active" % SERVICE)
        return 2

    got, where = proc_env_has(SERVICE, "NTFY_TOPIC")
    if got is None:
        restore("the running process has no NTFY_TOPIC (%s)" % where)
        return 2
    if got != topic:
        restore("the running process has a DIFFERENT topic (%s)" % where)
        return 2
    say("    running process carries NTFY_TOPIC (%s), %s" % (mask(got), where))

    say("\n" + "=" * 72)
    say("DONE. The topic now exists in exactly one file on this box:")
    say("  %s   (mode 600, not in any repository)" % ENV_PATH)
    say("The notifier unit is safe to publish -- it names no topic.")
    say("=" * 72)
    say("Undo:")
    say("  \\cp %s/wa-notifier.service.bak %s" % (BACKUP, UNIT))
    say("  \\cp %s/env.bak %s" % (BACKUP, ENV_PATH))
    say("  systemctl daemon-reload && systemctl restart %s" % SERVICE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
