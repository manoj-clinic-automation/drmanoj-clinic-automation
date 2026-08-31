#!/usr/bin/env python3
"""
setup_salt.py  --  create the patient fingerprint salt, once, without ever
showing it.

WHAT THIS IS FOR
  Patient mobiles never travel to the VPS as numbers; they travel as a salted
  one-way fingerprint. Both machines must use the SAME salt or nothing matches.
  A ten-digit number has only ten billion possibilities, so an UNSALTED hash is
  reversible by brute force in seconds -- the salt is what makes the fingerprint
  safe, and it is therefore a secret.

WHAT IT DOES
  1. Creates the salt ONCE and writes it to  patient_fp.env  beside this script.
  2. NEVER regenerates an existing salt. Changing it would orphan every
     fingerprint already on the VPS, so an existing file is left untouched and
     the script says so.
  3. Puts the single line to run on the VPS onto the WINDOWS CLIPBOARD, so it
     goes straight into Termius with Ctrl+V. It is never printed to the screen,
     never written to a log, and never passes through a chat.
  4. Refuses to run if the folder looks wrong, rather than scattering a secret.

The salt is not shown at any point. If you ever need it again, this file is the
only copy -- back it up with your other credentials.
"""
import os
import secrets
import subprocess
import sys

KEY = "PATIENT_FP_SALT"
HERE = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(HERE, "patient_fp.env")
VPS_ENV = "/root/finance/patient_fp.env"


def existing():
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith(KEY + "="):
                    return line.strip().split("=", 1)[1].strip()
    except OSError:
        pass
    return ""


def to_clipboard(text):
    """Windows clip.exe. Returns True if the line is on the clipboard."""
    try:
        p = subprocess.Popen("clip", stdin=subprocess.PIPE, shell=True)
        p.communicate(text.encode("utf-16-le"))
        return p.returncode == 0
    except OSError:
        return False


def inside_a_git_repo(start):
    """Walk up looking for .git. A secret must never be created inside a
    repository -- even a gitignored one, because the publish gate refuses to
    ship while an ignored file sits under deploy_kits, and it is right to:
    it cannot tell a deliberate secret from a file that was dropped by mistake.
    S211: this script was first run from the kit folder and did exactly that,
    stopping a publish. The gate caught it. This stops it happening again."""
    d = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(d, ".git")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return ""
        d = parent


def main():
    repo = inside_a_git_repo(HERE)
    if repo:
        print("=" * 66)
        print(" REFUSING - this folder is inside a git repository:")
        print("   %s" % repo)
        print("=" * 66)
        print("\nA salt must never be created inside a repository. Copy this")
        print("script and SETUP_SALT.bat into the follow-up tracker folder --")
        print("the one holding push_to_vps.py -- and run it there instead.")
        print("\nNothing was created. No secret was written.")
        return 1
    print("=" * 66)
    print(" PATIENT FINGERPRINT SALT  --  one-time setup")
    print("=" * 66)

    salt = existing()
    if salt:
        print("\nA salt already exists in this folder. It has NOT been changed.")
        print("Changing it would break every fingerprint already on the VPS.")
    else:
        salt = secrets.token_hex(32)
        try:
            with open(ENV_FILE, "w", encoding="utf-8", newline="") as f:
                f.write("%s=%s\n" % (KEY, salt))
            if os.name == "nt":
                subprocess.call('attrib +h "%s"' % ENV_FILE, shell=True)
        except OSError as ex:
            print("\n!! could not write %s\n   %s" % (ENV_FILE, ex))
            return 1
        print("\nA new salt was created and saved to:")
        print("   %s" % ENV_FILE)
        print("   (it is not shown here, and never will be)")

    line = ("mkdir -p /root/finance && umask 077 && printf '%s=%s\\n' > %s && "
            "chmod 600 %s && echo SALT_INSTALLED" % (KEY, salt, VPS_ENV, VPS_ENV))

    if to_clipboard(line):
        print("\nThe VPS line is now ON YOUR CLIPBOARD.")
        print("   Open Termius and press Ctrl+V, then Enter.")
        print("   You should see:  SALT_INSTALLED")
        print("\n   It is not printed here on purpose -- paste it, do not read it.")
    else:
        out = os.path.join(HERE, "VPS_SALT_LINE.txt")
        with open(out, "w", encoding="utf-8", newline="") as f:
            f.write(line + "\n")
        print("\nThe clipboard was not available, so the line was written to:")
        print("   %s" % out)
        print("   Open it, copy the single line into Termius, then DELETE the file.")

    print("\nAfter that, both machines fingerprint identically and nothing else")
    print("needs doing. This script can be run again safely -- it will never")
    print("replace a salt that already exists.")
    print("=" * 66)
    return 0


if __name__ == "__main__":
    sys.exit(main())
