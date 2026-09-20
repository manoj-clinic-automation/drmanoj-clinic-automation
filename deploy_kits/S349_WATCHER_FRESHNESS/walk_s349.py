#!/usr/bin/python3
# =============================================================================
#  walk_s349.py  ·  S349_WATCHER_FRESHNESS  ·  v1
#
#  Proves the kit on a COPY of the live finance_app.py and on freshness_page.py
#  without the live database, the live services or the network:
#
#    A · the patch applies exactly once, compiles, is idempotent, and changes
#        only the three places it names (every other line byte-identical);
#    B · THE WATCHER RULE, lifted OUT OF THE PATCHED FILE BY TEXT (the S319
#        technique -- what is tested is the code that will run, not a copy of
#        it), driven through a fake `setting` and a fake clock:
#          stale + Mon 11:00 IST            -> bad
#          stale + Mon 23:00 IST            -> info
#          stale + Sun 11:00 IST            -> info   (Sunday is out of hours)
#          stale + Sun 11:00, clinic_sunday -> bad
#          stale + hours moved to 10-13, at 09:30 -> info (the settings decide)
#          alive is False, any time         -> bad   (untouched branch)
#          alive True, fresh heartbeat      -> ok    (untouched branch)
#        + NEGATIVE CONTROL: the UNPATCHED text gives info at Mon 11:00 stale.
#    C · freshness_page: html_path() reads HTML_OUT from a conf, the env wins,
#        render() answers 503 with no file, 200 with the banner inside <body>,
#        the banner says STALE past 30 h, and the collector's own bytes are
#        returned unchanged below the banner;
#    D · LIVE SHAPE: a real Flask app, the module mounted through init() with a
#        fake require: a checker gets 200 + the banner; a non-checker gets 403;
#        the route is exactly /finance/freshness.
#
#  Run with the SAME python the service uses (/usr/bin/python3): flask must import.
# =============================================================================
import datetime as dt
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import time
import types

HERE = os.path.dirname(os.path.abspath(__file__))
LIVE = "/root/finance/finance_app.py"
OK, BAD = [], []


def check(name, cond):
    (OK if cond else BAD).append(name)
    print("   %s %s" % ("ok  " if cond else "FAIL", name))


# ------------------------------------------------------------------ A · patch
def lift_watcher(text):
    """The watcher block of _health_state, by text: from the `_w = _ps.get("watcher")`
    line to the line before the pull check's comment. Dedented into a function."""
    i = text.index('            _w = _ps.get("watcher") or {}\n')
    j = text.index('            # B2C: the pull itself failing is its own signal', i)
    block = text[i:j]
    lines = [ln[12:] if ln.startswith("            ") else ln for ln in block.splitlines()]
    src = ("def watcher_check(_ps, con, setting, add, dt):\n" +
           "\n".join("    " + ln for ln in lines) + "\n")
    ns = {}
    exec(compile(src, "<watcher>", "exec"), ns)
    return ns["watcher_check"]


class FakeDT(object):
    """A `dt` module stand-in with a fixed utcnow(); timedelta is the real one."""
    def __init__(self, ist):
        self._ist = ist
        self.timedelta = dt.timedelta

        class _D(object):
            @staticmethod
            def utcnow():
                return ist - dt.timedelta(hours=5, minutes=30)
        self.datetime = _D


def run_watcher(fn, ps, settings, ist):
    out = []

    def add(key, label, state, detail, hint=""):
        out.append((key, state, detail))

    def setting(con, key, default=None):
        return settings.get(key, default)
    fn(ps, None, setting, add, FakeDT(ist))
    assert len(out) == 1 and out[0][0] == "watcher", out
    return out[0][1], out[0][2]


