#!/usr/bin/env python3
"""
sweep_daily.py -- S210: the read-only daily sweep (S209 stocktake §4B).

Three questions, asked automatically instead of by the owner:
  1  does every page's JavaScript PARSE?           (the F-241 class)
  2  does every path a page fetch()es EXIST        (the "could not load" class)
     as a route in the apps?
  3  which API routes does NO page call?           (the F-161 / F-245 class --
     engine wired to nothing, twice in one day at S209)

READ-ONLY. Touches nothing, changes nothing, needs no restart. Exit 0 = quiet,
exit 1 = findings (prints them). Run by hand or from cron.

USAGE (VPS):
    /root/wa/venv/bin/python3 sweep_daily.py /root/finance
    python3 sweep_daily.py --selftest
"""
import os, re, subprocess, sys, tempfile

FETCH_RE = re.compile(r"""fetch\(\s*["'](/[^"'?]+)""")
ROUTE_RE = re.compile(r"""@(?:app|bp)\.route\(\s*["'](/[^"']+)["']""")
SCRIPT_RE = re.compile(r"<script[^>]*>(.*?)</script>", re.S | re.I)

def js_ok(html_text):
    """node --check on each script block; (ok, first_error)."""
    for blk in SCRIPT_RE.findall(html_text):
        if not blk.strip():
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                          encoding="utf-8") as f:
            f.write(blk); tmp = f.name
        try:
            r = subprocess.run(["node", "--check", tmp],
                               capture_output=True, text=True)
            if r.returncode != 0:
                return False, r.stderr.strip().splitlines()[-1][:160]
        finally:
            os.unlink(tmp)
    return True, ""

def route_covers(route, path):
    """Flask route pattern vs a fetched path. A path ending in '/' is a
    CONCATENATION PREFIX (fetch("/x/"+id)) and matches any route it starts."""
    if path.endswith("/"):
        return route.startswith(path) or route.startswith(path.rstrip("/"))
    pat = re.sub(r"<[^>]+>", "[^/]+", route)
    return re.fullmatch(pat, path) is not None

def sweep(root):
    pages, apps = [], []
    for dp, _dn, fn in os.walk(root):
        if any(x in dp for x in ("bak", "_to_delete", "__pycache__")):
            continue
        for n in fn:
            p = os.path.join(dp, n)
            if n.endswith(".html"):
                pages.append(p)
            elif n.endswith(".py") and not n.startswith("sweep_"):
                apps.append(p)
    routes, fetched, findings = [], {}, []
    for p in apps:
        try:
            routes += ROUTE_RE.findall(open(p, encoding="utf-8",
                                            errors="replace").read())
        except OSError:
            pass
    for p in pages:
        try:
            t = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        ok, err = js_ok(t)
        if not ok:
            findings.append("JS SYNTAX  %s: %s" % (os.path.basename(p), err))
        for u in FETCH_RE.findall(t):
            fetched.setdefault(u, []).append(os.path.basename(p))
    for u, srcs in sorted(fetched.items()):
        if not any(route_covers(r, u) for r in routes):
            findings.append("NO ROUTE   %s  (fetched by %s)" % (u, ",".join(sorted(set(srcs)))))
    for r in sorted(set(routes)):
        if "/api/" not in r:
            continue
        if not any(route_covers(r, u) for u in fetched):
            findings.append("NO CALLER  %s" % r)
    return findings

def selftest():
    ok = bad = 0
    def check(name, cond):
        nonlocal ok, bad
        if cond: ok += 1
        else: bad += 1; print("  FAIL:", name)
    import shutil
    d = tempfile.mkdtemp()
    open(os.path.join(d, "app.py"), "w").write(
        '@app.route("/x/api/used")\ndef a(): pass\n'
        '@app.route("/x/api/orphan")\ndef b(): pass\n'
        '@bp.route("/x/api/param/<int:i>/go")\ndef c(): pass\n')
    open(os.path.join(d, "good.html"), "w").write(
        '<script>fetch("/x/api/used").then(r=>r);fetch("/x/api/param/3/go");</script>')
    open(os.path.join(d, "broken.html"), "w").write(
        "<script>var s='patient's';</script>")
    open(os.path.join(d, "lost.html"), "w").write(
        '<script>fetch("/x/api/missing")</script>')
    f = sweep(d)
    check("broken JS caught", any(x.startswith("JS SYNTAX  broken") for x in f))
    check("fetch with no route caught", any("NO ROUTE   /x/api/missing" in x for x in f))
    check("orphan route caught", any("NO CALLER  /x/api/orphan" in x for x in f))
    check("used route NOT flagged", not any("/x/api/used" in x and "NO CALLER" in x for x in f))
    check("param route matched by concrete fetch", not any("param" in x for x in f))
    check("good page clean", not any("good" in x for x in f))
    shutil.rmtree(d)
    print("selftest: %d passed, %d failed" % (ok, bad))
    return 0 if bad == 0 else 1

def main(argv):
    """sweep_daily.py <root> [--baseline FILE [--write]]
    With a baseline: only findings NOT in it are reported (the daily mode --
    a standing orphan is a known fact, a NEW one is an alarm). --write records
    today's findings as the accepted baseline."""
    if len(argv) > 1 and argv[1] == "--selftest":
        return selftest()
    root = argv[1] if len(argv) > 1 else "."
    base_f = argv[argv.index("--baseline") + 1] if "--baseline" in argv else None
    f = sweep(root)
    if base_f and "--write" in argv:
        open(base_f, "w", encoding="utf-8").write("\n".join(f) + "\n")
        print("baseline written: %d accepted finding(s) -> %s" % (len(f), base_f))
        return 0
    if base_f and os.path.exists(base_f):
        known = set(open(base_f, encoding="utf-8").read().splitlines())
        f = [x for x in f if x not in known]
    if not f:
        print("SWEEP CLEAN -- nothing new since the baseline."
              if base_f else
              "SWEEP CLEAN -- every page parses, every fetch has a route, "
              "every API route has a caller.")
        return 0
    print("SWEEP FINDINGS (%d NEW):" % len(f))
    for x in f:
        print("  " + x)
    return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))
