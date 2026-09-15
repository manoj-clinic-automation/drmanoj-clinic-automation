#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prove_off_s274.py -- the ON-BOX proof, and it touches nothing live.

The guard reads the module-level _OFF_DIR. This imports each patched file as a
module, points _OFF_DIR at a temporary folder of its own, and proves the switch
there -- so no marker is ever created in the real /root/finance/_off and no
running cron job can be stopped by the proof.

It asserts, for each of the four files:
  * the helper and the guard are present
  * with its OWN marker in the temp folder, main() returns 0 and says so
  * with ALL_OFF, the same
  * with a ".txt" marker, the same
  * with NO marker, the guard does not fire
  * another job's marker does not stop it
"""
import importlib.util
import io
import os
import shutil
import sys
import tempfile

FILES = {
    "spine_cadence.py":    ("SPINE_OFF", "spine_cadence", ["--db", "/nonexistent.db"]),
    "sale_attribution.py": ("ATTRIBUTION_OFF", "sale_attribution", ["--db", "/nonexistent.db", "--report"]),
    "export_watch.py":     ("EXPORT_WATCH_OFF", "export_watch", ["--day", "today", "--db", "/nonexistent.db"]),
    "salts_refresh.py":    ("SALTS_REFRESH_OFF", "salts_refresh", ["--dry-run"]),
}

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name if cond else "%s  %s" % (name, detail))
    print(("   ok    " if cond else "   FAIL  ") + name + ("" if cond else "   " + detail))


def load(path, alias):
    spec = importlib.util.spec_from_file_location(alias, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


def call(mod, args):
    """Run main(args) and capture what it printed. Any exception is caught: a
    job that gets past the guard will usually fail on a missing database, and
    that is exactly what 'the guard did not fire' looks like."""
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    rc = None
    try:
        rc = mod.main(list(args))
    except BaseException as exc:            # SystemExit included
        rc = "exc:%s" % type(exc).__name__
    finally:
        sys.stdout = old
    return rc, buf.getvalue()


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "/root/finance"
    tmp = tempfile.mkdtemp(prefix="s274_proof_")
    offdir = os.path.join(tmp, "_off")
    os.makedirs(offdir)
    try:
        for name, (own, label, args) in sorted(FILES.items()):
            path = os.path.join(src, name)
            print("\n   -- %s" % name)
            if not os.path.isfile(path):
                check("%s exists" % name, False, "not found at %s" % path)
                continue
            text = io.open(path, encoding="utf-8").read()
            check("%s carries the helper" % name, "_off_marker" in text)
            check("%s names its own marker %s" % (name, own), '"%s"' % own in text)
            try:
                mod = load(path, "s274_" + label)
            except BaseException as exc:
                check("%s imports" % name, False, "%s: %s" % (type(exc).__name__, exc))
                continue
            if not hasattr(mod, "_OFF_DIR"):
                check("%s exposes _OFF_DIR" % name, False)
                continue
            check("%s points at the real folder by default" % name,
                  mod._OFF_DIR == "/root/finance/_off", mod._OFF_DIR)
            mod._OFF_DIR = offdir          # the proof never touches the real one

            for marker in (own, own + ".txt", "ALL_OFF"):
                p = os.path.join(offdir, marker)
                io.open(p, "w").write("proof\n")
                rc, out = call(mod, args)
                check("%s stops on %s" % (name, marker),
                      rc == 0 and ("%s: switched off" % label) in out,
                      "rc=%r out=%r" % (rc, out.strip()[:120]))
                os.remove(p)

            other = "SPINE_OFF" if own != "SPINE_OFF" else "ATTRIBUTION_OFF"
            p = os.path.join(offdir, other)
            io.open(p, "w").write("proof\n")
            rc, out = call(mod, args)
            check("%s is NOT stopped by %s" % (name, other),
                  ("%s: switched off" % label) not in out, out.strip()[:120])
            os.remove(p)

            rc, out = call(mod, args)
            check("%s runs past the guard with no marker" % name,
                  ("%s: switched off" % label) not in out, out.strip()[:120])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n   passed %d   failed %d" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print("   FAILED: %s" % f)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