def part_a_b(live):
    sys.path.insert(0, HERE)
    import patch_finance_app_s349 as P
    with open(live, "r", encoding="utf-8") as fh:
        text = fh.read()
    new, msgs = P.apply_to_text(text)
    already = (new == text and P.MARK in text)
    if already:
        print("   (the file already carries S349 -- testing it as it stands)")
        new = text
    check("A · the patch applies (or is already there)", new is not None)
    if new is None:
        print("   " + "; ".join(msgs))
        return None
    tmp = tempfile.mkdtemp(prefix="s349_")
    p = os.path.join(tmp, "patched.py")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(new)
    check("A · the patched file compiles",
          subprocess.run([sys.executable, "-B", "-m", "py_compile", p],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0)
    check("A · applying twice is a no-op", P.apply_to_text(new)[0] == new)
    if not already:
        a, b = text.splitlines(), new.splitlines()
        import difflib
        changed = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
        removed = [l for l in changed if l.startswith("-")]
        check("A · only the three named places change: 5 lines out (the info add(), the help-box close), %d in" % (len(changed) - len(removed)),
              len(removed) == 5 and all(("Medical PC capture" in l or "hours ago" in l or "float(_hbage)" in l
                                          or "hours; during the clinic day" in l or "record.</p></details>" in l) for l in removed))
        check("A · the 'alive is False' red branch is byte-identical", '            if _w.get("alive") is False:\n' in new
              and "the watcher is NOT running on the medical PC" in new)

    # --- B · the rule, lifted from the patched text ---------------------------
    fn = lift_watcher(new)
    stale = {"watcher": {"alive": True, "captures_today": 3}, "heartbeat": {"age_hours": 5.0}}
    fresh = {"watcher": {"alive": True, "captures_today": 3}, "heartbeat": {"age_hours": 0.2}}
    dead = {"watcher": {"alive": False}, "heartbeat": {"age_hours": 0.1}}
    mon11 = dt.datetime(2026, 9, 21, 11, 0)     # Monday
    mon23 = dt.datetime(2026, 9, 21, 23, 0)
    sun11 = dt.datetime(2026, 9, 20, 11, 0)     # Sunday
    base = {"pipeline.heartbeat_stale_hours": "2"}
    s, d = run_watcher(fn, stale, base, mon11)
    check("B · stale heartbeat, Monday 11:00 IST -> bad (DURING THE CLINIC DAY)", s == "bad" and "DURING THE CLINIC DAY" in d)
    s, d = run_watcher(fn, stale, base, mon23)
    check("B · stale heartbeat, Monday 23:00 IST -> info (out of hours)", s == "info" and "out of hours" in d)
    s, _ = run_watcher(fn, stale, base, sun11)
    check("B · stale heartbeat, Sunday 11:00 IST -> info (Sunday is out of hours)", s == "info")
    s, _ = run_watcher(fn, stale, dict(base, **{"pipeline.clinic_sunday": "1"}), sun11)
    check("B · ... but with pipeline.clinic_sunday = 1 -> bad", s == "bad")
    s, _ = run_watcher(fn, stale, dict(base, **{"pipeline.clinic_hour_from": "10", "pipeline.clinic_hour_to": "13"}),
                       dt.datetime(2026, 9, 21, 9, 30))
    check("B · hours moved to 10-13 by settings, 09:30 -> info (the settings decide)", s == "info")
    s, _ = run_watcher(fn, stale, dict(base, **{"pipeline.clinic_hour_from": "10", "pipeline.clinic_hour_to": "13"}),
                       dt.datetime(2026, 9, 21, 12, 30))
    check("B · ... and 12:30 -> bad", s == "bad")
    s, _ = run_watcher(fn, stale, dict(base, **{"pipeline.heartbeat_stale_hours": "8"}), mon11)
    check("B · a 5 h heartbeat under a 8 h window is not stale -> ok (the window setting still rules)", s == "ok")
    s, _ = run_watcher(fn, dead, base, mon23)
    check("B · alive is False, 23:00 -> bad (the untouched branch)", s == "bad")
    s, _ = run_watcher(fn, fresh, base, mon11)
    check("B · alive True, fresh heartbeat -> ok (the untouched branch)", s == "ok")
    s, _ = run_watcher(fn, {"heartbeat": {"age_hours": 0.1}}, base, mon11)
    check("B · no watcher section -> info (the untouched branch)", s == "info")
    if not already:
        fn0 = lift_watcher(text)
        s0, _ = run_watcher(fn0, stale, base, mon11)
        check("B · NEGATIVE CONTROL -- the UNPATCHED text says info at Monday 11:00 stale (the F-547 shape)", s0 == "info")
    shutil.rmtree(tmp, ignore_errors=True)
    return new


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


def main(argv):
    live = LIVE
    for a in argv[1:]:
        if a.startswith("--file="):
            live = a.split("=", 1)[1]
    if not os.path.isfile(live):
        print("RED -- %s is not there" % live)
        return 3
    print("-- A/B · the patch and the watcher rule (%s)" % live)
    part_a_b(live)
    print("-- C · freshness_page.py")
    part_c()
    print("-- D · live shape under flask (%s)" % sys.executable)
    part_d()
    print("\n%d check(s) ok, %d failed" % (len(OK), len(BAD)))
    if BAD:
        print("RED: " + "; ".join(BAD))
        return 1
    print("WALK OK -- %d checks" % len(OK))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
