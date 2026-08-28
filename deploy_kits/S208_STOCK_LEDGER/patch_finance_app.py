#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""patch_finance_app.py — mount the stock ledger inside the finance app.

TWO EDITS, AND IT REFUSES IF EITHER ANCHOR IS NOT EXACTLY WHERE IT EXPECTS IT.

    1. the front gate            let the pharmacy sender's token open ONE more
                                 path -- /stock/api/snapshot -- exactly the way
                                 it already opens /finance/api/marg-push. Without
                                 this the nightly push is refused 401 before the
                                 route ever runs, and every difference stays open
                                 forever. That was the S207 fault.
    2. the mount                 two lines, immediately before __main__, so the
                                 blueprint is registered at import time and
                                 gunicorn sees it.

WHY A PROGRAM AND NOT AN INSTRUCTION
    "Add these two lines after require exists" is a rule that depends on
    somebody remembering it at 11pm. This asserts every anchor occurs EXACTLY
    ONCE and stops otherwise, it is idempotent (running it twice changes
    nothing), and --revert takes both edits out again.

    python3 patch_finance_app.py --check  /root/finance/finance_app.py
    python3 patch_finance_app.py --apply  /root/finance/finance_app.py
    python3 patch_finance_app.py --revert /root/finance/finance_app.py

Exit 0 = done or already done · 1 = refused, nothing written.
"""
import io
import os
import sys

BEGIN = "# --- S208_STOCK_LEDGER begin -- the stock ledger, mounted here ---"
END = "# --- S208_STOCK_LEDGER end ---"

MOUNT = BEGIN + """
# Two lines, and they must run at IMPORT time: gunicorn imports finance_app:app
# and never reaches __main__. stock_app owns its own tables inside the same
# finance.db, behind the same gate, in the same backup.
#
# The pages sit under /finance/stock, NOT /stock -- the web server proxies only
# the /finance context to this app, so /stock answered 404 from the outside
# while existing perfectly well inside. The prefix is stock_app.init's default,
# defined in ONE place, so it cannot drift from what push_snapshot.py sends.
import stock_app                                              # noqa: E402
stock_app.init(app, db, require, unit=UNIT, marg_token=MARG_TOKEN)
""" + END + "\n\n"

# v2 mounted the same feature at /stock. That install went green and was still
# unreachable: the proxy never forwarded it. These two constants exist so a
# server already carrying v2 is MIGRATED rather than refused -- and so that a
# block edited by hand is refused rather than silently overwritten.
V2_MOUNT = BEGIN + """
# Two lines, and they must run at IMPORT time: gunicorn imports finance_app:app
# and never reaches __main__. stock_app owns its own tables inside the same
# finance.db, behind the same gate, in the same backup.
import stock_app                                              # noqa: E402
stock_app.init(app, db, require, unit=UNIT, marg_token=MARG_TOKEN)
""" + END + "\n\n"

GATE_ANCHOR = '"/finance/api/pipeline-status")'
GATE_PATCHED = ('"/finance/api/pipeline-status",\n'
                '                            "/finance/stock/api/snapshot")')
GATE_V2 = ('"/finance/api/pipeline-status",\n'
           '                            "/stock/api/snapshot")')

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

    n = src.count(GATE_ANCHOR)
    if GATE_PATCHED in src:
        notes.append("  ok      the gate already lets the sender in")
    elif GATE_V2 in src:
        notes.append("  ok      the gate carries the v2 path — it will be moved")
    elif n != 1:
        ok = False
        notes.append("  REFUSE  the gate anchor occurs %d times, expected 1" % n)
    else:
        notes.append("  ok      the gate anchor is where it should be")

    n = src.count(MAIN_ANCHOR)
    if n != 1:
        ok = False
        notes.append("  REFUSE  '__main__' occurs %d times, expected 1" % n)
    else:
        notes.append("  ok      the mount point is where it should be")

    if MOUNT in src:
        notes.append("  ok      the stock ledger is already mounted")
    elif V2_MOUNT in src:
        notes.append("  ok      v2 is mounted at /stock — it will be moved to "
                     "/finance/stock")
    elif BEGIN in src:
        ok = False
        notes.append("  REFUSE  a stock-ledger block is present but matches "
                     "neither version — it has been edited by hand")
    return ok, notes


def apply(src):
    if GATE_V2 in src:                       # v2 -> v3: move the path
        src = src.replace(GATE_V2, GATE_PATCHED)
    elif GATE_PATCHED not in src:
        assert src.count(GATE_ANCHOR) == 1
        src = src.replace(GATE_ANCHOR, GATE_PATCHED)
    if V2_MOUNT in src:                      # v2 -> v3: swap the block
        src = src.replace(V2_MOUNT, MOUNT)
    elif MOUNT not in src:
        assert BEGIN not in src, "an unrecognised block is present"
        assert src.count(MAIN_ANCHOR) == 1
        src = src.replace(MAIN_ANCHOR, "\n" + MOUNT + MAIN_ANCHOR.lstrip("\n"))
    return src


def revert(src):
    if GATE_PATCHED in src:
        src = src.replace(GATE_PATCHED, GATE_ANCHOR)
    elif GATE_V2 in src:
        src = src.replace(GATE_V2, GATE_ANCHOR)
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
