#!/usr/bin/env python3
"""patch_portal_f242_s239.py -- S239: END THE LOGIN LOOP (F-242) and close AF-12.

THE OWNER, 11-Sep-2026: "followup.dr-manoj.in keeps on hanging because of the cookie matter; staff face
problems; Amir could not do his entries that day."

THE CAUSE (F-242, reproduced by the S209 incident and the 07-Sep audit, AF-12):
  every broker login also planted an old 10-year "trusted device" cookie. When a person's real sign-in
  token ends -- after 30 days, or the moment ANYONE presses "Sign out everywhere" (a button that was on
  every STAFF home screen too) -- the browser keeps only the old cookie. /portal says "that is not an
  identity, sign in"; /portal/login says "you are signed in, go to /portal". Round and round, forever.
  The old cookie is HttpOnly, so no page could clear it, and /portal/logout did not exist.

THE FIX, five small edits to /root/portal/portal.py (live pin 7bc59115 -> new):
  1. /portal/login shows the sign-in form whenever there is no real sign-in, and CLEARS the old cookie
     -- the loop cannot happen, and a stuck phone frees itself by just opening the page.
  2. A login no longer plants the old cookie (sign-in stays 30 days, as always).
  3. With sign-ins in use, only a real sign-in counts as logged in (the old cookie alone opens nothing:
     not the case pack, not the WhatsApp sender -- AF-12).
  4. NEW /portal/logout -- signs this browser out cleanly.
  5. "Forget all devices" and "Sign out everywhere" appear, and work, for the doctor only.
Nothing else changes. Refuses unless the file is the pinned live version.
  usage: python3 patch_portal_f242_s239.py [portal.py path] [expected md5]
"""
import hashlib, sys, shutil, time
P = sys.argv[1] if len(sys.argv) > 1 else "/root/portal/portal.py"
FROM = sys.argv[2] if len(sys.argv) > 2 else "7bc591151553344e80d1e034a8f176d6"
src = open(P, encoding="utf-8").read()
have = hashlib.md5(src.encode("utf-8")).hexdigest()
if have != FROM:
    sys.exit("REFUSING: %s is %s, expected %s. Nothing changed." % (P, have, FROM))

