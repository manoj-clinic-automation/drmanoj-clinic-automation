#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_hub_autoapply_s243.py -- S243: the owner's hub says what the machine did.

TWO anchored changes to /root/finance/finance_ui/finance_approvals.html, inside
loadPushes() -- the pushed-reports table on the Marg card:

  1  an applied row whose applied_by is 'auto' reads
         "applied automatically <time>"      (was "loaded <time>" for every row)
  2  a superseded / rejected row names its rule when the server sent one:
         "superseded -- superseded by 1a2b3c4d"  /  "superseded -- older than applied"

Nothing else on the page moves (S218_CARDS_FINAL_CONTRACT rev 2 stands: no new
card, no new button).  Both anchors are the S218 FINAL bytes and are untouched by
every hub patch since (S219 M7, S220 x4 -- checked by grep at build).

    /root/wa/venv/bin/python3 -B patch_hub_autoapply_s243.py
        reads  HUB_PATH (default /root/finance/finance_ui/finance_approvals.html)
        writes HUB_PATH.new  (never the live file itself)
        prints the md5 before and after

Refuses unless each anchor occurs exactly once.  ALREADY PATCHED -> exit 0.
"""
import hashlib
import io
import os
import sys

TARGET = os.environ.get("HUB_PATH", "/root/finance/finance_ui/finance_approvals.html")
MARK = "S243 auto-apply"

A_OLD = ('              :(p.status==="applied"&&_loaded)?\'<span class="badge b-ok">✓ loaded \''
         '+esc((p.applied_at||"").slice(0,16))+"</span>"\n')
A_NEW = ('              :(p.status==="applied"&&_loaded)?\'<span class="badge b-ok">✓ \''
         '+(p.applied_by==="auto"?"applied automatically ":"loaded ")'
         '+esc((p.applied_at||"").slice(0,16))+"</span>" /* ' + MARK + ' */\n')

B_OLD = '              :\'<span class="badge b-bad">\'+esc(p.status)+"</span>";\n'
B_NEW = ('              :\'<span class="badge b-bad">\'+esc(p.status)'
         '+((p.auto&&p.auto.rule)?" — "+esc(p.auto.rule):"")+"</span>";\n')


def md5(b):
    return hashlib.md5(b).hexdigest()


def patch_text(src):
    if MARK in src:
        return src, "already"
    for nm, old in (("A", A_OLD), ("B", B_OLD)):
        n = src.count(old)
        if n != 1:
            return src, "refused: anchor %s occurs %d times (need exactly 1)" % (nm, n)
    return src.replace(A_OLD, A_NEW, 1).replace(B_OLD, B_NEW, 1), "patched"


def selftest(paths):
    ok = bad = 0

    def check(name, cond):
        nonlocal ok, bad
        if cond:
            ok += 1
            print("  PASS ", name)
        else:
            bad += 1
            print("  FAIL ", name)

    for p in paths:
        s = io.open(p, encoding="utf-8").read()
        out, st = patch_text(s)
        check("%s: patches (%s)" % (os.path.basename(p), st), st == "patched")
        if st != "patched":
            continue
        check("  applied-automatically wording present once",
              out.count('"applied automatically "') == 1)
        check("  the old wording survives for a hand apply", out.count('"loaded "') == 1)
        check("  the rule is shown on a superseded row", "p.auto.rule" in out)
        check("  only these two lines changed",
              sum(1 for a, b in zip(s.splitlines(), out.splitlines()) if a != b) == 2
              and len(s.splitlines()) == len(out.splitlines()))
        _, st2 = patch_text(out)
        check("  second run is a no-op", st2 == "already")
    _, st3 = patch_text("<html></html>\n")
    check("a stranger file is refused", st3.startswith("refused"))
    print("selftest: %d passed, %d failed" % (ok, bad))
    return 0 if bad == 0 else 1


def main(argv):
    if argv and argv[0] == "--selftest":
        return selftest(argv[1:])
    out_path = TARGET + ".new"
    if "--out" in argv:
        out_path = argv[argv.index("--out") + 1]
    raw = io.open(TARGET, "rb").read()
    src = raw.decode("utf-8")
    print("source %s md5 %s" % (TARGET, md5(raw)))
    new, st = patch_text(src)
    if st == "already":
        print("ALREADY PATCHED -- nothing to do")
        return 0
    if st != "patched":
        print("REFUSED: %s -- nothing written" % st[len("refused: "):])
        return 2
    io.open(out_path, "w", encoding="utf-8", newline="\n").write(new)
    print("wrote %s md5 %s" % (out_path, md5(new.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
