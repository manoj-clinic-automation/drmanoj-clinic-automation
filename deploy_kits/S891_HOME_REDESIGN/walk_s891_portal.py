#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s891_portal.py -- S891: the owner's portal home redesigned. The real portal.py (TO, or the live one for the CONTROL) imported
in a scratch copy of the portal folder with made-up secrets; the home rendered for the owner and for a staff login, and the Forms
page, through the portal's own functions. The English script is checked by node --check and run in node against a stub page.
Nothing leaves the process.

    python3 -B walk_s891_portal.py --live <the portal folder> --files <folder holding portal.py> [--expect-red] [--box]
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

ARGS = sys.argv[1:]


def opt(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d


LIVE, FILES = opt("--live", "/root/portal"), opt("--files")
EXPECT_RED = "--expect-red" in ARGS
GREEN_BOTH = ("A0", "C4", "C5", "C6", "E2", "Z1")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s891portal_")
    try:
        app = os.path.join(work, "portal")
        shutil.copytree(LIVE, app, ignore=shutil.ignore_patterns("*.pyc", "__pycache__", "*BACKUP*", "*.bak*", "*.db", "*.log"))
        if FILES and os.path.isfile(os.path.join(FILES, "portal.py")):
            shutil.copy(os.path.join(FILES, "portal.py"), os.path.join(app, "portal.py"))
        env = dict(os.environ, PORTAL_PIN_HASH="x", PORTAL_PIN_SALT="walk-salt", PORTAL_TOKEN_SEED="walk-seed", CLINIC_SSO_SECRET="walk-sso",
                   TILE_GRANTS_FILE=os.path.join(app, "tile_grants.json"), PORTAL_FORMS_DIR=os.path.join(work, "forms"))
        r = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--inner", app, work] + ARGS, env=env, cwd=work,
                           capture_output=True, text=True, timeout=300)
        sys.stdout.write(r.stdout)
        if r.returncode not in (0, 1) or os.environ.get("S891_WALK_DEBUG"):
            print(r.stderr[-3000:])
        sys.exit(r.returncode)
    finally:
        shutil.rmtree(work, ignore_errors=True)

APPD = ARGS[ARGS.index("--inner") + 1]
WORK = ARGS[ARGS.index("--inner") + 2]
_me = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") not in (_me, os.path.abspath("."))]
sys.path.insert(0, APPD)
RES = {}


def ck(name, fn, detail=None):
    try:
        ok = bool(fn())
        d = "" if ok or detail is None else detail()
    except Exception as e:                                           # noqa: BLE001
        ok, d = False, repr(e)
    RES[name.split(" ")[0]] = ok
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:400]) if (d and not ok) else ""))


