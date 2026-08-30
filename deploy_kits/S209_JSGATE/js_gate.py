#!/usr/bin/env python3
"""
js_gate.py -- refuse a page whose inline JavaScript does not parse.

WHY THIS EXISTS (S209, 30-Aug-2026)
    finance_approvals.html shipped with an English possessive inside a
    single-quoted JS string:

        h+='... the same patient's own earlier sale bill ...';

    The string ends at "patient". The rest of the line is a syntax error, and
    a syntax error anywhere in a <script> block stops the WHOLE block running.
    Every section of the owner's money console sat on "loading" for a day.

    Every gate was green while this was true. The kit's SUMS.md5 passed (the
    file WAS delivered intact), the finance smoke suite passed (721 checks --
    it tests routes and payloads, not pages), and the close recorded the
    console as live and verified. Nothing in the toolchain parsed the page.
    "Intact" is not "valid".

WHAT IT DOES
    Extracts every inline <script> block (blocks with src= are external and are
    skipped), and runs `node --check` on each.

EXIT CODES -- deliberately three, not two (F-119: exiting on a warning is a
              silent pass, and a gate that cannot run must never look green)
    0  every block parsed
    1  a block FAILED to parse -- refuse the install
    2  the gate COULD NOT RUN (node missing, file unreadable). NOT a pass.

USAGE
    python3 js_gate.py PAGE.html [PAGE2.html ...]
    python3 js_gate.py --selftest
"""
import os, re, shutil, subprocess, sys, tempfile

BLOCK = re.compile(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', re.S | re.I)


def node_bin():
    for n in ("node", "nodejs"):
        p = shutil.which(n)
        if p:
            return p
    return None


def check_text(html, node):
    """Return (n_blocks, [(index, error_line)]). Raises nothing."""
    bad = []
    blocks = [b for b in BLOCK.findall(html) if b.strip()]
    for i, b in enumerate(blocks):
        fd, tmp = tempfile.mkstemp(suffix=".js")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(b)
            r = subprocess.run([node, "--check", tmp],
                               capture_output=True, text=True)
            if r.returncode != 0:
                lines = [l for l in r.stderr.splitlines() if "Error" in l]
                bad.append((i, (lines[0] if lines else r.stderr.strip()).strip()))
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass
    return len(blocks), bad


def check_file(path, node):
    try:
        html = open(path, encoding="utf-8", errors="replace").read()
    except Exception as e:
        print("  !! CANNOT READ %s -- %s" % (path, e))
        return 2
    n, bad = check_text(html, node)
    if n == 0:
        print("  -- %s: no inline script (nothing to check)" % path)
        return 0
    if not bad:
        print("  ok %s: %d block(s) parsed" % (path, n))
        return 0
    for i, err in bad:
        print("  !! %s: block %d -- %s" % (path, i, err))
    return 1


def selftest():
    node = node_bin()
    if not node:
        print("SELFTEST CANNOT RUN -- node is not installed")
        return 2
    ok = bad = 0

    def check(name, cond):
        nonlocal ok, bad
        if cond:
            ok += 1
        else:
            bad += 1
            print("  FAIL:", name)

    good = "<html><script>var a=1; function f(){return 'x';}</script></html>"
    check("a valid page passes", check_text(good, node)[1] == [])

    # the real S209 fault, reproduced exactly
    real = ("<html><script>var h='';"
            "h+='<div>the same patient's own earlier sale bill</div>';"
            "</script></html>")
    n, b = check_text(real, node)
    check("the S209 apostrophe fault is CAUGHT", len(b) == 1)

    check("a page with no script at all is not a failure",
          check_text("<html><body>hi</body></html>", node) == (0, []))

    ext = '<html><script src="/x.js"></script></html>'
    check("an external script is skipped, not guessed at",
          check_text(ext, node) == (0, []))

    two = "<html><script>var a=1;</script><script>var b=(;</script></html>"
    n2, b2 = check_text(two, node)
    check("the SECOND block is checked too, not just the first",
          n2 == 2 and len(b2) == 1 and b2[0][0] == 1)

    check("an empty block is ignored",
          check_text("<html><script>  </script></html>", node) == (0, []))

    print("selftest: %d passed, %d failed" % (ok, bad))
    return 0 if bad == 0 else 1


def main(argv):
    if len(argv) > 1 and argv[1] == "--selftest":
        return selftest()
    if len(argv) < 2:
        print(__doc__)
        return 2
    node = node_bin()
    if not node:
        print("!! JS GATE COULD NOT RUN -- node is not installed on this machine.")
        print("   Exit 2 means UNKNOWN, not OK. Install node, or check the page")
        print("   on a machine that has it, before trusting this install.")
        return 2
    print("JS gate (node: %s)" % node)
    worst = 0
    for p in argv[1:]:
        worst = max(worst, check_file(p, node))
    print("RESULT:", {0: "PASS", 1: "REFUSED -- a page's script does not parse",
                      2: "COULD NOT RUN"}[worst])
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv))
