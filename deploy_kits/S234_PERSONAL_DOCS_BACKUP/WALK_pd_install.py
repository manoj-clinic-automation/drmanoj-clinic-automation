#!/usr/bin/env python3
"""WALK_pd_install.py — S234_PERSONAL_DOCS_BACKUP

Drives install.sh in a sandbox with stand-in pull and bundle scripts and proves
the thing that matters most: that ANY failure leaves the conf byte-identical to
what it was, so tonight's pull runs exactly as last night's.

Offline. Touches no live path, no Google, no real conf.
"""
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
INSTALL = os.path.join(HERE, "install.sh")
BOOK_ID = "1AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
EXISTING = ("SHEETS=1aaa:tracker,1bbb:audit,1ccc:renewals,"
            "1ddd:payment_register")

fails = []
n = [0]


def check(name, cond):
    n[0] += 1
    if not cond:
        fails.append(name)
        print("  FAIL  %s" % name)


PULL_STUB = r'''#!/usr/bin/env python3
"""Stand-in for sheets_pull.py. Behaviour is driven by files in the sandbox so
the walk can make it succeed or fail without any network."""
import json, os, sys
root = os.environ["SB"]
mode = sys.argv[1] if len(sys.argv) > 1 else ""
if mode == "preflight":
    if os.path.exists(os.path.join(root, "NOT_SHARED")):
        print("book personal_docs: NOT reachable (permission)")
        sys.exit(41)
    print("5 of 5 book(s) reachable")
    sys.exit(0)
if mode == "run":
    if os.path.exists(os.path.join(root, "PULL_FAILS")):
        print("rate limited"); sys.exit(43)
    d = os.path.join(os.environ["SHEETS_ROOT"], "personal_docs")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "Sheet1.csv"), "w").write("a,b\n1,2\n")
    json.dump({"title": "Personal Documents", "row_total": 2,
               "tabs": [{"tab": "Sheet1", "file": "Sheet1.csv", "rows": 2}]},
              open(os.path.join(d, "_BOOK.json"), "w"))
    print("pulled")
    sys.exit(0)
if mode == "list":
    print("on disk: personal_docs")
    sys.exit(0)
sys.exit(0)
'''

BUNDLE_STUB = r'''#!/usr/bin/env python3
"""Stand-in for clinic_state_backup.py — writes the state file the installer
reads back to prove the new book actually shipped."""
import json, os, sys
root = os.environ["SB"]
sheets = os.environ["SHEETS_ROOT"]
src = []
if not os.path.exists(os.path.join(root, "BUNDLE_SKIPS_BOOK")):
    d = os.path.join(sheets, "personal_docs")
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        src.append(os.path.join(d, f))
src.append(os.path.join(sheets, "audit", "x.csv"))
json.dump({"sources": src, "files_included": len(src)},
          open(os.environ["STATE_JSON"], "w"))
print("shipped %d file(s)" % len(src))
sys.exit(0)
'''


def sandbox(with_book_id=True, conf_body=None):
    sb = tempfile.mkdtemp(prefix="s234pd_")
    kit = os.path.join(sb, "kit")
    os.makedirs(kit)
    sheets = os.path.join(sb, "sheets")
    os.makedirs(sheets)
    conf = os.path.join(sb, "conf")
    with open(conf, "w") as fh:
        fh.write("SA_JSON=%s\n" % os.path.join(sb, "sa.json"))
        fh.write((conf_body if conf_body is not None else EXISTING) + "\n")
        fh.write("SHRINK_GUARD_PCT=20\n")
    json.dump({"client_email": "clinic-backup@example.iam.gserviceaccount.com"},
              open(os.path.join(sb, "sa.json"), "w"))
    if with_book_id:
        open(os.path.join(kit, "BOOK_ID.txt"), "w").write(BOOK_ID + "\n")
    pull = os.path.join(sb, "sheets_pull.py")
    bundle = os.path.join(sb, "bundle.py")
    open(pull, "w").write(PULL_STUB)
    open(bundle, "w").write(BUNDLE_STUB)
    for p in (pull, bundle):
        os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)
    return sb, kit, conf, pull, bundle, sheets


def run(sb, kit, conf, pull, bundle, sheets):
    env = dict(os.environ)
    env.update({"CONF": conf, "PULL": pull, "BUNDLE": bundle,
                "KIT_DIR": kit, "PY": sys.executable, "SB": sb,
                "SHEETS_ROOT": sheets,
                "STATE_JSON": os.path.join(sb, "state.json")})
    p = subprocess.run(["bash", INSTALL], env=env, capture_output=True,
                       text=True)
    return p.returncode, p.stdout + p.stderr