def node(args, timeout=60):
    try:
        return subprocess.run(["node"] + args, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return None


import portal as po                                                  # noqa: E402
from flask import render_template_string                             # noqa: E402

ck("A0 the real portal loads", lambda: po.app is not None)


def home_for(user, role):
    with po.app.test_request_context("/portal"):
        sections = po._visible_sections(role, False, user)
        blocks = po._home_blocks(sections, po._folders_for(user))
        who = {"user": user, "role": role}
        return render_template_string(po.PORTAL_HTML, sections=sections, blocks=blocks, sso=True, who=who, role=role, pc=False, s444_nowork=False), blocks


h, blocks = home_for("manoj", "doctor")
hs, _bs = home_for("shavez", "staff")
sty = re.search(r'<style id="s891">\n(.*?)</style>', h, re.S)
css = sty.group(1) if sty else ""
ck("C1 the owner's home carries the S891 style block exactly once, inside the body, after the head's own style",
   lambda: h.count('<style id="s891">') == 1 and h.index('<style id="s891">') > h.index("</style></head><body>"), lambda: h.count('<style id="s891">'))
slugs = re.findall(r'<button class="tile grp" type="button" id="gt-([^"]+)"', h)
ck("C2 every folder on the owner's home (%d) has its own colour in the block, and the panel too" % len(slugs),
   lambda: slugs and all(('[data-group="%s"],#g-%s{--acc:' % (s, s)) in css for s in slugs), lambda: [s for s in slugs if ('[data-group="%s"]' % s) not in css])
ck("C3 the CSS reaches the page as written: braces balance, the separator is the CSS escape \\00a0\\00b7 (backslash kept), no Jinja left",
   lambda: css and css.count("{") == css.count("}") and 'content:"\\00a0\\00b7  "' in css and "{%" not in css and "{{" not in css,
   lambda: (css.count("{"), css.count("}"), 'content:"\\00a0\\00b7' in css))
KCSS = os.path.join(FILES or "", "s891_home.css")
ck("C7 the style drawn on the page is the kit's s891_home.css byte for byte (the preview he approved, as written)",
   lambda: os.path.isfile(KCSS) and css == open(KCSS, encoding="utf-8").read(), lambda: (os.path.isfile(KCSS), len(css)))
ck("C4 the Forms page (it shares the head) carries no S891 block", lambda: "s891" not in po.FORMS_HTML and po.FORMS_HTML.startswith(po.HOME_HEAD))
ck("C5 the S890 folder lines and the Renewals mark are still on the owner's home (data-s890-renewals once, class gll)",
   lambda: h.count(" data-s890-renewals>") == 1 and 'class="gll"' in h, lambda: h.count(" data-s890-renewals>"))
ck("C6 a staff home still renders whole (its own tiles, </html>), with no doctor-only pieces",
   lambda: len(hs) > 1000 and "</html>" in hs and 'id="todayTile"' not in hs, lambda: len(hs))
ck("E1 the owner's call-alert card is in English: title, line and button; the Hindi title is not on his home",
   lambda: "Patient's name when a call comes" in h and "Turn on alerts</button>" in h and "The name and last visit show here" in h
   and "कॉल आने पर मरीज़ का नाम" not in h)
ck("E2 a staff home keeps the Hindi card and has no English script",
   lambda: "कॉल आने पर मरीज़ का नाम" in hs and "सूचना चालू करें</button>" in hs and "S891 (the owner" not in hs and "Turn on alerts" not in hs)
js = re.search(r"<script>\n(/\* S891 \(the owner, 19-Nov-2026\).*?)</script>", h, re.S)
jsok, jsmsg = False, "no script"
if js:
    jp = os.path.join(WORK, "s891.js")
    stub = ("var window=globalThis; var seen=[];\n"
            "function _pushSay(t){ seen.push(['say',t]); }\nfunction _pushState(t,w){ seen.push(['state',t,w]); }\n"
            "window._pushSay=_pushSay; window._pushState=_pushState;\n" + js.group(1) +
            "\nwindow._pushState('सूचना बंद है (blocked) — x', true); window._pushSay('✅ कॉल सूचना चालू है');"
            "window._pushState('नहीं हो पाया — NotAllowedError: y — दोबारा दबाएँ', true); window._pushState('', false); window._pushSay('other words');"
            "console.log(JSON.stringify(seen));\n")
    open(jp, "w", encoding="utf-8").write(stub)
    c = node(["--check", jp])
    if c is None:
        jsok, jsmsg = ("--box" in ARGS), "node is not here"
    elif c.returncode != 0:
        jsmsg = c.stderr[-300:]
    else:
        r = node([jp])
        out = (r.stdout or "").strip() if r else ""
        want = '[["state","Alerts are blocked — phone Settings → Apps → Chrome → Notifications on; then Chrome → Settings → Site settings → Notifications → allow followup.dr-manoj.in; then tap again",true],["say","✅ Call alerts are on"],["state","Could not turn on — NotAllowedError: y — tap again",true],["state","",false],["say","other words"]]'
        jsok, jsmsg = out == want, out[:400]
ck("E3 the English script is valid JavaScript and turns the page's own messages into English (unknown words pass through)", lambda: js and jsok, lambda: jsmsg)
src = open(os.path.join(APPD, "portal.py"), encoding="utf-8").read()
def _strip(t):
    t = re.sub(r'<style id="s891">\n.*?</style>\n', "", t, flags=re.S)
    t = re.sub(r"  \{% if role == 'doctor' %\}\n<script>\n/\* S891 \(the owner.*?</script>\n  \{% endif %\}\n", "", t, flags=re.S)
    t = re.sub(r"\{% if role == 'doctor' %\}[^{]*\{% else %\}([^{]*)\{% endif %\}", r"\1", t)
    return t
ck("D1 the file is the FROM plus exactly the S891 pieces (taken out, the rest is byte-for-byte 9da49bd1)",
   lambda: "s891" in src and hashlib.md5(_strip(src).encode("utf-8")).hexdigest() == "9da49bd14088498e0fe27fbe2f13134a",
   lambda: hashlib.md5(_strip(src).encode("utf-8")).hexdigest())
ck("Z1 the S657 folder script and the group grid are still on the page", lambda: "S657 (the owner, 26-Oct-2026): a group tile opens its panel IN PLACE" in h and 'id="groupGrid"' in h)
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad_ = [k for k in GREEN_BOTH if not RES.get(k)] + [k for k, v in RES.items() if v and k not in GREEN_BOTH]
    print("WALK S891 PORTAL CONTROL: %d red; %s" % (len(red), "AS IT MUST BE" if not bad_ else "NOT AS IT MUST BE: " + ", ".join(bad_)))
    sys.exit(0 if not bad_ else 1)
print("WALK S891 PORTAL: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
