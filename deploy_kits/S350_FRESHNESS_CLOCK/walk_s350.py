#!/usr/bin/python3
# =============================================================================
#  walk_s350.py  ·  S350_FRESHNESS_CLOCK  ·  v1
#
#  The S349 walk's module checks (C, D) over the corrected freshness_page.py, PLUS the one
#  check S349's walk could not make because it handed render() its own clock: a file three
#  hours old rendered on the REAL clock, with the process clock set to IST as on the box
#  (TZ=Asia/Kolkata), must say "3.0 h ago" -- S349's module says "0 min ago" there
#  (negative control, run against the S349 bytes if they are beside this kit).
# =============================================================================
import datetime as dt
import importlib.util
import os
import shutil
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
OK, BAD = [], []


def check(name, cond):
    (OK if cond else BAD).append(name)
    print("   %s %s" % ("ok  " if cond else "FAIL", name))


# ------------------------------------------------------------ C · the module
def load_fp(env=None):
    for k in ("FRESHNESS_HTML", "FRESHNESS_CONF"):
        os.environ.pop(k, None)
    for k, v in (env or {}).items():
        os.environ[k] = v
    spec = importlib.util.spec_from_file_location("freshness_page_%d" % int(time.time() * 1000),
                                                  os.path.join(HERE, "freshness_page.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def part_c():
    tmp = tempfile.mkdtemp(prefix="s349c_")
    conf = os.path.join(tmp, "freshness.conf")
    with open(conf, "w") as fh:
        fh.write("# comment\nNTFY_TOPIC=x\nHTML_OUT=%s\n" % os.path.join(tmp, "custom.html"))
    m = load_fp({"FRESHNESS_CONF": conf})
    check("C · html_path() reads HTML_OUT= from the conf", m.html_path() == os.path.join(tmp, "custom.html"))
    with open(conf, "w") as fh:
        fh.write("NTFY_TOPIC=x\n")
    m = load_fp({"FRESHNESS_CONF": conf})
    check("C · without HTML_OUT it is freshness.html beside the conf (freshness.py's own rule)",
          m.html_path() == os.path.join(tmp, "freshness.html"))
    m = load_fp({"FRESHNESS_CONF": conf, "FRESHNESS_HTML": os.path.join(tmp, "env.html")})
    check("C · FRESHNESS_HTML in the environment wins", m.html_path() == os.path.join(tmp, "env.html"))
    st, html = m.render()
    check("C · no file -> 503 and says the collector has not written it", st == 503 and "not written" in html)
    page = ('<!DOCTYPE html><html><head><title>Clinic freshness</title></head>'
            '<body class="x"><h1>Clinic freshness</h1><table><tr><td>leg</td></tr></table></body></html>')
    with open(os.path.join(tmp, "env.html"), "w") as fh:
        fh.write(page)
    now = time.time()
    os.utime(os.path.join(tmp, "env.html"), (now - 600, now - 600))
    st, html = m.render(now=now)
    check("C · file present -> 200", st == 200)
    check("C · the banner sits INSIDE <body>, before the collector's own h1",
          html.index('<body class="x">') < html.index("This table was written") < html.index("<h1>Clinic freshness</h1>"))
    check("C · the banner says how long ago (10 min) and is not stale", "10 min ago" in html and "more than a day old" not in html)
    check("C · the collector's own bytes are returned unchanged around the banner",
          html.replace(html[html.index("<div style=\"font-family:system-ui"):html.index("</div>", html.index("This table was written")) + 6], "") == page)
    os.utime(os.path.join(tmp, "env.html"), (now - 40 * 3600, now - 40 * 3600))
    st, html = m.render(now=now)
    check("C · 40 h old -> the banner says STALE (the 08:05 collector has not run)", st == 200 and "more than a day old" in html)
    shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------- D · flask
def part_d():
    try:
        from flask import Flask
    except Exception as ex:                                     # noqa: BLE001
        check("D · flask imports under this python (%s)" % sys.executable, False)
        print("   ", ex)
        return
    tmp = tempfile.mkdtemp(prefix="s349d_")
    html = os.path.join(tmp, "f.html")
    with open(html, "w") as fh:
        fh.write("<html><body><h1>Clinic freshness</h1></body></html>")
    m = load_fp({"FRESHNESS_HTML": html})
    app = Flask("walk")
    who = {"role": "checker"}

    def require(*roles, **kw):
        if who["role"] in roles:
            return {"user": "walk", "role": who["role"]}, None
        return None, ("not permitted", 403)
    m.init(app, require)
    rules = [r.rule for r in app.url_map.iter_rules() if "freshness" in r.rule]
    check("D · the route is exactly /finance/freshness", rules == ["/finance/freshness"])
    c = app.test_client()
    r = c.get("/finance/freshness")
    check("D · LIVE SHAPE: a checker gets 200 with the banner and the collector's table",
          r.status_code == 200 and b"This table was written" in r.data and b"<h1>Clinic freshness</h1>" in r.data)
    who["role"] = "maker"
    r = c.get("/finance/freshness")
    check("D · a non-checker gets 403", r.status_code == 403)
    shutil.rmtree(tmp, ignore_errors=True)



def part_e():
    """The real clock, under the box's own timezone."""
    os.environ["TZ"] = "Asia/Kolkata"
    try:
        time.tzset()
    except Exception:                                           # noqa: BLE001
        pass
    tmp = tempfile.mkdtemp(prefix="s350e_")
    html = os.path.join(tmp, "f.html")
    with open(html, "w") as fh:
        fh.write("<html><body><h1>Clinic freshness</h1></body></html>")
    three_h = time.time() - 3 * 3600
    os.utime(html, (three_h, three_h))
    m = load_fp({"FRESHNESS_HTML": html})
    st, out = m.render()                      # NO clock handed in: the module's own
    check("E · REAL CLOCK under TZ=Asia/Kolkata: a 3 h old file reads '3.0 h ago' (S349 read '0 min ago')",
          st == 200 and "3.0 h ago" in out)
    old = os.path.join(HERE, "..", "S349_WATCHER_FRESHNESS", "freshness_page.py")
    if os.path.isfile(old):
        spec = importlib.util.spec_from_file_location("fp349", old)
        m0 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m0)
        st0, out0 = m0.render()
        check("E · NEGATIVE CONTROL -- the S349 module on the same file and clock says '0 min ago'",
              st0 == 200 and "0 min ago" in out0)
    shutil.rmtree(tmp, ignore_errors=True)


def main(argv):
    print("-- C · freshness_page.py")
    part_c()
    print("-- D · live shape under flask (%s)" % sys.executable)
    part_d()
    print("-- E · the real clock")
    part_e()
    print("\n%d check(s) ok, %d failed" % (len(OK), len(BAD)))
    if BAD:
        print("RED: " + "; ".join(BAD))
        return 1
    print("WALK OK -- %d checks" % len(OK))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
