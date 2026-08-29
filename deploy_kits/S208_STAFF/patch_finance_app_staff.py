#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""patch_finance_app_staff.py — mount the staff joiner/exit register + its guided page.

ONE EDIT, AND IT REFUSES IF ANY ANCHOR IS NOT EXACTLY WHERE IT EXPECTS IT.

    the mount               two lines, immediately before __main__, so the
                            blueprint is registered at import time and gunicorn
                            sees it. darpan_app installs its own before_request
                            guard (the duplicate-filing block) at init -- no
                            edit to the app's gate is needed at all.

WHY A PROGRAM AND NOT AN INSTRUCTION
    Same reason as the stock ledger: a rule that depends on somebody
    remembering it is not a rule. Idempotent; --revert removes it byte-exactly;
    a hand-edited block is refused, never overwritten. The stock-ledger block,
    if present, is left completely alone.

    python3 patch_finance_app_staff.py --check  /root/finance/finance_app.py
    python3 patch_finance_app_staff.py --apply  /root/finance/finance_app.py
    python3 patch_finance_app_staff.py --revert /root/finance/finance_app.py

Exit 0 = done or already done · 1 = refused, nothing written.
"""
import io
import os
import sys

BEGIN = "# --- S208_STAFF begin -- the joiner/exit register, mounted here ---"
END = "# --- S208_STAFF end ---"

MOUNT = BEGIN + """
# The S207 register, byte-for-byte (65 checks), mounted under /finance/staff
# so the portal proxy reaches it, plus the guided page. What was prepared is
# not rebuilt -- this only gives it an address and a face.
import staff_pages                                            # noqa: E402
import joiner_app                                             # noqa: E402
joiner_app.init(app, db, staff_pages.joiner_require(require),
                url_prefix="/finance/staff")
staff_pages.init(app, require)
""" + END + "\n\n"

MAIN_ANCHOR = '\nif __name__ == "__main__":'

# Things that must exist before the mount can possibly work. Each is checked
# for EXACTLY ONE occurrence -- two would mean we cannot tell which one runs.
REQUIRED = ("\ndef require(", "\ndef db(", "\nMARG_TOKEN = ", "\nUNIT = ",
            "\napp = Flask(")


def read(path):
    with io.open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def check(src):
    """Return (ok, [notes]). Never modifies anything."""
    notes, ok = [], True
    for token in REQUIRED:
        n = src.count(token)
        if n != 1:
            ok = False
            notes.append("  REFUSE  %-18s occurs %d times, expected exactly 1"
                         % (token.strip(), n))
        else:
            notes.append("  ok      %s" % token.strip())

    n = src.count(MAIN_ANCHOR)
    if n != 1:
        ok = False
        notes.append("  REFUSE  '__main__' occurs %d times, expected 1" % n)
    else:
        notes.append("  ok      the mount point is where it should be")

    if MOUNT in src:
        notes.append("  ok      the register is already mounted")
    elif BEGIN in src:
        ok = False
        notes.append("  REFUSE  a staff block is present but does not match "
                     "— it has been edited by hand")
    return ok, notes


def apply(src):
    if MOUNT not in src:
        assert BEGIN not in src, "an unrecognised block is present"
        assert src.count(MAIN_ANCHOR) == 1
        src = src.replace(MAIN_ANCHOR, "\n" + MOUNT + MAIN_ANCHOR.lstrip("\n"))
    return src


def revert(src):
    if BEGIN in src:
        # The EXACT inverse of apply(): remove the exact text apply() inserted,
        # so a patch-then-revert round trip is byte-identical. If the block has
        # been hand-edited it will not match, and we refuse rather than guess --
        # a revert that "tidies up" is how a file quietly loses a line.
        block = MOUNT if MOUNT in src else V2_MOUNT
        if src.count(block) != 1:
            raise SystemExit("!! the mounted block has been edited by hand -- "
                             "refusing to remove it. Restore from the .bak "
                             "the installer made.")
        src = src.replace(block, "")
    return src


def main(argv):
    mode = argv[1] if len(argv) > 2 else ""
    path = argv[2] if len(argv) > 2 else ""
    if mode not in ("--check", "--apply", "--revert") or not path:
        print(__doc__)
        return 1
    if not os.path.isfile(path):
        print("!! not a file: %s" % path)
        return 1
    src = read(path)
    ok, notes = check(src)
    print("anchors in %s:" % os.path.basename(path))
    for n in notes:
        print(n)
    if mode == "--check":
        print("RESULT: %s" % ("PASS" if ok else "REFUSED"))
        return 0 if ok else 1
    if not ok:
        print("RESULT: REFUSED -- nothing written.")
        return 1
    out = apply(src) if mode == "--apply" else revert(src)
    if out == src:
        print("RESULT: already in the state you asked for -- nothing written.")
        return 0
    write(path, out)
    print("RESULT: %s, %d bytes -> %d bytes."
          % ("mounted" if mode == "--apply" else "removed", len(src), len(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
