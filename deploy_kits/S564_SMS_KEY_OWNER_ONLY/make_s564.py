#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s564.py -- kit S564_SMS_KEY_OWNER_ONLY (15-Oct-2026): the anchored patcher.  Builds bank_sms.py from the box's LIVE
bytes by counted edits: the source must be at its FROM pin; each anchor must occur exactly once in the text it is applied to,
in order, else the build STOPS; the result must be at its TO pin.  Built in memory first; nothing is written unless it builds.
    python3 -B make_s564.py --fin /root/finance --out <dir>
Writes only into --out.  The change: the 'Phone setup -- MacroDroid' fold (and the read of the phone's key) is drawn for the
owner's login only (bank_standin.is_owner, fail-soft: cannot be read = NOT the owner); its step 4 says what the phone sends today."""
import argparse
import hashlib
import os
import sys

PINS = {
    'bank_sms.py': ('053d4ccb85d64403daf9918a0ba6f46c', 'aa5278403ec85c898d808486e4c3cde3'),
}
TO_PIN = 'aa5278403ec85c898d808486e4c3cde3'

OLD_STEP4 = ('<li>Body: content type <b>form</b> · field <code>text</code> = <code>[sms_message]</code> · field <code>sender</code> = '
             '<code>[sms_number]</code></li>\n')
NEW_STEP4 = ('<li>What the phone sends: the SMS <code>[sms_message]</code> in a query parameter on the URL, plus a field named '
             '<code>from</code> = <code>[sms_number]</code> (the SMS number) — the macro as set on 15-Oct-2026.</li>\n')

EDITS = {
    'bank_sms.py': [
        ('unit\'s day is worked again; what the door accepts and answers is unchanged.\n"""\n',
         'unit\'s day is worked again; what the door accepts and answers is unchanged.\n\n'
         'S564 (15-Oct-2026) -- THE PHONE\'S KEY FOR THE OWNER ONLY. The "Phone setup -- MacroDroid" fold, which prints the phone\'s\n'
         'door key, is drawn (and the key file read) only for the owner\'s login (bank_standin.is_owner; if that cannot be read, the\n'
         'login is treated as NOT the owner). For every other login the fold is absent. Its step 4 says what the phone sends today.\n'
         'The door and the key file are unchanged.\n"""\n'),
        ('    owner = bool(BS is not None and BS.is_owner(con, u))\n',
         '    try:                                         # S564: fail-soft -- the owner test cannot be read = NOT the owner\n'
         '        owner = bool(BS is not None and BS.is_owner(con, u))\n'
         '    except Exception:                            # noqa: BLE001\n'
         '        owner = False\n'),
        ('    key = _key()\n    out.append("""<details class="card"><summary><b>Phone setup — MacroDroid</b> (one time)</summary>\n',
         '    if owner:                                    # S564: the phone\'s key -- drawn for the owner\'s login only, no hint for anyone else\n'
         '        key = _key()\n        out.append("""<details class="card"><summary><b>Phone setup — MacroDroid</b> (one time)</summary>\n'),
        (OLD_STEP4, NEW_STEP4),
    ],
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(name, src_bytes, check_to=True):
    frm = PINS[name][0]
    if md5(src_bytes) != frm:
        raise SystemExit("STOP: %s is %s, not its FROM pin %s -- it changed after this kit was built" % (name, md5(src_bytes), frm))
    t = src_bytes.decode("utf-8")
    for i, (a, b) in enumerate(EDITS[name], 1):
        n = t.count(a)
        if n != 1:
            raise SystemExit("STOP: %s edit %d: its anchor occurs %d times (must be exactly once)" % (name, i, n))
        t = t.replace(a, b, 1)
    out = t.encode("utf-8")
    if check_to and md5(out) != TO_PIN:
        raise SystemExit("STOP: %s built to %s, not its TO pin %s" % (name, md5(out), TO_PIN))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fin", default="/root/finance")
    ap.add_argument("--out", required=True)
    ap.add_argument("--print-to", action="store_true", help="build without the TO check and print the md5 (kit authoring only)")
    a = ap.parse_args()
    built = {}
    for name in PINS:                              # in memory first
        with open(os.path.join(a.fin, name), "rb") as fh:
            built[name] = build(name, fh.read(), check_to=not a.print_to)
    if a.print_to:
        for name, out in built.items():
            print("%s %s" % (name, md5(out)))
        return 0
    os.makedirs(a.out, exist_ok=True)
    for name, out in built.items():
        with open(os.path.join(a.out, name), "wb") as fh:
            fh.write(out)
        print("built %s %s -> %s (%d counted edits)" % (name, PINS[name][0][:8], TO_PIN[:8], len(EDITS[name])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
