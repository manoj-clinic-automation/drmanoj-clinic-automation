#!/usr/bin/env python3
"""make_s937.py -- kit S937_WA_ALL_AMPERSAND: porders_s454.py af66c3d3 -> TO, one exact anchor.
The WhatsApp-all confirm screen wrote the supplier keys into its <script> through html.escape -- inside <script> no entity is decoded,
so a key with '&' (RADHA MEDICAL & SCIENTIFIC), an apostrophe or '<' reached the server as '&amp;' / '&#x27;' and never equalled
wa_plan's list: 409 list_changed + reload, nothing queued. Now the list is JSON with & < > escaped as \\u00XX (JS reads the true name)."""
import hashlib, sys
src, dst = sys.argv[1], sys.argv[2]
FROM = "af66c3d36d90be1d540f2ddd525aab8b"
b = open(src, "rb").read()
if hashlib.md5(b).hexdigest() != FROM:
    sys.exit("not at FROM")
s = b.decode("utf-8")
OLD = '''% (P, esc(json.dumps([e["sn"] for e in q])).replace("&quot;", '"'), back))'''
NEW = '''% (P, _s937_js([e["sn"] for e in q]), back))          # S937: JSON for a <script>, never html.escape'''
assert s.count(OLD) == 1, "anchor 1"
s = s.replace(OLD, NEW)
OLD2 = '''def esc(s):
    return _html.escape("" if s is None else str(s), quote=True)
'''
NEW2 = OLD2 + '''

def _s937_js(v):
    """S937 (F-1619): a value written INSIDE a <script> element -- JSON, with & < > and the two JS line breaks as \\\\u escapes (the browser
    decodes no entity there; html.escape turned RADHA MEDICAL & SCIENTIFIC into '&amp;' and the WhatsApp-all list never matched)."""
    return (json.dumps(v, ensure_ascii=False).replace("&", "\\\\u0026").replace("<", "\\\\u003c").replace(">", "\\\\u003e")
            .replace("\\u2028", "\\\\u2028").replace("\\u2029", "\\\\u2029"))
'''
assert s.count(OLD2) == 1, "anchor 2"
s = s.replace(OLD2, NEW2)
open(dst, "w", encoding="utf-8").write(s)
print(hashlib.md5(s.encode("utf-8")).hexdigest())
