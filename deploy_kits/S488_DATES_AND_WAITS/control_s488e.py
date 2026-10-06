#!/usr/bin/env python3
"""control_s488e.py -- kit S488 part E, the negative control of walk 7.6 (the medical PC).

The NEW marg_watch.py's case function _s488_share_cases (the cases the NEW selftest runs) is run twice on scratch folders:
once with the NEW share_refused (must be green), once with the OLD file's share_refused (58b54f37, copied out of
deploy_kits/S480_MARG_TEXT_READERS into a temporary folder here, loaded under its own module name). The texts are kept
as refused by the NEW module's _keep_refused, which is byte-for-byte the OLD one (fdiff_s488e.py shows it unchanged).
Expected on OLD: the sale and register bodies and the whole reasons are copied -- those cases go RED.
Run with python -B from this folder, with marg_txt.py beside it; TEMP/TMP pointed inside this folder.
"""
import hashlib
import importlib.util
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = [p for p in (os.path.abspath(os.path.join(HERE, *[".."] * k)) for k in (2, 3)) if os.path.isdir(os.path.join(p, "deploy_kits", "S480_MARG_TEXT_READERS"))][0]   # the kit folder or a scratch folder
OLD_SRC = os.path.join(REPO, "deploy_kits", "S480_MARG_TEXT_READERS", "marg_watch.py")
OLD_PIN = "58b54f37865cb487720b95eaa4aedde5"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    if hashlib.md5(open(OLD_SRC, "rb").read()).hexdigest() != OLD_PIN:
        print("STOP: the OLD file is not %s" % OLD_PIN)
        return 2
    sys.path.insert(0, HERE)                                    # marg_txt.py beside this script
    tmp = tempfile.mkdtemp(prefix="ctl_s488e_", dir=HERE)
    try:
        os.makedirs(os.path.join(tmp, "old"))
        shutil.copyfile(OLD_SRC, os.path.join(tmp, "old", "marg_watch_old.py"))
        OLD = load("marg_watch_old", os.path.join(tmp, "old", "marg_watch_old.py"))
        NEW = load("marg_watch_new", os.path.join(HERE, "marg_watch.py"))
        NEW.NOTE_SINK = []                                      # notes are collected, never sent (as in the selftest)
        OLD.NOTE_SINK = []
        print("OLD %s  md5 %s" % (OLD_SRC, OLD_PIN))
        print("NEW %s  md5 %s" % (os.path.join(HERE, "marg_watch.py"),
                                  hashlib.md5(open(os.path.join(HERE, "marg_watch.py"), "rb").read()).hexdigest()))
        res = {}
        for tag, share in (("NEW", NEW.share_refused), ("OLD", OLD.share_refused)):
            got = []
            print("\n-- the walk 7.6 cases with the %s share_refused --" % tag)

            def ck(n, c):
                print(("  green " if c else "  RED   ") + n)
                got.append((n, bool(c)))
            NEW._s488_share_cases(ck, os.path.join(tmp, tag), share)
            res[tag] = got
        new_red = [n for n, c in res["NEW"] if not c]
        old_red = [n for n, c in res["OLD"] if not c]
        print("\nNEW: %d of %d green" % (len(res["NEW"]) - len(new_red), len(res["NEW"])))
        print("OLD: %d of %d RED -- the cases that fail on the OLD file:" % (len(old_red), len(res["OLD"])))
        for n in old_red:
            print("   RED  " + n)
        # what the OLD file actually put on Drive
        rtd = os.path.join(tmp, "OLD", "FromMedical", "refused_text")
        bodies = sorted(f for f in os.listdir(rtd) if f.endswith(".txt") and not f.endswith((".why.txt", ".withheld.txt")))
        whole = [f for f in os.listdir(rtd) if f.endswith(".why.txt") and b"from:" in open(os.path.join(rtd, f), "rb").read()]
        print("OLD put on Drive: %d bodies (%s) and %d whole-reason .why.txt (with 'from:'); .withheld.txt: %d"
              % (len(bodies), ", ".join(b.split("__")[1] for b in bodies), len(whole),
                 len([f for f in os.listdir(rtd) if f.endswith(".withheld.txt")])))
        ok = not new_red and len(old_red) >= 1
        print("\nCONTROL %s: NEW all green, OLD red on %d case(s)" % ("OK" if ok else "NOT AS EXPECTED", len(old_red)))
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
