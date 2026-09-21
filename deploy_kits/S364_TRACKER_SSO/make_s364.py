#!/usr/bin/env python3
# make_s364.py -- how portal.py S364 was made: three anchored edits on the LIVE bytes
# (portal.py d9a9dc40, read from the 21-Sep 01:35 bundle, = the Register's pin).
# Usage: python make_s364.py <live portal.py> <out portal.py>
import hashlib, sys

FROM = "d9a9dc409b203a4d8dcdd623aa54565f"
src, out = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
assert hashlib.md5(b).hexdigest() == FROM, "live portal.py is not d9a9dc40"
t = b.decode("utf-8")

def once(old, new, label):
    global t
    assert t.count(old) == 1, "anchor not unique: " + label + " (" + str(t.count(old)) + ")"
    t = t.replace(old, new)

EXEC = "https://script.google.com/macros/s/AKfycbyoQ5R3yvFC0B8arOnVWo4002BFfBGIVM2cBwpaMwUM4GaYw7d89jk1U_g38Ht0omcF/exec"

# 1 -- the optional import, beside the SSO libraries (a missing file = the old tile, never a crash)
once("""    import clinic_users
    _SSO_LIBS = True
except Exception:
    _SSO_LIBS = False
""", """    import clinic_users
    _SSO_LIBS = True
except Exception:
    _SSO_LIBS = False

# --- S364: the Callback Tracker opened already signed in (optional: absent = old tile) ---
try:
    import tracker_pass
    _TRACKER_PASS = True
except Exception:
    _TRACKER_PASS = False
""", "import")

# 2 -- the tile goes through the portal instead of straight to Google
once('''     "url": "%s",
     "roles": ["doctor"]},''' % EXEC, '''     "url": "/portal/go/call-tracker",
     "roles": ["doctor"]},''', "tile")

# 3 -- the two routes, after /portal/health
once('''    return {"service": "portal", "status": "ok" if ready else "unconfigured",
            "mode": mode}, (200 if ready else 503)
''', '''    return {"service": "portal", "status": "ok" if ready else "unconfigured",
            "mode": mode}, (200 if ready else 503)


# --- S364_TRACKER_SSO: the Callback Tracker opened from the Clinic app, already signed in ---
# The Tracker is a Google web app and cannot read our cookie. So the tile comes here; a signed-in
# person who is SHOWN the Call Tracker tile is sent on with a 120-second one-use pass
# (tracker_pass.py); the Tracker hands the pass back to /portal/sso/tracker-redeem server to
# server and signs that person in with their own agent key. Every failure -- and everyone who
# is not shown the tile -- lands on the plain Tracker address and its own key login, as before.
TRACKER_URL = "%s"


@app.route("/portal/go/call-tracker")
@login_required
def go_call_tracker():
    target = TRACKER_URL
    try:
        who = _sso_user(request)
        if who and _TRACKER_PASS:
            shown = {t["name"] for _g, _items in
                     _visible_sections(who["role"], _is_clinic_pc(request), who["user"])
                     for t in _items}
            if "Call Tracker" in shown:
                p = tracker_pass.mint(who["user"], who["role"],
                                      clinic_users.get_epoch(STORE), SSO_SECRET)
                target = TRACKER_URL + "?sso=" + urllib.parse.quote(p, safe="")
    except Exception:
        target = TRACKER_URL
    resp = make_response(redirect(target))
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["Referrer-Policy"] = "no-referrer"
    return resp


@app.route("/portal/sso/tracker-redeem", methods=["POST"])
def tracker_redeem():
    """Asked by the Tracker's own server (UrlFetchApp), never by a page. Answers who a live
    pass belongs to -- only if that person is still an active user, with their CURRENT role."""
    no = ({"ok": False}, 200)
    try:
        if not (_TRACKER_PASS and _sso_ready()):
            return no
        p = request.form.get("p") or ""
        if not p:
            p = (request.get_json(silent=True) or {}).get("p") or ""
        who = tracker_pass.redeem(p, SSO_SECRET, current_epoch=clinic_users.get_epoch(STORE))
        if not who:
            return no
        row = [u for u in clinic_users.list_users(STORE)
               if u.get("user") == who["user"] and u.get("active")]
        if not row:
            return no
        return {"ok": True, "user": who["user"], "role": row[0].get("role") or ""}, 200
    except Exception:
        return no
''' % EXEC, "routes")

open(out, "wb").write(t.encode("utf-8"))
print("portal.py S364 ->", hashlib.md5(t.encode("utf-8")).hexdigest())