def sheets_line(conf):
    for line in open(conf):
        if line.startswith("SHEETS="):
            return line.rstrip("\n")
    return ""


def main():
    print("WALK_pd_install — S234_PERSONAL_DOCS_BACKUP")

    # 1 · the ordinary run
    sb, kit, conf, pull, bundle, sheets = sandbox()
    before = sheets_line(conf)
    rc, out = run(sb, kit, conf, pull, bundle, sheets)
    check("install: exits 0", rc == 0)
    check("install: the book was added exactly once",
          sheets_line(conf).count(BOOK_ID) == 1)
    check("install: four books became five",
          len(sheets_line(conf).split(",")) ==
          len(before.split(",")) + 1)
    check("install: still exactly one SHEETS= line",
          sum(1 for l in open(conf) if l.startswith("SHEETS=")) == 1)
    check("install: the new book was pulled to disk",
          os.path.exists(os.path.join(sheets, "personal_docs", "Sheet1.csv")))
    check("install: it proved the book is INSIDE the shipped bundle",
          "inside the shipped bundle" in out)
    check("install: it prints the three lines and an undo",
          "books:" in out and "inbundle:" in out and "To undo:" in out)
    check("install: THE ID IS NEVER PRINTED", BOOK_ID not in out)

    # 2 · a second run is a no-op
    after1 = sheets_line(conf)
    rc2, out2 = run(sb, kit, conf, pull, bundle, sheets)
    check("second run: exits 0 and says it is already there",
          rc2 == 0 and "already there" in out2)
    check("second run: the conf is byte-identical",
          sheets_line(conf) == after1)
    shutil.rmtree(sb)

    # 3 · THE ONE THAT MATTERS: the sheet is not shared yet
    sb, kit, conf, pull, bundle, sheets = sandbox()
    open(os.path.join(sb, "NOT_SHARED"), "w").write("")
    before = open(conf).read()
    rc, out = run(sb, kit, conf, pull, bundle, sheets)
    check("not shared: stops, non-zero", rc != 0)
    check("not shared: THE CONF IS PUT BACK BYTE FOR BYTE",
          open(conf).read() == before)
    check("not shared: it names the service-account address to share with",
          "clinic-backup@example.iam.gserviceaccount.com" in out)
    check("not shared: it says the existing books are unaffected",
          "unaffected" in out)
    check("not shared: THE ID IS NEVER PRINTED", BOOK_ID not in out)
    shutil.rmtree(sb)

    # 4 · the pull itself fails after the conf was edited
    sb, kit, conf, pull, bundle, sheets = sandbox()
    open(os.path.join(sb, "PULL_FAILS"), "w").write("")
    before = open(conf).read()
    rc, out = run(sb, kit, conf, pull, bundle, sheets)
    check("pull fails: stops, non-zero", rc != 0)
    check("pull fails: the conf is put back byte for byte",
          open(conf).read() == before)
    shutil.rmtree(sb)

    # 5 · the bundle ships without the new book
    sb, kit, conf, pull, bundle, sheets = sandbox()
    open(os.path.join(sb, "BUNDLE_SKIPS_BOOK"), "w").write("")
    before = open(conf).read()
    rc, out = run(sb, kit, conf, pull, bundle, sheets)
    check("bundle misses it: stops rather than claiming success", rc != 0)
    check("bundle misses it: and says so in those words",
          "WITHOUT the new book" in out)
    check("bundle misses it: the conf is put back byte for byte",
          open(conf).read() == before)
    shutil.rmtree(sb)

    # 6 · no BOOK_ID.txt — the clone was not pulled
    sb, kit, conf, pull, bundle, sheets = sandbox(with_book_id=False)
    before = open(conf).read()
    rc, out = run(sb, kit, conf, pull, bundle, sheets)
    check("no id file: stops and says to run the first line again",
          rc != 0 and "deploy clone" in out)
    check("no id file: the conf was never touched",
          open(conf).read() == before)
    shutil.rmtree(sb)

    # 7 · a conf with two SHEETS lines is refused, not guessed at
    sb, kit, conf, pull, bundle, sheets = sandbox(
        conf_body=EXISTING + "\nSHEETS=1eee:stray")
    before = open(conf).read()
    rc, out = run(sb, kit, conf, pull, bundle, sheets)
    check("two SHEETS lines: refused", rc != 0 and "exactly one" in out)
    check("two SHEETS lines: the conf was never touched",
          open(conf).read() == before)
    shutil.rmtree(sb)

    print("")
    print("WALK_pd_install: %d checks, %d failures" % (n[0], len(fails)))
    for f in fails:
        print("  FAILED: %s" % f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
