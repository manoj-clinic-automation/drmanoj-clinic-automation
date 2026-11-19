#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s891.py -- S891 (the parent, S489, 19-Nov-2026): the owner's portal home redesigned (his 'ok' 08:12 on the live preview).
Reads the FROM portal.py (9da49bd1, S890's TO) and writes the TO beside it. Four exact anchors, each found exactly once:
  1. right after 'PORTAL_HTML = HOME_HEAD + \"\"\"' -- the S891 style block (s891_home.css), drawn on the home only (the Forms page,
     which shares HOME_HEAD, is untouched); backslashes doubled so the CSS reaches the page as written
  2-4. the call-alert card's title, its line and its button: English for the owner (role doctor), the Hindi kept for every staff home
  5. before the home's closing '</div></body></html>' -- the doctor-only script that turns the bar's own messages into English
    python3 make_s891.py <FROM portal.py> <s891_home.css> <s891_en.html> <TO portal.py>
"""
import hashlib
import sys

src, cssf, enf, out = sys.argv[1:5]
t = open(src, encoding="utf-8").read()
assert hashlib.md5(t.encode("utf-8")).hexdigest() == "9da49bd14088498e0fe27fbe2f13134a", "FROM is not 9da49bd1"
css = open(cssf, encoding="utf-8").read().replace("\\", "\\\\")
assert '"""' not in css and "{#" not in css and "{{" not in css and "{%" not in css
en = open(enf, encoding="utf-8").read()
assert '"""' not in en and "\\" not in en


def once(old, new):
    global t
    n = t.count(old)
    assert n == 1, "anchor found %d times: %r" % (n, old[:80])
    t = t.replace(old, new)


A1 = 'PORTAL_HTML = HOME_HEAD + """\n<div class="topbar">'
once(A1, 'PORTAL_HTML = HOME_HEAD + """\n<style id="s891">\n' + css + '</style>\n<div class="topbar">')
once('<div style="font-weight:600">कॉल आने पर मरीज़ का नाम</div>',
     '<div style="font-weight:600">{% if role == \'doctor\' %}Patient\'s name when a call comes{% else %}कॉल आने पर मरीज़ का नाम{% endif %}</div>')
once('font-size:13px">फ़ोन बजते ही नाम और पुरानी visit यहाँ दिखेगी</div>',
     'font-size:13px">{% if role == \'doctor\' %}The name and last visit show here as the phone rings{% else %}फ़ोन बजते ही नाम और पुरानी visit यहाँ दिखेगी{% endif %}</div>')
once('font-size:15px;font-weight:600">सूचना चालू करें</button>',
     'font-size:15px;font-weight:600">{% if role == \'doctor\' %}Turn on alerts{% else %}सूचना चालू करें{% endif %}</button>')
A5 = "      _pushState(DENIED_TXT, true);\n    }\n  }catch(e){ _pushDiag('load-error', {error: String(e&&e.message||e)}); }\n})();\n</script>\n</div></body></html>\n\"\"\""
once(A5, A5.replace("</script>\n</div></body></html>", "</script>\n" + en + "</div></body></html>"))
open(out, "w", encoding="utf-8").write(t)
print("make_s891: TO written", hashlib.md5(t.encode("utf-8")).hexdigest())
