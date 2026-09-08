#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
split_ntfy.py  --  S231 : separate the OWNER'S system alerts from the CLINIC'S
message alerts, which have shared one topic all along.

WHY
---
One topic carried everything: "New WhatsApp" for the staff, and the watchman,
health report and freshness shout for the owner. Four devices subscribe to it --
the owner's phone, his PC, the assistant PC, the reception PC and the
assistant's personal phone. So the staff have been receiving the owner's system
alerts, and -- the reason this matters now -- once the WhatsApp push carries the
FULL patient message, that message would appear on every one of those devices.

Splitting first makes that change safe, and costs the staff nothing: they keep
the topic they are already on.

  NTFY_TOPIC          (messages)  -- unchanged. Staff + owner. notifier_wa.py.
  WATCHDOG_NTFY_URL   (system)    -- REPOINTED to a new topic. Owner only.
                                     clinic_watchdog.py, clinic_health_report.py
  freshness.conf NTFY_URL         -- follows the system topic.

NO CODE CHANGES. NO SERVICE RESTARTS. The notifier is not touched at all, so
the message path cannot break.

RUN (VPS, root):
    /root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S231_NTFY_SPLIT/split_ntfy.py --check
    /root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S231_NTFY_SPLIT/split_ntfy.py --install
"""

import os
import re
import sys
import shutil
import secrets
import datetime
import urllib.request

ENV_PATH   = "/root/wa/.env"
FRESH_CONF = "/root/finance/freshness.conf"
STAMP      = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP     = "/root/_backup_S231_split_%s" % STAMP
ALPHABET   = "abcdefghjkmnpqrstuvwxyz23456789"
URL_RE     = re.compile(r'^https://ntfy\.sh/([A-Za-z0-9_\-]+)$')


def say(m=""):
    print(m, flush=True)


def mask(t):
    return t[:2] + "*" * (len(t) - 4) + t[-2:] if len(t) > 5 else "*" * len(t)


def read_env():
    out = {}
    for line in open(ENV_PATH, "r", errors="ignore"):
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def set_env(pairs):
    lines = open(ENV_PATH, "r", errors="ignore").read().splitlines()
    seen, out = set(), []
    for line in lines:
        k = line.split("=", 1)[0].strip() if "=" in line else None
        if k in pairs:
            out.append("%s=%s" % (k, pairs[k]))
            seen.add(k)
        else:
            out.append(line)
    for k, v in pairs.items():
        if k not in seen:
            out.append("%s=%s" % (k, v))
    open(ENV_PATH, "w").write("\n".join(out).rstrip("\n") + "\n")
    os.chmod(ENV_PATH, 0o600)


def push(url, title, body):
    req = urllib.request.Request(url, data=body.encode("utf-8"),
                                 headers={"Title": title, "Priority": "default"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status


def main():
    mode = "--check"
    for a in sys.argv[1:]:
        if a in ("--check", "--install"):
            mode = a

    say("=" * 72)
    say("S231 ntfy split  --  mode %s  --  %s" % (mode, STAMP))
    say("=" * 72)

    say("\n[1] what the box has today")
    if not os.path.exists(ENV_PATH):
        say("    REFUSING -- %s missing" % ENV_PATH)
        return 2
    env = read_env()
    msg_topic = env.get("NTFY_TOPIC", "")
    sys_url   = env.get("WATCHDOG_NTFY_URL", "")
    m = URL_RE.match(sys_url)
    if not msg_topic or not m:
        say("    REFUSING -- run the rotation and the finisher first.")
        return 2
    sys_topic = m.group(1)
    say("    messages (NTFY_TOPIC)        %s" % mask(msg_topic))
    say("    system   (WATCHDOG_NTFY_URL) %s" % mask(sys_topic))
    if msg_topic != sys_topic:
        say("    already split -- nothing to do")
        return 0
    say("    SAME TOPIC -- staff are receiving the owner's system alerts")

    say("\n[2] freshness conf")
    if not os.path.exists(FRESH_CONF):
        say("    REFUSING -- %s missing" % FRESH_CONF)
        return 2
    fresh = open(FRESH_CONF, "r", errors="ignore").read()
    if msg_topic not in fresh:
        say("    NOTE: it does not name the shared topic; it will be left alone")
    else:
        say("    names the shared topic; it will follow the system topic")

    if mode == "--check":
        say("\n[3] --check only. NOTHING WAS CHANGED.")
        return 0

    say("\n[3] backing up")
    os.makedirs(BACKUP, exist_ok=True)
    shutil.copy2(ENV_PATH, os.path.join(BACKUP, "env.bak"))
    shutil.copy2(FRESH_CONF, os.path.join(BACKUP, "freshness.conf.bak"))
    say("    %s" % BACKUP)

    new_sys = "".join(secrets.choice(ALPHABET) for _ in range(16))
    new_url = "https://ntfy.sh/" + new_sys

    say("\n[4] repointing the SYSTEM alerts only")
    set_env({"WATCHDOG_NTFY_URL": new_url})
    if read_env().get("WATCHDOG_NTFY_URL") != new_url:
        say("    REFUSING -- .env did not read back. Restore:")
        say("      \\cp %s/env.bak %s" % (BACKUP, ENV_PATH))
        return 2
    say("    WATCHDOG_NTFY_URL moved")

    back = read_env()
    if back.get("NTFY_TOPIC") != msg_topic:
        say("    REFUSING -- the MESSAGES topic changed. That must never happen.")
        say("      \\cp %s/env.bak %s" % (BACKUP, ENV_PATH))
        return 2
    say("    NTFY_TOPIC untouched -- staff keep the topic they are already on")

    if msg_topic in fresh:
        new_fresh = fresh.replace(msg_topic, new_sys)
        open(FRESH_CONF, "w").write(new_fresh)
        if msg_topic in open(FRESH_CONF, "r", errors="ignore").read():
            say("    REFUSING -- freshness.conf still names the old topic")
            return 2
        say("    freshness.conf moved to the system topic")

    say("\n[5] proving both topics still carry")
    ok = True
    try:
        say("    system   test push HTTP %s"
            % push(new_url, "Clinic system alerts",
                   "S231: watchman, health and freshness now come here. "
                   "This topic is yours alone."))
    except Exception as e:
        ok = False
        say("    system   test push FAILED: %s" % e)
    try:
        say("    messages test push HTTP %s"
            % push("https://ntfy.sh/" + msg_topic, "Clinic messages",
                   "S231: WhatsApp alerts continue to come here. Nothing to do."))
    except Exception as e:
        ok = False
        say("    messages test push FAILED: %s" % e)

    say("\n" + "=" * 72)
    say("DONE.")
    say("=" * 72)
    say("  STAFF DEVICES: no change. They stay on the messages topic.")
    say("")
    say("  YOUR PHONE ONLY -- add this second subscription, read it in fours:")
    say("")
    say("        %s   %s   %s   %s"
        % (new_sys[0:4], new_sys[4:8], new_sys[8:12], new_sys[12:16]))
    say("")
    say("  as one word:  %s" % new_sys)
    say("=" * 72)
    if not ok:
        say("NOTE: a push failed. Config is in place; retry before relying on it.")
    say("Undo:")
    say("  \\cp %s/env.bak %s" % (BACKUP, ENV_PATH))
    say("  \\cp %s/freshness.conf.bak %s" % (BACKUP, FRESH_CONF))
    return 0


if __name__ == "__main__":
    sys.exit(main())
