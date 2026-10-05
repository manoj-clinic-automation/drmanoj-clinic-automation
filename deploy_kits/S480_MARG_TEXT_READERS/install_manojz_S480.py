#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""install_manojz_S480.py -- kit S480_MARG_TEXT_READERS: the three files on Dr Manoj's PC (manojz). Run from THIS folder in the repository:

    python -B install_manojz_S480.py            place:  pins FROM -> TO, a .bak_S480_<from8> beside each, md5 read back; any red -> all put back
    python -B install_manojz_S480.py --undo     put the three .bak_S480_<from8> back, md5 read back
    python -B install_manojz_S480.py --check    read only: where each file stands

  D:\Downloads\margsync\MargPull\signatures.json   7f72c572 -> this folder's signatures.json (the same bytes the server holds after the kit)
  D:\Downloads\margsync\MargPull\marg_report.py    28b47d44 -> this folder's marg_report.py   (eeab5605 + the EMPTY rule; masked fixtures)
  D:\Downloads\margsync\PUSH_STOCK_DAILY.bat       5cbec862 -> ONE line: set KIT= points at this folder, whose push_expected.py and
                                                               marg_report.py the .bat then runs (S208_STOCK_LEDGER is frozen, F-512)

Not touched: MargPull\marg_router.py (318086e3 -- it reads the signatures), expected_on_capture.py (bd8565d6), every other file.
Self-contained: it imports nothing from the repository.
"""
import hashlib
import os
import sys

KIT = "S480_MARG_TEXT_READERS"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("S480_MARGSYNC", r"D:\Downloads\margsync")
KIT_LIVE = r"D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S480_MARG_TEXT_READERS"
BAT_OLD = b"set KIT=D:\\dr-manoj-git\\drmanoj-clinic-automation\\deploy_kits\\S208_STOCK_LEDGER\r\n"
BAT_NEW = b"set KIT=" + KIT_LIVE.encode("ascii") + b"\r\n"
FILES = [   # (the live file, its FROM pin, where the new bytes come from)
    (os.path.join(ROOT, "MargPull", "signatures.json"), "7f72c572808218fbfc008373336beea8", "signatures.json"),
    (os.path.join(ROOT, "MargPull", "marg_report.py"), "28b47d447cfd966411742055717a5c56", "marg_report.py"),
    (os.path.join(ROOT, "PUSH_STOCK_DAILY.bat"), "5cbec862593e201884b8f372775c7db2", None),
]
READ_ONLY = [(os.path.join(ROOT, "MargPull", "marg_router.py"), "318086e36b0088f2da57b95d19a86b98"),
             (os.path.join(ROOT, "MargPull", "expected_on_capture.py"), "bd8565d632fe20ce899bfbfc125c487c")]


def rd(p):
    with open(p, "rb") as fh:
        return fh.read()


def md5(b):
    return hashlib.md5(b).hexdigest()


def new_bytes(live, src):
    if src is not None:
        return rd(os.path.join(HERE, src))
    if live.count(BAT_OLD) != 1:
        raise SystemExit("!! PUSH_STOCK_DAILY.bat: its 'set KIT=' line is not there exactly once -- nothing placed")
    return live.replace(BAT_OLD, BAT_NEW)


def bak(path, frm):
    return "%s.bak_S480_%s" % (path, frm[:8])


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    undo, check = "--undo" in argv, "--check" in argv
    ro0 = [(p, md5(rd(p))) for p, _pin in READ_ONLY]
    for (p, pin), (_p, now) in zip(READ_ONLY, ro0):
        print("read only  %s  %s%s" % (now[:8], p, "" if now == pin else "   (NOT its pin %s)" % pin[:8]))
    if not undo and any(now != pin for (_p, pin), (_q, now) in zip(READ_ONLY, ro0)):
        if not check:
            raise SystemExit("!! a file this kit was walked against has moved -- nothing placed")
    plan = []
    for path, frm, src in FILES:
        live = rd(path)
        try:
            to = new_bytes(live, src) if md5(live) == frm else None
        except SystemExit:
            to = None
        to_md5 = md5(to) if to is not None else None
        b = bak(path, frm)
        state = "FROM" if md5(live) == frm else ("TO" if (os.path.exists(b) and md5(rd(b)) == frm and
                                                           md5(live) == md5(new_bytes(rd(b), src))) else "OTHER")
        plan.append(dict(path=path, frm=frm, live=live, to=to, to_md5=to_md5, bak=b, state=state))
        print("%-5s %s  %s%s" % (state, md5(live)[:8], path, ("  -> %s" % to_md5[:8]) if to_md5 else ""))
    if check:
        return 0
    if undo:
        for f in plan:
            if not os.path.exists(f["bak"]) or md5(rd(f["bak"])) != f["frm"]:
                raise SystemExit("!! %s is not there at its pin -- nothing put back" % f["bak"])
        for f in plan:
            with open(f["path"], "wb") as fh:
                fh.write(rd(f["bak"]))
        bad = [f["path"] for f in plan if md5(rd(f["path"])) != f["frm"]]
        for f in plan:
            print("put back  %s  %s" % (md5(rd(f["path"])), f["path"]))
        print("S480 manojz: %s" % ("UNDO RED -- %s" % bad if bad else "UNDONE (the three .bak_S480 files stay beside them)"))
        return 1 if bad else 0
    if all(f["state"] == "TO" for f in plan):
        print("-- ALREADY PLACED: the three files are at the kit's bytes")
        return 0
    if any(f["state"] != "FROM" for f in plan):
        raise SystemExit("!! a file is neither at its FROM pin nor placed by this kit -- someone changed it since the brief; nothing placed")
    if os.path.normcase(HERE) != os.path.normcase(KIT_LIVE):
        raise SystemExit("!! run this from %s (the folder the .bat will point at), not from %s -- nothing placed" % (KIT_LIVE, HERE))
    for need in ("push_expected.py", "marg_report.py", "signatures.json"):
        if not os.path.isfile(os.path.join(HERE, need)):
            raise SystemExit("!! %s is not in this folder -- nothing placed" % need)
    for f in plan:                                           # back up first, read every backup back
        with open(f["bak"], "wb") as fh:
            fh.write(f["live"])
        if md5(rd(f["bak"])) != f["frm"]:
            raise SystemExit("!! the backup %s does not read back -- nothing placed" % f["bak"])
    try:
        for f in plan:
            with open(f["path"], "wb") as fh:
                fh.write(f["to"])
        for f in plan:
            if md5(rd(f["path"])) != f["to_md5"]:
                raise RuntimeError("md5 read-back of %s" % f["path"])
        if [(p, md5(rd(p))) for p, _pin in READ_ONLY] != ro0:
            raise RuntimeError("a read-only file moved")
    except Exception as ex:                                  # noqa: BLE001 -- red after placing: everything put back, byte-identically
        for f in plan:
            with open(f["path"], "wb") as fh:
                fh.write(f["live"])
        print("!! RED after placing (%s) -- the three files put back: %s" % (ex, [md5(rd(f["path"]))[:8] for f in plan]))
        return 1
    for f in plan:
        print("placed  %s -> %s  %s   (backup %s)" % (f["frm"][:8], md5(rd(f["path"])), f["path"], os.path.basename(f["bak"])))
    print("S480 manojz: PLACED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
