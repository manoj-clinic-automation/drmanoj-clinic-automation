#!/usr/bin/env python3
"""
ring_setup.py -- kit S366_RING_POPUP. Writes, ONCE, the two 0600 config files the ring pop-up needs beside the
portal, and never overwrites a value that already exists:
  /root/portal/ring_hook.env      RING_HOOK_SECRET · RING_INTERNAL_KEY · RING_HOOK_PORT · VAPID_PUBLIC · VAPID_SUBJECT · VAPID_PRIVATE_PEM_FILE
  /root/portal/vapid_private.pem  the Web Push signing key (py_vapid)
Prints only which keys exist. `--webhook-url` prints the one line the owner pastes into the MyOperator panel
(it carries RING_HOOK_SECRET -- his terminal, his panel; the same pattern as the wa-webhook, S?).
"""
import base64
import os
import secrets
import sys

PD = os.environ.get("RING_PORTAL_DIR", "/root/portal")
ENV = os.path.join(PD, "ring_hook.env")
PEM = os.path.join(PD, "vapid_private.pem")
PORT = os.environ.get("RING_HOOK_PORT", "8110")
SUBJECT = os.environ.get("VAPID_SUBJECT", "mailto:drmka.ortho@gmail.com")
PUBLIC_URL = "https://followup.dr-manoj.in/ring-hook"


def read_env():
    out = {}
    try:
        for line in open(ENV, "r", encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip()
    except OSError:
        pass
    return out


def write_env(d):
    tmp = ENV + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write("# ring_hook.env -- S366_RING_POPUP. 0600. Read by ring-hook.service and by the portal. Never in the repo.\n")
        for k in ("RING_HOOK_SECRET", "RING_INTERNAL_KEY", "RING_HOOK_PORT", "VAPID_PUBLIC", "VAPID_SUBJECT", "VAPID_PRIVATE_PEM_FILE"):
            fh.write("%s=%s\n" % (k, d.get(k, "")))
    os.chmod(tmp, 0o600)
    os.replace(tmp, ENV)


def main(argv):
    d = read_env()
    if "--webhook-url" in argv:
        if not d.get("RING_HOOK_SECRET"):
            print("!! no RING_HOOK_SECRET yet -- run without arguments first"); return 1
        print(PUBLIC_URL + "?key=" + d["RING_HOOK_SECRET"]); return 0
    made = []
    if not d.get("RING_HOOK_SECRET"):
        d["RING_HOOK_SECRET"] = secrets.token_urlsafe(24); made.append("RING_HOOK_SECRET")
    if not d.get("RING_INTERNAL_KEY"):
        d["RING_INTERNAL_KEY"] = secrets.token_urlsafe(24); made.append("RING_INTERNAL_KEY")
    if not d.get("RING_HOOK_PORT"):
        d["RING_HOOK_PORT"] = PORT; made.append("RING_HOOK_PORT")
    if not d.get("VAPID_SUBJECT"):
        d["VAPID_SUBJECT"] = SUBJECT; made.append("VAPID_SUBJECT")
    d["VAPID_PRIVATE_PEM_FILE"] = d.get("VAPID_PRIVATE_PEM_FILE") or PEM
    if not (os.path.exists(d["VAPID_PRIVATE_PEM_FILE"]) and d.get("VAPID_PUBLIC")):
        from py_vapid import Vapid
        from cryptography.hazmat.primitives import serialization
        v = Vapid()
        if os.path.exists(d["VAPID_PRIVATE_PEM_FILE"]):
            v = Vapid.from_file(d["VAPID_PRIVATE_PEM_FILE"])
        else:
            v.generate_keys()
            with open(d["VAPID_PRIVATE_PEM_FILE"], "wb") as fh:
                fh.write(v.private_pem())
            os.chmod(d["VAPID_PRIVATE_PEM_FILE"], 0o600)
            made.append("vapid_private.pem")
        pub = v.public_key.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        d["VAPID_PUBLIC"] = base64.urlsafe_b64encode(pub).rstrip(b"=").decode("ascii"); made.append("VAPID_PUBLIC")
    write_env(d)
    print("ring_hook.env: %s · port %s · %s" % (("created " + ", ".join(made)) if made else "already complete, nothing changed",
                                               d["RING_HOOK_PORT"], "VAPID key present"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
