#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""install_manojz_S482.py -- kit S482_BILL_CHAIN, Part E (F-731): the one file on Dr Manoj's PC (manojz). Run from THIS folder:

    python -B install_manojz_S482.py            place:  pin FROM -> TO, a .bak_S482_<from8> beside it, md5 read back; red -> put back
    python -B install_manojz_S482.py --undo     put the .bak_S482_<from8> back, md5 read back
    python -B install_manojz_S482.py --check    read only: where the file stands

  D:\Downloads\margsync\MargPull\marg_gate.py    52f502d1 -> f5de9b4e   (built HERE from the live bytes by make_s482.py --manojz: five
                                                                        anchored edits, each anchor exactly once)

The outbox no longer re-sends a VERIFIED EMPTY sale sheet (at most three rows in index.csv) to the clinic's sale-bill route, which
answered 422 no_item_detail every ten minutes: it is recorded `empty_day` in _outbox_state.json and skipped; the picture stops listing
the day as NOT SENT; a stale _NEEDS_ATTENTION.txt goes when nothing is left to send. A sheet with bill rows is never touched.

Not touched: pipeline_status.py, PULL_FROM_MEDICAL.bat, the token, every other file. The file is placed by a rename (the ten-minute
pull never reads half a file). It imports nothing from the repository: make_s482.py is RUN (python -B), not imported.
"""
import hashlib
import os
import subprocess
import sys

KIT = "S482_BILL_CHAIN"
HERE = os.path.dirname(os.path.abspath(__file__))
PULL = os.environ.get("S482_MARGPULL", r"D:\Downloads\margsync\MargPull")
LIVE = os.path.join(PULL, "marg_gate.py")
FROM = "52f502d1ee1a59e37086fb3e514f7874"
TO = "f5de9b4eb974052fd5773c270d1481b2"
BAK = "%s.bak_S482_%s" % (LIVE, FROM[:8])


def rd(p):
    with open(p, "rb") as fh:
        return fh.read()


def md5(b):
    return hashlib.md5(b).hexdigest()


def put(path, data):
    tmp = path + ".s482_new"
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, path)


def build():
    """The new bytes, built from the live file by the kit's own patcher into a scratch folder inside the repository."""
    repo = os.path.dirname(os.path.dirname(HERE))
    out = os.path.join(repo if os.path.isdir(os.path.join(repo, ".git")) else HERE, "_scratch", KIT, "manojz_build")
    p = subprocess.run([sys.executable, "-B", os.path.join(HERE, "make_s482.py"), "--manojz", PULL, "--out", out],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    print("   " + p.stdout.strip().replace("\n", "\n   "))
    if p.returncode != 0:
        raise SystemExit("!! make_s482.py did not build marg_gate.py -- nothing placed")
    return rd(os.path.join(out, "manojz", "marg_gate.py"))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    undo, check = "--undo" in argv, "--check" in argv
    now = md5(rd(LIVE))
    state = "FROM" if now == FROM else ("TO" if now == TO else "OTHER")
    print("%-5s %s  %s%s" % (state, now, LIVE, ("   backup %s %s" % (os.path.basename(BAK), md5(rd(BAK))[:8])) if os.path.exists(BAK) else ""))
    if check:
        return 0
    if undo:
        if not os.path.exists(BAK) or md5(rd(BAK)) != FROM:
            raise SystemExit("!! %s is not there at its pin -- nothing put back" % BAK)
        put(LIVE, rd(BAK))
        back = md5(rd(LIVE))
        print("put back  %s  %s" % (back, LIVE))
        print("S482 manojz: %s" % ("UNDONE (the .bak_S482 file stays beside it)" if back == FROM else "UNDO RED"))
        return 0 if back == FROM else 1
    if state == "TO":
        print("-- ALREADY PLACED: marg_gate.py is at the kit's pin")
        return 0
    if state != "FROM":
        raise SystemExit("!! marg_gate.py is neither at its FROM pin nor placed by this kit -- someone changed it since the brief; nothing placed")
    live = rd(LIVE)
    new = build()
    if md5(new) != TO:
        raise SystemExit("!! the built marg_gate.py is %s, not the kit's pin %s -- nothing placed" % (md5(new), TO))
    try:
        compile(new, LIVE, "exec")
    except SyntaxError as ex:
        raise SystemExit("!! the built marg_gate.py does not compile (%s) -- nothing placed" % ex)
    with open(BAK, "wb") as fh:
        fh.write(live)
    if md5(rd(BAK)) != FROM:
        raise SystemExit("!! the backup %s does not read back -- nothing placed" % BAK)
    put(LIVE, new)
    if md5(rd(LIVE)) != TO:
        put(LIVE, live)
        print("!! RED after placing (md5 read-back) -- put back: %s" % md5(rd(LIVE)))
        return 1
    print("placed  %s -> %s  %s   (backup %s)" % (FROM[:8], md5(rd(LIVE)), LIVE, os.path.basename(BAK)))
    print("S482 manojz: PLACED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
