#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""relay_s590.py -- kit S590_WEBSITE_MAIL_RELAY (session S326, 18-Oct-2026). The two steps that touch the clinic Gmail's app
password, kept out of the shell so it is never on a command line, in the environment of another program, or on the screen.

    relay_s590.py check  <env file>                 -- sign in to smtp.gmail.com:587 with the env file's WATCHDOG_SMTP_USER /
                                                       WATCHDOG_SMTP_PASS (STARTTLS, login, quit -- nothing sent); prints
                                                       "LOGIN OK <masked user>" or "LOGIN FAILED <why>"
    relay_s590.py write  <env file> <sasl file>     -- writes "[smtp.gmail.com]:587 user:password" to <sasl file>, mode 600,
                                                       root-owned, created with a closed umask; prints "WROTE <masked user>"
    relay_s590.py to     <env file>                 -- prints the address the health mail goes to (WATCHDOG_SMTP_TO, else the
                                                       user) -- the inbox both tests are sent to

The env file is read the way clinic_health_report.py reads it (KEY=VALUE lines, quotes stripped). Nothing is printed but a masked
address. The password is a Gmail app password the box already holds and already uses for the daily health mail; this kit only
lets postfix use it too, for the website's mail. WordPress never sees it.
"""
import os, re, sys, smtplib, socket

HOST, PORT = "smtp.gmail.com", 587


def load_env(path):
    env = {}
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            if k.startswith("export "):
                k = k[7:].strip()
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
                v = v[1:-1]
            env[k] = v
    return env


def mask(a):
    return re.sub(r"^(.)[^@]*@", r"\1***@", a or "")


def creds(path):
    env = load_env(path)
    u, p = env.get("WATCHDOG_SMTP_USER", ""), env.get("WATCHDOG_SMTP_PASS", "")
    if not (u and p):
        print("NO CREDENTIALS in %s (WATCHDOG_SMTP_USER / WATCHDOG_SMTP_PASS)" % path)
        sys.exit(2)
    # A Gmail app password is 16 letters; it is often written in four groups with spaces, which Gmail ignores but postfix's map
    # cannot hold (a space ends the field). The groups are joined; any other space, tab or a colon in the user name is refused.
    squeezed = re.sub(r"\s+", "", p)
    if re.fullmatch(r"[A-Za-z]{16}", squeezed):
        p = squeezed
    if re.search(r"\s", u + p) or ":" in u:
        print("CREDENTIALS NOT USABLE IN THE MAP (a space in the password or a colon in the user name)")
        sys.exit(2)
    return env, u, p


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd, envf = sys.argv[1], sys.argv[2]
    env, u, p = creds(envf)
    if cmd == "check":
        try:
            s = smtplib.SMTP(HOST, PORT, timeout=30)
            try:
                s.ehlo(); s.starttls(); s.ehlo(); s.login(u, p)
            finally:
                try:
                    s.quit()
                except Exception:                              # noqa: BLE001
                    pass
            print("LOGIN OK %s" % mask(u))
        except (smtplib.SMTPException, socket.error, OSError) as e:
            print("LOGIN FAILED %s" % type(e).__name__)
            sys.exit(1)
    elif cmd == "write":
        dst = sys.argv[3]
        os.makedirs(os.path.dirname(dst), mode=0o700, exist_ok=True)
        old = os.umask(0o077)
        try:
            tmp = dst + ".s590tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write("[%s]:%d %s:%s\n" % (HOST, PORT, u, p))
            os.chmod(tmp, 0o600)
            os.replace(tmp, dst)
        finally:
            os.umask(old)
        print("WROTE %s" % mask(u))
    elif cmd == "to":
        print((env.get("WATCHDOG_SMTP_TO") or u).split(",")[0].strip())
    else:
        sys.exit(__doc__)
    p = ""


if __name__ == "__main__":
    main()