EDITS = [
# 3 -- _authed: in broker mode only a real sign-in counts
('''def _authed(req) -> bool:
    """Logged in via a valid SSO cookie OR a trusted device (transition-safe)."""
    return (_sso_user(req) is not None) or _is_trusted(req)
''',
'''def _authed(req) -> bool:
    """Logged in via a valid SSO cookie. The legacy trusted-device cookie counts ONLY when broker
    mode is not available (PIN-era estate). S239/F-242/AF-12: in broker mode a device cookie alone
    is not a login -- it was the loop's second half and a 10-year credential."""
    if _sso_ready():
        return _sso_user(req) is not None
    return _is_trusted(req)
'''),
# 1 + 2 -- login: form when no real sign-in, clear the old cookie; no longer plant it
('''    if not _usable():
        return render_template_string(CONFIG_ERROR_HTML), 503
    if _authed(request):
        return redirect("/portal")
    error = ""
''',
'''    if not _usable():
        return render_template_string(CONFIG_ERROR_HTML), 503
    if _authed(request):
        return redirect("/portal")
    error = ""
    # S239/F-242: a browser holding only the old device cookie is NOT signed in -- show the form and
    # clear that cookie, so the page can never bounce back to /portal again.
    _stale_device = bool(request.cookies.get(COOKIE_NAME))
'''),
('''            if role:
                resp = make_response(redirect("/portal"))
                # 1) the SSO cookie -- rides to every .dr-manoj.in clinic app
                token = clinic_sso.make_token(user, role,
                                              clinic_users.get_epoch(STORE), SSO_SECRET)
                resp.set_cookie(clinic_sso.COOKIE_NAME, token, **clinic_sso.cookie_kwargs())
                # 2) the device-trust cookie -- keeps the portal's own access identical to before
                resp.set_cookie(
                    COOKIE_NAME, _expected_device_token(),
                    max_age=10 * 365 * 24 * 3600,
                    secure=True, httponly=True, samesite="Lax", path="/portal",
                )
                return resp
            error = "Wrong username or password."
        return render_template_string(USERPASS_HTML, error=error)
''',
'''            if role:
                resp = make_response(redirect("/portal"))
                # the SSO cookie -- rides to every .dr-manoj.in clinic app (30 days)
                token = clinic_sso.make_token(user, role,
                                              clinic_users.get_epoch(STORE), SSO_SECRET)
                resp.set_cookie(clinic_sso.COOKIE_NAME, token, **clinic_sso.cookie_kwargs())
                # S239/AF-12: the 10-year device cookie is no longer planted; an old one is removed
                resp.delete_cookie(COOKIE_NAME, path="/portal")
                return resp
            error = "Wrong username or password."
        resp = make_response(render_template_string(USERPASS_HTML, error=error))
        if _stale_device:
            resp.delete_cookie(COOKIE_NAME, path="/portal")
        return resp
'''),
# 3 -- case pack / WhatsApp: the device cookie alone is not a user in broker mode
('''def _is_casepack_user(req) -> bool:
    who = _sso_user(req)
    if who is None:
        return _is_trusted(req)
''',
'''def _is_casepack_user(req) -> bool:
    who = _sso_user(req)
    if who is None:
        return (not _sso_ready()) and _is_trusted(req)      # S239/AF-12: F-98 completed
'''),
('''def _is_wa_user(req) -> bool:
    who = _sso_user(req)
    if who is None:
        return _is_trusted(req)
''',
'''def _is_wa_user(req) -> bool:
    who = _sso_user(req)
    if who is None:
        return (not _sso_ready()) and _is_trusted(req)      # S239/AF-12: F-98 completed
'''),
# 5 -- the two sign-everyone-out buttons: doctor only on the screen
('''  <div class="foot">
    <form method="POST" action="/portal/forget"''',
'''  <div class="foot">
    <a class="forget" href="/portal/logout" style="display:inline-block;text-decoration:none">Sign out of this phone</a>
    {% if role == 'doctor' %}
    <form method="POST" action="/portal/forget"'''),
('''      <button class="forget" type="submit">Sign out everywhere (all apps)</button>
    </form>
    {% endif %}
  </div>''',
'''      <button class="forget" type="submit">Sign out everywhere (all apps)</button>
    </form>
    {% endif %}
    {% endif %}
  </div>'''),
# 5 -- and on the server
('''    new_seed = secrets.token_urlsafe(32)
    rotated = _rotate_seed_in_config(new_seed)''',
'''    if not _is_doctor(request):
        abort(403)                                             # S239: doctor only
    new_seed = secrets.token_urlsafe(32)
    rotated = _rotate_seed_in_config(new_seed)'''),
('''    if _sso_ready():
        try:
            clinic_users.bump_epoch(STORE)''',
'''    if not _is_doctor(request):
        abort(403)                                             # S239: doctor only
    if _sso_ready():
        try:
            clinic_users.bump_epoch(STORE)'''),
# 4 -- /portal/logout
('''@app.route("/portal/signout-all", methods=["POST"])''',
'''@app.route("/portal/logout")
def logout():
    """S239/F-242: sign THIS browser out -- clears the sign-in and any old device cookie. No login
    needed, so a stuck browser can always use it."""
    resp = make_response(redirect("/portal/login"))
    if _SSO_LIBS:
        try:
            resp.set_cookie(clinic_sso.COOKIE_NAME, "", **clinic_sso.clear_cookie_kwargs())
        except Exception:
            pass
    resp.delete_cookie(COOKIE_NAME, path="/portal")
    return resp


@app.route("/portal/signout-all", methods=["POST"])'''),
]
for i, (a, b) in enumerate(EDITS, 1):
    n = src.count(a)
    if n != 1:
        sys.exit("REFUSING: edit %d anchor found %d times (expected 1). Nothing changed." % (i, n))
    src = src.replace(a, b)
compile(src, P, "exec")
if "--dry-run" in sys.argv:
    print("DRY RUN ok -- %d edits apply; new md5 %s" % (len(EDITS), hashlib.md5(src.encode()).hexdigest()))
    sys.exit(0)
bak = P + ".bak_S239_F242_" + time.strftime("%Y%m%d_%H%M%S")
shutil.copy2(P, bak)
open(P, "w", encoding="utf-8").write(src)
print("PATCHED %s -> %s  (backup %s)" % (have, hashlib.md5(src.encode("utf-8")).hexdigest(), bak))
