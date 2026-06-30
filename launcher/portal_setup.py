#!/usr/bin/env python3
"""
portal_setup.py  —  one-time PIN + secrets setup for the Clinic Launcher Portal
===============================================================================
Dr. Manoj Agarwal Clinic, Bareilly.

Creates /root/portal/portal_config.py with:
    PORTAL_PIN_HASH    = salted SHA-256 of your PIN  (the PIN itself is NEVER stored)
    PORTAL_PIN_SALT    = a random per-install salt
    PORTAL_TOKEN_SEED  = the device-trust server secret
    PORTAL_COOKIE_NAME = "clinic_portal_device"

This MATCHES portal.py exactly:  PORTAL_PIN_HASH = sha256(PORTAL_PIN_SALT + pin)
so the PIN you set here will log you in there. Nothing else.

Only the Python standard library is used, so either of these works:
    /root/wa/venv/bin/python3 /root/portal/portal_setup.py
    python3 /root/portal/portal_setup.py

After it finishes, restart the service:
    systemctl restart clinic-portal
"""

import os
import stat
import getpass
import hashlib
import secrets

CONFIG_DIR  = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(CONFIG_DIR, "portal_config.py")


def make_hash(salt: str, pin: str) -> str:
    """Identical to portal.py's _hash_pin: sha256(salt + pin)."""
    return hashlib.sha256((salt + pin).encode("utf-8")).hexdigest()


def main():
    print("=" * 60)
    print(" Clinic Portal  -  one-time PIN setup")
    print("=" * 60)
    print(" Config file: " + CONFIG_PATH)
    print()

    if os.path.exists(CONFIG_PATH):
        print("A portal_config.py already exists here.")
        ans = input('Overwrite it and set a NEW PIN? (type "yes" to confirm): ').strip().lower()
        if ans != "yes":
            print("Cancelled. Nothing was changed.")
            return
        print()

    # --- choose PIN (hidden, typed twice) -----------------------------------
    while True:
        pin1 = getpass.getpass("Choose a PIN (digits only, 4 to 8): ").strip()
        if not pin1.isdigit() or not (4 <= len(pin1) <= 8):
            print("  -> PIN must be 4 to 8 digits. Try again.\n")
            continue
        if len(pin1) < 6:
            print("  (note: 6 digits is safer than 4 — continuing anyway)")
        pin2 = getpass.getpass("Re-enter the same PIN to confirm: ").strip()
        if pin1 != pin2:
            print("  -> The two entries did not match. Try again.\n")
            continue
        break

    # --- generate secrets ----------------------------------------------------
    salt       = secrets.token_hex(16)        # random per-install salt
    pin_hash   = make_hash(salt, pin1)
    token_seed = secrets.token_urlsafe(32)    # rotating this = "forget all devices"

    body = (
        '# portal_config.py  -  SECRET. Created by portal_setup.py.\n'
        '# NEVER commit this file to git. NEVER share these values.\n'
        '# To change the PIN later: re-run  portal_setup.py  then  systemctl restart clinic-portal\n'
        '# "Forget all devices" in the portal rotates PORTAL_TOKEN_SEED automatically.\n'
        '\n'
        'PORTAL_PIN_HASH    = "%s"\n'
        'PORTAL_PIN_SALT    = "%s"\n'
        'PORTAL_TOKEN_SEED  = "%s"\n'
        'PORTAL_COOKIE_NAME = "clinic_portal_device"\n'
    ) % (pin_hash, salt, token_seed)

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(body)
    os.chmod(CONFIG_PATH, stat.S_IRUSR | stat.S_IWUSR)   # 600 (owner only)

    # --- self-check: the PIN we just set must validate ----------------------
    ok = (make_hash(salt, pin1) == pin_hash)

    print()
    print("Done.")
    print("  Config written : " + CONFIG_PATH)
    print("  Permissions    : 600 (owner read/write only)")
    print("  Self-check     : " + ("PASS" if ok else "FAIL — please re-run setup"))
    print()
    print("IMPORTANT — record your PIN now in Apple Notes (your sealed recovery).")
    print("The PIN is the ONLY thing you need to log in again.")
    print("It is NOT stored in readable form anywhere on the server.")
    print()
    print("Next:  systemctl restart clinic-portal")


if __name__ == "__main__":
    main()
