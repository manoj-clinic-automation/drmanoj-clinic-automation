#!/usr/bin/env python3
# make_s366.py -- how portal.py S366 was made: four anchored edits on the LIVE bytes (portal.py 62b223cd, S364).
# Usage: python make_s366.py <live portal.py> <out portal.py>   (needs portal_push.py beside it for the card text)
import hashlib, os, sys
FROM = "62b223cd4086d673f550e5eccf3380e0"
src, out = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
assert hashlib.md5(b).hexdigest() == FROM, "live portal.py is not 62b223cd (S364)"
t = b.decode("utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import portal_push  # noqa: E402

def once(old, new, label):
    global t
    assert t.count(old) == 1, "anchor not unique: " + label + " (" + str(t.count(old)) + ")"
    t = t.replace(old, new)

# 1 -- the optional import beside the S364 one (a missing file = no card, nothing else changes)
once("except Exception:\n    _TRACKER_PASS = False\n",
     "except Exception:\n    _TRACKER_PASS = False\n\n"
     "# --- S366: the ring-time pop-up's portal half (optional: absent = no card, no push routes) ---\n"
     "try:\n    import portal_push\n    _PORTAL_PUSH = True\nexcept Exception:\n    _PORTAL_PUSH = False\n", "import")

# 2 -- the push routes, registered once login_required exists
once('        return redirect("/portal/login")\n    return wrapper\n',
     '        return redirect("/portal/login")\n    return wrapper\n\n\n'
     '# S366_RING_POPUP: /portal/sw.js · /portal/push/{key,status,subscribe,unsubscribe,test}\n'
     'if _PORTAL_PUSH:\n    try:\n        portal_push.install(app, login_required, _sso_user)\n'
     '    except Exception:\n        _PORTAL_PUSH = False\n', "routes")

# 3 -- the card at the top of the home page (hidden until the page learns this login owns a ringing phone)
once('<div class="wrap">\n  {% if role == \'doctor\' %}\n  <div class="strip">',
     '<div class="wrap">\n' + portal_push.CARD_HTML + '  {% if role == \'doctor\' %}\n  <div class="strip">', "card")

# 4 -- the card's script, at the end of the home page's own script
once("   .catch(function(){});\n})();\n</script>\n</div></body></html>\n\"\"\"",
     "   .catch(function(){});\n})();\n" + portal_push.CARD_JS + "</script>\n</div></body></html>\n\"\"\"", "script")

open(out, "wb").write(t.encode("utf-8"))
print("portal.py S366 ->", hashlib.md5(t.encode("utf-8")).hexdigest())
