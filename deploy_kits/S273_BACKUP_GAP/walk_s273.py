#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s273.py -- the LIVE-SHAPE walk for S273.

Not a unit test. It builds a mock ROOT out of **the box's own nightly bundle**
-- the real tree, the real file names, the real bytes -- adds the six files the
S258 measurement found had no off-box copy, adds eight decoys that MUST stay
out, and then runs BOTH the live `code_bundle.py` and the patched one in their
own `build` mode over that tree.

It asserts three things, and a kit that cannot assert all three is not installed:

  1. NOTHING IS LOST.   Every file the live tool carries, the patched tool still
     carries. This is the regression that matters: the v1.1 lesson was that a
     pattern change silently dropped live files.
  2. THE SIX ARE IN.    Each of the six named files is carried by the patched
     tool and by neither the live one.
  3. NO WALL MOVED.     Every decoy -- a key json, a config.py, a secret-named
     json, a database, an upload, a file under the deploy clone that is not on
     DEPLOY_ALLOW -- is carried by NEITHER tool.

Usage:  python3 walk_s273.py --bundle <code_nightly.tar.gz> --live <code_bundle.py>
                             --patched <code_bundle.py after the patch>
"""
import argparse
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile

# the six S258 named -- each must be carried AFTER and not BEFORE
WANT = [
    "root/assetapp/asset_register.py",
    "root/shared/sarvam_ocr.py",
    "root/deploy/email_agent.py",
    "root/deploy/gen_live_pins.py",
    "root/deploy/sweep_baseline.txt",
    "root/deploy/repo/deploy_kits/S229_ITEM_SPINE/marg_spine.py",
    "root/finance/freshness_legs.json",
]

# things that must be carried by NEITHER tool
DECOYS = [
    "root/finance/patient_fp_key.json",                 # *key*.json
    "root/finance/secret_rules.json",                   # "secret" substring
    "root/assetapp/portal_config.py",                   # *config*.py
    "root/assetapp/assets.db",                          # *.db*
    "root/assetapp/uploads/scan001.py",                 # not matched: no recurse
    "root/deploy/live_pins.txt",                        # .txt, NOT on DEPLOY_ALLOW
    "root/deploy/repo/deploy_kits/S225_SALTS/block.py",  # deploy clone, not allowed
    "root/shared/shared.conf",                          # *.conf
]

EXTRA_OK = [
    "root/assetapp/scanner_widget.js",
    "root/assetapp/smoke_test.py",
    "root/deploy/verify_live_pins.py",
    "root/deploy/repo/deploy_kits/S229_ITEM_SPINE/marg_spine_schema.sql",
    "root/finance/cards_registry.json",
]

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name if cond else "%s  %s" % (name, detail))
    print(("  ok    " if cond else "  FAIL  ") + name + ("" if cond else "   " + detail))


def write(path, text):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def build_root(bundle, box):
    root = os.path.join(box, "ROOT")
    os.makedirs(root)
    with tarfile.open(bundle, "r:gz") as tf:
        tf.extractall(root)
    for junk in ("MANIFEST.md5", "BUNDLE_INFO.txt", "crontab.txt"):
        p = os.path.join(root, junk)
        if os.path.exists(p):
            os.remove(p)

    body = "# fixture\nVALUE = 1\n\n\ndef main():\n    return VALUE\n"
    for rel in WANT + EXTRA_OK + DECOYS:
        if rel.endswith(".json"):
            write(os.path.join(root, rel), '{\n  "legs": [\n    {"name": "marg", "hours": 30}\n  ]\n}\n')
        elif rel.endswith(".txt"):
            write(os.path.join(root, rel), "baseline 2026-09-01\n")
        elif rel.endswith(".sql"):
            write(os.path.join(root, rel), "CREATE TABLE IF NOT EXISTS t (a TEXT);\n")
        elif rel.endswith(".db"):
            write(os.path.join(root, rel), "SQLite format 3\n")
        elif rel.endswith(".conf"):
            write(os.path.join(root, rel), "[shared]\nmode = 1\n")
        else:
            write(os.path.join(root, rel), body)
    return root


def carried(tool, root, box, label):
    """Run a code_bundle.py in build mode over `root` and return its file set."""
    env = dict(os.environ)
    env["ROOT"] = root
    out = os.path.join(root, "root", "state_backup", "code_nightly.tar.gz")
    if os.path.exists(out):
        os.remove(out)
    p = subprocess.run([sys.executable, tool, "build"], env=env,
                       capture_output=True, text=True, cwd=box)
    if not os.path.exists(out):
        print("---- %s produced no bundle ----" % label)
        print(p.stdout[-3000:])
        print(p.stderr[-2000:])
        return None
    with tarfile.open(out, "r:gz") as tf:
        names = set(n for n in tf.getnames() if n not in
                    ("MANIFEST.md5", "BUNDLE_INFO.txt", "crontab.txt"))
    return names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--live", required=True)
    ap.add_argument("--patched", required=True)
    a = ap.parse_args()

    box = tempfile.mkdtemp(prefix="s273_walk_")
    try:
        root = build_root(a.bundle, box)

        print("\n--- the LIVE tool over the mock tree ---")
        before = carried(a.live, root, box, "live")
        if before is None:
            return 1
        print("    carries %d files" % len(before))

        print("\n--- the PATCHED tool over the same tree ---")
        after = carried(a.patched, root, box, "patched")
        if after is None:
            return 1
        print("    carries %d files" % len(after))

        print("\n--- 1 · NOTHING IS LOST ---")
        lost = sorted(before - after)
        check("every file the live tool carries is still carried", not lost,
              "lost %d: %s" % (len(lost), lost[:6]))

        print("\n--- 2 · THE SIX ARE IN ---")
        for rel in WANT:
            check("carried now, not before: %s" % rel,
                  rel in after and rel not in before,
                  "after=%s before=%s" % (rel in after, rel in before))

        print("\n--- 2b · and the files that ride with them ---")
        for rel in EXTRA_OK:
            check("carried now: %s" % rel, rel in after)

        print("\n--- 3 · NO WALL MOVED ---")
        for rel in DECOYS:
            check("carried by NEITHER tool: %s" % rel,
                  rel not in after and rel not in before,
                  "after=%s before=%s" % (rel in after, rel in before))

        print("\n--- 4 · the shape of the change ---")
        gained = sorted(after - before)
        print("    +%d files, -%d files" % (len(gained), len(lost)))
        for g in gained:
            print("      + %s" % g)
    finally:
        shutil.rmtree(box, ignore_errors=True)

    print("\n" + "-" * 66)
    print("  passed %d   failed %d" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print("  FAILED: %s" % f)
    print("-" * 66)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
